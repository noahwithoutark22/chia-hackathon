"""Direct DUT pin-access helper for the hamming_encoder cocotb + pyuvm bench.

Stage 1 (contract) artifact of the CHIA environment generator.

This is plain Python - NOT a SystemVerilog interface.  It centralizes every
access to the cocotb ``dut`` handle so later stages (driver, monitor,
assertions, coverage, scoreboard, sequences) use one canonical pin map,
exactly as recorded in CONTRACT.md.  Pin names and widths are authoritative:
they come from ``benchmarks/hamming_encoder/hamming_encoder.sv`` and
``generated/designs/hamming_encoder/rtl/rtl_info.json`` and must not be
"discovered" independently by other components.

Structural facts baked into this file (see CONTRACT.md sections 2-3):

* The DUT is *purely combinational*: it has exactly two pins,
  ``data_in`` (input, DATA_WIDTH bits) and ``code_out`` (output,
  CODE_WIDTH bits).  There is **no** ``clk`` port and **no** reset port on
  the DUT, so ``dut.clk`` / ``dut.tb_reset`` must never be referenced.
* ``clk`` and ``tb_reset`` are *testbench-only* (virtual) signals described
  by the ``ClockReset`` dataclass.  The reference clock is paced in Python
  with ``cocotb.triggers.Timer`` (see ``wait_clock_cycles``); the
  environment reset is a logical phase that only reinitializes
  predictor/scoreboard/coverage state and never touches the DUT.

The module also defines the pyuvm ConfigDB key constants every component
must use to retrieve shared objects (cocotb handle, pin wrapper, clock/reset
descriptor, elaboration geometry) plus the shared ``HammingConf`` geometry
object computed from the authoritative reference model.
"""

from dataclasses import dataclass

# ===========================================================================
# pyuvm ConfigDB keys (EXACT keys recorded in CONTRACT.md section 6).
#
# Components must obtain shared objects with these constants and must NOT
# invent alternative keys.  Standard pyuvm usage (exact call form for the
# installed pyuvm version is settled by the integration stage; the proven
# pyuvm-5.x form is shown):
#
#     write side (tb_top / test):
#         ConfigDB().set(None, "*", KEY_DUT, dut)
#         ConfigDB().set(None, "*", KEY_DUT_PINS, HammingDutPins(dut))
#         ConfigDB().set(None, "*", KEY_CLK_RST, ClockReset(...))
#         ConfigDB().set(None, "*", KEY_CONF, HammingConf.compute(...))
#
#     read side (any component):
#         dut   = ConfigDB().get(self, "", KEY_DUT)
#         pins  = ConfigDB().get(self, "", KEY_DUT_PINS)
#         clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
#         conf  = ConfigDB().get(self, "", KEY_CONF)
# ===========================================================================
KEY_DUT = "dut"                          # value type: cocotb top-level Module
KEY_DUT_PINS = "hamming_encoder.dut_pins"  # value type: HammingDutPins
KEY_CLK_RST = "hamming_encoder.clk_rst"    # value type: ClockReset dataclass
KEY_CONF = "hamming_encoder.conf"          # value type: HammingConf dataclass

# ===========================================================================
# Pin names (verbatim from the RTL port list).
# ===========================================================================
PIN_DATA_IN = "data_in"
PIN_CODE_OUT = "code_out"

# ===========================================================================
# Elaboration defaults (authoritative: hamming_encoder.sv / spec.md).
#
# DISC-1 (verification_plan.yaml): rtl_info.json reports SECDED default '1'
# and CODE_WIDTH default '1', which do not match the RTL declarations
# (SECDED = 1'b0) or spec.md (default 0).  The RTL and spec are
# authoritative; always set DATA_WIDTH/SECDED explicitly per test and read
# the active geometry from HammingConf, never from rtl_info.json defaults.
# ===========================================================================
DEFAULT_DATA_WIDTH = 4
DEFAULT_SECDED = 0


