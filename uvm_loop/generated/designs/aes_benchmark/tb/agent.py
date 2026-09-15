"""Stage 3 (observation) artifact of the CHIA generator: the pyuvm agent.

``AES128Agent`` is the hierarchical container that encapsulates the complete
stimulus/observation path of the ``aes128`` bench:

    AES128Sequencer --seq_item_export <-> seq_item_port--> AES128Driver
                                                           (drives DUT pins)
    AES128Driver / sequences          ->  DUT pins       -> AES128Monitor
                                                           (samples DUT pins)
    AES128Monitor.analysis_port --connect--> agent.analysis_port (to env)

It combines:

* the **stage-2 stimulus components** (``AES128Driver``, ``AES128Sequencer``)
  produced in the stimulus generation stage, and
* the **stage-3 monitor** (``AES128Monitor``) produced in this stage.

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

# The stage-2 stimulus components live in tb/driver.py / tb/sequencer.py
# (see the uvm_stimulus stage checkpoint).  They are imported defensively so
# this module stays importable even in a workspace where the stimulus stage
# has not been materialized yet; building an ACTIVE agent without them fails
# loudly in build_phase (a passive, monitor-only agent does not need them).
try:
    from tb.driver import AES128Driver
    from tb.sequencer import AES128Sequencer
    _STAGE2_IMPORT_ERROR = None
except ImportError as _err:  # pragma: no cover - depends on workspace state
    AES128Driver = None
    AES128Sequencer = None
    _STAGE2_IMPORT_ERROR = str(_err)

from tb.monitor import AES128Monitor

__all__ = ["AES128Agent"]


class AES128Agent(uvm_agent):
    """Active AES-128 agent: driver + sequencer + monitor, one analysis
    port."""

    def __init__(self, name="aes128_agent", parent=None):
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
        self.monitor = AES128Monitor("monitor", self)
        if self.active():
            if AES128Driver is None or AES128Sequencer is None:
                raise RuntimeError(
                    "AES128Agent: the stage-2 stimulus components "
                    "(tb/driver.py / tb/sequencer.py) are missing: "
                    f"{_STAGE2_IMPORT_ERROR}"
                )
            #: Stimulus path -- present only in active mode.
            self.driver = AES128Driver("driver", self)
            self.sequencer = AES128Sequencer("sequencer", self)
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