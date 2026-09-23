"""i2c_master functional coverage for the cocotb + pyuvm bench (coverage
stage).

Stage-5 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory; it is the authoritative convention record).

Implements the plan's ``functional_coverage`` section *entirely* in Python
with the ``cocotb-coverage`` library (``cocotb_coverage.coverage.CoverPoint``
/ ``CoverCross`` sampled through the shared ``coverage_db``).  There is no
SystemVerilog covergroup and no SVA anywhere in the project (CONTRACT.md
§8).

Two covergroups are implemented under the ``top`` coverage tree:

``top.cg_transaction`` (sampled on transaction_end -- one completed monitor
item per ``done`` pulse)::

    bin_slave_addr   bins addr_min=0 / addr_mid=64 / addr_max=127
    bin_rw           bins write=0 / read=1
    bin_tx_data      bins data_zero=0 / data_mid=128 / data_max=255
    bin_ack_error    bins ack_ok=0 / ack_err=1
    bin_rx_data      bins rx_zero=0 / rx_ones=255
    cross_rw_ack_error        (rw x ack_error)
    cross_addr_rw             (slave_addr x rw)
    cross_data_ack            (tx_data x ack_error)

``top.cg_control_protocol`` (sampled on transaction_end and reset events,
plus the derived control events a per-cycle pin observer raises)::

    bin_done                 bin pulse_seen=1 (done 0->1 edges)
    bin_busy                 bin asserted=1   (busy 0->1 rises)
    bin_start_while_busy     bin hit=1        (start==1 && busy==1 edges)
    bin_reset_injected       bin hit=1        (reset assertion events)
    bin_master_nack          bin observed=1   (sda_in==1 at the read ACK)
    bin_addr_ack             bins ack=0 / nack=1
    bin_data_ack             bins ack=0 / nack=1
    cross_addr_data_ack            (addr_ack x data_ack, write transactions)

BIN GATING (mirrors the golden sibling's transaction-semantics fix, W_04):
``bin_tx_data`` is sampled only for writes (rw == 0), where ``tx_data`` is a
data byte the master actually transmits; for a read it is a don't-care
default and must not fill data-pattern bins.  ``bin_data_ack`` /
``cross_addr_data_ack`` are sampled for writes only (a read has no slave
data-ACK phase -- the master NACKs after the read byte, captured by
``bin_master_nack``).  Where a variable is not applicable for a sample, the
matching coverpoint is sampled with ``None``: it matches no equality bin and
also clears the coverpoint's ``_new_hits`` so a later cross can never be
contaminated by a stale hit from a previous sample (cocotb-coverage
``CoverCross`` consumes the constituents' ``_new_hits``).

ACK-LEVEL DERIVATION (``I2CCoverage``): the ``addr_ack`` / ``data_ack`` /
``master_nack`` levels are *not* DUT pins -- they are the TB-slave's
``sda_in`` timeline at the nominal protocol sample points.  ``I2CCoverage``
runs its own per-cycle ring sampler (mirroring the scoreboard's discipline)
and, per completed item, locates the done 0->1 completion edge in the ring,
derives the acceptance index as ``cc - item.latency_cycles``, and majority-
votes ``sda_in`` (window +/- CLK_DIV/2) at the driver's documented advance
schedule (ADV_ADDR_ACK=10, ADV_DATA_ACK=19; see ``i2c_driver.py`` / CONTRACT
§13.3).  Ties/unknowns skip the affected bins (never guessed).  This is an
*estimative* slot (the plan's own timing note) -- the scoreboard owns the
rigorous alignment; coverage only bins derived protocol outcomes.

CORRUPTED-RTL BEHAVIOR: on the as-shipped RTL no transaction ever completes
(``done`` permanently high -- DIS-15; divider never advances -- DIS-18/19;
``busy`` never rises), so the monitor publishes hung/reset events only and
``cg_transaction`` plus the per-transaction ACK bins stay empty -- that is
the expected *coverage* catch evidence.  The event-driven control bins
still record what happened (``bin_done``[pulse_seen] once for the forced
0->1 done edge after deassert, ``bin_reset_injected`` for every reset
sequence).

WIRING (performed by the ENV in its connect phase, stage 6):
``coverage.connect_monitor(agent.monitor)`` subscribes the monitor's ``ap``
(completed items) and ``reset_ap`` (reset events) analysis ports to the
coverage FIFOs under pyuvm 5.0.0's broadcast model (CONTRACT.md §14.1).
The hung stream (``hung_ap``) carries no completed transactions and is not
consumed by coverage.

ConfigDB: reads the shared ``"dut"`` / ``"i2c_pins"`` keys in
``build_phase`` (exact keys from CONTRACT.md §6).  No new ConfigDB keys are
introduced.  Env-var knobs follow the family convention: ``I2C_CLK_DIV``
(default ``CLK_DIV_DEFAULT``) sets the DUT divider used for sample-point
slotting.

Cocotb 2.1.0 public APIs only: ``cocotb.start_soon``,
``cocotb.triggers.RisingEdge``; no ``cocotb.handle.ModifiableObject``
import.  The module's plain-Python self-check under ``__main__`` exercises
the pure ring helpers without cocotb/pyuvm/cocotb-coverage (sandbox).
"""

