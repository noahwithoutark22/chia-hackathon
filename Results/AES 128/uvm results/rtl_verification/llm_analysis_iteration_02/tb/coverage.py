"""AES-128 functional coverage (stage-5 COVERAGE artifact).

Implements the plan's ``functional_coverage`` section (covergroups
``cg_start_done_handshake``, ``cg_key_plaintext_patterns`` and
``cg_ciphertext_classes``) *entirely* in Python with the
``cocotb-coverage`` library (``cocotb_coverage.coverage.CoverPoint`` /
``CoverCross`` sampled through the shared, global ``coverage_db``
singleton).  There is no SystemVerilog covergroup anywhere in this project
(CONTRACT.md §8).

The three covergroups (plan names exact):

``top.cg_start_done_handshake``
    start/done handshake bins, sampled every clock cycle from the DUT pins
    (CONTRACT.md §2 pins ``start`` / ``done``) with the established
    mid-cycle falling-edge probe of CONTRACT.md §9.1 (a post-edge rising
    probe of ``start`` is racy with the driver's same-edge deassert):

        start_state   deasserted / asserted
        done_state    no_pulse  / done_pulse
        start_done_cross         (start_state x done_state)

``top.cg_key_plaintext_patterns``
    key/plaintext value classes, sampled from the monitor's published
    :class:`~transaction.Aes128Transaction` items (stage-3 analysis path;
    fields ``key`` / ``plaintext``, CONTRACT.md §5):

        key_pattern        all_zero / all_ones / fips197 / other
        plaintext_pattern  all_zero / all_ones / fips197 / other
        key_plaintext_cross           (key_pattern x plaintext_pattern)

``top.cg_ciphertext_classes``
    observed ciphertext class vs. the mandatory known-answer results
    (CONTRACT.md §3), sampled from the monitor's published items (field
    ``ciphertext``; the value sampled while ``done`` is high):

        ciphertext_class  fips197_ans / all_zero_ans / increment_ans / other

The plan's expression bins (``key == 2**128 - 1``, ``ciphertext ==
0x69c4...`` etc.) are implemented as **bin classifiers** (``xf``): each
128-bit integer is mapped to a small class id that is then matched by
equality against the ``bins`` list, with human-readable ``bins_labels``
matching the plan bin names.  This is the standard CHIA pattern for
cocotb-coverage (the library matches bins by ``rel(xf(sample), bin)`` with
``rel`` defaulting to equality; it has no expression-bin syntax).

SAMPLING SOURCES (two, per the stage rules)
-------------------------------------------
* Item-driven (``Aes128Coverage.write``): the ``uvm_subscriber``'s
  ``analysis_export`` receives every completed transaction the stage-3
  monitor publishes (environment connects ``agent.analysis_port`` to it).
  ``key`` / ``plaintext`` feed ``cg_key_plaintext_patterns`` and
  ``ciphertext`` feeds ``cg_ciphertext_classes`` -- exactly the
  transactions/fields published by the monitor from stage 3.
* Pin-driven (``run_phase``): ``cg_start_done_handshake`` is sampled on
  every clock cycle from ``dut.start`` / ``dut.done`` so the deasserted /
  no-pulse bins (which never appear on a completed monitor item) are
  exercised.  No pins beyond CONTRACT.md §2 are read, and no fields beyond
  CONTRACT.md §5 are invented.

Component contract for the integration (environment) stage:

    def build_phase(): resolves the shared ConfigDB keys ``"dut"`` and the
        optional ``"Aes128DutHelper"`` (CONTRACT.md §4) and builds nothing
        else -- the ``uvm_subscriber`` built-in ``analysis_export`` is the
        analysis sink.
    def connect_monitor(ap): subscribes ``ap`` (the agent's
        ``analysis_port``) to ``self.analysis_export`` -- equivalent to
        ``ap.connect(self.analysis_export)``.
    async def run_phase(): continuous handshake sampler.
    def write(item): item-driven sampling + counters.

End-of-test reporting goes through :func:`report_coverage`,
:func:`coverage_percentage` and :func:`coverage_summary_dict` (all read
the shared ``coverage_db``).

All APIs used here are public Cocotb 2.1.0 (``cocotb.triggers``, handle
``value``) and public pyuvm 5.0.0; ``cocotb_coverage`` 1.2.0 imports no
``cocotb`` symbols.  No SystemVerilog anywhere.
"""

