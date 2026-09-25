"""AES-128 stimulus sequences (pyuvm ``uvm_sequence`` subclasses).

This module implements the stimulus side of the verification plan
(plans/verification_plan.yaml) for the ``aes128`` DUT:

    * Directed sequences      — one per ``directed_test_scenarios`` entry;
      every class carries a ``SCENARIO_ID`` class attribute that exactly
      matches the plan entry's ``id`` (TC01..TC09).
    * Corner-case sequences   — one per ``corner_cases`` entry.
    * :class:`Aes128RandomizedSeq` — the ``randomized_testing_strategy``
      (constrained-random key/plaintext traffic with periodic reset
      injections between transactions).

Field contract (CONTRACT.md §5): sequences emit :class:`Aes128Transaction`
items whose only driven fields are ``start``, ``key`` and ``plaintext``.  No
extra field is added and no field is renamed.  Clock/reset are NOT
transaction fields: reset is applied by the sequences directly on the shared
``dut.rst_n`` handle (synchronous, active-low) and check actions sample DUT
outputs (``done``/``ciphertext``) through the same ``dut`` handle.

Sequencer handshake (shared with ``driver.py``): a sequence sends an item
with ``start_item()`` / ``finish_item()``; ``finish_item()`` returns only
after the driver has driven the one-cycle ``start`` strobe and released the
item.  The DUT then performs the encryption and pulses ``done``;
sequences *always* observe the ``done`` pulse (bounded wait) before sending
the next transaction, which is what keeps ``start`` strictly idle-only
(CONTRACT.md §7).  Sequence inline checks sample the post-edge values in
cocotb's read-only region (``await ReadOnly()``) — the same sampling
convention as the monitor (CONTRACT.md §2) — and raise a plain Python
``AssertionError`` when a check does not hold, failing the test immediately.

All APIs used here are public Cocotb 2.1.0 (``cocotb.triggers``,
handle ``value``/``setimmediatevalue``) and public pyuvm APIs.
"""

import importlib.util
import os
import pathlib
import random

from cocotb.triggers import ClockCycles, ReadOnly, RisingEdge, Timer
from pyuvm import ConfigDB, uvm_sequence

from transaction import Aes128Transaction

# ---------------------------------------------------------------------------
# Constants (CONTRACT.md §2, §3; plan known-answer vectors)
# ---------------------------------------------------------------------------
MASK128 = (1 << 128) - 1

# FIPS-197 official known-answer vector (spec §8 / reference TEST_VECTORS).
KEY_FIPS = 0x000102030405060708090A0B0C0D0E0F
PT_FIPS = 0x00112233445566778899AABBCCDDEEFF
CT_FIPS = 0x69C4E0D86A7B0430D8CDB78070B4C55A

# All-zero known-answer vector.
KEY_ZERO = 0x00000000000000000000000000000000
PT_ZERO = 0x00000000000000000000000000000000
CT_ZERO = 0x66E94BD4EF8A2C3B884CFA59CA342B2E

# Incrementing known-answer vector.
KEY_INCR = 0x000102030405060708090A0B0C0D0E0F
PT_INCR = 0x000102030405060708090A0B0C0D0E0F
CT_INCR = 0x0A940BB5416EF045F1C39458C653EA5A

# Additional directed-scenario vectors.
KEY_ALT = 0xFFEEDDCCBBAA99887766554433221100   # TC06: second key
PT_ALT = 0x8899AABBCCDDEEFF0011223344556677     # TC07: second plaintext

# Corner-case vectors.
PT_NONZERO = 0x0123456789ABCDEF0123456789ABCDEF  # cc_all_zero_key_nonzero_plaintext
KEY_ILLEGAL = 0xA5A5A5A5A5A5A5A5A5A5A5A5A5A5A5A5  # cc_start_while_busy restart data
PT_ILLEGAL = 0x5A5A5A5A5A5A5A5A5A5A5A5A5A5A5A5A

_DONE_TIMEOUT_CYCLES = 200    # generous: correct DUT done ~12 cycles after start
_RESTART_WATCH_CYCLES = 24    # bounded window used to catch a spurious 2nd done


