# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Driver for Hamming Encoder UVM testbench.
"""

from pyuvm import uvm_driver
from hamming_encoder_transaction import HammingEncoderTransaction


class HammingEncoderDriver(uvm_driver):
    """Driver for Hamming encoder.

    The driver receives HammingEncoderTransaction items and drives the
    data_in pin of the DUT.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut_helper = None

    def connect_phase(self):
        super().connect_phase()
        # Get the dut_helper from ConfigDB using the key defined in the contract.
        self.dut_helper = self.cdb_get("dut_helper", "")

    async def run_phase(self):
        while True:
            # Wait for the next item from the sequencer.
            item = await self.seq_item_port.get_next_item()
            # Drive the data_in pin.
            self.dut_helper.data_in = item.data_in
            # Mark the item as done.
            self.seq_item_port.item_done()