"""PyUVM test classes for the parameterized adder DUT.

Each test class extends ``uvm_test`` and drives a specific verification
scenario by building the ``AdderEnv`` and launching the appropriate
sequence(s) on the agent's sequencer.

Test classes are selectable via the ``UVM_TESTNAME`` environment variable
read by the top-level cocotb entry point (``test_top.py``), mirroring
the SV-UVM ``+UVM_TESTNAME`` plusarg convention.

Available test class names (exact strings, registered in the manifest):

  - ``AdderDirectedTest``           — single directed scenario
  - ``AdderBasicAdditionNoCarryTest``
  - ``AdderCarryPropagationTest``
  - ``AdderMaximumOverflowTest``
  - ``AdderCarryInIsolationTest``
  - ``AdderResetClearsOutputsTest``
  - ``AdderAllZerosTest``
  - ``AdderMidRangeAdditionTest``
  - ``AdderCornerCaseTest``         — all corner-case boundaries
  - ``AdderRandomTest``             — 1000 randomized transactions
  - ``AdderFullRegressionTest``     — all of the above in sequence
"""

from __future__ import annotations

from pyuvm import uvm_test

from adder_env import AdderEnv
from adder_sequences import (
    AdderResetSequence,
    BasicAdditionNoCarrySequence,
    CarryPropagationSequence,
    MaximumOverflowSequence,
    CarryInIsolationSequence,
    ResetClearsOutputsSequence,
    AllZerosSequence,
    MidRangeAdditionSequence,
    AdderAllCornerCasesSequence,
    AdderRandomSequence,
)


class _BaseAdderTest(uvm_test):
    """Shared base: builds the environment and provides a helper to run a sequence.

    Subclasses override ``get_sequence_class()`` (and optionally
    ``get_sequence_kwargs()``) to select which stimulus sequence to launch.
    """

    def __init__(self, name="adder_base_test", parent=None):
        super().__init__(name, parent)
        self.env: AdderEnv | None = None

    # ---- override points for subclasses ----

    def get_sequence_class(self):  # noqa: D401
        """Return the ``uvm_sequence`` class (or ``None`` for no sequence)."""
        return None

    def get_sequence_kwargs(self) -> dict:
        """Extra keyword arguments forwarded to the sequence constructor."""
        return {}

    # ---- UVM phases ----

    def build_phase(self):
        super().build_phase()
        self.env = AdderEnv("adder_env", self)

    async def run_phase(self):
        seq_cls = self.get_sequence_class()
        if seq_cls is None:
            return

        # Raise an objection for the whole sequence so pyuvm's
        # run_phase_complete() does not end the run before the stimulus has
        # finished (pyuvm sequences do not raise objections automatically).
        self.raise_objection(
            f"{self.get_full_name()} driving sequence "
            f"{seq_cls.__name__}"
        )
        try:
            seq = seq_cls(**self.get_sequence_kwargs())
            self.logger.info(
                "Test %s starting sequence %s on sequencer",
                self.get_full_name(),
                seq.get_name(),
            )
            await seq.start(self.env.agent.sequencer)
        finally:
            self.drop_objection()


# =====================================================================
# Directed tests (one per scenario)
# =====================================================================

class AdderDirectedTest(_BaseAdderTest):
    """Generic directed test — runs BasicAdditionNoCarry by default."""

    def __init__(self, name="adder_directed_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return BasicAdditionNoCarrySequence


class AdderBasicAdditionNoCarryTest(_BaseAdderTest):
    """basic_addition_no_carry: 16+32+0=48."""

    def __init__(self, name="adder_basic_addition_no_carry_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return BasicAdditionNoCarrySequence


class AdderCarryPropagationTest(_BaseAdderTest):
    """carry_propagation: 255+1+0 → sum=0, cout=1."""

    def __init__(self, name="adder_carry_propagation_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return CarryPropagationSequence


class AdderMaximumOverflowTest(_BaseAdderTest):
    """maximum_overflow: 255+255+1 → sum=255, cout=1."""

    def __init__(self, name="adder_maximum_overflow_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return MaximumOverflowSequence


class AdderCarryInIsolationTest(_BaseAdderTest):
    """carry_in_isolation: 0+0+1=1."""

    def __init__(self, name="adder_carry_in_isolation_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return CarryInIsolationSequence


class AdderResetClearsOutputsTest(_BaseAdderTest):
    """reset_clears_outputs: verify reset drives sum/cout to zero."""

    def __init__(self, name="adder_reset_clears_outputs_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return ResetClearsOutputsSequence


class AdderAllZerosTest(_BaseAdderTest):
    """all_zeros: 0+0+0=0."""

    def __init__(self, name="adder_all_zeros_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return AllZerosSequence


class AdderMidRangeAdditionTest(_BaseAdderTest):
    """mid_range_addition: 100+55+1=156."""

    def __init__(self, name="adder_mid_range_addition_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return MidRangeAdditionSequence


# =====================================================================
# Corner-case test
# =====================================================================

class AdderCornerCaseTest(_BaseAdderTest):
    """Corner-case test — sweeps all boundary operand combinations."""

    def __init__(self, name="adder_corner_case_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return AdderAllCornerCasesSequence


# =====================================================================
# Randomized test
# =====================================================================

class AdderRandomTest(_BaseAdderTest):
    """Randomized test — 1000 random transactions across full WIDTH range."""

    def __init__(self, name="adder_random_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        return AdderRandomSequence

    def get_sequence_kwargs(self) -> dict:
        return {"num_transactions": 1000}


# =====================================================================
# Full regression test
# =====================================================================

class AdderFullRegressionTest(_BaseAdderTest):
    """Runs all directed, corner-case, and randomized sequences back to back.

    This test exercises the full suite in a single run: first the reset
    sequence, then each directed scenario, then the corner-case sweep,
    and finally 1000 randomized transactions.
    """

    def __init__(self, name="adder_full_regression_test", parent=None):
        super().__init__(name, parent)

    def get_sequence_class(self):
        # Not used — run_phase is overridden directly.
        return None

    async def run_phase(self):
        seqs = [
            ("Reset", AdderResetSequence, {}),
            ("BasicAdditionNoCarry", BasicAdditionNoCarrySequence, {}),
            ("CarryPropagation", CarryPropagationSequence, {}),
            ("MaximumOverflow", MaximumOverflowSequence, {}),
            ("CarryInIsolation", CarryInIsolationSequence, {}),
            ("ResetClearsOutputs", ResetClearsOutputsSequence, {}),
            ("AllZeros", AllZerosSequence, {}),
            ("MidRangeAddition", MidRangeAdditionSequence, {}),
            ("AllCornerCases", AdderAllCornerCasesSequence, {}),
            ("Random", AdderRandomSequence, {"num_transactions": 1000}),
        ]

        # Keep the run alive until every sequence in the regression finishes.
        self.raise_objection(f"{self.get_full_name()} full regression")
        try:
            for label, seq_cls, kwargs in seqs:
                self.logger.info(
                    "Full regression: starting %s sequence", label
                )
                seq = seq_cls(name=f"regression_{label.lower()}_seq", **kwargs)
                await seq.start(self.env.agent.sequencer)
        finally:
            self.drop_objection()

        self.logger.info(
            "Full regression test complete: all %d sequences passed.", len(seqs)
        )
