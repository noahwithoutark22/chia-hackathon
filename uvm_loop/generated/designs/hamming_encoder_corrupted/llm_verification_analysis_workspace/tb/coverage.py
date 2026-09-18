# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Coverage component for Hamming Encoder UVM testbench.
"""

import cocotb
from cocotb_coverage.coverage import CoverPoint, CoverCross
from pyuvm import uvm_subscriber
from hamming_encoder_transaction import HammingEncoderTransaction


def parity_64bit(x):
    """Return the parity of a 64-bit integer (0 for even, 1 for odd)."""
    return bin(x).count("1") & 1


# Precompute masks for Hamming parity bits (72-bit codeword) at module level
# Bit indexing: bit0 is LSB, bit71 is MSB.
MASK_OVERALL = 0xFFFFFFFFFFFFFFFFFFFF  # 72 bits all set
MASK_P1 = 0
MASK_P2 = 0
MASK_P4 = 0
MASK_P8 = 0
MASK_P16 = 0
MASK_P32 = 0
MASK_P64 = 0

# P1: bits 0,2,4,...,70 (even indices, 0-indexed)
for i in range(0, 72, 2):
    MASK_P1 |= (1 << i)

# P2: bits 1,2,5,6,9,10,... (pattern: two on, two off starting at bit1)
for i in range(0, 72, 4):
    MASK_P2 |= (1 << (i + 1))
    MASK_P2 |= (1 << (i + 2))

# P4: bits 3-6, 11-14, ... (four on, four off starting at bit3)
for i in range(0, 72, 8):
    for j in range(4):
        MASK_P4 |= (1 << (i + 3 + j))

# P8: bits 7-14, 23-30, ... (eight on, eight off starting at bit7)
for i in range(0, 72, 16):
    for j in range(8):
        MASK_P8 |= (1 << (i + 7 + j))

# P16: bits 15-30, 47-62, ... (sixteen on, sixteen off starting at bit15)
for i in range(0, 72, 32):
    for j in range(16):
        MASK_P16 |= (1 << (i + 15 + j))

# P32: bits 31-62 (thirty-two on, thirty-two off starting at bit31)
for i in range(32, 64):
    MASK_P32 |= (1 << i)
# Note: we only have 72 bits, so bits 63-71 are not in P32. P32 covers bits 32-63 (1-indexed) -> bits 31-62 (0-indexed).

# P64: bits 63-70 (0-indexed) -> positions 64-71 (1-indexed)
for i in range(63, 71):
    MASK_P64 |= (1 << i)


class HammingEncoderCoverage(uvm_subscriber):
    """Coverage component for Hamming encoder.

    Subscribes to the monitor's analysis port and collects coverage
    on data_in and codeword.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def build_phase(self):
        super().build_phase()
        # No analysis port needed because we are a subscriber.

    def write(self, transaction):
        """Called by the monitor's analysis port for each transaction."""
        self.sample_coverage(transaction.data_in, transaction.codeword)

    def sample_coverage(self, data_in, codeword):
        """Sample all cover points."""
        self.cover_data_in(data_in, codeword)
        self.cover_overall_parity(data_in, codeword)
        self.cover_p1_parity(data_in, codeword)
        self.cover_p2_parity(data_in, codeword)
        self.cover_p4_parity(data_in, codeword)
        self.cover_p8_parity(data_in, codeword)
        self.cover_p16_parity(data_in, codeword)
        self.cover_p32_parity(data_in, codeword)
        self.cover_p64_parity(data_in, codeword)

    @CoverPoint("top.data_in_coverage", xf=lambda data_in, codeword: data_in,
                bins=[
                    0,
                    0xFFFFFFFFFFFFFFFF,
                    0xAAAAAAAAAAAAAAAA,
                    0x5555555555555555,
                    1,
                    0x8000000000000000,
                ],
                bins_labels=[
                    "input_zero",
                    "input_ones",
                    "input_alt_1010",
                    "input_alt_0101",
                    "input_lsb_set",
                    "input_msb_set",
                ])
    def cover_data_in(self, data_in, codeword):
        pass

    @CoverPoint("top.overall_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_OVERALL),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_overall_parity(self, data_in, codeword):
        pass

    @CoverPoint("top.p1_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_P1),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_p1_parity(self, data_in, codeword):
        pass

    @CoverPoint("top.p2_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_P2),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_p2_parity(self, data_in, codeword):
        pass

    @CoverPoint("top.p4_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_P4),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_p4_parity(self, data_in, codeword):
        pass

    @CoverPoint("top.p8_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_P8),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_p8_parity(self, data_in, codeword):
        pass

    @CoverPoint("top.p16_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_P16),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_p16_parity(self, data_in, codeword):
        pass

    @CoverPoint("top.p32_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_P32),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_p32_parity(self, data_in, codeword):
        pass

    @CoverPoint("top.p64_parity", xf=lambda data_in, codeword: parity_64bit(codeword & MASK_P64),
                bins=[0, 1],
                bins_labels=["even", "odd"])
    def cover_p64_parity(self, data_in, codeword):
        pass

    @CoverCross("top.input_vs_parity", items=[
        "top.data_in_coverage",
        "top.overall_parity"
    ])
    def cover_input_vs_parity(self, data_in, codeword):
        pass