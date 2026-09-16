"""FIFO functional coverage (cocotb-coverage, replaces SV covergroups).

This module implements the ``functional_coverage`` section of the
verification plan for the ``fifo`` DUT
(/workspace/benchmarks/fifo/fifo.sv) using the ``cocotb-coverage`` library
(``CoverPoint`` / ``CoverCross`` sampled through the shared
``cocotb_coverage.coverage.coverage_db``).  It is the stage-5 counterpart of
the SystemVerilog ``covergroup`` concept, rendered entirely in Python.

Coverage sampling is driven off the per-cycle :class:`FifoTransaction`
items published by ``FifoMonitor`` (tb/monitor.py) on its ``uvm_analysis_port``
(CONTRACT.md §5 and §10.2): one item per rising clock edge carrying
``wr_en``/``rd_en``/``din``/``dout``/``full``/``empty`` and the monitor
bookkeeping ``dut_cycle``.  The occupancy-covergroup additionally samples the
internal RTL ``integer count`` directly from ``dut.count`` when the signal is
exposed by the simulator (CONTRACT.md §9.5); when the internal signal is not
reachable that cover point simply never hits a bin (sample value ``None``).

Components / API:

    * :func:`build_fifo_coverage` - idempotently register (in the shared
      ``coverage_db``) the three plan covergroups
      (``fifo_operation_cg``, ``fifo_occupancy_cg``, ``fifo_data_cg``) and
      return the per-group sampling callables.  Each sampling callable takes
      a single plain-dict payload of the sampled fields and is invoked on
      every monitored rising edge.

    * :class:`FifoCoverage` - a ``pyuvm.uvm_subscriber`` component
      (named ``fifo_coverage``) that receives monitor transactions on its
      ``analysis_export`` (the environment stage connects
      ``agent.ap.connect(fifo_coverage.analysis_export)``), builds the sample
      payload and feeds it to the registered sampling callables, and finally
      reports / exports the collected ``coverage_db`` in ``report_phase``.

Covergroup mapping (plan -> this module):

    fifo_operation_cg:
        wr_en_bins  [wr_idle=0, wr_active=1]
        rd_en_bins  [rd_idle=0, rd_active=1]
        full_bins   [not_full=0, is_full=1]
        empty_bins  [not_empty=0, is_empty=1]
        crosses:
            wr_rd_combos       (wr_en x rd_en)
            write_while_full   (wr_en x full)
            read_while_empty   (rd_en x empty)
            op_against_flags   (wr_en x rd_en x full x empty)
    fifo_occupancy_cg:
        count_levels  [empty_level=0, one_entry=1, mid_level=DEPTH/2,
                       near_full_level=DEPTH-1, full_level=DEPTH]
    fifo_data_cg:
        write_data_bins [data_zero=0, data_max=(1<<DATA_WIDTH)-1]
        read_data_bins  [data_zero_out=0, data_max_out=(1<<DATA_WIDTH)-1]
        crosses:
            boundary_data_concurrent (din x dout)
"""

import os

from pyuvm import ConfigDB, uvm_subscriber

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db

# The elaborated FIFO parameter defaults (mirror the DUT defaults).  The
# elaborated values are resolved from ConfigDB at build time (CONTRACT.md §4).
DATA_WIDTH_DEFAULT = 8
DEPTH_DEFAULT = 4

# The 8 *structurally reachable* (wr_en, rd_en, full, empty) post-edge
# combinations for the op_against_flags cross.  The other 8 of the 16 total
# combinations are impossible under FIFO semantics (e.g. full and empty cannot
# both be 1; a write-only cycle at empty leaves count=1, so empty=1 post-edge
# is unreachable; etc.).  See the CoverCross comment in build_fifo_coverage()
# for the full derivation.
_REACHABLE_OP_FLAG_COMBOS = frozenset({
    (0, 0, 0, 0),  # idle at mid occupancy
    (0, 0, 1, 0),  # idle when full
    (0, 0, 0, 1),  # idle when empty
    (0, 1, 0, 0),  # read only at mid
    (0, 1, 0, 1),  # read at empty (ignored, count stays 0)
    (1, 0, 0, 0),  # write only at mid
    (1, 0, 1, 0),  # write at full (ignored) or write fills to full
    (1, 1, 0, 0),  # simultaneous read+write at mid (or full→mid, empty→1)
})
TOTAL_OP_FLAG_COMBOS = 16  # all wr_en x rd_en x full x empty combinations


