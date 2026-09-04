"""Top-level cocotb + pyuvm testbench entry point for the ``adder`` DUT.

This module is the ``python_test_module`` referenced by the simulation
manifest.  It contains a small number of ``@cocotb.test()`` coroutines
that:

  - read which UVM test class to run from ``UVM_TESTNAME`` (a string,
    mirroring SV-UVM ``+UVM_TESTNAME``),
  - start the clock with ``cocotb.clock.Clock`` and apply the reset via
    the shared ``DUTHelper`` (per CONTRACT.md clock/reset conventions),
  - populate the ``ConfigDB`` keys defined in CONTRACT.md Section 6,
  - call ``await uvm_root().run_test(<test_name>)``,
  - wrap the run in a watchdog so a hung test fails within a bounded
    number of clock cycles instead of silently exhausting the whole
    simulation.

Environment variables
~~~~~~~~~~~~~~~~~~~~~
``UVM_TESTNAME`` : name of the pyuvm test class to run.  Must be one of
    the test class names registered by ``generated_tb/adder_test.py``
    (e.g. ``AdderDirectedTest``, ``AdderCornerCaseTest``,
    ``AdderRandomTest``, ``AdderFullRegressionTest``).  Defaults to
    ``AdderFullRegressionTest`` when unset.
``CLK_PERIOD_NS`` : clock period in nanoseconds (default ``10``).
``RESET_HOLD_CYCLES`` : number of clock cycles reset is held before
    release at start (default ``5``).
``WATCHDOG_CYCLES`` : maximum number of clock cycles the whole run may
    take before the watchdog fails the test (default ``20000``).
"""

from __future__ import annotations

import os
import sys

import cocotb
from cocotb.clock import Clock

from pyuvm import uvm_root, ConfigDB

# ---------------------------------------------------------------------------
# Ensure ``generated_tb`` modules are importable.  When cocotb runs with the
# ``MODULE=generated_tb.test_top`` setting, this directory is on sys.path
# already; defensively add it so the imports below are robust.
# ---------------------------------------------------------------------------
_GEN_DIR = os.path.dirname(os.path.abspath(__file__))
if _GEN_DIR not in sys.path:
    sys.path.insert(0, _GEN_DIR)

# Import the DUT helper and all test classes so that every ``uvm_test``
# subclass registers itself in the pyuvm factory under its class name.
# (pyuvm registers every ``uvm_void`` subclass by ``cls.__name__`` at class
# creation time; importing the module is what makes the names resolvable.)
from dut_helper import DUTHelper            # noqa: E402
import adder_test                            # noqa: E402,F401  (registers tests)

# The adder's WIDTH parameter (default 8).  Matching the RTL parameter.
_ADDER_WIDTH = 8

# Tunable from the environment.
_CLK_PERIOD_NS = float(os.environ.get("CLK_PERIOD_NS", "10"))
_RESET_HOLD_CYCLES = int(os.environ.get("RESET_HOLD_CYCLES", "5"))
_WATCHDOG_CYCLES = int(os.environ.get("WATCHDOG_CYCLES", "20000"))
_DEFAULT_TEST = os.environ.get("UVM_TESTNAME", "AdderFullRegressionTest")


def _populate_configdb(dut) -> tuple[DUTHelper, int]:
    """Populate the shared ConfigDB keys defined in CONTRACT.md Section 6.

    Returns the constructed ``DUTHelper`` and the adder ``width`` so the
    top-level test can reuse them for reset sequencing.
    """
    helper = DUTHelper(dut, _ADDER_WIDTH)

    ConfigDB().set(None, "", "dut", dut)
    ConfigDB().set(None, "", "dut_helper", helper)
    ConfigDB().set(None, "", "width", _ADDER_WIDTH)
    ConfigDB().set(None, "", "clock_name", helper.clock_name)
    ConfigDB().set(None, "", "reset_name", helper.reset_name)
    ConfigDB().set(None, "", "reset_active_low", helper.reset_active_low)

    return helper, _ADDER_WIDTH


async def _start_clock_and_reset(dut, helper: DUTHelper) -> None:
    """Start the free-running clock and perform the initial reset.

    The clock is a continuous cocotb ``Clock`` on ``dut.clk`` (per
    CONTRACT.md Section 2/3).  The active-low asynchronous reset
    (``rst_n``) is asserted, held for ``RESET_HOLD_CYCLES`` edges, then
    released so the DUT starts from a known-zero state.
    """
    cocotb.start_soon(Clock(dut.clk, _CLK_PERIOD_NS, units="ns").start())

    # Drive the data inputs to a known (zero) value before and during reset
    # so the monitor never reads an X/Z on an undriven input while it is
    # sampling the DUT pins.
    await helper.set_inputs(a=0, b=0, cin=0)

    # Assert reset (active-low => drive rst_n low), hold, then release.
    await helper.reset_dut(_RESET_HOLD_CYCLES)

    # Let outputs settle cleanly after de-assertion before any stimulus.
    await helper.wait_clks(1)


async def _run_with_watchdog(test_name: str) -> None:
    """Run ``uvm_root().run_test`` inside a bounded-time watchdog.

    If the UVM run does not complete within ``WATCHDOG_CYCLES`` clock
    cycles (bounded by ``Timer`` scaled from the clock period), the run is
    aborted and the test fails — so a hung environment cannot silently
    consume the entire simulation.

    ``keep_singletons=True`` is required: this tb_top (the cocotb test)
    establishes the shared ``ConfigDB`` keys (Section 6 of CONTRACT.md)
    *before* the UVM run, and pyuvm's ``run_test`` would otherwise clear
    the ``ConfigDB`` singleton when rebuilding the tree.
    """
    timeout_ns = _CLK_PERIOD_NS * _WATCHDOG_CYCLES

    cocotb.log.info(
        "Launching UVM test '%s' with watchdog timeout of %d cycles "
        "(%.1f ns)",
        test_name, _WATCHDOG_CYCLES, timeout_ns,
    )
    await cocotb.triggers.with_timeout(
        uvm_root().run_test(test_name, keep_singletons=True),
        timeout_ns,
        "ns",
    )
    cocotb.log.info("UVM test '%s' completed within watchdog bounds.", test_name)


@cocotb.test()
async def run_uvm_test(dut):
    """Run the UVM test named by ``UVM_TESTNAME`` within a watchdog."""
    test_name = os.environ.get("UVM_TESTNAME", _DEFAULT_TEST)

    # Populate the shared ConfigDB before building any component.
    helper, width = _populate_configdb(dut)

    cocotb.log.info(
        "=== Adder cocotb+pyuvm testbench: running test '%s' "
        "(WIDTH=%d, clk_period=%sns) ===",
        test_name, width, _CLK_PERIOD_NS,
    )

    # Start the clock and bring the DUT out of reset.
    await _start_clock_and_reset(dut, helper)

    # Run the requested UVM test (drives sequences -> scoreboard/coverage/
    # assertions).  Wrapped in a watchdog so a hang fails cleanly.
    await _run_with_watchdog(test_name)
