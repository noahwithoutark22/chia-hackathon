"""Stage 4 (scoring) artifact of the CHIA generator: the pyuvm scoreboard.

``AES128Scoreboard`` is the reference-model (oracle) checker for the
``aes128`` DUT.  It implements the ``scoreboard_reference_model_strategy``
from the verification plan as a *parallel reference model* + *transaction
scorer*:

* **parallel_reference_model** -- the Python oracle
  ``aes_reference_model.encrypt_block(key_bytes, plaintext_bytes)`` is
  called as soon as a completed transaction arrives.  The stage-3 monitor
  already captured ``key`` / ``plaintext`` at the acceptance edge, so the
  expected ciphertext is produced "in parallel" with (and independently
  of) the DUT's own 12-cycle computation and stored until the transaction
  is scored.
* **transaction_scorer** -- each published transaction is scored on its
  own.  The scoreboard tracks the total number of transactions, matches,
  and mismatches and reports every mismatch with full hex context.

Input path
----------
The scoreboard consumes analysis items through a
``uvm_tlm_analysis_fifo``: the environment connects
``agent.analysis_port`` to ``scoreboard.analysis_export`` (the fifo's TLM
export).  Each item is an :class:`~tb.transaction.AES128Transaction` that
the stage-3 monitor already reconstructed at the ``done`` pulse:

* stimulus fields (``start``, ``key``, ``plaintext``) were captured at the
  acceptance edge (DUT idle + ``start == 1``), and
* output fields (``ciphertext``, ``busy``, ``done``) were sampled while
  ``dut.done == 1``: ``ciphertext`` holds the valid encrypted result,
  ``busy`` is 0 (deasserted on the same edge) and ``done`` is 1.

The scoreboard therefore **does not count cycles and does not read any DUT
pin**: it keys off the completed item itself, exactly as CONTRACT.md
section 7.4 advises (no hard-coded 12-cycle latency assumption, no
pipeline model).  The correct input/output cycle relationship is already
baked into the item by the monitor -- the item arrives at the ``done``
pulse with the stimulus that produced it.

Reset behavior
--------------
Reset aborts are handled upstream: the monitor drops any in-flight
transaction aborted by ``rst_n`` (or by a ``busy`` 1 -> 0 fall without
``done``, or by the ``done`` timeout) and never publishes it (CONTRACT.md
sections 7.1 / 7.5).  The scoreboard therefore only ever sees *completed,
non-reset-aborted* transactions, which is precisely the pass-criteria
scope: "DUT ciphertext must exactly match the Python reference model
output for every completed (non-reset-aborted) transaction."

Scoring rules
-------------
* Byte mapping (CONTRACT.md section 4): the 128-bit ``int`` fields are
  converted to/from 16-byte **big-endian** blocks
  (``int.to_bytes(16, 'big')``); the RTL maps ``[127:120]`` to AES state
  byte 0, so big-endian is the exact byte order the byte-oriented Python
  oracle expects.
* Comparison: the DUT ``ciphertext`` is compared **byte-by-byte** (16
  bytes) against ``encrypt_block(key, plaintext)``.  Any single-byte
  mismatch constitutes a verification failure (plan pass criteria).
* Error reporting (plan error_reporting): on mismatch the scoreboard
  reports the transaction number, DUT ciphertext, expected ciphertext,
  key, and plaintext in hexadecimal format, plus the number of differing
  bytes and the first mismatching byte position / values.
* Defensive item-contract check: a published item that violates the
  section-4 ``done``-pulse convention (``start != 1``, ``busy != 0`` or
  ``done != 1``) is also flagged as a failure.  With a correct monitor
  these checks never fire; they exist to catch a monitor bug loudly.
* The scoreboard deliberately does **not** raise on a mismatch so the run
  keeps collecting failures; the environment / test stage fails the test
  when ``mismatches`` is nonzero (or on a hard Python error).

Reference model sourcing
------------------------
The benchmark oracle ``aes_reference_model.encrypt_block`` is imported,
never reimplemented.  Search order:

1. ``tb.aes_reference_model`` -- a verbatim copy of
   ``benchmarks/aes_benchmark/aes_reference_model.py`` shipped next to
   this module (primary source, see the stage-4 summary / CONTRACT.md
   section 8.2);
2. the authoritative ``benchmarks/aes_benchmark`` directory (added to
   ``sys.path``), for workspaces where the copy has not been
   materialized.

Both expose the same module name ``aes_reference_model`` and the same
entry point ``encrypt_block``.
"""