import os
from collections import deque

try:  # cocotb is always present at simulation time; the fallback exists
    # only so the pure-Python self-check (__main__) can run in a sandbox
    # that does not have cocotb installed (see i2c_pins.py).
    from cocotb import start_soon
    from cocotb.triggers import RisingEdge

    _COCOTB_AVAILABLE = True
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    start_soon = RisingEdge = None
    _COCOTB_AVAILABLE = False

try:  # cocotb-coverage is present on the simulation worker.
    from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db

    _CCC_AVAILABLE = True
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    CoverCross = CoverPoint = coverage_db = None
    _CCC_AVAILABLE = False

try:  # pyuvm classes are required at simulation time.
    from pyuvm import ConfigDB, uvm_component, uvm_tlm_analysis_fifo

    from i2c_transaction import I2CTransaction

    _PYUVM_AVAILABLE = True
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    ConfigDB = uvm_component = uvm_tlm_analysis_fifo = None
    I2CTransaction = None
    _PYUVM_AVAILABLE = False

# ---------------------------------------------------------------------------
# i2c_pins re-exports cocotb-dependent handle helpers, so it can only be
# imported where cocotb is installed (simulation).  The fallback constants
# below are i2c_pins' documented defaults, kept so the pure-Python
# self-check (__main__) can run in a cocotb-less sandbox.
# ---------------------------------------------------------------------------
try:
    from i2c_pins import (
        CLK_DIV_DEFAULT,
        DONE_TIMEOUT_CYCLES,
        I2CPins,
        KEY_DUT,
        KEY_DUT_PINS,
        _to_int,
    )
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    CLK_DIV_DEFAULT = 4
    DONE_TIMEOUT_CYCLES = 2048
    I2CPins = None
    KEY_DUT = "dut"
    KEY_DUT_PINS = "i2c_pins"
    _to_int = None

# ---------------------------------------------------------------------------
# Intended-protocol advance schedule (CONTRACT.md §13.3, `i2c_driver.py`).
# The coverage component slots its per-transaction ACK samples at these
# nominal indices (advance * CLK_DIV cycles after acceptance), exactly like
# the scoreboard.  Same guarded-import pattern as `i2c_scoreboard.py`.
# ---------------------------------------------------------------------------
try:
    from i2c_driver import (
        ADV_ADDR_ACK,
        ADV_DATA_ACK,
        ADV_DATA_PHASE_START,
    )
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    ADV_ADDR_ACK = 10
    ADV_DATA_ACK = 19
    ADV_DATA_PHASE_START = 11

# ---------------------------------------------------------------------------
# Covergroup nodes in the shared coverage_db (plan covergroup names).
# ---------------------------------------------------------------------------
COVERGROUP_TRANSACTION = "top.cg_transaction"
COVERGROUP_CONTROL = "top.cg_control_protocol"

#: Ring buffer covering one full long transaction plus the monitor's
#: done-wait budget with generous margin (same sizing as the scoreboard).
RING_SIZE = max(8192, 4 * DONE_TIMEOUT_CYCLES + 128)


# ---------------------------------------------------------------------------
# Pure Python ring helpers (unit-testable without cocotb/pyuvm/coverage).
# The component methods are thin wrappers over these module functions so the
# whole sampling math stays testable in a plain-Python sandbox.
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


def _rel_index_for_advance(advance: int, clk_div: int) -> int:
    """Ring-relative index (clock cycles after acceptance) of the nominal
    sample edge for one FSM advance (one advance per CLK_DIV cycles)."""
    return int(advance) * max(1, int(clk_div))


