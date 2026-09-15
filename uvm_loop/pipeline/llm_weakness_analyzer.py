"""LLM-based analysis of verification weaknesses.

The analyzer sees simulation evidence, specification, reference model,
verification plan, and generated TB. It never receives RTL.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from chia.base.ChiaFunction import get
from chia.base.tools.BashTool import BashTool
from chia.models.opencode import OpenCodeLLM


def prepare_analysis_workspace(
    workspace: str | Path,
    spec_path: str | Path,
    ref_model_path: str | Path,
    plan_path: str | Path,
    tb_dir: str | Path,
    result_path: str | Path,
) -> Path:
    """Create an RTL-free workspace for the verification-analysis LLM."""

    root = Path(workspace).resolve()

    if root.exists():
        shutil.rmtree(root)

    (root / "tb").mkdir(parents=True)

    shutil.copy2(spec_path, root / "specification.md")
    shutil.copy2(ref_model_path, root / "reference_model.py")
    shutil.copy2(plan_path, root / "verification_plan.yaml")
    shutil.copy2(result_path, root / "simulation_result.json")

    src_tb = Path(tb_dir)

    for p in src_tb.rglob("*"):
        if not p.is_file():
            continue

        if p.name in {"libchia_ref_model.so"}:
            continue

        rel = p.relative_to(src_tb)

        if any(
            part in {".chia_sim", "__pycache__", ".git"}
            for part in rel.parts
        ):
            continue

        dest = root / "tb" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)

    return root


def build_analysis_prompt(workspace: str | Path) -> str:
    root = Path(workspace)

    return f"""
You are the Verification Analysis LLM for an LLM-driven cocotb + pyuvm
verification environment.

Your job is to analyze the current verification campaign and produce a
compact, actionable weakness report for a SECOND LLM that will modify the
existing verification environment.

IMPORTANT INFORMATION BOUNDARY:

The RTL implementation is intentionally unavailable.

You MUST NOT:
- search for RTL;
- inspect parent directories;
- request RTL;
- infer hidden RTL implementation details;
- modify the generated testbench;
- modify the specification;
- modify the reference model;
- modify the verification plan.

You MAY inspect only:

- {root}/specification.md
- {root}/reference_model.py
- {root}/verification_plan.yaml
- {root}/simulation_result.json
- {root}/tb/

The simulation_result.json contains the complete simulation/build/test logs.
Use those logs as the primary evidence for diagnosing failures.

The specification and reference model define expected behavior.
The verification plan defines intended verification scenarios.
The generated TB shows how those intentions are currently implemented.

TASK:

Analyze the complete simulation result and determine the most important
verification-environment weaknesses.

Distinguish carefully between:

1. DUT behavior failures evidenced by the test results.
2. Testbench synchronization/timing/alignment problems.
3. Driver/monitor transaction association problems.
4. Scoreboard/reference-model integration problems.
5. Missing or ineffective checking.
6. Missing stimulus/scenario coverage.
7. Missing functional coverage.
8. Test infrastructure/runtime failures.
9. Ambiguous evidence where root cause cannot confidently be determined.

Do NOT assume a root cause merely because a test failed.

For every weakness:
- cite concrete evidence from simulation_result.json;
- identify affected tests;
- identify likely TB files to inspect;
- state the hypothesis separately from the evidence;
- provide confidence;
- explain what the improvement LLM should investigate.

If the evidence is insufficient, explicitly say so.

DO NOT output raw simulation logs into the weakness report.

Write the final report to:

{root}/weakness_report.yaml

Use EXACTLY this structure:

schema_version: "2.0"

summary:
  overall_status: pass | functional_failure | infrastructure_failure | inconclusive
  tests_total: <integer>
  tests_passed: <integer>
  tests_failed: <integer>
  highest_severity: none | low | medium | high | critical

weaknesses:
  - id: W-LLM-001
    severity: low | medium | high | critical
    category: test_health | temporal_alignment | stimulus | checking | coverage | scoreboard | infrastructure | other
    title: "<short title>"
    affected_tests:
      - "<test name>"
    evidence:
      - "<specific observation from simulation evidence>"
    likely_cause: "<hypothesis, not claimed fact>"
    investigation_targets:
      - "<generated TB file>"
    recommended_action: "<what the improvement LLM should investigate/change>"
    confidence: low | medium | high

