"""i2c_master UVM driver for the cocotb + pyuvm bench (stimulus stage).

Stage-2 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory; it is the authoritative convention record).

``I2CDriver`` is the *only* component that writes to the DUT pins.  It is a
pyuvm ``uvm_driver`` (CONTRACT.md §5) that consumes ``I2CTransaction`` items
from its ``seq_item_port`` in ``run_phase()`` and, additionally, exposes a
set of public async task methods that orchestrated (flow) sequences use to
realize the plan's directed scenarios (TC-01..TC-13), timed corner cases and
the randomized strategy.  The split is documented in CONTRACT.md §13.

Two usage modes:

1. Item mode (plain transactions): ``run_phase()`` calls
   ``drive_transaction(item)`` = offer -> accept (busy 0->1) -> slave-side
   ``sda_in`` timeline -> done (0->1) -> completion sample into the item.

2. Flow mode (timed scenarios): the sequence calls driver tasks directly --
   ``assert_reset`` / ``deassert_reset``, ``start_transaction``,
   ``drive_slave_response`` (with optional per-phase ACK overrides and a
   mid-transaction hook), ``run_transaction``, ``pulse_start_while_busy``,
   ``complete_transaction``, ``expect_outputs``, ``settle``.

Cocotb 2.1.0 public-API notes honored throughout (verified against the
cocotb-2.1.0 wheel):

* Triggers ``RisingEdge`` / ``ClockCycles`` from ``cocotb.triggers``.
* ``cocotb.start_soon`` for the armed done-pulse watcher (never
  deprecated ``cocotb.fork``).
* ``cocotb.simtime.get_sim_time("ns")`` for latency measurement (the 2.x
  documented location; ``cocotb.utils.get_sim_time`` is a 2.1.0 alias).
* Pin accesses go through the shared ``I2CPins`` helper (``pins.clk``,
  ``pins.drive_*``, ``pins.read_*``, ``pins.sample_into_item``) and use
  ``dut.<pin>.value`` semantics; ``cocotb.handle.ModifiableObject`` is never
  imported (removed from cocotb 2.1.0).
"""

import os

from cocotb import start_soon
from cocotb.simtime import get_sim_time
from cocotb.triggers import ClockCycles, RisingEdge
from pyuvm import ConfigDB, uvm_driver

from i2c_pins import (
    CLK_DIV_DEFAULT,
    DONE_TIMEOUT_CYCLES,
    I2C_CLK_PERIOD_NS,
    I2CPins,
    KEY_DUT,
    KEY_DUT_PINS,
    RESET_CYCLES,
    SCL_IN_IDLE,
    SDA_IN_IDLE,
    SETTLE_CYCLES,
    START_TIMEOUT_CYCLES,
)
from i2c_transaction import I2CTransaction

# ---------------------------------------------------------------------------
# ConfigDB key used to share the driver instance with flow (orchestrated)
# sequences.  This is a Stage-2 addition, recorded in CONTRACT.md §13.  The
# env/test stage sets it once in build_phase after constructing the driver:
#
#     ConfigDB().set(None, "*", KEY_I2C_DRIVER, self.driver)
# ---------------------------------------------------------------------------
KEY_I2C_DRIVER = "i2c_driver"

# ---------------------------------------------------------------------------
# Intended-protocol advance schedule (spec §5/§6 + reference model).  The
# DUT FSM advances every CLK_DIV system-clock cycles (spec §9); a single
# byte transaction takes about 21 advances.  These indices are used by
# ``drive_slave_response`` to place the slave-side sda_in samples ahead of
# the nominal sample edges and hold them across the edges:
#
#     advance  0 : acceptance (IDLE -> START_COND, busy rises)
#     advance  1 : START_COND -> SEND_ADDR
#     advance  2..9  : SEND_ADDR, 8 address bits (master drives)
#     advance 10 : ADDR_ACK  (address ACK sample point)
#     advance 11..18 : data phase (SEND_DATA for write / READ_DATA for read)
#     advance 19 : write DATA_ACK sample / read READ_ACK (master NACK)
#     advance 20 : STOP_COND (correct RTL pulses done here)
# ---------------------------------------------------------------------------
ADV_ACCEPT = 0
ADV_ADDR_ACK = 10
ADV_DATA_PHASE_START = 11
ADV_DATA_ACK = 19
ADV_STOP = 20


