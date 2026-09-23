"""i2c_master UVM sequencer (stimulus stage).

Stage-2 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory).

``I2CSequencer`` is the pyuvm ``uvm_sequencer`` instance the driver's
``seq_item_port`` connects to (CONTRACT.md §6/§2).  It arbitrates plain
``I2CTransaction`` items from item-based sequences (corner cases,
single-transaction stimuli) to the driver's ``run_phase``.

In addition to the standard item flow, the stimulus stage uses a *virtual /
orchestrated* sequence style (CONTRACT.md §13): timed directed scenarios
(TC-01..TC-13), timed corner cases and the randomized strategy call the
driver's public async task methods directly.  Those sequences obtain the
driver through the ConfigDB key ``"i2c_driver"`` (``KEY_I2C_DRIVER`` in
``i2c_driver.py``), set once by the env/test stage in ``build_phase``.  As a
convenience the env also stores the same reference here as
``I2CSequencer.driver`` (CONNECTED in ``connect_phase``); either access path
is valid.

Cocotb 2.1.0 public-API notes: this module touches no cocotb symbols; it
only uses public pyuvm classes and the shared ConfigDB keys defined in
CONTRACT.md §6.
"""

from pyuvm import ConfigDB, uvm_sequencer

from i2c_pins import KEY_DUT, KEY_DUT_PINS
from i2c_transaction import I2CTransaction  # noqa: F401  (documents the item type)


class I2CSequencer(uvm_sequencer):
    """Sequencer for :class:`I2CTransaction` items plus flow-sequence glue.

    ``seq_item_export`` (inherited) connects to the driver's
    ``seq_item_port`` in the agent's ``connect_phase``.  ``driver`` is the
    same ``I2CDriver`` instance the ConfigDB key ``"i2c_driver"`` holds; it
    is set by the env in ``connect_phase`` and is what virtual/flow
    sequences may use as an alternative to ConfigDB.
    """

    def build_phase(self):
        super().build_phase()
        self.dut = ConfigDB().get(None, "", KEY_DUT)
        self.pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        # Set by the env in connect_phase (see CONTRACT.md §13).
        self.driver = None

    def connect_phase(self):
        super().connect_phase()
        if self.driver is not None:
            self.logger.info(
                f"I2CSequencer 'driver' reference attached: {self.driver.get_name()}"
            )