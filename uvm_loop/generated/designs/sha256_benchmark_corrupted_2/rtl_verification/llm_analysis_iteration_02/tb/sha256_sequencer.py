"""SHA-256 UVM sequencer (stage-2 STIMULUS artifact).

Thin ``uvm_sequencer`` subclass for the cocotb + pyuvm verification
environment described by CONTRACT.md.  It arbitrates ``Sha256Transaction``
items between the stimulus sequences (``sha256_sequences.py``) and the
pin driver (``sha256_driver.py``).

The sequencer intentionally carries no extra logic: pyuvm's ``uvm_sequencer``
provides the standard ``seq_q`` + ``seq_item_export`` plumbing that the
sequence ``start_item``/``finish_item`` and the driver
``seq_item_port.get_next_item``/``item_done`` handshake relies on.  The
agent (later stage) connects ``sequencer.seq_item_export`` to
``driver.seq_item_port`` in its connect phase.

No SystemVerilog anywhere: this is a pure pyuvm (5.0.0) Python component.
"""

from pyuvm import uvm_sequencer


class Sha256Sequencer(uvm_sequencer):
    """Sequencer that transports ``Sha256Transaction`` items.

    There is deliberately no custom ``build_phase``/``run_phase``: pyuvm's
    default ``run_phase`` pops items from ``seq_q`` and forwards them to
    ``seq_item_export`` (consumed by the driver's ``seq_item_port``).
    ``ConfigDB`` keys ``"dut"`` / ``"sha256_pins"`` are not needed here --
    they are consumed by the driver, monitor, scoreboard, etc.
    """

    def __init__(self, name: str = "sha256_sequencer", parent=None) -> None:
        super().__init__(name, parent)