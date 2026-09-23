"""i2c_master assertion checkers for the cocotb + pyuvm bench (assertions
stage).

Stage-5 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory; it is the authoritative convention record).

Per CONTRACT.md §8 there is no SystemVerilog assertion language (and no SVA)
anywhere in this project.  Every item in the plan's ``useful_assertions``
(all fifteen; all plan severity *error*) is implemented as a plain-Python
checker *coroutine* synchronized on the rising edge of the DUT clock via
public cocotb triggers and launched with ``cocotb.start_soon``.  A violated
check is flagged immediately: logged as an error and raised as an
``AssertionError``, which propagates out of the checker task and fails the
enclosing cocotb test at once (the SVA ``assert`` equivalent).

The fifteen plan items live in this module:

==================== ============================================ ===========
plan name            check                                        kind
==================== ============================================ ===========
a_reset_clears_outputs    busy/done/ack_error==0, rx_data==0 at the first clock edge after rst_n deassert                pin
a_address_byte_correct    observed address byte == (slave_addr<<1)|rw   txn
a_address_msb_first       address bit order == reference address_bits(), MSB first   txn
a_rw_bit_correct          address_byte[0] == rw                txn
a_write_data_correct      write-data byte transmitted == tx_data (writes)   txn
a_rx_data_correct         rx_data == byte driven on sda_in during the read-data phase (reads)   txn
a_addr_ack_error          sda_in==1 at the address-ACK sample implies ack_error asserted before the next phase   txn
a_data_ack_error          sda_in==1 at the write-data-ACK sample implies ack_error asserted (writes)   txn
a_ack_error_clear_on_success  ack_error==0 at completion when all expected ACKs were observed   txn
a_done_is_pulse           done is high for exactly one cycle (never two consecutive cycles)   pin
a_busy_spans_transaction  busy==1 from acceptance until the completion edge, then 0   pin
a_start_ignored_while_busy  start while busy must not abort/corrupt the in-flight transaction   pin
a_stop_returns_idle       after STOP the controller returns to IDLE and accepts the next start   pin
a_open_drain_release      sda_oe/scl_oe deassert (or line high) while the controller is idle   pin
a_clk_div_advance_timing  state-advance cadence respects CLK_DIV (per-bit spacing in the address phase)   txn
==================== ============================================ ===========

ARCHITECTURE.  ``I2CAssertions`` runs two kinds of checker:

* **pin checkers** (6) observe pins after every ``RisingEdge`` and need no
  transaction context (reset contract, one-cycle done, busy span, illegal
  start, stop/idle return, open-drain release);
* **transaction checkers** (9) consume ``_CompletedTransaction`` records
  produced by one shared observer coroutine ``_observe_stream``.  The
  observer maintains its own per-cycle ring (mirroring the scoreboard's
  discipline) and reconstructs each transaction the DUT actually completes:
  it latches the offer (``start`` high while idle), records acceptance on
  the ``busy`` 0->1 rise, and finalizes a record at the ``done`` 0->1 pulse,
  deriving the address/data serial bits from the ring at the driver's
  documented advance schedule (CONTRACT.md §13.3) and the ACK levels
  (``addr_ack`` / ``data_ack`` / ``master_nack``) from the TB slave's
  ``sda_in`` timeline by majority vote (window +/- CLK_DIV/2, mitigating the
  estimative timing of §13.3).  A transaction aborted by reset is dropped
  (CONTRACT.md §11), and a record whose required samples tie/unknown is
  skipped by the affected checkers -- never graded against a guessed value.
  Bounded waits follow the family convention (``START_TIMEOUT_CYCLES`` /
  ``DONE_TIMEOUT_CYCLES``; the deleted offer/hung windows are reported, not
  silently swallowed).

CORRUPTED-RTL REALITY (catch-report grading, CONTRACT.md §7.3/§14.2):
on the as-shipped RTL ``done <= 1'b1`` on every non-reset cycle (DIS-15),
``sda_oe``/``scl_oe`` are hardwired 1 with ``sda_out``/``scl_out``
hardwired 0 (both lines actively driven low), and the divider never reaches
``CLK_DIV`` so the FSM never advances and ``busy`` never rises
(DIS-18/19).  Consequently the *pin* checkers fire immediately and loudly:
``a_reset_clears_outputs`` at the first post-deassert edge (done==1),
``a_done_is_pulse`` on the second consecutive high-``done`` edge,
``a_open_drain_release`` on the first idle edge (lines driven low).  The
*transaction* checkers stay inert (no transaction ever completes), which is
itself the defect evidence; on a repaired variant they enforce the
protocol stream/ACK contract of ``useful_assertions``.

The always-running watchdog (CONTRACT.md §13.7/§8) is implemented here as
``watchdog()`` / ``launch_watchdog()``; per §13.7 it is **armed by the
integration stage** (the env/test stage must kill it on normal completion).
``launch_assertions()`` builds ``I2CAssertions`` and starts every checker.

Cocotb 2.1.0 public APIs only: ``cocotb.start_soon`` and
``cocotb.triggers.RisingEdge``; no ``cocotb.handle.ModifiableObject``
import; inter-task transport uses the standard ``asyncio.Queue`` (the
family's bounded-wait/task discipline is pyuvm-asyncio based, CONTRACT
§15).  The module keeps a plain-Python self-check under ``__main__`` that
needs neither cocotb nor pyuvm.
"""

import logging
import os
from collections import deque

try:  # cocotb is always present at simulation time; the fallback exists
    # only so the module's pure-Python self-check (__main__) can run in a
    # sandbox that does not have cocotb installed (see i2c_pins.py).
    from cocotb import queue, start_soon
    from cocotb.triggers import RisingEdge

    _COCOTB_AVAILABLE = True
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    start_soon = RisingEdge = queue = None
    _COCOTB_AVAILABLE = False

try:  # pyuvm's ConfigDB is required at simulation time.
    from pyuvm import ConfigDB

    _PYUVM_AVAILABLE = True
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    ConfigDB = None
    _PYUVM_AVAILABLE = False

