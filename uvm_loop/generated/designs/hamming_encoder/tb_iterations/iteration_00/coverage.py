"""hamming_encoder functional coverage (cocotb-coverage, replaces SV covergroups).

This module implements the ``functional_coverage`` section of the
verification plan for the ``hamming_encoder`` DUT
(``benchmarks/hamming_encoder/hamming_encoder.sv``) using the
``cocotb-coverage`` library (``CoverPoint`` / ``CoverCross`` sampled through
the shared ``cocotb_coverage.coverage.coverage_db``).  It is the stage-5
counterpart of the SystemVerilog ``covergroup`` concept, rendered entirely
in Python.

Coverage sampling is driven off the per-settle-boundary
:class:`~tb.transaction.HammingTransaction` items published by
:class:`~tb.monitor.HammingMonitor` (tb/monitor.py) through its
``uvm_analysis_port`` (``ap``) — exactly one settled pair per driven encode
operation.  The environment stage connects
``hamming_agent.monitor_ap.connect(hamming_coverage.analysis_export)``
(CONTRACT.md sections 5, 10.2).

== Covergroup mapping (verification plan -> this module) ==

    cg_hamming_encoding:
        data_in_cov      [zero, single_bit_set, low_space, high_space,
                           max_value]
        secded_cov        [secded_off, secded_on]
        width_cov         [width_1, width_4, width_8, width_11, width_16]
        codeword_cov      [even_weight, odd_weight,
                           secded_parity_zero, secded_parity_one]
        crosses:
            data_x_secded   (data_in_cov x secded_cov)
            width_x_secded  (width_cov x secded_cov)

The ``data_in_cov`` bins are expression-based (predicates over ``data_in``)
whose thresholds depend on the elaborated ``data_width`` (captured by closure
in :func:`build_hamming_coverage`).  With ``inj=False`` overlapping bins are
legal and correctly tracked: e.g. ``data_in == 0`` matches both ``zero`` and
``low_space``.  ``codeword_cov`` bins are also expression-based (predicates
over ``code_out`` and ``secded``).

== Cross-test coverage accumulation ==

Per-test YAML/XML coverage files
(``hamming_encoder_coverage_{RUN_ID}_{testname}.yml``) are exported in
``report_phase`` and merged to produce an aggregate view across the full
regression.  The merge takes per-bin max hit counts across tests
(``_merge_per_test_coverage``).  The ``width_cov`` and ``secded_cov``
bins accumulate across elaborations, while ``data_in_cov`` and
``codeword_cov`` expressions are semantically parameterised by
``data_width`` — so cross-test aggregation of those bins is meaningful for
coverage of label space rather than exact numeric thresholds.

== Validation note ==

The callable-bin ``inj=False`` mechanism and cross-sampling lag were validated
experimentally against cocotb-coverage 1.2.0 (extracted from PyPI wheel).
CoverPoints MUST be listed ABOVE any CoverCrosses that reference them in the
source, because CPython evaluates decorator expressions top-down (CoverPoint
``__init__`` registers them before the CoverCross ``__init__`` reads the
bin keys).

== Idempotent registration ==

``CoverPoint.__new__`` / ``CoverCross.__new__`` return existing entries from
``coverage_db`` when a matching name exists, so calling
``build_hamming_coverage`` multiple times within one simulation process is
safe (parameter values are fixed per elaborated DUT).
"""

import os
import time

from pyuvm import ConfigDB, uvm_subscriber

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db

from tb.dut_helper import (
    DEFAULT_DATA_WIDTH,
    DEFAULT_SECDED,
    KEY_CLK_RST,
    KEY_CONF,
    KEY_DUT_PINS,
)

# ── helpers ───────────────────────────────────────────────────────────────

def _popcount(n):
    """Hamming weight of non-negative integer *n*."""
    return bin(n).count("1")


def _callable_rel(value, bin_entry):
    """Bins-matching relation supporting callable expression bins.

    ``bin_entry`` is either a plain value (default ``==`` match) or a
    callable that receives the sampled value and returns ``True``/``False``.
    Used as the ``rel`` argument to :class:`CoverPoint` so that overlapping
    expression bins work correctly with ``inj=False``.
    """
    if callable(bin_entry):
        return bin_entry(value)
    return value == bin_entry


