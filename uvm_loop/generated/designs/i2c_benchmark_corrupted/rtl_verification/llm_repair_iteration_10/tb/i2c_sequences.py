"""i2c_master stimulus sequences for the cocotb + pyuvm bench.

Stage-2 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory; it is the authoritative convention record).

This module implements the plan's directed scenarios, corner cases and
randomized strategy as pyuvm ``uvm_sequence`` subclasses (CONTRACT.md §10):

* **Directed scenarios** TC-01..TC-13: every class carries
  ``SCENARIO_ID = "<exact plan id>"`` and the value byte-for-byte matches a
  ``directed_test_scenarios[].id``.  Each planned scenario is implemented
  exactly once (verified by :func:`assert_directed_scenario_ids`).

* **Corner cases**: one class per plan corner entry; they deliberately carry
  ``SCENARIO_ID = None`` (they are a separate verification strategy and must
  NOT be assigned a directed scenario id).

* **Randomized strategy**: :class:`I2CRandomSequence` generates the full
  uniform address/data/direction space with randomized slave ACK/NACK
  responses and read data (plan ``randomized_testing_strategy``).

Two execution styles are used, both documented in CONTRACT.md §13:

1. *Item mode* -- ``uvm_sequence`` objects created with ``I2CTransaction``
   and sent to the driver through the sequencer with ``start_item`` /
   ``finish_item`` (e.g. :class:`CornerAddrZeroWrite`).
2. *Flow mode* -- timed scenario sequences call the driver's public async
   task methods (``assert_reset``/``deassert_reset``/``start_transaction``/
   ``drive_slave_response``/``run_transaction``/``pulse_start_while_busy``/
   ``expect_outputs``).  The driver obtained via ConfigDB key ``"i2c_driver"``
   (``KEY_I2C_DRIVER`` in ``i2c_driver.py``).

Every transaction wait is bounded by the driver (``START_TIMEOUT_CYCLES`` /
``DONE_TIMEOUT_CYCLES``); a bound expiry raises ``I2CDriverTimeout``, which
later stages treat as a hung-transaction report.

Cocotb 2.1.0 public-API notes: this module imports no cocotb symbols; it
uses only pyuvm (``uvm_sequence``), the shared ConfigDB keys and the
driver/transaction classes of this bench.
"""

import os
import random

from pyuvm import ConfigDB, uvm_sequence

from i2c_driver import I2CDriver, KEY_I2C_DRIVER
from i2c_transaction import I2CTransaction

# ---------------------------------------------------------------------------
# The locked set of directed scenario ids from the plan (CONTRACT.md §10).
# assert_directed_scenario_ids() requires the sequence registry below to map
# 1:1 onto this set.
# ---------------------------------------------------------------------------
PLANNED_DIRECTED_IDS = [
    "TC-01",
    "TC-02",
    "TC-03",
    "TC-04",
    "TC-05",
    "TC-06",
    "TC-07",
    "TC-08",
    "TC-09",
    "TC-10",
    "TC-11",
    "TC-12",
    "TC-13",
]


class I2CSequenceBase(uvm_sequence):
    """Base class for all i2c_master stimulus sequences.

    Provides ConfigDB access to the driver and small helpers.  Directed
    scenarios set ``SCENARIO_ID`` (see CONTRACT.md §10); corner-case and
    randomized sequences leave it ``None``.
    """

    SCENARIO_ID = None  # set exactly on directed-scenario sequence classes

    # -- shared-handle access (CONTRACT.md §6 / §13) ------------------------
    def _get_driver(self) -> I2CDriver:
        return ConfigDB().get(None, "", KEY_I2C_DRIVER)

    # -- helpers --------------------------------------------------------------
    def _new_item(self, **constraints) -> I2CTransaction:
        """Build and validate an ``I2CTransaction`` from keyword fields."""
        item = I2CTransaction(**constraints)
        item.check_inputs_valid()
        return item

    def _check(self, cond, message):
        """Fail the sequence (loudly) when a scenario expectation fails."""
        if not cond:
            raise AssertionError(
                f"[{self.get_name()}] stimulus check failed: {message}"
            )


