# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Helper class for accessing Hamming Encoder DUT pins.

This provides a clean interface to get and set DUT pin values.
"""

class HammingEncoderDUTHelper:
    """Helper for accessing Hamming Encoder DUT pins.

    Args:
        dut: The cocotb dut handle for the hamming_encoder module.
    """

    def __init__(self, dut):
        self._dut = dut

    @property
    def data_in(self):
        """Get or set the data_in input port (64 bits)."""
        return self._dut.data_in

    @data_in.setter
    def data_in(self, value):
        self._dut.data_in.value = value

    @property
    def codeword(self):
        """Get or set the codeword output port (72 bits)."""
        return self._dut.codeword

    @codeword.setter
    def codeword(self, value):
        self._dut.codeword.value = value
