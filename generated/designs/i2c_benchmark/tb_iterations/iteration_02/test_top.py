"""Stage 6 (integration) artifact of the CHIA generator: cocotb top level.

This module is the single ``@cocotb.test()`` coroutine that cocotb invokes
when the Makefile specifies ``MODULE = test_top``.  It:

1. Starts the master clock (``clk``, period = ``I2C_CLK_PERIOD_NS`` ns).
2. Applies the active-low asynchronous reset (``rst_n``) plus deasserted
   stimulus inputs for a bounded number of cycles to bring the DUT into a
   known idle state.
3. Populates pyuvm ``ConfigDB`` with the DUT handle, the shared
   ``I2CDutPins`` wrapper, and the ``ClockReset`` descriptor (exactly the
   CONTRACT.md section 5 keys).
4. Arms the bounded clock-cycle watchdog (CONTRACT.md sections 8/11.2).
5. Reads ``UVM_TESTNAME`` (analogous to SV UVM's ``+UVM_TESTNAME``
   plusarg) and awaits ``uvm_root().run_test(<class>, keep_singletons=True)``.
   The test classes live in ``tb/test.py``; importing it registers them
   with pyuvm's factory so the name resolves at runtime.
6. Kills the watchdog on completion (success or failure).

pyuvm 5.0 compatibility notes (see CONTRACT.md stage-6 appendix):

* pyuvm 5.0's ``run_test`` defaults to ``keep_singletons=False``, which
  rebuilds the ConfigDB/factory singletons *before* ``build_phase``,
  silently discarding the keys set here; ``keep_singletons=True`` keeps
  them intact across the run.
* Stock pyuvm 5.0 accepts the wildcard store form ``set(None, "*", ...)``
  and the empty-path retrieve form ``get(component, "", ...)`` used
  throughout the bench, so no shims are required (unlike the FIFO bench on
  pyuvm 3.0.0).
"""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from pyuvm import ConfigDB, uvm_root

from tb import test as _tb_test_registry  # noqa: F401  (registers uvm_test classes)
from tb.assertions import launch_watchdog
from tb.dut_helper import (
    KEY_CLK_RST,
    KEY_DUT,
    KEY_DUT_PINS,
    ClockReset,
    I2CDutPins,
)

# ---------------------------------------------------------------------------
# Defaults (overridable through the Makefile / environment)
# ---------------------------------------------------------------------------
DEFAULT_CLK_PERIOD_NS = 10          # 100 MHz
DEFAULT_WATCHDOG_CYCLES = 300000    # generous bound, well above any scenario
DEFAULT_TESTNAME = "I2C01ResetBehaviorTest"


def _get_int_env(name, default):
    """Read an integer environment variable, falling back to *default*."""
    raw = os.environ.get(name)
    if raw is not None:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default
    return default


async def _drive_i2c_pullups(dut):
    """Model the I2C open-drain pull-ups (CONTRACT.md section 3).

    The DUT only ever *releases* scl/sda to high impedance; the raised
    bus level must come from the environment.  Verilator reports a
    released, otherwise-undriven line as '0' (not 'z'), so the idle /
    released checks (``scl_is_released`` / ``sda_is_released``) would
    wrongly fail without an explicit high drive.  Keep both lines driven
    high on every clock cycle; a real DUT pull-low would override this
    drive per the RTL resolution.
    """
    while True:
        dut.scl.value = 1
        dut.sda.value = 1
        await ClockCycles(dut.clk, 1)


@cocotb.test()
async def i2c_master_tb(dut):
    """Single cocotb entry point — mirrors SV UVM's ``+UVM_TESTNAME`` flow.

    ``UVM_TESTNAME`` selects which ``uvm_test`` subclass (tb/test.py) to
    run; ``I2C_SEED`` (randomized test), ``I2C_CLK_PERIOD_NS`` and
    ``I2C_WATCHDOG_CYCLES`` are configurable as well.
    """
    clock_period_ns = _get_int_env("I2C_CLK_PERIOD_NS", DEFAULT_CLK_PERIOD_NS)
    watchdog_cycles = _get_int_env("I2C_WATCHDOG_CYCLES", DEFAULT_WATCHDOG_CYCLES)
    test_name = os.environ.get("UVM_TESTNAME", DEFAULT_TESTNAME)

    dut._log.info(
        "i2c_master_tb: UVM_TESTNAME=%s clk_period_ns=%d watchdog_cycles=%d",
        test_name, clock_period_ns, watchdog_cycles)

    # -- start the master clock -------------------------------------------
    # posedge synchronous clock, period chosen by the environment
    # (the DUT is otherwise agnostic to the clock frequency).
    cocotb.start_soon(Clock(dut.clk, clock_period_ns, units="ns").start())

    # -- apply reset + idle stimulus ---------------------------------------
    # Active-low asynchronous reset (CONTRACT.md section 3); all transaction
    # inputs are held deasserted so the DUT settles to the reset/idle state.
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.rw.value = 0
    dut.slave_addr.value = 0
    dut.reg_addr.value = 0
    dut.write_data.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # -- model the I2C open-drain pull-ups (CONTRACT.md section 3) --------
    # The DUT releases scl/sda to high impedance and the environment is
    # responsible for the raised bus level.  Without this explicit high
    # drive the released lines read '0' in Verilator and every
    # bus-idle / scl-sda-released check fails.
    cocotb.start_soon(_drive_i2c_pullups(dut))

    # -- populate ConfigDB (CONTRACT.md section 5) ------------------------
    pins = I2CDutPins(dut)
    clkrs = ClockReset(
        clock_name="clk",
        reset_name="rst_n",
        reset_polarity="active_low",
        reset_type="asynchronous",
        clock_period_ns=clock_period_ns,
        reset_assert_value=0,
    )
    ConfigDB().set(None, "*", KEY_DUT, dut)
    ConfigDB().set(None, "*", KEY_DUT_PINS, pins)
    ConfigDB().set(None, "*", KEY_CLK_RST, clkrs)

    # -- arm the bounded watchdog (CONTRACT.md sections 8/11.2) ------------
    # pins/clkrs default to the ConfigDB keys just set.  The watchdog counts
    # rising clock edges and fails the test after `watchdog_cycles`; tb_top
    # kills it on normal completion (success or failure).
    watchdog_task = launch_watchdog(clkrs=clkrs, timeout_cycles=watchdog_cycles)

    # -- run the selected UVM test -----------------------------------------
    try:
        await uvm_root().run_test(test_name, keep_singletons=True)
    finally:
        watchdog_task.kill()

    dut._log.info("i2c_master_tb: test '%s' completed", test_name)