import os
import sys
import traceback

from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo

from tb.transaction import AES128Transaction

__all__ = ["AES128Scoreboard"]


def _load_reference_model():
    """Return the module exposing ``encrypt_block(key, plaintext)``.

    Tries the verbatim copy shipped in the tb directory first
    (``tb.aes_reference_model``), then falls back to the authoritative
    ``benchmarks/aes_benchmark`` directory on ``sys.path``.
    """
    try:
        from tb import aes_reference_model as ref_model
        return ref_model
    except ImportError:
        pass
    # Fallback: locate <workspace>/benchmarks/aes_benchmark relative to
    # this file (tb -> aes_benchmark -> designs -> generated -> workspace).
    bench_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..",
        "benchmarks", "aes_benchmark",
    ))
    if os.path.isdir(bench_dir) and bench_dir not in sys.path:
        sys.path.insert(0, bench_dir)
    import aes_reference_model as ref_model
    return ref_model


try:
    _REFERENCE_MODEL = _load_reference_model()
except Exception as _exc:  # pragma: no cover - environment-dependent
    raise ImportError(
        "AES128Scoreboard: cannot load the AES-128 reference model module "
        "'aes_reference_model' (needed for the encrypt_block oracle). "
        "Expected a verbatim copy at tb/aes_reference_model.py or the "
        "authoritative benchmarks/aes_benchmark directory. "
        f"Cause: {_exc!r}"
    ) from _exc

if not callable(getattr(_REFERENCE_MODEL, "encrypt_block", None)):
    raise AttributeError(
        "AES128Scoreboard: the reference-model module "
        f"'{_REFERENCE_MODEL.__name__}' does not expose "
        "encrypt_block(key, plaintext)."
    )


