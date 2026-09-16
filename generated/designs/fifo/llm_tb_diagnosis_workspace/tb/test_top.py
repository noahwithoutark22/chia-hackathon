"""cocotb top-level entry point for the ``fifo`` DUT testbench.

This module is the single ``@cocotb.test()`` coroutine that cocotb
invokes when the Makefile specifies ``MODULE = test_top``.  It:

1. Starts the master clock (``clk``, posedge, period = ``CLK_HALF_PERIOD_NS * 2``).
2. Applies the asynchronous active-low reset (``rst_n``) for a bounded
   number of cycles to bring the DUT into a known state.
3. Populates pyuvm ``ConfigDB`` with the DUT handle and elaborated
   parameters (CONTRACT.md §4, §9.1).
4. Starts the always-on assertion checkers (CONTRACT.md §12.2).
5. Starts the bounded watchdog (CONTRACT.md §12.3).
6. Reads the ``UVM_TESTNAME`` environment variable (analogous to SV UVM's
   ``+UVM_TESTNAME`` plusarg) and calls
   ``await uvm_root().run_test(<test_class>, keep_singletons=True)``.
7. Signals the watchdog on completion (success or failure).

pyuvm 3.0.0 compatibility (integration-stage decision, CONTRACT.md §10.4):

* **Wildcard ConfigDB retrieval.**  The whole testbench stores and retrieves
  config under the wildcard path ``"*"`` (CONTRACT.md §9.1).  Stock pyuvm
  3.0.0 rejects ``"*"`` in a ``get()`` retrieval path because its
  ``legal_chars`` allow-list excludes glob characters.  :func:`_install_pyuvm_shims`
  widens that class-level allow-list only, keeping the §9.1 call form intact.
* **Singleton preservation.**  pyuvm 3.0.0's ``run_test(test_name)`` defaults to
  ``keep_singletons=False``, which clears the ``ConfigDB`` singleton *before*
  ``build_phase`` — silently discarding the config keys set here.
  ``keep_singletons=True`` keeps the ConfigDB (and the factory's class
  registry) intact across the run.

The test class selected by ``UVM_TESTNAME`` is defined in ``test.py`` and
must exactly match one of the class names listed in
``generation_manifest.yaml``.
"""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Event
from pyuvm import ConfigDB, uvm_root

# Importing 'test' registers every uvm_test subclass in pyuvm's object
# registry, which is required for uvm_root().run_test("<ClassName>") to
# resolve the test by name at runtime.
import test  # noqa: F401  (side effect: register test classes)

from assertions import start_assertions, start_watchdog
from dut_helper import FifoDutHelper


# ---------------------------------------------------------------------------
# Default parameters (CONTRACT.md §1, §4)
# ---------------------------------------------------------------------------
DEFAULT_DATA_WIDTH = 8
DEFAULT_DEPTH = 4
DEFAULT_CLK_HALF_PERIOD_NS = 5  # 10 ns period → 100 MHz
DEFAULT_WATCHDOG_MAX_CYCLES = 2000


# ---------------------------------------------------------------------------
# Helper: resolve parameters from environment / defaults
# ---------------------------------------------------------------------------
def _get_int_env(name, default):
    """Read an integer from an environment variable, falling back to *default*."""
    raw = os.environ.get(name)
    if raw is not None:
        try:
            return int(raw)
        except ValueError:
            pass
    return default


# ---------------------------------------------------------------------------
# pyuvm 3.0.0 compatibility shims (CONTRACT.md §10.4)
# ---------------------------------------------------------------------------
def _install_pyuvm_shims():
    """Make the CONTRACT §9.1 wildcard ConfigDB form work on stock pyuvm.

    Every testbench component reads config with ``ConfigDB().get(None, "*",
    "<key>")`` (CONTRACT.md §4, §9.1).  pyuvm 3.0.0 rejects glob characters
    in a ``get()`` retrieval ``inst_name`` at
    ``s13_uvm_component.ConfigDB.legal_chars`` (a class-level allow-list),
    so the wildcard store/retrieve pairing is widened only by extending that
    allow-list with the ``fnmatch`` glob characters.  This is a one-time,
    process-wide, idempotent class attribute patch; the Legal call form in
    every component remains byte-for-byte the §9.1 form.
    """
    from pyuvm import ConfigDB as _ClassConfigDB

    glob_chars = set("*?[]!")
    missing = glob_chars - _ClassConfigDB.legal_chars
    if missing:
        _ClassConfigDB.legal_chars = _ClassConfigDB.legal_chars | missing


