"""AES-128 UVM stimulus sequences (stage 6 integration).

This module implements every scenario of the verification plan
(``plans/verification_plan.yaml``):

* the 11 directed scenario sequences (each pinned to its plan
  ``SCENARIO_ID``),
* the 5 corner-case sequences (no plan-ID; they extend the core directed
  set), and
* :class:`AESRandomizedSequence`, the randomized stimulus strategy
  (1000 random 128-bit pairs by default, ~10% idle reset injection, ~5%
  in-flight reset injection).

SEQUENCE vs. SCOREBOARD division of labor (``CONTRACT.md`` "Verification
isolation"): sequences drive *stimulus only*.  They never compare DUT output
against expected ciphertext values, because the target RTL is intentionally
buggy (plan ``DISC-001``: the final-round MixColumns guard never fires, so
MixColumns runs in all ten rounds).  The oracle comparison is performed
exclusively by :class:`tb.scoreboard.AES128Scoreboard`, whose mismatch
report is the intended bug-detection signal.  Sequences are allowed to check
*structural* timing properties (single-cycle ``done`` pulse, done completes
the in-flight transaction, outputs return to idle) because those are
scenario premises rather than cryptography.

Stimulus command conventions (``CONTRACT.md`` section 7.5): the active
driver offers each item; the sequence's own pin pokes (extra ``start``
activity while busy, reset injection) are performed only while the driver is
parked between items, so offer and poke never race.
"""

import os
import random as _random

import cocotb
from cocotb.triggers import RisingEdge

from pyuvm import ConfigDB, uvm_sequence

from tb.transaction import AES128Transaction

__all__ = [
    "PLAN_DIRECTED_IDS",
    "AESScenarioBase",
    "NistKatSeq",
    "AllZerosSeq",
    "AllOnesSeq",
    "AlternatingSeq",
    "ZeroKeyNonzeroPtSeq",
    "NonzeroKeyZeroPtSeq",
    "InputChangeWhileBusySeq",
    "RepeatedTransactionsSeq",
    "DonePulseWidthSeq",
    "ResetDuringIdleSeq",
    "ResetMidTransactionSeq",
    "CornerSingleBitKeySeq",
    "CornerFastRetriggerSeq",
    "CornerAllOnesKeyZeroPtSeq",
    "CornerZeroKeyAllOnesPtSeq",
    "CornerStartIgnoredWhenBusySeq",
    "AESRandomizedSequence",
    "DIRECTED_SEQUENCE_CLASSES",
    "CORNER_CASE_SEQUENCE_CLASSES",
    "verify_directed_scenario_ids",
]

# --------------------------------------------------------------------------
# Scenario identifiers (must be exactly the 11 plan IDs, each used once)
# --------------------------------------------------------------------------
PLAN_DIRECTED_IDS = (
    "nist_kat",
    "all_zeros",
    "all_ones",
    "alternating",
    "zero_key_nonzero_pt",
    "nonzero_key_zero_pt",
    "input_change_while_busy",
    "repeated_transactions",
    "done_pulse_width",
    "reset_during_idle",
    "reset_mid_transaction",
)

# --------------------------------------------------------------------------
# Stimulus constants (CONTRACT.md + FIPS-197 Appendix B / plan)
# --------------------------------------------------------------------------
KEY_NIST = 0x000102030405060708090A0B0C0D0E0F
PT_NIST = 0x00112233445566778899AABBCCDDEEFF
KEY_ALL_ONES = (1 << 128) - 1
PT_ALL_ONES = (1 << 128) - 1
KEY_ALTERNATING = 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
PT_ALTERNATING = 0x55555555555555555555555555555555


def _config_get(field_name):
    """Global ConfigDB read (context ``None`` matches ``"*"`` stores)."""
    return ConfigDB().get(None, "", field_name)


def _helper():
    """Shared :class:`tb.dut_helper.AES128DUTHelper` (CONTRACT.md 7.3)."""
    return _config_get("dut_helper")


def _dut():
    """Top-module sim handle (CONTRACT.md 7.3)."""
    return _config_get("dut")


