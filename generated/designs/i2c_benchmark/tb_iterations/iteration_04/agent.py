"""Stage 3 (observation) artifact of the CHIA generator: the pyuvm agent.

``I2CAgent`` is the hierarchical container that encapsulates the complete
stimulus/observation path of the i2c_master bench:

    I2CSequencer  --seq_item_export <-> seq_item_port-->  I2CDriver
                                                            (drives DUT pins)
    I2CDriver / sequences            ->  DUT pins        -> I2CMonitor
                                                            (samples DUT pins)
    I2CMonitor.analysis_port  --connect-->  agent.analysis_port (to env)

It combines:

* the **stage-2 stimulus components** (``I2CDriver``, ``I2CSequencer``)
  produced in the stimulus generation stage, and
* the **stage-3 monitor** (``I2CMonitor``) produced in this stage.

Connections (made in ``connect_phase``):

    agent.driver.seq_item_port.connect(agent.sequencer.seq_item_export)
    agent.monitor.analysis_port.connect(agent.analysis_port)

The agent is used in its default UVM active mode (pyuvm's ``uvm_agent``
defaults ``is_active`` to ``UVM_ACTIVE``): it contains the driver and
sequencer.  In passive mode (``is_active == UVM_PASSIVE``, configurable via
ConfigDB key ``"is_active"``) only the monitor is built, which is useful if
the env later reuses this agent purely for observation.
"""

from pyuvm import uvm_agent, uvm_analysis_port

from tb.driver import I2CDriver
from tb.monitor import I2CMonitor
from tb.sequencer import I2CSequencer

__all__ = ["I2CAgent"]


class I2CAgent(uvm_agent):
    """Active I2C agent: driver + sequencer + monitor, one analysis port."""

    def __init__(self, name="i2c_agent", parent=None):
        super().__init__(name, parent)
        self.driver = None
        self.sequencer = None
        self.monitor = None
        self.analysis_port = None

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        # pyuvm's uvm_agent.build_phase establishes is_active (default
        # UVM_ACTIVE, overridable via the ConfigDB key "is_active").
        super().build_phase()
        #: Analysis port exported to the environment: receives every
        #: transaction observed by the monitor.
        self.analysis_port = uvm_analysis_port("analysis_port", self)
        #: Passive observer -- always present.
        self.monitor = I2CMonitor("monitor", self)
        if self.active():
            #: Stimulus path -- present only in active mode.
            self.driver = I2CDriver("driver", self)
            self.sequencer = I2CSequencer("sequencer", self)
        else:
            self.logger.info(
                "%s is passive: no driver/sequencer built", self.get_name())

    def connect_phase(self):
        super().connect_phase()
        if self.active():
            # Standard UVM driver <-> sequencer pull connection.
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
        # Monitor observation flows out through the agent-level port.
        self.monitor.analysis_port.connect(self.analysis_port)