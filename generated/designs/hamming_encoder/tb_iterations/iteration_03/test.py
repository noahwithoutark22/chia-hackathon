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
        2. An inapplicable elaboration -> log-and-skip (still passes).
        3. An applicable elaboration -> at least one scored item, so a
           test that never exercised the DUT cannot false-pass.
        """
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            return  # guard against early phase failures
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
        conf = self._conf()
        if not type(self).elaboration_applies(conf):
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