"""Direct DUT pin-access helper for the i2c_master cocotb + pyuvm bench.

Stage 1 (contract) artifact of the CHIA environment generator.

This is plain Python - NOT a SystemVerilog interface.  It centralizes
every access to the cocotb ``dut`` handle so later stages (driver,
monitor, assertions, coverage) use one canonical pin map, exactly as
recorded in CONTRACT.md.  The pin names and widths are authoritative:
they come from ``i2c_master.sv`` / ``rtl_info.json`` and must not be
"discovered" independently by other components.

The module also defines the pyuvm ConfigDB key constants that every
component must use to retrieve shared objects, plus the ``ClockReset``
description object shared through ConfigDB.
"""

from dataclasses import dataclass


# ===========================================================================
# pyuvm ConfigDB keys (EXACT keys recorded in CONTRACT.md).
#
# Components must obtain shared objects with these constants and must NOT
# invent alternative keys.  Standard pyuvm usage:
#
#     write side (test / tb_top / env):
#         ConfigDB().set(None, "*", KEY_DUT, dut)
#         ConfigDB().set(None, "*", KEY_DUT_PINS, I2CDutPins(dut))
#         ConfigDB().set(None, "*", KEY_CLK_RST, ClockReset(...))
#
#     read side (any component):
#         dut   = ConfigDB().get(self, "", KEY_DUT)
#         pins  = ConfigDB().get(self, "", KEY_DUT_PINS)
#         clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
# ===========================================================================
KEY_DUT = "dut"                      # value type: cocotb top-level Module
KEY_DUT_PINS = "i2c_master.dut_pins"  # value type: I2CDutPins instance
KEY_CLK_RST = "i2c_master.clk_rst"    # value type: ClockReset dataclass


# ===========================================================================
# Pin names (verbatim from the RTL).
# ===========================================================================
PIN_CLK = "clk"
PIN_RST_N = "rst_n"
PIN_START = "start"
PIN_RW = "rw"
PIN_SLAVE_ADDR = "slave_addr"
PIN_REG_ADDR = "reg_addr"
PIN_WRITE_DATA = "write_data"
PIN_READ_DATA = "read_data"
PIN_BUSY = "busy"
PIN_DONE = "done"
PIN_ACK_ERROR = "ack_error"
PIN_SCL = "scl"
PIN_SDA = "sda"

# Bit widths of the multi-bit ports.
W_SLAVE_ADDR = 7
W_REG_ADDR = 8
W_WRITE_DATA = 8
W_READ_DATA = 8


@dataclass(frozen=True)
class ClockReset:
    """Structural clock/reset description shared via ConfigDB.

    Attributes codify the RTL clock/reset semantics so the clock generator
    and reset sequences do not disagree with CONTRACT.md:

    - ``clock_name``:    DUT clock port name (``clk``), rising-edge sync.
    - ``reset_name``:    DUT reset port name (``rst_n``).
    - ``reset_polarity``:``"active_low"``.
    - ``reset_type``:    ``"asynchronous"`` (async assert /
                         async deassert; RTL is sensitive to
                         ``negedge rst_n``).
    - ``clock_period_ns``: clock period chosen by tb_top for the
                         simulation (DUT is otherwise agnostic).
    - ``reset_assert_value``: value driven on rst_n while reset is
                         asserted (0 for active-low).
    """

    clock_name: str = PIN_CLK
    reset_name: str = PIN_RST_N
    reset_polarity: str = "active_low"
    reset_type: str = "asynchronous"
    clock_period_ns: int = 10
    reset_assert_value: int = 0