# ---------------------------------------------------------------------------
# Reference-model access (CONTRACT.md §3)
# ---------------------------------------------------------------------------
def _load_reference_encrypt():
    """Return the reference-model ``aes128_encrypt(plaintext, key)`` callable.

    Resolution order (lazy, so the module imports even when the model is not
    yet on ``sys.path`` at import time):

      1. ``aes128_reference_model`` importable from ``sys.path`` (the
         integration/tb_top stage puts the benchmark directory on
         ``PYTHONPATH``),
      2. the reference model file located next to the sibling
         ``benchmarks/aes128_benchmark_corrupted`` directory when this TB
         runs in the generated tree.
    """
    try:
        from aes128_reference_model import aes128_encrypt  # type: ignore
        return aes128_encrypt
    except Exception:
        pass

    candidates = [
        pathlib.Path(__file__).resolve().parents[4]
        / "benchmarks" / "aes128_benchmark_corrupted" / "aes128_reference_model.py",
        pathlib.Path("/workspace/benchmarks/aes128_benchmark_corrupted/aes128_reference_model.py"),
    ]
    for path in candidates:
        try:
            if path.is_file():
                spec = importlib.util.spec_from_file_location(
                    "aes128_reference_model", str(path)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.aes128_encrypt
        except Exception:
            continue
    return None


_REFERENCE_ENCRYPT = None


def _reference_aes128_encrypt(plaintext, key):
    """``aes128_encrypt(plaintext, key)`` with a 128-bit masked result."""
    global _REFERENCE_ENCRYPT
    if _REFERENCE_ENCRYPT is None:
        _REFERENCE_ENCRYPT = _load_reference_encrypt()
    if _REFERENCE_ENCRYPT is None:
        raise RuntimeError(
            "aes128_reference_model.aes128_encrypt is unavailable; make sure "
            "the benchmark directory is on PYTHONPATH (CONTRACT.md §3)"
        )
    return int(_REFERENCE_ENCRYPT(int(plaintext), int(key))) & MASK128


# ---------------------------------------------------------------------------
# ConfigDB access (CONTRACT.md §4 — exact keys)
# ---------------------------------------------------------------------------
def _config_get(field, default=None):
    """Retrieve a ConfigDB key using the CONTRACT §4 retrieval convention.

    Primary form is ``ConfigDB().get(None, "*", field)`` — the project-wide
    form documented in CONTRACT.md §4.  Some pinned pyuvm releases reject
    wildcard characters in a ``get()`` retrieval path (the integration /
    tb_top stage owns the official shim for that); when the primary form
    raises, we fall back to the equivalent ``inst_name=""`` retrieval
    against the same wildcard-stored key.  No key or value type is changed.
    """
    try:
        return ConfigDB().get(None, "*", field, default=default)
    except Exception:
        return ConfigDB().get(None, "", field, default=default)


# ---------------------------------------------------------------------------
# Shared sequence infrastructure
# ---------------------------------------------------------------------------
class Aes128SeqBase(uvm_sequence):
    """Common helpers for all AES-128 stimulus sequences.

    Subclasses implement ``async def body()``.  ConfigDB keys are read
    exactly as documented in CONTRACT.md §4 (``"dut"``, optional
    ``"Aes128DutHelper"``).  Clock/reset are structural signals and never
    part of a sequence item.
    """

    def __init__(self, name="aes128_sequence"):
        super().__init__(name)
        self.dut = None
        self._helper = None

    # -- environment resolution ----------------------------------------
    async def _setup(self):
        """Resolve the shared DUT handle and the optional helper."""
        self.dut = _config_get("dut")
        if self.dut is None:
            raise RuntimeError(
                f"[{self._tag()}] 'dut' not found in ConfigDB (key 'dut' must "
                "be set by the tb_top layer before sequences run)"
            )
        try:
            from dut_helper import Aes128DutHelper
        except Exception:  # pragma: no cover - helper lives next to sequences
            Aes128DutHelper = None
        helper = _config_get("Aes128DutHelper")
        if helper is None and Aes128DutHelper is not None:
            helper = Aes128DutHelper(self.dut)
        self._helper = helper

    def _tag(self):
        """Scenario tag used in log/assert messages (SCENARIO_ID if any)."""
        return getattr(self, "SCENARIO_ID", None) or self.get_name()

    # -- low-level pin primitives --------------------------------------
    def _drive(self, start, key, plaintext):
        """Synchronously drive the stimulus pins (masked to width)."""
        if self._helper is not None:
            self._helper.drive(
                int(start) & 0x1, int(key) & MASK128, int(plaintext) & MASK128
            )
        else:
            self.dut.start.setimmediatevalue(int(start) & 0x1)
            self.dut.key.setimmediatevalue(int(key) & MASK128)
            self.dut.plaintext.setimmediatevalue(int(plaintext) & MASK128)

    def _drive_idle(self):
        """Return stimulus pins to idle (``start=0``)."""
        if self._helper is not None:
            self._helper.idle()
        else:
            self.dut.start.setimmediatevalue(0)

    async def _wait(self, cycles):
        """Wait ``cycles`` clock cycles (no stimulus change; inputs stay idle)."""
        if cycles is not None and int(cycles) > 0:
            await ClockCycles(self.dut.clk, int(cycles))

    async def _reset(self, assert_cycles=2, idle_cycles=2):
        """Apply the canonical synchronous active-low reset (CONTRACT.md §6).

        ``rst_n`` is held low for ``assert_cycles`` rising edges with all
        stimulus pins idle, deasserted, then ``idle_cycles`` rising edges of
        settle time.  After this the DUT is expected to be idle with
        ``done == 0``.
        """
        # Callers may invoke this right after a read-only sample (e.g. the
        # `_wait_done`/`_check_done_low` helpers end in `await ReadOnly()`),
        # so we are still inside a cocotb GPI callback frame here.  Yielding
        # to the simulator leaves that frame and makes the following
        # setimmediatevalue writes (including reset) legal outside of the
        # ReadOnly phase.
        await Timer(1, "step")
        if self._helper is not None:
            await self._helper.reset_sync_active_low(
                int(assert_cycles), int(idle_cycles)
            )
        else:
            self._drive_idle()
            self.dut.rst_n.setimmediatevalue(0)
            await ClockCycles(self.dut.clk, max(1, int(assert_cycles)))
            self.dut.rst_n.setimmediatevalue(1)
            await ClockCycles(self.dut.clk, max(0, int(idle_cycles)))

    # -- high-level stimulus primitives ---------------------------------
    async def _send_transaction(self, key, plaintext, start=1):
        """Send one ``Aes128Transaction`` through the sequencer.

        ``start`` is the strobe value the driver asserts for exactly one
        rising edge (normally 1).  ``finish_item()`` returns after the
        driver has driven the strobe; the sequence is then responsible for
        observing the ``done`` pulse before the next transaction.
        """
        item = Aes128Transaction("stim")
        item.key = int(key) & MASK128
        item.plaintext = int(plaintext) & MASK128
        item.start = int(start) & 0x1
        await self.start_item(item)
        await self.finish_item(item)
        return item

    # -- checking / observation primitives ------------------------------
    async def _wait_done(self, timeout_cycles=_DONE_TIMEOUT_CYCLES):
        """Wait until ``done`` pulses high (post-edge), bounded.

        Returns the 0-based cycle index (relative to the poll start) at
        which ``done`` was observed high.  Raises ``AssertionError`` if no
        ``done`` pulse appears within ``timeout_cycles`` (so a hung DUT
        fails the test immediately instead of stalling the run).
        """
        for cycle in range(int(timeout_cycles)):
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            if int(self.dut.done.value) == 1:
                return int(cycle)
        raise AssertionError(
            f"[{self._tag()}] done never pulsed within {int(timeout_cycles)} "
            "clock cycles of the transaction start"
        )

    async def _wait_done_and_capture(self, timeout_cycles=_DONE_TIMEOUT_CYCLES):
        """Wait for ``done``; return post-edge ``done``/``ciphertext``/``cycle``.

        ``done`` and ``ciphertext`` are read in the SAME read-only region
        (CONTRACT.md §2 sampling convention), so the returned ciphertext is
        the value valid while ``done`` is high.
        """
        for cycle in range(int(timeout_cycles)):
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            if int(self.dut.done.value) == 1:
                return {
                    "done": 1,
                    "ciphertext": int(self.dut.ciphertext.value) & MASK128,
                    "cycle": int(cycle),
                }
        raise AssertionError(
            f"[{self._tag()}] done never pulsed within {int(timeout_cycles)} "
            "clock cycles of the transaction start"
        )

    async def _check_done_low(self, context=""):
        """Assert ``done`` is low (post-edge, read-only region)."""
        await ReadOnly()
        done = int(self.dut.done.value)
        if done != 0:
            raise AssertionError(
                f"[{self._tag()}] {context}: expected done==0, got {done}"
            )

    async def _assert_done_low_for(self, cycles, context=""):
        """Assert ``done`` stays low for ``cycles`` consecutive clock cycles."""
        for _ in range(int(cycles)):
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            if int(self.dut.done.value) != 0:
                raise AssertionError(
                    f"[{self._tag()}] {context}: unexpected done pulse within "
                    f"{int(cycles)} cycles"
                )

    def _assert_ciphertext(self, actual, expected, context=""):
        """Assert a sampled ciphertext equals the expected 128-bit value."""
        if int(actual) != int(expected):
            raise AssertionError(
                f"[{self._tag()}] {context}: ciphertext mismatch: "
                f"expected 0x{int(expected):032x}, got 0x{int(actual):032x}"
            )

    async def _reset_and_sync(self, assert_cycles=2, idle_cycles=1):
        """Plan default reset prologue and a done-low sanity check."""
        await self._reset(int(assert_cycles), int(idle_cycles))
        await self._check_done_low("after reset")


# ---------------------------------------------------------------------------
# Directed scenarios (plan 'directed_test_scenarios') — TC01..TC09
#
# Every class below has a class-level SCENARIO_ID matching the plan id
# exactly.  The SCENARIO_ID registry + assertion at the end of this section
# guards this invariant at import time.
# ---------------------------------------------------------------------------
class ResetReleaseIdleSeq(Aes128SeqBase):
    """TC01 reset_release_idle.

    Assert/release the synchronous reset, verify the DUT is idle (``done``
    low), and verify a transaction can be started afterwards.
    """

    SCENARIO_ID = "TC01"

    def __init__(self, name="ResetReleaseIdleSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC01] reset_release_idle: begin")
        # reset asserted for 3 cycles, released, 2 idle cycles (plan).
        await self._reset(assert_cycles=3, idle_cycles=2)
        # action: check done == 0 after reset.
        await self._check_done_low("done must be low after reset (TC01)")
        # description: verify a transaction can be started afterwards.
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        res = await self._wait_done_and_capture()
        self._assert_ciphertext(
            res["ciphertext"], CT_FIPS,
            "first transaction after reset must complete correctly",
        )
        self.logger.info("[TC01] reset_release_idle: passed")


class Fips197KnownAnswerSeq(Aes128SeqBase):
    """TC02 fips197_known_answer.

    Encrypt the official FIPS-197 vector and compare against the mandated
    ciphertext.
    """

    SCENARIO_ID = "TC02"

    def __init__(self, name="Fips197KnownAnswerSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC02] fips197_known_answer: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        res = await self._wait_done_and_capture()
        # action: check ciphertext sampled while done is high.
        self._assert_ciphertext(res["ciphertext"], CT_FIPS, "FIPS-197 vector")
        self.logger.info("[TC02] fips197_known_answer: passed")


class AllZeroKnownAnswerSeq(Aes128SeqBase):
    """TC03 all_zero_known_answer.

    Encrypt the all-zero key/plaintext and compare against the mandated
    ciphertext.
    """

    SCENARIO_ID = "TC03"

    def __init__(self, name="AllZeroKnownAnswerSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC03] all_zero_known_answer: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_ZERO, PT_ZERO)
        res = await self._wait_done_and_capture()
        self._assert_ciphertext(res["ciphertext"], CT_ZERO, "all-zero vector")
        self.logger.info("[TC03] all_zero_known_answer: passed")


class IncrementingKnownAnswerSeq(Aes128SeqBase):
    """TC04 incrementing_known_answer.

    Encrypt the incrementing vector and compare against the mandated
    ciphertext.
    """

    SCENARIO_ID = "TC04"

    def __init__(self, name="IncrementingKnownAnswerSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC04] incrementing_known_answer: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_INCR, PT_INCR)
        res = await self._wait_done_and_capture()
        self._assert_ciphertext(res["ciphertext"], CT_INCR, "incrementing vector")
        self.logger.info("[TC04] incrementing_known_answer: passed")


class BackToBackTransactionsSeq(Aes128SeqBase):
    """TC05 back_to_back_transactions.

    Run two complete transactions back to back; each must produce the
    reference ciphertext for its own key/plaintext pair.  Also verifies the
    DUT accepts a new transaction once ``done`` is observed.
    """

    SCENARIO_ID = "TC05"

    def __init__(self, name="BackToBackTransactionsSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC05] back_to_back_transactions: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        # First transaction: FIPS-197 vector.
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        res1 = await self._wait_done_and_capture()
        self._assert_ciphertext(res1["ciphertext"], CT_FIPS, "transaction 1")
        # Second transaction: all-zero vector (accepted once done observed).
        await self._send_transaction(KEY_ZERO, PT_ZERO)
        res2 = await self._wait_done_and_capture()
        self._assert_ciphertext(
            res2["ciphertext"], CT_ZERO,
            "transaction 2 must produce its own reference result; "
            "transaction 1 result must be unaffected",
        )
        self.logger.info("[TC05] back_to_back_transactions: passed")


class KeySensitivitySeq(Aes128SeqBase):
    """TC06 key_sensitivity.

    Fix plaintext, use two different keys; both ciphertexts must match the
    reference model and must differ from each other.
    """

    SCENARIO_ID = "TC06"

    def __init__(self, name="KeySensitivitySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC06] key_sensitivity: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        # key_a (plan) then key_b; same plaintext.
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        ct_a = (await self._wait_done_and_capture())["ciphertext"]
        await self._send_transaction(KEY_ALT, PT_FIPS)
        ct_b = (await self._wait_done_and_capture())["ciphertext"]
        self._assert_ciphertext(
            ct_a, _reference_aes128_encrypt(PT_FIPS, KEY_FIPS), "key_a result"
        )
        self._assert_ciphertext(
            ct_b, _reference_aes128_encrypt(PT_FIPS, KEY_ALT), "key_b result"
        )
        if ct_a == ct_b:
            raise AssertionError(
                f"[{self._tag()}] key sensitivity violated: ciphertext(key_a) == "
                f"ciphertext(key_b) == 0x{ct_a:032x}"
            )
        self.logger.info("[TC06] key_sensitivity: passed")


class PlaintextSensitivitySeq(Aes128SeqBase):
    """TC07 plaintext_sensitivity.

    Fix key, use two different plaintexts; both ciphertexts must match the
    reference model and must differ from each other.
    """

    SCENARIO_ID = "TC07"

    def __init__(self, name="PlaintextSensitivitySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC07] plaintext_sensitivity: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        # plaintext_a (plan) then plaintext_b; same key.
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        ct_a = (await self._wait_done_and_capture())["ciphertext"]
        await self._send_transaction(KEY_FIPS, PT_ALT)
        ct_b = (await self._wait_done_and_capture())["ciphertext"]
        self._assert_ciphertext(
            ct_a, _reference_aes128_encrypt(PT_FIPS, KEY_FIPS), "plaintext_a result"
        )
        self._assert_ciphertext(
            ct_b, _reference_aes128_encrypt(PT_ALT, KEY_FIPS), "plaintext_b result"
        )
        if ct_a == ct_b:
            raise AssertionError(
                f"[{self._tag()}] plaintext sensitivity violated: "
                f"ciphertext(plaintext_a) == ciphertext(plaintext_b) == "
                f"0x{ct_a:032x}"
            )
        self.logger.info("[TC07] plaintext_sensitivity: passed")


class DeterminismRepeatedEncryptionSeq(Aes128SeqBase):
    """TC08 determinism_repeated_encryption.

    Encrypt the identical (key, plaintext) pair twice; both ciphertexts
    must be identical and equal the reference result.
    """

    SCENARIO_ID = "TC08"

    def __init__(self, name="DeterminismRepeatedEncryptionSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC08] determinism_repeated_encryption: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        ct_run1 = (await self._wait_done_and_capture())["ciphertext"]
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        ct_run2 = (await self._wait_done_and_capture())["ciphertext"]
        exp = _reference_aes128_encrypt(PT_FIPS, KEY_FIPS)
        self._assert_ciphertext(ct_run1, exp, "run 1")
        self._assert_ciphertext(ct_run2, exp, "run 2")
        if ct_run1 != ct_run2:
            raise AssertionError(
                f"[{self._tag()}] determinism violated: run1=0x{ct_run1:032x} "
                f"!= run2=0x{ct_run2:032x}"
            )
        self.logger.info("[TC08] determinism_repeated_encryption: passed")


class DonePulseAndStartIgnoredWhileBusySeq(Aes128SeqBase):
    """TC09 done_pulse_and_start_ignored_while_busy.

    Verify ``done`` pulses for exactly one cycle and that a ``start``
    asserted while a transaction is in flight is ignored and does not
    corrupt the running transaction (which completes with the originally
    captured key/plaintext).
    """

    SCENARIO_ID = "TC09"

    def __init__(self, name="DonePulseAndStartIgnoredWhileBusySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("[TC09] done_pulse_and_start_ignored_while_busy: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        # Illegal restart while the transaction is in flight: the strobe is
        # driven again directly on the pins; per spec it must be ignored.
        self._drive(1, KEY_FIPS, PT_FIPS)
        await ClockCycles(self.dut.clk, 2)
        self._drive_idle()
        res = await self._wait_done_and_capture()
        self._assert_ciphertext(
            res["ciphertext"], CT_FIPS,
            "running transaction must complete with the originally captured data",
        )
        # done is a single-cycle pulse: one cycle after the pulse it is low.
        await self._wait(1)
        await self._check_done_low(
            "done must already be low again (single-cycle pulse), TC09"
        )
        # The ignored restart must not spawn a second transaction (bonus
        # bounded check that done stays low; the assertions stage counts
        # done pulses rigorously).
        await self._assert_done_low_for(
            _RESTART_WATCH_CYCLES, "no second done from ignored restart (TC09)"
        )
        self.logger.info("[TC09] done_pulse_and_start_ignored_while_busy: passed")


# ---------------------------------------------------------------------------
# Registry of directed sequences.  SCENARIO_IDs are authoritative (plan ids);
# the checks below are build-time guards on that invariant.
# ---------------------------------------------------------------------------
DIRECTED_SEQUENCES = [
    ("TC01", ResetReleaseIdleSeq),
    ("TC02", Fips197KnownAnswerSeq),
    ("TC03", AllZeroKnownAnswerSeq),
    ("TC04", IncrementingKnownAnswerSeq),
    ("TC05", BackToBackTransactionsSeq),
    ("TC06", KeySensitivitySeq),
    ("TC07", PlaintextSensitivitySeq),
    ("TC08", DeterminismRepeatedEncryptionSeq),
    ("TC09", DonePulseAndStartIgnoredWhileBusySeq),
]

DIRECTED_SCENARIO_IDS = [sid for sid, _ in DIRECTED_SEQUENCES]
assert len(set(DIRECTED_SCENARIO_IDS)) == len(DIRECTED_SCENARIO_IDS), (
    "duplicate SCENARIO_ID in directed sequences"
)
assert set(DIRECTED_SCENARIO_IDS) == {
    "TC01", "TC02", "TC03", "TC04", "TC05",
    "TC06", "TC07", "TC08", "TC09",
}, "directed sequence SCENARIO_ID set does not match plan ids"
assert all(
    getattr(cls, "SCENARIO_ID", None) == sid for sid, cls in DIRECTED_SEQUENCES
), "directed sequence class SCENARIO_ID must match its registry entry"


# ---------------------------------------------------------------------------
# Corner-case sequences (plan 'corner_cases').
# These are separate verification strategies and therefore intentionally carry
# no SCENARIO_ID (they do not directly implement a directed scenario).
# ---------------------------------------------------------------------------
class CornerAllOnesSeq(Aes128SeqBase):
    """cc_all_ones: key and plaintext both 128'hFF..FF.

    Ciphertext must equal the reference-model result for
    ``aes128_encrypt(0xFFFF..FF, 0xFFFF..FF)``.
    """

    def __init__(self, name="CornerAllOnesSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("cc_all_ones: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(MASK128, MASK128)
        res = await self._wait_done_and_capture()
        exp = _reference_aes128_encrypt(MASK128, MASK128)
        self._assert_ciphertext(res["ciphertext"], exp, "all-ones vector")
        self.logger.info("cc_all_ones: passed")


class CornerAlternatingPatternsSeq(Aes128SeqBase):
    """cc_alternating_patterns: alternating byte patterns 0xAA..AA / 0x55..55.

    Runs both pattern combinations; each result must match the reference
    model.
    """

    def __init__(self, name="CornerAlternatingPatternsSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("cc_alternating_patterns: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        aa = 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        uu = 0x55555555555555555555555555555555
        # Pattern (1): key = 0xAA..AA, plaintext = 0x55..55.
        await self._send_transaction(aa, uu)
        res1 = await self._wait_done_and_capture()
        self._assert_ciphertext(
            res1["ciphertext"],
            _reference_aes128_encrypt(uu, aa),
            "alternating pattern 1 (key=0xAA..AA, pt=0x55..55)",
        )
        # Pattern (2): key = 0x55..55, plaintext = 0xAA..AA.
        await self._send_transaction(uu, aa)
        res2 = await self._wait_done_and_capture()
        self._assert_ciphertext(
            res2["ciphertext"],
            _reference_aes128_encrypt(aa, uu),
            "alternating pattern 2 (key=0x55..55, pt=0xAA..AA)",
        )
        self.logger.info("cc_alternating_patterns: passed")


class CornerAllZeroKeyNonzeroPlaintextSeq(Aes128SeqBase):
    """cc_all_zero_key_nonzero_plaintext: zero key, non-zero plaintext.

    Ciphertext must match the reference model for
    ``aes128_encrypt(0x0123456789abcdef0123456789abcdef, 0)``.
    """

    def __init__(self, name="CornerAllZeroKeyNonzeroPlaintextSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("cc_all_zero_key_nonzero_plaintext: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_ZERO, PT_NONZERO)
        res = await self._wait_done_and_capture()
        exp = _reference_aes128_encrypt(PT_NONZERO, KEY_ZERO)
        self._assert_ciphertext(
            res["ciphertext"], exp,
            "zero-key / non-zero-plaintext vector",
        )
        self.logger.info("cc_all_zero_key_nonzero_plaintext: passed")


class CornerStartWhileBusySeq(Aes128SeqBase):
    """cc_start_while_busy: assert start mid-transaction.

    Per spec the restart must be ignored, the running transaction must
    complete with the originally captured key/plaintext, and no extra
    ``done`` pulse may appear.
    """

    def __init__(self, name="CornerStartWhileBusySeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("cc_start_while_busy: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        # Mid-transaction illegal restart with DIFFERENT data on the pins:
        # the DUT must ignore the strobe and keep the originally captured
        # key/plaintext.
        self._drive(1, KEY_ILLEGAL, PT_ILLEGAL)
        await ClockCycles(self.dut.clk, 2)
        self._drive_idle()
        res = await self._wait_done_and_capture()
        exp = _reference_aes128_encrypt(PT_FIPS, KEY_FIPS)
        self._assert_ciphertext(
            res["ciphertext"], exp,
            "running transaction must be unchanged by the ignored restart",
        )
        # No extra done pulse from the ignored restart (bounded window).
        await self._assert_done_low_for(
            _RESTART_WATCH_CYCLES, "cc_start_while_busy: no extra done pulse"
        )
        self.logger.info("cc_start_while_busy: passed")


class CornerResetMidTransactionSeq(Aes128SeqBase):
    """cc_reset_mid_transaction: assert reset during an in-progress
    encryption.

    The transaction state must be cleared; after reset the DUT must be idle
    (``done`` low) and a fresh transaction must run correctly and match the
    reference model.
    """

    def __init__(self, name="CornerResetMidTransactionSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("cc_reset_mid_transaction: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        # Assert reset while the encryption is in flight (3 low cycles +
        # 2 idle cycles).  The transaction state is cleared.
        await self._reset(assert_cycles=3, idle_cycles=2)
        await self._check_done_low("DUT must be idle (done low) after mid reset")
        # A fresh transaction afterwards must run correctly.
        await self._send_transaction(KEY_INCR, PT_INCR)
        res = await self._wait_done_and_capture()
        exp = _reference_aes128_encrypt(PT_INCR, KEY_INCR)
        self._assert_ciphertext(
            res["ciphertext"], exp,
            "post-reset transaction must match the reference model",
        )
        self.logger.info("cc_reset_mid_transaction: passed")


class CornerImmediateRestartAfterDoneSeq(Aes128SeqBase):
    """cc_immediate_restart_after_done: start the next transaction as soon
    as the previous one's ``done`` pulse is observed.

    The next transaction must be accepted and match the reference model.
    """

    def __init__(self, name="CornerImmediateRestartAfterDoneSeq"):
        super().__init__(name)

    async def body(self):
        await self._setup()
        self.logger.info("cc_immediate_restart_after_done: begin")
        await self._reset_and_sync(assert_cycles=2, idle_cycles=1)
        await self._send_transaction(KEY_FIPS, PT_FIPS)
        await self._wait_done()  # observe the done pulse
        # Immediate restart: send the next transaction right away (the
        # surrounding framework re-drives start within a couple of cycles).
        await self._send_transaction(KEY_INCR, PT_INCR)
        res = await self._wait_done_and_capture()
        exp = _reference_aes128_encrypt(PT_INCR, KEY_INCR)
        self._assert_ciphertext(
            res["ciphertext"], exp,
            "immediate successor transaction must match the reference model",
        )
        self.logger.info("cc_immediate_restart_after_done: passed")


# ---------------------------------------------------------------------------
# Randomized traffic (plan 'randomized_testing_strategy').
# ---------------------------------------------------------------------------
class Aes128RandomizedSeq(Aes128SeqBase):
    """Directed-random stimulus over the full 128-bit key/plaintext space.

    Every transaction uses a uniformly random 128-bit ``key`` and 128-bit
    ``plaintext`` (plan constraint ranges [0, 2**128 - 1]).  Only valid
    protocol usage is randomized: ``start`` is only ever asserted while the
    DUT is idle (the sequence waits for the ``done`` pulse before sending
    the next transaction).  A small fraction of the run — one in
    ``reset_every_n`` transactions (plan: 1 in 20) — injects a low reset
    pulse of 1..4 cycles *between* transactions to exercise idle recovery.

    The scoreboard/assertions stages check every accepted transaction
    against ``aes128_encrypt(plaintext, key)`` and the done-pulse protocol;
    this sequence only produces the stimulus and bounds the ``done`` wait.

    Tuning attributes (set before ``start()``): ``num_txns``,
    ``reset_every_n`` (or ``None`` to disable), ``seed``.
    """

    num_txns = 41
    reset_every_n = 20   # plan: 1 in 20 transactions get a reset injection
    reset_duration = (1, 4)   # plan: low-pulse width in cycles
    seed = None          # deterministic default; override via RANDOM_SEED

    def __init__(self, name="Aes128RandomizedSeq"):
        super().__init__(name)
        self._seed = None  # resolved seed actually used (see body)

    async def _inject_reset(self, duration):
        """Inject a low reset pulse of ``duration`` cycles and re-sync."""
        await self._reset(assert_cycles=int(duration), idle_cycles=2)
        await self._check_done_low("after randomized reset injection")

    async def body(self):
        await self._setup()
        # Resolve the RNG seed (deterministic by default):
        #   1) explicit class/instance seed if set,
        #   2) else the RANDOM_SEED environment variable when present,
        #   3) else a stable per-process hash of the sequence name.
        seed = self.seed
        if seed is None:
            env_seed = os.environ.get("RANDOM_SEED")
            if env_seed:
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
        num_txns = int(self.num_txns)
        reset_every_n = (
            int(self.reset_every_n) if self.reset_every_n else None
        )
        self.logger.info(
            "Aes128RandomizedSeq: seed=%d num_txns=%d reset_every_n=%s "
            "reset_duration=%s",
            seed, num_txns, reset_every_n, tuple(self.reset_duration),
        )

        await self._reset(assert_cycles=2, idle_cycles=2)
        injected = 0
        for i in range(num_txns):
            # Plan injection: reset between transactions, 1 in 20.
            if i > 0 and reset_every_n is not None and i % reset_every_n == 0:
                duration = rng.randint(*self.reset_duration)
                self.logger.info(
                    "Aes128RandomizedSeq: injecting reset (%d cycles) between "
                    "transactions %d and %d",
                    duration, i, i + 1,
                )
                await self._inject_reset(duration)
                injected += 1
            key = rng.getrandbits(128)
            plaintext = rng.getrandbits(128)
            await self._send_transaction(key, plaintext)
            await self._wait_done(timeout_cycles=_DONE_TIMEOUT_CYCLES)
        self.logger.info(
            "Aes128RandomizedSeq: completed %d randomized transactions "
            "(%d reset injections)",
            num_txns, injected,
        )


# ---------------------------------------------------------------------------
# Convenient collections of all stimulus-sequence classes for later stages.
# ---------------------------------------------------------------------------
CORNER_SEQUENCES = [
    CornerAllOnesSeq,
    CornerAlternatingPatternsSeq,
    CornerAllZeroKeyNonzeroPlaintextSeq,
    CornerStartWhileBusySeq,
    CornerResetMidTransactionSeq,
    CornerImmediateRestartAfterDoneSeq,
]

ALL_STIMULUS_SEQUENCES = (
    [cls for _, cls in DIRECTED_SEQUENCES] + CORNER_SEQUENCES
    + [Aes128RandomizedSeq]
)