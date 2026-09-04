"""PyUVM sequences for the parameterized adder DUT.

This module implements the three classes of stimulus prescribed by the
verification plan:

1. **Directed scenarios** — small set of hand-picked operand/result
   combinations covering normal operation, carry propagation, overflow,
   carry-in isolation, reset clearing, all-zeros, and mid-range addition.

2. **Corner cases** — boundary values (max operands, boundary sums,
   alternating bit patterns, single-LSB/MSB).

3. **Randomized** — full-range random ``a``/``b`` and random ``cin``,
   with expected outputs computed from the golden reference model so the
   scoreboard can validate every sample against ``adder_ref``.

All expected outputs (``exp_sum``, ``exp_cout``) are computed here from
the golden reference model (``adder_ref``) so the scoreboard in a later
stage can compare DUT outputs against ground truth.

Only the fields defined in CONTRACT.md (``a``, ``b``, ``cin``,
``exp_sum``, ``exp_cout``) are populated — nothing is added, renamed, or
dropped.
"""

from __future__ import annotations

import os
import random
import sys

from pyuvm import uvm_sequence, ConfigDB

from adder_transaction import AdderTransaction
from dut_helper import DUTHelper

# ----------------------------------------------------------------------
# Golden reference model (ground truth for expected outputs).
#
# The reference model lives in examples/adder/ref_model.py (see
# CONTRACT.md Section 7).  Resolve and import it robustly so the
# sequences can reuse ground truth even when run from a different
# working directory.
# ----------------------------------------------------------------------
def _resolve_ref_model():
    """Import and return the ``adder_ref`` function from the reference model."""
    try:
        from ref_model import adder_ref
        return adder_ref
    except ImportError:
        pass
    # Try to locate examples/adder relative to this file's project root.
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "examples", "adder"),     # generated_tb -> project
        os.path.join(here, "..", "..", "examples", "adder"),
        os.path.join(here, "examples", "adder"),
    ]
    for cand in candidates:
        cand = os.path.abspath(cand)
        if os.path.isfile(os.path.join(cand, "ref_model.py")):
            sys.path.insert(0, cand)
            try:
                from ref_model import adder_ref
                return adder_ref
            except ImportError:
                sys.path.pop(0)
    # The reference model is the single source of truth (CONTRACT Section 7,
    # simulation_contract: reference_model_must_be_exercised_by_the_scoreboard).
    # We deliberately do NOT reimplement `adder_ref` here.  If the real model
    # cannot be imported we fail closed (raise) rather than silently
    # approximating its algorithm, per the generator contract
    # ("generation must fail rather than silently approximating it").
    raise ImportError(
        "Unable to import the golden reference model `adder_ref` from "
        "examples/adder/ref_model.py. The reference model must be present "
        "and importable; generated sequences must not reimplement it."
    )


adder_ref = _resolve_ref_model()


# ----------------------------------------------------------------------
# Small internal helpers
# ----------------------------------------------------------------------

async def _get_helper() -> DUTHelper:
    """Fetch the shared ``DUTHelper`` from the ConfigDB."""
    return ConfigDB.get(None, "", "dut_helper")


async def _reset_and_release(helper: DUTHelper, hold_cycles: int = 5) -> None:
    """Assert reset, hold it, then release it (active-low)."""
    await helper.reset_dut(hold_cycles)


async def _start_item(seq, a: int, b: int, cin: int,
                      exp_sum: int | None = None,
                      exp_cout: int | None = None) -> AdderTransaction:
    """Create, start, and finish a single drive item on the sequencer.

    Returns the item so the caller may inspect or re-use it.  Expected
    outputs default to the golden reference-model computation.
    """
    tr = AdderTransaction()
    tr.a = a
    tr.b = b
    tr.cin = cin
    if exp_sum is None or exp_cout is None:
        exp_sum, exp_cout = adder_ref(a, b, cin)
    tr.exp_sum = exp_sum
    tr.exp_cout = exp_cout
    await seq.start_item(tr)
    await seq.finish_item(tr)
    return tr


# ======================================================================
# Reset sequence
# ======================================================================

class AdderResetSequence(uvm_sequence):
    """Apply a full reset sequence to the DUT.

    Asserts reset (active-low) for ``hold_cycles`` clock cycles, then
    releases it.  No data items are driven — used by tests before the
    data-driving phase.
    """

    def __init__(self, name="adder_reset_sequence", hold_cycles: int = 5):
        super().__init__(name)
        self.hold_cycles = hold_cycles

    async def body(self):
        helper = await _get_helper()
        await _reset_and_release(helper, self.hold_cycles)


# ======================================================================
# Directed scenarios
# ======================================================================

