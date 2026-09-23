#!/usr/bin/env python3
"""RTL -> UVM-verified RTL (uvm_loop) -> closed GDS (orfs_loop). See rtl_to_gds/README.md."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_UVM_DIR = REPO_ROOT / "uvm_loop"
DEFAULT_ORFS_REPO = Path(os.environ.get("CHIA_ORFS_REPO") or REPO_ROOT / "orfs_loop")

# Container-side mount points, fixed by cluster.yaml.
CONTAINER_ORFS = "/root/OpenROAD-flow-scripts"
CONTAINER_UVM = "/workspace"
CONTAINER_ORFS_REPO = "/root/chia-orfs"
DESIGNS_SUBDIR = "rtl_to_gds_designs"

# One self-contained folder per run: runs/<design>/<timestamp>/.
DEFAULT_RUNS_DIR = REPO_ROOT / "runs"

CLOCK_PORT_CANDIDATES = ["clk", "clock", "clk_i", "i_clk", "CLK", "clk_in"]

UVM_RESOURCES = ["rtl_extract", "sim_worker", "opencode_tools"]
ORFS_RESOURCES = ["orfs_run", "opencode_creds"]


class PipelineError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[rtl_to_gds] {msg}", flush=True)


# ------------------------------------------------------------- log collection

def start_console_tee(log_path: Path) -> subprocess.Popen:
    """Duplicate this process's stdout/stderr into `log_path` from here on.

    Redirects the real OS file descriptors (not just sys.stdout), via a
    `tee` child fed through a pipe, so output from subprocess.call'd children
    (run_uvm_stage, run_orfs_stage) is captured too, not just this script's
    own print()/log() calls. tee's own stdout stays attached to whatever this
    process inherited, so the console still sees everything live; it's the
    pipe write-end this process's fd 1/2 get pointed at.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    tee = subprocess.Popen(["tee", "-a", str(log_path)], stdin=subprocess.PIPE)
    os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
    os.dup2(tee.stdin.fileno(), sys.stderr.fileno())
    return tee


def stop_console_tee(tee: subprocess.Popen | None) -> None:
    if tee is None:
        return
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        tee.stdin.close()
        tee.wait(timeout=10)
    except Exception:
        pass


# Log-like files worth pulling into one place; explicitly excludes physical-
# design artifacts (GDS/DEF/LEF/CDL/ODB/build trees) which are large and are
# not logs -- they stay where ORFS/uvm_loop already put them.
_LOG_COLLECT_EXTENSIONS = {".log", ".json", ".yaml", ".yml", ".rpt", ".txt", ".done"}
_LOG_COLLECT_EXCLUDE_DIRS = {".chia_sim", "objects", "__pycache__", "tb", "src", "verified_rtl"}


def _copy_logs_from(src_root: Path, dest_root: Path) -> list[str]:
    """Copy every log-like file under src_root into dest_root, preserving its
    relative path. Best-effort: a file that fails to copy is skipped rather
    than failing the whole run -- this is convenience aggregation, not a
    source of truth (the originals are left in place, untouched).
    """
    copied = []
    if not src_root.is_dir():
        return copied
    for path in src_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _LOG_COLLECT_EXTENSIONS:
            continue
        rel = path.relative_to(src_root)
        if _LOG_COLLECT_EXCLUDE_DIRS & set(rel.parts[:-1]):
            continue
        dest = dest_root / rel
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            copied.append(str(rel))
        except OSError:
            continue
    return copied


