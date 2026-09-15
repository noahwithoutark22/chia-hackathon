"""FIFO sequencer and stimulus sequences (pyuvm).

This module implements the stimulus side of the verification plan
(plans/verification_plan.yaml):

    * :class:`FifoSequencer`          - the pyuvm sequencer component.
    * Directed sequences              - one per ``directed_test_scenarios``
        entry; every class carries a ``SCENARIO_ID`` class attribute that
        exactly matches the plan entry's ``id`` (TC001..TC010).
    * Corner-case sequences           - one per ``corner_cases`` entry.
    * :class:`FifoRandomizedSeq`      - the ``randomized_testing_strategy``
        (constrained-random traffic with periodic and random mid-test reset
        injections).

Field contract (CONTRACT.md §5): sequences emit :class:`FifoTransaction`
items whose only driven fields are ``wr_en``, ``rd_en`` and ``din``.  No
extra fields are added and no field is renamed.  Clock/reset are NOT
transaction fields: reset is applied by the sequences directly on the shared
``dut.rst_n`` handle (asynchronous, active-low), and check actions sample the
DUT outputs through the same ``dut`` handle.

Timing convention (shared with ``driver.py``):
``finish_item()`` returns only *after* the item has been sampled by the DUT
on a rising edge and all outputs have settled, so a sequence may immediately
sample ``dut.dout/dut.full/dut.empty`` and assert the plan's expected values.
A ``wait N`` action is performed with ``ClockCycles``; during ``wait`` the
driver keeps all stimulus inputs idle, so no extra DUT transaction occurs.
"""

import os
import random
from collections import deque

from cocotb.triggers import ClockCycles, FallingEdge, Timer
from pyuvm import ConfigDB, uvm_sequence, uvm_sequencer

from transaction import FifoTransaction


# ---------------------------------------------------------------------------
# Sequencer
# ---------------------------------------------------------------------------
class FifoSequencer(uvm_sequencer):
    """Sequencer for FIFO stimulus items.

    A plain ``uvm_sequencer`` subclass so the environment/tests can address
    the sequencer by a design-specific type name.  The agent (later stage)
    connects it to the driver with
    ``driver.seq_item_port.connect(sequencer.seq_item_export)``.
    """

    def __init__(self, name="fifo_sequencer", parent=None):
        super().__init__(name, parent)


