"""i2c_master test classes (stage-6 TEST artifact).

One ``uvm_test`` subclass per directed verification-plan scenario
(``verification_plan.yaml`` ``directed_test_scenarios`` TC-01..TC-13), plus a
corner-case aggregate test and a constrained-random test -- exactly the 15
entries in ``generation_manifest.yaml`` ``test_classes``.

    directed (each with an explicit ``get_sequence_class()`` returning the
    stimulus sequence class SYMBOL, never a string):
        ResetIdleCheckTest           -> TC-01 reset_idle_check
        WriteBasicTest               -> TC-02 write_basic
        WriteZeroTest                -> TC-03 write_zero
        WriteMaxTest                 -> TC-04 write_max
        ReadBasicTest                -> TC-05 read_basic
        ReadMaxTest                  -> TC-06 read_max
        WriteAddrNackTest            -> TC-07 write_addr_nack
        WriteDataNackTest            -> TC-08 write_data_nack
        ReadAddrNackTest             -> TC-09 read_addr_nack
        StartWhileBusyTest           -> TC-10 start_while_busy
        ResetDuringTransactionTest   -> TC-11 reset_during_transaction
        DonePulseCheckTest           -> TC-12 done_pulse_check
        AddressMsbFirstCheckTest     -> TC-13 address_msb_first_check

    additional verification strategies (NO directed scenario id; their
    sequences carry ``SCENARIO_ID = None``, CONTRACT.md §10/§13.6):
        I2CCornerTest                -> all 14 plan corner-case sequences
        I2CRandomTest                -> randomized_testing_strategy

Each directed test selects its stimulus via ``get_sequence_class()`` (a class
symbol) so a static auditor -- this stage's consistency check,
``results/stage6_integration/stage6_consistency_checks.py`` -- can verify the
mapping against the plan without running the simulator.

GRADING SEMANTIC (locked, CONTRACT.md §8/§14/§15/§16):

* ``order_error_count``, ``hung_count``, ``intent_ungraded_count`` and
  ``error_count`` are REAL contract violations: ``report_phase`` fails the
  test when any is non-zero.  On the as-shipped corrupted RTL these are the
  *intended catch reports* -- ``done`` is permanently high (DIS-15) and the
  divider never advances (DIS-18/19), so every data-path transaction hangs
  (``I2CDriverTimeout``) and the scenario-level ``expect`` checks fail
  (``ScenarioCheckFailure``).  The tests therefore FAIL on the corrupted RTL
  exactly as the benchmark expects, and PASS only on a repaired variant.
* ``mismatch_count`` is a *catch report* (CONTRACT.md §15): it is logged but
  never fails a test by itself; the scoreboard's structured
  ``discrepancy_reports`` carry the per-defect details.
* The plan assertion checkers (launched by the env) fail the test fail-fast
  on the first violation (CONTRACT.md §16); their summary is logged in
  ``report_phase``.
* A per-test watchdog budget (CONTRACT.md §13.7/§17) is armed in
  ``run_phase`` and disarmed when the scenario completes;
  ``WATCHDOG_BUDGET_CYCLES`` defaults to ``WATCHDOG_MARGIN_CYCLES`` (10000)
  and is raised for the corner and randomized tests because those scenarios
  are longer.
"""

import os

from cocotb.triggers import ClockCycles

from pyuvm import ConfigDB, uvm_test

from i2c_coverage import (
    control_coverage_percentage,
    coverage_percentage,
    transaction_coverage_percentage,
)
from i2c_env import I2CEnv, WATCHDOG_MARGIN_CYCLES
from i2c_pins import KEY_DUT_PINS
from i2c_sequences import (
    AddressMsbFirstCheckSequence,
    CornerAddrMaxRead,
    CornerAddrMaxWrite,
    CornerAddrZeroWrite,
    CornerBackToBackTransactions,
    CornerClkDivMin,
    CornerDataMaxWrite,
    CornerDataZeroWrite,
    CornerMissingAddrAck,
    CornerMissingDataAck,
    CornerReleasedBusNoAck,
    CornerResetMidTransaction,
    CornerRxAllOnesRead,
    CornerRxAllZerosRead,
    CornerStartOneCycle,
    DonePulseCheckSequence,
    I2CRandomSequence,
    ReadAddrNackSequence,
    ReadBasicSequence,
    ReadMaxSequence,
    ResetDuringTransactionSequence,
    ResetIdleCheckSequence,
    StartWhileBusySequence,
    WriteAddrNackSequence,
    WriteBasicSequence,
    WriteDataNackSequence,
    WriteMaxSequence,
    WriteZeroSequence,
)

