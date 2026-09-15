"""Stage 6 (integration) artifact of the CHIA generator: cocotb top level.

This module is the single ``@cocotb.test()`` coroutine that cocotb invokes
when the Makefile specifies ``MODULE = test_top``.  It:

1. Starts the master clock (``clk``, period = ``AES_CLK_PERIOD_NS`` ns).
2. Applies the active-low asynchronous reset (``rst_n``) plus deasserted
   stimulus inputs for a bounded number of cycles to bring the DUT into a
   known idle state.
3. Populates pyuvm ``ConfigDB`` with exactly the CONTRACT.md section 7.3
   keys: ``"dut"`` (top handle), ``"dut_helper"`` (shared
   :class:`tb.dut_helper.AES128DUTHelper`), ``"clock_signal"`` (``"clk"``)
   and ``"reset_signal"`` (``"rst_n"``).
4. Arms the bounded clock-cycle watchdog (CONTRACT.md section 6/8).
5. Reads ``UVM_TESTNAME`` (analogous to SV UVM's ``+UVM_TESTNAME`` plusarg)
   and awaits ``uvm_root().run_test(<class>, keep_singletons=True)``.  The
   test classes live in ``tb/test.py``; importing it registers them with
   pyuvm's factory so the name resolves at runtime.
6. Kills the watchdog on completion (success or failure).

pyuvm 5.0 compatibility notes (CONTRACT.md stage-6 appendix):

* pyuvm 5.0's ``run_test`` defaults to ``keep_singletons=False``, which
  rebuilds the ConfigDB/factory singletons *before* ``build_phase``,
  silently discarding the keys set here; ``keep_singletons=True`` keeps
  them intact across the run.
* Stock pyuvm 5.0 accepts the wildcard store form ``set(None, "*", ...)``
  and the empty-path retrieve form ``get(component, "", ...)`` used
  throughout the bench, so no shims are required.
"""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from pyuvm import ConfigDB, uvm_root

from tb import test as _tb_test_registry  # noqa: F401  (registers uvm_test classes)
from tb.assertions import launch_watchdog
from tb.dut_helper import AES128DUTHelper, make_dut_helper

# ---------------------------------------------------------------------------
# Defaults (overridable through the Makefile / environment)
# ---------------------------------------------------------------------------
DEFAULT_CLK_PERIOD_NS = 10          # 100 MHz
DEFAULT_WATCHDOG_CYCLES = 500000    # generous bound, well above any scenario
DEFAULT_TESTNAME = "AESNistKatTest"


def _get_int_env(name, default):
    """Read an integer environment variable, falling back to *default*."""
    raw = os.environ.get(name)
    if raw is not None:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default
    return default


@cocotb.test()
async def aes128_tb(dut):
    """Single cocotb entry point — mirrors SV UVM's ``+UVM_TESTNAME`` flow.

    ``UVM_TESTNAME`` selects which ``uvm_test`` subclass (tb/test.py) to
    run; ``AES_CLK_PERIOD_NS`` and ``AES_WATCHDOG_CYCLES`` are configurable
    as well (``AES_NUM_RANDOM``/``AES_IN_FLIGHT_RESET_PROB``/
    ``AES_IDLE_RESET_PROB``/``AES_SEED`` are consumed by the randomized
    test itself).
    """
    clock_period_ns = _get_int_env("AES_CLK_PERIOD_NS", DEFAULT_CLK_PERIOD_NS)
    watchdog_cycles = _get_int_env("AES_WATCHDOG_CYCLES", DEFAULT_WATCHDOG_CYCLES)
    test_name = os.environ.get("UVM_TESTNAME", DEFAULT_TESTNAME)

    dut._log.info(
        "aes128_tb: UVM_TESTNAME=%s clk_period_ns=%d watchdog_cycles=%d",
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
    dut.key.value = 0
    dut.plaintext.value = 0
    await ClockCycles(dut.clk, 4)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # -- populate ConfigDB (CONTRACT.md section 7.3) ----------------------
    helper = make_dut_helper(dut)
    ConfigDB().set(None, "*", "dut", dut)
    ConfigDB().set(None, "*", "dut_helper", helper)
    ConfigDB().set(None, "*", "clock_signal", helper.CLOCK_SIGNAL)
    ConfigDB().set(None, "*", "reset_signal", helper.RESET_SIGNAL)

    # -- arm the bounded watchdog (CONTRACT.md sections 6/8) ---------------
    # helper defaults to the ConfigDB key just set.  The watchdog counts
    # rising clock edges and fails the test after `watchdog_cycles`; test_top
    # kills it on normal completion (success or failure).
    watchdog_task = launch_watchdog(helper=helper, timeout_cycles=watchdog_cycles)

    # -- run the selected UVM test -----------------------------------------
    try:
        await uvm_root().run_test(test_name, keep_singletons=True)
    finally:
        watchdog_task.kill()

    dut._log.info("aes128_tb: test '%s' completed", test_name)