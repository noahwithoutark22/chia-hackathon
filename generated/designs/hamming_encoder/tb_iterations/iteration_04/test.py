"""hamming_encoder test classes (stage 6: INTEGRATION).

This module defines one pyuvm ``uvm_test`` subclass per directed plan
scenario (TC1..TC8), plus a corner-case aggregate test and a randomized
test, matching ``generation_manifest.yaml`` exactly::

    HammingTC1Test .. HammingTC8Test   (directed scenarios)
    HammingCornerTest                  (all corner-case sequences)
    HammingRandomizedTest              (constrained-random traffic)

Each directed test starts exactly the sequence class that manifests its
``SCENARIO_ID`` (the mapping is checked by the pipeline's
``validate_scenario_manifest``), so a test's stimulus and its sequence
can never drift apart.

== Adaptive-skip design (one elaboration per simulation) ==

The DUT is elaborated once per simulation with a fixed ``DATA_WIDTH`` /
``SECDED`` pair.  Plan scenarios target several elaborations (CONTRACT.md
section 4), so a test whose scenario is inapplicable to the active
elaboration logs why and passes without exercising the DUT -- matching the
guarded, log-and-skip behaviour of the sequences themselves (sequences.py)
and keeping every manifest test green under the default elaboration
(DATA_WIDTH=4, SECDED=0) used by the worker.  ``elaboration_applies`` on
each test mirrors the guard of its mapped sequence exactly.

* ``report_phase`` always enforces **zero scoreboard mismatches** (a
  mismatch has already raised ``AssertionError`` in the scoreboard, so
  this is a belt-and-braces final gate).
* For an **applicable** elaboration the test must also have exercised at
  least one scored item (``_num_items_checked > 0``), so a silently
  crashed/crashed-early sequence cannot false-pass (the empty-run guard
  the FIFO bench establishes).
* For an **inapplicable** elaboration the test passes without the item
  guard -- it is skipped by design, not by accident.

== Execution/skip ledger (report-only, W2 visibility) ==

Every ``report_phase`` additionally exports a machine-readable per-test
execution/skip record (``hamming_encoder_execution_{RUN_ID_}{test}_
d{DATA_WIDTH}_s{SECDED}.yml``) and merges all per-test records
(RUN_ID-scoped, excluding the generic and aggregate files -- exactly
mirroring tb/coverage.py) into ``hamming_encoder_execution_aggregate.yml``
with ``tests_total`` / ``tests_executed`` / ``tests_skipped`` and the
executed/skipped scenario-id lists.  A skipped (inapplicable) test also
logs a WARNING-level ``TEST SKIPPED -> SCENARIO <id> NOT EXECUTED`` line
(the exact ``TEST SKIPPED`` prefix of the existing info line is preserved).
The ledger is **reporting only**: it never changes a pass/fail verdict, and
every file operation is try/except-wrapped so a ledger failure degrades to
a warning exactly like tb/coverage.py's export path.

== Run-phase objection contract ==

``run_phase`` raises a pyuvm run-phase objection while ``_run_scenario``
executes and drops it afterwards.  pyuvm's ``run_test`` waits for
``run_phase_complete()`` (which only returns once the last objection is
dropped) before the synchronous report phases, so the scoreboard's final
counters are settled when ``report_phase`` evaluates pass/fail.

== tb_reset = environment-only (CONTRACT.md sections 3, 11.4) ==

Tests whose mapped sequence performs a tb_reset phase at scenario start
(TC1, randomized) call ``HammingScoreboard.reset_checker()`` once per
tb_reset phase, exactly as CONTRACT.md section 11.4 requires.  Nothing here
ever touches ``dut.clk`` / ``dut.tb_reset``: pacing uses the virtual
reference clock through ``wait_clock_cycles``.
"""

import functools
import os

from pyuvm import ConfigDB, uvm_test

from tb.dut_helper import KEY_CLK_RST, KEY_CONF, wait_clock_cycles
from tb.env import HammingEnv
from tb.sequences import (
    CORNER_CASE_SEQUENCE_CLASSES,
    HammingRandomizedSequence,
    AlternatingAndBoundaryPatternsSeq,   # TC8
    ExhaustiveSweepHamming128Seq,        # TC5
    ExhaustiveSweepHamming74Seq,         # TC4
    ParameterizedWidthConfigurationsSeq, # TC7
    ResetAndZeroInitialStateSeq,         # TC1
    SingleBitWalkSeq,                    # TC6
    SpecExampleHamming74Seq,             # TC2
    SpecExampleHamming84SECDEDSeq,       # TC3
)

