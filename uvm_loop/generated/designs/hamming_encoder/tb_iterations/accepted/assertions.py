"""hamming_encoder always-on assertions in Python (replaces SVA) + watchdog.

This module implements the ``useful_assertions`` section of the verification
plan for the ``hamming_encoder`` DUT
(``benchmarks/hamming_encoder/hamming_encoder.sv``) as plain Python checker
coroutines.  There is no SystemVerilog: no covergroup, no SVA, no
``interface``.  Every check is an ``assert`` statement inside a coroutine
launched with ``cocotb.start_soon``.  When a check does not hold, the
``AssertionError`` propagates out of the task and fails the cocotb test
immediately.

== DUT timing model (CONTRACT.md sections 2-3, 8) ==

The DUT is *purely combinational*: it has exactly two pins (``data_in``,
``code_out``) and **no** ``clk`` / reset port.  The testbench reference clock
is virtual: one reference cycle is one ``Timer(clkrs.clock_period_ns)`` wait
(``wait_clock_cycles``), and its expiry is where stimulus is applied and
(after the combinational settle) outputs are sampled.  These checkers must
therefore **never** reference ``dut.clk`` / ``dut.tb_reset`` / ``RisingEdge``;
they pace themselves exclusively with ``wait_clock_cycles``.

== Sampling cadence ==

Each checker loop calls ``_settled_sample()``: wait one reference cycle, then
a small settle offset (a tenth of the period, ``NOT`` ``Timer(0)``) before
reading the pins.  The offset deterministically places every read in a
timestep strictly *after* the boundary at which the driver writes ``data_in``
(and after the combinational deltas have settled), so the sampled
``(data_in, code_out)`` pair is always a consistent settle pair — never a
same-timestep transient mix.  Until the first drive the pins carry X/Z and
``pins_driven()`` is False, so the window is skipped.  Because ``data_in``
holds each driven word for the full two-cycle per-item cadence, every driven
pair is observed at least once (some twice), which is harmless for an
always-true invariant.

== Assertion -> plan-item mapping (plan ``useful_assertions``) ==

    check_data_width_positive          data_width_positive
    check_output_matches_reference_model output_matches_reference_model
    check_secded_overall_even_parity   secded_overall_even_parity
    check_data_bits_preserved_in_codeword data_bits_preserved_in_codeword
    check_parity_cover_set_definition  parity_cover_set_definition

``check_data_width_positive`` is a one-shot assertion (per elaboration, it
fails at build time if DATA_WIDTH is not > 0; the reference model raises
``ValueError`` for non-positive widths and the RTL issues ``$fatal``).
``check_secded_overall_even_parity`` is vacuous (concise True) when the
elaboration is non-SECDED and is skipped.

The structural helpers (:func:`deinterleave`, :func:`_ham_vector`) are pure
functions of ``code_out`` + ``HammingConf`` and implement the spec section 3
bit mapping independently of the reference model's arithmetic, so the
placement/parity-structure checks do not share code with the oracle used by
``check_output_matches_reference_model`` and the scoreboard.

Watchdog:

    :class:`HammingWatchdog` / :func:`start_watchdog` implement the required
    bounded-run guard: if the ``done`` signal (a ``cocotb.triggers.Event``)
    has not been set within a bounded number of virtual reference cycles, the
    watchdog raises ``AssertionError`` and fails the test, so a hung test
    cannot silently exhaust the whole simulation run.
"""

import logging

import cocotb
from cocotb.triggers import Event, Timer

from pyuvm import ConfigDB

from tb.dut_helper import (
    KEY_CLK_RST,
    KEY_CONF,
    KEY_DUT_PINS,
    wait_clock_cycles,
)

# Authoritative Python reference model (CONTRACT.md section 7).  A
# byte-for-byte copy lives at tb/ref_model.py beside the other TB modules;
# import it from the copy first and fall back only for alternate run
# layouts (same chain as tb/scoreboard.py).  The model is the single
# arithmetic/behavior oracle used by check_output_matches_reference_model.
try:  # pragma: no cover - import-path selection
    from tb.ref_model import HammingParams, hamming_encode
except ImportError:  # pragma: no cover - import-path selection
    try:
        from benchmarks.hamming_encoder.ref_model import (  # type: ignore
            HammingParams,
            hamming_encode,
        )
    except ImportError:  # pragma: no cover - import-path selection
        try:
            from hamming_encoder.ref_model import (  # type: ignore
                HammingParams,
                hamming_encode,
            )
        except ImportError:  # pragma: no cover - import-path selection
            from ref_model import HammingParams, hamming_encode  # type: ignore

