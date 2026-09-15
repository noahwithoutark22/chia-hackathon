"""Stage 5 (assertions) artifact of the CHIA generator: SVA-replacement
Python checkers for the i2c_master bench.

Per CONTRACT.md section 8 there is no SystemVerilog assertion language in
this project.  Every plan item in ``useful_assertions`` is implemented as a
plain-Python checker *coroutine* that runs continuously, synchronized on
the rising edge of the DUT clock via cocotb triggers, and is launched with
``cocotb.start_soon``.  A violated check is flagged immediately:

* **severity "error"**  -> logged as an error and raised as an
  ``AssertionError``, which propagates out of the checker task and fails
  the enclosing cocotb test immediately (the SVA ``assert`` equivalent).
* **severity "warning"** -> logged as a warning and counted in
  ``violations`` (the SVA ``cover``/info equivalent); warnings document
  design rules and do not by themselves fail the test.

The plan's six assertions are implemented here, each as a method whose
name and docstring tie it back to its plan item:

========= ================================================= ==========
plan name check                                             severity
========= ================================================= ==========
reset_clears_outputs            busy/done/ack_error==0, read_data==0x00 on the first clock edge after rst_n deassert          error
busy_deasserted_after_done      done==1 implies busy==0                     error
done_pulses_exactly_one_cycle   done never high two consecutive cycles      error
ack_error_implies_unsupported_address  ack_error==1 at done implies the *request-latched* slave_addr != 0x50   error
no_simultaneous_start_done      never (done==1 && start==1)                warning
scl_sda_released_in_idle        bus lines not driven low while busy==0      warning
========= ================================================= ==========

Sampling semantics (important): all checkers sample pins *after* each
``RisingEdge`` (i.e. the post-edge register values, which is what SVA on
``posedge clk`` observes for register outputs).  Reset is asynchronous and
active low; every checker skips sampling while ``rst_n`` is not high so the
pre-reset / unknown-value window (``x``/``z``) cannot produce spurious
failures, and the ``done`` cycle itself (busy==0, done==1, both open-drain
lines released after STOP_PHASE) passes every rule above.  The
``ack_error_implies_unsupported_address`` checker additionally probes the
stimulus pins at the request-latch point (the mid-cycle falling edge and
the latching rising edge, exactly ``I2CMonitor``'s sampling discipline) so
it can pair each ``done`` pulse with the *latched* slave address instead of
the released pin, which the driver returns to 0x00 right after latching.

The integration (environment) stage starts the checkers via
:func:`launch_assertions` (or ``I2CAssertions.start()``) and reports the
``violations`` counters at end of test.  The always-running watchdog
requested by CONTRACT.md section 8 is provided here as
:func:`launch_watchdog` (a bounded clock-cycle runner that the environment
starts and kills on normal completion).
"""

import logging

import cocotb
from cocotb.triggers import FallingEdge, RisingEdge
from pyuvm import ConfigDB

from tb.dut_helper import KEY_CLK_RST, KEY_DUT_PINS, W_SLAVE_ADDR, _to_int

__all__ = [
    "I2CAssertions",
    "ASSERTION_SEVERITY",
    "launch_assertions",
    "launch_watchdog",
    "watchdog",
]

#: Module logger (cocotb configures the logging hierarchy at sim start).
_log = logging.getLogger("tb.assertions")


# ---------------------------------------------------------------------------
# Plan metadata (useful_assertions).
# ---------------------------------------------------------------------------


ASSERTION_SEVERITY = {
    # plan name                     -> plan severity
    "reset_clears_outputs": "error",
    "busy_deasserted_after_done": "error",
    "done_pulses_exactly_one_cycle": "error",
    "ack_error_implies_unsupported_address": "error",
    "no_simultaneous_start_done": "warning",
    "scl_sda_released_in_idle": "warning",
}

#: The one I2C slave address that must never NACK (CONTRACT.md section 2).
SUPPORTED_SLAVE_ADDR = 0x50


