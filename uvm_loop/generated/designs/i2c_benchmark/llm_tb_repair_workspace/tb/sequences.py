"""Stage 2 (stimulus) artifact of the CHIA generator: pyuvm sequences.

This module implements the stimulus layer of the i2c_master bench:

* **Directed scenario sequences** -- one class per plan
  ``directed_test_scenarios[i].id`` (I2C_01 .. I2C_14).  Every directed
  class carries a class-level ``SCENARIO_ID`` whose value *exactly* matches
  its plan id, and the module verifies at import time that each plan id
  appears **exactly once** (``verify_directed_scenario_ids``).

* **Corner-case sequences** -- the plan ``corner_cases`` list (a separate
  verification strategy, therefore intentionally carrying **no**
  ``SCENARIO_ID``).

* **Randomized sequence** -- the plan ``randomized_testing_strategy``: a
  constrained-random, back-to-back stream of write/read transactions with
  rare reset-during-transaction injection, self-scored against the
  independent Python reference model.

Design rules honoured here (CONTRACT.md):

* Normal stimulus reaches the DUT exclusively through ``I2CDriver``:
  sequences send ``I2CTransaction`` items with ``start_item()`` /
  ``finish_item()``; the driver offers them exactly while idle.
* Two scenarios need cycle-exact stimulus and therefore poke the pins
  directly through the ConfigDB-shared ``I2CDutPins`` helper (the driver is
  parked on ``get_next_item`` during those windows, so no two coroutines
  ever drive the pins at once):
    - I2C_10 "Start While Busy Is Ignored" (must assert ``start`` *while*
      ``busy``, which the idle-gated driver is forbidden to do);
    - I2C_12 "Open-Drain Bus Release" (must sample scl/sda in the
      one-cycle START-like and access phases).
* Checks are plain-Python ``assert``-style checks that raise
  ``AssertionError`` and fail the enclosing cocotb test immediately.
* Functional coverage and always-running assertion checkers are later-stage
  artifacts; only lane-driving/self-checking coroutines are started here.
"""

import random

import cocotb
from cocotb.triggers import RisingEdge
from pyuvm import uvm_sequence, ConfigDB

from tb.dut_helper import KEY_DUT_PINS, _to_int
from tb.transaction import I2CTransaction, SUPPORTED_SLAVE_ADDR

# Reference model (independent oracle).  Depending on the run layout the
# repository root or the benchmark directory is on sys.path; try both.
try:
    from benchmarks.i2c_benchmark.i2c_reference_model import I2CReferenceModel
except ImportError:  # pragma: no cover - environment-dependent
    from i2c_reference_model import I2CReferenceModel

__all__ = [
    "I2CScenarioBase",
    "ResetBehaviorSeq",
    "WriteThenReadBackSeq",
    "ReadBeforeWriteSeq",
    "RepeatedWritesSeq",
    "BoundaryAddr00Seq",
    "BoundaryAddrFFSeq",
    "UnsupportedSlave00Seq",
    "UnsupportedSlave01Seq",
    "UnsupportedSlave7FSeq",
    "StartWhileBusySeq",
    "DonePulseWidthSeq",
    "OpenDrainBusReleaseSeq",
    "MultiRegIndependenceSeq",
    "BackToBackSeq",
    "CornerReadNeverWrittenSeq",
    "CornerAddr00BoundarySeq",
    "CornerAddrFFBoundarySeq",
    "CornerData00Seq",
    "CornerDataFFSeq",
    "CornerData55Seq",
    "CornerDataAASeq",
    "CornerUnsupported00Seq",
    "CornerUnsupported7FSeq",
    "CornerUnsupported01Seq",
    "CornerStartWhileBusySeq",
    "I2CRandomizedSequence",
    "DIRECTED_SEQUENCE_CLASSES",
    "CORNER_CASE_SEQUENCE_CLASSES",
    "RANDOMIZED_SEQUENCE_CLASS",
    "PLAN_DIRECTED_IDS",
    "verify_directed_scenario_ids",
]

# ---------------------------------------------------------------------------
# Cross-scenario consistency policy.
#
# Several scenarios assert that a register "has never been written":
#   I2C_03      reads reg 0x42, expects 0x00
#   I2C_10      reads reg 0x20, expects 0x00 (busy-time start was ignored)
#   corner      reads reg 0x2A, expects 0x00 (read-of-never-written)
# The RTL memory is *not* cleared by reset while the reference model's is
# (CONTRACT.md section 3).  To keep every expectation valid in *any* run
# order of the scenarios inside one simulation, those three addresses are
# reserved: the randomized sequence never *writes* to them (3 of 256
# addresses -- negligible constraint reduction).
# ---------------------------------------------------------------------------
RESERVED_NEVER_WRITTEN = frozenset({0x20, 0x2A, 0x42})

