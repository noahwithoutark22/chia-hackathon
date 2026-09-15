"""Stage 6 (integration) artifact of the CHIA generator: the pyuvm tests.

This module defines the complete test layer for the i2c_master bench.  All
class names here are the exact ``UVM_TESTNAME`` values listed in
``generation_manifest.yaml`` and selectable through the Makefile::

    I2C01ResetBehaviorTest      .. I2C14BackToBackTest  (directed scenarios,
                                                        one per plan id)
    I2CCornerCaseTest                                   (all corner cases)
    I2CRandomizedTest                                   (constrained-random)

Every test is a ``uvm_test`` subclass of :class:`I2CTestBase`:

* ``build_phase``  -- creates :class:`~tb.env.I2CEnv` (agent + scoreboard +
  coverage + assertion checkers);
* ``run_phase``    -- raises a run-phase objection, starts the stimulus
  ``uvm_sequence`` on ``env.agent.sequencer``, and drops the objection;
* ``report_phase`` -- enforces pass/fail: zero scoreboard failures and the
  minimum exercised-transaction guard required for the scenario.

Consistency guards run at import time: :func:`verify_directed_scenario_ids`
(from tb/sequences.py) already checks the *sequence* side against the plan;
:func:`verify_directed_test_scenario_ids` here checks the *test* side and
cross-checks the test -> sequence pairing (every directed test's
``SEQUENCE_CLASS`` must implement the same plan ``SCENARIO_ID``).
"""

import os

from cocotb.triggers import ClockCycles
from pyuvm import ConfigDB, uvm_test

from tb.dut_helper import KEY_DUT
from tb.env import I2CEnv
from tb.sequences import (
    CORNER_CASE_SEQUENCE_CLASSES,
    I2CRandomizedSequence,
    PLAN_DIRECTED_IDS,
    BackToBackSeq,
    BoundaryAddr00Seq,
    BoundaryAddrFFSeq,
    DonePulseWidthSeq,
    MultiRegIndependenceSeq,
    OpenDrainBusReleaseSeq,
    ReadBeforeWriteSeq,
    RepeatedWritesSeq,
    ResetBehaviorSeq,
    StartWhileBusySeq,
    UnsupportedSlave00Seq,
    UnsupportedSlave01Seq,
    UnsupportedSlave7FSeq,
    WriteThenReadBackSeq,
    verify_directed_scenario_ids,
)

__all__ = [
    "I2CTestBase",
    "I2C01ResetBehaviorTest",
    "I2C02WriteThenReadBackTest",
    "I2C03ReadBeforeWriteTest",
    "I2C04RepeatedWritesTest",
    "I2C05BoundaryAddr00Test",
    "I2C06BoundaryAddrFFTest",
    "I2C07UnsupportedSlave00Test",
    "I2C08UnsupportedSlave01Test",
    "I2C09UnsupportedSlave7FTest",
    "I2C10StartWhileBusyTest",
    "I2C11DonePulseWidthTest",
    "I2C12OpenDrainBusReleaseTest",
    "I2C13MultiRegIndependenceTest",
    "I2C14BackToBackTest",
    "I2CCornerCaseTest",
    "I2CRandomizedTest",
    "DIRECTED_TEST_CLASSES",
    "verify_directed_test_scenario_ids",
]


