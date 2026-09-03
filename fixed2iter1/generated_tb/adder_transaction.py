"""Transaction / sequence_item for the parameterized adder DUT.

This is a pyuvm ``uvm_sequence_item`` subclass that carries every DUT
input field plus (for convenience) a copy of the expected outputs so
that the scoreboard can compare DUT results against the reference model
prediction.

Field names use short, lowercase names that mirror the Verilog port
names.  Types are plain Python ``int`` — cocotb will handle the
width-aware conversion when driving / sampling.
"""

from pyuvm import uvm_sequence_item


class AdderTransaction(uvm_sequence_item):
    """Sequence item for the ``adder`` DUT.

    Attributes
    ----------
    a : int
        First WIDTH-bit unsigned operand (DUT input).
    b : int
        Second WIDTH-bit unsigned operand (DUT input).
    cin : int
        Carry-in (DUT input, 1 bit).
    exp_sum : int | None
        Expected WIDTH-bit sum output (set by the scoreboard / reference
        model before comparison).
    exp_cout : int | None
        Expected carry-out (set by the scoreboard / reference model
        before comparison).
    """

    def __init__(self, name="adder_transaction"):
        super().__init__(name)
        # --- DUT input fields -------------------------------------------
        self.a: int = 0
        self.b: int = 0
        self.cin: int = 0
        # --- expected output fields (populated by ref model / scorebd) --
        self.exp_sum: int = 0
        self.exp_cout: int = 0

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def do_copy(self, other):
        """UVM-style deep copy."""
        super().do_copy(other)
        self.a = other.a
        self.b = other.b
        self.cin = other.cin
        self.exp_sum = other.exp_sum
        self.exp_cout = other.exp_cout

    def __str__(self):
        return (
            f"AdderTransaction(a=0x{self.a:X}, b=0x{self.b:X}, "
            f"cin={self.cin}, exp_sum=0x{self.exp_sum:X}, "
            f"exp_cout={self.exp_cout})"
        )

    def __eq__(self, other):
        if not isinstance(other, AdderTransaction):
            return NotImplemented
        return (
            self.a == other.a
            and self.b == other.b
            and self.cin == other.cin
            and self.exp_sum == other.exp_sum
            and self.exp_cout == other.exp_cout
        )
