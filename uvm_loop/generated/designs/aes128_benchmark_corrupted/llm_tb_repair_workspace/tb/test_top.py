"""cocotb top-level entry point for the AES-128 DUT testbench (stage 6).

This module is the single ``@cocotb.test()`` coroutine that cocotb invokes
when ``MODULE = test_top`` (see Makefile and ``generation_manifest.yaml``
``python_test_module: test_top``).  It:

1. drives a known pre-clock idle state -- ``rst_n`` asserted (active-low)
   and every stimulus pin deasserted -- with ``setimmediatevalue`` so the
   first rising edges of the clock already see reset asserted
   (CONTRACT.md §3/§6);
2. starts the master clock (``dut.clk``, posedge, period
   ``2 * CLK_HALF_PERIOD_NS`` ns; CONTRACT.md §6);
3. applies the canonical synchronous active-low reset pulse via
   ``Aes128DutHelper.reset_sync_active_low()`` and lets the DUT settle to
   idle (CONTRACT.md §6: ``done == 0``, ``ciphertext == 0``);
4. populates pyuvm ``ConfigDB`` with exactly the CONTRACT.md §4 keys --
   ``"dut"`` (top handle), ``"CLK_HALF_PERIOD_NS"`` (int half-period in ns
   with default 5 -> 10 ns period / 100 MHz) and the optional sugar key
   ``"Aes128DutHelper"``  -- using the documented
   ``ConfigDB().set(None, "*", key, value)`` storage form;
5. selects the pyuvm test class from the ``UVM_TESTNAME`` environment
   variable (the SV ``+UVM_TESTNAME`` analogue; set by the runner from
   ``generation_manifest.yaml`` ``test_classes``) and awaits
   ``uvm_root().run_test(test_name, keep_singletons=True)`` --
   ``keep_singletons=True`` is REQUIRED or pyuvm 5.0.0 rebuilds the
   ConfigDB/factory singletons before ``build_phase`` and silently discards
   the keys set in step 4;
6. wraps ``run_test`` in a coarse simulation-time
   ``cocotb.triggers.with_timeout`` bound (CONTRACT.md §8 watchdog
   alternative) so a hung test cannot run forever, independent of the
   clock-cycle watchdog from ``tb/assertions.py`` that is armed here and
   killed on completion (success or failure); and
7. reports the shared functional ``coverage_db`` at the end
   (``cov_report`` in the manifest run options).

The env starts the structural assertion checkers and the coverage sampler in
its ``build_phase`` (CONTRACT.md §11.1/§11.2).  Importing :mod:`tests` below
registers every ``uvm_test`` subclass in pyuvm's factory (auto-registration
via ``FactoryMeta``), which ``run_test("<ClassName>")`` resolves by name.

All APIs used are public Cocotb 2.1.0 and public pyuvm 5.0.0.  No
SystemVerilog anywhere.
"""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, SimTimeoutError, with_timeout

from pyuvm import ConfigDB, uvm_root

# Importing tests registers every uvm_test subclass in pyuvm's factory
# registry (side effect, plus the import-time plan cross-check); run_test
# resolves UVM_TESTNAME by name.
import tests  # noqa: F401

from assertions import launch_watchdog
from coverage import report_coverage
from dut_helper import Aes128DutHelper

# ---------------------------------------------------------------------------
# Defaults (overridable via environment, mirroring the aes_benchmark family)
# ---------------------------------------------------------------------------
DEFAULT_CLK_HALF_PERIOD_NS = 5      # CONTRACT.md §4 default -> 10 ns period
DEFAULT_WATCHDOG_CYCLES = 100000    # CONTRACT.md §11.2 watchdog constant
DEFAULT_TESTNAME = "Aes128Fips197KnownAnswerTest"

# Outer simulation-time bound in clock cycles (CONTRACT.md §8).  Must
# comfortably exceed every legitimate scenario on a REPAIRED RTL: directed
# scenarios ~30..40 cycles, the corner test ~120, the randomized run
# (~41 transactions + resets) ~1000 cycles; 10000 cycles is generous.
OUTER_BUDGET_CYCLES = 10000