# ===========================================================================
# Shared elaboration geometry (ConfigDB KEY_CONF).
# ===========================================================================
@dataclass(frozen=True)
class HammingConf:
    """DUT elaboration geometry shared through ConfigDB.

    Computed by the authoritative Python reference model
    (``HammingParams.compute`` in ``benchmarks/hamming_encoder/ref_model.py``)
    so the bench never re-derives the Hamming geometry itself.  Attributes:

    - ``data_width`` : DATA_WIDTH elaboration parameter (K, > 0).
    - ``secded``     : SECDED elaboration parameter, 0 or 1.
    - ``parity_bits``: derived R (smallest R with 2**R >= K + R + 1).
    - ``base_width`` : derived DATA_WIDTH + PARITY_BITS.
    - ``code_width`` : derived BASE_WIDTH + (SECDED ? 1 : 0); width
                       of ``code_out``.
    """

    data_width: int
    secded: int
    parity_bits: int
    base_width: int
    code_width: int

    @classmethod
    def compute(cls, data_width, secded):
        """Build the geometry for an elaboration from the reference model."""
        from benchmarks.hamming_encoder.ref_model import HammingParams

        data_width = int(data_width)
        secded = int(bool(secded))
        if data_width <= 0:
            raise ValueError(f"DATA_WIDTH must be > 0, got {data_width}")
        params = HammingParams.compute(data_width, secded)
        return cls(
            data_width=data_width,
            secded=secded,
            parity_bits=params.parity_bits,
            base_width=params.base_width,
            code_width=params.code_width,
        )

    def data_in_max(self):
        """Largest valid data_in value for this elaboration (2**W - 1)."""
        return (1 << self.data_width) - 1


# code_out width of the default elaboration (DATA_WIDTH=4, SECDED=0 ->
# Hamming(7,4), CODE_WIDTH=7), used by the pin helpers as a last-resort
# mask width when no HammingConf is supplied.
DEFAULT_CODE_WIDTH = HammingConf.compute(DEFAULT_DATA_WIDTH, DEFAULT_SECDED).code_width


# ===========================================================================
# Testbench clock / reset descriptor (ConfigDB KEY_CLK_RST).
# ===========================================================================
@dataclass(frozen=True)
class ClockReset:
    """Structural clock/reset description shared via ConfigDB.

    The DUT has **no** clock or reset port (purely combinational); ``clk``
    and ``tb_reset`` are testbench-only virtual signals, so this descriptor
    -- not any DUT pin -- is the single source of truth for later stages.

    - ``clock_name``      : ``"clk"``, the testbench reference clock name.
    - ``reset_name``      : ``"tb_reset"``, the environment reset name.
    - ``reset_polarity``  : ``"active_low"`` (asserted = 0).
    - ``reset_type``      : ``"asynchronous"`` (not edge-tied; applied for
                            whole reset phases between stimulus blocks).
    - ``clock_period_ns`` : reference-cycle duration chosen by tb_top
                            (default 10 ns); the DUT is otherwise agnostic.
    - ``reset_assert_value`` : ``0`` (active-low asserted level).
    - ``clk_is_virtual``  : True - no ``dut.clk`` pin; cycles are paced with
                            ``Timer(clock_period_ns)`` (wait_clock_cycles).
    - ``reset_is_virtual``: True - no ``dut.tb_reset`` pin; asserting reset
                            only reinitializes environment components.
    """

    clock_name: str = "clk"
    reset_name: str = "tb_reset"
    reset_polarity: str = "active_low"
    reset_type: str = "asynchronous"
    clock_period_ns: int = 10
    reset_assert_value: int = 0
    clk_is_virtual: bool = True
    reset_is_virtual: bool = True


