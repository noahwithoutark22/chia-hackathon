"""i2c_master DUT pin-access helper.

Stage-1 CONTRACT artifact.  This is plain Python -- NOT a SystemVerilog
interface -- that centralizes every access to the i2c_master DUT pins
through the cocotb top-level ``dut`` handle (see CONTRACT.md in this
directory).

Why a helper at all: every later cocotb+pyuvm stage (driver, monitor,
scoreboard, assertions, coverage, env, test) reads and writes exactly the
same pins with the same value semantics.  Centralizing the raw
``dut.<pin>.value`` access here keeps those conventions identical across
components and pins every structural constant (clock, reset, timing
budgets, ConfigDB keys) in one place.

Cocotb 2.1.0 public-API notes honored throughout (verified against the
cocotb-2.1.0 wheel):

* Driving a pin: ``dut.<pin>.value = <int>`` (default Deposit action).
* Reading a pin: ``int(dut.<pin>.value)`` -- the documented 2.1.0 read
  path (``int(dut.<pin>)`` casts are deprecated and are never used).
* ``cocotb.handle.ModifiableObject`` is intentionally never imported;
  cocotb 2.1.0 does not export it.  Pin access only uses public handle
  attribute access and ``.value``.
* ``cocotb.clock.Clock(signal, period, unit=...)`` -- the 2.x spelling
  (``units`` was renamed ``unit`` in cocotb 2.0).
* Coroutine helpers use ``cocotb.triggers`` (``RisingEdge``,
  ``ClockCycles``) and ``async``/``await`` only; no ``cocotb.fork``.

The ``I2CPins`` instance (and the raw ``dut`` handle) are shared between
UVM components through pyuvm's ``ConfigDB`` -- exact keys: ``"dut"`` and
``"i2c_pins"`` (defined below and recorded in CONTRACT.md).
"""

try:  # cocotb is always present at simulation time; the fallback
    # exists only so the module's pure-Python self-test (`__main__`) can
    # run in a plain-Python sandbox that does not have cocotb installed.
    from cocotb.clock import Clock
    from cocotb.triggers import ClockCycles, RisingEdge
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    Clock = ClockCycles = RisingEdge = None

# ----------------------------------------------------------------------
# pyuvm ConfigDB keys (EXACT keys recorded in CONTRACT.md).
#
# Components must obtain shared objects with these constants and must NOT
# invent alternative keys.  Standard pyuvm usage:
#
#     write side (test_top / env):
#         ConfigDB().set(None, "*", KEY_DUT, dut)
#         ConfigDB().set(None, "*", KEY_DUT_PINS, I2CPins(dut))
#
#     read side (any component):
#         dut   = ConfigDB().get(None, "", KEY_DUT)
#         pins  = ConfigDB().get(None, "", KEY_DUT_PINS)
# ----------------------------------------------------------------------
KEY_DUT = "dut"             # value type: cocotb top-level DUT handle
KEY_DUT_PINS = "i2c_pins"   # value type: I2CPins instance

# ----------------------------------------------------------------------
# Pin names -- must match CONTRACT.md and the RTL (i2c_master.sv) exactly.
# ----------------------------------------------------------------------
CLK_NAME = "clk"
RST_NAME = "rst_n"
START_NAME = "start"
SLAVE_ADDR_NAME = "slave_addr"
RW_NAME = "rw"
TX_DATA_NAME = "tx_data"
SDA_IN_NAME = "sda_in"
SCL_IN_NAME = "scl_in"
RX_DATA_NAME = "rx_data"
DONE_NAME = "done"
BUSY_NAME = "busy"
ACK_ERROR_NAME = "ack_error"
SDA_OUT_NAME = "sda_out"
SDA_OE_NAME = "sda_oe"
SCL_OUT_NAME = "scl_out"
SCL_OE_NAME = "scl_oe"

# Pin widths in bits (from rtl_info.json / verification plan).
CLK_WIDTH = 1
RST_WIDTH = 1
START_WIDTH = 1
SLAVE_ADDR_WIDTH = 7
RW_WIDTH = 1
TX_DATA_WIDTH = 8
SDA_IN_WIDTH = 1
SCL_IN_WIDTH = 1
RX_DATA_WIDTH = 8
DONE_WIDTH = 1
BUSY_WIDTH = 1
ACK_ERROR_WIDTH = 1
SDA_OUT_WIDTH = 1
SDA_OE_WIDTH = 1
SCL_OUT_WIDTH = 1
SCL_OE_WIDTH = 1