def collect_run_logs(logs_dir: Path, uvm_dir: Path, cfg: dict,
                     run_dir: Path | None, result: dict) -> Path:
    """Gather every log/report/state file this exact run produced -- UVM
    verification and ORFS closure -- into one directory, so nothing has to be
    hunted down across uvm_loop/generated/designs/<design>/ and
    <orfs_repo>/orfs_runs/<run>/ separately afterwards.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)

    name = cfg["name"]
    output_parent = str(cfg.get("output_parent", "generated/designs")).rstrip("/")
    gen_root = uvm_dir / output_parent / name

    uvm_copied = _copy_logs_from(gen_root, logs_dir / "uvm")
    orfs_copied = _copy_logs_from(run_dir, logs_dir / "orfs") if run_dir else []

    # The ORFS design directory holds the config this run actually closed with
    # (config.mk, constraint.sdc, the synthesised RTL, rtl_handoff.json). It is
    # not log-shaped, so _copy_logs_from skips it -- but it is the one thing you
    # need to reproduce the result, so copy it wholesale.
    config_copied = []
    design_dir_str = result.get("orfs_design_dir")
    if design_dir_str and Path(design_dir_str).is_dir():
        dest = logs_dir / "orfs_config"
        for path in Path(design_dir_str).rglob("*"):
            if not path.is_file():
                continue
            target = dest / path.relative_to(design_dir_str)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                config_copied.append(str(path.relative_to(design_dir_str)))
            except OSError:
                continue

    (logs_dir / "manifest.json").write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "design": name,
        "uvm_source": str(gen_root),
        "orfs_source": str(run_dir) if run_dir else None,
        "orfs_config_source": design_dir_str,
        "final_gds": result.get("final_gds"),
        "uvm_files_collected": len(uvm_copied),
        "orfs_files_collected": len(orfs_copied),
        "orfs_config_files_collected": len(config_copied),
    }, indent=2))
    (logs_dir / "rtl_to_gds.json").write_text(json.dumps(result, indent=2, default=str))
    log(f"Collected {len(uvm_copied) + len(orfs_copied)} log files and "
        f"{len(config_copied)} ORFS config files into {logs_dir}")
    return logs_dir


# ---------------------------------------------------------------- stage 1: UVM

def resolve_design_config(arg: str, uvm_dir: Path) -> Path:
    for candidate in (Path(arg), uvm_dir / arg):
        if candidate.is_file():
            return candidate.resolve()
    raise PipelineError(f"Design config not found: {arg} (also tried under {uvm_dir})")


def run_uvm_stage(uvm_dir: Path, design_config: Path, supervised_iters: int | None) -> None:
    if supervised_iters is not None:
        cmd = ["./run_forever.sh", os.path.relpath(design_config, uvm_dir), str(supervised_iters)]
    else:
        cmd = [sys.executable, "-u", "-m", "pipeline.run14", "--design-config", str(design_config)]
    log(f"UVM stage: {' '.join(cmd)}  (cwd={uvm_dir})")
    rc = subprocess.call(cmd, cwd=uvm_dir)
    if rc != 0:
        raise PipelineError(f"UVM verification stage exited with status {rc}")


def load_handoff(uvm_dir: Path, cfg: dict, allow_unverified: bool) -> dict:
    """Read run14's RTL-verification state and locate the accepted RTL snapshot."""
    name = cfg["name"]
    output_parent = str(cfg.get("output_parent", "generated/designs")).rstrip("/")
    gen_root = uvm_dir / output_parent / name
    ver_root = gen_root / "rtl_verification"
    state_path = ver_root / "rtl_verification_state.json"
    if not state_path.exists():
        raise PipelineError(
            f"No RTL verification state at {state_path} -- the UVM loop has not "
            "reached its RTL verification phase for this design yet."
        )
    state = json.loads(state_path.read_text())

    verified = state.get("status") == "verified" and state.get("verified") is True
    # rtl_outcome=="no_repair" means the RTL-repair loop's diagnosis LLM
    # concluded no fix was needed -- but that conclusion can be reached
    # without a single genuinely passing simulation (e.g. "failures are
    # testbench-related, not RTL"), so it is NOT the same guarantee as
    # `verified`. Treating it as automatically handoff-eligible let the
    # LLM use no_repair as an escape hatch from the repair loop instead
    # of actually fixing the RTL until all required tests pass. It now
    # requires the same explicit --allow-unverified acknowledgement as
    # any other unverified state.
    if not verified:
        summary = {k: state.get(k) for k in ("status", "verified", "rtl_outcome", "stop_reason")}
        if not allow_unverified:
            raise PipelineError(
                f"RTL is not verified ({summary}); refusing to send it to ORFS. "
                "Re-run the UVM stage, or pass --allow-unverified to proceed anyway."
            )
        log(f"WARNING: proceeding with unverified RTL: {summary}")

    # The state file stores absolute host paths from whichever checkout ran it,
    # so rebuild the snapshot path from the layout rather than trusting them.
    accepted = ver_root / "accepted" / Path(cfg["rtl"]).name
    if not accepted.exists():
        raise PipelineError(f"Accepted RTL snapshot missing: {accepted}")

    rtl_info_path = gen_root / "rtl" / "rtl_info.json"
    rtl_info = json.loads(rtl_info_path.read_text()) if rtl_info_path.exists() else {}

    return {
        "design": name,
        "accepted_rtl": accepted,
        "state": state,
        "state_path": state_path,
        "verified": verified,
        "outcome": "verified" if verified else (state.get("rtl_outcome") or state.get("status")),
        "rtl_info": rtl_info,
    }


