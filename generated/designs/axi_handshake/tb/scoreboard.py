"""AxiHandshake scoreboard (pyuvm ``uvm_scoreboard``) + reference-model integration.

Role / strategy (``scoreboard_reference_model_strategy``):
    * ``inline_reference_model``: the Python oracle ``ref_model``
      (CONTRACT.md §6 — ``benchmarks/axi_handshake/ref_model.py``, copied
      verbatim into this tb directory) is used directly.  For every cycle's
      transaction the scoreboard calls
      ``ref_model.step(s_valid, s_data, m_ready)`` with the *sampled* DUT
      inputs carried by the transaction and compares the returned
      ``(s_ready, m_valid, m_data)`` against the *sampled* DUT outputs in the
      same transaction.
    * ``reset_synchronization``: ``ref_model.reset()`` is invoked while the
      active-low reset is asserted and again on the deassertion edge, so the
      oracle and the DUT always begin every post-reset window from the same
      empty state (``s_ready=1, m_valid=0, m_data=0``).

Timing / alignment (CONTRACT.md §2, §6, §7):
    All three DUT outputs are **combinational** (``assign`` statements in the
    RTL), i.e. latency 0.  The monitor samples every pin in the read-only
    region after the rising edge, so a transaction carries the inputs
    presented on that edge *and* the outputs settled for that same edge.
    ``ref_model.step()`` likewise computes its outputs from the single-entry
    queue state *before* this cycle's transfer resolution, i.e. for the same
    cycle as its inputs.  The comparison is therefore a direct single-cycle
    check with no pipeline assumption.

Reset:
    Reset is not a transaction field, so the scoreboard observes ``dut.rst_n``
    directly.  ``get()`` and the monitor's ``put`` both occur in the read-only
    region of the same timestep (no simulation time advances between them), so
    ``dut.rst_n`` read immediately after ``get()`` is the post-edge value for
    the cycle that produced the transaction (active-low, CONTRACT.md §2).

Watchdog:
    An always-running coroutine (``cocotb.start_soon``) fails the test if the
    monitor → scoreboard pipeline goes idle for a bounded number of clock
    cycles, which can only happen if the environment is hung.  The
    authoritative overall test-duration watchdog (bounded ``with_timeout``
    around the test body) is applied at the test / top stage.

ConfigDB keys consumed (CONTRACT.md §5):
    - ``"dut"``            — cocotb SimHandleBase
    - ``"dut_helper"``     — DutHelper instance
    - ``"ref_model"``      — module reference (oracle module)
    - ``"reset_polarity"`` — ``"active_low"``
    - ``"clock_period"``   — int (ns)
"""

import cocotb
from cocotb.triggers import RisingEdge
from cocotb.utils import get_sim_time
from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo

import ref_model  # behavioral oracle, CONTRACT.md §6

# Bounded idle allowance for the scoreboard-local watchdog (defence in depth).
# The scoreboard consumes exactly one monitor transaction per clock cycle, so
# a gap of this many cycles with *no* transaction means the environment hung.
# The authoritative overall watchdog lives in the test / top stage.
WATCHDOG_IDLE_CYCLES = 1_000_000