def _ring_get(ring: deque, gi: int) -> dict | None:
    """Return the ring entry with global index ``gi`` or None."""
    for e in reversed(ring):
        if e["gi"] == gi:
            return e
        if e["gi"] < gi:
            return None  # exact index already evicted from history
    return None


def _find_new_done_edge(ring: deque, done_edge_gi: int) -> int | None:
    """Return the global index of the newest unconsumed done 0->1 edge in
    the ring, or None."""
    for e in reversed(ring):
        gi = e["gi"]
        if gi <= done_edge_gi:
            return None
        prev = _ring_get(ring, gi - 1)
        if prev is not None and e["done"] == 1 and prev["done"] == 0:
            return gi
    return None


def _sample_majority(
    ring: deque,
    accept_gi: int,
    rel: int,
    field: str,
    clk_div: int,
) -> int | None:
    """Majority vote of ring ``field`` over [rel-window, rel+window] after
    ``accept_gi``; window defaults to CLK_DIV // 2 (drives' estimative
    slotting, CONTRACT.md §13.3)."""
    half = max(1, int(clk_div)) // 2
    votes = []
    for gi in range(accept_gi + rel - half, accept_gi + rel + half + 1):
        e = _ring_get(ring, gi)
        if e is None:
            continue
        v = e.get(field)
        if v in (0, 1):
            votes.append(v)
    return _majority_bit(votes)


