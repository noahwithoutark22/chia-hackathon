"""PyUVM environment for the parameterized adder DUT.

The environment (``uvm_env``) instantiates and wires together the four
observation/checking subcomponents:

  - ``AdderAgent``                — stimulus (driver + sequencer) + monitor
  - ``AdderScoreboard``           — reference-model comparison
  - ``AdderCoverageCollector``    — functional coverage via cocotb-coverage
  - ``AdderAssertions``           — Python assertion checkers (SVA replacement)

Connection topology (per CONTRACT.md):

  agent.ap ──→ scoreboard.fifo  (uvm_tlm_analysis_fifo)
  agent.ap ──→ coverage         (uvm_subscriber / analysis_export)

The assertion component runs its own always-running checker coroutines in
``run_phase`` and does not need an analysis-port connection.
"""

from __future__ import annotations

from pyuvm import uvm_env, ConfigDB

from adder_agent import AdderAgent
from adder_scoreboard import AdderScoreboard
from adder_coverage import AdderCoverageCollector
from adder_assertions import AdderAssertions


class AdderEnv(uvm_env):
    """Environment that wires agent → scoreboard + coverage + assertions.

    Parameters
    ----------
    name : str
        Instance name (default ``"adder_env"``).
    parent : uvm_component
        Parent component (normally the test).
    """

    def __init__(self, name="adder_env", parent=None):
        super().__init__(name, parent)
        self.agent: AdderAgent | None = None
        self.scoreboard: AdderScoreboard | None = None
        self.coverage: AdderCoverageCollector | None = None
        self.assertions: AdderAssertions | None = None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Instantiate all sub-components."""
        super().build_phase()

        self.agent = AdderAgent("adder_agent", self)
        self.scoreboard = AdderScoreboard("adder_scoreboard", self)
        self.coverage = AdderCoverageCollector("adder_coverage_collector", self)
        self.assertions = AdderAssertions("adder_assertions", self)

        self.logger.info(
            "AdderEnv %s built: agent + scoreboard + coverage + assertions",
            self.get_full_name(),
        )

    def connect_phase(self):
        """Wire the monitor analysis port to scoreboard and coverage.

        The agent exposes ``agent.ap`` which is the monitor's analysis port.
        The scoreboard's FIFO ``analysis_export`` and the coverage collector's
        ``analysis_export`` both subscribe to the same stream.
        """
        super().connect_phase()

        # agent.ap → scoreboard FIFO
        self.agent.ap.connect(self.scoreboard.fifo.analysis_export)

        # agent.ap → coverage collector
        self.agent.ap.connect(self.coverage.analysis_export)

        self.logger.info(
            "AdderEnv %s connected: agent.ap -> scoreboard.fifo + coverage",
            self.get_full_name(),
        )