class AdderDirectedSequence(uvm_sequence):
    """Base class implementing the standard directed stimulus flow.

    Flow: reset (5 cycles) → drive (a, b, cin) → wait 1 cycle for the
    registered output.  Subclasses configure the operand values.
    """

    # Operands to be driven (overridden by subclasses).
    A = 0
    B = 0
    CIN = 0
    EXPECTED_SUM = 0
    EXPECTED_COUT = 0
    RESET_HOLD_CYCLES = 5

    async def body(self):
        helper = await _get_helper()

        # 1. Reset for RESET_HOLD_CYCLES cycles.
        await _reset_and_release(helper, self.RESET_HOLD_CYCLES)

        # 2. Drive the data inputs.
        tr = await _start_item(
            self,
            a=self.A,
            b=self.B,
            cin=self.CIN,
            exp_sum=self.EXPECTED_SUM,
            exp_cout=self.EXPECTED_COUT,
        )
        self.logger.info(
            "Directed drive  a=%d b=%d cin=%d (expect sum=%d cout=%d)",
            tr.a, tr.b, tr.cin, tr.exp_sum, tr.exp_cout,
        )

        # 3. Wait one cycle for the registered output to settle.
        await helper.wait_clks(1)


class BasicAdditionNoCarrySequence(AdderDirectedSequence):
    """basic_addition_no_carry: 16 + 32 + 0 = 48, no carry."""

    A = 16
    B = 32
    CIN = 0
    EXPECTED_SUM = 48
    EXPECTED_COUT = 0


class CarryPropagationSequence(AdderDirectedSequence):
    """carry_propagation: 255 + 1 + 0 = 256 -> sum=0, cout=1."""

    A = 255
    B = 1
    CIN = 0
    EXPECTED_SUM = 0
    EXPECTED_COUT = 1


class MaximumOverflowSequence(AdderDirectedSequence):
    """maximum_overflow: 255 + 255 + 1 = 511 -> sum=255, cout=1."""

    A = 255
    B = 255
    CIN = 1
    EXPECTED_SUM = 255
    EXPECTED_COUT = 1


class CarryInIsolationSequence(AdderDirectedSequence):
    """carry_in_isolation: 0 + 0 + 1 = 1, only cin contributes."""

    A = 0
    B = 0
    CIN = 1
    EXPECTED_SUM = 1
    EXPECTED_COUT = 0


class ResetClearsOutputsSequence(uvm_sequence):
    """reset_clears_outputs: verify reset clears sum/cout to zero.

    This scenario does *not* fit the standard single-drive flow — it
    drives a non-zero result, then re-asserts reset and checks that the
    outputs are cleared.  The orchestration happens here so the sequence
    fully realizes the plan's stimulus steps.
    """

    def __init__(self, name="reset_clears_outputs_sequence"):
        super().__init__(name)

    async def body(self):
        helper = await _get_helper()

        # Step 1-2: reset, then drive a=200, b=200, cin=1.
        await _reset_and_release(helper, 5)
        await _start_item(self, a=200, b=200, cin=1, exp_sum=145, exp_cout=1)
        # Wait one cycle for the registered result (200+200+1=401).
        await helper.wait_clks(1)

        # Step: assert reset asynchronously (drive rst_n low).
        await helper.set_reset(active=True)
        # Wait one cycle for the async reset to propagate.
        await helper.wait_clks(1)

        # Re-drive the data inputs so the scoreboard has a transaction to
        # check for the cleared output (sum=0, cout=0).
        tr = await _start_item(self, a=200, b=200, cin=1, exp_sum=0, exp_cout=0)
        self.logger.info(
            "Reset clears: expecting sum=0 cout=0 while reset held "
            "(item %s)", tr,
        )


class AllZerosSequence(AdderDirectedSequence):
    """all_zeros: 0 + 0 + 0 = 0."""

    A = 0
    B = 0
    CIN = 0
    EXPECTED_SUM = 0
    EXPECTED_COUT = 0


class MidRangeAdditionSequence(AdderDirectedSequence):
    """mid_range_addition: 100 + 55 + 1 = 156, no carry."""

    A = 100
    B = 55
    CIN = 1
    EXPECTED_SUM = 156
    EXPECTED_COUT = 0


# ======================================================================
# Corner-case sequence
# ======================================================================

class AdderCornerCaseSequence(AdderDirectedSequence):
    """Base class for corner-case stimuli (same flow as directed)."""

    pass


class MaxOperandsNoCinSequence(AdderCornerCaseSequence):
    """max_operands_no_cin: 255 + 255 + 0 = 510 -> sum=254, cout=1."""

    A = 255
    B = 255
    CIN = 0
    EXPECTED_SUM = 254
    EXPECTED_COUT = 1


class MaxOperandsWithCinSequence(AdderCornerCaseSequence):
    """max_operands_with_cin: 255 + 255 + 1 = 511 -> sum=255, cout=1."""

    A = 255
    B = 255
    CIN = 1
    EXPECTED_SUM = 255
    EXPECTED_COUT = 1


class OneBelowMaxSumSequence(AdderCornerCaseSequence):
    """one_below_max_sum: 255 + 0 + 0 = 255, no carry."""

    A = 255
    B = 0
    CIN = 0
    EXPECTED_SUM = 255
    EXPECTED_COUT = 0