# ---------------------------------------------------------------------------
# Cocotb value -> int coercion.  Guarding X/Z makes the bench deterministic
# instead of raising on uninitialized pins.
# ---------------------------------------------------------------------------
def _to_int(pin_value, width):
    """Return pin_value as a non-negative int; X/Z bits are read as 0.

    cocotb BinaryValue/LogicArray values (detected via ``binstr``) are
    decoded with ``int()``, which already interprets them as a bit vector.
    Plain strings fall through to character-set classification so that a
    binary-looking vector such as ``"10100101"`` decodes as 165 rather than
    base-10 10100101; X/Z bits are stripped to 0 deterministically.
    """
    if pin_value is None:
        return 0

    if isinstance(pin_value, int):
        # Plain Python ints are already the desired numeric value.
        return pin_value if pin_value >= 0 else 0

    if hasattr(pin_value, "binstr"):
        # cocotb BinaryValue / LogicArray.
        try:
            return int(pin_value)
        except (ValueError, TypeError):
            s = pin_value.binstr or ""
    else:
        s = str(pin_value)

    if s == "" or s.isspace():
        return 0

    s = s.replace("x", "0").replace("X", "0")
    s = s.replace("z", "0").replace("Z", "0")
    if set(s) <= {"0", "1"}:
        return int(s, 2)
    try:
        return int(s, 10)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Strict pin sampling.  ``_to_int`` coerces X/Z to 0 for determinism,
# which is exactly right for stimulus sampling but would silently mask an
# undriven (X/Z) *pin* as 0 -- and the scoreboard's most common expected
# codeword for small inputs is often 0 or a value containing few set bits
# (likewise an undriven ``data_in`` could false-pass a zero-data oracle).
# The strict samplers reject such samples at the single point where each pin
# must be a genuine 0/1 drive.
# ---------------------------------------------------------------------------
def _has_unknown_bits(pin_value):
    """Return True when *pin_value* contains any X or Z bit (4-state value)."""
    if pin_value is None or isinstance(pin_value, int):
        return False
    if hasattr(pin_value, "binstr"):
        s = pin_value.binstr or ""
    else:
        s = str(pin_value)
    s = s.lower()
    return "x" in s or "z" in s


def _check_pins_are_driven(raw_pins, source="output"):
    """Reject a pin sample that contains any X/Z bit (W3 guard).

    ``raw_pins`` maps pin name -> the *raw* (pre-``_to_int``) pin value.
    Raises :class:`AssertionError` when a sampled pin carries an X or Z bit.
    ``source`` ("output" | "input") only selects the error wording: for an
    output an unknown bit means the DUT never drove the pin, for an input it
    means the stimulus side never drove it -- either way the unknown bit
    must not be silently coerced to ``0`` by ``_to_int`` (which could
    false-pass a zero-data oracle).
    """
    unknown = {
        name: str(value)
        for name, value in raw_pins.items()
        if _has_unknown_bits(value)
    }
    if unknown:
        detail = ", ".join(f"{k}={v!r}" for k, v in unknown.items())
        kind = "outputs" if source == "output" else "inputs"
        raise AssertionError(
            f"X/Z on DUT {kind} sampled after combinational settle: "
            f"{detail} (an undriven pin must not be silently coerced to "
            "0 and scored as the reference-model result)")
    return None