class AESScenarioBase(uvm_sequence):
    """Scenario building blocks shared by every stimulus sequence.

    Class-level ``SCENARIO_ID`` pins a directed sequence to its plan ID;
    corner sequences keep ``SCENARIO_ID = None``.
    """

    SCENARIO_ID = None
    #: Clock cycles the bench-level reset is held low at scenario start.
    RESET_CYCLES = 5
    #: Idle clock cycles after reset deassert before stimulus begins.
    SETTLE_CYCLES = 2
    #: Bounded wait for ``done`` (12-cycle latency, generous margin).
    DONE_TIMEOUT_CYCLES = 64
    #: Bounded wait for ``busy`` to rise after an offer.
    BUSY_RISE_TIMEOUT_CYCLES = 16

    # -- low-level helpers ------------------------------------------------

    async def _reset(self, cycles=None, settle=None):
        """Bench-level reset: pull ``rst_n`` low, then release and settle.

        All stimulus pins are parked in reset-legal state during the pulse.
        """
        helper = _helper()
        helper.start = 0
        helper.key = 0
        helper.plaintext = 0
        helper.rst_n = 0
        await self._clock_edges(cycles if cycles is not None else self.RESET_CYCLES)
        helper.rst_n = 1
        await self._clock_edges(settle if settle is not None else self.SETTLE_CYCLES)

    async def _assert_reset(self, cycles):
        """Assert ``rst_n`` for the given number of cycles (no deassert)."""
        helper = _helper()
        helper.start = 0
        helper.rst_n = 0
        await self._clock_edges(cycles)

    async def _deassert_reset(self, settle=None):
        """Release ``rst_n`` and settle."""
        helper = _helper()
        helper.rst_n = 1
        await self._clock_edges(settle if settle is not None else self.SETTLE_CYCLES)

    @staticmethod
    async def _clock_edges(num_cycles):
        for _ in range(num_cycles):
            await RisingEdge(_dut().clk)

    async def _wait_busy(self, timeout=None):
        """Wait until ``busy`` rises (offer acceptance)."""
        helper = _helper()
        limit = timeout if timeout is not None else self.BUSY_RISE_TIMEOUT_CYCLES
        for _ in range(limit):
            await RisingEdge(helper.dut.clk)
            if int(helper.busy) == 1:
                return
        raise AssertionError(
            f"{self.get_name()}: busy did not rise within {limit} cycles"
        )

    async def _wait_done(self, timeout=None):
        """Wait for the transaction's ``done`` pulse; check its structure.

        On success returns ``(ciphertext, busy, done)`` sampled on the
        ``done`` edge.  Raises :class:`AssertionError` if the pulse never
        arrives (timeout), is wider than one clock, or the DUT aborts
        (reset during operation / busy fell without done).
        """
        helper = _helper()
        limit = timeout if timeout is not None else self.DONE_TIMEOUT_CYCLES
        for _ in range(limit):
            await RisingEdge(helper.dut.clk)
            rst = int(helper.rst_n)
            busy = int(helper.busy)
            done = int(helper.done)
            if rst == 0:
                raise AssertionError(
                    f"{self.get_name()}: reset asserted while waiting for done"
                )
            if done == 1:
                if busy != 0:
                    raise AssertionError(
                        f"{self.get_name()}: busy=={busy} while done pulses "
                        f"(done must accompany the busy deassertion)"
                    )
                sample = (int(helper.ciphertext), busy, done)
                await RisingEdge(helper.dut.clk)
                if int(helper.done) != 0:
                    raise AssertionError(
                        f"{self.get_name()}: done pulse wider than one clock"
                    )
                return sample
            if busy == 0:
                raise AssertionError(
                    f"{self.get_name()}: busy fell before done "
                    f"(transaction aborted or never accepted)"
                )
        raise AssertionError(
            f"{self.get_name()}: timed out waiting for done "
            f"({limit} cycles)"
        )

    # -- stimulus delivery -------------------------------------------------

    async def _drive(self, key, plaintext, start=1, tag="tx"):
        """Offer one item through the sequencer/driver (fire-and-forget)."""
        item = AES128Transaction(f"{self.get_name()}_{tag}")
        item.set_inputs(int(start), int(key), int(plaintext))
        await self.start_item(item)
        await self.finish_item(item)
        return item

    async def _drive_and_wait(self, key, plaintext, tag="tx"):
        """Offer one item and wait for its ``done`` (full directed step)."""
        item = await self._drive(key, plaintext, tag=tag)
        outs = await self._wait_done()
        return item, outs

    # -- scenario body (override in subclasses) ----------------------------

    async def body(self):
        raise NotImplementedError(f"{self.get_name()}: body() not implemented")


