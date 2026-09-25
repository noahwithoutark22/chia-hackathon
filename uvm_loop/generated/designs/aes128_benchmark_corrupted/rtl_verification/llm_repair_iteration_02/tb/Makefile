# Makefile for the cocotb + pyuvm AES-128 testbench (Verilator flow).
#
# Standard cocotb flow (SIM=verilator, TOPLEVEL=aes128, MODULE=test_top)
# for manual runs.  The integration runner builds its own launcher Makefile
# under .chia_sim/, but this file is the persistent, human-runnable flow
# and the source of the compile-time conventions.
#
# Usage:
#   make                                        # default pyuvm test
#   make UVM_TESTNAME=Aes128CornerTest          # run a specific test
#   make UVM_TESTNAME=Aes128RandomizedTest AES128_RANDOM_SEED=7
#
# Every runnable test class name lives in generation_manifest.yaml;
# UVM_TESTNAME must be one of those names (test_top.py reads it).

# ---- cocotb simulation settings ------------------------------------------
SIM             = verilator
TOPLEVEL        = aes128
MODULE          = test_top

# ---- RTL source (read-only, must not be modified) ------------------------
VERILOG_SOURCES = /workspace/benchmarks/aes128_benchmark_corrupted/aes128.sv

# ---- Verilator compile flags ----------------------------------------------
# --timing is required (the cocotb flow needs timed simulation even though
# the DUT reset is synchronous).  -Wno-fatal downgrades non-fatal lint
# warnings; the datapath-width relaxations mirror the reference fifo flow.
COMPILE_ARGS    += --timing -Wno-fatal
COMPILE_ARGS    += -Wno-WIDTH -Wno-CASEINCOMPLETE -Wno-UNOPTFLAT

# ---- Build parallelism -----------------------------------------------------
COMPILE_ARGS    += -j 0

# ---- pyuvm test selection (read by test_top.py) ---------------------------
UVM_TESTNAME    ?= Aes128Fips197KnownAnswerTest
export UVM_TESTNAME

# ---- cocotb flow (must be included last) ----------------------------------
include $(shell cocotb-config --makefiles)/Makefile.sim