__all__ = [
    "HammingTestBase",
    "HammingTC1Test",
    "HammingTC2Test",
    "HammingTC3Test",
    "HammingTC4Test",
    "HammingTC5Test",
    "HammingTC6Test",
    "HammingTC7Test",
    "HammingTC8Test",
    "HammingCornerTest",
    "HammingRandomizedTest",
]

# Defaults for the randomized strategy (plan randomized_testing_strategy).
RANDOM_VECTORS = 1000
RANDOM_SEED_DEFAULT = 0x5EED
RANDOM_BOUNDARY_PROB = 0.25

# Virtual-reference-cycle drains after each sequence, letting the monitor
# publish and the scoreboard consume every final transaction before the
# run-phase objection is dropped (CONTRACT.md section 8).
DRAIN_CYCLES = 2
RANDOM_DRAIN_CYCLES = 5


# ---------------------------------------------------------------------------
# Execution/skip ledger (W2 visibility; report-only, never verdict-changing)
# ---------------------------------------------------------------------------
# Each test's report_phase exports a per-test execution/skip YAML record and
# merges every per-test record into hamming_encoder_execution_aggregate.yml,
# so the regression can distinguish executed from skipped plan scenarios and
# audit the actual (DATA_WIDTH, SECDED) elaboration of every test.  All file
# I/O is best-effort (try/except -> warning), mirroring tb/coverage.py.
_LEDGER_RUN_ID = os.environ.get("RUN_ID", "").strip()

# Corner/Randomized tests intentionally carry no SCENARIO_ID in
# generation_manifest.yaml; the aggregate maps them to stable role labels.
_LEDGER_ROLE_LABELS = {
    "HammingCornerTest": "corner",
    "HammingRandomizedTest": "randomized",
}

_LEDGER_GENERIC_YAML = "hamming_encoder_execution.yml"
_LEDGER_AGGREGATE_YAML = "hamming_encoder_execution_aggregate.yml"


@functools.lru_cache(maxsize=1)
def _manifest_scenario_map():
    """Map test class name -> plan scenario id from generation_manifest.yaml.

    The manifest's ``scenarios`` table is the authoritative test->scenario
    mapping (the pipeline validates it against the sequences), so reading it
    here keeps the ledger's scenario ids from drifting from the manifest.
    Returns ``{}`` (best-effort) when the file cannot be located/parsed.
    """
    import yaml as _yaml  # delayed import (report-time only)

    candidates = [
        os.path.join(os.path.dirname(__file__), "generation_manifest.yaml"),
        "generation_manifest.yaml",
    ]
    for path in candidates:
        try:
            with open(path) as fh:
                manifest = _yaml.safe_load(fh) or {}
        except Exception:  # pragma: no cover - run-layout fallback
            continue
        mapping = {}
        for entry in manifest.get("scenarios", []) or []:
            test_name = (entry or {}).get("test")
            sid = (entry or {}).get("id")
            if test_name and sid:
                mapping[test_name] = sid
        return mapping
    return {}


def _ledger_test_name():
    """UVM_TESTNAME (== manifest test class); matches tb/coverage.py naming.

    pyuvm 3.0.0 instantiates the selected test as ``uvm_test_top``, so
    ``self.get_name()`` is not the class name -- the env var is (same source
    tb/coverage.py uses for its per-test coverage file names).
    """
    return os.environ.get("UVM_TESTNAME", "unknown")


def _build_execution_record(test_name, conf, applicable, sb, skip_reason):
    """Build one per-test execution/skip ledger record (report-only)."""
    return {
        "test": test_name,
        "data_width": int(conf.data_width),
        "secded": int(conf.secded),
        "code_width": int(conf.code_width),
        "applicable": bool(applicable),
        "executed": bool(applicable and sb._num_items_checked > 0),
        "items_checked": int(sb._num_items_checked),
        "items_passed": int(sb._num_passed),
        "mismatches": int(sb._num_mismatches),
        "scenario_id": _manifest_scenario_map().get(test_name),
        "skip_reason": skip_reason,
    }