# --------------------------------------------------------------------------
# Directed scenario sequences (plan IDs)
# --------------------------------------------------------------------------
class NistKatSeq(AESScenarioBase):
    """``nist_kat`` - FIPS-197 Appendix B known-answer test vector."""

    SCENARIO_ID = "nist_kat"

    async def body(self):
        await self._reset()
        item, outs = await self._drive_and_wait(KEY_NIST, PT_NIST)
        self.logger.info(
            "%s: nist_kat done - ciphertext=%#034x", self.get_name(), outs[0]
        )
        self.logger.debug(
            "%s: nist_kat - reference oracle would produce the FIPS-197 "
            "value; DUT mismatch is scored by the scoreboard (DISC-001)",
            self.get_name(),
        )


class AllZerosSeq(AESScenarioBase):
    """``all_zeros`` - all-zero key and plaintext."""

    SCENARIO_ID = "all_zeros"

    async def body(self):
        await self._reset()
        await self._drive_and_wait(0, 0)


class AllOnesSeq(AESScenarioBase):
    """``all_ones`` - all-ones key and plaintext."""

    SCENARIO_ID = "all_ones"

    async def body(self):
        await self._reset()
        await self._drive_and_wait(KEY_ALL_ONES, PT_ALL_ONES)


class AlternatingSeq(AESScenarioBase):
    """``alternating`` - 0xAA..AA key with 0x55..55 plaintext."""

    SCENARIO_ID = "alternating"

    async def body(self):
        await self._reset()
        await self._drive_and_wait(KEY_ALTERNATING, PT_ALTERNATING)


class ZeroKeyNonzeroPtSeq(AESScenarioBase):
    """``zero_key_nonzero_pt`` - zero key with a nonzero plaintext."""

    SCENARIO_ID = "zero_key_nonzero_pt"

    async def body(self):
        await self._reset()
        await self._drive_and_wait(0, PT_NIST)


class NonzeroKeyZeroPtSeq(AESScenarioBase):
    """``nonzero_key_zero_pt`` - nonzero key with a zero plaintext."""

    SCENARIO_ID = "nonzero_key_zero_pt"

    async def body(self):
        await self._reset()
        await self._drive_and_wait(KEY_NIST, 0)


class InputChangeWhileBusySeq(AESScenarioBase):
    """``input_change_while_busy`` - stimulus change during encryption.

    Protocol premise (``CONTRACT.md`` section 4): inputs are latched at
    acceptance; changing them mid-operation must not corrupt the in-flight
    transaction.  Exactly one completed transaction is expected.
    """

    SCENARIO_ID = "input_change_while_busy"

    async def body(self):
        await self._reset()
        await self._drive(KEY_NIST, PT_NIST)
        await self._wait_busy()
        # Inputs no longer needed: hold an all-ones/zero change for 5 cycles
        # (the DUT should keep processing the latched input).
        helper = _helper()
        helper.key = KEY_ALL_ONES
        helper.plaintext = 0
        await self._clock_edges(5)
        outs = await self._wait_done()
        self.logger.debug(
            "%s: input change while busy survived - ciphertext=%#034x",
            self.get_name(),
            outs[0],
        )


class RepeatedTransactionsSeq(AESScenarioBase):
    """``repeated_transactions`` - two back-to-back transactions."""

    SCENARIO_ID = "repeated_transactions"

    async def body(self):
        await self._reset()
        await self._drive_and_wait(KEY_NIST, PT_NIST)
        await self._drive_and_wait(KEY_ALL_ONES, 0)


class DonePulseWidthSeq(AESScenarioBase):
    """``done_pulse_width`` - ``done`` pulses for exactly one clock.

    Structural double check: ``_wait_done`` fails if the pulse is wider than
    one clock; the assertion checker ``done_single_pulse`` cross-checks every
    transaction.
    """

    SCENARIO_ID = "done_pulse_width"

    async def body(self):
        await self._reset()
        await self._drive_and_wait(KEY_NIST, PT_NIST)


class ResetDuringIdleSeq(AESScenarioBase):
    """``reset_during_idle`` - reset while the DUT is idle.

    A reset is issued after the bench-level reset/settle, while idle, then
    the DUT is driven normally.  A single completed transaction is expected
    after the extra reset.
    """

    SCENARIO_ID = "reset_during_idle"

    async def body(self):
        await self._reset()
        await self._assert_reset(10)
        await self._deassert_reset(settle=5)
        await self._drive_and_wait(KEY_NIST, PT_NIST)


