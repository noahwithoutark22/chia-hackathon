#!/usr/bin/env python3
"""Stage-6 INTEGRATION consistency checks for the SHA-256 generated TB.

Runs WITHOUT importing cocotb / pyuvm / cocotb-coverage (they are not
installed in this engineering shell), so every check is static
(``ast``-based, YAML/text-based).  It audits:

  1. generation_manifest.yaml against the worker contract
     (workers/sim/run.py ``validate_manifest`` mirror): required fields,
     resolved paths under /workspace, file/extension rules, non-empty
     test_classes, python_test_module == test_top.
  2. verification_plan.yaml directed scenario ids  <->  sha256_sequences.py
     ``SCENARIO_ID`` attributes  <->  sha256_test.py directed test classes
     (staticmethod ``get_sequence_class``) and the DIRECTED_SCENARIO_TESTS
     registry  <->  manifest ``scenarios``.
  3. corner-case / randomized wiring (no SCENARIO_ID by design; corner
     aggregate drives all six plan corner sequences; randomized budget and
     defaults).
  4. test_top.py entry-point wiring: exactly the two ConfigDB keys
     (CONTRACT.md §5), ``keep_singletons=True`` on ``run_test``,
     ``with_timeout`` outer bound, UVM_TESTNAME selection, sha256_test
     factory import.
  5. tb/Makefile cocotb-flow wiring (SIM/TOPLEVEL/MODULE/VERILOG_SOURCES/
     include Makefile.sim / UVM_TESTNAME default).
  6. Env wiring (agent + scoreboard built, coverage + assertions started,
     scoreboard connected to the monitor analysis port).

Exit code 0 iff all checks pass; a JSON report is written beside the
script.  Usage:

    python3 results/stage6_integration/stage6_consistency_checks.py
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import yaml

WORKSPACE = Path("/workspace").resolve()
TB_DIR = WORKSPACE / "generated" / "designs" / "sha256_benchmark_corrupted"
TB = TB_DIR / "tb"
RESULTS_DIR = Path(__file__).resolve().parent

PLAN = TB_DIR / "verification_plan.yaml"
MANIFEST = TB / "generation_manifest.yaml"
SEQUENCES_PY = TB / "sha256_sequences.py"
TEST_PY = TB / "sha256_test.py"
TEST_TOP_PY = TB / "test_top.py"
ENV_PY = TB / "sha256_env.py"
MAKEFILE = TB / "Makefile"

ERRORS: list[str] = []
CHECKS: list[dict] = []
MANIFEST_SCENARIO_IDS: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    CHECKS.append({"label": label, "ok": bool(ok), "detail": detail})
    if not ok:
        ERRORS.append(f"{label}: {detail}")
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" +
          (f"  --  {detail}" if detail else ""))
    return bool(ok)


def expect(ok: bool, label: str, detail: str = "") -> None:
    check(label, ok, detail)


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def load_ast(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def py_class_names(tree: ast.Module) -> list[str]:
    return [
        node.name for node in tree.body
        if isinstance(node, ast.ClassDef)
    ]


def class_bases(tree: ast.Module, name: str) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return [ast.unparse(b) for b in node.bases]
    return []


def _static_value(node, env: dict) -> object:
    """Evaluate tiny constant expressions (int literals, NAME refs, binops)."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        pass
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if isinstance(node, ast.BinOp):
        left = _static_value(node.left, env)
        right = _static_value(node.right, env)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)) \
                and isinstance(node.op, ast.Mult):
            return left * right
    return None


def class_attr(tree: ast.Module, cls: str, attr: str, env: dict = None):
    """Value of a module-level class attribute (constexpr where possible)."""
    env = env or {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for stmt in node.body:
                if (isinstance(stmt, ast.Assign)
                        and len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Name)
                        and stmt.targets[0].id == attr):
                    return _static_value(stmt.value, env)
    return None


def module_attr(tree: ast.Module, attr: str, env: dict = None):
    """Value of a module-level assignment to ``attr``."""
    env = env or {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == attr):
            return _static_value(node.value, env)
    return None


