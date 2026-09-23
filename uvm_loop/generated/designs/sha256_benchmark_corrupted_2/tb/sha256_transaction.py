"""SHA-256 transaction / sequence_item.

Stage-1 CONTRACT artifact for the cocotb + pyuvm verification environment
(see CONTRACT.md in this directory; it is the authoritative convention
record for every later stage).

``Sha256Transaction`` is a pyuvm ``uvm_sequence_item`` whose fields are
plain Python attributes:

* Driven fields (map 1:1 to DUT input pins, see CONTRACT.md):
  ``start`` (1 bit) and ``block`` (512 bits, big-endian word order).
* Observed fields (populated by the monitor from DUT output pins):
  ``done`` (1 bit) and ``digest`` (256 bits).
* Metadata fields (testbench bookkeeping, NOT DUT pins):
  ``txn_id`` (monotonic in-order id for scoreboard matching / reporting)
  and ``latency_cycles`` (measured start->completion latency, used for the
  fixed-cycle-latency completion checks the corrupted RTL requires).

DUT `block` is packed big-endian: ``block[511:480]`` is the first 32-bit
SHA-256 message word.  A Python ``int`` therefore represents the reference
model's 64-byte big-endian block directly, via ``int.to_bytes(64, "big")``
(the ``block_bytes`` property).

The class deliberately avoids pyuvm field-automation macros: pyuvm 5.0.0
does not ship ``uvm_object_utils`` / ``uvm_field_*`` and the project style
is plain attributes.
"""

from pyuvm import uvm_sequence_item

# Widths of the DUT transaction data paths (authoritative source:
# rtl_info.json + verification plan; reproduced in CONTRACT.md).
START_WIDTH = 1
BLOCK_WIDTH = 512
DONE_WIDTH = 1
DIGEST_WIDTH = 256

BLOCK_BYTES = BLOCK_WIDTH // 8    # 64  -- reference-model block size
DIGEST_BYTES = DIGEST_WIDTH // 8  # 32  -- reference-model digest size


def _mask(value: int, width: int) -> int:
    """Coerce an int into ``width`` unsigned bits (raises on negatives)."""
    value = int(value)
    if value < 0:
        raise ValueError(f"negative value {value} cannot be packed into {width} bits")
    return value & ((1 << width) - 1)


class Sha256Transaction(uvm_sequence_item):
    """One SHA-256 single-block compression transaction."""

    def __init__(
        self,
        name: str = "sha256_transaction",
        start: int = 0,
        block: int = 0,
        done: int = 0,
        digest: int = 0,
        txn_id: int = 0,
        latency_cycles: int = 0,
    ) -> None:
        super().__init__(name)

        # DUT input fields (driven by the stimulus side).
        self.start = _mask(start, START_WIDTH)
        self.block = _mask(block, BLOCK_WIDTH)

        # DUT output fields (observed by the monitor).
        self.done = _mask(done, DONE_WIDTH)
        self.digest = _mask(digest, DIGEST_WIDTH)

        # Testbench-only metadata (not DUT pins).
        self.txn_id = int(txn_id)
        self.latency_cycles = int(latency_cycles)

    # ------------------------------------------------------------------
    # Convenience conversions for the reference model / scoreboard
    # ------------------------------------------------------------------
    @property
    def block_bytes(self) -> bytes:
        """The 512-bit ``block`` as 64 big-endian bytes.

        This is exactly the input format accepted by the golden reference
        model ``sha256_reference_model.block_to_digest(bytes)``.
        """
        return self.block.to_bytes(BLOCK_BYTES, "big")

    @property
    def digest_bytes(self) -> bytes:
        """The 256-bit ``digest`` as 32 big-endian bytes (hashlib format)."""
        return self.digest.to_bytes(DIGEST_BYTES, "big")

    # ------------------------------------------------------------------
    # Reporting (pyuvm uses ``convert2string`` for uvm_info() output)
    # ------------------------------------------------------------------
    def convert2string(self) -> str:
        return (
            f"{self.get_name()}[txn_id={self.txn_id} "
            f"start={self.start} "
            f"block=0x{self.block:0128x} "
            f"done={self.done} "
            f"digest=0x{self.digest:064x} "
            f"latency_cycles={self.latency_cycles}]"
        )

    def __str__(self) -> str:
        return self.convert2string()