import logging

import cocotb  # noqa: F401  (cocotb.start_soon documented in module docstring)
from cocotb.triggers import FallingEdge, ReadOnly

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from pyuvm import ConfigDB, uvm_subscriber

from transaction import Aes128Transaction

__all__ = [
    "Aes128Coverage",
    "coverage_db",
    "sample_handshake",
    "sample_input_patterns",
    "sample_ciphertext_class",
    "coverage_percentage",
    "coverage_summary_dict",
    "report_coverage",
    "export_coverage_yaml",
    "export_coverage_xml",
]

_log = logging.getLogger("tb.coverage")

# ---------------------------------------------------------------------------
# Plan / CONTRACT constants
# ---------------------------------------------------------------------------

#: Mask for all 128-bit buses (CONTRACT.md §2).
MASK128 = (1 << 128) - 1

#: Coverage tree root (matches the sibling CHIA TBs).
COVERAGE_TOP = "top"

COVERGROUP_HANDSHAKE = f"{COVERAGE_TOP}.cg_start_done_handshake"
COVERGROUP_PATTERNS = f"{COVERAGE_TOP}.cg_key_plaintext_patterns"
COVERGROUP_CIPHERTEXT = f"{COVERAGE_TOP}.cg_ciphertext_classes"

# Plan value-class constants (functional_coverage bins).
KEY_ALL_ZERO = 0x00000000000000000000000000000000
KEY_ALL_ONES = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
KEY_FIPS197 = 0x000102030405060708090A0B0C0D0E0F

PT_ALL_ZERO = 0x00000000000000000000000000000000
PT_ALL_ONES = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
PT_FIPS197 = 0x00112233445566778899AABBCCDDEEFF

CT_FIPS197_ANS = 0x69C4E0D86A7B0430D8CDB78070B4C55A
CT_ALL_ZERO_ANS = 0x66E94BD4EF8A2C3B884CFA59CA342B2E
CT_INCREMENT_ANS = 0x0A940BB5416EF045F1C39458C653EA5A


# ---------------------------------------------------------------------------
# Bin classifiers (plan expression bins -> class ids matched by equality).
# ---------------------------------------------------------------------------
def _classify_key(value: int) -> int:
    """Map a 128-bit key integer to its plan ``key_pattern`` bin id.

    0 = all_zero, 1 = all_ones, 2 = fips197, 3 = other.
    """
    value = int(value) & MASK128
    if value == KEY_ALL_ZERO:
        return 0
    if value == KEY_ALL_ONES:
        return 1
    if value == KEY_FIPS197:
        return 2
    return 3


def _classify_plaintext(value: int) -> int:
    """Map a 128-bit plaintext integer to its plan ``plaintext_pattern`` id.

    0 = all_zero, 1 = all_ones, 2 = fips197, 3 = other.
    """
    value = int(value) & MASK128
    if value == PT_ALL_ZERO:
        return 0
    if value == PT_ALL_ONES:
        return 1
    if value == PT_FIPS197:
        return 2
    return 3