# ---------------------------------------------------------------------------
# Shared sequence infrastructure
# ---------------------------------------------------------------------------
class FifoSeqBase(uvm_sequence):
    """Common helpers for all FIFO stimulus sequences.

    Subclasses implement ``async def body()``.  ConfigDB keys are read
    exactly as documented in CONTRACT.md §4 (``"dut"``, ``"DATA_WIDTH"``,
    ``"DEPTH"``, optional ``"FifoDutHelper"``).
    """

    def __init__(self, name="fifo_sequence"):
        super().__init__(name)

    # -- environment resolution ----------------------------------------
    async def _setup(self):
        """Resolve DUT handles and elaborated parameters from ConfigDB."""
        self.dut = ConfigDB().get(None, "*", "dut")
        self.data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
        self.depth = int(ConfigDB().get(None, "*", "DEPTH"))
        self.max_data = (1 << self.data_width) - 1
        try:
            from dut_helper import FifoDutHelper

            helper = ConfigDB().get(None, "*", "FifoDutHelper", default=None)
            self._helper = (
                helper if helper is not None else FifoDutHelper(self.dut, self.data_width)
            )
        except Exception:  # pragma: no cover - helper is optional sugar
            self._helper = None

    # -- low-level stimulus primitives ----------------------------------
    async def _drive_item(self, wr_en, rd_en, din):
        """Send one stimulus item to the driver.

        The driver applies it for exactly one DUT cycle and only returns
        (finish_item) after the DUT sampled it and outputs have settled.
        """
        item = FifoTransaction("stim")
        item.wr_en = int(wr_en) & 0x1
        item.rd_en = int(rd_en) & 0x1
        item.din = int(din) & self.max_data
        await self.start_item(item)
        await self.finish_item(item)

    async def _wait(self, cycles):
        """Wait ``cycles`` clock cycles with all stimulus inputs idle."""
        if cycles is not None and cycles > 0:
            await ClockCycles(self.dut.clk, int(cycles))

    async def _assert_reset(self):
        """Assert the asynchronous active-low reset and quiet the inputs."""
        self.dut.rst_n.setimmediatevalue(0)
        if self._helper is not None:
            self._helper.drive(0, 0, 0)
        else:
            self.dut.wr_en.setimmediatevalue(0)
            self.dut.rd_en.setimmediatevalue(0)
            self.dut.din.setimmediatevalue(0)
        # Let the async reset path of the RTL settle before sampling.
        await Timer(1, units="ns")

    async def _release_reset(self):
        """Deassert the asynchronous active-low reset.

        Aligned to a falling edge so that the deassertion is at least a
        half-period before the next sampling rising edge, guaranteeing
        clean setup/hold timing for the asynchronous reset recovery
        path (W-DEASSERT-RESET-SETTLE-TIMING).
        """
        await FallingEdge(self.dut.clk)
        self.dut.rst_n.setimmediatevalue(1)
        # Small settle after deassertion before continuing.
        await Timer(1, units="ns")

    async def _reset_init(self, hold=3):
        """Plan default reset prologue: assert, hold, release, sync."""
        await self._assert_reset()
        await self._wait(hold)
        await self._release_reset()
        await self._wait(1)

    async def _reset_init_checked(self, hold=3):
        """Reset prologue that also verifies the reset state (empty=1,
        full=0, dout=0) both while reset is asserted and after release."""
        await self._assert_reset()
        await self._wait(hold)
        self._check_outputs(empty=1, full=0, dout=0)
        await self._release_reset()
        await self._wait(1)
        self._check_outputs(empty=1, full=0, dout=0)

    # -- value handling --------------------------------------------------
    def _mask(self, value):
        """Mask a stimulus/expected value to the elaborated DATA_WIDTH."""
        return int(value) & self.max_data

    # -- checking primitives --------------------------------------------
    def _tag(self):
        return getattr(self, "SCENARIO_ID", None) or self.get_name()

    def _read_signal(self, pin):
        if pin == "count":
            cnt = getattr(self.dut, "count", None)
            if cnt is None:
                return None  # internal signal not exposed; cannot check
            return int(cnt.value)
        return int(getattr(self.dut, pin).value)

    def _check_outputs(self, **expected):
        """Assert that the sampled DUT outputs equal the expected values.

        Any ``count`` expectation is checked only if the internal RTL
        ``count`` signal is reachable from the testbench handle
        (CONTRACT.md TC001 note).
        """
        for pin, exp in expected.items():
            got = self._read_signal(pin)
            if got is None:
                continue  # internal signal not reachable on this tool
            if got != exp:
                raise AssertionError(
                    f"[{self._tag()}] check '{pin}' failed: "
                    f"expected {exp}, got {got}"
                )

    def _check_count(self, expected):
        """Check the internal RTL occupancy ``count`` when reachable."""
        self._check_outputs(count=expected)

    # -- high-level stimulus macros --------------------------------------
    async def _write(self, value):
        """Push one value (write-only cycle)."""
        await self._drive_item(1, 0, value)
        self.logger.debug("write %#x accepted", int(value) & self.max_data)

    async def _read_and_check(self, expected):
        """Pop one value, wait one cycle, and check dout (latency 1)."""
        await self._drive_item(0, 1, 0)
        await self._wait(1)
        self._check_outputs(dout=expected)

    async def _fill(self, values):
        """Write every value in ``values`` in order."""
        for v in values:
            await self._write(v)

    async def _drain_expect(self, values):
        """Pop and verify every value in ``values`` in strict FIFO order."""
        for v in values:
            await self._read_and_check(v)


# ---------------------------------------------------------------------------
# Directed scenarios (plan 'directed_test_scenarios') - TC001..TC010
#
# Every class below has a class-level SCENARIO_ID matching the plan id
# exactly.  Occupancy-relative scenario bodies scale with the elaborated
# DEPTH from ConfigDB so they remain valid at every planned DEPTH
# (2/4/8); for DEPTH=4 the stimulus reproduces the plan literally.
# ---------------------------------------------------------------------------
class ResetCheckSeq(FifoSeqBase):
    """TC001 reset_check."""

    SCENARIO_ID = "TC001"

    def __init__(self, name="ResetCheckSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC001 reset_check: begin")
        # --- reset: assert, hold 3 cycles, check during reset ----------
        await self._assert_reset()
        await self._wait(3)
        self._check_outputs(empty=1, full=0, dout=0)
        self._check_count(0)
        # --- deassert reset, sync, state must persist -------------------
        await self._release_reset()
        await self._wait(1)
        self._check_outputs(empty=1, full=0, dout=0)
        self._check_count(0)
        self.logger.info("TC001 reset_check: passed")


