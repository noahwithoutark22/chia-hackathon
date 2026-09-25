"""AES-128 assertions (stage-5 ASSERTIONS artifact): SVA-replacement
Python checkers for the ``aes128`` DUT.

There is no SystemVerilog assertion language in this project (CONTRACT.md
§8).  Every plan item in ``useful_assertions`` is implemented as a
plain-Python checker *coroutine* that runs continuously, synchronized on
the DUT clock via public Cocotb 2.1.0 triggers, and is launched with
``cocotb.start_soon``.  A violated check is flagged immediately: the
checker logs an error, counts the violation, and raises ``AssertionError``
out of its coroutine body, which fails the enclosing cocotb test at once
(the SVA ``assert`` equivalent).

PLAN MAPPING (verification_plan.yaml ``useful_assertions``; every item is
severity "error"):

``reset_returns_dut_to_idle``
    After reset release ``done == 0`` and a following ``start`` offer is
    accepted within a bounded number of cycles.  Detects DISC-01 (the
    reset branch leaving ``busy`` high so no transaction can ever start).

``start_requires_idle``
    A ``start`` asserted during an active transaction must be ignored: the
    active transaction must complete with the ciphertext predicted from the
    *originally captured* key/plaintext.  If a mid-flight start altered the
    result this check fires.

``done_pulse_width_one``
    ``done`` must never stay high for two consecutive clock cycles (pulses
    exactly one cycle per completed transaction and does not remain high).

``transaction_terminates``
    Every accepted ``start`` (offer sampled while the DUT is idle) must
    produce a ``done`` pulse within a bounded number of cycles after the
    ~10 AES rounds.  Detects DISC-01/DISC-02 (encryption never completes,
    ``done`` never asserted).

``ciphertext_matches_reference``
    When ``done`` is sampled high, ``ciphertext`` must equal
    ``aes128_reference_model.aes128_encrypt(plaintext, key)`` for the key/
    plaintext captured at the transaction that started it.

``fips197_known_answer``
    The FIPS-197 vector (key 0x000102030405060708090a0b0c0d0e0f,
    plaintext 0x00112233445566778899aabbccddeeff) must produce ciphertext
    0x69c4e0d86a7b0430d8cdb78070b4c55a.

SAMPLING TIMING (CONTRACT.md §2/§6 and the stage-3 observation additions
§9.1 -- not re-derived here)
--------------------------------
* Stimulus (``start`` / ``key`` / ``plaintext``) is sampled with the
  mid-cycle *falling-edge* probe: the driver holds the offer stable for one
  full clock cycle, so the values read at the falling edge are exactly the
  values the DUT latches on the following rising edge.  A rising-edge probe
  of ``start`` would be racy with the driver's same-edge deassert.
* Outputs (``done`` / ``ciphertext``) are sampled post-edge
  (``await RisingEdge(...)`` then ``await ReadOnly()``), the same
  sampling convention as the monitor and sequences; ``ciphertext`` is only
  meaningful while ``done`` is high.
* Reset state is taken from the post-edge ``rst_n`` sample, matching the
  DUT's synchronous sampling of ``rst_n`` at the rising edge.

Each checker coroutine advances its own independent state machine (no
shared mutable per-edge counters between checkers), so the checkers can be
started/stopped in any combination and never interfere with each other.

A deterministic WATCHDOG coroutine is also provided (CONTRACT.md §8 /
stage rule): ``launch_watchdog`` starts an always-running coroutine that
fails the test if more than ``timeout_cycles`` clock cycles elapse without
the owner (environment/test stage) killing it on normal completion, so a
hung simulation cannot silently exhaust the whole run.  The test stage may
equally wrap its body in ``cocotb.triggers.with_timeout`` instead; this
module supplies the always-running alternative.

All APIs used here are public Cocotb 2.1.0 (``cocotb.start_soon``,
``cocotb.triggers``) and public pyuvm 5.0.0 (``ConfigDB``).  No
SystemVerilog anywhere.
"""

import importlib
import logging
import os
import sys

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

from pyuvm import ConfigDB