def _export_execution_record(record, logger):
    """Write the per-test execution ledger YAML (best-effort).

    Per-test filenames are unique per (test, DATA_WIDTH, SECDED) so a future
    multi-elaboration regression accumulates every configuration a test
    runs; the generic ``hamming_encoder_execution.yml`` stays last-test-wins
    for backward compatibility (same as tb/coverage.py's generic export).
    """
    try:
        import yaml as _yaml
    except ImportError:  # pragma: no cover - tooling
        logger.warning(
            "HammingExecution ledger export: PyYAML not available; "
            "skipping per-test record")
        return
    try:
        test_safe = record["test"].replace(" ", "_")
        run_prefix = f"{_LEDGER_RUN_ID}_" if _LEDGER_RUN_ID else ""
        per_test_yaml = (
            f"hamming_encoder_execution_{run_prefix}{test_safe}"
            f"_d{record['data_width']}_s{record['secded']}.yml"
        )
        with open(per_test_yaml, "w") as fh:
            _yaml.safe_dump(record, fh, sort_keys=False)
        with open(_LEDGER_GENERIC_YAML, "w") as fh:
            _yaml.safe_dump(record, fh, sort_keys=False)
        logger.info(
            "HammingExecution ledger exported to %s", per_test_yaml)
    except Exception as exc:  # pragma: no cover - filesystem/tooling
        logger.warning(
            "HammingExecution ledger export failed: %s", exc)


def _merge_execution_ledger(logger):
    """Aggregate per-test execution/skip ledgers into the aggregate YAML.

    Reads every ``hamming_encoder_execution_*.yml`` file (excluding the
    generic and the aggregate output), RUN_ID-scoped when ``RUN_ID`` is set
    (exactly mirroring tb/coverage.py's merge), deduplicates by
    (test, DATA_WIDTH, SECDED) so a test that runs multiple elaborations
    keeps one record per configuration, and persists a regression-level
    summary: tests_total/tests_executed/tests_skipped plus the executed and
    skipped scenario-id lists.  Best-effort reporting only.
    """
    import glob as _glob

    try:
        import yaml as _yaml
    except ImportError:  # pragma: no cover - tooling
        logger.warning(
            "HammingExecution merge: PyYAML not available; skipping "
            "aggregate")
        return

    ledger_files = sorted(
        _glob.glob("hamming_encoder_execution_*.yml")
    )
    ledger_files = [
        f for f in ledger_files
        if f not in (_LEDGER_GENERIC_YAML, _LEDGER_AGGREGATE_YAML)
    ]
    if _LEDGER_RUN_ID:
        run_prefixed = [
            f for f in ledger_files
            if f.startswith(f"hamming_encoder_execution_{_LEDGER_RUN_ID}_")
        ]
        if run_prefixed:
            logger.info(
                "HammingExecution merge: scoping to RUN_ID=%s (%d file(s))",
                _LEDGER_RUN_ID, len(run_prefixed),
            )
            ledger_files = run_prefixed
        else:
            logger.info(
                "HammingExecution merge: no RUN_ID=%s-scoped files found",
                _LEDGER_RUN_ID,
            )
            return
    if not ledger_files:
        logger.info(
            "HammingExecution merge: no per-test ledger files found")
        return

    records = {}
    for fpath in ledger_files:
        try:
            with open(fpath) as fh:
                data = _yaml.safe_load(fh)
        except Exception:  # pragma: no cover - filesystem/tooling
            continue
        if not isinstance(data, dict) or "test" not in data:
            continue
        key = (data["test"], int(data.get("data_width", -1)),
               int(data.get("secded", -1)))
        records[key] = data  # one record per (test, dw, secded) key
    if not records:
        logger.info(
            "HammingExecution merge: no records parsed from %d file(s)",
            len(ledger_files),
        )
        return

    ordered = [records[key] for key in sorted(records)]
    executed = [r for r in ordered if r.get("executed")]
    skipped = [r for r in ordered if not r.get("executed")]
    executed_ids = [
        r.get("scenario_id")
        or _LEDGER_ROLE_LABELS.get(r.get("test"), r.get("test"))
        for r in executed
    ]
    skipped_ids = [
        r["scenario_id"] for r in skipped if r.get("scenario_id")
    ]
    aggregate = {
        "schema_version": "1.0",
        "run_id": _LEDGER_RUN_ID or None,
        "tests_total": len(ordered),
        "tests_executed": len(executed),
        "tests_skipped": len(skipped),
        "executed_scenario_ids": sorted(dict.fromkeys(executed_ids)),
        "skipped_scenario_ids": sorted(dict.fromkeys(skipped_ids)),
        "records": ordered,
    }
    try:
        with open(_LEDGER_AGGREGATE_YAML, "w") as fh:
            _yaml.safe_dump(aggregate, fh, sort_keys=False)
        logger.info(
            "HammingExecution aggregate exported to %s: total=%d "
            "executed=%d skipped=%d",
            _LEDGER_AGGREGATE_YAML, len(ordered), len(executed),
            len(skipped),
        )
    except Exception as exc:  # pragma: no cover - filesystem/tooling
        logger.warning(
            "HammingExecution aggregate export failed: %s", exc)


