"""Stage 6 (integration) artifact of the CHIA generator: the AES pyuvm tests.

This module defines the complete test layer for the ``aes128`` bench.  All
class names here are the exact ``UVM_TESTNAME`` values listed in
``generation_manifest.yaml`` and selectable through the Makefile::

    AESNistKatTest               .. AESResetMidTransactionTest  (directed,
                                                        one per plan id)
    AESCornerCaseTest                                        (corner set)
    AESRandomizedTest                              (constrained-random)

Every test is a ``uvm_test`` subclass of :class:`AESTestBase`:

* ``build_phase``  -- creates :class:`~tb.environment.AES128Environment`
  (agent + scoreboard + coverage + assertion checkers);
* ``run_phase``    -- raises a run-phase objection, starts the stimulus
  ``uvm_sequence`` on ``env.agent.sequencer``, lets the scoreboard drain
  the tail, and drops the objection;
* ``report_phase`` -- enforces pass/fail: zero oracle mismatches and the
  minimum completed-transaction guard required by the scenario.

VERDICT SEMANTICS (``CONTRACT.md`` "Verification isolation"): the target RTL
``aes128.sv`` is intentionally buggy per verification-plan item ``DISC-001``
(the final-round MixColumns guard ``if (round == 4'd10)`` never fires, so
MixColumns runs in all ten rounds).  The scoreboard compares the DUT
ciphertext against the FIPS-197-correct reference model and therefore
reports a mismatch on **every completed transaction**.  ``report_phase``
fails every such test - which is the intended bug-detection outcome, not a
testbench defect.  Only :class:`AESResetMidTransactionTest` (by design
exercises no completed transaction) is expected to pass.  The pass criteria
are written against the *reference model*, never against the buggy RTL.

Consistency guards run at import time: :func:`verify_directed_scenario_ids`
(from tb/sequences.py) checks the sequence side against the plan;
:func:`verify_directed_test_scenario_ids` here checks the test side and
cross-checks every directed test -> sequence ``SCENARIO_ID`` pairing.
"""

import os

from cocotb.triggers import ClockCycles
from pyuvm import ConfigDB, uvm_test

from tb.environment import AES128Environment
from tb.sequences import (
    CORNER_CASE_SEQUENCE_CLASSES,
    DIRECTED_SEQUENCE_CLASSES,
    AllOnesSeq,
    AllZerosSeq,
    AlternatingSeq,
    DonePulseWidthSeq,
    InputChangeWhileBusySeq,
    NistKatSeq,
    NonzeroKeyZeroPtSeq,
    PLAN_DIRECTED_IDS,
    RepeatedTransactionsSeq,
    ResetDuringIdleSeq,
    ResetMidTransactionSeq,
    ZeroKeyNonzeroPtSeq,
    AESRandomizedSequence,
    verify_directed_scenario_ids,
)

__all__ = [
    "AESTestBase",
    "AESNistKatTest",
    "AESAllZerosTest",
    "AESAllOnesTest",
    "AESAlternatingTest",
    "AESZeroKeyNonzeroPtTest",
    "AESNonzeroKeyZeroPtTest",
    "AESInputChangeWhileBusyTest",
    "AESRepeatedTransactionsTest",
    "AESDonePulseWidthTest",
    "AESResetDuringIdleTest",
    "AESResetMidTransactionTest",
    "AESCornerCaseTest",
    "AESRandomizedTest",
    "DIRECTED_TEST_CLASSES",
    "verify_directed_test_scenario_ids",
]


class AESTestBase(uvm_test):
    """Base test: builds the environment and enforces the pass criteria.

    Class attributes overridden by the concrete tests:

    * ``SCENARIO_ID``            -- plan id for directed tests (``None`` for
      the corner/randomized strategies).
    * ``SEQUENCE_CLASS``         -- the stimulus ``uvm_sequence`` to start.
    * ``REQUIRES_TRANSACTIONS``  -- if True (every data-path scenario), the
      scoreboard must have scored at least one completed transaction,
      otherwise the test fails (a test whose driver/sequence crashed before
      any stimulus must not silently pass).
    """

    SCENARIO_ID = None
    SEQUENCE_CLASS = None
    REQUIRES_TRANSACTIONS = True

    def __init__(self, name="aes_test", parent=None):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        super().build_phase()
        self.env = AES128Environment("aes128_env", self)
        self.logger.info("%s: AES128Environment created", self.get_name())

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
                "no stimulus applied",
                self.get_name(),
            )
            return
        await self._run_single_sequence(self.SEQUENCE_CLASS)

    async def _run_single_sequence(self, seq_class, drain_cycles=4):
        """Start *seq_class* and wait a few cycles for the scoreboard to
        process the final monitor transactions."""
        seq = seq_class()
        await seq.start(self.env.agent.sequencer)
        dut = ConfigDB().get(self, "", "dut")
        await ClockCycles(dut.clk, drain_cycles)

    def report_phase(self):
        """Enforce pass/fail: zero oracle mismatches and (for scenarios that
        must exercise the data path) at least one scored transaction."""
        super().report_phase()
        sb = self.env.scoreboard
        if sb is None:
            self.logger.error(
                "%s: TEST FAILED - no scoreboard was built",
                self.get_name(),
            )
            raise AssertionError("AES env has no scoreboard (early crash?)")

        results = sb.results()
        if results["mismatches"] > 0:
            self.logger.error(
                "%s: TEST FAILED - scoreboard reported %d mismatch(es) out "
                "of %d completed transaction(s) (oracle = FIPS-197 "
                "reference model; this is the intended DISC-001 bug "
                "detection)",
                self.get_name(),
                results["mismatches"],
                results["transactions"],
            )
            raise AssertionError(
                f"AES128Scoreboard reported {results['mismatches']} "
                f"comparison mismatch(es): DUT ciphertext does not match "
                f"the AES-128 reference-model oracle"
            )

        if self.REQUIRES_TRANSACTIONS and results["transactions"] == 0:
            self.logger.error(
                "%s: TEST FAILED - zero completed transactions scored "
                "(driver/sequence may have crashed before exercising any "
                "stimulus)",
                self.get_name(),
            )
            raise AssertionError(
                "AES128Scoreboard scored 0 transactions - no stimulus was "
                "exercised"
            )

        self.logger.info(
            "TEST PASSED: %s (%s): %d completed transaction(s) matched the "
            "reference model, 0 mismatches",
            self.get_name(),
            self.SCENARIO_ID,
            results["transactions"],
        )


