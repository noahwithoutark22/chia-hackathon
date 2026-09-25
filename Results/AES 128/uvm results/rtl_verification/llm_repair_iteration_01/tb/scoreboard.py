"""AES-128 predictive scoreboard (pyuvm ``uvm_scoreboard``).

Stage-4 (SCOREBOARD) artifact of the CHIA cocotb+pyuvm generator for the
``aes128`` DUT (``benchmarks/aes128_benchmark_corrupted/aes128.sv``).

ROLE (plan ``scoreboard_reference_model_strategy``)
--------------------------------------------------
:class:`Aes128Scoreboard` implements the two-pronged predictive strategy
exactly as the plan specifies:

* *reference_model_predictor* -- for every completed transaction the
  expected ciphertext is computed from the data captured at ``start``:
  ``aes128_reference_model.aes128_encrypt(plaintext, key)`` is the *only*
  encryption computation in the TB.  The reference model is imported
  directly (a verbatim copy of the authoritative benchmark module is
  shipped at ``tb/aes128_reference_model.py``; if that is not importable
  the authoritative ``benchmarks/aes128_benchmark_corrupted`` directory is
  added to ``sys.path``).  Its arithmetic is never reimplemented or
  translated here.
* *transaction_in_order_scoreboard* -- exactly one transaction is in
  flight at a time, so every published monitor item (a ``done`` pulse
  paired with its captured start) maps to the single in-flight
  transaction; matching is strictly in order and each item is scored as it
  arrives.

INPUT PATH / CYCLE RELATIONSHIP (do not assume a pipeline)
----------------------------------------------------------
The scoreboard is purely item-driven, per the CONTRACT.md §7
latency-discovery rule: verification is driven by the ``done`` pulse,
never by a hard-coded cycle count.  The stage-3 monitor (CONTRACT.md §9.1)
already applied the DUT's registered input/output relationship
(CONTRACT.md §2, §6: inputs sampled and outputs updated on the positive
clock edge):

* stimulus fields (``start``/``key``/``plaintext``) were captured with a
  mid-cycle falling-edge probe at the acceptance edge, and
* output fields (``done``/``ciphertext``) were sampled post-edge (cocotb
  read-only region) while ``done == 1``.

A published :class:`~transaction.Aes128Transaction` therefore already
carries the exact (input, output) pair that belongs to one transaction.
The scoreboard does not count cycles, does not read any DUT pin, and does
not assume a fixed AES latency or a pipeline.

Items arrive through a ``uvm_tlm_analysis_fifo``:

* ``env.connect_phase``: ``agent.analysis_port.connect(scoreboard.analysis_export)``
  (or the convenience ``scoreboard.connect_monitor(agent.analysis_port)``).

PROTOCOL-VIOLATION REPORTING (reported separately, plan error_reporting)
------------------------------------------------------------------------
Item-level protocol anomalies are counted in a separate bucket so they are
never blurred with ciphertext mismatches:

* ``start != 1`` on a published item -- a "done pulse without a captured
  accepted start" reached the scoreboard;
* ``done != 1`` on a published item -- a corrupted completion record.

Pin-level protocol anomalies that are invisible at the item level (an
unexpected ``done`` pulse the monitor already dropped, a stuck-``done``
high, a ``done`` pulse wider than one cycle) are owned by the
always-running assertion checkers of the assertions stage (CONTRACT.md
§9.1).  The scoreboard keeps its own counters (``protocol_errors``,
``order_errors``, ``ungradable_errors``) so the two reporting domains
stay separate.

IN-ORDER INTEGRITY
------------------
The monitor stamps every published item with its monotonic rising-edge
counter ``dut_cycle`` (never reset, even across reset aborts, which the
monitor drops without publishing).  Successive published items must carry
strictly increasing ``dut_cycle`` stamps; a non-increasing stamp means the
monitor/transport dropped, duplicated, or reordered an item and is
reported as an ``order_errors`` anomaly.  ``txn_id`` is NOT used for
ordering: the passive monitor cannot observe the driver's stimulus-side id
(CONTRACT.md §5, §9.1), so the scoreboard assigns its own 1-based
transaction index for reports.

PASS CRITERIA (as scored here)
------------------------------
``passing`` requires every scored transaction to match the reference-model
prediction (``mismatches == 0``) AND zero protocol/order/ungradable errors
(``error_count == 0``).  Note that for this target RTL a ciphertext
mismatch against the FIPS-197 oracle is the *intended* bug-detection
outcome (plan DISCs); the test stage derives the final verdict from
:meth:`results`.

All APIs used here are public pyuvm 5.0.0 APIs
(``uvm_scoreboard``, ``uvm_tlm_analysis_fifo``, ``ConfigDB``).  This
module needs no cocotb trigger/handle access: scoring is purely
item-driven, so there are no ``cocotb.*`` imports to go stale.  No
SystemVerilog anywhere.
"""