def instance_attr(tree: ast.Module, cls: str, attr: str):
    """Last ``self.<attr> = <constexpr>`` found in __init__ (or any method)."""
    value = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for stmt in node.body:
                if not isinstance(stmt, ast.FunctionDef):
                    continue
                for s in stmt.body:
                    if (isinstance(s, ast.Assign) and len(s.targets) == 1
                            and isinstance(s.targets[0], ast.Attribute)
                            and isinstance(s.targets[0].value, ast.Name)
                            and s.targets[0].value.id == "self"
                            and s.targets[0].attr == attr):
                        value = _static_value(s.value, {})
    return value


def class_methods(tree: ast.Module, cls: str) -> dict[str, ast.FunctionDef]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {
                stmt.name: stmt for stmt in node.body
                if isinstance(stmt, ast.FunctionDef)
            }
    return {}


def is_staticmethod(fn: ast.FunctionDef) -> bool:
    return any(
        isinstance(d, ast.Name) and d.id == "staticmethod"
        for d in fn.decorator_list
    )


def return_symbol(fn: ast.FunctionDef):
    """Symbol returned by a single-return body (e.g. a class name)."""
    for stmt in fn.body:
        if isinstance(stmt, ast.Return) and stmt.value is not None:
            return ast.unparse(stmt.value)
    return None


# ---------------------------------------------------------------------------
# 1. Manifest / worker contract
# ---------------------------------------------------------------------------
def check_manifest() -> None:
    global MANIFEST_SCENARIO_IDS
    if not MANIFEST.is_file():
        check("manifest exists", False, str(MANIFEST))
        return
    data = yaml.safe_load(MANIFEST.read_text())
    top_module = data.get("top_module")
    top_file = data.get("top_file")
    compile_files = data.get("compile_files")
    test_classes = data.get("test_classes")
    python_test_module = str(data.get("python_test_module", "")).strip()

    check("manifest.top_module == 'sha256'",
          top_module == "sha256", detail=repr(top_module))
    check("manifest.top_file is str", isinstance(top_file, str),
          repr(top_file))
    check("manifest.compile_files non-empty list",
          isinstance(compile_files, list) and len(compile_files) > 0,
          repr(compile_files))
    check("manifest.test_classes non-empty list",
          isinstance(test_classes, list) and len(test_classes) > 0,
          repr(test_classes))
    check("manifest.test_classes == 11 entries",
          isinstance(test_classes, list) and len(test_classes) == 11,
          repr(len(test_classes) if isinstance(test_classes, list) else None))
    check("manifest.python_test_module == 'test_top'",
          python_test_module == "test_top", repr(python_test_module))

    # Worker path rules (resolve under /workspace; allowed HDL suffixes).
    if isinstance(top_file, str):
        p = (WORKSPACE / top_file).resolve()
        ok = (WORKSPACE in p.parents and p.is_file()
              and p.suffix.lower() in {".sv", ".v", ".vh", ".svh"})
        check("manifest top_file resolves in workspace to HDL",
              ok, str(p))
    if isinstance(compile_files, list):
        bad = []
        for item in compile_files:
            p = (WORKSPACE / str(item)).resolve()
            if not (WORKSPACE in p.parents and p.is_file()
                    and p.suffix.lower() in {".sv", ".v", ".vh", ".svh"}):
                bad.append(str(p))
        check("manifest compile_files all resolve in workspace",
              not bad, "; ".join(bad) if bad else f"{len(compile_files)} file(s)")
    if isinstance(test_classes, list):
        expect(all(isinstance(t, str) and t.strip() for t in test_classes),
               "manifest test_classes all non-empty strings",
               repr(test_classes))

    # --- manifest scenarios mapping -----------------------------------
    scenarios = data.get("scenarios", [])
    check("manifest has 'scenarios' mapping",
          isinstance(scenarios, list) and len(scenarios) > 0,
          f"{len(scenarios)} entries")
    if isinstance(scenarios, list):
        ids = [s.get("id") for s in scenarios]
        names = [s.get("name") for s in scenarios]
        check("manifest scenario ids unique", len(set(ids)) == len(ids),
              repr(ids))
        check("manifest scenario id == name", ids == names, "")
        MANIFEST_SCENARIO_IDS = ids