# ----------------------------------------------------------------------
# Structural / timing conventions (authoritative, see CONTRACT.md).
# ----------------------------------------------------------------------
I2C_CLK_PERIOD_NS = 10.0     # default clock period used by the generated TB
CLK_EDGE = "posedge"         # all sequential logic is rising-edge

RST_POLARITY = "active_low"  # rst_n: asserted when 0
RST_STYLE = "synchronous"    # RTL sensitivity: always_ff @(posedge clk)
RST_ACTIVE_VALUE = 0
RST_INACTIVE_VALUE = 1

CLK_DIV_DEFAULT = 4          # DUT parameter default (plan default / test_values)

# Reset / settle cadence (plan scenarios: hold reset >= 4 cycles; family
# convention uses 8).  RESET_CYCLES/SETTLE_CYCLES are consumed by the
# reset sequence and by test_top's initial reset application.
RESET_CYCLES = 8
SETTLE_CYCLES = 2

# Bounded-wait budgets (all in rising-edge clock cycles):
#
# START_TIMEOUT_CYCLES: how long the driver/monitor waits from start
#   offer -> start acceptance (busy rising 0->1) before declaring a hung
#   start.  On a correct RTL, acceptance happens within a few CLK_DIV
#   steps of the offer.
# DONE_TIMEOUT_CYCLES: per-transaction completion budget (start
#   acceptance -> done pulse).  A correct single-byte transaction takes on
#   the order of 21 state advances * CLK_DIV (~340 cycles at CLK_DIV=16);
#   2048 leaves generous margin.  The corrupted RTL never completes (see
#   CONTRACT.md), so this budget is what bounds each hung transaction.
# WATCHDOG_CYCLES: global run bound for the always-running watchdog that
#   test_top arms around the whole pyuvm run.
START_TIMEOUT_CYCLES = 64
DONE_TIMEOUT_CYCLES = 2048
WATCHDOG_CYCLES = 300000

# Read default the TB holds on the bus inputs while idle / between events.
#   sda_in default 1: released high = NACK / no traffic.
#   scl_in default 1: released high; the corrupted RTL never samples
#   scl_in at all (it is documented as sampled but unused).
SDA_IN_IDLE = 1
SCL_IN_IDLE = 1


# ----------------------------------------------------------------------
# Deterministic value coercion.  Outputs are purely 0/1 in this DUT, but
# guarding X/Z makes the bench deterministic instead of raising.
# ----------------------------------------------------------------------
def _to_int(pin_value, width: int) -> int:
    """Return pin_value as a non-negative int; X/Z bits are read as 0.

    Accepts cocotb ``LogicArray``/``BinaryValue`` values (detected via
    ``binstr``), plain strings, and ints.  Binary-looking strings decode
    as binary vectors; X/Z bits are stripped to 0 deterministically.
    """
    if pin_value is None:
        return 0

    if isinstance(pin_value, int):
        # Plain Python ints are already the desired numeric value (they
        # reach this helper from components that sampled cocotb values
        # earlier).  Decoding them via str() would corrupt values such as
        # 111 (0x6F), whose decimal text "111" is also a valid binary
        # string and would be re-read as binary 7.
        return pin_value if pin_value >= 0 else 0

    if hasattr(pin_value, "binstr"):
        try:
            return int(pin_value) & ((1 << width) - 1)
        except (ValueError, TypeError):
            s = pin_value.binstr or ""
    else:
        s = str(pin_value)

    if s == "" or s.isspace():
        return 0

    s = s.replace("x", "0").replace("X", "0")
    s = s.replace("z", "0").replace("Z", "0")
    if set(s) <= {"0", "1"}:
        return int(s, 2) & ((1 << width) - 1)
    try:
        return int(s, 10) & ((1 << width) - 1)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Strict (X/Z-rejecting) output sampling for the completion point.
# ``_to_int`` coerces X/Z to 0 for determinism, which is exactly right for
# stimulus sampling and level checks, but would silently mask an undriven
# (X/Z) *output* as 0/0x00 -- the value the reference model most often
# expects (reset state, cleared rx_data).  These helpers let the monitor
# reject such samples at the completion point, where every output must be
# a genuine 0/1 drive.
# ---------------------------------------------------------------------------
def _has_unknown_bits(pin_value) -> bool:
    """Return True when *pin_value* contains any X or Z bit (4-state value)."""
    if pin_value is None or isinstance(pin_value, int):
        return False
    if hasattr(pin_value, "binstr"):
        s = pin_value.binstr or ""
    else:
        s = str(pin_value)
    s = s.lower()
    return "x" in s or "z" in s


