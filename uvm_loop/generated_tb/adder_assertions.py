"""Assertion checkers (SVA replacement) for the parameterized adder DUT.

This implements the ``useful_assertions`` from the verification plan
(Stage 5 — Coverage & Assertions) as plain Python checkers.  Each checker is
an always-running coroutine started with ``cocotb.start_soon`` from the
component's ``run_phase``; it synchronizes on cocotb clock/reset triggers and
uses plain ``assert`` statements so a violation fails the test immediately.

The checkers replace SystemVerilog assertions (SVA) — there is no SV code
here, only Python.  Implemented plan items:

* ``reset_clears_sum``   — async assertion: on negedge ``rst_n``, ``sum`` -> 0.
* ``reset_clears_cout``  — async assertion: on negedge ``rst_n``, ``cout`` -> 0.
* ``output_matches_addition`` — on posedge ``clk`` (``rst_n`` high) the
  registered ``{cout, sum}`` equals the *previous* cycle's ``a + b + cin``.
* ``no_x_or_z_on_outputs`` — ``sum``/``cout`` must not be X or Z while
  ``rst_n`` is high.

All pin access goes through the shared ``DUTHelper`` (CONTRACT.md Sections 3,
5, 6) whose cached signal handles are read directly; no SV interface is used.
"""

from __future__ import annotations

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly, Timer, Combine

from pyuvm import uvm_component, ConfigDB