def check_manifest_scenario_names(seq_classes: dict,
                                  registry: dict) -> None:
    """Manifest scenarios reference real sequence + test class names."""
    data = yaml.safe_load(MANIFEST.read_text())
    scenarios = data.get("scenarios", [])
    ids = [s.get("id") for s in scenarios]
    expect(set(ids) == set(MANIFEST_SCENARIO_IDS),
           "manifest 'scenarios' ids == plan directed ids",
           f"missing={set(MANIFEST_SCENARIO_IDS) - set(ids)} "
           f"extra={set(ids) - set(MANIFEST_SCENARIO_IDS)}")
    for s in scenarios:
        sid = s.get("id")
        seq = s.get("sequence")
        test = s.get("test")
        check(f"manifest scenario '{sid}' test '{test}' is the vetted "
              "directed test class",
              registry.get(sid) == test,
              f"registry='{registry.get(sid)}' manifest='{test}'")
        check(f"manifest scenario '{sid}' sequence '{seq}' has that "
              "SCENARIO_ID",
              seq_classes.get(seq) == sid,
              f"seq[SCENARIO_ID]={seq_classes.get(seq)!r}")


# ---------------------------------------------------------------------------
# 2. Plan <-> sequences <-> tests wiring
# ---------------------------------------------------------------------------
def check_plan_wiring() -> None:
    plan = yaml.safe_load(PLAN.read_text())
    directed = plan.get("directed_test_scenarios", [])
    plan_ids = [str(d.get("name")) for d in directed]
    corner = plan.get("corner_cases", [])
    randomized = plan.get("randomized_testing_strategy", {})
    check("plan has 9 directed ids", len(plan_ids) == 9, repr(plan_ids))
    check("plan has 6 corner cases", isinstance(corner, list)
          and len(corner) == 6,
          str(len(corner) if isinstance(corner, list) else corner))
    check("plan has randomized_testing_strategy mapping",
          isinstance(randomized, dict) and len(randomized) > 0,
          repr(list(randomized.keys())))

    seq_tree = load_ast(SEQUENCES_PY)
    seq_classes = {}
    for name in py_class_names(seq_tree):
        bases = class_bases(seq_tree, name)
        if "Sha256StimulusBase" in bases:
            seq_classes[name] = class_attr(seq_tree, name, "SCENARIO_ID")

    expect(len(seq_classes) == 16,
           "sequences: exactly 16 Sha256StimulusBase subclasses",
           str(len(seq_classes)))
    id_to_seq = {sid: [] for sid in plan_ids}
    extra_with_id = []
    for name, sid in seq_classes.items():
        if sid is not None:
            if sid in id_to_seq:
                id_to_seq[sid].append(name)
            else:
                extra_with_id.append((name, sid))
    check("each directed plan id has exactly one sequence class",
          all(len(v) == 1 for v in id_to_seq.values()),
          repr({k: v for k, v in id_to_seq.items() if len(v) != 1}))
    check("no sequence class carries a non-plan SCENARIO_ID",
          not extra_with_id, repr(extra_with_id))

    corner_seqs = {n for n, s in seq_classes.items() if s is None
                   and n != "Sha256RandomizedSequence"}
    expect(len(corner_seqs) == 6,
           "six corner sequences exist (no SCENARIO_ID by design)",
           ", ".join(sorted(corner_seqs)))
    check("Sha256RandomizedSequence has no SCENARIO_ID",
          seq_classes.get("Sha256RandomizedSequence") is None, "")

    # ------------------------------------------------------------------
    # sha256_test.py wiring
    # ------------------------------------------------------------------
    test_tree = load_ast(TEST_PY)
    test_classes_all = py_class_names(test_tree)
    uvm_tests = [
        n for n in test_classes_all
        if "uvm_test" in class_bases(test_tree, n)
        or "Sha256BaseTest" in class_bases(test_tree, n)
    ]
    runnable = {n for n in uvm_tests if n != "Sha256BaseTest"}
    expect(len(runnable) == 11,
           "sha256_test defines 11 runnable uvm_test subclasses",
           repr(sorted(runnable)))

    manifest = yaml.safe_load(MANIFEST.read_text())
    manifest_tests = manifest.get("test_classes", [])
    check("manifest.test_classes == uvm_test subclasses in sha256_test",
          set(manifest_tests) == runnable,
          f"manifest-only={set(manifest_tests) - runnable} "
          f"py-only={runnable - set(manifest_tests)}")

    # Registry keys == plan ids; values are directed TEST classes.
    registry = {}
    for node in test_tree.body:
        if isinstance(node, ast.Assign) and node.targets \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "DIRECTED_SCENARIO_TESTS":
            if isinstance(node.value, ast.Dict):
                for k, v in zip(node.value.keys, node.value.values):
                    if isinstance(k, ast.Constant):
                        registry[str(k.value)] = ast.unparse(v)
    check("DIRECTED_SCENARIO_TESTS keys == plan directed ids",
          set(registry) == set(plan_ids),
          f"missing={set(plan_ids) - set(registry)} "
          f"extra={set(registry) - set(plan_ids)}")
    check("DIRECTED_SCENARIO_TESTS values are directed test classes (not "
          "strings)",
          all(v in runnable for v in registry.values()),
          repr(registry))

    # Each directed test: staticmethod get_sequence_class returning the
    # class symbol for the SAME plan id it is registered under.
    for sid in plan_ids:
        test_cls = registry.get(sid)
        expect(test_cls in runnable,
               f"scenario '{sid}' registry test class exists",
               f"registry='{test_cls}'")
        methods = class_methods(test_tree, test_cls)
        gsc = methods.get("get_sequence_class")
        expect(gsc is not None and is_staticmethod(gsc),
               f"{test_cls}.get_sequence_class is a staticmethod",
               "missing or not staticmethod")
        if gsc is None:
            continue
        ret = return_symbol(gsc)
        # Must return a class SYMBOL, not a string literal.
        if ret is not None and ret.startswith("'"):
            check(f"{test_cls}.get_sequence_class() returns a CLASS symbol",
                  False, f"string literal {ret}")
            continue
        sid_of_seq = seq_classes.get(ret)
        check(f"{test_cls}.get_sequence_class() -> '{ret}' has SCENARIO_ID "
              f"'{sid}'", sid_of_seq == sid,
              f"seq[SCENARIO_ID]={sid_of_seq!r}")
        seq_name = test_cls.removesuffix("Test") + "Sequence"
        if seq_name in seq_classes:
            check(f"class-name parity {seq_name} <-> {test_cls}", True,
                  seq_name)

    # Corner aggregate test drives all six corner sequences.
    corner_test = "Sha256CornerTest"
    expect(corner_test in runnable, f"{corner_test} is a uvm_test subclass",
           "")
    allow = instance_attr(test_tree, corner_test, "_allow_invalid_blocks")
    check(f"{corner_test}.__init__ sets _allow_invalid_blocks True",
          allow is True, repr(allow))
    tuple_names = []
    for node in test_tree.body:
        if isinstance(node, ast.Assign) and node.targets \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "SHA256_CORNER_SEQUENCES" \
                and isinstance(node.value, ast.Tuple):
            tuple_names = [ast.unparse(e) for e in node.value.elts]
    expect(len(tuple_names) == 6,
           "SHA256_CORNER_SEQUENCES holds the 6 corner classes",
           repr(tuple_names))
    corner_plan_names = {"Sha256MaximumMessageLengthSequence",
                         "Sha256StartDeassertedSameCycleSequence",
                         "Sha256BlockAllOnesSequence",
                         "Sha256BlockAlternatingPatternSequence",
                         "Sha256ResetDuringProcessingSequence",
                         "Sha256BlockChangesDuringProcessingSequence"}
    check("SHA256_CORNER_SEQUENCES == plan corner sequence set",
          set(tuple_names) == corner_plan_names,
          f"missing={corner_plan_names - set(tuple_names)} "
          f"extra={set(tuple_names) - corner_plan_names}")
    for n in tuple_names:
        expect(n in seq_classes and seq_classes[n] is None,
               f"corner class {n} carries no SCORENARIO_ID",
               repr(seq_classes.get(n)))
    budget = class_attr(test_tree, corner_test, "WATCHDOG_BUDGET_CYCLES",
                        env={"WATCHDOG_MARGIN_CYCLES": 500})
    check(f"{corner_test} watchdog budget == 2 x margin (1000)",
          budget == 1000, repr(budget))

    # Randomized test.
    rand_test = "Sha256RandomizedTest"
    expect(rand_test in runnable, f"{rand_test} is a uvm_test subclass", "")
    rbudget = class_attr(test_tree, rand_test, "WATCHDOG_BUDGET_CYCLES",
                         env={"WATCHDOG_MARGIN_CYCLES": 500})
    check(f"{rand_test} watchdog budget == 8 x margin (4000)",
          rbudget == 4000, repr(rbudget))
    rallow = instance_attr(test_tree, rand_test, "_allow_invalid_blocks")
    check(f"{rand_test} does not enable invalid blocks",
          rallow is not True, repr(rallow))
    n_txn = module_attr(test_tree, "DEFAULT_RANDOM_TRANSACTIONS")
    seed = module_attr(test_tree, "DEFAULT_RANDOM_SEED")
    check("DEFAULT_RANDOM_TRANSACTIONS == 20 (plan)",
          n_txn == 20, repr(n_txn))
    check("DEFAULT_RANDOM_SEED is deterministic int",
          isinstance(seed, int) and 0 < seed < 2**31, repr(seed))

    # Reset-only test semantics.
    reset_test = "Sha256ResetInitializationTest"
    rq = instance_attr(test_tree, reset_test,
                       "_require_graded_transactions")
    check("ResetInitializationTest._require_graded_transactions is False",
          rq is False, repr(rq))
    check("Sha256ResetInitializationSequence.SCENARIO_ID == "
          "'reset_initialization'",
          seq_classes.get("Sha256ResetInitializationSequence")
          == "reset_initialization",
          repr(seq_classes.get("Sha256ResetInitializationSequence")))

    check_manifest_scenario_names(seq_classes, registry)


