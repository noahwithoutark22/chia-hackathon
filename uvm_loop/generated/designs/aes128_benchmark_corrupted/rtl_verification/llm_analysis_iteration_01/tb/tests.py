"""AES-128 test classes (stage-6 TEST artifact).

One ``uvm_test`` subclass per directed verification-plan scenario
(``verification_plan.yaml`` ``directed_test_scenarios``, ids ``TC01``..``TC09``),
plus a corner-case aggregate test and a constrained-random test -- exactly
the ``test_classes`` list in ``generation_manifest.yaml`` and the
``scenarios`` mapping recorded there.

    directed scenarios (each with an explicit ``get_sequence_class()`` that
    returns the mapped stimulus sequence class SYMBOL, never a string):
        Aes128ResetReleaseIdleTest                -> ResetReleaseIdleSeq                (TC01)
        Aes128Fips197KnownAnswerTest              -> Fips197KnownAnswerSeq              (TC02)
        Aes128AllZeroKnownAnswerTest              -> AllZeroKnownAnswerSeq              (TC03)
        Aes128IncrementingKnownAnswerTest         -> IncrementingKnownAnswerSeq         (TC04)
        Aes128BackToBackTransactionsTest          -> BackToBackTransactionsSeq          (TC05)
        Aes128KeySensitivityTest                  -> KeySensitivitySeq                  (TC06)
        Aes128PlaintextSensitivityTest            -> PlaintextSensitivitySeq            (TC07)
        Aes128DeterminismRepeatedEncryptionTest   -> DeterminismRepeatedEncryptionSeq   (TC08)
        Aes128DonePulseAndStartIgnoredWhileBusyTest -> DonePulseAndStartIgnoredWhileBusySeq (TC09)

    additional verification strategies (NO ``SCENARIO_ID``, plan
    ``corner_cases`` / ``randomized_testing_strategy`` -- separate sections
    with no directed-scenario entry in the manifest):
        Aes128CornerTest     -> runs all six corner-case sequences
        Aes128RandomizedTest -> randomized_testing_strategy

Each directed test class MUST define ``get_sequence_class()`` explicitly
(it is never inherited) and the method MUST return the exact sequence class
named in ``generation_manifest.yaml`` ``scenarios[].sequence``.  The static
scenario-manifest validator verifies this mapping through the Python AST,
and the import-time guard :func:`verify_directed_test_scenario_ids` re-checks
it at runtime against the sequence side's ``SCENARIO_ID`` registry.

GRADING SEMANTIC (plan pass criteria written against the reference model,
never against the buggy RTL -- this is an intentionally corrupted benchmark):

* Scoreboard ``protocol_errors`` / ``order_errors`` / ``ungradable_errors``
  are REAL verification-environment contract violations and always fail the
  test in ``report_phase``.
* A data-path test that scored zero completed transactions fails (its
  driver/sequence crashed before exercising any stimulus).
* Ciphertext ``mismatches`` against the reference-model oracle also fail
  the test: the plan's pass criterion is "100% of completed transactions
  match aes128_encrypt(plaintext, key)".  On this corrupted RTL
  (DISC-01/DISC-02: ``busy`` stays high after reset and the round counter
  increments by 2 so ``done`` is never asserted) the sequences' bounded
  ``done`` waits and the env's assertion checkers fail the test first --
  the intended bug-detection outcome.
* On a repaired RTL every scenario completes with zero mismatches and
  passes.

All APIs used here are public pyuvm 5.0.0 (``uvm_test``, ``ConfigDB``) and
public Cocotb 2.1.0 (``cocotb.triggers.ClockCycles``).  No SystemVerilog
anywhere.
"""

import os

from cocotb.triggers import ClockCycles

from pyuvm import ConfigDB, uvm_test

from coverage import coverage_summary_dict
from env import Aes128Env
from sequences import (
    Aes128RandomizedSeq,
    AllZeroKnownAnswerSeq,
    BackToBackTransactionsSeq,
    CORNER_SEQUENCES,
    DeterminismRepeatedEncryptionSeq,
    DIRECTED_SEQUENCES,
    DonePulseAndStartIgnoredWhileBusySeq,
    Fips197KnownAnswerSeq,
    IncrementingKnownAnswerSeq,
    KeySensitivitySeq,
    PlaintextSensitivitySeq,
    ResetReleaseIdleSeq,
)

