"""hamming_encoder pyuvm scoreboard (stage 4: SCOREBOARD).

``HammingScoreboard`` implements the checker side of the cocotb + pyuvm
testbench: it consumes the :class:`~tb.transaction.HammingTransaction`
items published by :class:`~tb.monitor.HammingMonitor` -- exactly one per
settled encode operation, carrying precisely the fields of CONTRACT.md
section 5 -- and compares the DUT's sampled ``code_out`` bit-for-bit
against the authoritative Python golden model ``hamming_encode`` from
``benchmarks/hamming_encoder/ref_model.py``.

Strategy (``scoreboard_reference_model_strategy``, plan and CONTRACT.md
section 7-8):

* *python_golden_predictor*: for every consumed item the scoreboard calls
  ``hamming_encode(data_in, data_width, secded)`` (exact argument order
  of section 7 -- never reimplemented, never adapted on mismatch) and
  obtains ``(expected_code_out, HammingParams)``.  ``params.code_width``
  width-checks and masks the sampled ``code_out``.

* *sample_compare*: the monitor samples ``data_in`` and ``code_out`` at
  the *same* virtual-cycle boundary -- the combinational settle instant of
  the transaction (latency 0, section 8).  A monitor item therefore
  already pairs the driven input with its settled output and no timestamp
  deskewing is needed: ``get()`` from the analysis FIFO and the
  comparison happen with no simulation time advancing in between.

The relationship between input and output is the *single-cycle
combinational* one, NOT a pipeline::

    expected, params = hamming_encode(item.data_in, item.data_width,
                                      item.secded)
    mask = (1 << params.code_width) - 1
    assert (expected & mask) == (item.code_out & mask)   # bit-exact

The DUT has **no** ``clk`` and **no** reset port; ``code_out`` is a pure
function of ``data_in`` and ``tb_reset`` only reinitializes environment
state (sections 2-3).  Consequently the scoreboard's predictor is
stateless (each check is self-contained) and the scoreboard never samples
``dut.clk`` / ``dut.tb_reset`` -- nor any other DUT pin beyond the live
snapshot used for error reporting.

Failure reporting / pass criteria (plan ``error_reporting``): on any bit
difference the scoreboard logs, at error severity, ``data_in``,
``DATA_WIDTH``, ``SECDED``, expected ``code_out``, actual ``code_out``,
the differing bit indices and a best-effort live pin snapshot, counts the
error into the per-(DATA_WIDTH, SECDED) statistics, and raises
``AssertionError`` -- failing the current test immediately.  A clean run
is summarised per configuration at ``report_phase``.

The watchdog (CONTRACT.md section 9) is owned by the stage-5
coverage/assertions module (same split as the FIFO bench); the scoreboard
deliberately does not host it.
"""

from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo

from tb.dut_helper import (
    KEY_CLK_RST,
    KEY_CONF,
    KEY_DUT_PINS,
)
from tb.transaction import HammingTransaction

# Authoritative Python reference model (CONTRACT.md section 7).  A
# byte-for-byte copy lives at tb/ref_model.py beside the other TB modules
# (same convention as the FIFO bench); import it from the copy first and
# fall back only for alternate run layouts.  The model is the single
# arithmetic/behavior oracle -- it is called, never reimplemented, and a
# DUT mismatch never causes it to be adapted.
try:  # pragma: no cover - import-path selection
    from tb.ref_model import HammingParams, hamming_encode
except ImportError:  # pragma: no cover - import-path selection
    try:
        from benchmarks.hamming_encoder.ref_model import (  # type: ignore
            HammingParams,
            hamming_encode,
        )
    except ImportError:  # pragma: no cover - import-path selection
        try:
            from hamming_encoder.ref_model import (  # type: ignore
                HammingParams,
                hamming_encode,
            )
        except ImportError:  # pragma: no cover - import-path selection
            from ref_model import HammingParams, hamming_encode  # type: ignore

__all__ = ["HammingScoreboard"]


def _bin(value, width):
    """MSB-first binary string of *value* padded/truncated to *width*."""
    if width <= 0:
        return "()"
    return format(value, f"0{width}b")


