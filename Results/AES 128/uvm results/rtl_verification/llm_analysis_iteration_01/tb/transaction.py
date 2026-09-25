"""AES-128 transaction / sequence_item.

This module defines the single pyuvm sequence item exchanged between the
sequencer/driver on the stimulus side and the monitor/scoreboard on the
analysis side for the ``aes128`` DUT
(``benchmarks/aes128_benchmark_corrupted/aes128.sv``).

Field naming and width conventions are frozen in CONTRACT.md.  Do not
rename fields or change their meaning in later stages; later stages
(sequences, driver, monitor, scoreboard, environment, tests) read this
class as-is.  The DUT has NO module parameters (the ``SBOX``/``RCON``
tables in rtl_info.json are internal ``localparam`` arrays, not
configurable parameters), so all widths below are literal constants.

Per-item fields (plain Python attributes, int values; no ``uvm_object``
field macros required):

    start:      1-bit transaction start strobe
                (driven by sequence -> driver -> DUT).
    key:        128-bit AES-128 encryption key; most-significant byte is
                AES state byte 0 (driven by sequence -> driver -> DUT).
    plaintext:  128-bit plaintext block; most-significant byte is AES
                state byte 0 (driven by sequence -> driver -> DUT).
    done:       1-bit completion pulse, high for exactly one cycle when
                ``ciphertext`` is valid (sampled by monitor).
    ciphertext: 128-bit ciphertext output, valid to sample while
                ``done`` is high (sampled by monitor).
    txn_id:     int bookkeeping id, monotonically increasing, assigned by
                the driver when a transaction is accepted at ``start``.
    dut_cycle:  int or None bookkeeping field; 0-based rising-edge index
                at which the monitor sampled this item.

Clock (``clk``) and reset (``rst_n``) are structural signals and are NOT
transaction fields (CONTRACT.md §5).
"""

from pyuvm import uvm_sequence_item


class Aes128Transaction(uvm_sequence_item):
    """Plain-python transaction for the ``aes128`` single-block encryptor."""

    # DUT constant widths (from rtl_info.json / CONTRACT.md §2).
    KEY_WIDTH = 128
    PLAINTEXT_WIDTH = 128
    CIPHERTEXT_WIDTH = 128

    def __init__(self, name: str = "Aes128Transaction"):
        super().__init__(name)
        # Stimulus (input) fields, driven by the driver.
        self.start = 0       # 1 bit
        self.key = 0         # KEY_WIDTH bits
        self.plaintext = 0   # PLAINTEXT_WIDTH bits
        # Observed (output) fields, sampled by the monitor.
        self.done = 0        # 1 bit
        self.ciphertext = 0  # CIPHERTEXT_WIDTH bits
        # Bookkeeping (fill as described in CONTRACT.md §5).
        self.txn_id = 0          # int transaction identifier
        self.dut_cycle = None    # int | None: sampled edge index

    def __str__(self) -> str:
        return (
            f"{self.get_name()}(txn_id={self.txn_id}, start={self.start}, "
            f"key=0x{self.key:032x}, plaintext=0x{self.plaintext:032x}, "
            f"done={self.done}, ciphertext=0x{self.ciphertext:032x}, "
            f"dut_cycle={self.dut_cycle})"
        )

    def copy(self, other: "Aes128Transaction") -> None:
        """Copy ``other``'s attribute values into ``self``."""
        self.start = other.start
        self.key = other.key
        self.plaintext = other.plaintext
        self.done = other.done
        self.ciphertext = other.ciphertext
        self.txn_id = other.txn_id
        self.dut_cycle = other.dut_cycle

    def clone(self) -> "Aes128Transaction":
        """Return a deep copy of this transaction."""
        c = Aes128Transaction()
        c.copy(self)
        return c