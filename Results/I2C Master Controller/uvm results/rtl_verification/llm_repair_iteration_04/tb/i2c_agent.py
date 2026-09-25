"""i2c_master UVM agent for the cocotb + pyuvm bench (observation stage).

Stage-3 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory; it is the authoritative convention record).

``I2CAgent`` is a pyuvm ``uvm_agent`` that encapsulates the stimulus stage's
driver + sequencer (CONTRACT.md §13) and this stage's monitor:

* build_phase: honors the standard active/passive switch (base
  ``uvm_agent.build_phase`` reads the ConfigDB ``"is_active"`` key and
  defaults to ``UVM_ACTIVE``).  In an active agent it builds the
  ``I2CSequencer`` and ``I2CDriver``; the ``I2CMonitor`` is always built
  (passive agents still observe).
* connect_phase: connects ``driver.seq_item_port`` to
  ``sequencer.seq_item_export`` (the standard pull connection) and sets the
  documented convenience copy ``I2CSequencer.driver`` (CONTRACT.md §13.1).

The ConfigDB key ``"i2c_driver"`` (``KEY_I2C_DRIVER``) is deliberately NOT
set here: CONTRACT.md §13.1 records that the env/test stage sets it exactly
once in ``build_phase``.  This agent only holds the live references
(``self.driver`` / ``self.sequencer``) for the env to store and for
``connect_phase`` wiring.

Consumers connect directly to the monitor's analysis ports
(``agent.monitor.ap`` / ``agent.monitor.hung_ap`` / ``agent.monitor.reset_ap``);
no agent-level forwarding ports are created (they would only duplicate the
monitor's ports without adding semantics).

Cocotb 2.1.0 public-API notes: this module imports no cocotb symbols; it
only uses public pyuvm classes (``uvm_agent``, ``uvm_active_passive_enum``,
``ConfigDB``) and the shared ConfigDB keys defined in CONTRACT.md §6.
"""

from pyuvm import ConfigDB, uvm_active_passive_enum, uvm_agent

from i2c_driver import I2CDriver
from i2c_monitor import I2CMonitor
from i2c_pins import I2CPins, KEY_DUT, KEY_DUT_PINS
from i2c_sequencer import I2CSequencer


class I2CAgent(uvm_agent):
    """Encapsulates the i2c_master driver/sequencer (stimulus) and monitor
    (observation).  ``is_active`` follows the standard UVM contract: an
    active agent contains driver + sequencer + monitor; a passive agent
    contains only the monitor."""

    def build_phase(self):
        # Base uvm_agent.build_phase() sets self.is_active from the
        # ConfigDB "is_active" key (UVM_ACTIVE default) -- see §13.1 / the
        # pyuvm reference implementation.
        super().build_phase()
        self.dut = ConfigDB().get(None, "", KEY_DUT)
        self.pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        if not isinstance(self.pins, I2CPins):
            self.logger.warning(
                f"ConfigDB['{KEY_DUT_PINS}'] is not an I2CPins: {self.pins!r}"
            )

        self.sequencer = None
        self.driver = None
        if self.active():
            self.sequencer = I2CSequencer("sequencer", self)
            self.driver = I2CDriver("driver", self)
        # The monitor observes in both active and passive configurations.
        self.monitor = I2CMonitor("monitor", self)
        self.logger.info(
            f"I2CAgent built: is_active={self.is_active} "
            f"({uvm_active_passive_enum.UVM_ACTIVE!s}); "
            f"driver={self.driver is not None}, "
            f"sequencer={self.sequencer is not None}, monitor={True}"
        )

    def connect_phase(self):
        super().connect_phase()
        if self.active():
            # Standard pull-mode item connection (CONTRACT.md §2).
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
            # Documented convenience copy for flow sequences (CONTRACT.md
            # §13.1); the ConfigDB "i2c_driver" key remains authoritative
            # and is set by the env/test stage.
            self.sequencer.driver = self.driver
            self.logger.info(
                "I2CAgent connected item path "
                "driver.seq_item_port -> sequencer.seq_item_export"
            )