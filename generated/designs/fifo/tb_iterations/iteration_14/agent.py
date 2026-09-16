"""FIFO agent (pyuvm ``uvm_agent``).

This component encapsulates the *stimulus* and *observation* sides of the
FIFO testbench for reuse by the environment stage:

    * an active agent owns the ``FifoSequencer`` (stimulus stage,
      ``tb/sequences.py``), the ``FifoDriver`` (stimulus stage,
      ``tb/driver.py``) and the ``FifoMonitor`` (this stage,
      ``tb/monitor.py``), and wires
      ``driver.seq_item_port.connect(sequencer.seq_item_export)``;
    * a passive agent owns only the ``FifoMonitor`` (pure observation).

``is_active`` defaults to ``UVM_ACTIVE`` (pyuvm ``uvm_agent``
``build_phase`` behavior); it can be overridden through the pyuvm ConfigDB
key ``is_active`` for the agent's instance path, which the environment/tests
may choose to do.  No DUT pin is driven or sampled here directly: the agent
only *contains* and *connects* the subcomponents, exactly as the UVM agent
role prescribes.

Analysis output: in ``connect_phase`` the agent passes the monitor's
analysis port upward as ``FifoAgent.ap`` (same object as
``FifoAgent.monitor.ap``), so scoreboards can connect against either
handle.  This matches the pyuvm TLM convention where a ``uvm_analysis_port``
``write()`` broadcasts to every connected subscriber.
"""

from pyuvm import uvm_active_passive_enum, uvm_agent

from driver import FifoDriver
from monitor import FifoMonitor
from sequences import FifoSequencer


class FifoAgent(uvm_agent):
    """Active/passive agent wrapping sequencer + driver + monitor."""

    def __init__(self, name="fifo_agent", parent=None):
        super().__init__(name, parent)
        self.sequencer = None
        self.driver = None
        self.monitor = None
        self.ap = None  # pass-through of the monitor analysis port

    def build_phase(self):
        """Create the monitor (always) and, when active, the sequencer and
        driver.  Creating each subcomponent with ``self`` as parent registers
        it in the UVM hierarchy (pyuvm ``uvm_component``)."""
        super().build_phase()
        self.monitor = FifoMonitor("fifo_monitor", self)
        if self.get_is_active() == uvm_active_passive_enum.UVM_ACTIVE:
            self.sequencer = FifoSequencer("fifo_sequencer", self)
            self.driver = FifoDriver("fifo_driver", self)
            self.logger.debug(
                "%s: active agent (driver + sequencer + monitor)",
                self.get_full_name(),
            )
        else:
            self.logger.debug(
                "%s: passive agent (monitor only)", self.get_full_name()
            )

    def connect_phase(self):
        """Connect driver <-> sequencer (active only) and expose the
        monitor's analysis port at the agent boundary."""
        super().connect_phase()
        # The monitor's build_phase has already run (top-down build), so its
        # analysis port exists here (bottom-up connect).
        self.ap = self.monitor.ap
        if self.get_is_active() == uvm_active_passive_enum.UVM_ACTIVE:
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
            self.logger.debug(
                "%s: driver.seq_item_port -> sequencer.seq_item_export",
                self.get_full_name(),
            )