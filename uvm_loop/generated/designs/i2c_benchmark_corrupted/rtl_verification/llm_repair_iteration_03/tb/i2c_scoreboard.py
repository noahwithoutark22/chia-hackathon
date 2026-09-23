"""i2c_master UVM scoreboard for the cocotb + pyuvm bench (scoreboard stage).

Stage-4 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory; it is the authoritative convention record).

``I2CScoreboard`` is a pyuvm ``uvm_scoreboard`` implementing the plan's
``scoreboard_reference_model_strategy`` (transaction scoreboard + stream
checker + control monitor) with the independent Python reference model as
the only oracle:

* the **transaction scoreboard** compares each completed ``I2CTransaction``
  against the reference-model dictionary produced by
  ``write_transaction()`` / ``read_transaction()``,
* the **stream checker** reconstructs the DUT-driven serial stream from the
  open-drain drive controls (``sda_out``/``sda_oe``/``scl_out``/``scl_oe``
  and external pull-up resolution, CONTRACT.md §8) and compares it bit by
  bit, MSB first, against ``address_bits()`` / ``byte_bits()`` /
  ``expected_write_bytes()``,
* the **control monitor** checks the control-signal protocol at the
  completion point: ``done`` is a one-cycle pulse, ``busy`` spans the
  transaction and returns to 0 at IDLE after STOP, ``ack_error`` asserts
  exactly when an expected ACK is missing and stays low otherwise.

ALL-IMPORTANT INTENT RULE (CONTRACT.md §7.1/§14.1/§14.2):
``slave_ack`` and ``read_data`` are TB-side *intent* fields that cannot be
observed from DUT pins; the monitor leaves them at their constructor
defaults and the scoreboard must not derive ACK expectations from monitor
items alone.  This scoreboard therefore runs its own per-cycle pin sampler
(``_sample_pin_trace``) that records the TB-driven ``sda_in`` timeline into
a ring buffer and *recovers the intent from it*: the slave ACK levels and
the read-data byte are read back from the ``sda_in`` pin at the nominal
protocol sample points (the driver's intended advance schedule, ADV_*),
with a majority vote over a +/- CLK_DIV/2 cycle window to absorb the
estimative timing of CONTRACT.md §13.3.  The reference model is then called
with that recovered intent, so the comparison is always TB-intent-consistent
and never fabricates expectations.  If the sampler cannot align its ring to
the monitor's ``_stream_trace`` (or a sample is a tie/unknown), the item is
marked ``intent_ungraded`` and reported -- it is never graded against a
guessed intent.

ALIGNMENT MODEL (completed items):
The monitor publishes an item at the ``done`` 0->1 completion edge with
``latency_cycles`` = acceptance -> completion edges (CONTRACT.md §7.2).  The
scoreboard finds the matching ``done`` 0->1 edge in its own per-cycle ring
(``cc``), sets the acceptance index ``accept_gi = cc - latency_cycles`` and
cross-validates the monitor's ``_stream_trace`` against the ring's DUT-sourced
fields (sda/scl levels + sda_oe/scl_oe/sda_out/scl_out) over the whole trace
window (small offsets tolerated).  Sample points in ring coordinates are
``accept_gi + advance * CLK_DIV`` (a sampled value recorded one edge per
clock cycle), mirroring the driver's advance schedule exactly.

CORRUPTED-RTL SEMANTIC (CONTRACT.md §7.3, catch-report grading):
On the as-shipped RTL no transaction ever completes (``done`` permanently
high -- DIS-15; the divider never advances -- DIS-18/19; ``busy`` never
rises), so the completed-item path above is exercised only on a repaired
variant.  On the as-shipped RTL the monitor publishes ``I2CHungTransaction``
reports on ``hung_ap`` and ``I2CResetEvent`` events on ``reset_ap``; the
scoreboard converts those into structured defect reports
(``discrepancy_reports``) and counters.  ``mismatch_count > 0`` and
``hung_count > 0`` are *catch reports* (the desired negative-test
observations), not by themselves test failures -- the env/test stage (5)
grades the plan's pass criteria from the counters, treating
``order_error_count``/``error_count`` as real contract violations, exactly
like the sha256 sibling (``sha256_scoreboard.py``).

WIRING (performed by the ENV in its connect phase, stage 5):
``scoreboard.connect_monitor(agent.monitor)`` subscribes all three monitor
analysis ports (``ap``, ``hung_ap``, ``reset_ap``) to the matching
scoreboard FIFOs under pyuvm's broadcast model (CONTRACT.md §14.1).  An
``agent`` object (with ``.monitor``) or a raw monitor is accepted.

ConfigDB: reads the shared ``"dut"`` and ``"i2c_pins"`` keys in
``build_phase`` (exact keys from CONTRACT.md §6; both list the scoreboard as
a consumer).  No new ConfigDB keys are introduced.  ``""``-path retrieve
``ConfigDB().get(None, "", key)`` per §6; never ``"*"``.

Cocotb 2.1.0 public APIs only: ``cocotb.start_soon``,
``cocotb.triggers.RisingEdge``, ``cocotb.simtime.get_sim_time``; no
``cocotb.handle.ModifiableObject`` import.  The module keeps a plain-Python
self-check under ``__main__`` (no cocotb/pyuvm required for the pure-helper
checks).
"""

import os
from collections import deque

try:  # cocotb is always present at simulation time; the fallback exists
    # only so the module's pure-Python self-check (__main__) can run in a
    # sandbox that does not have cocotb installed (see i2c_pins.py).
    from cocotb import start_soon
    from cocotb.simtime import get_sim_time
    from cocotb.triggers import RisingEdge

    _COCOTB_AVAILABLE = True
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    start_soon = get_sim_time = RisingEdge = None
    _COCOTB_AVAILABLE = False

try:  # pyuvm classes are required at simulation time; the fallback exists
    # only so the pure-helper self-check can run without the UVM stack.
    from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo

    from i2c_transaction import I2CTransaction

    _PYUVM_AVAILABLE = True
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    ConfigDB = uvm_scoreboard = uvm_tlm_analysis_fifo = None
    I2CTransaction = None
    _PYUVM_AVAILABLE = False