# Every planned directed scenario id (from plans/verification_plan.yaml).
PLAN_DIRECTED_IDS = (
    "I2C_01", "I2C_02", "I2C_03", "I2C_04", "I2C_05", "I2C_06", "I2C_07",
    "I2C_08", "I2C_09", "I2C_10", "I2C_11", "I2C_12", "I2C_13", "I2C_14",
)


def _config_get(key):
    """Read a ConfigDB entry from a sequence context.

    pyuvm's ``ConfigDB.get`` requires a ``uvm_component`` as its context;
    sequences are ``uvm_object``s.  The bench stores its shared objects
    globally (``ConfigDB().set(None, "*", KEY_..., value)``), so sequences
    read them through the ``uvm_root`` context, which resolves to exactly
    the same store.
    """
    return ConfigDB().get(None, "", key)


# ---------------------------------------------------------------------------
# Shared substrate for the scenario (directed + corner) sequences.
# ---------------------------------------------------------------------------
class I2CScenarioBase(uvm_sequence):
    """Common helpers for directed and corner-case scenario sequences."""

    #: Plan scenario id; None for corner-case sequences (by design).
    SCENARIO_ID = None

    RESET_CYCLES = 8          # plan: every scenario starts with an 8-cycle reset
    SETTLE_CYCLES = 2         # post-deassert settle edges
    DONE_TIMEOUT_CYCLES = 512 # bound for a hung transaction (see watchdog notes)

    def __init__(self, name="i2c_scenario_seq"):
        super().__init__(name)

    # ------------------------------------------------------------------
    # ConfigDB access
    # ------------------------------------------------------------------
    def _pins(self):
        """The shared ``I2CDutPins`` helper (CONTRACT.md key)."""
        return _config_get(KEY_DUT_PINS)

    # ------------------------------------------------------------------
    # Reset stimulus (structural signal; driven directly on the pins)
    # ------------------------------------------------------------------
    async def _reset(self, cycles=None):
        """Assert/release the active-low asynchronous reset.

        ``start`` (and the other stimulus pins) are held deasserted for the
        whole window; the DUT then settles in the reset/idle state (busy=0,
        done=0, ack_error=0, read_data=0x00, scl/sda released).
        """
        if cycles is None:
            cycles = self.RESET_CYCLES
        pins = self._pins()
        pins.release_inputs()
        pins.assert_reset()
        for _ in range(cycles):
            await RisingEdge(pins.clk)
        pins.deassert_reset()
        for _ in range(self.SETTLE_CYCLES):
            await RisingEdge(pins.clk)

    # ------------------------------------------------------------------
    # Transaction stimulus through the driver (normal path)
    # ------------------------------------------------------------------
    async def _do_tx(self, rw=0, slave_addr=SUPPORTED_SLAVE_ADDR, reg_addr=0,
                     write_data=0, tag="tx"):
        """Send one ``I2CTransaction`` via the sequencer to ``I2CDriver``.

        Returns after the driver has offered the request to the DUT (the
        latching edge has passed); the transaction is then in flight.
        """
        item = I2CTransaction(f"{self.get_name()}_{tag}")
        item.start = 1
        item.rw = rw
        item.slave_addr = slave_addr
        item.reg_addr = reg_addr
        item.write_data = write_data
        item.check_inputs_valid()
        await self.start_item(item)
        await self.finish_item(item)
        return item

    # ------------------------------------------------------------------
    # Transaction stimulus bypassing the driver (cycle-exact scenarios)
    # ------------------------------------------------------------------
    async def _direct_offer(self, rw=0, slave_addr=SUPPORTED_SLAVE_ADDR,
                            reg_addr=0, write_data=0):
        """Offer a transaction by poking the stimulus pins directly.

        Used only by scenarios whose stimulus must align with the FSM at
        cycle precision (I2C_10's busy-time start and I2C_12's bus-phase
        sampling).  In both scenarios the driver is guaranteed to be parked
        on ``get_next_item`` while this runs, so there is never concurrent
        pin driving.
        """
        pins = self._pins()
        clk = pins.clk
        # Wait for an idle edge, then offer on the following latch edge.
        while True:
            await RisingEdge(clk)
            if _to_int(pins.busy.value, 1) == 0:
                break
        pins.drive_inputs(start=1, rw=rw, slave_addr=slave_addr,
                          reg_addr=reg_addr, write_data=write_data)
        await RisingEdge(clk)      # latching edge
        pins.start.value = 0
        pins.release_inputs()

    # ------------------------------------------------------------------
    # Observation / checks
    # ------------------------------------------------------------------
    async def _wait_done(self):
        """Wait for the next ``done`` pulse and return its sampled outputs.

        Also verifies the pulse is exactly one clock cycle wide (done must
        be low on the following cycle), as asserted by the plan's
        completion-pulse semantics.
        """
        pins = self._pins()
        clk = pins.clk
        for _ in range(self.DONE_TIMEOUT_CYCLES):
            await RisingEdge(clk)
            outs = pins.sample_outputs()
            if outs["done"] == 1:
                # single-cycle width check
                await RisingEdge(clk)
                nxt = pins.sample_outputs()
                if nxt["done"] != 0:
                    raise AssertionError(
                        f"{self.get_name()}: done pulse wider than one cycle")
                return outs
        raise AssertionError(
            f"{self.get_name()}: timed out waiting for a done pulse "
            f"({self.DONE_TIMEOUT_CYCLES} cycles)")

    def _check(self, expect, sample=None, where=""):
        """Assert sampled outputs match the ``expect`` dict (plain-Python)."""
        pins = self._pins()
        if sample is None:
            sample = pins.sample_outputs()
        for key, want in expect.items():
            got = int(sample[key])
            if got != int(want):
                raise AssertionError(
                    f"{self.get_name()}: check failed {where}: {key} "
                    f"expected {int(want):#x}, got {got:#x}")
        return True

    def _check_bus_idle(self, where=""):
        """Both open-drain lines must be released (z or pulled up to 1)."""
        pins = self._pins()
        if not pins.scl_is_released() or not pins.sda_is_released():
            raise AssertionError(
                f"{self.get_name()}: bus not idle {where}: "
                f"scl={pins.scl_level()!r} sda={pins.sda_level()!r}")
        return True

    @staticmethod
    def _released(level):
        # Simulators may report a released open-drain line as "z" or "Z"
        # (lowered here, mirroring I2CDutPins.scl_is_released/sda_is_released);
        # "1" means a pull-up is applied in the environment.
        return str(level).lower() in ("z", "1")