class I2CDriverTimeout(Exception):
    """A bounded stimulus wait elapsed (a hung transaction / hung start).

    Raised by the driver's bounded waits:

    * ``start_transaction`` -> busy did not rise (0->1) within
      :data:`START_TIMEOUT_CYCLES` of the start offer;
    * ``complete_transaction`` / the armed done watcher -> a done 0->1 edge
      did not occur within :data:`DONE_TIMEOUT_CYCLES` of acceptance.

    The as-shipped (corrupted) RTL provokes this for every data-path
    transaction (CONTRACT.md §7.3); later stages must translate it into a
    structured "hung transaction" report rather than swallowing it.
    """

    def __init__(self, stage, message, item=None):
        self.stage = stage      # "start-acceptance" | "done-pulse"
        self.message = message
        self.item = item
        item_str = f" item={item}" if item is not None else ""
        super().__init__(f"I2CDriverTimeout[{stage}]: {message}{item_str}")


class ScenarioCheckFailure(Exception):
    """A plan ``expect`` action did not hold (scenario-level check).

    Raised by ``expect_outputs`` when a sampled DUT output differs from the
    value the directed/corner scenario's ``expect`` action requires.  This is
    a stimulus-stage scenario expectation (CONTRACT.md §13), distinct from
    the always-running protocol checker coroutines the checking stage adds.
    """

    def __init__(self, message, expected=None, observed=None):
        self.expected = expected or {}
        self.observed = observed or {}
        super().__init__(message)