class AdderAssertions(uvm_component):
    """Runs the assertion checker coroutines for the adder DUT.

    Parameters
    ----------
    name : str
        Instance name (default ``"adder_assertions"``).
    parent : uvm_component
        Parent component (normally the environment).
    """

    def __init__(self, name="adder_assertions", parent=None):
        super().__init__(name, parent)
        self.width: int = 8
        self.helper = None
        self.dut = None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Retrieve the DUT access helper and width from the ConfigDB."""
        super().build_phase()
        # ConfigDB accessors, per CONTRACT.md Section 6 (keys set by tb_top).
        self.dut = ConfigDB.get(None, "", "dut")
        self.helper = ConfigDB.get(None, "", "dut_helper")
        self.width = ConfigDB.get(None, "", "width")
        self.clock_name = ConfigDB.get(None, "", "clock_name")
        self.reset_name = ConfigDB.get(None, "", "reset_name")
        self.reset_active_low = ConfigDB.get(None, "", "reset_active_low")
        self.logger.info(
            "AdderAssertions %s ready (width=%d, clk=%s, rst=%s, "
            "active_low=%s)",
            self.get_full_name(), self.width, self.clock_name,
            self.reset_name, self.reset_active_low,
        )

    # ------------------------------------------------------------------
    # Value helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_bin(handle):
        """Return the numeric value of ``handle``, or ``None`` if X/Z.

        ``int(handle.value)`` raises on X/Z, so we first inspect the string
        form; a string containing ``X`` or ``Z`` (either polarity) is mapped
        to ``None`` to flag an X/Z condition cleanly.
        """
        as_str = str(handle.value)
        if any(ch in as_str for ch in "XZxz"):
            return None
        return int(handle.value)

    # ------------------------------------------------------------------
    # Checkers (plain Python assertions replacing SVA)
    # ------------------------------------------------------------------

    async def _check_reset_clears_sum(self):
        """``reset_clears_sum``: async reset drives ``sum`` to zero.

        Triggers on the falling edge of ``rst_n`` (independent of the clock)
        and, after letting the combinational async reset propagate, asserts the
        registered ``sum`` output is cleared to zero.
        """
        while True:
            await FallingEdge(self.helper._rst_n)
            # Let the asynchronous `sum <= 0` non-blocking assignment settle.
            await Timer(1, "step")
            val = self._read_bin(self.helper._sum)
            assert val == 0, (
                f"reset_clears_sum violation: after async assertion of "
                f"{self.reset_name}, sum={val} != 0 (expected cleared to 0)"
            )

    async def _check_reset_clears_cout(self):
        """``reset_clears_cout``: async reset drives ``cout`` to zero.

        Triggers on the falling edge of ``rst_n`` (independent of the clock)
        and, after letting the combinational async reset propagate, asserts the
        registered ``cout`` is cleared to zero.
        """
        while True:
            await FallingEdge(self.helper._rst_n)
            await Timer(1, "step")
            val = self._read_bin(self.helper._cout)
            assert val == 0, (
                f"reset_clears_cout violation: after async assertion of "
                f"{self.reset_name}, cout={val} != 0 (expected cleared to 0)"
            )

    async def _check_output_matches_addition(self):
        """``output_matches_addition``: single-cycle registered adder.

        On every ``posedge clk`` while ``rst_n`` is high the registered outputs
        must equal ``a + b + cin`` computed from the inputs presented during
        the *previous* cycle (``{cout, sum} == $past(a) + $past(b) + $past(cin)``,
        the DUT's 1-cycle registered latency).

        To make the "previous cycle" inputs deterministic regardless of how the
        driver task is scheduled at the rising edge (the driver updates inputs
        in the rising-edge region), the cycle's settled inputs are captured at
        the ``FallingEdge`` (mid-cycle, guaranteed stable) and compared against
        the outputs sampled at the next ``ReadOnly`` region.
        """
        clk = self.helper._clk
        width = self.width
        mask = (1 << width) - 1

        while True:
            # Capture the inputs that the DUT will register at the next posedge
            # (settled mid-cycle, so this is ordering-independent of the driver).
            await FallingEdge(clk)
            prev_a = int(self.helper._a.value)
            prev_b = int(self.helper._b.value)
            prev_cin = int(self.helper._cin.value)

            await RisingEdge(clk)
            await ReadOnly()
            sum_val, cout_val = await self.helper.sample_outputs()

            if not self._read_bin(self.helper._rst_n):
                # Reset asserted at this edge: output forced to 0 regardless of
                # inputs (covered by reset_clears_*); skip the add check.
                continue

            total = prev_a + prev_b + prev_cin
            exp_sum = total & mask
            exp_cout = (total >> width) & 1

            assert (sum_val, cout_val) == (exp_sum, exp_cout), (
                f"output_matches_addition violation at "
                f"{cocotb.utils.get_sim_time('ns')}ns: "
                f"prev(a=0x{prev_a:0{(width + 3) // 4}X}, "
                f"b=0x{prev_b:0{(width + 3) // 4}X}, cin={prev_cin}) -> "
                f"DUT(sum=0x{sum_val:0{(width + 3) // 4}X}, cout={cout_val})"
                f" != expected(sum=0x{exp_sum:0{(width + 3) // 4}X}, "
                f"cout={exp_cout})"
            )

    async def _check_no_x_or_z_on_outputs(self):
        """``no_x_or_z_on_outputs``: outputs must not be X/Z while rst_n high.

        Samples ``sum`` and ``cout`` in the read-only region of each positive
        clock edge while ``rst_n`` is deasserted (high) and fails the test if
        either output is X or Z (a design or connectivity issue).
        """
        clk = self.helper._clk
        while True:
            await RisingEdge(clk)
            await ReadOnly()
            if not self._read_bin(self.helper._rst_n):
                continue  # reset asserted: skip (reset_clears_* handles reset)
            for name, handle in (("sum", self.helper._sum),
                                 ("cout", self.helper._cout)):
                if self._read_bin(handle) is None:
                    raise AssertionError(
                        f"no_x_or_z_on_outputs violation at "
                        f"{cocotb.utils.get_sim_time('ns')}ns: {name} is "
                        f"X or Z ('{str(handle.value)}') while "
                        f"{self.reset_name} is high"
                    )

    # ------------------------------------------------------------------
    # Run phase: launch all checkers as background tasks
    # ------------------------------------------------------------------

    async def run_phase(self) -> None:
        """Start every checker coroutine and keep running until one fails.

        Because the plan requires the checkers to run continuously and to fail
        the test immediately, they are started with ``cocotb.start_soon`` and
        awaited via :class:`cocotb.triggers.Combine`.  If any checker raises,
        the exception propagates out of ``run_phase`` and fails the test.
        """
        checkers = [
            cocotb.start_soon(self._check_reset_clears_sum()),
            cocotb.start_soon(self._check_reset_clears_cout()),
            cocotb.start_soon(self._check_output_matches_addition()),
            cocotb.start_soon(self._check_no_x_or_z_on_outputs()),
        ]
        # Checkers are infinite loops; Combine fires only if one raises, in
        # which case the exception is re-raised here to fail the test.
        await Combine(*checkers)