class HammingDutPins:
    """Single canonical wrapper around the cocotb ``dut`` handle.

    Every direct pin access in the generated bench goes through this class,
    using the exact pin names of the RTL (``dut.<pin>``).  The class is
    intentionally dumb: no protocol knowledge, no timing - it only converts
    between Python ints and DUT pin values, so it stays useful to every
    component (driver, monitor, checkers, coverage, scoreboard).
    """

    def __init__(self, dut):
        self.dut = dut

    # ------------------------------------------------------------------
    # Pin handles (read-only convenience accessors)
    # ------------------------------------------------------------------
    @property
    def data_in(self):
        return self.dut.data_in

    @property
    def code_out(self):
        return self.dut.code_out

    # ------------------------------------------------------------------
    # Stimulus side
    # ------------------------------------------------------------------
    def drive_data_in(self, value, data_width=None):
        """Write the ``data_in`` pin from an int, masked to DATA_WIDTH bits.

        The mask keeps out-of-range ints from corrupting neighbouring bits
        on the RTL port.  ``data_width`` defaults to the RTL/spec default
        (4); callers holding a ``HammingConf`` should pass ``conf.data_width``.
        """
        width = data_width if data_width is not None else DEFAULT_DATA_WIDTH
        mask = (1 << width) - 1
        self.dut.data_in.value = int(value) & mask

    def drive_zero(self, data_width=None):
        """Drive the all-zero data word (convenience for reset/handshake)."""
        self.drive_data_in(0, data_width=data_width)

    # ------------------------------------------------------------------
    # Observation side
    # ------------------------------------------------------------------
    def sample_code_out(self, code_width=None):
        """Return ``code_out`` as an int (X/Z read as 0 for determinism).

        ``code_width`` defaults to the default elaboration's width (7);
        callers holding a ``HammingConf`` / item should pass the active
        ``code_width`` so the value is never truncated by the mask.
        """
        width = code_width if code_width is not None else DEFAULT_CODE_WIDTH
        return _to_int(self.dut.code_out.value, width)

    def sample_code_out_strict(self, code_width=None):
        """Sample ``code_out``, rejecting any X/Z bit (W3 guard).

        After a drive and its combinational settle the output must be a
        genuine 0/1 drive.  If ``code_out`` contains X/Z this raises
        :class:`AssertionError` before ``_to_int`` can coerce the unknown
        bit to 0 -- closing the false-pass hole where an undriven output
        (0x0) matches the reference-model result for zero data.
        """
        raw = {"code_out": self.dut.code_out.value}
        _check_pins_are_driven(raw, source="output")
        return self.sample_code_out(code_width)

    def sample_data_in(self, data_width=None):
        """Return ``data_in`` as an int (X/Z read as 0 for determinism).

        Mirror of :meth:`sample_code_out` for the stimulus side, provided so
        the monitor can record the exact input value that produced a sampled
        codeword.  ``data_width`` defaults to the default elaboration's
        width (4); callers holding a ``HammingConf`` / item should pass the
        active ``data_width``.
        """
        width = data_width if data_width is not None else DEFAULT_DATA_WIDTH
        return _to_int(self.dut.data_in.value, width)

    def sample_data_in_strict(self, data_width=None):
        """Sample ``data_in``, rejecting any X/Z bit (W3 guard, input side).

        After the first drive the input pin must be a genuine 0/1 stimulus;
        an X/Z bit here means the stimulus side is broken or undriven.
        Raises :class:`AssertionError` before ``_to_int`` can coerce the
        unknown bit to 0, closing the same false-pass hole the strict output
        sampler closes on ``code_out``.
        """
        raw = {"data_in": self.dut.data_in.value}
        _check_pins_are_driven(raw, source="input")
        return self.sample_data_in(data_width)

    def pins_driven(self):
        """True when ``data_in`` and ``code_out`` both carry no X/Z bit.

        The monitor polls this at each virtual cycle boundary to skip the
        undriven pre-first-drive / reset window (when ``code_out`` has no
        settled value yet) and to lock its sampling cadence onto the first
        genuine drive.  After the first transaction the DUT is always driven,
        so this stays True for the remainder of the run.
        """
        return not _has_unknown_bits(self.dut.data_in.value) and not (
            _has_unknown_bits(self.dut.code_out.value)
        )

    def sample_into_item(self, item):
        """Capture the observed ``code_out`` pin into ``item.code_out``.

        The monitor calls this after the item's data_in drive has had one
        reference cycle to settle (CONTRACT.md section 8).  The item's own
        ``code_width`` (from its geometry) is used for the mask, and X/Z
        outputs raise immediately.
        """
        item.code_out = self.sample_code_out_strict(item.code_width)

    def __str__(self):
        return f"HammingDutPins(top={self.dut._name})"


