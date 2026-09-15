"""cocotb top-level entry point for the ``hamming_encoder`` DUT testbench.

This module is the single ``@cocotb.test()`` coroutine cocotb invokes when
the Makefile specifies ``MODULE = test_top``.  It:

1. Resolves the elaboration parameters (``DATA_WIDTH``, ``SECDED``) and
   pacing budget (``CLK_PERIOD_NS``, ``WATCHDOG_MAX_CYCLES``) from
   environment variables with the CONTRACT.md defaults.
2. Populates pyuvm ``ConfigDB`` with the DUT handle, the canonical pin
   wrapper, the virtual clock/reset descriptor and the shared ``HammingConf``
   geometry (CONTRACT.md section 6, exact keys).
3. Starts the bounded watchdog (CONTRACT.md section 9).
4. Reads the ``UVM_TESTNAME`` environment variable (analogous to SV UVM's
   ``+UVM_TESTNAME`` plusarg) and calls
   ``await uvm_root().run_test(<test_name>, keep_singletons=True)``.
5. Signals the watchdog on completion (success or failure).

== No cocotb ``Clock`` / reset drive (CONTRACT.md sections 2-3, 9) ==

``hamming_encoder`` is *purely combinational*: its port list has exactly
``data_in`` (input) and ``code_out`` (output) and **no** ``clk`` or reset
pin.  There is therefore no ``dut.clk`` to start a cocotb ``Clock`` on and
no ``dut.tb_reset`` to toggle.  The reference clock is *virtual* -- one
reference cycle is one ``Timer`` wait implemented by
``dut_helper.wait_clock_cycles`` -- and the environment reset (``tb_reset``)
is a logical phase owned by the sequences, which only reinitializes
predictor/scoreboard/coverage state.  This module must never reference
``dut.clk`` / ``dut.tb_reset``; the always-on assertion checkers are started
by the environment's ``build_phase`` (``start_assertions()``, exactly once),
before any sequence drives the DUT.

pyuvm 3.0.0 compatibility (integration-stage decision; CONTRACT.md section 6
defines the exact ConfigDB keys and section 9 mandates sharing objects only
through them):

* **Wildcard ConfigDB retrieval.**  The bench stores and retrieves config
  under the wildcard path ``"*"``.  Stock pyuvm 3.0.0 rejects ``"*"`` in a
  ``get()`` retrieval path because its ``legal_chars`` allow-list excludes
  glob characters; :func:`_install_pyuvm_shims` widens that class-level
  allow-list only, keeping the section 6 call form intact.
* **Singleton preservation.**  pyuvm 3.0.0's ``run_test(test_name)`` defaults
  to ``keep_singletons=False``, which clears the ``ConfigDB`` singleton
  *before* ``build_phase`` -- silently discarding the keys set here.
  ``keep_singletons=True`` keeps the ConfigDB (and the factory's class
  registry) intact across the run.

The test class selected by ``UVM_TESTNAME`` is defined in ``tb/test.py`` and
must exactly match one of the class names listed in
``generation_manifest.yaml``.
"""

import os

import cocotb
from pyuvm import ConfigDB, uvm_root

# Importing tb.test registers every uvm_test subclass in pyuvm's factory
# registry, required for uvm_root().run_test("<ClassName>") to resolve the
# test by name at runtime.  (tb.-prefixed import: the generated bench is a
# 'tb' package, unlike the flat-module FIFO bench.)
import tb.test  # noqa: F401  (side effect: register test classes)

from tb.assertions import start_watchdog
from tb.dut_helper import (
    ClockReset,
    HammingConf,
    HammingDutPins,
    KEY_CLK_RST,
    KEY_CONF,
    KEY_DUT,
    KEY_DUT_PINS,
)