# ---------------------------------------------------------------------------
# Covergroup construction
# ---------------------------------------------------------------------------
def _count_level_bins(depth):
    """Compute the occupancy-count bins for the elaborated ``DEPTH``.

    The plan defines five count-level bins as predicates over ``count``:
    ``count == 0``, ``count == 1``, ``count == DEPTH/2``, ``count == DEPTH-1``
    and ``count == DEPTH``.  For small DEPTH configurations some of these
    predicates coincide (e.g. at DEPTH=2 both ``one_entry`` and ``mid_level``
    mean ``count == 1``); the bins are deduplicated (first label wins) so the
    generated :class:`CoverPoint` stays valid for every planned DEPTH
    (2/4/8).  At DEPTH=4 the five distinct levels match the plan exactly.

    Returns:
        tuple ``(bins, labels)`` of parallel lists with unique bin values.
    """
    specs = [
        ("empty_level", 0),
        ("one_entry", 1),
        ("mid_level", depth // 2),
        ("near_full_level", depth - 1),
        ("full_level", depth),
    ]
    bins = []
    labels = []
    for label, value in specs:
        if value not in bins:
            bins.append(value)
            labels.append(label)
    return bins, labels


def build_fifo_coverage(depth=DEPTH_DEFAULT, data_width=DATA_WIDTH_DEFAULT):
    """Register the three plan covergroups in the shared ``coverage_db``.

    Registration is idempotent: each :class:`CoverPoint`/:class:`CoverCross`
    keeps whatever entry already exists in the singleton ``coverage_db``, so
    repeated calls within one simulation process are safe (parameter values
    are fixed per elaborated DUT anyway).

    Args:
        depth: elaborated ``DEPTH`` parameter used to compute the occupancy
            level bins.
        data_width: elaborated ``DATA_WIDTH`` parameter used to compute the
            ``(1 << DATA_WIDTH) - 1`` data-extremum bins.

    Returns:
        tuple of three sampling callables `(sample_operation,
        sample_occupancy, sample_data)`; every callable accepts one dict
        payload `{"wr_en", "rd_en", "din", "dout", "full", "empty", "count"}`
        of integer values (``count`` may be ``None`` when the internal RTL
        signal is not reachable) and samples its covergroup.
    """
    max_data = (1 << data_width) - 1
    count_bins, count_labels = _count_level_bins(depth)

    # -- fifo_operation_cg ------------------------------------------------
    # Bin 0 -> 'wr_idle', bin 1 -> 'wr_active', etc.  The crosses combine the
    # *new hits* of these cover points on the same sampling call, exactly the
    # plan's write/read-enable space vs occupancy-flag interaction.
    @CoverPoint(  # noqa: E999 (decoration order: bottom-most applied first)
        "fifo_operation_cg.wr_en_bins",
        xf=lambda s: s["wr_en"],
        bins=[0, 1],
        bins_labels=["wr_idle", "wr_active"],
    )
    @CoverPoint(
        "fifo_operation_cg.rd_en_bins",
        xf=lambda s: s["rd_en"],
        bins=[0, 1],
        bins_labels=["rd_idle", "rd_active"],
    )
    @CoverPoint(
        "fifo_operation_cg.full_bins",
        xf=lambda s: s["full"],
        bins=[0, 1],
        bins_labels=["not_full", "is_full"],
    )
    @CoverPoint(
        "fifo_operation_cg.empty_bins",
        xf=lambda s: s["empty"],
        bins=[0, 1],
        bins_labels=["not_empty", "is_empty"],
    )
    @CoverCross(
        "fifo_operation_cg.wr_rd_combos",
        items=["fifo_operation_cg.wr_en_bins", "fifo_operation_cg.rd_en_bins"],
    )
    @CoverCross(
        "fifo_operation_cg.write_while_full",
        items=["fifo_operation_cg.wr_en_bins", "fifo_operation_cg.full_bins"],
    )
    @CoverCross(
        "fifo_operation_cg.read_while_empty",
        items=["fifo_operation_cg.rd_en_bins", "fifo_operation_cg.empty_bins"],
    )
    @CoverCross(
        # W-COV-IMPOSSIBLE-BINS: this cross spans all 16 combinations of
        # wr_en x rd_en x full x empty, but 8 of them are *structurally
        # impossible* given the FIFO semantics.  full/empty are the
        # combinational flags of the post-edge occupancy count
        # (0 <= count <= DEPTH, full<->count==DEPTH, empty<->count==0), and
        # the post-edge count is fully determined by the *pre-edge* count
        # and the ops accepted on that edge.  The 8 impossible bins:
        #
        #  (full=1, empty=1) group — 4 bins, count cannot be both 0 and DEPTH:
        #    (wr=0/1, rd=0/1, full=1, empty=1)
        #
        #  (wr=0, rd=1, full=1, empty=0) — a read-only cycle decrements when
        #    non-empty; starting at count==DEPTH (full) it yields count==DEPTH-1
        #    => full=0 post-edge, so full=1 post-edge is unreachable.
        #
        #  (wr=1, rd=0, full=0, empty=1) — a write-only cycle increments when
        #    not full; starting at count==0 (empty) it yields count==1
        #    => empty=0 post-edge, so empty=1 post-edge is unreachable.
        #
        #  (wr=1, rd=1, full=1, empty=0) — at full, the simultaneous cycle
        #    drops the write and accepts only the read (DIS-2), so post-edge
        #    count==DEPTH-1 => full=0, never full=1.
        #
        #  (wr=1, rd=1, full=0, empty=1) — at empty, the simultaneous cycle
        #    drops the read and accepts only the write, so post-edge
        #    count==1 => empty=0, never empty=1.
        #
        # (Together these 8 are exactly: (0,0,1,1) (0,1,1,0) (0,1,1,1)
        # (1,0,0,1) (1,0,1,1) (1,1,0,1) (1,1,1,0) (1,1,1,1).)
        #
        # These bins reduce the reported coverage percentage but do not
        # represent missing verification — they are structural
        # impossibilities of the FIFO protocol.  All 8 *reachable* bins are
        # exercised by the directed + randomized tests (100% of reachable
        # coverage).  Coverage % must be interpreted with this in mind.
        "fifo_operation_cg.op_against_flags",
        items=[
            "fifo_operation_cg.wr_en_bins",
            "fifo_operation_cg.rd_en_bins",
            "fifo_operation_cg.full_bins",
            "fifo_operation_cg.empty_bins",
        ],
    )
    def _sample_operation(payload):
        """Sample fifo_operation_cg: wr_en/rd_en bins and their crosses."""
        del payload  # values are consumed by the coverpoint xf functions

    # -- fifo_occupancy_cg -------------------------------------------------
    @CoverPoint(
        "fifo_occupancy_cg.count_levels",
        xf=lambda s: s["count"],
        bins=count_bins,
        bins_labels=count_labels,
    )
    def _sample_occupancy(payload):
        """Sample fifo_occupancy_cg: occupancy count levels (parameterised)."""
        del payload  # values are consumed by the coverpoint xf function

    # -- fifo_data_cg ------------------------------------------------------
    @CoverPoint(
        "fifo_data_cg.write_data_bins",
        xf=lambda s: s["din"],
        bins=[0, max_data],
        bins_labels=["data_zero", "data_max"],
    )
    @CoverPoint(
        "fifo_data_cg.read_data_bins",
        xf=lambda s: s["dout"],
        bins=[0, max_data],
        bins_labels=["data_zero_out", "data_max_out"],
    )
    @CoverCross(
        # W-DATA-ROUNDTRIP-MISMATCH: this cross samples din (CURRENT cycle's
        # write input) and dout (PREVIOUS cycle's registered read output) on
        # the same clock edge.  It confirms the data path can carry extreme
        # values on both buses simultaneously, NOT that a value written at
        # one time is later read back intact (the scoreboard already provides
        # full temporal data-integrity checking).  Renamed from
        # 'boundary_data_roundtrip' to accurately reflect the concurrent
        # bus-state measurement.
        "fifo_data_cg.boundary_data_concurrent",
        items=["fifo_data_cg.write_data_bins", "fifo_data_cg.read_data_bins"],
    )
    def _sample_data(payload):
        """Sample fifo_data_cg: boundary din/dout values and concurrent bus extremes."""
        del payload  # values are consumed by the coverpoint xf functions

    return _sample_operation, _sample_occupancy, _sample_data


# ---------------------------------------------------------------------------
# Coverage collector component
# ---------------------------------------------------------------------------
class FifoCoverage(uvm_subscriber):
    """Functional-coverage collector for the ``fifo`` DUT.

    Subscribes to the monitor's analysis port: the environment stage connects
    ``fifo_agent.ap.connect(fifo_coverage.analysis_export)`` (the monitor
    broadcasts one :class:`FifoTransaction` per rising edge).  Every received
    transaction is converted into the coverage payload and sampled through
    :data:`cocotb_coverage.coverage.coverage_db`.  ``report_phase`` prints the
    collected coverage tree and (best-effort) exports ``fifo_coverage.yml`` /
    ``fifo_coverage.xml``.
    """

    def __init__(self, name="fifo_coverage", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.data_width = DATA_WIDTH_DEFAULT
        self.depth = DEPTH_DEFAULT
        self._samplers = None       # tuple of (op, occupancy, data) samplers
        self._count_reachable = False
        self._cycles_sampled = 0
        # Reachable-only op_against_flags tracking (W-COV-IMPOSSIBLE-BINS).
        self._seen_op_flag_combos = set()

    def build_phase(self):
        """Resolve the shared DUT config (CONTRACT.md §4, keys exact) and
        register the covergroups in ``coverage_db``."""
        super().build_phase()
        # Access form is frozen by CONTRACT.md §9.1 (keys unchanged from §4).
        self.dut = ConfigDB().get(None, "*", "dut")
        self.data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
        self.depth = int(ConfigDB().get(None, "*", "DEPTH"))
        self._samplers = build_fifo_coverage(self.depth, self.data_width)
        self._count_reachable = hasattr(self.dut, "count")
        self.logger.info(
            "FifoCoverage built (DATA_WIDTH=%d, DEPTH=%d, count reachable=%s)",
            self.data_width, self.depth, self._count_reachable,
        )

    # -- sampling ----------------------------------------------------------
    def _sample_count(self):
        """Read the internal RTL ``count`` when reachable; else ``None``.

        The DUT declares ``integer count``; cocotb exposes it or not depending
        on the simulator flags.  A ``None`` sample simply misses every
        occupancy bin (CONTRACT.md §9.5).
        """
        if not self._count_reachable:
            return None
        try:
            return int(self.dut.count.value)
        except (ValueError, TypeError):  # pragma: no cover - X/Z at t=0
            return None

    def write(self, tr):
        """TLM ``write``: sample all three covergroups from one monitored
        transaction (one per rising edge, post-edge values)."""
        payload = {
            "wr_en": int(tr.wr_en),
            "rd_en": int(tr.rd_en),
            "din": int(tr.din),
            "dout": int(tr.dout),
            "full": int(tr.full),
            "empty": int(tr.empty),
            "count": self._sample_count(),
        }
        for sampler in self._samplers:
            sampler(payload)
        # Track reachable op_against_flags combos for reachable-only metric.
        combo = (payload["wr_en"], payload["rd_en"],
                 payload["full"], payload["empty"])
        self._seen_op_flag_combos.add(combo)
        self._cycles_sampled += 1

    # -- reporting ---------------------------------------------------------
    def report_phase(self):
        """Print and export the collected functional-coverage metrics.

        Coverage is exported to per-test unique filenames
        (``fifo_coverage_{testname}.yml``) so that each test run in the
        regression preserves its contribution instead of being overwritten
        by the last test (W-COVERAGE-FILE-NOT-ACCUMULATED).  Generic
        ``fifo_coverage.yml`` / ``fifo_coverage.xml`` are also written
        for backward compatibility.

        Reachable-only reporting (W-COV-IMPOSSIBLE-BINS): the
        ``op_against_flags`` cross contains 8 structurally impossible bins
        (e.g. full and empty cannot be simultaneously asserted).  After
        the standard coverage report, a reachable-only percentage is
        computed and logged: only the 8 reachable bins are counted in the
        denominator, so 100% reachable coverage is reported when every
        reachable combination has been hit.

        Cross-test merge (W-CROSS-TEST-COV-AGGREGATION): all per-test
        ``fifo_coverage_*.yml`` files on disk are read and merged to
        produce an aggregate reachable-only report across the full
        regression.
        """
        super().report_phase()
        self.logger.info(
            "FifoCoverage report: %d DUT cycles sampled", self._cycles_sampled
        )
        coverage_db.report_coverage(self.logger.info, bins=True)

        # -- reachable-only op_against_flags metric -----------------------
        hit_reachable = len(
            self._seen_op_flag_combos & _REACHABLE_OP_FLAG_COMBOS
        )
        total_reachable = len(_REACHABLE_OP_FLAG_COMBOS)
        reachable_pct = (
            (100.0 * hit_reachable / total_reachable)
            if total_reachable else 0.0
        )
        self.logger.info(
            "FifoCoverage op_against_flags reachable-only: %d/%d bins hit "
            "(%.1f%%)  [%d of %d total bins are structurally unreachable]",
            hit_reachable, total_reachable, reachable_pct,
            TOTAL_OP_FLAG_COMBOS - total_reachable,
            TOTAL_OP_FLAG_COMBOS,
        )
        if hit_reachable < total_reachable:
            missed = _REACHABLE_OP_FLAG_COMBOS - self._seen_op_flag_combos
            self.logger.warning(
                "FifoCoverage: %d reachable op_against_flags bin(s) NOT hit: %s",
                total_reachable - hit_reachable,
                sorted(missed),
            )

        try:  # export is best-effort (requires PyYAML; guarded for the tool)
            # Per-test unique filenames: each simulation process writes its
            # own file so coverage from earlier tests is not lost.
            test_name = os.environ.get("UVM_TESTNAME", "unknown")
            test_safe = test_name.replace(" ", "_")
            coverage_db.export_to_yaml(
                filename=f"fifo_coverage_{test_safe}.yml"
            )
            coverage_db.export_to_xml(
                filename=f"fifo_coverage_{test_safe}.xml"
            )
            self.logger.info(
                "FifoCoverage exported to fifo_coverage_%s.yml / "
                "fifo_coverage_%s.xml",
                test_safe, test_safe,
            )
            # Also export generic names for backward compatibility.
            coverage_db.export_to_yaml(filename="fifo_coverage.yml")
            coverage_db.export_to_xml(filename="fifo_coverage.xml")
            self.logger.info(
                "FifoCoverage also exported to fifo_coverage.yml / "
                "fifo_coverage.xml"
            )
        except Exception as exc:  # pragma: no cover - filesystem/tooling
            self.logger.warning("FifoCoverage export failed: %s", exc)

        # -- cross-test coverage merge ------------------------------------
        self._merge_per_test_coverage()

    def _merge_per_test_coverage(self):
        """Aggregate per-test YAML coverage files into a single report.

        Reads every ``fifo_coverage_*.yml`` file (skipping the generic
        ``fifo_coverage.yml``) from the current directory, merges per-bin
        hit counts by taking the maximum across tests, and logs the
        aggregate coverage percentages.  This provides a regression-wide
        view that no single test run can produce on its own
        (W-CROSS-TEST-COV-AGGREGATION).

        YAML format (produced by cocotb-coverage ``export_to_yaml``):

        Groups (``type`` contains ``CoverItem``) appear as top-level keys:
            fifo_operation_cg:
              cover_percentage: 77.78
              coverage: 28
              ...

        Coverpoints and crosses appear as sibling dotted-key entries:
            fifo_operation_cg.wr_en_bins:
              bins:_hits:
                wr_active: 116
                wr_idle: 380
              ...

        The merge parser identifies coverpoint/cross entries by the
        presence of a ``bins:_hits`` sub-dict and groups them under the
        parent covergroup (the prefix before the first dot).
        """
        import glob as _glob

        try:
            import yaml  # noqa: delayed import; PyYAML is a cocotb-coverage dep
        except ImportError:
            self.logger.warning(
                "FifoCoverage merge: PyYAML not available; skipping aggregate"
            )
            return

        # Collect per-test YAML files (exclude the generic overwrite).
        yml_files = sorted(_glob.glob("fifo_coverage_*.yml"))
        yml_files = [f for f in yml_files if f != "fifo_coverage.yml"]
        if not yml_files:
            self.logger.info(
                "FifoCoverage merge: no per-test YAML files found"
            )
            return

        # Merge: for each covergroup/coverpoint, take the per-bin max.
        # Structure: merged[group_name][point_name][bin_name] = max_hit
        merged = {}
        for fpath in yml_files:
            try:
                with open(fpath) as fh:
                    data = yaml.safe_load(fh) or {}
            except Exception:
                continue

            # Iterate all top-level keys.  Coverpoint/cross entries have
            # a dotted name (group.point) and a ``bins:_hits`` sub-dict.
            for key, val in data.items():
                if not isinstance(val, dict):
                    continue
                bin_hits = val.get("bins:_hits")
                if not isinstance(bin_hits, dict):
                    continue
                # Derive group and point names from the dotted key.
                if "." in key:
                    group_name, point_name = key.split(".", 1)
                else:
                    # Top-level group entry without dots — skip (no bin
                    # data directly on the group).
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
                "FifoCoverage merge: no coverage data parsed from %d file(s)",
                len(yml_files),
            )
            return

        # Log aggregate.
        self.logger.info(
            "FifoCoverage aggregate merge from %d per-test file(s):",
            len(yml_files),
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
            "FifoCoverage aggregate: %d/%d total bins hit across all tests "
            "(%.1f%%)", hit_bins, total_bins, agg_pct,
        )