import importlib
import os
import sys
import traceback

from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo

from transaction import Aes128Transaction

__all__ = ["Aes128Scoreboard"]

#: Name of the reference-model module (CONTRACT.md §3).
_REF_MODULE_NAME = "aes128_reference_model"

#: Mask for all 128-bit buses (CONTRACT.md §2).
MASK128 = (1 << 128) - 1

#: Number of bytes in a 128-bit AES block (byte-oriented big-endian).
BLOCK_BYTES = 16


def _load_reference_model():
    """Return the authoritative ``aes128_reference_model`` module.

    Search order (both expose the identical module name and the identical
    entry point ``aes128_encrypt(plaintext, key)`` -- CONTRACT.md §3):

    1. ``aes128_reference_model`` already importable (a verbatim copy is
       shipped at ``tb/aes128_reference_model.py``; when the tb directory
       is on ``sys.path``/the working directory this is the module used);
    2. the authoritative ``benchmarks/aes128_benchmark_corrupted``
       directory (added to ``sys.path``) for workspaces where the copy has
       not been materialized.
    """
    try:
        return importlib.import_module(_REF_MODULE_NAME)
    except ImportError:
        pass
    # Fallback: locate <workspace>/benchmarks/aes128_benchmark_corrupted
    # relative to this file (tb -> aes128_benchmark_corrupted -> designs
    # -> generated -> workspace).
    bench_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..",
        "benchmarks", "aes128_benchmark_corrupted",
    ))
    if os.path.isdir(bench_dir) and bench_dir not in sys.path:
        sys.path.insert(0, bench_dir)
    return importlib.import_module(_REF_MODULE_NAME)


def _verify_oracle(module):
    """Validate the oracle module before trusting any score it produces.

    Require the documented entry point ``aes128_encrypt(plaintext, key)``
    (argument order exactly as CONTRACT.md §3) and verify that the module
    reproduces every entry of its own ``TEST_VECTORS`` -- the mandatory
    known answers (FIPS-197 ``69c4e0d8...``, all-zero ``66e94bd4...``,
    incrementing ``0a940bb5...``) the plan lists.  A corrupt oracle would
    silently poison every mismatch report, so a failed check is raised here
    at import time rather than discovered mid-run.
    """
    fn = getattr(module, "aes128_encrypt", None)
    if not callable(fn):
        raise AttributeError(
            f"Aes128Scoreboard: reference-model module "
            f"'{getattr(module, '__name__', module)!r}' does not expose "
            "aes128_encrypt(plaintext, key)."
        )
    vectors = getattr(module, "TEST_VECTORS", []) or []
    for vector in vectors:
        try:
            key = int(vector["key"], 16)
            plaintext = int(vector["plaintext"], 16)
            expected = int(vector["ciphertext"], 16)
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "Aes128Scoreboard: malformed TEST_VECTORS entry in "
                f"reference model: {vector!r}: {exc!r}"
            ) from exc
        got = fn(plaintext, key)
        if got != expected:
            raise RuntimeError(
                "Aes128Scoreboard: reference model failed its own known-"
                f"answer vector {vector.get('name', '?')}: expected "
                f"ciphertext 0x{expected:032x}, model returned "
                f"0x{got:032x} -- refusing to score against a broken oracle."
            )
    return module


try:
    _REFERENCE_MODEL = _verify_oracle(_load_reference_model())
except Exception as _exc:  # pragma: no cover - environment-dependent
    raise ImportError(
        "Aes128Scoreboard: cannot load/validate the AES-128 reference model "
        "module 'aes128_reference_model' (needed for the aes128_encrypt "
        "oracle). Expected a verbatim copy at tb/aes128_reference_model.py "
        "or the authoritative benchmarks/aes128_benchmark_corrupted "
        f"directory. Cause: {_exc!r}"
    ) from _exc


