"""Transaction (sequence_item) for the axi_handshake DUT.

Every non-clock/non-reset DUT pin appears as a plain Python attribute.
The driver populates the input-side fields; the monitor populates the
output-side fields; the scoreboard compares the two.
"""

from pyuvm import uvm_sequence_item


class AxiHandshakeTxn(uvm_sequence_item):
    """AXI-Stream elastic-buffer transaction.

    Attributes
    ----------
    s_valid : int
        1-bit source valid (DUT input).
    s_data : int
        8-bit source payload (DUT input).
    m_ready : int
        1-bit downstream ready (DUT input).
    s_ready : int
        1-bit DUT ready (DUT output).
    m_valid : int
        1-bit output valid (DUT output).
    m_data : int
        8-bit output payload (DUT output).
    """

    def __init__(self, name="AxiHandshakeTxn"):
        super().__init__(name)

        # --- driver-side (DUT inputs) ---
        self.s_valid = 0
        self.s_data = 0
        self.m_ready = 0

        # --- monitor-side (DUT outputs) ---
        self.s_ready = 0
        self.m_valid = 0
        self.m_data = 0

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def set_inputs(self, s_valid: int, s_data: int, m_ready: int):
        """Populate the driver-side fields in one call."""
        self.s_valid = int(s_valid) & 0x1
        self.s_data = int(s_data) & 0xFF
        self.m_ready = int(m_ready) & 0x1
        return self

    def set_outputs(self, s_ready: int, m_valid: int, m_data: int):
        """Populate the monitor-side fields in one call."""
        self.s_ready = int(s_ready) & 0x1
        self.m_valid = int(m_valid) & 0x1
        self.m_data = int(m_data) & 0xFF
        return self

    def do_copy(self, rhs):
        super().do_copy(rhs)
        self.s_valid = rhs.s_valid
        self.s_data = rhs.s_data
        self.m_ready = rhs.m_ready
        self.s_ready = rhs.s_ready
        self.m_valid = rhs.m_valid
        self.m_data = rhs.m_data

    def __eq__(self, other):
        if not isinstance(other, AxiHandshakeTxn):
            return NotImplemented
        return (
            self.s_valid == other.s_valid
            and self.s_data == other.s_data
            and self.m_ready == other.m_ready
            and self.s_ready == other.s_ready
            and self.m_valid == other.m_valid
            and self.m_data == other.m_data
        )

    def __repr__(self):
        return (
            f"AxiHandshakeTxn("
            f"s_valid={self.s_valid}, s_data=0x{self.s_data:02X}, "
            f"m_ready={self.m_ready} | "
            f"s_ready={self.s_ready}, m_valid={self.m_valid}, "
            f"m_data=0x{self.m_data:02X})"
        )
