"""Stage 5 (coverage) artifact of the CHIA generator: functional coverage.

Implements the ``functional_coverage`` section of the verification plan for
the i2c_master bench *entirely* in Python with the ``cocotb-coverage``
library (``cocotb_coverage.coverage.CoverPoint`` / ``CoverCross`` sampled
through the shared ``coverage_db``).  There is no SystemVerilog covergroup
and no SVA anywhere in the project (CONTRACT.md section 8).

The plan describes one covergroup, ``transaction_cg``, sampled on each
``done`` pulse to cover the transaction space (direction, slave-address
class, register-address class, write-data patterns, acknowledgment outcome
and read-data patterns), plus three crosses::

    top.transaction_cg.rw_cp
    top.transaction_cg.slave_addr_cp
    top.transaction_cg.reg_addr_cp
    top.transaction_cg.write_data_cp
    top.transaction_cg.ack_error_cp
    top.transaction_cg.read_data_cp
    top.transaction_cg.rw_x_slave_addr
    top.transaction_cg.rw_x_reg_addr
    top.transaction_cg.slave_addr_x_ack_error

Sampling data source (CONTRACT.md stage-3 addition, section 9.1): the
``I2CMonitor`` publishes one :class:`~tb.transaction.I2CTransaction` per
completed transaction (sampled while ``dut.done == 1``).  A monitor item
therefore *is* a "done-pulse sample" of the transaction space, carrying
``rw``, ``slave_addr``, ``reg_addr``, ``write_data`` (stimulus fields) and
``ack_error``, ``read_data`` (observed-output fields).  Sampling coverage
from these items means coverage is inherently sampled only on completed
transactions, exactly as the plan's ``sample_on: done`` requires.

How this is wired (integration stage 6):
``agent.analysis_port`` -> (fan-out) -> ``scoreboard.analysis_export`` and
``coverage.analysis_export``.  ``I2CCoverage`` is a pyuvm
``uvm_subscriber``: its built-in ``analysis_export`` forwards every monitor
item to ``write()``, which funnels the item into the shared coverage
database.  End-of-test reporting uses
``report_transaction_coverage(logger)`` / ``coverage_db``.

Range bins: ``cocotb-coverage`` matches bins by equality against the value
selected by ``vname`` / ``xf``.  The plan's ranged bins (e.g. slave-address
0x00..0x7F grouped into low / supported / high) are therefore expressed as
*bin classifiers* (``xf``) that map the variable to a small class id, with
``bins_labels`` giving the plan's bin names for human-readable reports and
cross-bin tuples.
"""

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from pyuvm import uvm_subscriber

from tb.dut_helper import _to_int
from tb.transaction import I2CTransaction

__all__ = [
    "I2CCoverage",
    "COVERGROUP",
    "coverage_db",
    "sample_transaction",
    "report_transaction_coverage",
    "transaction_coverage_percentage",
]

# ---------------------------------------------------------------------------
# Covergroup node (plan: functional_coverage.covergroups[0].name).
# All coverpoints / crosses live under this node in the shared coverage_db.
# ---------------------------------------------------------------------------
COVERGROUP = "top.transaction_cg"

#: Supported I2C slave address (CONTRACT.md / reference model agreement).
SUPPORTED_SLAVE_ADDR = 0x50

# ---------------------------------------------------------------------------
# Bin classifiers (range -> class id for cocotb-coverage equality bins).
# Returning None means "no bin matched" (the sample is simply not counted;
# exactly like an SV coverpoint bin set that does not include the value).
# ---------------------------------------------------------------------------


def _classify_slave_addr(v):
    """Classify a 7-bit slave address per plan bins:
    ``supported_0x50`` / ``unsupported_low`` (0..0x4F) /
    ``unsupported_high`` (0x51..0x7F)."""
    if int(v) == SUPPORTED_SLAVE_ADDR:
        return 0
    return 1 if int(v) < SUPPORTED_SLAVE_ADDR else 2


def _classify_reg_addr(v):
    """Classify an 8-bit register address per plan bins:
    ``boundary_0x00`` / ``boundary_0xFF`` / ``mid_range`` (1..0xFE)."""
    v = int(v)
    if v == 0x00:
        return 0
    if v == 0xFF:
        return 1
    return 2