# ---------------------------------------------------------------------------
# Virtual reference-clock pacing (CONTRACT.md section 3).
#
# The DUT is combinational and has no ``clk`` pin, so the testbench
# reference clock cannot be a cocotb ``Clock``/``RisingEdge`` on the DUT.
# Each reference cycle is instead one ``Timer(clock_period_ns)`` wait; the
# "posedge of clk" is the instant a cycle timer expires and is where
# stimulus is applied and (after settle) outputs are sampled.  Later stages
# (driver, monitor, sequences, tb_top) must use these helpers instead of
# ``RisingEdge(dut.clk)`` / ``ClockCycles(dut.clk, n)``.
# ---------------------------------------------------------------------------
async def wait_clock_cycles(clkrs, n=1):
    """Wait ``n`` cycles of the virtual testbench reference clock.

    ``clkrs`` is the ConfigDB-shared ``ClockReset`` instance.  Each cycle
    lasts ``clkrs.clock_period_ns`` ns (default 10).  ``Timer`` is imported
    lazily so this module stays importable outside a running simulation.
    """
    from cocotb.triggers import Timer

    for _ in range(n):
        await Timer(clkrs.clock_period_ns, units="ns")


async def wait_settle(clkrs, settle_cycles=1):
    """Wait the combinational-settle window after driving ``data_in``.

    Latency is 0 (plan): ``code_out`` tracks ``data_in`` combinationally,
    but the one-cycle settle window makes sampling deterministic at the next
    cycle boundary.  Can be called with ``settle_cycles=0`` plus a
    ``Timer(0)``-style read if cycle-exact sampling is ever required.
    """
    await wait_clock_cycles(clkrs, settle_cycles)


# ---------------------------------------------------------------------------
# TB-internal self-check for value decoding, strict output sampling, and the
# geometry table (spec section 4.3).  Runs only when executed directly:
#     python -m tb.dut_helper   (from the repo root)   or
#     python tb/dut_helper.py
# Under cocotb the module is imported (not run), so this never interferes
# with a simulation.  Does not import cocotb or pyuvm.
# ---------------------------------------------------------------------------
def _self_test():
    class _FakeBin:
        def __init__(self, binstr):
            self.binstr = binstr

    # ---- _to_int decoding -------------------------------------------
    assert _to_int(None, 8) == 0
    assert _to_int(7, 8) == 7
    assert _to_int(_FakeBin("10100101"), 8) == 0xA5
    assert _to_int(_FakeBin("1x0z01"), 4) == 0b100001  # x/z -> 0, then binary
    assert _to_int("111", 3) == 0b111
    assert _to_int("tmp", 8) == 0

    # ---- strict sampler ----------------------------------------------
    driven = {"code_out": _FakeBin("10100101")}
    _check_pins_are_driven(driven)          # must not raise (default output)
    _check_pins_are_driven({"data_in": _FakeBin("1")}, source="input")
    for bad in (_FakeBin("1xz00101"), _FakeBin("x"), _FakeBin("z")):
        try:
            _check_pins_are_driven({"code_out": bad})
        except AssertionError:
            pass
        else:
            raise AssertionError("strict sampler failed to reject X/Z")
    for bad_out in (_FakeBin("x"), _FakeBin("z")):
        try:
            _check_pins_are_driven({"data_in": bad_out}, source="input")
        except AssertionError:
            pass
        else:
            raise AssertionError("input strict sampler failed to reject X/Z")

    # ---- geometry (spec section 4.3 table) ---------------------------
    expected = {
        1: (2, 3, 4),
        4: (3, 7, 8),
        8: (4, 12, 13),
        11: (4, 15, 16),
        16: (5, 21, 22),
    }
    for dw, (pb, bw, cw) in expected.items():
        for secded_expected, secded in ((bw, 0), (cw, 1)):
            conf = HammingConf.compute(dw, secded)
            assert conf.parity_bits == pb, conf
            assert conf.base_width == conf.data_width + conf.parity_bits
            assert conf.code_width == (bw if secded == 0 else cw), conf
            assert conf.data_in_max() == (1 << dw) - 1

    assert DEFAULT_CODE_WIDTH == 7  # default elaboration W=4, S=0
    try:
        HammingConf.compute(0, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("HammingConf.compute accepted DATA_WIDTH=0")

    print("dut_helper self-check OK")


if __name__ == "__main__":
    _self_test()