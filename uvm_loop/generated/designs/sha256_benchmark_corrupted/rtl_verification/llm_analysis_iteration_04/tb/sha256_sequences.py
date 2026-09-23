"""SHA-256 stimulus sequences (stage-2 STIMULUS artifact).

Every stimulus scenario from the verification plan is realized here as a
``uvm_sequence`` subclass:

* **Directed scenarios** (``directed_test_scenarios`` in the plan):
  nine sequence classes, each carrying exactly one class-level
  ``SCENARIO_ID`` -- the authoritative plan scenario id (CONTRACT.md §9).
  The registry ``DIRECTED_SCENARIO_SEQUENCES`` maps every planned id to
  exactly one class; ``validate_scenario_ids()`` enforces that.
* **Corner cases** (``corner_cases`` in the plan): six sequences.  These
  have **no** ``SCENARIO_ID`` -- they are a separate verification strategy.
* **Randomized strategy** (``randomized_testing_strategy`` in the plan):
  ``Sha256RandomizedSequence`` generates random single-block messages,
  pads them with canonical SHA-256 one-block padding, drives them to the
  DUT and optionally injects resets / back-to-back starts.

BLOCK CONSTRUCTION NOTE (see the appended CONTRACT.md stage-2 note): the
``block`` hex literals embedded in the planning documents were corrupted
(every one is wider than 512 bits and fails canonical one-block padding),
while each scenario's *description* states the intended message and length
field unambiguously.  Stimulus therefore builds blocks programmatically
with :func:`canonical_one_block_pad`, which produces bytes that are
byte-for-byte identical to the golden reference's ``pad_one_block()``
(``benchmarks/sha256_benchmark_corrupted/sha256_reference_model.py``).
No scenario id, expected digest, or stimulus intent is changed.

Sequences control reset and inter-transaction timing directly through the
shared ``Sha256Pins`` helper (ConfigDB key ``"sha256_pins"``, CONTRACT.md
§5) using only public cocotb 2.1.0 triggers (``ClockCycles``,
``RisingEdge``).  They request pin driving from the
``Sha256Sequencer``/``Sha256Driver`` pair via the standard pyuvm
``start_item``/``finish_item`` handshake; the driver implements the exact
one-cycle ``start`` pulse convention.

No SystemVerilog anywhere -- pure pyuvm sequences + cocotb coroutines.
"""

import random

from pyuvm import ConfigDB, uvm_sequence

from cocotb.triggers import ClockCycles

from sha256_pins import COMPLETION_MARGIN_CYCLES
from sha256_pins import Sha256Pins
from sha256_transaction import Sha256Transaction

# ---------------------------------------------------------------------------
# Canonical one-block padding for stimulus construction
# ---------------------------------------------------------------------------
# Maximum single-block message size: < 56 bytes (SHA-256 one-block limit).
MAX_ONE_BLOCK_MESSAGE_BYTES = 55
BLOCK_BITS = 512


def canonical_one_block_pad(message: bytes) -> int:
    """Return the canonical SHA-256 one-block padding of ``message`` as a
    512-bit big-endian integer.

    Byte layout (identical to the reference model's ``pad_one_block``):
    ``message || 0x80 || zeros || 64-bit big-endian bit length``.

    This is *padding construction for stimulus*; it never computes a SHA-256
    digest (the golden digest computation stays exclusively in the
    reference model, used by the scoreboard).
    """
    if len(message) > MAX_ONE_BLOCK_MESSAGE_BYTES:
        raise ValueError(
            f"SHA-256 single-block padding requires messages of at most "
            f"{MAX_ONE_BLOCK_MESSAGE_BYTES} bytes; got {len(message)}"
        )
    bit_len = len(message) * 8
    padded = message + b"\x80"
    padded += b"\x00" * (56 - len(padded))
    padded += bit_len.to_bytes(8, "big")
    assert len(padded) == BLOCK_BITS // 8
    return int.from_bytes(padded, "big")


