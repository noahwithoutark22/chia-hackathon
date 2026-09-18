# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Test classes for Hamming Encoder UVM testbench.
"""

import cocotb
from pyuvm import uvm_test
from env import HammingEncoderEnv
from sequences import (
    SeqAllZerosInput,
    SeqAllOnesInput,
    SeqAlternating1010,
    SeqAlternating0101,
    SeqSingleBitSetLSB,
    SeqSingleBitSetMSB,
    SeqMaximumInputValue,
    SeqMinimumInputValue,
    SeqPowerOfTwoDataPattern,
    SeqRandomized
)


class HammingEncoderBaseTest(uvm_test):
    """Base test class for Hamming encoder tests."""

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        super().build_phase()
        self.env = HammingEncoderEnv("env", self)

    def end_of_elaboration_phase(self):
        super().end_of_elaboration_phase()

    def start_of_simulation_phase(self):
        super().start_of_simulation_phase()
        # This is where we would typically raise objections, but we'll do it in run_phase.

    async def run_phase(self):
        # Raise objection to keep the test running until we drop it.
        self.raise_objection()
        # The actual test logic is in the subclasses.
        await self.custom_run_phase()
        # Drop objection when done.
        self.drop_objection()

    async def custom_run_phase(self):
        """To be overridden by subclasses."""
        raise NotImplementedError


class TestAllZerosInput(HammingEncoderBaseTest):
    """Test for scenario all_zeros_input (ID 1)."""

    async def custom_run_phase(self):
        seq = SeqAllZerosInput("seq_all_zeros")
        await seq.start(self.env.agent.sequencer)


class TestAllOnesInput(HammingEncoderBaseTest):
    """Test for scenario all_ones_input (ID 2)."""

    async def custom_run_phase(self):
        seq = SeqAllOnesInput("seq_all_ones")
        await seq.start(self.env.agent.sequencer)


class TestAlternating1010(HammingEncoderBaseTest):
    """Test for scenario alternating_1010 (ID 3)."""

    async def custom_run_phase(self):
        seq = SeqAlternating1010("seq_alt_1010")
        await seq.start(self.env.agent.sequencer)


class TestAlternating0101(HammingEncoderBaseTest):
    """Test for scenario alternating_0101 (ID 4)."""

    async def custom_run_phase(self):
        seq = SeqAlternating0101("seq_alt_0101")
        await seq.start(self.env.agent.sequencer)


class TestSingleBitSetLSB(HammingEncoderBaseTest):
    """Test for scenario single_bit_set_lsb (ID 5)."""

    async def custom_run_phase(self):
        seq = SeqSingleBitSetLSB("seq_lsb_set")
        await seq.start(self.env.agent.sequencer)


class TestSingleBitSetMSB(HammingEncoderBaseTest):
    """Test for scenario single_bit_set_msb (ID 6)."""

    async def custom_run_phase(self):
        seq = SeqSingleBitSetMSB("seq_msb_set")
        await seq.start(self.env.agent.sequencer)


class TestMaximumInputValue(HammingEncoderBaseTest):
    """Corner case: maximum input value."""

    async def custom_run_phase(self):
        seq = SeqMaximumInputValue("seq_max_input")
        await seq.start(self.env.agent.sequencer)


class TestMinimumInputValue(HammingEncoderBaseTest):
    """Corner case: minimum input value."""

    async def custom_run_phase(self):
        seq = SeqMinimumInputValue("seq_min_input")
        await seq.start(self.env.agent.sequencer)


class TestPowerOfTwoDataPattern(HammingEncoderBaseTest):
    """Corner case: power-of-two data pattern."""

    async def custom_run_phase(self):
        seq = SeqPowerOfTwoDataPattern("seq_power_of_two")
        await seq.start(self.env.agent.sequencer)


class TestRandomized(HammingEncoderBaseTest):
    """Randomized test with random delays."""

    async def custom_run_phase(self):
        seq = SeqRandomized("seq_randomized", count=100)
        await seq.start(self.env.agent.sequencer)