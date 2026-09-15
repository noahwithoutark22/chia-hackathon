"""FIFO scoreboard (pyuvm ``uvm_scoreboard``) + reference-model integration.

This component implements the *checker* side of the FIFO testbench.  It
consumes the per-cycle :class:`FifoTransaction` items published by
``FifoMonitor`` (one per rising clock edge, CONTRACT.md §5 and §10.2),
advances a reference-model predictor on every cycle, and compares the DUT's
post-edge outputs against the predictor's expectations.

Role / strategy (scoreboard_reference_model_strategy):
    * predictor_scoreboard: a Python predictor invokes
      ``ref_model.step(state, wr_en, rd_en, din, depth)`` on every rising
      clock edge, tracking the expected queue contents and expected ``dout``.
      Expected ``full``/``empty`` derive from the expected queue length.
    * in_order_comparator: after each edge the comparator checks
      ``dout``/``full``/``empty`` (and, when reachable, the internal
      ``count``).  ``dout`` is compared against the value the predictor
      pops for the accepted read (matching the RTL's registered, latency-1
      output); ``full``/``empty``/``count`` are compared every cycle.
      Because the predictor always pops the *oldest* queued entry, matching
      ``dout`` enforces strict FIFO ordering and catches data drop or
      duplication.

Timing / alignment (CONTRACT.md §2, §6, §7, §10.2):
    The monitor samples post-edge values in cocotb's read-only region; a
    transaction therefore carries the inputs the DUT sampled on that edge
    and the outputs settled *after* that same edge:
        * ``dout`` is the latency-1 registered output: the value shown
          after an edge at which a read was accepted is the entry popped by
          that edge (the RTL's ``dout <= mem[rd_ptr]`` nonblocking update).
        * ``full``/``empty`` are the combinational flags derived from the
          post-edge ``count``.
    ``ref_model.step(state, ...)`` returns the new queue and the ``dout``
    popped by *this* cycle, so for a single item the comparison is direct:
        * new_state["dout"]               ==  item.dout   (latency 1)
        * len(new_state["queue"])==depth  ==  item.full
        * len(new_state["queue"])==0      ==  item.empty
        * len(new_state["queue"])         ==  dut.count   (when reachable)
    This is a single-cycle (registered-output) relationship, NOT a
    multi-cycle pipeline.

Reset (CONTRACT.md §10.2):
    Reset is NOT a transaction field, so the scoreboard observes ``dut.rst_n``
    directly.  Reading ``dut.rst_n`` immediately after ``get()`` from the
    analysis FIFO yields the post-edge value for that cycle (put and get both
    occur in the read-only region of the same timestep, so no simulation time
    advances between them).  Whenever ``rst_n == 0`` the predictor state is
    re-armed with ``ref_model.reset()``, matching the RTL's asynchronous
    active-low reset (empty=1, full=0, dout=0).
"""

from collections import deque

from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo

import ref_model