# ---------------------------------------------------------------------------
# i2c_pins re-exports cocotb-dependent handle helpers, so it can only be
# imported where cocotb is installed (simulation).  The fallback constants
# below are i2c_pins' documented defaults, kept so the pure-Python
# self-check (__main__) can run in a cocotb-less sandbox (same pattern as
# i2c_scoreboard.py).
# ---------------------------------------------------------------------------
try:
    from i2c_pins import (
        CLK_DIV_DEFAULT,
        DONE_TIMEOUT_CYCLES,
        I2CPins,
        KEY_DUT_PINS,
        START_TIMEOUT_CYCLES,
        WATCHDOG_CYCLES,
        _to_int,
    )
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    CLK_DIV_DEFAULT = 4
    DONE_TIMEOUT_CYCLES = 2048
    I2CPins = None
    KEY_DUT_PINS = "i2c_pins"
    START_TIMEOUT_CYCLES = 64
    WATCHDOG_CYCLES = 300000
    _to_int = None

try:  # Intended-protocol advance schedule (CONTRACT.md §13.3,
    # `i2c_driver.py`); same guarded-import pattern as i2c_scoreboard.py.
    from i2c_driver import (
        ADV_ACCEPT,
        ADV_ADDR_ACK,
        ADV_DATA_PHASE_START,
        ADV_DATA_ACK,
        ADV_STOP,
    )
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    ADV_ACCEPT = 0
    ADV_ADDR_ACK = 10
    ADV_DATA_PHASE_START = 11
    ADV_DATA_ACK = 19
    ADV_STOP = 20

# The reference model is the ONLY protocol oracle (CONTRACT.md §8); it is a
# pure-Python module and is importable in any context (verbatim tb copy, §15).
from i2c_reference_model import address_bits as _ref_address_bits

#: Module logger (cocotb configures the logging hierarchy at sim start).
_log = logging.getLogger("tb.i2c_assertions")

#: Ring buffer covering one full long transaction plus the monitor's
#: done-wait budget with generous margin (same sizing as the scoreboard).
RING_SIZE = max(8192, 4 * DONE_TIMEOUT_CYCLES + 128)

# ---------------------------------------------------------------------------
# Plan metadata (useful_assertions; every item is severity "error").
# ---------------------------------------------------------------------------
ASSERTION_SEVERITY = {
    "a_reset_clears_outputs": "error",
    "a_address_byte_correct": "error",
    "a_address_msb_first": "error",
    "a_rw_bit_correct": "error",
    "a_write_data_correct": "error",
    "a_rx_data_correct": "error",
    "a_addr_ack_error": "error",
    "a_data_ack_error": "error",
    "a_ack_error_clear_on_success": "error",
    "a_done_is_pulse": "error",
    "a_busy_spans_transaction": "error",
    "a_start_ignored_while_busy": "error",
    "a_stop_returns_idle": "error",
    "a_open_drain_release": "error",
    "a_clk_div_advance_timing": "error",
}

#: Error-severity only in this plan (a fail() always raises).
assert set(ASSERTION_SEVERITY.values()) == {"error"}

#: Checkers that consume per-transaction records (all others are pin-based).
TXN_CHECKER_NAMES = {
    "a_address_byte_correct",
    "a_address_msb_first",
    "a_rw_bit_correct",
    "a_write_data_correct",
    "a_rx_data_correct",
    "a_addr_ack_error",
    "a_data_ack_error",
    "a_ack_error_clear_on_success",
    "a_clk_div_advance_timing",
}

#: Pin-based checkers (always-on).
PIN_CHECKER_NAMES = set(ASSERTION_SEVERITY) - TXN_CHECKER_NAMES


# ---------------------------------------------------------------------------
# Pure Python helpers (unit-testable without cocotb/pyuvm).
# ---------------------------------------------------------------------------
def _majority_bit(values) -> int | None:
    """Return the majority 0/1 value among *values*, or None on an empty
    set or an exact tie.  ``None`` inputs do not count as votes."""
    ones = sum(1 for v in values if v == 1)
    zeros = sum(1 for v in values if v == 0)
    if ones == 0 and zeros == 0:
        return None
    if ones == zeros:
        return None
    return 1 if ones > zeros else 0


def _rel_index_for_advance(advance: int, clk_div: int) -> int:
    """Ring-relative index (clock cycles after acceptance) of the nominal
    sample edge for one FSM advance (one advance per CLK_DIV cycles)."""
    return int(advance) * max(1, int(clk_div))


def _ring_get(ring: deque, gi: int) -> dict | None:
    """Return the ring entry with global index ``gi`` or None."""
    for e in reversed(ring):
        if e["gi"] == gi:
            return e
        if e["gi"] < gi:
            return None  # exact index already evicted from history
    return None


def _sample_majority_ring(
    ring: deque,
    accept_gi: int,
    rel: int,
    field: str,
    clk_div: int,
) -> int | None:
    """Majority vote of ring ``field`` over [rel-window, rel+window] after
    ``accept_gi``; window defaults to CLK_DIV // 2 (drivers' estimative
    slotting, CONTRACT.md §13.3)."""
    half = max(1, int(clk_div)) // 2
    votes = []
    for gi in range(accept_gi + rel - half, accept_gi + rel + half + 1):
        e = _ring_get(ring, gi)
        if e is None:
            continue
        v = e.get(field)
        if v in (0, 1):
            votes.append(v)
    return _majority_bit(votes)


def _bits_from_list(bits) -> int | None:
    """Assemble an int from an MSB-first bit list; None on any non-0/1."""
    value = 0
    for b in bits:
        if b not in (0, 1):
            return None
        value = (value << 1) | b
    return value