# ---------------------------------------------------------------------------
# 3. test_top.py wiring
# ---------------------------------------------------------------------------
def check_test_top() -> None:
    check("test_top.py exists at exact worker path", TEST_TOP_PY.is_file(),
          str(TEST_TOP_PY))
    tree = load_ast(TEST_TOP_PY)

    # ConfigDB keys: exactly dut + sha256_pins as Constant args.
    set_calls = []
    keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "set" \
                and "ConfigDB" in ast.unparse(node.func.value):
            args = [ast.unparse(a) for a in node.args] + \
                   [f"{k.arg}={ast.unparse(k.value)}" for k in node.keywords]
            set_calls.append("ConfigDB().set(" + ", ".join(args) + ")")
            if len(node.args) >= 3 and isinstance(node.args[2], ast.Constant):
                keys.add(str(node.args[2].value))
    check("ConfigDB keys are exactly {'dut','sha256_pins'} (CONTRACT.md §5)",
          keys == {"dut", "sha256_pins"}, repr(sorted(keys)))
    expect(len(set_calls) == 2,
           "ConfigDB().set called exactly twice (dut, sha256_pins)",
           "; ".join(set_calls))

    # run_test keep_singletons=True.
    run_tests = []
    keep = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "run_test":
            run_tests.append(ast.unparse(node))
            for k in node.keywords:
                if k.arg == "keep_singletons" and isinstance(k.value,
                                                             ast.Constant):
                    keep = bool(k.value.value)
    expect(len(run_tests) == 1, "uvm_root().run_test called exactly once",
           "; ".join(run_tests))
    check("run_test(..., keep_singletons=True)", keep is True,
          f"keep_singletons={keep}")

    # with_timeout wrapping run_test (coro, budget, "ns") 3-arg form.
    timeout_wraps = []
    third_arg_ns = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "with_timeout":
            timeout_wraps.append(ast.unparse(node))
            if len(node.args) >= 3:
                third_arg_ns = (isinstance(node.args[2], ast.Constant)
                                and node.args[2].value == "ns")
    expect(bool(timeout_wraps), "with_timeout present (outer sim-time bound)",
           "; ".join(timeout_wraps))
    check("with_timeout(..., budget, 'ns')", third_arg_ns,
          "time unit literal must be 'ns'")

    src = TEST_TOP_PY.read_text()
    default = re.search(r"DEFAULT_TEST\s*=\s*[\"']([\w]+)[\"']", src)
    check("DEFAULT_TEST fallback == Sha256ResetInitializationTest",
          bool(default) and default.group(1) == "Sha256ResetInitializationTest",
          default.group(1) if default else "missing")
    check("test_top reads UVM_TESTNAME env var", "UVM_TESTNAME" in src, "")
    check("test_top imports sha256_test (factory registration)",
          "import sha256_test" in src, "")
    check("test_top drives reset via Sha256Pins", "drive_reset" in src, "")
    check("test_top starts make_clock clock",
          "make_clock" in src and "clock.start" in src, "")
    check("test_top reports coverage", "report_coverage" in src, "")
    check("test_top catches SimTimeoutError", "SimTimeoutError" in src, "")