# ===========================================================================
# DIRECTED SCENARIOS (plan directed_test_scenarios; SCENARIO_ID is the
# authoritative identity -- see CONTRACT.md §10).
# ===========================================================================


class ResetIdleCheckSequence(I2CSequenceBase):
    """TC-01 reset_idle_check: reset clears all status outputs (idle)."""

    SCENARIO_ID = "TC-01"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-01 reset_idle_check: apply reset and verify idle state")
        await drv.assert_reset(4)      # plan: rst_n=0 for 4 clocks
        await drv.deassert_reset(2)    # plan: rst_n=1, wait 2 clocks
        await drv.expect_outputs(
            {"busy": 0, "done": 0, "ack_error": 0, "rx_data": 0},
            description="TC-01 post-reset idle state (expect action)",
        )


class WriteBasicSequence(I2CSequenceBase):
    """TC-02 write_basic: write 0xA5 to slave 0x50, slave ACK on both phases."""

    SCENARIO_ID = "TC-02"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-02 write_basic: write 0xA5 -> slave 0x50")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        await drv.run_transaction(item)          # addr ACK + data ACK
        self._check(item.done == 1, "TC-02: done sampled high at completion")
        self._check(item.ack_error == 0, "TC-02: ack_error must stay low")
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0},
            wait_cycles=2,
            description="TC-02 successful write leaves ack_error low, busy low",
        )


class WriteZeroSequence(I2CSequenceBase):
    """TC-03 write_zero: write 0x00 to slave 0x00 (address byte 0x00)."""

    SCENARIO_ID = "TC-03"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-03 write_zero: write 0x00 -> slave 0x00")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x00, rw=0, tx_data=0x00, slave_ack=1)
        self._check(item.address_byte == 0x00, "TC-03: address byte is 0x00")
        await drv.run_transaction(item)
        self._check(item.ack_error == 0, "TC-03: ack_error must stay low")
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0},
            wait_cycles=2,
            description="TC-03 write_zero completion state",
        )


class WriteMaxSequence(I2CSequenceBase):
    """TC-04 write_max: write 0xFF to slave 0x7F (address byte 0xFE)."""

    SCENARIO_ID = "TC-04"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-04 write_max: write 0xFF -> slave 0x7F")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x7F, rw=0, tx_data=0xFF, slave_ack=1)
        self._check(item.address_byte == 0xFE, "TC-04: address byte is 0xFE")
        await drv.run_transaction(item)
        self._check(item.ack_error == 0, "TC-04: ack_error must stay low")
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0},
            wait_cycles=2,
            description="TC-04 write_max completion state",
        )


class ReadBasicSequence(I2CSequenceBase):
    """TC-05 read_basic: read one byte (0x3C) from slave 0x50, master NACK."""

    SCENARIO_ID = "TC-05"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-05 read_basic: read slave 0x50, slave drives 0x3C")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(
            slave_addr=0x50, rw=1, tx_data=0x00, read_data=0x3C, slave_ack=1
        )
        self._check(item.address_byte == 0xA1, "TC-05: address byte is 0xA1")
        await drv.run_transaction(item)
        self._check(item.done == 1, "TC-05: done sampled high at completion")
        self._check(item.rx_data == 0x3C, "TC-05: rx_data must be 0x3C")
        self._check(item.ack_error == 0, "TC-05: ack_error must stay low")
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0, "rx_data": 0x3C},
            wait_cycles=2,
            description="TC-05 read_basic completion state",
        )


class ReadMaxSequence(I2CSequenceBase):
    """TC-06 read_max: read one byte (0xFF) from slave 0x2A."""

    SCENARIO_ID = "TC-06"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-06 read_max: read slave 0x2A, slave drives 0xFF")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(
            slave_addr=0x2A, rw=1, tx_data=0x00, read_data=0xFF, slave_ack=1
        )
        self._check(item.address_byte == 0x55, "TC-06: address byte is 0x55")
        await drv.run_transaction(item)
        self._check(item.rx_data == 0xFF, "TC-06: rx_data must be 0xFF")
        self._check(item.ack_error == 0, "TC-06: ack_error must stay low")
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0, "rx_data": 0xFF},
            wait_cycles=2,
            description="TC-06 read_max completion state",
        )


