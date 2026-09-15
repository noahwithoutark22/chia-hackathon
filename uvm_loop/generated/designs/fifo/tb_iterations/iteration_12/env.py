"""FIFO environment (pyuvm ``uvm_env``).

This module assembles the major verification components into a single
environment that tests can instantiate and configure:

    * ``FifoAgent``        (active by default: sequencer + driver + monitor)
    * ``FifoScoreboard``   (predictor + in-order comparator against ref_model)
    * ``FifoCoverage``     (cocotb-coverage functional coverage collector)

The environment wires the monitor's analysis port to both the scoreboard
(through its ``uvm_tlm_analysis_fifo``) and the coverage subscriber, so
every post-edge :class:`FifoTransaction` is consumed by all three
components simultaneously.

Ownership of ``start_assertions`` and ``start_watchdog`` belongs to the
test layer (``test.py``), not the environment — the env builds and
connects components; the test starts auxiliary coroutines and enforces
pass/fail.

ConfigDB keys (CONTRACT.md §4): the test layer must populate ``"dut"``,
``"DATA_WIDTH"``, ``"DEPTH"`` (and optionally ``"FifoDutHelper"``)
before ``build_phase`` traverses the component hierarchy.
"""

from pyuvm import uvm_env

from agent import FifoAgent
from coverage import FifoCoverage
from scoreboard import FifoScoreboard


class FifoEnv(uvm_env):
    """Top-level environment for the ``fifo`` DUT."""

    def __init__(self, name="fifo_env", parent=None):
        super().__init__(name, parent)
        self.agent = None
        self.scoreboard = None
        self.coverage = None

    def build_phase(self):
        """Create the agent, scoreboard, and coverage subscriber.

        Subcomponent names are chosen to match the UVM hierarchy
        conventions documented in CONTRACT.md §10.1 (agent) and §12.1
        (coverage).  The scoreboard is named ``fifo_scoreboard`` (§11.2).
        """
        super().build_phase()
        self.agent = FifoAgent("fifo_agent", self)
        self.scoreboard = FifoScoreboard("fifo_scoreboard", self)
        self.coverage = FifoCoverage("fifo_coverage", self)
        self.logger.info("FifoEnv build_phase complete")

    def connect_phase(self):
        """Wire the monitor's analysis port to scoreboard and coverage.

        ``agent.ap`` is the same object as ``agent.monitor.ap`` (§10.3);
        connecting it to both ``scoreboard.analysis_export`` and
        ``coverage.analysis_export`` broadcasts every monitor transaction
        to both consumers (pyuvm ``uvm_analysis_port`` fan-out).
        """
        super().connect_phase()
        # Scoreboard: monitor items -> analysis_fifo -> run_phase
        self.agent.ap.connect(self.scoreboard.analysis_export)
        # Coverage: monitor items -> uvm_subscriber TLM write()
        self.agent.ap.connect(self.coverage.analysis_export)
        self.logger.info("FifoEnv connect_phase: agent.ap -> scoreboard + coverage")