# ===========================================================================
# Directed scenario sequences (plan directed_test_scenarios).
# ===========================================================================
class ResetBehaviorSeq(I2CScenarioBase):
    """I2C_01: Reset Behavior."""

    SCENARIO_ID = "I2C_01"

    def __init__(self, name="i2c_01_reset_behavior"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        self._check(
            {"busy": 0, "done": 0, "ack_error": 0, "read_data": 0},
            where="after reset",
        )
        self._check_bus_idle(where="after reset")


class WriteThenReadBackSeq(I2CScenarioBase):
    """I2C_02: Write Then Read Back (0xAA -> reg 0x10, read back)."""

    SCENARIO_ID = "I2C_02"

    def __init__(self, name="i2c_02_write_then_read_back"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        # write 0xAA to reg 0x10 on supported slave 0x50
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x10, write_data=0xAA)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "busy": 0, "done": 1}, sample,
                    where="write done")
        # read it back
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x10, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0xAA, "busy": 0, "done": 1},
                    sample, where="read done")
        self.logger.info("%s: read back 0xAA OK", self.get_name())


class ReadBeforeWriteSeq(I2CScenarioBase):
    """I2C_03: Read Before Write Returns Zero (reg 0x42, never written)."""

    SCENARIO_ID = "I2C_03"

    def __init__(self, name="i2c_03_read_before_write"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        # 0x42 is a reserved address: no scenario ever writes it (see
        # RESERVED_NEVER_WRITTEN above), so it returns 0x00.
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x42, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x00, "done": 1}, sample,
                    where="read never-written reg 0x42")


class RepeatedWritesSeq(I2CScenarioBase):
    """I2C_04: Repeated Writes to Same Register (last write wins)."""

    SCENARIO_ID = "I2C_04"

    def __init__(self, name="i2c_04_repeated_writes"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x08, write_data=0x55)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="first write")
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x08, write_data=0xAA)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="overwrite")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x08, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0xAA, "done": 1}, sample,
                    where="read back")


class BoundaryAddr00Seq(I2CScenarioBase):
    """I2C_05: Boundary Register Address 0x00 (write 0xFF, read back)."""

    SCENARIO_ID = "I2C_05"

    def __init__(self, name="i2c_05_boundary_addr_00"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x00, write_data=0xFF)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="write 0xFF")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x00, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0xFF, "done": 1}, sample,
                    where="read back 0xFF")


class BoundaryAddrFFSeq(I2CScenarioBase):
    """I2C_06: Boundary Register Address 0xFF (write 0x55, read back)."""

    SCENARIO_ID = "I2C_06"

    def __init__(self, name="i2c_06_boundary_addr_ff"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0xFF, write_data=0x55)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="write 0x55")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0xFF, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x55, "done": 1}, sample,
                    where="read back 0x55")


class UnsupportedSlave00Seq(I2CScenarioBase):
    """I2C_07: Unsupported Slave Address 0x00 (NACK behaviour)."""

    SCENARIO_ID = "I2C_07"

    def __init__(self, name="i2c_07_unsupported_slave_00"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x00, reg_addr=0x00, write_data=0x55)
        sample = await self._wait_done()
        self._check({"ack_error": 1, "busy": 0, "read_data": 0x00, "done": 1},
                    sample, where="unsupported write 0x00")