__all__ = [
    "Aes128Assertions",
    "ASSERTION_SEVERITY",
    "launch_assertions",
    "watchdog",
    "launch_watchdog",
    "WATCHDOG_DEFAULT_CYCLES",
]

_log = logging.getLogger("tb.assertions")

# ---------------------------------------------------------------------------
# Plan / CONTRACT constants
# ---------------------------------------------------------------------------

#: Mask for all 128-bit buses (CONTRACT.md §2).
MASK128 = (1 << 128) - 1

# FIPS-197 known-answer constants (plan ``fips197_known_answer``; the same
# values as the sequences / reference-model TEST_VECTORS).
KEY_FIPS197 = 0x000102030405060708090A0B0C0D0E0F
PT_FIPS197 = 0x00112233445566778899AABBCCDDEEFF
CT_FIPS197 = 0x69C4E0D86A7B0430D8CDB78070B4C55A

#: Bounded "time to done" window for an accepted start (clock cycles).
#: A correct DUT pulses ``done`` ~12-14 cycles after the start edge (10 AES
#: rounds plus registration); 80 cycles is a >5x margin for any correct
#: implementation and far below the sequences' own 200-cycle done waits, so
#: the SVA-equivalent checker is the first fence against a hung/stuck FSM
#: (DISC-01/DISC-02: no ``done`` is ever produced).
DONE_WINDOW_CYCLES = 80

#: Default watchdog budget (clock cycles).  Generous: the directed/random
#: workloads finish in a few thousand cycles; 100000 only trips on a truly
#: hung simulation.  The test stage may arm a tighter bound for a known
#: workload.
WATCHDOG_DEFAULT_CYCLES = 100000

#: Plan item severity mapping (all six useful_assertions are "error").
ASSERTION_SEVERITY = {
    "reset_returns_dut_to_idle": "error",
    "start_requires_idle": "error",
    "done_pulse_width_one": "error",
    "transaction_terminates": "error",
    "ciphertext_matches_reference": "error",
    "fips197_known_answer": "error",
}


# ---------------------------------------------------------------------------
# Reference-model access (CONTRACT.md §3; same resolution order as the
# scoreboard, but non-fatal: the checker degrades to a logged warning if the
# oracle is unavailable rather than refusing to run).
# ---------------------------------------------------------------------------
def _load_reference_encrypt():
    """Return the validated ``aes128_encrypt(plaintext, key)`` callable.

    Search order: (1) the verbatim tb copy ``aes128_reference_model`` on
    ``sys.path`` (tb directory), (2) the authoritative
    ``benchmarks/aes128_benchmark_corrupted`` directory.  The module is
    only trusted after it reproduces its own ``TEST_VECTORS``.  Returns
    ``None`` when the model is absent/corrupt (the scoreboard remains the
    authoritative comparator in that case).
    """
    model = None
    try:
        import aes128_reference_model  # type: ignore
        model = aes128_reference_model
    except ImportError:
        pass
    if model is None:
        bench_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..",
            "benchmarks", "aes128_benchmark_corrupted",
        ))
        if os.path.isdir(bench_dir) and bench_dir not in sys.path:
            sys.path.insert(0, bench_dir)
        try:
            model = importlib.import_module("aes128_reference_model")
        except ImportError:
            return None
    fn = getattr(model, "aes128_encrypt", None)
    if not callable(fn):
        return None
    try:
        for vector in getattr(model, "TEST_VECTORS", []) or []:
            key = int(vector["key"], 16)
            plaintext = int(vector["plaintext"], 16)
            expected = int(vector["ciphertext"], 16)
            if fn(plaintext, key) != expected:
                return None
    except Exception:  # pragma: no cover - malformed oracle
        return None
    return fn


def _config_get(field, default=None):
    """Retrieve a ConfigDB key using the CONTRACT.md §4 retrieval convention.

    Identical to the other tb modules: primary form
    ``ConfigDB().get(None, "*", field)``, falling back to the equivalent
    ``inst_name=""`` retrieval when the pinned pyuvm 5.0.0 runtime rejects
    the wildcard retrieval path.  No key or value type is changed.
    """
    try:
        return ConfigDB().get(None, "*", field, default=default)
    except Exception:
        return ConfigDB().get(None, "", field, default=default)