# Reset applied here (CONTRACT.md §6): asserted across a few rising edges,
# then released -- statistics identical to helper.reset_sync_active_low().
RESET_ASSERT_CYCLES = 3
RESET_IDLE_CYCLES = 2


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
async def aes128_tb_top(dut):
    """Single cocotb entry point -- mirrors SV UVM's ``+UVM_TESTNAME`` flow.

    ``UVM_TESTNAME`` selects which ``uvm_test`` subclass (:mod:`tests`) to
    run; ``AES128_CLK_HALF_PERIOD_NS`` and ``AES128_WATCHDOG_CYCLES`` are
    configurable as well.  The randomized test itself consumes
    ``AES128_RANDOM_SEED``/``AES128_NUM_RANDOM`` (see ``tests.py``).
    """
    clk_half_period_ns = _get_int_env(
        "AES128_CLK_HALF_PERIOD_NS", DEFAULT_CLK_HALF_PERIOD_NS)
    watchdog_cycles = _get_int_env(
        "AES128_WATCHDOG_CYCLES", DEFAULT_WATCHDOG_CYCLES)
    test_name = os.environ.get("UVM_TESTNAME", DEFAULT_TESTNAME).strip()

    dut._log.info(
        "aes128_tb_top: UVM_TESTNAME=%s clk_half_period_ns=%d "
        "watchdog_cycles=%d cocotb=%s",
        test_name, clk_half_period_ns, watchdog_cycles, cocotb.__version__,
    )

    # -- pre-clock idle state (CONTRACT.md §3/§6) ---------------------------
    # Synchronous reset: assert rst_n before the clock starts so the very
    # first rising edges already see it low; all stimulus pins deasserted.
    setimmediate = dut.rst_n.setimmediatevalue
    setimmediate(0)  # rst_n = 0: reset asserted (active low)
    dut.start.setimmediatevalue(0)
    dut.key.setimmediatevalue(0)
    dut.plaintext.setimmediatevalue(0)

    # -- master clock (CONTRACT.md §6) ----------------------------------------
    # Positive-edge clock, period = 2 * CLK_HALF_PERIOD_NS (default 10 ns).
    clock = Clock(dut.clk, 2 * clk_half_period_ns, unit="ns")
    cocotb.start_soon(clock.start())

    # -- synchronous reset pulse + settle to idle (CONTRACT.md §6) -----------
    helper = Aes128DutHelper(dut)
    await helper.reset_sync_active_low(
        assert_cycles=RESET_ASSERT_CYCLES, idle_cycles=RESET_IDLE_CYCLES)

    # -- populate ConfigDB (CONTRACT.md §4, exact keys) -----------------------
    # "Aes128DutHelper" is optional sugar; "dut" + "CLK_HALF_PERIOD_NS" are
    # the keys every component resolves.
    ConfigDB().set(None, "*", "dut", dut)
    ConfigDB().set(None, "*", "CLK_HALF_PERIOD_NS", clk_half_period_ns)
    ConfigDB().set(None, "*", "Aes128DutHelper", helper)

    # -- arm the bounded clock-cycle watchdog (CONTRACT.md §8/§11.2) ----------
    # Counts rising clock edges and raises after `watchdog_cycles` without a
    # done pulse; test_top kills it on completion (success or failure).
    watchdog_task = launch_watchdog(dut=dut, timeout_cycles=watchdog_cycles)

    # -- run the selected pyuvm test under the coarse sim-time bound ----------
    outer_budget_ns = int(OUTER_BUDGET_CYCLES * 2 * clk_half_period_ns)
    try:
        await with_timeout(
            uvm_root().run_test(test_name, keep_singletons=True),
            outer_budget_ns,
            "ns",
        )
    except SimTimeoutError:
        dut._log.error(
            "aes128_tb_top: OUTER WATCHDOG fired: run_test('%s') exceeded "
            "%d cycles (%d ns) of simulation time. The clock-cycle watchdog "
            "and the runner's OS timeout remain as backstops.",
            test_name, OUTER_BUDGET_CYCLES, outer_budget_ns,
        )
        raise
    finally:
        watchdog_task.kill()
        report_coverage(logger=print)

    dut._log.info("aes128_tb_top: test '%s' completed", test_name)