class I2CDriver(uvm_driver):
    """Drives every i2c_master DUT pin from ``I2CTransaction`` items.

    Reads the shared ``dut`` and ``I2CPins`` handles from ConfigDB under the
    exact keys ``"dut"`` / ``"i2c_pins"`` (CONTRACT.md §6; keys are set by
    ``test_top.py`` before the pyuvm tree is built).
    """

    def build_phase(self):
        super().build_phase()
        self.dut = ConfigDB().get(None, "", KEY_DUT)
        self.pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        if not isinstance(self.pins, I2CPins):
            self.logger.warning(
                f"ConfigDB['{KEY_DUT_PINS}'] is not an I2CPins: {self.pins!r}"
            )
        # CLK_DIV is a DUT parameter; the TB runs with the default unless a
        # worker override feeds I2C_CLK_DIV.  The stimulus timeline adapts to
        # this cadence (one FSM advance per CLK_DIV cycles).
        self.clk_div = int(os.environ.get("I2C_CLK_DIV", CLK_DIV_DEFAULT))
        if self.clk_div < 1:
            self.clk_div = CLK_DIV_DEFAULT
        self.clk_period_ns = float(
            os.environ.get("I2C_CLK_PERIOD_NS", I2C_CLK_PERIOD_NS)
        )
        # Simulation time (ns) of the last accepted transaction's busy-rise
        # edge; used to measure latency_cycles (acceptance -> done pulse).
        self._accept_ns = None
        self.logger.info(
            f"i2c_driver ready (clk_div={self.clk_div}, "
            f"clock_period={self.clk_period_ns} ns)"
        )

    # ------------------------------------------------------------------
    # run_phase: item mode (plain sequence items via the sequencer)
    # ------------------------------------------------------------------
    async def run_phase(self):
        """Pull ``I2CTransaction`` items and execute each fully.

        A bounded-wait expiry is surfaced loudly: the requesting sequence is
        unblocked (``item_done``) and the exception is re-raised so the test
        fails with a hung-transaction report rather than a silent stall.
        """
        while True:
            item = await self.seq_item_port.get_next_item()
            try:
                await self.drive_transaction(item)
            except I2CDriverTimeout:
                self.seq_item_port.item_done()
                self.logger.error(f"hung transaction: {item}")
                raise
            self.seq_item_port.item_done()

    # ------------------------------------------------------------------
    # Public: complete single-transaction flow (used by run_phase and by
    # flow sequences that want the whole thing in one call)
    # ------------------------------------------------------------------
    async def drive_transaction(self, item):
        """Execute one full transaction for *item* (offer -> ... -> done)."""
        await self.start_transaction(item)
        done_task = start_soon(self._wait_done_edge(item, DONE_TIMEOUT_CYCLES))
        await self.drive_slave_response(item)
        await done_task
        self._record_completion(item)

    async def run_transaction(
        self,
        item,
        *,
        addr_ack=None,
        data_ack=None,
        mid_transaction=None,
    ):
        """Flow-sequence convenience: offer, slave timeline, done, record.

        ``addr_ack`` / ``data_ack`` optionally override the item's
        ``slave_ack`` per ACK phase (plan TC-08, corner case
        ``missing_data_ack``); ``mid_transaction`` is an optional async
        callable invoked right after the address-ACK window (plan TC-10).
        """
        await self.start_transaction(item)
        done_task = start_soon(self._wait_done_edge(item, DONE_TIMEOUT_CYCLES))
        await self.drive_slave_response(
            item,
            addr_ack=addr_ack,
            data_ack=data_ack,
            mid_transaction=mid_transaction,
        )
        await done_task
        self._record_completion(item)

    # ------------------------------------------------------------------
    # Public: structural reset tasks (plan actions reset/deassert_reset)
    # ------------------------------------------------------------------
    async def assert_reset(self, hold_cycles=RESET_CYCLES):
        """Assert the active-low synchronous reset for *hold_cycles* edges.

        Mirrors the plan's ``reset`` action (``rst_n: 0`` for N cycles).
        """
        self.pins.assert_reset()
        await ClockCycles(self.pins.clk, max(1, int(hold_cycles)))
        self.logger.info(f"reset asserted for {max(1, int(hold_cycles))} cycles")

    async def deassert_reset(self, settle_cycles=SETTLE_CYCLES):
        """Deassert the reset and wait *settle_cycles* rising edges.

        Mirrors the plan's ``deassert_reset`` action (``rst_n: 1`` and wait).
        """
        self.pins.deassert_reset()
        await ClockCycles(self.pins.clk, max(1, int(settle_cycles)))
        self.logger.info(f"reset deasserted, settled {max(1, int(settle_cycles))} cycles")

    async def reset_phase(
        self,
        hold_cycles=RESET_CYCLES,
        settle_cycles=SETTLE_CYCLES,
    ):
        """Convenience: assert reset for *hold_cycles*, then deassert settle."""
        await self.assert_reset(hold_cycles)
        await self.deassert_reset(settle_cycles)

    async def settle(self, cycles=SETTLE_CYCLES):
        """Idle the bus for *cycles* rising edges (no pin changes)."""
        await ClockCycles(self.pins.clk, max(1, int(cycles)))

    # ------------------------------------------------------------------
    # Public: transaction-offer flow (plan actions start_write/start_read,
    # release_start)
    # ------------------------------------------------------------------
    async def start_transaction(self, item, offer_cycles=1):
        """Offer *item*'s start request and wait (bounded) for acceptance.

        Drives ``start=1`` together with the item's address/direction/data
        pins for ``offer_cycles`` rising edges, then releases ``start`` (the
        plan's ``release_start`` action).  Acceptance = ``busy`` rising 0->1
        (CONTRACT.md §7.1); returns the number of clock cycles spent waiting
        for the busy rise.  Raises :class:`I2CDriverTimeout` if busy never
        rises within :data:`START_TIMEOUT_CYCLES`.
        """
        item.check_inputs_valid()
        self.logger.info(f"offer: {item}")
        self.pins.drive_transaction(item)  # start=1 plus addr/rw/tx/sda/scl
        await ClockCycles(self.pins.clk, max(1, int(offer_cycles)))
        self.pins.drive_start(0)           # release_start
        cycles = await self._wait_busy_rise(START_TIMEOUT_CYCLES, item)
        self._accept_ns = get_sim_time("ns")
        self.logger.info(
            f"transaction accepted (busy 0->1) after {cycles} clock cycles"
        )
        return cycles

    # ------------------------------------------------------------------
    # Public: slave-side sda_in timeline (plan actions drive_ack /
    # drive_nack / drive_byte)
    # ------------------------------------------------------------------
    async def drive_slave_response(
        self,
        item,
        *,
        addr_ack=None,
        data_ack=None,
        mid_transaction=None,
    ):
        """Present the TB-slave's ``sda_in`` waveform for the busy transaction.

        The item is assumed to have been accepted (``busy`` high).  The
        schedule below drives ``sda_in`` approximately one FSM advance
        (``CLK_DIV`` clock cycles) before each nominal sample edge and holds
        it across the edge, so a DUT that advances on the nominal cadence
        samples the intended level.  This is an *estimative* timeline, not a
        locked cycle contract -- completion is still keyed on the done pulse
        (CONTRACT.md §7).

        :param item: the ``I2CTransaction`` being executed.
        :param addr_ack: optional 0/1 override of ``item.slave_ack`` for the
            address-ACK phase only.
        :param data_ack: optional 0/1 override of ``item.slave_ack`` for the
            write-data-ACK phase only (read transactions have no slave
            data-ACK; after the read byte the master NACKs).
        :param mid_transaction: optional ``async def hook(driver)`` invoked
            right after the address-ACK window (used by plan TC-10's illegal
            start-while-busy assertion and by randomized mid-resets).
        """
        ack_level = 0 if int(item.slave_ack) else 1
        addr_ack_level = ack_level if addr_ack is None else (0 if int(addr_ack) else 1)
        data_ack_level = ack_level if data_ack is None else (0 if int(data_ack) else 1)
        cdiv = max(1, int(self.clk_div))

        # Address transmission window (advances 1..9): the master drives SDA;
        # the TB (slave) leaves the line released high.
        await ClockCycles(self.pins.clk, 8 * cdiv)
        # Present the address-ACK level a full advance ahead of the nominal
        # ADDR_ACK sample and hold it across the sample edge.
        self.pins.drive_sda_in(addr_ack_level)
        await ClockCycles(self.pins.clk, cdiv)
        self.logger.info(f"address ACK level presented: sda_in={addr_ack_level}")
        await ClockCycles(self.pins.clk, cdiv)  # nominal ADDR_ACK sample edge

        # Optional mid-transaction stimulus (TC-10 spur, random mid-resets).
        if mid_transaction is not None:
            await mid_transaction(self)

        if item.is_read:
            # READ_DATA advances 11..18: slave drives read_data MSB first.
            for i in range(8):
                bit = (int(item.read_data) >> (7 - i)) & 1
                self.pins.drive_sda_in(bit)
                await ClockCycles(self.pins.clk, cdiv)
            # Advance 19 READ_ACK (master NACK): slave releases SDA high.
            self.pins.drive_sda_in(SDA_IN_IDLE)
            await ClockCycles(self.pins.clk, cdiv)  # nominal READ_ACK edge
            await ClockCycles(self.pins.clk, cdiv)  # advance 20 STOP
        else:
            # SEND_DATA advances 11..18: master drives; slave releases.
            self.pins.drive_sda_in(SDA_IN_IDLE)
            await ClockCycles(self.pins.clk, 7 * cdiv)
            # Present the write-data ACK level before the nominal DATA_ACK
            # sample and hold it across the edge.
            self.pins.drive_sda_in(data_ack_level)
            await ClockCycles(self.pins.clk, cdiv)
            self.logger.info(f"write-data ACK level presented: sda_in={data_ack_level}")
            await ClockCycles(self.pins.clk, cdiv)  # nominal DATA_ACK edge
            await ClockCycles(self.pins.clk, cdiv)  # advance 20 STOP
        # Release the bus for the STOP/IDLE window.
        self.pins.drive_sda_in(SDA_IN_IDLE)

    # ------------------------------------------------------------------
    # Public: completion flow (plan action wait_for_done)
    # ------------------------------------------------------------------
    async def complete_transaction(self, item):
        """Wait for the done 0->1 pulse (armed), then record the item.

        Use when the done watcher was not already armed by
        ``run_transaction``/``drive_transaction`` (e.g. the randomized
        sequence arms it through ``drive_slave_response``+a parallel watcher,
        or a directed flow has already driven the timeline and now only wants
        the completion wait).
        """
        done_task = start_soon(self._wait_done_edge(item, DONE_TIMEOUT_CYCLES))
        await done_task
        self._record_completion(item)

    async def _wait_done_edge(self, item, timeout_cycles=DONE_TIMEOUT_CYCLES):
        """Wait for a done 0->1 edge within *timeout_cycles*; else timeout.

        Armed only after acceptance (CONTRACT.md §7.3).  On the as-shipped
        RTL ``done`` is permanently high after reset, so no 0->1 edge ever
        occurs after acceptance and this raises :class:`I2CDriverTimeout`
        (the bounded "hung transaction" report).
        """
        cycles = 0
        while cycles < timeout_cycles:
            prev = self.pins.read_done()
            await RisingEdge(self.pins.clk)
            cycles += 1
            cur = self.pins.read_done()
            if cur == 1 and prev == 0:
                return cycles
        raise I2CDriverTimeout(
            stage="done-pulse",
            message=(
                f"no done 0->1 pulse within {timeout_cycles} cycles after "
                "start acceptance (transaction hung on the DUT)"
            ),
            item=item,
        )

    def _record_completion(self, item):
        """Sample the completion-point outputs into *item* and set latency.

        ``sample_outputs_strict()`` rejects X/Z at the completion point
        (CONTRACT.md §3.4) before ``sample_into_item`` coerces them.
        """
        self.pins.sample_outputs_strict()
        self.pins.sample_into_item(item)
        if self._accept_ns is not None:
            now_ns = get_sim_time("ns")
            item.latency_cycles = max(
                0, int(round((now_ns - self._accept_ns) / self.clk_period_ns))
            )
        self.logger.info(f"completion sampled: {item}")

    # ------------------------------------------------------------------
    # Public: illegal (mid-transaction) start pulse (plan TC-10)
    # ------------------------------------------------------------------
    async def pulse_start_while_busy(self, item, hold_cycles=1):
        """Assert a second ``start`` request while a transaction is active.

        Drives ``start=1`` (with the given item's address/direction/data
        fields) for ``hold_cycles`` rising edges, then releases it.  Used to
        verify that a start offered while ``busy`` is ignored (spec §7 /
        plan TC-10).  The driver does not wait for acceptance here.
        """
        item.check_inputs_valid()
        self.logger.info(
            f"pulsing start while busy (must be ignored): {item}"
        )
        self.pins.drive_transaction(item)
        await ClockCycles(self.pins.clk, max(1, int(hold_cycles)))
        self.pins.drive_start(0)

    # ------------------------------------------------------------------
    # Public: plan action ``expect`` -- sample outputs and require values
    # ------------------------------------------------------------------
    async def expect_outputs(
        self,
        expected,
        *,
        wait_cycles=0,
        description="",
    ):
        """Sample the DUT status outputs and require *expected* values.

        *expected* maps output pin names (``busy``, ``done``, ``ack_error``,
        ``rx_data``) to required ints.  Optionally wait *wait_cycles* rising
        edges first (the plan's ``cycles`` field on expect actions).  Raises
        :class:`ScenarioCheckFailure` on a mismatch.
        """
        if int(wait_cycles) > 0:
            await ClockCycles(self.pins.clk, int(wait_cycles))
        outs = self.pins.sample_outputs()
        mismatches = {}
        for name, want in expected.items():
            if name not in outs:
                raise ValueError(
                    f"expect_outputs: '{name}' is not a DUT status output; "
                    f"valid names: {sorted(outs)}"
                )
            want = int(want)
            got = int(outs[name])
            if got != want:
                mismatches[name] = (want, got)
        if mismatches:
            detail = ", ".join(
                f"{name}: expected {w}, got {g}"
                for name, (w, g) in sorted(mismatches.items())
            )
            where = f" ({description})" if description else ""
            raise ScenarioCheckFailure(
                message=(
                    f"scenario expect check failed{where}: {detail}; "
                    f"full sample: {outs}"
                ),
                expected={n: w for n, (w, _g) in mismatches.items()},
                observed={n: g for n, (_w, g) in mismatches.items()},
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _wait_busy_rise(self, timeout_cycles, item=None):
        """Wait until ``busy`` reads 1 after a rising edge; bounded."""
        cycles = 0
        while cycles < timeout_cycles:
            await RisingEdge(self.pins.clk)
            cycles += 1
            if self.pins.read_busy():
                return cycles
        raise I2CDriverTimeout(
            stage="start-acceptance",
            message=(
                f"busy never rose (0->1) within {timeout_cycles} cycles of "
                "the start offer; the DUT did not accept the transaction "
                "(hung start)"
            ),
            item=item,
        )