"""UVM driver for the axi_handshake DUT.

Drives the three functional input pins (s_valid, s_data, m_ready) on
every rising clock edge, synchronised via cocotb triggers.  The ``dut``
handle and clock signal name are obtained from pyuvm ConfigDB exactly
as specified in CONTRACT.md.

Timing contract
---------------
1. ``await RisingEdge(clk)`` – align to the active clock edge.
2. Apply input signals from the current sequence item.
3. ``await RisingEdge(clk)`` – let the DUT's sequential elements capture.
4. ``await ReadOnly()`` – allow all combinational outputs to settle.
5. ``item_done()`` – hand control back to the sequence.

After step 5 the sequence may safely sample DUT outputs.
"""

from cocotb.triggers import RisingEdge, ReadOnly
from pyuvm import uvm_driver, ConfigDB


class AxiHandshakeDriver(uvm_driver):
    """Drives s_valid / s_data / m_ready onto the DUT each cycle."""

    def __init__(self, name, parent):
        super().__init__(name, parent)

    # ------------------------------------------------------------------
    # UVM run_phase – one transaction per loop iteration
    # ------------------------------------------------------------------

    async def run_phase(self):
        dut = ConfigDB().get(None, "", "dut")
        clk = dut.clk

        while True:
            seq_item = await self.seq_item_port.get_next_item()
            if seq_item is None:
                break

            # --- 1. Wait for the next rising clock edge ----------------
            await RisingEdge(clk)

            # --- 2. Drive DUT input pins --------------------------------
            dut.s_valid.value = seq_item.s_valid & 0x1
            dut.s_data.value = seq_item.s_data & 0xFF
            dut.m_ready.value = seq_item.m_ready & 0x1

            # --- 3. Let the DUT capture on the next edge ----------------
            await RisingEdge(clk)

            # --- 4. Allow combinational outputs to settle ----------------
            await ReadOnly()

            # --- 5. Release the item back to the sequencer ---------------
            self.seq_item_port.item_done()