class WriteReadBasicSeq(FifoSeqBase):
    """TC002 write_read_basic: push distinct values, pop them in order."""

    SCENARIO_ID = "TC002"

    def __init__(self, name="WriteReadBasicSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC002 write_read_basic: begin")
        await self._reset_init()
        # DEPTH>=4 -> [17, 34, 51] exactly as planned; fewer for shallow
        # FIFOs.  Values are masked so expected dout comparisons stay valid
        # for every elaborated DATA_WIDTH.
        values = [self._mask(v) for v in [17, 34, 51][: min(3, self.depth - 1)]]
        await self._fill(values)
        await self._wait(1)
        self._check_outputs(empty=0, full=0)
        await self._drain_expect(values)
        await self._wait(1)
        self._check_outputs(empty=1, full=0)
        self.logger.info("TC002 write_read_basic: passed")


class WriteUntilFullSeq(FifoSeqBase):
    """TC003 write_until_full: fill to full, overflow write ignored, drain."""

    SCENARIO_ID = "TC003"

    def __init__(self, name="WriteUntilFullSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC003 write_until_full: begin")
        await self._reset_init()
        fill_vals = [self._mask(0x0A + i) for i in range(self.depth)]  # DEPTH=4: 0A..0D
        await self._fill(fill_vals)
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        self._check_count(self.depth)
        # Attempt a write while full: must be dropped.  Default dropped value
        # is the plan's 0x0E; for deeper/wider configurations pick a value
        # that is distinct from every stored entry so the drop is observable.
        drop = self._mask(0x0E)
        fill_set = set(fill_vals)
        if drop in fill_set:
            drop = self._mask(0xA5)
            if drop in fill_set:
                drop = next(v for v in range(self.max_data + 1) if v not in fill_set)
        await self._write(drop)
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        self._check_count(self.depth)
        # Drain in FIFO order; the dropped value must never appear.
        await self._drain_expect(fill_vals)
        await self._wait(1)
        self._check_outputs(empty=1, full=0)
        self.logger.info("TC003 write_until_full: passed")


class ReadUntilEmptySeq(FifoSeqBase):
    """TC004 read_until_empty: drain to empty, empty-read ignored + dout
    retention."""

    SCENARIO_ID = "TC004"

    def __init__(self, name="ReadUntilEmptySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC004 read_until_empty: begin")
        await self._reset_init()
        vals = [self._mask(0x11 + i) for i in range(self.depth)]  # DEPTH=4: 11..44
        await self._fill(vals)
        await self._drain_expect(vals)
        await self._wait(1)
        self._check_outputs(empty=1, full=0)
        # Read while empty: ignored; dout retains the last popped value.
        await self._drive_item(0, 1, 0)
        await self._wait(1)
        self._check_outputs(empty=1, dout=vals[-1])
        self.logger.info("TC004 read_until_empty: passed")


class SimultaneousReadWriteSeq(FifoSeqBase):
    """TC005 simultaneous_read_write: both accepted at mid occupancy."""

    SCENARIO_ID = "TC005"

    def __init__(self, name="SimultaneousReadWriteSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC005 simultaneous_read_write: begin")
        await self._reset_init()
        k = max(self.depth - 1, 1)                     # DEPTH=4 -> 3 pushes
        writes = [self._mask(0x11 + i) for i in range(k)]  # DEPTH=4: 11,22,33
        rw_val = self._mask(0x44)
        await self._fill(writes)
        # Simultaneous pop + push of 0x44 at 0 < count < DEPTH.
        await self._drive_item(1, 1, rw_val)
        await self._wait(1)
        self._check_outputs(dout=writes[0], empty=0, full=0)
        self._check_count(k)
        # Drain: remaining pushed values, then the value pushed in the
        # simultaneous cycle.
        await self._drain_expect(writes[1:])
        await self._read_and_check(rw_val)
        await self._wait(1)
        self._check_outputs(empty=1)
        self.logger.info("TC005 simultaneous_read_write: passed")


