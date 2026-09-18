# Copyright (c) 2026 CHIA Open Source
# SPDX-License-Identifier: Apache-2.0

"""
Top-level cocotb test module for Hamming Encoder UVM testbench.
"""

import os
import cocotb
from pyuvm import uvm_root, ConfigDB
from dut_helper import HammingEncoderDUTHelper

# Importing 'test_classes' bundles every uvm_test subclass so
# uvm_root().run_test() can resolve the class by name at runtime.
import test_classes  # noqa: F401 (side effect: register test classes)


async def setup_config_db(dut):
    """Set up ConfigDB with the DUT helper."""
    # Create and set the DUT helper
    dut_helper = HammingEncoderDUTHelper(dut)
    ConfigDB().set(None, "*", "dut_helper", dut_helper)


@cocotb.test()
async def run_test(dut):
    """Top-level test that runs the UVM test specified by UVM_TESTNAME."""
    # Set up ConfigDB
    await setup_config_db(dut)
    
    # Get the test name from environment variable, default to TestAllZerosInput
    test_name = os.environ.get("UVM_TESTNAME", "TestAllZerosInput")
    
    # Run the test. keep_singletons=True is required: run_test() otherwise
    # clears all Singleton-metaclass instances (including ConfigDB) at
    # start, wiping the dut_helper set above before build_phase can read it.
    await uvm_root().run_test(test_name, keep_singletons=True)