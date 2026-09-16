"""FifoDutHelper: centralized direct pin access to the ``fifo`` DUT.

This is plain Python (NOT a SystemVerilog interface).  It wraps the
cocotb ``dut`` handle so that every DUT pin is accessed through exactly
one place, using the pin names and widths recorded in CONTRACT.md.

``dut`` itself is shared across components via ConfigDB under the key
``"dut"`` (see CONTRACT.md).  The helper is optional; later stages may
drive ``dut.<pin>`` directly, but should prefer this module so access
conventions never drift.

Pins (direction / width / access):
    clk    input  / 1            -> dut.clk
    rst_n  input  / 1            -> dut.rst_n
    wr_en  input  / 1            -> dut.wr_en
    rd_en  input  / 1            -> dut.rd_en
    din    input  / DATA_WIDTH   -> dut.din
    dout   output / DATA_WIDTH   -> dut.dout
    full   output / 1            -> dut.full
    empty  output / 1            -> dut.empty

Stimulus applied through the helper is always injected *synchronously*:
value drives are performed with ``value.setimmediatevalue()`` inside the
``cocotb.test``/driver coroutine context, so they are not gated by any
signal-change trigger.  Callers that want HDL-level timing should use
``dut.pre_clock``/``dut.post_clock`` cocotb scheduling hooks instead.
"""

from cocotb.triggers import FallingEdge, RisingEdge, Timer


class FifoDutHelper:
    """Thin, read-only-by-convention wrapper around the cocotb ``dut``."""

    def __init__(self, dut, data_width: int = 8):
        """Bind the helper to a cocotb DUT handle.

        Args:
            dut: the cocotb handle for top-level module ``fifo``.
            data_width: DATA_WIDTH parameter of the DUT (default 8);
                used only for width validation helpers.
        """
        self.dut = dut
        self.data_width = data_width
        self._validate()

    # -- Validation -----------------------------------------------------
    def _validate(self) -> None:
        """Fail eagerly if the dut handle lacks any contracted pin."""
        for pin in ("clk", "rst_n", "wr_en", "rd_en", "din", "dout",
                    "full", "empty"):
            assert hasattr(self.dut, pin), f"DUT missing pin '{pin}'"

    # -- Structural accessors -------------------------------------------
    @property
    def clk(self):
        return self.dut.clk

    @property
    def rst_n(self):
        return self.dut.rst_n

    @property
    def wr_en(self):
        return self.dut.wr_en

    @property
    def rd_en(self):
        return self.dut.rd_en

    @property
    def din(self):
        return self.dut.din

    @property
    def dout(self):
        return self.dut.dout

    @property
    def full(self):
        return self.dut.full

    @property
    def empty(self):
        return self.dut.empty

    # -- Clock / reset helpers -------------------------------------------
    async def clock(self, half_period_ns: int = 5) -> None:
        """(Deprecated stub) Prefer dedicated clock coroutines in tb_top.

        Kept so later stages always have a single place to change clock
        generation if the period changes.
        """
        del half_period_ns  # placeholder; real clock lives in tb_top
        raise NotImplementedError(
            "Clock generation is owned by the tb_top stage; use those coroutines.")

    async def reset_async_active_low(self) -> None:
        """Drive the asynchronous active-low reset: pulse ``rst_n`` low."""
        self.dut.rst_n.setimmediatevalue(0)
        await FallingEdge(self.dut.clk)   # deassert on a falling edge
        await RisingEdge(self.dut.clk)    # let one cycle pass asserted
        self.dut.rst_n.setimmediatevalue(1)
        await RisingEdge(self.dut.clk)    # settle out of reset
        await Timer(1, units="ns")

    # -- Drive / sample conveniences -------------------------------------
    def drive(self, wr_en: int, rd_en: int, din: int) -> None:
        """Synchronously drive stimulus inputs.

        Uses ``setimmediatevalue`` so values are in effect for the next
        rising clock edge without waiting on a signal-trigger event.
        ``din`` is masked to DATA_WIDTH bits.
        """
        self.dut.wr_en.setimmediatevalue(int(wr_en) & 0x1)
        self.dut.rd_en.setimmediatevalue(int(rd_en) & 0x1)
        mask = (1 << self.data_width) - 1
        self.dut.din.setimmediatevalue(int(din) & mask)

    def sample(self) -> dict:
        """Sample all DUT outputs combinationally.

        Returns dict with integer values: ``{"dout":..., "full":...,
        "empty":...}``.  ``dout`` is the registered output; sample after
        a rising edge for post-edge values (see CONTRACT.md latency=1).
        """
        return {
            "dout": int(self.dut.dout.value),
            "full": int(self.dut.full.value),
            "empty": int(self.dut.empty.value),
        }