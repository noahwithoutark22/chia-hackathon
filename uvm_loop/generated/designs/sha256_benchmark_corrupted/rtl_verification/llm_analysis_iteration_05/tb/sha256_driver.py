"""SHA-256 UVM driver (stage-2 STIMULUS artifact).

Pin-driving component for the cocotb + pyuvm verification environment
described by CONTRACT.md.  The driver consumes one ``Sha256Transaction``
at a time from ``seq_item_port`` and transfers it onto the DUT input pins
(``start``, ``block``) synchronized to ``dut.clk``.

DRIVER PROTOCOL (documented convention, the whole environment depends on
it -- see the CONTRACT.md stage-2 note):

* Each received item with ``start == 1`` is driven as exactly ONE `start`
  pulse of minimum width ("one cycle" in sampling terms): the RTL samples
  ``start`` on the rising edge of ``clk``, and the driver guarantees that
  exactly one rising edge observes ``start == 1`` per item, with ``start == 0``
  on the neighbouring rising edges.
* ``block`` is placed on the bus a full clock period before the sampling
  edge and is held stable across it (the RTL captures ``block`` on the
  same edge as ``start == 1``).
* To avoid delta-cycle races at the sampling edge, all input changes are
  made on / just after *falling* edges, so every value is settled for a
  full half clock period before the rising edge that samples it.
* An item with ``start == 0`` is a "no-drive" item: the driver leaves the
  input pins idle and completes the item immediately (used if a future
  stimulus wants to handshake without asserting start).

ConfigDB: the driver reads ``"sha256_pins"`` (a ``Sha256Pins`` instance)
in ``build_phase`` -- exact key from CONTRACT.md §5.  It never touches
the raw ``dut`` handle directly.
"""

from pyuvm import ConfigDB, uvm_driver

from cocotb.triggers import FallingEdge

from sha256_pins import Sha256Pins


class Sha256Driver(uvm_driver):
    """Pulses ``start`` and drives ``block`` for each sequence item."""

    def __init__(self, name: str = "sha256_driver", parent=None) -> None:
        super().__init__(name, parent)
        self.pins = None  # type: Sha256Pins  (populated in build_phase)

    def build_phase(self) -> None:
        """Fetch the shared ``Sha256Pins`` helper from ConfigDB.

        Exact key: ``"sha256_pins"`` (CONTRACT.md §5).  Raising here fails
        the test early if the environment was assembled without the key.
        """
        super().build_phase()
        self.pins = ConfigDB().get(None, "", "sha256_pins")
        if self.pins is None:
            self.logger.error(
                "CONTRACT key 'sha256_pins' missing from ConfigDB: "
                "cannot drive the DUT."
            )
            raise RuntimeError(
                "Sha256Driver.build_phase: ConfigDB key 'sha256_pins' not found"
            )

    async def run_phase(self) -> None:
        """Drive every received item and ack it when the pulse is done."""
        self._idle_inputs()
        while True:
            item = await self.seq_item_port.get_next_item()
            self.logger.debug("Driving item: %s", item.convert2string())
            await self._drive_item(item)
            self.seq_item_port.item_done()

    # ------------------------------------------------------------------
    # Pin-driving internals
    # ------------------------------------------------------------------
    def _idle_inputs(self) -> None:
        """Drive the input pins to a known deasserted state at time zero
        (avoids sampling X's before the first transaction)."""
        self.pins.drive_start(0)
        self.pins.drive_block(0)

    async def _drive_item(self, item) -> None:
        """Implement the driver protocol on the DUT input pins.

        Falling-edge schedule (F0 / F1 / F2 are consecutive falling edges;
        the rising edges between them are the DUT sampling edges):

            F0: drive ``block`` = item.block, ``start`` = 0
            F1: drive ``start``  = 1   -> exactly one rising edge samples
                                          (block, start=1)  [transaction edge]
            F2: drive ``start``  = 0, ``block`` = 0
        """
        if int(item.start) == 0:
            # No-drive item: leave the bus idle, only re-sync to the clock.
            await FallingEdge(self.pins.clk)
            self.pins.drive_start(0)
            self.pins.drive_block(0)
            return

        # F0: place the block on the bus one full cycle before sampling.
        await FallingEdge(self.pins.clk)
        self.pins.drive_block(int(item.block))
        self.pins.drive_start(0)

        # F1: assert start; the next rising edge captures block + start.
        await FallingEdge(self.pins.clk)
        self.pins.drive_start(1)

        # F2: deassert; start is high for exactly one sampled clock cycle.
        await FallingEdge(self.pins.clk)
        self.pins.drive_start(0)
        self.pins.drive_block(0)