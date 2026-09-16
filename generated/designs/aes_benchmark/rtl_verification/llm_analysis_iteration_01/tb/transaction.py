"""AES-128 transaction / sequence_item for pyuvm.

This module defines the single transaction class used by every
cocotb+pyuvm component (driver, monitor, scoreboard, sequences, etc.).

Convention
----------
- All fields are plain Python ``int`` attributes.
- Input fields  -> driven by the driver, represent DUT input ports
  (excluding clock / reset, which are structural).
- Output fields -> sampled from the DUT by the monitor.
"""

from pyuvm import uvm_sequence_item


class AES128Transaction(uvm_sequence_item):
    """Sequence-item carrying one AES-128 encryption transaction.

    Input fields  (driven by driver -> DUT inputs):
        start   : 1-bit  - pulse to launch encryption (accepted only while idle)
        key     : 128-bit AES key
        plaintext : 128-bit plaintext block

    Output fields (sampled from DUT outputs):
        ciphertext : 128-bit encrypted result (valid when done pulses)
        busy       : 1-bit, high while encryption is active
        done       : 1-bit, one-clock completion pulse
    """

    def __init__(self, name="AES128Transaction"):
        super().__init__(name)

        # ── Input fields (driver drives these onto the DUT) ──────────
        self.start: int = 0          # 1-bit
        self.key: int = 0            # 128-bit
        self.plaintext: int = 0      # 128-bit

        # ── Output fields (monitor samples these from the DUT) ───────
        self.ciphertext: int = 0     # 128-bit
        self.busy: int = 0           # 1-bit
        self.done: int = 0           # 1-bit

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def set_inputs(self, start: int, key: int, plaintext: int) -> None:
        """Populate all input fields at once."""
        self.start = start
        self.key = key
        self.plaintext = plaintext

    def set_outputs(self, ciphertext: int, busy: int, done: int) -> None:
        """Populate all output fields at once."""
        self.ciphertext = ciphertext
        self.busy = busy
        self.done = done

    def __eq__(self, other):
        if not isinstance(other, AES128Transaction):
            return NotImplemented
        return (
            self.start == other.start
            and self.key == other.key
            and self.plaintext == other.plaintext
            and self.ciphertext == other.ciphertext
            and self.busy == other.busy
            and self.done == other.done
        )

    def __repr__(self):
        return (
            f"AES128Transaction("
            f"start=0x{self.start:x}, "
            f"key=0x{self.key:032x}, "
            f"plaintext=0x{self.plaintext:032x}, "
            f"ciphertext=0x{self.ciphertext:032x}, "
            f"busy={self.busy}, "
            f"done={self.done})"
        )

    def convert2string(self):
        return repr(self)
