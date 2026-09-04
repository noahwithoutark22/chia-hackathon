"""Transaction-level scoreboard for the parameterized adder DUT.

The scoreboard is a ``uvm_scoreboard`` that:
  1. Receives monitor transactions via a ``uvm_tlm_analysis_fifo``.
  2. Computes the **expected** ``{sum, cout}`` by calling the golden
     reference model ``adder_ref`` (from ``examples/adder/ref_model.py``).
  3. Compares the expected values against the DUT's observed output
     (carried in the transaction's ``exp_sum`` / ``exp_cout`` fields,
     which — per the monitor — hold the registered DUT pin values).

Any mismatch is reported immediately with the cycle count, input values,
observed DUT output, and the expected reference-model output.

The reference model lives at ``/workspace/examples/adder/ref_model.py``
and is imported at module scope so the scoreboard MUST NOT reimplement
its arithmetic logic.
"""

from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Ensure the reference model directory is on sys.path so we can import it.
# ---------------------------------------------------------------------------
_REF_DIR = os.path.join(os.path.dirname(__file__), os.pardir,
                         "examples", "adder")
_REF_DIR = os.path.abspath(_REF_DIR)
if _REF_DIR not in sys.path:
    sys.path.insert(0, _REF_DIR)

from ref_model import adder_ref  # noqa: E402  (from examples/adder/ref_model.py)

from pyuvm import (uvm_scoreboard, uvm_tlm_analysis_fifo, ConfigDB)

from adder_transaction import AdderTransaction


class AdderScoreboard(uvm_scoreboard):
    """Scoreboard that checks every DUT output against the reference model.

    Parameters
    ----------
    name : str
        Instance name (default ``"adder_scoreboard"``).
    parent : uvm_component
        Parent component (normally the environment).
    """

    def __init__(self, name="adder_scoreboard", parent=None):
        super().__init__(name, parent)
        self.fifo: uvm_tlm_analysis_fifo | None = None
        self.export = None  # convenience alias; set in build_phase

        # Counters for final summary
        self._match_count: int = 0
        self._mismatch_count: int = 0
        self._transaction_count: int = 0
        self._first_mismatch_detail: str | None = None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Create the TLM analysis FIFO that receives monitor transactions."""
        super().build_phase()
        self.fifo = uvm_tlm_analysis_fifo("fifo", self)
        self.export = self.fifo.analysis_export

        # Retrieve the width parameter from ConfigDB (CONTRACT.md §6).
        self.width: int = ConfigDB.get(None, "", "width")

    def connect_phase(self):
        """Connect the FIFO to the agent's analysis port.

        The actual connection to ``agent.ap`` is done by the environment
        (``connect_phase``).  Here we just log readiness.
        """
        super().connect_phase()
        self.logger.info(
            "AdderScoreboard %s ready — FIFO connected, width=%d",
            self.get_full_name(),
            self.width,
        )

    async def run_phase(self) -> None:
        """Continuously pull transactions from the FIFO and check them.

        This coroutine runs for the entire simulation and never returns
        (until the test ends).
        """
        while True:
            # Block until a transaction is available in the FIFO.
            tr: AdderTransaction = await self.fifo.get()

            self._transaction_count += 1

            # ----- Compute expected result from the reference model -----
            exp_sum, exp_cout = adder_ref(tr.a, tr.b, tr.cin, self.width)

            # ----- Compare against observed DUT output ------------------
            # ``tr.exp_sum`` and ``tr.exp_cout`` carry the *observed*
            # DUT pin values (set by the monitor), despite the "exp" prefix.
            observed_sum = tr.exp_sum
            observed_cout = tr.exp_cout

            if exp_sum == observed_sum and exp_cout == observed_cout:
                self._match_count += 1
                self.logger.debug(
                    "MATCH #%d: a=0x%0*X b=0x%0*X cin=%d "
                    "-> sum=0x%0*X cout=%d",
                    self._transaction_count,
                    (self.width + 3) // 4, tr.a,
                    (self.width + 3) // 4, tr.b,
                    tr.cin,
                    (self.width + 3) // 4, observed_sum,
                    observed_cout,
                )
            else:
                self._mismatch_count += 1
                detail = (
                    f"MISMATCH at transaction #{self._transaction_count}: "
                    f"a=0x{tr.a:0{(self.width + 3) // 4}X} "
                    f"b=0x{tr.b:0{(self.width + 3) // 4}X} "
                    f"cin={tr.cin} | "
                    f"DUT sum=0x{observed_sum:0{(self.width + 3) // 4}X} "
                    f"cout={observed_cout} | "
                    f"expected sum=0x{exp_sum:0{(self.width + 3) // 4}X} "
                    f"cout={exp_cout}"
                )
                self.logger.error(detail)
                if self._first_mismatch_detail is None:
                    self._first_mismatch_detail = detail
                # Fail the test immediately on any mismatch (per spec).
                assert False, detail

    def check_phase(self):
        """Final check: report summary statistics.

        Called by pyuvm at end-of-simulation.  Log the totals so the
        operator can see at a glance whether the scoreboard was exercised.
        """
        super().check_phase()
        self.logger.info(
            "AdderScoreboard summary: %d transactions, %d matches, "
            "%d mismatches",
            self._transaction_count,
            self._match_count,
            self._mismatch_count,
        )
        if self._mismatch_count > 0 and self._first_mismatch_detail:
            self.logger.error(
                "First mismatch detail: %s", self._first_mismatch_detail,
            )