class UnsupportedSlave01Seq(I2CScenarioBase):
    """I2C_08: Unsupported Slave Address 0x01 (NACK read)."""

    SCENARIO_ID = "I2C_08"

    def __init__(self, name="i2c_08_unsupported_slave_01"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=1, slave_addr=0x01, reg_addr=0x10, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 1, "read_data": 0x00, "done": 1}, sample,
                    where="unsupported read 0x01")


class UnsupportedSlave7FSeq(I2CScenarioBase):
    """I2C_09: Unsupported Slave Address 0x7F (NACK write)."""

    SCENARIO_ID = "I2C_09"

    def __init__(self, name="i2c_09_unsupported_slave_7f"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x7F, reg_addr=0xFF, write_data=0xAA)
        sample = await self._wait_done()
        self._check({"ack_error": 1, "read_data": 0x00, "done": 1}, sample,
                    where="unsupported write 0x7F")


class StartWhileBusyFlowBase(I2CScenarioBase):
    """Shared body for the I2C_10 directed scenario and the identical
    "Start While Busy" corner case (kept separate, no SCENARIO_ID here)."""

    async def _start_while_busy_flow(self):
        pins = self._pins()
        clk = pins.clk
        await self._reset()

        # Count done pulses over the primary-transaction window; exactly
        # one is expected (the busy-time start must add none).
        done_pulse_counts = []

        async def _count_done():
            post_done = -1
            for _ in range(24):
                await RisingEdge(clk)
                done_pulse_counts.append(_to_int(pins.done.value, 1))
                if post_done >= 0:
                    post_done += 1
                    if post_done >= 2:
                        return
                elif done_pulse_counts[-1] == 1:
                    post_done = 0

        counter = cocotb.start_soon(_count_done())

        # Primary write of 0x11 to reg 0x10 (direct offer for exact timing).
        await self._direct_offer(rw=0, slave_addr=0x50, reg_addr=0x10,
                                 write_data=0x11)

        # The DUT asserts `busy` one clock cycle after the request-latching
        # edge, so wait for it to rise before asserting that the primary
        # write is in flight (and before poking the busy-time start).
        busy_seen = False
        for _ in range(8):
            await RisingEdge(clk)
            if _to_int(pins.busy.value, 1) == 1:
                busy_seen = True
                break
        if not busy_seen:
            raise AssertionError(
                f"{self.get_name()}: primary write did not go busy")

        # Assert a *second* request while the controller is busy.  The FSM
        # is in START_PHASE/ACCESS here, so `start` is ignored; only the
        # primary transaction may complete.
        pins.drive_inputs(start=1, rw=0, slave_addr=0x50, reg_addr=0x20,
                          write_data=0x22)
        await RisingEdge(clk)     # START_PHASE -> ACCESS
        await RisingEdge(clk)     # ACCESS -> STOP_PHASE
        pins.start.value = 0
        pins.release_inputs()

        sample = await self._wait_done()
        self._check({"ack_error": 0, "busy": 0, "done": 1}, sample,
                    where="primary done")
        await counter
        if sum(done_pulse_counts) != 1:
            raise AssertionError(
                f"{self.get_name()}: expected exactly one done pulse, "
                f"counted {sum(done_pulse_counts)} "
                f"(busy-time start must be ignored)")

        # Read reg 0x20: the busy-time start never landed -> 0x00.
        await self._direct_offer(rw=1, slave_addr=0x50, reg_addr=0x20,
                                 write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x00, "busy": 0, "done": 1},
                    sample, where="read reg 0x20")

        # Read reg 0x10: the primary write landed -> 0x11.
        await self._direct_offer(rw=1, slave_addr=0x50, reg_addr=0x10,
                                 write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x11, "busy": 0, "done": 1},
                    sample, where="read reg 0x10")
        self.logger.info("%s: busy-time start ignored; primary intact",
                         self.get_name())


class StartWhileBusySeq(StartWhileBusyFlowBase):
    """I2C_10: Start While Busy Is Ignored."""

    SCENARIO_ID = "I2C_10"

    def __init__(self, name="i2c_10_start_while_busy"):
        super().__init__(name)

    async def body(self):
        await self._start_while_busy_flow()


