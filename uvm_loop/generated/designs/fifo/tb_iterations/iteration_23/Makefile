# Makefile for the cocotb + pyuvm FIFO testbench (Verilator flow)
#
# Usage:
#   make                          # run default test (FifoTC001Test)
#   make UVM_TESTNAME=FifoTC003Test  # run a specific test
#   make UVM_TESTNAME=FifoRandomizedTest DATA_WIDTH=8 DEPTH=4
#
# All parameters are passed as environment variables to the cocotb test.
# Verilator compile flags include --timing and -DUVM_NO_DPI per the
# verilator_compatibility hard requirements.

# ---- cocotb simulation settings ------------------------------------------
SIM             = verilator
TOPLEVEL        = fifo
MODULE          = test_top

# ---- RTL source (read-only, must not be modified) ------------------------
VERILOG_SOURCES = /workspace/benchmarks/fifo/fifo.sv

# ---- Verilator compile / sim flags ---------------------------------------
COMPILE_ARGS    += --timing -DUVM_NO_DPI
COMPILE_ARGS    += -Wno-WIDTH -Wno-CASEINCOMPLETE -Wno-UNOPTFLAT

# ---- Parallelism (verilator_compatibility: build_parallelism) ------------
COMPILE_ARGS    += -j 0

# ---- cocotb test parameters (overridable on the make command line) -------
UVM_TESTNAME    ?= FifoTC001Test
DATA_WIDTH      ?= 8
DEPTH           ?= 4
CLK_HALF_PERIOD_NS ?= 5
WATCHDOG_MAX_CYCLES ?= 2000

export UVM_TESTNAME
export DATA_WIDTH
export DEPTH
export CLK_HALF_PERIOD_NS
export WATCHDOG_MAX_CYCLES

# ---- Wave dumping (optional; uncomment for VCD) -------------------------
# SIM_ARGS       += --trace
# COMPILE_ARGS   += --trace

# ---- cocotb flow (must be included last) --------------------------------
include $(shell cocotb-config --makefiles)/Makefile.sim