def detect_top(handoff: dict, override: str | None) -> str:
    if override:
        return override
    if handoff["rtl_info"].get("module"):
        return handoff["rtl_info"]["module"]
    modules = re.findall(r"^\s*module\s+(\w+)", handoff["accepted_rtl"].read_text(), re.M)
    if len(modules) == 1:
        return modules[0]
    raise PipelineError(f"Cannot determine top module (found {modules}); pass --top.")


def detect_clock_port(handoff: dict, override: str | None) -> str | None:
    if override:
        return None if override.lower() == "none" else override
    ports = handoff["rtl_info"].get("ports")
    if ports:
        inputs = {p["name"] for p in ports if p.get("direction") == "input"}
    else:
        inputs = set(re.findall(r"\binput\b[^;,)]*?\b(\w+)\s*[,;)]", handoff["accepted_rtl"].read_text()))
    for cand in CLOCK_PORT_CANDIDATES:
        if cand in inputs:
            return cand
    return None


# ------------------------------------------------------- stage 2: ORFS onboarding

_INOUT_RE = re.compile(r"\binout\s+(?:wire\s+|logic\s+|tri\s+)?(\[[^\]]+\]\s*)?(\w+)")


def split_tristate_ports(text: str) -> tuple[str, list[dict]]:
    """Move tri-state drivers on inout ports out to the pad: P -> P_pad_oe + P_pad_o."""
    # ORFS standard-cell flows have no tri-state cell mapping, so a core-level
    # `assign P = en ? v : 1'bz` fails synthesis; a real chip puts that buffer in the pad.
    changes = []
    for m in list(_INOUT_RE.finditer(text)):
        width, port = (m.group(1) or "").strip(), m.group(2)
        drivers = list(re.finditer(
            rf"^[ \t]*assign\s+{port}\s*=\s*(.+?)\s*\?\s*(.+?)\s*:\s*(?:\d*'[bB]z|'z)\s*;[^\n]*\n",
            text, re.M))
        refs = len(re.findall(rf"\b{port}\b", text))
        if len(drivers) != 1 or refs != 2:
            raise PipelineError(
                f"inout port {port!r}: expected exactly one `assign {port} = en ? v : 1'bz;` "
                f"and no other uses (found {len(drivers)} drivers, {refs} references). "
                "Split it by hand or pass --no-tristate-split."
            )
        en, val = drivers[0].group(1), drivers[0].group(2)
        oe, o = f"{port}_pad_oe", f"{port}_pad_o"
        w = f"{width} " if width else ""
        text = text.replace(drivers[0].group(0), f"    assign {oe} = {en};\n    assign {o} = {val};\n", 1)
        text = text.replace(m.group(0), f"output wire {w}{oe},\n    output wire {w}{o}", 1)
        changes.append({"port": port, "enable": en, "value": val,
                        "physical_ports": [oe, o], "pad_function": f"{port} = {oe} ? {o} : 'z"})
    return text, changes


