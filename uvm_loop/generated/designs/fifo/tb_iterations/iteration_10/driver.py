"""FIFO stimulus driver (pyuvm ``uvm_driver``).

This component transfers, one transaction at a time, the items produced by
sequences on the ``FifoSequencer`` to the DUT pins.  Pin names, widths, and
access conventions are frozen in CONTRACT.md:

    wr_en  -> dut.wr_en   (1 bit)
    rd_en  -> dut.rd_en   (1 bit)
    din    -> dut.din     (DATA_WIDTH bits)

Clock and reset are NOT transaction fields (CONTRACT.md): ``clk`` is owned
by the clock generator in tb_top and ``rst_n`` is driven directly by the
sequences (reset is not part of the sequence item).

Stimulus/drive convention (contract §2): values are applied synchronously
with ``setimmediatevalue`` so they are stable for the next rising edge.  The
driver applies every item for exactly one DUT clock cycle:

    1. ``get_next_item()`` returns (the sequence has already called
       ``finish_item()``, which released the item into the driver),
    2. align to a falling edge and drive the item's pins; the values are
       sampled by the DUT on the *next* rising edge,
    3. wait for the following falling edge (half a period after the sampling
       edge, by which time all registered outputs and combinational flags
       have settled),
    4. ``item_done()``, which releases the sequence's ``finish_item()``.

Consequence: when a sequence's ``finish_item()`` returns, the item has been
sampled by the DUT and the outputs read from ``dut.dout/full/empty`` are
settled.  Sequences rely on this convention for their inline checks.

Drive stability (W-DRIVER-TRY-NEXT-CRASH fix): the driver uses only the
blocking ``get_next_item()``/``item_done()`` sequencer API, which returns
the sequence item itself.  The previous back-to-back optimization used
``try_next_item()``, which on the pinned runtime pyuvm returns a *Boolean
availability flag* rather than the item (or a ``(item, seq_id)`` tuple on
other versions).  Unconditionally treating that Boolean as an item crashed
every data-path test with ``AttributeError: 'bool' object has no attribute
'wr_en'``.  The blocking API is version-stable and always yields the item
itself.  Consecutive items each drive the DUT for one full cycle; the
CONTRACT §9.3 "wall" (an idle cycle between items) is preserved, which is a
declared no-op for FIFO semantics and does not weaken any functional check.
"""

from cocotb.triggers import FallingEdge
from pyuvm import ConfigDB, uvm_driver


class FifoDriver(uvm_driver):
    """Drives FIFO pins from sequences; one item per DUT clock cycle."""

    def __init__(self, name="fifo_driver", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.data_width = 8
        self.depth = 4
        self._helper = None

    def build_phase(self):
        """Resolve the shared DUT config (CONTRACT.md §4, keys exact)."""
        super().build_phase()
        self.dut = ConfigDB().get(None, "*", "dut")
        self.data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
        self.depth = int(ConfigDB().get(None, "*", "DEPTH"))
        # The FifoDutHelper is optional sugar (CONTRACT.md §4); build one if
        # the tb_top layer did not already share it.
        try:
            from dut_helper import FifoDutHelper

            helper = ConfigDB().get(None, "*", "FifoDutHelper", default=None)
            self._helper = (
                helper if helper is not None else FifoDutHelper(self.dut, self.data_width)
            )
        except Exception:  # pragma: no cover - helper is optional
            self._helper = None

    # -- Pin driving ---------------------------------------------------
    def _drive(self, wr_en, rd_en, din):
        """Apply one set of stimulus values; din is masked to DATA_WIDTH."""
        if self._helper is not None:
            self._helper.drive(wr_en, rd_en, din)
        else:
            self.dut.wr_en.setimmediatevalue(int(wr_en) & 0x1)
            self.dut.rd_en.setimmediatevalue(int(rd_en) & 0x1)
            mask = (1 << self.data_width) - 1
            self.dut.din.setimmediatevalue(int(din) & mask)

    def _drive_idle(self):
        """Deassert all stimulus inputs (no-op cycle for the DUT)."""
        self._drive(0, 0, 0)

    # -- Main loop ------------------------------------------------------
    async def run_phase(self):
        """Pull items from the sequencer and apply one per clock cycle.

        (W-DRIVER-TRY-NEXT-CRASH fix) Only the blocking
        ``get_next_item()``/``item_done()`` sequencer API is used — it
        returns the sequence item itself on every pyuvm version, so the
        driver never dereferences a Boolean or a tuple.  Each item is
        applied for one full DUT clock cycle: align to a falling edge,
        drive the pins (sampled on the next rising edge), wait for the
        following falling edge (by which time all registered outputs and
        combinational flags have settled), then ``item_done()`` to release
        the sequence.  An idle cycle (``wr_en=0``, ``rd_en=0``) is driven
        before blocking for the next item, preserving CONTRACT §9.3's
        declared idle "wall" between consecutive items (a no-op for FIFO
        semantics).
        """
        self._drive_idle()
        while True:
            # Blocks until the sequence has released an item to the
            # sequencer (the item itself is returned — never a bool).
            item = await self.seq_item_port.get_next_item()
            # Align to the falling edge and drive the item's pins; the DUT
            # samples them on the next rising edge.
            await FallingEdge(self.dut.clk)
            self._drive(item.wr_en, item.rd_en, item.din)
            # Wait for the following falling edge: by then the rising edge
            # has sampled the values and all DUT outputs have settled.
            await FallingEdge(self.dut.clk)
            self.seq_item_port.item_done()
            self.logger.debug(
                "drove item: wr_en=%d rd_en=%d din=%#x",
                int(item.wr_en), int(item.rd_en), int(item.din),
            )
            # Idle cycle (CONTRACT §9.3 wall), then block once more.
            self._drive_idle()