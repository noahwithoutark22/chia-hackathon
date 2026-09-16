"""UVM passive monitor for the axi_handshake DUT.

The monitor samples **all** non-clock/non-reset DUT pins on every rising
clock edge (after combinational settling via ``ReadOnly``) and publishes
an ``AxiHandshakeTxn`` through its ``uvm_analysis_port``.

Timing
------
1. ``await RisingEdge(clk)`` — align to the active clock edge.
2. ``await ReadOnly()`` — allow combinational outputs to settle.
3. Read every DUT pin through the shared ``dut_helper``.
4. Populate an ``AxiHandshakeTxn`` and write it to ``ap``.

The transaction carries **both** the input-side fields (what the driver
was driving) **and** the output-side fields (what the DUT produced),
which is exactly what the scoreboard needs to call the reference model
and compare.

ConfigDB keys consumed (per CONTRACT.md §5):
  - ``"dut"``         — cocotb SimHandleBase
  - ``"dut_helper"``  — DutHelper instance
"""

from cocotb.triggers import RisingEdge, ReadOnly
from pyuvm import uvm_monitor, uvm_analysis_port, ConfigDB

from transaction import AxiHandshakeTxn


class AxiHandshakeMonitor(uvm_monitor):
    """Passive monitor that observes the axi_handshake bus every cycle.

    An ``uvm_analysis_port`` named ``ap`` publishes each sampled
    transaction.  Downstream components (scoreboard, coverage) connect
    to this port.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.ap = uvm_analysis_port("ap", self)

    # ------------------------------------------------------------------
    # UVM build_phase
    # ------------------------------------------------------------------

    def build_phase(self):
        super().build_phase()

    # ------------------------------------------------------------------
    # UVM run_phase — infinite sampling loop
    # ------------------------------------------------------------------

    async def run_phase(self):
        """Sample every cycle and publish the bus state."""
        dut = ConfigDB().get(None, "", "dut")
        dut_helper = ConfigDB().get(None, "", "dut_helper")
        clk = dut.clk

        while True:
            # 1. Align to the next rising clock edge
            await RisingEdge(clk)

            # 2. Allow combinational outputs to settle
            await ReadOnly()

            # 3. Read all DUT pins through the shared helper
            inputs = dut_helper.read_inputs()   # s_valid, s_data, m_ready
            outputs = dut_helper.read_outputs()  # s_ready, m_valid, m_data

            # 4. Build a transaction with the full bus state
            txn = AxiHandshakeTxn()
            txn.set_inputs(
                s_valid=inputs["s_valid"],
                s_data=inputs["s_data"],
                m_ready=inputs["m_ready"],
            )
            txn.set_outputs(
                s_ready=outputs["s_ready"],
                m_valid=outputs["m_valid"],
                m_data=outputs["m_data"],
            )

            # 5. Publish for scoreboard / coverage
            self.ap.write(txn)
