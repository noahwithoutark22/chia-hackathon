"""FIFO observation monitor (pyuvm ``uvm_monitor``).

This component implements the *observation* side of the FIFO testbench: it
samples the DUT pins on every rising clock edge and broadcasts one
:class:`FifoTransaction` per cycle on a ``uvm_analysis_port`` for the
scoreboard.  Pin names, widths, directions, and the sampling timing
relationship are frozen in CONTRACT.md:

    clk    input  / 1            -> dut.clk    (edge reference only)
    rst_n  input  / 1            -> dut.rst_n  (NOT a transaction field)
    wr_en  input  / 1            -> dut.wr_en  (sampled per edge)
    rd_en  input  / 1            -> dut.rd_en  (sampled per edge)
    din    input  / DATA_WIDTH   -> dut.din    (sampled per edge)
    dout   output / DATA_WIDTH   -> dut.dout   (registered, latency 1)
    full   output / 1            -> dut.full   (combinational)
    empty  output / 1            -> dut.empty  (combinational)

Sampling convention (CONTRACT.md §2): sample ``dut.dout``, ``dut.full``,
``dut.empty`` *after* each rising edge (post-edge values).  ``dout`` is a
registered output with latency 1, so the value read after an edge at which a
read was accepted is the entry that was popped.  Because the RTL updates
``wr_ptr``/``rd_ptr``/``count``/``dout`` with nonblocking assignments and
``full``/``empty`` are re-derived through an ``always_comb`` block, the
monitor synchronizes on ``RisingEdge(dut.clk)`` and then waits for cocotb's
read-only phase (``ReadOnly()``): by then every delta step of the timestep
has settled, so the sampled values are final post-edge values.  This is the
canonical pyuvm monitor pattern and replaces a SystemVerilog clocking-block
/ monitor.

Published items carry exactly the fields of :class:`FifoTransaction`
(CONTRACT.md §5): the driven inputs ``wr_en``/``rd_en``/``din`` exactly as
the DUT sampled them on the edge, the observed outputs
``dout``/``full``/``empty``, and the bookkeeping ``dut_cycle`` (a 0-based
index of the sampled rising edge).  The monitor samples *every* edge,
including edges while the asynchronous reset is asserted; reset is not a
transaction field, so downstream consumers (scoreboard/tests) must observe
``dut.rst_n`` directly to align their reference-model state across the
reset injections performed by the sequences.
"""

from cocotb.triggers import ReadOnly, RisingEdge
from pyuvm import ConfigDB, uvm_analysis_port, uvm_monitor

from transaction import FifoTransaction


class FifoMonitor(uvm_monitor):
    """Samples the FIFO pins post-edge and publishes one transaction per
    rising clock edge on the ``fifo_analysis_port``."""

    def __init__(self, name="fifo_monitor", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.data_width = 8   # elaborated value, resolved in build_phase
        self.depth = 4        # elaborated value, resolved in build_phase
        self._helper = None
        self.ap = None                    # uvm_analysis_port, build_phase
        self._edge_index = 0              # rising-edge counter for dut_cycle

    def build_phase(self):
        """Resolve the shared DUT config (CONTRACT.md §4, keys exact) and
        create the analysis port."""
        super().build_phase()
        # Access form is frozen by CONTRACT.md §9.1 (keys unchanged from §4).
        self.dut = ConfigDB().get(None, "*", "dut")
        self.data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
        self.depth = int(ConfigDB().get(None, "*", "DEPTH"))
        # FifoDutHelper is optional sugar (CONTRACT.md §4); build one if the
        # tb_top layer did not already share it.
        try:
            from dut_helper import FifoDutHelper

            helper = ConfigDB().get(None, "*", "FifoDutHelper", default=None)
            self._helper = (
                helper if helper is not None else FifoDutHelper(self.dut, self.data_width)
            )
        except Exception:  # pragma: no cover - helper is optional
            self._helper = None
        # Analysis port broadcast to scoreboards/subscribers (UVM).  The
        # scoreboard stage connects it (directly or via a
        # uvm_tlm_analysis_fifo); connect() is validated by pyuvm.
        self.ap = uvm_analysis_port("fifo_analysis_port", self)

    # -- sampling ---------------------------------------------------------
    def _read(self, pin):
        """Read a DUT pin as a plain Python ``int`` (exact pin names from
        CONTRACT.md §2)."""
        return int(getattr(self.dut, pin).value)

    def _sample(self):
        """Build one fully-populated :class:`FifoTransaction` from the
        current post-edge, read-only bus values."""
        item = FifoTransaction(f"{self.get_name()}_item")
        # Stimulus inputs exactly as the DUT sampled them on this edge.
        item.wr_en = self._read("wr_en")
        item.rd_en = self._read("rd_en")
        item.din = self._read("din")
        # Observed outputs: post-edge values (dout latency 1).
        if self._helper is not None:
            obs = self._helper.sample()
            item.dout = obs["dout"]
            item.full = obs["full"]
            item.empty = obs["empty"]
        else:
            item.dout = self._read("dout")
            item.full = self._read("full")
            item.empty = self._read("empty")
        # Monitor bookkeeping: index of the sampled rising edge.
        item.dut_cycle = self._edge_index
        return item

    # -- main loop ---------------------------------------------------------
    async def run_phase(self):
        """Sample the DUT on every rising edge and broadcast a transaction."""
        self.logger.info(
            "FifoMonitor started (DATA_WIDTH=%d, DEPTH=%d)",
            self.data_width, self.depth,
        )
        while True:
            await RisingEdge(self.dut.clk)
            # Same timestep, read-only region: all nonblocking RTL updates
            # (count/wr_ptr/rd_ptr/dout) and the combinational re-derivation
            # of full/empty have settled -> final post-edge values.
            await ReadOnly()
            item = self._sample()
            self._edge_index += 1
            self.ap.write(item)
            self.logger.debug(
                "cycle %d: wr=%d rd=%d din=%#x dout=%#x full=%d empty=%d",
                item.dut_cycle, item.wr_en, item.rd_en, item.din, item.dout,
                item.full, item.empty,
            )