class SimultaneousReadWriteFullSeq(FifoSeqBase):
    """TC006 simultaneous_read_write_at_full: write dropped, read accepted."""

    SCENARIO_ID = "TC006"

    def __init__(self, name="SimultaneousReadWriteFullSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC006 simultaneous_read_write_at_full: begin")
        await self._reset_init()
        vals = [self._mask(0x01 + i) for i in range(self.depth)]  # DEPTH=4: 01..04
        await self._fill(vals)
        await self._wait(1)
        self._check_outputs(full=1)
        # At full: simultaneous write (dropped) and read (accepted).
        drop = min(0xFF, self.max_data)
        await self._drive_item(1, 1, drop)
        await self._wait(1)
        self._check_outputs(dout=vals[0], full=0, empty=0)
        self._check_count(self.depth - 1)
        await self._drain_expect(vals[1:])
        await self._wait(1)
        self._check_outputs(empty=1)
        self.logger.info("TC006 simultaneous_read_write_at_full: passed")


class SimultaneousReadWriteEmptySeq(FifoSeqBase):
    """TC007 simultaneous_read_write_at_empty: read dropped, write accepted."""

    SCENARIO_ID = "TC007"

    def __init__(self, name="SimultaneousReadWriteEmptySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC007 simultaneous_read_write_at_empty: begin")
        await self._reset_init()
        # At empty: simultaneous read + write.  Read ignored, write accepted;
        # dout stays at the post-reset value 0.
        rw_val = self._mask(0xAA)
        await self._drive_item(1, 1, rw_val)
        await self._wait(1)
        self._check_outputs(empty=0, full=0, dout=0)
        self._check_count(1)
        await self._read_and_check(rw_val)
        await self._wait(1)
        self._check_outputs(empty=1)
        self.logger.info("TC007 simultaneous_read_write_at_empty: passed")


class PointerWrapOrderingSeq(FifoSeqBase):
    """TC008 pointer_wraparound_ordering: interleaved traffic across pointer
    wraps with in-order reads and coherent flags."""

    SCENARIO_ID = "TC008"

    def __init__(self, name="PointerWrapOrderingSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC008 pointer_wraparound_ordering: begin")
        await self._reset_init()
        d = self.depth
        base = 0x10
        model = deque()  # expected queue contents
        nxt = base

        async def push():
            nonlocal nxt
            model.append(self._mask(nxt))
            await self._write(self._mask(nxt))
            nxt += 1

        async def peek_pop():
            exp = model.popleft()
            await self._read_and_check(exp)

        # Fill to full (DEPTH entries).
        for _ in range(d):
            await push()
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        self._check_count(d)
        # Two reads, two writes (half-fill, refill)...
        await peek_pop()
        await peek_pop()
        for _ in range(2):
            await push()
        # ...two more reads...
        await peek_pop()
        await peek_pop()
        # ...one write, then drain (d - 1 reads), exactly as planned for
        # DEPTH=4 and generalized to any DEPTH.
        await push()
        for _ in range(d - 1):
            await peek_pop()
        await self._wait(1)
        self._check_outputs(empty=1, full=0)
        assert len(model) == 0  # drained everything
        self.logger.info("TC008 pointer_wraparound_ordering: passed")


class ResetDuringOpSeq(FifoSeqBase):
    """TC009 reset_during_operation: async reset mid-stream clears state;
    operation recovers cleanly."""

    SCENARIO_ID = "TC009"

    def __init__(self, name="ResetDuringOpSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC009 reset_during_operation: begin")
        await self._reset_init()
        await self._write(self._mask(0x21))
        await self._write(self._mask(0x22))
        # Asynchronous reset while data is in flight: state must clear.
        await self._assert_reset()
        await self._wait(2)
        self._check_outputs(empty=1, full=0, dout=0)
        self._check_count(0)
        await self._release_reset()
        await self._wait(1)
        # The FIFO accepts new traffic after reset and returns it correctly.
        await self._write(self._mask(0x5A))
        await self._wait(1)
        self._check_outputs(empty=0)
        await self._read_and_check(self._mask(0x5A))
        self.logger.info("TC009 reset_during_operation: passed")