class I2CTestBase(uvm_test):
    """Base test: builds the environment and enforces the pass criteria.

    Class attributes overridden by the concrete tests:

    * ``SCENARIO_ID``       -- plan id for directed tests (``None`` for the
      corner/randomized strategies).
    * ``SEQUENCE_CLASS``    -- the stimulus ``uvm_sequence`` to start.
    * ``REQUIRES_TRANSACTIONS`` -- if True (every data-path test), the
      scoreboard must have scored at least one completed transaction,
      otherwise the test fails (a test whose driver/sequence crashed before
      any stimulus must not silently pass).
    """

    SCENARIO_ID = None
    SEQUENCE_CLASS = None
    REQUIRES_TRANSACTIONS = True

    #: Randomized-test knobs (overridable via environment variables).
    NUM_RANDOM_TRANSACTIONS = 60
    RESET_INJECTION_PROBABILITY = 0.05

    def __init__(self, name="i2c_test", parent=None):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        super().build_phase()
        self.env = I2CEnv("i2c_env", self)
        self.logger.info("%s: I2CEnv created", self.get_name())

    async def run_phase(self):
        """Run the stimulus scenario under a run-phase objection.

        pyuvm's ``uvm_root().run_test()`` waits for the run-phase objection
        to be dropped and only then runs the synchronous report phases, so
        raising the objection guarantees the scenario (and the final monitor
        transaction drain) completes before ``report_phase`` evaluates the
        pass criteria.
        """
        self.raise_objection()
        try:
            await self._run_scenario()
        finally:
            self.drop_objection()

    async def _run_scenario(self):
        """Stimulus entry point; concrete tests override/use this default.

        The default starts ``self.SEQUENCE_CLASS`` (directed tests) on the
        agent's sequencer and lets the scoreboard drain the tail.
        """
        if self.SEQUENCE_CLASS is None:
            self.logger.warning(
                "%s._run_scenario(): no SEQUENCE_CLASS defined, "
                "no stimulus applied", self.get_name())
            return
        await self._run_single_sequence(self.SEQUENCE_CLASS)

    async def _run_single_sequence(self, seq_class, drain_cycles=2):
        """Start *seq_class* and wait a few cycles for the scoreboard to
        process the remaining monitor transactions."""
        seq = seq_class()
        await seq.start(self.env.agent.sequencer)
        dut = ConfigDB().get(self, "", KEY_DUT)
        await ClockCycles(dut.clk, drain_cycles)

    def report_phase(self):
        """Enforce pass/fail: zero scoreboard failures and (for data-path
        tests) at least one scored transaction."""
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            self.logger.error("%s: TEST FAILED - no scoreboard was built",
                              self.get_name())
            raise AssertionError("I2C env has no scoreboard (early crash?)")

        if sb.failed_count > 0:
            self.logger.error(
                "%s: TEST FAILED - %d scoreboard failure(s) across %d items "
                "(%d reset(s) observed)",
                self.get_name(), sb.failed_count, sb.item_count,
                sb.reset_count)
            raise AssertionError(
                f"I2CScoreboard reported {sb.failed_count} comparison "
                f"failure(s)")

        if self.REQUIRES_TRANSACTIONS and sb.item_count == 0:
            self.logger.error(
                "%s: TEST FAILED - zero completed transactions scored "
                "(driver/sequence may have crashed before exercising any "
                "stimulus)", self.get_name())
            raise AssertionError(
                "I2CScoreboard scored 0 items - no stimulus was exercised")

        self.logger.info(
            "TEST PASSED: %s (%s): %d completed transactions matched the "
            "reference model, 0 failures, %d reset(s) observed",
            self.get_name(), self.SCENARIO_ID, sb.item_count, sb.reset_count)


# ---------------------------------------------------------------------------
# Directed scenario tests (plan directed_test_scenarios I2C_01 .. I2C_14)
# ---------------------------------------------------------------------------
class I2C01ResetBehaviorTest(I2CTestBase):
    """I2C_01: Reset Behavior (reset-only by design: no transactions)."""

    SCENARIO_ID = "I2C_01"
    SEQUENCE_CLASS = ResetBehaviorSeq
    REQUIRES_TRANSACTIONS = False  # reset/deassert path only, by plan

    def __init__(self, name="I2C01ResetBehaviorTest", parent=None):
        super().__init__(name, parent)


class I2C02WriteThenReadBackTest(I2CTestBase):
    """I2C_02: Write Then Read Back."""

    SCENARIO_ID = "I2C_02"
    SEQUENCE_CLASS = WriteThenReadBackSeq

    def __init__(self, name="I2C02WriteThenReadBackTest", parent=None):
        super().__init__(name, parent)


class I2C03ReadBeforeWriteTest(I2CTestBase):
    """I2C_03: Read Before Write Returns Zero."""

    SCENARIO_ID = "I2C_03"
    SEQUENCE_CLASS = ReadBeforeWriteSeq

    def __init__(self, name="I2C03ReadBeforeWriteTest", parent=None):
        super().__init__(name, parent)


class I2C04RepeatedWritesTest(I2CTestBase):
    """I2C_04: Repeated Writes to Same Register."""

    SCENARIO_ID = "I2C_04"
    SEQUENCE_CLASS = RepeatedWritesSeq

    def __init__(self, name="I2C04RepeatedWritesTest", parent=None):
        super().__init__(name, parent)


class I2C05BoundaryAddr00Test(I2CTestBase):
    """I2C_05: Boundary Register Address 0x00."""

    SCENARIO_ID = "I2C_05"
    SEQUENCE_CLASS = BoundaryAddr00Seq

    def __init__(self, name="I2C05BoundaryAddr00Test", parent=None):
        super().__init__(name, parent)


