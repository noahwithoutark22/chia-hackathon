"""FIFO test classes (pyuvm ``uvm_test`` subclasses).

This module defines one test class per directed verification-plan scenario
(TC001–TC010), plus a corner-case aggregate test and a randomized test.
Each test class instantiates :class:`FifoEnv` (agent + scoreboard +
coverage), starts the appropriate stimulus sequence on the agent's
sequencer, and enforces the pass/fail criterion in ``report_phase``:
zero scoreboard mismatches means pass; any mismatch means fail.

The top-level cocotb entry point (``test_top.py``) selects which test
class to run via the ``UVM_TESTNAME`` environment variable and delegates
to ``uvm_root().run_test(test_class_name)``.

Test class names (must match ``generation_manifest.yaml`` exactly)::

    FifoTC001Test  –  FifoTC010Test   (directed scenarios)
    FifoCornerTest                    (all corner-case sequences)
    FifoRandomizedTest                (constrained-random traffic)
"""

from cocotb.triggers import ClockCycles
from pyuvm import ConfigDB, uvm_test

from env import FifoEnv
from sequences import (
    BackToBackSeq,
    BoundaryRoundtripSeq,
    CORNER_SEQUENCES,
    FifoRandomizedSeq,
    PointerWrapOrderingSeq,
    ReadUntilEmptySeq,
    ResetCheckSeq,
    ResetDuringOpSeq,
    SimultaneousReadWriteEmptySeq,
    SimultaneousReadWriteFullSeq,
    SimultaneousReadWriteSeq,
    WriteReadBasicSeq,
    WriteUntilFullSeq,
)


# ---------------------------------------------------------------------------
# Base test
# ---------------------------------------------------------------------------
class FifoTestBase(uvm_test):
    """Common base for every FIFO test.

    * ``build_phase`` creates :class:`FifoEnv` (which in turn builds the
      agent, scoreboard, and coverage subscriber).
    * ``run_phase`` raises a UVM run-phase objection, runs
      ``_run_scenario()`` (overridden by subclasses to start the specific
      stimulus sequence(s)) and drops the objection, so that pyuvm's
      ``run_test()`` waits for the whole scenario before the synchronous
      report phases execute.
    * ``report_phase`` enforces the pass/fail criterion: the scoreboard
      must have recorded zero mismatches.
    """

    def __init__(self, name="fifo_test", parent=None):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        super().build_phase()
        self.env = FifoEnv("fifo_env", self)
        self.logger.info("%s: FifoEnv created", self.get_name())

    async def run_phase(self):
        """Run the stimulus scenario under a run-phase objection.

        pyuvm's ``uvm_root().run_test()`` waits for ``run_phase_complete()``
        and only then executes the synchronous extract/check/report phases.
        ``run_phase_complete()`` proceeds as soon as the last run-phase
        objection is dropped, but gives up immediately when no objection is
        ever raised.  Raising an objection here (UVM convention) therefore
        guarantees the scenario task runs to completion (and the final
        monitor items are drained) before ``report_phase`` evaluates the
        scoreboard's mismatch count.
        """
        self.raise_objection()
        try:
            await self._run_scenario()
        finally:
            self.drop_objection()

    async def _run_scenario(self):
        """Stimulus entry point; concrete tests override this.

        Subclasses start their sequence(s) here (and optionally wait extra
        clock cycles for the scoreboard to drain).  The base implementation
        applies no stimulus.
        """
        self.logger.warning(
            "%s._run_scenario() not overridden: no stimulus applied",
            self.get_name(),
        )

    def report_phase(self):
        """Enforce pass/fail: zero scoreboard mismatches AND minimum
        exercised stimulus = pass.

        (W-EMPTY-FUNCTIONAL-VERIFICATION): a test that crashed in the
        driver/sequence before any data-path stimulus must NOT silently
        pass just because mismatch count is zero.  We require at least
        one scoreboard comparison (items_checked > 0).
        """
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            return  # should not happen, but guard against early phase failures
        if sb._mismatch_count > 0:
            self.logger.error(
                "TEST FAILED: %d scoreboard mismatch(es) across %d checked items "
                "(%d resets observed)",
                sb._mismatch_count,
                sb._items_checked,
                sb._reset_observed,
            )
            raise AssertionError(
                f"FifoScoreboard reported {sb._mismatch_count} mismatch(es)"
            )
        # Minimum-stimulus guard: if the driver/sequence crashed before any
        # data-path cycle was exercised, items_checked stays 0 and the test
        # would falsely pass.  Require at least one checked item.
        if sb._items_checked == 0:
            self.logger.error(
                "TEST FAILED: zero scoreboard items checked — no functional "
                "stimulus was exercised (driver/sequence may have crashed)"
            )
            raise AssertionError(
                "FifoScoreboard checked 0 items — test exercised no stimulus"
            )
        self.logger.info(
            "TEST PASSED: %d items checked, 0 mismatches, %d resets observed",
            sb._items_checked,
            sb._reset_observed,
        )