class ResetMidTransactionSeq(AESScenarioBase):
    """``reset_mid_transaction`` - abort a transaction mid-operation.

    The offer is accepted (``busy`` rises), then ``rst_n`` is pulsed while
    the DUT is in ``ROUND_RUN``.  The in-flight transaction must be dropped:
    after the reset, ``busy==0``, ``done==0`` and ``ciphertext==0``.
    No completed transaction is expected (the monitor counts the dropped
    item; the scoreboard stays at zero transactions).
    """

    SCENARIO_ID = "reset_mid_transaction"

    async def body(self):
        await self._reset()
        await self._drive(KEY_NIST, PT_NIST)
        await self._wait_busy()
        # Wait 5 further cycles so the DUT is well into ROUND_RUN, then cut
        # the transaction short.
        await self._clock_edges(5)
        await self._assert_reset(3)
        helper = _helper()
        await self._clock_edges(3)
        if int(helper.busy) != 0 or int(helper.done) != 0:
            raise AssertionError(
                f"{self.get_name()}: post-reset outputs not idle "
                f"(busy={int(helper.busy)}, done={int(helper.done)})"
            )
        if int(helper.ciphertext) != 0:
            raise AssertionError(
                f"{self.get_name()}: ciphertext not cleared by reset "
                f"(=0x{int(helper.ciphertext):032x})"
            )
        await self._deassert_reset(settle=3)
        if int(helper.busy) != 0 or int(helper.done) != 0:
            raise AssertionError(
                f"{self.get_name()}: DUT not idle after reset release"
            )


# --------------------------------------------------------------------------
# Corner-case sequences (plan "corner cases" section; no SCENARIO_ID)
# --------------------------------------------------------------------------
class CornerSingleBitKeySeq(AESScenarioBase):
    """Corner: single-bit key ``0x01`` with an all-zero plaintext."""

    SCENARIO_ID = None

    async def body(self):
        await self._reset()
        await self._drive_and_wait(0x01, 0)


class CornerFastRetriggerSeq(AESScenarioBase):
    """Corner: new offer the very next cycle after ``done``.

    The driver parks at the ``done`` edge (busy==0) and offers immediately;
    the DUT latches on the following edge - the tightest allowed re-trigger.
    """

    SCENARIO_ID = None

    async def body(self):
        await self._reset()
        await self._drive_and_wait(KEY_NIST, PT_NIST)
        await self._drive_and_wait(KEY_ALL_ONES, 0)


class CornerAllOnesKeyZeroPtSeq(AESScenarioBase):
    """Corner: all-ones key with a zero plaintext."""

    SCENARIO_ID = None

    async def body(self):
        await self._reset()
        await self._drive_and_wait(KEY_ALL_ONES, 0)


class CornerZeroKeyAllOnesPtSeq(AESScenarioBase):
    """Corner: zero key with an all-ones plaintext."""

    SCENARIO_ID = None

    async def body(self):
        await self._reset()
        await self._drive_and_wait(0, PT_ALL_ONES)


class CornerStartIgnoredWhenBusySeq(AESScenarioBase):
    """Corner: ``start`` is ignored while ``busy``.

    After the first offer is in flight, a second ``start=1`` with different
    inputs is driven for a few cycles.  Per the protocol it must be ignored;
    exactly one completed transaction is expected.
    """

    SCENARIO_ID = None

    async def body(self):
        await self._reset()
        await self._drive(KEY_NIST, PT_NIST)
        await self._wait_busy()
        helper = _helper()
        helper.start = 1
        helper.key = KEY_ALL_ONES
        helper.plaintext = 0
        await self._clock_edges(3)
        helper.start = 0
        await self._wait_done()


