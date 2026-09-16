# Makefile for cocotb + pyuvm testbench (axi_handshake DUT)
#
# Usage:
#   make                     # run default test (SmokeAfterResetTest)
#   make TEST=StallHoldTest  # run a specific test
#   make clean               # remove build artifacts
#
# The UVM_TESTNAME environment variable is set from $(TEST) and read
# by test_top.py to select the UVM test class.

# ─────────────────────────────────────────────────────────────────
#  cocotb / simulator configuration
# ─────────────────────────────────────────────────────────────────

SIM         ?= verilator
TOPLEVEL    = axi_handshake
MODULE      = test_top

# Only the existing DUT RTL is compiled — no generated SystemVerilog.
VERILOG_SOURCES = ../../../../benchmarks/axi_handshake/axi_handshake.sv

# UVM test to run (default: directed smoke test)
TEST ?= SmokeAfterResetTest

# Pass UVM_TESTNAME to the Python test module
export UVM_TESTNAME = $(TEST)

# ─────────────────────────────────────────────────────────────────
#  Verilator-specific flags
# ─────────────────────────────────────────────────────────────────

# Compile with timing support (required by simulation_contract)
COMPILE_ARGS += --timing

# UVM DPI is disabled (simulation_contract §verilator)
COMPILE_ARGS += -DUVM_NO_DPI

# Build in parallel
COMPILE_ARGS += -j 0

# ─────────────────────────────────────────────────────────────────
#  cocotb sim-level settings
# ─────────────────────────────────────────────────────────────────

# Extra plusargs (none needed — UVM_TESTNAME is an env var)
SIM_ARGS +=

# Include the tb directory in PYTHONPATH so modules resolve correctly
export PYTHONPATH := $(shell pwd):$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: clean

clean:
	rm -rf sim_build results.xml __pycache__
	rm -rf dump.vcd sim.log
