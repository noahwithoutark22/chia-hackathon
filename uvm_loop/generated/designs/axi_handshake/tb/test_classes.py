"""UVM test classes for the axi_handshake DUT.

Each ``uvm_test`` subclass:

1. Creates the ``AxiHandshakeEnv`` in ``build_phase``.
2. Runs the appropriate directed / corner-case / randomized sequence
   in ``run_phase`` (raising and dropping objections to keep the
   simulation alive).

Test class names are selectable via the ``UVM_TESTNAME`` environment
variable read by ``test_top.py``.

ConfigDB keys set by tests (CONTRACT.md §5):
  - ``"clock_period"`` — may be set or overridden per test.
"""

from pyuvm import uvm_test, uvm_root, ConfigDB

from environment import AxiHandshakeEnv
from sequences import (
    # Directed sequences (one per plan scenario)
    SmokeAfterResetSequence,
    StallHoldSequence,
    SimultaneousTransferSequence,
    SequentialLoadsSequence,
    NoInputWhenStalledSequence,
    ResetDuringTransferSequence,
    # Corner-case sequences
    BackToBackFullRateSequence,
    AllZeroPayloadSequence,
    AllOnePayloadSequence,
    ProducerHoldsForeverSequence,
    # Randomized sequence
    RandomStimulusSequence,
)


# ═══════════════════════════════════════════════════════════════════
#  Base test class
# ═══════════════════════════════════════════════════════════════════

class _AxiHandshakeBaseTest(uvm_test):
    """Base test that creates the environment.

    Subclasses override ``_run_scenario()`` to start their specific
    sequence(s) on the agent's sequencer.
    """

    def __init__(self, name="axi_handshake_base_test", parent=None):
        super().__init__(name, parent)
        self.env = None
        self._seqr = None

    def build_phase(self):
        super().build_phase()
        self.env = AxiHandshakeEnv("env", self)

    def connect_phase(self):
        super().connect_phase()

    async def run_phase(self):
        """Raise objection, run scenario, drop objection."""
        self.raise_objection()
        self._seqr = self.env.agent.sequencer
        await self._run_scenario()
        self.drop_objection()

    async def _run_scenario(self):
        """Override in subclasses to run the specific sequence."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _run_scenario()"
        )


# ═══════════════════════════════════════════════════════════════════
#  Directed tests — one per plan scenario
# ═══════════════════════════════════════════════════════════════════

class SmokeAfterResetTest(_AxiHandshakeBaseTest):
    """Runs SmokeAfterResetSequence (plan scenario: smoke_after_reset)."""

    def __init__(self, name="SmokeAfterResetTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = SmokeAfterResetSequence()
        await seq.start(self._seqr)


class StallHoldTest(_AxiHandshakeBaseTest):
    """Runs StallHoldSequence (plan scenario: stall_hold)."""

    def __init__(self, name="StallHoldTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = StallHoldSequence()
        await seq.start(self._seqr)


class SimultaneousTransferTest(_AxiHandshakeBaseTest):
    """Runs SimultaneousTransferSequence (plan scenario: simultaneous_transfer)."""

    def __init__(self, name="SimultaneousTransferTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = SimultaneousTransferSequence()
        await seq.start(self._seqr)


class SequentialLoadsTest(_AxiHandshakeBaseTest):
    """Runs SequentialLoadsSequence (plan scenario: sequential_loads)."""

    def __init__(self, name="SequentialLoadsTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = SequentialLoadsSequence()
        await seq.start(self._seqr)


class NoInputWhenStalledTest(_AxiHandshakeBaseTest):
    """Runs NoInputWhenStalledSequence (plan scenario: no_input_when_stalled)."""

    def __init__(self, name="NoInputWhenStalledTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = NoInputWhenStalledSequence()
        await seq.start(self._seqr)


class ResetDuringTransferTest(_AxiHandshakeBaseTest):
    """Runs ResetDuringTransferSequence (plan scenario: reset_during_transfer)."""

    def __init__(self, name="ResetDuringTransferTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = ResetDuringTransferSequence()
        await seq.start(self._seqr)


# ═══════════════════════════════════════════════════════════════════
#  Corner-case tests
# ═══════════════════════════════════════════════════════════════════

class BackToBackFullRateTest(_AxiHandshakeBaseTest):
    """Runs BackToBackFullRateSequence."""

    def __init__(self, name="BackToBackFullRateTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = BackToBackFullRateSequence()
        await seq.start(self._seqr)


class AllZeroPayloadTest(_AxiHandshakeBaseTest):
    """Runs AllZeroPayloadSequence."""

    def __init__(self, name="AllZeroPayloadTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = AllZeroPayloadSequence()
        await seq.start(self._seqr)


class AllOnePayloadTest(_AxiHandshakeBaseTest):
    """Runs AllOnePayloadSequence."""

    def __init__(self, name="AllOnePayloadTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = AllOnePayloadSequence()
        await seq.start(self._seqr)


class ProducerHoldsForeverTest(_AxiHandshakeBaseTest):
    """Runs ProducerHoldsForeverSequence."""

    def __init__(self, name="ProducerHoldsForeverTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = ProducerHoldsForeverSequence()
        await seq.start(self._seqr)


# ═══════════════════════════════════════════════════════════════════
#  Randomized test
# ═══════════════════════════════════════════════════════════════════

class RandomStimulusTest(_AxiHandshakeBaseTest):
    """Runs RandomStimulusSequence (1000 randomized cycles + periodic reset)."""

    def __init__(self, name="RandomStimulusTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        seq = RandomStimulusSequence()
        await seq.start(self._seqr)