class DonePulseWidthSeq(I2CScenarioBase):
    """I2C_11: Done Pulse Width (one cycle; busy low while done)."""

    SCENARIO_ID = "I2C_11"

    def __init__(self, name="i2c_11_done_pulse_width"):
        super().__init__(name)

    async def body(self):
        pins = self._pins()
        clk = pins.clk
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x05, write_data=0x5A)

        # Find the done pulse and sample its full window.
        for _ in range(self.DONE_TIMEOUT_CYCLES):
            await RisingEdge(clk)
            outs = pins.sample_outputs()
            if outs["done"] == 1:
                break
        else:
            raise AssertionError(
                f"{self.get_name()}: no done pulse observed")
        if outs["busy"] != 0:
            raise AssertionError(
                f"{self.get_name()}: busy must be low while done is high "
                f"(busy={outs['busy']})")
        await RisingEdge(clk)
        nxt = pins.sample_outputs()
        if nxt["done"] != 0:
            raise AssertionError(
                f"{self.get_name()}: done stayed high beyond one cycle")
        self.logger.info("%s: done high exactly one cycle with busy low",
                         self.get_name())


class OpenDrainBusReleaseSeq(I2CScenarioBase):
    """I2C_12: Open-Drain Bus Release.

    Verifies, by sampling every cycle across a transaction window:
      * sda is driven low while scl stays released (START-like phase);
      * scl is driven low while sda stays released (access phase);
      * both lines are released again after completion.
    """

    SCENARIO_ID = "I2C_12"

    def __init__(self, name="i2c_12_open_drain_bus_release"):
        super().__init__(name)

    async def body(self):
        pins = self._pins()
        clk = pins.clk

        await self._reset()
        self._check_bus_idle(where="after reset")

        # Background sampler: scl/sda every cycle through the transaction,
        # plus 6 settle samples after the done pulse (capped at 40 edges).
        trace = []

        async def _sample_bus():
            post_done = -1
            for _ in range(40):
                await RisingEdge(clk)
                trace.append({
                    "scl": pins.scl_level(),
                    "sda": pins.sda_level(),
                    "busy": _to_int(pins.busy.value, 1),
                    "done": _to_int(pins.done.value, 1),
                })
                if post_done >= 0:
                    post_done += 1
                    if post_done >= 6:
                        return
                elif trace[-1]["done"] == 1:
                    post_done = 0

        sampler = cocotb.start_soon(_sample_bus())
        await self._do_tx(rw=0, slave_addr=SUPPORTED_SLAVE_ADDR, reg_addr=0x00,
                          write_data=0x00)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "busy": 0, "done": 1}, sample,
                    where="bus-release write done")
        await sampler

        # START-like phase: sda driven low, scl released.
        if not any(s["sda"] == "0" and self._released(s["scl"])
                   for s in trace):
            raise AssertionError(
                f"{self.get_name()}: never saw START-like phase "
                f"(sda low, scl released); trace={trace}")

        # Access phase: scl driven low, sda released.
        if not any(s["scl"] == "0" and self._released(s["sda"])
                   for s in trace):
            raise AssertionError(
                f"{self.get_name()}: never saw access phase "
                f"(scl low, sda released); trace={trace}")

        # After the completion pulse both lines are released again.
        done_idx = next((i for i, s in enumerate(trace) if s["done"] == 1),
                        None)
        if done_idx is None:
            raise AssertionError(
                f"{self.get_name()}: bus trace never saw done; trace={trace}")
        if not all(self._released(s["scl"]) and self._released(s["sda"])
                   for s in trace[done_idx:]):
            raise AssertionError(
                f"{self.get_name()}: bus lines not released after completion; "
                f"trace={trace}")

        self._check_bus_idle(where="after transaction completion")
        self.logger.info("%s: open-drain START/access/idle behaviour OK",
                         self.get_name())


class MultiRegIndependenceSeq(I2CScenarioBase):
    """I2C_13: Multi-Register Independence."""

    SCENARIO_ID = "I2C_13"

    def __init__(self, name="i2c_13_multi_reg_independence"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        for reg, data in ((0x01, 0x11), (0x02, 0x22), (0x03, 0x33)):
            await self._do_tx(rw=0, slave_addr=0x50, reg_addr=reg,
                              write_data=data)
            sample = await self._wait_done()
            self._check({"ack_error": 0, "done": 1}, sample,
                        where=f"write reg {reg:#04x}")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x02, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x22, "done": 1}, sample,
                    where="read reg 0x02")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x01, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x11, "done": 1}, sample,
                    where="read reg 0x01")


class BackToBackSeq(I2CScenarioBase):
    """I2C_14: Back-to-Back Transactions."""

    SCENARIO_ID = "I2C_14"

    def __init__(self, name="i2c_14_back_to_back"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x0A, write_data=0x12)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="first tx")
        # Start the read immediately after completion (driver re-offers as
        # soon as the DUT is idle again -- CONTRACT.md section 6).
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x0A, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x12, "done": 1}, sample,
                    where="back-to-back read")


# ===========================================================================
# Corner-case sequences (plan corner_cases; no SCENARIO_ID by design).
# ===========================================================================
class CornerReadNeverWrittenSeq(I2CScenarioBase):
    """Read of Never-Written Register -> 0x00 (reserved address 0x2A)."""

    def __init__(self, name="i2c_corner_read_never_written"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x2A, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x00, "done": 1}, sample,
                    where="corner read never-written 0x2A")


