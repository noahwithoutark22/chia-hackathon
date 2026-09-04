"""PyUVM agent for the parameterized adder DUT.

The agent encapsulates the three stimulus/observation components:
  - ``AdderSequencer`` — arbitrates sequences producing items
  - ``AdderDriver``   — drives ``a``/``b``/``cin`` onto the DUT pins
  - ``AdderMonitor``  — passively samples DUT outputs and publishes
    observed transactions on its analysis port

The driver's ``seq_item_port`` is connected to the sequencer's
``seq_item_export`` (per CONTRACT.md Section 9.1), forming the classic
UVM stimulus pipeline.

The agent also exposes ``self.ap`` (a direct reference to the monitor's
analysis port) so a later-stage environment / scoreboard can connect it
straight to a ``uvm_tlm_analysis_fifo`` without reaching inside the
monitor.

Active vs passive (CONTRACT.md / pyuvm ``uvm_agent`` conventions):
  - **Active** (default): builds sequencer + driver + monitor and
    connects the stimulus path.  Used on interfaces that the testbench
    drives.
  - **Passive**: builds only the monitor, observing without driving.
    Useful for a second observation point.
A later stage may set ``ConfigDB`` key ``"is_active"`` under the agent's
hierarchy to select the mode; the value must be a
``uvm_active_passive_enum`` (``UVM_ACTIVE`` / ``UVM_PASSIVE``).
"""

from __future__ import annotations

from pyuvm import uvm_agent, uvm_active_passive_enum

from adder_sequencer import AdderSequencer
from adder_driver import AdderDriver
from adder_monitor import AdderMonitor


class AdderAgent(uvm_agent):
    """Agent encapsulating sequencer / driver / monitor for the adder.

    Parameters
    ----------
    name : str
        Instance name (default ``"adder_agent"``).
    parent : uvm_component
        Parent component, normally the environment.
    """

    def __init__(self, name="adder_agent", parent=None):
        super().__init__(name, parent)
        self.sequencer: AdderSequencer | None = None
        self.driver: AdderDriver | None = None
        self.monitor: AdderMonitor | None = None
        # Alias for the monitor's analysis port (scoreboard hook).
        self.ap: object | None = None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Construct the sequencer, driver and/or monitor subcomponents."""
        super().build_phase()

        # The monitor is always present: it passively samples the DUT.
        self.monitor = AdderMonitor("adder_monitor", self)
        self.ap = self.monitor.ap

        if self.active():
            # Active agent: also build the stimulus path.
            self.sequencer = AdderSequencer("adder_sequencer", self)
            self.driver = AdderDriver("adder_driver", self)
        else:
            self.logger.info(
                "AdderAgent %s is passive: sequencer/driver not built.",
                self.get_full_name(),
            )

    def connect_phase(self):
        """Connect driver sequencer-port to the sequencer export."""
        super().connect_phase()
        if self.active():
            # Exactly the connection prescribed by CONTRACT.md Section 9.
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
            self.logger.info(
                "Connected driver.seq_item_port -> "
                "sequencer.seq_item_export in %s",
                self.get_full_name(),
            )
