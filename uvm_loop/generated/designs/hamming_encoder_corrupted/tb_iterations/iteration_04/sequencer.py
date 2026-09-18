# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Sequencer for Hamming Encoder UVM testbench.
"""

from pyuvm import uvm_sequencer
from hamming_encoder_transaction import HammingEncoderTransaction


class HammingEncoderSequencer(uvm_sequencer):
    """Sequencer for Hamming encoder transactions.

    The sequencer produces instances of HammingEncoderTransaction.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)