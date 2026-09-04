#!/usr/bin/env python3
"""Cocotb build + run configuration for the ``adder`` DUT testbench.

This is the equivalent of a cocotb ``Makefile`` but written against the
Python runner API (``cocotb.runner.get_runner``).  It:

  - compiles the *existing* DUT RTL only (``examples/adder/adder.sv``) —
    no generated SystemVerilog exists in this project,
  - builds the simulation with the ``verilator`` simulator (with timing
    enabled, since the DUT is registered/synchronous),
  - runs the top-level Python test module ``generated_tb.test_top``.

The UVM test to run is selected by the ``UVM_TESTNAME`` environment
variable (default ``AdderFullRegressionTest``), mirroring SV-UVM
``+UVM_TESTNAME``.  Additional knobs (``CLK_PERIOD_NS``,
``RESET_HOLD_CYCLES``, ``WATCHDOG_CYCLES``) are forwarded as environment
variables to the simulation.

Run (from the repository root)::

    # Build + run the full regression by default
    python generated_tb/test_runner.py

    # Pick a specific UVM test
    UVM_TESTNAME=AdderRandomTest python generated_tb/test_runner.py

    # AIO: list all available test names first
    python generated_tb/test_runner.py --list-tests
"""

from __future__ import annotations

import argparse
import os
import sys

from cocotb.runner import get_runner

# ---------------------------------------------------------------------------
# Canned values — mirror test_top.py defaults.
# ---------------------------------------------------------------------------
_TOP_MODULE = "adder"
_TOP_FILE = os.path.join("examples", "adder", "adder.sv")
_PYTHON_TEST_MODULE = "generated_tb.test_top"  # noq: .py omitted

# Environment variable knobs forwarded into the simulation.
_PASSED_ENV_VARS = ("UVM_TESTNAME", "CLK_PERIOD_NS", "RESET_HOLD_CYCLES",
                    "WATCHDOG_CYCLES")


def _default_test_env() -> list[str]:
    """Return a ``[VAR=value,...]`` list of the env knobs (only ones set)."""
    out = []
    for var in _PASSED_ENV_VARS:
        if var in os.environ:
            out.append(f"{var}={os.environ[var]}")
    return out


def _list_tests() -> None:
    """List the selectable UVM test class names by importing adder_test."""
    gen_dir = os.path.dirname(os.path.abspath(__file__))
    if gen_dir not in sys.path:
        sys.path.insert(0, gen_dir)
    import adder_test  # noqa: F401  (registers the classes)
    from pyuvm import uvm_factory
    factory = uvm_factory()
    # All names registered in the factory that end with "Test".
    names = sorted(
        n for n in factory.fd.classes if n.endswith("Test")
    )
    print("\nSelectable UVM_TESTNAME values (registered in the factory):\n")
    for name in names:
        print(f"  {name}")
    print()


def _build_and_run(clean: bool = False) -> None:
    """Build the DUT with Verilator and run the cocotb test module."""
    runner = get_runner("verilator")

    # Only the DUT RTL is compiled — there is no generated SystemVerilog.
    # ``--timing`` is required because the DUT's registered/async-reset
    # ``always @(posedge clk or negedge rst_n)`` block relies on real clock
    # events (simulation_contract: require_timing).
    runner.build(
        verilog_sources=[os.path.join(os.getcwd(), _TOP_FILE)],
        hdl_toplevel=_TOP_MODULE,
        always=True,
        build_args=[
            "--timing",
            "-j", "0",  # build parallelism per simulation contract
        ],
        timescale=("1ns", "1ps"),
        clean=clean,
    )

    runner.test(
        hdl_toplevel=_TOP_MODULE,
        test_module=_PYTHON_TEST_MODULE,
        plusargs=None,
        waves=True,
        extra_env=_default_test_env(),
        verbose=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list-tests", action="store_true",
        help="Print the selectable UVM test class names and exit.",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Force a clean rebuild (remove prior build artifacts).",
    )
    args = parser.parse_args()

    if args.list_tests:
        _list_tests()
        return 0

    print("=== Adder cocotb+pyuvm integration: build & run ===")
    print(f"  top module      : {_TOP_MODULE}")
    print(f"  top RTL file    : {_TOP_FILE}")
    print(f"  python test mod : {_PYTHON_TEST_MODULE}")
    print(f"  UVM_TESTNAME    : {os.environ.get('UVM_TESTNAME', 'AdderFullRegressionTest')}")
    _build_and_run(clean=args.clean)
    return 0


if __name__ == "__main__":
    sys.exit(main())
