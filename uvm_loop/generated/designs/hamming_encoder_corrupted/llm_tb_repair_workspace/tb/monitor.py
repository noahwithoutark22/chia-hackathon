# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Monitor for Hamming Encoder UVM testbench.
"""

import cocotb
from cocotb.triggers import ValueChange, Timer
from pyuvm import uvm_monitor, uvm_analysis_port
from pyuvm import ConfigDB

from hamming_encoder_transaction import HammingEncoderTransaction


class HammingEncoderMonitor(uvm_monitor):
    """Monitor for Hamming encoder.

    Observes the data_in pin of the DUT and captures transactions.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.helper = None
        self.ap = uvm_analysis_port("ap", self)

    def build_phase(self):
        super().build_phase()
        self.helper = ConfigDB().get(self, "", "dut_helper")
        if self.helper is None:
            raise RuntimeError("Failed to get helper from ConfigDB")

    async def run_phase(self):
        while True:
            await ValueChange(self.helper.data_in)
            # Allow time for combinational output to propagate
            await Timer(1, 'ns')
            # Sample the input data_in and output codeword
            try:
                data_in_val = self.helper.data_in.value
                data_in_val_int = data_in_val.integer
                codeword_val = self.helper.codeword.value
                codeword_val_int = codeword_val.integer
            except ValueError:
                self.logger.error(f"One of data_in or codeword contains unresolvable bits (x or z)")
                data_in_val_int = 0
                codeword_val_int = 0
            # Create a transaction
            trans = HammingEncoderTransaction()
            trans.data_in = data_in_val_int
            trans.codeword = codeword_val_int
            # Publish the transaction
            self.ap.write(trans)