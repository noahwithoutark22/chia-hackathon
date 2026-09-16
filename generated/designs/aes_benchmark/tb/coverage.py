"""Stage 5 (coverage) artifact of the CHIA generator: functional coverage.

Implements the ``functional_coverage`` section of the verification plan for
the ``aes128`` bench *entirely* in Python with the ``cocotb-coverage``
library (``cocotb_coverage.coverage.CoverPoint`` / ``CoverCross`` sampled
through the shared ``coverage_db``).  There is no SystemVerilog covergroup
anywhere in this project (CONTRACT.md section 6).

Four covergroups
----------------

``cg_input_patterns`` -- key and plaintext value bins, sampled from monitor
items (transactions published by :class:`~tb.monitor.AES128Monitor`):

    top.cg_input_patterns.bv_key_value
    top.cg_input_patterns.bv_plaintext_value
    top.cg_input_patterns.cross_key_plaintext

``cg_fsm_transitions`` -- FSM state and busy behavior, sampled every clock
edge directly from the DUT:

    top.cg_fsm_transitions.bv_state
    top.cg_fsm_transitions.busy_cp
    top.cg_fsm_transitions.cross_state_busy

``cg_reset_scenarios`` -- reset observed during IDLE and during operation,
sampled every clock edge from the DUT:

    top.cg_reset_scenarios.bv_reset_during_idle
    top.cg_reset_scenarios.bv_reset_during_operation

``cg_done_behavior`` -- done pulse observed, sampled every clock edge:

    top.cg_done_behavior.bv_done_high

Sampling data source
--------------------
* **Input patterns**: sampled via :func:`sample_input_patterns` each time
  a :class:`~tb.transaction.AES128Transaction` arrives through the
  ``analysis_export`` (connected to ``agent.analysis_port`` by the
  environment stage).  Key and plaintext are stimulus fields on the item,
  so coverage is sampled only on completed transactions (CONTRACT.md
  section 4).
* **FSM / Reset / Done**: sampled every ``RisingEdge(dut.clk)`` by the
  ``_sample_cycle_loop`` coroutine, started from ``run_phase``.  These
  covergroups observe the DUT pins/state continuously and do not depend on
  monitor items.

State encoding (CONTRACT.md section 1; RTL ``aes128.sv``)
    IDLE = 0, ROUND_RUN = 1, FINISH = 2

Value-binning
-------------
cocotb-coverage matches bins by equality.  The plan's ``key`` /
``plaintext`` value bins are expressed as *bin classifiers* (``xf``)
mapping 128-bit integers to small class ids; ``None`` means "no bin
matched".  The ``state`` / ``rst_n`` / ``busy`` / ``done`` coverpoints
use either xf classifiers or direct integer bin values.

For ``cg_reset_scenarios``, each bin's condition spans *two* variables
(rst_n AND state / busy).  cocotb-coverage ``xf`` only sees the variable
selected by ``vname``, so the component pre-computes a *class id* for
each joint condition and passes it as the coverpoint's sampled value: bin
id ``1`` = condition true, ``0`` = not counted.

How this is wired (integration stage 6)
----------------------------------------
``AES128Coverage`` is a ``pyuvm.uvm_subscriber``: its built-in
``analysis_export`` receives monitor items via ``write()`` (input-pattern
coverage).  ``run_phase`` starts the continuous FSM/reset/done sampler.
The environment connects ``agent.analysis_port`` to both
``scoreboard.analysis_export`` and ``coverage.analysis_export``.

End-of-test reporting uses :func:`report_coverage` /
``coverage_db.report_coverage``.
"""

import logging

import cocotb  # noqa: F401  (cocotb.start_soon used in run_phase)
from cocotb.triggers import RisingEdge

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from pyuvm import ConfigDB, uvm_subscriber

from tb.transaction import AES128Transaction

__all__ = [
    "AES128Coverage",
    "coverage_db",
    "sample_input_patterns",
    "report_coverage",
    "coverage_percentage",
]

_log = logging.getLogger("tb.coverage")

# ---------------------------------------------------------------------------
# Plan metadata constants.
# ---------------------------------------------------------------------------

COVERGROUP_INPUT = "top.cg_input_patterns"
COVERGROUP_FSM = "top.cg_fsm_transitions"
COVERGROUP_RESET = "top.cg_reset_scenarios"
COVERGROUP_DONE = "top.cg_done_behavior"