class I2C06BoundaryAddrFFTest(I2CTestBase):
    """I2C_06: Boundary Register Address 0xFF."""

    SCENARIO_ID = "I2C_06"
    SEQUENCE_CLASS = BoundaryAddrFFSeq

    def __init__(self, name="I2C06BoundaryAddrFFTest", parent=None):
        super().__init__(name, parent)


class I2C07UnsupportedSlave00Test(I2CTestBase):
    """I2C_07: Unsupported Slave Address 0x00."""

    SCENARIO_ID = "I2C_07"
    SEQUENCE_CLASS = UnsupportedSlave00Seq

    def __init__(self, name="I2C07UnsupportedSlave00Test", parent=None):
        super().__init__(name, parent)


class I2C08UnsupportedSlave01Test(I2CTestBase):
    """I2C_08: Unsupported Slave Address 0x01."""

    SCENARIO_ID = "I2C_08"
    SEQUENCE_CLASS = UnsupportedSlave01Seq

    def __init__(self, name="I2C08UnsupportedSlave01Test", parent=None):
        super().__init__(name, parent)


class I2C09UnsupportedSlave7FTest(I2CTestBase):
    """I2C_09: Unsupported Slave Address 0x7F."""

    SCENARIO_ID = "I2C_09"
    SEQUENCE_CLASS = UnsupportedSlave7FSeq

    def __init__(self, name="I2C09UnsupportedSlave7FTest", parent=None):
        super().__init__(name, parent)


class I2C10StartWhileBusyTest(I2CTestBase):
    """I2C_10: Start While Busy Is Ignored."""

    SCENARIO_ID = "I2C_10"
    SEQUENCE_CLASS = StartWhileBusySeq

    def __init__(self, name="I2C10StartWhileBusyTest", parent=None):
        super().__init__(name, parent)


class I2C11DonePulseWidthTest(I2CTestBase):
    """I2C_11: Done Pulse Width."""

    SCENARIO_ID = "I2C_11"
    SEQUENCE_CLASS = DonePulseWidthSeq

    def __init__(self, name="I2C11DonePulseWidthTest", parent=None):
        super().__init__(name, parent)


class I2C12OpenDrainBusReleaseTest(I2CTestBase):
    """I2C_12: Open-Drain Bus Release."""

    SCENARIO_ID = "I2C_12"
    SEQUENCE_CLASS = OpenDrainBusReleaseSeq

    def __init__(self, name="I2C12OpenDrainBusReleaseTest", parent=None):
        super().__init__(name, parent)


class I2C13MultiRegIndependenceTest(I2CTestBase):
    """I2C_13: Multi-Register Independence."""

    SCENARIO_ID = "I2C_13"
    SEQUENCE_CLASS = MultiRegIndependenceSeq

    def __init__(self, name="I2C13MultiRegIndependenceTest", parent=None):
        super().__init__(name, parent)


class I2C14BackToBackTest(I2CTestBase):
    """I2C_14: Back-to-Back Transactions."""

    SCENARIO_ID = "I2C_14"
    SEQUENCE_CLASS = BackToBackSeq

    def __init__(self, name="I2C14BackToBackTest", parent=None):
        super().__init__(name, parent)


