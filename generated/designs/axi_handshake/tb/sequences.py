"""Sequences for the axi_handshake DUT.

Structure
---------
* ``_AxiBaseSequence`` – shared helpers (reset, drive, check).
* **Directed sequences** – one per ``directed_test_scenarios`` entry;
  each carries a ``SCENARIO_ID`` matching the plan verbatim.
* **Corner-case sequences** – exercise specific boundary conditions
  declared in ``corner_cases``.
* **Randomized sequence** – generates random stimuli per the
  ``randomized_testing_strategy`` for scoreboard-based checking.

Driving conventions
-------------------
* ``_drive(...)`` pushes an ``AxiHandshakeTxn`` through the sequencer
  to the driver.  The driver applies inputs on the next rising clock
  edge and returns after the DUT has processed them.
* ``_check(...)`` reads DUT outputs via the shared ``dut_helper`` and
  asserts they match the expected values.
* ``_reset_dut(cycles)`` drives ``rst_n`` low for *cycles* rising
  edges, then deasserts it and waits for one additional edge so the DUT
  exits reset cleanly.
"""

import random

from cocotb.triggers import RisingEdge, ReadOnly
from pyuvm import uvm_sequence, ConfigDB

from transaction import AxiHandshakeTxn


# ═══════════════════════════════════════════════════════════════════
#  Base class – common helpers
# ═══════════════════════════════════════════════════════════════════

class _AxiBaseSequence(uvm_sequence):
    """Provides reset / drive / check convenience methods.

    Subclasses override ``body()`` to compose a test scenario using
    these helpers.
    """

    # -- helpers -----------------------------------------------------

    async def _reset_dut(self, cycles=5):
        """Assert rst_n low for *cycles* rising edges, then release."""
        dut = ConfigDB().get(None, "", "dut")
        clk = dut.clk

        dut.rst_n.value = 0
        for _ in range(cycles):
            await RisingEdge(clk)

        dut.rst_n.value = 1
        await RisingEdge(clk)   # DUT exits reset on this edge
        await ReadOnly()        # let outputs settle

    async def _drive(self, s_valid, s_data, m_ready):
        """Send one transaction through the sequencer to the driver.

        The driver applies these inputs on the next rising clock edge
        and blocks until the DUT has captured them (one full cycle).
        """
        item = AxiHandshakeTxn()
        item.set_inputs(s_valid, s_data, m_ready)
        await self.start_item(item)
        await self.finish_item(item)

    async def _check(self, **expected):
        """Read DUT outputs and assert they match *expected*.

        Any mismatch raises ``AssertionError`` immediately, failing
        the test.
        """
        dut_helper = ConfigDB().get(None, "", "dut_helper")
        outputs = dut_helper.read_outputs()
        for key, value in expected.items():
            actual = outputs[key]
            assert actual == value, (
                f"[{self.get_name()}] Check FAILED: {key} "
                f"expected 0x{value:02X}, got 0x{actual:02X} "
                f"(full outputs: {outputs})"
            )


# ═══════════════════════════════════════════════════════════════════
#  Directed sequences  (one per plan scenario, ID preserved)
# ═══════════════════════════════════════════════════════════════════

class SmokeAfterResetSequence(_AxiBaseSequence):
    """smoke_after_reset – load one item after reset and verify output."""

    SCENARIO_ID = "smoke_after_reset"

    async def body(self):
        await self._reset_dut(cycles=5)

        # Drive first input item with output ready
        await self._drive(s_valid=1, s_data=0xA5, m_ready=1)

        # Buffer now holds A5, m_valid is high
        await self._check(s_ready=1, m_valid=1, m_data=0xA5)

        # Release input; output is consumed when m_ready is high
        await self._drive(s_valid=0, s_data=0, m_ready=1)

        # After consumption with no new input, m_valid deasserts
        await self._check(m_valid=0)


class StallHoldSequence(_AxiBaseSequence):
    """stall_hold – output stall must hold m_valid and m_data."""

    SCENARIO_ID = "stall_hold"

    async def body(self):
        await self._reset_dut(cycles=5)

        # Load first item
        await self._drive(s_valid=1, s_data=0x42, m_ready=1)

        # Stall the output (m_ready deasserted)
        await self._drive(s_valid=0, s_data=0, m_ready=0)

        # m_valid and m_data must be held; s_ready must be 0 during stall
        await self._check(m_valid=1, m_data=0x42, s_ready=0)

        # Attempt input while stalled – should not be accepted
        await self._drive(s_valid=1, s_data=0xFF, m_ready=0)

        # Buffer still holds 0x42; input was not accepted
        await self._check(m_valid=1, m_data=0x42, s_ready=0)

        # Release the stall
        await self._drive(s_valid=0, s_data=0, m_ready=1)

        # After consumption, m_valid deasserts and m_data returns to default
        await self._check(m_valid=0, m_data=0x00)


class SimultaneousTransferSequence(_AxiBaseSequence):
    """simultaneous_transfer – consume + load in the same cycle."""

    SCENARIO_ID = "simultaneous_transfer"

    async def body(self):
        await self._reset_dut(cycles=5)

        # Load item 0x11
        await self._drive(s_valid=1, s_data=0x11, m_ready=1)

        # Buffer now holds 0x11
        await self._check(m_valid=1, m_data=0x11)

        # Simultaneously consume 0x11 and load 0x22
        await self._drive(s_valid=1, s_data=0x22, m_ready=1)

        # Buffer now holds 0x22; m_valid stayed high
        await self._check(m_valid=1, m_data=0x22)