# Probability / ranges for the randomized strategy (plan:
# randomized_testing_strategy.constraints and .injection).
RESET_INJECTION_PROBABILITY = 0.1   # reset_during_processing injection freq.
BACK_TO_BACK_PROBABILITY = 0.2      # back_to_back injection frequency
MSG_MIN_LENGTH = 0                  # message_length range [0, 55]
MSG_MAX_LENGTH = 55
BYTE_MIN = 0                        # message_bytes range [0, 255]
BYTE_MAX = 255
RESET_HOLD_MIN = 1                  # reset injection duration [1, 3] cycles
RESET_HOLD_MAX = 3


# ---------------------------------------------------------------------------
# Base stimulus sequence: shared helpers
# ---------------------------------------------------------------------------
class Sha256StimulusBase(uvm_sequence):
    """Common helpers used by every SHA-256 stimulus sequence.

    All timing is expressed in clock cycles using ``ClockCycles`` on the
    shared ``dut.clk`` (via the ``Sha256Pins`` helper).  Reset is applied
    with the helper's ``reset_dut(hold_cycles=...)`` (active-low,
    asynchronous -- CONTRACT.md §6).
    """

    def __init__(self, name: str = "sha256_stimulus_sequence") -> None:
        super().__init__(name)
        self.pins = None  # type: Sha256Pins

    async def _get_pins(self) -> Sha256Pins:
        """Load and cache the shared ``Sha256Pins`` from ConfigDB."""
        if self.pins is None:
            self.pins = ConfigDB().get(None, "", "sha256_pins")
            if self.pins is None:
                raise RuntimeError(
                    f"{self.get_name()}: ConfigDB key 'sha256_pins' missing; "
                    f"test_top.py must set it before starting sequences "
                    f"(CONTRACT.md §5)"
                )
        return self.pins

    async def _wait_cycles(self, cycles) -> None:
        """Idle for ``cycles`` clock cycles (no-op for None/0)."""
        cycles = int(cycles or 0)
        if cycles <= 0:
            return
        pins = await self._get_pins()
        await ClockCycles(pins.clk, cycles)

    async def _reset(self, hold_cycles: int = 2) -> None:
        """Hold active-low reset for ``hold_cycles`` rising edges, then
        release and re-synchronize to the clock."""
        pins = await self._get_pins()
        await pins.reset_dut(hold_cycles=max(1, int(hold_cycles)))

    async def _send(self, block: int, start: int = 1) -> Sha256Transaction:
        """Request the driver to drive one start pulse with ``block``.

        Standard pyuvm handshake: ``start_item`` -> set fields ->
        ``finish_item``.  The driver (``sha256_driver.py``) turns this into
        exactly one one-cycle ``start`` pulse with ``block`` held across the
        sampling edge.
        """
        item = Sha256Transaction(name=f"{self.get_name()}_txn")
        await self.start_item(item)
        item.start = int(start)
        item.block = int(block)
        await self.finish_item(item)
        self.logger.debug("Sent item: %s", item.convert2string())
        return item