# ---------------------------------------------------------------------------
# Checker collection
# ---------------------------------------------------------------------------


class Aes128Assertions:
    """Always-running Python assertion checkers for the ``aes128`` DUT.

    Constructor arguments are optional; when omitted, the shared ConfigDB
    keys (``"dut"`` and the optional ``"Aes128DutHelper"``, CONTRACT.md §4)
    are used to resolve the DUT handle.  :meth:`start` launches the six
    checker coroutines with ``cocotb.start_soon``; each checker fails the
    test immediately (``AssertionError``) on its first violation.

    Usage (integration stage)::

        checks = launch_assertions()     # or Aes128Assertions().start()
        ...
        checks.summarize()               # end-of-test report
    """

    def __init__(self, dut=None, helper=None, log=None):
        self.dut = dut if dut is not None else _config_get("dut")
        self._helper = helper
        if self._helper is None and self.dut is not None:
            try:
                from dut_helper import Aes128DutHelper
            except Exception:  # pragma: no cover - helper lives next to us
                Aes128DutHelper = None
            if Aes128DutHelper is not None:
                self._helper = Aes128DutHelper(self.dut)
        self.log = log if log is not None else _log
        #: Reference-model oracle (None -> checkers degrade gracefully).
        self._ref_encrypt = _load_reference_encrypt()
        self._ref_warned = False
        #: Running cocotb tasks, one per checker (filled by start()).
        self.tasks = []
        #: plan-name -> number of violations raised so far.
        self.violations = {name: 0 for name in ASSERTION_SEVERITY}
        #: plan-name -> number of soft informational warnings logged.
        self.warnings = {name: 0 for name in ASSERTION_SEVERITY}
        self._started = False

    # ------------------------------------------------------------------
    # Launch control
    # ------------------------------------------------------------------
    def start(self):
        """Launch every checker with ``cocotb.start_soon`` (idempotent).

        Returns the list of cocotb tasks.  Must be called while the cocotb
        simulation is running (never at import time).
        """
        if self._started:
            return self.tasks
        if self.dut is None:
            raise RuntimeError(
                "Aes128Assertions: 'dut' not found in ConfigDB; set the "
                "'dut' key (CONTRACT.md §4) before launching assertions"
            )
        self._started = True
        self.tasks = [
            cocotb.start_soon(self._check_reset_returns_dut_to_idle()),
            cocotb.start_soon(self._check_start_requires_idle()),
            cocotb.start_soon(self._check_done_pulse_width_one()),
            cocotb.start_soon(self._check_transaction_terminates()),
            cocotb.start_soon(self._check_ciphertext_matches_reference()),
            cocotb.start_soon(self._check_fips197_known_answer()),
        ]
        self.log.info(
            "Aes128Assertions: launched %d checker coroutines via "
            "cocotb.start_soon (oracle=%s)",
            len(self.tasks),
            "available" if self._ref_encrypt is not None else "unavailable",
        )
        return self.tasks

    def stop(self):
        """Kill all checker tasks (used when the test tears down)."""
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
        warns = ", ".join(
            f"{name}={count}"
            for name, count in sorted(self.warnings.items())
            if count
        )
        if not counts:
            counts = "none"
        if not warns:
            warns = "none"
        return (
            f"Aes128Assertions: {len(self.tasks)} active checkers, "
            f"violations -> {counts}; warnings -> {warns}"
        )

    def get_summary(self) -> str:
        return self.summarize()

    def convert2string(self) -> str:
        return self.summarize()

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _read_pin(self, name):
        """Read one DUT pin via CONTRACT.md §2/§4 (helper handle preferred).

        Values are plain ints; a pin that still resolves to X/Z at the
        sample point is mapped to 0 with a warning so the checkers never die
        on uninitialised simulation state (Cocotb 2.1.0 documented read
        path).  A 128-bit ``ciphertext`` with unknown bits therefore reads as
        0, which cannot match the oracle prediction and is reported as a
        mismatch when sampled at a ``done`` pulse.
        """
        if self._helper is not None:
            try:
                handle = getattr(self._helper, name)
            except AttributeError:  # pragma: no cover - helper mirrors pins
                handle = getattr(self.dut, name)
        else:
            handle = getattr(self.dut, name)
        try:
            return int(handle.value)
        except ValueError:
            self.log.warning(
                "Aes128Assertions: pin '%s' not resolvable (X/Z at sample "
                "point); sampled as 0",
                name,
            )
            return 0

    def _ref(self, plaintext, key):
        """Reference-model prediction (masked) or None if unavailable."""
        if self._ref_encrypt is None:
            if not self._ref_warned:
                self.log.warning(
                    "Aes128Assertions: reference model unavailable; "
                    "ciphertext equality checks are skipped"
                )
                self._ref_warned = True
            return None
        try:
            return int(self._ref_encrypt(
                int(plaintext) & MASK128, int(key) & MASK128)) & MASK128
        except Exception:  # pragma: no cover - oracle contract violation
            return None

    def _fail(self, name, message):
        """Flag an error-severity violation: log + raise immediately."""
        self.violations[name] += 1
        self.log.error("[assertion %s] FAILED: %s", name, message)
        raise AssertionError(f"assertion '{name}' failed: {message}")

    def _warn(self, name, message):
        """Soft informational note (never fails the test).

        Used for ambiguous pin-level observations that the monitor /
        scoreboard already own (strict done-pulse accounting lives there per
        CONTRACT.md §9.1/§10.1).
        """
        self.warnings[name] += 1
        self.log.warning("[assertion %s] NOTE: %s", name, message)

    # ------------------------------------------------------------------
    # Plan item: reset_returns_dut_to_idle  (severity error)
    # "after reset release, done == 0 and a following start is accepted
    #  within a bounded time"
    # ------------------------------------------------------------------
    async def _check_reset_returns_dut_to_idle(self):
        """The DUT must be idle after reset and accept a following start.

        Detects the reset branch leaving the DUT busy (DISC-01: the RTL
        drives ``busy <= 1'b1`` in reset, and since start is gated on
        ``start && !busy`` no transaction can ever start).  After every
        0->1 ``rst_n`` transition the checker verifies ``done == 0`` and
        arms the first ``start`` offer that appears: that offer must
        produce a ``done`` pulse within ``DONE_WINDOW_CYCLES``.
        """
        dut = self.dut
        prev_rst = 1       # assumption at launch; corrected on first sample
        need_start = False  # reset released; waiting for a start offer
        waiting = False     # post-release offer pending completion
        wait_cycles = 0
        while True:
            await FallingEdge(dut.clk)
            start = self._read_pin("start")
            await RisingEdge(dut.clk)
            await ReadOnly()
            rst = self._read_pin("rst_n")
            done = self._read_pin("done")

            if rst == 0:
                # Reset active: no acceptance duty now (mid-transaction or
                # between-transaction resets simply abort the expectation).
                waiting = False
                need_start = False
                wait_cycles = 0
                prev_rst = 0
                continue

            if prev_rst == 0 and rst == 1:
                # Reset release edge: the DUT must be idle, done low.
                if done != 0:
                    self._fail(
                        "reset_returns_dut_to_idle",
                        f"done sampled high ({done}) on the cycle after reset "
                        "release; the DUT must return to the idle state with "
                        "done==0 (plan reset_returns_dut_to_idle)",
                    )
                need_start = True
                waiting = False
                wait_cycles = 0

            if need_start:
                if start == 1 and done == 0:
                    # First start offer after release: start the bounded
                    # acceptance timer.
                    waiting = True
                    wait_cycles = 0
                    need_start = False

            if waiting:
                wait_cycles += 1
                if done == 1:
                    # Accepted: the start after reset completed within bound.
                    waiting = False
                    wait_cycles = 0
                elif wait_cycles > DONE_WINDOW_CYCLES:
                    self._fail(
                        "reset_returns_dut_to_idle",
                        "a start sampled after reset release produced no done "
                        f"pulse within {DONE_WINDOW_CYCLES} clock cycles; the "
                        "DUT did not return to idle so the start was never "
                        "honored (plan reset_returns_dut_to_idle; cf. DISC-01 "
                        "reset leaving the DUT busy)",
                    )

            prev_rst = rst

    # ------------------------------------------------------------------
    # Plan item: start_requires_idle  (severity error)
    # "start asserted during an active transaction must be ignored"
    # ------------------------------------------------------------------
    async def _check_start_requires_idle(self):
        """A ``start`` during an active transaction must be ignored.

        The checker tracks each accepted offer's original key/plaintext
        (captured with the CONTRACT.md §9.1 falling-edge probe).  If a
        further ``start`` strobe is observed while the transaction is in
        flight, the eventual completion ciphertext must still equal the
        reference prediction for the *original* stimulus -- if the
        mid-flight start was honored (transaction re-captured), the result
        differs and this check fires.
        """
        dut = self.dut
        in_flight = False
        orig_key = 0
        orig_plaintext = 0
        mid_starts = 0
        while True:
            await FallingEdge(dut.clk)
            start = self._read_pin("start")
            key = self._read_pin("key")
            plaintext = self._read_pin("plaintext")
            await RisingEdge(dut.clk)
            await ReadOnly()
            rst = self._read_pin("rst_n")
            done = self._read_pin("done")
            ciphertext = self._read_pin("ciphertext")

            if rst == 0:
                in_flight = False
                mid_starts = 0
                continue

            if in_flight:
                if start == 1:
                    mid_starts += 1
                    self.log.debug(
                        "start_requires_idle: mid-flight start strobe "
                        "sampled (count=%d); it must be ignored",
                        mid_starts,
                    )
                if done == 1:
                    if mid_starts > 0:
                        expected = self._ref(orig_plaintext, orig_key)
                        if expected is not None:
                            if ciphertext != expected:
                                self._fail(
                                    "start_requires_idle",
                                    "a start asserted during an active "
                                    "transaction was NOT ignored: the "
                                    "completion ciphertext "
                                    f"0x{ciphertext:032x} does not match "
                                    "aes128_encrypt(plaintext, key) of the "
                                    f"originally captured data (expected "
                                    f"0x{expected:032x}); the start must "
                                    "only be honored while the DUT is idle",
                                )
                        else:
                            self._warn(
                                "start_requires_idle",
                                "reference model unavailable; ignored-start "
                                "result check skipped",
                            )
                    in_flight = False
                    mid_starts = 0
            else:
                if start == 1 and done == 0:
                    in_flight = True
                    orig_key = key & MASK128
                    orig_plaintext = plaintext & MASK128
                    mid_starts = 0

    # ------------------------------------------------------------------
    # Plan item: done_pulse_width_one  (severity error)
    # "done is high for exactly one cycle per completed transaction"
    # ------------------------------------------------------------------
    async def _check_done_pulse_width_one(self):
        """``done`` must never stay high for two consecutive clock cycles.

        Sampled post-edge (``RisingEdge`` + ``ReadOnly``) every cycle: a
        second high sample immediately after a high sample means the pulse
        is wider than one cycle (stuck-``done`` / wide-pulse anomaly).
        """
        dut = self.dut
        prev_done = 0
        pulses_observed = 0
        while True:
            await RisingEdge(dut.clk)
            await ReadOnly()
            rst = self._read_pin("rst_n")
            done = self._read_pin("done")

            if rst == 0:
                prev_done = 0
                continue

            if prev_done == 1 and done == 1:
                self._fail(
                    "done_pulse_width_one",
                    "done stayed high for two consecutive clock cycles "
                    "(sampled done==1 on the previous and the current rising "
                    "edge); done must pulse for exactly one cycle per "
                    "completed transaction",
                )
            if done == 1:
                pulses_observed += 1
                self.log.debug(
                    "done_pulse_width_one: completion pulse #%d observed",
                    pulses_observed,
                )
            prev_done = done

    # ------------------------------------------------------------------
    # Plan item: transaction_terminates  (severity error)
    # "accepted start implies done asserted within a bounded number of
    #  cycles"
    # ------------------------------------------------------------------
    async def _check_transaction_terminates(self):
        """Every accepted start must produce a ``done`` pulse in bounded time.

        Any ``start`` offer sampled at the falling edge with ``done`` low
        while out of reset is treated as an accepted request (the DUT is
        always idle at that point in a single-in-flight protocol).  If
        ``done`` does not pulse within ``DONE_WINDOW_CYCLES`` the
        transaction is hung (DISC-01/DISC-02: ``busy`` stuck after reset /
        round counter never reaches the completion round).  A reset asserted
        mid-transaction aborts the expectation instead of failing it.
        """
        dut = self.dut
        in_flight = False
        wait_cycles = 0
        while True:
            await FallingEdge(dut.clk)
            start = self._read_pin("start")
            await RisingEdge(dut.clk)
            await ReadOnly()
            rst = self._read_pin("rst_n")
            done = self._read_pin("done")

            if rst == 0:
                # Reset aborts an in-flight transaction (plan corner case
                # cc_reset_mid_transaction) -- not a hang.
                in_flight = False
                wait_cycles = 0
                continue

            if not in_flight:
                if start == 1 and done == 0:
                    in_flight = True
                    wait_cycles = 0
            else:
                wait_cycles += 1
                if done == 1:
                    in_flight = False
                    wait_cycles = 0
                elif wait_cycles > DONE_WINDOW_CYCLES:
                    self._fail(
                        "transaction_terminates",
                        "an accepted start produced no done pulse within "
                        f"{DONE_WINDOW_CYCLES} clock cycles; the encryption "
                        "transaction never terminated (plan "
                        "transaction_terminates; cf. DISC-01/DISC-02: done "
                        "is never asserted)",
                    )

    # ------------------------------------------------------------------
    # Plan item: ciphertext_matches_reference  (severity error)
    # "done => ciphertext == aes128_encrypt(plaintext, key)"
    # ------------------------------------------------------------------
    async def _check_ciphertext_matches_reference(self):
        """Every ``done`` pulse's ciphertext must match the oracle for the
        stimulus captured at the transaction start.

        The original key/plaintext are captured with the falling-edge probe
        (the values the DUT latches on the following rising edge), identical
        to the monitor/scoreboard pairing.  An unpaired ``done`` pulse
        (nothing tracked) is only an informational note: strict
        done-pulse accounting is owned by the monitor/scoreboard
        (CONTRACT.md §9.1/§10.1).
        """
        dut = self.dut
        in_flight = False
        orig_key = 0
        orig_plaintext = 0
        while True:
            await FallingEdge(dut.clk)
            start = self._read_pin("start")
            key = self._read_pin("key")
            plaintext = self._read_pin("plaintext")
            await RisingEdge(dut.clk)
            await ReadOnly()
            rst = self._read_pin("rst_n")
            done = self._read_pin("done")
            ciphertext = self._read_pin("ciphertext")

            if rst == 0:
                in_flight = False
                continue

            if not in_flight:
                if done == 1:
                    self._warn(
                        "ciphertext_matches_reference",
                        "done pulse with no tracked in-flight transaction "
                        f"(ciphertext=0x{ciphertext:032x}); nothing to "
                        "compare against aes128_encrypt(plaintext, key)",
                    )
                if start == 1 and done == 0:
                    in_flight = True
                    orig_key = key & MASK128
                    orig_plaintext = plaintext & MASK128
            else:
                if done == 1:
                    expected = self._ref(orig_plaintext, orig_key)
                    if expected is not None:
                        if ciphertext != expected:
                            self._fail(
                                "ciphertext_matches_reference",
                                "done => ciphertext == aes128_encrypt("
                                "plaintext, key) violated: expected "
                                f"0x{expected:032x}, got (DUT) "
                                f"0x{ciphertext:032x}",
                            )
                    else:
                        self._warn(
                            "ciphertext_matches_reference",
                            "reference model unavailable; equality check "
                            "skipped",
                        )
                    in_flight = False

    # ------------------------------------------------------------------
    # Plan item: fips197_known_answer  (severity error)
    # "FIPS-197 key/plaintext => ciphertext == 0x69c4e0d8..."
    # ------------------------------------------------------------------
    async def _check_fips197_known_answer(self):
        """The FIPS-197 known-answer vector must produce its mandated
        ciphertext.

        Only transactions whose captured stimulus equals the FIPS-197
        key/plaintext pair are checked; other vectors are left to
        ``ciphertext_matches_reference``.
        """
        dut = self.dut
        in_flight = False
        fips_armed = False
        while True:
            await FallingEdge(dut.clk)
            start = self._read_pin("start")
            key = self._read_pin("key")
            plaintext = self._read_pin("plaintext")
            await RisingEdge(dut.clk)
            await ReadOnly()
            rst = self._read_pin("rst_n")
            done = self._read_pin("done")
            ciphertext = self._read_pin("ciphertext")

            if rst == 0:
                in_flight = False
                fips_armed = False
                continue

            if not in_flight:
                if start == 1 and done == 0:
                    in_flight = True
                    fips_armed = (
                        (key & MASK128) == KEY_FIPS197
                        and (plaintext & MASK128) == PT_FIPS197
                    )
            else:
                if done == 1:
                    if fips_armed:
                        if ciphertext != CT_FIPS197:
                            self._fail(
                                "fips197_known_answer",
                                "FIPS-197 known-answer mismatch: expected "
                                f"0x{CT_FIPS197:032x}, got (DUT) "
                                f"0x{ciphertext:032x}",
                            )
                        else:
                            self.log.debug(
                                "fips197_known_answer: FIPS-197 vector "
                                "produced the mandated ciphertext",
                            )
                    in_flight = False
                    fips_armed = False


