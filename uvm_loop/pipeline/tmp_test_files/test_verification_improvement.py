import json
from pathlib import Path
import yaml

from pipeline.verification_improvement import analyze_verification_state, prepare_sanitized_workspace


def test_analyzer_reports_failed_tests_and_missing_coverage(tmp_path):
    plan = {
        "directed_test_scenarios": [{"name": "reset_clear"}, {"name": "backpressure"}],
        "functional_coverage": {"covergroups": [{"name": "g", "bins": [{"name": "a"}], "crosses": []}]},
    }
    (tmp_path / "plan.yaml").write_text(yaml.safe_dump(plan))
    tb = tmp_path / "tb"
    tb.mkdir()
    (tb / "generation_manifest.yaml").write_text(yaml.safe_dump({"test_classes": ["ResetClearTest"]}))
    (tb / "test.py").write_text("class ResetClearTest: pass\n")
    result = {"tests": {"ResetClearTest": {"status": "pass", "clean_exit": True, "log": ""}, "Other": {"status": "hang", "clean_exit": False, "log": ""}}}
    (tmp_path / "result.json").write_text(json.dumps(result))
    report = analyze_verification_state(tmp_path / "plan.yaml", tb, tmp_path / "result.json", 0)
    ids = {w["id"] for w in report["weaknesses"]}
    assert "W-TEST-HEALTH" in ids
    assert "W-COVERAGE-METRIC" in ids
    assert report["rtl_exposed_to_llm"] is False


def test_sanitized_workspace_contains_no_rtl(tmp_path):
    spec = tmp_path / "spec.md"; spec.write_text("spec")
    ref = tmp_path / "ref.py"; ref.write_text("def ref(): pass")
    plan = tmp_path / "plan.yaml"; plan.write_text("dut: x")
    tb = tmp_path / "tb"; tb.mkdir(); (tb / "test.py").write_text("pass")
    report = {"weaknesses": [], "rtl_exposed_to_llm": False}
    root = prepare_sanitized_workspace(tmp_path / "agent", spec, ref, plan, tb, report)
    files = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    assert all("rtl" not in p.lower() for p in files)
    assert "tb/test.py" in files
