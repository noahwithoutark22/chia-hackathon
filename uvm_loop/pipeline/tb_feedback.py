"""LLM diagnosis and repair loop for generated UVM environments."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
import yaml

from pipeline.pyuvm_reference import pyuvm_api_reference

MAX_LOG_CHARS = 20000


def _runtime_test_name(class_name: str, declaration: str, manifest: dict[str, Any]) -> str:
    params = re.search(r"#\s*\((.*?)\)", declaration, re.S)
    if not params:
        return class_name
    body = params.group(1)

    matches = re.findall(
        r"parameter\s+(?:int|integer|longint|bit|logic)\s+(\w+)\s*=\s*([^,]+)",
        body,
    )

    if len(matches) == 1:
        pname, default = matches[0]
        if pname in manifest:
            return f"{class_name}#({manifest[pname]})"
        if default.strip().isdigit():
            return f"{class_name}#({default.strip()})"
    return class_name


def ensure_simulation_manifest(tb_dir: str) -> Path:
    """Validate/enrich the existing generation manifest deterministically."""
    root = Path(tb_dir).resolve()
    manifest_path = root / "generation_manifest.yaml"

    if not manifest_path.exists():
        raise RuntimeError(f"Missing generation_manifest.yaml: {manifest_path}")

    data = yaml.safe_load(manifest_path.read_text()) or {}
    if not isinstance(data, dict):
        raise RuntimeError("generation_manifest.yaml must be a YAML mapping")

    files = [str(x) for x in data.get("files", [])]
    filelist = root / "filelist.f"

    if filelist.exists():
        listed = []
        for line in filelist.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and line.endswith(".sv"):
                listed.append(line)
        if listed:
            files = listed

    sv_files = [x for x in files if x.endswith(".sv") and (root / x).exists()]
    if not sv_files:
        sv_files = [p.name for p in sorted(root.glob("*.sv"))]

    if not sv_files:
        raise RuntimeError("No generated SystemVerilog files found")

    top_file = data.get("top_file")
    top_module = data.get("top_module")

    if not top_file or not top_module:
        for name in reversed(sv_files):
            text = (root / name).read_text(errors="replace")
            if "run_test" not in text:
                continue
            m = re.search(
                r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\b",
                text,
            )
            if m:
                top_file = name
                top_module = m.group(1)
                break

    if not top_file or not top_module:
        raise RuntimeError("Could not determine top_file/top_module")

    tests = data.get("test_classes")
    dut_name = str(data.get("dut_name", ""))

    if isinstance(tests, list):
        tests = [
            str(x)
            for x in tests
            if str(x).split("#", 1)[0].startswith(f"{dut_name}_test_")
        ]

    if not tests:
        tests = []
        for name in sv_files:
            text = (root / name).read_text(errors="replace")
            for m in re.finditer(
                r"\bclass\s+([A-Za-z_][A-Za-z0-9_$]*)\s*(#\s*\([^;{]*\))?\s+extends\s+[A-Za-z_][A-Za-z0-9_$]*",
                text,
                re.S,
            ):
                cls = m.group(1)
                if dut_name and cls.startswith(f"{dut_name}_test_"):
                    tests.append(
                        _runtime_test_name(cls, m.group(2) or "", data)
                    )

        tests = list(dict.fromkeys(tests))

    if not tests:
        raise RuntimeError("Could not determine runnable UVM test classes")

    data["top_module"] = top_module
    data["top_file"] = top_file
    data["compile_files"] = sv_files
    data["test_classes"] = tests

    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False))
    return manifest_path


# =========================================================
# Generated-TB compatibility diagnosis
# =========================================================

def scan_generated_tb_compatibility(tb_dir: str) -> list[dict[str, Any]]:
    """
    Deterministically identify generated constructs known to be incompatible
    with the project's Verilator 5.042 + UVM 1800.2-2020.3.1 flow.

    These are generation defects, not simulator defects, when found in the
    generated TB.
    """
    root = Path(tb_dir).resolve()
    findings: list[dict[str, Any]] = []

    patterns = [
        (
            "parameterized_interface_declaration",
            re.compile(
                r"(?im)^\s*interface\s+[A-Za-z_][A-Za-z0-9_$]*\s*#\s*\("
            ),
            "Parameterized interface declaration found. "
            "The interface declaration must be concrete/non-parameterized."
        ),
        (
            "parameterized_virtual_interface",
            re.compile(
                r"(?i)\bvirtual\s+[A-Za-z_][A-Za-z0-9_$]*_if\s*#\s*\("
            ),
            "Parameterized virtual-interface type found. "
            "Use virtual <dut>_if without #(...)."
        ),
        (
            "parameterized_config_db_virtual_interface",
            re.compile(
                r"(?i)uvm_config_db\s*#\s*\(\s*virtual\s+"
                r"[A-Za-z_][A-Za-z0-9_$]*_if\s*#\s*\("
            ),
            "uvm_config_db is specialized with a parameterized virtual-interface "
            "type. Use uvm_config_db#(virtual <dut>_if)."
        ),
    ]

    for sv_path in sorted(root.glob("*.sv")):
        source = sv_path.read_text(errors="replace")
        lines = source.splitlines()

        for code, pattern, message in patterns:
            for match in pattern.finditer(source):
                line_no = source.count("\n", 0, match.start()) + 1
                source_line = lines[line_no - 1].strip() if lines else ""
                findings.append(
                    {
                        "file": str(sv_path.relative_to(root)),
                        "line": line_no,
                        "code": code,
                        "message": message,
                        "source": source_line,
                    }
                )

    return findings


def format_compatibility_findings(tb_dir: str) -> str:
    findings = scan_generated_tb_compatibility(tb_dir)
    if not findings:
        return "NONE"
    return json.dumps(findings, indent=2)


def build_diagnosis_prompt(
    result_path: str,
    spec: str,
    ref_model: str,
    plan: str,
    tb_dir: str = "/workspace",
    update_plan_path: str = "/workspace/results/tb_update_plan.yaml",
) -> str:
    compatibility_findings = format_compatibility_findings(tb_dir)

    return f"""
