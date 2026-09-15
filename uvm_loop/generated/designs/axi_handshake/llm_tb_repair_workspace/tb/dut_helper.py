"""Lightweight helper for direct DUT pin access.

Centralises every read/write of a DUT signal behind a single object so
that drivers, monitors, and checkers share one consistent API.  This is
*plain Python* — there is no SystemVerilog interface involved.

Usage in a component::

    from dut_helper import DutHelper

    # obtain helper (typically via ConfigDB)
    helper = ConfigDB().get(None, "", "dut_helper")
    helper.write_inputs(s_valid=1, s_data=0xAB, m_ready=0)
    await ReadOnly()            # let signals propagate
    rd = helper.read_outputs()
"""

from cocotb.triggers import RisingEdge, ReadOnly


class DutHelper:
    """Facade over the cocotb ``dut`` handle for the axi_handshake DUT."""

    # Signal names kept in one place so a rename is a one-line fix.
    _INPUT_PINS = ("s_valid", "s_data", "m_ready")
    _OUTPUT_PINS = ("s_ready", "m_valid", "m_data")

    def __init__(self, dut):
        self._dut = dut

    # ------------------------------------------------------------------
    # Write helpers  (driver uses these)
    # ------------------------------------------------------------------

    def write_inputs(self, *, s_valid: int = 0, s_data: int = 0,
                     m_ready: int = 0):
        """Drive all DUT input signals (excluding clk / rst_n)."""
        self._dut.s_valid.value = s_valid & 0x1
        self._dut.s_data.value = s_data & 0xFF
        self._dut.m_ready.value = m_ready & 0x1

    # ------------------------------------------------------------------
    # Read helpers  (monitor / scoreboard use these)
    # ------------------------------------------------------------------

    def read_outputs(self) -> dict:
        """Return current values of all DUT output signals."""
        return {
            "s_ready": int(self._dut.s_ready.value),
            "m_valid": int(self._dut.m_valid.value),
            "m_data": int(self._dut.m_data.value),
        }

    def read_inputs(self) -> dict:
        """Return current values of all DUT input signals (except clk/rst_n)."""
        return {
            "s_valid": int(self._dut.s_valid.value),
            "s_data": int(self._dut.s_data.value),
            "m_ready": int(self._dut.m_ready.value),
        }

    # ------------------------------------------------------------------
    # Signal name accessors (for introspection / ConfigDB sharing)
    # ------------------------------------------------------------------

    @property
    def input_pin_names(self):
        return list(self._INPUT_PINS)

    @property
    def output_pin_names(self):
        return list(self._OUTPUT_PINS)
