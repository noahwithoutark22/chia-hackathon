"""SHA-256 functional coverage (stage-5 COVERAGE artifact).

Implements the plan's ``functional_coverage`` covergroups with the
``cocotb-coverage`` library (CONTRACT.md §1/§36-38).  There is no
SystemVerilog covergroup anywhere; every cover object below is a
``cocotb_coverage.coverage`` ``CoverPoint`` / ``CoverCross`` registered in
the shared, global ``coverage_db`` singleton, which is the single coverage
database every component samples.

PLAN MAPPING (verification_plan.yaml ``functional_coverage``):

* ``message_length_cg`` -- coverage of the input message length in bits,
  derived from the ``block[63:0]`` length field (the 64-bit big-endian bit
  length stored at the tail of the pre-padded 512-bit block, CONTRACT.md
  §3) sampled at ``start`` edges (plan ``sample_on: start``):
  ``msg_len_bits`` with bins ``zero_len`` [0,0], ``short_len`` [1,128],
  ``medium_len`` [129,256], ``long_len`` [257,384], ``max_len`` [385,440].
* ``control_signals_cg`` -- coverage of control-signal transitions, sampled
  on every clock edge (plan ``sample_on: clk``): ``start_pulse``
  (#asserted/#deasserted), ``done_pulse`` (#asserted/#deasserted) and the
  ``start_done_cross`` cross over ``(start, done)``.

SAMPLING DRIVER (how the coverage below is fed, per CONTRACT.md §5/§8):

* ``Sha256FunctionalCoverage`` is a plain-Python always-running coroutine
  (started with public Cocotb 2.1.0 ``cocotb.start_soon``) synchronized on
  ``RisingEdge(dut.clk)``.  It reads the exact CONTRACT fields ``start``,
  ``done`` and ``block`` through the shared ``Sha256Pins`` helper
  (ConfigDB key ``"sha256_pins"``, §5) -- the very same fields the stage-3
  monitor captures into ``Sha256Transaction`` (start/block at the start
  edge, done at the fixed-latency completion edge, §12) -- so the coverage
  is driven off the monitor's published transaction field set.  No pins or
  fields beyond CONTRACT.md §3 are invented.
* ``block[63:0]`` is sampled on the cycles where ``start`` is observed high
  (plan ``sample_on: start``); ``start``/``done`` and the cross are sampled
  on every rising edge (plan ``sample_on: clk``).

Cocotb 2.1.0 + pyuvm 5.0.0 compatible; ``cocotb_coverage`` 1.2.0 imports no
``cocotb`` symbols, so it works unchanged on the pinned Cocotb 2.1.0 stack
(the 1.2.0 wheel from the project cache must be installed with
``--no-deps`` alongside Cocotb 2.1.0).
"""

import logging

import cocotb

from cocotb.triggers import RisingEdge

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db

from sha256_pins import Sha256Pins

# ----------------------------------------------------------------------
# Covergroup / coverpoint names (registered under the shared coverage_db).
# ----------------------------------------------------------------------
COVERAGE_TOP = "sha256"

MSG_LEN_CP_NAME = f"{COVERAGE_TOP}.message_length_cg.msg_len_bits"

START_CP_NAME = f"{COVERAGE_TOP}.control_signals_cg.start_pulse"
DONE_CP_NAME = f"{COVERAGE_TOP}.control_signals_cg.done_pulse"
START_DONE_CROSS_NAME = f"{COVERAGE_TOP}.control_signals_cg.start_done_cross"

# Width of the block tail length field (block[63:0]) used by the plan's
# msg_len_bits coverpoint.
LENGTH_FIELD_WIDTH_BITS = 64

# Plan bin ranges for msg_len_bits (message length in BITS).
MSG_LEN_BINS = [
    (0, 0),      # zero_len
    (1, 128),    # short_len
    (129, 256),  # medium_len
    (257, 384),  # long_len
    (385, 440),  # max_len  (single-block SHA-256: unpadded length < 56 bytes)
]
MSG_LEN_BIN_LABELS = ["zero_len", "short_len", "medium_len", "long_len", "max_len"]


# ----------------------------------------------------------------------
# Bin relations
# ----------------------------------------------------------------------
def _in_range(value: int, bin_range: tuple) -> bool:
    """Range-bin relation: a value hits a bin iff min <= value <= max."""
    lo, hi = bin_range
    return lo <= value <= hi


# ----------------------------------------------------------------------
# Coverpoints / cross (decorators; construction also registers them into
# the shared coverage_db).  Decorators are evaluated top-to-bottom, so the
# CoverCross below is constructed after its two CoverPoints already exist
# in coverage_db (required by CoverCross.__init__), and applied innermost,
# which is exactly the ordering that makes the cross correlate the current
# call's point hits.
# ----------------------------------------------------------------------
@CoverPoint(
    name=MSG_LEN_CP_NAME,
    vname="msg_len_bits",
    bins=MSG_LEN_BINS,
    bins_labels=MSG_LEN_BIN_LABELS,
    rel=_in_range,
)
def sample_msg_len(msg_len_bits: int) -> None:
    """Sample ``block[63:0]`` (message length in bits) at a ``start`` edge.

    Covergroup ``message_length_cg`` (plan).  ``block[63:0]`` is the
    64-bit big-endian bit-length field of the pre-padded block; sampling is
    invoked by the coverage driver only on cycles where ``start`` is
    observed high (plan ``sample_on: start``).
    """