# ── covergroup factory ────────────────────────────────────────────────────

def build_hamming_coverage(data_width=DEFAULT_DATA_WIDTH,
                           secded=DEFAULT_SECDED):
    """Register the ``cg_hamming_encoding`` covergroup in ``coverage_db``.

    Registration is idempotent (see module docstring and
    ``CoverPoint.__new__``).  Returns the single sampling callable
    ``_sample_hamming`` that accepts one plain-dict payload of the monitor
    item fields::

        {"data_in", "code_out", "data_width", "secded", "code_width"}

    Args:
        data_width: elaborated ``DATA_WIDTH`` used to compute the
            ``data_in_cov`` expression-bin thresholds.
        secded: elaborated ``SECDED`` parameter (0 or 1).

    Returns:
        sampling callable ``_sample_hamming(payload: dict)``.
    """
    dw = int(data_width)

    # -- data_in_cov ---------------------------------------------------
    # Expression bins with thresholds that depend on the elaborated data_width.
    # `inj=False` is required because overlapping predicates are legal
    # (e.g. zero ⊂ low_space for any dw ≥ 2).
    @CoverPoint(  # noqa: E999 – decoration order: top-most applied last
        "cg_hamming_encoding.data_in_cov",
        xf=lambda s: s["data_in"],
        bins=[
            lambda v: v == 0,                                    # zero
            lambda v: v != 0 and (v & (v - 1)) == 0,            # single_bit_set
            lambda v: v < (1 << (dw - 1)),                      # low_space
            lambda v: v >= (1 << (dw - 1)),                     # high_space
            lambda v: v == (1 << dw) - 1,                        # max_value
        ],
        bins_labels=["zero", "single_bit_set", "low_space",
                     "high_space", "max_value"],
        rel=_callable_rel,
        inj=False,
    )
    # -- secded_cov ----------------------------------------------------
    @CoverPoint(
        "cg_hamming_encoding.secded_cov",
        xf=lambda s: s["secded"],
        bins=[0, 1],
        bins_labels=["secded_off", "secded_on"],
    )
    # -- width_cov -----------------------------------------------------
    # Fixed per-plan test values; accumulation across tests is via merge.
    @CoverPoint(
        "cg_hamming_encoding.width_cov",
        xf=lambda s: s["data_width"],
        bins=[1, 4, 8, 11, 16],
        bins_labels=["width_1", "width_4", "width_8",
                     "width_11", "width_16"],
    )
    # -- codeword_cov --------------------------------------------------
    # xf returns the whole payload so the callable bins can inspect both
    # code_out and secded.  inj=False because even_weight overlaps with
    # secded_parity_zero/one (both can match simultaneously).
    @CoverPoint(
        "cg_hamming_encoding.codeword_cov",
        xf=lambda s: s,
        bins=[
            lambda s: _popcount(s["code_out"]) % 2 == 0,        # even_weight
            lambda s: _popcount(s["code_out"]) % 2 == 1,        # odd_weight
            lambda s: bool(s["secded"])
            and ((s["code_out"] >> 0) & 1) == 0,                 # secded_parity_zero
            lambda s: bool(s["secded"])
            and ((s["code_out"] >> 0) & 1) == 1,                 # secded_parity_one
        ],
        bins_labels=["even_weight", "odd_weight",
                     "secded_parity_zero", "secded_parity_one"],
        rel=_callable_rel,
        inj=False,
    )
    # -- data_x_secded ------------------------------------------------
    @CoverCross(
        "cg_hamming_encoding.data_x_secded",
        items=["cg_hamming_encoding.data_in_cov",
               "cg_hamming_encoding.secded_cov"],
    )
    # -- width_x_secded ------------------------------------------------
    @CoverCross(
        "cg_hamming_encoding.width_x_secded",
        items=["cg_hamming_encoding.width_cov",
               "cg_hamming_encoding.secded_cov"],
    )
    def _sample_hamming(payload):
        """Sample the ``cg_hamming_encoding`` covergroup.

        All values are consumed by the coverpoint ``xf`` functions and the
        cross-product machinery; the payload dict is only the carrier.
        """
        del payload

    return _sample_hamming