def _check_outputs_are_driven(raw_outputs) -> None:
    """Reject a completion-point output sample that contains any X/Z bit.

    *raw_outputs* maps output name -> the *raw* (pre-``_to_int``) pin
    value.  Raises :class:`AssertionError` when any status output carries
    an X or Z bit, i.e. the DUT never drove that output; a drive-less DUT
    would otherwise be coerced to ``0`` / ``0x00`` by ``_to_int`` and
    could false-pass every oracle that expects the all-zero result.
    """
    unknown = {
        name: str(value)
        for name, value in raw_outputs.items()
        if _has_unknown_bits(value)
    }
    if unknown:
        detail = ", ".join(f"{k}={v!r}" for k, v in unknown.items())
        raise AssertionError(
            "X/Z on DUT outputs sampled at the completion point: "
            f"{detail} (an undriven/tri-stated output must not be silently "
            "coerced to 0 and scored as the reference-model result)"
        )


def make_clock(dut, period_ns: float = I2C_CLK_PERIOD_NS, unit: str = "ns"):
    """Build a cocotb.clock.Clock for ``dut.clk``.

    The caller must ``clock.start()`` it (typically in the cocotb test).
    Public Cocotb 2.1.0 API: ``Clock(signal, period, unit=...)``; ``unit``
    replaced the 1.x ``units`` keyword in cocotb 2.0.
    """
    return Clock(dut.clk, period_ns, unit=unit)


