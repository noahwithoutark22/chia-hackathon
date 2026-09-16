"""Stage 4 (check) artifact of the CHIA generator: the pyuvm scoreboard.

``I2CScoreboard`` is the pass/fail oracle of the bench.  It subscribes to
the agent's monitor stream (``I2CMonitor.analysis_port`` ->
``I2CAgent.analysis_port`` -> ``scoreboard.analysis_export``) and scores
every completed transaction against the *independent* Python reference
model (CONTRACT.md section 7)::

    expected = I2CReferenceModel().transact(
        item.rw, item.slave_addr, item.reg_addr, item.write_data)

and compares the monitor's sampled outputs (taken while ``done == 1``,
CONTRACT.md sections 6/9) field by field.

**Comparison scope** (stage-6 consistency pass, CONTRACT.md section 12;
authoritative rule from the plan's ``scoreboard_reference_model_strategy``):
``ack_error``, ``busy``, and completion behaviour are compared for *every*
transaction; ``read_data`` is compared only where the plan gives it defined
semantics:

* supported-address **reads** -- must equal the model's memory value
  (``0x00`` if never written);
* **unsupported-address** transactions (write *and* read) -- must equal
  ``0x00``;
* supported-address **writes** -- the specification leaves ``read_data``
  during a write unspecified (it is "data returned by a read"), so the byte
  is verified through later reads instead and ``read_data`` is **not**
  compared on supported writes.  Sampling the stale value the RTL retains
  across writes is therefore *not* a defect (I2C_DISC_001 concerns only
  unsupported-address transactions).

Design rules honoured here:

* The scoreboard is pure observation: it drives no pins, hands out no
  stimulus, and runs no transactions of its own.
* It never reimplements behavior; it only feeds the reference model and
  compares.  Any expected/observed mismatch is a genuine DUT-vs-model
  divergence and is logged as an error and raised immediately (failing
  the enclosing cocotb test, per CONTRACT.md section 8).
* The reference model memory is cleared whenever ``rst_n`` is asserted
  (reset-equivalent clearing -- CONTRACT.md section 3's remedy for the
  documented RTL-vs-model memory divergence).  A small always-running
  watcher coroutine (``_watch_reset``) taps the shared ``I2CDutPins``
  handle on the falling edge of the active-low asynchronous reset and
  calls ``I2CReferenceModel.reset()`` so model state tracks the bench's
  resets (scenario start-up resets and the randomized sequence's
  mid-flight reset injection).
* Because ``I2CMonitor`` drops aborted (reset-struck) in-flight
  transactions instead of publishing them (CONTRACT.md section 9.1),
  every item this scoreboard receives is a *completed* transaction; the
  scoreboard therefore never needs to pair monitor items with sequence
  items 1:1.
* Counters (``item_count``, ``matched_count``, ``failed_count``,
  ``reset_count``) are exposed for the environment's end-of-test report.
"""

from cocotb.triggers import FallingEdge
from pyuvm import uvm_scoreboard, uvm_analysis_export, ConfigDB

from tb.dut_helper import KEY_DUT_PINS, _to_int
from tb.transaction import I2CTransaction, SUPPORTED_SLAVE_ADDR

# Reference model (independent oracle).  Depending on the run layout the
# repository root or the benchmark directory is on sys.path; try both
# (mirrors tb/sequences.py).
try:  # pragma: no cover - environment-dependent
    from benchmarks.i2c_benchmark.i2c_reference_model import I2CReferenceModel
except ImportError:  # pragma: no cover - environment-dependent
    from i2c_reference_model import I2CReferenceModel

__all__ = ["I2CScoreboard"]