# ---------------------------------------------------------------------------
# Directed scenario tests (plan directed_test_scenarios, one per plan id)
# ---------------------------------------------------------------------------
class AESNistKatTest(AESTestBase):
    """nist_kat - FIPS-197 Appendix B known-answer test vector."""

    SCENARIO_ID = "nist_kat"
    SEQUENCE_CLASS = NistKatSeq

    def __init__(self, name="AESNistKatTest", parent=None):
        super().__init__(name, parent)


class AESAllZerosTest(AESTestBase):
    """all_zeros - all-zero key and plaintext."""

    SCENARIO_ID = "all_zeros"
    SEQUENCE_CLASS = AllZerosSeq

    def __init__(self, name="AESAllZerosTest", parent=None):
        super().__init__(name, parent)


class AESAllOnesTest(AESTestBase):
    """all_ones - all-ones key and plaintext."""

    SCENARIO_ID = "all_ones"
    SEQUENCE_CLASS = AllOnesSeq

    def __init__(self, name="AESAllOnesTest", parent=None):
        super().__init__(name, parent)


class AESAlternatingTest(AESTestBase):
    """alternating - 0xAA..AA key with 0x55..55 plaintext."""

    SCENARIO_ID = "alternating"
    SEQUENCE_CLASS = AlternatingSeq

    def __init__(self, name="AESAlternatingTest", parent=None):
        super().__init__(name, parent)


class AESZeroKeyNonzeroPtTest(AESTestBase):
    """zero_key_nonzero_pt - zero key with a nonzero plaintext."""

    SCENARIO_ID = "zero_key_nonzero_pt"
    SEQUENCE_CLASS = ZeroKeyNonzeroPtSeq

    def __init__(self, name="AESZeroKeyNonzeroPtTest", parent=None):
        super().__init__(name, parent)


class AESNonzeroKeyZeroPtTest(AESTestBase):
    """nonzero_key_zero_pt - nonzero key with a zero plaintext."""

    SCENARIO_ID = "nonzero_key_zero_pt"
    SEQUENCE_CLASS = NonzeroKeyZeroPtSeq

    def __init__(self, name="AESNonzeroKeyZeroPtTest", parent=None):
        super().__init__(name, parent)


class AESInputChangeWhileBusyTest(AESTestBase):
    """input_change_while_busy - stimulus change during encryption."""

    SCENARIO_ID = "input_change_while_busy"
    SEQUENCE_CLASS = InputChangeWhileBusySeq

    def __init__(self, name="AESInputChangeWhileBusyTest", parent=None):
        super().__init__(name, parent)


class AESRepeatedTransactionsTest(AESTestBase):
    """repeated_transactions - two back-to-back transactions."""

    SCENARIO_ID = "repeated_transactions"
    SEQUENCE_CLASS = RepeatedTransactionsSeq

    def __init__(self, name="AESRepeatedTransactionsTest", parent=None):
        super().__init__(name, parent)


class AESDonePulseWidthTest(AESTestBase):
    """done_pulse_width - done pulses for exactly one clock."""

    SCENARIO_ID = "done_pulse_width"
    SEQUENCE_CLASS = DonePulseWidthSeq

    def __init__(self, name="AESDonePulseWidthTest", parent=None):
        super().__init__(name, parent)


class AESResetDuringIdleTest(AESTestBase):
    """reset_during_idle - reset while the DUT is idle."""

    SCENARIO_ID = "reset_during_idle"
    SEQUENCE_CLASS = ResetDuringIdleSeq

    def __init__(self, name="AESResetDuringIdleTest", parent=None):
        super().__init__(name, parent)