@CoverPoint(
    name=START_CP_NAME,
    vname="start",
    bins=[1, 0],
    bins_labels=["asserted", "deasserted"],
)
@CoverPoint(
    name=DONE_CP_NAME,
    vname="done",
    bins=[1, 0],
    bins_labels=["asserted", "deasserted"],
)
@CoverCross(
    name=START_DONE_CROSS_NAME,
    items=[START_CP_NAME, DONE_CP_NAME],
)
def sample_control_signals(start: int, done: int) -> None:
    """Sample ``start`` and ``done`` on every clock edge (plan ``sample_on:
    clk``), including the ``start_done_cross`` over both variables."""


# ----------------------------------------------------------------------
# Coverage sampling driver
# ----------------------------------------------------------------------
class Sha256FunctionalCoverage:
    """Always-running sampler for the plan's functional covergroups.

    NOT a UVM component: a plain-Python coroutine object that reads the DUT
    pins through the shared ``Sha256Pins`` helper and samples the shared
    ``coverage_db`` on every rising edge of ``clk``.
    """

    def __init__(self, pins: Sha256Pins, logger=None) -> None:
        self.pins = pins
        self.log = logger or logging.getLogger("sha256_coverage")
        # Reporting counters (env/test stage may read them).
        self.control_samples = 0     # (start, done) samples taken
        self.length_samples = 0      # block[63:0] samples taken at start

    async def sample_forever(self) -> None:
        """Sample the plan's covergroups on every rising edge of ``clk``.

        First await is a pure sync (no reads at time zero); the driver of
        the environment has already idled the input pins before the first
        sampled edge (CONTRACT.md §11 driver protocol).
        """
        await RisingEdge(self.pins.clk)
        while True:
            await RisingEdge(self.pins.clk)
            start = self._read("start")
            done = self._read("done")
            sample_control_signals(start, done)
            self.control_samples += 1
            if start == 1:
                block = self._read("block")
                msg_len_bits = block & ((1 << LENGTH_FIELD_WIDTH_BITS) - 1)
                sample_msg_len(msg_len_bits)
                self.length_samples += 1

    def start(self):
        """Start the sampler as a background cocotb coroutine."""
        return cocotb.start_soon(self.sample_forever())

    # ------------------------------------------------------------------
    # Pin sampling helpers (defensive: X/Z maps to 0, as in the monitor)
    # ------------------------------------------------------------------
    def _read(self, what: str) -> int:
        reader = {
            "start": self.pins.read_start,
            "block": self.pins.read_block,
            "done": self.pins.read_done,
        }[what]
        try:
            return int(reader())
        except ValueError as exc:
            self.log.warning(
                "Pin '%s' not resolvable (X/Z at sample time) -- sampling 0. %s",
                what,
                exc,
            )
            return 0


# ----------------------------------------------------------------------
# Reports / integration helpers (used by the env/test stage)
# ----------------------------------------------------------------------
def report_coverage(logger=None, bins: bool = False, node: str = "") -> None:
    """Print the shared ``coverage_db`` (sorted) with optional bin detail.

    ``logger`` is any callable taking one string (e.g. ``print`` or a
    ``logging.Logger.info`` bound method).
    """
    coverage_db.report_coverage(logger or print, bins=bins, node=node)


def coverage_summary_dict() -> dict:
    """Coverage summary over the leaf CoverPoint/CoverCross items."""
    items = []
    total_covered = 0
    total_size = 0
    for name in sorted(coverage_db):
        item = coverage_db[name]
        if isinstance(item, (CoverPoint, CoverCross)):
            total_covered += int(item.coverage)
            total_size += int(item.size)
            items.append(
                {
                    "name": name,
                    "covered": int(item.coverage),
                    "size": int(item.size),
                    "percent": float(item.cover_percentage),
                }
            )
    return {
        "items": items,
        "total_covered": total_covered,
        "total_size": total_size,
        "total_percent": (100.0 * total_covered / total_size)
        if total_size
        else 0.0,
    }


def export_coverage_yaml(filename: str = "coverage.yml") -> None:
    """Export the shared coverage_db to YAML (thin public wrapper)."""
    coverage_db.export_to_yaml(filename=filename)


def export_coverage_xml(filename: str = "coverage.xml") -> None:
    """Export the shared coverage_db to XML (thin public wrapper)."""
    coverage_db.export_to_xml(filename=filename)


def start_coverage(pins: Sha256Pins = None) -> Sha256FunctionalCoverage:
    """Build and start the coverage sampler.

    ``pins`` may be passed explicitly or fetched from ConfigDB under the
    exact ``"sha256_pins"`` key (CONTRACT.md §5/§13 retrieval form).
    """
    if pins is None:
        from pyuvm import ConfigDB

        pins = ConfigDB().get(None, "", "sha256_pins")
        if pins is None:
            raise RuntimeError(
                "CONTRACT key 'sha256_pins' missing from ConfigDB: "
                "cannot sample functional coverage."
            )
    sampler = Sha256FunctionalCoverage(pins)
    sampler.start()
    return sampler