class _CompletedTransaction:
    """One fully-observed transaction reconstructed by the stream observer.

    Carries the offer stimulus (latched at the start offer), the observed
    completion values (sampled at the done 0->1 edge), the derived ACK
    levels (``addr_ack`` / ``data_ack`` / ``master_nack`` from the TB
    slave's ``sda_in`` timeline), and the reconstructed serial stream
    (``address_bits`` on the bus level; ``write_bits`` / ``read_bits`` on
    the bus / slave timeline).  ``*_valid`` flags tell the checkers which
    derived data is trustworthy (ties/unknowns are never graded).
    """

    __slots__ = (
        "slave_addr", "rw", "tx_data", "rx_data",
        "addr_ack", "data_ack", "master_nack",
        "address_bits", "address_valid",
        "write_bits", "write_valid",
        "read_bits", "read_valid",
        "ack_error", "busy", "done",
        "accept_gi", "done_gi",
        "start_while_busy_observed",
    )

    def __init__(self) -> None:
        self.slave_addr = 0
        self.rw = 0
        self.tx_data = 0
        self.rx_data = 0
        self.addr_ack = None
        self.data_ack = None
        self.master_nack = None
        self.address_bits = []
        self.address_valid = False
        self.write_bits = []
        self.write_valid = False
        self.read_bits = []
        self.read_valid = False
        self.ack_error = 0
        self.busy = 0
        self.done = 0
        self.accept_gi = -1
        self.done_gi = -1
        self.start_while_busy_observed = False