class AES128Scoreboard(uvm_scoreboard):
    """Reference-model transaction scorer for the ``aes128`` DUT.

    Consumes one :class:`~tb.transaction.AES128Transaction` per completed
    (non-reset-aborted) transaction from the monitor analysis fifo and
    compares the DUT ``ciphertext`` byte-by-byte against
    ``aes_reference_model.encrypt_block(key, plaintext)``.
    """

    def __init__(self, name="aes128_scoreboard", parent=None):
        super().__init__(name, parent)

        # Shared DUT config (CONTRACT.md section 5; retrieval form section
        # 7.3).  Diagnostic use only -- scoring is purely item-driven, so
        # these are never required for the comparison itself.
        self.dut = None
        self.helper = None

        # TLM analysis path.  The environment stage connects the monitor's
        # analysis port here:
        #   agent.analysis_port.connect(scoreboard.analysis_export)
        self.analysis_fifo = None
        self.analysis_export = None

        # Scoring accounting (exposed for the environment report).
        self.transactions = 0   # total items scored
        self.matches = 0        # items with zero problems
        self.mismatches = 0     # items with at least one problem
        self._failures = []     # per-item human-readable failure strings

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        """Resolve shared config and create the TLM analysis fifo."""
        super().build_phase()
        # CONTRACT.md section 7.3: empty-scope retrieval path matches the
        # wildcard store (``set(None, "*", key, value)``) under pyuvm 5.0.
        self.dut = ConfigDB().get(self, "", "dut")
        self.helper = ConfigDB().get(self, "", "dut_helper")
        if self.dut is None or self.helper is None:
            self.logger.warning(
                "%s: 'dut'/'dut_helper' not found in ConfigDB; scoring "
                "continues (item-driven, no pin access needed)",
                self.get_name())

        # Buffers monitor items; analysis_export is what the environment
        # connects the agent's analysis_port to.
        self.analysis_fifo = uvm_tlm_analysis_fifo(
            "aes128_analysis_fifo", self)
        self.analysis_export = self.analysis_fifo.analysis_export
        self.logger.info(
            "%s: built (oracle module=%s; encrypt_block=%r)",
            self.get_name(),
            _REFERENCE_MODEL.__name__,
            _REFERENCE_MODEL.encrypt_block,
        )

    async def run_phase(self):
        """Consume monitor transactions and score each against the oracle."""
        self.logger.info("%s: run_phase started", self.get_name())
        while True:
            tr = await self.analysis_fifo.get()
            self._score(tr)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    @staticmethod
    def _to_bytes(value: int) -> bytes:
        """128-bit ``int`` -> 16 bytes, big-endian (MSB = AES state byte 0).

        Matches the RTL byte mapping ([127:120] is AES state byte 0) and
        the byte-oriented Python oracle's expectations (CONTRACT.md section
        4).
        """
        return value.to_bytes(16, "big")

    @staticmethod
    def _to_int(block: bytes) -> int:
        """16 bytes -> 128-bit ``int`` (big-endian)."""
        return int.from_bytes(block, "big")

    def _compute_expected(self, tr):
        """Run the reference model on the transaction's stimulus.

        Returns ``(expected_ciphertext_int, expected_ciphertext_bytes)``.
        """
        key = int(tr.key)
        plaintext = int(tr.plaintext)
        expected_bytes = _REFERENCE_MODEL.encrypt_block(
            self._to_bytes(key), self._to_bytes(plaintext))
        return self._to_int(expected_bytes), expected_bytes

    def _score(self, tr: AES128Transaction) -> None:
        """Score one completed transaction (see module docstring)."""
        self.transactions += 1

        problems = []
        expected_int = None
        try:
            # Defensive item-contract sanity (CONTRACT.md section 4): a
            # published item must represent a completed transaction -- an
            # accepted offer (start==1) completed by the done pulse
            # (done==1, busy==0).  These never fire with a correct monitor.
            if int(tr.start) != 1:
                problems.append(
                    f"start field is {int(tr.start)} (expected 1 for a "
                    "completed, accepted transaction)")
            if int(tr.busy) != 0:
                problems.append(
                    f"busy field is {int(tr.busy)} (expected 0 while done "
                    "pulses)")
            if int(tr.done) != 1:
                problems.append(
                    f"done field is {int(tr.done)} (expected 1 marking the "
                    "completion pulse)")

            # Parallel reference model: expected result computed
            # immediately, compared byte-by-byte at done time.
            expected_int, expected_bytes = self._compute_expected(tr)
            dut_int = int(tr.ciphertext)
            dut_bytes = self._to_bytes(dut_int)
            differing = [
                (idx, dut_bytes[idx], expected_bytes[idx])
                for idx in range(16)
                if dut_bytes[idx] != expected_bytes[idx]
            ]
            if differing:
                first_byte, dut_val, exp_val = differing[0]
                problems.append(
                    "ciphertext mismatch: "
                    f"DUT 0x{dut_int:032x} vs expected 0x{expected_int:032x} "
                    f"({len(differing)} byte(s) differ; first at byte "
                    f"{first_byte}: DUT 0x{dut_val:02x}, expected "
                    f"0x{exp_val:02x})")
        except Exception as exc:  # noqa: BLE001 - scoring must keep going
            problems.append(
                "hard error while scoring: "
                f"{exc!r}\n{traceback.format_exc()}")

        if problems:
            self.mismatches += 1
            msg = (
                f"MISMATCH transaction #{self.transactions}: "
                f"key=0x{int(tr.key):032x}, "
                f"plaintext=0x{int(tr.plaintext):032x}, "
                f"DUT ciphertext=0x{int(tr.ciphertext):032x}"
            )
            if expected_int is not None:
                msg += f", expected ciphertext=0x{expected_int:032x}"
            msg += " :: " + "; ".join(problems)
            self.logger.error(msg)
            self._failures.append(msg)
        else:
            self.matches += 1

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def report_phase(self):
        """Summarize pass/fail statistics for the test framework."""
        super().report_phase()
        self.logger.info(
            "%s: report: %d transaction(s), %d match(es), %d mismatch(es)",
            self.get_name(), self.transactions, self.matches,
            self.mismatches)
        if self.mismatches:
            self.logger.warning(
                "%s: FAILED: %d comparison mismatch(es)",
                self.get_name(), self.mismatches)

    @property
    def passing(self) -> bool:
        """True when every scored transaction matched the oracle."""
        return self.mismatches == 0

    def results(self) -> dict:
        """Summary dict for the environment / test pass criteria."""
        return {
            "transactions": self.transactions,
            "matches": self.matches,
            "mismatches": self.mismatches,
            "passing": self.passing,
            "failures": list(self._failures),
        }