log = logging.getLogger("hamming_encoder.assertions")


# ── pure structural helpers (spec section 3) ──────────────────────────────

def _popcount(n):
    """Hamming weight of non-negative integer *n*."""
    return bin(n).count("1")


def _is_power_of_two(n):
    """True when *n* is a positive power of two."""
    return n != 0 and (n & (n - 1)) == 0


def deinterleave(code_out, conf):
    """Extract the data bits from the non-power-of-two positions of the
    codeword, reproducing ``data_in`` (spec section 3 step 1).

    Non-SECDED: Hamming position ``pos`` maps to code bit ``pos-1``.
    SECDED: position ``pos`` maps to code bit ``pos`` (bit 0 is the overall
    parity).  Data bits occupy positions 1..base_width that are not exact
    powers of two, consumed in order from ``data_in`` bit 0 upward.
    """
    base_width = conf.base_width
    offset = 1 if conf.secded else 0
    extracted = 0
    data_idx = 0
    for pos in range(1, base_width + 1):
        if _is_power_of_two(pos):
            continue
        bit = (code_out >> (pos - 1 + offset)) & 1
        extracted |= bit << data_idx
        data_idx += 1
    return extracted


def _ham_vector(code_out, conf):
    """Extract the 1-indexed Hamming-position bit vector from *code_out*.

    Returns a list ``ham`` with ``len == conf.base_width + 1`` where
    ``ham[pos]`` (1 <= pos <= base_width) is the bit at Hamming position
    ``pos`` (spec section 3 step 2; position ``pos`` maps to code bit
    ``pos-1`` non-SECDED or ``pos`` SECDED).  ``ham[0]`` is unused padding.
    """
    n = conf.base_width
    offset = 1 if conf.secded else 0
    ham = [0] * (n + 1)
    for pos in range(1, n + 1):
        ham[pos] = (code_out >> (pos - 1 + offset)) & 1
    return ham


# ── assertion checker bundle ──────────────────────────────────────────────

