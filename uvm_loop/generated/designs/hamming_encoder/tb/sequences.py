"""hamming_encoder pyuvm sequences (stage 2: STIMULUS).

This module implements the stimulus layer of the hamming_encoder bench:

* **Directed scenario sequences** -- one class per plan
  ``directed_test_scenarios[i].id`` (TC1 .. TC8).  Every directed class
  carries a class-level ``SCENARIO_ID`` whose value *exactly* matches its
  plan id, and the module verifies at import time that each plan id appears
  **exactly once** (``verify_directed_scenario_ids``).

* **Corner-case sequences** -- the plan ``corner_cases`` list (a separate
  verification strategy, therefore intentionally carrying **no**
  ``SCENARIO_ID``).

* **Randomized sequence** -- the plan ``randomized_testing_strategy``: a
  constrained-random data stream with boundary-concentrated values,
  self-scored against the authoritative Python reference model and paced by
  an environment reset per configuration.

Design rules honoured here (CONTRACT.md):

* All stimulus reaches the DUT exclusively through ``HammingDriver``:
  sequences send ``HammingTransaction`` items with ``start_item()`` /
  ``finish_item()``; the driver applies each item at a virtual cycle
  boundary and paces one settle cycle, so when ``finish_item`` returns the
  combinational ``code_out`` is settled and safe to sample.
* The DUT has **no** ``clk`` / reset pins: ``clk`` and ``tb_reset`` are
  virtual testbench signals described by the ConfigDB-shared ``ClockReset``.
  Sequences pace time with ``wait_clock_cycles(clkrs, n)`` (Timer waits) --
  never ``RisingEdge(dut.clk)``.
* ``tb_reset`` is environment-only: ``_reset_environment`` only paces the
  asserted/deasserted reference-cycle windows (CONTRACT.md section 3); it
  never drives or clears the DUT (``code_out`` must not be used as a reset
  oracle).
* Checks are plain-Python ``assert``/``AssertionError`` failures that fail
  the enclosing cocotb test immediately.  Every driven vector is checked
  bit-exactly (masked to the active ``CODE_WIDTH``) against
  ``hamming_encode(data_in, data_width, secded)`` from the authoritative
  reference model.
* The DUT is elaborated once per simulation with a *fixed*
  ``DATA_WIDTH``/``SECDED``.  Plan scenarios that mention both SECDED
  modes or several widths are realised across the elaborations chosen by
  the test stage: each sequence uses the active ``HammingConf``
  (ConfigDB ``KEY_CONF``) and guards itself to the elaborations it
  targets, logging and skipping (instead of failing) when started under an
  inapplicable elaboration.
* Functional coverage and always-running assertion checkers are later-stage
  artifacts; only item-producing/self-checking coroutines run here.
"""

import random

from pyuvm import ConfigDB, uvm_sequence

from tb.dut_helper import (
    HammingConf,
    KEY_CLK_RST,
    KEY_CONF,
    KEY_DUT_PINS,
    wait_clock_cycles,
)
from tb.transaction import HammingTransaction

# Authoritative Python reference model (CONTRACT.md section 7).  Depending
# on the run layout the repository root or the benchmark directory is on
# sys.path; try the canonical path first.
try:  # pragma: no cover - path selection
    from benchmarks.hamming_encoder.ref_model import hamming_encode
except ImportError:
    try:  # pragma: no cover - path selection
        from hamming_encoder.ref_model import hamming_encode
    except ImportError:
        from ref_model import hamming_encode  # pragma: no cover

__all__ = [
    "HammingScenarioBase",
    # directed
    "ResetAndZeroInitialStateSeq",
    "SpecExampleHamming74Seq",
    "SpecExampleHamming84SECDEDSeq",
    "ExhaustiveSweepHamming74Seq",
    "ExhaustiveSweepHamming128Seq",
    "SingleBitWalkSeq",
    "ParameterizedWidthConfigurationsSeq",
    "AlternatingAndBoundaryPatternsSeq",
    # corner cases
    "ZeroDataWordSeq",
    "AllOnesDataWordSeq",
    "SingleBitDataWalkSeq",
    "MinimumDataWidthSeq",
    "ParityBitCountTransitionSeq",
    "SECDEDOrderingShiftSeq",
    "SECDEDCodewordEvenWeightSeq",
    "HammingWeightSymmetrySeq",
    # randomized
    "HammingRandomizedSequence",
    # registries / verification
    "DIRECTED_SEQUENCE_CLASSES",
    "CORNER_CASE_SEQUENCE_CLASSES",
    "RANDOMIZED_SEQUENCE_CLASS",
    "PLAN_DIRECTED_IDS",
    "verify_directed_scenario_ids",
]

