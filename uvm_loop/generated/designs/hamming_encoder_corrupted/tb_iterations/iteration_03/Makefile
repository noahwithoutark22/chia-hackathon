# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

# Makefile for cocotb testbench

SIM := verilator
TOPLEVEL := hamming_encoder
MODULE := test_top

# Path to the DUT RTL file (relative to this directory)
VERILOG_SOURCES := ../../../benchmarks/hamming_encoder_benchmark_corrupted/hamming_encoder.sv

# Include cocotb's Makefile to get the default rules
include $(shell cocotb-config --makefiles)/Makefile.sim