class I2CScoreboard(uvm_scoreboard):
    """Scores monitored I2C transactions against the reference model.

    Attributes:
        analysis_export (`uvm_analysis_export` subclass): the TLM sink the
            environment connects to ``agent.analysis_port``.
        model (I2CReferenceModel): the independent oracle instance.
        item_count (int): completed transactions received.
        matched_count (int): transactions whose outputs matched the model.
        failed_count (int): transactions that raised a mismatch.
        reset_count (int): ``rst_n`` assertions observed by the reset
            watcher.
    """

    # ------------------------------------------------------------------
    # Analysis export: forwards monitor items to _on_monitor_item()
    # (the pyuvm uvm_subscriber.uvm_AnalysisImp pattern restated on a
    # `uvm_scoreboard` base, which provides no export of its own).
    # ------------------------------------------------------------------
    class _AnalysisExport(uvm_analysis_export):

        def __init__(self, name, parent, write_fn):
            super().__init__(name, parent)
            self._write_fn = write_fn

        def write(self, datum):
            self._write_fn(datum)

    def __init__(self, name="i2c_scoreboard", parent=None, model=None):
        super().__init__(name, parent)
        self.analysis_export = self._AnalysisExport(
            "analysis_export", self, self._on_monitor_item)
        # Injectable oracle for tests; independent instance by default.
        self.model = model if model is not None else I2CReferenceModel()
        self.item_count = 0
        self.matched_count = 0
        self.failed_count = 0
        self.reset_count = 0
        self.pins = None

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        self.pins = ConfigDB().get(self, "", KEY_DUT_PINS)

    async def run_phase(self):
        """Keep the model's virtual memory in sync with DUT resets.

        ``rst_n`` is the active-low asynchronous reset (CONTRACT.md section
        3).  Every assertion of the reset applies the documented
        reset-equivalent clearing to the reference model so the oracle
        mirrors the semantics the sequences are authored against (the
        randomized sequence, in particular, only reads registers written
        after the most recent reset).
        """
        while True:
            await FallingEdge(self.pins.rst_n)
            self.model.reset()
            self.reset_count += 1
            self.logger.info(
                "%s: rst_n asserted -> reference model memory cleared"
                " (%d so far)", self.get_name(), self.reset_count)

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------
    def _on_monitor_item(self, item):
        """Score one completed monitor item against the reference model.

        Called synchronously from the monitor coroutine (analysis
        semantics); raising an :class:`AssertionError` here propagates to
        the monitor's ``run_phase`` and fails the enclosing cocotb test
        immediately (CONTRACT.md section 8).
        """
        if not isinstance(item, I2CTransaction):
            raise AssertionError(
                f"{self.get_name()}: expected I2CTransaction on "
                f"analysis_export, got {type(item).__name__}")

        self.item_count += 1

        # The monitor only publishes completed transactions sampled while
        # `done == 1`; anything else indicates a monitor bug.
        if _to_int(item.done, 1) != 1:
            raise AssertionError(
                f"{self.get_name()}: monitor item without done pulse "
                f"({item})")

        expected = self.model.transact(
            item.rw, item.slave_addr, item.reg_addr, item.write_data)

        # read_data has defined semantics (plan scoreboard strategy) only for
        # supported-address reads (model memory) and unsupported-address
        # transactions (0x00); it is deliberately NOT compared for supported
        # writes (spec leaves it unspecified; the byte is verified through
        # later reads).
        compare_read_data = (
            int(item.slave_addr) != SUPPORTED_SLAVE_ADDR or int(item.rw) == 1)

        checks = (
            ("busy", _to_int(item.busy, 1),
             int(expected["busy_after"])),
            ("ack_error", _to_int(item.ack_error, 1),
             int(expected["ack_error"])),
        )
        if compare_read_data:
            checks = checks + (
                ("read_data", _to_int(item.read_data, 8),
                 int(expected["read_data"])),
            )
        for field, got, want in checks:
            if got != want:
                self.failed_count += 1
                self.logger.error(
                    "%s: MISMATCH field=%s (item %s): expected %#x, "
                    "observed %#x",
                    self.get_name(), field, item, int(want), int(got))
                raise AssertionError(
                    f"{self.get_name()}: {field} mismatch: model said "
                    f"{want:#x}, DUT returned {got:#x} ({item})")

        # Model/observations agree; the model already applied any write
        # side effect inside transact().
        self.matched_count += 1
        self.logger.debug(
            "%s: match #%d: %s", self.get_name(), self.matched_count, item)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def summarize(self):
        """One-line result summary for the environment's end-of-test log."""
        return (
            f"{self.get_name()}: {self.item_count} items, "
            f"{self.matched_count} matched, {self.failed_count} failed, "
            f"{self.reset_count} resets observed"
        )