class CornerAddr00BoundarySeq(I2CScenarioBase):
    """Register Address 0x00 Boundary (write 0x00, read back)."""

    def __init__(self, name="i2c_corner_addr_00_boundary"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x00, write_data=0x00)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample,
                    where="corner write @0x00")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x00, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x00, "done": 1}, sample,
                    where="corner read @0x00")


class CornerAddrFFBoundarySeq(I2CScenarioBase):
    """Register Address 0xFF Boundary (write 0xFF, read back)."""

    def __init__(self, name="i2c_corner_addr_ff_boundary"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0xFF, write_data=0xFF)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample,
                    where="corner write @0xFF")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0xFF, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0xFF, "done": 1}, sample,
                    where="corner read @0xFF")


class CornerData00Seq(I2CScenarioBase):
    """Data Value 0x00 (write 0x00 to reg 0x2B, read back)."""

    def __init__(self, name="i2c_corner_data_00"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x2B, write_data=0x00)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="corner w0x00")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x2B, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x00, "done": 1}, sample,
                    where="corner r0x00")


class CornerDataFFSeq(I2CScenarioBase):
    """Data Value 0xFF (write 0xFF to reg 0x2C, read back)."""

    def __init__(self, name="i2c_corner_data_ff"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x2C, write_data=0xFF)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="corner w0xFF")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x2C, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0xFF, "done": 1}, sample,
                    where="corner r0xFF")


class CornerData55Seq(I2CScenarioBase):
    """Data Value 0x55 (write 0x55 to reg 0x2D, read back)."""

    def __init__(self, name="i2c_corner_data_55"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x2D, write_data=0x55)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="corner w0x55")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x2D, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0x55, "done": 1}, sample,
                    where="corner r0x55")


class CornerDataAASeq(I2CScenarioBase):
    """Data Value 0xAA (write 0xAA to reg 0x2E, read back)."""

    def __init__(self, name="i2c_corner_data_aa"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x50, reg_addr=0x2E, write_data=0xAA)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "done": 1}, sample, where="corner w0xAA")
        await self._do_tx(rw=1, slave_addr=0x50, reg_addr=0x2E, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 0, "read_data": 0xAA, "done": 1}, sample,
                    where="corner r0xAA")


class CornerUnsupported00Seq(I2CScenarioBase):
    """Unsupported Address 0x00 (write -> ack_error=1, read_data=0)."""

    def __init__(self, name="i2c_corner_unsupported_00"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x00, reg_addr=0x00, write_data=0x55)
        sample = await self._wait_done()
        self._check({"ack_error": 1, "read_data": 0x00, "done": 1}, sample,
                    where="corner unsupported 0x00")


class CornerUnsupported7FSeq(I2CScenarioBase):
    """Unsupported Address 0x7F (write -> ack_error=1, read_data=0)."""

    def __init__(self, name="i2c_corner_unsupported_7f"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=0, slave_addr=0x7F, reg_addr=0xFF, write_data=0xAA)
        sample = await self._wait_done()
        self._check({"ack_error": 1, "read_data": 0x00, "done": 1}, sample,
                    where="corner unsupported 0x7F")


class CornerUnsupported01Seq(I2CScenarioBase):
    """Unsupported Address 0x01 (read -> ack_error=1, read_data=0)."""

    def __init__(self, name="i2c_corner_unsupported_01"):
        super().__init__(name)

    async def body(self):
        await self._reset()
        await self._do_tx(rw=1, slave_addr=0x01, reg_addr=0x10, write_data=0)
        sample = await self._wait_done()
        self._check({"ack_error": 1, "read_data": 0x00, "done": 1}, sample,
                    where="corner unsupported 0x01")


class CornerStartWhileBusySeq(StartWhileBusyFlowBase):
    """Start While Busy (corner case; identical stimulus to I2C_10).

    Intentionally carries no ``SCENARIO_ID``: it is a separate corner-case
    strategy, not the directed scenario.
    """

    def __init__(self, name="i2c_corner_start_while_busy"):
        super().__init__(name)

    async def body(self):
        await self._start_while_busy_flow()