def _classify_write_data(v):
    """Classify a write-data byte per plan bins:
    ``data_0x00`` / ``data_0xFF`` / ``data_0x55`` / ``data_0xAA``
    (any other byte is not binned and is not counted)."""
    v = int(v)
    if v == 0x00:
        return 0
    if v == 0xFF:
        return 1
    if v == 0x55:
        return 2
    if v == 0xAA:
        return 3
    return None  # no matching bin


def _classify_read_data(v):
    """Classify a read-data byte per plan bins:
    ``read_zero`` / ``read_pattern_0xAA`` / ``read_pattern_0x55`` /
    ``read_max`` (any other read value is not binned)."""
    v = int(v)
    if v == 0x00:
        return 0
    if v == 0xAA:
        return 1
    if v == 0x55:
        return 2
    if v == 0xFF:
        return 3
    return None  # no matching bin


# ---------------------------------------------------------------------------
# Coverpoints (registered on import into the shared coverage_db).
#
# Decorated functions must be called with *positional* arguments only
# (cocotb-coverage does not accept keyword calls on sampling functions) and
# each one takes exactly the variables it covers, in this fixed order:
# (rw, slave_addr, reg_addr, write_data, ack_error, read_data).
# ---------------------------------------------------------------------------

@CoverPoint(
    f"{COVERGROUP}.rw_cp", vname="rw", bins=[0, 1],
    bins_labels=["write", "read"],
)
def _cp_rw(rw):
    """bin rw_cp: write / read."""


@CoverPoint(
    f"{COVERGROUP}.slave_addr_cp", vname="slave_addr",
    xf=_classify_slave_addr, bins=[0, 1, 2],
    bins_labels=["supported_0x50", "unsupported_low", "unsupported_high"],
)
def _cp_slave_addr(slave_addr):
    """bin slave_addr_cp: supported 0x50 / unsupported low / high."""


@CoverPoint(
    f"{COVERGROUP}.reg_addr_cp", vname="reg_addr",
    xf=_classify_reg_addr, bins=[0, 1, 2],
    bins_labels=["boundary_0x00", "boundary_0xFF", "mid_range"],
)
def _cp_reg_addr(reg_addr):
    """bin reg_addr_cp: boundary 0x00 / 0xFF / mid-range."""


@CoverPoint(
    f"{COVERGROUP}.write_data_cp", vname="write_data",
    xf=_classify_write_data, bins=[0, 1, 2, 3],
    bins_labels=["data_0x00", "data_0xFF", "data_0x55", "data_0xAA"],
)
def _cp_write_data(write_data):
    """bin write_data_cp: 0x00 / 0xFF / 0x55 / 0xAA patterns."""


@CoverPoint(
    f"{COVERGROUP}.ack_error_cp", vname="ack_error", bins=[0, 1],
    bins_labels=["no_nack", "nack"],
)
def _cp_ack_error(ack_error):
    """bin ack_error_cp: no_nack / nack (acknowledgment outcome)."""


@CoverPoint(
    f"{COVERGROUP}.read_data_cp", vname="read_data",
    xf=_classify_read_data, bins=[0, 1, 2, 3],
    bins_labels=[
        "read_zero", "read_pattern_0xAA",
        "read_pattern_0x55", "read_max",
    ],
)
def _cp_read_data(read_data):
    """bin read_data_cp: 0x00 / 0xAA / 0x55 / 0xFF read patterns."""


# ---------------------------------------------------------------------------
# Crosses (plan functional_coverage: crosses).
#
# A cocotb-coverage cross samples the *new hits* of its constituent
# coverpoints on the same sampling event, so the coverpoints above must be
# sampled before the crosses in every ``sample_transaction()`` call.
# ---------------------------------------------------------------------------

@CoverCross(
    f"{COVERGROUP}.rw_x_slave_addr",
    items=[f"{COVERGROUP}.rw_cp", f"{COVERGROUP}.slave_addr_cp"],
)
def _cross_rw_x_slave_addr(rw, slave_addr):
    """Cross direction with slave-address class."""


@CoverCross(
    f"{COVERGROUP}.rw_x_reg_addr",
    items=[f"{COVERGROUP}.rw_cp", f"{COVERGROUP}.reg_addr_cp"],
)
def _cross_rw_x_reg_addr(rw, reg_addr):
    """Cross direction with register-address class."""