# ---------------------------------------------------------------------------
# Default parameters (CONTRACT.md sections 1, 4; DISC-1).
#
# NB: the RTL elaborates with DATA_WIDTH=4, SECDED=0 by default.  Local
# Makefile runs may -G-override the RTL parameters; the worker runs plain
# (no -G overrides -> RTL defaults).  Everything downstream reads the active
# geometry from the ConfigDB HammingConf, never from these defaults.
# ---------------------------------------------------------------------------
DEFAULT_DATA_WIDTH = 4
DEFAULT_SECDED = 0
DEFAULT_CLK_PERIOD_NS = 10   # one virtual reference cycle
DEFAULT_WATCHDOG_MAX_CYCLES = 100000


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
# pyuvm 3.0.0 compatibility shims (integration-stage decision)
# ---------------------------------------------------------------------------
def _install_pyuvm_shims():
    """Make the CONTRACT section 6 wildcard ConfigDB form work on pyuvm.

    Every bench component reads config with ``ConfigDB().get(None, "*",
    "<key>")`` (CONTRACT.md section 6).  pyuvm 3.0.0 rejects glob characters
    in a ``get()`` retrieval ``inst_name`` at
    ``s13_uvm_component.ConfigDB.legal_chars`` (a class-level allow-list),
    so the wildcard store/retrieve pairing is widened only by extending that
    allow-list with the ``fnmatch`` glob characters.  This is a one-time,
    process-wide, idempotent class attribute patch; the exact section 6 call
    form in every component remains byte-for-byte unchanged.
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
async def hamming_tb_top(dut):
    """Single cocotb entry point -- mirrors SV UVM's ``+UVM_TESTNAME`` flow.

    The ``UVM_TESTNAME`` environment variable selects which ``uvm_test``
    subclass to instantiate.  All other parameters (``DATA_WIDTH``,
    ``SECDED``, ``CLK_PERIOD_NS``, ``WATCHDOG_MAX_CYCLES``) are configurable
    via environment variables with CONTRACT.md defaults.
    """
    # -- resolve parameters ------------------------------------------------
    data_width = _get_int_env("DATA_WIDTH", DEFAULT_DATA_WIDTH)
    secded = _get_int_env("SECDED", DEFAULT_SECDED)
    clk_period_ns = _get_int_env("CLK_PERIOD_NS", DEFAULT_CLK_PERIOD_NS)
    watchdog_max_cycles = _get_int_env(
        "WATCHDOG_MAX_CYCLES", DEFAULT_WATCHDOG_MAX_CYCLES)

    # -- install pyuvm compatibility shims (before any ConfigDB work) ------
    _install_pyuvm_shims()

    test_name = os.environ.get("UVM_TESTNAME", "HammingTC1Test")
    dut._log.info(
        "hamming_tb_top: UVM_TESTNAME=%s  DATA_WIDTH=%d  SECDED=%d  "
        "CLK_PERIOD_NS=%d  WATCHDOG_MAX_CYCLES=%d",
        test_name, data_width, secded, clk_period_ns, watchdog_max_cycles,
    )

    # -- no cocotb Clock / reset drive (CONTRACT.md sections 2-3) ---------
    # The DUT has no clk/reset port; the reference clock is virtual and the
    # tb_reset phase is logical.  Prime data_in so the input pin carries a
    # genuine 0/1 value from time zero (code_out settles combinationally,
    # so no undriven-X window is ever sampled once sequences start driving).
    dut.data_in.setimmediatevalue(0)

    # -- populate ConfigDB (CONTRACT.md section 6, exact keys) ------------
    # These keys are read by every UVM component in build_phase / run_phase
    # through the KEY_* constants in tb/dut_helper.py.
    pins = HammingDutPins(dut)
    clkrs = ClockReset(clock_period_ns=clk_period_ns)
    conf = HammingConf.compute(data_width, secded)
    ConfigDB().set(None, "*", KEY_DUT, dut)
    ConfigDB().set(None, "*", KEY_DUT_PINS, pins)
    ConfigDB().set(None, "*", KEY_CLK_RST, clkrs)
    ConfigDB().set(None, "*", KEY_CONF, conf)

    # -- always-on assertions ----------------------------------------------
    # Started exactly once by HammingEnv.build_phase via start_assertions()
    # (ConfigDB resolves pins/clkrs/conf); the environment kills those tasks
    # in final_phase.  Nothing to wire here beyond the shared config above.

    # -- start bounded watchdog (CONTRACT.md section 9) ---------------------
    # Virtual reference cycles are the budget unit.  start_watchdog creates
    # and returns the done Event; the test body sets it on completion below.
    _wd_task, done_event = start_watchdog(
        clkrs,
        max_cycles=watchdog_max_cycles,
        description=f"hamming_encoder test '{test_name}'",
    )

    # -- run the selected UVM test -----------------------------------------
    # keep_singletons=True: pyuvm 3.0.0's default clears the ConfigDB
    # singleton before build_phase, which would discard the keys set above.
    try:
        await uvm_root().run_test(test_name, keep_singletons=True)
    finally:
        # Signal the watchdog that the test body completed so it can exit
        # quietly (CONTRACT.md section 9), on success or failure alike.
        done_event.set()

    dut._log.info("hamming_tb_top: test '%s' completed", test_name)