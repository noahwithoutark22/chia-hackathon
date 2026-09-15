"""FIFO transaction / sequence_item.

This module defines the single pyuvm sequence item exchanged between the
sequencer/driver on the stimulus side and the monitor/scoreboard on the
analysis side for the ``fifo`` DUT (benchmarks/fifo/fifo.sv).

Field naming and width conventions are frozen in CONTRACT.md.  Do not
rename fields or change their meaning in later stages; later stages
(sequences, driver, monitor, scoreboard) read this class as-is.

Static class attributes:
    DATA_WIDTH:  width of ``din`` / ``dout`` (DUT parameter, default 8).
    DEPTH:       number of entries the FIFO can hold (DUT parameter, default 4).

Per-item fields (plain Python attributes, no ``uvm_object`` ``built()``
machinery required for this design):
    wr_en: 1-bit write request (driven by sequence -> driver -> DUT).
    rd_en: 1-bit read request  (driven by sequence -> driver -> DUT).
    din:   DATA_WIDTH-bit input data (driven by sequence -> driver -> DUT).
    dout:  DATA_WIDTH-bit registered output data (sampled by monitor).
    full:  1-bit combinational full flag  (sampled by monitor).
    empty: 1-bit combinational empty flag (sampled by monitor).
"""

from pyuvm import uvm_sequence_item


class FifoTransaction(uvm_sequence_item):
    """Plain-python transaction for the synchronous FIFO DUT."""

    # DUT structural parameters (mirror defaults from rtl_info.json).
    DATA_WIDTH = 8
    DEPTH = 4

    def __init__(self, name: str = "FifoTransaction"):
        super().__init__(name)
        # Stimulus (input) fields, driven by the driver.
        self.wr_en = 0  # 1 bit
        self.rd_en = 0  # 1 bit
        self.din = 0    # DATA_WIDTH bits
        # Observed (output) fields, sampled by the monitor.
        self.dout = 0   # DATA_WIDTH bits
        self.full = 0   # 1 bit
        self.empty = 0  # 1 bit
        # Bookkeeping, sampled by the monitor after the DUT edge.
        self.dut_cycle = None  # int cycle index at which this item was sampled

    def __str__(self) -> str:
        return (
            f"{self.get_name()}(wr_en={self.wr_en}, rd_en={self.rd_en}, "
            f"din={self.din}, dout={self.dout}, full={self.full}, "
            f"empty={self.empty})"
        )

    def copy(self, other: "FifoTransaction") -> None:
        """Copy ``other``'s attribute values into ``self``."""
        self.wr_en = other.wr_en
        self.rd_en = other.rd_en
        self.din = other.din
        self.dout = other.dout
        self.full = other.full
        self.empty = other.empty
        self.dut_cycle = other.dut_cycle

    def clone(self) -> "FifoTransaction":
        """Return a deep copy of this transaction."""
        c = FifoTransaction()
        c.copy(self)
        return c