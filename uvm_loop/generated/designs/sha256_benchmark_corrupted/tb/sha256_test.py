"""SHA-256 test classes (stage-6 TEST artifact).

One ``uvm_test`` subclass per directed verification-plan scenario
(``verification_plan.yaml`` ``directed_test_scenarios``), plus a
corner-case aggregate test and a constrained-random test -- exactly the
``test_classes`` list in ``generation_manifest.yaml`` and the ``scenarios``
mapping recorded there.

    directed (each with an explicit ``get_sequence_class()`` returning the
    stimulus sequence class SYMBOL, never a string):
        Sha256ResetInitializationTest    -> reset_initialization
        Sha256EmptyMessageTest           -> empty_message
        Sha256SingleByteATest            -> single_byte_a
        Sha256AbcMessageTest             -> abc_message
        Sha256HelloWorldTest             -> hello_world
        Sha256QuickBrownFoxTest          -> quick_brown_fox
        Sha256BackToBackTransactionsTest -> back_to_back_transactions
        Sha256StartWhileBusyRestartsTest -> start_while_busy_restarts
        Sha256DoneBehaviorContinuousTest -> done_behavior_continuous

    additional verification strategies (NO ``SCENARIO_ID``, CONTRACT.md §9):
        Sha256CornerTest                 -> all six corner-case sequences
        Sha256RandomizedTest             -> randomized_testing_strategy

Each directed test selects its stimulus via ``get_sequence_class()`` (a
class symbol) so a static auditor -- this stage's consistency check,
``results/stage6_integration/stage6_consistency_checks.py`` -- can verify
the mapping against ``directed_test_scenarios`` without running the
simulator.

GRADING SEMANTIC (locked, CONTRACT.md §8/§14/§15):

* ``order_error_count`` and ``invalid_block_count`` (for tests that drive
  only canonically padded blocks) are REAL contract violations: ``report_phase``
  fails the test when they are non-zero.
* ``mismatch_count`` is an EXPECTED *catch report* on this corrupted RTL
  (DISC-001..DISC-017) and never fails a test by itself: the scoreboard's
  digest reports (transaction id, block, expected/actual digest, cycle) are
  logged (CONTRACT.md §14), and the structural
  ``transaction_completes_within_latency`` checker (started by the env)
  fails the test fail-fast ~72 cycles after the first start (CONTRACT.md
  §15).
* A per-test watchdog budget (CONTRACT.md §7) is armed in ``run_phase`` and
  disarmed when the scenario completes; ``WATCHDOG_BUDGET_CYCLES`` defaults
  to ``WATCHDOG_MARGIN_CYCLES`` (500) and is raised for the corner and
  randomized tests because those scenarios are longer.
"""

import os

from cocotb.triggers import ClockCycles

from pyuvm import ConfigDB, uvm_test

from sha256_coverage import coverage_summary_dict
from sha256_env import Sha256Env
from sha256_pins import WATCHDOG_MARGIN_CYCLES
from sha256_sequences import (
    Sha256AbcMessageSequence,
    Sha256BackToBackTransactionsSequence,
    Sha256BlockAllOnesSequence,
    Sha256BlockAlternatingPatternSequence,
    Sha256BlockChangesDuringProcessingSequence,
    Sha256DoneBehaviorContinuousSequence,
    Sha256EmptyMessageSequence,
    Sha256HelloWorldSequence,
    Sha256MaximumMessageLengthSequence,
    Sha256QuickBrownFoxSequence,
    Sha256RandomizedSequence,
    Sha256ResetDuringProcessingSequence,
    Sha256ResetInitializationSequence,
    Sha256SingleByteASequence,
    Sha256StartDeassertedSameCycleSequence,
    Sha256StartWhileBusyRestartsSequence,
)

# All six corner-case sequences (plan ``corner_cases``; no SCENARIO_ID).
SHA256_CORNER_SEQUENCES = (
    Sha256MaximumMessageLengthSequence,
    Sha256StartDeassertedSameCycleSequence,
    Sha256BlockAllOnesSequence,
    Sha256BlockAlternatingPatternSequence,
    Sha256ResetDuringProcessingSequence,
    Sha256BlockChangesDuringProcessingSequence,
)

# Randomized defaults: the plan (``randomized_testing_strategy``) fixes the
# message-length (0..55) and message-byte (0..255) ranges; the seed is
# deterministic so failures are reproducible (override with RANDOM_SEED).
DEFAULT_RANDOM_TRANSACTIONS = 20
DEFAULT_RANDOM_SEED = 24601


