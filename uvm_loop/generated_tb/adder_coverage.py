"""Functional coverage collector for the parameterized adder DUT.

Implements the ``input_operand_coverage`` covergroup from the verification
plan (Stage 5 — Coverage & Assertions) using the ``cocotb-coverage`` library
(``CoverPoint`` / ``CoverCross``) sampled through the shared module-level
``coverage_db``.

The collector is a pyuvm ``uvm_subscriber`` that attaches to the agent's
monitor analysis port.  Every published :class:`AdderTransaction` triggers a
coverage sample on its **input operand fields** (``a``, ``b``, ``cin``) — the
exact fields defined by CONTRACT.md Section 4.  It intentionally does **not**
invent coverage points on pins or fields that the contract does not define.

Coverage hierarchy (plan ``input_operand_coverage``)::

    input_operand_coverage
      .a_values        -> CoverPoint on ``a``  (zero/low/mid/high/max)
      .b_values        -> CoverPoint on ``b``  (zero/low/mid/high/max)
      .cin_values      -> CoverPoint on ``cin`` (zero/one)
      .a_b_cin_cross   -> CoverCross over all three CoverPoints

Because the range helper returns the covering bin (a ``(lo, hi)`` tuple), the
CoverPoints use a custom relation and explicit bins so that an operand value
lands in exactly one range bin.  Bins are labelled so the cross bins read as,
e.g. ``('a_low', 'b_high', 'cin_one')``.
"""

from __future__ import annotations

from pyuvm import uvm_subscriber, ConfigDB
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db

from adder_transaction import AdderTransaction

# ---------------------------------------------------------------------------
# Coverage definition (module level so the singleton ``coverage_db`` is
# populated exactly once at import time, regardless of component instances).
# ---------------------------------------------------------------------------

# Namespace prefix shared by every coverage item in this covergroup.
_COV = "adder.input_operand_coverage"


def _in_range(value, bin_def):
    """Relation: ``value`` matches bin iff it falls inside ``[lo, hi]``.

    All bins here are ``(lo, hi)`` range tuples (per plan), so the check is a
    simple inclusive interval test.
    """
    return bin_def[0] <= value <= bin_def[1]


def _eq(value, bin_def):
    """Exact-equality relation used by the 1-bit ``cin`` CoverPoint."""
    return value == bin_def


# ---- CoverPoints (defined before the cross so they are registered) --------

_cp_a = CoverPoint(
    f"{_COV}.a_values",
    xf=lambda a, b, _cin: a,
    rel=_in_range,
    bins=[(0, 0), (1, 63), (64, 191), (192, 254), (255, 255)],
    bins_labels=["a_zero", "a_low", "a_mid", "a_high", "a_max"],
    at_least=1,
)

_cp_b = CoverPoint(
    f"{_COV}.b_values",
    xf=lambda _a, b, _cin: b,
    rel=_in_range,
    bins=[(0, 0), (1, 63), (64, 191), (192, 254), (255, 255)],
    bins_labels=["b_zero", "b_low", "b_mid", "b_high", "b_max"],
    at_least=1,
)

_cp_cin = CoverPoint(
    f"{_COV}.cin_values",
    xf=lambda _a, _b, cin: cin,
    rel=_eq,
    bins=[0, 1],
    bins_labels=["cin_zero", "cin_one"],
    at_least=1,
)

_cross = CoverCross(
    f"{_COV}.a_b_cin_cross",
    [f"{_COV}.a_values", f"{_COV}.b_values", f"{_COV}.cin_values"],
    at_least=1,
)

# ---- Sampling wrappers (decorator style registers the sample call) --------


@_cp_a
def _sample_a(a, b, cin):
    """Sample the ``a`` CoverPoint."""


@_cp_b
def _sample_b(a, b, cin):
    """Sample the ``b`` CoverPoint."""


@_cp_cin
def _sample_cin(a, b, cin):
    """Sample the ``cin`` CoverPoint."""


@_cross
def _sample_cross(a, b, cin):
    """Sample the three-way cross (reads the CoverPoints' new hits)."""


# ---------------------------------------------------------------------------
# PyUVM subscriber
# ---------------------------------------------------------------------------


class AdderCoverageCollector(uvm_subscriber):
    """Attaches to the monitor analysis port and samples functional coverage.

    This is a ``uvm_subscriber`` (CONTRACT/plan Stage 5).  The environment
    (Stage 6) must connect ``agent.ap`` to this subscriber's
    ``analysis_export`` (``agent.ap.connect(self.coverage.analysis_export)``).
    Every transaction that arrives on that port is passed to :meth:`write`,
    which samples the operand fields into the shared ``coverage_db``.

    Parameters
    ----------
    name : str
        Instance name (default ``"adder_coverage_collector"``).
    parent : uvm_component
        Parent component (normally the environment).
    """

    def __init__(self, name="adder_coverage_collector", parent=None):
        super().__init__(name, parent)
        self.width: int = 8

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Retrieve the width parameter (and DUT access) from ConfigDB."""
        super().build_phase()
        self.width = ConfigDB.get(None, "", "width")
        # ``dut`` is fetched only to confirm ConfigDB wiring is present;
        # coverage itself is sampled from monitor transactions.
        self.dut = ConfigDB.get(None, "", "dut")
        self.logger.info(
            "AdderCoverageCollector %s ready (width=%d)", self.get_full_name(),
            self.width,
        )

    # ------------------------------------------------------------------
    # Subscriber callback
    # ------------------------------------------------------------------

    def write(self, tr: "AdderTransaction") -> None:
        """Sample coverage from one observed transaction.

        The plan drives coverage off the transaction's operand fields, so we
        sample ``a``, ``b`` and ``cin`` exactly as the monitor published them.
        The cross CoverPoints are sampled in the same event (coverpoints first,
        cross last) so the cross reads the just-updated per-point hits.
        """
        a = int(tr.a)
        b = int(tr.b)
        cin = int(tr.cin)
        _sample_a(a, b, cin)
        _sample_b(a, b, cin)
        _sample_cin(a, b, cin)
        _sample_cross(a, b, cin)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def check_phase(self):
        """Summarize the functional coverage accumulated in ``coverage_db``.

        Runs at end-of-simulation (pyuvm ``check_phase``); the shared,
        module-level ``coverage_db`` holds all hits collected by this
        subscriber during the run.
        """
        super().check_phase()
        self.logger.info("=== Functional coverage report (%s) ===",
                         self.get_full_name())
        coverage_db.report_coverage(self.logger.info, bins=False, node="adder")