__all__ = [
    "Aes128TestBase",
    "Aes128ResetReleaseIdleTest",
    "Aes128Fips197KnownAnswerTest",
    "Aes128AllZeroKnownAnswerTest",
    "Aes128IncrementingKnownAnswerTest",
    "Aes128BackToBackTransactionsTest",
    "Aes128KeySensitivityTest",
    "Aes128PlaintextSensitivityTest",
    "Aes128DeterminismRepeatedEncryptionTest",
    "Aes128DonePulseAndStartIgnoredWhileBusyTest",
    "Aes128CornerTest",
    "Aes128RandomizedTest",
    "DIRECTED_TEST_CLASSES",
    "DIRECTED_TEST_CLASSES_BY_ID",
    "verify_directed_test_scenario_ids",
]


def _config_get(field, default=None):
    """Retrieve a ConfigDB key using the CONTRACT.md §4 retrieval convention.

    Identical helper to the other tb modules: primary form
    ``ConfigDB().get(None, "*", field)``, falling back to the equivalent
    ``inst_name=""`` retrieval when the pinned pyuvm 5.0.0 runtime rejects
    wildcard characters in a retrieval path.  No key or value type is
    changed.
    """
    try:
        return ConfigDB().get(None, "*", field, default=default)
    except Exception:
        return ConfigDB().get(None, "", field, default=default)


# ---------------------------------------------------------------------------
# Base test
# ---------------------------------------------------------------------------
class Aes128TestBase(uvm_test):
    """Common base for every AES-128 test.

    * ``build_phase`` creates :class:`~env.Aes128Env` (agent + scoreboard +
      coverage + the always-running assertion checkers, CONTRACT.md §11.2).
    * ``run_phase`` raises a run-phase objection, runs ``_run_scenario()``
      (subclass-specific) and drops the objection in a ``finally`` even on
      failure -- so an exception raised by the scenario propagates out of
      ``uvm_root().run_test()`` promptly instead of hanging the run phase.
    * ``report_phase`` grades the plan pass criteria from the scoreboard's
      public counters (CONTRACT.md §10.1) and logs the assertion/coverage
      summaries.
    """

    #: True for every data-path scenario: the scoreboard must have graded at
    #: least one completed transaction or the test fails (guards against a
    #: silently-empty stimulus run).
    _require_graded_transactions = True

    def __init__(self, name: str = "aes128_test", parent=None) -> None:
        super().__init__(name, parent)
        self.env = None  # type: Aes128Env | None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Build the environment (agent + scoreboard + coverage + checks)."""
        super().build_phase()
        self.env = Aes128Env("aes128_env", self)
        self.logger.info("%s: Aes128Env created", self.get_name())

    async def run_phase(self) -> None:
        """Run the scenario under a run-phase objection.

        The objection makes ``uvm_root().run_test()`` wait for the whole
        scenario (including the final monitor-transaction drain) before the
        synchronous report phases execute.  The ``finally`` guarantees the
        objection is dropped when the scenario raises, so the failure
        propagates immediately to the enclosing cocotb test (no hang, no
        reliance on the watchdog for the failure itself).
        """
        self.raise_objection(f"{self.get_name()} scenario")
        try:
            await self._run_scenario()
        finally:
            self.drop_objection(f"{self.get_name()} scenario")

    # ------------------------------------------------------------------
    # Scenario selection (subclasses)
    # ------------------------------------------------------------------
    def get_sequence_class(self):
        """Return this test's stimulus sequence class (a class symbol).

        Required for every DIRECTED scenario test; ``report_phase``/the
        scenario-manifest validator enforce that it returns the exact
        sequence class named in ``generation_manifest.yaml``.
        """
        raise NotImplementedError(
            "directed scenario tests must override get_sequence_class()"
        )

    async def _run_scenario(self) -> None:
        """Default directed-scenario runner: start the mapped sequence and
        give the scoreboard a short drain window."""
        seq = self.get_sequence_class()()
        await seq.start(self.env.agent.sequencer)
        dut = _config_get("dut")
        if dut is not None:
            await ClockCycles(dut.clk, 4)  # drain final monitor transactions

    def report_phase(self) -> None:
        """Enforce the plan pass criteria from the scoreboard counters.

        Failures are raised as ``AssertionError`` (fails the test):

        * protocol/order/ungradable errors -- environment contract violations;
        * zero graded transactions for a data-path scenario;
        * ciphertext mismatches against the reference-model oracle.
        """
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            self.logger.error(
                "%s: TEST FAILED - no scoreboard was built", self.get_name()
            )
            raise AssertionError(
                f"{self.get_name()}: Aes128Env has no scoreboard (early crash?)"
            )
        results = sb.results()
        self.logger.info("SCOREBOARD: %s", sb.get_summary())
        if self.env.assertions is not None:
            self.logger.info("ASSERTIONS: %s", self.env.assertions.summarize())
        cov = coverage_summary_dict()
        self.logger.info(
            "COVERAGE: %d/%d bins covered (%.1f%% total)",
            cov["total_covered"], cov["total_size"], cov["total_percent"],
        )

        problems = []
        if results["mismatches"] > 0:
            problems.append(
                f"{results['mismatches']} ciphertext mismatch(es) against "
                "the reference-model oracle aes128_encrypt(plaintext, key) "
                "(out of %d completed transaction(s))" % results["transactions"]
            )
        if (results["protocol_errors"] > 0 or results["order_errors"] > 0
                or results["ungradable_errors"] > 0):
            problems.append(
                "scoreboard contract violations: "
                f"protocol_errors={results['protocol_errors']} "
                f"order_errors={results['order_errors']} "
                f"ungradable_errors={results['ungradable_errors']}"
            )
        if self._require_graded_transactions and results["transactions"] == 0:
            problems.append(
                "zero scoreboard-graded transactions (driver/sequence may "
                "have crashed before driving any stimulus)"
            )
        if problems:
            self.logger.error("TEST FAILED: %s", "; ".join(problems))
            raise AssertionError(
                f"{self.get_name()}: plan pass criteria violated: "
                f"{'; '.join(problems)}"
            )
        self.logger.info(
            "TEST PASSED: %s (%d completed transaction(s), all matching the "
            "reference model, %d non-ciphertext errors)",
            self.get_name(), results["transactions"], results["error_count"],
        )