# ---------------------------------------------------------------------------
# Main cocotb test coroutine
# ---------------------------------------------------------------------------
@cocotb.test()
async def fifo_tb_top(dut):
    """Single cocotb entry point — mirrors SV UVM's ``+UVM_TESTNAME`` flow.

    The ``UVM_TESTNAME`` environment variable selects which
    :class:`uvm_test` subclass to instantiate.  All other parameters
    (``DATA_WIDTH``, ``DEPTH``, ``CLK_HALF_PERIOD_NS``,
    ``WATCHDOG_MAX_CYCLES``) are configurable via environment variables
    with sensible defaults.
    """
    # -- resolve parameters ------------------------------------------------
    data_width = _get_int_env("DATA_WIDTH", DEFAULT_DATA_WIDTH)
    depth = _get_int_env("DEPTH", DEFAULT_DEPTH)
    clk_half_period_ns = _get_int_env("CLK_HALF_PERIOD_NS", DEFAULT_CLK_HALF_PERIOD_NS)
    watchdog_max_cycles = _get_int_env("WATCHDOG_MAX_CYCLES", DEFAULT_WATCHDOG_MAX_CYCLES)

    # -- install pyuvm compatibility shims (before any ConfigDB work) ------
    _install_pyuvm_shims()

    test_name = os.environ.get("UVM_TESTNAME", "FifoTC001Test")
    dut._log.info(
        "fifo_tb_top: UVM_TESTNAME=%s  DATA_WIDTH=%d  DEPTH=%d  "
        "CLK_HALF_PERIOD_NS=%d  WATCHDOG_MAX_CYCLES=%d",
        test_name, data_width, depth, clk_half_period_ns, watchdog_max_cycles,
    )

    # -- start clock -------------------------------------------------------
    clock = Clock(dut.clk, clk_half_period_ns * 2, units="ns")
    cocotb.start_soon(clock.start())

    # -- apply reset (CONTRACT.md §6: active-low, asynchronous) -----------
    dut.rst_n.setimmediatevalue(0)
    dut.wr_en.setimmediatevalue(0)
    dut.rd_en.setimmediatevalue(0)
    dut.din.setimmediatevalue(0)
    await ClockCycles(dut.clk, 3)
    dut.rst_n.setimmediatevalue(1)
    await ClockCycles(dut.clk, 2)

    # -- populate ConfigDB (CONTRACT.md §4, §9.1) -------------------------
    # These keys are read by every UVM component in build_phase / run_phase.
    ConfigDB().set(None, "*", "dut", dut)
    ConfigDB().set(None, "*", "DATA_WIDTH", data_width)
    ConfigDB().set(None, "*", "DEPTH", depth)
    ConfigDB().set(None, "*", "CLK_HALF_PERIOD_NS", clk_half_period_ns)

    # Optionally share a FifoDutHelper (CONTRACT.md §4).
    helper = FifoDutHelper(dut, data_width)
    ConfigDB().set(None, "*", "FifoDutHelper", helper)

    # -- start always-on assertions (CONTRACT.md §12.2) --------------------
    assertions_inst = start_assertions(dut, depth, data_width)

    # -- start bounded watchdog (CONTRACT.md §12.3) ------------------------
    done_event = Event(name="test_done")
    _wd_task, _wd_done = start_watchdog(
        dut,
        max_cycles=watchdog_max_cycles,
        done=done_event,
        description=f"fifo test '{test_name}'",
    )

    # -- run the selected UVM test -----------------------------------------
    # keep_singletons=True: pyuvm 3.0.0's default clears the ConfigDB
    # singleton before build_phase, which would discard the keys set above.
    # (See module docstring, "pyuvm 3.0.0 compatibility".)
    try:
        await uvm_root().run_test(test_name, keep_singletons=True)
    finally:
        # Signal the watchdog that the test body has completed so it can
        # exit early (CONTRACT.md §12.3).
        done_event.set()

    dut._log.info("fifo_tb_top: test '%s' completed", test_name)