# FSM state encoding (RTL aes128.sv typedef enum logic [1:0])
STATE_IDLE = 0
STATE_ROUND_RUN = 1
STATE_FINISH = 2

# Key value bins (CONTRACT.md functional_coverage.covergroups[0])
KEY_ALL_ZEROS = 0x00000000000000000000000000000000
KEY_ALL_ONES = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
KEY_ALTERNATING_A = 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
KEY_SINGLE_BIT_LSB = 0x00000000000000000000000000000001

# Plaintext value bins
PT_ALL_ZEROS = 0x00000000000000000000000000000000
PT_ALL_ONES = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
PT_ALTERNATING_5 = 0x55555555555555555555555555555555
PT_NIST_VECTOR = 0x00112233445566778899AABBCCDDEEFF

# FSM state internal signal name (for defensive access in the sampler).
_STATE_SIGNAL = "state"

# ---------------------------------------------------------------------------
# Input-pattern classifiers (key, plaintext) -- value-equality bins.
# ---------------------------------------------------------------------------


def _classify_key(v):
    """Map a 128-bit key integer to a bin id, or None if no bin matches."""
    v = int(v)
    if v == KEY_ALL_ZEROS:
        return 0
    if v == KEY_ALL_ONES:
        return 1
    if v == KEY_ALTERNATING_A:
        return 2
    if v == KEY_SINGLE_BIT_LSB:
        return 3
    return None


def _classify_plaintext(v):
    """Map a 128-bit plaintext integer to a bin id, or None."""
    v = int(v)
    if v == PT_ALL_ZEROS:
        return 0
    if v == PT_ALL_ONES:
        return 1
    if v == PT_ALTERNATING_5:
        return 2
    if v == PT_NIST_VECTOR:
        return 3
    return None


# ---------------------------------------------------------------------------
# Input-pattern coverpoints and cross.
# ---------------------------------------------------------------------------


@CoverPoint(
    f"{COVERGROUP_INPUT}.bv_key_value",
    vname="key",
    xf=_classify_key,
    bins=[0, 1, 2, 3],
    bins_labels=["all_zeros", "all_ones", "alternating_a", "single_bit_lsb"],
)
def _cp_key(key):
    """bv_key_value: all_zeros / all_ones / alternating_a / single_bit_lsb."""


@CoverPoint(
    f"{COVERGROUP_INPUT}.bv_plaintext_value",
    vname="plaintext",
    xf=_classify_plaintext,
    bins=[0, 1, 2, 3],
    bins_labels=["all_zeros", "all_ones", "alternating_5", "nist_vector"],
)
def _cp_plaintext(plaintext):
    """bv_plaintext_value: all_zeros / all_ones / alternating_5 / nist_vector."""


@CoverCross(
    f"{COVERGROUP_INPUT}.cross_key_plaintext",
    items=[
        f"{COVERGROUP_INPUT}.bv_key_value",
        f"{COVERGROUP_INPUT}.bv_plaintext_value",
    ],
)
def _cross_key_plaintext(key, plaintext):
    """Cross key-value patterns with plaintext-value patterns."""


def sample_input_patterns(key, plaintext):
    """Sample the ``cg_input_patterns`` covergroup from one monitor item.

    ``key`` and ``plaintext`` are 128-bit integers from a completed
    :class:`~tb.transaction.AES128Transaction` published by the monitor
    (CONTRACT.md section 4).  Coverpoints are sampled first (they feed the
    cross), then the cross.
    """
    _cp_key(key)
    _cp_plaintext(plaintext)
    _cross_key_plaintext(key, plaintext)


# ---------------------------------------------------------------------------
# FSM state classifier and coverpoints + cross (cg_fsm_transitions).
# ---------------------------------------------------------------------------


def _classify_state(v):
    """Map 2-bit FSM state integer to a bin id, or None."""
    v = int(v)
    if v == STATE_IDLE:
        return 0
    if v == STATE_ROUND_RUN:
        return 1
    if v == STATE_FINISH:
        return 2
    return None


@CoverPoint(
    f"{COVERGROUP_FSM}.bv_state",
    vname="state",
    xf=_classify_state,
    bins=[0, 1, 2],
    bins_labels=["idle", "round_run", "finish"],
)
def _cp_state(state):
    """bv_state: idle / round_run / finish."""


@CoverPoint(
    f"{COVERGROUP_FSM}.busy_cp",
    vname="busy",
    bins=[0, 1],
    bins_labels=["idle", "active"],
)
def _cp_busy(busy):
    """busy_cp: 0 (idle) / 1 (active)."""