class FifoScoreboard(uvm_scoreboard):
    """Predictor + in-order comparator for the ``fifo`` DUT."""

    def __init__(self, name="fifo_scoreboard", parent=None):
        super().__init__(name, parent)
        # Shared DUT config (CONTRACT.md §4; access form §9.1).  Resolved in
        # build_phase.
        self.dut = None
        self.data_width = 8
        self.depth = 4

        # Analysis connection.  The environment stage connects the monitor's
        # analysis port here: monitor.ap.connect(scoreboard.analysis_export).
        self.analysis_fifo = None
        self.analysis_export = None

        # Predictor state (a dict {"queue": deque, "dout": int}, per
        # ref_model.reset/step).  The deque is mutated in place by step().
        self._state = None

        # Accounting.
        self.edge_index = 0          # 0-based rising-edge counter (matches dut_cycle)
        self._items_checked = 0
        self._mismatch_count = 0
        self._pass_count = 0
        self._reset_observed = 0
        self._failures = []          # human-readable mismatch strings
        self._recent = deque(maxlen=8)  # trace of recent operations for debug

    # -- phases ------------------------------------------------------------

    def build_phase(self):
        """Resolve the shared DUT config and create the TLM analysis FIFO."""
        super().build_phase()
        self.dut = ConfigDB().get(None, "*", "dut")
        self.data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
        self.depth = int(ConfigDB().get(None, "*", "DEPTH"))
        self._state = ref_model.reset()

        # A uvm_tlm_analysis_fifo buffers monitor items and provides an
        # analysis_export that the env connects to the monitor's analysis
        # port.  uvm_AnalysisExport.write() puts into the fifo nonblockingly,
        # and get() blocks until an item is available (classic pyuvm bridge).
        self.analysis_fifo = uvm_tlm_analysis_fifo("fifo_analysis_fifo", self)
        self.analysis_export = self.analysis_fifo.analysis_export
        self.logger.info(
            "FifoScoreboard built (DATA_WIDTH=%d, DEPTH=%d)",
            self.data_width, self.depth,
        )

    # -- main loop ---------------------------------------------------------

    async def run_phase(self):
        """Consume one monitor transaction per cycle; predict and compare."""
        self.logger.info("FifoScoreboard run_phase started")
        while True:
            tr = await self.analysis_fifo.get()
            # Reading rst_n here yields the post-edge value for the cycle that
            # produced *tr* (put and get share the read-only timestep).
            rst_n = self._read("rst_n")
            self._state = self._advance_and_check(tr, rst_n)

    # -- predictor / comparator --------------------------------------------

    def _read(self, pin):
        """Read a DUT pin as a plain Python ``int`` (pin names per §2)."""
        return int(getattr(self.dut, pin).value)

    def _advance_and_check(self, tr, rst_n):
        """Advance the predictor for one cycle and compare against *tr*.

        Returns the predictor state to carry into the next cycle.
        """
        cycle = tr.dut_cycle if tr.dut_cycle is not None else self.edge_index
        self.edge_index += 1

        # Record this operation for the debug trace.
        self._recent.append(
            (cycle, tr.wr_en, tr.rd_en, tr.din)
        )

        # Reset alignment: an asserted rst_n re-arms the predictor, exactly
        # mirroring the asynchronous active-low reset of the DUT.
        if rst_n == 0:
            self._reset_observed += 1
            state = ref_model.reset()
            self._check(tr, state, cycle,
                        expect_reset_mode=True)
            return state

        # Normal cycle: one combinational step (registered-output latency 1).
        state = ref_model.step(
            self._state, int(tr.wr_en), int(tr.rd_en), int(tr.din), self.depth,
        )
        self._check(tr, state, cycle, expect_reset_mode=False)
        return state

    def _check(self, tr, new_state, cycle, expect_reset_mode):
        """Compare the DUT item against the predictor's new state.

        Reports every mismatch with full context (cycle, operation, expected
        vs actual, expected queue contents, recent operation trace) and bumps
        the mismatch counter.  A raised assertion is intentionally avoided
        here so the whole test can continue collecting failures; the test /
        assertions stage fails the test when the mismatch count is nonzero
        (or on a hard Python error).  The strategy's pass criteria are all
        exercised by these comparisons.
        """
        self._items_checked += 1

        q = new_state["queue"]
        exp_dout = int(new_state["dout"])
        exp_full = 1 if (len(q) == self.depth) else 0
        exp_empty = 1 if (len(q) == 0) else 0
        exp_count = len(q)

        act_dout = int(tr.dout)
        act_full = int(tr.full)
        act_empty = int(tr.empty)
        act_count = None
        count_reachable = True
        try:
            act_count = int(self.dut.count.value)
        except Exception:
            count_reachable = False  # internal signal not exposed (see §9.5)

        problems = []
        if act_dout != exp_dout:
            problems.append(f"dout: exp {exp_dout} got {act_dout}")
        if act_full != exp_full:
            problems.append(f"full: exp {exp_full} got {act_full}")
        if act_empty != exp_empty:
            problems.append(f"empty: exp {exp_empty} got {act_empty}")
        if count_reachable and act_count != exp_count:
            problems.append(f"count: exp {exp_count} got {act_count}")

        if problems:
            self._mismatch_count += 1
            trace = "  ".join(
                f"[cyc{c}:wr{w}/rd{r}={d:#x}]"
                for (c, w, r, d) in self._recent
            )
            msg = (
                f"MISMATCH cycle {cycle} (rst_n={int(self._read('rst_n'))}, "
                f"reset_mode={int(expect_reset_mode)}): "
                f"op(wr_en={tr.wr_en}, rd_en={tr.rd_en}, "
                f"din={tr.din:#x}) "
                + "; ".join(problems) +
                f"; expected queue len={exp_count} contents={list(q)}"
                f"; recent ops: {trace or '<none>'}"
            )
            self.logger.error(msg)
            self._failures.append(msg)
        else:
            self._pass_count += 1

    # -- reporting ---------------------------------------------------------

    def report_phase(self):
        """Summarize pass/fail statistics for the test framework."""
        super().report_phase()
        self.logger.info(
            "FifoScoreboard report: %d items checked, %d passed, "
            "%d mismatches, %d resets observed",
            self._items_checked,
            self._pass_count,
            self._mismatch_count,
            self._reset_observed,
        )
        if self._mismatch_count:
            self.logger.warning(
                "FifoScoreboard FAILED: %d comparison mismatch(es)",
                self._mismatch_count,
            )