class I2CPins:
    """Named, centralized access to every i2c_master DUT pin.

    ``dut`` is the cocotb top-level handle (the ``dut`` argument passed
    to the test entry point in ``test_top.py``).  Handles are cached as
    attributes so components can write ``pins.tx_data.value = ...`` or use
    the named read/drive helpers below.

    The class is intentionally dumb: no protocol knowledge, no timing --
    it only converts between Python ints and DUT pin values, so it stays
    useful to every component (driver, monitor, scoreboard, assertions,
    coverage).
    """

    def __init__(self, dut) -> None:
        self.dut = dut
        # Structural pins.
        self.clk = dut.clk
        self.rst_n = dut.rst_n
        # Input pins.
        self.start = dut.start
        self.slave_addr = dut.slave_addr
        self.rw = dut.rw
        self.tx_data = dut.tx_data
        self.sda_in = dut.sda_in
        self.scl_in = dut.scl_in
        # Output pins.
        self.rx_data = dut.rx_data
        self.done = dut.done
        self.busy = dut.busy
        self.ack_error = dut.ack_error
        self.sda_out = dut.sda_out
        self.sda_oe = dut.sda_oe
        self.scl_out = dut.scl_out
        self.scl_oe = dut.scl_oe

    # ------------------------------------------------------------------
    # Reset / clock convenience (structural, for tb_top and tests)
    # ------------------------------------------------------------------
    def drive_reset(self, active: bool) -> None:
        """Assert (``active=True``) or deassert the low-active reset."""
        self.rst_n.value = RST_ACTIVE_VALUE if active else RST_INACTIVE_VALUE

    def assert_reset(self) -> None:
        """Drive the active-low reset asserted (0)."""
        self.rst_n.value = RST_ACTIVE_VALUE

    def deassert_reset(self) -> None:
        """Drive the active-low reset deasserted (1)."""
        self.rst_n.value = RST_INACTIVE_VALUE

    async def reset_dut(self, hold_cycles: int = RESET_CYCLES) -> None:
        """Apply the synchronous active-low reset.

        Assert ``rst_n`` low, hold it for ``hold_cycles`` rising clock
        edges (the RTL samples reset on ``posedge clk``), then deassert
        and wait one more rising edge so the first post-reset state is
        settled.  The clock must already be running.
        """
        self.drive_reset(True)
        await ClockCycles(self.clk, max(1, int(hold_cycles)))
        self.drive_reset(False)
        await RisingEdge(self.clk)

    # ------------------------------------------------------------------
    # Drive helpers (input pins)
    # ------------------------------------------------------------------
    def drive_start(self, value: int) -> None:
        self.start.value = int(value) & 0x1

    def drive_slave_addr(self, value: int) -> None:
        self.slave_addr.value = int(value) & 0x7F

    def drive_rw(self, value: int) -> None:
        self.rw.value = int(value) & 0x1

    def drive_tx_data(self, value: int) -> None:
        self.tx_data.value = int(value) & 0xFF

    def drive_sda_in(self, value: int) -> None:
        self.sda_in.value = int(value) & 0x1

    def drive_scl_in(self, value: int) -> None:
        self.scl_in.value = int(value) & 0x1

    def drive_inputs(
        self,
        start: int = 0,
        slave_addr: int = 0,
        rw: int = 0,
        tx_data: int = 0,
        sda_in: int = SDA_IN_IDLE,
        scl_in: int = SCL_IN_IDLE,
    ) -> None:
        """Write stimulus pins from explicit ints (driver-level helper)."""
        self.drive_start(start)
        self.drive_slave_addr(slave_addr)
        self.drive_rw(rw)
        self.drive_tx_data(tx_data)
        self.drive_sda_in(sda_in)
        self.drive_scl_in(scl_in)

    def drive_transaction(self, item) -> None:
        """Write every stimulus pin from an I2CTransaction item.

        Values are masked to the port width so out-of-range ints cannot
        corrupt neighbouring bits on the RTL port.  ``sda_in`` starts at
        the item's default level; the driver owns the per-cycle waveform
        derived from ``item.slave_ack`` / ``item.read_data``.
        """
        self.drive_start(item.start)
        self.drive_slave_addr(item.slave_addr)
        self.drive_rw(item.rw)
        self.drive_tx_data(item.tx_data)
        self.drive_sda_in(item.sda_in)
        self.drive_scl_in(item.scl_in)

    def release_inputs(self) -> None:
        """Return stimulus pins to decorrelated / harmless defaults.

        Used when not actively driving a transaction: ``start`` low, bus
        inputs released high (sda_in/scl_in idle = 1).
        """
        self.drive_inputs(
            start=0,
            slave_addr=0,
            rw=0,
            tx_data=0,
            sda_in=SDA_IN_IDLE,
            scl_in=SCL_IN_IDLE,
        )

    # ------------------------------------------------------------------
    # Read helpers (input + output pins)
    # ------------------------------------------------------------------
    def read_start(self) -> int:
        return _to_int(self.start.value, START_WIDTH)

    def read_slave_addr(self) -> int:
        return _to_int(self.slave_addr.value, SLAVE_ADDR_WIDTH)

    def read_rw(self) -> int:
        return _to_int(self.rw.value, RW_WIDTH)

    def read_tx_data(self) -> int:
        return _to_int(self.tx_data.value, TX_DATA_WIDTH)

    def read_sda_in(self) -> int:
        return _to_int(self.sda_in.value, SDA_IN_WIDTH)

    def read_scl_in(self) -> int:
        return _to_int(self.scl_in.value, SCL_IN_WIDTH)

    def read_rx_data(self) -> int:
        return _to_int(self.rx_data.value, RX_DATA_WIDTH)

    def read_done(self) -> int:
        return _to_int(self.done.value, DONE_WIDTH)

    def read_busy(self) -> int:
        return _to_int(self.busy.value, BUSY_WIDTH)

    def read_ack_error(self) -> int:
        return _to_int(self.ack_error.value, ACK_ERROR_WIDTH)

    def read_sda_out(self) -> int:
        return _to_int(self.sda_out.value, SDA_OUT_WIDTH)

    def read_sda_oe(self) -> int:
        return _to_int(self.sda_oe.value, SDA_OE_WIDTH)

    def read_scl_out(self) -> int:
        return _to_int(self.scl_out.value, SCL_OUT_WIDTH)

    def read_scl_oe(self) -> int:
        return _to_int(self.scl_oe.value, SCL_OE_WIDTH)

    # ------------------------------------------------------------------
    # Aggregate helpers for driver / monitor / scoreboard convenience
    # ------------------------------------------------------------------
    def sample_inputs(self) -> dict:
        """Return the six DUT input pins as currently driven (dict of ints)."""
        return {
            "start": self.read_start(),
            "slave_addr": self.read_slave_addr(),
            "rw": self.read_rw(),
            "tx_data": self.read_tx_data(),
            "sda_in": self.read_sda_in(),
            "scl_in": self.read_scl_in(),
        }

    def sample_outputs(self) -> dict:
        """Return the eight DUT output pins as currently sampled (dict of ints)."""
        return {
            "rx_data": self.read_rx_data(),
            "done": self.read_done(),
            "busy": self.read_busy(),
            "ack_error": self.read_ack_error(),
            "sda_out": self.read_sda_out(),
            "sda_oe": self.read_sda_oe(),
            "scl_out": self.read_scl_out(),
            "scl_oe": self.read_scl_oe(),
        }

    def sample_outputs_strict(self) -> dict:
        """Sample the outputs, rejecting any X/Z bit (completion point).

        For the monitor's completion sampling (CONTRACT.md): while the
        monitor declares a transaction complete every output must be a
        genuine 0/1 drive.  If any status output contains X/Z this raises
        :class:`AssertionError` before ``_to_int`` can coerce the unknown
        bit to 0 -- closing the hole where an undriven output matches the
        reference model's most common expectations (``0`` / ``0x00``).
        """
        raw = {
            "rx_data": self.rx_data.value,
            "done": self.done.value,
            "busy": self.busy.value,
            "ack_error": self.ack_error.value,
        }
        _check_outputs_are_driven(raw)
        return self.sample_outputs()

    def sample_into_item(self, item) -> None:
        """Capture the observed output pins into ``item``'s output fields.

        Call at the completion point (monitor).  Fills ``rx_data``,
        ``done``, ``busy``, ``ack_error`` and the four open-drain control
        outputs ``sda_out``/``sda_oe``/``scl_out``/``scl_oe``.
        """
        outs = self.sample_outputs()
        item.rx_data = outs["rx_data"]
        item.done = outs["done"]
        item.busy = outs["busy"]
        item.ack_error = outs["ack_error"]
        item.sda_out = outs["sda_out"]
        item.sda_oe = outs["sda_oe"]
        item.scl_out = outs["scl_out"]
        item.scl_oe = outs["scl_oe"]

    # ------------------------------------------------------------------
    # Open-drain bus resolution (for the stream checker / assertions)
    # ------------------------------------------------------------------
    def resolve_sda_level(self) -> int:
        """Externally-visible SDA bus level from the DUT's open-drain controls.

        Models the shared bus with an external pull-up: when ``sda_oe``
        deasserts (0) the DUT releases the line and the pull-up drives it
        high (1); when ``sda_oe`` asserts (1) the driven ``sda_out`` value
        appears on the line.
        """
        if self.read_sda_oe() == 0:
            return 1
        return self.read_sda_out()

    def resolve_scl_level(self) -> int:
        """Externally-visible SCL bus level from the DUT's open-drain controls."""
        if self.read_scl_oe() == 0:
            return 1
        return self.read_scl_out()

    def __repr__(self) -> str:
        return f"I2CPins(dut={self.dut!r})"


