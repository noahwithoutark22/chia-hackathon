"""Top-level cocotb entry point for the axi_handshake testbench.

This module is referenced by the Makefile as ``MODULE``.  cocotb
discovers the ``@cocotb.test()`` coroutine(s) here and runs them.

Each test:
1. Reads the UVM test class name from the ``UVM_TESTNAME`` environment
   variable (mirroring ``+UVM_TESTNAME`` in SV UVM).
2. Starts the clock via ``cocotb.clock.Clock``.
3. Applies reset per CONTRACT.md §2 (active-low synchronous, held for
   enough cycles).
4. Populates pyuvm ConfigDB with all shared objects (CONTRACT.md §5).
5. Calls ``await uvm_root().run_test(<test_class_name>)``.
6. Is wrapped by a deterministic watchdog (HARD_CONSTRAINTS) so a hung
   test cannot silently exhaust the simulation run.

Makefile usage::

    MODULE = test_top
    UVM_TESTNAME = SmokeAfterResetTest
"""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.result import SimTimeoutError
from cocotb.triggers import RisingEdge
from pyuvm import uvm_root, ConfigDB

from dut_helper import DutHelper

# Registry of all known test classes (name → class).
# The UVM_TESTNAME env var is matched against these keys.
import test_classes as _tc

TEST_CLASS_MAP = {
    "SmokeAfterResetTest":          _tc.SmokeAfterResetTest,
    "StallHoldTest":                _tc.StallHoldTest,
    "SimultaneousTransferTest":     _tc.SimultaneousTransferTest,
    "SequentialLoadsTest":          _tc.SequentialLoadsTest,
    "NoInputWhenStalledTest":       _tc.NoInputWhenStalledTest,
    "ResetDuringTransferTest":      _tc.ResetDuringTransferTest,
    "BackToBackFullRateTest":       _tc.BackToBackFullRateTest,
    "AllZeroPayloadTest":           _tc.AllZeroPayloadTest,
    "AllOnePayloadTest":            _tc.AllOnePayloadTest,
    "ProducerHoldsForeverTest":     _tc.ProducerHoldsForeverTest,
    "RandomStimulusTest":           _tc.RandomStimulusTest,
}

# Watchdog: maximum number of clock cycles before the test is killed.
# Directed tests are short; even the longest (sequential_loads) needs
# < 50 cycles.  Random stimulus runs 1000 cycles + resets.
# We use a generous multiplier.
WATCHDOG_CYCLES = 100_000

# Default clock period (ns)
DEFAULT_CLOCK_PERIOD_NS = 10


@cocotb.test()
async def run_axi_handshake_test(dut):
    """Single cocotb entry point for all UVM test classes.

    Selects the test class via ``UVM_TESTNAME`` env var.
    """
    # ------------------------------------------------------------------
    # 1. Resolve the test class
    # ------------------------------------------------------------------
    test_name = os.environ.get("UVM_TESTNAME", "SmokeAfterResetTest")
    if test_name not in TEST_CLASS_MAP:
        available = ", ".join(sorted(TEST_CLASS_MAP.keys()))
        raise ValueError(
            f"Unknown UVM_TESTNAME='{test_name}'. "
            f"Available: {available}"
        )
    test_cls = TEST_CLASS_MAP[test_name]

    # ------------------------------------------------------------------
    # 2. Start the clock (CONTRACT.md §2: posedge clk)
    # ------------------------------------------------------------------
    clock_period_ns = DEFAULT_CLOCK_PERIOD_NS
    cocotb.log.info(
        "Starting clock: period=%d ns, top_module=axi_handshake", clock_period_ns
    )
    clock = Clock(dut.clk, clock_period_ns, units="ns")
    cocotb.start_soon(clock.start())

    # ------------------------------------------------------------------
    # 3. Apply reset (CONTRACT.md §2: active-low synchronous)
    # ------------------------------------------------------------------
    dut.rst_n.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    cocotb.log.info("Reset deasserted")

    # ------------------------------------------------------------------
    # 4. Populate ConfigDB (CONTRACT.md §5)
    # ------------------------------------------------------------------
    dut_helper = DutHelper(dut)

    # Import ref_model for the scoreboard
    import ref_model

    ConfigDB().set(None, "", "dut", dut)
    ConfigDB().set(None, "", "dut_helper", dut_helper)
    ConfigDB().set(None, "", "clock_period", clock_period_ns)
    ConfigDB().set(None, "", "clk_name", "clk")
    ConfigDB().set(None, "", "rst_name", "rst_n")
    ConfigDB().set(None, "", "reset_polarity", "active_low")
    ConfigDB().set(None, "", "ref_model", ref_model)

    cocotb.log.info(
        "ConfigDB populated: dut, dut_helper, clock_period=%d, "
        "clk_name='clk', rst_name='rst_n', reset_polarity='active_low', "
        "ref_model=<module>",
        clock_period_ns,
    )

    # ------------------------------------------------------------------
    # 5. Run the UVM test with a deterministic watchdog
    # ------------------------------------------------------------------
    cocotb.log.info("Launching UVM test: %s", test_name)

    # The watchdog wraps the entire UVM run: if run_test() does not
    # complete within WATCHDOG_CYCLES clock periods the test is killed.
    watchdog_ns = WATCHDOG_CYCLES * clock_period_ns
    try:
        await cocotb.triggers.with_timeout(
            uvm_root().run_test(test_cls, keep_singletons=True),
            watchdog_ns,
            "ns",
        )
    except SimTimeoutError:
        cocotb.log.error(
            "WATCHDOG: test '%s' did not complete within %d clock cycles "
            "(%d ns).  Killing simulation.",
            test_name,
            WATCHDOG_CYCLES,
            watchdog_ns,
        )
        raise

    cocotb.log.info("UVM test '%s' completed successfully", test_name)