# ===========================================================================
# Randomized sequence (plan randomized_testing_strategy).
# ===========================================================================
class I2CRandomizedSequence(I2CScenarioBase):
    """Constrained-random back-to-back I2C transactions.

    Generates ``num_transactions`` randomized write/read transactions whose
    fields stay within the plan constraints (slave_addr 7-bit, reg_addr
    8-bit, write_data 8-bit, rw 1-bit), with the supported address ``0x50``
    appearing frequently.  After every transaction the sequence waits for
    the ``done`` pulse and scores the DUT outputs against the independent
    *reference model* (the same oracle the scoreboard uses).

    Every so often (``reset_injection_probability``) a reset is injected
    *while* a transaction is in flight, exactly as the plan describes:

      * the in-flight transaction is aborted (no ``done`` pulse follows),
      * the controller recovers to the reset/idle state,
      * the reference model is reset, and
      * the aborted transaction never participates in any comparison.

    Because the RTL memory survives reset while the model's does not
    (CONTRACT.md section 3), supported-slave reads are restricted to
    registers written *after* the most recent reset; this keeps every
    sampled read consistent with the (reset) reference model.  The reserved
    never-written registers (``RESERVED_NEVER_WRITTEN``) are never written.

    Self-scoring compares ``read_data`` only where the plan gives it defined
    semantics (supported reads and unsupported-address transactions), and
    never on supported writes (CONTRACT.md section 12 / stage-6 consistency
    pass) -- the same scope the scoreboard applies.
    """

    def __init__(self, name="i2c_randomized_seq", num_transactions=60,
                 reset_injection_probability=0.05, seed=None):
        super().__init__(name)
        self.num_transactions = int(num_transactions)
        self.reset_injection_probability = float(reset_injection_probability)
        self.seed = seed
        self.rng = random.Random(seed)
        self.model = None
        self._written = set()
        self._prev_rw = 0

    # ------------------------------------------------------------------
    # Random field generators (respect the plan constraints)
    # ------------------------------------------------------------------
    def _random_slave_addr(self):
        if self.rng.random() < 0.4:
            return SUPPORTED_SLAVE_ADDR
        return self.rng.randrange(0x00, 0x80)  # 0 .. 0x7F

    def _random_reg_addr(self):
        while True:
            reg = self.rng.randrange(0x00, 0x100)  # 0 .. 0xFF
            if reg not in RESERVED_NEVER_WRITTEN:
                return reg

    def _random_item(self, tag):
        """Build and validate one randomized I2CTransaction."""
        slave_addr = self._random_slave_addr()
        reg_addr = self._random_reg_addr()
        write_data = self.rng.randrange(0x00, 0x100)
        # rw alternates between reads and writes (mostly).
        rw = 1 - self._prev_rw if self.rng.random() < 0.7 \
            else self.rng.randrange(0, 2)
        if rw == 1 and slave_addr == SUPPORTED_SLAVE_ADDR and \
                not self._written:
            # Supported reads may only hit regs written since the last
            # reset; with none written, convert to a write.
            rw = 0
        elif rw == 1 and slave_addr == SUPPORTED_SLAVE_ADDR and \
                self.rng.random() < 0.8:
            reg_addr = self.rng.choice(sorted(self._written))
        self._prev_rw = rw

        item = I2CTransaction(tag)
        item.start = 1
        item.rw = rw
        item.slave_addr = slave_addr
        item.reg_addr = reg_addr
        item.write_data = write_data
        item.check_inputs_valid()
        return item

    # ------------------------------------------------------------------
    # Body
    # ------------------------------------------------------------------
    async def body(self):
        self.model = I2CReferenceModel()
        # deterministic starting point: bench reset + model reset together
        await self._reset()
        self.model.reset()
        self._written = set()
        self._prev_rw = 0

        for idx in range(self.num_transactions):
            if self.rng.random() < self.reset_injection_probability:
                await self._inject_reset_during_transaction(idx)
            else:
                await self._random_transaction(idx)

        # Leave the DUT idle: no transaction in flight.
        pins = self._pins()
        for _ in range(self.DONE_TIMEOUT_CYCLES):
            await RisingEdge(pins.clk)
            if _to_int(pins.busy.value, 1) == 0:
                break
        self.logger.info(
            "%s: completed %d transactions (seed=%r)",
            self.get_name(), self.num_transactions, self.seed)

    async def _random_transaction(self, idx):
        item = self._random_item(f"{self.get_name()}_tx{idx}")
        self.logger.info("%s: tx %d -> %s", self.get_name(), idx, item)

        await self.start_item(item)
        await self.finish_item(item)

        sample = await self._wait_done()
        if sample["done"] != 1:
            raise AssertionError(
                f"{self.get_name()}: tx {idx} produced no done pulse")
        if sample["busy"] != 0:
            raise AssertionError(
                f"{self.get_name()}: busy must return to 0 at done (tx {idx} "
                f"busy={sample['busy']})")

        # Score against the independent reference model.  read_data is only
        # a meaningful comparison for supported-address reads (model memory
        # value) and unsupported-address transactions (must be 0x00); it is
        # intentionally NOT compared for supported writes (the spec leaves
        # read_data during a write unspecified -- CONTRACT.md section 12 /
        # stage-6 consistency pass), exactly matching the scoreboard scope.
        expected = self.model.transact(
            item.rw, item.slave_addr, item.reg_addr, item.write_data)
        if sample["ack_error"] != expected["ack_error"]:
            raise AssertionError(
                f"{self.get_name()}: tx {idx} ack_error mismatch: got "
                f"{sample['ack_error']}, model {expected['ack_error']} "
                f"(slave_addr={item.slave_addr:#04x})")
        compare_read_data = (
            item.slave_addr != SUPPORTED_SLAVE_ADDR or item.rw == 1)
        if compare_read_data and sample["read_data"] != expected["read_data"]:
            raise AssertionError(
                f"{self.get_name()}: tx {idx} read_data mismatch: got "
                f"{sample['read_data']:#x}, model {expected['read_data']:#x} "
                f"({item})")

        if item.rw == 0 and item.slave_addr == SUPPORTED_SLAVE_ADDR:
            self._written.add(item.reg_addr)

    async def _inject_reset_during_transaction(self, idx):
        """Abort an in-flight randomized transaction with a mid-flight reset."""
        pins = self._pins()
        clk = pins.clk

        item = self._random_item(f"{self.get_name()}_inj{idx}")
        self.logger.info("%s: injecting reset during tx -> %s",
                         self.get_name(), item)
        await self.start_item(item)
        await self.finish_item(item)

        # Wait for the request to be accepted (transaction in progress).
        busy_seen = False
        for _ in range(8):
            await RisingEdge(clk)
            if _to_int(pins.busy.value, 1) == 1:
                busy_seen = True
                break
        if not busy_seen:
            raise AssertionError(
                f"{self.get_name()}: injection tx {idx} never went busy")

        # Assert the asynchronous reset for 2..4 cycles, then release.
        duration = self.rng.randint(2, 4)
        pins.assert_reset()
        for _ in range(duration):
            await RisingEdge(clk)
        pins.deassert_reset()
        for _ in range(4):
            await RisingEdge(clk)

        # The controller must have recovered to the reset/idle state.
        outs = pins.sample_outputs()
        if outs["busy"] != 0 or outs["done"] != 0 or outs["ack_error"] != 0:
            raise AssertionError(
                f"{self.get_name()}: controller did not recover after "
                f"reset injection ({outs})")

        # Reference model is cleared by this reset (CONTRACT.md section 3);
        # the aborted transaction is not scored (it produced no done pulse).
        self.model.reset()
        self._written = set()


