"""Stage 5 (assertions) artifact of the CHIA generator: SVA-replacement
Python checkers for the ``aes128`` bench.

Per CONTRACT.md section 6 there is no SystemVerilog assertion language in
this project.  Every plan item in ``useful_assertions`` is implemented as a
plain-Python checker *coroutine* that runs continuously, synchronized on
the rising edge of the DUT clock via cocotb triggers, and is launched with
``cocotb.start_soon``.  A violated check is flagged immediately:

* **severity "error"**  -> logged as an error and raised as an
  ``AssertionError``, which propagates out of the checker coroutine and
  fails the enclosing cocotb test immediately (the SVA ``assert``
  equivalent).
* **severity "warning"** -> logged as a warning and counted in
  ``violations`` (the SVA ``cover``/info equivalent); warnings document
  design rules and do not by themselves fail the test.

The plan's eight assertions are implemented here, each as an async method
whose name and docstring ties it back to its plan item:

======== ================================================= ========== plan
name                                                     severity
======== ================================================= ==========
done_single_pulse              done deasserts on next cycle             error
busy_deasserts_with_done       busy low when done pulses               error
busy_high_during_operation     busy stays high until done               error
no_start_ignored_while_busy    start during busy keeps busy high        warning
reset_clears_outputs           outputs zero within one clock of reset   error
ciphertext_valid_when_done     no unknown bits in ciphertext at done   error
operation_latency              done exactly 12 cycles after start       error
busy_low_when_idle             busy==0 when FSM is in IDLE             error
======== ================================================= ==========

Sampling semantics
------------------
All checkers sample pins *after* each ``RisingEdge(dut.clk)`` (the
post-edge register values, which is what SVA on ``posedge clk`` observes
for register outputs).  Reset is asynchronous and active low; most
checkers skip sampling while ``rst_n`` is not high so the pre-reset
unknown-value window cannot produce spurious failures.  The
``reset_clears_outputs`` checker manages its own reset-edge tracking
rather than skipping.

State access
------------
``busy_low_when_idle`` requires reading the internal FSM ``state`` register
(directly via ``dut.state.value``).  Under the standard cocotb Verilator
build (``--public-flat-rw``), internal signals are accessible.  If the
signal is unavailable (AttributeError / ValueError / TypeError), the
checker logs a warning once and degrades to skipping the check gracefully.

Integration (environment stage)
-------------------------------
The integration stage starts the checkers via :func:`launch_assertions`
and reports the ``violations`` counters at end of test.  The always-running
watchdog requested by CONTRACT.md section 6 is provided here as
:func:`launch_watchdog` (a bounded clock-cycle runner that the environment
starts and kills on normal completion).
"""

import logging

import cocotb
from cocotb.triggers import FallingEdge, RisingEdge
from pyuvm import ConfigDB

from tb.dut_helper import AES128DUTHelper

__all__ = [
    "AES128Assertions",
    "ASSERTION_SEVERITY",
    "launch_assertions",
    "launch_watchdog",
    "watchdog",
]

_log = logging.getLogger("tb.assertions")

# FSM state encoding (RTL aes128.sv typedef enum logic [1:0])
_STATE_IDLE = 0
_STATE_ROUND_RUN = 1
_STATE_FINISH = 2

# ---------------------------------------------------------------------------
# Plan metadata (useful_assertions).
# ---------------------------------------------------------------------------

ASSERTION_SEVERITY = {
    # plan name                       -> plan severity
    "done_single_pulse": "error",
    "busy_deasserts_with_done": "error",
    "busy_high_during_operation": "error",
    "no_start_ignored_while_busy": "warning",
    "reset_clears_outputs": "error",
    "ciphertext_valid_when_done": "error",
    "operation_latency": "error",
    "busy_low_when_idle": "error",
}


# ---------------------------------------------------------------------------
# Checker collection.
# ---------------------------------------------------------------------------


