"""hamming_encoder pyuvm agent (stage 3: OBSERVATION).

``HammingAgent`` groups the stimulus-side components created in stage 2
(:class:`~tb.driver.HammingDriver`, :class:`~tb.sequencer.HammingSequencer`)
with this stage's passive :class:`~tb.monitor.HammingMonitor` and wires them
together exactly as the integration stages expect:

* ``driver.seq_item_port`` -> ``sequencer.seq_item_export`` (the standard
  UVM request/response machinery that lets sequences run items through the
  driver), and
* ``monitor_ap`` re-exposes ``monitor.ap`` so the environment (scoreboard,
  coverage, etc.) can subscribe to observed transactions.

The agent is **active** (``is_active == UVM_ACTIVE``): the DUT has no
handshake and no valid signal (CONTRACT.md section 3), so solely driving
without observing is meaningless.  Passive monitor-only operation is not
useful for this bench, so only the active configuration is wired.

ConfigDB keys: none read by the agent itself -- the shared objects
(``KEY_DUT_PINS`` / ``KEY_CLK_RST`` / ``KEY_CONF``) are resolved by the
driver and by the monitor in their own ``build_phase`` calls
(CONTRACT.md section 6).
"""

from pyuvm import uvm_agent

from tb.driver import HammingDriver
from tb.monitor import HammingMonitor
from tb.sequencer import HammingSequencer

__all__ = ["HammingAgent"]


class HammingAgent(uvm_agent):
    """Active agent: driver + sequencer on the stimulus side, monitor on
    the observation side, all internally wired."""

    def __init__(self, name="hamming_agent", parent=None):
        super().__init__(name, parent)
        self.sequencer = None
        self.driver = None
        self.monitor = None
        self.monitor_ap = None

    def build_phase(self):
        """Build the sequencer, driver and monitor child components.

        The DUT is always actively driven and observed (no passive support is
        wired), so ``uvm_agent.build_phase`` keeps ``is_active == UVM_ACTIVE``.
        The shared ConfigDB objects are resolved by the children themselves.
        """
        super().build_phase()
        self.sequencer = HammingSequencer("sequencer", self)
        self.driver = HammingDriver("driver", self)
        self.monitor = HammingMonitor("monitor", self)
        self.monitor_ap = self.monitor.ap

    def connect_phase(self):
        """Connect the driver's seq_item_port to the sequencer."""
        super().connect_phase()
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)