"""AES-128 sequencer (pyuvm ``uvm_sequencer``).

This is the stimulus-side sequencer component for the ``aes128`` DUT
(``benchmarks/aes128_benchmark_corrupted/aes128.sv``).  It is a plain
``uvm_sequencer`` subclass so the agent/environment/tests can address the
sequencer by a design-specific type name.

The agent stage connects it to the driver with::

    driver.seq_item_port.connect(sequencer.seq_item_export)

Sequences send :class:`Aes128Transaction` items through this sequencer
using ``uvm_sequence.start_item()`` / ``uvm_sequence.finish_item()``
(pyuvm 5.0.0: both are coroutines and must be awaited).

Field and ConfigDB conventions are frozen in CONTRACT.md (keys ``"dut"``,
``"CLK_HALF_PERIOD_NS"``, optional ``"Aes128DutHelper"``); this component
only mediates item traffic and needs no configuration of its own.
"""

from pyuvm import uvm_sequencer


class Aes128Sequencer(uvm_sequencer):
    """Sequencer that arbitrates ``Aes128Transaction`` items to the driver.

    One :class:`Aes128Transaction` is exchanged per AES-128 encryption
    transaction (CONTRACT.md §5).  Item field names and meaning are NOT
    redefined here.
    """

    def __init__(self, name="aes128_sequencer", parent=None):
        super().__init__(name, parent)