"""cocotb top-level entry point for the i2c_master DUT testbench.

This module is the single ``@cocotb.test()`` coroutine that cocotb invokes
when ``MODULE = test_top`` (see Makefile and ``generation_manifest.yaml``
``python_test_module: test_top``).  It:

1. builds the shared ``I2CPins`` helper and drives a known pre-clock idle
   state (start=0, bus inputs released high; CONTRACT.md §3/§11);
2. starts the master clock (``dut.clk``, posedge, ``I2C_CLK_PERIOD_NS``;
   CONTRACT.md §6);
3. applies the synchronous active-low reset and re-syncs on ``clk``
   (CONTRACT.md §6);
4. populates pyuvm ``ConfigDB`` with the two exact keys required by every
   component -- ``"dut"`` and ``"i2c_pins"`` (CONTRACT.md §6) -- using the
   documented ``ConfigDB().set(None, "*", key, value)`` storage form;
5. selects the pyuvm test class from the ``UVM_TESTNAME`` environment
   variable (set by ``workers/sim/run.py`` from
   ``generation_manifest.yaml`` ``test_classes``, the SV ``+UVM_TESTNAME``
   analogue) and awaits ``uvm_root().run_test(test_name,
   keep_singletons=True)`` -- ``keep_singletons=True`` is REQUIRED or
   pyuvm 5.0.0 clears the ``ConfigDB`` singleton before ``build_phase`` and
   silently discards the keys set in step 4;
6. wraps ``run_test`` in a coarse simulation-time
   ``cocotb.triggers.with_timeout`` bound (the CONTRACT.md §8/§13.7 watchdog
   alternative, independent of the per-test cycle watchdog each test arms via
   ``env.arm_watchdog``); and
7. reports the shared functional ``coverage_db`` at the end.

The env launches the structural assertion checkers and the coverage sampler
in its ``build_phase`` (CONTRACT.md §16).  Importing :mod:`i2c_test` below
registers every ``uvm_test`` subclass in pyuvm's factory (auto-registration
via ``FactoryMeta``), which ``run_test("<ClassName>")`` resolves by name.
"""

import os

import cocotb
from cocotb.triggers import ClockCycles, SimTimeoutError, with_timeout

from pyuvm import ConfigDB, uvm_root

# Importing i2c_test registers every uvm_test subclass in pyuvm's factory
# registry (side effect); run_test resolves UVM_TESTNAME by name.
import i2c_test  # noqa: F401

from i2c_coverage import report_coverage
from i2c_pins import (
    I2C_CLK_PERIOD_NS,
    I2CPins,
    KEY_DUT,
    KEY_DUT_PINS,
    RESET_CYCLES,
    SETTLE_CYCLES,
    WATCHDOG_CYCLES,
    make_clock,
)

# Outer simulation-time bound in clock cycles (CONTRACT.md §8/§13.7).  It
# must exceed every test's largest legitimate scenario on a REPAIRED RTL
# with a wide margin: directed scenarios fit in ~100 cycles, the corner test
# in ~1000, the randomized run in ~20000.  The global WATCHDOG_CYCLES
# (300000) is generous and cheap.
OUTER_BUDGET_CYCLES = WATCHDOG_CYCLES
OUTER_BUDGET_NS = int(OUTER_BUDGET_CYCLES * I2C_CLK_PERIOD_NS)

# Reset applied here (CONTRACT.md §6): hold active-low reset across a few
# rising edges, then release; the synchronous deassert resynchronizes on clk.
RESET_HOLD_CYCLES = RESET_CYCLES
RESET_SETTLE_CYCLES = SETTLE_CYCLES

# UVM_TESTNAME fallback if the variable is not set (the worker always sets
# it from generation_manifest.yaml).
DEFAULT_TEST = "ResetIdleCheckTest"


@cocotb.test()
async def i2c_tb_top(dut):
    """Single cocotb entry point for the i2c_master pyuvm environment."""
    test_name = os.environ.get("UVM_TESTNAME", DEFAULT_TEST).strip()
    dut._log.info(
        "i2c_tb_top: UVM_TESTNAME=%s  cocotb=%s",
        test_name, cocotb.__version__,
    )

    pins = I2CPins(dut)

    # -- pre-clock idle state (CONTRACT.md §3/§11) ---------------------------
    pins.drive_reset(True)   # rst_n = 0: reset asserted (active low)
    pins.release_inputs()    # start=0, addr=0, rw=0, tx=0, sda_in=1, scl_in=1

    # -- master clock (CONTRACT.md §6) ----------------------------------------
    clock = make_clock(dut)  # Clock(pins.clk, I2C_CLK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    # -- reset sequence (CONTRACT.md §6) --------------------------------------
    await ClockCycles(pins.clk, RESET_HOLD_CYCLES)
    pins.drive_reset(False)  # release reset; the synchronous deassert
    await ClockCycles(pins.clk, RESET_SETTLE_CYCLES)  # re-syncs on clk

    # -- ConfigDB (CONTRACT.md §6, exact keys, documented storage form) -------
    ConfigDB().set(None, "*", KEY_DUT, dut)
    ConfigDB().set(None, "*", KEY_DUT_PINS, pins)

    # -- run the selected pyuvm test under the coarse sim-time bound ----------
    try:
        await with_timeout(
            uvm_root().run_test(test_name, keep_singletons=True),
            OUTER_BUDGET_NS,
            "ns",
        )
    except SimTimeoutError:
        dut._log.error(
            "i2c_tb_top: OUTER WATCHDOG fired: run_test('%s') exceeded "
            "%d cycles (%d ns) of simulation time. The per-test cycle "
            "watchdog and the worker's OS timeout remain as backstops.",
            test_name, OUTER_BUDGET_CYCLES, OUTER_BUDGET_NS,
        )
        raise
    finally:
        report_coverage(logger=print)

    dut._log.info("i2c_tb_top: test '%s' completed", test_name)