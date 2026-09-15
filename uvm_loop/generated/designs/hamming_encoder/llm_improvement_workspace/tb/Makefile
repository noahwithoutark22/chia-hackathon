# Makefile for the cocotb + pyuvm hamming_encoder testbench (Verilator flow)
#
# Usage:
#   make                                  # run default test (HammingTC1Test)
#   make UVM_TESTNAME=HammingTC8Test      # run a specific test
#   make UVM_TESTNAME=HammingTC5Test DATA_WIDTH=8 SECDED=0
#   make UVM_TESTNAME=HammingTC3Test DATA_WIDTH=4 SECDED=1
#
# DATA_WIDTH / SECDED are passed to Verilator as -G (parameter) overrides
# AND exported to the cocotb process, so the elaborated geometry always
# matches the geometry the testbench computes from HammingConf.
#
# Per-test default elaboration matrix (weakness W01/W02/W03):
#   The DUT is elaborated once per simulation.  A plain
#   `make UVM_TESTNAME=<test>` (no DATA_WIDTH/SECDED override) used to
#   elaborate the RTL default (DATA_WIDTH=4, SECDED=0) for EVERY test, so
#   TC3 (SECDED), TC5 (width 8), TC7 (width 1/11/16) and the SECDED/width-
#   gated corner sequences took the log-and-skip path and passed with 0
#   scored items (vacuous pass).  Each plan scenario is therefore now given
#   its target (DATA_WIDTH, SECDED) elaboration as the DEFAULT for that
#   test, applied ONLY when the caller passes no explicit DATA_WIDTH/SECDED
#   override (neither on the command line nor in the environment).  An
#   explicit override always wins and leaves the mapping inert, preserving
#   the legacy default elaboration (4,0) for any unrecognised test name.
#
# Verilator compile flags include --timing and -DUVM_NO_DPI per the
# verilator_compatibility hard requirements.

# ---- cocotb simulation settings ------------------------------------------
SIM             = verilator
TOPLEVEL        = hamming_encoder
MODULE          = test_top

# ---- RTL source (read-only, must not be modified) ------------------------
VERILOG_SOURCES = /workspace/benchmarks/hamming_encoder/hamming_encoder.sv

# ---- DUT elaboration parameters (-G overrides, applied to the RTL) -------
COMPILE_ARGS    += -GDATA_WIDTH=$(DATA_WIDTH) -GSECDED=$(SECDED)

# ---- Verilator compile / sim flags ---------------------------------------
COMPILE_ARGS    += --timing -DUVM_NO_DPI
COMPILE_ARGS    += -Wno-WIDTH -Wno-CASEINCOMPLETE -Wno-UNOPTFLAT

# ---- Parallelism (verilator_compatibility: build_parallelism) ------------
COMPILE_ARGS    += -j 0

# ---- cocotb test parameters (overridable on the make command line) -------
# NB: the DUT has no clk/reset port; CLK_PERIOD_NS is the virtual reference
# cycle duration, not a DUT clock.
UVM_TESTNAME    ?= HammingTC1Test
CLK_PERIOD_NS   ?= 10
WATCHDOG_MAX_CYCLES ?= 100000

# ---- Per-test default elaboration matrix --------------------------------
# One simulation = one elaboration, so each test defaults to the plan
# (DATA_WIDTH, SECDED) configuration that makes its scenario applicable
# (mirrors test.py elaboration_applies and the sequence guards):
#   TC1/TC2 -> (4,0)   TC3/TC4/TC6/TC8 -> (4,1)   TC5 -> (8,0)
#   TC7 -> (1,0)       HammingCornerTest -> (16,0)
#   HammingRandomizedTest -> (8,1)
# The defaults are applied ONLY when DATA_WIDTH/SECDED are undefined in the
# make invocation (not provided on the command line and not exported in the
# environment); any explicit override is honoured unchanged and makes the
# mapping inert.  Unrecognised test names keep the legacy default (4,0).
_TEST_DEFAULT_ELABORATIONS := \
  HammingTC1Test:4:0 \
  HammingTC2Test:4:0 \
  HammingTC3Test:4:1 \
  HammingTC4Test:4:1 \
  HammingTC5Test:8:0 \
  HammingTC6Test:4:1 \
  HammingTC7Test:1:0 \
  HammingTC8Test:4:1 \
  HammingCornerTest:16:0 \
  HammingRandomizedTest:8:1

ifeq ($(origin DATA_WIDTH),undefined)
_test_matrix_cfg := $(filter $(UVM_TESTNAME):%,$(_TEST_DEFAULT_ELABORATIONS))
DATA_WIDTH := $(if $(_test_matrix_cfg),$(word 2,$(subst :, ,$(_test_matrix_cfg))),4)
endif

ifeq ($(origin SECDED),undefined)
_test_matrix_cfg := $(filter $(UVM_TESTNAME):%,$(_TEST_DEFAULT_ELABORATIONS))
SECDED := $(if $(_test_matrix_cfg),$(word 3,$(subst :, ,$(_test_matrix_cfg))),0)
endif

export UVM_TESTNAME
export DATA_WIDTH
export SECDED
export CLK_PERIOD_NS
export WATCHDOG_MAX_CYCLES

# ---- PYTHONPATH for the generated 'tb' package ---------------------------
# The generated bench imports its modules as a package (tb.env, tb.test,
# tb.sequences, ...).  /workspace on the path additionally resolves the
# benchmarks.hamming_encoder.ref_model fallback import used by several TB
# modules.  The trailing :$(PYTHONPATH) preserves worker-set entries.
PYTHONPATH := /workspace:$(abspath ..):$(abspath .):$(PYTHONPATH)
export PYTHONPATH

# ---- Wave dumping (optional; uncomment for VCD) -------------------------
# SIM_ARGS       += --trace
# COMPILE_ARGS   += --trace

# ---- cocotb flow (must be included last) --------------------------------
include $(shell cocotb-config --makefiles)/Makefile.sim