class HammingAssertions:
    """Bundle of always-running hamming_encoder assertion checker coroutines.

    Instantiate with the ConfigDB-shared pin helper, clock/reset descriptor
    and geometry (resolved by :func:`start_assertions` unless given) and call
    :meth:`start` to launch every checker with ``cocotb.start_soon``.  Any
    checker failure raises ``AssertionError`` and fails the test.
    """

    def __init__(self, pins, clkrs, conf, logger=None):
        self.pins = pins
        self.clkrs = clkrs
        self.conf = conf
        self.logger = logger if logger is not None else log
        self.tasks = []   # cocotb Tasks of the spawned checkers
        # Settle-offset: a strict fraction of the virtual clock period that
        # places every pin read AFTER the boundary drive and its
        # combinational deltas (never Timer(0)).  max(1, ...) guards
        # sub-nanosecond periods.
        self._settle_offset_ns = max(
            1, int(self.clkrs.clock_period_ns / 10.0)
        ) if self.clkrs is not None else 1

    # -- lifecycle -----------------------------------------------------

    def start(self):
        """Launch all checker coroutines with ``cocotb.start_soon``.

        Returns the list of cocotb Tasks (one per plan assertion) for
        callers that want to join/cancel them.
        """
        if self.tasks:  # idempotent: do not double-spawn on re-entry
            return self.tasks
        checkers = [
            self.check_data_width_positive,
            self.check_output_matches_reference_model,
            self.check_secded_overall_even_parity,
            self.check_data_bits_preserved_in_codeword,
            self.check_parity_cover_set_definition,
        ]
        self.tasks = [cocotb.start_soon(fn()) for fn in checkers]
        self.logger.info(
            "HammingAssertions started: %d checker coroutine(s)",
            len(self.tasks),
        )
        return self.tasks

    # -- sampling helper ------------------------------------------------

    async def _settled_sample(self):
        """Wait one virtual reference cycle plus a settle offset and return
        the settled ``(data_in, code_out)`` pair, or ``None`` when the DUT
        pins are not yet driven (pre-first-drive / tb_reset window).

        The strict samplers reject X/Z pins outright, so an undriven pin can
        never be silently coerced to 0 and false-pass a zero-data oracle.
        """
        await wait_clock_cycles(self.clkrs, 1)
        await Timer(self._settle_offset_ns, units="ns")
        if not self.pins.pins_driven():
            return None
        data_in = self.pins.sample_data_in_strict(
            data_width=self.conf.data_width)
        code_out = self.pins.sample_code_out_strict(
            code_width=self.conf.code_width)
        return data_in, code_out

    # -- checkers -------------------------------------------------------

    async def check_data_width_positive(self):
        """data_width_positive (severity error, one-shot per elaboration).

        DATA_WIDTH must be greater than zero at elaboration.  The RTL issues
        ``$fatal`` and the reference model raises ``ValueError`` for
        non-positive widths; this checker mirrors that guard in the
        generated testbench.  Completed immediately after the assertion.
        """
        assert self.conf.data_width > 0, (
            f"data_width_positive violated: DATA_WIDTH={self.conf.data_width} "
            f"(must be > 0)"
        )
        self.logger.info(
            "HammingAssertions: data_width_positive holds "
            "(DATA_WIDTH=%d)", self.conf.data_width,
        )

    async def check_output_matches_reference_model(self):
        """output_matches_reference_model (severity error, every drive).

        After each data_in drive and combinational settle, ``code_out`` must
        equal ``hamming_encode(data_in, DATA_WIDTH, SECDED)`` bit-for-bit.
        Primary DUT-versus-oracle check; a failure indicates a DUT defect and
        must not cause the reference model to be adapted.
        """
        cycle = 0
        while True:
            sample = await self._settled_sample()
            if sample is None:
                cycle += 1
                continue
            data_in, code_out = sample
            expected, params = hamming_encode(
                data_in, self.conf.data_width, bool(self.conf.secded),
            )
            # Reference geometry must agree with the active elaboration
            # (ConfigDB HammingConf) — a mismatch is an environment/setup
            # bug that must fail loudly instead of scoring with the wrong
            # width (mirrors the scoreboard's geometry cross-check).
            assert isinstance(params, HammingParams) and (
                params.data_width == self.conf.data_width
                and bool(params.secded) == bool(self.conf.secded)
                and params.code_width == self.conf.code_width
                and params.parity_bits == self.conf.parity_bits
                and params.base_width == self.conf.base_width
            ), (
                f"output_matches_reference_model: reference-model geometry "
                f"{params} disagrees with active elaboration {self.conf}"
            )
            # Both sides are exactly code_width bits; the mask keeps the
            # comparison robust to any width drift.
            mask = (1 << params.code_width) - 1
            assert (expected & mask) == (code_out & mask), (
                f"output_matches_reference_model violated at settle "
                f"#{cycle}: data_in={data_in:#x} (DATA_WIDTH="
                f"{self.conf.data_width}, SECDED={self.conf.secded}) has "
                f"code_out={code_out:#x}, expected "
                f"{expected & mask:#x} per hamming_encode"
            )
            cycle += 1

    async def check_secded_overall_even_parity(self):
        """secded_overall_even_parity (severity error).

        With SECDED=1 the full CODE_WIDTH codeword has even parity
        (XOR-reduction equals 0), validating the overall-parity placement at
        ``code_out[0]`` independently of the exact codeword value.  Vacuously
        True and therefore skipped when the elaboration is non-SECDED.
        """
        if not (self.conf.secded == 1):
            self.logger.info(
                "HammingAssertions: secded_overall_even_parity not "
                "applicable (SECDED=0); skipping"
            )
            return
        cycle = 0
        while True:
            sample = await self._settled_sample()
            if sample is None:
                cycle += 1
                continue
            _data_in, code_out = sample
            assert _popcount(code_out) % 2 == 0, (
                f"secded_overall_even_parity violated at settle "
                f"#{cycle}: code_out={code_out:#x} has odd weight "
                f"({_popcount(code_out)}) but SECDED=1 requires even parity"
            )
            cycle += 1

    async def check_data_bits_preserved_in_codeword(self):
        """data_bits_preserved_in_codeword (severity error).

        Deinterleaving the non-power-of-two positions of the base codeword
        from ``code_out`` must reproduce ``data_in`` exactly — independent
        of the parity-bit computation (spec section 3 step 1).
        """
        cycle = 0
        while True:
            sample = await self._settled_sample()
            if sample is None:
                cycle += 1
                continue
            data_in, code_out = sample
            extracted = deinterleave(code_out, self.conf)
            assert extracted == data_in, (
                f"data_bits_preserved_in_codeword violated at settle "
                f"#{cycle}: data_in={data_in:#x} but deinterleaving "
                f"code_out={code_out:#x} "
                f"(DATA_WIDTH={self.conf.data_width}, "
                f"SECDED={self.conf.secded}) gives {extracted:#x}"
            )
            cycle += 1

    async def check_parity_cover_set_definition(self):
        """parity_cover_set_definition (severity error).

        Each parity bit at position ``2**p`` equals the XOR of every position
        ``pos`` (excluding ``2**p`` itself) for which ``(pos & 2**p) != 0`` —
        the structural covering-set definition of spec section 3 step 4,
        verified on the deinterleaved codeword.
        """
        cycle = 0
        while True:
            sample = await self._settled_sample()
            if sample is None:
                cycle += 1
                continue
            _data_in, code_out = sample
            ham = _ham_vector(code_out, self.conf)
            n = self.conf.base_width
            for p in range(self.conf.parity_bits):
                parity_pos = 1 << p
                cover = 0
                for pos in range(1, n + 1):
                    if pos != parity_pos and (pos & parity_pos):
                        cover ^= ham[pos]
                assert ham[parity_pos] == cover, (
                    f"parity_cover_set_definition violated at settle "
                    f"#{cycle}: parity bit at position {parity_pos} of "
                    f"code_out={code_out:#x} is {ham[parity_pos]} but the "
                    f"XOR of its cover set "
                    f"({{pos: 1<=pos<={n}, pos!={parity_pos}, "
                    f"(pos & {parity_pos})!=0}}) is {cover}"
                )
            cycle += 1


