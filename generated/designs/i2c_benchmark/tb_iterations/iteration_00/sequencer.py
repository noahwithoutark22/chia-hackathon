"""Stage 2 (stimulus) artifact of the CHIA generator: the pyuvm sequencer.

This module provides ``I2CSequencer``, the pyuvm ``uvm_sequencer`` that
routes ``I2CTransaction`` sequence items from the stimulus sequences to the
``I2CDriver``.  It carries no protocol knowledge -- pyuvm's
``uvm_sequencer`` already implements the request/response machinery
(``seq_item_export``, ``start_item``/``finish_item``, ``get_next_item``)
that the sequences and the driver use; this subclass only fixes the item
type used by the bench and gives a stable place to hang bench-wide
sequencer configuration if later stages need it.

The sequencer is connected to the driver by the agent/env (later stage):

    driver.seq_item_port.connect(sequencer.seq_item_export)
"""

from pyuvm import uvm_sequencer

from tb.transaction import I2CTransaction

__all__ = ["I2CSequencer"]


class I2CSequencer(uvm_sequencer):
    """Sequencer for :class:`~tb.transaction.I2CTransaction` items.

    The base ``uvm_sequencer`` provides:
      * ``start_item(item)`` / ``finish_item(item)``   -- sequence side
      * ``seq_item_export``                            -- driver side
      * queueing / arbitration of concurrently running sequences
    """

    def __init__(self, name="i2c_sequencer", parent=None):
        super().__init__(name, parent)
        # The item type handled by this sequencer (informational; pyuvm
        # does not enforce a type on the queue).
        self.sequence_item_type = I2CTransaction