# ---------------------------------------------------------------------------
# 4. Makefile
# ---------------------------------------------------------------------------
def check_makefile() -> None:
    check("tb/Makefile exists", MAKEFILE.is_file(), str(MAKEFILE))
    if not MAKEFILE.is_file():
        return
    text = MAKEFILE.read_text()

    def line_has(pat): return bool(
        re.search(rf"^\s*{pat}\s*$", text, re.MULTILINE))
    check("Makefile SIM = verilator", line_has(r"SIM\s*=\s*verilator"), "")
    check("Makefile TOPLEVEL = sha256", line_has(r"TOPLEVEL\s*=\s*sha256"), "")
    check("Makefile MODULE = test_top", line_has(r"MODULE\s*=\s*test_top"), "")
    check("Makefile VERILOG_SOURCES -> sha256.sv (read-only DUT)",
          re.search(r"VERILOG_SOURCES\s*=\s*.+sha256\.sv", text) is not None, "")
    check("Makefile includes cocotb Makefile.sim",
          "include $(shell cocotb-config --makefiles)/Makefile.sim" in text, "")
    check("Makefile UVM_TESTNAME default settable",
          re.search(r"UVM_TESTNAME\s*\?=\s*Sha256ResetInitializationTest",
                    text) is not None, "")
    check("Makefile COMPILE_ARGS include --timing", "--timing" in text, "")