class SequentialLoadsSequence(_AxiBaseSequence):
    """sequential_loads – load and consume three items in order."""

    SCENARIO_ID = "sequential_loads"

    async def body(self):
        await self._reset_dut(cycles=5)

        for data in [0x01, 0x02, 0x03]:
            # Load
            await self._drive(s_valid=1, s_data=data, m_ready=1)
            await self._check(m_valid=1, m_data=data)

            # Consume
            await self._drive(s_valid=0, s_data=0, m_ready=1)
            await self._check(m_valid=0)


class NoInputWhenStalledSequence(_AxiBaseSequence):
    """no_input_when_stalled – s_ready deasserted during output stall."""

    SCENARIO_ID = "no_input_when_stalled"

    async def body(self):
        await self._reset_dut(cycles=5)

        # Load the buffer
        await self._drive(s_valid=1, s_data=0xBB, m_ready=1)

        # Keep s_valid high but stall the output
        await self._drive(s_valid=1, s_data=0xCC, m_ready=0)

        # m_data must still be BB, s_ready must be 0 – input not accepted
        await self._check(m_valid=1, m_data=0xBB, s_ready=0)

        # Drain the buffer
        await self._drive(s_valid=0, s_data=0, m_ready=1)

        # Buffer drained
        await self._check(m_valid=0)


class ResetDuringTransferSequence(_AxiBaseSequence):
    """reset_during_transfer – reset mid-transfer clears buffer."""

    SCENARIO_ID = "reset_during_transfer"

    async def body(self):
        await self._reset_dut(cycles=5)

        # Load an item
        await self._drive(s_valid=1, s_data=0xDD, m_ready=1)
        await self._check(m_valid=1, m_data=0xDD)

        # Assert reset again
        await self._reset_dut(cycles=3)

        # Buffer cleared by reset
        await self._check(m_valid=0, s_ready=1)


# ═══════════════════════════════════════════════════════════════════
#  Corner-case sequences  (no SCENARIO_ID – not directed scenarios)
# ═══════════════════════════════════════════════════════════════════

class BackToBackFullRateSequence(_AxiBaseSequence):
    """Back-to-back full-rate transfers.

    Keep both s_valid and m_ready asserted continuously.  Each cycle
    the output consumes the current item and the input loads a new one.
    m_valid must remain high the entire time after the first item.
    """

    async def body(self):
        await self._reset_dut(cycles=5)

        # First item – buffer fills
        await self._drive(s_valid=1, s_data=0x01, m_ready=1)
        await self._check(m_valid=1, s_ready=1)

        # Sustained full-rate: consume + load each cycle
        for i in range(0x02, 0x07):
            await self._drive(s_valid=1, s_data=i, m_ready=1)
            await self._check(m_valid=1, s_ready=1)


class AllZeroPayloadSequence(_AxiBaseSequence):
    """All-zero payload – transfer 0x00 and verify."""

    async def body(self):
        await self._reset_dut(cycles=5)

        await self._drive(s_valid=1, s_data=0x00, m_ready=1)
        await self._check(m_valid=1, m_data=0x00)


class AllOnePayloadSequence(_AxiBaseSequence):
    """All-one payload – transfer 0xFF and verify."""

    async def body(self):
        await self._reset_dut(cycles=5)

        await self._drive(s_valid=1, s_data=0xFF, m_ready=1)
        await self._check(m_valid=1, m_data=0xFF)


class ProducerHoldsForeverSequence(_AxiBaseSequence):
    """Producer holds s_valid high while consumer never reads.

    After loading the buffer the producer keeps s_valid=1 with
    different data values while m_ready=0.  The DUT must never accept
    a new item.  On release (m_ready=1) the original item emerges.
    """

    async def body(self):
        await self._reset_dut(cycles=5)

        original = 0xAA

        # Load the buffer with the original value
        await self._drive(s_valid=1, s_data=original, m_ready=1)
        await self._check(m_valid=1, m_data=original)

        # Producer keeps pushing while consumer is stalled
        for data in [0xBB, 0xCC, 0xDD]:
            await self._drive(s_valid=1, s_data=data, m_ready=0)
            await self._check(m_valid=1, m_data=original, s_ready=0)

        # Release: consumer reads, producer stops
        await self._drive(s_valid=0, s_data=0, m_ready=1)

        # Buffer drained
        await self._check(m_valid=0)


# ═══════════════════════════════════════════════════════════════════
#  Randomized sequence  (scoreboard checks against reference model)
# ═══════════════════════════════════════════════════════════════════

class RandomStimulusSequence(_AxiBaseSequence):
    """Randomized s_valid / s_data / m_ready each cycle.

    Periodically injects reset (every ~100 cycles on average, held
    for 3–5 cycles).  The scoreboard (generated in a later stage)
    compares DUT outputs against the reference model each cycle.
    """

    NUM_CYCLES = 1000
    RESET_AVG_INTERVAL = 100  # average cycles between resets

    async def body(self):
        for _cycle in range(self.NUM_CYCLES):
            # --- Periodic reset injection --------------------------------
            if random.randint(0, self.RESET_AVG_INTERVAL - 1) == 0:
                reset_cycles = random.randint(3, 5)
                await self._reset_dut(cycles=reset_cycles)

            # --- Randomise inputs ----------------------------------------
            s_valid = random.randint(0, 1)
            s_data = random.randint(0, 0xFF)
            m_ready = random.randint(0, 1)

            await self._drive(s_valid, s_data, m_ready)
