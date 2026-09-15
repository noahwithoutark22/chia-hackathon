"""UVM environment for the axi_handshake DUT.

The ``AxiHandshakeEnv`` wires together:

* **Agent** (driver + sequencer + monitor)
* **Scoreboard** (reference-model predictor + comparator)
* **Coverage subscriber** (cocotb-coverage CoverPoint/CoverCross)
* **Assertion checkers** (always-running coroutines via ``cocotb.start_soon``)

The environment is instantiated by the test classes (``uvm_test``
subclasses) during ``build_phase``.

ConfigDB keys consumed (CONTRACT.md §5):
  - ``"dut"``            — cocotb SimHandleBase
  - ``"dut_helper"``     — DutHelper instance
  - ``"ref_model"``      — module reference (oracle)
  - ``"reset_polarity"`` — ``"active_low"``
  - ``"clock_period"``   — int (ns)
  - ``"clk_name"``       — ``"clk"``
  - ``"rst_name"``       — ``"rst_n"``
"""

import cocotb
from pyuvm import uvm_env

from agent import AxiHandshakeAgent
from scoreboard import AxiHandshakeScoreboard
from coverage import AxiHandshakeCoverage
from assertions import (
    assertion_m_valid_held_during_stall,
    assertion_s_ready_only_when_can_accept,
    assertion_no_data_drop,
)


class AxiHandshakeEnv(uvm_env):
    """Top-level UVM environment for the axi_handshake DUT.

    After ``build_phase`` the following attributes are available:

    Attributes
    ----------
    agent : AxiHandshakeAgent
    scoreboard : AxiHandshakeScoreboard
    coverage : AxiHandshakeCoverage
    """

    def __init__(self, name="axi_handshake_env", parent=None):
        super().__init__(name, parent)
        self.agent = None
        self.scoreboard = None
        self.coverage = None
        self._assertion_tasks = []

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Create sub-components."""
        super().build_phase()

        self.agent = AxiHandshakeAgent("agent", self)
        self.scoreboard = AxiHandshakeScoreboard("scoreboard", self)
        self.coverage = AxiHandshakeCoverage("coverage", self)

        self.logger.info("AxiHandshakeEnv built")

    def connect_phase(self):
        """Wire monitor analysis port to scoreboard and coverage.

        The monitor's ``uvm_analysis_port`` publishes transactions
        every cycle.  Both the scoreboard (TLM FIFO) and the coverage
        subscriber need to receive each transaction.
        """
        super().connect_phase()

        # Monitor → Scoreboard (through TLM analysis FIFO)
        self.agent.monitor_ap.connect(self.scoreboard.analysis_export)

        # Monitor → Coverage subscriber
        self.agent.monitor_ap.connect(self.coverage.analysis_export)

        self.logger.info("AxiHandshakeEnv connected")

    def start_of_simulation_phase(self):
        """Launch always-running assertion checker coroutines.

        These run concurrently with the driver, monitor, scoreboard,
        and coverage.  A failed assertion raises AssertionError
        immediately, failing the test.
        """
        super().start_of_simulation_phase()
        self._assertion_tasks = [
            cocotb.start_soon(assertion_m_valid_held_during_stall()),
            cocotb.start_soon(assertion_s_ready_only_when_can_accept()),
            cocotb.start_soon(assertion_no_data_drop()),
        ]
        self.logger.info(
            "AxiHandshakeEnv: %d assertion checkers launched",
            len(self._assertion_tasks),
        )

    def report_phase(self):
        """Summarize environment results."""
        super().report_phase()
        self.logger.info("AxiHandshakeEnv report_phase complete")