def _config_get(field, default=None):
    """Retrieve a ConfigDB key using the CONTRACT.md §4 retrieval convention.

    Identical helper to ``driver.py``/``monitor.py``: the documented
    project-wide form is ``ConfigDB().get(None, "*", field)``, but the
    pinned pyuvm 5.0.0 runtime rejects wildcard characters in a *retrieval*
    path ("inst_name wildcards only allowed when storing"); when the
    primary form raises we fall back to the equivalent ``inst_name=""``
    retrieval against the same wildcard-stored key.  No key or value type
    is changed.
    """
    try:
        return ConfigDB().get(None, "*", field, default=default)
    except Exception:
        return ConfigDB().get(None, "", field, default=default)


class Aes128Scoreboard(uvm_scoreboard):
    """Reference-model, in-order transaction scorer for the ``aes128`` DUT.

    Consumes one :class:`~transaction.Aes128Transaction` per completed
    (non-reset-aborted) transaction from the monitor analysis fifo and
    compares the DUT ``ciphertext`` (sampled while ``done`` is high)
    against ``aes128_reference_model.aes128_encrypt(plaintext, key)``.
    """

    def __init__(self, name="aes128_scoreboard", parent=None):
        super().__init__(name, parent)

        # Shared DUT config (CONTRACT.md §4).  Diagnostic only -- scoring
        # is purely item-driven, so the handle is never required for the
        # comparison itself.
        self.dut = None

        # TLM analysis path.  The environment stage connects the agent's
        # analysis port here:
        #   agent.analysis_port.connect(scoreboard.analysis_export)
        # (or scoreboard.connect_monitor(agent.analysis_port)).
        self.analysis_fifo = None
        self.analysis_export = None

        # Scoring accounting (exposed for the environment/test report).
        self.transactions = 0      # total items consumed and graded
        self.matches = 0           # ciphertext matched the oracle
        self.mismatches = 0        # ciphertext differed from the oracle
        self.protocol_errors = 0   # item-level protocol violations
        self.order_errors = 0      # non-increasing dut_cycle stamps
        self.ungradable_errors = 0 # oracle rejected the stimulus / item type
        self.error_count = 0       # protocol + order + ungradable
        self._failures = []        # per-item human-readable failure strings
        self._protocol_violations = []  # separate protocol-only reports
        self._prev_dut_cycle = None     # in-order integrity watermark

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self):
        """Resolve shared config (optional) and build the analysis fifo."""
        super().build_phase()
        # CONTRACT.md §4: 'dut' is authoritative; the helper is optional
        # sugar that this component does not need.  Scoring is item-driven,
        # so a missing handle is a warning, not a reason to refuse scoring.
        self.dut = _config_get("dut")
        if self.dut is None:
            self.logger.warning(
                "%s: 'dut' not found in ConfigDB; scoring continues "
                "(item-driven, no pin access needed)",
                self.get_name(),
            )
        # Buffers monitor items; analysis_export is what the environment
        # connects the agent's analysis_port to.
        self.analysis_fifo = uvm_tlm_analysis_fifo(
            "aes128_sb_fifo", self)
        self.analysis_export = self.analysis_fifo.analysis_export
        self.logger.info(
            "%s: built (oracle module=%s; aes128_encrypt=%r; "
            "known-answer vectors=%d)",
            self.get_name(),
            _REFERENCE_MODEL.__name__,
            _REFERENCE_MODEL.aes128_encrypt,
            len(getattr(_REFERENCE_MODEL, "TEST_VECTORS", []) or []),
        )

    def connect_monitor(self, ap):
        """Subscribe a monitor/agent analysis port to the scoreboard fifo.

        pyuvm 5.0.0: ``uvm_analysis_port.connect(export)`` appends the
        export to the port's ``subscribers``; ``ap.write(datum)`` then
        broadcasts to them (CONTRACT.md §9.2).  The fifo's
        ``analysis_export.write`` enqueues into the queue, so every
        transaction the monitor publishes is received in order.
        Equivalent to ``ap.connect(self.analysis_export)``.
        """
        if ap is None:
            raise ValueError("connect_monitor: analysis port is None")
        ap.connect(self.analysis_export)

    async def run_phase(self):
        """Consume completed transactions in order and grade each one.

        Blocking get from the analysis fifo: the fifo is written by the
        monitor through the analysis broadcast model, so this loop sleeps
        while nothing has completed and wakes once per transaction.
        Transactions arrive in start order (one in flight at a time,
        CONTRACT.md §7/§9.1), so grading here is naturally in order.
        """
        self.logger.info("%s: run_phase started", self.get_name())
        while True:
            tr = await self.analysis_fifo.get()
            self._score(tr)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    @staticmethod
    def _to_bytes(value: int) -> bytes:
        """128-bit ``int`` -> 16 bytes, big-endian.

        The most-significant byte of the 128-bit vector is AES state byte 0
        and the state is arranged column-major (CONTRACT.md §3), so big-
        endian is the natural byte order for the mismatch detail report.
        Only used for reporting; the oracle itself works on ints directly.
        """
        return int(value).to_bytes(BLOCK_BYTES, "big")

    def _score(self, tr) -> None:
        """Grade one completed transaction (see module docstring)."""
        if not isinstance(tr, Aes128Transaction):
            self.ungradable_errors += 1
            self.error_count += 1
            self.logger.error(
                "%s: received a non-Aes128Transaction item: %r "
                "(not graded, counted as an error)",
                self.get_name(), tr,
            )
            return

        self.transactions += 1
        idx = self.transactions  # 1-based scoreboard transaction id
        problems = []

        # --- 1) In-order integrity: the monitor's dut_cycle stamp is a
        #         monotonic rising-edge counter (never reset, dropped items
        #         are not published), so successive published items must
        #         carry strictly increasing stamps.  Any other value means
        #         the monitor/transport dropped, duplicated, or reordered a
        #         transaction ("strictly in order" pass criterion).
        dut_cycle = None
        try:
            dut_cycle = int(tr.dut_cycle) if tr.dut_cycle is not None else None
        except (TypeError, ValueError):
            dut_cycle = None
        if dut_cycle is not None:
            prev = self._prev_dut_cycle
            if prev is not None and dut_cycle <= prev:
                self.order_errors += 1
                self.error_count += 1
                problems.append(
                    "order anomaly: dut_cycle=%d is not strictly greater "
                    "than the previous published item's %d (missing, "
                    "duplicate, or reordered transaction in the stream)"
                    % (dut_cycle, prev)
                )
            self._prev_dut_cycle = dut_cycle

        # --- 2) Item-level protocol contract (plan error_reporting:
        #         "done without start", "extra done" -- reported
        #         separately).  A completed item must represent an accepted
        #         offer (start==1) completed by the done pulse (done==1).
        #         These never fire with a correct monitor; they exist to
        #         catch a monitor/environment bug loudly and to keep
        #         protocol accounting out of the ciphertext bucket.
        try:
            start_field = int(tr.start)
        except (TypeError, ValueError):
            start_field = -1
        try:
            done_field = int(tr.done)
        except (TypeError, ValueError):
            done_field = -1
        protocol_issues = []
        if start_field != 1:
            protocol_issues.append(
                f"done pulse without a captured accepted start: start "
                f"field = {tr.start!r} (expected 1 for a completed, "
                "accepted transaction)")
        if done_field != 1:
            protocol_issues.append(
                f"completion record corrupt: done field = {tr.done!r} "
                "(expected 1 marking the done pulse)")
        if protocol_issues:
            self.protocol_errors += 1
            self.error_count += 1
            self._protocol_violations.append(
                f"txn #{idx}: " + "; ".join(protocol_issues))
            problems.extend(protocol_issues)

        # --- 3) Reference-model prediction (CONTRACT.md §3:
        #         aes128_encrypt(plaintext, key); no byte reordering is
        #         performed by the testbench).  The DUT ciphertext sampled
        #         while done was high is compared to the prediction.
        try:
            key = int(tr.key)
            plaintext = int(tr.plaintext)
            expected = _REFERENCE_MODEL.aes128_encrypt(plaintext, key)
        except Exception as exc:  # noqa: BLE001 - scoring must keep going
            self.ungradable_errors += 1
            self.error_count += 1
            problems.append(
                "ungradable: the oracle rejected the captured stimulus "
                f"(key={tr.key!r}, plaintext={tr.plaintext!r}): {exc!r}")
            self.logger.debug("%s", traceback.format_exc())
        else:
            try:
                actual_int = int(tr.ciphertext)
            except (TypeError, ValueError):
                actual_int = -1  # sentinel: not an int -> cannot match
            if not (0 <= actual_int <= MASK128):
                # The monitor always masks ciphertext to 128 bits
                # (CONTRACT.md §2), so an out-of-range value means a corrupt
                # item.  It cannot equal the prediction, so it grades as a
                # mismatch (not an ungradable: the oracle is fine); the
                # message names the actual value.
                self.mismatches += 1
                problems.append(
                    "ciphertext mismatch: expected (reference model) "
                    f"0x{expected:032x}, actual (DUT) {tr.ciphertext!r} "
                    "(out of the 128-bit range)"
                )
            elif actual_int == expected:
                self.matches += 1
                self.logger.info(
                    "MATCH txn #%d (dut_cycle=%s): key=0x%032x "
                    "plaintext=0x%032x ciphertext=0x%032x",
                    idx, dut_cycle, key, plaintext, actual_int,
                )
            else:
                self.mismatches += 1
                actual_bytes = self._to_bytes(actual_int)
                expected_bytes = self._to_bytes(expected)
                differing = [
                    (byte_i, actual_bytes[byte_i], expected_bytes[byte_i])
                    for byte_i in range(BLOCK_BYTES)
                    if actual_bytes[byte_i] != expected_bytes[byte_i]
                ]
                first_byte, dut_val, exp_val = differing[0]
                problems.append(
                    "ciphertext mismatch: "
                    f"expected (reference model) 0x{expected:032x}, "
                    f"actual (DUT) 0x{actual_int:032x} "
                    f"({len(differing)} byte(s) differ; first at byte "
                    f"{first_byte}: DUT 0x{dut_val:02x}, expected "
                    f"0x{exp_val:02x})"
                )

        if problems:
            # Per-item failure record with the full transaction context
            # required by the plan's error_reporting.  Key/plaintext are
            # reported unmasked so a corrupt (e.g. >128-bit) value stays
            # visible in the record.
            msg = (
                f"txn #{idx} (dut_cycle={dut_cycle}): "
                f"key=0x{int(tr.key):032x}, "
                f"plaintext=0x{int(tr.plaintext):032x}, "
            )
            try:
                msg += f"actual ciphertext=0x{int(tr.ciphertext):032x}"
            except (TypeError, ValueError):
                msg += f"actual ciphertext={tr.ciphertext!r}"
            msg += " :: " + "; ".join(problems)
            self.logger.error("%s", msg)
            self._failures.append(msg)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    @property
    def passing(self) -> bool:
        """True when the plan pass criteria hold as far as the scoreboard
        can see: every scored transaction matched the reference-model
        prediction and there were no protocol/order/ungradable errors."""
        return self.mismatches == 0 and self.error_count == 0

    def results(self) -> dict:
        """Summary dict for the environment / test pass criteria."""
        return {
            "transactions": self.transactions,
            "matches": self.matches,
            "mismatches": self.mismatches,
            "protocol_errors": self.protocol_errors,
            "order_errors": self.order_errors,
            "ungradable_errors": self.ungradable_errors,
            "error_count": self.error_count,
            "passing": self.passing,
            "failures": list(self._failures),
        }

    def get_summary(self) -> str:
        """Compact one-line scoring summary for log/report phases."""
        s = self.results()
        return (
            f"Aes128Scoreboard[{self.get_name()}]: "
            f"transactions={s['transactions']} "
            f"matches={s['matches']} mismatches={s['mismatches']} "
            f"protocol_errors={s['protocol_errors']} "
            f"order_errors={s['order_errors']} "
            f"ungradable_errors={s['ungradable_errors']} "
            f"error_count={s['error_count']} passing={s['passing']}"
        )

    def convert2string(self) -> str:
        return self.get_summary()

    def report_phase(self):
        """Summarize pass/fail statistics for the test framework."""
        super().report_phase()
        self.logger.info("%s: %s", self.get_name(), self.get_summary())
        if self._protocol_violations:
            self.logger.warning(
                "%s: %d protocol violation(s) reported separately:",
                self.get_name(), self.protocol_errors,
            )
            for violation in self._protocol_violations:
                self.logger.warning("    %s", violation)
        if self.mismatches:
            self.logger.warning(
                "%s: FAILED: %d comparison mismatch(es) against the "
                "reference model",
                self.get_name(), self.mismatches,
            )