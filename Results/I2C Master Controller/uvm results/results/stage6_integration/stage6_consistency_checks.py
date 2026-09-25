#!/usr/bin/env python3
"""Stage-6 INTEGRATION consistency checks for the i2c_master generated TB.

Runs WITHOUT importing cocotb / pyuvm / cocotb-coverage (they are not
installed in this engineering shell), so every check is static
(``ast``-based, YAML/text-based).  It audits:

  1. generation_manifest.yaml against the worker contract
     (workers/sim/run.py ``validate_manifest`` mirror): required fields,
     resolved paths under /workspace, file/extension rules, non-empty
     test_classes, python_test_module == test_top.
  2. verification_plan.yaml directed scenario ids (TC-01..TC-13)
     <->  i2c_sequences.py ``SCENARIO_ID`` attributes  <->  i2c_test.py
     directed test classes (staticmethod ``get_sequence_class``) and the
     DIRECTED_SCENARIO_TESTS registry  <->  manifest ``scenarios``.
  3. corner-case / randomized wiring (no SCENARIO_ID by design; corner
     aggregate drives all 14 plan corner sequences; randomized budget and
     deterministic seed/item defaults).
  4. test_top.py entry-point wiring: exactly the two ConfigDB keys
     (CONTRACT.md §6), ``keep_singletons=True`` on ``run_test``,
     ``with_timeout`` outer sim-time bound, UVM_TESTNAME selection,
     i2c_test factory import.
  5. tb/Makefile cocotb-flow wiring (SIM/TOPLEVEL/MODULE/VERILOG_SOURCES/
     include Makefile.sim / UVM_TESTNAME default).
  6. Env wiring (agent + scoreboard + coverage built, assertion checkers
     launched, driver ConfigDB key + monitor analysis ports connected in
     connect_phase, watchdog primitives).

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
TB_DIR = WORKSPACE / "generated" / "designs" / "i2c_benchmark_corrupted"
TB = TB_DIR / "tb"
RESULTS_DIR = Path(__file__).resolve().parent

PLAN = TB_DIR / "plans" / "verification_plan.yaml"
MANIFEST = TB / "generation_manifest.yaml"
SEQUENCES_PY = TB / "i2c_sequences.py"
TEST_PY = TB / "i2c_test.py"
TEST_TOP_PY = TB / "test_top.py"
ENV_PY = TB / "i2c_env.py"
MAKEFILE = TB / "Makefile"

#: Env module constant (CONTRACT.md §17); used to resolve the tests'
#: `WATCHDOG_BUDGET_CYCLES = <k> * WATCHDOG_MARGIN_CYCLES` constexprs.
WATCHDOG_MARGIN_CYCLES = 10000

#: Expected plan directed ids and derived counts (CONTRACT.md §10).
PLAN_DIRECTED_IDS = [f"TC-{i:02d}" for i in range(1, 14)]  # TC-01..TC-13
N_RUNNABLE_TESTS = 15            # 13 directed + I2CCornerTest + I2CRandomTest
N_CORNER_SEQUENCES = 14

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


def module_tuple_names(tree: ast.Module, name: str) -> list[str]:
    """Element names of a module-level tuple assigned to ``name``."""
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == name
                and isinstance(node.value, ast.Tuple)):
            return [ast.unparse(e) for e in node.value.elts]
    return []


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

    check("manifest.top_module == 'i2c_master'",
          top_module == "i2c_master", detail=repr(top_module))
    check("manifest.top_file is str", isinstance(top_file, str),
          repr(top_file))
    check("manifest.compile_files non-empty list",
          isinstance(compile_files, list) and len(compile_files) > 0,
          repr(compile_files))
    check("manifest.test_classes non-empty list",
          isinstance(test_classes, list) and len(test_classes) > 0,
          repr(test_classes))
    check(f"manifest.test_classes == {N_RUNNABLE_TESTS} entries",
          isinstance(test_classes, list)
          and len(test_classes) == N_RUNNABLE_TESTS,
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
        check("manifest scenario ids are TC-01..TC-13",
              ids == PLAN_DIRECTED_IDS, repr(ids))
        check("manifest scenario names non-empty (plan snake_case)",
              all(isinstance(n, str) and n for n in names), repr(names))
        # Every manifest id/name pair must match the plan directed entry.
        plan = yaml.safe_load(PLAN.read_text())
        plan_by_id = {
            str(d.get("id")): str(d.get("name"))
            for d in plan.get("directed_test_scenarios", [])
        }
        mismatch = [
            f"{i}:{n}" for i, n in zip(ids, names)
            if plan_by_id.get(i) != n
        ]
        check("manifest id/name pairs match the plan directed scenarios",
              not mismatch, "; ".join(mismatch) if mismatch else repr(ids))
        MANIFEST_SCENARIO_IDS = ids


# ---------------------------------------------------------------------------
# 2. Plan <-> sequences <-> tests wiring
# ---------------------------------------------------------------------------
def check_plan_wiring() -> None:
    plan = yaml.safe_load(PLAN.read_text())
    directed = plan.get("directed_test_scenarios", [])
    plan_ids = [str(d.get("id")) for d in directed]
    corner = plan.get("corner_cases", [])
    randomized = plan.get("randomized_testing_strategy", {})
    check(f"plan directed ids == {PLAN_DIRECTED_IDS}",
          plan_ids == PLAN_DIRECTED_IDS, repr(plan_ids))
    check(f"plan has {N_CORNER_SEQUENCES} corner cases", isinstance(corner, list)
          and len(corner) == N_CORNER_SEQUENCES,
          str(len(corner) if isinstance(corner, list) else corner))
    check("plan has randomized_testing_strategy mapping",
          isinstance(randomized, dict) and len(randomized) > 0,
          repr(list(randomized.keys())))

    seq_tree = load_ast(SEQUENCES_PY)
    seq_classes = {}
    for name in py_class_names(seq_tree):
        bases = class_bases(seq_tree, name)
        if "I2CSequenceBase" in bases:
            seq_classes[name] = class_attr(seq_tree, name, "SCENARIO_ID")

    expect(len(seq_classes) == 28,
           "sequences: exactly 28 I2CSequenceBase subclasses "
           "(13 directed + 14 corner + 1 randomized)",
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
                   and n != "I2CRandomSequence"}
    expect(len(corner_seqs) == N_CORNER_SEQUENCES,
           f"{N_CORNER_SEQUENCES} corner sequences exist "
           "(no SCENARIO_ID by design)",
           ", ".join(sorted(corner_seqs)))
    check("I2CRandomSequence has no SCENARIO_ID",
          seq_classes.get("I2CRandomSequence") is None, "")

    # ------------------------------------------------------------------
    # i2c_test.py wiring
    # ------------------------------------------------------------------
    test_tree = load_ast(TEST_PY)
    test_classes_all = py_class_names(test_tree)
    uvm_tests = [
        n for n in test_classes_all
        if "uvm_test" in class_bases(test_tree, n)
        or "I2CBaseTest" in class_bases(test_tree, n)
    ]
    runnable = {n for n in uvm_tests if n != "I2CBaseTest"}
    expect(len(runnable) == N_RUNNABLE_TESTS,
           f"i2c_test defines {N_RUNNABLE_TESTS} runnable uvm_test subclasses",
           repr(sorted(runnable)))

    manifest = yaml.safe_load(MANIFEST.read_text())
    manifest_tests = manifest.get("test_classes", [])
    check("manifest.test_classes == uvm_test subclasses in i2c_test",
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

    # Corner aggregate test drives all 14 corner sequences.
    corner_test = "I2CCornerTest"
    expect(corner_test in runnable, f"{corner_test} is a uvm_test subclass",
           "")
    tuple_names = module_tuple_names(test_tree, "I2C_CORNER_SEQUENCES")
    expect(len(tuple_names) == N_CORNER_SEQUENCES,
           f"I2C_CORNER_SEQUENCES holds the {N_CORNER_SEQUENCES} corner "
           "classes", repr(tuple_names))
    corner_plan_names = {
        "CornerAddrZeroWrite", "CornerAddrMaxWrite", "CornerAddrMaxRead",
        "CornerDataZeroWrite", "CornerDataMaxWrite", "CornerRxAllOnesRead",
        "CornerRxAllZerosRead", "CornerMissingAddrAck", "CornerMissingDataAck",
        "CornerStartOneCycle", "CornerBackToBackTransactions",
        "CornerResetMidTransaction", "CornerClkDivMin",
        "CornerReleasedBusNoAck",
    }
    check("I2C_CORNER_SEQUENCES == plan corner sequence set",
          set(tuple_names) == corner_plan_names,
          f"missing={corner_plan_names - set(tuple_names)} "
          f"extra={set(tuple_names) - corner_plan_names}")
    for n in tuple_names:
        expect(n in seq_classes and seq_classes[n] is None,
               f"corner class {n} carries no SCENARIO_ID",
               repr(seq_classes.get(n)))
    budget = class_attr(test_tree, corner_test, "WATCHDOG_BUDGET_CYCLES",
                        env={"WATCHDOG_MARGIN_CYCLES": WATCHDOG_MARGIN_CYCLES})
    check(f"{corner_test} watchdog budget == 6 x margin (60000)",
          budget == 60000, repr(budget))

    # Randomized test.
    rand_test = "I2CRandomTest"
    expect(rand_test in runnable, f"{rand_test} is a uvm_test subclass", "")
    rbudget = class_attr(test_tree, rand_test, "WATCHDOG_BUDGET_CYCLES",
                         env={"WATCHDOG_MARGIN_CYCLES": WATCHDOG_MARGIN_CYCLES})
    check(f"{rand_test} watchdog budget == 20 x margin (200000)",
          rbudget == 200000, repr(rbudget))
    rseed = module_attr(test_tree, "DEFAULT_RANDOM_SEED")
    ritems = module_attr(test_tree, "DEFAULT_RANDOM_TRANSACTIONS")
    check("DEFAULT_RANDOM_TRANSACTIONS == 100 (plan strategy)",
          ritems == 100, repr(ritems))
    check("DEFAULT_RANDOM_SEED is deterministic int",
          isinstance(rseed, int) and 0 < rseed < 2**31, repr(rseed))

    # Directed base class USES the env margin as the default budget.
    base_budget = class_attr(
        test_tree, "I2CBaseTest", "WATCHDOG_BUDGET_CYCLES",
        env={"WATCHDOG_MARGIN_CYCLES": WATCHDOG_MARGIN_CYCLES})
    check("I2CBaseTest watchdog budget == WATCHDOG_MARGIN_CYCLES (10000)",
          base_budget == WATCHDOG_MARGIN_CYCLES, repr(base_budget))

    # Reset-only test semantics.
    reset_test = "ResetIdleCheckTest"
    rq = instance_attr(test_tree, reset_test,
                       "_require_graded_transactions")
    check("ResetIdleCheckTest._require_graded_transactions is False",
          rq is False, repr(rq))
    check("ResetIdleCheckSequence.SCENARIO_ID == 'TC-01'",
          seq_classes.get("ResetIdleCheckSequence") == "TC-01",
          repr(seq_classes.get("ResetIdleCheckSequence")))

    check_manifest_scenario_names(seq_classes, registry)


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
# 3. test_top.py wiring
# ---------------------------------------------------------------------------
def check_test_top() -> None:
    check("test_top.py exists at exact worker path", TEST_TOP_PY.is_file(),
          str(TEST_TOP_PY))
    tree = load_ast(TEST_TOP_PY)

    # ConfigDB keys: exactly dut + i2c_pins, passed as the KEY_DUT /
    # KEY_DUT_PINS constants (CONTRACT.md §6).  Resolve the third argument
    # expression and verify the constants' literal values from i2c_pins.py.
    set_calls = []
    keys = set()          # third-arg expressions, e.g. {KEY_DUT, KEY_DUT_PINS}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "set" \
                and "ConfigDB" in ast.unparse(node.func.value):
            args = [ast.unparse(a) for a in node.args] + \
                   [f"{k.arg}={ast.unparse(k.value)}" for k in node.keywords]
            set_calls.append("ConfigDB().set(" + ", ".join(args) + ")")
            if len(node.args) >= 3:
                keys.add(ast.unparse(node.args[2]))
    key_values = {}
    pins_src = ENV_PY.parent.joinpath("i2c_pins.py")
    if pins_src.is_file():
        pins_tree = load_ast(pins_src)
        for key_name in ("KEY_DUT", "KEY_DUT_PINS"):
            val = module_attr(pins_tree, key_name)
            if isinstance(val, str):
                key_values[key_name] = val
    check("i2c_pins defines KEY_DUT == 'dut' and KEY_DUT_PINS == 'i2c_pins'",
          key_values == {"KEY_DUT": "dut", "KEY_DUT_PINS": "i2c_pins"},
          repr(key_values))
    check("ConfigDB keys are exactly {'dut','i2c_pins'} (CONTRACT.md §6)",
          keys == {"KEY_DUT", "KEY_DUT_PINS"} and set(key_values) == keys,
          repr(sorted(keys)))
    expect(len(set_calls) == 2,
           "ConfigDB().set called exactly twice (dut, i2c_pins)",
           "; ".join(set_calls))

    # run_test keep_singletons=True (pyuvm 5.0.0 clears ConfigDB otherwise).
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

    # Outer budget must be derived from the pins WATCHDOG_CYCLES constant.
    outer_ok = "WATCHDOG_CYCLES" in TEST_TOP_PY.read_text()
    check("outer bound derives from CONTRACT WATCHDOG_CYCLES", outer_ok, "")

    src = TEST_TOP_PY.read_text()
    default = re.search(r"DEFAULT_TEST\s*=\s*[\"']([\w]+)[\"']", src)
    check("DEFAULT_TEST fallback == ResetIdleCheckTest",
          bool(default) and default.group(1) == "ResetIdleCheckTest",
          default.group(1) if default else "missing")
    check("test_top reads UVM_TESTNAME env var", "UVM_TESTNAME" in src, "")
    check("test_top imports i2c_test (factory registration)",
          "import i2c_test" in src, "")
    check("test_top drives reset via I2CPins", "drive_reset" in src, "")
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
    check("Makefile TOPLEVEL = i2c_master",
          line_has(r"TOPLEVEL\s*=\s*i2c_master"), "")
    check("Makefile MODULE = test_top", line_has(r"MODULE\s*=\s*test_top"), "")
    check("Makefile VERILOG_SOURCES -> i2c_master.sv (read-only DUT)",
          re.search(r"VERILOG_SOURCES\s*=\s*.+i2c_master\.sv", text)
          is not None, "")
    check("Makefile includes cocotb Makefile.sim",
          "include $(shell cocotb-config --makefiles)/Makefile.sim" in text, "")
    check("Makefile UVM_TESTNAME default settable",
          re.search(r"UVM_TESTNAME\s*\?=\s*ResetIdleCheckTest",
                    text) is not None, "")
    check("Makefile COMPILE_ARGS include --timing", "--timing" in text, "")


# ---------------------------------------------------------------------------
# 5. Env wiring
# ---------------------------------------------------------------------------
def check_env() -> None:
    check("tb/i2c_env.py exists", ENV_PY.is_file(), str(ENV_PY))
    tree = load_ast(ENV_PY)
    methods = class_methods(tree, "I2CEnv")
    build = methods.get("build_phase")
    connect = methods.get("connect_phase")
    expect(build is not None, "I2CEnv.build_phase exists", "")
    expect(connect is not None, "I2CEnv.connect_phase exists", "")

    build_src = ast.unparse(build) if build else ""
    connect_src = ast.unparse(connect) if connect else ""
    check("build_phase instantiates agent + scoreboard",
          "I2CAgent(" in build_src and "I2CScoreboard(" in build_src, "")
    check("build_phase instantiates coverage + launches assertion checkers",
          "I2CCoverage(" in build_src and "launch_assertions(" in build_src,
          "")
    check("connect_phase sets KEY_I2C_DRIVER (CONTRACT.md §13.1/§17.3)",
          "KEY_I2C_DRIVER" in connect_src, "")
    check("connect_phase wires scoreboard.connect_monitor(agent)",
          "connect_monitor" in connect_src and "self.agent" in connect_src,
          "")

    # Watchdog primitives + margin constant (CONTRACT.md §17.4).
    names = set(py_class_names(tree))
    expect("I2CEnv" in names, "I2CEnv class exists", "")
    env_methods = class_methods(tree, "I2CEnv")
    expect("arm_watchdog" in env_methods and "disarm_watchdog" in env_methods,
           "I2CEnv owns arm_watchdog/disarm_watchdog primitives", "")
    margin = module_attr(tree, "WATCHDOG_MARGIN_CYCLES")
    check("i2c_env.WATCHDOG_MARGIN_CYCLES == 10000",
          margin == WATCHDOG_MARGIN_CYCLES, repr(margin))
    check("i2c_env references launch_watchdog",
          "launch_watchdog" in ENV_PY.read_text(), "")


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