# ===========================================================================
# Registries and scenario-id verification.
# ===========================================================================
DIRECTED_SEQUENCE_CLASSES = [
    ResetBehaviorSeq,          # I2C_01
    WriteThenReadBackSeq,      # I2C_02
    ReadBeforeWriteSeq,        # I2C_03
    RepeatedWritesSeq,         # I2C_04
    BoundaryAddr00Seq,         # I2C_05
    BoundaryAddrFFSeq,         # I2C_06
    UnsupportedSlave00Seq,     # I2C_07
    UnsupportedSlave01Seq,     # I2C_08
    UnsupportedSlave7FSeq,     # I2C_09
    StartWhileBusySeq,         # I2C_10
    DonePulseWidthSeq,         # I2C_11
    OpenDrainBusReleaseSeq,    # I2C_12
    MultiRegIndependenceSeq,   # I2C_13
    BackToBackSeq,             # I2C_14
]

CORNER_CASE_SEQUENCE_CLASSES = [
    CornerReadNeverWrittenSeq,
    CornerAddr00BoundarySeq,
    CornerAddrFFBoundarySeq,
    CornerData00Seq,
    CornerDataFFSeq,
    CornerData55Seq,
    CornerDataAASeq,
    CornerUnsupported00Seq,
    CornerUnsupported7FSeq,
    CornerUnsupported01Seq,
    CornerStartWhileBusySeq,
]

RANDOMIZED_SEQUENCE_CLASS = I2CRandomizedSequence


def verify_directed_scenario_ids():
    """Return {plan id -> sequence class}; raise if any plan id is missing
    or appears more than once (scenario IDs are the connecting identity
    between the plan and the generated bench)."""
    seen = {}
    for cls in DIRECTED_SEQUENCE_CLASSES:
        sid = getattr(cls, "SCENARIO_ID", None)
        if sid is None:
            raise AssertionError(
                f"{cls.__name__} is a directed sequence but has no "
                f"SCENARIO_ID")
        if sid not in PLAN_DIRECTED_IDS:
            raise AssertionError(
                f"{cls.__name__} carries unknown scenario id {sid!r}")
        if sid in seen:
            raise AssertionError(
                f"scenario id {sid} is implemented twice "
                f"({seen[sid].__name__} and {cls.__name__})")
        seen[sid] = cls
    missing = set(PLAN_DIRECTED_IDS) - set(seen)
    if missing:
        raise AssertionError(
            f"missing directed scenario ids: {sorted(missing)}")
    return seen


# Verified at import time so a plan/implementation drift fails loudly.
_DIRECTED_BY_ID = verify_directed_scenario_ids()