# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Scoreboard for Hamming Encoder UVM testbench.
"""

import cocotb
from cocotb.triggers import Timer
from pyuvm import uvm_scoreboard, uvm_tlm_analysis_fifo, ConfigDB
from hamming_encoder_transaction import HammingEncoderTransaction

# Import the reference model
import sys
sys.path.append("/workspace/benchmarks/hamming_encoder_benchmark_corrupted")
from hamming_reference_model import encode


class HammingEncoderScoreboard(uvm_scoreboard):
    """Scoreboard for Hamming encoder.
    
    Compares the DUT's codeword output with the expected output from the
    reference model for each input data_in transaction.
    """

    def __init__(self, name="HammingEncoderScoreboard", parent=None):
        super().__init__(name, parent)
        self.helper = None
        self.errors = 0
        self.analysis_fifo = None
        self.analysis_export = None

    def build_phase(self):
        super().build_phase()
        # Get the DUT helper from ConfigDB
        self.helper = ConfigDB().get(self, "", "dut_helper")
        if self.helper is None:
            raise RuntimeError("Failed to get helper from ConfigDB")
        # A uvm_tlm_analysis_fifo buffers monitor items and exposes an
        # analysis_export (non-blocking write) that the environment connects
        # to the monitor's analysis port; get() blocks until an item arrives.
        self.analysis_fifo = uvm_tlm_analysis_fifo("analysis_fifo", self)
        self.analysis_export = self.analysis_fifo.analysis_export

    def connect_phase(self):
        super().connect_phase()
        # The analysis import will be connected by the parent component (agent/env)
        pass

    async def run_phase(self):
        """Process transactions from the analysis FIFO."""
        while True:
            # Wait for a transaction from the FIFO
            trans = await self.analysis_fifo.get()
            # Compute expected codeword using reference model
            data_in_val = trans.data_in
            expected_codeword = encode(data_in_val)
            
            # Wait for the DUT output to settle (allow combinational propagation)
            await Timer(1, 'ns')
            
            # Read actual codeword from DUT
            try:
                try:
                    actual_codeword = self.helper.codeword.value.integer
                except ValueError:
                    self.logger.error(f"codeword contains unresolvable bits (x or z)")
                    actual_codeword = 0
            except ValueError:
                self.logger.error(f"codeword contains unresolvable bits (x or z) for data_in=0x{data_in_val:016x}")
                actual_codeword = 0
            
            # Compare
            if actual_codeword != expected_codeword:
                self.errors += 1
                self.logger.error(
                    f"Scoreboard mismatch: data_in=0x{data_in_val:016x}, "
                    f"expected_codeword=0x{expected_codeword:018x}, "
                    f"actual_codeword=0x{actual_codeword:018x}"
                )
                # Optionally, we can also show bit-wise difference
                xor = actual_codeword ^ expected_codeword
                self.logger.error(f"Bit-wise difference (XOR): 0x{xor:018x}")
            else:
                self.logger.debug(
                    f"Scoreboard match: data_in=0x{data_in_val:016x}, "
                    f"codeword=0x{actual_codeword:018x}"
                )

    def report_phase(self):
        super().report_phase()
        if self.errors > 0:
            self.logger.error(f"Scoreboard reported {self.errors} errors.")
        else:
            self.logger.info("Scoreboard: No errors detected.")