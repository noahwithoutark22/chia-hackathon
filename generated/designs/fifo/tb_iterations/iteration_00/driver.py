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

Back-to-back support: after ``item_done()``, the driver immediately checks
whether the sequencer already has the next item queued (via
``try_next_item()``).  If so, the new item is applied on the **same**
falling edge, eliminating the idle cycle between consecutive items.  When
the sequencer has no item ready, an idle cycle (``wr_en=0``, ``rd_en=0``)
is inserted as before, and the driver blocks on ``get_next_item()`` until
the next item arrives.

Consequence: when a sequence's ``finish_item()`` returns, the item has been
sampled by the DUT and the outputs read from ``dut.dout/full/empty`` are
settled.  Sequences rely on this convention for their inline checks.
"""

from cocotb.triggers import FallingEdge
from pyuvm import ConfigDB, uvm_driver


class FifoDriver(uvm_driver):
    """Drives FIFO pins from sequences; one item per DUT clock cycle.

    Supports back-to-back operation: when the sequencer immediately
    provides the next item, it is applied on the very next falling edge
    without an intervening idle cycle.
    """

    def __init__(self, name="fifo_driver", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.data_width = 8
        self.depth = 4
        self._helper = None
        self._has_try_next = False  # resolved in build_phase

    def build_phase(self):
        """Resolve the shared DUT config (CONTRACT.md §4, keys exact)."""
        super().build_phase()
        self.dut = ConfigDB().get(None, "*", "dut")
        self.data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
        self.depth = int(ConfigDB().get(None, "*", "DEPTH"))
        # Check whether the sequencer port exposes try_next_item() (UVM
        # standard).  When available the driver can eliminate idle cycles
        # between consecutive items (W-NO-BACK-TO-BACK fix).
        self._has_try_next = hasattr(self.seq_item_port, "try_next_item")
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

        Back-to-back support (W-NO-BACK-TO-BACK): after releasing the
        sequence with ``item_done()``, the driver immediately tries
        ``try_next_item()``.  If the next item is already queued, it is
        driven on the **same** falling edge (no idle cycle).  Otherwise
        an idle cycle is driven and the driver blocks on
        ``get_next_item()``.

        The ``driven_on_this_fe`` flag prevents a double-drive when the
        back-to-back item was already applied on the current falling edge;
        the next iteration skips the ``await FallingEdge + drive`` pair
        and goes directly to the sampling ``await FallingEdge``.
        """
        self._drive_idle()
        item = await self.seq_item_port.get_next_item()
        driven_on_this_fe = False
        while True:
            # Drive the item on the falling edge (unless it was already
            # driven on this edge by the back-to-back path).
            if not driven_on_this_fe:
                await FallingEdge(self.dut.clk)
                self._drive(item.wr_en, item.rd_en, item.din)
            driven_on_this_fe = False
            # The rising edge between the previous FE and this FE samples
            # the driven values; by this FE all DUT outputs have settled.
            await FallingEdge(self.dut.clk)
            self.seq_item_port.item_done()
            self.logger.debug(
                "drove item: wr_en=%d rd_en=%d din=%#x",
                int(item.wr_en), int(item.rd_en), int(item.din),
            )
            # --- Back-to-back check --------------------------------
            # After item_done(), the sequence's finish_item() returns
            # synchronously and, if the sequence immediately queues the
            # next item (consecutive start_item/finish_item calls), that
            # item is already in the sequencer FIFO.  try_next_item()
            # returns it without blocking; we drive it on THIS FE so the
            # next rising edge samples the new item (no idle cycle).
            if self._has_try_next:
                try:
                    next_item = self.seq_item_port.try_next_item()
                except Exception:
                    next_item = None
            else:
                next_item = None

            if next_item is not None:
                self._drive(next_item.wr_en, next_item.rd_en, next_item.din)
                item = next_item
                driven_on_this_fe = True
                self.logger.debug(
                    "back-to-back: wr_en=%d rd_en=%d din=%#x",
                    int(next_item.wr_en), int(next_item.rd_en),
                    int(next_item.din),
                )
            else:
                # No back-to-back item: drive idle and block until the
                # next item arrives.
                self._drive_idle()
                item = await self.seq_item_port.get_next_item()