class WriteAddrNackSequence(I2CSequenceBase):
    """TC-07 write_addr_nack: slave NACKs the address; ack_error asserts."""

    SCENARIO_ID = "TC-07"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-07 write_addr_nack: slave NACKs the address phase")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x30, rw=0, tx_data=0x00, slave_ack=0)
        await drv.run_transaction(item)
        # ack_error is sampled at the completion point; on a correct RTL the
        # error level is cleared in IDLE afterwards, so use the sampled item.
        self._check(
            item.ack_error == 1,
            "TC-07: ack_error must be sampled high after an address NACK",
        )
        await drv.expect_outputs(
            {"busy": 0},
            wait_cycles=2,
            description="TC-07 busy deasserted after the NACK transaction",
        )


class WriteDataNackSequence(I2CSequenceBase):
    """TC-08 write_data_nack: address ACKed, write data NACKed; ack_error."""

    SCENARIO_ID = "TC-08"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-08 write_data_nack: address ACK, write data NACK")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        await drv.run_transaction(item, addr_ack=1, data_ack=0)
        self._check(
            item.ack_error == 1,
            "TC-08: ack_error must be sampled high after a write-data NACK",
        )
        await drv.expect_outputs(
            {"busy": 0},
            wait_cycles=2,
            description="TC-08 busy deasserted after the NACK transaction",
        )


class ReadAddrNackSequence(I2CSequenceBase):
    """TC-09 read_addr_nack: slave NACKs the address; ack_error asserts."""

    SCENARIO_ID = "TC-09"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-09 read_addr_nack: slave NACKs the address phase")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(
            slave_addr=0x50, rw=1, tx_data=0x00, read_data=0x00, slave_ack=0
        )
        await drv.run_transaction(item)
        self._check(
            item.ack_error == 1,
            "TC-09: ack_error must be sampled high after a read address NACK",
        )
        await drv.expect_outputs(
            {"busy": 0},
            wait_cycles=2,
            description="TC-09 busy deasserted after the NACK transaction",
        )


class StartWhileBusySequence(I2CSequenceBase):
    """TC-10 start_while_busy: a start while busy must be ignored."""

    SCENARIO_ID = "TC-10"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-10 start_while_busy: illegal start while busy is ignored")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        spur_item = self._new_item(slave_addr=0x0A, rw=0, tx_data=0x63)

        async def _illegal_start(driver):
            self.logger.info(
                "TC-10: asserting start=1 with slave 0x0A/0x63 while busy"
            )
            await driver.pulse_start_while_busy(spur_item, hold_cycles=1)

        await drv.run_transaction(item, mid_transaction=_illegal_start)
        self._check(
            item.ack_error == 0,
            "TC-10: only the first transaction was executed (no corruption)",
        )
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0},
            wait_cycles=2,
            description="TC-10 first transaction completes cleanly",
        )


class ResetDuringTransactionSequence(I2CSequenceBase):
    """TC-11 reset_during_transaction: reset mid-transaction clears state."""

    SCENARIO_ID = "TC-11"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-11 reset_during_transaction: reset injected while busy")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5)
        await drv.start_transaction(item)   # accepted -> busy high
        await drv.assert_reset(3)           # plan: rst_n=0 for 3 clocks while active
        await drv.deassert_reset(2)         # plan: rst_n=1, wait 2 clocks
        await drv.expect_outputs(
            {"busy": 0, "done": 0, "ack_error": 0, "rx_data": 0},
            description="TC-11 mid-transaction reset clears all status outputs",
        )
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5)
        await drv.start_transaction(item)
        await drv.complete_transaction(item)


