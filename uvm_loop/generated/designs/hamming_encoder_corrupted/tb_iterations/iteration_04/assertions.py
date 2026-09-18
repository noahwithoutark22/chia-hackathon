# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Assertion checkers for Hamming Encoder UVM testbench.
"""

import cocotb
from cocotb.triggers import ValueChange, Timer
from pyuvm import ConfigDB


def parity_64bit(x):
    """Return the parity of a 64-bit integer (0 for even, 1 for odd)."""
    return bin(x).count("1") & 1


async def overall_parity_check():
    """Checker for overall parity: entire 72-bit codeword must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val) == 0, f"Overall parity check failed: codeword=0x{codeword_val:x} has odd parity"


async def hamming_parity_p1_check():
    """Checker for P1 parity: bits 1,3,5,... (1-indexed) must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    # Build mask for P1: bits 0,2,4,...,70 (0-indexed)
    mask = 0
    for i in range(0, 72, 2):
        mask |= (1 << i)
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val & mask) == 0, f"Hamming P1 parity check failed: (codeword & 0x{mask:x}) has odd parity"


async def hamming_parity_p2_check():
    """Checker for P2 parity: bits 2,3,6,7,10,11,... (1-indexed) must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    # Build mask for P2: bits 1,2,5,6,9,10,... (0-indexed)
    mask = 0
    for i in range(0, 72, 4):
        mask |= (1 << (i + 1))
        mask |= (1 << (i + 2))
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val & mask) == 0, f"Hamming P2 parity check failed: (codeword & 0x{mask:x}) has odd parity"


async def hamming_parity_p4_check():
    """Checker for P4 parity: bits 4-7,12-15,... (1-indexed) must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    # Build mask for P4: bits 3-6,11-14,... (0-indexed)
    mask = 0
    for i in range(0, 72, 8):
        for j in range(4):
            mask |= (1 << (i + 3 + j))
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val & mask) == 0, f"Hamming P4 parity check failed: (codeword & 0x{mask:x}) has odd parity"


async def hamming_parity_p8_check():
    """Checker for P8 parity: bits 8-15,24-31,... (1-indexed) must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    # Build mask for P8: bits 7-14,23-30,... (0-indexed)
    mask = 0
    for i in range(0, 72, 16):
        for j in range(8):
            mask |= (1 << (i + 7 + j))
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val & mask) == 0, f"Hamming P8 parity check failed: (codeword & 0x{mask:x}) has odd parity"


async def hamming_parity_p16_check():
    """Checker for P16 parity: bits 16-31,48-63,... (1-indexed) must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    # Build mask for P16: bits 15-30,47-62,... (0-indexed)
    mask = 0
    for i in range(0, 72, 32):
        for j in range(16):
            mask |= (1 << (i + 15 + j))
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val & mask) == 0, f"Hamming P16 parity check failed: (codeword & 0x{mask:x}) has odd parity"


async def hamming_parity_p32_check():
    """Checker for P32 parity: bits 32-63 (1-indexed) must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    # Build mask for P32: bits 31-62 (0-indexed)
    mask = 0
    for i in range(31, 63):
        mask |= (1 << i)
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val & mask) == 0, f"Hamming P32 parity check failed: (codeword & 0x{mask:x}) has odd parity"


async def hamming_parity_p64_check():
    """Checker for P64 parity: bits 64-71 (1-indexed) must have even parity."""
    helper = ConfigDB().get(None, "", "dut_helper")
    # Build mask for P64: bits 63-70 (0-indexed)
    mask = 0
    for i in range(63, 71):
        mask |= (1 << i)
    while True:
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
        codeword_val = helper.codeword.value
        assert parity_64bit(codeword_val & mask) == 0, f"Hamming P64 parity check failed: (codeword & 0x{mask:x}) has odd parity"


async def watchdog(timeout_cycles=10000):
    """Watchdog timer that fails the test if it does not finish within timeout_cycles."""
    helper = ConfigDB().get(None, "", "dut_helper")
    for _ in range(timeout_cycles):
        await ValueChange(helper.data_in)
        await Timer(1, 'ns')
    raise AssertionError(f"Watchdog timeout after {timeout_cycles} clock cycles")