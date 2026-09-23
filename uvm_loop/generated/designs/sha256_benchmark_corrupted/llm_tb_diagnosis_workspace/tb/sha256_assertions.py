"""SHA-256 structural assertions (stage-5 ASSERTIONS artifact).

Implements the plan's ``useful_assertions`` as plain-Python checker
coroutines started with public Cocotb 2.1.0 ``cocotb.start_soon``.  They
run continuously, synchronized on ``RisingEdge(dut.clk)`` (CONTRACT.md
§1/§36-39), and raise ``AssertionError`` on the first violation, which
fails the test immediately -- this replaces SVA.  There is no
SystemVerilog assertion anywhere.

PLAN MAPPING (verification_plan.yaml ``useful_assertions``):

* ``reset_sets_done_high`` (severity error)
    SVA: ``!rst_n |-> (done == 1)``
    The RTL drives ``done <= 1'b1`` in its asynchronous reset branch
    (DISC-001); while reset is asserted, ``done`` must equal 1.
* ``digest_holds_until_next`` (severity error)
    SVA: ``(!start && $past(start, 1, 70)) |=> (digest == $past(digest))``
    Once a transaction has reached its fixed-cycle completion sample
    (``COMPLETION_MARGIN_CYCLES`` after its start edge) and no new start
    is being asserted, the digest must remain stable until the next
    transaction's completion window (or reset).  The plan note "qualified
    with past start to avoid reset" is honored: the check engages only
    after a genuine 0->1 start edge and is suspended while reset is
    active.
* ``transaction_completes_within_latency`` (severity error)
    SVA: ``start & !$past(start) |-> ##[64:70] (digest != 0)``
    After a genuine start edge the DUT must produce a non-zero digest
    within [``EXPECTED_LATENCY_CYCLES``, ``COMPLETION_MARGIN_CYCLES``]
    (64..70, CONTRACT.md §7) cycles.  Completion is tracked by fixed cycle
    count -- the broken ``done`` pin is never used to infer completion
    (DISC-001/DISC-013).  ``digest != 0`` at any cycle inside the band
    satisfies the window; still zero after start+70 is a violation.
    NOTE (corrupted RTL): digest is only assigned under ``round == 62``
    which the RTL never reaches (DISC-008/014), so this assertion is
    expected to FIRE on this DUT -- it is the structural detection of
    "no completion ever".

A deterministic WATCHDOG coroutine is provided as well (CONTRACT.md
§1/§7): ``Sha256Assertions.start_watchdog(budget_cycles)`` fails the test
if ``budget_cycles`` clock cycles elapse without ``disarm_watchdog()``,
so a hung test cannot exhaust the whole simulation run.  (The env/test
stage may equally wrap its test body in
``cocotb.triggers.with_timeout`` instead; this module supplies the
always-running alternative.)

The per-edge decision logic is factored into pure functions
(``_step_digest_hold`` / ``_step_latency``) so the checker behaviour can
be unit-tested without a simulator; the coroutines only sample the pins
(through the shared ``Sha256Pins`` helper, ConfigDB key ``"sha256_pins"``,
§5) and feed the steps.
"""

import logging

import cocotb

from cocotb.triggers import RisingEdge

from sha256_pins import (
    COMPLETION_MARGIN_CYCLES,
    EXPECTED_LATENCY_CYCLES,
    WATCHDOG_MARGIN_CYCLES,
    Sha256Pins,
)


# ----------------------------------------------------------------------
# Pure per-edge decision logic (unit-testable, no cocotb required)
# ----------------------------------------------------------------------
def _step_digest_hold(state: dict, *, in_reset: bool, cur_start: int,
                      cur_digest: int):
    """Advance the ``digest_holds_until_next`` state machine one edge.

    ``state`` keys: ``cycle`` (last processed edge, starts at 0),
    ``prev_start``, ``prev_digest``, ``completion_cycle`` (edge at which the
    current transaction's fixed-latency completion sample lands, or None).

    Returns ``(new_state, violation_message_or_None)``.
    """
    cycle = state["cycle"] + 1
    out = dict(state)
    out["cycle"] = cycle

    if in_reset:
        # Reset invalidates any hold contract ("qualified ... to avoid
        # reset"): re-sync history, no check this edge.
        out["prev_start"] = cur_start
        out["prev_digest"] = cur_digest
        out["completion_cycle"] = None
        return out, None

    prev_start = state["prev_start"]

    if cur_start == 1 and prev_start == 0:
        # Genuine start edge: a new transaction runs; the digest may change
        # until its completion sample lands COMPLETION_MARGIN_CYCLES later.
        out["completion_cycle"] = cycle + COMPLETION_MARGIN_CYCLES
    elif out["completion_cycle"] is not None and cycle > out["completion_cycle"]:
        # Past the last completion sample and not starting: the digest must
        # hold its value until the next transaction completes (or reset).
        prev_digest = state["prev_digest"]
        if cur_digest != prev_digest:
            return out, (
                f"digest_holds_until_next violated: digest changed while no "
                f"transaction was in flight (cycle {cycle} > completion "
                f"cycle {out['completion_cycle']}): 0x{prev_digest:064x} -> "
                f"0x{cur_digest:064x}. Digest must hold until the next "
                f"transaction completes."
            )

    out["prev_start"] = cur_start
    out["prev_digest"] = cur_digest
    return out, None