def _classify_ciphertext(value: int) -> int:
    """Map a 128-bit ciphertext integer to its plan ``ciphertext_class`` id.

    0 = fips197_ans, 1 = all_zero_ans, 2 = increment_ans, 3 = other.
    """
    value = int(value) & MASK128
    if value == CT_FIPS197_ANS:
        return 0
    if value == CT_ALL_ZERO_ANS:
        return 1
    if value == CT_INCREMENT_ANS:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Coverpoints / crosses (constructing the decorators registers them in the
# shared coverage_db; CoverCross is built after its CoverPoints exist).
# ---------------------------------------------------------------------------


@CoverPoint(
    name=f"{COVERGROUP_HANDSHAKE}.start_state",
    vname="start",
    bins=[0, 1],
    bins_labels=["deasserted", "asserted"],
)
def _cp_start_state(start):
    """start_state: deasserted (0) / asserted (1)."""


@CoverPoint(
    name=f"{COVERGROUP_HANDSHAKE}.done_state",
    vname="done",
    bins=[0, 1],
    bins_labels=["no_pulse", "done_pulse"],
)
def _cp_done_state(done):
    """done_state: no_pulse (0) / done_pulse (1)."""


@CoverCross(
    name=f"{COVERGROUP_HANDSHAKE}.start_done_cross",
    items=[
        f"{COVERGROUP_HANDSHAKE}.start_state",
        f"{COVERGROUP_HANDSHAKE}.done_state",
    ],
)
def _cross_start_done(start, done):
    """start_done_cross: start asserted with and without a done pulse."""


@CoverPoint(
    name=f"{COVERGROUP_PATTERNS}.key_pattern",
    vname="key",
    xf=_classify_key,
    bins=[0, 1, 2, 3],
    bins_labels=["all_zero", "all_ones", "fips197", "other"],
)
def _cp_key_pattern(key):
    """key_pattern: all_zero / all_ones / fips197 / other."""


@CoverPoint(
    name=f"{COVERGROUP_PATTERNS}.plaintext_pattern",
    vname="plaintext",
    xf=_classify_plaintext,
    bins=[0, 1, 2, 3],
    bins_labels=["all_zero", "all_ones", "fips197", "other"],
)
def _cp_plaintext_pattern(plaintext):
    """plaintext_pattern: all_zero / all_ones / fips197 / other."""


@CoverCross(
    name=f"{COVERGROUP_PATTERNS}.key_plaintext_cross",
    items=[
        f"{COVERGROUP_PATTERNS}.key_pattern",
        f"{COVERGROUP_PATTERNS}.plaintext_pattern",
    ],
)
def _cross_key_plaintext(key, plaintext):
    """key_plaintext_cross: key and plaintext classes in combination."""


@CoverPoint(
    name=f"{COVERGROUP_CIPHERTEXT}.ciphertext_class",
    vname="ciphertext",
    xf=_classify_ciphertext,
    bins=[0, 1, 2, 3],
    bins_labels=["fips197_ans", "all_zero_ans", "increment_ans", "other"],
)
def _cp_ciphertext_class(ciphertext):
    """ciphertext_class: fips197_ans / all_zero_ans / increment_ans / other."""


# ---------------------------------------------------------------------------
# Sampling entry points (called by the collector; the coverpoint wrappers
# must run before the cross wrapper so the cross reads the current sample's
# point hits -- cocotb-coverage correlates the previous CoverPoint calls).
# ---------------------------------------------------------------------------


def sample_handshake(start: int, done: int) -> None:
    """Sample ``cg_start_done_handshake`` from one clock-cycle observation.

    ``start`` / ``done`` are 1-bit integers read mid-cycle (CONTRACT.md
    §9.1 falling-edge probe): ``start`` is the offer the DUT samples on the
    next rising edge; ``done`` is the stable register output of the current
    cycle.
    """
    _cp_start_state(int(start) & 0x1)
    _cp_done_state(int(done) & 0x1)
    _cross_start_done(int(start) & 0x1, int(done) & 0x1)


def sample_input_patterns(key: int, plaintext: int) -> None:
    """Sample ``cg_key_plaintext_patterns`` from one monitor transaction.

    ``key`` / ``plaintext`` are the 128-bit stimulus fields of a completed
    :class:`~transaction.Aes128Transaction` published by the monitor
    (CONTRACT.md §5).
    """
    _cp_key_pattern(int(key) & MASK128)
    _cp_plaintext_pattern(int(plaintext) & MASK128)
    _cross_key_plaintext(int(key) & MASK128, int(plaintext) & MASK128)


def sample_ciphertext_class(ciphertext: int) -> None:
    """Sample ``cg_ciphertext_classes`` from one monitor transaction.

    ``ciphertext`` is the 128-bit output field of a completed transaction
    (the value sampled by the monitor while ``done`` is high).
    """
    _cp_ciphertext_class(int(ciphertext) & MASK128)


# ---------------------------------------------------------------------------
# Coverage collector component (pyuvm uvm_subscriber).
# ---------------------------------------------------------------------------


def _config_get(field, default=None):
    """Retrieve a ConfigDB key using the CONTRACT.md §4 retrieval convention.

    Identical to ``driver.py``/``monitor.py``/``sequences.py``: the
    documented project-wide form is ``ConfigDB().get(None, "*", field)``,
    but the pinned pyuvm 5.0.0 runtime rejects wildcard characters in a
    *retrieval* path; when the primary form raises we fall back to the
    equivalent ``inst_name=""`` retrieval against the same wildcard-stored
    key.  No key or value type is changed.
    """
    try:
        return ConfigDB().get(None, "*", field, default=default)
    except Exception:
        return ConfigDB().get(None, "", field, default=default)


class Aes128Coverage(uvm_subscriber):
    """Coverage collector for the ``aes128`` DUT.

    A pyuvm ``uvm_subscriber`` provides a built-in ``analysis_export``
    (attribute ``self.analysis_export``); the environment stage connects
    ``agent.analysis_port`` to it (or calls :meth:`connect_monitor`).  Every
    completed transaction published by the stage-3 monitor
    (:class:`~monitor.Aes128Monitor`) reaches :meth:`write` and is funnelled
    into the shared ``coverage_db`` via :func:`sample_input_patterns` /
    :func:`sample_ciphertext_class`.

    ``run_phase`` additionally runs the continuous ``cg_start_done_handshake``
    sampler, reading the DUT pins ``start`` / ``done`` (CONTRACT.md §2) with
    the mid-cycle falling-edge probe of CONTRACT.md §9.1 so the sample is
    never racy with the driver's same-edge ``start`` deassert.

    The collector is observation-only: it never drives pins, never raises on
    the DUT's behalf, and never fails the test by itself.
    """

    def __init__(self, name="aes128_coverage", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self._helper = None
        #: Completed transactions processed for item-driven coverage.
        self.sample_count = 0
        #: Clock-cycle observations processed by the handshake sampler.
        self.handshake_samples = 0

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self):
        """Resolve the shared ``dut`` handle (+ optional helper)."""
        super().build_phase()
        self.dut = _config_get("dut")
        if self.dut is None:
            self.logger.warning(
                "%s: 'dut' not found in ConfigDB; item-driven coverage "
                "still works (monitor items carry all sampled fields), but "
                "the cg_start_done_handshake pin sampler is disabled",
                self.get_name(),
            )
            return
        try:
            from dut_helper import Aes128DutHelper
        except Exception:  # pragma: no cover - helper lives next to coverage
            Aes128DutHelper = None
        helper = _config_get("Aes128DutHelper")
        if helper is None and Aes128DutHelper is not None:
            helper = Aes128DutHelper(self.dut)
        self._helper = helper

    def connect_monitor(self, ap):
        """Subscribe a monitor/agent analysis port to this subscriber.

        ``ap.write(datum)`` broadcasts to ``ap.subscribers``, which includes
        ``self.analysis_export`` after this call (pyuvm 5.0.0 broadcast
        model, CONTRACT.md §9.2).  Equivalent to ``ap.connect(
        self.analysis_export)``.
        """
        if ap is None:
            raise ValueError("connect_monitor: analysis port is None")
        ap.connect(self.analysis_export)

    def write(self, item):
        """uvm_subscriber write() -- called for every connected transaction.

        Samples ``cg_key_plaintext_patterns`` and
        ``cg_ciphertext_classes`` from the monitor's published item
        (fields ``key``, ``plaintext``, ``ciphertext`` -- CONTRACT.md §5).
        """
        if not isinstance(item, Aes128Transaction):
            self.logger.error(
                "%s: expected Aes128Transaction on analysis_export, got %s",
                self.get_name(),
                type(item).__name__,
            )
            return
        sample_input_patterns(item.key, item.plaintext)
        sample_ciphertext_class(item.ciphertext)
        self.sample_count += 1
        self.logger.debug(
            "%s: sampled item-driven coverage from %s (%d total)",
            self.get_name(),
            item,
            self.sample_count,
        )

    async def run_phase(self):
        """Sample ``cg_start_done_handshake`` on every clock cycle.

        Uses the CONTRACT.md §9.1 mid-cycle falling-edge probe (``start``
        is the stable offer for the next rising edge; ``done`` is the stable
        register output), so the bin values are identical to what the DUT
        itself observes at the clock.  Runs for the whole simulation like
        the monitor's run_phase loop.
        """
        if self.dut is None:
            self.logger.warning(
                "%s: run_phase -- 'dut' unavailable; "
                "handshake coverage disabled",
                self.get_name(),
            )
            return
        self.logger.info("%s: run_phase started (handshake sampler active)",
                         self.get_name())
        while True:
            await FallingEdge(self.dut.clk)
            await ReadOnly()
            start = self._read_pin("start")
            done = self._read_pin("done")
            sample_handshake(start, done)
            self.handshake_samples += 1

    # ------------------------------------------------------------------
    # Pin sampling helper (defensive, identical to the monitor's).
    # ------------------------------------------------------------------
    def _read_pin(self, name):
        """Read one DUT pin via the CONTRACT.md §2/§4 access path.

        Values are plain ints; a pin still resolving to X/Z at the sample
        point is mapped to 0 with a warning (Cocotb 2.1.0 documented read
        path) so coverage never dies on uninitialised simulation state.
        """
        if self._helper is not None:
            try:
                handle = getattr(self._helper, name)
            except AttributeError:  # pragma: no cover - helper mirrors pins
                handle = getattr(self.dut, name)
        else:
            handle = getattr(self.dut, name)
        try:
            return int(handle.value)
        except ValueError:
            self.logger.warning(
                "%s: pin '%s' not resolvable (X/Z at sample point); "
                "sampling 0",
                self.get_name(), name,
            )
            return 0

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def report(self, logger=None, bins=False):
        """Log the coverage tree; return overall coverage percentage."""
        report_coverage(logger, bins=bins)
        return coverage_percentage()

    def summary(self) -> str:
        """One-line summary for the env/test end-of-test report."""
        return (
            f"Aes128Coverage[{self.get_name()}]: samples={self.sample_count}, "
            f"handshake_samples={self.handshake_samples}, "
            f"overall={coverage_percentage():.1f}%"
        )

    def convert2string(self) -> str:
        return self.summary()


# ---------------------------------------------------------------------------
# Reporting helpers for the integration (environment) stage.
# ---------------------------------------------------------------------------


def coverage_percentage() -> float:
    """Overall coverage across the three covergroups (0.0 -- 100.0)."""
    total_pct = 0.0
    count = 0
    for cg in (COVERGROUP_HANDSHAKE, COVERGROUP_PATTERNS,
               COVERGROUP_CIPHERTEXT):
        node = coverage_db.get(cg)
        if node is not None:
            total_pct += float(node.cover_percentage)
            count += 1
    return total_pct / count if count > 0 else 0.0


def coverage_summary_dict() -> dict:
    """Per-leaf coverage summary over every CoverPoint / CoverCross item."""
    items = []
    total_covered = 0
    total_size = 0
    for name in sorted(coverage_db):
        item = coverage_db[name]
        if isinstance(item, (CoverPoint, CoverCross)):
            total_covered += int(item.coverage)
            total_size += int(item.size)
            items.append({
                "name": name,
                "covered": int(item.coverage),
                "size": int(item.size),
                "percent": float(item.cover_percentage),
            })
    return {
        "items": items,
        "total_covered": total_covered,
        "total_size": total_size,
        "total_percent": (100.0 * total_covered / total_size)
        if total_size else 0.0,
    }


def report_coverage(logger=None, bins: bool = False, node: str = "") -> None:
    """Print the shared ``coverage_db`` (sorted) with optional bin detail.

    ``logger`` is any callable taking one string (e.g. ``print`` or a bound
    ``logging.Logger.info``).
    """
    coverage_db.report_coverage(logger or _log.info, bins=bins, node=node)


def export_coverage_yaml(filename: str = "coverage.yml") -> None:
    """Export the shared ``coverage_db`` to YAML."""
    coverage_db.export_to_yaml(filename=filename)


def export_coverage_xml(filename: str = "coverage.xml") -> None:
    """Export the shared ``coverage_db`` to XML."""
    coverage_db.export_to_xml(filename=filename)