# ---------------------------------------------------------------------------
# Checker collection.
# ---------------------------------------------------------------------------


class I2CAssertions:
    """Always-running Python assertion checkers for the i2c_master DUT.

    Constructor arguments are optional; when omitted, the shared
    ``I2CDutPins`` / ``ClockReset`` objects are fetched from pyuvm's
    ``ConfigDB`` using exactly the CONTRACT.md keys (``KEY_DUT_PINS`` /
    ``KEY_CLK_RST``).

    Usage (integration stage)::

        checks = I2CAssertions()          # or via launch_assertions()
        tasks = checks.start()            # cocotb.start_soon per checker
        ...
        checks.summarize()                # end-of-test report of violations

    Error-severity checkers raise :class:`AssertionError` on the first
    violation (the enclosing cocotb test fails immediately); warning-level
    checkers log and count.  ``violations`` maps plan-name -> count of
    times the check has failed or warned.
    """

    def __init__(self, pins=None, clkrs=None, log=None):
        #: Shared pin helper (CONTRACT.md key KEY_DUT_PINS).
        self.pins = (pins if pins is not None
                     else ConfigDB().get(None, "", KEY_DUT_PINS))
        #: Shared clock/reset descriptor (CONTRACT.md key KEY_CLK_RST).
        self.clkrs = (clkrs if clkrs is not None
                      else ConfigDB().get(None, "", KEY_CLK_RST))
        self.log = log if log is not None else _log
        #: Running cocotb tasks, one per checker (filled by start()).
        self.tasks = []
        #: plan-name -> number of violations/warnings observed so far.
        self.violations = {name: 0 for name in ASSERTION_SEVERITY}
        self._started = False

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
            cocotb.start_soon(self._check_reset_clears_outputs()),
            cocotb.start_soon(self._check_busy_deasserted_after_done()),
            cocotb.start_soon(self._check_done_pulses_exactly_one_cycle()),
            cocotb.start_soon(
                self._check_ack_error_implies_unsupported_address()),
            cocotb.start_soon(self._check_no_simultaneous_start_done()),
            cocotb.start_soon(self._check_scl_sda_released_in_idle()),
        ]
        self.log.info(
            "I2CAssertions: launched %d checker coroutines via "
            "cocotb.start_soon", len(self.tasks))
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
            if count)
        if not counts:
            counts = "none"
        return (f"I2CAssertions: {len(self.tasks)} active checkers, "
                f"violations -> {counts}")

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _in_reset(self):
        """True while ``rst_n`` is asserted (0) or still unknown (x/z).

        Reset is active-low and asynchronous (CONTRACT.md section 3); all
        checkers skip sampling during this window so the pre-reset X window
        and power-up cannot fabricate violations.
        """
        return _to_int(self.pins.rst_n.value, 1) != 1

    def _fail(self, name, message):
        """Flag an error-severity violation: log + raise immediately."""
        assert ASSERTION_SEVERITY[name] == "error", \
            f"internal: {name} is not an error-severity assertion"
        self.violations[name] += 1
        self.log.error(
            "[assertion %s] FAILED: %s", name, message)
        raise AssertionError(f"assertion '{name}' failed: {message}")

    def _warn(self, name, message):
        """Flag a warning-severity violation: log + count (non-fatal)."""
        assert ASSERTION_SEVERITY[name] == "warning", \
            f"internal: {name} is not a warning-severity assertion"
        self.violations[name] += 1
        self.log.warning(
            "[assertion %s] WARNING: %s", name, message)

    # ------------------------------------------------------------------
    # Plan item: reset_clears_outputs  (severity error)
    # "At the first clock edge after deasserting rst_n: busy == 0 && done
    #  == 0 && ack_error == 0 && read_data == 0x00"
    # ------------------------------------------------------------------
    async def _check_reset_clears_outputs(self):
        """Spec section 2 reset contract on the DUT outputs.

        Detects every ``rst_n`` 0 -> 1 transition across rising clock
        edges and samples the outputs at that very edge; all four must
        still hold their reset values (busy/done/ack_error == 0 and
        read_data == 0x00).  Re-arms automatically for every subsequent
        reset assertion.
        """
        pins = self.pins
        prev_rst = _to_int(pins.rst_n.value, 1)
        while True:
            await RisingEdge(pins.clk)
            cur_rst = _to_int(pins.rst_n.value, 1)
            if prev_rst == 0 and cur_rst == 1:
                outs = pins.sample_outputs()
                bad = {}
                for key, want in (("busy", 0), ("done", 0),
                                  ("ack_error", 0), ("read_data", 0x00)):
                    if int(outs[key]) != int(want):
                        bad[key] = int(outs[key])
                if bad:
                    self._fail(
                        "reset_clears_outputs",
                        f"outputs not at reset values on the first clock "
                        f"edge after rst_n deassertion: {bad!r}")
            prev_rst = cur_rst

    # ------------------------------------------------------------------
    # Plan item: busy_deasserted_after_done  (severity error)
    # "done == 1 implies busy == 0"
    # ------------------------------------------------------------------
    async def _check_busy_deasserted_after_done(self):
        """The completion state drives busy low and done high together
        (reference model ``busy_after == 0``).  Sampled at every rising
        edge while out of reset: a ``done`` pulse with ``busy`` still high
        is a violation.
        """
        pins = self.pins
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                continue
            if (_to_int(pins.done.value, 1) == 1
                    and _to_int(pins.busy.value, 1) == 1):
                self._fail(
                    "busy_deasserted_after_done",
                    f"done==1 observed while busy==1 (busy={pins.busy.value}, "
                    f"done={pins.done.value})")

    # ------------------------------------------------------------------
    # Plan item: done_pulses_exactly_one_cycle  (severity error)
    # "(done == 1) at cycle N implies (done == 0) at cycle N+1"
    # ------------------------------------------------------------------
    async def _check_done_pulses_exactly_one_cycle(self):
        """Guards the single-cycle completion-pulse behavior.

        ``done`` is a register cleared on every clock edge except the
        COMPLETE cycle; two consecutive post-edge samples with done==1
        therefore mean the pulse spanned two cycles (a DUT defect).
        Reset history is reset whenever the FSM is (re)initialized.
        """
        pins = self.pins
        prev_done = 0
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                prev_done = 0
                continue
            cur_done = _to_int(pins.done.value, 1)
            if prev_done == 1 and cur_done == 1:
                self._fail(
                    "done_pulses_exactly_one_cycle",
                    f"done stayed high for two consecutive clock cycles "
                    f"(cycle N and cycle N+1 both sampled done==1)")
            prev_done = cur_done

    # ------------------------------------------------------------------
    # Plan item: ack_error_implies_unsupported_address  (severity error)
    # "On done with ack_error == 1: slave_addr != 0x50"
    # ------------------------------------------------------------------
    async def _check_ack_error_implies_unsupported_address(self):
        """The supported address 0x50 must never produce a NACK.

        The released ``slave_addr`` pin cannot be used for this check: the
        driver returns the stimulus pins to idle defaults immediately after
        the DUT latches a request, so by the time the ``done`` pulse fires
        (CONTRACT.md section 6) the pin already reads 0x00 and the check
        would be a vacuous no-op.  Instead, this checker reconstructs the
        *latched* slave address at the request-latch point, mirroring
        ``I2CMonitor``'s sampling discipline, and pairs each ``done`` pulse
        with it:

        1. **Rising-edge request-latch probe** -- ``start==1`` while
           ``busy==0`` at the latching rising edge (covers offers driven in
           the low clock phase; like the monitor, this always-running edge
           wait resumes before the driver's one-shot release, so the pins
           still carry the values the DUT just latched).
        2. **Mid-cycle falling-edge probe** -- the same condition sampled at
           the falling edge inside the offer cycle (covers offers driven in
           the high clock phase).  The captured address is committed only
           *after* the next done-edge evaluation, so a done pulse is never
           paired with the next back-to-back offer.

        At every rising edge, done-edge evaluation takes precedence over
        offer latching: ``done==1`` with ``ack_error==1`` is compared
        against the address that was latched for the transaction actually
        completing.  ``None`` (before any offer, or cleared by reset)
        cannot be correlated and is skipped conservatively.  Reset injection
        clears the latched state, so a reset-aborted transaction can never
        leave a stale pairing behind.
        """
        pins = self.pins
        #: Address latched at the most recent request-latch point -- the
        #: address of the transaction whose done pulse is expected next
        #: (None while unknown / between resets).
        latched_addr = None
        #: Address captured by the mid-cycle falling-edge probe; the DUT
        #: latches that offer at the *next* rising edge, so it is committed
        #: only after the done-edge evaluation of that edge.
        pending_addr = None
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                latched_addr = None
                pending_addr = None
                continue

            # Done-edge evaluation takes precedence over offer latching: a
            # done pulse coinciding with the next back-to-back offer is
            # checked against the address latched for the transaction that
            # is actually completing.
            if (_to_int(pins.done.value, 1) == 1
                    and _to_int(pins.ack_error.value, 1) == 1
                    and latched_addr == SUPPORTED_SLAVE_ADDR):
                self._fail(
                    "ack_error_implies_unsupported_address",
                    f"done with ack_error==1 while the request-latched "
                    f"slave_addr was the supported address "
                    f"{SUPPORTED_SLAVE_ADDR:#04x} (supported addresses "
                    f"must never be NACKed)")

            # Commit an offer seen at the previous mid-cycle probe: its
            # latching edge is this rising edge.
            if pending_addr is not None:
                latched_addr = pending_addr
                pending_addr = None
            # Rising-edge request-latch probe (low-phase offers).
            if (_to_int(pins.start.value, 1) == 1
                    and _to_int(pins.busy.value, 1) == 0):
                latched_addr = _to_int(pins.slave_addr.value, W_SLAVE_ADDR)

            # Mid-cycle falling-edge probe (high-phase offers): capture the
            # offer now and commit its address at the next rising edge.
            await FallingEdge(pins.clk)
            if self._in_reset():
                latched_addr = None
                pending_addr = None
                continue
            if (_to_int(pins.start.value, 1) == 1
                    and _to_int(pins.busy.value, 1) == 0):
                pending_addr = _to_int(pins.slave_addr.value, W_SLAVE_ADDR)

    # ------------------------------------------------------------------
    # Plan item: no_simultaneous_start_done  (severity warning)
    # "never (done == 1 && start == 1)"
    # ------------------------------------------------------------------
    async def _check_no_simultaneous_start_done(self):
        """Keeps transactions well separated in the scoreboard's FIFO.

        Sampled at every rising edge while out of reset.  Request cycles
        are defined by a distinct ``start`` pulse; a ``start`` overlap with
        the completion pulse would collapse the two transactions into one
        window.  (Note: the driver may drive the *next* offer's ``start``
        during the high phase of the ``done`` cycle, but edge-sampled
        checks observe ``start==0`` at the done-pulse edge, so this rule
        holds in normal operation.)
        """
        pins = self.pins
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                continue
            if (_to_int(pins.done.value, 1) == 1
                    and _to_int(pins.start.value, 1) == 1):
                self._warn(
                    "no_simultaneous_start_done",
                    f"done==1 and start==1 sampled at the same clock edge "
                    f"(done={pins.done.value}, start={pins.start.value})")

    # ------------------------------------------------------------------
    # Plan item: scl_sda_released_in_idle  (severity warning)
    # "When busy == 0 ...: scl != 0 and sda != 0" (open-drain release)
    # ------------------------------------------------------------------
    async def _check_scl_sda_released_in_idle(self):
        """Verifies the open-drain release behavior between transactions.

        While ``busy == 0`` (idle, including the completion cycle) neither
        open-drain line may be actively driven low: ``scl``/``sda`` must
        read ``z`` (released, no pull-up) or ``1`` (released plus pull-up),
        exactly what ``I2CDutPins.scl_is_released()`` /
        ``sda_is_released()`` report.  Mid-transaction (``busy==1``) the
        lines are legitimately driven low and are skipped.
        """
        pins = self.pins
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                continue
            if _to_int(pins.busy.value, 1) != 0:
                continue  # active transaction: lines may be driven
            if not pins.scl_is_released():
                self._warn(
                    "scl_sda_released_in_idle",
                    f"scl actively driven low ({pins.scl_level()!r}) while "
                    f"busy==0 (open-drain line must be released)")
            if not pins.sda_is_released():
                self._warn(
                    "scl_sda_released_in_idle",
                    f"sda actively driven low ({pins.sda_level()!r}) while "
                    f"busy==0 (open-drain line must be released)")


