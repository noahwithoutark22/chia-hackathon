"""AES-128 UVM sequencer (stage 6 integration; closes the stage-2 sequencer gap).

The :class:`AES128Sequencer` is the passive hub between the stimulus
:class:`tb.sequences` and the active :class:`tb.driver.AES128Driver`.  It
runs no ``run_phase`` of its own: it simply mediates
``start_item()/finish_item()`` calls from sequences with
``get_next_item()/item_done()`` calls from the driver (pyuvm
``uvm_sequencer`` semantics, IEEE 1800.2 section 16).

The sequencer declares :attr:`AES128Sequencer.sequence_item_type` so that
:class:`tb.sequences.AESScenarioBase` can be statically checked against the
agreed transaction class (``CONTRACT.md`` section 6).
"""

from pyuvm import uvm_sequencer

from tb.transaction import AES128Transaction

__all__ = ["AES128Sequencer"]


class AES128Sequencer(uvm_sequencer):
    """Sequencer for :class:`tb.transaction.AES128Transaction` items."""

    def __init__(self, name="aes128_sequencer", parent=None):
        super().__init__(name, parent)
        #: Item type this sequencer exchanges (check-time contract).
        self.sequence_item_type = AES128Transaction