# ---------------------------------------------------------------------------
# Convenience launcher for the integration (environment) stage.
# ---------------------------------------------------------------------------


def launch_assertions(dut=None, helper=None, log=None):
    """Build :class:`Aes128Assertions` (ConfigDB-shared unless overridden)
    and launch every checker with ``cocotb.start_soon``.

    Returns the instance (``.tasks`` are the running checker coroutines).
    """
    checks = Aes128Assertions(dut=dut, helper=helper, log=log)
    checks.start()
    return checks


# ---------------------------------------------------------------------------
# Watchdog (CONTRACT.md §8 / stage rule: fail the test if it does not finish
# within a bounded number of clock cycles).
#
# The watchdog is *launched* and *terminated* by the integration stage:
#     task = launch_watchdog(dut, timeout_cycles)
#     ...run the test body...
#     task.kill()                       # normal completion
# If the body hangs (busy stuck, FSM dead, no done pulses), the watchdog
# keeps counting rising edges and raises once `timeout_cycles` elapse.
# ---------------------------------------------------------------------------


async def watchdog(dut, timeout_cycles, log=None):
    """Bounded clock-cycle watchdog coroutine.

    Counts rising clock edges; raises ``AssertionError`` once more than
    ``timeout_cycles`` edges elapse without this task being killed by its
    owner.  A hung FSM with the clock still running is guaranteed to trip
    it.
    """
    log = log if log is not None else _log
    cycles = 0
    while True:
        await RisingEdge(dut.clk)
        cycles += 1
        if cycles > int(timeout_cycles):
            raise AssertionError(
                f"WATCHDOG: test did not finish within {int(timeout_cycles)} "
                "clock cycles; failing the hung simulation"
            )


def launch_watchdog(dut=None, timeout_cycles=WATCHDOG_DEFAULT_CYCLES,
                    log=None):
    """Start the bounded clock-cycle watchdog via ``cocotb.start_soon``.

    ``dut`` defaults to the ConfigDB-shared ``"dut"`` handle (CONTRACT.md
    §4).  ``timeout_cycles`` is the wall of clock cycles no test body may
    exceed.  Returns the running cocotb task; the environment must
    ``kill()`` it on normal completion.
    """
    if dut is None:
        dut = _config_get("dut")
    if dut is None:
        raise RuntimeError(
            "launch_watchdog: 'dut' not found in ConfigDB; cannot arm the "
            "clock-cycle watchdog"
        )
    task = cocotb.start_soon(watchdog(dut, int(timeout_cycles), log=log))
    _log.info("WATCHDOG: armed for %d clock cycles", int(timeout_cycles))
    return task