# ---------------------------------------------------------------------------
# Convenience launcher for the integration (environment) stage.
# ---------------------------------------------------------------------------


def launch_assertions(pins=None, clkrs=None, log=None):
    """Build ``I2CAssertions`` (ConfigDB-shared pins unless given) and
    launch every checker with ``cocotb.start_soon``.  Returns the instance
    (``.tasks`` are the running checker coroutines)."""
    checks = I2CAssertions(pins=pins, clkrs=clkrs, log=log)
    checks.start()
    return checks


# ---------------------------------------------------------------------------
# Watchdog (CONTRACT.md section 8; an always-running coroutine that fails
# the test if the run does not finish within a bounded number of clock
# cycles, so a hung test cannot silently exhaust the whole simulation).
#
# The watchdog is *launched* and *terminated* by the integration stage:
#   task = launch_watchdog(pins, clkrs, timeout_cycles)
#   ...run the test body...
#   task.kill()          # normal completion
# If the body hangs (busy stuck, FSM dead, no done pulses), the watchdog
# keeps counting rising edges and raises once `timeout_cycles` elapses.
# ---------------------------------------------------------------------------


async def watchdog(pins, clkrs, timeout_cycles, log=None):
    """Bounded clock-cycle watchdog coroutine.

    Counts rising clock edges; fails the test with an :class:`AssertionError`
    if more than ``timeout_cycles`` edges elapse without this task being
    killed by its owner (the environment kills it on normal completion).
    A hung FSM with the clock still running is guaranteed to trip it.
    """
    log = log if log is not None else _log
    timeframe_ns = timeout_cycles * int(clkrs.clock_period_ns)
    cycles = 0
    while True:
        await RisingEdge(pins.clk)
        cycles += 1
        if cycles > timeout_cycles:
            raise AssertionError(
                f"WATCHDOG: test did not finish within {timeout_cycles} "
                f"clock cycles (~{timeframe_ns} ns at {clkrs.clock_period_ns}"
                f" ns period); failing hung simulation")


def launch_watchdog(pins=None, clkrs=None, timeout_cycles=200000, log=None):
    """Start the bounded clock-cycle watchdog via ``cocotb.start_soon``.

    ``pins``/``clkrs`` default to the ConfigDB-shared ``I2CDutPins`` /
    ``ClockReset`` (CONTRACT.md keys).  ``timeout_cycles`` is the wall of
    clock cycles no test body may exceed (generous default; the test stage
    may pick a tighter bound for a known workload).  Returns the running
    cocotb task; the environment must ``kill()`` it on normal completion.
    """
    pins = (pins if pins is not None
            else ConfigDB().get(None, "", KEY_DUT_PINS))
    clkrs = (clkrs if clkrs is not None
             else ConfigDB().get(None, "", KEY_CLK_RST))
    task = cocotb.start_soon(
        watchdog(pins, clkrs, int(timeout_cycles), log=log))
    _log.info(
        "WATCHDOG: armed for %d clock cycles", int(timeout_cycles))
    return task