# ---------------------------------------------------------------------------
# Checker collection.
# ---------------------------------------------------------------------------
class I2CAssertions:
    """Always-running SVA-replacement checkers for the i2c_master DUT.

    Optional constructor arguments are fetched from pyuvm's ``ConfigDB``
    under the exact CONTRACT.md key (``KEY_DUT_PINS``) when omitted.

    Usage (integration stage)::

        checks = launch_assertions()      # or I2CAssertions().start()
        ...
        checks.summarize()                # end-of-test violation report

    Every plan assertion has severity "error", so a violation always logs
    and raises :class:`AssertionError` (the enclosing cocotb test fails
    immediately).  ``violations`` maps each plan name to its hit count.
    """

    def __init__(self, pins=None, log=None):
        #: Shared pin helper (CONTRACT.md key KEY_DUT_PINS).
        self.pins = (
            pins if pins is not None
            else ConfigDB().get(None, "", KEY_DUT_PINS)
        )
        self.log = log if log is not None else _log
        self.clk_div = max(
            1, int(os.environ.get("I2C_CLK_DIV", CLK_DIV_DEFAULT))
        )
        #: Running cocotb tasks, one per checker (filled by start()).
        self.tasks = []
        #: plan-name -> number of violations observed so far.
        self.violations = {name: 0 for name in sorted(ASSERTION_SEVERITY)}
        #: Per-cycle ring fed by the stream observer (whole simulation).
        self.ring = deque(maxlen=RING_SIZE)
        self.ring_gi = 0
        #: Completed-transaction records observed so far.
        self.txn_record_count = 0
        #: Observer-internal stream state.
        self._offer = None            # (slave_addr, rw, tx_data) or None
        self._accepted = False
        self._accept_gi = -1
        self._accept_addr = 0
        self._accept_rw = 0
        self._accept_tx = 0
        self._active_start_while_busy = False
        #: cocotb.queue.Queue per transaction checker (observer fan-out).
        self._queues = {name: queue.Queue() for name in sorted(TXN_CHECKER_NAMES)}
        self._started = False

    # ------------------------------------------------------------------
    # Launch control
    # ------------------------------------------------------------------
    def start(self):
        """Launch the observer plus every checker with ``cocotb.start_soon``
        (idempotent).  Returns the list of cocotb tasks."""
        if self._started:
            return self.tasks
        if self.pins is None:
            self.log.error(
                "I2CAssertions.start(): no I2CPins handle "
                "(ConfigDB['%s'] missing); checkers disabled",
                KEY_DUT_PINS,
            )
            return self.tasks
        self._started = True
        self.tasks = [
            start_soon(self._observe_stream()),
            # --- pin checkers (always-on) -----------------------------
            start_soon(self._check_a_reset_clears_outputs()),
            start_soon(self._check_a_done_is_pulse()),
            start_soon(self._check_a_busy_spans_transaction()),
            start_soon(self._check_a_start_ignored_while_busy()),
            start_soon(self._check_a_stop_returns_idle()),
            start_soon(self._check_a_open_drain_release()),
            # --- transaction checkers (consume observer records) -------
            start_soon(self._check_a_address_byte_correct()),
            start_soon(self._check_a_address_msb_first()),
            start_soon(self._check_a_rw_bit_correct()),
            start_soon(self._check_a_write_data_correct()),
            start_soon(self._check_a_rx_data_correct()),
            start_soon(self._check_a_addr_ack_error()),
            start_soon(self._check_a_data_ack_error()),
            start_soon(self._check_a_ack_error_clear_on_success()),
            start_soon(self._check_a_clk_div_advance_timing()),
        ]
        self.log.info(
            "I2CAssertions: launched %d checker coroutines via "
            "cocotb.start_soon (observer + %d pin + %d transaction)",
            len(self.tasks),
            len(PIN_CHECKER_NAMES),
            len(TXN_CHECKER_NAMES),
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
            f"I2CAssertions: {len(self.tasks)} active checkers, "
            f"txns_observed={self.txn_record_count}, "
            f"violations -> {counts}"
        )

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _in_reset(self):
        """True while ``rst_n`` is asserted (0) or still unknown (x/z)."""
        return _to_int(self.pins.rst_n.value, 1) != 1

    def _fail(self, name, message):
        """Flag an error-severity violation: log + raise immediately
        (SVA ``assert`` equivalent -- all plan severities are error)."""
        self.violations[name] += 1
        self.log.error("[assertion %s] FAILED: %s", name, message)
        raise AssertionError(f"assertion '{name}' failed: {message}")

    # ------------------------------------------------------------------
    # Ring helpers (thin wrappers over the pure module functions)
    # ------------------------------------------------------------------
    def _ring_append(self) -> None:
        self.ring.append(
            {
                "gi": self.ring_gi,
                "start": self.pins.read_start(),
                "slave_addr": self.pins.read_slave_addr(),
                "rw": self.pins.read_rw(),
                "tx_data": self.pins.read_tx_data(),
                "sda_in": self.pins.read_sda_in(),
                "scl_in": self.pins.read_scl_in(),
                "sda_out": self.pins.read_sda_out(),
                "sda_oe": self.pins.read_sda_oe(),
                "scl_out": self.pins.read_scl_out(),
                "scl_oe": self.pins.read_scl_oe(),
                "sda_level": self.pins.resolve_sda_level(),
                "scl_level": self.pins.resolve_scl_level(),
                "done": self.pins.read_done(),
                "busy": self.pins.read_busy(),
                "ack_error": self.pins.read_ack_error(),
                "rx_data": self.pins.read_rx_data(),
                "rst": _to_int(self.pins.rst_n.value, 1),
            }
        )
        self.ring_gi += 1

    def _ring_get(self, gi: int) -> dict | None:
        return _ring_get(self.ring, gi)

    def _sample_majority(self, accept_gi: int, rel: int, field: str):
        return _sample_majority_ring(
            self.ring, accept_gi, rel, field, self.clk_div
        )

    # ------------------------------------------------------------------
    # Stream observer (shared by the transaction checkers)
    # ------------------------------------------------------------------
    async def _observe_stream(self) -> None:
        """Reconstruct completed transactions from the pin timeline.

        Every rising edge: ring append, then the offer/accept/finalize
        state machine.  A reset assertion aborts any in-flight window
        (CONTRACT.md §11).  On a done 0->1 pulse with an accepted
        transaction the observer derives the serial stream and ACK levels
        from the ring and fans out one ``_CompletedTransaction`` record to
        every transaction checker.
        """
        await RisingEdge(self.pins.clk)
        prev_done = 0
        prev_busy = 0
        while True:
            await RisingEdge(self.pins.clk)
            self._ring_append()
            gi = self.ring_gi - 1
            e = self._ring_get(gi)
            if e is None:  # pragma: no cover - defensive (never evicted)
                continue
            if e["rst"] == 0:
                self._discard_in_flight()
                prev_done = 0
                prev_busy = 0
                continue
            busy = e["busy"]
            done = e["done"]
            start = e["start"]
            if self._accepted:
                if start == 1 and busy == 1:
                    self._active_start_while_busy = True
                if done == 1 and prev_done == 0:
                    self._finalize_transaction(gi, e)
            else:
                if busy == 1:
                    # Acceptance (busy 0->1 rise; covers busy already high
                    # when the observer starts -- an inexorable offer).
                    self._start_accepted(gi, e)
                elif start == 1 and prev_busy == 0:
                    # Offer latch: the DUT latches the request on the edge
                    # where start is high while idle.
                    self._offer = (
                        int(e["slave_addr"]),
                        int(e["rw"]),
                        int(e["tx_data"]),
                    )
            prev_done = done
            prev_busy = busy

    def _discard_in_flight(self) -> None:
        """Reset assertion: drop the offer/active window (§11)."""
        self._offer = None
        self._accepted = False
        self._accept_gi = -1
        self._active_start_while_busy = False

    def _start_accepted(self, gi: int, e: dict) -> None:
        if self._offer is not None:
            addr, rw, tx = self._offer
        else:
            # Inexorable busy: capture the current stimulus (monitor
            # convention -- `start` read as already-accepted).
            addr, rw, tx = (
                int(e["slave_addr"]),
                int(e["rw"]),
                int(e["tx_data"]),
            )
        self._accept_addr = addr
        self._accept_rw = rw
        self._accept_tx = tx
        self._accept_gi = gi
        self._active_start_while_busy = False
        self._accepted = True
        self._offer = None

    def _finalize_transaction(self, done_gi: int, e: dict) -> None:
        """Build and fan out the completed-transaction record."""
        rec = _CompletedTransaction()
        rec.slave_addr = self._accept_addr
        rec.rw = self._accept_rw
        rec.tx_data = self._accept_tx
        rec.rx_data = int(e["rx_data"])
        rec.ack_error = int(e["ack_error"])
        rec.busy = int(e["busy"])
        rec.done = int(e["done"])
        rec.accept_gi = self._accept_gi
        rec.done_gi = done_gi
        rec.start_while_busy_observed = bool(self._active_start_while_busy)
        cdiv = max(1, self.clk_div)

        # Address byte (advances 2..9, bus level, MSB first).
        bits = []
        ok = True
        for j in range(8):
            b = self._sample_majority(
                rec.accept_gi, _rel_index_for_advance(2 + j, cdiv),
                "sda_level",
            )
            if b is None:
                ok = False
                break
            bits.append(b)
        rec.address_bits = bits
        rec.address_valid = ok

        # ACK levels from the TB slave's sda_in timeline.
        rec.addr_ack = self._sample_majority(
            rec.accept_gi, _rel_index_for_advance(ADV_ADDR_ACK, cdiv),
            "sda_in",
        )
        if rec.rw == 0:
            rec.data_ack = self._sample_majority(
                rec.accept_gi, _rel_index_for_advance(ADV_DATA_ACK, cdiv),
                "sda_in",
            )
            rec.master_nack = None
            # Write-data byte (advances 11..18, bus level, MSB first).
            bits = []
            ok = True
            for j in range(8):
                b = self._sample_majority(
                    rec.accept_gi,
                    _rel_index_for_advance(ADV_DATA_PHASE_START + j, cdiv),
                    "sda_level",
                )
                if b is None:
                    ok = False
                    break
                bits.append(b)
            rec.write_bits = bits
            rec.write_valid = ok
        else:
            rec.data_ack = None
            rec.master_nack = self._sample_majority(
                rec.accept_gi, _rel_index_for_advance(ADV_DATA_ACK, cdiv),
                "sda_in",
            )
            # Read-data byte (advances 11..18, slave's sda_in, MSB first).
            bits = []
            ok = True
            for j in range(8):
                b = self._sample_majority(
                    rec.accept_gi,
                    _rel_index_for_advance(ADV_DATA_PHASE_START + j, cdiv),
                    "sda_in",
                )
                if b is None:
                    ok = False
                    break
                bits.append(b)
            rec.read_bits = bits
            rec.read_valid = ok

        self.txn_record_count += 1
        for q in self._queues.values():
            q.put_nowait(rec)

        self._accepted = False
        self._accept_gi = -1
        self._active_start_while_busy = False
        self.log.debug(
            f"assertions observed completed txn @{done_gi} "
            f"(accept_gi={rec.accept_gi}): addr_ack={rec.addr_ack} "
            f"data_ack={rec.data_ack} master_nack={rec.master_nack}"
        )

    # ------------------------------------------------------------------
    # Plan item: a_reset_clears_outputs (severity error)
    # ------------------------------------------------------------------
    async def _check_a_reset_clears_outputs(self) -> None:
        """On the first clock edge after deasserting rst_n:
        busy == 0 and done == 0 and ack_error == 0 and rx_data == 0x00.

        Detects every ``rst_n`` 0->1 transition across rising edges and
        samples the outputs at that very edge; any nonzero output is a
        violation.  Re-arms for every subsequent reset assertion.
        """
        pins = self.pins
        prev_rst = _to_int(pins.rst_n.value, 1)
        while True:
            await RisingEdge(pins.clk)
            cur_rst = _to_int(pins.rst_n.value, 1)
            if prev_rst == 0 and cur_rst == 1:
                outs = pins.sample_outputs()
                bad = {
                    k: int(outs[k])
                    for k, want in (
                        ("busy", 0), ("done", 0),
                        ("ack_error", 0), ("rx_data", 0x00),
                    )
                    if int(outs[k]) != int(want)
                }
                if bad:
                    self._fail(
                        "a_reset_clears_outputs",
                        f"outputs not at reset values on the first clock "
                        f"edge after rst_n deassertion: {bad!r}",
                    )
            prev_rst = cur_rst

    # ------------------------------------------------------------------
    # Plan item: a_done_is_pulse (severity error)
    # ------------------------------------------------------------------
    async def _check_a_done_is_pulse(self) -> None:
        """done is high for exactly one clock per transaction and low
        during idle -- never high on two consecutive sampled edges.

        ``done`` is a register cleared on every clock edge except the
        COMPLETE cycle; two consecutive high post-edge samples mean the
        "pulse" spanned two cycles (a DUT defect).  Reset history clears.
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
                    "a_done_is_pulse",
                    f"done stayed high for two consecutive clock cycles "
                    f"(cycle N and cycle N+1 both sampled done==1); done "
                    "must be a one-cycle completion pulse, low during idle",
                )
            prev_done = cur_done

    # ------------------------------------------------------------------
    # Plan item: a_busy_spans_transaction (severity error)
    # ------------------------------------------------------------------
    async def _check_a_busy_spans_transaction(self) -> None:
        """busy == 1 from start acceptance until the STOP/completion edge,
        then busy == 0.

        A ``busy`` drop before any done edge is a violation (busy released
        early / FSM died); a done edge with ``busy`` still high violates
        the ``then busy == 0`` return-to-idle half of the plan item.
        """
        pins = self.pins
        prev_done = 0
        busy_seen = False
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                prev_done = 0
                busy_seen = False
                continue
            done = _to_int(pins.done.value, 1)
            busy = _to_int(pins.busy.value, 1)
            done_edge = done == 1 and prev_done == 0
            if busy == 1:
                busy_seen = True
            elif busy_seen and not done_edge:
                self._fail(
                    "a_busy_spans_transaction",
                    f"busy dropped to 0 before any done completion pulse "
                    f"(sampled busy=0 while a transaction was active); busy "
                    "must span the transaction until completion",
                )
            if done_edge and busy == 1:
                self._fail(
                    "a_busy_spans_transaction",
                    f"busy=1 sampled at the done completion edge (busy "
                    "must return to 0 at completion / IDLE after STOP)",
                )
            if done_edge:
                busy_seen = False
            prev_done = done

    # ------------------------------------------------------------------
    # Plan item: a_start_ignored_while_busy (severity error)
    # ------------------------------------------------------------------
    async def _check_a_start_ignored_while_busy(self) -> None:
        """A start asserted while busy must be ignored: no new capture, no
        abort -- the in-flight transaction completes unchanged.

        Once a start-while-busy pulse is observed, busy must stay asserted
        until a done edge (an abort/corruption would drop busy first).
        Stream/value corruption of the in-flight transaction is caught by
        the per-transaction checkers against the reference model.
        """
        pins = self.pins
        prev_done = 0
        prev_busy = 0
        active = False
        start_while_busy_seen = False
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                prev_done = 0
                prev_busy = 0
                active = False
                start_while_busy_seen = False
                continue
            done = _to_int(pins.done.value, 1)
            busy = _to_int(pins.busy.value, 1)
            start = _to_int(pins.start.value, 1)
            done_edge = done == 1 and prev_done == 0
            if busy == 1 and prev_busy == 0:
                active = True
            if active and start == 1 and busy == 1:
                start_while_busy_seen = True
            if start_while_busy_seen and busy == 0 and not done_edge:
                self._fail(
                    "a_start_ignored_while_busy",
                    f"start asserted while busy aborted the in-flight "
                    f"transaction (busy dropped to 0 without a done pulse "
                    f"after a start-while-busy edge); the illegal start "
                    "must be ignored",
                )
            if done_edge:
                active = False
                start_while_busy_seen = False
            prev_done = done
            prev_busy = busy

    # ------------------------------------------------------------------
    # Plan item: a_stop_returns_idle (severity error)
    # ------------------------------------------------------------------
    async def _check_a_stop_returns_idle(self) -> None:
        """After STOP the controller returns to IDLE and is ready for the
        next start: busy deasserts at completion, and a start offered after
        the completion edge must be accepted (busy rises) within the
        documented bound."""
        pins = self.pins
        prev_done = 0
        state = "idle"          # "idle" | "post_done" | "await_accept"
        pending_cycles = 0
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                prev_done = 0
                state = "idle"
                pending_cycles = 0
                continue
            done = _to_int(pins.done.value, 1)
            busy = _to_int(pins.busy.value, 1)
            start = _to_int(pins.start.value, 1)
            done_edge = done == 1 and prev_done == 0
            if done_edge:
                if busy != 0:
                    self._fail(
                        "a_stop_returns_idle",
                        f"busy={busy} at the done completion edge (STOP "
                        "must return the controller to IDLE / busy=0)",
                    )
                state = "post_done"
                pending_cycles = 0
            elif state == "post_done":
                if busy == 1:
                    # The next transaction was accepted cleanly: back to
                    # the normal idle watch.
                    state = "idle"
                    pending_cycles = 0
                elif start == 1:
                    pending_cycles += 1
                    if pending_cycles > START_TIMEOUT_CYCLES:
                        self._fail(
                            "a_stop_returns_idle",
                            f"a start offered after STOP was not accepted "
                            f"within {START_TIMEOUT_CYCLES} clock cycles "
                            "(busy never rose; the controller did not "
                            "return to a clean IDLE)",
                        )
            prev_done = done

    # ------------------------------------------------------------------
    # Plan item: a_open_drain_release (severity error)
    # ------------------------------------------------------------------
    async def _check_a_open_drain_release(self) -> None:
        """SDA/SCL drive-enables deassert when the line is released so the
        pull-up drives high (spec section 10): while idle (busy == 0)
        neither open-drain line may be actively driven low."""
        pins = self.pins
        while True:
            await RisingEdge(pins.clk)
            if self._in_reset():
                continue
            if _to_int(pins.busy.value, 1) != 0:
                continue  # active transaction: lines are legitimately driven
            if pins.resolve_sda_level() == 0:
                self._fail(
                    "a_open_drain_release",
                    f"SDA resolved level 0 while busy==0 (sda_oe={_to_int(pins.sda_oe.value, 1)}, "
                    f"sda_out={_to_int(pins.sda_out.value, 1)}); the line "
                    "must be released (driven high via pull-up) while idle",
                )
            if pins.resolve_scl_level() == 0:
                self._fail(
                    "a_open_drain_release",
                    f"SCL resolved level 0 while busy==0 (scl_oe={_to_int(pins.scl_oe.value, 1)}, "
                    f"scl_out={_to_int(pins.scl_out.value, 1)}); the line "
                    "must be released (driven high via pull-up) while idle",
                )

    # ------------------------------------------------------------------
    # Plan item: a_address_byte_correct (severity error)
    # ------------------------------------------------------------------
    async def _check_a_address_byte_correct(self) -> None:
        """The transmitted address byte equals (slave_addr << 1) | rw
        (spec section 4).  Reconstructed from the bus-level stream."""
        q = self._queues["a_address_byte_correct"]
        while True:
            rec = await q.get()
            if not rec.address_valid:
                continue
            observed = _bits_from_list(rec.address_bits)
            expected = (int(rec.slave_addr) << 1) | int(rec.rw)
            if observed != expected:
                self._fail(
                    "a_address_byte_correct",
                    f"txn@accept_gi={rec.accept_gi}: observed address byte "
                    f"0x{observed:02x} != (slave_addr<<1)|rw = 0x{expected:02x} "
                    f"(slave_addr=0x{rec.slave_addr:02x}, rw={rec.rw})",
                )

    # ------------------------------------------------------------------
    # Plan item: a_address_msb_first (severity error)
    # ------------------------------------------------------------------
    async def _check_a_address_msb_first(self) -> None:
        """The address byte is transmitted MSB first: its bit order equals
        the reference model's ``address_bits()`` list, bit for bit."""
        q = self._queues["a_address_msb_first"]
        while True:
            rec = await q.get()
            if not rec.address_valid:
                continue
            expected = list(
                _ref_address_bits(int(rec.slave_addr), bool(rec.rw))
            )
            observed = list(rec.address_bits)
            if observed != expected:
                mism = [
                    i for i in range(8)
                    if observed[i] != expected[i]
                ]
                self._fail(
                    "a_address_msb_first",
                    f"txn@accept_gi={rec.accept_gi}: address bits "
                    f"{observed} != MSB-first reference {expected} "
                    f"(mismatching bit positions {mism}); address stream "
                    "must be transmitted MSB first (spec section 4)",
                )

    # ------------------------------------------------------------------
    # Plan item: a_rw_bit_correct (severity error)
    # ------------------------------------------------------------------
    async def _check_a_rw_bit_correct(self) -> None:
        """The R/W bit in the address byte matches the rw input
        (address_byte[0] == rw; the LSB is the last bit in MSB-first
        transmission order)."""
        q = self._queues["a_rw_bit_correct"]
        while True:
            rec = await q.get()
            if not rec.address_valid:
                continue
            if rec.address_bits[-1] != int(rec.rw):
                self._fail(
                    "a_rw_bit_correct",
                    f"txn@accept_gi={rec.accept_gi}: address byte R/W bit "
                    f"(last transmitted, MSB-first) = "
                    f"{rec.address_bits[-1]} != rw input {int(rec.rw)}",
                )

    # ------------------------------------------------------------------
    # Plan item: a_write_data_correct (severity error)
    # ------------------------------------------------------------------
    async def _check_a_write_data_correct(self) -> None:
        """The write data byte transmitted during the write-data phase
        equals tx_data (write transactions)."""
        q = self._queues["a_write_data_correct"]
        while True:
            rec = await q.get()
            if rec.rw == 1:
                continue
            if not rec.write_valid:
                continue
            observed = _bits_from_list(rec.write_bits)
            if observed != int(rec.tx_data):
                self._fail(
                    "a_write_data_correct",
                    f"txn@accept_gi={rec.accept_gi}: write-data byte "
                    f"0x{observed:02x} != tx_data 0x{int(rec.tx_data):02x}",
                )

    # ------------------------------------------------------------------
    # Plan item: a_rx_data_correct (severity error)
    # ------------------------------------------------------------------
    async def _check_a_rx_data_correct(self) -> None:
        """rx_data holds the byte the slave drove on sda_in during the read
        data phase, sampled MSB first (read transactions)."""
        q = self._queues["a_rx_data_correct"]
        while True:
            rec = await q.get()
            if rec.rw == 0:
                continue
            if not rec.read_valid:
                continue
            driven = _bits_from_list(rec.read_bits)
            if int(rec.rx_data) != driven:
                self._fail(
                    "a_rx_data_correct",
                    f"txn@accept_gi={rec.accept_gi}: rx_data "
                    f"0x{int(rec.rx_data):02x} != byte driven on sda_in "
                    f"during the read-data phase 0x{driven:02x}",
                )

    # ------------------------------------------------------------------
    # Plan item: a_addr_ack_error (severity error)
    # ------------------------------------------------------------------
    async def _check_a_addr_ack_error(self) -> None:
        """If the slave NACKs the address (sda_in == 1 at the address-ACK
        sample), ack_error must assert before the next phase."""
        q = self._queues["a_addr_ack_error"]
        while True:
            rec = await q.get()
            if rec.addr_ack is None:
                continue
            if rec.addr_ack == 1:
                ack_high = self._sample_majority(
                    rec.accept_gi,
                    _rel_index_for_advance(ADV_ADDR_ACK, max(1, self.clk_div)),
                    "ack_error",
                )
                if ack_high != 1:
                    self._fail(
                        "a_addr_ack_error",
                        f"txn@accept_gi={rec.accept_gi}: sda_in==1 at the "
                        "address-ACK sample (slave NACKed) but ack_error "
                        "was not asserted in the address-ACK phase",
                    )

    # ------------------------------------------------------------------
    # Plan item: a_data_ack_error (severity error)
    # ------------------------------------------------------------------
    async def _check_a_data_ack_error(self) -> None:
        """If the slave NACKs the write data (sda_in == 1 at the write-data
        ACK sample), ack_error must assert (write transactions)."""
        q = self._queues["a_data_ack_error"]
        while True:
            rec = await q.get()
            if rec.rw == 1:
                continue
            if rec.data_ack is None:
                continue
            if rec.data_ack == 1:
                ack_high = self._sample_majority(
                    rec.accept_gi,
                    _rel_index_for_advance(ADV_DATA_ACK, max(1, self.clk_div)),
                    "ack_error",
                )
                if ack_high != 1:
                    self._fail(
                        "a_data_ack_error",
                        f"txn@accept_gi={rec.accept_gi}: sda_in==1 at the "
                        "write-data-ACK sample (slave NACKed the data) but "
                        "ack_error was not asserted in the data-ACK phase",
                    )

    # ------------------------------------------------------------------
    # Plan item: a_ack_error_clear_on_success (severity error)
    # ------------------------------------------------------------------
    async def _check_a_ack_error_clear_on_success(self) -> None:
        """A fully acknowledged transaction leaves ack_error low: at
        completion, when every expected ACK was observed, ack_error == 0."""
        q = self._queues["a_ack_error_clear_on_success"]
        while True:
            rec = await q.get()
            if rec.rw == 0:
                if rec.addr_ack is None or rec.data_ack is None:
                    continue
                fully_acked = rec.addr_ack == 0 and rec.data_ack == 0
            else:
                if rec.addr_ack is None:
                    continue
                fully_acked = rec.addr_ack == 0
            if fully_acked and int(rec.ack_error) != 0:
                self._fail(
                    "a_ack_error_clear_on_success",
                    f"txn@accept_gi={rec.accept_gi}: ack_error="
                    f"{int(rec.ack_error)} at completion although all "
                    "expected ACKs were observed (ack_error must be 0 on a "
                    "fully acknowledged transaction)",
                )

    # ------------------------------------------------------------------
    # Plan item: a_clk_div_advance_timing (severity error)
    # ------------------------------------------------------------------
    async def _check_a_clk_div_advance_timing(self) -> None:
        """The transaction-engine state advances every CLK_DIV system-clock
        cycles (spec section 9): consecutive address-bit transitions on the
        bus must be exactly CLK_DIV cycles apart.  A flat address (fewer
        than two transitions) is inconclusive and is not graded."""
        q = self._queues["a_clk_div_advance_timing"]
        while True:
            rec = await q.get()
            cdiv = max(1, self.clk_div)
            lo = rec.accept_gi + _rel_index_for_advance(2, cdiv)
            hi = rec.accept_gi + _rel_index_for_advance(9, cdiv)
            positions = []
            prev_level = None
            for gi in range(lo, hi + 1):
                e = self._ring_get(gi)
                if e is None:
                    prev_level = None
                    continue
                level = e.get("sda_level")
                if level not in (0, 1):
                    prev_level = None
                    continue
                if prev_level is not None and level != prev_level:
                    positions.append(gi)
                prev_level = level
            if len(positions) < 2:
                # Flat address (or corrupted divider produced no bits):
                # not enough transitions to judge the cadence -- skip.
                continue
            spacings = [
                positions[i + 1] - positions[i]
                for i in range(len(positions) - 1)
            ]
            bad = [s for s in spacings if s != cdiv]
            if bad:
                self._fail(
                    "a_clk_div_advance_timing",
                    f"txn@accept_gi={rec.accept_gi}: state-advance cadence "
                    f"deviates from CLK_DIV={cdiv}; observed spacing "
                    f"between consecutive address-bit transitions "
                    f"{spacings} cycles (all must equal CLK_DIV)",
                )