@CoverCross(
    f"{COVERGROUP}.slave_addr_x_ack_error",
    items=[f"{COVERGROUP}.slave_addr_cp", f"{COVERGROUP}.ack_error_cp"],
)
def _cross_slave_addr_x_ack_error(slave_addr, ack_error):
    """Cross slave-address class with acknowledgment outcome (NACK must
    correlate with unsupported addresses)."""


# ---------------------------------------------------------------------------
# Sampling entry point (one "done pulse" sample -> whole covergroup).
# ---------------------------------------------------------------------------


def sample_transaction(item):
    """Sample the ``transaction_cg`` covergroup from one monitor item.

    ``item`` is an :class:`~tb.transaction.I2CTransaction` published by
    ``I2CMonitor`` -- i.e. a completed transaction sampled at its ``done``
    pulse (CONTRACT.md stage-3 addition).  All write/read-stimulus fields
    and observed-output fields exist on the item by contract; no DUT pin is
    touched here.

    Coverpoints are sampled first (they feed the crosses), then the crosses.
    """
    if not isinstance(item, I2CTransaction):
        raise TypeError(
            "sample_transaction() requires an I2CTransaction monitor item, "
            f"got {type(item).__name__}"
        )

    rw = _to_int(item.rw, 1)
    slave_addr = _to_int(item.slave_addr, 7)
    reg_addr = _to_int(item.reg_addr, 8)
    write_data = _to_int(item.write_data, 8)
    ack_error = _to_int(item.ack_error, 1)
    read_data = _to_int(item.read_data, 8)

    # Coverpoints first: each records its own `_new_hits` for this sample.
    _cp_rw(rw)
    _cp_slave_addr(slave_addr)
    _cp_reg_addr(reg_addr)
    _cp_write_data(write_data)
    _cp_ack_error(ack_error)
    _cp_read_data(read_data)

    # Crosses second (they consume the coverpoints' `_new_hits`).
    _cross_rw_x_slave_addr(rw, slave_addr)
    _cross_rw_x_reg_addr(rw, reg_addr)
    _cross_slave_addr_x_ack_error(slave_addr, ack_error)


# ---------------------------------------------------------------------------
# Reporting helpers for the integration (environment) stage.
# ---------------------------------------------------------------------------


def transaction_coverage_percentage():
    """Overall covergroup percentage (0.0..100.0) for end-of-test reports."""
    group = coverage_db.get(COVERGROUP)
    if group is None:
        return 0.0
    return float(group.cover_percentage)


def report_transaction_coverage(logger, bins=False):
    """Dump the ``transaction_cg`` coverage tree through ``logger``.

    ``logger`` is a callable (e.g. ``pyuvm_logger.info``); ``bins=True``
    also prints per-bin hit counts.
    """
    coverage_db.report_coverage(logger, bins=bins, node=COVERGROUP)


# ---------------------------------------------------------------------------
# Coverage collector component (pyuvm uvm_subscriber).
# ---------------------------------------------------------------------------


class I2CCoverage(uvm_subscriber):
    """Coverage collector subscribing to the monitor's transaction stream.

    A pyuvm ``uvm_subscriber`` provides a built-in ``analysis_export``
    (attribute ``self.analysis_export``); the integration stage connects
    ``agent.analysis_port`` to it.  Every completed transaction published
    by :class:`~tb.monitor.I2CMonitor` reaches ``write()`` and is funnelled
    into the shared ``coverage_db`` through :func:`sample_transaction`.

    The collector is observation-only: it never drives pins, never raises
    on the DUT's behalf, and never fails the test by itself -- like an SV
    covergroup, it only records and reports what happened.
    """

    def __init__(self, name="i2c_coverage", parent=None):
        super().__init__(name, parent)
        #: Completed (done-pulse) transactions processed as coverage samples.
        self.sample_count = 0

    def write(self, item):
        """uvm_subscriber write() -- called for every connected transaction."""
        if not isinstance(item, I2CTransaction):
            self.logger.error(
                "%s: expected I2CTransaction on analysis_export, got %s",
                self.get_name(), type(item).__name__)
            return
        sample_transaction(item)
        self.sample_count += 1
        self.logger.debug(
            "%s: sampled %s (%d total)", self.get_name(), item,
            self.sample_count)

    def report(self, logger=None, bins=False):
        """Log the covergroup coverage report; defaults to this component's
        logger.  Returns the overall covergroup percentage."""
        log = logger if logger is not None else self.logger.info
        report_transaction_coverage(log, bins=bins)
        return transaction_coverage_percentage()