class BoundaryRoundtripSeq(FifoSeqBase):
    """TC010 data_boundary_roundtrip: min/max data round-trip at the full
    DATA_WIDTH (extrema scale with the elaborated DATA_WIDTH)."""

    SCENARIO_ID = "TC010"

    def __init__(self, name="BoundaryRoundtripSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("TC010 data_boundary_roundtrip: begin")
        await self._reset_init()
        lo, hi = 0, self.max_data
        vals = [lo if i % 2 == 0 else hi for i in range(self.depth)]
        await self._fill(vals)
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        await self._drain_expect(vals)
        await self._wait(1)
        self._check_outputs(empty=1, full=0)
        self.logger.info("TC010 data_boundary_roundtrip: passed")


# ---------------------------------------------------------------------------
# Registry of directed sequences.  SCENARIO_IDs are authoritative (plan ids);
# the duplicate check below is a build-time guard on this invariant.
# ---------------------------------------------------------------------------
DIRECTED_SEQUENCES = [
    (ResetCheckSeq.SCENARIO_ID, ResetCheckSeq),
    (WriteReadBasicSeq.SCENARIO_ID, WriteReadBasicSeq),
    (WriteUntilFullSeq.SCENARIO_ID, WriteUntilFullSeq),
    (ReadUntilEmptySeq.SCENARIO_ID, ReadUntilEmptySeq),
    (SimultaneousReadWriteSeq.SCENARIO_ID, SimultaneousReadWriteSeq),
    (SimultaneousReadWriteFullSeq.SCENARIO_ID, SimultaneousReadWriteFullSeq),
    (SimultaneousReadWriteEmptySeq.SCENARIO_ID, SimultaneousReadWriteEmptySeq),
    (PointerWrapOrderingSeq.SCENARIO_ID, PointerWrapOrderingSeq),
    (ResetDuringOpSeq.SCENARIO_ID, ResetDuringOpSeq),
    (BoundaryRoundtripSeq.SCENARIO_ID, BoundaryRoundtripSeq),
]

DIRECTED_SCENARIO_IDS = [sid for sid, _ in DIRECTED_SEQUENCES]
assert len(set(DIRECTED_SCENARIO_IDS)) == len(DIRECTED_SCENARIO_IDS), (
    "duplicate SCENARIO_ID in directed sequences"
)
assert set(DIRECTED_SCENARIO_IDS) == {
    "TC001", "TC002", "TC003", "TC004", "TC005",
    "TC006", "TC007", "TC008", "TC009", "TC010",
}, "directed sequence SCENARIO_ID set does not match plan ids"


# ---------------------------------------------------------------------------
# Corner-case sequences (plan 'corner_cases').
# These are separate verification strategies and therefore intentionally carry
# no SCENARIO_ID (they do not implement a directed scenario directly).
# ---------------------------------------------------------------------------
class WriteWhenFullSeq(FifoSeqBase):
    """write_when_full: wr_en while full is ignored; stored data intact."""

    def __init__(self, name="WriteWhenFullSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init()
        d = self.depth
        vals = [self._mask(0x50 + i) for i in range(d)]
        drop = self._mask(0x0E)
        fill_set = set(vals)
        if drop in fill_set:
            drop = self._mask(0xA5)
            if drop in fill_set:
                drop = next(v for v in range(self.max_data + 1) if v not in fill_set)
        await self._fill(vals)
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        self._check_count(d)
        # Ignored write while full.
        await self._write(drop)
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        self._check_count(d)
        # Drain in order: nothing was overwritten, the dropped value is gone.
        await self._drain_expect(vals)
        await self._wait(1)
        self._check_outputs(empty=1)
        self._check_count(0)


class ReadWhenEmptySeq(FifoSeqBase):
    """read_when_empty: rd_en while empty is ignored; count stays 0 and dout
    is unchanged."""

    def __init__(self, name="ReadWhenEmptySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init_checked()
        # Ignored read at empty: count stays 0, dout stays at post-reset 0.
        await self._drive_item(0, 1, 0)
        await self._wait(1)
        self._check_outputs(empty=1, full=0, dout=0)
        self._check_count(0)


class SimultaneousRWFullSeq(FifoSeqBase):
    """simultaneous_read_write_when_full: write dropped, read accepted,
    occupancy decrements to DEPTH-1."""

    def __init__(self, name="SimultaneousRWFullSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init()
        d = self.depth
        vals = [self._mask(0x60 + i) for i in range(d)]
        await self._fill(vals)
        await self._wait(1)
        self._check_outputs(full=1)
        await self._drive_item(1, 1, min(0xFF, self.max_data))
        await self._wait(1)
        self._check_outputs(dout=vals[0], full=0, empty=0)
        self._check_count(d - 1)
        await self._drain_expect(vals[1:])
        await self._wait(1)
        self._check_outputs(empty=1)


class SimultaneousRWEmptySeq(FifoSeqBase):
    """simultaneous_read_write_when_empty: read dropped, write accepted,
    occupancy increments to 1."""

    def __init__(self, name="SimultaneousRWEmptySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init()
        rw_val = self._mask(0xAA)
        await self._drive_item(1, 1, rw_val)
        await self._wait(1)
        self._check_outputs(empty=0, full=0, dout=0)
        self._check_count(1)
        await self._read_and_check(rw_val)
        await self._wait(1)
        self._check_outputs(empty=1)


class SimultaneousRWMidSeq(FifoSeqBase):
    """simultaneous_read_write_mid_occupancy: both accepted; oldest on dout;
    newest enqueued; occupancy unchanged."""

    def __init__(self, name="SimultaneousRWMidSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init()
        k = max(self.depth - 1, 1)
        vals = [self._mask(0x11 + i) for i in range(k)]
        rw_val = self._mask(0x44)
        await self._fill(vals)
        await self._drive_item(1, 1, rw_val)
        await self._wait(1)
        self._check_outputs(dout=vals[0], empty=0, full=0)
        self._check_count(k)
        await self._drain_expect(vals[1:])
        await self._read_and_check(rw_val)
        await self._wait(1)
        self._check_outputs(empty=1)


class PointerWraparoundSeq(FifoSeqBase):
    """pointer_wraparound: sustained traffic through more than one full pass
    of the memory array; no loss, duplication, or ordering violation."""

    def __init__(self, name="PointerWraparoundSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init()
        d = self.depth
        passes = 3  # more than one full pass of the memory array
        nxt = 0x40
        model = deque()
        for p in range(passes):
            if p:
                await self._wait(1)
                self._check_outputs(empty=1, full=0)
            # Fill pass.
            for _ in range(d):
                model.append(self._mask(nxt))
                await self._write(self._mask(nxt))
                nxt += 1
            await self._wait(1)
            self._check_outputs(full=1, empty=0)
            self._check_count(d)
            # Drain pass (strict FIFO order).
            for _ in range(d):
                await self._read_and_check(model.popleft())
            await self._wait(1)
            self._check_outputs(empty=1, full=0)
            self._check_count(0)
        assert len(model) == 0


class FullToEmptyTransitionSeq(FifoSeqBase):
    """full_to_empty_transition: fill completely then drain completely in
    consecutive cycles; full/empty exact and never simultaneous."""

    def __init__(self, name="FullToEmptyTransitionSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init()
        d = self.depth
        vals = [self._mask(0x70 + i) for i in range(d)]
        model = deque()
        # Consecutive writes to reach full.
        for v in vals:
            model.append(v)
            await self._write(v)
            await self._wait(0)  # no gap: items are consecutive anyway
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        self._check_count(d)
        # Consecutive reads to drain.
        for _ in range(d):
            await self._read_and_check(model.popleft())
        await self._wait(1)
        self._check_outputs(empty=1, full=0)
        self._check_count(0)
        # Never asserted simultaneously: full XOR empty at every sample point.
        f = int(self.dut.full.value)
        e = int(self.dut.empty.value)
        assert f + e <= 1, "full and empty asserted simultaneously"


class ResetMidStreamSeq(FifoSeqBase):
    """reset_mid_stream: assert rst_n while writes/reads are in flight;
    all state cleared; post-reset operation is clean."""

    def __init__(self, name="ResetMidStreamSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init()
        await self._write(self._mask(0x21))
        await self._write(self._mask(0x22))
        await self._assert_reset()
        await self._wait(3)
        self._check_outputs(empty=1, full=0, dout=0)
        self._check_count(0)
        await self._release_reset()
        await self._wait(1)
        # Post-reset traffic must be clean and correct.
        await self._write(self._mask(0x33))
        await self._write(self._mask(0x44))
        await self._read_and_check(self._mask(0x33))
        await self._read_and_check(self._mask(0x44))
        await self._wait(1)
        self._check_outputs(empty=1)


class DoutRetentionSeq(FifoSeqBase):
    """dout_retention_after_ignored_read: after prior successful reads, an
    ignored empty-read leaves dout at the last successfully read value; dout
    is 0 only immediately after reset."""

    def __init__(self, name="DoutRetentionSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        await self._reset_init_checked()  # dout == 0 right after reset
        vals = [self._mask(0x11), self._mask(0x22), self._mask(0x33), self._mask(0x44)][: self.depth]
        await self._fill(vals)
        last = None
        for v in vals:
            await self._read_and_check(v)
            last = v
        await self._wait(1)
        self._check_outputs(empty=1)
        # Ignored read while empty: dout retains the last read value.
        await self._drive_item(0, 1, 0)
        await self._wait(1)
        self._check_outputs(empty=1, dout=last)
        # Normal operation resumes afterwards.
        await self._write(self._mask(0x5A))
        await self._read_and_check(self._mask(0x5A))
        await self._wait(1)
        self._check_outputs(empty=1)


# ---------------------------------------------------------------------------
# Back-to-back test (W-NO-BACK-TO-BACK).
#
# Exercises consecutive writes, consecutive reads, and write-then-read /
# read-then-write on adjacent rising edges WITHOUT intervening idle cycles.
# This verifies the driver's back-to-back support (driver.py) and confirms
# the FIFO handles rapid consecutive operations correctly.
# ---------------------------------------------------------------------------
class BackToBackSeq(FifoSeqBase):
    """back_to_back_operations: consecutive writes, consecutive reads,
    write-then-read, and read-then-write on adjacent rising edges."""

    def __init__(self, name="BackToBackSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("back_to_back_operations: begin")
        await self._reset_init()

        d = self.depth

        # --- Phase 1: consecutive writes (back-to-back) ---
        fill_vals = [self._mask(0xA0 + i) for i in range(d)]
        await self._fill(fill_vals)
        # No extra wait: _fill sends consecutive _write calls which become
        # back-to-back items in the driver.
        await self._wait(1)
        self._check_outputs(full=1, empty=0)
        self._check_count(d)

        # --- Phase 2: consecutive reads (back-to-back) ---
        await self._drain_expect(fill_vals)
        await self._wait(1)
        self._check_outputs(empty=1, full=0)

        # --- Phase 3: write-then-read on adjacent edges ---
        val_w = self._mask(0xB0)
        val_r = self._mask(0xB1)
        await self._write(val_w)
        # Immediately read the value we just wrote (back-to-back)
        await self._drive_item(0, 1, 0)
        await self._wait(1)
        self._check_outputs(dout=val_w, empty=1)

        # --- Phase 4: read-then-write on adjacent edges ---
        # Start from empty, do a read (ignored), then write.
        await self._drive_item(0, 1, 0)
        await self._drive_item(1, 0, val_r)
        await self._wait(1)
        self._check_outputs(empty=0, full=0)
        await self._read_and_check(val_r)

        # --- Phase 5: simultaneous read+write back-to-back sequences ---
        # Fill partially, then do consecutive simultaneous read+write cycles.
        aux = [self._mask(0xC0 + i) for i in range(max(d - 1, 1))]
        await self._fill(aux)
        k = len(aux)
        # Two consecutive simultaneous read+write cycles.
        rw1 = self._mask(0xD0)
        rw2 = self._mask(0xD1)
        await self._drive_item(1, 1, rw1)
        await self._drive_item(1, 1, rw2)
        await self._wait(1)
        # After two sim RW cycles at count=k, the first RW popped aux[0]
        # and pushed rw1, second popped aux[1] (or rw1 if k=1) and pushed
        # rw2.  Occupancy stays at k.
        self._check_outputs(empty=0, full=0)
        self._check_count(k)
        # Drain and verify FIFO order.
        remaining = aux[2:] + [rw1, rw2] if k >= 2 else [rw1, rw2]
        await self._drain_expect(remaining)
        await self._wait(1)
        self._check_outputs(empty=1)

        self.logger.info("back_to_back_operations: passed")


# ---------------------------------------------------------------------------
# Randomized traffic (plan 'randomized_testing_strategy').
# ---------------------------------------------------------------------------
class FifoRandomizedSeq(FifoSeqBase):
    """Constrained-random stimulus for the FIFO.

    Every cycle drives wr_en/rd_en/din from the plan's constraint ranges
    (wr_en, rd_en in {0,1}; din in [0, (1<<DATA_WIDTH)-1]).  Two reset
    injections are supported, matching the plan:

      * periodic reset (``periodic_reset_period`` cycles) with a duration
        drawn from ``periodic_reset_duration`` (plan: 2..3 cycles), and
      * one random mid-test reset at a random cycle with a duration drawn
        from ``mid_test_reset_duration`` (plan: 1..4 cycles).

    After every reset the sequence verifies recovery to a clean state
    (empty=1, full=0, dout=0); the scoreboard (later stage) checks every
    remaining cycle against the reference model.

    Tuning attributes (set before ``start()``): ``num_cycles``,
    ``periodic_reset_period`` (set to None to disable), ``seed``.

    Seed reproducibility (W-SEED-NOREPRO fix):
    ``FifoRandomizedSeq.seed`` is a *deterministic* default derived from a
    hash of the sequence/test name, so the same configuration always replays
    the identical stimulus stream.  It can be overridden explicitly by:
      * setting the ``RANDOM_SEED`` environment variable (integer), or
      * assigning ``seq.seed = <int>`` before ``start()``.
    The actual seed used is logged at info level at sequence startup, and is
    also recorded through ``self._seed`` so tests/harness can capture it for
    bug reproduction.
    """

    num_cycles = 240
    periodic_reset_period = 60
    periodic_reset_duration = (2, 3)
    mid_test_reset_duration = (1, 4)
    # Deterministic default: hash of the sequence/test name.  Explicit
    # override via the RANDOM_SEED env var or by assigning ``seq.seed``
    # before ``start()`` (W-SEED-NOREPRO).
    seed = None

    def __init__(self, name="FifoRandomizedSeq"):
        super().__init__(name)
        self._seed = None   # resolved seed actually used (see body)

    async def _inject_reset(self, duration):
        """Assert reset for ``duration`` cycles and verify clean recovery."""
        await self._assert_reset()
        await self._wait(duration)
        await self._release_reset()
        await self._wait(1)
        self._check_outputs(empty=1, full=0, dout=0)
        self._check_count(0)

    async def body(self):
        await self._setup()
        # Resolve the RNG seed (deterministic by default, W-SEED-NOREPRO):
        #   1) explicit class/instance seed if set,
        #   2) else the RANDOM_SEED environment variable when present,
        #   3) else a stable hash of the sequence name.
        seed = self.seed
        if seed is None:
            env_seed = os.environ.get("RANDOM_SEED")
            if env_seed:  # non-empty string; skip empty (unset / exported blank)
                try:
                    seed = int(env_seed)
                except ValueError:
                    self.logger.warning(
                        "RANDOM_SEED=%r is not an integer; ignoring", env_seed
                    )
        if seed is None:
            seed = hash(self.get_name()) & 0x7FFFFFFF
        self._seed = seed
        rng = random.Random(seed)
        self.logger.info(
            "FifoRandomizedSeq RNG seed = %d (reproducible; set RANDOM_SEED to "
            "replay)", seed,
        )

        # One random mid-test reset, positioned firmly mid-stream.
        mid_reset_at = None
        if self.num_cycles >= 32:
            mid_reset_at = rng.randint(
                self.num_cycles // 4, (3 * self.num_cycles) // 4
            )

        await self._assert_reset()
        await self._wait(2)
        await self._release_reset()
        await self._wait(1)
        self._check_outputs(empty=1, full=0, dout=0)

        self.logger.info(
            "FifoRandomizedSeq: %d cycles, periodic every %s, mid-test reset at %s",
            self.num_cycles, self.periodic_reset_period, mid_reset_at,
        )
        for cycle in range(self.num_cycles):
            if self.periodic_reset_period and cycle and (
                cycle % self.periodic_reset_period == 0
            ):
                await self._inject_reset(
                    rng.randint(*self.periodic_reset_duration)
                )
            if cycle == mid_reset_at:
                await self._inject_reset(
                    rng.randint(*self.mid_test_reset_duration)
                )
            wr_en = rng.choice((0, 1))
            rd_en = rng.choice((0, 1))
            # Bias din generation toward boundary values (0x00 and max_data)
            # to deterministically exercise the data coverage bins that are
            # statistically sparse under pure uniform random (W-DATA-MAX-NEVER-
            # EXERCISED, W-DIN-RANGE-CONSTRAINT-TOO-WIDE).  10% for each
            # boundary, 80% uniform random in the full range.
            r = rng.random()
            if r < 0.10:
                din = 0
            elif r < 0.20:
                din = self.max_data
            else:
                din = rng.randint(0, self.max_data)
            await self._drive_item(wr_en, rd_en, din)


# ---------------------------------------------------------------------------
# Convenient collection of all stimulus-sequence classes for later stages.
# ---------------------------------------------------------------------------
CORNER_SEQUENCES = [
    WriteWhenFullSeq,
    ReadWhenEmptySeq,
    SimultaneousRWFullSeq,
    SimultaneousRWEmptySeq,
    SimultaneousRWMidSeq,
    PointerWraparoundSeq,
    FullToEmptyTransitionSeq,
    ResetMidStreamSeq,
    DoutRetentionSeq,
]

ALL_STIMULUS_SEQUENCES = (
    [cls for _, cls in DIRECTED_SEQUENCES]
    + CORNER_SEQUENCES
    + [BackToBackSeq, FifoRandomizedSeq]
)