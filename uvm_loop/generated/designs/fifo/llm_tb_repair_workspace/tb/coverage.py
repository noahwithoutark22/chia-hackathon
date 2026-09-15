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
            boundary_data_roundtrip (din x dout)
"""

from pyuvm import ConfigDB, uvm_subscriber

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db

# The elaborated FIFO parameter defaults (mirror the DUT defaults).  The
# elaborated values are resolved from ConfigDB at build time (CONTRACT.md §4).
DATA_WIDTH_DEFAULT = 8
DEPTH_DEFAULT = 4


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
        "fifo_data_cg.boundary_data_roundtrip",
        items=["fifo_data_cg.write_data_bins", "fifo_data_cg.read_data_bins"],
    )
    def _sample_data(payload):
        """Sample fifo_data_cg: boundary din/dout values and round-trip."""
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
        self._cycles_sampled += 1

    # -- reporting ---------------------------------------------------------
    def report_phase(self):
        """Print and export the collected functional-coverage metrics."""
        super().report_phase()
        self.logger.info(
            "FifoCoverage report: %d DUT cycles sampled", self._cycles_sampled
        )
        coverage_db.report_coverage(self.logger.info, bins=True)
        try:  # export is best-effort (requires PyYAML; guarded for the tool)
            coverage_db.export_to_yaml(filename="fifo_coverage.yml")
            coverage_db.export_to_xml(filename="fifo_coverage.xml")
            self.logger.info(
                "FifoCoverage exported to fifo_coverage.yml / fifo_coverage.xml"
            )
        except Exception as exc:  # pragma: no cover - filesystem/tooling
            self.logger.warning("FifoCoverage export failed: %s", exc)