def _step_latency(state: dict, *, in_reset: bool, cur_start: int,
                  cur_digest: int):
    """Advance the ``transaction_completes_within_latency`` machine one edge.

    ``state`` keys: ``cycle`` (last processed edge, starts at 0),
    ``prev_start``, ``pending`` (list of start-cycle ticks of transactions
    whose non-zero-digest window [start+64, start+70] is still open).

    Returns ``(new_state, violation_message_or_None)``.
    """
    cycle = state["cycle"] + 1
    out = dict(state)
    out["cycle"] = cycle

    if in_reset:
        # Reset clears all open latency windows (no completion contract).
        out["pending"] = []
        out["prev_start"] = cur_start
        return out, None

    prev_start = state["prev_start"]
    pending = list(out["pending"])

    if cur_start == 1 and prev_start == 0:
        pending.append(cycle)

    still_open = []
    for start_cycle in pending:
        band_lo = start_cycle + EXPECTED_LATENCY_CYCLES
        band_hi = start_cycle + COMPLETION_MARGIN_CYCLES
        if cur_digest != 0 and band_lo <= cycle <= band_hi:
            continue  # satisfied: non-zero digest observed inside the band
        if cycle > band_hi:
            return out, (
                f"transaction_completes_within_latency violated: transaction "
                f"started at cycle {start_cycle} did not produce a non-zero "
                f"digest within {EXPECTED_LATENCY_CYCLES}.."
                f"{COMPLETION_MARGIN_CYCLES} cycles (digest still "
                f"0x{cur_digest:064x} at cycle {cycle}). The RTL never "
                f"reaches its completion state (digest assignment gated on "
                f"round==62, DISC-008/014)."
            )
        still_open.append(start_cycle)

    out["pending"] = still_open
    out["prev_start"] = cur_start
    return out, None


