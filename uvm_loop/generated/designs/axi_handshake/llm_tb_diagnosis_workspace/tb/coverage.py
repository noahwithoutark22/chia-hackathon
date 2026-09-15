"""Functional coverage for the axi_handshake DUT.

Uses the ``cocotb-coverage`` library (``CoverPoint`` / ``CoverCross``)
sampled through a pyuvm ``uvm_subscriber`` connected to the monitor's
analysis port.

Coverage groups (matching verification_plan.yaml §functional_coverage):

* **handshake_cg** — cross of input_transfer and output_transfer events.
* **payload_cg** — range of s_data values accepted by the DUT.

The stall_cg from the plan is implemented as a simple counter tracked
in write() and reported in report_phase; cocotb-coverage does not
support histogram-style bin ranges natively, so the stall tracking
is done inline.

ConfigDB keys consumed (CONTRACT.md §5):
  - ``"dut"`` — cocotb SimHandleBase
"""

from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db
from pyuvm import uvm_subscriber


# ═══════════════════════════════════════════════════════════════════
#  CoverPoints / CoverCross declarations
# ═══════════════════════════════════════════════════════════════════

# --- handshake_cg (verification_plan §functional_coverage) --------

@CoverPoint(
    name="handshake_cg.input_transfer_bin",
    vname="input_transfer",
    xf=None,
    bins=[
        ("input_accepted",      lambda v: v == 1),
        ("input_not_accepted",  lambda v: v == 0),
    ],
    weight=1,
    at_least=1,
)
@CoverPoint(
    name="handshake_cg.output_transfer_bin",
    vname="output_transfer",
    xf=None,
    bins=[
        ("output_accepted",  lambda v: v == 1),
        ("output_stalled",   lambda v: v == 0),
    ],
    weight=1,
    at_least=1,
)
@CoverCross(
    name="handshake_cg.xfer_cross",
    items=[
        "handshake_cg.input_transfer_bin",
        "handshake_cg.output_transfer_bin",
    ],
    weight=1,
    at_least=1,
)
def _handshake_cross(input_transfer, output_transfer):
    """Dummy function for the cross coverpoint — called by the library."""
    pass


# --- payload_cg (verification_plan §functional_coverage) ----------

@CoverPoint(
    name="payload_cg.payload_value_bin",
    vname="s_data",
    xf=None,
    bins=[
        ("all_zeros",  lambda v: v == 0x00),
        ("all_ones",   lambda v: v == 0xFF),
        ("mid_range",  lambda v: 128 <= v <= 254),
        ("low_range",  lambda v: 1 <= v <= 127),
    ],
    weight=1,
    at_least=1,
)
def _payload_bins(s_data):
    """Dummy function for the payload coverpoint — called by the library."""
    pass


# ═══════════════════════════════════════════════════════════════════
#  Coverage subscriber (pyuvm uvm_subscriber)
# ═══════════════════════════════════════════════════════════════════

class AxiHandshakeCoverage(uvm_subscriber):
    """Subscribes to monitor transactions and samples functional coverage.

    The environment connects ``monitor.ap`` to this subscriber's
    ``analysis_export`` (inherited from ``uvm_subscriber``).  Each
    arriving ``AxiHandshakeTxn`` is decoded and the appropriate
    ``cocotb-coverage`` coverpoints are sampled.

    Stall tracking (stall_cg) is handled inline: a running counter
    tracks consecutive cycles where m_valid=1 && m_ready=0.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        # stall_cg bookkeeping
        self._stall_count = 0
        self._stall_1 = False
        self._stall_2_to_5 = False
        self._stall_6_plus = False
        self._items_sampled = 0

    # ------------------------------------------------------------------
    # write() — called by uvm_subscriber TLM machinery
    # ------------------------------------------------------------------

    def write(self, txn):
        """Sample coverage for one monitor transaction."""
        self._items_sampled += 1

        s_valid = int(txn.s_valid) & 0x1
        s_data = int(txn.s_data) & 0xFF
        m_ready = int(txn.m_ready) & 0x1
        s_ready = int(txn.s_ready) & 0x1
        m_valid = int(txn.m_valid) & 0x1

        # --- handshake_cg sampling ---------------------------------
        input_transfer = 1 if (s_valid and s_ready) else 0
        output_transfer = 1 if (m_valid and m_ready) else 0

        # The decorator-wrapped _handshake_cross() is the cocotb-coverage
        # sampling mechanism: one call records samples for both handshake
        # coverpoints and the cross coverpoint.
        _handshake_cross(input_transfer, output_transfer)

        # --- payload_cg sampling (only on accepted inputs) ----------
        if input_transfer:
            _payload_bins(s_data)

        # --- stall_cg tracking (inline, not a CoverPoint) ----------
        if m_valid and not m_ready:
            self._stall_count += 1
        else:
            if self._stall_count == 1:
                self._stall_1 = True
            elif 2 <= self._stall_count <= 5:
                self._stall_2_to_5 = True
            elif self._stall_count >= 6:
                self._stall_6_plus = True
            self._stall_count = 0

    # ------------------------------------------------------------------
    # report_phase
    # ------------------------------------------------------------------

    def report_phase(self):
        """Log coverage summary and stall coverage."""
        super().report_phase()

        # Finalize any trailing stall
        if self._stall_count == 1:
            self._stall_1 = True
        elif 2 <= self._stall_count <= 5:
            self._stall_2_to_5 = True
        elif self._stall_count >= 6:
            self._stall_6_plus = True

        self.logger.info(
            "AxiHandshakeCoverage: %d items sampled", self._items_sampled
        )
        self.logger.info(
            "Stall coverage: 1-cycle=%s, 2-5-cycle=%s, 6+-cycle=%s",
            self._stall_1,
            self._stall_2_to_5,
            self._stall_6_plus,
        )

        # Report cocotb-coverage summary
        try:
            coverage_db.report_coverage(
                self.logger.info, bins=True
            )
        except Exception as exc:
            self.logger.warning(
                "coverage_db.report_coverage failed: %s", exc
            )