class AES128Assertions:
    """Always-running Python assertion checkers for the ``aes128`` DUT.

    Constructor arguments are optional; when omitted, the shared
    ``dut`` / ``AES128DUTHelper`` objects are fetched from pyuvm's
    ``ConfigDB`` using exactly the CONTRACT.md keys (``"dut"`` /
    ``"dut_helper"``).

    Usage (integration stage)::

        checks = AES128Assertions()          # or via launch_assertions()
        tasks = checks.start()              # cocotb.start_soon per checker
        ...
        checks.summarize()                  # end-of-test report of violations

    Error-severity checkers raise :class:`AssertionError` on the first
    violation (the enclosing cocotb test fails immediately); warning-level
    checkers log and count.  ``violations`` maps plan-name -> count of
    times the check has failed or warned.
    """

    def __init__(self, dut=None, helper=None, log=None):
        #: Raw cocotb DUT handle (for clock triggers and internal signals).
        self.dut = dut if dut is not None else ConfigDB().get(None, "", "dut")
        #: Pin-access helper (CONTRACT.md section 5 / §7.3).
        self.helper = (
            helper if helper is not None
            else ConfigDB().get(None, "", "dut_helper")
        )
        self.log = log if log is not None else _log
        #: Running cocotb tasks, one per checker (filled by start()).
        self.tasks = []
        #: plan-name -> number of violations/warnings observed so far.
        self.violations = {name: 0 for name in ASSERTION_SEVERITY}
        self._started = False
        self._state_warned = False  # one-shot: state signal unavailable

    # ------------------------------------------------------------------
    # Launch control
    # ------------------------------------------------------------------
    def start(self):
        """Launch every checker with ``cocotb.start_soon`` (idempotent).

        Returns the list of cocotb tasks.  Must be called while the cocotb
        simulation is running (from the environment/test coroutine), not at
        import time.
        """
        if self._started:
            return self.tasks
        self._started = True
        self.tasks = [
            cocotb.start_soon(self._check_done_single_pulse()),
            cocotb.start_soon(self._check_busy_deasserts_with_done()),
            cocotb.start_soon(self._check_busy_high_during_operation()),
            cocotb.start_soon(self._check_no_start_ignored_while_busy()),
            cocotb.start_soon(self._check_reset_clears_outputs()),
            cocotb.start_soon(self._check_ciphertext_valid_when_done()),
            cocotb.start_soon(self._check_operation_latency()),
            cocotb.start_soon(self._check_busy_low_when_idle()),
        ]
        self.log.info(
            "AES128Assertions: launched %d checker coroutines via "
            "cocotb.start_soon",
            len(self.tasks),
        )
        return self.tasks

    def stop(self):
        """Kill all checker tasks (used when the environment tears down)."""
        for task in self.tasks:
            try:
                task.kill()
            except Exception:  # pragma: no cover - defensive teardown
                pass
        self.tasks = []
        self._started = False

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def summarize(self):
        """One-line summary for the environment's end-of-test report."""
        counts = ", ".join(
            f"{name}={count}"
            for name, count in sorted(self.violations.items())
            if count
        )
        if not counts:
            counts = "none"
        return (
            f"AES128Assertions: {len(self.tasks)} active checkers, "
            f"violations -> {counts}"
        )

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _in_reset(self):
        """True while ``rst_n`` is deasserted (0) or still unknown (x/z).

        Reset is active-low and asynchronous (CONTRACT.md section 3); most
        checkers skip sampling during this window so the pre-reset X window
        and power-up cannot fabricate violations.
        """
        try:
            return int(self.helper.rst_n) != 1
        except (ValueError, TypeError):
            return True  # unknown / X -- treat as "in reset"

    def _read_state(self):
        """Read the internal FSM ``state`` register.

        Returns the integer value (0=IDLE, 1=ROUND_RUN, 2=FINISH) or
        ``None`` if the signal is not accessible.  Logs a warning once
        when the signal is unavailable.
        """
        try:
            val = int(self.dut.state.value)
            if val in (_STATE_IDLE, _STATE_ROUND_RUN, _STATE_FINISH):
                return val
            return None
        except (AttributeError, ValueError, TypeError, Exception):
            if not self._state_warned:
                self.log.warning(
                    "AES128Assertions: cannot read internal 'state' "
                    "signal; busy_low_when_idle check will be skipped"
                )
                self._state_warned = True
            return None

    def _fail(self, name, message):
        """Flag an error-severity violation: log + raise immediately."""
        self.violations[name] += 1
        self.log.error("[assertion %s] FAILED: %s", name, message)
        raise AssertionError(f"assertion '{name}' failed: {message}")

    def _warn(self, name, message):
        """Flag a warning-severity violation: log + count (non-fatal)."""
        self.violations[name] += 1
        self.log.warning("[assertion %s] WARNING: %s", name, message)

    # ------------------------------------------------------------------
    # Plan item: done_single_pulse  (severity error)
    # "done === 1 |=> done === 0"
    # ------------------------------------------------------------------
    async def _check_done_single_pulse(self):
        """Guards the single-cycle completion-pulse behavior.

        ``done`` must never be high for two consecutive clock cycles.
        Sampled at every rising edge while out of reset.  Reset history
        is reset whenever ``rst_n`` is deasserted (FSM re-initialized).
        """
        dut = self.dut
        helper = self.helper
        prev_done = 0
        while True:
            await RisingEdge(dut.clk)
            if self._in_reset():
                prev_done = 0
                continue
            cur_done = int(helper.done)
            if prev_done == 1 and cur_done == 1:
                self._fail(
                    "done_single_pulse",
                    "done stayed high for two consecutive clock cycles "
                    "(cycle N and cycle N+1 both sampled done==1)",
                )
            prev_done = cur_done

    # ------------------------------------------------------------------
    # Plan item: busy_deasserts_with_done  (severity error)
    # "done === 1 |-> busy === 0"
    # ------------------------------------------------------------------
    async def _check_busy_deasserts_with_done(self):
        """The completion state drives busy low and done high together.

        Sampled at every rising edge while out of reset: a ``done`` pulse
        with ``busy`` still high is a violation (CONTRACT.md section 4).
        """
        dut = self.dut
        helper = self.helper
        while True:
            await RisingEdge(dut.clk)
            if self._in_reset():
                continue
            cur_done = int(helper.done)
            cur_busy = int(helper.busy)
            if cur_done == 1 and cur_busy == 1:
                self._fail(
                    "busy_deasserts_with_done",
                    f"done==1 observed while busy==1 (busy={cur_busy}, "
                    f"done={cur_done})",
                )

    # ------------------------------------------------------------------
    # Plan item: busy_high_during_operation  (severity error)
    # "$rose(busy) |=> busy throughout [*1:10]"
    # Description: busy must remain high continuously from the clock
    # after start acceptance until done pulses.
    # ------------------------------------------------------------------
    async def _check_busy_high_during_operation(self):
        """Busy must stay high throughout the entire operation.

        Detects each ``busy`` 0->1 transition (start acceptance).  From
        the edge after the rise, busy must remain 1 on every subsequent
        rising clock edge until ``done`` pulses; a fall to 0 before done
        is a violation.  Transactions aborted by reset injection are not
        penalised (the checker clears its tracking state on ``_in_reset``).
        """
        dut = self.dut
        helper = self.helper
        prev_busy = 0
        tracking = False
        while True:
            await RisingEdge(dut.clk)
            if self._in_reset():
                prev_busy = 0
                tracking = False
                continue
            cur_busy = int(helper.busy)
            cur_done = int(helper.done)
            if tracking:
                if cur_done == 1:
                    # Transaction completed (done and busy deassert
                    # together on this edge).
                    tracking = False
                elif cur_busy == 0:
                    # busy fell to 0 before done -- violation.
                    self._fail(
                        "busy_high_during_operation",
                        "busy fell to 0 before done pulse "
                        f"(busy={cur_busy} at this edge)",
                    )
            # Detect busy 0->1 rise only when not already tracking.
            if not tracking and prev_busy == 0 and cur_busy == 1:
                tracking = True
            prev_busy = cur_busy

    # ------------------------------------------------------------------
    # Plan item: no_start_ignored_while_busy  (severity warning)
    # "busy === 1 && $rose(start) |=> busy === 1"
    # ------------------------------------------------------------------
    async def _check_no_start_ignored_while_busy(self):
        """A ``start`` pulse while busy must not interrupt the operation.

        If ``start`` rises while ``busy`` is high, the next clock cycle
        must still have ``busy`` high (the ongoing transaction is not
        aborted).  Sampled at every rising edge while out of reset.
        """
        dut = self.dut
        helper = self.helper
        prev_start = 0
        # One-shot: set when we detect start rising while busy;
        # cleared on the next edge after the check.
        need_check_next = False
        while True:
            await RisingEdge(dut.clk)
            if self._in_reset():
                prev_start = 0
                need_check_next = False
                continue
            cur_start = int(helper.start)
            cur_busy = int(helper.busy)
            if need_check_next:
                need_check_next = False
                if cur_busy != 1:
                    self._warn(
                        "no_start_ignored_while_busy",
                        "busy fell to 0 on the clock after start was "
                        f"asserted while busy (busy={cur_busy})",
                    )
            if cur_busy == 1 and prev_start == 0 and cur_start == 1:
                # start rose while busy -- check the next clock edge
                need_check_next = True
            prev_start = cur_start

    # ------------------------------------------------------------------
    # Plan item: reset_clears_outputs  (severity error)
    # "$fell(rst_n) |-> ##1 busy === 0 && done === 0 && ciphertext === 0"
    # ------------------------------------------------------------------
    async def _check_reset_clears_outputs(self):
        """Within one clock of ``rst_n`` falling, all outputs must be zero.

        Detects every ``rst_n`` 1->0 transition (``$fell``) at a rising
        clock edge and samples the outputs at the *next* rising clock edge
        (``##1``).  All three outputs must be 0 at that check point.

        This checker tracks its own reset state (no ``_in_reset`` guard)
        because the check inherently spans reset-active and
        reset-inactive windows.
        """
        dut = self.dut
        helper = self.helper
        prev_rst = 1  # assume out of reset at start
        check_next = False
        while True:
            await RisingEdge(dut.clk)
            cur_rst = int(helper.rst_n)

            if check_next:
                check_next = False
                # ##1 check: one clock after $fell(rst_n)
                cur_busy = int(helper.busy)
                cur_done = int(helper.done)
                try:
                    cur_ct = int(helper.ciphertext)
                except (ValueError, TypeError):
                    # ciphertext has X/Z bits -- not zero, violation
                    cur_ct = -1  # force mismatch
                if cur_busy != 0 or cur_done != 0 or cur_ct != 0:
                    bad = {}
                    if cur_busy != 0:
                        bad["busy"] = cur_busy
                    if cur_done != 0:
                        bad["done"] = cur_done
                    if cur_ct != 0:
                        bad["ciphertext"] = cur_ct
                    self._fail(
                        "reset_clears_outputs",
                        f"outputs not at reset values on the clock after "
                        f"rst_n fell: {bad!r}",
                    )

            # Detect $fell(rst_n): prev_rst==1, cur_rst==0
            if prev_rst == 1 and cur_rst == 0:
                check_next = True  # check at the next clocking event

            prev_rst = cur_rst

    # ------------------------------------------------------------------
    # Plan item: ciphertext_valid_when_done  (severity error)
    # "done === 1 |-> !$isunknown(ciphertext)"
    # ------------------------------------------------------------------
    async def _check_ciphertext_valid_when_done(self):
        """Ciphertext must contain no unknown (X/Z/U/W) bits when done
        pulses.

        In cocotb 2.x, ``dut.ciphertext.value`` returns a ``LogicArray``
        for a 128-bit vector.  The ``is_resolvable`` property is ``True``
        only when every bit is 0, 1, L, or H (no X, Z, U, W, or -).
        An unresolved ciphertext at the done pulse is a DUT defect.
        """
        dut = self.dut
        helper = self.helper
        while True:
            await RisingEdge(dut.clk)
            if self._in_reset():
                continue
            cur_done = int(helper.done)
            if cur_done == 1:
                try:
                    ct_val = dut.ciphertext.value  # LogicArray
                    if not ct_val.is_resolvable:
                        self._fail(
                            "ciphertext_valid_when_done",
                            f"ciphertext contains unknown bits at done "
                            f"pulse: {str(ct_val)}",
                        )
                except Exception:
                    # If we cannot read ciphertext at all, report rather
                    # than silently ignoring.
                    self._fail(
                        "ciphertext_valid_when_done",
                        "could not read ciphertext value for unknown-bit "
                        "check at done pulse",
                    )

    # ------------------------------------------------------------------
    # Plan item: operation_latency  (severity error)
    # "$rose(start && !busy) |-> ##12 done === 1"
    # Note (CONTRACT.md §7.4): the acceptance cycle is counted as cycle 1;
    # done fires on cycle 12, i.e. 11 rising edges after the acceptance
    # edge.  The checker uses the transition-based acceptance detection
    # (busy 0->1) for robustness to sampling skew.
    # ------------------------------------------------------------------
    async def _check_operation_latency(self):
        """Done must occur exactly 12 clock cycles after start is sampled
        in the IDLE state.

        Acceptance is detected by the ``busy`` 0->1 transition (same
        semantics as :class:`~tb.monitor.AES128Monitor`).  The counter
        counts rising clock edges from the acceptance edge; done must
        appear exactly 11 edges later (§7.4: acceptance cycle = cycle 1,
        done = cycle 12).

        Transactions aborted by reset (busy falls without done) are
        silently ignored -- the operation was cancelled, not late.
        """
        dut = self.dut
        helper = self.helper
        # §7.4 / plan: done at cycle 12 (acceptance counted as cycle 1)
        # = 11 edges after the acceptance edge.
        _EXPECTED_EDGES = 11

        prev_busy = 0
        latched = False
        cycle_counter = 0
        while True:
            await RisingEdge(dut.clk)
            if self._in_reset():
                prev_busy = 0
                latched = False
                cycle_counter = 0
                continue
            cur_busy = int(helper.busy)
            cur_done = int(helper.done)

            if latched:
                cycle_counter += 1
                if cur_done == 1:
                    # Done pulse -- check the edge count.
                    if cycle_counter != _EXPECTED_EDGES:
                        self._fail(
                            "operation_latency",
                            f"done pulse arrived {cycle_counter + 1} "
                            f"cycles after start acceptance "
                            f"({cycle_counter} edges), expected 12 cycles "
                            f"({_EXPECTED_EDGES} edges)",
                        )
                    latched = False
                    cycle_counter = 0
                elif cur_busy == 0:
                    # busy fell without done -- operation was reset-aborted
                    # or a protocol anomaly; do not flag as a latency
                    # violation (the watchdog catches truly hung FSMs).
                    latched = False
                    cycle_counter = 0
            else:
                # Detect busy 0->1 rise (= acceptance edge).
                if prev_busy == 0 and cur_busy == 1:
                    latched = True
                    cycle_counter = 0

            prev_busy = cur_busy

    # ------------------------------------------------------------------
    # Plan item: busy_low_when_idle  (severity error)
    # "state == IDLE |-> busy === 0"
    # ------------------------------------------------------------------
    async def _check_busy_low_when_idle(self):
        """Busy must be 0 when the FSM is in IDLE state.

        Requires reading the internal ``state`` register directly from the
        DUT hierarchy (accessible via ``--public-flat-rw`` in Verilator).
        If the signal is not accessible, the check degrades gracefully
        (logged warning, skipped for the rest of the simulation).
        """
        dut = self.dut
        helper = self.helper
        while True:
            await RisingEdge(dut.clk)
            if self._in_reset():
                continue
            state_val = self._read_state()
            if state_val is None:
                # State not accessible -- skip this check.
                continue
            if state_val == _STATE_IDLE:
                cur_busy = int(helper.busy)
                if cur_busy != 0:
                    self._fail(
                        "busy_low_when_idle",
                        f"state==IDLE ({state_val}) but busy=={cur_busy}",
                    )