# ---------------------------------------------------------------------------
# Coverpoints / crosses (registered on import into the shared coverage_db).
#
# Decorated functions must be called with *positional* arguments only
# (cocotb-coverage rejects keyword calls on sampling functions).  Each
# coverpoint takes exactly its variable; ``None`` matches no equality bin
# and clears ``_new_hits`` (used for not-applicable samples).
# ---------------------------------------------------------------------------
if _CCC_AVAILABLE:

    @CoverPoint(
        f"{COVERGROUP_TRANSACTION}.bin_slave_addr",
        vname="slave_addr",
        bins=[0, 64, 127],
        bins_labels=["addr_min", "addr_mid", "addr_max"],
    )
    def _t_cp_slave_addr(slave_addr):
        """bin_slave_addr: addr_min=0 / addr_mid=64 / addr_max=127."""

    @CoverPoint(
        f"{COVERGROUP_TRANSACTION}.bin_rw",
        vname="rw",
        bins=[0, 1],
        bins_labels=["write", "read"],
    )
    def _t_cp_rw(rw):
        """bin_rw: write=0 / read=1."""

    @CoverPoint(
        f"{COVERGROUP_TRANSACTION}.bin_tx_data",
        vname="tx_data",
        bins=[0, 128, 255],
        bins_labels=["data_zero", "data_mid", "data_max"],
    )
    def _t_cp_tx_data(tx_data):
        """bin_tx_data: data_zero=0 / data_mid=128 / data_max=255.

        Sampled only for write transactions (rw == 0) in
        :func:`sample_transaction_cg`, so every hit is a byte the master
        actually transmitted (never a read's don't-care default)."""

    @CoverPoint(
        f"{COVERGROUP_TRANSACTION}.bin_ack_error",
        vname="ack_error",
        bins=[0, 1],
        bins_labels=["ack_ok", "ack_err"],
    )
    def _t_cp_ack_error(ack_error):
        """bin_ack_error: ack_ok=0 / ack_err=1 (observed at completion)."""

    @CoverPoint(
        f"{COVERGROUP_TRANSACTION}.bin_rx_data",
        vname="rx_data",
        bins=[0, 255],
        bins_labels=["rx_zero", "rx_ones"],
    )
    def _t_cp_rx_data(rx_data):
        """bin_rx_data: rx_zero=0 / rx_ones=255 (observed read byte)."""

    @CoverCross(
        f"{COVERGROUP_TRANSACTION}.cross_rw_ack_error",
        items=[
            f"{COVERGROUP_TRANSACTION}.bin_rw",
            f"{COVERGROUP_TRANSACTION}.bin_ack_error",
        ],
    )
    def _t_cross_rw_ack_error(rw, ack_error):
        """Cross direction with ACK success/failure."""

    @CoverCross(
        f"{COVERGROUP_TRANSACTION}.cross_addr_rw",
        items=[
            f"{COVERGROUP_TRANSACTION}.bin_slave_addr",
            f"{COVERGROUP_TRANSACTION}.bin_rw",
        ],
    )
    def _t_cross_addr_rw(slave_addr, rw):
        """Cross slave-address class with direction."""

    @CoverCross(
        f"{COVERGROUP_TRANSACTION}.cross_data_ack",
        items=[
            f"{COVERGROUP_TRANSACTION}.bin_tx_data",
            f"{COVERGROUP_TRANSACTION}.bin_ack_error",
        ],
    )
    def _t_cross_data_ack(tx_data, ack_error):
        """Cross write-data extremes with the ACK outcome."""

    # --- control-protocol covergroup ------------------------------------

    @CoverPoint(
        f"{COVERGROUP_CONTROL}.bin_done",
        vname="done",
        bins=[1],
        bins_labels=["pulse_seen"],
    )
    def _c_cp_done(done):
        """bin_done: pulse_seen=1 on each observed done 0->1 edge."""

    @CoverPoint(
        f"{COVERGROUP_CONTROL}.bin_busy",
        vname="busy",
        bins=[1],
        bins_labels=["asserted"],
    )
    def _c_cp_busy(busy):
        """bin_busy: asserted=1 on each observed busy 0->1 rise."""

    @CoverPoint(
        f"{COVERGROUP_CONTROL}.bin_start_while_busy",
        vname="start_while_busy",
        bins=[1],
        bins_labels=["hit"],
    )
    def _c_cp_start_while_busy(start_while_busy):
        """bin_start_while_busy: hit=1 on each start==1 && busy==1 edge."""

    @CoverPoint(
        f"{COVERGROUP_CONTROL}.bin_reset_injected",
        vname="reset_injected",
        bins=[1],
        bins_labels=["hit"],
    )
    def _c_cp_reset_injected(reset_injected):
        """bin_reset_injected: hit=1 on each reset assertion event."""

    @CoverPoint(
        f"{COVERGROUP_CONTROL}.bin_master_nack",
        vname="master_nack",
        bins=[1],
        bins_labels=["observed"],
    )
    def _c_cp_master_nack(master_nack):
        """bin_master_nack: observed=1 when sda_in==1 at the read-ACK
        sample (the master NACKs after a one-byte read)."""

    @CoverPoint(
        f"{COVERGROUP_CONTROL}.bin_addr_ack",
        vname="addr_ack",
        bins=[0, 1],
        bins_labels=["ack", "nack"],
    )
    def _c_cp_addr_ack(addr_ack):
        """bin_addr_ack: ack=0 / nack=1 (sda_in at the address-ACK sample;
        0 = slave pulled the line low = acknowledged)."""

    @CoverPoint(
        f"{COVERGROUP_CONTROL}.bin_data_ack",
        vname="data_ack",
        bins=[0, 1],
        bins_labels=["ack", "nack"],
    )
    def _c_cp_data_ack(data_ack):
        """bin_data_ack: ack=0 / nack=1 (sda_in at the write-data-ACK
        sample; write transactions only)."""

    @CoverCross(
        f"{COVERGROUP_CONTROL}.cross_addr_data_ack",
        items=[
            f"{COVERGROUP_CONTROL}.bin_addr_ack",
            f"{COVERGROUP_CONTROL}.bin_data_ack",
        ],
    )
    def _c_cross_addr_data_ack(addr_ack, data_ack):
        """Cross address-ACK with data-ACK (all four combinations, writes)."""

    # ------------------------------------------------------------------
    # Sampling API
    # ------------------------------------------------------------------

    def sample_transaction_cg(item) -> None:
        """Sample the ``top.cg_transaction`` covergroup from one monitor
        item (a completed transaction sampled at its done pulse).

        ``item`` must be an :class:`I2CTransaction` published by the
        monitor (CONTRACT.md §14.2); ``bin_tx_data`` and
        ``cross_data_ack`` are gated to writes.  Coverpoints are sampled
        first (they feed the crosses), then the crosses.
        """
        if not isinstance(item, I2CTransaction):
            raise TypeError(
                "sample_transaction_cg() requires an I2CTransaction monitor "
                f"item, got {type(item).__name__}"
            )
        if getattr(item, "hung", False):
            # Defensive: hung reports carry no completion and are never
            # sampled into the transaction covergroup.
            return

        rw = _to_int(item.rw, 1)
        slave_addr = _to_int(item.slave_addr, 7)
        tx_data = _to_int(item.tx_data, 8)
        ack_error = _to_int(item.ack_error, 1)
        rx_data = _to_int(item.rx_data, 8)

        # Coverpoints first: each records its own `_new_hits` for this
        # sample.  tx_data is sampled only for writes; for a read it is
        # sampled with None (no bin, and clears `_new_hits`) so the
        # cross_data_ack cannot be contaminated by a stale write-dat
        # hit from a previous sample.
        _t_cp_rw(rw)
        _t_cp_slave_addr(slave_addr)
        if rw == 0:
            _t_cp_tx_data(tx_data)
        else:
            _t_cp_tx_data(None)
        _t_cp_ack_error(ack_error)
        _t_cp_rx_data(rx_data)

        # Crosses second (they consume the coverpoints' `_new_hits`).
        _t_cross_rw_ack_error(rw, ack_error)
        _t_cross_addr_rw(slave_addr, rw)
        _t_cross_data_ack(tx_data, ack_error)

    def sample_control_ack(
        addr_ack: int | None = None,
        data_ack: int | None = None,
        master_nack: int | None = None,
    ) -> None:
        """Sample the per-transaction ACK bins of ``cg_control_protocol``.

        Called at transaction_end with the derived ACK levels.  ``None``
        values are not-applicable and match no bin.  ``bin_data_ack`` and
        ``cross_addr_data_ack`` are sampled only when ``data_ack`` is not
        None (write transactions); read transactions feed ``master_nack``.
        """
        _c_cp_addr_ack(addr_ack) if addr_ack is not None else _c_cp_addr_ack(None)
        if data_ack is not None:
            _c_cp_data_ack(data_ack)
            _c_cross_addr_data_ack(addr_ack, data_ack)
        else:
            # Clear stale data_ack hits so a later write's cross cannot be
            # contaminated by a read transaction's "no data ACK" event.
            _c_cp_data_ack(None)
        if master_nack is not None:
            _c_cp_master_nack(master_nack)
        else:
            _c_cp_master_nack(None)

    def sample_control_done_seen() -> None:
        """Sample bin_done[pulse_seen] (a done 0->1 edge was observed)."""

        _c_cp_done(1)

    def sample_control_busy_seen() -> None:
        """Sample bin_busy[asserted] (a busy 0->1 rise was observed)."""

        _c_cp_busy(1)

    def sample_control_start_while_busy_seen() -> None:
        """Sample bin_start_while_busy[hit] (start asserted while busy)."""

        _c_cp_start_while_busy(1)

    def sample_control_reset_seen() -> None:
        """Sample bin_reset_injected[hit] (a reset assertion event)."""

        _c_cp_reset_injected(1)

    # ------------------------------------------------------------------
    # Reporting helpers (used by the env/test stage)
    # ------------------------------------------------------------------

    def _group_percentage(name: str) -> float:
        group = coverage_db.get(name)
        if group is None:
            return 0.0
        return float(group.cover_percentage)

    def transaction_coverage_percentage() -> float:
        """Overall ``cg_transaction`` percentage (0.0..100.0)."""
        return _group_percentage(COVERGROUP_TRANSACTION)

    def control_coverage_percentage() -> float:
        """Overall ``cg_control_protocol`` percentage (0.0..100.0)."""
        return _group_percentage(COVERGROUP_CONTROL)

    def coverage_percentage() -> float:
        """Mean of the two plan covergroup percentages (0.0..100.0)."""
        return (transaction_coverage_percentage()
                + control_coverage_percentage()) / 2.0

    def report_transaction_coverage(logger, bins: bool = False) -> None:
        """Dump the ``cg_transaction`` tree through ``logger`` (a callable
        such as ``logger.info``); ``bins=True`` prints per-bin hits."""
        coverage_db.report_coverage(
            logger, bins=bins, node=COVERGROUP_TRANSACTION
        )

    def report_control_coverage(logger, bins: bool = False) -> None:
        """Dump the ``cg_control_protocol`` tree through ``logger``."""
        coverage_db.report_coverage(logger, bins=bins, node=COVERGROUP_CONTROL)

    def report_coverage(logger, bins: bool = False) -> None:
        """Dump both plan covergroups through ``logger``."""
        report_transaction_coverage(logger, bins=bins)
        report_control_coverage(logger, bins=bins)


