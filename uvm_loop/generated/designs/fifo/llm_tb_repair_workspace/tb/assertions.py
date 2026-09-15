"""FIFO always-on assertions in Python (replaces SVA) + bounded watchdog.

This module implements the ``useful_assertions`` section of the verification
plan for the ``fifo`` DUT (/workspace/benchmarks/fifo/fifo.sv) as plain
Python checker coroutines.  There is no SystemVerilog: no covergroup, no SVA,
no ``interface``.  Every check is an ``assert`` statement inside an
always-running coroutine that synchronizes on the DUT clock edge via cocotb
triggers (``RisingEdge`` + ``ReadOnly``) and is launched with
``cocotb.start_soon``.  When a check does not hold the ``AssertionError``
propagates out of the task and fails the cocotb test immediately.

The checker coroutines sample the DUT pins directly through the shared
``dut`` handle using exactly the pin names of CONTRACT.md §2.  They sample in
cocotb's read-only region (post-edge values), i.e. the same values the
monitor publishes (§10.2), and only after all nonblocking RTL updates and the
combinational ``full``/``empty`` re-derivation have settled.

Assertion -> plan-item mapping (plan ``useful_assertions``):

    check_reset_clean_state       reset_clean_state
    check_no_overflow             no_overflow
    check_no_underflow            no_underflow
    check_occupancy_bounds        occupancy_bounds
    check_flags_mutually_exclusive flags_mutually_exclusive
    check_count_update_consistency count_update_consistency
    check_fifo_ordering           fifo_ordering

Notes:

    * The three count-based checks (no_overflow, no_underflow,
      occupancy_bounds, count_update_consistency) read the internal RTL
      ``integer count`` via ``dut.count``.  When that signal is not exposed by
      the simulator the check is skipped for that cycle (CONTRACT.md §9.5);
      the module logs a warning once.
    * ``check_fifo_ordering`` uses the shared reference model
      (tb/ref_model.py, a byte-for-byte copy of the behavioral oracle per
      CONTRACT.md §11.1) with the exact call form
      ``ref_model.step(state, wr_en, rd_en, din, depth)``; it does not
      reimplement any queue logic.

Watchdog:

    :class:`FifoWatchdog` / :func:`start_watchdog` implement the required
    bounded-run guard: if the ``done`` signal (a ``cocotb.triggers.Event``)
    has not been set within a bounded number of DUT clock cycles, the watchdog
    raises ``AssertionError`` and fails the test, so a hung test cannot
    silently exhaust the whole simulation run.
"""

import logging

import cocotb
from cocotb.triggers import Event, ReadOnly, RisingEdge

from pyuvm import ConfigDB

import ref_model

log = logging.getLogger("fifo.assertions")