# All 14 plan corner-case sequences (verification_plan.yaml ``corner_cases``;
# none carries a directed scenario id, CONTRACT.md §10/§13.6).
I2C_CORNER_SEQUENCES = (
    CornerAddrZeroWrite,            # addr_zero_write
    CornerAddrMaxWrite,             # addr_max_write
    CornerAddrMaxRead,              # addr_max_read
    CornerDataZeroWrite,            # data_zero_write
    CornerDataMaxWrite,             # data_max_write
    CornerRxAllOnesRead,            # rx_all_ones_read
    CornerRxAllZerosRead,           # rx_all_zeros_read
    CornerMissingAddrAck,           # missing_addr_ack
    CornerMissingDataAck,           # missing_data_ack
    CornerStartOneCycle,            # start_one_cycle
    CornerBackToBackTransactions,   # back_to_back_transactions
    CornerResetMidTransaction,      # reset_mid_transaction
    CornerClkDivMin,                # clk_div_min
    CornerReleasedBusNoAck,         # released_bus_no_ack
)

# Randomized defaults (plan ``randomized_testing_strategy``): the number of
# generated transactions (I2CRandomSequence default), and a deterministic
# replay seed so failures are reproducible (override with I2C_SEED).
DEFAULT_RANDOM_TRANSACTIONS = 100
DEFAULT_RANDOM_SEED = 24601


