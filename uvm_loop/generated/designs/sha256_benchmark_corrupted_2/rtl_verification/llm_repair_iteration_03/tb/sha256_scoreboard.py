"""SHA-256 UVM scoreboard (stage-4 SCOREBOARD artifact).

In-order comparison component for the cocotb + pyuvm verification
environment described by CONTRACT.md.

ROLE (plan ``scoreboard_reference_model_strategy``):
    The corrupted RTL does NOT implement a correct SHA-256 compression
    function (CONTRACT.md §8: DISC-002..DISC-017); ``done`` stays 1
    continuously (DISC-001) and ``busy`` is never released (DISC-013).
    The scoreboard therefore consumes exactly the monitor's completed
    transactions -- one per start pulse, in start order, with the digest
    sampled COMPLETION_MARGIN_CYCLES after the start edge (CONTRACT.md §7
    fixed-cycle completion model, §12 monitor) -- predicts the expected
    digest with the golden Python reference model
    ``sha256_reference_model.block_to_digest`` and *reports* every digest
    mismatch (transaction id, input block, expected digest, actual digest,
    and cycle of mismatch).  The scoreboard NEVER reimplements SHA-256:
    the reference model (imported directly, copied verbatim into this
    ``tb/`` directory) is the only digest computation in the TB.

MATCHING / ORDERING MODEL (in-order):
    The monitor assigns monotonic, 1-based, per-start-pulse ``txn_id`` and
    publishes transactions in start order (fixed equal completion latency,
    CONTRACT.md §7/§12).  The scoreboard consumes the FIFO in the same
    order and enforces txn_id contiguity (``txn.txn_id`` must equal the
    next expected id): a gap/duplicate/reorder is reported as an
    ``order_error`` and counts against "no extra/missing transactions".

IMPORTANT SEMANTIC (corrupted-RTL grading, CONTRACT.md §8):
    ``mismatch_count > 0`` is a *catch report*, not by itself a test
    failure -- for this RTL a digest mismatch vs. the golden reference is
    the EXPECTED and DESIRED observation (it proves the environment
    detects the faults).  ``order_error_count`` and
    ``invalid_block_count`` are real contract violations.  The env/test
    stage (stage 5) grades pass/fail from the plan's intent and these
    counters.

WIRING (performed by the ENV in its connect phase, stage 5):
    ``scoreboard.connect_monitor(agent.ap)``, which subscribes the
    monitor's analysis port to the scoreboard's fifo
    (``agent.ap.connect(self.fifo.analysis_export)``, CONTRACT.md §12
    pyuvm broadcast model).  ``connect_monitor`` is the documented stable
    entry point; ``fifo.analysis_export`` is also public.

ConfigDB: reads the shared ``"dut"`` key in ``build_phase`` (exact key
from CONTRACT.md §5; the scoreboard is listed as a ``"dut"`` consumer).
No new ConfigDB keys are introduced.

Cocotb 2.1.0 public APIs used: ``cocotb.utils.get_sim_time`` (cycle of
mismatch attribution) and the pyuvm 5.0.0 ``uvm_tlm_analysis_fifo``
(``analysis_export`` put side / ``get_peek_export.get()`` blocking get).
No SystemVerilog anywhere: pure pyuvm (5.0.0) + cocotb (2.1.0).
"""

from cocotb.utils import get_sim_time

from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo

from sha256_pins import CLK_PERIOD_NS, COMPLETION_MARGIN_CYCLES
from sha256_reference_model import block_to_digest
from sha256_transaction import Sha256Transaction

# Number of clock cycles after the start edge at which the monitor samples
# the DUT outputs (CONTRACT.md §7/§12).  Pure reporting metadata: the
# scoreboard grades the digest the monitor sampled exactly this many cycles
# after the start pulse.
SAMPLE_DIGEST_CYCLES = COMPLETION_MARGIN_CYCLES