# ---------------------------------------------------------------------------
# Cocotb value -> int coercion.  Outputs are purely 0/1 in this DUT, but
# guarding X/Z makes the bench deterministic instead of raising.
# ---------------------------------------------------------------------------
def _to_int(pin_value, width):
    """Return pin_value as a non-negative int; X/Z bits are read as 0.

    cocotb BinaryValue/LogicArray values (detected via ``binstr``) are
    decoded with ``int()``, which already interprets them as a bit vector.
    Plain strings fall through to character-set classification so that a
    binary-looking vector such as ``"10100101"`` decodes as 165 rather
    than base-10 10100101; X/Z bits are stripped to 0 deterministically.
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


class I2CDutPins:
    """Single canonical wrapper around the cocotb ``dut`` handle.

    Every direct pin access in the generated bench goes through this class,
    using the exact pin names of the RTL (``dut.<pin>``).  The class is
    intentionally dumb: no protocol knowledge, no timing - it only
    converts between Python ints and DUT pin values, so it stays useful to
    every component (driver, monitor, checkers, coverage).
    """

    def __init__(self, dut):
        self.dut = dut

    # ------------------------------------------------------------------
    # Pin handles (read-only convenience accessors)
    # ------------------------------------------------------------------
    @property
    def clk(self):
        return self.dut.clk

    @property
    def rst_n(self):
        return self.dut.rst_n

    @property
    def start(self):
        return self.dut.start

    @property
    def rw(self):
        return self.dut.rw

    @property
    def slave_addr(self):
        return self.dut.slave_addr

    @property
    def reg_addr(self):
        return self.dut.reg_addr

    @property
    def write_data(self):
        return self.dut.write_data

    @property
    def read_data(self):
        return self.dut.read_data

    @property
    def busy(self):
        return self.dut.busy

    @property
    def done(self):
        return self.dut.done

    @property
    def ack_error(self):
        return self.dut.ack_error

    @property
    def scl(self):
        return self.dut.scl

    @property
    def sda(self):
        return self.dut.sda

    # ------------------------------------------------------------------
    # Stimulus side
    # ------------------------------------------------------------------
    def drive_transaction(self, item):
        """Write every stimulus pin from an I2CTransaction item.

        Values are masked to the port width so out-of-range ints cannot
        corrupt neighbouring bits on the RTL port.
        """
        self.dut.start.value = int(item.start) & 0x1
        self.dut.rw.value = int(item.rw) & 0x1
        self.dut.slave_addr.value = int(item.slave_addr) & 0x7F
        self.dut.reg_addr.value = int(item.reg_addr) & 0xFF
        self.dut.write_data.value = int(item.write_data) & 0xFF

    def drive_inputs(self, start=0, rw=0, slave_addr=0, reg_addr=0,
                     write_data=0):
        """Write stimulus pins from explicit ints (driver-level helper)."""
        self.dut.start.value = int(start) & 0x1
        self.dut.rw.value = int(rw) & 0x1
        self.dut.slave_addr.value = int(slave_addr) & 0x7F
        self.dut.reg_addr.value = int(reg_addr) & 0xFF
        self.dut.write_data.value = int(write_data) & 0xFF

    def release_inputs(self):
        """Return stimulus pins to decorrelated / harmless defaults
        (used when not actively driving a transaction)."""
        self.drive_inputs(start=0, rw=0, slave_addr=0, reg_addr=0,
                          write_data=0)

    # ------------------------------------------------------------------
    # Observation side
    # ------------------------------------------------------------------
    def sample_outputs(self):
        """Return a dict of the four output pins sampled immediately.

        Keys: ``read_data`` (int 8 bits), ``busy``, ``done``, ``ack_error``
        (ints, 1 bit).
        """
        return {
            "read_data": _to_int(self.dut.read_data.value, W_READ_DATA),
            "busy": _to_int(self.dut.busy.value, 1),
            "done": _to_int(self.dut.done.value, 1),
            "ack_error": _to_int(self.dut.ack_error.value, 1),
        }

    def sample_into_item(self, item):
        """Capture the observed output pins into ``item``'s output fields.

        Call while the DUT ``done`` pin is high (the monitor does exactly
        this).  ``read_data`` is the value returned by a read transaction.
        """
        outs = self.sample_outputs()
        item.done = outs["done"]
        item.busy = outs["busy"]
        item.ack_error = outs["ack_error"]
        item.read_data = outs["read_data"]

    # ------------------------------------------------------------------
    # Open-drain I2C lines (inouts)
    # ------------------------------------------------------------------
    # scl/sda are open-drain inouts: the DUT drives 0 or releases to
    # high-impedance (Z).  Pull-ups are modelled by the environment
    # (tb_top / driver), so a released line reads 1 where pull-ups are
    # applied and Z otherwise.
    def scl_level(self):
        """Return 0, 1, or 'z' for the raw scl level."""
        s = str(self.dut.scl.value)
        return s if s in ("0", "1", "z", "Z", "x", "X") else s

    def sda_level(self):
        """Return 0, 1, or 'z' for the raw sda level."""
        s = str(self.dut.sda.value)
        return s if s in ("0", "1", "z", "Z", "x", "X") else s

    def scl_is_released(self):
        """True when scl is high-impedance (dut not driving it low)."""
        return str(self.dut.scl.value).lower() in ("z", "1")

    def sda_is_released(self):
        """True when sda is high-impedance (dut not driving it low)."""
        return str(self.dut.sda.value).lower() in ("z", "1")

    # ------------------------------------------------------------------
    # Reset / clock convenience (structural, for tb_top and test)
    # ------------------------------------------------------------------
    def assert_reset(self):
        """Drive the active-low reset asserted (0)."""
        self.dut.rst_n.value = 0

    def deassert_reset(self):
        """Drive the active-low reset deasserted (1)."""
        self.dut.rst_n.value = 1

    def __str__(self):
        return f"I2CDutPins(top={self.dut._name})"