# --------------------------------------------------------------------------
# Randomized stimulus strategy (plan section "Randomized Testing Strategy")
# --------------------------------------------------------------------------
class AESRandomizedSequence(AESScenarioBase):
    """Randomized stimulus: N random 128-bit pairs with reset injection.

    Per transaction the sequence rolls a die: with probability
    ``in_flight_reset_p`` a reset is injected while the offer is in flight
    (after acceptance, mid-operation); otherwise with probability
    ``idle_reset_p`` a reset is injected between transactions (DUT idle).
    The remaining transactions run clean.  Seed is reported for
    reproducibility.
    """

    SCENARIO_ID = None

    #: Defaults from the plan: 1000 pairs, ~10% idle reset, ~5% in-flight.
    DEFAULT_NUM_TRANSACTIONS = 1000
    DEFAULT_IN_FLIGHT_RESET_P = 0.05
    DEFAULT_IDLE_RESET_P = 0.10

    def __init__(
        self,
        name="aes_randomized_sequence",
        num_transactions=None,
        in_flight_reset_p=None,
        idle_reset_p=None,
        seed=None,
    ):
        super().__init__(name)  # pyuvm uvm_sequence __init__ takes name only
        self.num_transactions = (
            num_transactions
            if num_transactions is not None
            else self.DEFAULT_NUM_TRANSACTIONS
        )
        self.in_flight_reset_p = (
            in_flight_reset_p
            if in_flight_reset_p is not None
            else self.DEFAULT_IN_FLIGHT_RESET_P
        )
        self.idle_reset_p = (
            idle_reset_p
            if idle_reset_p is not None
            else self.DEFAULT_IDLE_RESET_P
        )
        self.seed = seed if seed is not None else int.from_bytes(os.urandom(4), "big")
        self.rng = None
        self.offered = 0
        self.in_flight_resets = 0
        self.idle_resets = 0

    async def body(self):
        self.rng = _random.Random(self.seed)
        self.logger.info(
            "%s: randomized stimulus - seed=%d pairs=%d "
            "(in_flight_p=%.2f idle_p=%.2f)",
            self.get_name(),
            self.seed,
            self.num_transactions,
            self.in_flight_reset_p,
            self.idle_reset_p,
        )
        await self._reset()
        for idx in range(self.num_transactions):
            key = self.rng.getrandbits(128)
            plaintext = self.rng.getrandbits(128)
            await self._drive(key, plaintext, tag=f"tx{idx}")
            roll = self.rng.random()
            if roll < self.in_flight_reset_p:
                await self._inject_reset_in_flight()
                self.in_flight_resets += 1
            elif roll < self.in_flight_reset_p + self.idle_reset_p:
                await self._inject_reset_idle()
                self.idle_resets += 1
            self.offered += 1
        self.logger.info(
            "%s: randomized stimulus complete - offered=%d, "
            "in_flight_resets=%d, idle_resets=%d, seed=%d",
            self.get_name(),
            self.offered,
            self.in_flight_resets,
            self.idle_resets,
            self.seed,
        )

    async def _inject_reset_in_flight(self):
        """Wait for acceptance, then reset mid-operation."""
        try:
            await self._wait_busy()
        except AssertionError:
            raise AssertionError(
                f"{self.get_name()}: in-flight reset requested but the "
                f"offer was never accepted"
            )
        await self._assert_reset(self.rng.randint(2, 5))
        await self._deassert_reset(settle=4)

    async def _inject_reset_idle(self):
        """Wait for the DUT to go idle, then reset between transactions."""
        helper = _helper()
        for _ in range(self.DONE_TIMEOUT_CYCLES):
            await RisingEdge(helper.dut.clk)
            if int(helper.busy) == 0:
                break
        await self._assert_reset(self.rng.randint(2, 5))
        await self._deassert_reset(settle=4)


# --------------------------------------------------------------------------
# Registries + plan cross-checks
# --------------------------------------------------------------------------
DIRECTED_SEQUENCE_CLASSES = (
    NistKatSeq,
    AllZerosSeq,
    AllOnesSeq,
    AlternatingSeq,
    ZeroKeyNonzeroPtSeq,
    NonzeroKeyZeroPtSeq,
    InputChangeWhileBusySeq,
    RepeatedTransactionsSeq,
    DonePulseWidthSeq,
    ResetDuringIdleSeq,
    ResetMidTransactionSeq,
)

CORNER_CASE_SEQUENCE_CLASSES = (
    CornerSingleBitKeySeq,
    CornerFastRetriggerSeq,
    CornerAllOnesKeyZeroPtSeq,
    CornerZeroKeyAllOnesPtSeq,
    CornerStartIgnoredWhenBusySeq,
)


def verify_directed_scenario_ids():
    """Check that the 11 directed classes carry the plan IDs exactly once.

    Called at import time so a drift between the plan and the sequence layer
    fails the test run immediately.
    """
    declared = [cls.SCENARIO_ID for cls in DIRECTED_SEQUENCE_CLASSES]
    missing = [sid for sid in PLAN_DIRECTED_IDS if sid not in declared]
    duplicates = [sid for sid in set(declared) if declared.count(sid) > 1]
    extras = [sid for sid in declared if sid not in PLAN_DIRECTED_IDS]
    problems = []
    if missing:
        problems.append(f"missing plan IDs: {missing}")
    if duplicates:
        problems.append(f"duplicate plan IDs: {duplicates}")
    if extras:
        problems.append(f"IDs not in the plan: {extras}")
    if problems:
        raise RuntimeError(
            "AES sequences vs verification plan mismatch: " + "; ".join(problems)
        )


verify_directed_scenario_ids()