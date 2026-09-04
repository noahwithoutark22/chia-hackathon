"""Thin helper for direct DUT pin access.

This module wraps the cocotb ``dut`` handle and exposes named helpers
that every UVM component can retrieve from the ``ConfigDB`` and use to
drive or sample signals without guessing pin names or widths.

All helpers are plain synchronous Python — the caller is responsible for
using them inside ``@cocotb.coroutine`` / ``async def`` blocks at the
appropriate clock edge.

Usage inside a driver / monitor / scoreboard::

    from dut_helper import DUTHelper
    helper: DUTHelper = ConfigDB.get(None, "", "dut_helper")
    await helper.set_inputs(a=42, b=7, cin=0)
    sum_val, cout_val = await helper.sample_outputs()
"""

from __future__ import annotations

from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly, Timer
from cocotb.handle import SimHandleBase


class DUTHelper:
    """Centralized pin-access helper for the ``adder`` DUT.

    Parameters
    ----------
    dut : SimHandleBase
        The cocotb ``dut`` handle.
    width : int
        Parameterized bit-width of the adder (default 8).
    """

    def __init__(self, dut: SimHandleBase, width: int = 8):
        self.dut = dut
        self.width = width
        # Cache signal handles for performance.
        self._a = dut.a
        self._b = dut.b
        self._cin = dut.cin
        self._sum = dut.sum
        self._cout = dut.cout
        self._clk = dut.clk
        self._rst_n = dut.rst_n

    # ------------------------------------------------------------------
    # Signal names (read-only properties for documentation / logging)
    # ------------------------------------------------------------------

    @property
    def clock_name(self) -> str:
        return "clk"

    @property
    def reset_name(self) -> str:
        return "rst_n"

    @property
    def reset_active_low(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Input helpers
    # ------------------------------------------------------------------

    async def set_inputs(self, a: int = 0, b: int = 0, cin: int = 0) -> None:
        """Drive all DUT input signals (excluding clk / rst_n).

        Call this *after* ``RisingEdge(clk)`` in a driver to allow
        combinational setup before the next registering edge.
        """
        self._a.value = a
        self._b.value = b
        self._cin.value = cin

    async def set_reset(self, active: bool) -> None:
        """Drive rst_n.  ``active=True`` means assert reset (drive low)."""
        self._rst_n.value = 0 if active else 1

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    async def sample_outputs(self) -> tuple[int, int]:
        """Sample and return ``(sum, cout)`` after outputs have settled.

        The caller should wait for ``ReadOnly()`` (or a clock edge + small
        delta) before calling so that the registered values are stable.
        """
        sum_val = int(self._sum.value)
        cout_val = int(self._cout.value)
        return sum_val, cout_val

    # ------------------------------------------------------------------
    # Clock / reset utilities
    # ------------------------------------------------------------------

    async def wait_clks(self, n: int = 1) -> None:
        """Wait for *n* positive clock edges."""
        for _ in range(n):
            await RisingEdge(self._clk)

    async def wait_negedge_rst(self) -> None:
        """Wait for the falling edge of ``rst_n`` (reset assertion)."""
        await FallingEdge(self._rst_n)

    async def wait_posedge_rst(self) -> None:
        """Wait for the rising edge of ``rst_n`` (reset de-assertion)."""
        await RisingEdge(self._rst_n)

    async def reset_dut(self, hold_cycles: int = 2) -> None:
        """Assert reset, hold for *hold_cycles* clock cycles, then release."""
        self._rst_n.value = 0
        for _ in range(hold_cycles):
            await RisingEdge(self._clk)
        self._rst_n.value = 1