# ---------------------------------------------------------------------------
# Shared stimulus helpers
# ---------------------------------------------------------------------------
async def _drain_cycles(n=DRAIN_CYCLES):
    """Pace ``n`` virtual reference cycles (no DUT clock is touched)."""
    clkrs = ConfigDB().get(None, "*", KEY_CLK_RST)
    await wait_clock_cycles(clkrs, n)


async def _run_single_sequence(test, seq_cls, drain_cycles=DRAIN_CYCLES):
    """Start ``seq_cls`` on the agent's sequencer and let the scoreboard
    drain the final monitor transactions."""
    seq = seq_cls()
    await seq.start(test.env.agent.sequencer)
    await _drain_cycles(drain_cycles)


# ---------------------------------------------------------------------------
# Base test
# ---------------------------------------------------------------------------
class HammingTestBase(uvm_test):
    """Common substrate for every hamming_encoder test.

    * ``build_phase`` creates :class:`~tb.env.HammingEnv` (agent +
      scoreboard + coverage, plus the always-on assertion checkers).
    * ``run_phase`` raises a run-phase objection around ``_run_scenario()``
      so the whole scenario (and its drains) completes before the report
      phases.
    * ``report_phase`` enforces the pass criteria (adaptive-skip design
      described in the module docstring).
    """

    #: Whether this test's mapped sequence performs a tb_reset phase at
    #: scenario start, requiring one ``reset_checker()`` call (CONTRACT.md
    #: section 11.4).
    RESET_BEFORE_SCENARIO = False

    def __init__(self, name="hamming_test", parent=None):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        """Create :class:`~tb.env.HammingEnv` under this test."""
        super().build_phase()
        self.env = HammingEnv("hamming_env", self)
        self.logger.info("%s: HammingEnv created", self.get_name())

    # ------------------------------------------------------------------
    # Elaboration applicability (adaptive-skip design)
    # ------------------------------------------------------------------
    @classmethod
    def elaboration_applies(cls, conf):
        """True when this test's scenario is meaningful for *conf*.

        Every subclass mirrors the elaboration guard of its mapped
        sequence (same predicate, same intent).  Must be overridden.
        """
        raise NotImplementedError(
            f"{cls.__name__} must implement elaboration_applies()")

    # ------------------------------------------------------------------
    # Run phase: scenario under a run-phase objection
    # ------------------------------------------------------------------
    async def run_phase(self):
        """Run the stimulus scenario under a pyuvm objection.

        Dropping the objection in a ``finally`` guarantees
        ``run_phase_complete()`` returns only after ``_run_scenario`` (and
        its drains) fully completes, so the scoreboard's final counters are
        set when ``report_phase`` runs.
        """
        self.raise_objection()
        try:
            if self.RESET_BEFORE_SCENARIO:
                # One reset_checker() per tb_reset phase (CONTRACT 11.4).
                self.env.scoreboard.reset_checker()
            await self._run_scenario()
        finally:
            self.drop_objection()

    async def _run_scenario(self):
        """Stimulus entry point; concrete tests override this."""
        self.logger.warning(
            "%s._run_scenario() not overridden: no stimulus applied",
            self.get_name(),
        )

    # ------------------------------------------------------------------
    # ConfigDB access
    # ------------------------------------------------------------------
    def _conf(self):
        """Shared ``HammingConf`` geometry (ConfigDB KEY_CONF)."""
        return ConfigDB().get(None, "*", KEY_CONF)

    # ------------------------------------------------------------------
    # Pass/fail evaluation
    # ------------------------------------------------------------------
    def report_phase(self):
        """Enforce the pass criteria (adaptive-skip design).

        1. Zero scoreboard mismatches is always required.
        2. An inapplicable elaboration -> log-and-skip (still passes); the
           skip is also WARNING-logged (``TEST SKIPPED -> SCENARIO <id> NOT
           EXECUTED``) and recorded in the execution/skip ledger, making the
           unexercised scenario visible and machine-readable without
           changing the verdict.
        3. An applicable elaboration -> at least one scored item, so a
           test that never exercised the DUT cannot false-pass.

        The ledger export + merge below is report-only (never a verdict
        change) and fully try/except-wrapped: a ledger failure degrades to
        a warning exactly like tb/coverage.py's export path.
        """
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            return  # guard against early phase failures
        conf = self._conf()
        applicable = bool(type(self).elaboration_applies(conf))
        skip_reason = None
        if not applicable:
            skip_reason = (
                f"inapplicable to (DATA_WIDTH={conf.data_width}, "
                f"SECDED={conf.secded})"
            )
        test_name = _ledger_test_name()
        record = _build_execution_record(
            test_name, conf, applicable, sb, skip_reason)
        _export_execution_record(record, self.logger)
        _merge_execution_ledger(self.logger)

        if sb._num_mismatches > 0:
            self.logger.error(
                "TEST FAILED: %d scoreboard mismatch(es) across %d checked "
                "items (%d passed, %d reset(s) observed)",
                sb._num_mismatches, sb._num_items_checked,
                sb._num_passed, sb._num_resets,
            )
            raise AssertionError(
                f"HammingScoreboard reported {sb._num_mismatches} "
                "mismatch(es)"
            )
        if not applicable:
            scenario_id = record.get("scenario_id")
            self.logger.warning(
                "TEST SKIPPED -> SCENARIO %s NOT EXECUTED: %s is "
                "inapplicable to this elaboration (DATA_WIDTH=%d, "
                "SECDED=%d); passing without stimulus",
                scenario_id if scenario_id is not None else "?",
                test_name, conf.data_width, conf.secded,
            )
            self.logger.info(
                "TEST SKIPPED: %s is inapplicable to this elaboration "
                "(DATA_WIDTH=%d, SECDED=%d); passing without stimulus",
                self.get_name(), conf.data_width, conf.secded,
            )
            return
        sb = self.env.scoreboard
        if sb._num_items_checked == 0:
            self.logger.error(
                "TEST FAILED: zero scoreboard items checked — an "
                "applicable scenario exercised no stimulus "
                "(DATA_WIDTH=%d, SECDED=%d)",
                conf.data_width, conf.secded,
            )
            raise AssertionError(
                "HammingScoreboard checked 0 items — applicable test "
                "exercised no stimulus"
            )
        self.logger.info(
            "TEST PASSED: %d items checked, 0 mismatches, %d passed, %d "
            "reset(s) observed (DATA_WIDTH=%d, SECDED=%d)",
            sb._num_items_checked, sb._num_passed, sb._num_resets,
            conf.data_width, conf.secded,
        )