# ---------------------------------------------------------------------------
# Directed scenario tests (one per plan directed_test_scenarios id; each
# class explicitly maps its scenario sequence via get_sequence_class())
# ---------------------------------------------------------------------------
class Aes128ResetReleaseIdleTest(Aes128TestBase):
    """TC01 reset_release_idle: reset release leaves the DUT idle and a
    transaction can be started afterwards."""

    def __init__(self, name: str = "Aes128ResetReleaseIdleTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return ResetReleaseIdleSeq


class Aes128Fips197KnownAnswerTest(Aes128TestBase):
    """TC02 fips197_known_answer: official FIPS-197 known-answer vector."""

    def __init__(self, name: str = "Aes128Fips197KnownAnswerTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return Fips197KnownAnswerSeq


class Aes128AllZeroKnownAnswerTest(Aes128TestBase):
    """TC03 all_zero_known_answer: all-zero key/plaintext known-answer."""

    def __init__(self, name: str = "Aes128AllZeroKnownAnswerTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return AllZeroKnownAnswerSeq


class Aes128IncrementingKnownAnswerTest(Aes128TestBase):
    """TC04 incrementing_known_answer: incrementing key/plaintext vector."""

    def __init__(self, name: str = "Aes128IncrementingKnownAnswerTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return IncrementingKnownAnswerSeq


class Aes128BackToBackTransactionsTest(Aes128TestBase):
    """TC05 back_to_back_transactions: two complete transactions in a row."""

    def __init__(self, name: str = "Aes128BackToBackTransactionsTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return BackToBackTransactionsSeq


class Aes128KeySensitivityTest(Aes128TestBase):
    """TC06 key_sensitivity: fixed plaintext, two keys, both results must
    match the reference model and differ from each other."""

    def __init__(self, name: str = "Aes128KeySensitivityTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return KeySensitivitySeq


class Aes128PlaintextSensitivityTest(Aes128TestBase):
    """TC07 plaintext_sensitivity: fixed key, two plaintexts, both results
    must match the reference model and differ from each other."""

    def __init__(self, name: str = "Aes128PlaintextSensitivityTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return PlaintextSensitivitySeq


class Aes128DeterminismRepeatedEncryptionTest(Aes128TestBase):
    """TC08 determinism_repeated_encryption: identical vector encrypted twice
    must yield identical reference-matching ciphertexts."""

    def __init__(self, name: str = "Aes128DeterminismRepeatedEncryptionTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return DeterminismRepeatedEncryptionSeq


class Aes128DonePulseAndStartIgnoredWhileBusyTest(Aes128TestBase):
    """TC09 done_pulse_and_start_ignored_while_busy: done pulses exactly one
    cycle and a start asserted mid-transaction is ignored."""

    def __init__(self, name: str = "Aes128DonePulseAndStartIgnoredWhileBusyTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    def get_sequence_class(self):
        return DonePulseAndStartIgnoredWhileBusySeq


# ---------------------------------------------------------------------------
# Directed registries + plan cross-checks (the manifest maps id -> test ->
# sequence; these guards catch plan drift at import time).
# ---------------------------------------------------------------------------
DIRECTED_TEST_CLASSES = (
    Aes128ResetReleaseIdleTest,
    Aes128Fips197KnownAnswerTest,
    Aes128AllZeroKnownAnswerTest,
    Aes128IncrementingKnownAnswerTest,
    Aes128BackToBackTransactionsTest,
    Aes128KeySensitivityTest,
    Aes128PlaintextSensitivityTest,
    Aes128DeterminismRepeatedEncryptionTest,
    Aes128DonePulseAndStartIgnoredWhileBusyTest,
)

DIRECTED_TEST_CLASSES_BY_ID = {
    "TC01": Aes128ResetReleaseIdleTest,
    "TC02": Aes128Fips197KnownAnswerTest,
    "TC03": Aes128AllZeroKnownAnswerTest,
    "TC04": Aes128IncrementingKnownAnswerTest,
    "TC05": Aes128BackToBackTransactionsTest,
    "TC06": Aes128KeySensitivityTest,
    "TC07": Aes128PlaintextSensitivityTest,
    "TC08": Aes128DeterminismRepeatedEncryptionTest,
    "TC09": Aes128DonePulseAndStartIgnoredWhileBusyTest,
}


def verify_directed_test_scenario_ids():
    """Check the plan -> test -> sequence id chain.

    The 9 directed test classes must cover the directed plan ids
    (``DIRECTED_SEQUENCES`` in sequences.py) exactly once, every test class
    must define ``get_sequence_class()`` *explicitly* (not inherit the base
    placeholder), and the returned symbol must be the exact sequence class
    whose ``SCENARIO_ID`` matches the plan id.
    """
    problems = []
    seq_by_id = dict(DIRECTED_SEQUENCES)
    for sid, test_cls in DIRECTED_TEST_CLASSES_BY_ID.items():
        if sid not in seq_by_id:
            problems.append(f"test {test_cls.__name__} maps plan id {sid!r} "
                            "that is not declared by any directed sequence")
            continue
        seq_cls = seq_by_id[sid]
        if "get_sequence_class" not in test_cls.__dict__:
            problems.append(
                f"{test_cls.__name__} must define get_sequence_class() "
                "explicitly"
            )
            continue
        # Probe the method with a dummy instance: the concrete bodies only
        # return the sequence class symbol, so this never instantiates a
        # uvm component at import time.
        returned = test_cls.get_sequence_class(None)
        if returned is not seq_cls:
            problems.append(
                f"{test_cls.__name__}.get_sequence_class() returned "
                f"{getattr(returned, '__name__', returned)!r}; expected "
                f"{seq_cls.__name__} (plan id {sid!r})"
            )
        if getattr(seq_cls, "SCENARIO_ID", None) != sid:
            problems.append(
                f"sequence {seq_cls.__name__} declares SCENARIO_ID "
                f"{getattr(seq_cls, 'SCENARIO_ID', None)!r}; expected {sid!r}"
            )
    declared_ids = set(DIRECTED_TEST_CLASSES_BY_ID)
    plan_ids = {sid for sid, _ in DIRECTED_SEQUENCES}
    if declared_ids != plan_ids:
        problems.append(
            "test-side directed ids do not match the sequence-side set: "
            f"tests={sorted(declared_ids)} sequences={sorted(plan_ids)}"
        )
    if problems:
        raise RuntimeError(
            "AES-128 tests vs plan/sequence mismatch: " + "; ".join(problems)
        )


# ---------------------------------------------------------------------------
# Corner-case aggregate test (plan ``corner_cases`` -- no SCENARIO_ID)
# ---------------------------------------------------------------------------
class Aes128CornerTest(Aes128TestBase):
    """Runs every corner-case sequence from the plan sequentially.

    All six corner scenarios complete at least one transaction against the
    reference model (``cc_reset_mid_transaction`` also verifies the
    in-flight abort and the fresh post-reset transaction), so the normal
    data-path grading applies.
    """

    def __init__(self, name: str = "Aes128CornerTest", parent=None) -> None:
        super().__init__(name, parent)

    async def _run_scenario(self) -> None:
        dut = _config_get("dut")
        for seq_cls in CORNER_SEQUENCES:
            self.logger.info("%s: starting %s", self.get_name(),
                             seq_cls.__name__)
            seq = seq_cls()
            await seq.start(self.env.agent.sequencer)
            if dut is not None:
                await ClockCycles(dut.clk, 2)  # drain between corners
        if dut is not None:
            await ClockCycles(dut.clk, 4)  # final drain


# ---------------------------------------------------------------------------
# Randomized test (plan ``randomized_testing_strategy`` -- no SCENARIO_ID)
# ---------------------------------------------------------------------------
#: Deterministic default seed for the randomized run (override with
#: ``AES128_RANDOM_SEED``; the sequence also honours ``RANDOM_SEED``).
DEFAULT_RANDOM_SEED = 0xA1E8  # hex "A1E8" ~ "AES"; 68,072 (reproducible)
DEFAULT_RANDOM_TRANSACTIONS = 41  # matches Aes128RandomizedSeq.num_txns


class Aes128RandomizedTest(Aes128TestBase):
    """Constrained-random full-space key/plaintext traffic
    (randomized_testing_strategy).

    Uses a deterministic RNG seed by default so failures are reproducible;
    export ``AES128_RANDOM_SEED=<int>`` (or ``RANDOM_SEED=<int>``, honoured
    by the sequence) to replay a specific run.
    """

    def __init__(self, name: str = "Aes128RandomizedTest", parent=None) -> None:
        super().__init__(name, parent)
        self._seq = None  # holds the started sequence for seed reporting

    async def _run_scenario(self) -> None:
        seq = Aes128RandomizedSeq()
        env_seed = os.environ.get("AES128_RANDOM_SEED")
        if env_seed is not None:
            try:
                seq.seed = int(env_seed)
            except ValueError:
                self.logger.warning(
                    "AES128_RANDOM_SEED=%r is not an integer; ignoring",
                    env_seed,
                )
        env_num = os.environ.get("AES128_NUM_RANDOM")
        if env_num is not None:
            try:
                seq.num_txns = int(env_num)
            except ValueError:
                self.logger.warning(
                    "AES128_NUM_RANDOM=%r is not an integer; ignoring",
                    env_num,
                )
        self._seq = seq
        self.logger.info(
            "%s: knobs - num_txns=%d seed=%s reset_every_n=%s",
            self.get_name(), seq.num_txns, seq.seed, seq.reset_every_n,
        )
        await seq.start(self.env.agent.sequencer)
        dut = _config_get("dut")
        if dut is not None:
            await ClockCycles(dut.clk, 8)  # drain final monitor transactions

    def report_phase(self) -> None:
        if getattr(self, "_seq", None) is not None:
            seed = getattr(self._seq, "_seed", None)
            if seed is not None:
                self.logger.info(
                    "Aes128RandomizedTest used RNG seed %d "
                    "(replay with AES128_RANDOM_SEED=%d)",
                    seed, seed,
                )
        super().report_phase()


# Import-time plan cross-check (fails loudly on plan drift).
verify_directed_test_scenario_ids()