# ---------------------------------------------------------------------------
# TB-internal unit check for the strict completion-point sampler.  Runs only
# when this module is executed directly (python i2c_pins.py); under cocotb
# the module is imported (not run), so this self-check never interferes with
# a simulation.
# ---------------------------------------------------------------------------
def _self_test_strict_output_sampler() -> None:
    """Check that the strict sampler rejects X/Z and accepts 0/1 samples."""

    class _FakeBin:
        def __init__(self, binstr):
            self.binstr = binstr

    driven = {
        "rx_data": _FakeBin("10100101"),
        "busy": _FakeBin("0"),
        "done": _FakeBin("1"),
        "ack_error": _FakeBin("0"),
    }
    _check_outputs_are_driven(driven)
    decoded = {
        name: _to_int(value, 8 if name == "rx_data" else 1)
        for name, value in driven.items()
    }
    assert decoded == {
        "rx_data": 0xA5,
        "busy": 0,
        "done": 1,
        "ack_error": 0,
    }, decoded

    for bad_name, bad_value in (
        ("rx_data", _FakeBin("1xz00101")),
        ("busy", _FakeBin("x")),
        ("done", _FakeBin("z")),
        ("ack_error", _FakeBin("x")),
    ):
        bad = dict(driven)
        bad[bad_name] = bad_value
        try:
            _check_outputs_are_driven(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(
                f"_check_outputs_are_driven failed to reject X/Z on {bad_name}"
            )
    print("i2c_pins: strict completion-point output sampler self-check OK")


if __name__ == "__main__":
    _self_test_strict_output_sampler()