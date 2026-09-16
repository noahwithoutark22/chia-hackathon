"""hamming_encoder transaction / sequence_item for the cocotb + pyuvm bench.

Stage 1 (contract) artifact of the CHIA environment generator.

Defines the single pyuvm ``uvm_sequence_item`` type shared by every
component of the generated testbench.  Field names, widths, and meaning are
authoritative for later stages and are recorded in CONTRACT.md; the DUT
port list comes verbatim from ``benchmarks/hamming_encoder/
hamming_encoder.sv`` and ``generated/designs/hamming_encoder/rtl/
rtl_info.json``.

The DUT is a *purely combinational* Hamming encoder: each transaction
represents one encode operation -- drive ``data_in``, then sample the
combinationally-settled ``code_out`` (latency 0).  The testbench reference
clock ``clk`` and the environment-only reset ``tb_reset`` are structural
testbench signals, **not** transaction fields (UVM rules): they have no DUT
pins and must never appear in an item.
"""

import random

from pyuvm import uvm_sequence_item

from tb.dut_helper import (
    DEFAULT_DATA_WIDTH,
    DEFAULT_SECDED,
    HammingConf,
)


class HammingTransaction(uvm_sequence_item):
    """One combinational Hamming encode operation plus its observed output.

    Stimulus attribute (maps 1:1 to the DUT ``data_in`` input port)::

        data_in    int, DATA_WIDTH bits   data word to encode

    Observed-output attribute (filled in by the monitor after the
    combinational settle, maps 1:1 to the DUT ``code_out`` output port)::

        code_out   int, CODE_WIDTH bits   encoded Hamming codeword

    Elaboration-configuration attributes (NOT DUT-port fields; recorded so
    the scoreboard can call the reference model with the *generator
    constants* it needs)::

        data_width int   DATA_WIDTH elaboration parameter (K)
        secded     int   0 or 1, SECDED elaboration parameter
        code_width int   derived CODE_WIDTH = BASE_WIDTH + (SECDED ? 1 : 0)

    ``data_width`` / ``secded`` default to the RTL/spec elaboration defaults
    (4, 0) but each test elaborates its own configuration; use
    :meth:`HammingTransaction.configure` (or the constructor keyword
    arguments) to set the class/instance geometry for the active
    elaboration before creating items.
    """

    # Class-level elaboration defaults (authoritative: hamming_encoder.sv
    # declares DATA_WIDTH = 4, SECDED = 1'b0; spec.md section 2.1 agrees).
    DATA_WIDTH = DEFAULT_DATA_WIDTH
    SECDED = DEFAULT_SECDED

    # Fields that ``randomize(**constraints)`` will accept.  ``data_width``,
    # ``secded`` and ``code_width`` are excluded on purpose: constraining
    # them per-item would silently desync the item's geometry from the DUT
    # elaboration it was created for.
    _RANDOMIZABLE_FIELDS = ("data_in", "code_out")

    def __init__(self, name="hamming_transaction", data_width=None, secded=None):
        super().__init__(name)

        # --- elaboration configuration for this item ------------------
        self.data_width = int(
            data_width if data_width is not None else type(self).DATA_WIDTH
        )
        self.secded = int(bool(
            secded if secded is not None else type(self).SECDED
        ))
        conf = HammingConf.compute(self.data_width, self.secded)
        self.code_width = conf.code_width

        # --- stimulus field -------------------------------------------
        self.data_in = 0

        # --- observed-output field (monitor fills this) ----------------
        self.code_out = 0

    # ------------------------------------------------------------------
    # Geometry configuration
    # ------------------------------------------------------------------
    @classmethod
    def configure(cls, data_width=None, secded=None):
        """Set the class-level elaboration defaults for subsequently created
        items.  Call once per test (after the DUT elaboration is known),
        e.g. ``HammingTransaction.configure(data_width=8, secded=0)``."""
        if data_width is not None:
            cls.DATA_WIDTH = int(data_width)
        if secded is not None:
            cls.SECDED = int(bool(secded))
        return cls

    # ------------------------------------------------------------------
    # Constrained randomization
    # ------------------------------------------------------------------
    def randomize(self, **constraints):
        """Constrained-randomize the stimulus field.

        - ``data_in``: uniform over the full data space
          ``0 .. (1 << data_width) - 1`` (``data_width`` from this item's
          elaboration configuration).
        - ``code_out`` is not randomized (monitor-owned); a constraint may
          force it, which is only useful for directed oracle checks.

        Any keyword ``constraints`` override fields after generation, e.g.
        ``item.randomize(data_in=0b0101)``.  Unknown or non-randomizable
        field names raise AttributeError so typos fail loudly.
        """
        self.data_in = random.randrange(1 << self.data_width)

        for name, value in constraints.items():
            if name not in self._RANDOMIZABLE_FIELDS:
                raise AttributeError(
                    f"HammingTransaction.randomize() constraint '{name}' is "
                    f"not a randomizable field of HammingTransaction (allowed: "
                    f"{', '.join(self._RANDOMIZABLE_FIELDS)})"
                )
            setattr(self, name, value)

        return True

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def check_inputs_valid(self):
        """Raise ValueError if any stimulus field exceeds its port width.

        Mirrors the width validation performed by the Python reference
        model (``hamming_encode`` raises for ``data_in`` outside
        ``0 .. 2**data_width - 1`` and for non-positive ``data_width``).
        """
        if self.data_width <= 0:
            raise ValueError(
                f"DATA_WIDTH must be > 0, got {self.data_width}")
        if not 0 <= self.data_in < (1 << self.data_width):
            raise ValueError(
                f"data_in must fit in {self.data_width} bits (0 .. "
                f"{(1 << self.data_width) - 1}), got {self.data_in}")
        return True

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def __str__(self):
        def _bin(value, width):
            if width <= 0:
                return "()"
            return format(value, f"0{width}b")

        return (
            f"HammingTransaction(DATA_WIDTH={self.data_width}, "
            f"SECDED={self.secded}, "
            f"data_in={_bin(self.data_in, self.data_width)}"
            f"={self.data_in:#x}, "
            f"code_out={_bin(self.code_out, self.code_width)}"
            f"={self.code_out:#x})"
        )