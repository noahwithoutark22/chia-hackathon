"""Metric-driven, RTL-blind improvement loop for generated cocotb+pyuvm TBs.

The simulator may see RTL.  The improvement LLM never does: it operates on a
sanitized workspace containing only the specification, reference model,
verification plan, current TB, and a structured weakness report.
"""
from __future__ import annotations

import ast
import json
import re
import shutil
from pathlib import Path
from typing import Any
import yaml


PROTECTED = {"specification", "reference_model", "verification_plan"}

# Advisory reasoning guidance for the LLM improvement loop. This is deliberately
# not interpreted by this module as a rule engine; the LLM remains responsible
# for engineering judgment.
REASONING_GUIDANCE_FILENAME = "verification_reasoning_guidance.yaml"
IMPROVEMENT_HISTORY_FILENAME = "improvement_history.json"
IMPROVEMENT_DECISION_FILENAME = "improvement_decision.yaml"

ALLOWED_TB_SUFFIXES = {".py", ".yaml", ".yml", ".md", ".json", ".toml", ".ini", ".txt", ".sh"}


def _read(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""


def _all_logs(result: dict[str, Any]) -> str:
    chunks = []
    for t in (result.get("tests") or {}).values():
        chunks.append(str(t.get("log", "")))
    build = result.get("build") or {}
    chunks.append(str(build.get("log", "")))
    return "\n".join(chunks)


def parse_coverage(result: dict[str, Any], tb_dir: Path | None = None) -> dict[str, Any]:
    """Extract aggregate functional coverage from simulator logs.

    Prefer the explicit aggregate ``FUNCTIONAL COVERAGE: X%`` line emitted by
    the generated TB. Individual coverpoint/cross percentages must not be
    mistaken for the overall functional coverage percentage.
    """
    text = _all_logs(result)

    # Preferred format emitted by the generated cocotb-coverage TB:
    #   FUNCTIONAL COVERAGE: 35.71% (15/42 bins)
    aggregate_values = []

    for m in re.finditer(
        r"(?i)\bFUNCTIONAL\s+COVERAGE\s*:\s*(\d+(?:\.\d+)?)\s*%",
        text,
    ):
        try:
            v = float(m.group(1))
            if 0 <= v <= 100:
                aggregate_values.append(v)
        except ValueError:
            pass

    if aggregate_values:
        return {
            "available": True,
            "percentage": max(aggregate_values),
        }

    # Fallback for generated TBs that export an aggregate coverage percentage
    # in YAML. Do not use individual coverpoint percentages.
    if tb_dir and tb_dir.exists():
        for artifact in list(tb_dir.rglob("*.yml")) + list(tb_dir.rglob("*.yaml")):
            if artifact.name == "generation_manifest.yaml":
                continue

            raw = _read(artifact)

            for m in re.finditer(
                r"(?im)^\s*(?:functional_coverage|coverage_percentage|cover_percentage)"
                r"\s*:\s*(\d+(?:\.\d+)?)\s*$",
                raw,
            ):
                try:
                    v = float(m.group(1))
                    if 0 <= v <= 100:
                        return {
                            "available": True,
                            "percentage": v,
                        }
                except ValueError:
                    pass

    return {
        "available": False,
        "percentage": None,
    }


def _scenario_tokens(plan: dict[str, Any]) -> list[str]:
    out = []
    for s in plan.get("directed_test_scenarios", []) or []:
        if isinstance(s, dict):
            name = str(s.get("name", s.get("id", "")))
            if name:
                out.append(name)
    return out


def _normalise(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())



def _extract_scenario_ids(source: str) -> dict[str, str | None]:
    """Return generated test/sequence class -> resolved SCENARIO_ID.

    Resolution is intentionally local to the generated TB and follows simple
    Python inheritance so base-class scenario IDs are counted correctly.
    """
    classes: dict[str, tuple[list[str], str | None]] = {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        scenario_id = None
        for item in node.body:
            if isinstance(item, ast.Assign):
                targets = item.targets
            elif isinstance(item, ast.AnnAssign):
                targets = [item.target]
            else:
                continue
            if any(isinstance(t, ast.Name) and t.id == "SCENARIO_ID" for t in targets):
                if isinstance(item.value, ast.Constant) and item.value.value is not None:
                    scenario_id = str(item.value.value)
        classes[node.name] = (bases, scenario_id)

    resolved: dict[str, str | None] = {}
    visiting: set[str] = set()

    def resolve(name: str) -> str | None:
        if name in resolved:
            return resolved[name]
        if name in visiting:
            return None
        visiting.add(name)
        bases, own = classes.get(name, ([], None))
        value = own
        if value is None:
            for base in bases:
                value = resolve(base)
                if value is not None:
                    break
        visiting.discard(name)
        resolved[name] = value
        return value

    for name in classes:
        resolve(name)
    return resolved


def _result_text(value: Any) -> str:
    """Convert a simulation command/env representation into searchable text."""
    if isinstance(value, dict):
        return " ".join(f"{k}={_result_text(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return " ".join(_result_text(v) for v in value)
    return str(value)


def _parameter_coverage(
    plan: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Measure explicitly exercised parameter values from simulation commands.

    Defaults are deliberately not counted as parameter coverage: a parameter
    value is considered exercised only when the regression evidence explicitly
    supplies that override.
    """
    params = plan.get("parameters") or {}
    if not isinstance(params, dict):
        return {"available": False, "score": 100.0, "planned": {}, "observed": {}}

    planned: dict[str, list[str]] = {}
    for name, definition in params.items():
        if isinstance(definition, dict):
            values = definition.get("test_values", definition.get("values", []))
        else:
            values = definition
        if isinstance(values, (list, tuple)):
            planned[str(name)] = [str(v) for v in values]

    if not planned:
        return {"available": False, "score": 100.0, "planned": {}, "observed": {}}

    observed = {name: set() for name in planned}
    tests = result.get("tests") or {}
    for data in tests.values():
        text = _result_text(data)
        for name, values in planned.items():
            for value in values:
                if re.search(
                    rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*=\s*{re.escape(value)}(?![A-Za-z0-9_])",
                    text,
                ):
                    observed[name].add(value)

    planned_count = sum(len(v) for v in planned.values())
    observed_count = sum(len(observed[k]) for k in planned)
    score = 100.0 * observed_count / planned_count if planned_count else 100.0
    return {
        "available": True,
        "score": score,
        "planned": planned,
        "observed": {k: sorted(v) for k, v in observed.items()},
    }


def _scenario_coverage(
    plan: dict[str, Any],
    source: str,
    result: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Measure planned scenario IDs that are generated and actually executed."""
    planned_ids = []
    planned_names = []
    for item in plan.get("directed_test_scenarios", []) or []:
        if isinstance(item, dict):
            sid = item.get("id")
            name = item.get("name")
            if sid:
                planned_ids.append(str(sid))
            elif name:
                planned_names.append(str(name))

    generated_classes = _extract_scenario_ids(source)
    generated_ids = {sid for sid in generated_classes.values() if sid}

    # Prefer manifest-declared test classes when available; otherwise inspect
    # generated classes directly. This keeps the scorer compatible with older
    # manifests.
    manifest_tests = [str(x) for x in (manifest.get("test_classes") or [])]
    test_classes = set(manifest_tests) if manifest_tests else {
        name for name in generated_classes if re.search(r"Test$", name)
    }

    executed_tests = {str(name) for name, data in (result.get("tests") or {}).items()
                      if data.get("status") == "pass" and data.get("clean_exit")}

    executed_ids = set()
    for cls in test_classes:
        sid = generated_classes.get(cls)
        if sid is None:
            continue
        if any(_normalise(cls) in _normalise(name) or _normalise(name) in _normalise(cls)
               for name in executed_tests):
            executed_ids.add(sid)

    # If the plan has stable IDs, use them as the authoritative scenario unit.
    if planned_ids:
        generated = len(set(planned_ids) & generated_ids)
        executed = len(set(planned_ids) & executed_ids)
        planned_count = len(set(planned_ids))
    else:
        # Legacy plans without IDs retain the old name-based fallback.
        tokens = planned_names
        norm_tests = {_normalise(x) for x in test_classes}
        matched = [s for s in tokens if _normalise(s) and
                   any(_normalise(s) in t or t in _normalise(s) for t in norm_tests)]
        planned_count = len(tokens)
        generated = len(matched)
        executed = sum(
            1 for s in matched
            if any(_normalise(s) in _normalise(name) or _normalise(name) in _normalise(s)
                   for name in executed_tests)
        )

    score = 100.0 * executed / planned_count if planned_count else 100.0
    return {
        "planned": planned_count,
        "generated": generated,
        "executed": executed,
        "score": score,
        "planned_ids": sorted(set(planned_ids)),
        "generated_ids": sorted(generated_ids),
        "executed_ids": sorted(executed_ids),
    }


def analyze_verification_state(
    plan_path: str | Path,
    tb_dir: str | Path,
    result_path: str | Path,
    iteration: int,
    previous_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a deterministic weakness report from plan, TB and results."""
    plan = yaml.safe_load(Path(plan_path).read_text()) or {}
    result = json.loads(Path(result_path).read_text())
    root = Path(tb_dir)
    py_files = sorted(root.glob("*.py"))
    source = "\n".join(_read(p) for p in py_files)
    manifest = {}
    mp = root / "generation_manifest.yaml"
    if mp.exists():
        manifest = yaml.safe_load(mp.read_text()) or {}

    tests = result.get("tests") or {}
    passed = sum(1 for x in tests.values() if x.get("status") == "pass" and x.get("clean_exit"))
    total = len(tests)
    failed = total - passed
    cov = parse_coverage(result, root)

    assertions = len(re.findall(r"(?m)\bassert\s+", source))
    checker_coroutines = len(re.findall(r"async\s+def\s+_check_", source))
    test_classes = len(re.findall(r"class\s+\w*Test\s*\(", source))
    sequences = len(re.findall(r"class\s+\w*Sequence\s*\(", source))
    scenario_metrics = _scenario_coverage(plan, source, result, manifest)
    parameter_metrics = _parameter_coverage(plan, result)

    weaknesses: list[dict[str, Any]] = []
    if failed:
        weaknesses.append({
            "id": "W-TEST-HEALTH",
            "category": "test_health",
            "severity": "high",
            "description": f"{failed} of {total} runnable tests did not complete successfully.",
            "evidence": {"passed": passed, "total": total},
        })
    if checker_coroutines == 0 and assertions == 0:
        weaknesses.append({
            "id": "W-ASSERTIONS",
            "category": "checking",
            "severity": "high",
            "description": "No explicit Python assertion/checker evidence was found in the generated TB.",
        })

    scenarios = _scenario_tokens(plan)
    unmatched = []
    if scenario_metrics["planned"]:
        unmatched = [
            sid for sid in scenario_metrics["planned_ids"]
            if sid not in set(scenario_metrics["executed_ids"])
        ]
    if unmatched:
        weaknesses.append({
            "id": "W-SCENARIO-COVERAGE",
            "category": "stimulus",
            "severity": "medium",
            "description": "Planned scenarios are not all represented by successfully executed generated tests.",
            "scenarios": unmatched,
            "evidence": {
                "planned": scenario_metrics["planned"],
                "generated": scenario_metrics["generated"],
                "executed": scenario_metrics["executed"],
            },
        })

    coverage_plan = plan.get("functional_coverage") or {}
    planned_groups = coverage_plan.get("covergroups", []) if isinstance(coverage_plan, dict) else []
    planned_points = 0
    planned_crosses = 0
    for g in planned_groups or []:
        if isinstance(g, dict):
            planned_points += len(g.get("bins", []) or [])
            planned_crosses += len(g.get("crosses", []) or [])
    coverage_defs = len(re.findall(r"\bCoverPoint\s*\(", source))
    cross_defs = len(re.findall(r"\bCoverCross\s*\(", source))
    if planned_points and coverage_defs < planned_points:
        weaknesses.append({
            "id": "W-COVERAGE-DEFS",
            "category": "coverage",
            "severity": "medium",
            "description": "Generated coverage implementation has fewer CoverPoint definitions than the plan's coverage entries.",
            "evidence": {"planned": planned_points, "generated": coverage_defs},
        })
    if planned_crosses and cross_defs < planned_crosses:
        weaknesses.append({
            "id": "W-CROSS-DEFS",
            "category": "coverage",
            "severity": "medium",
            "description": "Generated coverage implementation has fewer CoverCross definitions than the plan.",
            "evidence": {"planned": planned_crosses, "generated": cross_defs},
        })

    if not cov["available"]:
        weaknesses.append({
            "id": "W-COVERAGE-METRIC",
            "category": "measurement",
            "severity": "medium",
            "description": "No machine-readable functional coverage percentage was observed in simulation output.",
            "action": "Add deterministic coverage export/reporting to the TB without weakening existing checks.",
        })

    test_health = 100.0 * passed / total if total else 0.0
    if cov["available"]:
        coverage_quality = float(cov["percentage"])
    elif planned_points:
        coverage_quality = min(100.0, 100.0 * coverage_defs / planned_points)
    else:
        coverage_quality = 0.0

    planned_assertions = len(plan.get("useful_assertions", []) or [])
    if planned_assertions:
        # Planned assertions are verified structurally by the presence of real
        # Python assertions. Checker coroutines are an additional signal, not a
        # prerequisite, because cocotb+pyUVM TBs may perform checks in tests,
        # scoreboards, monitors, or synchronous helpers.
        assertion_evidence = assertions + checker_coroutines
        assertion_quality = min(100.0, 100.0 * assertion_evidence / planned_assertions)
    else:
        assertion_quality = 100.0 if assertions or checker_coroutines else 0.0

    scenario_quality = float(scenario_metrics["score"])
    parameter_quality = float(parameter_metrics["score"])

    # Deterministic TB-quality score used for candidate acceptance. Keep this
    # compatible with the existing top-level quality_score field, but make the
    # components reflect actual TB evidence. Mutation effectiveness is kept
    # separate and will be added when mutation testing is introduced.
    quality_score = round(
        0.30 * test_health
        + 0.25 * coverage_quality
        + 0.20 * assertion_quality
        + 0.15 * scenario_quality
        + 0.10 * parameter_quality,
        2,
    )

    # Strip implementation-identifying paths from the feedback artifact. The
    # LLM should see verification evidence, not the RTL location or command.
    safe_result = {
        "status": result.get("status"),
        "tests": {
            name: {
                "status": data.get("status"),
                "clean_exit": data.get("clean_exit"),
                "timed_out": data.get("timed_out"),
                "counts": data.get("counts", {}),
                "log": str(data.get("log", ""))[-6000:],
            }
            for name, data in tests.items()
        },
    }

    report = {
        "schema_version": "1.0",
        "iteration": iteration,
        "quality_score": quality_score,
        "metrics": {
            "tests_total": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "functional_coverage": cov,
            "planned_coverage_points": planned_points,
            "generated_coverage_points": coverage_defs,
            "planned_coverage_crosses": planned_crosses,
            "generated_coverage_crosses": cross_defs,
            "python_assertions": assertions,
            "checker_coroutines": checker_coroutines,
            "test_classes": test_classes,
            "sequences": sequences,
            "planned_assertions": planned_assertions,
            "test_health_score": round(test_health, 2),
            "coverage_quality_score": round(coverage_quality, 2),
            "assertion_quality_score": round(assertion_quality, 2),
            "scenario_quality_score": round(scenario_quality, 2),
            "scenario_coverage": scenario_metrics,
            "parameter_coverage": parameter_metrics,
            "tb_quality_score": quality_score,
        },
        "weaknesses": weaknesses,
        "authoritative_inputs": ["specification", "reference_model", "verification_plan"],
        "rtl_exposed_to_llm": False,
        "simulation_evidence": safe_result,
    }
    if previous_report:
        report["comparison"] = {
            "previous_quality_score": previous_report.get("quality_score"),
            "delta": round(quality_score - float(previous_report.get("quality_score", quality_score)), 2),
        }
    return report


def prepare_sanitized_workspace(
    workspace: str | Path,
    spec_path: str | Path,
    ref_model_path: str | Path,
    plan_path: str | Path,
    tb_dir: str | Path,
    weakness_report: dict[str, Any],
    reasoning_guidance_path: str | Path | None = None,
    improvement_history: list[dict[str, Any]] | dict[str, Any] | None = None,
    decision: dict[str, Any] | None = None,
) -> Path:
    """Create the only filesystem tree exposed to the improvement agent.

    The first six positional arguments are intentionally unchanged for
    backwards compatibility with the existing run14.py flow. Optional
    reasoning guidance, experiment history, and a frozen decision are copied
    into the same sanitized workspace when supplied.
    """
    root = Path(workspace).resolve()
    if root.exists():
        shutil.rmtree(root)
    (root / "tb").mkdir(parents=True)
    shutil.copy2(spec_path, root / "specification.md")
    shutil.copy2(ref_model_path, root / "reference_model.py")
    shutil.copy2(plan_path, root / "verification_plan.yaml")
    src_tb = Path(tb_dir)
    for p in src_tb.rglob("*"):
        if not p.is_file() or p.name in {"libchia_ref_model.so"}:
            continue
        rel = p.relative_to(src_tb)
        # Never copy generated build trees, compiled objects, or caches.
        if any(part in {".chia_sim", "__pycache__", ".git"} for part in rel.parts):
            continue
        dest = root / "tb" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)

    (root / "weakness_report.yaml").write_text(
        yaml.safe_dump(weakness_report, sort_keys=False)
    )

    if reasoning_guidance_path:
        guidance = Path(reasoning_guidance_path)
        if guidance.exists():
            shutil.copy2(guidance, root / REASONING_GUIDANCE_FILENAME)

    if improvement_history is not None:
        (root / IMPROVEMENT_HISTORY_FILENAME).write_text(
            json.dumps(improvement_history, indent=2, sort_keys=False)
        )

    if decision is not None:
        (root / IMPROVEMENT_DECISION_FILENAME).write_text(
            yaml.safe_dump(decision, sort_keys=False)
        )

    return root


def collect_tb_changes(sanitized_tb: Path, real_tb: Path) -> list[str]:
    """Apply only TB changes from the sanitized workspace; return changed files."""
    changed = []
    src_files = {p.relative_to(sanitized_tb) for p in sanitized_tb.rglob("*") if p.is_file() and not p.is_symlink()}
    dst_files = {p.relative_to(real_tb) for p in real_tb.rglob("*") if p.is_file() and not p.is_symlink()}
    for rel in sorted(src_files | dst_files):
        if rel.parts[0] in {".chia_sim", "__pycache__", ".git"}:
            continue
        if rel.suffix.lower() not in ALLOWED_TB_SUFFIXES:
            continue
        src = sanitized_tb / rel
        dst = real_tb / rel
        if src.exists():
            before = dst.read_bytes() if dst.exists() else None
            after = src.read_bytes()
            if before != after:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                changed.append(str(rel))
        elif dst.exists():
            dst.unlink()
            changed.append(str(rel))
    return changed


def build_improvement_decision_prompt(workspace: str | Path) -> str:
    """Build the read-only reasoning prompt used before TB modification.

    The prompt intentionally treats guidance as advisory and keeps RTL outside
    the sanitized workspace. It asks for a compact engineering record rather
    than private chain-of-thought.
    """
    root = Path(workspace)
    return f"""
You are the verification reasoning/decision engineer for an iterative
cocotb + pyuvm verification-environment improvement loop.

Your filesystem is intentionally sanitized. You may access ONLY:
- {root}/specification.md
- {root}/reference_model.py
- {root}/verification_plan.yaml
- {root}/weakness_report.yaml
- {root}/verification_reasoning_guidance.yaml (if present)
- {root}/improvement_history.json (if present)
- {root}/tb/

The RTL implementation is NOT available and must remain unknown. Never search
parent directories, request RTL, infer hidden RTL implementation details, or
modify any file.

TASK:
Diagnose the reported verification-environment weakness and decide whether an
improvement experiment is justified. Use the specification, reference model,
verification plan, current TB, weakness report, guidance, and prior experiment
history.

The reasoning guidance is ADVISORY and NON-EXHAUSTIVE. It is a search-space
accelerator, not a rule engine. Do not force a weakness into a guidance
category. You may reject a suggested mechanism, identify a mechanism not listed
there, identify interacting mechanisms, or choose no_change/defer when the
evidence does not justify a safe intervention.

Choose the smallest effective TB-only intervention. Do not modify RTL,
specification, reference model, verification plan, or the frozen verification
contract. Avoid repeating an intervention that history shows to be ineffective
unless you explain why the new evidence justifies trying again.

Return ONLY a concise YAML engineering decision with this shape:
schema_version: "1.0"
decision:
  action: improve | no_change | defer
  weakness_id: "..."
  failure_class: "..."
  failure_mechanism: "..."
  source: guidance_supported | independent_analysis | mixed
  confidence: high | medium | low
diagnosis:
  observed_problem: "..."
  consequence: "..."
candidate_interventions:
  - "..."
selected_intervention:
  type: "..."
  expected_effect:
    - "..."
regression_risks:
  - "..."
validation:
  - "..."

Do not include hidden chain-of-thought or a long narrative.
""".strip()


def _coerce_yaml_mapping(value: Any) -> dict[str, Any]:
    """Return a mapping from an LLM response or parsed object."""
    if isinstance(value, dict):
        return value

    text = str(value or "").strip()
    if not text:
        return {}

    fenced = re.search(
        r"```(?:yaml|yml)?\s*(.*?)```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = yaml.safe_load(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def normalize_improvement_decision(value: Any) -> dict[str, Any]:
    """Normalize an LLM decision safely without inventing engineering facts.

    Invalid or incomplete improvement decisions become ``defer`` rather than
    triggering an unintended TB modification.
    """
    data = _coerce_yaml_mapping(value)
    raw_decision = data.get("decision")
    if not isinstance(raw_decision, dict):
        raw_decision = {}

    action = str(raw_decision.get("action", "defer")).strip().lower()
    if action not in {"improve", "no_change", "defer"}:
        action = "defer"

    source = str(raw_decision.get("source", "independent_analysis")).strip()
    if source not in {"guidance_supported", "independent_analysis", "mixed"}:
        source = "independent_analysis"

    confidence = str(raw_decision.get("confidence", "low")).strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    out = dict(data)
    out["schema_version"] = "1.0"
    out["decision"] = {
        "action": action,
        "weakness_id": str(raw_decision.get("weakness_id", "")),
        "failure_class": str(raw_decision.get("failure_class", "")),
        "failure_mechanism": str(raw_decision.get("failure_mechanism", "")),
        "source": source,
        "confidence": confidence,
    }

    selected = out.get("selected_intervention")
    if action == "improve" and not isinstance(selected, dict):
        out["decision"]["action"] = "defer"
        out["decision"]["confidence"] = "low"

    return out


def save_improvement_decision(
    path: str | Path,
    decision: dict[str, Any] | Any,
) -> dict[str, Any]:
    """Normalize and persist one improvement decision."""
    normalized = normalize_improvement_decision(decision)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(normalized, sort_keys=False))
    return normalized


def load_improvement_history(path: str | Path) -> list[dict[str, Any]]:
    """Load experiment history; malformed/missing history safely becomes []."""
    target = Path(path)
    if not target.exists():
        return []
    try:
        data = json.loads(target.read_text())
    except Exception:
        return []

    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("history"), list):
        return [x for x in data["history"] if isinstance(x, dict)]
    return []


def append_improvement_history(
    path: str | Path,
    entry: dict[str, Any],
) -> list[dict[str, Any]]:
    """Append one experiment result with a temporary-file replace."""
    history = load_improvement_history(path)
    history.append(dict(entry))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(history, indent=2, sort_keys=False))
    tmp.replace(target)
    return history


def build_improvement_prompt(
    workspace: str | Path,
    decision: dict[str, Any] | None = None,
) -> str:
    root = Path(workspace)

    decision_clause = ""
    if decision is not None:
        decision_clause = f"""
A separate reasoning stage has already produced the following FROZEN
engineering decision:

{yaml.safe_dump(normalize_improvement_decision(decision), sort_keys=False)}

Execute the selected intervention in that decision. Do not silently substitute
a different improvement objective. If the selected intervention is impossible
or unsafe after inspecting the TB, make no unrelated changes and explain the
blocker in your final summary.
""".strip()

    return f"""
You are an autonomous verification-environment improvement engineer.

Your filesystem is intentionally sanitized. You may access ONLY:
- {root}/specification.md
- {root}/reference_model.py
- {root}/verification_plan.yaml
- {root}/weakness_report.yaml
- {root}/verification_reasoning_guidance.yaml (if present)
- {root}/improvement_history.json (if present)
- {root}/improvement_decision.yaml (if present)
- {root}/tb/

The RTL implementation is NOT available and must remain unknown. Do not try
path traversal, do not search parent directories, and do not request RTL.
The specification and reference model are authoritative for functionality.
The weakness report is authoritative evidence about the current environment.

TASK:
Improve the EXISTING TB in {root}/tb using the selected engineering decision
when one is supplied. Prefer small, targeted edits over regeneration. Preserve
working tests, checks, coverage and public test names. Do not weaken checks to
improve metrics. Do not modify the specification, reference model, plan, or
verification contract.

The reasoning guidance, if present, is advisory and non-exhaustive. The
improvement history records prior experiments and should be used to avoid
repeating ineffective changes.

{decision_clause}

The resulting TB must remain cocotb + pyuvm and must be runnable by the
existing simulation manifest. If the selected intervention is not actionable
from the supplied evidence, do not invent DUT behavior to address it.

After editing, inspect the changed files for Python syntax, imports, pyuvm
phase correctness, race conditions, and consistency with the contract. Do not
edit outside {root}/tb.

Return a concise summary only. The actual deliverable is the modified files.
""".strip()