constraints:
  rtl_exposed_to_llm: false
  diagnosis_must_be_rtl_independent: true

authoritative_inputs:
  - specification
  - reference_model
  - verification_plan
  - simulation_result

IMPORTANT:
- Do not include metrics that are not supported by simulation_result.json.
- Do not invent failures.
- Do not include generic advice unrelated to observed evidence.
- Prefer a small number of high-value weaknesses over many superficial ones.
- If several failing tests exhibit the same underlying pattern, report ONE
  consolidated weakness rather than repeating it for every test.

After writing the file, verify that it is valid YAML and follows the exact
schema above.

Do not modify any other file.

Return only a short confirmation.
""".strip()


def validate_weakness_report(report: dict[str, Any]) -> None:
    """Strict validation of the LLM-produced weakness report."""

    required = {
        "schema_version",
        "summary",
        "weaknesses",
        "constraints",
        "authoritative_inputs",
    }

    missing = required - set(report)
    if missing:
        raise RuntimeError(
            f"LLM weakness report missing fields: {sorted(missing)}"
        )

    if report["schema_version"] != "2.0":
        raise RuntimeError(
            f"Unsupported weakness report schema: "
            f"{report['schema_version']!r}"
        )

    summary = report["summary"]

    for field in (
        "overall_status",
        "tests_total",
        "tests_passed",
        "tests_failed",
        "highest_severity",
    ):
        if field not in summary:
            raise RuntimeError(
                f"LLM weakness report summary missing {field!r}"
            )

    if not isinstance(report["weaknesses"], list):
        raise RuntimeError("LLM weakness report 'weaknesses' must be a list.")

    weakness_fields = {
        "id",
        "severity",
        "category",
        "title",
        "affected_tests",
        "evidence",
        "likely_cause",
        "investigation_targets",
        "recommended_action",
        "confidence",
    }

    for weakness in report["weaknesses"]:
        missing = weakness_fields - set(weakness)

        if missing:
            raise RuntimeError(
                f"Weakness {weakness.get('id', '<unknown>')} "
                f"missing fields: {sorted(missing)}"
            )

        if not isinstance(weakness["evidence"], list):
            raise RuntimeError(
                f"Weakness {weakness['id']} evidence must be a list."
            )

        if not isinstance(weakness["investigation_targets"], list):
            raise RuntimeError(
                f"Weakness {weakness['id']} investigation_targets "
                "must be a list."
            )

    constraints = report["constraints"]

    if constraints.get("rtl_exposed_to_llm") is not False:
        raise RuntimeError(
            "Invalid weakness report: RTL exposure must be false."
        )


def generate_llm_weakness_report(
    workspace: str | Path,
    spec_path: str | Path,
    ref_model_path: str | Path,
    plan_path: str | Path,
    tb_dir: str | Path,
    result_path: str | Path,
) -> dict[str, Any]:
    """Run the RTL-blind analysis LLM and return its structured report."""

    root = Path(workspace).resolve()

    prepare_analysis_workspace(
        root,
        spec_path,
        ref_model_path,
        plan_path,
        tb_dir,
        result_path,
    )

    bash = BashTool(
        "verification_analysis_workspace",
        work_dir=str(root),
        timeout_seconds=1200,
        task_options={"resources": {"opencode_tools": 1}},
    )

    llm = OpenCodeLLM(
        model="opencode/big-pickle",
        work_dir=str(root),
        timeout_seconds=1200,
        retries=1,
    )

    try:
        response = get(
            llm.prompt.chia_remote(
                llm,
                build_analysis_prompt(root),
                tools=[bash],
            )
        )

        if not response.success:
            raise RuntimeError(
                "Verification analysis LLM failed:\n"
                f"{response.stderr}"
            )

        report_path = root / "weakness_report.yaml"

        if not report_path.exists():
            raise RuntimeError(
                "Verification analysis LLM completed without creating "
                f"{report_path}"
            )

        try:
            report = yaml.safe_load(
                report_path.read_text()
            )
        except yaml.YAMLError as exc:
            raise RuntimeError(
                f"LLM weakness report is invalid YAML: {exc}"
            ) from exc

        if not isinstance(report, dict):
            raise RuntimeError(
                "LLM weakness report must contain a YAML mapping."
            )

        validate_weakness_report(report)

        return report

    finally:
        bash.stop()