# ---------------------------------------------------------------------------
# Convenience launcher for the integration (environment) stage.
# ---------------------------------------------------------------------------
def launch_assertions(pins=None, log=None):
    """Build ``I2CAssertions`` (ConfigDB-shared pins unless given) and
    launch the observer plus every checker with ``cocotb.start_soon``.
    Returns the instance (``.tasks`` are the running checker coroutines)."""
    checks = I2CAssertions(pins=pins, log=log)
    checks.start()
    return checks


# ---------------------------------------------------------------------------
# Watchdog (CONTRACT.md §8/§13.7: an always-running coroutine that fails
# the test if the run does not finish within a bounded number of clock
# cycles, so a hung test cannot silently exhaust the whole simulation).
#
# The watchdog is *armed* and *terminated* by the integration stage (the
# env/test stage, per §13.7):
#   task = launch_watchdog(pins)          # or watchdog(pins, timeout)
#   ...run the test body...
#   task.kill()                           # normal completion
# If the body hangs (busy stuck, FSM dead, no done pulses), the watchdog
# keeps counting rising edges and raises once `timeout_cycles` elapses.
# ---------------------------------------------------------------------------
async def watchdog(pins, timeout_cycles, log=None):
    """Bounded clock-cycle watchdog coroutine.

    Counts rising clock edges; raises :class:`AssertionError` if more than
    ``timeout_cycles`` edges elapse without this task being killed by its
    owner.  A hung FSM with the clock still running is guaranteed to trip
    it.
    """
    log = log if log is not None else _log
    budget = max(1, int(timeout_cycles))
    cycles = 0
    while True:
        await RisingEdge(pins.clk)
        cycles += 1
        if cycles > budget:
            raise AssertionError(
                f"WATCHDOG: test did not finish within {budget} clock "
                "cycles; failing the hung simulation"
            )