# ── standalone launcher ───────────────────────────────────────────────────

def start_assertions(pins=None, clkrs=None, conf=None, logger=None):
    """Resolve the shared DUT config and start every assertion checker.

    ``pins``/``clkrs``/``conf`` default to the shared ConfigDB values
    (CONTRACT.md section 6, keys exact).  The returned
    :class:`HammingAssertions` instance carries ``.tasks`` (the spawned
    cocotb Tasks).  The integration (env/tb_top/tests) stage is expected to
    call this exactly once, e.g. ``start_assertions()`` at the start of the
    test body, before sequences start driving.
    """
    if pins is None:
        pins = ConfigDB().get(None, "*", KEY_DUT_PINS)
    if clkrs is None:
        clkrs = ConfigDB().get(None, "*", KEY_CLK_RST)
    if conf is None:
        conf = ConfigDB().get(None, "*", KEY_CONF)
    assertions = HammingAssertions(pins, clkrs, conf, logger)
    assertions.start()
    return assertions


# ── bounded-run watchdog ─────────────────────────────────────────────────

class HammingWatchdog:
    """Bounded-run watchdog that fails a hung test (plan watchdog rule).

    Counts virtual reference cycles (``wait_clock_cycles``); if ``done`` (a
    ``cocotb.triggers.Event``) has not been set within ``max_cycles`` cycles,
    :meth:`run` raises ``AssertionError`` and thereby fails the test
    immediately.  The test / tb_top layer sets ``done`` (``done.set()``) when
    the test body completes (typically in a ``finally``), letting the
    watchdog exit quietly early.

    The DUT has no ``clk`` pin, so the watchdog uses the virtual reference
    clock (``wait_clock_cycles``) exactly like every other stage-5 component.
    """

    def __init__(self, clkrs, max_cycles, done,
                 description="hamming_encoder simulation", logger=None):
        self.clkrs = clkrs
        self.max_cycles = int(max_cycles)
        self.done = done
        self.description = description
        self.logger = logger if logger is not None else log

    async def run(self):
        """Wait for ``done`` or the bounded cycle budget, whichever first."""
        for spent in range(self.max_cycles):
            if self.done.is_set():
                return
            await wait_clock_cycles(self.clkrs, 1)
        if not self.done.is_set():
            raise AssertionError(
                f"watchdog timeout: {self.description} did not finish within "
                f"{self.max_cycles} virtual reference cycles"
            )


def start_watchdog(clkrs, max_cycles, done=None,
                   description="hamming_encoder simulation"):
    """Launch a bounded watchdog coroutine and return its cocotb Task.

    Args:
        clkrs: ConfigDB-shared ``ClockReset`` (virtual reference clock).
        max_cycles: number of reference cycles the run is allowed to take.
        done: ``cocotb.triggers.Event`` set by the test body on completion;
            a fresh ``Event`` is created when omitted.
        description: human-readable label for the watchdog error message.
    """
    if done is None:
        done = Event()
    watchdog = HammingWatchdog(clkrs, max_cycles, done, description)
    return cocotb.start_soon(watchdog.run()), done


def watchdog_event_for(max_cycles, clkrs=None,
                       description="hamming_encoder simulation"):
    """One-shot convenience: start the watchdog and return ``(task, done)``
    with ``clkrs`` resolved from ConfigDB when not given."""
    if clkrs is None:
        clkrs = ConfigDB().get(None, "*", KEY_CLK_RST)
    return start_watchdog(clkrs, max_cycles, None, description)