# Makefile for the cocotb + pyuvm I2C-master testbench (Verilator flow).
#
# This file implements the standard cocotb flow (SIM=verilator,
# TOPLEVEL=i2c_master, MODULE=test_top) for manual runs.  The integration
# worker (workers/sim/run.py) builds its own launcher Makefile under
# .chia_sim/, but this file is the persistent, human-runnable flow and the
# source of the compile-time conventions.
#
# Usage:
#   make                                          # default pyuvm test
#   make UVM_TESTNAME=WriteBasicTest              # run a specific test
#
# Every runnable test class name lives in generation_manifest.yaml;
# UVM_TESTNAME must be one of those names (test_top.py reads it).
#
# The DUT RTL is read-only (must not be modified); this testbench is pure
# Python (cocotb 2.1.0 + pyuvm 5.0.0) and compiles nothing but the RTL.

# ---- cocotb simulation settings ------------------------------------------
SIM             = verilator
TOPLEVEL        = i2c_master
MODULE          = test_top

# ---- RTL source (read-only, must not be modified) ------------------------
VERILOG_SOURCES = /workspace/benchmarks/i2c_benchmark_corrupted/i2c_master.sv

# ---- Verilator compile flags ----------------------------------------------
# --timing is required (the RTL uses clocked always_ff blocks).  -Wno-fatal
# downgrades non-fatal lint warnings; the datapath-width relaxations mirror
# the sibling sha256 reference testbench.
COMPILE_ARGS    += --timing -Wno-fatal
COMPILE_ARGS    += -Wno-WIDTH -Wno-CASEINCOMPLETE -Wno-UNOPTFLAT

# ---- Build parallelism -----------------------------------------------------
COMPILE_ARGS    += -j 0

# ---- pyuvm test selection (read by test_top.py) ---------------------------
UVM_TESTNAME    ?= ResetIdleCheckTest
export UVM_TESTNAME

# ---- cocotb flow (must be included last) ----------------------------------
include $(shell cocotb-config --makefiles)/Makefile.sim