# ----------------------------------------------------------------------
# Checker controller
# ----------------------------------------------------------------------
class Sha256Assertions:
    """Owns the three structural checker coroutines and the watchdog.

    Plain Python (not a UVM component): it reads the DUT pins through the
    shared ``Sha256Pins`` helper and raises AssertionError on violation.
    """

    def __init__(self, pins: Sha256Pins = None, logger=None) -> None:
        if pins is None:
            from pyuvm import ConfigDB

            pins = ConfigDB().get(None, "", "sha256_pins")
            if pins is None:
                raise RuntimeError(
                    "CONTRACT key 'sha256_pins' missing from ConfigDB: "
                    "cannot run structural assertions."
                )
        self.pins = pins
        self.log = logger or logging.getLogger("sha256_assertions")
        self.tasks = []                 # started checker tasks
        self.watchdog_task = None       # started watchdog task (if any)
        self._watchdog_disarmed = False

    # ------------------------------------------------------------------
    # Launch API (public Cocotb 2.1.0 cocotb.start_soon)
    # ------------------------------------------------------------------
    def start(self) -> list:
        """Start the three plan assertions as background cocotb coroutines.

        An unhandled AssertionError in any of them fails the test.
        """
        self.tasks = [
            cocotb.start_soon(self.check_reset_sets_done_high()),
            cocotb.start_soon(self.check_digest_holds_until_next()),
            cocotb.start_soon(self.check_transaction_completes_within_latency()),
        ]
        return self.tasks

    def start_watchdog(self, budget_cycles: int = WATCHDOG_MARGIN_CYCLES):
        """Start the always-running watchdog coroutine.

        It fails the test if ``budget_cycles`` clock cycles elapse without
        :meth:`disarm_watchdog`.  ``budget_cycles`` defaults to
        ``WATCHDOG_MARGIN_CYCLES`` (CONTRACT.md §7)."""
        self._watchdog_disarmed = False
        self.watchdog_task = cocotb.start_soon(
            self.check_watchdog(int(budget_cycles))
        )
        return self.watchdog_task

    def disarm_watchdog(self) -> None:
        """Disarm the watchdog (call when the test body finishes normally)."""
        self._watchdog_disarmed = True

    # ------------------------------------------------------------------
    # Plan assertion: reset_sets_done_high
    # ------------------------------------------------------------------
    async def check_reset_sets_done_high(self) -> None:
        """``!rst_n |-> (done == 1)`` -- plan 'reset_sets_done_high'.

        The RTL drives ``done <= 1'b1`` while reset is asserted (DISC-001);
        this checker samples on every rising edge and fails immediately if
        reset is active while ``done != 1``.
        """
        await RisingEdge(self.pins.clk)  # sync; never sample time zero
        while True:
            await RisingEdge(self.pins.clk)
            rst_n = self._read("rst_n")
            if rst_n == 0:
                done = self._read("done")
                if done != 1:
                    raise AssertionError(
                        f"reset_sets_done_high violated: rst_n=0 (reset "
                        f"asserted) but done={done} (expected 1 -- the RTL "
                        f"drives done=1 on reset, DISC-001)."
                    )

    # ------------------------------------------------------------------
    # Plan assertion: digest_holds_until_next
    # ------------------------------------------------------------------
    async def check_digest_holds_until_next(self) -> None:
        """``(!start && $past(start,1,70)) |=> (digest == $past(digest))``.

        Digest must remain stable between transactions: once a transaction
        has reached its fixed-cycle completion sample
        (``COMPLETION_MARGIN_CYCLES`` after its start edge) and no new start
        is being asserted, the digest must not change until the next
        transaction's completion window or reset.
        """
        state = {
            "cycle": 0,
            "prev_start": self._read("start"),
            "prev_digest": self._read("digest"),
            "completion_cycle": None,
        }
        while True:
            await RisingEdge(self.pins.clk)
            rst_n = self._read("rst_n")
            cur_start = self._read("start")
            cur_digest = self._read("digest")
            state, violation = _step_digest_hold(
                state, in_reset=(rst_n == 0),
                cur_start=cur_start, cur_digest=cur_digest,
            )
            if violation is not None:
                self._fail(violation)

    # ------------------------------------------------------------------
    # Plan assertion: transaction_completes_within_latency
    # ------------------------------------------------------------------
    async def check_transaction_completes_within_latency(self) -> None:
        """``start & !$past(start) |-> ##[64:70] (digest != 0)``.

        After a genuine start edge the DUT must produce a non-zero digest
        within [64, 70] cycles (fixed-cycle completion model, CONTRACT.md
        §7).  ``digest != 0`` at any cycle inside the band satisfies the
        window; still zero after start+70 is a violation.  The broken
        ``done`` pin is never used to infer completion.
        """
        state = {
            "cycle": 0,
            "prev_start": self._read("start"),
            "pending": [],
        }
        while True:
            await RisingEdge(self.pins.clk)
            rst_n = self._read("rst_n")
            cur_start = self._read("start")
            cur_digest = self._read("digest")
            state, violation = _step_latency(
                state, in_reset=(rst_n == 0),
                cur_start=cur_start, cur_digest=cur_digest,
            )
            if violation is not None:
                self._fail(violation)

    # ------------------------------------------------------------------
    # Watchdog (always-running hang detector, CONTRACT.md §1/§7)
    # ------------------------------------------------------------------
    async def check_watchdog(self, budget_cycles: int) -> None:
        """Fail the test if ``budget_cycles`` cycles elapse un-disarmed.

        Counts rising edges of ``clk``; the env/test stage disarms it when
        its scenarios finish (or uses a with_timeout wrapper instead).
        """
        for _ in range(max(1, int(budget_cycles))):
            await RisingEdge(self.pins.clk)
            if self._watchdog_disarmed:
                return
        raise AssertionError(
            "WATCHDOG: test did not finish within the bounded "
            f"{budget_cycles}-cycle budget (CONTRACT.md §7, "
            f"WATCHDOG_MARGIN_CYCLES={WATCHDOG_MARGIN_CYCLES}). A hung "
            "test cannot be allowed to exhaust the whole simulation run."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fail(self, violation: str) -> None:
        """Log the violation and raise -- this fails the test immediately."""
        self.log.error("ASSERTION FAILED: %s", violation)
        raise AssertionError(violation)

    def _read(self, what: str) -> int:
        if what == "rst_n":
            # Sha256Pins exposes the raw handle for rst_n; use the standard
            # Cocotb 2.1.0 read path (int(value)) with an X/Z guard.
            try:
                return int(self.pins.rst_n.value)
            except ValueError as exc:
                self.log.warning(
                    "Pin 'rst_n' not resolvable (X/Z at sample time) -- "
                    "sampling 0. %s",
                    exc,
                )
                return 0
        reader = {
            "start": self.pins.read_start,
            "done": self.pins.read_done,
            "digest": self.pins.read_digest,
        }[what]
        try:
            return int(reader())
        except ValueError as exc:
            self.log.warning(
                "Pin '%s' not resolvable (X/Z at sample time) -- sampling 0. %s",
                what,
                exc,
            )
            return 0


# ----------------------------------------------------------------------
# Module-level convenience launch helper (used by the env/test stage)
# ----------------------------------------------------------------------
def start_assertions(pins: Sha256Pins = None) -> Sha256Assertions:
    """Build and start every plan assertion checker.

    ``pins`` may be passed explicitly or fetched from ConfigDB under the
    exact ``"sha256_pins"`` key (CONTRACT.md §5/§13 retrieval form).
    Returns the controller (call ``disarm_watchdog`` / ``start_watchdog``
    as desired).
    """
    controller = Sha256Assertions(pins)
    controller.start()
    return controller