You are the failure-diagnosis engineer for an LLM-generated cocotb+pyuvm environment.

The RTL implementation is intentionally unavailable to you. Work only from the
specification, reference model, verification plan, generated TB, and simulation
result. Do NOT attempt to locate, reconstruct, or request RTL. Do NOT edit any
files in this step.

Read these authoritative inputs:

- Specification: {spec}
- Reference model: {ref_model}
- Accepted verification plan: {plan}
- Generated UVM environment: {tb_dir}
- Simulation result: {result_path}

The simulation result contains compiler/linker/runtime logs. Determine the
root cause, but do not treat generic Verilator/UVM infrastructure requirements
as a DUT-specific defect.

KNOWN VERILATOR 5.042 + UVM 1800.2-2020.3.1 GENERATION RULE:
A parameterized virtual-interface type such as `virtual <dut>_if#(...)`, a
parameterized interface declaration such as `interface <dut>_if#(...)`, or a
`uvm_config_db` specialization using that parameterized virtual-interface type
is a GENERATION BUG.

The safe pattern is:
1. concrete/non-parameterized interface declaration with concrete signal widths;
2. `virtual <dut>_if` in driver/monitor/scoreboard/sequences;
3. `uvm_config_db#(virtual <dut>_if)` consistently for set/get;
4. DUT parameterization remains allowed at the DUT instantiation.

DETERMINISTIC COMPATIBILITY SCAN:
{compatibility_findings}

IMPORTANT CLASSIFICATION RULE:
- If the simulation reports a Verilator internal fault AND the deterministic
  scan identifies one of the forbidden parameterized-interface patterns,
  verdict MUST be generation_bug.
- Do NOT classify that case as template_bug.
- Do NOT propose changing Verilator, UVM, Docker, compiler flags, RTL,
  specification, reference model, or verification plan.
- Repair only the generated TB files containing the forbidden patterns.
- If the internal fault occurs with NONE of the forbidden patterns, inspect
  the generated files and simulation command carefully before classifying it.
  Do not assume every internal fault is a simulator defect.

DIAGNOSIS GROUNDING RULES:

The simulation result is the primary evidence for the diagnosis.

Before assigning a root cause or proposing a TB change:
1. Identify the exact failing test and failure.
2. Extract the exact generated-TB file, line, function/class, and error message
   when available.