@CoverCross(
    f"{COVERGROUP_FSM}.cross_state_busy",
    items=[
        f"{COVERGROUP_FSM}.bv_state",
        f"{COVERGROUP_FSM}.busy_cp",
    ],
)
def _cross_state_busy(state, busy):
    """Cross FSM state with busy to verify idle/finish have busy low, round_run
    has busy high."""


def sample_fsm(state, busy):
    """Sample ``cg_fsm_transitions`` covergroup.

    ``state`` is the 2-bit FSM state register value (0/1/2);
    ``busy`` is the 1-bit output.  Both sampled every ``RisingEdge(clk)``
    by the continuous sampler coroutine.
    """
    _cp_state(state)
    _cp_busy(busy)
    _cross_state_busy(state, busy)


# ---------------------------------------------------------------------------
# Reset-scenario coverpoints (cg_reset_scenarios).
#
# Each bin's condition spans two variables (rst_n AND state or busy).
# cocotb-coverage xf only sees one variable, so the component pre-computes
# a *joint class id* and passes it as the sampled value:  1 = condition
# true,  0 = not counted.
# ---------------------------------------------------------------------------


@CoverPoint(
    f"{COVERGROUP_RESET}.bv_reset_during_idle",
    vname="rst_n",
    bins=[1],
    bins_labels=["reset_idle"],
)
def _cp_reset_idle(rst_n):
    """bv_reset_during_idle: rst_n==0 && state==IDLE (pre-classified to 1)."""


@CoverPoint(
    f"{COVERGROUP_RESET}.bv_reset_during_operation",
    vname="rst_n",
    bins=[1],
    bins_labels=["reset_busy"],
)
def _cp_reset_busy(rst_n):
    """bv_reset_during_operation: rst_n==0 && busy==1 (pre-classified to 1)."""


def sample_reset_scenarios(rst_n_idle_class, rst_n_busy_class):
    """Sample ``cg_reset_scenarios`` from a clock-edge observation.

    Arguments are pre-computed class ids (1 = bin condition true, 0 =
    condition false / not counted).
    """
    _cp_reset_idle(rst_n_idle_class)
    _cp_reset_busy(rst_n_busy_class)


# ---------------------------------------------------------------------------
# Done-behavior coverpoint (cg_done_behavior).
# ---------------------------------------------------------------------------


@CoverPoint(
    f"{COVERGROUP_DONE}.bv_done_high",
    vname="done",
    bins=[1],
    bins_labels=["done_pulse"],
)
def _cp_done_high(done):
    """bv_done_high: done==1 observed at a clock edge."""


def sample_done_behavior(done_val):
    """Sample ``cg_done_behavior`` from a clock-edge observation.

    ``done_val`` is 1 when the done pulse is observed, 0 otherwise.
    Only bin hits (value == 1) count.
    """
    _cp_done_high(done_val)


# ---------------------------------------------------------------------------
# Coverage collector component (pyuvm uvm_subscriber).
# ---------------------------------------------------------------------------