# ---------------------------------------------------------------------------
# Corner-case aggregate test (plan corner_cases; no SCENARIO_ID, by design)
# ---------------------------------------------------------------------------
class I2CCornerCaseTest(I2CTestBase):
    """Runs every corner-case sequence from the plan sequentially.

    Corner-case sequences intentionally carry no ``SCENARIO_ID`` (they form
    a separate verification strategy); they are collected in
    ``CORNER_CASE_SEQUENCE_CLASSES`` (tb/sequences.py).  Each corner starts
    with its own reset, so the reference model (cleared in lockstep with the
    DUT by the scoreboard's reset watcher) matches every expectation.
    """

    SCENARIO_ID = None
    SEQUENCE_CLASS = None

    def __init__(self, name="I2CCornerCaseTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        dut = ConfigDB().get(self, "", KEY_DUT)
        for seq_cls in CORNER_CASE_SEQUENCE_CLASSES:
            await self._run_single_sequence(seq_cls, drain_cycles=2)
        # Final drain after the last corner sequence.
        await ClockCycles(dut.clk, 2)


# ---------------------------------------------------------------------------
# Randomized test (plan randomized_testing_strategy)
# ---------------------------------------------------------------------------
class I2CRandomizedTest(I2CTestBase):
    """Runs the constrained-random stimulus sequence.

    ``I2CRandomizedSequence`` drives back-to-back randomized write/read
    transactions with rare mid-flight reset injection and self-scores every
    transaction against the reference model (so a mismatch fails the test at
    the sequence level before the scoreboard even sees the item).

    The RNG seed defaults to ``None`` (time-seeded); set the ``I2C_SEED``
    environment variable to an integer to replay a failing run.
    """

    SCENARIO_ID = None
    SEQUENCE_CLASS = None

    def __init__(self, name="I2CRandomizedTest", parent=None):
        super().__init__(name, parent)
        self._seq = None  # holds the started sequence for seed reporting

    async def _run_scenario(self):
        raw_seed = os.environ.get("I2C_SEED")
        seed = int(raw_seed) if raw_seed is not None else None
        seq = I2CRandomizedSequence(
            num_transactions=self.NUM_RANDOM_TRANSACTIONS,
            reset_injection_probability=self.RESET_INJECTION_PROBABILITY,
            seed=seed)
        self._seq = seq
        await seq.start(self.env.agent.sequencer)
        dut = ConfigDB().get(self, "", KEY_DUT)
        await ClockCycles(dut.clk, 5)  # let the scoreboard drain the tail

    def report_phase(self):
        seq_seed = getattr(self._seq, "seed", None) if self._seq else None
        if seq_seed is not None:
            self.logger.info(
                "I2CRandomizedTest used RNG seed %r (replay with I2C_SEED=%s)",
                seq_seed, seq_seed)
        super().report_phase()


# ---------------------------------------------------------------------------
# Registry + scenario-id verification (mirrors tb/sequences.py).
# ---------------------------------------------------------------------------
DIRECTED_TEST_CLASSES = [
    I2C01ResetBehaviorTest,          # I2C_01
    I2C02WriteThenReadBackTest,      # I2C_02
    I2C03ReadBeforeWriteTest,        # I2C_03
    I2C04RepeatedWritesTest,         # I2C_04
    I2C05BoundaryAddr00Test,         # I2C_05
    I2C06BoundaryAddrFFTest,         # I2C_06
    I2C07UnsupportedSlave00Test,     # I2C_07
    I2C08UnsupportedSlave01Test,     # I2C_08
    I2C09UnsupportedSlave7FTest,     # I2C_09
    I2C10StartWhileBusyTest,         # I2C_10
    I2C11DonePulseWidthTest,         # I2C_11
    I2C12OpenDrainBusReleaseTest,    # I2C_12
    I2C13MultiRegIndependenceTest,   # I2C_13
    I2C14BackToBackTest,             # I2C_14
]


def verify_directed_test_scenario_ids():
    """Return {plan id -> test class}; raise if the test layer drifts from
    the plan or from the sequence layer.

    Cross-checks both registries: the sequence class a test starts must
    implement exactly the same ``SCENARIO_ID`` as its test.
    """
    seq_by_id = verify_directed_scenario_ids()
    seen = {}
    for cls in DIRECTED_TEST_CLASSES:
        sid = getattr(cls, "SCENARIO_ID", None)
        if sid is None:
            raise AssertionError(
                f"{cls.__name__} is a directed test but has no SCENARIO_ID")
        if sid not in PLAN_DIRECTED_IDS:
            raise AssertionError(
                f"{cls.__name__} carries unknown scenario id {sid!r}")
        if sid in seen:
            raise AssertionError(
                f"scenario id {sid} has two test classes "
                f"({seen[sid].__name__} and {cls.__name__})")
        seq_cls = getattr(cls, "SEQUENCE_CLASS", None)
        if seq_cls is None or getattr(seq_cls, "SCENARIO_ID", None) != sid:
            raise AssertionError(
                f"{cls.__name__}.SEQUENCE_CLASS does not implement "
                f"SCENARIO_ID {sid} "
                f"(sequence layer says {seq_by_id[sid].__name__} -> "
                f"{getattr(seq_by_id[sid], 'SCENARIO_ID', None)})")
        seen[sid] = cls
    missing = set(PLAN_DIRECTED_IDS) - set(seen)
    if missing:
        raise AssertionError(
            f"missing directed test scenario ids: {sorted(missing)}")
    return seen


# Verified at import time so plan/sequence/test drift fails loudly.
_DIRECTED_TEST_BY_ID = verify_directed_test_scenario_ids()