class HammingScoreboard(uvm_scoreboard):
    """Predictor-style scoreboard comparing DUT ``code_out`` to
    ``hamming_encode`` bit-exactly.

    Attributes
    ----------
    pins : HammingDutPins | None
        ConfigDB-shared pin helper (resolved in ``build_phase``; used only
        for best-effort live error snapshots).
    clkrs : ClockReset | None
        ConfigDB-shared virtual clock/reset descriptor (resolved for the
        section 6 key contract; the scoreboard paces nothing itself).
    conf : HammingConf | None
        ConfigDB-shared active elaboration geometry (``DATA_WIDTH`` /
        ``SECDED`` / derived widths).
    analysis_fifo : uvm_tlm_analysis_fifo | None
        Buffers monitor items; the env connects
        ``agent.monitor_ap`` -> ``analysis_export``.
    analysis_export : uvm_analysis_export | None
        The analysis FIFO's export; the env connects the monitor's
        analysis port to this.
    """

    def __init__(self, name="hamming_scoreboard", parent=None):
        super().__init__(name, parent)
        self.pins = None   # HammingDutPins (ConfigDB KEY_DUT_PINS)
        self.clkrs = None  # ClockReset     (ConfigDB KEY_CLK_RST)
        self.conf = None   # HammingConf    (ConfigDB KEY_CONF)

        # Analysis connection.  The env stage connects the monitor's
        # analysis port to this export: agent.monitor_ap.connect(
        # scoreboard.analysis_export).
        self.analysis_fifo = None
        self.analysis_export = None

        # Per-block accounting.  ``reset_checker()`` clears these during
        # the tb_reset logical phase (CONTRACT.md section 3/11.4).
        self._num_items_checked = 0
        self._num_passed = 0
        self._num_mismatches = 0
        self._num_resets = 0
        self._failures = []  # human-readable mismatch reports (debug)

        # Cumulative per-configuration statistics: key (data_width, secded)
        # -> {"checked": int, "passed": int, "mismatches": int, "failures":
        # list[str]}.  Never cleared by reset_checker(): this is the
        # end-of-regression summary the plan asks for.
        self._per_conf = {}

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        """Resolve the shared DUT config and create the TLM analysis FIFO."""
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

        self.analysis_fifo = uvm_tlm_analysis_fifo(
            "hamming_analysis_fifo", self)
        self.analysis_export = self.analysis_fifo.analysis_export
        self.logger.info(
            "HammingScoreboard built (DATA_WIDTH=%d, SECDED=%d, "
            "CODE_WIDTH=%d)",
            self.conf.data_width, self.conf.secded, self.conf.code_width,
        )

    async def run_phase(self):
        """Consume one monitor item per settled encode operation; predict
        and compare it immediately."""
        self.logger.info("HammingScoreboard run_phase started")
        while True:
            item = await self.analysis_fifo.get()
            if item is None:  # defensive: pyuvm signals end-of-run
                break
            self._check_item(item)

    # ------------------------------------------------------------------
    # Golden predictor + comparator
    # ------------------------------------------------------------------
    def _check_item(self, item):
        """Validate, predict and bit-exactly compare one monitor item.

        Raises ``AssertionError`` (failing the current cocotb test
        immediately) on the first bit difference; raises
        ``RuntimeError``/``ValueError`` for environment-setup bugs
        (geometry disagreement, out-of-range ``data_in``, wrong item
        type).
        """
        if not isinstance(item, HammingTransaction):
            raise TypeError(
                f"{self.get_name()}: expected HammingTransaction, got "
                f"{type(item).__name__}")
        # Mirrors the reference model's width validation (0 <= data_in <
        # 2**data_width, data_width > 0); a malformed item fails fast.
        item.check_inputs_valid()

        expected, params = hamming_encode(
            item.data_in, item.data_width, bool(item.secded))
        self._check_geometry(item, params)

        code_width = params.code_width
        mask = (1 << code_width) - 1
        expected_masked = expected & mask
        actual = item.code_out
        actual_masked = actual & mask

        self._num_items_checked += 1
        stats = self._per_conf.setdefault(
            (item.data_width, item.secded),
            {"checked": 0, "passed": 0, "mismatches": 0, "failures": []},
        )
        stats["checked"] += 1

        if actual != actual_masked:
            # A sampled value wider than the geometry is an environment
            # bug (the pin is exactly CODE_WIDTH bits), not a DUT defect.
            raise AssertionError(
                f"{self.get_name()}: sampled code_out={actual:#x} carries "
                f"bits above CODE_WIDTH={code_width} for "
                f"DATA_WIDTH={item.data_width} SECDED={item.secded} "
                f"(environment/monitor geometry bug)")

        if expected_masked != actual_masked:
            self._num_mismatches += 1
            stats["mismatches"] += 1
            bit_indices = self.differing_bit_indices(
                expected_masked, actual_masked, code_width)
            msg = self._report_mismatch(
                item, expected_masked, actual_masked, bit_indices,
                code_width,
            )
            stats["failures"].append(msg)
            self._failures.append(msg)
            # "flag any bit difference immediately" + plan "fail the
            # current test": a raised AssertionError ends the cocotb /
            # pyuvm run right here.
            raise AssertionError(msg)

        self._num_passed += 1
        stats["passed"] += 1

    def _predict_geometry(self, params, item):
        """Return True when *params* (reference-model geometry) matches the
        item/active elaboration geometry."""
        conf = self.conf
        return (
            params.data_width == item.data_width == conf.data_width
            and bool(params.secded) == bool(item.secded) == bool(conf.secded)
            and params.parity_bits == conf.parity_bits
            and params.base_width == conf.base_width
            and params.code_width == item.code_width == conf.code_width
        )

    def _check_geometry(self, item, params):
        """Cross-check item / HammingConf / HammingParams geometry.

        The scoreboard must apply the *same* generator constants the item
        was created under.  Any disagreement means the reference-model
        copy, the ConfigDB ``HammingConf`` and the item were configured
        inconsistently -- an environment bug that must fail loudly instead
        of silently scoring with the wrong width.
        """
        if not self._predict_geometry(params, item):
            raise RuntimeError(
                f"{self.get_name()}: geometry disagreement between monitor "
                f"item, active HammingConf and reference-model HammingParams"
                f" -- item=(data_width={item.data_width}, secded="
                f"{item.secded}, code_width={item.code_width}), "
                f"conf=(data_width={self.conf.data_width}, secded="
                f"{self.conf.secded}, parity_bits={self.conf.parity_bits}, "
                f"base_width={self.conf.base_width}, "
                f"code_width={self.conf.code_width}), "
                f"params={params}")

    @staticmethod
    def differing_bit_indices(expected, actual, width):
        """Indices (0..width-1, LSB-first) where expected/actual differ."""
        diff = int(expected) ^ int(actual)
        return [i for i in range(width) if (diff >> i) & 1]

    def _report_mismatch(self, item, expected, actual, bit_indices,
                         code_width):
        """Log (error severity) and return a full mismatch report."""
        msg = (
            f"code_out MISMATCH vs hamming_encode: "
            f"data_in={item.data_in:#x} "
            f"({_bin(item.data_in, item.data_width)}), "
            f"DATA_WIDTH={item.data_width}, SECDED={item.secded}, "
            f"expected code_out={expected:#x} "
            f"({_bin(expected, code_width)}), "
            f"actual code_out={actual:#x} "
            f"({_bin(actual, code_width)}), "
            f"differing bit indices={bit_indices}"
        )
        live = self._live_pin_snapshot(item)
        if live:
            msg += f"; live pins: {live}"
        self.logger.error("%s", msg)
        return msg

    def _live_pin_snapshot(self, item):
        """Best-effort current DUT pin values for a mismatch report.

        ``get()`` from the analysis FIFO and this read happen in the same
        simulation timestep (the monitor's put and the scoreboard's get
        share the settle instant), so the snapshot shows the very pins the
        item was sampled from.  Never fails the check: only used for
        diagnostics.
        """
        try:
            return (
                f"data_in={self.pins.sample_data_in(item.data_width):#x}, "
                f"code_out={self.pins.sample_code_out(item.code_width):#x}"
            )
        except Exception:  # pragma: no cover - defensive diagnostics
            return ""

    # ------------------------------------------------------------------
    # Environment-reset hook (tb_reset is a logical phase, CONTRACT.md
    # section 3)
    # ------------------------------------------------------------------
    def reset_checker(self):
        """Reinitialize per-block accounting during a tb_reset phase.

        The predictor is stateless, so nothing predictive needs re-arming;
        this only clears the current block's check/pass/mismatch counters
        while preserving the cumulative per-(DATA_WIDTH, SECDED) statistics
        that back the end-of-regression summary.  The environment/tests
        stage MUST call this once per tb_reset phase.
        """
        self._num_items_checked = 0
        self._num_passed = 0
        self._num_mismatches = 0
        self._failures = []
        self._num_resets += 1
        self.logger.debug(
            "HammingScoreboard state cleared (tb_reset phase #%d)",
            self._num_resets)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def report_phase(self):
        """Per-block summary plus cumulative per-configuration summary."""
        super().report_phase()
        self.logger.info(
            "HammingScoreboard report: %d items checked, %d passed, "
            "%d mismatches, %d reset(s) observed",
            self._num_items_checked,
            self._num_passed,
            self._num_mismatches,
            self._num_resets,
        )
        for (data_width, secded) in sorted(self._per_conf):
            stats = self._per_conf[(data_width, secded)]
            self.logger.info(
                "HammingScoreboard config (DATA_WIDTH=%d, SECDED=%d): "
                "%d checked, %d passed, %d mismatches",
                data_width, secded,
                stats["checked"], stats["passed"], stats["mismatches"],
            )
        if self._num_mismatches:
            self.logger.warning(
                "HammingScoreboard FAILED: %d comparison mismatch(es)",
                self._num_mismatches)