# ---------------------------------------------------------------------------
# i2c_pins re-exports cocotb-dependent handle helpers, so it can only be
# imported where cocotb is installed (simulation).  The fallback constants
# below are i2c_pins' documented defaults and exist solely so the module's
# plain-Python self-check (__main__) can run in a cocotb-less sandbox.
# ---------------------------------------------------------------------------
try:
    from i2c_pins import (
        CLK_DIV_DEFAULT,
        DONE_TIMEOUT_CYCLES,
        I2C_CLK_PERIOD_NS,
        I2CPins,
        KEY_DUT,
        KEY_DUT_PINS,
        START_TIMEOUT_CYCLES,
        _to_int,
    )
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    CLK_DIV_DEFAULT = 4
    DONE_TIMEOUT_CYCLES = 2048
    I2C_CLK_PERIOD_NS = 10.0
    START_TIMEOUT_CYCLES = 64
    I2CPins = None
    KEY_DUT = "dut"
    KEY_DUT_PINS = "i2c_pins"
    _to_int = None

# ---------------------------------------------------------------------------
# The reference model is the ONLY oracle.  It is imported by bare name from
# the verbatim copy in this tb/ directory (byte-identical to
# benchmarks/i2c_benchmark_corrupted/i2c_reference_model.py, md5sum-checked
# at copy time -- see CONTRACT.md §15).  Nothing in the TB reimplements the
# I2C protocol expectations.
# ---------------------------------------------------------------------------
from i2c_reference_model import (
    address_bits as _ref_address_bits,
    byte_bits as _ref_byte_bits,
    expected_write_bytes as _ref_expected_write_bytes,
    make_address_byte as _ref_make_address_byte,
    read_transaction as _ref_read_transaction,
    write_transaction as _ref_write_transaction,
)

# ---------------------------------------------------------------------------
# Intended-protocol advance schedule (CONTRACT.md §13.3, `i2c_driver.py`).
# The driver *imports* nothing from here; this module *binds* to the same
# symbols when the driver is importable (simulation time).  The fallback
# values below are the driver's documented constants, kept for the
# plain-Python self-check:
#
#     advance  0 : acceptance (IDLE -> START_COND, busy rises)
#     advance  1 : START_COND -> SEND_ADDR
#     advance  2..9  : SEND_ADDR, 8 address bits (master drives)
#     advance 10 : ADDR_ACK  (address ACK sample point)
#     advance 11..18 : data phase (SEND_DATA for write / READ_DATA for read)
#     advance 19 : write DATA_ACK sample / read READ_ACK (master NACK)
#     advance 20 : STOP_COND (correct RTL pulses done here)
# ---------------------------------------------------------------------------
try:
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


def _bits_msb(value: int, width: int = 8) -> list[int]:
    """Return ``value`` as ``width`` bits, MSB first (the serial bit order)."""
    return [ (int(value) >> shift) & 1 for shift in range(width - 1, -1, -1) ]


def _expected_addr_bits(slave_addr: int, rw: int) -> list[int]:
    """Expected 8 transmitted address bits, MSB first (reference model)."""
    return list(_ref_address_bits(int(slave_addr), bool(int(rw))))


def _expected_write_stream_bits(slave_addr: int, tx_data: int) -> list[int]:
    """Expected 16 transmitted bits of a write (address byte, then data
    byte, MSB first) -- the reference model's ``expected_write_bytes()``."""
    stream = _ref_expected_write_bytes(int(slave_addr), int(tx_data))
    return _bits_msb(int(stream[0]), 8) + _bits_msb(int(stream[1]), 8)


def _rel_index_for_advance(advance: int, clk_div: int) -> int:
    """Ring-relative index (clock cycles after acceptance) of the nominal
    sample edge for one FSM advance (one advance per CLK_DIV cycles)."""
    return int(advance) * max(1, int(clk_div))