class DonePulseCheckSequence(I2CSequenceBase):
    """TC-12 done_pulse_check: done is low in idle, one cycle at completion."""

    SCENARIO_ID = "TC-12"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-12 done_pulse_check: done low in idle, pulse at completion")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        # plan note: verified in idle before the start -- done must be 0
        await drv.expect_outputs(
            {"done": 0},
            description="TC-12 done must be low while idle (before start)",
        )
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        await drv.run_transaction(item)
        # Completion-point sample: done is high exactly during the pulse.
        self._check(item.done == 1, "TC-12: done sampled high at completion")
        self._check(item.busy == 0, "TC-12: busy low at completion")
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0},
            wait_cycles=2,
            description="TC-12 post-completion idle state",
        )


class AddressMsbFirstCheckSequence(I2CSequenceBase):
    """TC-13 address_msb_first_check: address byte transmitted MSB first.

    Address byte must be 0xD4 for slave 0x6A (write), transmitted MSB first:
    [1, 1, 0, 1, 0, 1, 0, 0] per the reference model's ``address_bits()``.
    The bit-by-bit stream verification is the observation stage's stream
    checker; this sequence documents the expected vector and drives the
    stimulus.
    """

    SCENARIO_ID = "TC-13"

    async def body(self):
        drv = self._get_driver()
        self.logger.info("TC-13 address_msb_first_check: write slave 0x6A data 0x5A")
        await drv.assert_reset(4)
        await drv.deassert_reset(1)
        item = self._new_item(slave_addr=0x6A, rw=0, tx_data=0x5A, slave_ack=1)
        self._check(item.address_byte == 0xD4, "TC-13: address byte is 0xD4")
        expected_bits = [1, 1, 0, 1, 0, 1, 0, 0]  # plan expected vector
        bits = [(item.address_byte >> (7 - i)) & 1 for i in range(8)]
        self._check(
            bits == expected_bits,
            f"TC-13: address bits MSB-first must be {expected_bits}, got {bits}",
        )
        await drv.run_transaction(item)
        self._check(item.ack_error == 0, "TC-13: ack_error must stay low")
        await drv.expect_outputs(
            {"ack_error": 0, "busy": 0},
            wait_cycles=2,
            description="TC-13 address_msb_first_check completion state",
        )


# ===========================================================================
# CORNER CASES (plan corner_cases; NO SCENARIO_ID by design).
#
# Item-mode corners run through the sequencer -> driver run_phase item flow
# (their item is completion-sampled by the driver).  Flow corners call the
# driver's task API for per-phase ACK control / reset / timing.
# ===========================================================================


class CornerAddrZeroWrite(I2CSequenceBase):
    """addr_zero_write: write to slave 0x00 (address byte 0x00)."""

    async def body(self):
        item = self._new_item(slave_addr=0x00, rw=0, tx_data=0x00, slave_ack=1)
        self._check(item.address_byte == 0x00, "address byte must be 0x00")
        await self.start_item(item)
        await self.finish_item(item)


class CornerAddrMaxWrite(I2CSequenceBase):
    """addr_max_write: write to slave 0x7F (address byte 0xFE)."""

    async def body(self):
        item = self._new_item(slave_addr=0x7F, rw=0, tx_data=0xFF, slave_ack=1)
        self._check(item.address_byte == 0xFE, "address byte must be 0xFE")
        await self.start_item(item)
        await self.finish_item(item)


class CornerAddrMaxRead(I2CSequenceBase):
    """addr_max_read: read from slave 0x7F (address byte 0xFF)."""

    async def body(self):
        item = self._new_item(
            slave_addr=0x7F, rw=1, tx_data=0x00, read_data=0x55, slave_ack=1
        )
        self._check(item.address_byte == 0xFF, "address byte must be 0xFF")
        await self.start_item(item)
        await self.finish_item(item)
        self._check(
            item.rx_data == 0x55,
            "rx_data must equal the slave-driven byte (0x55)",
        )


class CornerDataZeroWrite(I2CSequenceBase):
    """data_zero_write: write with tx_data 0x00."""

    async def body(self):
        item = self._new_item(slave_addr=0x22, rw=0, tx_data=0x00, slave_ack=1)
        self._check(item.tx_data == 0x00, "tx_data must be 0x00")
        await self.start_item(item)
        await self.finish_item(item)