# ---------------------------------------------------------------------------
# Directed scenario tests (TC1..TC8)
# ---------------------------------------------------------------------------
class HammingTC1Test(HammingTestBase):
    """TC1 — reset_and_zero_initial_state (Hamming(7,4))."""

    RESET_BEFORE_SCENARIO = True

    def __init__(self, name="HammingTC1Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width == 4 and conf.secded == 0

    async def _run_scenario(self):
        # The sequence asserts tb_reset (2 cycles) then releases it (1
        # cycle): the tb_reset phase for this scenario.
        await _run_single_sequence(self, ResetAndZeroInitialStateSeq)


class HammingTC2Test(HammingTestBase):
    """TC2 — spec_example_hamming_74 (spec.md section 4.1)."""

    def __init__(self, name="HammingTC2Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width == 4 and conf.secded == 0

    async def _run_scenario(self):
        await _run_single_sequence(self, SpecExampleHamming74Seq)


class HammingTC3Test(HammingTestBase):
    """TC3 — spec_example_hamming_84_secded (spec.md section 4.2)."""

    def __init__(self, name="HammingTC3Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width == 4 and conf.secded == 1

    async def _run_scenario(self):
        await _run_single_sequence(self, SpecExampleHamming84SECDEDSeq)


class HammingTC4Test(HammingTestBase):
    """TC4 — exhaustive_sweep_hamming_74 (all 16 vectors, active SECDED)."""

    def __init__(self, name="HammingTC4Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width == 4

    async def _run_scenario(self):
        await _run_single_sequence(self, ExhaustiveSweepHamming74Seq)


class HammingTC5Test(HammingTestBase):
    """TC5 — exhaustive_sweep_hamming_128 (DATA_WIDTH=8, SECDED=0)."""

    def __init__(self, name="HammingTC5Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width == 8 and conf.secded == 0

    async def _run_scenario(self):
        await _run_single_sequence(self, ExhaustiveSweepHamming128Seq)


class HammingTC6Test(HammingTestBase):
    """TC6 — single_bit_walk (every data-bit position, active SECDED)."""

    def __init__(self, name="HammingTC6Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        # Valid for every (DATA_WIDTH, SECDED) elaboration.
        return True

    async def _run_scenario(self):
        await _run_single_sequence(self, SingleBitWalkSeq)


class HammingTC7Test(HammingTestBase):
    """TC7 — parameterized_width_configurations (DATA_WIDTH in {1,11,16})."""

    def __init__(self, name="HammingTC7Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width in (1, 11, 16)

    async def _run_scenario(self):
        await _run_single_sequence(self, ParameterizedWidthConfigurationsSeq)


class HammingTC8Test(HammingTestBase):
    """TC8 — alternating_and_boundary_patterns (4-bit patterns)."""

    def __init__(self, name="HammingTC8Test", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width == 4

    async def _run_scenario(self):
        await _run_single_sequence(self, AlternatingAndBoundaryPatternsSeq)


# ---------------------------------------------------------------------------
# Corner-case aggregate test
# ---------------------------------------------------------------------------
class HammingCornerTest(HammingTestBase):
    """Runs every corner-case sequence from the plan sequentially.

    Corner-case sequences (plan ``corner_cases``) intentionally carry no
    ``SCENARIO_ID``; they are collected in ``CORNER_CASE_SEQUENCE_CLASSES``
    (sequences.py).  The elaboration-gated corners (DATA_WIDTH=1 /
    {5,16} / SECDED=1) log-and-skip under an inapplicable elaboration; the
    un-gated corners (zero / all-ones / single-bit walk / weight symmetry)
    drive at least one vector under *any* elaboration, so this test always
    exercises and scores real stimulus.
    """

    def __init__(self, name="HammingCornerTest", parent=None):
        super().__init__(name, parent)

    @classmethod
    def elaboration_applies(cls, conf):
        # The un-gated corner sequences always drive >= 1 item regardless
        # of the active elaboration.
        return True

    async def _run_scenario(self):
        for seq_cls in CORNER_CASE_SEQUENCE_CLASSES:
            seq = seq_cls()
            await seq.start(self.env.agent.sequencer)
            # Brief drain between sequences so the scoreboard consumes
            # each item before the next sequence starts.
            await _drain_cycles(DRAIN_CYCLES)
        # Final drain after the last sequence.
        await _drain_cycles(DRAIN_CYCLES)


# ---------------------------------------------------------------------------
# Randomized test
# ---------------------------------------------------------------------------
class HammingRandomizedTest(HammingTestBase):
    """Runs the constrained-random sequence (plan randomized_testing_strategy).

    ``HammingRandomizedSequence`` drives boundary-concentrated + uniform
    ``data_in`` values for the active elaboration and self-scores each
    vector against the reference model.  The plan's per-configuration
    environment reset is performed at scenario start, so this test also
    clears the scoreboard's per-block accounting once (CONTRACT.md section
    11.4).  A deterministic default seed (``RANDOM_SEED`` env var override)
    makes failures reproducible.
    """

    RESET_BEFORE_SCENARIO = True

    def __init__(self, name="HammingRandomizedTest", parent=None):
        super().__init__(name, parent)
        self._seq = None  # holds the started sequence for seed reporting

    @classmethod
    def elaboration_applies(cls, conf):
        return conf.data_width in (4, 8)

    async def _run_scenario(self):
        # int(str(...), 0) so "0x1234"-style seeds in RANDOM_SEED are
        # accepted and the integer default round-trips safely.
        seed = int(str(os.environ.get("RANDOM_SEED", RANDOM_SEED_DEFAULT)), 0)
        seq = HammingRandomizedSequence(
            num_vectors=RANDOM_VECTORS,
            seed=seed,
            boundary_prob=RANDOM_BOUNDARY_PROB,
        )
        self._seq = seq
        # The sequence performs the tb_reset phase (2 cycles asserted, 1
        # released) at scenario start.
        await seq.start(self.env.agent.sequencer)
        # Allow the scoreboard to drain the final transactions.
        await _drain_cycles(RANDOM_DRAIN_CYCLES)

    def report_phase(self):
        if self._seq is not None and self._seq.seed is not None:
            self.logger.info(
                "HammingRandomizedTest used RNG seed %d (replay with "
                "RANDOM_SEED=%d)", self._seq.seed, self._seq.seed,
            )
        super().report_phase()