if _PYUVM_AVAILABLE:

    class I2CScoreboard(uvm_scoreboard):
        """In-order reference-model + stream + control scoreboard.

        Consumes three monitor streams (completed items, hung reports,
        reset events) and runs its own per-cycle pin sampler for intent
        recovery and completion-edge alignment.  See the module docstring
        for the full design contract.
        """

        # Ring buffer covering one full long transaction plus the monitor's
        # done-wait budget with generous margin.
        RING_SIZE = max(8192, 4 * DONE_TIMEOUT_CYCLES + 128)

        # Alignment offsets (ring cycles) tried when cross-validating the
        # monitor's _stream_trace against the sampler ring.
        ALIGNMENT_OFFSETS = (0, -1, 1, -2, 2)

        # Above this fraction of mismatching ring-vs-trace frames the item is
        # declared intent_ungraded (never graded against a guessed intent).
        ALIGNMENT_MAX_BAD_FRACTION = 0.02

        # Cap on retained discrepancy reports (bounds memory on long runs).
        MAX_REPORTS = 1000

        def __init__(self, name: str = "i2c_scoreboard", parent=None) -> None:
            super().__init__(name, parent)
            self.dut = None          # shared cocotb top-level handle (§6)
            self.pins = None         # shared I2CPins handle (§6)
            self.clk_div = CLK_DIV_DEFAULT
            self.clk_period_ns = I2C_CLK_PERIOD_NS

            # Analysis FIFOs fed by the env's connect phase.
            self.obs_fifo = None     # completed I2CTransaction items (ap)
            self.hung_fifo = None    # I2CHungTransaction reports (hung_ap)
            self.reset_fifo = None   # I2CResetEvent events (reset_ap)

            # Sampler ring and alignment bookkeeping.
            self._ring = deque(maxlen=self.RING_SIZE)
            self._ring_gi = 0        # global edge counter for ring entries
            self._done_edge_gi = -1  # global index of last consumed done 0->1
            self._last_completed_id = None  # last graded monitor txn_id
            self._sb_tasks = []      # run_phase background tasks

            # Public scoring counters (read by the env/test stage).
            self.txn_count = 0              # completed items consumed
            self.graded_count = 0           # items graded (intent recovered)
            self.intent_ungraded_count = 0  # items not gradable
            self.match_count = 0            # all phase checks hold
            self.mismatch_count = 0         # >=1 phase check failed (catch)
            self.stream_error_count = 0     # serial-stream bit deviations
            self.control_error_count = 0    # control/protocol deviations
            self.ack_error_count = 0        # ACK-phase deviations
            self.order_error_count = 0      # duplicate/out-of-order txn_id
            self.hung_count = 0             # hung-transaction reports
            self.reset_assert_count = 0     # reset assertion events
            self.reset_deassert_count = 0   # reset deassertion events
            self.error_count = 0            # real contract issues
            self.discrepancy_reports = []   # structured defect reports

        # ------------------------------------------------------------------
        # UVM phases
        # ------------------------------------------------------------------
        def build_phase(self) -> None:
            """Fetch the shared ``dut`` / ``i2c_pins`` handles and build the
            three analysis FIFOs (CONTRACT.md §6; exact keys)."""
            super().build_phase()
            self.dut = ConfigDB().get(None, "", KEY_DUT)
            self.pins = ConfigDB().get(None, "", KEY_DUT_PINS)
            if not isinstance(self.pins, I2CPins):
                self.logger.warning(
                    f"ConfigDB['{KEY_DUT_PINS}'] is not an I2CPins: "
                    f"{self.pins!r}"
                )
            if self.pins is None:
                raise RuntimeError(
                    "I2CScoreboard.build_phase: CONTRACT key "
                    f"'{KEY_DUT_PINS}' missing from ConfigDB: the pin "
                    "sampler and intent recovery cannot run."
                )
            self.clk_div = max(
                1, int(os.environ.get("I2C_CLK_DIV", CLK_DIV_DEFAULT))
            )
            self.clk_period_ns = float(
                os.environ.get("I2C_CLK_PERIOD_NS", I2C_CLK_PERIOD_NS)
            )
            self.obs_fifo = uvm_tlm_analysis_fifo("i2c_sb_obs_fifo", self)
            self.hung_fifo = uvm_tlm_analysis_fifo("i2c_sb_hung_fifo", self)
            self.reset_fifo = uvm_tlm_analysis_fifo("i2c_sb_reset_fifo", self)
            self.logger.info(
                f"i2c_scoreboard ready (clk_div={self.clk_div}, "
                f"ring_size={self.RING_SIZE}, "
                f"start_timeout={START_TIMEOUT_CYCLES}, "
                f"done_timeout={DONE_TIMEOUT_CYCLES})"
            )

        def connect_monitor(self, monitor) -> None:
            """Subscribe all three monitor analysis ports to the FIFOs.

            Accepts the agent's monitor (``agent.monitor``) or an agent
            object (resolved via ``.monitor``).  pyuvm 5.0.0:
            ``uvm_analysis_port.connect(export)`` appends the FIFO's
            ``analysis_export`` to the port's subscribers (CONTRACT.md
            §14.1 broadcast model).
            """
            src = getattr(monitor, "monitor", monitor)
            if src is None:
                raise ValueError("connect_monitor: no monitor/agent given")
            for name, port_name, fifo in (
                ("ap", "ap", self.obs_fifo),
                ("hung_ap", "hung_ap", self.hung_fifo),
                ("reset_ap", "reset_ap", self.reset_fifo),
            ):  # noqa: B007 - name kept for clarity
                port = getattr(src, port_name, None)
                if port is None:
                    raise ValueError(
                        f"connect_monitor: source has no '{port_name}' "
                        "analysis port"
                    )
                port.connect(fifo.analysis_export)
            self.logger.info(
                "connected monitor ap/hung_ap/reset_ap -> scoreboard FIFOs"
            )

        async def run_phase(self) -> None:
            """Run the four parallel consumers/checkers.

            All four are started with public Cocotb 2.1.0
            ``cocotb.start_soon``; ``run_phase`` awaits the primary consumer
            (completed items), which never returns during the simulation.
            The sibling tasks (hung, reset, pin sampler) run as background
            coroutines; pyuvm terminates all phase tasks when the test ends
            (family pattern, CONTRACT.md §15).
            """
            tasks = [
                start_soon(self._consume_completed()),
                start_soon(self._consume_hung()),
                start_soon(self._consume_reset()),
                start_soon(self._sample_pin_trace()),
            ]
            self._sb_tasks = tasks
            await tasks[0]

        # ------------------------------------------------------------------
        # Consumer coroutines (run_phase background tasks)
        # ------------------------------------------------------------------
        async def _consume_completed(self) -> None:
            """Consume completed ``I2CTransaction`` items in order."""
            while True:
                item = await self.obs_fifo.get_peek_export.get()
                self.txn_count += 1
                await self._score_completed(item)

        async def _consume_hung(self) -> None:
            """Consume ``I2CHungTransaction`` reports (never graded as pass)."""
            while True:
                item = await self.hung_fifo.get_peek_export.get()
                self._report_hung(item)

        async def _consume_reset(self) -> None:
            """Consume ``I2CResetEvent`` notifications (control events)."""
            while True:
                event = await self.reset_fifo.get_peek_export.get()
                kind = str(getattr(event, "kind", "?"))
                if kind == "asserted":
                    self.reset_assert_count += 1
                elif kind == "deasserted":
                    self.reset_deassert_count += 1
                else:
                    self.logger.warning(
                        f"reset event with unknown kind: {event}"
                    )
                self.logger.info(f"reset event: {event}")

        async def _sample_pin_trace(self) -> None:
            """Record one per-cycle pin observation into the ring buffer.

            Runs on every rising clock edge for the whole simulation.  The
            ring feeds completion-edge alignment, intent recovery, and the
            hung-report bus symptoms.  Only reads pins (passive).
            """
            if self.pins is None:
                self.logger.error(
                    "pin sampler disabled: no I2CPins handle in ConfigDB"
                )
                return
            while True:
                await RisingEdge(self.pins.clk)
                self._ring.append(
                    {
                        "gi": self._ring_gi,
                        "sda_in": self.pins.read_sda_in(),
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
                self._ring_gi += 1

        # ------------------------------------------------------------------
        # Completed-item scoring
        # ------------------------------------------------------------------
        async def _score_completed(self, item) -> None:
            """Grade one completed item against the reference model.

            Order integrity is checked first (CONTRACT.md §14.3: monitor
            ids are monotonic; gaps are attributable to hung reports and
            reset-dropped items, so only duplicates/reorders are errors).
            Then the done 0->1 completion edge is located in the ring
            (retrying a few clock edges to let the sampler catch up),
            alignment is cross-validated against ``item._stream_trace``, the
            slave intent is recovered from ``sda_in``, and the reference
            model is called with it.
            """
            if not isinstance(item, I2CTransaction):
                self.error_count += 1
                self.logger.error(
                    "Scoreboard received a non-I2CTransaction object on "
                    "the completed stream: %r (ignored for grading, counted "
                    "as an error)",
                    item,
                )
                return
            if getattr(item, "hung", False):
                # Defensive: hung items belong on hung_ap.  If one ever
                # lands here, grade it as a hung report instead.
                self._report_hung(item)
                return
            self._check_order(item)

            cc = self._find_new_done_edge()
            for _retry in range(3):
                if cc is not None:
                    break
                if self.pins is not None:
                    await RisingEdge(self.pins.clk)
                cc = self._find_new_done_edge()
            if cc is None:
                self._mark_ungraded(
                    item,
                    "could not locate the done 0->1 completion edge in the "
                    "sampler ring (sampler/monitor mismatch?); item is not "
                    "graded",
                )
                return
            self._done_edge_gi = cc
            self._grade_completed(item, cc)

        def _check_order(self, item) -> None:
            """Enforce in-order, contiguous completed-stream ids with the
            documented gap semantics (CONTRACT.md §14.3)."""
            tid = int(item.txn_id)
            if self._last_completed_id is None:
                self._last_completed_id = tid
                return
            if tid <= self._last_completed_id:
                self.order_error_count += 1
                self.error_count += 1
                self.logger.error(
                    "TX ORDER ERROR: txn_id=%d duplicated or out-of-order "
                    "(last completed txn_id=%d).  The completed-transaction "
                    "stream must be strictly increasing.",
                    tid,
                    self._last_completed_id,
                )
            elif tid - self._last_completed_id > 1:
                # Not an error: monitor ids are also consumed by hung
                # reports and by reset-dropped items (CONTRACT.md §14.3).
                self.logger.debug(
                    "txn_id gap %d..%d in completed stream (ids consumed by "
                    "hung reports / reset-dropped items)",
                    self._last_completed_id + 1,
                    tid - 1,
                )
            self._last_completed_id = tid

        def _grade_completed(self, item, cc: int) -> None:
            """Recover intent, call the reference model, and run the three
            plan checkers (transaction / stream / control)."""
            latency = max(0, int(getattr(item, "latency_cycles", 0) or 0))
            accept_gi = cc - latency
            if accept_gi < 0:
                self._mark_ungraded(
                    item,
                    f"completion edge (gi={cc}) precedes acceptance "
                    f"(latency_cycles={latency}); ring history too short",
                )
                return

            off = self._best_alignment_offset(item, accept_gi)
            if off is None:
                self._mark_ungraded(
                    item,
                    "sampler ring could not be aligned to the monitor's "
                    "_stream_trace (DUT-sourced field cross-check failed); "
                    "item is not graded against a guessed intent",
                )
                return
            accept_gi += off
            if off != 0:
                self.logger.debug(
                    f"txn_id={item.txn_id}: ring/trace alignment accepted at "
                    f"offset {off} cycle(s)"
                )

            # --- Intent recovery from the TB slave's sda_in timeline -----
            cdiv = self.clk_div
            addr_ack = self._sample_majority(
                accept_gi, _rel_index_for_advance(ADV_ADDR_ACK, cdiv), "sda_in"
            )
            if addr_ack is None:
                self._mark_ungraded(
                    item, "address-ACK sda_in sample is a tie/unknown"
                )
                return
            if item.is_read:
                read_data = 0
                for i in range(8):
                    bit = self._sample_majority(
                        accept_gi,
                        _rel_index_for_advance(ADV_DATA_PHASE_START + i, cdiv),
                        "sda_in",
                    )
                    if bit is None:
                        self._mark_ungraded(
                            item, f"read-data bit {i} sda_in is a tie/unknown"
                        )
                        return
                    read_data = (read_data << 1) | bit
                slave_ack = 1 if addr_ack == 0 else 0
                read_data_intent = read_data
            else:
                data_ack = self._sample_majority(
                    accept_gi, _rel_index_for_advance(ADV_DATA_ACK, cdiv), "sda_in"
                )
                if data_ack is None:
                    self._mark_ungraded(
                        item, "write-data-ACK sda_in sample is a tie/unknown"
                    )
                    return
                slave_ack = 1 if (addr_ack == 0 and data_ack == 0) else 0
                read_data_intent = 0

            # --- Reference-model prediction (the ONLY oracle) ------------
            try:
                if item.is_read:
                    expected = _ref_read_transaction(
                        item.slave_addr, read_data_intent, slave_ack=slave_ack
                    )
                else:
                    expected = _ref_write_transaction(
                        item.slave_addr, item.tx_data, slave_ack=slave_ack
                    )
            except ValueError as exc:  # defensive: masked fields fit ranges
                self.error_count += 1
                self._append_report(
                    {
                        "txn_id": int(item.txn_id),
                        "kind": "reference_rejected",
                        "detail": str(exc),
                    }
                )
                self.logger.error(
                    f"reference model rejected txn_id={item.txn_id}: {exc}"
                )
                return

            self.graded_count += 1

            # --- Per-phase grading ---------------------------------------
            view = self._observed_ref_view(
                item, read_data_intent if item.is_read else None
            )
            ref_diffs = self._reference_dict_diff(expected, view)
            errors: list[tuple[str, str]] = []
            self._phase_errors_from_ref_diff(ref_diffs, errors)
            self._check_stream(item, accept_gi, errors)
            self._check_control(item, accept_gi, cc, errors)

            if errors:
                self.mismatch_count += 1
                diff_repr = "; ".join(
                    f"{k}: expected {exp!r}, observed {obs!r}"
                    for k, (exp, obs) in ref_diffs.items()
                ) or "(no reference-dict diff; stream/control deviations)"
                self.logger.error(
                    f"MISMATCH txn_id={item.txn_id} "
                    f"phases=[{', '.join(p for p, _d in errors)}] "
                    f"cycle={self._current_cycle()} "
                    f"ref_dict_diff={{{diff_repr}}}"
                )
                for phase, detail in errors:
                    self.logger.error(f"    [{phase}] {detail}")
                self._append_report(
                    {
                        "txn_id": int(item.txn_id),
                        "kind": "mismatch",
                        "phase": ", ".join(p for p, _d in errors),
                        "detail": "; ".join(f"[{p}] {d}" for p, d in errors),
                        "ref_dict": dict(expected),
                    }
                )
            else:
                self.match_count += 1
                self.logger.info(
                    f"MATCH txn_id={item.txn_id}: reference prediction, "
                    "serial stream, and control checks all hold "
                    f"(latency_cycles={latency})"
                )

        # ------------------------------------------------------------------
        # Ring / alignment helpers
        # ------------------------------------------------------------------
        def _ring_get(self, gi: int) -> dict | None:
            """Return the ring entry with global index ``gi`` or None."""
            for e in reversed(self._ring):
                if e["gi"] == gi:
                    return e
                if e["gi"] < gi:
                    return None  # exact index already evicted from history
            return None

        def _find_new_done_edge(self) -> int | None:
            """Return the global index of the newest unconsumed done 0->1
            edge in the ring, or None."""
            for e in reversed(self._ring):
                gi = e["gi"]
                if gi <= self._done_edge_gi:
                    return None
                prev = self._ring_get(gi - 1)
                if prev is not None and e["done"] == 1 and prev["done"] == 0:
                    return gi
            return None

        def _sample_majority(
            self, accept_gi: int, rel: int, field: str, window: int | None = None
        ) -> int | None:
            """Majority vote of ring ``field`` over [rel-window, rel+window]
            after ``accept_gi``; window defaults to CLK_DIV // 2."""
            half = (self.clk_div // 2) if window is None else int(window)
            votes = []
            for gi in range(accept_gi + rel - half, accept_gi + rel + half + 1):
                e = self._ring_get(gi)
                if e is None:
                    continue
                v = e.get(field)
                if v in (0, 1):
                    votes.append(v)
            return _majority_bit(votes)

        def _sample_control(self, accept_gi: int, rel: int, field: str) -> int | None:
            """Exact (window-less) ring read at one relative index."""
            e = self._ring_get(accept_gi + rel)
            if e is None:
                return None
            v = e.get(field)
            return v if v in (0, 1) else None

        def _alignment_bad_fraction(self, item, accept_gi: int) -> float:
            """Fraction of _stream_trace frames mismatching the ring.

            Compares the six DUT-sourced fields the monitor traced
            (``sda``/``scl`` resolved levels and the ``sda_out``/``sda_oe``/
            ``scl_out``/``scl_oe`` controls) against the ring entries at the
            same clock edges (trace[t] <-> ring[accept_gi + 1 + t]).
            """
            trace = getattr(item, "_stream_trace", None) or []
            if not trace:
                return 0.0
            total = 0
            bad = 0
            limit = min(len(trace), self.RING_SIZE - 16)
            for t in range(limit):
                e = self._ring_get(accept_gi + 1 + t)
                total += 1
                if e is None:
                    bad += 1  # missing ring history frames as a mismatch
                    continue
                tr = trace[t]
                pairs = (
                    (tr.get("sda"), e.get("sda_level")),
                    (tr.get("scl"), e.get("scl_level")),
                    (tr.get("sda_out"), e.get("sda_out")),
                    (tr.get("sda_oe"), e.get("sda_oe")),
                    (tr.get("scl_out"), e.get("scl_out")),
                    (tr.get("scl_oe"), e.get("scl_oe")),
                )
                if any(a != b for a, b in pairs):
                    bad += 1
            if total == 0:
                return 0.0
            return bad / total

        def _best_alignment_offset(self, item, accept_gi: int) -> int | None:
            """Choose the alignment offset with the lowest frame-mismatch
            fraction; None if even the best exceeds the tolerance."""
            best_off = 0
            best_bad = 1.1
            for off in self.ALIGNMENT_OFFSETS:
                bad = self._alignment_bad_fraction(item, accept_gi + off)
                if bad < best_bad - 1e-9:
                    best_bad = bad
                    best_off = off
            if best_bad > self.ALIGNMENT_MAX_BAD_FRACTION:
                return None
            return best_off

        # ------------------------------------------------------------------
        # Plan checkers (transaction / stream / control)
        # ------------------------------------------------------------------
        def _observed_ref_view(self, item, read_data_intent: int | None = None) -> dict:
            """Observed-attribute view keyed like the reference dict."""
            view = {
                "start": int(item.start),
                "address": int(item.slave_addr),
                "address_byte": int(item.address_byte),
                "rw": int(item.rw),
                "tx_data": int(item.tx_data),
                "expected_ack_error": int(item.ack_error),
                "rx_data": int(item.rx_data),
                "done": int(item.done),
                "busy": int(item.busy),
            }
            if read_data_intent is not None:
                view["slave_data"] = int(read_data_intent)
            return view

        def _reference_dict_diff(self, expected: dict, view: dict) -> dict:
            """Return {key: (expected, observed)} for reference-dict keys
            that differ from the observed view (bool-vs-int normalized)."""
            diffs: dict[str, tuple] = {}

            def _norm(v) -> int:
                if isinstance(v, bool):
                    return int(v)
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return -1

            for key in ("start", "address", "address_byte", "rw", "tx_data",
                        "expected_ack_error"):
                if key in expected and key in view:
                    if _norm(expected[key]) != _norm(view[key]):
                        diffs[key] = (expected[key], view[key])
            if "expected_rx_data" in expected:
                if _norm(expected["expected_rx_data"]) != _norm(view.get("rx_data")):
                    diffs["rx_data"] = (expected["expected_rx_data"],
                                        view.get("rx_data"))
            return diffs

        def _phase_errors_from_ref_diff(
            self, diffs: dict, errors: list[tuple[str, str]]
        ) -> None:
            """Turn reference-dict diffs into plan phase-tagged errors."""
            for key, (exp, obs) in diffs.items():
                if key == "expected_ack_error":
                    self.ack_error_count += 1
                    errors.append(
                        ("ACK", f"ack_error expected {exp}, observed {obs}")
                    )
                elif key == "address_byte":
                    self.stream_error_count += 1
                    errors.append(
                        (
                            "address",
                            f"address_byte expected 0x{exp:02x}, "
                            f"observed 0x{obs:02x}",
                        )
                    )
                elif key == "rx_data":
                    self.stream_error_count += 1
                    errors.append(
                        (
                            "read-data",
                            f"rx_data expected 0x{exp:02x}, observed 0x{obs:02x}",
                        )
                    )
                else:
                    self.control_error_count += 1
                    errors.append(
                        ("control", f"{key} expected {exp}, observed {obs}")
                    )

        def _check_stream(self, item, accept_gi: int, errors: list) -> None:
            """Reconstruct the DUT-driven serial stream and compare it bit by
            bit, MSB first, against the reference model (plan stream_checker).
            """
            cdiv = self.clk_div
            # Address byte (advances 2..9; index (2+j)*cdiv after acceptance).
            ref_addr = _expected_addr_bits(item.slave_addr, item.rw)
            for j, exp in enumerate(ref_addr):
                obs = self._sample_majority(
                    accept_gi, _rel_index_for_advance(2 + j, cdiv), "sda_level"
                )
                if obs != exp:
                    self.stream_error_count += 1
                    errors.append(
                        (
                            "address",
                            f"address bit {j} (MSB-first) expected {exp}, "
                            f"observed {obs}",
                        )
                    )
            if item.is_read:
                # During READ_DATA the master must release SDA (slave drives);
                # a still-asserted sda_oe signals a drive-control deviation.
                for j in range(8):
                    oe = self._sample_majority(
                        accept_gi,
                        _rel_index_for_advance(ADV_DATA_PHASE_START + j, cdiv),
                        "sda_oe",
                    )
                    if oe == 1:
                        self.stream_error_count += 1
                        errors.append(
                            (
                                "read-data",
                                f"master keeps sda_oe asserted during "
                                f"READ_DATA bit {j} (expected released so the "
                                "slave can drive the line)",
                            )
                        )
                        break
            else:
                # Write data byte (advances 11..18), SEND_DATA.
                for j, exp in enumerate(_bits_msb(int(item.tx_data), 8)):
                    obs = self._sample_majority(
                        accept_gi,
                        _rel_index_for_advance(ADV_DATA_PHASE_START + j, cdiv),
                        "sda_level",
                    )
                    if obs != exp:
                        self.stream_error_count += 1
                        errors.append(
                            (
                                "write-data",
                                f"data bit {j} (MSB-first) expected {exp}, "
                                f"observed {obs}",
                            )
                        )

        def _check_control(self, item, accept_gi: int, cc: int, errors: list) -> None:
            """Control-monitor checks at/around the completion point (plan
            control_monitor): done pulse shape, busy span/return-to-idle,
            ack_error-low-in-idle, and the STOP condition."""
            cdiv = self.clk_div
            # done is a one-cycle pulse; observed via the located edge.
            if int(item.done) != 1:
                self.control_error_count += 1
                errors.append(
                    ("STOP", f"done expected 1 at the completion pulse, "
                             f"observed {item.done}")
                )
            nxt = self._ring_get(cc + 1)
            if nxt is not None and nxt["done"] != 0:
                self.control_error_count += 1
                errors.append(
                    (
                        "STOP",
                        "done is not a one-cycle pulse (still high after the "
                        "completion edge)",
                    )
                )
            # busy spans the transaction (sample mid-address and mid-data).
            for mid_advance in (5, 12):
                busy_mid = self._sample_control(
                    accept_gi, _rel_index_for_advance(mid_advance, cdiv), "busy"
                )
                if busy_mid != 1:
                    self.control_error_count += 1
                    errors.append(
                        (
                            "control",
                            f"busy expected 1 at advance {mid_advance} (busy "
                            f"spans the transaction), observed {busy_mid}",
                        )
                    )
            # busy returns to 0 at completion (IDLE after STOP).
            if int(item.busy) != 0:
                self.control_error_count += 1
                errors.append(
                    (
                        "STOP",
                        f"busy expected 0 at completion (IDLE after STOP), "
                        f"observed {item.busy}",
                    )
                )
            # ack_error stays low in IDLE before acceptance (DIS-11 catch).
            ack_idle = True
            for k in range(1, min(8, accept_gi) + 1):
                e = self._ring_get(accept_gi - k)
                if e is not None and e["ack_error"] != 0:
                    ack_idle = False
                    break
            if not ack_idle:
                self.control_error_count += 1
                errors.append(
                    (
                        "control",
                        "ack_error asserted during the idle window before "
                        "acceptance (expected 0 in IDLE)",
                    )
                )
            # STOP condition: SDA 0->1 while SCL high near the completion edge.
            stop_ok = False
            for gi in range(cc - 8, cc + 3):
                e = self._ring_get(gi)
                prev = self._ring_get(gi - 1)
                if (
                    e is not None
                    and prev is not None
                    and e["scl_level"] == 1
                    and prev["sda_level"] == 0
                    and e["sda_level"] == 1
                ):
                    stop_ok = True
                    break
            if not stop_ok:
                self.control_error_count += 1
                errors.append(
                    (
                        "STOP",
                        "no SDA 0->1 while SCL high (STOP condition) "
                        "observed in the completion window",
                    )
                )

        # ------------------------------------------------------------------
        # Hung / ungraded / reporting helpers
        # ------------------------------------------------------------------
        def _report_hung(self, item) -> None:
            """Convert an I2CHungTransaction into a structured defect report.

            Never graded as a pass (CONTRACT.md §7.3/§14.1): a bounded wait
            elapsed (``hung_stage`` = start-acceptance / done-pulse /
            completion-sample).  The report carries the observed outputs at
            expiry plus a short bus-symptom summary from the sampler ring.
            """
            self.hung_count += 1
            self.error_count += 1
            stage = str(getattr(item, "hung_stage", "unknown"))
            tid = int(getattr(item, "txn_id", -1))
            latency = getattr(item, "latency_cycles", None)
            outs = {
                "rx_data": getattr(item, "rx_data", None),
                "done": getattr(item, "done", None),
                "busy": getattr(item, "busy", None),
                "ack_error": getattr(item, "ack_error", None),
                "sda_oe": getattr(item, "sda_oe", None),
                "scl_oe": getattr(item, "scl_oe", None),
            }
            symptom = self._recent_bus_symptom()
            self.logger.error(
                f"HUNG TRANSACTION txn_id={tid} stage={stage} "
                f"latency_cycles={latency} outs_at_expiry={outs} "
                f"bus_symptom={symptom} item={item}"
            )
            self._append_report(
                {
                    "txn_id": tid,
                    "kind": "hung",
                    "hung_stage": stage,
                    "latency_cycles": latency,
                    "outs_at_expiry": outs,
                    "bus_symptom": symptom,
                }
            )

        def _recent_bus_symptom(self) -> str:
            """Compact textual bus-activity summary over the last ~64 ring
            entries (drives the hung-report diagnosis on this DUT)."""
            recent = list(self._ring)[-64:]
            if not recent:
                return "no ring history yet"
            n = len(recent)
            done_high = sum(int(e["done"]) for e in recent)
            busy_high = sum(int(e["busy"]) for e in recent)
            ack_high = sum(int(e["ack_error"]) for e in recent)
            done_edges = sum(
                1
                for i in range(1, n)
                if recent[i]["done"] == 1 and recent[i - 1]["done"] == 0
            )
            if done_high == n:
                done_desc = "done permanently high (no 0->1 edge)"
            elif done_high == 0:
                done_desc = "done all low"
            else:
                done_desc = f"done mixed ({done_high}/{n} high, {done_edges} edges)"
            return (
                f"last-{n}-cycle window: done_1={done_high} busy_1={busy_high} "
                f"ack_error_1={ack_high} -> {done_desc}; "
                f"{'busy idle-flat (never rose)' if busy_high == 0 else 'busy saw activity'}"
            )

        def _mark_ungraded(self, item, reason: str) -> None:
            """Count and report an item whose intent could not be recovered;
            it is never graded against a guessed intent."""
            self.intent_ungraded_count += 1
            self.error_count += 1
            tid = int(getattr(item, "txn_id", -1))
            self.logger.error(
                f"INTENT UNGRADED txn_id={tid}: {reason}"
            )
            self._append_report(
                {"txn_id": tid, "kind": "intent_ungraded", "detail": reason}
            )

        def _append_report(self, report: dict) -> None:
            """Append one structured defect report (bounded list)."""
            if len(self.discrepancy_reports) < self.MAX_REPORTS:
                self.discrepancy_reports.append(report)

        def _current_cycle(self) -> int:
            """Approximate current clock cycle (sim time / clock period)."""
            try:
                period_ps = int(round(float(self.clk_period_ns) * 1000.0))
                sim_ps = int(get_sim_time("ps"))
            except Exception as exc:  # pragma: no cover - only outside a sim
                self.logger.debug("get_sim_time unavailable: %s", exc)
                return -1
            if period_ps <= 0:
                return sim_ps
            return sim_ps // period_ps

        # ------------------------------------------------------------------
        # Summary API (read by the env/test stage)
        # ------------------------------------------------------------------
        def get_summary_dict(self) -> dict:
            """Return the scoring counters and derived metrics as a dict."""
            return {
                "txn_count": self.txn_count,
                "graded_count": self.graded_count,
                "intent_ungraded_count": self.intent_ungraded_count,
                "match_count": self.match_count,
                "mismatch_count": self.mismatch_count,
                "stream_error_count": self.stream_error_count,
                "control_error_count": self.control_error_count,
                "ack_error_count": self.ack_error_count,
                "order_error_count": self.order_error_count,
                "hung_count": self.hung_count,
                "reset_assert_count": self.reset_assert_count,
                "reset_deassert_count": self.reset_deassert_count,
                "error_count": self.error_count,
                "discrepancy_report_count": len(self.discrepancy_reports),
                "clk_div": self.clk_div,
            }

        def get_summary(self) -> str:
            """Compact single-line scoring summary (for the env/test stage)."""
            s = self.get_summary_dict()
            return (
                f"I2CScoreboard[{self.get_name()}]: "
                f"txn_count={s['txn_count']} "
                f"graded={s['graded_count']} match={s['match_count']} "
                f"mismatch={s['mismatch_count']} "
                f"intent_ungraded={s['intent_ungraded_count']} "
                f"stream_err={s['stream_error_count']} "
                f"control_err={s['control_error_count']} "
                f"ack_err={s['ack_error_count']} "
                f"order_err={s['order_error_count']} hung={s['hung_count']} "
                f"reset_assert={s['reset_assert_count']} "
                f"reset_deassert={s['reset_deassert_count']} "
                f"error_count={s['error_count']} "
                f"reports={s['discrepancy_report_count']}"
            )

        def convert2string(self) -> str:
            return self.get_summary()


# ---------------------------------------------------------------------------
# Plain-Python self-checks (no simulator required).  The pure-helper checks
# run in any sandbox; the class-logic checks additionally need pyuvm
# (available on the simulation worker's PYTHONPATH).
# ---------------------------------------------------------------------------
def _self_test_pure_helpers() -> None:
    """Check the pure helper functions and the reference-model bindings."""
    # Majority voting.
    assert _majority_bit([]) is None
    assert _majority_bit([0, 0, 1]) == 0
    assert _majority_bit([1, 1, 0]) == 1
    assert _majority_bit([0, 1]) is None
    assert _majority_bit([0, 1, 1, 0, 0]) == 0
    assert _majority_bit([None, None, 1, 1, 0]) == 1
    assert _majority_bit([None, None]) is None

    # Serial bit order (MSB first).
    assert _bits_msb(0x50, 8) == [0, 1, 0, 1, 0, 0, 0, 0]
    assert _bits_msb(0x00, 8) == [0] * 8
    assert _bits_msb(0xFF, 8) == [1] * 8

    # Reference-model bindings produce the documented address/stream bits.
    assert _expected_addr_bits(0x50, 0) == [1, 0, 1, 0, 0, 0, 0, 0]
    assert _expected_addr_bits(0x50, 1) == [1, 0, 1, 0, 0, 0, 0, 1]
    assert _expected_addr_bits(0x00, 0) == [0] * 8
    assert _expected_addr_bits(0x7F, 1) == [1] * 8
    assert _expected_write_stream_bits(0x50, 0xA5) == (
        _bits_msb(0x50 << 1, 8) + _bits_msb(0xA5, 8)
    )

    # Ring-relative advance indexing (advance * CLK_DIV).
    assert _rel_index_for_advance(0, 4) == 0
    assert _rel_index_for_advance(10, 4) == 40
    assert _rel_index_for_advance(20, 16) == 320
    assert _rel_index_for_advance(2, 1) == 2

    # Reference-model dictionary sanity (the oracle contract, CONTRACT.md §8).
    w = _ref_write_transaction(0x50, 0xA5, slave_ack=True)
    assert w["start"] is True and w["stop"] is True
    assert w["address_byte"] == 0xA0
    assert w["expected_slave_acks"] == 2
    assert w["expected_ack_error"] is False
    w_nack = _ref_write_transaction(0x50, 0xA5, slave_ack=False)
    assert w_nack["expected_ack_error"] is True
    r = _ref_read_transaction(0x50, 0x3C, slave_ack=True)
    assert r["address_byte"] == 0xA1
    assert r["expected_rx_data"] == 0x3C
    assert r["master_final_ack"] is False
    assert r["expected_slave_acks"] == 1

    # ADV advance schedule matches the driver's documented constants.
    assert (ADV_ACCEPT, ADV_ADDR_ACK, ADV_DATA_PHASE_START, ADV_DATA_ACK,
            ADV_STOP) == (0, 10, 11, 19, 20)

    print("i2c_scoreboard: pure-helper self-check OK")


def _self_test_class_logic() -> None:
    """Check the ring/alignment/grading helpers on a synthetic timeline.
    Requires pyuvm (it instantiates I2CScoreboard)."""
    if not _PYUVM_AVAILABLE:
        print("i2c_scoreboard: class-logic self-check SKIPPED (no pyuvm)")
        return
    sb = I2CScoreboard("sb_synth")
    sb.clk_div = 4

    # Build a synthetic ring: 4 idle cycles, acceptance at gi=4, one cycle
    # of "busy active" work, done 0->1 pulse at gi=10, idle after.
    # (Every entry carries the full field set the sampler records so the
    # alignment helper sees produced values only.)
    def _entry(gi, done=0, busy=0, **rest):
        e = {
            "gi": gi, "sda_in": 1, "sda_out": 1, "sda_oe": 0,
            "scl_out": 1, "scl_oe": 0, "sda_level": 1, "scl_level": 1,
            "done": done, "busy": busy, "ack_error": 0, "rx_data": 0,
            "rst": 1,
        }
        e.update(rest)
        return e

    entries = []
    gi = 0
    for _ in range(4):  # idle (gi 0..3)
        entries.append(_entry(gi))
        gi += 1
    entries.append(_entry(4, busy=1))                                   # acceptance
    for _ in range(5):                                                  # active (5..9)
        entries.append(_entry(gi, busy=1))
        gi += 1
    entries.append(_entry(10, done=1, busy=0))                          # pulse
    entries.append(_entry(11, done=0, busy=0))
    for e in entries:
        sb._ring.append(e)

    # Newest unconsumed done edge is gi=10.
    assert sb._find_new_done_edge() == 10
    sb._done_edge_gi = 10
    assert sb._find_new_done_edge() is None  # consumed now

    # Ring lookup by global index, oldest eviction semantics.
    assert sb._ring_get(10)["done"] == 1
    assert sb._ring_get(0)["done"] == 0
    assert sb._ring_get(-5) is None

    # Alignment: a matching trace (fields equal at ring[accept_gi+1+t]).
    # The active entries (gi 5..10) carry the alternating pattern
    # 0,1,0,1,0,1 in sda_level/sda_out/sda_in with sda_oe=1 (master driving);
    # idle entries are released high (sda_level=1, sda_oe=0).
    def _with_bus(gi, pattern, busy=1):
        e = _entry(gi, busy=busy, done=1 if gi == 10 else 0)
        e.update(
            {
                "sda_in": pattern, "sda_out": pattern, "sda_oe": 1,
                "sda_level": pattern,
            }
        )
        return e

    for i, gi in enumerate(range(5, 11)):
        sb._ring[gi] = _with_bus(gi, i % 2)

    class _FakeItem:
        pass

    item = _FakeItem()
    trace_pat = [i % 2 for i in range(6)]
    item._stream_trace = [
        {"sda": p, "scl": 1, "sda_out": p, "sda_oe": 1, "scl_out": 1,
         "scl_oe": 0}
        for p in trace_pat
    ]
    # done edge at gi=10, latency 6 -> acceptance gi=4; trace[t] <-> gi=5+t.
    bad = sb._alignment_bad_fraction(item, 4)
    assert bad == 0.0, bad
    # Wrong acceptance index mismatches a good fraction of frames.
    bad_wrong = sb._alignment_bad_fraction(item, 6)
    assert bad_wrong > 0.3, bad_wrong
    # An index whose frames all fell out of ring history is not "aligned".
    bad_gone = sb._alignment_bad_fraction(item, 11)
    assert bad_gone == 1.0, bad_gone
    assert sb._best_alignment_offset(item, 4) == 0

    # Reference-dict diff normalization (bool vs int).
    expected = _ref_write_transaction(0x50, 0xA5, slave_ack=True)
    view_ok = {
        "start": 1, "address": 0x50, "address_byte": 0xA0, "rw": 0,
        "tx_data": 0xA5, "expected_ack_error": 0, "rx_data": 0,
    }
    assert sb._reference_dict_diff(expected, view_ok) == {}
    view_bad = dict(view_ok)
    view_bad["expected_ack_error"] = 1
    diffs = sb._reference_dict_diff(expected, view_bad)
    assert "expected_ack_error" in diffs, diffs

    # Read-transaction diff on rx_data.
    expected_r = _ref_read_transaction(0x50, 0x3C, slave_ack=True)
    view_r = {
        "start": 1, "address": 0x50, "address_byte": 0xA1, "rw": 1,
        "tx_data": 0, "expected_ack_error": 0, "rx_data": 0x3C,
    }
    assert sb._reference_dict_diff(expected_r, view_r) == {}
    view_r_bad = dict(view_r)
    view_r_bad["rx_data"] = 0x3D
    assert "rx_data" in sb._reference_dict_diff(expected_r, view_r_bad)

    print("i2c_scoreboard: class-logic self-check OK")


if __name__ == "__main__":
    _self_test_pure_helpers()
    _self_test_class_logic()