def render_sdc(top: str, clock_port: str | None, period: float, io_pct: float) -> str:
    # `set clk_period` is the form orfs_config_bridge patches for CLOCK_PERIOD tuning.
    lines = [
        "# Generated by rtl_to_gds.py from UVM-verified RTL.",
        f"current_design {top}",
        "",
        f"set clk_period {period}",
        f"set clk_io_pct {io_pct}",
        "",
    ]
    if clock_port:
        lines += [
            f"create_clock -name core_clock -period $clk_period [get_ports {clock_port}]",
            "create_clock -name vclk -period $clk_period",
            "set non_clock_inputs [all_inputs -no_clocks]",
        ]
    else:
        lines += [
            "# No clock port detected: combinational design, constrained I/O-to-I/O",
            "# against a virtual clock.",
            "create_clock -name vclk -period $clk_period",
            "set non_clock_inputs [all_inputs]",
        ]
    lines += [
        "set_input_delay [expr $clk_period * $clk_io_pct] -clock vclk $non_clock_inputs",
        "set_output_delay [expr $clk_period * $clk_io_pct] -clock vclk [all_outputs]",
        "",
    ]
    return "\n".join(lines)


def render_config_mk(*, platform, top, nickname, verilog_files, sdc, clock_port, period,
                     core_utilization, place_density, synth_frontend) -> str:
    files = " \\\n\t".join(verilog_files)
    return (
        "# Generated by rtl_to_gds.py from UVM-verified RTL -- regenerate, don't hand-edit.\n"
        "# Paths are container paths inside the orfs_run workers.\n"
        f"export PLATFORM = {platform}\n"
        f"export DESIGN_NAME = {top}\n"
        f"export DESIGN_NICKNAME = {nickname}\n"
        "\n"
        f"export VERILOG_FILES = \\\n\t{files}\n"
        f"export SDC_FILE = {sdc}\n"
        + (f"export SYNTH_HDL_FRONTEND = {synth_frontend}\n" if synth_frontend else "")
        + "\n"
        + (f"export CLOCK_PORT = {clock_port}\n" if clock_port else "")
        + f"export CLOCK_PERIOD = {period}\n"
        "\n"
        f"export CORE_UTILIZATION = {core_utilization}\n"
        f"export PLACE_DENSITY = {place_density}\n"
    )