def _to_int(value):
    """Best-effort integer conversion of a cocotb ``BinaryValue``.

    Returns ``None`` when the value is not resolvable (X/Z, e.g. the start of
    simulation before the clock/reset generator drives the pins); the callers
    skip such a cycle instead of failing on simulator-initialization junk.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _read_count(dut):
    """Read the internal RTL ``count`` when reachable; ``None`` otherwise."""
    if not hasattr(dut, "count"):
        return None
    try:
        return int(dut.count.value)
    except (ValueError, TypeError):
        return None


class FifoAssertions:
    """Bundle of always-running FIFO assertion checker coroutines.

    Instantiate with the shared DUT handle plus the elaborated parameters
    (resolved from ConfigDB by :func:`start_assertions` unless given) and
    call :meth:`start` to launch every checker with ``cocotb.start_soon``.
    Any checker failure raises ``AssertionError`` and fails the test.
    """

    def __init__(self, dut, depth, data_width, logger=None):
        self.dut = dut
        self.depth = int(depth)
        self.data_width = int(data_width)
        self.logger = logger if logger is not None else log
        self.tasks = []          # cocotb Tasks of the spawned checkers
        self._count_warned = False

    # -- lifecycle ---------------------------------------------------------

    def start(self):
        """Launch all checker coroutines with ``cocotb.start_soon``.

        Returns the list of cocotb Tasks (one per plan assertion) for callers
        that want to join/cancel them.
        """
        if self.tasks:  # idempotent: do not double-spawn on re-entry
            return self.tasks
        checkers = [
            self.check_reset_clean_state,
            self.check_no_overflow,
            self.check_no_underflow,
            self.check_occupancy_bounds,
            self.check_flags_mutually_exclusive,
            self.check_count_update_consistency,
            self.check_fifo_ordering,
        ]
        self.tasks = [cocotb.start_soon(fn()) for fn in checkers]
        self.logger.info(
            "FifoAssertions started: %d checker coroutines", len(self.tasks)
        )
        return self.tasks

    # -- sampling helper ---------------------------------------------------

    def _count(self):
        """Internal count with an optional one-time reachability warning."""
        cnt = _read_count(self.dut)
        if cnt is None and not self._count_warned:
            self._count_warned = True
            self.logger.warning(
                "internal RTL 'count' is not reachable from the testbench "
                "handle; count-based assertion checks are being skipped "
                "(CONTRACT.md §9.5)"
            )
        return cnt

    # -- checkers ----------------------------------------------------------

    async def check_reset_clean_state(self):
        """reset_clean_state (severity error).

        After the asynchronous active-low reset is asserted (sampled
        ``rst_n == 0`` post-edge), the FIFO must be empty (``empty == 1``),
        not full (``full == 0``) and ``dout`` must be cleared (``dout == 0``).
        """
        cycle = 0
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            rst_n = _to_int(self.dut.rst_n.value)
            if rst_n is None:
                continue
            if rst_n == 0:
                empty = _to_int(self.dut.empty.value)
                full = _to_int(self.dut.full.value)
                dout = _to_int(self.dut.dout.value)
                if empty is None or full is None or dout is None:
                    continue
                assert empty == 1, (
                    f"reset_clean_state violated at cycle {cycle}: rst_n asserted "
                    f"but empty={empty} (expected 1)"
                )
                assert full == 0, (
                    f"reset_clean_state violated at cycle {cycle}: rst_n asserted "
                    f"but full={full} (expected 0)"
                )
                assert dout == 0, (
                    f"reset_clean_state violated at cycle {cycle}: rst_n asserted "
                    f"but dout={dout:#x} (expected 0)"
                )
            cycle += 1

    async def check_no_overflow(self):
        """no_overflow (severity error).

        A write while the FIFO is full is ignored: if the DUT sampled
        ``full == 1 && wr_en == 1`` on a rising edge then ``count`` must not
        increase on the following cycle.  (``full`` seen pre-edge by edge *k*
        is the post-edge ``full`` value sampled at edge *k-1*.)
        """
        prev = None  # (full, wr_en, count) of the previous resolved cycle
        cycle = 0
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            full = _to_int(self.dut.full.value)
            wr_en = _to_int(self.dut.wr_en.value)
            count = self._count()
            if full is None or wr_en is None:
                continue
            if prev is not None and count is not None:
                prev_full, _prev_wr_en, prev_count = prev
                if prev_full and wr_en:
                    assert count <= prev_count, (
                        f"no_overflow violated at cycle {cycle}: write requested "
                        f"while full (full={prev_full}, wr_en={wr_en}) but count "
                        f"increased from {prev_count} to {count}"
                    )
            if count is not None:
                prev = (full, wr_en, count)
            cycle += 1

    async def check_no_underflow(self):
        """no_underflow (severity error).

        A read while the FIFO is empty is ignored: if the DUT sampled
        ``empty == 1 && rd_en == 1`` on a rising edge then ``count`` must not
        decrease on the following cycle.
        """
        prev = None  # (empty, rd_en, count) of the previous resolved cycle
        cycle = 0
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            empty = _to_int(self.dut.empty.value)
            rd_en = _to_int(self.dut.rd_en.value)
            count = self._count()
            if empty is None or rd_en is None:
                continue
            if prev is not None and count is not None:
                prev_empty, _prev_rd_en, prev_count = prev
                if prev_empty and rd_en:
                    assert count >= prev_count, (
                        f"no_underflow violated at cycle {cycle}: read requested "
                        f"while empty (empty={prev_empty}, rd_en={rd_en}) but "
                        f"count decreased from {prev_count} to {count}"
                    )
            if count is not None:
                prev = (empty, rd_en, count)
            cycle += 1

    async def check_occupancy_bounds(self):
        """occupancy_bounds (severity error).

        The occupancy count always stays within ``[0, DEPTH]`` inclusive at
        every clock edge.
        """
        cycle = 0
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            count = self._count()
            if count is None:
                continue
            assert 0 <= count <= self.depth, (
                f"occupancy_bounds violated at cycle {cycle}: count={count} "
                f"outside [0, {self.depth}]"
            )
            cycle += 1

    async def check_flags_mutually_exclusive(self):
        """flags_mutually_exclusive (severity error).

        ``full`` and ``empty`` are never asserted simultaneously.
        """
        cycle = 0
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            full = _to_int(self.dut.full.value)
            empty = _to_int(self.dut.empty.value)
            if full is None or empty is None:
                continue
            assert not (full and empty), (
                f"flags_mutually_exclusive violated at cycle {cycle}: "
                f"full={full} and empty={empty} asserted simultaneously"
            )
            cycle += 1

    async def check_count_update_consistency(self):
        """count_update_consistency (severity error).

        ``count_next == count + (wr_accepted && !rd_accepted) -
        (rd_accepted && !wr_accepted)``: count increments on a write-only
        accepted cycle, decrements on a read-only accepted cycle and is
        unchanged when both or neither operation is accepted.  Acceptance of
        the operation on edge *k* is decided with the pre-edge flags, i.e. the
        post-edge ``full``/``empty`` sampled at edge *k-1*.

        Reset-aware: when ``rst_n`` is deasserted (active low, i.e. 0), the
        previous-state tracker is cleared and no comparison is performed,
        mirroring the scoreboard's reset handling.
        """
        prev = None  # (full, empty, count) of the previous resolved cycle
        cycle = 0
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            rst_n = _to_int(self.dut.rst_n.value)
            wr_en = _to_int(self.dut.wr_en.value)
            rd_en = _to_int(self.dut.rd_en.value)
            full = _to_int(self.dut.full.value)
            empty = _to_int(self.dut.empty.value)
            count = self._count()
            if rst_n is None or wr_en is None or rd_en is None or full is None or empty is None:
                continue
            # During reset, clear previous state and skip the comparison.
            if rst_n == 0:
                prev = None
                cycle += 1
                continue
            if prev is not None and count is not None:
                prev_full, prev_empty, prev_count = prev
                wr_acc = bool(wr_en) and not prev_full
                rd_acc = bool(rd_en) and not prev_empty
                expected = (
                    prev_count
                    + (1 if (wr_acc and not rd_acc) else 0)
                    - (1 if (rd_acc and not wr_acc) else 0)
                )
                assert count == expected, (
                    f"count_update_consistency violated at cycle {cycle}: "
                    f"wr_en={wr_en} rd_en={rd_en} full_prev={prev_full} "
                    f"empty_prev={prev_empty}; expected count {expected} "
                    f"(from {prev_count}), got {count}"
                )
            if count is not None:
                prev = (full, empty, count)
            cycle += 1

    async def check_fifo_ordering(self):
        """fifo_ordering (severity error).

        A read pops the *oldest* unread written value; data returns in
        first-in-first-out order.  Implemented against the shared reference
        model (CONTRACT.md §11.1): every cycle advances
        ``ref_model.step(state, wr_en, rd_en, din, depth)`` and the model's
        registered (latency-1) ``dout`` is compared to the DUT's post-edge
        ``dout``.  Because the model always pops the oldest queued entry,
        matching ``dout`` enforces strict FIFO ordering (and no drop/dup).
        Resets re-arm the model with ``ref_model.reset()`` and require
        ``dout == 0``.
        """
        state = ref_model.reset()
        cycle = 0
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            rst_n = _to_int(self.dut.rst_n.value)
            wr_en = _to_int(self.dut.wr_en.value)
            rd_en = _to_int(self.dut.rd_en.value)
            din = _to_int(self.dut.din.value)
            dout = _to_int(self.dut.dout.value)
            if rst_n is None or wr_en is None or rd_en is None:
                continue
            if din is None or dout is None:
                continue
            if rst_n == 0:
                state = ref_model.reset()
                assert dout == 0, (
                    f"fifo_ordering violated at cycle {cycle}: reset asserted "
                    f"but dout={dout:#x} (expected 0)"
                )
            else:
                state = ref_model.step(
                    state, int(wr_en), int(rd_en), int(din), self.depth
                )
                exp_dout = int(state["dout"])
                assert exp_dout == dout, (
                    f"fifo_ordering violated at cycle {cycle}: wr_en={wr_en} "
                    f"rd_en={rd_en} din={din:#x}; expected dout={exp_dout:#x} "
                    f"(oldest queued value per reference model), got "
                    f"{dout:#x}"
                )
            cycle += 1


# ---------------------------------------------------------------------------
# Standalone launchers
# ---------------------------------------------------------------------------
def start_assertions(dut=None, depth=None, data_width=None):
    """Resolve the DUT config and start every assertion checker coroutine.

    ``dut``/``depth``/``data_width`` default to the shared ConfigDB values
    (CONTRACT.md §4, access form §9.1).  The returned :class:`FifoAssertions`
    instance carries ``.tasks`` (the spawned cocotb Tasks).  The integration
    (env/tb_top/tests) stage is expected to call this exactly once, e.g.
    ``start_assertions()`` at the start of the test body.
    """
    if dut is None:
        dut = ConfigDB().get(None, "*", "dut")
    if depth is None:
        depth = int(ConfigDB().get(None, "*", "DEPTH"))
    if data_width is None:
        data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
    assertions = FifoAssertions(dut, depth, data_width)
    assertions.start()
    return assertions


class FifoWatchdog:
    """Bounded-run watchdog that fails a hung test (plan watchdog rule).

    Counts DUT rising edges; if ``done`` (a ``cocotb.triggers.Event``) has
    not been set within ``max_cycles`` edges, :meth:`run` raises
    ``AssertionError`` and thereby fails the test immediately.  The test /
    tb_top layer sets ``done`` (``done.set()``) when the test body completes
    (typically in a ``finally``), letting the watchdog exit quietly early.
    """

    def __init__(self, dut, max_cycles, done, description="fifo simulation",
                 logger=None):
        self.dut = dut
        self.max_cycles = int(max_cycles)
        self.done = done
        self.description = description
        self.logger = logger if logger is not None else log

    async def run(self):
        """Wait for ``done`` or the bounded cycle budget, whichever first."""
        for spent in range(self.max_cycles):
            if self.done.is_set():
                return
            await RisingEdge(self.dut.clk)
        if not self.done.is_set():
            raise AssertionError(
                f"watchdog timeout: {self.description} did not finish within "
                f"{self.max_cycles} clock cycles"
            )


def start_watchdog(dut, max_cycles, done=None, description="fifo simulation"):
    """Launch a bounded watchdog coroutine and return its cocotb Task.

    Args:
        dut: shared cocotb DUT handle (per-cycle edge counter).
        max_cycles: number of DUT clock cycles the run is allowed to take.
        done: ``cocotb.triggers.Event`` that the test body sets on completion;
            a fresh ``Event`` is created when omitted.
        description: human-readable label for the watchdog error message.
    """
    if done is None:
        done = Event()
    watchdog = FifoWatchdog(dut, max_cycles, done, description)
    return cocotb.start_soon(watchdog.run()), done


def watchdog_event_for(max_cycles, dut=None, description="fifo simulation"):
    """One-shot convenience: start the watchdog and return ``(task, done)``
    with ``dut`` resolved from ConfigDB when not given."""
    if dut is None:
        dut = ConfigDB().get(None, "*", "dut")
    return start_watchdog(dut, max_cycles, None, description)