"""PyUVM driver for the parameterized adder DUT.

The driver pulls ``AdderTransaction`` items from the sequencer via
``seq_item_port`` and drives the DUT input pins (``a``, ``b``, ``cin``)
on each rising clock edge using the ``DUTHelper`` obtained from the
``ConfigDB``.

Reset and clock management are handled outside the driver — by the
testbench top or by sequences that orchestrate the full test flow.  The
driver only concerns itself with presenting data inputs at the correct
clock edge.

Driving convention (per CONTRACT.md Section 8):
  - After ``RisingEdge(clk)``, set ``a``, ``b``, ``cin`` so that the
    DUT's registered adder captures them on the next ``posedge clk``.
"""

from pyuvm import uvm_driver, ConfigDB
from cocotb.triggers import RisingEdge


class AdderDriver(uvm_driver):
    """Drive ``a``, ``b``, ``cin`` onto the DUT input ports each clock cycle.

    The driver obtains the ``DUTHelper`` from the ``ConfigDB`` (key
    ``"dut_helper"``) during ``build_phase`` and uses it in
    ``run_phase`` to drive inputs synchronised to ``RisingEdge(clk)``.
    """

    def __init__(self, name="adder_driver", parent=None):
        super().__init__(name, parent)

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Retrieve the shared ``DUTHelper`` from the ``ConfigDB``."""
        super().build_phase()
        self.helper = ConfigDB.get(None, "", "dut_helper")

    async def run_phase(self):
        """Main driver loop: get_next_item → RisingEdge → drive → item_done.

        The loop runs for the entire simulation lifetime.  Sequences
        send ``AdderTransaction`` items through the sequencer; the
        driver consumes them one at a time and drives the corresponding
        DUT pins.
        """
        clk = self.helper._clk

        while True:
            # Block until a sequence provides a new item.
            item = await self.seq_item_port.get_next_item()

            # Synchronise to the next positive clock edge before driving.
            await RisingEdge(clk)

            # Apply data inputs via the helper (sets a, b, cin).
            await self.helper.set_inputs(item.a, item.b, item.cin)

            self.logger.info(
                "Drive  a=0x%02X  b=0x%02X  cin=%0d",
                item.a,
                item.b,
                item.cin,
            )

            # Signal to the sequencer that we are done with this item.
            self.seq_item_port.item_done()
