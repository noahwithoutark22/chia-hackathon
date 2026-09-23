# Makefile for the cocotb + pyuvm SHA-256 testbench (Verilator flow).
#
# This file implements the standard cocotb flow (SIM=verilator,
# TOPLEVEL=sha256, MODULE=test_top) for manual runs.  The integration
# worker (workers/sim/run.py) builds its own launcher Makefile under
# .chia_sim/, but this file is the persistent, human-runnable flow and the
# source of the compile-time conventions.
#
# Usage:
#   make                                     # default pyuvm test
#   make UVM_TESTNAME=Sha256AbcMessageTest   # run a specific test
#
# Every runnable test class name lives in generation_manifest.yaml;
# UVM_TESTNAME must be one of those names (test_top.py reads it).

# ---- cocotb simulation settings ------------------------------------------
SIM             = verilator
TOPLEVEL        = sha256
MODULE          = test_top

# ---- RTL source (read-only, must not be modified) ------------------------
VERILOG_SOURCES = /workspace/benchmarks/sha256_benchmark_corrupted/sha256.sv

# ---- Verilator compile flags ----------------------------------------------
# --timing is required (the RTL uses an asynchronous reset).  -Wno-fatal
# downgrades non-fatal lint warnings; the datapath-width relaxations mirror
# the reference fifo testbench.
COMPILE_ARGS    += --timing -Wno-fatal
COMPILE_ARGS    += -Wno-WIDTH -Wno-CASEINCOMPLETE -Wno-UNOPTFLAT

# ---- Build parallelism -----------------------------------------------------
COMPILE_ARGS    += -j 0

# ---- pyuvm test selection (read by test_top.py) ---------------------------
UVM_TESTNAME    ?= Sha256ResetInitializationTest
export UVM_TESTNAME

# ---- cocotb flow (must be included last) ----------------------------------
include $(shell cocotb-config --makefiles)/Makefile.sim