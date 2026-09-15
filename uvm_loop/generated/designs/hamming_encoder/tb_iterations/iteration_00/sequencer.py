"""hamming_encoder pyuvm sequencer (stage 2: STIMULUS).

``HammingSequencer`` is the pyuvm ``uvm_sequencer`` that routes
:class:`~tb.transaction.HammingTransaction` items produced by the stimulus
sequences to :class:`~tb.driver.HammingDriver`.  It carries no protocol
knowledge: pyuvm's ``uvm_sequencer`` already implements the standard
request/response machinery (``seq_item_export``,
``start_item``/``finish_item``, ``get_next_item``/``item_done``); this
subclass only fixes the item type used by the bench and provides a stable
home for bench-wide sequencer configuration if later stages need it.

Connection (made by the agent / environment, a later stage)::

    driver.seq_item_port.connect(sequencer.seq_item_export)
"""

from pyuvm import uvm_sequencer

from tb.transaction import HammingTransaction

__all__ = ["HammingSequencer"]


class HammingSequencer(uvm_sequencer):
    """Sequencer for :class:`~tb.transaction.HammingTransaction` items.

    The base ``uvm_sequencer`` provides:

      * ``start_item(item)`` / ``finish_item(item)`` -- sequence side,
      * ``seq_item_export``                            -- driver side,
      * arbitration of concurrently running sequences.

    ``sequence_item_type`` is informational: pyuvm does not enforce an item
    type on the queue, but stamping it documents (and lets later stages
    introspect) which item class this sequencer carries.
    """

    def __init__(self, name="hamming_sequencer", parent=None):
        super().__init__(name, parent)
        self.sequence_item_type = HammingTransaction