class AxiHandshakeScoreboard(uvm_scoreboard):
    """Cycle-accurate predictor + in-order comparator for ``axi_handshake``."""

    def __init__(self, name="axi_handshake_scoreboard", parent=None):
        super().__init__(name, parent)

        # Resolved in build_phase from ConfigDB (CONTRACT.md §5).
        self.dut = None
        self.dut_helper = None
        self.ref_model = None
        self.reset_polarity = "active_low"
        self.clock_period_ns = 10

        # TLM analysis FIFO bridging the monitor's analysis port.  The
        # environment stage connects ``monitor.ap.connect(sb.analysis_export)``.
        self.analysis_fifo = None
        self.analysis_export = None

        # --- scoreboard accounting / pass criteria inputs ---
        self.cycle = 0                 # number of monitor items consumed
        self.items_checked = 0         # items compared (reset + normal)
        self.pass_count = 0
        self.mismatch_count = 0
        self.reset_cycles = 0          # cycles observed with reset asserted
        self.input_transfers = 0       # input transfers accepted (oracle)
        self.output_transfers = 0      # output transfers accepted (oracle)
        self._failures = []            # human-readable mismatch strings
        self._prev_reset_asserted = None
        self._last_activity_cycle = 0  # for the local watchdog
        self._watchdog_task = None

    # ------------------------------------------------------------------
    # UVM build_phase
    # ------------------------------------------------------------------

    def build_phase(self):
        """Resolve the shared DUT / oracle config and create the analysis FIFO."""
        super().build_phase()

        self.dut = ConfigDB().get(None, "", "dut")
        if self.dut is None:
            raise RuntimeError(
                "AxiHandshakeScoreboard: ConfigDB key 'dut' not set"
            )

        self.dut_helper = ConfigDB().get(None, "", "dut_helper")
        self.ref_model = ConfigDB().get(None, "", "ref_model") or ref_model
        self.reset_polarity = str(
            ConfigDB().get(None, "", "reset_polarity") or "active_low"
        )
        clock_period = ConfigDB().get(None, "", "clock_period")
        if clock_period is not None:
            self.clock_period_ns = int(clock_period)

        # Buffered TLM bridge: uvm_tlm_analysis_fifo provides an
        # analysis_export that the environment connects to the monitor's
        # analysis port; get() blocks until an item is available.
        self.analysis_fifo = uvm_tlm_analysis_fifo("analysis_fifo", self)
        self.analysis_export = self.analysis_fifo.analysis_export

        self.logger.info(
            "AxiHandshakeScoreboard built "
            "(reset_polarity=%s, clock_period=%d ns)",
            self.reset_polarity,
            self.clock_period_ns,
        )

    # ------------------------------------------------------------------
    # UVM run_phase — one oracle step + comparison per monitor item
    # ------------------------------------------------------------------

    async def run_phase(self):
        """Consume one monitor transaction per cycle; predict and compare."""
        self._watchdog_task = cocotb.start_soon(self._watchdog())
        self.logger.info("AxiHandshakeScoreboard run_phase started")
        while True:
            tr = await self.analysis_fifo.get()
            self.cycle += 1
            self._last_activity_cycle = self.cycle
            self._check_transaction(tr)

    # ------------------------------------------------------------------
    # Predictor + comparator
    # ------------------------------------------------------------------

    def _check_transaction(self, tr):
        """Advance the oracle one cycle and compare against the DUT sample."""
        # Reset alignment (active-low, CONTRACT.md §2 / §7): re-arm the oracle
        # for every reset-asserted cycle and again on the deassertion edge so
        # the DUT and the oracle always leave reset from an identical empty
        # state.  dut.rst_n is read in the same read-only timestep that the
        # monitor used to sample *tr*.
        reset_asserted = self._reset_is_asserted()
        if reset_asserted:
            self.reset_cycles += 1
            self.ref_model.reset()
        elif self._prev_reset_asserted:
            # Deassertion edge (0 -> 1 for active-low): fresh empty oracle.
            self.ref_model.reset()
        self._prev_reset_asserted = reset_asserted

        # Cycle-accurate oracle call (latency 0): outputs are for the *same*
        # cycle as the inputs, exactly as specified in CONTRACT.md §6 / §7.
        exp_s_ready, exp_m_valid, exp_m_data = (
            int(v) for v in self.ref_model.step(
                int(tr.s_valid), int(tr.s_data), int(tr.m_ready)
            )
        )
        act_s_ready = int(tr.s_ready)
        act_m_valid = int(tr.m_valid)
        act_m_data = int(tr.m_data)

        self.items_checked += 1

        # Track genuinely meaningful traffic as judged by the oracle, so the
        # test stage can reject runs that never exercised the data path.
        if int(tr.s_valid) and exp_s_ready:
            self.input_transfers += 1
        if exp_m_valid and int(tr.m_ready):
            self.output_transfers += 1

        problems = []
        if act_s_ready != exp_s_ready:
            problems.append(f"s_ready: expected {exp_s_ready} got {act_s_ready}")
        if act_m_valid != exp_m_valid:
            problems.append(f"m_valid: expected {exp_m_valid} got {act_m_valid}")
        if act_m_data != exp_m_data:
            problems.append(
                f"m_data: expected 0x{exp_m_data:02X} got 0x{act_m_data:02X}"
            )

        if problems:
            self.mismatch_count += 1
            live = ""
            if self.dut_helper is not None:
                try:
                    live = " live DUT " + str(self.dut_helper.read_outputs())
                except Exception:  # pragma: no cover — diagnostics only
                    live = ""
            msg = (
                f"MISMATCH cycle={self.cycle} "
                f"(sim_time={get_sim_time(units='ns'):.1f} ns, "
                f"rst_n={'0' if reset_asserted else '1'}): "
                f"stimulus: s_valid={int(tr.s_valid)}, "
                f"s_data=0x{int(tr.s_data):02X}, "
                f"m_ready={int(tr.m_ready)}; "
                + "; ".join(problems)
                + live
            )
            self.logger.error(msg)
            self._failures.append(msg)
        else:
            self.pass_count += 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset_is_asserted(self) -> bool:
        """Return True when the (possibly active-low) reset is asserted."""
        val = int(self.dut.rst_n.value)
        if self.reset_polarity == "active_low":
            return val == 0
        return val != 0

    async def _watchdog(self):
        """Always-running local watchdog (defence in depth).

        Fails the test if no monitor transaction arrives for
        ``WATCHDOG_IDLE_CYCLES`` consecutive clock cycles, which can only
        happen if the monitor → scoreboard pipeline is hung or disconnected.
        The authoritative overall test-duration watchdog lives in the test /
        top stage.
        """
        clk = self.dut.clk
        while True:
            await RisingEdge(clk)
            if (self.cycle - self._last_activity_cycle) >= WATCHDOG_IDLE_CYCLES:
                msg = (
                    f"AxiHandshakeScoreboard watchdog: no monitor transaction "
                    f"received for {WATCHDOG_IDLE_CYCLES} clock cycles "
                    f"({WATCHDOG_IDLE_CYCLES * self.clock_period_ns} ns) — "
                    f"environment hung or scoreboard disconnected"
                )
                self.logger.error(msg)
                raise AssertionError(msg)

    # ------------------------------------------------------------------
    # UVM report_phase
    # ------------------------------------------------------------------

    def report_phase(self):
        """Summarize pass/fail statistics for the test framework."""
        super().report_phase()
        self.logger.info(
            "AxiHandshakeScoreboard report: %d items checked, %d passed, "
            "%d mismatches, %d reset cycles, %d input transfers, "
            "%d output transfers",
            self.items_checked,
            self.pass_count,
            self.mismatch_count,
            self.reset_cycles,
            self.input_transfers,
            self.output_transfers,
        )
        if self.mismatch_count:
            self.logger.warning(
                "AxiHandshakeScoreboard FAILED: %d comparison mismatch(es)",
                self.mismatch_count,
            )