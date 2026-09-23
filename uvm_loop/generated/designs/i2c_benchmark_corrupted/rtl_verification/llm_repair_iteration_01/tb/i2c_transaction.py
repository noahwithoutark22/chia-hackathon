"""i2c_master transaction / sequence_item for the cocotb + pyuvm bench.

Stage-1 CONTRACT artifact for the CHIA cocotb+pyuvm environment generator
(see CONTRACT.md in this directory; it is the authoritative convention
record for every later stage).

``I2CTransaction`` is a pyuvm ``uvm_sequence_item`` whose fields are plain
Python attributes (pyuvm 5.0.0 has no ``uvm_object_utils`` /
field-automation macros):

* Stimulus fields (map 1:1 to DUT input ports other than ``clk``/``rst_n``,
  see CONTRACT.md): ``start`` (1 bit), ``slave_addr`` (7 bits), ``rw``
  (1 bit), ``tx_data`` (8 bits), ``sda_in`` (1 bit), ``scl_in`` (1 bit).
* Slave-response intent fields (NOT DUT pins): ``slave_ack`` (1 bit) and
  ``read_data`` (8 bits).  These describe how the testbench models the I2C
  slave on the shared bus: the driver derives the per-cycle ``sda_in``
  waveform from them (ACK/NACK level at ACK sample points and, for a read
  transaction, the data byte driven MSB-first during the read-data phase).
* Observed fields (populated by the monitor from DUT output pins):
  ``rx_data`` (8 bits), ``done`` (1), ``busy`` (1), ``ack_error`` (1),
  ``sda_out`` (1), ``sda_oe`` (1), ``scl_out`` (1), ``scl_oe`` (1).
* Metadata fields (testbench bookkeeping, NOT DUT pins): ``txn_id``
  (monotonic in-order id for scoreboard matching / error reporting) and
  ``latency_cycles`` (measured start->completion cycle count).

``clk`` and ``rst_n`` are structural signals and never appear as
transaction fields (UVM rules).

Public Cocotb 2.1.0 note: this module imports no cocotb symbols.  It only
depends on pyuvm's ``uvm_sequence_item``, so it stays importable in any
plain-Python context (simulation, unit checks, AST consistency checks).
"""

import random

from pyuvm import uvm_sequence_item

# ---------------------------------------------------------------------------
# Widths (bits), authoritative source: rtl_info.json + verification plan,
# reproduced in CONTRACT.md.  Ports are declared:
#   slave_addr -> input [6:0] (7 bits)
#   tx_data    -> input [7:0] (8 bits)
#   rx_data    -> output [7:0] (8 bits)
# all other data ports are 1 bit.
# ---------------------------------------------------------------------------
START_WIDTH = 1
SLAVE_ADDR_WIDTH = 7
RW_WIDTH = 1
TX_DATA_WIDTH = 8
SDA_IN_WIDTH = 1
SCL_IN_WIDTH = 1
RX_DATA_WIDTH = 8
DONE_WIDTH = 1
BUSY_WIDTH = 1
ACK_ERROR_WIDTH = 1
SDA_OUT_WIDTH = 1
SDA_OE_WIDTH = 1
SCL_OUT_WIDTH = 1
SCL_OE_WIDTH = 1

SLAVE_ADDR_MAX = (1 << SLAVE_ADDR_WIDTH) - 1   # 0x7F
TX_DATA_MAX = (1 << TX_DATA_WIDTH) - 1         # 0xFF
RX_DATA_MAX = (1 << RX_DATA_WIDTH) - 1         # 0xFF


def _mask(value: int, width: int) -> int:
    """Coerce an int into ``width`` unsigned bits (raises on negatives)."""
    value = int(value)
    if value < 0:
        raise ValueError(f"negative value {value} cannot be packed into {width} bits")
    return value & ((1 << width) - 1)


