# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Sequences for Hamming Encoder UVM testbench.
"""

import sys
import random
import cocotb
from cocotb.triggers import Timer
from pyuvm import uvm_sequence, ConfigDB
from hamming_encoder_transaction import HammingEncoderTransaction

# Add the path to the reference model for the corrupted design.
sys.path.append("/workspace/benchmarks/hamming_encoder_benchmark_corrupted")
from hamming_reference_model import encode


class HammingEncoderBaseSequence(uvm_sequence):
    """Base sequence providing common utilities."""

    async def get_dut_helper(self):
        """Retrieve the DUT helper from ConfigDB."""
        # Sequences aren't uvm_components (no cdb_get), so use ConfigDB
        # directly. The key is defined in the contract: `dut_helper`
        dut_helper = ConfigDB().get(None, "", "dut_helper")
        if dut_helper is None:
            raise RuntimeError("Failed to get dut_helper from ConfigDB")
        return dut_helper

    def compute_expected_codeword(self, data_in: int) -> int:
        """Compute the expected codeword using the reference model."""
        return encode(data_in)

    def check_codeword(self, dut_helper, data_in: int, label: str = "") -> bool:
        """Directly compare the DUT's current codeword output against the
        reference model, reading the signal in-line (no monitor/scoreboard
        analysis-port hop). This is deliberately synchronous with the drive
        above so there is no race against an async subscriber that may not
        get scheduled before the test's objection drops.

        Returns:
            True if comparison succeeded (values match or mismatch logged),
            False if codeword contains unresolvable bits (x/z).
        """
        expected = self.compute_expected_codeword(data_in)
        prefix = f"{label}: " if label else ""
        try:
            actual = dut_helper.codeword.value.integer
        except ValueError:
            self.logger.warning(f"{prefix}codeword contains unresolvable bits (x or z)")
            return False

        if actual != expected:
            self.logger.error(
                f"{prefix}Expected codeword 0x{expected:018X}, got 0x{actual:018X}"
            )
            return False

        return True


class HammingEncoderDirectedSequence(HammingEncoderBaseSequence):
    """Base class for directed sequences with a scenario ID."""
    # Subclasses must override this with the exact scenario ID from the plan.
    SCENARIO_ID = None

    async def body(self):
        # This method should be overridden by subclasses to implement the scenario.
        raise NotImplementedError


# Directed scenarios from the plan.

class SeqAllZerosInput(HammingEncoderDirectedSequence):
    """Test with all zero input data."""
    SCENARIO_ID = "1"

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0x0000000000000000

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle (interpreted as 1 delta cycle)
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, f"Scenario {self.SCENARIO_ID}")


class SeqAllOnesInput(HammingEncoderDirectedSequence):
    """Test with all ones input data."""
    SCENARIO_ID = "2"

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0xFFFFFFFFFFFFFFFF

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, f"Scenario {self.SCENARIO_ID}")


class SeqAlternating1010(HammingEncoderDirectedSequence):
    """Test with alternating 1010 pattern (LSB first)."""
    SCENARIO_ID = "3"

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0xAAAAAAAAAAAAAAAA

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, f"Scenario {self.SCENARIO_ID}")


class SeqAlternating0101(HammingEncoderDirectedSequence):
    """Test with alternating 0101 pattern (LSB first)."""
    SCENARIO_ID = "4"

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0x5555555555555555

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, f"Scenario {self.SCENARIO_ID}")


class SeqSingleBitSetLSB(HammingEncoderDirectedSequence):
    """Test with only LSB set."""
    SCENARIO_ID = "5"

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0x0000000000000001

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, f"Scenario {self.SCENARIO_ID}")


class SeqSingleBitSetMSB(HammingEncoderDirectedSequence):
    """Test with only MSB set."""
    SCENARIO_ID = "6"

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0x8000000000000000

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, f"Scenario {self.SCENARIO_ID}")


# Corner-case sequences (no SCENARIO_ID required).

class SeqMaximumInputValue(HammingEncoderBaseSequence):
    """Corner case: maximum input value (all ones)."""

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0xFFFFFFFFFFFFFFFF

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, "Maximum input value")


class SeqMinimumInputValue(HammingEncoderBaseSequence):
    """Corner case: minimum input value (all zeros)."""

    async def body(self):
        dut_helper = await self.get_dut_helper()
        data_in = 0x0000000000000000

        # Apply inputs
        txn = HammingEncoderTransaction("txn")
        txn.data_in = data_in
        await self.start_item(txn)
        await self.finish_item(txn)

        # Wait for 1 cycle
        await Timer(1, 'ns')

        self.check_codeword(dut_helper, data_in, "Minimum input value")


class SeqPowerOfTwoDataPattern(HammingEncoderBaseSequence):
    """Corner case: power-of-two data pattern (single bit set at each power-of-two position)."""

    async def body(self):
        dut_helper = await self.get_dut_helper()
        # Test each power-of-two position from 0 to 63.
        for bit_pos in range(64):
            data_in = 1 << bit_pos

            # Apply inputs
            txn = HammingEncoderTransaction("txn")
            txn.data_in = data_in
            await self.start_item(txn)
            await self.finish_item(txn)

            # Wait for 1 cycle (interpreted as 1 delta cycle)
            await Timer(1, 'ns')

            self.check_codeword(
                dut_helper, data_in, f"Power-of-two bit {bit_pos}"
            )


# Randomized sequence.

class SeqRandomized(HammingEncoderBaseSequence):
    """Randomized sequence with random delays between stimulus changes."""

    def __init__(self, name="SeqRandomized", count=100):
        super().__init__(name)
        self.count = count  # Number of random transactions to generate

    async def body(self):
        dut_helper = await self.get_dut_helper()
        for i in range(self.count):
            # Generate random 64-bit data_in
            data_in = random.getrandbits(64)

            # Apply inputs
            txn = HammingEncoderTransaction("txn")
            txn.data_in = data_in
            await self.start_item(txn)
            await self.finish_item(txn)

            # Apply random delay between 0 and 10 nanoseconds
            # Wait for a random number of nanoseconds (0 to 4)
            delay_cycles = random.randint(0, 4)
            for _ in range(delay_cycles):
                await Timer(1, 'ns')
            # Always wait at least 1ns before checking so the DUT's
            # combinational output has settled from this data_in value.
            if delay_cycles == 0:
                await Timer(1, 'ns')

            self.check_codeword(dut_helper, data_in, f"Randomized iteration {i}")