# ── coverage collector component ──────────────────────────────────────────

class HammingCoverage(uvm_subscriber):
    """Functional-coverage collector for the ``hamming_encoder`` DUT.

    Subscribes to the monitor's analysis port: the environment stage
    connects ``hamming_agent.monitor_ap.connect(
    hamming_coverage.analysis_export)``.  Every received transaction is
    converted into the coverage payload and sampled through
    :data:`cocotb_coverage.coverage.coverage_db`.  ``report_phase`` prints
    the collected coverage tree and exports per-test YAML/XML files.

    Attributes
    ----------
    conf : HammingConf | None
        ConfigDB-shared elaboration geometry (resolved in ``build_phase``).
    _sampler : callable | None
        The registered ``_sample_hamming`` callable from
        :func:`build_hamming_coverage`.
    """

    def __init__(self, name="hamming_coverage", parent=None):
        super().__init__(name, parent)
        self.pins = None    # HammingDutPins
        self.clkrs = None   # ClockReset
        self.conf = None    # HammingConf
        self._sampler = None
        self._items_sampled = 0
        self._run_start_time = time.time()
        self._run_id = os.environ.get("RUN_ID", "").strip()

    def build_phase(self):
        """Resolve the shared DUT config and register the covergroup."""
        super().build_phase()
        self.pins = ConfigDB().get(self, "", KEY_DUT_PINS)
        self.clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
        self.conf = ConfigDB().get(self, "", KEY_CONF)
        if None in (self.pins, self.clkrs, self.conf):
            raise RuntimeError(
                f"{self.get_name()}: missing ConfigDB entries "
                f"(KEY_DUT_PINS={self.pins is not None}, "
                f"KEY_CLK_RST={self.clkrs is not None}, "
                f"KEY_CONF={self.conf is not None}) -- tb_top must share "
                "them before the environment is built"
            )
        self._sampler = build_hamming_coverage(
            self.conf.data_width, self.conf.secded,
        )
        self.logger.info(
            "HammingCoverage built (DATA_WIDTH=%d, SECDED=%d, "
            "CODE_WIDTH=%d)",
            self.conf.data_width, self.conf.secded, self.conf.code_width,
        )

    # -- sampling -------------------------------------------------------
    def write(self, tr):
        """TLM ``write``: sample the covergroup from one monitored
        settled encode operation."""
        payload = {
            "data_in": int(tr.data_in),
            "code_out": int(tr.code_out),
            "data_width": int(tr.data_width),
            "secded": int(tr.secded),
            "code_width": int(tr.code_width),
        }
        self._sampler(payload)
        self._items_sampled += 1

    # -- reporting ------------------------------------------------------
    def report_phase(self):
        """Print and export the collected functional-coverage metrics.

        Per-test unique filenames (``hamming_encoder_coverage_{RUN_ID}_
        {testname}.yml``) preserve each test's contribution for cross-test
        aggregation.  See module docstring for merge semantics.
        """
        super().report_phase()
        self.logger.info(
            "HammingCoverage report: %d items sampled",
            self._items_sampled,
        )
        coverage_db.report_coverage(self.logger.info, bins=True)

        try:
            test_name = os.environ.get("UVM_TESTNAME", "unknown")
            test_safe = test_name.replace(" ", "_")
            run_prefix = f"{self._run_id}_" if self._run_id else ""
            per_test_yaml = (
                f"hamming_encoder_coverage_{run_prefix}{test_safe}.yml"
            )
            per_test_xml = (
                f"hamming_encoder_coverage_{run_prefix}{test_safe}.xml"
            )
            coverage_db.export_to_yaml(filename=per_test_yaml)
            coverage_db.export_to_xml(filename=per_test_xml)
            self.logger.info(
                "HammingCoverage exported to %s / %s",
                per_test_yaml, per_test_xml,
            )
            if self._run_id:
                self.logger.info(
                    "  (run-scoped by RUN_ID=%s)", self._run_id)
            # Generic names for backward compatibility.
            coverage_db.export_to_yaml(
                filename="hamming_encoder_coverage.yml")
            coverage_db.export_to_xml(
                filename="hamming_encoder_coverage.xml")
        except Exception as exc:  # pragma: no cover - filesystem/tooling
            self.logger.warning(
                "HammingCoverage export failed: %s", exc)

        self._merge_per_test_coverage()

    # -- cross-test merge -----------------------------------------------
    def _merge_per_test_coverage(self):
        """Aggregate per-test YAML coverage files into a single report.

        Reads every ``hamming_encoder_coverage_*.yml`` file (excluding the
        generic ``hamming_encoder_coverage.yml``), merges per-bin hit counts
        by taking the maximum across tests, and logs the aggregate
        percentages.  See module docstring for the semantic caveat on
        parameterised bins (``data_in_cov``, ``codeword_cov``).
        """
        import glob as _glob

        try:
            import yaml  # noqa: delayed import
        except ImportError:
            self.logger.warning(
                "HammingCoverage merge: PyYAML not available; "
                "skipping aggregate"
            )
            return

        yml_files = sorted(
            _glob.glob("hamming_encoder_coverage_*.yml")
        )
        yml_files = [
            f for f in yml_files
            if f != "hamming_encoder_coverage.yml"
        ]
        if self._run_id:
            run_prefixed = [
                f for f in yml_files
                if f.startswith(
                    f"hamming_encoder_coverage_{self._run_id}_"
                )
            ]
            if run_prefixed:
                self.logger.info(
                    "HammingCoverage merge: scoping to RUN_ID=%s "
                    "(%d file(s))",
                    self._run_id, len(run_prefixed),
                )
                yml_files = run_prefixed
            else:
                self.logger.info(
                    "HammingCoverage merge: no RUN_ID=%s-scoped "
                    "files found",
                    self._run_id,
                )
                return
        if not yml_files:
            self.logger.info(
                "HammingCoverage merge: no per-test YAML files found"
            )
            return

        stale_count = 0
        fresh_files = []
        for fpath in yml_files:
            try:
                mtime = os.path.getmtime(fpath)
            except OSError:
                continue
            if mtime >= self._run_start_time:
                fresh_files.append(fpath)
            else:
                stale_count += 1
        if stale_count:
            self.logger.warning(
                "HammingCoverage merge: excluded %d stale per-test "
                "file(s)", stale_count,
            )
        yml_files = fresh_files
        if not yml_files:
            self.logger.info(
                "HammingCoverage merge: no fresh per-test files "
                "(%d stale excluded)", stale_count,
            )
            return

        merged = {}
        for fpath in yml_files:
            try:
                with open(fpath) as fh:
                    data = yaml.safe_load(fh) or {}
            except Exception:
                continue
            for key, val in data.items():
                if not isinstance(val, dict):
                    continue
                bin_hits = val.get("bins:_hits")
                if not isinstance(bin_hits, dict):
                    continue
                if "." in key:
                    group_name, point_name = key.split(".", 1)
                else:
                    continue
                if group_name not in merged:
                    merged[group_name] = {}
                if point_name not in merged[group_name]:
                    merged[group_name][point_name] = {}
                for bin_name, hit_count in bin_hits.items():
                    prev = merged[group_name][point_name].get(bin_name, 0)
                    merged[group_name][point_name][bin_name] = max(
                        prev, int(hit_count) if hit_count else 0
                    )

        if not merged:
            self.logger.info(
                "HammingCoverage merge: no data parsed from %d "
                "file(s)", len(yml_files),
            )
            return

        self.logger.info(
            "HammingCoverage aggregate merge from %d per-test "
            "file(s):", len(yml_files),
        )
        total_bins = 0
        hit_bins = 0
        for group_name, points in sorted(merged.items()):
            for pt_name, bins in sorted(points.items()):
                pt_total = len(bins)
                pt_hit = sum(1 for v in bins.values() if v > 0)
                total_bins += pt_total
                hit_bins += pt_hit
                self.logger.info(
                    "  %s.%s: %d/%d bins hit (%.1f%%)",
                    group_name, pt_name, pt_hit, pt_total,
                    100.0 * pt_hit / pt_total if pt_total else 0.0,
                )
        agg_pct = 100.0 * hit_bins / total_bins if total_bins else 0.0
        self.logger.info(
            "HammingCoverage aggregate: %d/%d bins hit "
            "(%.1f%%)", hit_bins, total_bins, agg_pct,
        )
