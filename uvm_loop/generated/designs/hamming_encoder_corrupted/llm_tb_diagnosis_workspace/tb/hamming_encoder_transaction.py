# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Transaction class for Hamming Encoder UVM testbench.

This defines the sequence_item that carries the input data to the DUT.
"""

from pyuvm import uvm_sequence_item


class HammingEncoderTransaction(uvm_sequence_item):
    """Sequence item for Hamming encoder transactions.

    Attributes:
        data_in (int): 64-bit input data to be encoded.
        codeword (int): 72-bit encoded codeword.
    """

    def __init__(self, name="HammingEncoderTransaction"):
        super().__init__(name)
        self.data_in = 0
        self.codeword = 0

    def __eq__(self, other):
        if not isinstance(other, HammingEncoderTransaction):
            return False
        return self.data_in == other.data_in and self.codeword == other.codeword

    def __copy__(self):
        trans = HammingEncoderTransaction()
        trans.data_in = self.data_in
        trans.codeword = self.codeword
        return trans

    def do_print(self, printer):
        printer.print_field("data_in", self.data_in, 64)
        printer.print_field("codeword", self.codeword, 72)