class I2CTransaction(uvm_sequence_item):
    """One single-byte I2C master transaction, plus observed outputs.

    Stimulus attributes (driven by the driver; each maps 1:1 to a DUT
    input port)::

        start       int, 1 bit   transaction request; sampled only while idle
        slave_addr  int, 7 bits  I2C slave address (0x00..0x7F)
        rw          int, 1 bit   0 = write, 1 = read
        tx_data     int, 8 bits  data byte for a write transaction
        sda_in      int, 1 bit   default SDA level the TB presents on sda_in
                                 (1 = released/high = NACK; 0 = low = ACK);
                                 the driver derives the per-cycle waveform
                                 from ``slave_ack`` and ``read_data``
        scl_in      int, 1 bit   SCL level held on scl_in (default 1; the
                                 corrupted RTL never samples this pin)

    Slave-response intent attributes (NOT DUT pins; the driver maps them
    into the ``sda_in`` waveform the TB drives)::

        slave_ack   int, 1 bit   1 = slave drives ACK (sda_in low at ACK
                                 sample points), 0 = slave NACKs (high)
        read_data   int, 8 bits  byte the slave drives MSB-first during a
                                 read transaction's data phase (ignored for
                                 writes; 0 by default)

    Observed-output attributes (filled by the monitor at the completion
    point, see CONTRACT.md)::

        rx_data     int, 8 bits  received byte of a read transaction
        done        int, 1 bit   done value (1 only at a completion pulse
                                 on a correct RTL; the corrupted RTL drives
                                 it permanently high -- see CONTRACT.md)
        busy        int, 1 bit   busy value sampled at completion
        ack_error   int, 1 bit   ack_error value sampled at completion
        sda_out     int, 1 bit   open-drain SDA data value
        sda_oe      int, 1 bit   SDA drive-enable (1 = drive, 0 = release)
        scl_out     int, 1 bit   open-drain SCL data value
        scl_oe      int, 1 bit   SCL drive-enable

    Metadata attributes (NOT DUT pins)::

        txn_id          int  monotonic id (scoreboard match/reporting)
        latency_cycles  int  measured start-acceptance -> completion cycles
    """

    def __init__(
        self,
        name: str = "i2c_transaction",
        start: int = 1,
        slave_addr: int = 0x50,
        rw: int = 0,
        tx_data: int = 0,
        sda_in: int = 1,
        scl_in: int = 1,
        slave_ack: int = 1,
        read_data: int = 0,
        rx_data: int = 0,
        done: int = 0,
        busy: int = 0,
        ack_error: int = 0,
        sda_out: int = 0,
        sda_oe: int = 0,
        scl_out: int = 0,
        scl_oe: int = 0,
        txn_id: int = 0,
        latency_cycles: int = 0,
    ) -> None:
        super().__init__(name)

        # --- stimulus fields (DUT input pins) --------------------------
        self.start = _mask(start, START_WIDTH)
        self.slave_addr = _mask(slave_addr, SLAVE_ADDR_WIDTH)
        self.rw = _mask(rw, RW_WIDTH)
        self.tx_data = _mask(tx_data, TX_DATA_WIDTH)
        self.sda_in = _mask(sda_in, SDA_IN_WIDTH)
        self.scl_in = _mask(scl_in, SCL_IN_WIDTH)

        # --- slave-response intent (NOT DUT pins) ----------------------
        self.slave_ack = _mask(slave_ack, 1)
        self.read_data = _mask(read_data, RX_DATA_WIDTH)

        # --- observed-output fields (DUT output pins) ------------------
        self.rx_data = _mask(rx_data, RX_DATA_WIDTH)
        self.done = _mask(done, DONE_WIDTH)
        self.busy = _mask(busy, BUSY_WIDTH)
        self.ack_error = _mask(ack_error, ACK_ERROR_WIDTH)
        self.sda_out = _mask(sda_out, SDA_OUT_WIDTH)
        self.sda_oe = _mask(sda_oe, SDA_OE_WIDTH)
        self.scl_out = _mask(scl_out, SCL_OUT_WIDTH)
        self.scl_oe = _mask(scl_oe, SCL_OE_WIDTH)

        # --- testbench-only metadata (NOT DUT pins) --------------------
        self.txn_id = int(txn_id)
        self.latency_cycles = int(latency_cycles)

    # ------------------------------------------------------------------
    # Derived protocol properties (reference-model compatible)
    # ------------------------------------------------------------------
    @property
    def address_byte(self) -> int:
        """The 8-bit I2C address byte: ``(slave_addr << 1) | rw``.

        Identical to the reference model's ``make_address_byte()``.
        """
        return (self.slave_addr << 1) | self.rw

    @property
    def is_read(self) -> bool:
        """True when this item represents a read transaction (rw == 1)."""
        return bool(self.rw)

    # ------------------------------------------------------------------
    # Constrained randomization (for the plan's randomized strategy)
    # ------------------------------------------------------------------
    def randomize(self, **constraints) -> bool:
        """Constrained-randomize the stimulus + slave-response fields.

        Ranges follow the verification plan's ``randomized_testing_strategy``
        constraints:

        - ``slave_addr``: uniform 0x00..0x7F (7 bit)
        - ``rw``: uniform 0/1
        - ``tx_data``: uniform 0x00..0xFF (only meaningful when rw == 0)
        - ``read_data``: uniform 0x00..0xFF (only meaningful when rw == 1)
        - ``slave_ack``: uniform 0/1
        - ``start``: always 1 (the item always represents a request offered
          while idle)
        - ``sda_in``/``scl_in``: 1 (released bus default)

        Any keyword ``constraints`` override fields after generation, e.g.
        ``item.randomize(rw=1, slave_addr=0x50)``.  Unknown field names
        raise AttributeError so typos fail loudly.
        """
        self.slave_addr = random.randrange(0, 0x80)      # 0x00..0x7F
        self.rw = random.randrange(0, 2)
        self.tx_data = random.randrange(0, 0x100)        # 0x00..0xFF
        self.slave_ack = random.randrange(0, 2)
        self.read_data = random.randrange(0, 0x100)      # 0x00..0xFF
        self.start = 1
        self.sda_in = 1
        self.scl_in = 1

        for field_name, value in constraints.items():
            if not hasattr(self, field_name):
                raise AttributeError(
                    f"I2CTransaction.randomize() constraint '{field_name}' "
                    f"is not a field of I2CTransaction"
                )
            setattr(self, field_name, value)

        return True

    # ------------------------------------------------------------------
    # Width validation (mirrors the reference model's ValueError checks)
    # ------------------------------------------------------------------
    def check_inputs_valid(self) -> bool:
        """Raise ValueError if any stimulus field exceeds its port width.

        Mirrors the width validation performed by the Python reference
        model (``i2c_reference_model.py``).
        """
        for name, value, width in (
            ("start", self.start, START_WIDTH),
            ("rw", self.rw, RW_WIDTH),
            ("sda_in", self.sda_in, SDA_IN_WIDTH),
            ("scl_in", self.scl_in, SCL_IN_WIDTH),
            ("slave_ack", self.slave_ack, 1),
        ):
            if value not in (0, 1):
                raise ValueError(f"{name} must be {width} bit, got {value}")
        if not 0 <= self.slave_addr <= SLAVE_ADDR_MAX:
            raise ValueError(
                f"slave_addr must be {SLAVE_ADDR_WIDTH} bits (0x00..0x7F), "
                f"got {self.slave_addr}"
            )
        if not 0 <= self.tx_data <= TX_DATA_MAX:
            raise ValueError(
                f"tx_data must be {TX_DATA_WIDTH} bits (0x00..0xFF), "
                f"got {self.tx_data}"
            )
        if not 0 <= self.read_data <= RX_DATA_MAX:
            raise ValueError(
                f"read_data must be {RX_DATA_WIDTH} bits (0x00..0xFF), "
                f"got {self.read_data}"
            )
        return True

    # ------------------------------------------------------------------
    # Reporting (pyuvm uses ``convert2string`` for uvm_info() output)
    # ------------------------------------------------------------------
    def convert2string(self) -> str:
        return (
            f"{self.get_name()}[txn_id={self.txn_id} "
            f"start={self.start} "
            f"addr=0x{self.slave_addr:02x} rw={self.rw} "
            f"tx_data=0x{self.tx_data:02x} "
            f"sda_in={self.sda_in} scl_in={self.scl_in} "
            f"slave_ack={self.slave_ack} read_data=0x{self.read_data:02x} "
            f"rx_data=0x{self.rx_data:02x} done={self.done} "
            f"busy={self.busy} ack_error={self.ack_error} "
            f"sda_out={self.sda_out} sda_oe={self.sda_oe} "
            f"scl_out={self.scl_out} scl_oe={self.scl_oe} "
            f"latency_cycles={self.latency_cycles}]"
        )

    def __str__(self) -> str:
        return self.convert2string()