class AES128Coverage(uvm_subscriber):
    """Coverage collector for the ``aes128`` DUT.

    A pyuvm ``uvm_subscriber`` provides a built-in ``analysis_export``
    (attribute ``self.analysis_export``); the integration stage connects
    ``agent.analysis_port`` to it.  Every completed transaction published
    by :class:`~tb.monitor.AES128Monitor` reaches ``write()`` and is
    funnelled into the shared ``coverage_db`` through
    :func:`sample_input_patterns`.

    Additionally, ``run_phase`` starts the continuous FSM/reset/done
    sampler coroutine that samples ``cg_fsm_transitions``,
    ``cg_reset_scenarios``, and ``cg_done_behavior`` on every
    ``RisingEdge(clk)``.

    The collector is observation-only: it never drives pins, never raises
    on the DUT's behalf, and never fails the test by itself.
    """

    def __init__(self, name="aes128_coverage", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.helper = None
        #: Completed transactions processed as coverage samples.
        self.sample_count = 0
        self._clock_task = None
        self._state_available = None  # determined on first sample

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        super().build_phase()
        # CONTRACT.md section 5 / §7.3: empty-scope retrieval.
        self.dut = ConfigDB().get(self, "", "dut")
        self.helper = ConfigDB().get(self, "", "dut_helper")
        if self.dut is None or self.helper is None:
            self.logger.warning(
                "%s: 'dut' / 'dut_helper' not found in ConfigDB; "
                "continuous coverage sampling will be skipped",
                self.get_name(),
            )

    def write(self, item):
        """uvm_subscriber write() -- called for every connected transaction.

        Samples the ``cg_input_patterns`` covergroup from the monitor's
        published item (key, plaintext stimulus fields).
        """
        if not isinstance(item, AES128Transaction):
            self.logger.error(
                "%s: expected AES128Transaction on analysis_export, got %s",
                self.get_name(),
                type(item).__name__,
            )
            return
        sample_input_patterns(item.key, item.plaintext)
        self.sample_count += 1
        self.logger.debug(
            "%s: sampled input patterns from %s (%d total)",
            self.get_name(),
            item,
            self.sample_count,
        )

    async def run_phase(self):
        """Start the continuous FSM/reset/done sampler coroutine.

        ``_sample_cycle_loop`` runs for the whole simulation as an independent
        cocotb task, so ``run_phase`` deliberately returns immediately (it
        must NOT block: pyuvm's phase machinery awaits this coroutine).
        """
        if self.dut is None or self.helper is None:
            self.logger.warning(
                "%s: run_phase -- dut/dut_helper unavailable; "
                "continuous coverage sampling disabled",
                self.get_name(),
            )
            return
        self._clock_task = cocotb.start_soon(self._sample_cycle_loop())
        self.logger.info(
            "%s: run_phase started (continuous sampler active)",
            self.get_name(),
        )

    async def _sample_cycle_loop(self):
        """Sample FSM, reset, and done covergroups on every clock edge.

        Runs for the entire simulation; ``run_phase`` starts it with
        ``cocotb.start_soon``.
        """
        dut = self.dut
        helper = self.helper
        self._state_available = None  # probe on first cycle
        state_warned = False

        while True:
            await RisingEdge(dut.clk)

            # ── Read DUT state (internal) ──────────────────────────────
            state_val = None
            try:
                raw = dut.state.value  # cocotb 2.x LogicArray or int
                state_val = int(raw)
                if state_val not in (STATE_IDLE, STATE_ROUND_RUN, STATE_FINISH):
                    state_val = None  # invalid value
                else:
                    self._state_available = True
            except (AttributeError, ValueError, TypeError, Exception):
                self._state_available = False
                if not state_warned:
                    self.logger.warning(
                        "%s: cannot read internal 'state' signal; "
                        "FSM coverpoints will not be sampled",
                        self.get_name(),
                    )
                    state_warned = True

            # ── Read DUT outputs / reset ───────────────────────────────
            rst_n = int(helper.rst_n)
            busy = int(helper.busy)
            done = int(helper.done)

            # ── cg_fsm_transitions ────────────────────────────────────
            if state_val is not None:
                sample_fsm(state_val, busy)

            # ── cg_reset_scenarios ────────────────────────────────────
            if rst_n == 0:
                rst_idle_class = (
                    1 if (state_val is not None
                          and state_val == STATE_IDLE) else 0
                )
                rst_busy_class = 1 if busy == 1 else 0
                sample_reset_scenarios(rst_idle_class, rst_busy_class)

            # ── cg_done_behavior ──────────────────────────────────────
            sample_done_behavior(done)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def report(self, logger=None, bins=False):
        """Log the coverage tree through ``logger``.

        ``logger`` defaults to this component's logger.
        Returns the overall coverage percentage (0.0 -- 100.0).
        """
        log = logger if logger is not None else self.logger.info
        report_coverage(log, bins=bins)
        return coverage_percentage()


# ---------------------------------------------------------------------------
# Reporting helpers for the integration (environment) stage.
# ---------------------------------------------------------------------------


def coverage_percentage():
    """Overall coverage across all four covergroups (0.0 -- 100.0)."""
    total_pct = 0.0
    count = 0
    for cg in (COVERGROUP_INPUT, COVERGROUP_FSM,
               COVERGROUP_RESET, COVERGROUP_DONE):
        node = coverage_db.get(cg)
        if node is not None:
            total_pct += float(node.cover_percentage)
            count += 1
    return total_pct / count if count > 0 else 0.0


def report_coverage(logger, bins=False):
    """Dump the coverage tree through ``logger``.

    ``logger`` is a callable (e.g. ``self.logger.info``).
    ``bins=True`` also prints per-bin hit counts.
    """
    for cg in (COVERGROUP_INPUT, COVERGROUP_FSM,
               COVERGROUP_RESET, COVERGROUP_DONE):
        coverage_db.report_coverage(logger, bins=bins, node=cg)