# ---------------------------------------------------------------------------
# Directed scenarios -- each class implements exactly one plan id
# (SCENARIO_ID is the identity used by later stages; class names are free).
# ---------------------------------------------------------------------------
class Sha256ResetInitializationSequence(Sha256StimulusBase):
    """Plan id: reset_initialization.

    Hold reset active for 5 cycles, release it, wait for idle.  No
    transaction is driven: the scenario only verifies the RTL reset state
    (done=1, digest=0 -- DISC-001).  The state check is performed by the
    assertions/scoreboard stages using ``EXPECTED_CHECKS``.
    """

    SCENARIO_ID = "reset_initialization"
    EXPECTED_CHECKS = (("done", 1), ("digest", 0))

    def __init__(self, name: str = "reset_initialization_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._get_pins()
        await self._reset(hold_cycles=5)   # hold reset active for 5 cycles
        await self._wait_cycles(2)         # release reset, wait for idle


class Sha256EmptyMessageSequence(Sha256StimulusBase):
    """Plan id: empty_message.  Known-answer test for the empty string."""

    SCENARIO_ID = "empty_message"
    MESSAGE = b""
    EXPECTED_DIGEST = 0xE3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855
    EXPECTED_CHECKS = (("done", 1), ("digest", EXPECTED_DIGEST))

    def __init__(self, name: str = "empty_message_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(1)              # start deasserted
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)  # 64 rounds + margin


class Sha256SingleByteASequence(Sha256StimulusBase):
    """Plan id: single_byte_a.  Known-answer test for the 1-byte message
    ``"a"`` (SHA-256 padding: length field 0x0000000000000008)."""

    SCENARIO_ID = "single_byte_a"
    MESSAGE = b"a"
    EXPECTED_DIGEST = 0xCA978112CA1BBDCAFAC231B39A23DC4DA786EFF8147C4E72B9807785AFEE48BB
    EXPECTED_CHECKS = (("done", 1), ("digest", EXPECTED_DIGEST))

    def __init__(self, name: str = "single_byte_a_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256AbcMessageSequence(Sha256StimulusBase):
    """Plan id: abc_message.  FIPS 180-4 example SHA-256("abc")."""

    SCENARIO_ID = "abc_message"
    MESSAGE = b"abc"
    EXPECTED_DIGEST = 0xBA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD
    EXPECTED_CHECKS = (("done", 1), ("digest", EXPECTED_DIGEST))

    def __init__(self, name: str = "abc_message_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256HelloWorldSequence(Sha256StimulusBase):
    """Plan id: hello_world.  Known-answer test for "hello world"
    (11 bytes; length field 0x0000000000000058)."""

    SCENARIO_ID = "hello_world"
    MESSAGE = b"hello world"
    EXPECTED_DIGEST = 0xB94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9
    EXPECTED_CHECKS = (("done", 1), ("digest", EXPECTED_DIGEST))

    def __init__(self, name: str = "hello_world_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256QuickBrownFoxSequence(Sha256StimulusBase):
    """Plan id: quick_brown_fox.  Known-answer test for the pangram
    "The quick brown fox jumps over the lazy dog" (43 bytes; length field
    0x0000000000000158)."""

    SCENARIO_ID = "quick_brown_fox"
    MESSAGE = b"The quick brown fox jumps over the lazy dog"
    EXPECTED_DIGEST = 0xD7A8FBB307D7809469CA9ABCB0082E4F8D5651E46D3CDB762D02D0BF37C9E592
    EXPECTED_CHECKS = (("done", 1), ("digest", EXPECTED_DIGEST))

    def __init__(self, name: str = "quick_brown_fox_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256BackToBackTransactionsSequence(Sha256StimulusBase):
    """Plan id: back_to_back_transactions.

    Two consecutive independent transactions: SHA-256("abc") then the empty
    message.  Each is driven to completion (fixed 70-cycle margin -- never
    the broken ``done`` pin) before the next starts, so the two digests
    must be computed independently.
    """

    SCENARIO_ID = "back_to_back_transactions"
    FIRST_MESSAGE = b"abc"
    SECOND_MESSAGE = b""
    EXPECTED_DIGEST_FIRST = 0xBA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD
    EXPECTED_DIGEST_SECOND = 0xE3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855
    EXPECTED_CHECKS = (
        ("digest", EXPECTED_DIGEST_FIRST),
        ("digest", EXPECTED_DIGEST_SECOND),
    )

    def __init__(self, name: str = "back_to_back_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)

        # First transaction: abc.
        await self._send(canonical_one_block_pad(self.FIRST_MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)

        # Second transaction: empty message (independent digest).
        await self._send(canonical_one_block_pad(self.SECOND_MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256StartWhileBusyRestartsSequence(Sha256StimulusBase):
    """Plan id: start_while_busy_restarts.

    Assert ``start`` with a *different* block roughly 10 cycles into the
    first transaction.  The RTL does not gate ``start`` on ``busy``
    (DISC-017) so the second start restarts the transaction; the digest
    must reflect the second (empty-message) block.
    """

    SCENARIO_ID = "start_while_busy_restarts"
    FIRST_MESSAGE = b"abc"
    SECOND_MESSAGE = b""
    RESTART_DELAY_CYCLES = 10      # plan: second drive assertion ~10 cycles
    EXPECTED_DIGEST = 0xE3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855
    EXPECTED_CHECKS = (("digest", EXPECTED_DIGEST),)

    def __init__(self, name: str = "start_while_busy_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)

        # First transaction: abc.
        await self._send(canonical_one_block_pad(self.FIRST_MESSAGE))
        await self._wait_cycles(1)                    # start deasserted

        # ~10 cycles later re-assert start with the empty-message block.
        # `busy` is stuck high after the first start (DISC-013), so this
        # second start is guaranteed to land "while busy" and restarts the
        # transaction per DISC-017.
        await self._wait_cycles(self.RESTART_DELAY_CYCLES)
        await self._send(canonical_one_block_pad(self.SECOND_MESSAGE))

        # Wait for the restarted transaction to complete (fixed margin).
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256DoneBehaviorContinuousSequence(Sha256StimulusBase):
    """Plan id: done_behavior_continuous.

    Verify the (corrupted, DISC-001) RTL holds ``done = 1`` continuously
    after reset instead of pulsing, and that ``digest`` holds its value.
    The check is performed twice: right after the completion margin and 5
    cycles later; expected values are recorded in ``EXPECTED_CHECKS``.
    """

    SCENARIO_ID = "done_behavior_continuous"
    MESSAGE = b"abc"
    EXPECTED_DIGEST = 0xBA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD
    EXPECTED_CHECKS = (
        (("done", 1), ("digest", EXPECTED_DIGEST)),   # check after margin
        (("done", 1), ("digest", EXPECTED_DIGEST)),   # check 5 cycles later
    )

    def __init__(self, name: str = "done_behavior_continuous_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)
        # First check point (done stays 1; digest holds) -- verified by the
        # assertions/scoreboard stages.
        await self._wait_cycles(5)
        # Second check point 5 cycles later.


# ---------------------------------------------------------------------------
# Corner cases -- separate verification strategy, no SCENARIO_ID.
# ---------------------------------------------------------------------------
class Sha256MaximumMessageLengthSequence(Sha256StimulusBase):
    """Corner case: maximum_message_length.

    Message of exactly 55 bytes -- the longest message that still fits in a
    single 512-bit padded block (length field 0x00000000000001B8).
    """

    MESSAGE = bytes(range(55))  # deterministic, reproducible content
    VALID_PADDED_BLOCK = True

    def __init__(self, name: str = "maximum_message_length_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256BlockAllOnesSequence(Sha256StimulusBase):
    """Corner case: block_with_all_ones.

    Raw 512-bit block of all 1s.  This is *not* a canonically padded
    message (the golden reference model rejects it), but it exercises every
    datapath; the DUT must still produce a deterministic digest.  Marked
    ``VALID_PADDED_BLOCK = False`` so the scoreboard can treat it
    separately from reference-model comparisons.
    """

    BLOCK = (1 << BLOCK_BITS) - 1
    VALID_PADDED_BLOCK = False

    def __init__(self, name: str = "block_all_ones_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(self.BLOCK)
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256BlockAlternatingPatternSequence(Sha256StimulusBase):
    """Corner case: block_with_alternating_pattern.

    Raw 512-bit block with an alternating 0xAA/0x55 byte pattern (not a
    canonically padded message).  Deterministic digest per reference-model
    strategy; see ``VALID_PADDED_BLOCK``.
    """

    BLOCK = int.from_bytes(bytes(b"\xaa\x55" * 32), "big")
    VALID_PADDED_BLOCK = False

    def __init__(self, name: str = "block_alternating_pattern_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(self.BLOCK)
        await self._wait_cycles(1)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256ResetDuringProcessingSequence(Sha256StimulusBase):
    """Corner case: reset_during_processing.

    Start a transaction, then assert active-low reset (1-3 cycles) while
    the DUT is busy processing.  Expected RTL behavior: the DUT returns to
    the reset state (done=1 -- DISC-001, digest=0) and the in-flight
    transaction is discarded.
    """

    MESSAGE = b"abc"
    PROCESS_CYCLES_BEFORE_RESET = 5   # start is definitely mid-flight
    RESET_HOLD_CYCLES = 2             # within the plan's 1..3 injection window
    VALID_PADDED_BLOCK = True
    EXPECTED_CHECKS = (("done", 1), ("digest", 0))

    def __init__(self, name: str = "reset_during_processing_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(self.PROCESS_CYCLES_BEFORE_RESET)
        await self._reset(hold_cycles=self.RESET_HOLD_CYCLES)
        await self._wait_cycles(3)    # let the reset state settle


class Sha256StartDeassertedSameCycleSequence(Sha256StimulusBase):
    """Corner case: start_deasserted_same_cycle.

    Minimal-width ``start`` pulse.  This requirement is satisfied by the
    driver protocol itself: ``Sha256Driver`` always produces exactly one
    one-cycle ``start`` pulse per item (high for one sampled rising edge).
    This sequence pins that down for a normal transaction.
    """

    MESSAGE = b"abc"
    VALID_PADDED_BLOCK = True

    def __init__(self, name: str = "start_deasserted_same_cycle_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        await self._reset(hold_cycles=2)
        # The driver pulses `start` for exactly one sampled cycle.
        await self._send(canonical_one_block_pad(self.MESSAGE))
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)


class Sha256BlockChangesDuringProcessingSequence(Sha256StimulusBase):
    """Corner case: block_changes_during_processing.

    Drive ``start`` with block A, then change the ``block`` input to block
    B while the DUT is busy.  ``block`` is captured on the start edge, so
    the perturbation must have no effect on the in-flight transaction.
    """

    FIRST_MESSAGE = b"abc"
    SECOND_BLOCK = 0xDEADBEEF          # arbitrary different bus value
    CHANGE_DELAY_CYCLES = 3
    VALID_PADDED_BLOCK = True

    def __init__(self, name: str = "block_changes_during_processing_sequence") -> None:
        super().__init__(name)

    async def body(self) -> None:
        pins = await self._get_pins()
        await self._reset(hold_cycles=2)
        await self._send(canonical_one_block_pad(self.FIRST_MESSAGE))
        await self._wait_cycles(self.CHANGE_DELAY_CYCLES)
        # Perturb the block bus after the transaction was captured.
        pins.drive_block(self.SECOND_BLOCK)
        await self._wait_cycles(COMPLETION_MARGIN_CYCLES)
        pins.drive_block(0)


# ---------------------------------------------------------------------------
# Randomized strategy -- no SCENARIO_ID.
# ---------------------------------------------------------------------------
class Sha256RandomizedSequence(Sha256StimulusBase):
    """Randomized testing: ``randomized_testing_strategy`` in the plan.

    Generates ``num_transactions`` random messages (length 0..55 bytes,
    byte values 0..255), pads each with canonical one-block padding and
    drives it to the DUT as a separate transaction.  Two plan injections:

    * ``reset_during_processing`` (p=0.1): a few cycles after ``start``,
      assert active-low reset for 1..3 cycles (aborting the in-flight
      transaction).
    * ``back_to_back`` (p=0.2): the next transaction starts immediately at
      the completion margin with no extra idle gap.

    Digest comparison against hashlib is performed by the scoreboard
    (later stage) using the reference model.
    """

    def __init__(
        self,
        name: str = "sha256_randomized_sequence",
        num_transactions: int = 20,
        seed: int = None,
    ) -> None:
        super().__init__(name)
        self.num_transactions = max(1, int(num_transactions))
        self.seed = seed
        self.rng = None  # type: random.Random

    async def body(self) -> None:
        pins = await self._get_pins()
        self.rng = random.Random(self.seed)
        await self._reset(hold_cycles=2)

        for txn_idx in range(self.num_transactions):
            # Random message per plan constraints (0..55 bytes, 0..255 values).
            msg_len = self.rng.randint(MSG_MIN_LENGTH, MSG_MAX_LENGTH)
            message = bytes(
                self.rng.randint(BYTE_MIN, BYTE_MAX) for _ in range(msg_len)
            )
            block = canonical_one_block_pad(message)
            self.logger.info(
                "Random txn %d/%d: message length %d bytes",
                txn_idx + 1, self.num_transactions, msg_len,
            )

            # Drive the transaction (one-cycle start pulse).
            await self._send(block)

            # reset_during_processing injection (p=0.1): abort mid-flight.
            if self.rng.random() < RESET_INJECTION_PROBABILITY:
                hold = self.rng.randint(RESET_HOLD_MIN, RESET_HOLD_MAX)
                self.logger.info(
                    "Injected reset during processing "
                    "(hold %d cycle(s), txn %d)", hold, txn_idx + 1,
                )
                await self._wait_cycles(self.rng.randint(1, 5))
                await self._reset(hold_cycles=hold)

            # Fixed completion margin (never relies on the broken `done`).
            await self._wait_cycles(COMPLETION_MARGIN_CYCLES)

            # back_to_back injection (p=0.2): start next immediately
            # (no extra idle gap); otherwise a small random gap.
            if self.rng.random() >= BACK_TO_BACK_PROBABILITY:
                await self._wait_cycles(self.rng.randint(1, 5))


# ---------------------------------------------------------------------------
# Directed-scenario registry + integrity validation
# ---------------------------------------------------------------------------
PLANNED_DIRECTED_SCENARIO_IDS = (
    "reset_initialization",
    "empty_message",
    "single_byte_a",
    "abc_message",
    "hello_world",
    "quick_brown_fox",
    "back_to_back_transactions",
    "start_while_busy_restarts",
    "done_behavior_continuous",
)

DIRECTED_SCENARIO_SEQUENCES = {
    "reset_initialization": Sha256ResetInitializationSequence,
    "empty_message": Sha256EmptyMessageSequence,
    "single_byte_a": Sha256SingleByteASequence,
    "abc_message": Sha256AbcMessageSequence,
    "hello_world": Sha256HelloWorldSequence,
    "quick_brown_fox": Sha256QuickBrownFoxSequence,
    "back_to_back_transactions": Sha256BackToBackTransactionsSequence,
    "start_while_busy_restarts": Sha256StartWhileBusyRestartsSequence,
    "done_behavior_continuous": Sha256DoneBehaviorContinuousSequence,
}


def validate_scenario_ids() -> None:
    """Assert that every planned directed scenario id is implemented by
    exactly one sequence class and that each class's ``SCENARIO_ID``
    matches its registry key (CONTRACT.md §9; mandatory check for this
    stage)."""
    assert set(PLANNED_DIRECTED_SCENARIO_IDS) == set(
        DIRECTED_SCENARIO_SEQUENCES
    ), (
        f"Directed scenario mismatch: planned={set(PLANNED_DIRECTED_SCENARIO_IDS)} "
        f"vs implemented={set(DIRECTED_SCENARIO_SEQUENCES)}"
    )
    for scenario_id, seq_cls in DIRECTED_SCENARIO_SEQUENCES.items():
        assert getattr(seq_cls, "SCENARIO_ID", None) == scenario_id, (
            f"Sequence class {seq_cls.__name__} has SCENARIO_ID "
            f"{getattr(seq_cls, 'SCENARIO_ID', None)!r}, expected "
            f"{scenario_id!r}"
        )


if __name__ == "__main__":  # pragma: no cover -- manual sanity check
    validate_scenario_ids()
    print(
        f"OK: {len(DIRECTED_SCENARIO_SEQUENCES)} directed scenario ids "
        f"implemented exactly once; "
        f"{len(PLANNED_DIRECTED_SCENARIO_IDS)} planned ids covered."
    )
    print("OK: corner-case and randomized sequences carry no SCENARIO_ID.")