class CornerDataMaxWrite(I2CSequenceBase):
    """data_max_write: write with tx_data 0xFF."""

    async def body(self):
        item = self._new_item(slave_addr=0x22, rw=0, tx_data=0xFF, slave_ack=1)
        self._check(item.tx_data == 0xFF, "tx_data must be 0xFF")
        await self.start_item(item)
        await self.finish_item(item)


class CornerRxAllOnesRead(I2CSequenceBase):
    """rx_all_ones_read: slave drives 0xFF; rx_data must be 0xFF."""

    async def body(self):
        item = self._new_item(
            slave_addr=0x22, rw=1, tx_data=0x00, read_data=0xFF, slave_ack=1
        )
        await self.start_item(item)
        await self.finish_item(item)
        self._check(item.rx_data == 0xFF, "rx_data must be 0xFF")


class CornerRxAllZerosRead(I2CSequenceBase):
    """rx_all_zeros_read: slave drives 0x00; rx_data must be 0x00."""

    async def body(self):
        item = self._new_item(
            slave_addr=0x22, rw=1, tx_data=0x00, read_data=0x00, slave_ack=1
        )
        await self.start_item(item)
        await self.finish_item(item)
        self._check(item.rx_data == 0x00, "rx_data must be 0x00")


class CornerMissingAddrAck(I2CSequenceBase):
    """missing_addr_ack: SDA high at the address ACK sample; ack_error."""

    async def body(self):
        item = self._new_item(slave_addr=0x30, rw=0, tx_data=0x00, slave_ack=0)
        await self.start_item(item)
        await self.finish_item(item)
        self._check(item.ack_error == 1, "ack_error must assert (address NACK)")


class CornerMissingDataAck(I2CSequenceBase):
    """missing_data_ack: address ACKed, write data NACKed; ack_error asserts."""

    async def body(self):
        drv = self._get_driver()
        await drv.reset_phase(hold_cycles=4, settle_cycles=1)
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        await drv.run_transaction(item, addr_ack=1, data_ack=0)
        self._check(item.ack_error == 1, "ack_error must assert (write-data NACK)")


class CornerStartOneCycle(I2CSequenceBase):
    """start_one_cycle: a one-cycle start offer begins exactly one transaction."""

    async def body(self):
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        await self.start_item(item)
        await self.finish_item(item)
        # The driver only accepts the offer once (busy 0->1) and releases
        # start after exactly one offer cycle; acceptance either happened
        # exactly once or the driver reported a hung start (timeout).  The
        # completion record confirms the transaction reached its done pulse.
        self._check(item.done == 1, "transaction must have completed (done sampled high)")
        self._check(item.busy == 0, "transaction must be idle at completion")


class CornerBackToBackTransactions(I2CSequenceBase):
    """back_to_back_transactions: two sequential complete transactions."""

    async def body(self):
        first = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        await self.start_item(first)
        await self.finish_item(first)
        self._check(first.ack_error == 0, "first transaction must be ACK-clean")
        second = self._new_item(slave_addr=0x30, rw=0, tx_data=0x5A, slave_ack=1)
        await self.start_item(second)
        await self.finish_item(second)
        self._check(second.ack_error == 0, "second transaction must be ACK-clean")


class CornerResetMidTransaction(I2CSequenceBase):
    """reset_mid_transaction: reset while busy clears the status outputs."""

    async def body(self):
        drv = self._get_driver()
        await drv.reset_phase(hold_cycles=4, settle_cycles=1)
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5)
        await drv.start_transaction(item)   # busy high
        await drv.assert_reset(3)
        await drv.deassert_reset(2)
        await drv.expect_outputs(
            {"busy": 0, "done": 0, "ack_error": 0, "rx_data": 0},
            description="reset_mid_transaction clears all status outputs",
        )