class AESResetMidTransactionTest(AESTestBase):
    """reset_mid_transaction - reset aborts an in-flight transaction.

    By plan this scenario exercises no completed transaction (the DUT must
    drop the in-flight encryption), so the scoreboard-transaction guard is
    relaxed here; the pin-level post-reset checks live in the sequence.
    """

    SCENARIO_ID = "reset_mid_transaction"
    SEQUENCE_CLASS = ResetMidTransactionSeq
    REQUIRES_TRANSACTIONS = False

    def __init__(self, name="AESResetMidTransactionTest", parent=None):
        super().__init__(name, parent)


# ---------------------------------------------------------------------------
# Corner-case and randomized strategy tests
# ---------------------------------------------------------------------------
class AESCornerCaseTest(AESTestBase):
    """Corner-case set: all five plan corner scenarios, back to back.

    Exercises the single-bit key, fast re-trigger right after ``done``,
    all-ones key / zero plaintext, zero key / all-ones plaintext and
    start-ignored-while-busy premises; all five complete at least one
    transaction (six total, the fast re-trigger runs two).
    """

    SCENARIO_ID = None
    SEQUENCE_CLASS = None

    def __init__(self, name="AESCornerCaseTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        for seq_class in CORNER_CASE_SEQUENCE_CLASSES:
            await self._run_single_sequence(seq_class, drain_cycles=4)


class AESRandomizedTest(AESTestBase):
    """Randomized strategy: N random pairs with idle/in-flight resets.

    Reads the environment overrides ``AES_NUM_RANDOM``,
    ``AES_IN_FLIGHT_RESET_PROB``, ``AES_IDLE_RESET_PROB`` and ``AES_SEED``
    (defaults: 1000 pairs, 5% in-flight reset, 10% idle reset, random
    seed), reporting the chosen seed for reproducibility.
    """

    SCENARIO_ID = None
    SEQUENCE_CLASS = None

    def __init__(self, name="AESRandomizedTest", parent=None):
        super().__init__(name, parent)

    async def _run_scenario(self):
        num = int(os.environ.get("AES_NUM_RANDOM", "1000"))
        in_flight_p = float(os.environ.get("AES_IN_FLIGHT_RESET_PROB", "0.05"))
        idle_p = float(os.environ.get("AES_IDLE_RESET_PROB", "0.10"))
        seed_env = os.environ.get("AES_SEED", None)
        seed = int(seed_env) if seed_env is not None else None
        seq = AESRandomizedSequence(
            num_transactions=num,
            in_flight_reset_p=in_flight_p,
            idle_reset_p=idle_p,
            seed=seed,
        )
        self.logger.info(
            "%s: AESRandomizedTest knobs - pairs=%d in_flight_p=%.2f "
            "idle_p=%.2f seed_env=%s",
            self.get_name(),
            num,
            in_flight_p,
            idle_p,
            seed_env,
        )
        await seq.start(self.env.agent.sequencer)
        dut = ConfigDB().get(self, "", "dut")
        await ClockCycles(dut.clk, 8)


# ---------------------------------------------------------------------------
# Registries + plan cross-checks
# ---------------------------------------------------------------------------
DIRECTED_TEST_CLASSES = (
    AESNistKatTest,
    AESAllZerosTest,
    AESAllOnesTest,
    AESAlternatingTest,
    AESZeroKeyNonzeroPtTest,
    AESNonzeroKeyZeroPtTest,
    AESInputChangeWhileBusyTest,
    AESRepeatedTransactionsTest,
    AESDonePulseWidthTest,
    AESResetDuringIdleTest,
    AESResetMidTransactionTest,
)


def verify_directed_test_scenario_ids():
    """Check the plan -> test -> sequence id chain.

    The 11 directed test classes must cover the plan IDs exactly once, and
    every test's ``SEQUENCE_CLASS`` must declare the same ``SCENARIO_ID``.
    """
    declared = [cls.SCENARIO_ID for cls in DIRECTED_TEST_CLASSES]
    problems = []
    missing = [sid for sid in PLAN_DIRECTED_IDS if sid not in declared]
    duplicates = [sid for sid in set(declared) if declared.count(sid) > 1]
    extras = [sid for sid in declared if sid not in PLAN_DIRECTED_IDS]
    if missing:
        problems.append(f"missing plan IDs: {missing}")
    if duplicates:
        problems.append(f"duplicate plan IDs: {duplicates}")
    if extras:
        problems.append(f"IDs not in the plan: {extras}")
    for test_cls in DIRECTED_TEST_CLASSES:
        seq_cls = test_cls.SEQUENCE_CLASS
        if seq_cls is None or seq_cls.SCENARIO_ID != test_cls.SCENARIO_ID:
            problems.append(
                f"{test_cls.__name__}: SEQUENCE_CLASS "
                f"{getattr(seq_cls, '__name__', None)} does not carry "
                f"SCENARIO_ID {test_cls.SCENARIO_ID!r}"
            )
    if problems:
        raise RuntimeError(
            "AES tests vs plan/sequence mismatch: " + "; ".join(problems)
        )


# Import-time guards (both sides fail loudly on plan drift).
verify_directed_scenario_ids()
verify_directed_test_scenario_ids()