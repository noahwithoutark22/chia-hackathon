"""UVM agent for the axi_handshake DUT.

Encapsulates the three active components of the verification
environment that sit on the DUT boundary:

  * **Driver**   — drives ``s_valid``, ``s_data``, ``m_ready`` (input side).
  * **Sequencer** — relays sequence items to the driver.
  * **Monitor**  — passively samples **all** DUT pins each cycle and
    publishes ``AxiHandshakeTxn`` through its ``uvm_analysis_port``.

The agent owns these sub-components, wires the driver to the sequencer,
and re-exposes the monitor's analysis port so that the environment
(scoreboard, coverage) can connect to it.

ConfigDB keys consumed (per CONTRACT.md §5):
  - ``"dut"``        — cocotb SimHandleBase (passed through to driver/monitor)
  - ``"dut_helper"`` — DutHelper instance (passed through to monitor)
"""

from pyuvm import uvm_agent, uvm_analysis_port

from driver import AxiHandshakeDriver
from sequencer import AxiHandshakeSequencer
from monitor import AxiHandshakeMonitor


class AxiHandshakeAgent(uvm_agent):
    """Agent that wraps driver + sequencer + monitor for the
    axi_handshake DUT.

    After ``build_phase`` the following attributes are available:

    Attributes
    ----------
    driver : AxiHandshakeDriver
    sequencer : AxiHandshakeSequencer
    monitor : AxiHandshakeMonitor
    monitor_ap : uvm_analysis_port
        Alias to ``monitor.ap`` for convenient connection from the
        environment.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        # Will be created in build_phase
        self.driver = None
        self.sequencer = None
        self.monitor = None
        self.monitor_ap = None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Create sub-components.

        In active mode the driver and sequencer are both created so
        that sequences can run.  The monitor is always created
        (passive observation is always needed).
        """
        super().build_phase()

        # Active components
        self.sequencer = AxiHandshakeSequencer("sequencer", self)
        self.driver = AxiHandshakeDriver("driver", self)

        # Passive component (always present)
        self.monitor = AxiHandshakeMonitor("monitor", self)
        self.monitor_ap = self.monitor.ap

    def connect_phase(self):
        """Wire driver's seq_item_port to the sequencer's export.

        This is the standard UVM TLM connection that allows the driver
        to request the next sequence item from the sequencer.
        """
        super().connect_phase()
        self.driver.seq_item_port.connect(
            self.sequencer.seq_item_export
        )