# ---------------------------------------------------------------------------
# Helper: run a single sequence and let the scoreboard drain
# ---------------------------------------------------------------------------
async def _run_single_sequence(test, seq_class, drain_cycles=2):
    """Instantiate *seq_class*, start it on the agent's sequencer, and
    wait a few clock cycles for the scoreboard to process remaining items."""
    dut = ConfigDB().get(None, "*", "dut")
    seq = seq_class()
    await seq.start(test.env.agent.sequencer)
    # Let the scoreboard drain the final monitor transactions.
    await ClockCycles(dut.clk, drain_cycles)


# ---------------------------------------------------------------------------
# Directed scenario tests (TC001–TC010)
# ---------------------------------------------------------------------------
class FifoTC001Test(FifoTestBase):
    """TC001 — reset_check."""

    def __init__(self, name="FifoTC001Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, ResetCheckSeq)


class FifoTC002Test(FifoTestBase):
    """TC002 — write_read_basic."""

    def __init__(self, name="FifoTC002Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, WriteReadBasicSeq)


class FifoTC003Test(FifoTestBase):
    """TC003 — write_until_full."""

    def __init__(self, name="FifoTC003Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, WriteUntilFullSeq)


class FifoTC004Test(FifoTestBase):
    """TC004 — read_until_empty."""

    def __init__(self, name="FifoTC004Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, ReadUntilEmptySeq)


class FifoTC005Test(FifoTestBase):
    """TC005 — simultaneous_read_write."""

    def __init__(self, name="FifoTC005Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, SimultaneousReadWriteSeq)


class FifoTC006Test(FifoTestBase):
    """TC006 — simultaneous_read_write_at_full."""

    def __init__(self, name="FifoTC006Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, SimultaneousReadWriteFullSeq)


class FifoTC007Test(FifoTestBase):
    """TC007 — simultaneous_read_write_at_empty."""

    def __init__(self, name="FifoTC007Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, SimultaneousReadWriteEmptySeq)


class FifoTC008Test(FifoTestBase):
    """TC008 — pointer_wraparound_ordering."""

    def __init__(self, name="FifoTC008Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, PointerWrapOrderingSeq)


class FifoTC009Test(FifoTestBase):
    """TC009 — reset_during_operation."""

    def __init__(self, name="FifoTC009Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, ResetDuringOpSeq)


class FifoTC010Test(FifoTestBase):
    """TC010 — data_boundary_roundtrip."""

    def __init__(self, name="FifoTC010Test", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, BoundaryRoundtripSeq)


# ---------------------------------------------------------------------------
# Corner-case aggregate test
# ---------------------------------------------------------------------------
class FifoCornerTest(FifoTestBase):
    """Runs every corner-case sequence from the plan sequentially.

    Corner-case sequences (``corner_cases`` section of the plan) do not
    carry a ``SCENARIO_ID``; they are collected in ``CORNER_SEQUENCES``
    (sequences.py).
    """

    def __init__(self, name="FifoCornerTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        dut = ConfigDB().get(None, "*", "dut")
        for seq_cls in CORNER_SEQUENCES:
            seq = seq_cls()
            await seq.start(self.env.agent.sequencer)
            # Brief drain between sequences so the scoreboard can catch up.
            await ClockCycles(dut.clk, 2)
        # Final drain after the last sequence.
        await ClockCycles(dut.clk, 2)


# ---------------------------------------------------------------------------
# Back-to-back operations test (W-NO-BACK-TO-BACK)
# ---------------------------------------------------------------------------
class FifoBackToBackTest(FifoTestBase):
    """Exercises consecutive operations without intervening idle cycles.

    Verifies that the driver's back-to-back support works correctly and
    that the FIFO handles rapid consecutive writes, consecutive reads,
    and mixed operations on adjacent rising edges.
    """

    def __init__(self, name="FifoBackToBackTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        await _run_single_sequence(self, BackToBackSeq)


# ---------------------------------------------------------------------------
# Randomized test
# ---------------------------------------------------------------------------
class FifoRandomizedTest(FifoTestBase):
    """Runs the constrained-random stimulus sequence.

    ``FifoRandomizedSeq`` drives random wr_en/rd_en/din values with
    periodic and random mid-test reset injections (plan
    ``randomized_testing_strategy``).  The sequence uses a deterministic
    RNG seed (W-SEED-NOREPRO) so failures are reproducible via
    ``RANDOM_SEED`` (see ``sequences.py``).
    """

    def __init__(self, name="FifoRandomizedTest", parent=None):
        super().__init__(name, parent)
        self._seq = None  # holds the started sequence for seed reporting

    async def _run_scenario(self):
        dut = ConfigDB().get(None, "*", "dut")
        seq = FifoRandomizedSeq()
        self._seq = seq
        await seq.start(self.env.agent.sequencer)
        # Let the scoreboard drain remaining monitor transactions.
        await ClockCycles(dut.clk, 5)

    def report_phase(self):
        if getattr(self, "_seq", None) is not None and self._seq._seed is not None:
            self.logger.info(
                "FifoRandomizedTest used RNG seed %d (replay with "
                "RANDOM_SEED=%d)", self._seq._seed, self._seq._seed,
            )
        super().report_phase()