# ---------------------------------------------------------------------------
# Convenience launcher for the integration (environment) stage.
# ---------------------------------------------------------------------------


def launch_assertions(dut=None, helper=None, log=None):
    """Build ``AES128Assertions`` (ConfigDB-shared unless overridden) and
    launch every checker with ``cocotb.start_soon``.

    Returns the instance (``.tasks`` are the running checker coroutines).
    """
    checks = AES128Assertions(dut=dut, helper=helper, log=log)
    checks.start()
    return checks


# ---------------------------------------------------------------------------
# Watchdog (CONTRACT.md section 6; an always-running coroutine that fails
# the test if the run does not finish within a bounded number of clock
# cycles, so a hung test cannot silently exhaust the whole simulation).
#
# The watchdog is *launched* and *terminated* by the integration stage:
#   task = launch_watchdog(helper, timeout_cycles)
#   ...run the test body...
#   task.kill()          # normal completion
# If the body hangs (busy stuck, FSM dead, no done pulses), the watchdog
# keeps counting rising edges and raises once `timeout_cycles` elapses.
# ---------------------------------------------------------------------------


async def watchdog(helper, timeout_cycles, log=None):
    """Bounded clock-cycle watchdog coroutine.

    Counts rising clock edges; fails the test with an :class:`AssertionError`
    if more than ``timeout_cycles`` edges elapse without this task being
    killed by its owner (the environment kills it on normal completion).
    A hung FSM with the clock still running is guaranteed to trip it.
    """
    log = log if log is not None else _log
    cycles = 0
    while True:
        await RisingEdge(helper.dut.clk)
        cycles += 1
        if cycles > timeout_cycles:
            raise AssertionError(
                f"WATCHDOG: test did not finish within {timeout_cycles} "
                f"clock cycles; failing hung simulation"
            )


def launch_watchdog(helper=None, timeout_cycles=200000, log=None):
    """Start the bounded clock-cycle watchdog via ``cocotb.start_soon``.

    ``helper`` defaults to the ConfigDB-shared ``AES128DUTHelper``
    (CONTRACT.md key ``"dut_helper"``).  ``timeout_cycles`` is the wall of
    clock cycles no test body may exceed (generous default; the test stage
    may pick a tighter bound for a known workload).

    Returns the running cocotb task; the environment must ``kill()`` it on
    normal completion.
    """
    if helper is None:
        helper = ConfigDB().get(None, "", "dut_helper")
    task = cocotb.start_soon(
        watchdog(helper, int(timeout_cycles), log=log)
    )
    _log.info(
        "WATCHDOG: armed for %d clock cycles", int(timeout_cycles)
    )
    return task