3. Inspect the corresponding generated-TB implementation.
4. Verify that the proposed root cause actually exists in that code.
5. Verify that the proposed root cause is consistent with the observed
   simulation state and error.
6. Only then create the repair plan.

Do not infer a root cause merely because it is a common failure mode.

In particular:
- Do not classify a failure as reset-related unless the simulation evidence
  shows that reset was active or the failure is directly caused by reset
  handling.
- Do not claim that code is missing a behavior if the inspected generated TB
  already implements that behavior.
- Do not propose changing a file unrelated to the actual failure location
  unless the inspected code proves that the unrelated file is the true root
  cause.
- If the evidence does not support the diagnosis, investigate the generated TB
  further rather than inventing a cause.

The changes section must contain the minimal generated-TB change that fixes the
diagnosed root cause.

Before finalizing the YAML, check this chain for consistency:

SIMULATION FAILURE
    -> FAILING FILE / FUNCTION / LINE
    -> INSPECTED GENERATED CODE
    -> ROOT CAUSE
    -> PROPOSED CHANGE

If the proposed change is already present in the generated TB, do not propose
that same change again. Re-evaluate the root cause.

Create {update_plan_path} with exactly:

version: "1.0"

verdict: generation_bug | template_bug | non_actionable

root_cause:
  category: compile | elaboration | connectivity | driver | monitor | sequence | scoreboard | reference_model_integration | reset | timeout | other
  file: <relative generated-TB file, or null if not applicable>
  line: <line number, or null if not available>
  function: <function/class/method, or null if not available>
  summary: <short root cause>
  evidence: <specific evidence from the result>

changes:
  - file: <relative path under generated_tb>
    action: modify | add | delete
    reason: <why>
    instructions:
      - <minimal concrete change>

validation:
  tests:
    - <exact runnable test name>
  requirements:
    - build succeeds
    - no UVM_ERROR or UVM_FATAL
    - no reference-model mismatch

Rules:
- Do not propose changing RTL, spec, reference model, or verification plan.
- Do not propose unrelated cleanup or redesign.
- Only list files that actually need modification.
- If the result is a clean pass, verdict must be non_actionable.
- If the failure is a genuine simulator/toolchain/template problem with no
  generated-TB defect responsible, verdict must be template_bug.
- If a test timed out, determine whether the watchdog itself is missing/broken
  before calling it template_bug; a generated driver/sequence/objection
  deadlock is generation_bug.
- Keep the plan minimal and directly actionable.
- For forbidden virtual-interface/config_db patterns, preserve concrete widths
  in the interface and make set/get use exactly the same non-parameterized
  virtual-interface type.
""".strip()


def build_repair_prompt(plan_path: str, workspace: str = "/workspace") -> str:
    return f"""
You are repairing an LLM-generated cocotb+pyuvm verification environment.
{pyuvm_api_reference()}

Your filesystem is intentionally sanitized. The RTL implementation is NOT
available to you. Work only inside {workspace}. Do not search parent
directories, request RTL, or attempt to reconstruct it.

Read:
- {plan_path}
- {workspace}/tb
- {workspace}/specification.md
- {workspace}/reference_model.py
- {workspace}/verification_plan.yaml

Apply ONLY the changes described in {plan_path}.

Rules:
- Modify only files under {workspace}/tb.
- Do not modify the specification, reference model, or verification plan.
- Do not redesign the UVM architecture.
- Preserve existing test names and manifest/build configuration unless the
  update plan explicitly requires changing them.
- Fix the root cause, not just the observed symptom.
- Preserve the existing cocotb+pyuvm architecture and contract.
- Do not introduce SystemVerilog UVM code or RTL dependencies.
- After editing, inspect all affected files for syntax, connectivity, widths,
  UVM phase/objection correctness, and reference-model integration.
- Keep the change minimal.
- Do not disable or work around the simulator by removing UVM_NO_DPI,
  --timing, watchdogs, or timeout handling.
- Do not merely silence a Verilator warning; fix the generated construct.

Return a concise summary only. Do not paste source code.
""".strip()


def summarize_result_for_llm(result_path: str) -> str:
    data = json.loads(Path(result_path).read_text())
    return json.dumps(data, indent=2)[-MAX_LOG_CHARS:]