# ---------------------------------------------------------------------------
# Base test
# ---------------------------------------------------------------------------
class Sha256BaseTest(uvm_test):
    """Common base for every SHA-256 test.

    * ``build_phase`` creates :class:`Sha256Env` (agent + scoreboard +
      coverage + assertion checkers, CONTRACT.md §15).
    * ``run_phase`` raises a run-phase objection, starts the per-test
      watchdog budget, runs ``_run_scenario()`` (subclass-specific), and
      disarms the watchdog before dropping the objection -- so pyuvm's
      ``run_test()`` waits for the whole scenario before the synchronous
      report phases execute.
    * ``report_phase`` grades the plan pass/fail from the scoreboard's public
      counters (CONTRACT.md §14) plus the structural assertion counter.
    """

    #: Watchdog budget in clock cycles (CONTRACT.md §7).  Must fit this
    #: test's longest legitimate scenario on a REPAIRED RTL; the directed
    #: KAT scenarios fit in WATCHDOG_MARGIN_CYCLES (500); the corner and
    #: randomized tests override with larger bounds.
    WATCHDOG_BUDGET_CYCLES = WATCHDOG_MARGIN_CYCLES

    def __init__(self, name: str = "sha256_test", parent=None) -> None:
        super().__init__(name, parent)
        self.env = None  # type: Sha256Env
        # Whether the scenario must produce at least one scoreboard-graded
        # transaction to PASS (guards against a silently-empty run).  The
        # dedicated reset-only test sets this to False.
        self._require_graded_transactions = True
        # Whether non-canonical raw blocks are an EXPECTED part of the
        # scenario (the corner test drives all-ones / alternating blocks
        # that the golden reference rejects by design).
        self._allow_invalid_blocks = False

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Build the environment (agent + scoreboard + coverage + checks)."""
        super().build_phase()
        self.env = Sha256Env("sha256_env", self)
        self.logger.info("%s: Sha256Env created", self.get_name())

    async def run_phase(self) -> None:
        """Run the scenario under a run-phase objection + watchdog budget."""
        self.raise_objection(f"{self.get_name()} scenario")
        self.env.assertions.start_watchdog(self.WATCHDOG_BUDGET_CYCLES)
        try:
            await self._run_scenario()
        finally:
            self.env.assertions.disarm_watchdog()
            self.drop_objection(f"{self.get_name()} scenario")

    # ------------------------------------------------------------------
    # Scenario selection (subclasses)
    # ------------------------------------------------------------------
    @staticmethod
    def get_sequence_class():
        """Return this test's stimulus sequence class (a class symbol).

        Required for every DIRECTED scenario test (the consistency check
        enforces it); corner/randomized tests override ``_run_scenario``
        directly.
        """
        raise NotImplementedError(
            "directed scenario tests must override get_sequence_class()"
        )

    async def _run_scenario(self) -> None:
        """Default directed-scenario runner: start the mapped sequence and
        give the scoreboard a brief drain window.

        ``get_sequence_class()`` returns the class symbol -- this is the
        single wiring point audited by the stage-6 consistency check.
        """
        seq = self.get_sequence_class()()
        await seq.start(self.env.agent.sequencer)
        pins = ConfigDB().get(None, "", "sha256_pins")
        await ClockCycles(pins.clk, 2)  # drain final monitor transactions

    def report_phase(self) -> None:
        """Enforce the plan pass criteria from the scoreboard counters.

        Raises (failing the test) only for REAL contract violations:
        transaction-stream order errors, unexpected invalid blocks, and
        (for data-path tests) an empty graded stream.  Digest mismatches
        are expected catch reports on this corrupted RTL and never fail a
        test by themselves (CONTRACT.md §8/§14).
        """
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            return  # guard against early-phase failures
        problems = self._scoreboard_failures(sb)
        # The structural checkers (started by the env) fail the test
        # directly on the first violation (CONTRACT.md §15); report how
        # many checker coroutines watched this run.
        self.logger.info(
            "ASSERTIONS: %d structural checker coroutine(s) active",
            len(self.env.assertions.tasks),
        )
        cov = coverage_summary_dict()
        self.logger.info(
            "COVERAGE: %d/%d bins covered (%.1f%% total)",
            cov["total_covered"], cov["total_size"], cov["total_percent"],
        )
        self.logger.info("SCOREBOARD: %s", sb.get_summary())
        if problems:
            self.logger.error("TEST FAILED: %s", "; ".join(problems))
            raise AssertionError(
                f"{self.get_name()}: scoreboard contract violations: "
                f"{'; '.join(problems)}"
            )
        self.logger.info(
            "TEST PASSED: scoreboard clean (%d txns graded, %d match, "
            "%d mismatch 'catch reports')",
            sb.txn_count, sb.match_count, sb.mismatch_count,
        )

    # ------------------------------------------------------------------
    # Grading helpers
    # ------------------------------------------------------------------
    def _scoreboard_failures(self, sb) -> list:
        """Return the real contract violations observed by the scoreboard."""
        problems = []
        if sb.order_error_count > 0:
            problems.append(
                f"order errors={sb.order_error_count} (missing/duplicate/"
                "out-of-order completed transactions)"
            )
        if not self._allow_invalid_blocks and sb.invalid_block_count > 0:
            problems.append(f"invalid blocks={sb.invalid_block_count}")
        if self._require_graded_transactions and sb.txn_count == 0:
            problems.append(
                "no scoreboard-graded transactions (driver/sequence may "
                "have crashed before driving any block)"
            )
        return problems


# ---------------------------------------------------------------------------
# Directed scenario tests (one per plan directed_test_scenarios id)
# ---------------------------------------------------------------------------
class Sha256ResetInitializationTest(Sha256BaseTest):
    """reset_initialization: verify the RTL reset state.

    The sequence holds reset and returns to idle without driving any
    transaction; this test additionally samples the DUT outputs and checks
    the plan's expected reset values (done=1 per DISC-001, digest=0).
    """

    def __init__(self, name: str = "Sha256ResetInitializationTest",
                 parent=None) -> None:
        super().__init__(name, parent)
        # By design this scenario never starts a transaction, so an empty
        # scoreboard stream is a PASS, not a crash symptom.
        self._require_graded_transactions = False

    @staticmethod
    def get_sequence_class():
        return Sha256ResetInitializationSequence

    async def _run_scenario(self) -> None:
        pins = ConfigDB().get(None, "", "sha256_pins")
        seq = self.get_sequence_class()()
        await seq.start(self.env.agent.sequencer)
        await ClockCycles(pins.clk, 1)
        done = pins.read_done()
        digest = pins.read_digest()
        if done != 1 or digest != 0:
            raise AssertionError(
                "reset_initialization failed: after reset expected "
                f"done=1 digest=0 (plan reset values), observed "
                f"done={done} digest=0x{digest:064x}"
            )
        self.logger.info(
            "reset_initialization: reset state OK (done=1, digest=0)"
        )
        await ClockCycles(pins.clk, 1)


class Sha256EmptyMessageTest(Sha256BaseTest):
    """empty_message: known-answer test for the empty string."""

    def __init__(self, name: str = "Sha256EmptyMessageTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256EmptyMessageSequence


class Sha256SingleByteATest(Sha256BaseTest):
    """single_byte_a: known-answer test for the 1-byte message ``"a"``."""

    def __init__(self, name: str = "Sha256SingleByteATest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256SingleByteASequence


class Sha256AbcMessageTest(Sha256BaseTest):
    """abc_message: FIPS 180-4 known-answer test for ``"abc"``."""

    def __init__(self, name: str = "Sha256AbcMessageTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256AbcMessageSequence


class Sha256HelloWorldTest(Sha256BaseTest):
    """hello_world: known-answer test for ``"hello world"``."""

    def __init__(self, name: str = "Sha256HelloWorldTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256HelloWorldSequence


class Sha256QuickBrownFoxTest(Sha256BaseTest):
    """quick_brown_fox: known-answer test for the 43-byte pangram."""

    def __init__(self, name: str = "Sha256QuickBrownFoxTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256QuickBrownFoxSequence


class Sha256BackToBackTransactionsTest(Sha256BaseTest):
    """back_to_back_transactions: two independent digests in sequence."""

    def __init__(self, name: str = "Sha256BackToBackTransactionsTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256BackToBackTransactionsSequence


class Sha256StartWhileBusyRestartsTest(Sha256BaseTest):
    """start_while_busy_restarts: a start while busy restarts the run."""

    def __init__(self, name: str = "Sha256StartWhileBusyRestartsTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256StartWhileBusyRestartsSequence


class Sha256DoneBehaviorContinuousTest(Sha256BaseTest):
    """done_behavior_continuous: done stays 1 continuously (DISC-001)."""

    def __init__(self, name: str = "Sha256DoneBehaviorContinuousTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return Sha256DoneBehaviorContinuousSequence


# Registry keyed by exact plan scenario id (used by the consistency check
# and by the generation_manifest.yaml ``scenarios`` mapping).
DIRECTED_SCENARIO_TESTS = {
    "reset_initialization": Sha256ResetInitializationTest,
    "empty_message": Sha256EmptyMessageTest,
    "single_byte_a": Sha256SingleByteATest,
    "abc_message": Sha256AbcMessageTest,
    "hello_world": Sha256HelloWorldTest,
    "quick_brown_fox": Sha256QuickBrownFoxTest,
    "back_to_back_transactions": Sha256BackToBackTransactionsTest,
    "start_while_busy_restarts": Sha256StartWhileBusyRestartsTest,
    "done_behavior_continuous": Sha256DoneBehaviorContinuousTest,
}


# ---------------------------------------------------------------------------
# Corner-case aggregate test (plan ``corner_cases`` -- no SCENARIO_ID)
# ---------------------------------------------------------------------------
class Sha256CornerTest(Sha256BaseTest):
    """Runs every corner-case sequence from the plan sequentially.

    Two of the six corner sequences intentionally drive raw 512-bit blocks
    (all-ones / alternating) that the golden reference model rejects, so
    ``invalid_block_count > 0`` is EXPECTED here and does not fail the
    test (``_allow_invalid_blocks = True``).
    """

    # 6 scenarios x (~78 cycles + drain) plus preamble: 2x the directed
    # default so a legit corner run always fits.
    WATCHDOG_BUDGET_CYCLES = 2 * WATCHDOG_MARGIN_CYCLES

    def __init__(self, name: str = "Sha256CornerTest",
                 parent=None) -> None:
        super().__init__(name, parent)
        self._allow_invalid_blocks = True

    async def _run_scenario(self) -> None:
        pins = ConfigDB().get(None, "", "sha256_pins")
        for seq_cls in SHA256_CORNER_SEQUENCES:
            self.logger.info("Sha256CornerTest: starting %s", seq_cls.__name__)
            seq = seq_cls()
            await seq.start(self.env.agent.sequencer)
            # Brief drain so the scoreboard grades the previous corner's
            # transactions before the next sequence resets the DUT.
            await ClockCycles(pins.clk, 2)
        await ClockCycles(pins.clk, 2)  # final drain


# ---------------------------------------------------------------------------
# Randomized test (plan ``randomized_testing_strategy`` -- no SCENARIO_ID)
# ---------------------------------------------------------------------------
class Sha256RandomizedTest(Sha256BaseTest):
    """Constrained-random single-block traffic (randomized_testing_strategy).

    Uses a deterministic RNG seed by default so failures are reproducible;
    export ``RANDOM_SEED=<int>`` to replay a specific run.
    """

    # 20 transactions x (70-cycle completion margin + gaps + possible
    # mid-flight resets): generously 8x the directed default so a legit
    # randomized run always fits (both on a repaired RTL and here).
    WATCHDOG_BUDGET_CYCLES = 8 * WATCHDOG_MARGIN_CYCLES

    def __init__(self, name: str = "Sha256RandomizedTest",
                 parent=None) -> None:
        super().__init__(name, parent)
        self._seq = None  # holds the started sequence for seed reporting

    async def _run_scenario(self) -> None:
        env_seed = os.environ.get("RANDOM_SEED")
        seed = int(env_seed) if env_seed is not None else DEFAULT_RANDOM_SEED
        seq = Sha256RandomizedSequence(
            num_transactions=DEFAULT_RANDOM_TRANSACTIONS,
            seed=seed,
        )
        self._seq = seq
        await seq.start(self.env.agent.sequencer)
        pins = ConfigDB().get(None, "", "sha256_pins")
        await ClockCycles(pins.clk, 5)  # drain final monitor transactions

    def report_phase(self) -> None:
        if getattr(self, "_seq", None) is not None and self._seq.seed is not None:
            self.logger.info(
                "Sha256RandomizedTest used RNG seed %d "
                "(replay with RANDOM_SEED=%d)",
                self._seq.seed, self._seq.seed,
            )
        super().report_phase()