def launch_watchdog(pins=None, timeout_cycles=None, log=None):
    """Start the bounded clock-cycle watchdog via ``cocotb.start_soon``.

    ``pins`` defaults to the ConfigDB-shared ``I2CPins`` (CONTRACT.md §6
    key).  ``timeout_cycles`` defaults to ``WATCHDOG_CYCLES`` (the global
    run bound from i2c_pins).  Returns the running cocotb task; the env
    must ``kill()`` it on normal completion.
    """
    log = log if log is not None else _log
    if pins is None:
        pins = ConfigDB().get(None, "", KEY_DUT_PINS)
    if pins is None:
        raise ValueError(
            "launch_watchdog: no I2CPins handle (ConfigDB['%s'] missing); "
            "cannot arm the watchdog",
            KEY_DUT_PINS,
        )
    budget = WATCHDOG_CYCLES if timeout_cycles is None else int(timeout_cycles)
    task = start_soon(watchdog(pins, budget, log=log))
    log.info("WATCHDOG: armed for %d clock cycles", budget)
    return task


# ---------------------------------------------------------------------------
# Plain-Python self-checks (no simulator required): the pure helpers only
# (the observer/checkers need cocotb and a live DUT).
# ---------------------------------------------------------------------------
def _self_test_pure_helpers() -> None:
    assert _majority_bit([]) is None
    assert _majority_bit([0, 0, 1]) == 0
    assert _majority_bit([1, 1, 0]) == 1
    assert _majority_bit([0, 1]) is None
    assert _majority_bit([None, None, 1, 1, 0]) == 1

    # Advance schedule slotting (advance * CLK_DIV); the driver contract.
    assert (ADV_ACCEPT, ADV_ADDR_ACK, ADV_DATA_PHASE_START, ADV_DATA_ACK,
            ADV_STOP) == (0, 10, 11, 19, 20)
    assert _rel_index_for_advance(0, 4) == 0
    assert _rel_index_for_advance(10, 4) == 40
    assert _rel_index_for_advance(19, 4) == 76
    assert _rel_index_for_advance(2, 1) == 2

    # Ring lookup + majority sampling on a synthetic timeline.
    ring = deque(maxlen=8192)
    for gi in range(12):
        ring.append(
            {
                "gi": gi, "sda_in": 1, "sda_out": 1, "sda_oe": 0,
                "scl_out": 1, "scl_oe": 0, "sda_level": 1, "scl_level": 1,
                "done": 1 if gi == 10 else 0, "busy": 0, "ack_error": 0,
                "rx_data": 0, "rst": 1,
            }
        )
    assert _ring_get(ring, 10)["done"] == 1
    assert _ring_get(ring, 0)["done"] == 0
    assert _ring_get(ring, -3) is None
    # A window with only line-high votes returns 1.
    assert _sample_majority_ring(ring, 0, 10, "sda_in", 4) == 1

    # MSB-first assembly helper.
    assert _bits_from_list([1, 0, 1, 0, 0, 0, 0, 0]) == 0xA0
    assert _bits_from_list([0, 0, 0, 0, 0, 0, 0, 0]) == 0x00
    assert _bits_from_list([1] * 8) == 0xFF
    assert _bits_from_list([1, None, 1]) is None

    # Reference-model address bits (the ONLY oracle, §8).
    assert list(_ref_address_bits(0x50, False)) == [1, 0, 1, 0, 0, 0, 0, 0]
    assert list(_ref_address_bits(0x50, True)) == [1, 0, 1, 0, 0, 0, 0, 1]

    # Plan metadata: fifteen plan items, every severity "error".
    assert len(ASSERTION_SEVERITY) == 15, ASSERTION_SEVERITY
    assert len(PIN_CHECKER_NAMES) == 6
    assert len(TXN_CHECKER_NAMES) == 9
    assert PIN_CHECKER_NAMES | TXN_CHECKER_NAMES == set(ASSERTION_SEVERITY)

    print("i2c_assertions: pure-helper self-check OK")


if __name__ == "__main__":
    _self_test_pure_helpers()