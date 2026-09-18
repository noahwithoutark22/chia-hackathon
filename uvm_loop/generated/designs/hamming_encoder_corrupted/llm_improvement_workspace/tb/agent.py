# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Agent for Hamming Encoder UVM testbench.
"""

from pyuvm import uvm_agent
from driver import HammingEncoderDriver
from sequencer import HammingEncoderSequencer
from monitor import HammingEncoderMonitor


class HammingEncoderAgent(uvm_agent):
    """Agent for Hamming encoder.

    Contains a sequencer, driver, and monitor.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.sequencer = None
        self.driver = None
        self.monitor = None

    def build_phase(self):
        super().build_phase()
        # Create the sequencer, driver, and monitor.
        self.sequencer = HammingEncoderSequencer("sequencer", self)
        self.driver = HammingEncoderDriver("driver", self)
        self.monitor = HammingEncoderMonitor("monitor", self)

    def connect_phase(self):
        super().connect_phase()
        # Connect the driver to the sequencer.
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)