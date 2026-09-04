#!/usr/bin/env python3
"""Run a generated CHIA UVM environment with Verilator + UVM.

The worker deliberately keeps execution deterministic:
  * generated_tb/generation_manifest.yaml is the source of TB file order;
  * UVM is compiled with UVM_NO_DPI;
  * the CHIA Python reference model is linked through ref_model_adapter.cpp;
  * every test is run behind a hard OS timeout;
  * a structured simulation_result.json is emitted for the repair loop.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

UVM_HOME = Path(os.environ.get("UVM_HOME", "/opt/uvm/src"))
DEFAULT_TIMEOUT = 60
DEFAULT_BUILD_TIMEOUT = 1800
MAX_LOG_CHARS = 12000


def run_cmd(
    cmd: list[str],
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env if env is not None else os.environ.copy(),
    )


def tail(text: str, limit: int = MAX_LOG_CHARS) -> str:
    return text[-limit:] if len(text) > limit else text


def load_manifest(tb_dir: Path) -> dict[str, Any]:
    path = tb_dir / "generation_manifest.yaml"
    if not path.exists():
        raise RuntimeError(f"Missing generation manifest: {path}")
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid generation_manifest.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("generation_manifest.yaml must contain a mapping")
    return data


def validate_manifest(manifest: dict[str, Any], tb_dir: Path) -> tuple[str, Path, list[Path], list[str]]:
    top_module = manifest.get("top_module")
    top_file = manifest.get("top_file")
    compile_files = manifest.get("compile_files")
    tests = manifest.get("test_classes")

    if not top_module or not isinstance(top_module, str):
        raise RuntimeError("Manifest field 'top_module' is required")
    if not top_file or not isinstance(top_file, str):
        raise RuntimeError("Manifest field 'top_file' is required")
    if not isinstance(compile_files, list) or not compile_files:
        raise RuntimeError("Manifest field 'compile_files' must be a non-empty list")
    if not isinstance(tests, list) or not tests:
        raise RuntimeError("Manifest field 'test_classes' must be a non-empty list")

    def resolve_tb_file(name: str) -> Path:
        p = (tb_dir / name).resolve()
        if tb_dir.resolve() not in p.parents and p != tb_dir.resolve():
            raise RuntimeError(f"Manifest file escapes TB directory: {name}")
        if not p.exists():
            raise RuntimeError(f"Manifest references missing file: {name}")
        if p.suffix.lower() != ".sv":
            raise RuntimeError(f"compile_files may only contain .sv files: {name}")
        return p

    top_path = resolve_tb_file(top_file)
    files = [resolve_tb_file(str(x)) for x in compile_files]
    test_names = [str(x) for x in tests if str(x).strip()]
    if not test_names:
        raise RuntimeError("Manifest contains no runnable tests")
    return top_module, top_path, files, test_names



def detect_compatibility_findings(tb_dir: Path) -> list[dict[str, str]]:
    """Detect known Verilator/UVM generation patterns before/after build.

    These findings are evidence for diagnosis; they do not replace compiler
    results and do not attempt to edit the generated environment.
    """
    findings: list[dict[str, str]] = []
    for path in sorted(tb_dir.glob("*.sv")):
        text = path.read_text(errors="replace")
        text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        if re.search(r"virtual\s+[A-Za-z_]\w*\s*#\s*\(", text):
            findings.append({
                "code": "parameterized_virtual_interface",
                "file": path.name,
                "message": "Parameterized virtual-interface type detected; use virtual <dut>_if with concrete interface widths.",
            })
        if re.search(r"uvm_config_db\s*#\s*\(\s*virtual\s+[A-Za-z_]\w*\s*#", text):
            findings.append({
                "code": "parameterized_config_db_virtual_interface",
                "file": path.name,
                "message": "uvm_config_db is specialized with a parameterized virtual-interface type, a known Verilator 5.042 compatibility hazard.",
            })
    return findings

def classify_build_error(log: str) -> str:
    lower = log.lower()
    if "uvm_hdl_" in log or "uvm_re_" in log or "undefined reference to `uvm" in lower:
        return "toolchain_or_uvm_dpi_error"
    if "internal fault" in lower or "corrupted size" in lower or "mismatching next->prev_size" in lower:
        return "verilator_internal_fault"
    if "undefined reference" in lower:
        return "link_error"
    if re.search(r"%Error", log) or "syntax error" in lower:
        return "compile_or_elaboration_error"
    return "unknown_build_error"


def classify_runtime(log: str, returncode: int, timed_out: bool) -> str:
    if timed_out:
        return "hang"
    if "UVM_FATAL" in log:
        return "uvm_fatal"
    if "UVM_ERROR" in log:
        return "uvm_error"
    if returncode != 0:
        return "runtime_error"
    return "pass"


def parse_counts(log: str) -> dict[str, int]:
    def count(pattern: str) -> int:
        return len(re.findall(pattern, log))

    return {
        "uvm_errors": count(r"\bUVM_ERROR\b"),
        "uvm_fatals": count(r"\bUVM_FATAL\b"),
        "uvm_warnings": count(r"\bUVM_WARNING\b"),
        "scoreboard_mismatches": count(r"\bmismatch\b"),
    }


def build_reference_model(tb_dir: Path, build_timeout: int) -> dict[str, Any]:
    """Build the Python-reference-model DPI bridge inside the sim container.

    Prefer the generated build_dpi.sh so the generated environment remains the
    source of truth.  If an older TB does not contain that script, fall back to
    the same deterministic g++ command here.  In both cases the resulting
    adapter is a shared library; ref_model_adapter.cpp is never passed to
    Verilator as a compilation unit.
    """
    script = tb_dir / "build_dpi.sh"
    adapter = tb_dir / "ref_model_adapter.cpp"
    ref_model = tb_dir / "ref_model.py"
    output = tb_dir / "libchia_ref_model.so"

    if not adapter.exists():
        return {"status": "fail", "category": "generation_missing_reference_model_adapter", "log": str(adapter)}
    if not ref_model.exists():
        return {"status": "fail", "category": "generation_missing_reference_model", "log": str(ref_model)}

    output.unlink(missing_ok=True)

    if script.exists():
        cmd = ["bash", str(script)]
    else:
        if not shutil.which("g++"):
            return {"status": "fail", "category": "toolchain_missing_gxx", "log": "g++ not found"}
        try:
            cxxflags = subprocess.check_output(
                ["python3-config", "--embed", "--cflags"], text=True
            ).split()
            ldflags = subprocess.check_output(
                ["python3-config", "--embed", "--ldflags"], text=True
            ).split()
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            return {"status": "fail", "category": "toolchain_missing_python_config", "log": str(exc)}

        # Keep the Python shared library discoverable when the final Verilator
        # executable starts.  python3-config's -L flags are link-time only.
        python_prefix = Path(sys.executable).resolve().parent.parent
        python_lib = python_prefix / "lib"
        cmd = [
            "g++", "-std=c++17", "-fPIC", "-shared",
            *cxxflags,
            str(adapter),
            *ldflags,
            f"-Wl,-rpath,{python_lib}",
            "-o", str(output),
        ]

    try:
        result = run_cmd(cmd, cwd=tb_dir, timeout=build_timeout)
    except subprocess.TimeoutExpired as exc:
        log = tail((exc.stdout or "") + (exc.stderr or ""))
        return {"status": "fail", "category": "dpi_build_timeout", "log": log, "command": cmd}
    except Exception as exc:
        return {"status": "fail", "category": "dpi_build_invocation_error", "log": str(exc), "command": cmd}

    log = result.stdout + result.stderr
    if result.returncode != 0:
        return {
            "status": "fail",
            "category": "dpi_build_error",
            "returncode": result.returncode,
            "log": tail(log),
            "command": cmd,
        }
    if not output.exists():
        return {
            "status": "fail",
            "category": "dpi_library_missing",
            "returncode": result.returncode,
            "log": tail(log),
            "command": cmd,
        }

    return {
        "status": "pass",
        "returncode": result.returncode,
        "library": str(output),
        "log": tail(log),
        "command": cmd,
    }


def build(
    rtl: Path,
    tb_dir: Path,
    compile_files: list[Path],
    top_module: str,
    build_dir: Path,
    build_timeout: int,
) -> dict[str, Any]:
    if not shutil.which("verilator"):
        return {"status": "fail", "category": "toolchain_missing_verilator", "log": "verilator not found"}
    if not (UVM_HOME / "uvm_pkg.sv").exists():
        return {"status": "fail", "category": "toolchain_missing_uvm", "log": str(UVM_HOME / "uvm_pkg.sv") + " not found"}

    build_dir.mkdir(parents=True, exist_ok=True)

    dpi_result = build_reference_model(tb_dir, build_timeout)
    if dpi_result["status"] != "pass":
        return dpi_result

    dpi_library = Path(dpi_result["library"])

    # The reference-model adapter is already compiled as a shared library by
    # build_dpi.sh.  Verilator only needs to link that library; it must not
    # compile ref_model_adapter.cpp itself.
    python_prefix = Path(sys.executable).resolve().parent.parent
    python_lib = python_prefix / "lib"
    linker_flags = (
        f"-L{tb_dir} -lchia_ref_model "
        f"-Wl,-rpath,{tb_dir} "
        f"-Wl,-rpath,{python_lib}"
    )

    cmd = [
        "verilator",
        "-Wno-fatal",
        "--binary",
        "--timing",
        "-j",
        "0",
        "--top-module",
        top_module,
        "--Mdir",
        str(build_dir),
        f"+incdir+{UVM_HOME}",
        f"+incdir+{tb_dir}",
        "+define+UVM_NO_DPI",
        "-Wno-TIMESCALEMOD",
        str(UVM_HOME / "uvm_pkg.sv"),
        str(rtl),
        *[str(p) for p in compile_files],
        "--LDFLAGS",
        linker_flags,
    ]

    try:
        result = run_cmd(cmd, cwd=tb_dir, timeout=build_timeout)
    except subprocess.TimeoutExpired as exc:
        log = tail((exc.stdout or "") + (exc.stderr or ""))
        return {"status": "fail", "category": "build_timeout", "log": log}
    except Exception as exc:
        return {"status": "fail", "category": "build_invocation_error", "log": str(exc)}

    log = result.stdout + result.stderr
    if result.returncode != 0:
        return {
            "status": "fail",
            "category": classify_build_error(log),
            "returncode": result.returncode,
            "log": tail(log),
            "command": cmd,
            "reference_model_dpi": dpi_result,
            "compatibility_findings": detect_compatibility_findings(tb_dir),
        }

    binary = build_dir / f"V{top_module}"
    if not binary.exists():
        return {
            "status": "fail",
            "category": "build_missing_executable",
            "returncode": result.returncode,
            "log": tail(log),
            "command": cmd,
            "reference_model_dpi": dpi_result,
        }

    return {
        "status": "pass",
        "returncode": result.returncode,
        "log": tail(log),
        "binary": str(binary),
        "command": cmd,
        "reference_model_dpi": dpi_result,
        "reference_model_library": str(dpi_library),
    }


def run_test(binary: Path, test_name: str, tb_dir: Path, timeout_s: int) -> dict[str, Any]:
    # Keep the generated TB's factory name exactly as supplied by the manifest.
    cmd = ["timeout", "--signal=TERM", "--kill-after=5", str(timeout_s), str(binary), f"+UVM_TESTNAME={test_name}"]
    env = os.environ.copy()
    python_prefix = Path(sys.executable).resolve().parent.parent
    python_lib = python_prefix / "lib"
    ld_parts = [str(tb_dir), str(python_lib)]
    if env.get("LD_LIBRARY_PATH"):
        ld_parts.append(env["LD_LIBRARY_PATH"])
    env["LD_LIBRARY_PATH"] = os.pathsep.join(ld_parts)

    try:
        result = run_cmd(cmd, cwd=tb_dir, timeout=timeout_s + 10, env=env)
    except subprocess.TimeoutExpired as exc:
        log = tail((exc.stdout or "") + (exc.stderr or ""))
        return {
            "status": "hang",
            "category": "worker_timeout",
            "timed_out": True,
            "returncode": None,
            "counts": parse_counts(log),
            "log": log,
            "command": cmd,
        }

    log = result.stdout + result.stderr
    # GNU timeout returns 124 for its own timeout and 137 when the kill-after
    # escalation reaches SIGKILL. Treat both as a hang.
    watchdog_expired = "CHIA_WATCHDOG_EXPIRED" in log
    timed_out = result.returncode in {124, 137} or watchdog_expired
    status = "hang" if watchdog_expired else classify_runtime(log, result.returncode, timed_out)

    return {
        "status": status,
        "category": "timeout" if timed_out else status,
        "timed_out": timed_out,
        "watchdog_expired": watchdog_expired,
        "returncode": result.returncode,
        "counts": parse_counts(log),
        "clean_exit": not timed_out and result.returncode == 0,
        "log": tail(log),
        "command": cmd,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtl", required=True)
    ap.add_argument("--tb", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--test-timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--build-timeout", type=int, default=DEFAULT_BUILD_TIMEOUT)
    args = ap.parse_args()

    rtl = Path(args.rtl).resolve()
    tb_dir = Path(args.tb).resolve()
    output = Path(args.output).resolve()
    build_dir = tb_dir / ".chia_sim" / "obj_dir"

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "fail",
        "rtl": str(rtl),
        "tb_dir": str(tb_dir),
        "toolchain": {
            "verilator": "5.042",
            "uvm": "1800.2-2020.3.1",
            "uvm_no_dpi": True,
        },
        "tests": {},
    }

    try:
        if not rtl.exists():
            raise RuntimeError(f"RTL not found: {rtl}")
        if not tb_dir.is_dir():
            raise RuntimeError(f"TB directory not found: {tb_dir}")

        manifest = load_manifest(tb_dir)
        top_module, top_file, compile_files, tests = validate_manifest(manifest, tb_dir)
        result["manifest"] = manifest
        result["top_module"] = top_module
        result["top_file"] = str(top_file)
        result["compile_files"] = [str(p) for p in compile_files]
        result["test_classes"] = tests

        build_result = build(
            rtl, tb_dir, compile_files, top_module, build_dir, args.build_timeout
        )
        result["build"] = build_result
        if build_result["status"] != "pass":
            result["status"] = "build_failure"
        else:
            binary = Path(build_result["binary"])
            for test in tests:
                test_result = run_test(binary, test, tb_dir, args.test_timeout)
                result["tests"][test] = test_result

            if all(x["status"] == "pass" and x["clean_exit"] for x in result["tests"].values()):
                result["status"] = "pass"
            elif any(x["status"] == "hang" for x in result["tests"].values()):
                result["status"] = "hang"
            elif any(x["status"] in {"uvm_error", "uvm_fatal", "runtime_error"} for x in result["tests"].values()):
                result["status"] = "functional_failure"
            else:
                result["status"] = "fail"

    except Exception as exc:
        result["status"] = "validation_error"
        result["error"] = str(exc)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