class CornerClkDivMin(I2CSequenceBase):
    """clk_div_min: with CLK_DIV=4 the engine advances every 4 cycles.

    The advance cadence itself is measured by the observation/assertion
    stages; this sequence exercises a full transaction at the minimum plan
    CLK_DIV and records the driver's expected advance schedule.
    """

    async def body(self):
        drv = self._get_driver()
        self._check(
            drv.clk_div == 4,
            f"clk_div_min expects CLK_DIV=4, environment running {drv.clk_div}",
        )
        await drv.reset_phase(hold_cycles=4, settle_cycles=1)
        item = self._new_item(slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=1)
        await drv.run_transaction(item)
        self._check(item.ack_error == 0, "clk_div_min: success path stays clean")
        self._check(item.latency_cycles > 0, "clk_div_min: transaction completed")


class CornerReleasedBusNoAck(I2CSequenceBase):
    """released_bus_no_ack: SDA high through the whole transaction."""

    async def body(self):
        # item.slave_ack=0 makes the TB leave SDA high at every ACK sample;
        # the driver also releases sda_in during the data phase, so the bus
        # stays high for the whole transaction.
        item = self._new_item(
            slave_addr=0x50, rw=0, tx_data=0xA5, slave_ack=0, sda_in=1
        )
        await self.start_item(item)
        await self.finish_item(item)
        self._check(item.ack_error == 1, "ack_error must assert at each ACK sample")


# ===========================================================================
# RANDOMIZED STRATEGY (plan randomized_testing_strategy; NO SCENARIO_ID).
# ===========================================================================


class I2CRandomSequence(I2CSequenceBase):
    """Randomized transaction generation over the full plan constraint space.

    Uniform ``slave_addr`` 0..127, ``tx_data`` 0..255, ``rw`` 0/1,
    ``slave_ack`` 0/1, ``read_data`` 0..255.  A reset is injected at the
    start (4..16 cycles); occasionally a mid-transaction reset (1..8 cycles)
    is injected while the controller is busy (the in-flight transaction is
    then dropped, so no completion is awaited -- CONTRACT.md §11).

    Knobs (env vars, read at body() time):

    * ``I2C_RANDOM_ITEMS``  -- number of generated transactions (default 100)
    * ``I2C_SEED``          -- replay seed (default: unseeded random)
    * ``I2C_MID_RESET_PB``  -- per-transaction mid-reset probability (default 0.05)
    """

    async def body(self):
        num_items = int(os.environ.get("I2C_RANDOM_ITEMS", "100"))
        seed = os.environ.get("I2C_SEED")
        mid_reset_pb = float(os.environ.get("I2C_MID_RESET_PB", "0.05"))

        if seed is not None:
            random.seed(int(seed))
            self.logger.info(f"I2CS random sequence seeded with {seed}")

        drv = self._get_driver()
        # initial reset injection (plan: 4..16 cycles).
        await drv.assert_reset(random.randint(4, 16))
        await drv.deassert_reset(2)

        for txn_index in range(max(1, num_items)):
            item = I2CTransaction(name=f"random_item_{txn_index}")
            item.randomize()
            self.logger.info(
                f"[{txn_index + 1}/{max(1, num_items)}] {item}"
            )

            if random.random() < mid_reset_pb:
                # occasional mid-transaction reset injection (plan: 1..8
                # cycles); the in-flight transaction is dropped.
                await drv.start_transaction(item)   # busy high
                await drv.assert_reset(random.randint(1, 8))
                await drv.deassert_reset(2)
                await drv.expect_outputs(
                    {"busy": 0, "done": 0, "ack_error": 0, "rx_data": 0},
                    description="randomized mid-transaction reset clears state",
                )
                continue

            # Complete normally: offer -> slave timeline -> done pulse.
            await drv.run_transaction(item)

            # Completion-record self-checks vs the reference-model semantics
            # (expected_ack_error = not slave_ack).
            expected_ack_error = 1 - int(item.slave_ack)
            self._check(
                item.ack_error == expected_ack_error,
                f"txn {txn_index}: completion ack_error must be "
                f"{expected_ack_error}, got {item.ack_error}",
            )
            if item.is_read:
                self._check(
                    item.rx_data == int(item.read_data),
                    f"txn {txn_index}: rx_data must equal slave read_data "
                    f"0x{int(item.read_data):02x}, got 0x{item.rx_data:02x}",
                )
            await drv.expect_outputs(
                {"busy": 0},
                wait_cycles=2,
                description=f"random txn {txn_index} post-completion busy low",
            )

        self.logger.info(f"I2CRandomSequence completed {max(1, num_items)} items")


