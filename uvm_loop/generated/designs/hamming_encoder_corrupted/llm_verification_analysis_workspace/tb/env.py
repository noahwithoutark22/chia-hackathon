# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Environment for Hamming Encoder UVM testbench.
"""

import cocotb
from pyuvm import uvm_env
from agent import HammingEncoderAgent
from scoreboard import HammingEncoderScoreboard
from coverage import HammingEncoderCoverage
from assertions import (
    overall_parity_check,
    hamming_parity_p1_check,
    hamming_parity_p2_check,
    hamming_parity_p4_check,
    hamming_parity_p8_check,
    hamming_parity_p16_check,
    hamming_parity_p32_check,
    hamming_parity_p64_check,
    watchdog
)


class HammingEncoderEnv(uvm_env):
    """Environment for Hamming encoder.

    Contains agent, scoreboard, coverage, and starts assertion checkers.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.agent = None
        self.scoreboard = None
        self.coverage = None

    def build_phase(self):
        super().build_phase()
        # Create components
        self.agent = HammingEncoderAgent("agent", self)
        self.scoreboard = HammingEncoderScoreboard("scoreboard", self)
        self.coverage = HammingEncoderCoverage("coverage", self)

    def connect_phase(self):
        super().connect_phase()
        # Connect agent's monitor to scoreboard and coverage
        self.agent.monitor.ap.connect(self.scoreboard.analysis_export)
        self.agent.monitor.ap.connect(self.coverage.analysis_export)

    def start_phase(self):
        super().start_phase()
        # Start assertion checker coroutines
        cocotb.start_soon(overall_parity_check())
        cocotb.start_soon(hamming_parity_p1_check())
        cocotb.start_soon(hamming_parity_p2_check())
        cocotb.start_soon(hamming_parity_p4_check())
        cocotb.start_soon(hamming_parity_p8_check())
        cocotb.start_soon(hamming_parity_p16_check())
        cocotb.start_soon(hamming_parity_p32_check())
        cocotb.start_soon(hamming_parity_p64_check())
        # Start watchdog
        cocotb.start_soon(watchdog(timeout_cycles=10000))