# ---------------------------------------------------------------------------
# Base test
# ---------------------------------------------------------------------------
class I2CBaseTest(uvm_test):
    """Common base for every i2c_master test.

    * ``build_phase`` creates :class:`I2CEnv` (agent + scoreboard + coverage
      + assertion checkers, CONTRACT.md §16).
    * ``run_phase`` raises a run-phase objection, arms the per-test watchdog
      budget, runs ``_run_scenario()`` (subclass-specific), and disarms the
      watchdog before dropping the objection -- so pyuvm's ``run_test()``
      waits for the whole scenario before the report phases execute.
    * ``report_phase`` grades the plan pass/fail from the scoreboard's public
      counters (CONTRACT.md §15) and logs the coverage / assertion summaries.
    """

    #: Per-test watchdog budget in clock cycles (CONTRACT.md §13.7/§17).
    #: Must fit this test's longest legitimate scenario on a REPAIRED RTL;
    #: the corner and randomized tests override with larger bounds.
    WATCHDOG_BUDGET_CYCLES = WATCHDOG_MARGIN_CYCLES

    def __init__(self, name: str = "i2c_test", parent=None) -> None:
        super().__init__(name, parent)
        self.env = None  # type: I2CEnv
        # Whether the scenario must produce at least one scoreboard-graded
        # transaction to PASS (guards against a silently-empty run).  The
        # reset-only scenario TC-01 sets this to False.
        self._require_graded_transactions = True

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Build the environment (agent + scoreboard + coverage + checks)."""
        super().build_phase()
        self.env = I2CEnv("i2c_env", self)
        self.logger.info("%s: I2CEnv created", self.get_name())

    async def run_phase(self) -> None:
        """Run the scenario under a run-phase objection + watchdog budget."""
        self.raise_objection(f"{self.get_name()} scenario")
        self.env.arm_watchdog(self.WATCHDOG_BUDGET_CYCLES)
        try:
            await self._run_scenario()
        finally:
            self.env.disarm_watchdog()
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
        pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        await ClockCycles(pins.clk, 2)  # drain final monitor transactions

    def report_phase(self) -> None:
        """Enforce the plan pass criteria from the scoreboard counters.

        Fails (raising ``AssertionError``) for REAL contract violations:
        transaction-stream order errors, hung-transaction reports,
        intent-ungraded items, the aggregate ``error_count``, and (for
        data-path tests) an empty graded stream.  Digest mismatches are
        expected catch reports on this corrupted RTL and never fail a test
        by themselves (CONTRACT.md §14/§15); the assertion checkers already
        fail the test fail-fast on the first violation (§16).
        """
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            return  # guard against early-phase failures
        problems = self._scoreboard_failures(sb)
        # Coverage is reported/logged, never a pass/fail gate (CONTRACT.md
        # §16; the plan pass criteria treat assertion + scoreboard violations
        # as the pass/fail signal).
        self.logger.info(
            "COVERAGE: transaction=%.1f%% control=%.1f%% total=%.1f%%",
            transaction_coverage_percentage(),
            control_coverage_percentage(),
            coverage_percentage(),
        )
        self.logger.info(
            "ASSERTIONS: %s",
            self.env.assertions.summarize()
            if self.env.assertions is not None else "not launched",
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
        """Return the real contract violations observed by the scoreboard.

        On the as-shipped corrupted RTL these are the intended catch
        reports (CONTRACT.md §15 grading semantic): every data-path
        transaction hangs, so ``hung_count``/``error_count`` fail the test.
        """
        problems = []
        if sb.order_error_count > 0:
            problems.append(
                f"order errors={sb.order_error_count} (missing/duplicate/"
                "out-of-order completed transactions)"
            )
        if sb.hung_count > 0:
            problems.append(
                f"hung transactions={sb.hung_count} (a bounded wait "
                "elapsed; the DUT never completed/sampled this transaction)"
            )
        if sb.intent_ungraded_count > 0:
            problems.append(
                f"intent-ungraded transactions={sb.intent_ungraded_count} "
                "(alignment against the shared sampler could not be regained)"
            )
        if sb.error_count > 0:
            problems.append(
                f"scoreboard error_count={sb.error_count} (order+hung+"
                "ungraded+reference-rejected+non-I2CTransaction)"
            )
        if self._require_graded_transactions and sb.txn_count == 0:
            problems.append(
                "no scoreboard-graded transactions (driver/sequence may "
                "have crashed before driving any transaction)"
            )
        return problems


# ---------------------------------------------------------------------------
# Directed scenario tests (one per plan directed_test_scenarios id TC-01..
# TC-13; the consistency check keys DIRECTED_SCENARIO_TESTS by these ids)
# ---------------------------------------------------------------------------
class ResetIdleCheckTest(I2CBaseTest):
    """TC-01 reset_idle_check: reset clears all status outputs (idle)."""

    def __init__(self, name: str = "ResetIdleCheckTest",
                 parent=None) -> None:
        super().__init__(name, parent)
        # By design this scenario never starts a transaction, so an empty
        # scoreboard stream is a PASS, not a crash symptom.
        self._require_graded_transactions = False

    @staticmethod
    def get_sequence_class():
        return ResetIdleCheckSequence


class WriteBasicTest(I2CBaseTest):
    """TC-02 write_basic: write 0xA5 -> slave 0x50, slave ACK on both phases."""

    def __init__(self, name: str = "WriteBasicTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return WriteBasicSequence


class WriteZeroTest(I2CBaseTest):
    """TC-03 write_zero: write 0x00 -> slave 0x00 (address byte 0x00)."""

    def __init__(self, name: str = "WriteZeroTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return WriteZeroSequence


class WriteMaxTest(I2CBaseTest):
    """TC-04 write_max: write 0xFF -> slave 0x7F (address byte 0xFE)."""

    def __init__(self, name: str = "WriteMaxTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return WriteMaxSequence


class ReadBasicTest(I2CBaseTest):
    """TC-05 read_basic: read one byte (0x3C) from slave 0x50, master NACK."""

    def __init__(self, name: str = "ReadBasicTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return ReadBasicSequence


class ReadMaxTest(I2CBaseTest):
    """TC-06 read_max: read one byte (0xFF) from slave 0x2A."""

    def __init__(self, name: str = "ReadMaxTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return ReadMaxSequence


class WriteAddrNackTest(I2CBaseTest):
    """TC-07 write_addr_nack: slave NACKs the address; ack_error asserts."""

    def __init__(self, name: str = "WriteAddrNackTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return WriteAddrNackSequence


class WriteDataNackTest(I2CBaseTest):
    """TC-08 write_data_nack: address ACKed, write data NACKed; ack_error."""

    def __init__(self, name: str = "WriteDataNackTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return WriteDataNackSequence


class ReadAddrNackTest(I2CBaseTest):
    """TC-09 read_addr_nack: slave NACKs the address; ack_error asserts."""

    def __init__(self, name: str = "ReadAddrNackTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return ReadAddrNackSequence


class StartWhileBusyTest(I2CBaseTest):
    """TC-10 start_while_busy: a start while busy must be ignored."""

    def __init__(self, name: str = "StartWhileBusyTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return StartWhileBusySequence


class ResetDuringTransactionTest(I2CBaseTest):
    """TC-11 reset_during_transaction: reset mid-transaction clears state."""

    def __init__(self, name: str = "ResetDuringTransactionTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return ResetDuringTransactionSequence


class DonePulseCheckTest(I2CBaseTest):
    """TC-12 done_pulse_check: done is low in idle, pulses one cycle."""

    def __init__(self, name: str = "DonePulseCheckTest", parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return DonePulseCheckSequence


class AddressMsbFirstCheckTest(I2CBaseTest):
    """TC-13 address_msb_first_check: address byte transmitted MSB first."""

    def __init__(self, name: str = "AddressMsbFirstCheckTest",
                 parent=None) -> None:
        super().__init__(name, parent)

    @staticmethod
    def get_sequence_class():
        return AddressMsbFirstCheckSequence


# Registry keyed by the exact plan scenario id (TC-01..TC-13); used by the
# consistency check and by the generation_manifest.yaml ``scenarios`` mapping.
DIRECTED_SCENARIO_TESTS = {
    "TC-01": ResetIdleCheckTest,
    "TC-02": WriteBasicTest,
    "TC-03": WriteZeroTest,
    "TC-04": WriteMaxTest,
    "TC-05": ReadBasicTest,
    "TC-06": ReadMaxTest,
    "TC-07": WriteAddrNackTest,
    "TC-08": WriteDataNackTest,
    "TC-09": ReadAddrNackTest,
    "TC-10": StartWhileBusyTest,
    "TC-11": ResetDuringTransactionTest,
    "TC-12": DonePulseCheckTest,
    "TC-13": AddressMsbFirstCheckTest,
}


# ---------------------------------------------------------------------------
# Corner-case aggregate test (plan ``corner_cases`` -- no directed id)
# ---------------------------------------------------------------------------
class I2CCornerTest(I2CBaseTest):
    """Runs every plan corner-case sequence sequentially.

    On the as-shipped corrupted RTL the data-path corners hang
    (``I2CDriverTimeout``) and the control corners fail their
    ``expect_outputs`` checks -- the intended catch behavior.  On a repaired
    RTL all fourteen complete within the raised watchdog budget.
    """

    # 14 scenarios x (~100+-cycle margins plus the reset/offer preambles):
    # 6x the directed default so a legit corner run always fits.
    WATCHDOG_BUDGET_CYCLES = 6 * WATCHDOG_MARGIN_CYCLES

    def __init__(self, name: str = "I2CCornerTest", parent=None) -> None:
        super().__init__(name, parent)

    async def _run_scenario(self) -> None:
        pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        for seq_cls in I2C_CORNER_SEQUENCES:
            self.logger.info(
                "I2CCornerTest: starting %s", seq_cls.__name__
            )
            seq = seq_cls()
            await seq.start(self.env.agent.sequencer)
            # Brief drain so the scoreboard grades the previous corner's
            # transactions before the next sequence resets the DUT.
            await ClockCycles(pins.clk, 2)
        await ClockCycles(pins.clk, 2)  # final drain


# ---------------------------------------------------------------------------
# Randomized test (plan ``randomized_testing_strategy`` -- no directed id)
# ---------------------------------------------------------------------------
class I2CRandomTest(I2CBaseTest):
    """Constrained-random single-byte traffic (randomized_testing_strategy).

    ``I2CRandomSequence`` reads its knobs at ``body()`` time; the test fixes
    a deterministic default seed (``I2C_SEED``) and item count
    (``I2C_RANDOM_ITEMS``) via ``os.environ.setdefault`` so a failure is
    reproducible, while an explicit environment override still wins.
    """

    # 100 transactions x (completion margin + gaps + possible mid-flight
    # resets): generously 20x the directed default so a legit randomized run
    # always fits (both on a repaired RTL and here).
    WATCHDOG_BUDGET_CYCLES = 20 * WATCHDOG_MARGIN_CYCLES

    def __init__(self, name: str = "I2CRandomTest", parent=None) -> None:
        super().__init__(name, parent)
        self._seq = None  # holds the started sequence for seed reporting

    async def _run_scenario(self) -> None:
        # Deterministic replay by default; explicit env vars still win
        # (I2CRandomSequence reads them at body() time).
        os.environ.setdefault("I2C_SEED", str(DEFAULT_RANDOM_SEED))
        os.environ.setdefault("I2C_RANDOM_ITEMS", str(DEFAULT_RANDOM_TRANSACTIONS))
        seq = I2CRandomSequence()
        self._seq = seq
        await seq.start(self.env.agent.sequencer)
        pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        await ClockCycles(pins.clk, 5)  # drain final monitor transactions

    def report_phase(self) -> None:
        if getattr(self, "_seq", None) is not None:
            seed = os.environ.get("I2C_SEED")
            self.logger.info(
                "I2CRandomTest used I2C_SEED=%s (replay with I2C_SEED=%s)",
                seed, seed,
            )
        super().report_phase()