# ---------------------------------------------------------------------------
# 5. Env wiring
# ---------------------------------------------------------------------------
def check_env() -> None:
    check("tb/sha256_env.py exists", ENV_PY.is_file(), str(ENV_PY))
    tree = load_ast(ENV_PY)
    methods = class_methods(tree, "Sha256Env")
    build = methods.get("build_phase")
    connect = methods.get("connect_phase")
    expect(build is not None, "Sha256Env.build_phase exists", "")
    expect(connect is not None, "Sha256Env.connect_phase exists", "")

    build_src = ast.unparse(build) if build else ""
    connect_src = ast.unparse(connect) if connect else ""
    check("build_phase instantiates agent + scoreboard",
          "Sha256Agent(" in build_src and "Sha256Scoreboard(" in build_src, "")
    check("build_phase starts coverage + assertions",
          "start_coverage()" in build_src and "start_assertions()" in build_src,
          "")
    check("connect_phase wires scoreboard.connect_monitor(agent.ap)",
          "connect_monitor" in connect_src and "agent.ap" in connect_src, "")


def main() -> int:
    if not TB_DIR.is_dir():
        print(f"TB dir not found: {TB_DIR}", file=sys.stderr)
        return 2
    check_manifest()
    check_plan_wiring()
    check_test_top()
    check_makefile()
    check_env()

    summary = {
        "schema_version": "1.0",
        "status": "pass" if not ERRORS else "fail",
        "total_checks": len(CHECKS),
        "passed": sum(1 for c in CHECKS if c["ok"]),
        "failed": len(ERRORS),
        "errors": ERRORS,
        "tb_dir": str(TB_DIR),
        "checks": CHECKS,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = RESULTS_DIR / "stage6_consistency_report.json"
    report.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\n{'ALL CHECKS PASSED' if not ERRORS else 'CHECKS FAILED'}: "
          f"{summary['passed']}/{summary['total_checks']} -> {report}")
    return 0 if not ERRORS else 1


if __name__ == "__main__":
    raise SystemExit(main())