class Sha256Scoreboard(uvm_scoreboard):
    """In-order digest scoreboard backed by the golden reference model."""

    def __init__(self, name: str = "sha256_scoreboard", parent=None) -> None:
        super().__init__(name, parent)
        # Shared DUT handle (populated in build_phase, CONTRACT.md §5).
        self.dut = None
        # Analysis FIFO receiving the monitor's completed transactions.
        self.fifo = None  # type: uvm_tlm_analysis_fifo
        # In-order bookkeeping ("no extra/missing transactions").
        self._expected_txn_id = 1  # monitor ids are 1-based and monotonic

        # Public scoring counters (read by the env/test stage):
        self.txn_count = 0          # transactions consumed and graded
        self.match_count = 0        # observed digest == reference digest
        self.mismatch_count = 0     # observed digest != reference digest
        self.invalid_block_count = 0  # reference model rejected the block
        self.order_error_count = 0  # txn_id gap/duplicate/out-of-order
        self.error_count = 0        # order + invalid (real contract issues)

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Fetch the shared ``dut`` handle and build the analysis FIFO.

        Exact ConfigDB key: ``"dut"`` (CONTRACT.md §5).  Raising here fails
        the test early if the environment was assembled without the key.
        """
        super().build_phase()
        self.dut = ConfigDB().get(None, "", "dut")
        if self.dut is None:
            self.logger.error(
                "CONTRACT key 'dut' missing from ConfigDB: cannot grade "
                "transaction timing/cycle information."
            )
            raise RuntimeError(
                "Sha256Scoreboard.build_phase: ConfigDB key 'dut' not found"
            )
        # Unbounded analysis fifo (pyuvm sizes it 0 = unlimited).
        self.fifo = uvm_tlm_analysis_fifo("sha256_sb_fifo", self)

    def connect_monitor(self, ap) -> None:
        """Subscribe a monitor/agent analysis port to the scoreboard FIFO.

        pyuvm 5.0.0: ``uvm_analysis_port.connect(export)`` appends the
        export to the port's ``subscribers``; ``ap.write(datum)`` then
        broadcasts to them (CONTRACT.md §12).  The fifo's
        ``analysis_export.write`` enqueues into the queue, so every
        transaction the monitor publishes is received in order.
        """
        if ap is None:
            raise ValueError("connect_monitor: analysis port is None")
        ap.connect(self.fifo.analysis_export)

    def connect_phase(self) -> None:
        """No intra-component wiring.

        The environment connects the agent's analysis port to
        ``self.fifo.analysis_export`` (via :meth:`connect_monitor`) in its
        own connect phase, since the agent is a sibling component.
        """
        super().connect_phase()

    async def run_phase(self) -> None:
        """Consume completed transactions in order and grade each one.

        Blocking get from ``get_peek_export``: the fifo is written by the
        monitor through the analysis broadcast model, so this loop sleeps
        while nothing has completed and wakes per completed transaction.
        Transactions arrive in start order (equal fixed completion latency,
        CONTRACT.md §7/§12), so grading here is naturally in-order.
        """
        while True:
            txn = await self.fifo.get_peek_export.get()
            if not isinstance(txn, Sha256Transaction):
                self.error_count += 1
                self.logger.error(
                    "Scoreboard received a non-Sha256Transaction object: %r "
                    "(ignored for grading, counted as an error)",
                    txn,
                )
                continue
            self._check_transaction(txn)

    # ------------------------------------------------------------------
    # Grading internals
    # ------------------------------------------------------------------
    def _check_transaction(self, txn: Sha256Transaction) -> None:
        """Grade one completed transaction against the reference model."""
        self.txn_count += 1

        # --- 1) In-order integrity: txn_id must be the next id in the
        #         stream.  Any other value means the monitor/transport
        #         dropped, duplicated, or reordered a transaction
        #         ("no extra/missing transactions" pass criterion).
        if txn.txn_id != self._expected_txn_id:
            self.order_error_count += 1
            self.error_count += 1
            self.logger.error(
                "TX ORDER ERROR: txn_id=%d (expected %d): missing, "
                "duplicate, or out-of-order transaction in the stream. "
                "Completed-transaction stream must be contiguous.",
                txn.txn_id,
                self._expected_txn_id,
            )
        self._expected_txn_id = txn.txn_id + 1

        # --- 2) Reference-model prediction (CONTRACT.md §8): the golden
        #         expected digest is computed ONLY by block_to_digest.
        #         The observed digest was sampled COMPLETION_MARGIN_CYCLES
        #         after the start edge (monitor, §12); that fixed-cycle
        #         relationship is the input/output contract applied here.
        try:
            expected_bytes = block_to_digest(txn.block_bytes)
        except ValueError as exc:
            # The reference model rejected the 64-byte block (fails
            # canonical SHA-256 one-block padding).  Cannot grade the
            # digest -- report the ungradable transaction.
            self.invalid_block_count += 1
            self.error_count += 1
            self.logger.error(
                "INVALID BLOCK for txn_id=%d: reference model rejected the "
                "padded block (%s). observed digest=0x%064x, expected "
                "digest=UNKNOWN (ungradable). block=0x%0128x cycle=%d",
                txn.txn_id,
                exc,
                int(txn.digest),
                txn.block,
                self._current_cycle(),
            )
            return

        actual_bytes = txn.digest_bytes
        if isinstance(expected_bytes, bytes) and len(expected_bytes) != 32:
            # Defensive: a non-32-byte return from the reference would
            # break .hex() padding assumptions; treat as ungradable.
            self.error_count += 1
            self.logger.error(
                "Reference model returned unexpected length %d for "
                "txn_id=%d; cannot grade.",
                len(expected_bytes),
                txn.txn_id,
            )
            return

        expected_hex = expected_bytes.hex()
        actual_hex = actual_bytes.hex()
        block_hex = f"0x{txn.block:0128x}"
        cycle = self._current_cycle()

        if actual_bytes == expected_bytes:
            self.match_count += 1
            self.logger.info(
                "MATCH txn_id=%d: digest=0x%s at cycle %d "
                "(sampled %d cycles after start edge)",
                txn.txn_id,
                actual_hex,
                cycle,
                txn.latency_cycles,
            )
        else:
            # Primary error report: transaction id, input block, expected
            # digest, actual digest, and cycle of mismatch (plan
            # error_reporting).  For this corrupted RTL a mismatch is the
            # expected catch, so it is counted and reported but does NOT
            # by itself fail the test (env/test stage grades intent).
            self.mismatch_count += 1
            self.logger.error(
                "DIGEST MISMATCH txn_id=%d: "
                "block=%s expected_digest=0x%s actual_digest=0x%s "
                "cycle_of_mismatch=%d "
                "(digest sampled %d cycles after start edge)",
                txn.txn_id,
                block_hex,
                expected_hex,
                actual_hex,
                cycle,
                txn.latency_cycles,
            )

        # --- 3) done is consumed as a data field.  DISC-001 drives it at 1
        #         continuously after reset; the scoreboard flags a non-1
        #         observation as a warning only -- strict done-continuity
        #         is asserted by the assertions stage (CONTRACT.md §8).
        if int(txn.done) != 1:
            self.logger.warning(
                "txn_id=%d: observed done=%d (expected 1 per DISC-001). "
                "Structural done continuity is checked by the assertions "
                "stage, not the scoreboard.",
                txn.txn_id,
                int(txn.done),
            )

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def _current_cycle(self) -> int:
        """Approximate current clock cycle number (cycles since time zero).

        Uses public Cocotb 2.1.0 ``cocotb.utils.get_sim_time``: the
        simulator time in ps divided by the clock period in ps, floored.
        The monitor publishes a transaction immediately after the
        completion rising edge, so this is the cycle at which the sampled
        digest is being graded.  Purely a reporting/attribution value;
        if it cannot be obtained, -1 is returned and the mismatch report
        still carries the txn id, block, and digests.
        """
        try:
            period_ps = int(round(CLK_PERIOD_NS * 1000.0))
            sim_ps = int(get_sim_time("ps"))
        except Exception as exc:  # pragma: no cover - only outside a sim
            self.logger.debug("get_sim_time unavailable: %s", exc)
            return -1
        if period_ps <= 0:
            return sim_ps
        return sim_ps // period_ps

    def get_summary_dict(self) -> dict:
        """Return the scoring counters and derived metrics as a dict."""
        return {
            "txn_count": self.txn_count,
            "match_count": self.match_count,
            "mismatch_count": self.mismatch_count,
            "invalid_block_count": self.invalid_block_count,
            "order_error_count": self.order_error_count,
            "error_count": self.error_count,
            "sample_digest_cycles": SAMPLE_DIGEST_CYCLES,
        }

    def get_summary(self) -> str:
        """Compact single-line scoring summary (for the env/test stage)."""
        s = self.get_summary_dict()
        return (
            f"Sha256Scoreboard[{self.get_name()}]: "
            f"txn_count={s['txn_count']} "
            f"match={s['match_count']} mismatch={s['mismatch_count']} "
            f"invalid_block={s['invalid_block_count']} "
            f"order_error={s['order_error_count']} "
            f"error_count={s['error_count']} "
            f"(digest sampled {s['sample_digest_cycles']} cycles after "
            f"start edge)"
        )

    def convert2string(self) -> str:
        return self.get_summary()