"""cocotb top-level entry point for the SHA-256 DUT testbench.

This module is the single ``@cocotb.test()`` coroutine that cocotb
invokes when ``MODULE = test_top`` (see Makefile and
``generation_manifest.yaml`` ``python_test_module: test_top``).  It:

1. builds the shared ``Sha256Pins`` helper and drives a known pre-clock
   idle state (start=0, block=0; CONTRACT.md §3/§11);
2. starts the master clock (``dut.clk``, posedge, ``CLK_PERIOD_NS``;
   CONTRACT.md §6);
3. applies the active-low ASYNCHRONOUS reset and re-syncs on ``clk``
   (CONTRACT.md §6);
4. populates pyuvm ``ConfigDB`` with the two exact keys required by every
   component -- ``"dut"`` and ``"sha256_pins"`` (CONTRACT.md §5) -- using
   the documented ``ConfigDB().set(None, "*", key, value)`` storage form;
5. selects the pyuvm test class from the ``UVM_TESTNAME`` environment
   variable (set by ``workers/sim/run.py`` from
   ``generation_manifest.yaml`` ``test_classes``, the SV ``+UVM_TESTNAME``
   analogue) and awaits ``uvm_root().run_test(test_name,
   keep_singletons=True)`` -- ``keep_singletons=True`` is REQUIRED or
   pyuvm 5.0.0 clears the ``ConfigDB`` singleton before ``build_phase`` and
   silently discards the keys set in step 4;
6. wraps ``run_test`` in a coarse simulation-time
   ``cocotb.triggers.with_timeout`` bound (the CONTRACT.md §1/§7 watchdog
   alternative) so a hung test cannot run forever, independently of the
   per-test cycle watchdog the tests arm via ``env.assertions``; and
7. reports the shared functional ``coverage_db`` at the end.

The env starts the structural assertion checkers and coverage sampler in
its ``build_phase`` (CONTRACT.md §15).  Importing :mod:`sha256_test` below
registers every ``uvm_test`` subclass in pyuvm's factory (auto-registration
via ``FactoryMeta``), which ``run_test("<ClassName>")`` resolves by name.
"""

import os

import cocotb
from cocotb.triggers import ClockCycles, SimTimeoutError, with_timeout

from pyuvm import ConfigDB, uvm_root

# Importing sha256_test registers every uvm_test subclass in pyuvm's
# factory registry (side effect); run_test resolves UVM_TESTNAME by name.
import sha256_test  # noqa: F401

from sha256_coverage import report_coverage
from sha256_pins import CLK_PERIOD_NS, Sha256Pins, make_clock

# Outer simulation-time bound in clock cycles (CONTRACT.md §7).  Must
# exceed every test's largest legitimate scenario on a REPAIRED RTL with a
# wide margin: directed KATs ~75..150 cycles, the corner test ~500, the
# randomized run <= ~2600 cycles.  10000 cycles is generous and cheap.
OUTER_BUDGET_CYCLES = 10000
OUTER_BUDGET_NS = int(OUTER_BUDGET_CYCLES * CLK_PERIOD_NS)

# Reset applied here (CONTRACT.md §6): hold active-low reset across a few
# rising edges, then release (asynchronous deassert resynchronizes to clk).
RESET_HOLD_CYCLES = 3
RESET_SETTLE_CYCLES = 2

# UVM_TESTNAME fallback if the variable is not set (the worker always sets
# it from generation_manifest.yaml).
DEFAULT_TEST = "Sha256ResetInitializationTest"


@cocotb.test()
async def sha256_tb_top(dut):
    """Single cocotb entry point for the SHA-256 pyuvm environment."""
    test_name = os.environ.get("UVM_TESTNAME", DEFAULT_TEST).strip()
    dut._log.info(
        "sha256_tb_top: UVM_TESTNAME=%s  cocotb=%s",
        test_name, cocotb.__version__,
    )

    pins = Sha256Pins(dut)

    # -- pre-clock idle state (CONTRACT.md §3/§11) ---------------------------
    pins.drive_reset(True)  # rst_n = 0: reset asserted (active low)
    pins.drive_start(0)     # input pins at defined deasserted values
    pins.drive_block(0)

    # -- master clock (CONTRACT.md §6) ----------------------------------------
    clock = make_clock(dut)  # Clock(pins.clk, CLK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    # -- reset sequence (CONTRACT.md §6) --------------------------------------
    await ClockCycles(pins.clk, RESET_HOLD_CYCLES)
    pins.drive_reset(False)  # release reset (async); resync on clk below
    await ClockCycles(pins.clk, RESET_SETTLE_CYCLES)

    # -- ConfigDB (CONTRACT.md §5, exact keys, documented storage form) -------
    ConfigDB().set(None, "*", "dut", dut)
    ConfigDB().set(None, "*", "sha256_pins", pins)

    # -- run the selected pyuvm test under the coarse sim-time bound ----------
    try:
        await with_timeout(
            uvm_root().run_test(test_name, keep_singletons=True),
            OUTER_BUDGET_NS,
            "ns",
        )
    except SimTimeoutError:
        dut._log.error(
            "sha256_tb_top: OUTER WATCHDOG fired: run_test('%s') exceeded "
            "%d cycles (%d ns) of simulation time. The per-test cycle "
            "watchdog and the worker's OS timeout remain as backstops.",
            test_name, OUTER_BUDGET_CYCLES, OUTER_BUDGET_NS,
        )
        raise
    finally:
        report_coverage(logger=print)

    dut._log.info("sha256_tb_top: test '%s' completed", test_name)