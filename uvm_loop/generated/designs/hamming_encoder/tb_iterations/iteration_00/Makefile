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
# matches the geometry the testbench computes from HammingConf.  The worker
# runs the default elaboration (DATA_WIDTH=4, SECDED=0).
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
DATA_WIDTH      ?= 4
SECDED          ?= 0
CLK_PERIOD_NS   ?= 10
WATCHDOG_MAX_CYCLES ?= 100000

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