if _PYUVM_AVAILABLE and _CCC_AVAILABLE:

    class I2CCoverage(uvm_component):
        """Coverage collector component for the two plan covergroups.

        ``I2CCoverage`` is a pyuvm ``uvm_component`` (mirroring
        ``I2CScoreboard``'s anatomy): it owns two analysis FIFOs
        (``obs_fifo`` -- completed items on ``ap``; ``reset_fifo`` --
        reset events on ``reset_ap``) fed by the env's connect phase, and a
        per-cycle pin ring sampler that feeds (a) derived per-transaction
        ACK levels (``addr_ack`` / ``data_ack`` / ``master_nack``) and
        (b) the derived control events (done edges / busy rises /
        start-while-busy).  It never drives pins and never fails the test:
        like an SV covergroup, it only records and reports what happened.
        """

        RING_SIZE = RING_SIZE

        def __init__(self, name: str = "i2c_coverage", parent=None) -> None:
            super().__init__(name, parent)
            self.dut = None      # shared cocotb top-level handle (§6)
            self.pins = None     # shared I2CPins handle (§6)
            self.clk_div = CLK_DIV_DEFAULT
            self.obs_fifo = None
            self.reset_fifo = None
            self.ring = deque(maxlen=self.RING_SIZE)
            self.ring_gi = 0
            self.done_edge_gi = -1
            self.sample_count = 0          # completed items sampled
            self.ack_sampled_count = 0     # items with derived ACK levels
            self.ack_skipped_count = 0     # items without derivable ACKs
            self.reset_event_count = 0     # reset events consumed
            self._tasks = []

        # --------------------------------------------------------------
        # UVM phases
        # --------------------------------------------------------------
        def build_phase(self) -> None:
            """Fetch the shared ``dut`` / ``i2c_pins`` handles (§6) and
            build the two analysis FIFOs."""
            super().build_phase()
            self.dut = ConfigDB().get(None, "", KEY_DUT)
            self.pins = ConfigDB().get(None, "", KEY_DUT_PINS)
            if not isinstance(self.pins, I2CPins):
                self.logger.warning(
                    f"ConfigDB['{KEY_DUT_PINS}'] is not an I2CPins: "
                    f"{self.pins!r}"
                )
            self.clk_div = max(
                1, int(os.environ.get("I2C_CLK_DIV", CLK_DIV_DEFAULT))
            )
            self.obs_fifo = uvm_tlm_analysis_fifo("i2c_cov_obs_fifo", self)
            self.reset_fifo = uvm_tlm_analysis_fifo("i2c_cov_reset_fifo", self)
            self.logger.info(
                f"i2c_coverage ready (clk_div={self.clk_div}, "
                f"ring_size={self.RING_SIZE})"
            )

        def connect_monitor(self, monitor) -> None:
            """Subscribe the monitor's ``ap`` and ``reset_ap`` analysis
            ports to the coverage FIFOs.

            Accepts the agent's monitor (``agent.monitor``) or an agent
            object (resolved via ``.monitor``).  The hung stream
            (``hung_ap``) carries no completed transactions and is not
            consumed by coverage (documented in the module docstring).
            """
            src = getattr(monitor, "monitor", monitor)
            if src is None:
                raise ValueError("connect_monitor: no monitor/agent given")
            ports = (("ap", self.obs_fifo), ("reset_ap", self.reset_fifo))
            for port_name, fifo in ports:
                port = getattr(src, port_name, None)
                if port is None:
                    raise ValueError(
                        f"connect_monitor: source has no '{port_name}' "
                        "analysis port"
                    )
                port.connect(fifo.analysis_export)
            self.logger.info(
                "connected monitor ap/reset_ap -> coverage FIFOs"
            )

        async def run_phase(self) -> None:
            """Run the three parallel consumers/samplers.

            All three are started with public Cocotb 2.1.0
            ``cocotb.start_soon``; ``run_phase`` awaits the primary
            consumer (completed items), which never returns during the
            simulation.  pyuvm terminates all phase tasks when the test
            ends (family pattern, CONTRACT.md §15).
            """
            tasks = [
                start_soon(self._consume_transactions()),
                start_soon(self._consume_resets()),
                start_soon(self._sample_pin_events()),
            ]
            self._tasks = tasks
            await tasks[0]

        # --------------------------------------------------------------
        # Consumers / samplers
        # --------------------------------------------------------------
        async def _consume_transactions(self) -> None:
            """Consume completed ``I2CTransaction`` items in order and
            sample both covergroups."""
            while True:
                item = await self.obs_fifo.get_peek_export.get()
                self.sample_count += 1
                try:
                    sample_transaction_cg(item)
                except Exception as exc:  # noqa: BLE001 - never kill the
                    # consumer; report and keep going.
                    self.logger.error(
                        "transaction coverage sample failed: %s", exc
                    )
                if self.pins is not None:
                    levels = await self._derive_ack_levels(item)
                    if levels is None:
                        self.ack_skipped_count += 1
                    else:
                        self.ack_sampled_count += 1
                        addr_ack, data_ack, master_nack = levels
                        try:
                            sample_control_ack(addr_ack, data_ack, master_nack)
                        except Exception as exc:  # noqa: BLE001
                            self.logger.error(
                                "control coverage sample failed: %s", exc
                            )
                else:
                    self.ack_skipped_count += 1

        async def _consume_resets(self) -> None:
            """Consume ``I2CResetEvent`` notifications; every assertion
            samples ``bin_reset_injected``."""
            while True:
                event = await self.reset_fifo.get_peek_export.get()
                self.reset_event_count += 1
                if str(getattr(event, "kind", "?")) == "asserted":
                    sample_control_reset_seen()
                self.logger.debug(f"coverage reset event: {event}")

        async def _sample_pin_events(self) -> None:
            """One per-cycle pin observation: ring append plus derived
            control-event detection (done edge / busy rise /
            start-while-busy).  Only reads pins (passive)."""
            if self.pins is None:
                self.logger.error(
                    "pin event sampler disabled: no I2CPins handle in "
                    "ConfigDB"
                )
                return
            prev_done = 0
            prev_busy = 0
            while True:
                await RisingEdge(self.pins.clk)
                self._ring_append()
                done = self.pins.read_done()
                busy = self.pins.read_busy()
                if done == 1 and prev_done == 0:
                    sample_control_done_seen()
                if busy == 1 and prev_busy == 0:
                    sample_control_busy_seen()
                if self.pins.read_start() == 1 and busy == 1:
                    sample_control_start_while_busy_seen()
                prev_done = done
                prev_busy = busy

        # --------------------------------------------------------------
        # Ring helpers (thin wrappers over the pure module functions)
        # --------------------------------------------------------------
        def _ring_append(self) -> None:
            self.ring.append(
                {
                    "gi": self.ring_gi,
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
            self.ring_gi += 1

        def _ring_get(self, gi: int) -> dict | None:
            return _ring_get(self.ring, gi)

        def _find_new_done_edge(self) -> int | None:
            return _find_new_done_edge(self.ring, self.done_edge_gi)

        def _sample_majority(
            self, accept_gi: int, rel: int, field: str
        ) -> int | None:
            return _sample_majority(
                self.ring, accept_gi, rel, field, self.clk_div
            )

        async def _derive_ack_levels(self, item):
            """Derive (addr_ack, data_ack, master_nack) for one completed
            item from the sampler ring, or None when the item cannot be
            aligned (never guessed).

            Locates the newest unconsumed done 0->1 edge (retried a few
            clock edges to let the sampler catch up) and slots the driver's
            advance schedule after the derived acceptance index.
            """
            latency = max(0, int(getattr(item, "latency_cycles", 0) or 0))
            cc = self._find_new_done_edge()
            for _retry in range(3):
                if cc is not None:
                    break
                await RisingEdge(self.pins.clk)
                cc = self._find_new_done_edge()
            if cc is None:
                return None
            self.done_edge_gi = cc
            accept_gi = cc - latency
            if accept_gi < 0:
                self.logger.debug(
                    f"txn_id={item.txn_id}: completion edge (gi={cc}) "
                    f"precedes acceptance (latency_cycles={latency}); "
                    "ACK bins skipped"
                )
                return None
            cdiv = max(1, self.clk_div)
            addr_ack = self._sample_majority(
                accept_gi, _rel_index_for_advance(ADV_ADDR_ACK, cdiv),
                "sda_in",
            )
            if item.is_read:
                master_nack = self._sample_majority(
                    accept_gi, _rel_index_for_advance(ADV_DATA_ACK, cdiv),
                    "sda_in",
                )
                return (addr_ack, None, master_nack)
            data_ack = self._sample_majority(
                accept_gi, _rel_index_for_advance(ADV_DATA_ACK, cdiv),
                "sda_in",
            )
            return (addr_ack, data_ack, None)

        # --------------------------------------------------------------
        # Reporting API (read by the env/test stage)
        # --------------------------------------------------------------
        def get_summary_dict(self) -> dict:
            """Return the coverage counters and percentages as a dict."""
            return {
                "sample_count": self.sample_count,
                "ack_sampled_count": self.ack_sampled_count,
                "ack_skipped_count": self.ack_skipped_count,
                "reset_event_count": self.reset_event_count,
                "transaction_percentage": transaction_coverage_percentage(),
                "control_percentage": control_coverage_percentage(),
                "coverage_percentage": coverage_percentage(),
            }

        def get_summary(self) -> str:
            """Compact single-line coverage summary."""
            s = self.get_summary_dict()
            return (
                f"I2CCoverage[{self.get_name()}]: "
                f"samples={s['sample_count']} "
                f"ack_derived={s['ack_sampled_count']} "
                f"ack_skipped={s['ack_skipped_count']} "
                f"resets={s['reset_event_count']} "
                f"txn_cg={s['transaction_percentage']:.1f}% "
                f"ctrl_cg={s['control_percentage']:.1f}% "
                f"overall={s['coverage_percentage']:.1f}%"
            )

        def convert2string(self) -> str:
            return self.get_summary()


# ---------------------------------------------------------------------------
# Plain-Python self-checks (no simulator / pyuvm / cocotb-coverage needed).
# The pure ring helpers are exercised; the decorated samplers and the
# pyuvm component require the simulation worker's stack and are skipped
# here.
# ---------------------------------------------------------------------------
def _self_test_pure_ring_helpers() -> None:
    assert _majority_bit([]) is None
    assert _majority_bit([0, 0, 1]) == 0
    assert _majority_bit([1, 1, 0]) == 1
    assert _majority_bit([0, 1]) is None
    assert _majority_bit([None, None, 1, 1, 0]) == 1
    assert _majority_bit([None, None]) is None

    # Advance schedule slotting (advance * CLK_DIV).
    assert _rel_index_for_advance(0, 4) == 0
    assert _rel_index_for_advance(10, 4) == 40
    assert _rel_index_for_advance(19, 16) == 304
    assert _rel_index_for_advance(2, 1) == 2

    # Synthetic ring: 4 idle cycles, acceptance at gi=4, active, then a
    # done 0->1 pulse at gi=10 and idle after (scoreboard-style timeline).
    def _entry(gi, done=0, busy=0, sda_in=1):
        return {
            "gi": gi, "sda_in": sda_in, "sda_out": 1, "sda_oe": 0,
            "scl_out": 1, "scl_oe": 0, "sda_level": 1, "scl_level": 1,
            "done": done, "busy": busy, "ack_error": 0, "rx_data": 0,
            "rst": 1,
        }

    ring = deque(maxlen=8192)
    gi = 0
    for _ in range(4):
        ring.append(_entry(gi))
        gi += 1
    ring.append(_entry(4, busy=1))                                      # acceptance
    gi += 1
    for _ in range(5):                                                  # active 5..9
        ring.append(_entry(gi, busy=1))
        gi += 1
    ring.append(_entry(10, done=1, busy=0))                             # pulse
    ring.append(_entry(11, done=0, busy=0))

    assert _find_new_done_edge(ring, -1) == 10
    assert _find_new_done_edge(ring, 10) is None   # consumed

    # Ring lookup by global index.
    assert _ring_get(ring, 10)["done"] == 1
    assert _ring_get(ring, 0)["done"] == 0
    assert _ring_get(ring, -5) is None

    # Majority sampling of sda_in at rel index 40 (accept gi=4 -> gi=44
    # does not exist) yields None (unknown), while rel 6 (gi=10) with the
    # line high yields 1.
    assert _sample_majority(ring, 4, 6, "sda_in", 4) == 1
    assert _sample_majority(ring, 4, 40, "sda_in", 4) is None

    print("i2c_coverage: pure ring-helper self-check OK")


if __name__ == "__main__":
    _self_test_pure_ring_helpers()