def onboard_into_orfs(handoff: dict, orfs_repo: Path, args) -> dict:
    flow_dir = orfs_repo / "orfs-native-build" / "flow"
    if not (flow_dir / "Makefile").exists():
        raise PipelineError(
            f"{flow_dir} is not an ORFS checkout. Initialise the submodule "
            "(git submodule update --init orfs_loop/orfs-native-build) and apply "
            "orfs-native-build.patch, or point --orfs-repo / CHIA_ORFS_REPO at a repo that has one."
        )

    top = detect_top(handoff, args.top)
    clock_port = detect_clock_port(handoff, args.clock_port)
    nickname = args.orfs_design_name or f"chia_{handoff['design']}".lower()
    if not re.fullmatch(r"[a-z0-9_]+", nickname):
        raise PipelineError(f"Invalid ORFS design name {nickname!r}")

    # ORFS's own flow/designs tree is root-owned, so designs live in the (user-owned)
    # orfs repo instead; orfs_loop resolves everything relative to config.mk's dir.
    rel_design = Path(DESIGNS_SUBDIR) / args.platform / nickname
    host_design = orfs_repo / rel_design
    (host_design / "src").mkdir(parents=True, exist_ok=True)

    rtl = handoff["accepted_rtl"]
    (host_design / "verified_rtl").mkdir(exist_ok=True)
    shutil.copy2(rtl, host_design / "verified_rtl" / rtl.name)
    physical_text, tristate_changes = rtl.read_text(), []
    if not args.no_tristate_split:
        physical_text, tristate_changes = split_tristate_ports(physical_text)
    physical_rtl = host_design / "src" / rtl.name
    physical_rtl.write_text(physical_text)
    for change in tristate_changes:
        log(f"  tri-state port {change['port']} -> {change['physical_ports']} (pad: {change['pad_function']})")

    c_design = f"{CONTAINER_ORFS_REPO}/{rel_design.as_posix()}"
    c_sdc = f"{c_design}/constraint.sdc"
    # Yosys's built-in reader rejects common SV (package imports in module headers,
    # `int unsigned` params), which the UVM loop's RTL routinely uses.
    frontend = args.synth_frontend
    if frontend == "auto":
        frontend = "slang" if rtl.suffix == ".sv" else ""
    elif frontend == "yosys":
        frontend = ""
    (host_design / "constraint.sdc").write_text(
        render_sdc(top, clock_port, args.clock_period, args.clock_io_pct)
    )
    (host_design / "config.mk").write_text(render_config_mk(
        platform=args.platform, top=top, nickname=nickname,
        verilog_files=[f"{c_design}/src/{rtl.name}"], sdc=c_sdc, clock_port=clock_port,
        period=args.clock_period, core_utilization=args.core_utilization,
        place_density=args.place_density, synth_frontend=frontend,
    ))

    provenance = {
        "source_design": handoff["design"],
        "rtl_outcome": handoff["outcome"],
        "verified": handoff["verified"],
        "accepted_rtl": str(rtl),
        "accepted_rtl_md5": hashlib.md5(rtl.read_bytes()).hexdigest(),
        "physical_rtl_md5": hashlib.md5(physical_rtl.read_bytes()).hexdigest(),
        "physical_rtl_identical_to_verified": not tristate_changes,
        "tristate_port_splits": tristate_changes,
        "verification_state": str(handoff["state_path"]),
        "top_module": top,
        "clock_port": clock_port,
        "clock_period": args.clock_period,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    (host_design / "rtl_handoff.json").write_text(json.dumps(provenance, indent=2))

    log(f"ORFS design written: {host_design}")
    log(f"  top={top} clock_port={clock_port or '(none, virtual clock)'} period={args.clock_period}")
    return {
        "nickname": nickname,
        "host_design_dir": host_design,
        "config_mk": f"{c_design}/config.mk",
        "reports_root": f"{CONTAINER_ORFS}/flow/reports/{args.platform}/{nickname}/base",
        "provenance": provenance,
    }


# --------------------------------------------------------------- stage 3: ORFS

def run_orfs_stage(orfs_repo: Path, design: dict, extra: list[str]) -> tuple[int, Path]:
    cmd = [
        sys.executable, "-u", str(orfs_repo / "orfs_loop.py"),
        "--design-name", design["nickname"],
        "--design-config-mk", design["config_mk"],
        "--reports-root", design["reports_root"],
    ]
    if "--run-dir" in extra:
        run_dir = Path(extra[extra.index("--run-dir") + 1])
        run_dir = run_dir if run_dir.is_absolute() else orfs_repo / run_dir
    else:
        run_dir = orfs_repo / "orfs_runs" / f"{design['nickname']}-{int(time.time())}"
        cmd += ["--run-dir", str(run_dir)]
    cmd += extra
    log(f"ORFS stage: {' '.join(cmd)}  (cwd={orfs_repo})")
    return subprocess.call(cmd, cwd=orfs_repo), run_dir


# ------------------------------------------------------------------ preflight

def container_mounts(container: str) -> dict[str, Path] | None:
    """Destination -> host source for a container, or None if it doesn't exist."""
    try:
        out = subprocess.run(
            ["docker", "inspect", "-f", "{{json .Mounts}}", container],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return {m["Destination"]: Path(m["Source"]).resolve() for m in json.loads(out.stdout or "[]")}


def preflight(uvm_dir: Path, orfs_repo: Path, need_uvm: bool, need_orfs: bool) -> None:
    if not (need_uvm or need_orfs):
        return
    import ray

    ray.init(address="auto", logging_level="ERROR", log_to_driver=False)
    try:
        available = ray.cluster_resources()
    finally:
        ray.shutdown()

    needed = (UVM_RESOURCES if need_uvm else []) + (ORFS_RESOURCES if need_orfs else [])
    missing = [r for r in needed if available.get(r, 0) < 1]
    problems = [f"Ray cluster has no '{r}' resource" for r in missing]

    user = os.environ.get("USER", "")
    checks = []
    if need_uvm:
        checks += [(f"chia-rtl-{user}-0", CONTAINER_UVM, uvm_dir),
                   (f"chia-sim-{user}-0", CONTAINER_UVM, uvm_dir),
                   (f"chia-opencode-{user}-0", CONTAINER_UVM, uvm_dir)]
    if need_orfs:
        checks += [(f"chia-orfs-{user}-0", CONTAINER_ORFS_REPO, orfs_repo)]
    for container, dest, expected in checks:
        mounts = container_mounts(container)
        if mounts is None:
            continue
        src = mounts.get(dest)
        if src is None:
            problems.append(f"{container} has no mount at {dest} (expected {expected})")
        elif src != expected.resolve():
            problems.append(f"{container} mounts {src} at {dest}, expected {expected}")

    if problems:
        raise PipelineError(
            "Preflight failed:\n  - " + "\n  - ".join(problems) +
            "\nBring the combined cluster up with rtl_to_gds/cluster.yaml "
            "(see its header), or pass --skip-preflight."
        )
    log("Preflight OK")


# ----------------------------------------------------------------------- main

def parse_args(argv: list[str]):
    if "--" in argv:
        split = argv.index("--")
        argv, orfs_extra = argv[:split], argv[split + 1:]
    else:
        orfs_extra = []

    ap = argparse.ArgumentParser(description="UVM-verify RTL, then close it to GDS with ORFS.")
    ap.add_argument("--design-config", required=True,
                    help="uvm_loop design YAML (path, or relative to uvm_loop/)")
    ap.add_argument("--uvm-dir", type=Path, default=DEFAULT_UVM_DIR)
    ap.add_argument("--orfs-repo", type=Path, default=DEFAULT_ORFS_REPO,
                    help="Directory holding orfs_loop.py + orfs-native-build/; must be the one "
                         "the orfs_run workers mount (default: $CHIA_ORFS_REPO or orfs_loop/)")
    ap.add_argument("--skip-uvm", action="store_true",
                    help="Don't run the UVM loop; use its existing verified result")
    ap.add_argument("--uvm-supervised", type=int, metavar="MAX_ITERS", default=None,
                    help="Run the UVM loop under run_forever.sh with this iteration cap")
    ap.add_argument("--allow-unverified", action="store_true",
                    help="Hand RTL to ORFS even if the UVM loop did not verify it")
    ap.add_argument("--platform", default="sky130hd")
    ap.add_argument("--orfs-design-name", default=None,
                    help="ORFS design directory / nickname (default: chia_<design>)")
    ap.add_argument("--top", default=None, help="Top module (default: from rtl_info.json)")
    ap.add_argument("--clock-port", default=None,
                    help="Clock port (default: auto-detect; 'none' for combinational)")
    ap.add_argument("--clock-period", type=float, default=10.0,
                    help="Starting clock period, in the platform's SDC units (ns for sky130hd)")
    ap.add_argument("--clock-io-pct", type=float, default=0.2)
    ap.add_argument("--core-utilization", type=float, default=40.0)
    ap.add_argument("--place-density", type=float, default=0.6)
    ap.add_argument("--no-tristate-split", action="store_true",
                    help="Don't move inout tri-state drivers out to <port>_pad_oe/_pad_o")
    ap.add_argument("--synth-frontend", choices=["auto", "slang", "yosys"], default="auto",
                    help="HDL reader for synthesis (auto: slang for .sv, yosys otherwise)")
    ap.add_argument("--prepare-only", action="store_true",
                    help="Stop after writing the ORFS design; print the orfs_loop command")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--result-json", type=Path, default=None,
                    help="Also write the run record (stage timings, handoff, ORFS outcome) here")
    ap.add_argument("--runs-dir", type=Path, default=None,
                    help=f"Parent directory for run folders (default: {DEFAULT_RUNS_DIR}). "
                         "Each run gets <runs-dir>/<design>/<timestamp>/ holding the UVM "
                         "logs, the ORFS logs, and the exact ORFS config the run used.")
    ap.add_argument("--logs-dir", type=Path, default=None,
                    help="Use this exact directory for the run folder instead of the "
                         "<runs-dir>/<design>/<timestamp> layout.")
    ap.add_argument("--no-logs-collect", action="store_true",
                    help="Disable log collection and the console tee entirely")
    args = ap.parse_args(argv)
    return args, orfs_extra


def main(argv: list[str] | None = None) -> int:
    args, orfs_extra = parse_args(sys.argv[1:] if argv is None else argv)
    uvm_dir = args.uvm_dir.resolve()
    orfs_repo = args.orfs_repo.resolve()

    stages: dict[str, dict] = {}
    result: dict = {"argv": sys.argv, "stages": stages}
    # Set before the try block so finish() (reachable from the except clause
    # too) never NameErrors if something fails before these are computed,
    # e.g. an unresolvable --design-config.
    cfg: dict = {}
    logs_dir: Path | None = None
    tee: subprocess.Popen | None = None

    def timed(name, fn, *a):
        start = time.time()
        stages[name] = {"started_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start))}
        try:
            return fn(*a)
        finally:
            stages[name]["wall_seconds"] = round(time.time() - start, 1)

    def finish(rc: int) -> int:
        result["exit_code"] = rc
        if args.result_json:
            args.result_json.parent.mkdir(parents=True, exist_ok=True)
            args.result_json.write_text(json.dumps(result, indent=2, default=str))
        run_dir_str = result.get("orfs_run_dir")
        run_dir = Path(run_dir_str) if run_dir_str else None
        if run_dir and run_dir.is_dir():
            (run_dir / "rtl_to_gds.json").write_text(json.dumps(result, indent=2, default=str))
        if not args.no_logs_collect and logs_dir is not None and cfg:
            try:
                collect_run_logs(logs_dir, uvm_dir, cfg, run_dir, result)
            except Exception as exc:  # best-effort: never fail a run over log collection
                log(f"WARNING: log collection failed: {exc}")
        stop_console_tee(tee)
        return rc

    try:
        design_config = resolve_design_config(args.design_config, uvm_dir)
        cfg = yaml.safe_load(design_config.read_text())

        if args.logs_dir:
            logs_dir = args.logs_dir.resolve()
        else:
            runs_root = (args.runs_dir or DEFAULT_RUNS_DIR).resolve()
            stamp = time.strftime("%Y%m%d_%H%M%S")
            logs_dir = runs_root / cfg["name"] / stamp
        if not args.no_logs_collect:
            tee = start_console_tee(logs_dir / "console.log")
            log(f"Logs for this run will be collected under {logs_dir}")

        run_uvm = not args.skip_uvm
        if not args.skip_preflight:
            preflight(uvm_dir, orfs_repo, need_uvm=run_uvm, need_orfs=not args.prepare_only)

        if run_uvm:
            timed("uvm", run_uvm_stage, uvm_dir, design_config, args.uvm_supervised)

        handoff = load_handoff(uvm_dir, cfg, args.allow_unverified)
        result["uvm_state"] = handoff["state"]
        log(f"RTL handoff: {handoff['accepted_rtl']} ({handoff['outcome']})")

        design = onboard_into_orfs(handoff, orfs_repo, args)
        result["rtl_handoff"] = design["provenance"]
        result["orfs_design_dir"] = str(design["host_design_dir"])

        if args.prepare_only:
            log("Prepared only. Run the ORFS loop with:")
            print(f"  cd {orfs_repo} && python3 orfs_loop.py --design-name {design['nickname']} "
                  f"--design-config-mk {design['config_mk']} "
                  f"--reports-root {design['reports_root']} {' '.join(orfs_extra)}")
            return finish(0)

        rc, run_dir = timed("orfs", run_orfs_stage, orfs_repo, design, orfs_extra)
    except PipelineError as exc:
        log(f"ERROR: {exc}")
        result["error"] = str(exc)
        return finish(2)

    summary_path = run_dir / "summary.json"
    orfs_summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    final_gds = run_dir / "final.gds"
    result.update({
        "orfs_run_dir": str(run_dir),
        "orfs_status": orfs_summary.get("status"),
        "final_gds": str(final_gds) if final_gds.exists() else None,
        "orfs_exit_code": rc,
    })
    log(f"ORFS status: {result['orfs_status']}  exit={rc}")
    log(f"Final GDS: {result['final_gds'] or 'not produced'}")
    return finish(rc)


if __name__ == "__main__":
    sys.exit(main())
