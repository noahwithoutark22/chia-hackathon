"""Direct DUT pin-access helper for the AES-128 cocotb+pyuvm testbench.

Centralizes all access to the cocotb ``dut`` handle so later stages
(driver, monitor, checker, etc.) never hard-code pin names inline.
This is plain Python, NOT a SystemVerilog interface.

The helper object is shared between UVM components through pyuvm's
ConfigDB under the key ``"dut_helper"`` (see CONTRACT.md).

Pin access convention (exactly as recorded in CONTRACT.md):
    write:  dut.start.value = x
            dut.key.value = value  (value as int, <= 2**128 - 1)
            dut.plaintext.value = value
    read:   dut.ciphertext.value   -> int
            dut.busy.value         -> int (0 or 1)
            dut.done.value         -> int (0 or 1)
"""

# Stage-5 compatibility fix: cocotb 2.1.0 (the pinned runtime, CONTRACT.md
# section 7.3) only exports ``SimHandleBase`` (``SimHandle`` was removed in
# cocotb 2.0).  This name is used for typing only, so aliasing it is safe.
from cocotb.handle import SimHandleBase as SimHandle  # typing only


class AES128DUTHelper:
    """Thin wrapper that names every AES-128 DUT pin access.

    Attributes mirror the DUT port names. Reads return plain ``int``;
    writes accept plain ``int``.
    """

    # ── Signal metadata (single source of truth for pin names) ────────
    CLOCK_SIGNAL = "clk"
    RESET_SIGNAL = "rst_n"

    # Widths from rtl_info.json / aes128.sv
    WIDTH_KEY = 128
    WIDTH_PLAINTEXT = 128
    WIDTH_CIPHERTEXT = 128

    def __init__(self, dut):
        """Wrap a validated cocotb ``dut`` handle.

        ``dut`` must expose the exact pins listed in CONTRACT.md.
        An ``AttributeError``/``ValueError`` is raised here (fail fast)
        if any pin is missing, so misnamed RTL ports surface at build
        time rather than deep inside a test.
        """
        self.dut = dut
        self._check_pins()

    def _check_pins(self):
        missing = [p for p in self.pin_names() if not hasattr(self.dut, p)]
        if missing:
            raise AttributeError(
                f"DUT is missing pins {missing}; expected exact port list: "
                f"{self.pin_names()}"
            )

    @classmethod
    def pin_names(cls):
        """All DUT pins in canonical order, excluding clock/reset."""
        return ["start", "key", "plaintext", "ciphertext", "busy", "done"]

    # ── Reset ---------------------------------------------------------
    @property
    def rst_n(self):
        return self.dut.rst_n.value

    @rst_n.setter
    def rst_n(self, value: int):
        self.dut.rst_n.value = value

    # ── Inputs (write path) -------------------------------------------
    @property
    def start(self):
        return self.dut.start.value

    @start.setter
    def start(self, value: int):
        self.dut.start.value = value

    @property
    def key(self):
        return self.dut.key.value

    @key.setter
    def key(self, value: int):
        if not (0 <= value < (1 << self.WIDTH_KEY)):
            raise ValueError(f"key out of range for {self.WIDTH_KEY} bits: {value}")
        self.dut.key.value = value

    @property
    def plaintext(self):
        return self.dut.plaintext.value

    @plaintext.setter
    def plaintext(self, value: int):
        if not (0 <= value < (1 << self.WIDTH_PLAINTEXT)):
            raise ValueError(
                f"plaintext out of range for {self.WIDTH_PLAINTEXT} bits: {value}"
            )
        self.dut.plaintext.value = value

    # ── Outputs (read path) -------------------------------------------
    @property
    def ciphertext(self):
        return self.dut.ciphertext.value

    @property
    def busy(self):
        return self.dut.busy.value

    @property
    def done(self):
        return self.dut.done.value

    # ── Grouped helpers -----------------------------------------------
    def drive_command(self, start: int, key: int, plaintext: int) -> None:
        """Drive all input pins at once."""
        self.start = start
        self.key = key
        self.plaintext = plaintext

    def sample_outputs(self):
        """Read all output pins, returns ``(ciphertext, busy, done)`` ints."""
        return self.ciphertext, self.busy, self.done

    def __repr__(self):
        return (
            f"AES128DUTHelper("
            f"start={int(self.start)}, "
            f"key=0x{int(self.key):032x}, "
            f"plaintext=0x{int(self.plaintext):032x}, "
            f"ciphertext=0x{int(self.ciphertext):032x}, "
            f"busy={int(self.busy)}, "
            f"done={int(self.done)})"
        )


def make_dut_helper(dut):
    """Construct an :class:`AES128DUTHelper` from a cocotb ``dut`` handle."""
    return AES128DUTHelper(dut)