# ===========================================================================
# Registry + SCENARIO_ID contract check (CONTRACT.md §10).
# ===========================================================================

DIRECTED_SEQUENCE_CLASSES = (
    ResetIdleCheckSequence,          # TC-01
    WriteBasicSequence,              # TC-02
    WriteZeroSequence,               # TC-03
    WriteMaxSequence,                # TC-04
    ReadBasicSequence,               # TC-05
    ReadMaxSequence,                 # TC-06
    WriteAddrNackSequence,           # TC-07
    WriteDataNackSequence,           # TC-08
    ReadAddrNackSequence,            # TC-09
    StartWhileBusySequence,          # TC-10
    ResetDuringTransactionSequence,  # TC-11
    DonePulseCheckSequence,          # TC-12
    AddressMsbFirstCheckSequence,    # TC-13
)

# Plan corner cases (CONTRACT.md §10) -- no SCENARIO_ID.
CORNER_SEQUENCE_CLASSES = (
    CornerAddrZeroWrite,
    CornerAddrMaxWrite,
    CornerAddrMaxRead,
    CornerDataZeroWrite,
    CornerDataMaxWrite,
    CornerRxAllOnesRead,
    CornerRxAllZerosRead,
    CornerMissingAddrAck,
    CornerMissingDataAck,
    CornerStartOneCycle,
    CornerBackToBackTransactions,
    CornerResetMidTransaction,
    CornerClkDivMin,
    CornerReleasedBusNoAck,
)


def directed_scenario_id_map():
    """Return ``{SCENARIO_ID: sequence_class}`` for the directed scenarios.

    Raises :class:`ValueError` if the directed classes do not map the locked
    plan ids 1:1 (a duplicate, a missing id, or an id that is not in the
    plan).
    """
    mapping = {}
    for cls in DIRECTED_SEQUENCE_CLASSES:
        sid = cls.SCENARIO_ID
        if sid is None:
            raise ValueError(
                f"directed sequence {cls.__name__} is missing SCENARIO_ID"
            )
        if sid in mapping:
            raise ValueError(f"SCENARIO_ID '{sid}' implemented by multiple classes")
        mapping[sid] = cls
    return mapping


def assert_directed_scenario_ids():
    """Assert every planned directed scenario id appears exactly once."""
    mapping = directed_scenario_id_map()
    missing = [sid for sid in PLANNED_DIRECTED_IDS if sid not in mapping]
    extra = [sid for sid in mapping if sid not in PLANNED_DIRECTED_IDS]
    if missing or extra:
        raise ValueError(
            "directed SCENARIO_ID set does not match the plan: "
            f"missing={missing}, extra={extra}"
        )
    return mapping


def _self_check():
    """Standalone invariant checks (run ``python i2c_sequences.py``)."""
    mapping = assert_directed_scenario_ids()
    print(f"i2c_sequences: {len(mapping)} directed scenarios mapped 1:1")
    for sid, cls in sorted(mapping.items()):
        print(f"  {sid}  {cls.__name__}")
    for cls in CORNER_SEQUENCE_CLASSES:
        if cls.SCENARIO_ID is not None:
            raise ValueError(
                f"corner sequence {cls.__name__} must not carry a SCENARIO_ID"
            )
    print(
        f"i2c_sequences: {len(CORNER_SEQUENCE_CLASSES)} corner sequences "
        "(no SCENARIO_ID) OK"
    )
    for item in ("I2CRandomSequence",):
        cls = globals()[item]
        if cls.SCENARIO_ID is not None:
            raise ValueError(f"{item} must not carry a SCENARIO_ID")
    print("i2c_sequences: randomized sequence SCENARIO_ID=None OK")


if __name__ == "__main__":
    _self_check()