# ---------------------------------------------------------------------------
# Every planned directed scenario id (from plans/verification_plan.yaml).
# ---------------------------------------------------------------------------
PLAN_DIRECTED_IDS = ("TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "TC7", "TC8")

# Spec worked-example codewords (spec.md section 4.1 / 4.2), kept as
# explicit literals so the sequences reproduce the *documented* values, not
# just whatever the reference model returns.  A disagreement between the
# two is a spec/model problem that must fail loudly.
SPEC_EXAMPLE_74_CODE = 0b0101101  # data_in=4'b0101, DATA_WIDTH=4, SECDED=0
SPEC_EXAMPLE_84_SECDED_CODE = 0b01011010  # same data, SECDED=1

# spec.md section 4.3 geometry table: data_width ->
# (PARITY_BITS, CODE_WIDTH(SECDED=0), CODE_WIDTH(SECDED=1)).
SPEC_GEOMETRY_TABLE = {
    1: (2, 3, 4),
    4: (3, 7, 8),
    8: (4, 12, 13),
    11: (4, 15, 16),
    16: (5, 21, 22),
}


# ---------------------------------------------------------------------------
# Small pure helpers (no simulation state).
# ---------------------------------------------------------------------------
def _alternating_pattern(width):
    """A ``width``-bit alternating ``0b1010...`` pattern (LSB-first)."""
    patt = 0
    for i in range(1, width, 2):
        patt |= 1 << i
    return patt


def _bit_reverse(value, width):
    """Reverse the low ``width`` bits of ``value``."""
    rev = 0
    for i in range(width):
        if (value >> i) & 1:
            rev |= 1 << (width - 1 - i)
    return rev


def _popcount(value):
    """Number of set bits (reduction-XOR companion used by corner cases)."""
    return bin(int(value)).count("1")


# ---------------------------------------------------------------------------
# Shared substrate for all sequence flavours.
# ---------------------------------------------------------------------------
class HammingScenarioBase(uvm_sequence):
    """Common helpers for directed, corner-case and randomized sequences."""

    #: Plan scenario id; None for corner-case/randomized sequences (by design).
    SCENARIO_ID = None

    RESET_ASSERT_CYCLES = 2    # plan: tb_reset asserted for 2 reference cycles
    RESET_DEASSERT_CYCLES = 1  # plan: then released for 1 cycle

    def __init__(self, name="hamming_scenario_seq"):
        super().__init__(name)

    # ------------------------------------------------------------------
    # ConfigDB access (CONTRACT.md section 6, exact keys)
    # ------------------------------------------------------------------
    @staticmethod
    def _config_get(key):
        """Read a ConfigDB entry from a sequence context.

        pyuvm's ``ConfigDB.get`` takes a ``uvm_component`` context;
        sequences are ``uvm_object``s.  The bench stores its shared objects
        globally (``ConfigDB().set(None, "*", KEY_..., value)``), so
        sequences read them through the global context with an empty scope,
        which resolves to exactly the same store.
        """
        return ConfigDB().get(None, "", key)

    def _pins(self):
        """Shared ``HammingDutPins`` helper (KEY_DUT_PINS)."""
        return self._config_get(KEY_DUT_PINS)

    def _clkrs(self):
        """Shared ``ClockReset`` virtual clock/reset descriptor (KEY_CLK_RST)."""
        return self._config_get(KEY_CLK_RST)

    def _conf(self):
        """Active elaboration geometry (KEY_CONF).

        Falls back to the ``HammingTransaction`` class defaults (derived
        through ``HammingConf.compute``) if the key is absent, so a
        sequence started before ``tb_top`` shared ``KEY_CONF`` still behaves
        deterministically instead of crashing on a bare ``None``.
        """
        conf = self._config_get(KEY_CONF)
        if conf is None:
            conf = HammingConf.compute(
                HammingTransaction.DATA_WIDTH, HammingTransaction.SECDED)
            self.logger.warning(
                "%s: KEY_CONF not found in ConfigDB; derived geometry from "
                "HammingTransaction defaults: %s", self.get_name(), conf)
        return conf

    # ------------------------------------------------------------------
    # Reference-model oracle (CONTRACT.md section 7)
    # ------------------------------------------------------------------
    @staticmethod
    def _reference(data_in, data_width, secded):
        """``hamming_encode(data_in, data_width, secded)`` -> (code, params).

        Argument order and values are exactly the reference-model contract;
        this is a pure forward, never a reimplementation.
        """
        return hamming_encode(int(data_in), int(data_width), bool(secded))

    # ------------------------------------------------------------------
    # Reset stimulus (virtual, environment-only)
    # ------------------------------------------------------------------
    async def _reset_environment(self, cycles=None, deassert_cycles=None):
        """Pace the virtual ``tb_reset`` phase (CONTRACT.md section 3).

        ``tb_reset`` is active-low, asynchronous and *virtual*: asserting it
        is a logical phase during which predictor/scoreboard/coverage
        components reinitialise their own state.  It never drives or clears
        the DUT.  This helper paces ``cycles`` reference cycles for the
        asserted window (plan uses 2) then ``deassert_cycles`` cycles for
        the released window (plan uses 1) so stimulus resumes on a clean
        boundary.
        """
        if cycles is None:
            cycles = self.RESET_ASSERT_CYCLES
        if deassert_cycles is None:
            deassert_cycles = self.RESET_DEASSERT_CYCLES
        await wait_clock_cycles(self._clkrs(), cycles)
        await wait_clock_cycles(self._clkrs(), deassert_cycles)

    # ------------------------------------------------------------------
    # Transaction stimulus (always through the driver)
    # ------------------------------------------------------------------
    async def _drive(self, data_in, tag="tx"):
        """Send one :class:`~tb.transaction.HammingTransaction` via the
        sequencer to :class:`~tb.driver.HammingDriver`.

        Returns after the driver has applied ``data_in`` and paced the
        combinational-settle window (``finish_item`` returns once the item
        is done), so the caller may sample ``code_out`` immediately.
        """
        conf = self._conf()
        item = HammingTransaction(
            f"{self.get_name()}_{tag}",
            data_width=conf.data_width,
            secded=conf.secded,
        )
        item.data_in = int(data_in)
        item.check_inputs_valid()
        await self.start_item(item)
        await self.finish_item(item)
        return item

    # ------------------------------------------------------------------
    # Observation / checks
    # ------------------------------------------------------------------
    def _sample_code(self):
        """Sample ``code_out`` strictly (X/Z on the pin raises)."""
        conf = self._conf()
        return self._pins().sample_code_out_strict(code_width=conf.code_width)

    def _check_expected(self, data_in, tag="check"):
        """Compare sampled ``code_out`` bit-exactly with the reference model.

        Raises :class:`AssertionError` (failing the cocotb test
        immediately) on any mismatch, reporting data_in, DATA_WIDTH, SECDED,
        expected/actual codewords and the differing bit indices -- the
        error-reporting payload the plan requires.  Returns the sampled
        codeword for callers that need to inspect it further.
        """
        conf = self._conf()
        expected, _params = self._reference(data_in, conf.data_width,
                                            conf.secded)
        actual = self._sample_code()
        if actual != expected:
            diff = [i for i in range(conf.code_width)
                    if ((actual ^ expected) >> i) & 1]
            raise AssertionError(
                f"{self.get_name()}[{tag}] code_out mismatch: "
                f"data_in={data_in:0{conf.data_width}b}=0x{data_in:x} "
                f"(DATA_WIDTH={conf.data_width}, SECDED={conf.secded}): "
                f"expected={expected:0{conf.code_width}b}=0x{expected:x}, "
                f"actual={actual:0{conf.code_width}b}=0x{actual:x}, "
                f"differing bit indices={diff}")
        return actual

    # ------------------------------------------------------------------
    # Elaboration applicability
    # ------------------------------------------------------------------
    def _targets(self, applies, why):
        """Log-and-skip guard for elaboration-specific scenarios.

        The DUT is elaborated once per simulation with a fixed
        DATA_WIDTH/SECDED; a sequence that targets other elaborations logs
        why it is not applicable here and returns without doing anything
        (the test stage wires each sequence to the elaborations it needs).
        """
        if not applies:
            self.logger.info(
                "%s: not applicable (%s); skipping", self.get_name(), why)
        return applies


# ===========================================================================
# Directed scenario sequences (plan directed_test_scenarios).
# ===========================================================================
class ResetAndZeroInitialStateSeq(HammingScenarioBase):
    """TC1: reset_and_zero_initial_state (Hamming(7,4))."""

    SCENARIO_ID = "TC1"

    def __init__(self, name="tc1_reset_and_zero_initial_state"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width == 4 and conf.secded == 0,
                "TC1 targets DATA_WIDTH=4/SECDED=0 (Hamming(7,4))"):
            return
        # Assert the environment reset (tb_reset, active-low) for 2
        # reference cycles, release it for 1; the DUT is untouched.
        await self._reset_environment(cycles=2)
        # Drive the all-zero data word and confirm the all-zero codeword.
        await self._drive(0, tag="zero_data")
        actual = self._check_expected(0, tag="all-zero codeword")
        assert actual == 0, (
            f"{self.get_name()}[TC1]: all-zero data word must encode to an "
            f"all-zero codeword, got {actual:#x} ({actual:07b})")


class SpecExampleHamming74Seq(HammingScenarioBase):
    """TC2: spec_example_hamming_74 (spec.md section 4.1 worked example)."""

    SCENARIO_ID = "TC2"

    def __init__(self, name="tc2_spec_example_hamming_74"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width == 4 and conf.secded == 0,
                "TC2 requires DATA_WIDTH=4/SECDED=0"):
            return
        expected, _ = self._reference(0b0101, conf.data_width, conf.secded)
        # The reference-model result must reproduce the documented literal.
        assert expected == SPEC_EXAMPLE_74_CODE, (
            f"{self.get_name()}[TC2]: reference model disagrees with "
            f"spec.md section 4.1: model {expected:07b}, spec "
            f"{SPEC_EXAMPLE_74_CODE:07b}")
        await self._drive(0b0101, tag="spec_4_1_input")
        self._check_expected(0b0101, tag="spec section 4.1 codeword")


class SpecExampleHamming84SECDEDSeq(HammingScenarioBase):
    """TC3: spec_example_hamming_84_secded (spec.md section 4.2 example)."""

    SCENARIO_ID = "TC3"

    def __init__(self, name="tc3_spec_example_hamming_84_secded"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width == 4 and conf.secded == 1,
                "TC3 requires DATA_WIDTH=4/SECDED=1"):
            return
        expected, _ = self._reference(0b0101, conf.data_width, conf.secded)
        assert expected == SPEC_EXAMPLE_84_SECDED_CODE, (
            f"{self.get_name()}[TC3]: reference model disagrees with "
            f"spec.md section 4.2: model {expected:08b}, spec "
            f"{SPEC_EXAMPLE_84_SECDED_CODE:08b}")
        await self._drive(0b0101, tag="spec_4_2_input")
        self._check_expected(0b0101, tag="spec section 4.2 SECDED codeword")


class ExhaustiveSweepHamming74Seq(HammingScenarioBase):
    """TC4: exhaustive_sweep_hamming_74.

    Exhaustively drives all :math:`2^{DATA_WIDTH}` data words for the active
    SECDED mode (DATA_WIDTH=4 gives the plan's 16 vectors; the plan's "both
    SECDED modes" is covered across the SECDED=0 and SECDED=1 elaborations)
    and checks every codeword bit-exactly against ``hamming_encode``.
    """

    SCENARIO_ID = "TC4"

    def __init__(self, name="tc4_exhaustive_sweep_hamming_74"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width == 4,
                "TC4 targets DATA_WIDTH=4 (Hamming(7,4) / Hamming(8,4))"):
            return
        count = 1 << conf.data_width
        self.logger.info(
            "%s: exhaustive sweep of %d vectors "
            "(DATA_WIDTH=%d, SECDED=%d)",
            self.get_name(), count, conf.data_width, conf.secded)
        for value in range(count):
            await self._drive(value, tag=f"sweep{value}")
            self._check_expected(value, tag=f"sweep[{value}]")


class ExhaustiveSweepHamming128Seq(HammingScenarioBase):
    """TC5: exhaustive_sweep_hamming_128.

    Exhaustively drives all 256 data words at DATA_WIDTH=8, SECDED=0
    (Hamming(12,8)) and checks each 12-bit codeword against the reference
    model; also verifies the derived geometry (R=4, CODE_WIDTH=12).
    """

    SCENARIO_ID = "TC5"

    def __init__(self, name="tc5_exhaustive_sweep_hamming_128"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width == 8 and conf.secded == 0,
                "TC5 requires DATA_WIDTH=8/SECDED=0 (Hamming(12,8))"):
            return
        assert conf.parity_bits == 4, (
            f"{self.get_name()}[TC5]: expected PARITY_BITS=4 at "
            f"DATA_WIDTH=8, got {conf.parity_bits}")
        assert conf.code_width == 12, (
            f"{self.get_name()}[TC5]: expected CODE_WIDTH=12 at "
            f"DATA_WIDTH=8/SECDED=0, got {conf.code_width}")
        for value in range(1 << conf.data_width):
            await self._drive(value, tag=f"sweep{value}")
            self._check_expected(value, tag=f"sweep[{value}]")


class SingleBitWalkSeq(HammingScenarioBase):
    """TC6: single_bit_walk.

    Walks a single high bit across every ``data_in`` position for the
    active elaboration (both SECDED modes are covered across elaborations);
    each minimal-weight codeword stresses the parity XOR trees and is
    checked bit-exactly against the reference model.
    """

    SCENARIO_ID = "TC6"

    def __init__(self, name="tc6_single_bit_walk"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        for bit in range(conf.data_width):
            value = 1 << bit
            await self._drive(value, tag=f"bit{bit}")
            self._check_expected(value, tag=f"single-bit[{bit}]")


class ParameterizedWidthConfigurationsSeq(HammingScenarioBase):
    """TC7: parameterized_width_configurations.

    Smoke-tests the additional elaborations DATA_WIDTH in {1, 11, 16} with
    the active SECDED mode using representative vectors {0, max,
    alternating}, checks them against the reference model, and verifies the
    derived geometry against the spec.md section 4.3 table.  Started under
    any other elaboration it logs and skips.
    """

    SCENARIO_ID = "TC7"

    def __init__(self, name="tc7_parameterized_width_configurations"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width in (1, 11, 16),
                "TC7 targets DATA_WIDTH in {1, 11, 16} "
                f"(active DATA_WIDTH={conf.data_width})"):
            return
        pb, cw_secded0, cw_secded1 = SPEC_GEOMETRY_TABLE[conf.data_width]
        expected_cw = cw_secded1 if conf.secded else cw_secded0
        assert conf.parity_bits == pb, (
            f"{self.get_name()}[TC7]: PARITY_BITS mismatch at "
            f"DATA_WIDTH={conf.data_width}: expected {pb}, got "
            f"{conf.parity_bits}")
        assert conf.code_width == expected_cw, (
            f"{self.get_name()}[TC7]: CODE_WIDTH mismatch at "
            f"DATA_WIDTH={conf.data_width}/SECDED={conf.secded}: expected "
            f"{expected_cw}, got {conf.code_width}")
        patterns = (0, conf.data_in_max(),
                    _alternating_pattern(conf.data_width))
        for value in patterns:
            await self._drive(value, tag=f"width{conf.data_width}_v{value}")
            self._check_expected(value, tag=f"width{conf.data_width}[{value}]")


class AlternatingAndBoundaryPatternsSeq(HammingScenarioBase):
    """TC8: alternating_and_boundary_patterns.

    Drives targeted non-trivial 4-bit patterns under the active SECDED mode
    (both modes covered across elaborations) and checks each against the
    reference model.
    """

    SCENARIO_ID = "TC8"

    def __init__(self, name="tc8_alternating_and_boundary_patterns"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width == 4,
                "TC8 targets DATA_WIDTH=4 (4-bit patterns)"):
            return
        patterns = (0b0011, 0b1001, 0b0110, 0b1010, 0b0101)
        for value in patterns:
            await self._drive(value, tag=f"pattern{value}")
            self._check_expected(value, tag=f"pattern[{value:04b}]")


# ===========================================================================
# Corner-case sequences (plan corner_cases; intentionally no SCENARIO_ID).
# ===========================================================================
class ZeroDataWordSeq(HammingScenarioBase):
    """corner: zero_data_word.

    data_in = 0: every data and parity bit is 0, so the codeword is all
    zeros in both SECDED modes.
    """

    def __init__(self, name="corner_zero_data_word"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        await self._drive(0, tag="zero")
        actual = self._check_expected(0, tag="zero data word")
        assert actual == 0, (
            f"{self.get_name()}: zero data word must encode to all-zero "
            f"codeword, got {actual:#x}")


class AllOnesDataWordSeq(HammingScenarioBase):
    """corner: all_ones_data_word.

    data_in = 2**DATA_WIDTH - 1: maximum-density codeword, checked
    bit-exactly against the reference model (e.g. DATA_WIDTH=4:
    SECDED=0 -> 7'b1111111, SECDED=1 -> 8'b11111111).
    """

    def __init__(self, name="corner_all_ones_data_word"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        value = conf.data_in_max()
        await self._drive(value, tag="all_ones")
        self._check_expected(value, tag="all-ones data word")


class SingleBitDataWalkSeq(HammingScenarioBase):
    """corner: single_bit_data_walk.

    Drives data_in = 1<<i for every i in 0..DATA_WIDTH-1, visiting each
    data-bit placement position individually (minimal-weight codewords
    stress the parity XOR chains).
    """

    def __init__(self, name="corner_single_bit_data_walk"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        for bit in range(conf.data_width):
            value = 1 << bit
            await self._drive(value, tag=f"bit{bit}")
            self._check_expected(value, tag=f"single-bit[{bit}]")


class MinimumDataWidthSeq(HammingScenarioBase):
    """corner: minimum_data_width.

    DATA_WIDTH=1, the smallest legal elaboration (Hamming(3,1) /
    Hamming(4,1) SECDED): R=2, CODE_WIDTH=3 (SECDED=0) or 4 (SECDED=1);
    both data_in values match the reference model.
    """

    def __init__(self, name="corner_minimum_data_width"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width == 1,
                "minimum_data_width targets DATA_WIDTH=1 "
                f"(active DATA_WIDTH={conf.data_width})"):
            return
        expected_cw = 4 if conf.secded else 3
        assert conf.parity_bits == 2, (
            f"{self.get_name()}: expected PARITY_BITS=2 at DATA_WIDTH=1, "
            f"got {conf.parity_bits}")
        assert conf.code_width == expected_cw, (
            f"{self.get_name()}: expected CODE_WIDTH={expected_cw} at "
            f"DATA_WIDTH=1/SECDED={conf.secded}, got {conf.code_width}")
        for value in (0, 1):
            await self._drive(value, tag=f"w1_v{value}")
            self._check_expected(value, tag=f"DATA_WIDTH=1[{value}]")


class ParityBitCountTransitionSeq(HammingScenarioBase):
    """corner: parity_bit_count_transition.

    DATA_WIDTH=5 (first width requiring R=4) and DATA_WIDTH=16 (R=5) --
    the derived-localparam boundaries around the spec section 4.3 table.
    In the active elaboration, verifies PARITY_BITS/CODE_WIDTH follow the
    spec formulas and drives representative vectors checked against the
    reference model.
    """

    def __init__(self, name="corner_parity_bit_count_transition"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width in (5, 16),
                "parity_bit_count_transition targets DATA_WIDTH in {5, 16} "
                f"(active DATA_WIDTH={conf.data_width})"):
            return
        expected_pb = {5: 4, 16: 5}[conf.data_width]
        assert conf.parity_bits == expected_pb, (
            f"{self.get_name()}: expected PARITY_BITS={expected_pb} at "
            f"DATA_WIDTH={conf.data_width}, got {conf.parity_bits}")
        assert conf.code_width == conf.data_width + expected_pb + (
            1 if conf.secded else 0), (
            f"{self.get_name()}: CODE_WIDTH does not follow the spec "
            f"section 2.2 formula at DATA_WIDTH={conf.data_width}: "
            f"{conf.code_width}")
        patterns = (0, conf.data_in_max(),
                    _alternating_pattern(conf.data_width),
                    1 << (conf.data_width // 2))
        for value in patterns:
            await self._drive(value, tag=f"w{conf.data_width}_v{value}")
            self._check_expected(value, tag=f"transition[{value}]")


class SECDEDOrderingShiftSeq(HammingScenarioBase):
    """corner: secded_ordering_shift.

    For a SECDED=1 elaboration, verifies the spec section 3.1 bit-order
    relationship directly on the DUT output: the base (non-SECDED) codeword
    occupies code_out[CODE_WIDTH-1:1] (shifted up exactly one bit) and
    code_out[0] is the overall even-parity bit of the base codeword.
    """

    def __init__(self, name="corner_secded_ordering_shift"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.secded == 1,
                "secded_ordering_shift requires a SECDED=1 elaboration"):
            return
        width = conf.data_width
        vectors = [0, conf.data_in_max()]
        if width >= 4:
            vectors.append(0b0101)  # the spec worked-example input
        vectors.extend(1 << i for i in range(width))
        for value in dict.fromkeys(vectors):  # dedupe, keep order
            await self._drive(value, tag=f"shift{value}")
            full = self._check_expected(value, tag=f"secded[full:{value}]")
            # Base codeword shifted up one bit; bit 0 is overall parity.
            base = full >> 1
            base_mask = (1 << conf.base_width) - 1
            expected_base, _ = self._reference(value, width, 0)
            assert (base & base_mask) == expected_base, (
                f"{self.get_name()}: SECDED bit-order shift broken for "
                f"data_in={value:#x}: base of DUT codeword "
                f"{(base & base_mask):#0{conf.base_width + 2}x} != "
                f"hamming_encode(..., secded=False) {expected_base:#x}")
            overall_parity = full & 1
            assert overall_parity == (_popcount(base & base_mask) & 1), (
                f"{self.get_name()}: code_out[0] is not the overall even "
                f"parity of the base codeword for data_in={value:#x}: got "
                f"{overall_parity}, expected "
                f"{_popcount(base & base_mask) & 1}")


class SECDEDCodewordEvenWeightSeq(HammingScenarioBase):
    """corner: secded_codeword_even_weight.

    For SECDED=1, the complete CODE_WIDTH codeword (including the overall
    parity bit) always has even Hamming weight: reduction-XOR of all bits
    of ``code_out`` is 0 for every data_in.
    """

    def __init__(self, name="corner_secded_codeword_even_weight"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.secded == 1,
                "secded_codeword_even_weight requires a SECDED=1 "
                "elaboration"):
            return
        width = conf.data_width
        rng = random.Random(0x5EED)  # fixed seed: deterministic breadth
        vectors = {0, conf.data_in_max()}
        vectors.update(1 << i for i in range(width))
        for _ in range(8):
            vectors.add(rng.randrange(1 << width))
        for value in sorted(vectors):
            await self._drive(value, tag=f"even{value}")
            full = self._check_expected(value, tag=f"even-weight[{value}]")
            assert _popcount(full) % 2 == 0, (
                f"{self.get_name()}: SECDED codeword for data_in={value:#x} "
                f"has odd weight ({_popcount(full)} ones): {full:#x}")


class HammingWeightSymmetrySeq(HammingScenarioBase):
    """corner: hamming_weight_symmetry.

    Structural consistency probe: data_in values that are complements or
    bit-reverses of each other produce codewords whose weight/parity
    relationships follow from the linear Hamming construction.  Used only
    as a consistency oracle -- every vector is still checked bit-exactly
    against the reference model.
    """

    def __init__(self, name="corner_hamming_weight_symmetry"):
        super().__init__(name)

    async def body(self):
        conf = self._conf()
        width = conf.data_width
        maximum = conf.data_in_max()
        seeds = [0, 1, maximum]
        if width >= 4:
            seeds.append(0b0101)
        seen = set()
        for seed in seeds:
            for value in (seed, maximum ^ seed, _bit_reverse(seed, width)):
                if value in seen:
                    continue
                seen.add(value)
                await self._drive(value, tag=f"sym{value}")
                self._check_expected(value, tag=f"symmetry[{value}]")


# ===========================================================================
# Randomized sequence (plan randomized_testing_strategy).
# ===========================================================================
class HammingRandomizedSequence(HammingScenarioBase):
    """Constrained-random data stream for the active elaboration.

    Generates ``num_vectors`` data_in values uniformly across the full data
    space merged with boundary-concentrated values (0, max, single-bit
    patterns, near-max), so rare codewords are reached as well.  Every
    vector is driven through the driver and checked bit-exactly against the
    reference model (the same oracle the scoreboard applies); the always-on
    scoreboard/monitor independently re-checks the same stream.

    Elaboration handling (plan ``constraints``: data_width in [4, 8],
    secded in {0, 1}): the DUT is elaborated once per simulation, so this
    sequence exercises the *active* (DATA_WIDTH, SECDED) configuration;
    the plan's multi-configuration coverage accumulates across elaborations
    chosen by the test stage.  Started under an out-of-range data width it
    logs and skips.

    Injection (plan ``injection``): an environment reset (``tb_reset``
    asserted for 2 reference cycles) is performed at the start of each
    configuration, clearing predictor/scoreboard/coverage state; it never
    affects the combinational DUT.
    """

    def __init__(self, name="hamming_randomized_seq", num_vectors=1000,
                 seed=None, boundary_prob=0.25):
        super().__init__(name)
        self.num_vectors = int(num_vectors)
        self.seed = seed
        self.boundary_prob = float(boundary_prob)
        self.rng = random.Random(seed)
        self.num_driven = 0
        self.num_checked = 0

    # ------------------------------------------------------------------
    # Random field generators (respect the plan constraints)
    # ------------------------------------------------------------------
    def _random_data_in(self):
        """One data_in value: boundary-concentrated or uniform.

        - with probability ``boundary_prob``: 0 / max / a single-bit
          pattern / a near-max (max minus a single bit) value;
        - otherwise uniform across the low half (0 .. 2**(W-1)-1) and the
          high half (2**(W-1) .. 2**W-1) with equal probability.
        """
        conf = self._conf()
        width = conf.data_width
        maximum = conf.data_in_max()
        r = self.rng.random()
        if r < self.boundary_prob:
            kind = self.rng.randrange(4)
            if kind == 0:
                return 0
            if kind == 1:
                return maximum
            if kind == 2:
                return 1 << self.rng.randrange(width)
            return maximum ^ (1 << self.rng.randrange(width))
        half = 1 << (width - 1)
        if self.rng.random() < 0.5:
            return self.rng.randrange(half)
        return self.rng.randrange(half, 1 << width)

    # ------------------------------------------------------------------
    # Body
    # ------------------------------------------------------------------
    async def body(self):
        conf = self._conf()
        if not self._targets(
                conf.data_width in (4, 8),
                "randomized strategy constrains DATA_WIDTH to [4, 8] "
                f"(active DATA_WIDTH={conf.data_width})"):
            return

        # plan injection: environment reset per configuration.
        await self._reset_environment(cycles=2)

        self.logger.info(
            "%s: starting %d randomized vectors (DATA_WIDTH=%d, SECDED=%d, "
            "seed=%r)",
            self.get_name(), self.num_vectors, conf.data_width,
            conf.secded, self.seed)

        for idx in range(self.num_vectors):
            value = self._random_data_in()
            await self._drive(value, tag=f"rand{idx}")
            self._check_expected(value, tag=f"rand[{idx}]")
            self.num_driven += 1
            self.num_checked += 1

        self.logger.info(
            "%s: completed %d randomized vectors, all bit-exact "
            "(DATA_WIDTH=%d, SECDED=%d)",
            self.get_name(), self.num_checked, conf.data_width,
            conf.secded)


# ===========================================================================
# Registries and scenario-id verification.
# ===========================================================================
DIRECTED_SEQUENCE_CLASSES = [
    ResetAndZeroInitialStateSeq,          # TC1
    SpecExampleHamming74Seq,              # TC2
    SpecExampleHamming84SECDEDSeq,        # TC3
    ExhaustiveSweepHamming74Seq,          # TC4
    ExhaustiveSweepHamming128Seq,         # TC5
    SingleBitWalkSeq,                     # TC6
    ParameterizedWidthConfigurationsSeq,  # TC7
    AlternatingAndBoundaryPatternsSeq,    # TC8
]

CORNER_CASE_SEQUENCE_CLASSES = [
    ZeroDataWordSeq,
    AllOnesDataWordSeq,
    SingleBitDataWalkSeq,
    MinimumDataWidthSeq,
    ParityBitCountTransitionSeq,
    SECDEDOrderingShiftSeq,
    SECDEDCodewordEvenWeightSeq,
    HammingWeightSymmetrySeq,
]

RANDOMIZED_SEQUENCE_CLASS = HammingRandomizedSequence


def verify_directed_scenario_ids():
    """Return {plan id -> sequence class}; raise if any plan id is missing
    or appears more than once (scenario IDs are the connecting identity
    between the plan and the generated bench)."""
    seen = {}
    for cls in DIRECTED_SEQUENCE_CLASSES:
        sid = getattr(cls, "SCENARIO_ID", None)
        if sid is None:
            raise AssertionError(
                f"{cls.__name__} is a directed sequence but has no "
                f"SCENARIO_ID")
        if sid not in PLAN_DIRECTED_IDS:
            raise AssertionError(
                f"{cls.__name__} carries unknown scenario id {sid!r}")
        if sid in seen:
            raise AssertionError(
                f"scenario id {sid} is implemented twice "
                f"({seen[sid].__name__} and {cls.__name__})")
        seen[sid] = cls
    missing = set(PLAN_DIRECTED_IDS) - set(seen)
    if missing:
        raise AssertionError(
            f"missing directed scenario ids: {sorted(missing)}")
    return seen


# Verified at import time so a plan/implementation drift fails loudly.
_DIRECTED_BY_ID = verify_directed_scenario_ids()