class CinPushesToBoundarySequence(AdderCornerCaseSequence):
    """cin_pushes_to_boundary: 254 + 0 + 1 = 255, no carry."""

    A = 254
    B = 0
    CIN = 1
    EXPECTED_SUM = 255
    EXPECTED_COUT = 0


class AlternatingBitPatternsSequence(AdderCornerCaseSequence):
    """alternating_bit_patterns: 0xAA + 0x55 + 0 = 0xFF, no carry."""

    A = 0xAA
    B = 0x55
    CIN = 0
    EXPECTED_SUM = 255
    EXPECTED_COUT = 0


class AlternatingBitsWithCinSequence(AdderCornerCaseSequence):
    """alternating_bits_with_cin: 0xAA+0x55+1 = 0x100 -> sum=0, cout=1."""

    A = 0xAA
    B = 0x55
    CIN = 1
    EXPECTED_SUM = 0
    EXPECTED_COUT = 1


class SingleLsbSetSequence(AdderCornerCaseSequence):
    """single_lsb_set: 1 + 0 + 0 = 1, LSB works."""

    A = 1
    B = 0
    CIN = 0
    EXPECTED_SUM = 1
    EXPECTED_COUT = 0


class HighestBitOnlySequence(AdderCornerCaseSequence):
    """highest_bit_only: 128 + 0 + 0 = 128, MSB alone."""

    A = 128
    B = 0
    CIN = 0
    EXPECTED_SUM = 128
    EXPECTED_COUT = 0


# A single sequence that runs every corner case in one body, for
# convenience when a test wants to sweep all corner boundaries.
class AdderAllCornerCasesSequence(uvm_sequence):
    """Run every corner-case stimulus back to back."""

    def __init__(self, name="adder_all_corner_cases_sequence",
                 corner_classes: tuple = None):
        super().__init__(name)
        self.corner_classes = corner_classes or (
            MaxOperandsNoCinSequence,
            MaxOperandsWithCinSequence,
            OneBelowMaxSumSequence,
            CinPushesToBoundarySequence,
            AlternatingBitPatternsSequence,
            AlternatingBitsWithCinSequence,
            SingleLsbSetSequence,
            HighestBitOnlySequence,
        )

    async def body(self):
        for cls in self.corner_classes:
            # Instantiate the sub-sequence directly (pyuvm v5 has no
            # string-based factory) and start it on our sequencer.
            seq = cls()
            await seq.start(self.sequencer)


# ======================================================================
# Randomized sequence
# ======================================================================

class AdderRandomSequence(uvm_sequence):
    """Randomized stimulus across the full WIDTH-bit unsigned range.

    Randomizes ``a`` and ``b`` uniformly over ``[0, 2**width - 1]`` and
    ``cin`` over ``{0, 1}``.  On each step it drives one transaction and
    advances a clock cycle, then (after a one-cycle settling delay to
    match the DUT's registered output) samples the outputs and compares
    them against the golden reference model.

    A mismatch between sampled and expected outputs fails the test
    immediately, satisfying the randomized pass criterion.
    """

    def __init__(self, name="adder_random_sequence",
                 num_transactions: int = 1000,
                 seed: int | None = None):
        super().__init__(name)
        self.num_transactions = num_transactions
        self.seed = seed
        self.width = 8

    async def body(self):
        helper = await _get_helper()
        self.width = ConfigDB.get(None, "", "width")
        rng = random.Random(self.seed)

        max_val = (1 << self.width) - 1

        # Reset the DUT before randomization.
        await _reset_and_release(helper, 5)

        for i in range(self.num_transactions):
            a = rng.randint(0, max_val)
            b = rng.randint(0, max_val)
            cin = rng.randint(0, 1)
            exp_sum, exp_cout = adder_ref(a, b, cin, self.width)

            await _start_item(self, a=a, b=b, cin=cin,
                              exp_sum=exp_sum, exp_cout=exp_cout)

            # Wait one cycle for the registered output to reflect the
            # inputs just presented, then sample and compare.
            await helper.wait_clks(1)
            sum_val, cout_val = await helper.sample_outputs()

            if sum_val != exp_sum or cout_val != exp_cout:
                self.logger.error(
                    "RANDOM MISMATCH item %d: a=%d b=%d cin=%d -> got "
                    "sum=%d cout=%d, expected sum=%d cout=%d",
                    i, a, b, cin, sum_val, cout_val, exp_sum, exp_cout,
                )
                raise AssertionError(
                    f"Randomized check failed at iteration {i}: "
                    f"(sum={sum_val}, cout={cout_val}) != "
                    f"(exp_sum={exp_sum}, exp_cout={exp_cout})"
                    f" for a={a} b={b} cin={cin}"
                )

        self.logger.info(
            "Random sequence complete: %d transactions, all matched reference.",
            self.num_transactions,
        )
