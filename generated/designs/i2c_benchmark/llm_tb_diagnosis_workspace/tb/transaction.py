"""i2c_master transaction / sequence_item for the cocotb + pyuvm bench.

Stage 1 (contract) artifact of the CHIA environment generator.

Defines the single pyuvm ``uvm_sequence_item`` type shared by every
component of the generated testbench.  Field names, widths, and meaning
are authoritative for later stages and are recorded in CONTRACT.md; the
DUT port list is taken verbatim from ``generated/designs/i2c_benchmark/
rtl/rtl_info.json`` and ``benchmarks/i2c_benchmark/i2c_master.sv``.

No clock / reset fields live in the transaction: ``clk`` and ``rst_n``
are structural signals (see UVM rules).
"""

import random

from pyuvm import uvm_sequence_item


# ---------------------------------------------------------------------------
# Widths (bits), straight from the RTL port declarations:
#   slave_addr -> input [6:0]  (7 bits)
#   reg_addr   -> input [7:0]  (8 bits)
#   write_data -> input [7:0]  (8 bits)
#   read_data  -> output [7:0] (8 bits)
# ---------------------------------------------------------------------------
RW_WIDTH = 1
SLAVE_ADDR_WIDTH = 7
REG_ADDR_WIDTH = 8
DATA_WIDTH = 8

# The only I2C slave supported by this benchmark (spec, reference model,
# and RTL agree): 7-bit address 0x50.
SUPPORTED_SLAVE_ADDR = 0x50


class I2CTransaction(uvm_sequence_item):
    """One register-oriented I2C transaction, plus its observed outputs.

    Stimulus attributes (each maps 1:1 to a DUT input port; ``start`` is
    driven high for the single cycle in which the transaction is offered
    while the DUT is idle)::

        start       int, 1 bit   transaction request pulse
        rw          int, 1 bit   0 = write, 1 = read
        slave_addr  int, 7 bits  I2C slave address (supported: 0x50)
        reg_addr    int, 8 bits  register / memory byte address
        write_data  int, 8 bits  data byte for a write transaction

    Output attributes (filled in by the monitor when the DUT issues its
    single-cycle ``done`` pulse, per spec section 8)::

        read_data   int, 8 bits  data returned by a read transaction
        busy        int, 1 bit   busy value sampled at the done pulse
        done        int, 1 bit   1 when a completion pulse was observed
        ack_error   int, 1 bit   1 when the slave address is unsupported
    """

    def __init__(self, name="i2c_transaction"):
        super().__init__(name)

        # --- stimulus fields -------------------------------------------
        self.start = 1
        self.rw = 0
        self.slave_addr = SUPPORTED_SLAVE_ADDR
        self.reg_addr = 0
        self.write_data = 0

        # --- observed-output fields (monitor fills these) --------------
        self.read_data = 0
        self.busy = 0
        self.done = 0
        self.ack_error = 0

    # ------------------------------------------------------------------
    # Constrained randomization
    # ------------------------------------------------------------------
    def randomize(self, **constraints):
        """Constrained-randomize the stimulus fields.

        - ``slave_addr``: 40 % chance of the supported address ``0x50``
          (so supported-slave behavior is exercised frequently) and 60 %
          chance of a uniform 7-bit address (explores unsupported-slave
          NACK paths).
        - ``rw``, ``reg_addr``, ``write_data``: uniform over their full
          widths.
        - ``start`` is always 1: this item always represents a request to
          be presented while idle.

        Any keyword ``constraints`` override fields after generation, e.g.
        ``item.randomize(rw=1, reg_addr=0x00)``.  Unknown field names
        raise AttributeError so typos fail loudly.
        """
        if random.random() < 0.4:
            self.slave_addr = SUPPORTED_SLAVE_ADDR
        else:
            self.slave_addr = random.randrange(0x00, 0x80)  # 0 .. 0x7F

        self.rw = random.randrange(0, 2)
        self.reg_addr = random.randrange(0x00, 0x100)  # 0 .. 0xFF
        self.write_data = random.randrange(0x00, 0x100)  # 0 .. 0xFF
        self.start = 1

        for name, value in constraints.items():
            if not hasattr(self, name):
                raise AttributeError(
                    f"I2CTransaction.randomize() constraint '{name}' is "
                    f"not a field of I2CTransaction"
                )
            setattr(self, name, value)

        return True

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def check_inputs_valid(self):
        """Raise ValueError if any stimulus field exceeds its port width.

        Mirrors the width validation performed by the Python reference
        model (I2CReferenceModel.transact).
        """
        if self.rw not in (0, 1):
            raise ValueError(f"rw must be 1 bit, got {self.rw}")
        if not 0 <= self.slave_addr <= 0x7F:
            raise ValueError(
                f"slave_addr must be {SLAVE_ADDR_WIDTH} bits, got "
                f"{self.slave_addr}"
            )
        if not 0 <= self.reg_addr <= 0xFF:
            raise ValueError(
                f"reg_addr must be {REG_ADDR_WIDTH} bits, got {self.reg_addr}"
            )
        if not 0 <= self.write_data <= 0xFF:
            raise ValueError(
                f"write_data must be {DATA_WIDTH} bits, got {self.write_data}"
            )
        return True

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def __str__(self):
        return (
            f"I2CTransaction(start={self.start}, rw={self.rw}, "
            f"slave_addr={self.slave_addr:#06x}, "
            f"reg_addr={self.reg_addr:#04x}, "
            f"write_data={self.write_data:#04x}, "
            f"read_data={self.read_data:#04x}, "
            f"busy={self.busy}, done={self.done}, ack_error={self.ack_error})"
        )