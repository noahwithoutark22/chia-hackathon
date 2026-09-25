"""AES-128 UVM environment (stage-6 INTEGRATION artifact).

:class:`Aes128Env` is the pyuvm ``uvm_env`` that assembles every earlier
stage's verification component for the ``aes128`` DUT
(``benchmarks/aes128_benchmark_corrupted/aes128.sv``):

* :class:`~agent.Aes128Agent`      (stages 2/3: sequencer + driver + monitor)
* :class:`~scoreboard.Aes128Scoreboard`  (stage 4: reference-model,
   in-order transaction scorer)
* :class:`~coverage.Aes128Coverage`      (stage 5: cocotb-coverage
   ``uvm_subscriber``, item-driven + always-on handshake sampler)
* :class:`~assertions.Aes128Assertions`  (stage 5: the six plan assertion
   checkers launched with ``cocotb.start_soon``, plus the clock-cycle
   watchdog launcher the tb_top stage arms)

WIRING (CONTRACT.md §10.1/§11.1/§11.2 -- owned by the env stage):

* ``build_phase`` constructs the agent, the scoreboard and the coverage
  subscriber, then starts the six always-running assertion checkers via
  ``assertions.launch_assertions()`` (which wraps ``cocotb.start_soon``;
  must run while the cocotb simulation is active, which build_phase under
  ``uvm_root().run_test()`` is).
* ``connect_phase`` subscribes the agent's analysis port -- the broadcast
  sink of the stage-3 monitor (CONTRACT.md §9.2) -- to the scoreboard's
  analysis FIFO and to the coverage subscriber's ``analysis_export`` using
  the documented stable entry points ``scoreboard.connect_monitor(ap)`` /
  ``coverage.connect_monitor(ap)`` (CONTRACT.md §10.1/§11.1).  Every
  completed transaction the monitor publishes is therefore graded in order
  AND sampled for functional coverage.
* ``report_phase`` logs the scoreboard summary, the assertion summary and
  the shared ``coverage_db`` summary for the end-of-test report.  Pass/fail
  judgment is owned by the test classes (``tests.py``); this report is
  informational only.

No new ConfigDB keys are introduced: the env reads only the CONTRACT.md
§4 keys already set by the tb_top layer (``"dut"``, ``"CLK_HALF_PERIOD_NS"``,
optional ``"Aes128DutHelper"``).

All APIs used here are public pyuvm 5.0.0 and public Cocotb 2.1.0 APIs.
No SystemVerilog anywhere.
"""

from pyuvm import uvm_env

from agent import Aes128Agent
from assertions import launch_assertions
from coverage import Aes128Coverage, coverage_summary_dict
from scoreboard import Aes128Scoreboard

__all__ = ["Aes128Env"]


class Aes128Env(uvm_env):
    """Top-level verification environment for the ``aes128`` DUT.

    Instantiates the agent (stimulus + observation), the scoreboard
    (reference-model grading), the coverage subscriber (cocotb-coverage)
    and the assertion checker controller, and wires them together.
    """

    def __init__(self, name: str = "aes128_env", parent=None) -> None:
        super().__init__(name, parent)
        self.agent = None       # type: Aes128Agent | None
        self.scoreboard = None  # type: Aes128Scoreboard | None
        self.coverage = None    # type: Aes128Coverage | None
        self.assertions = None  # type: Aes128Assertions | None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Build the agent + scoreboard + coverage and start the checkers.

        The six always-running assertion checkers are launched here with
        ``cocotb.start_soon`` (via ``launch_assertions``) so they observe
        the entire test -- including every sequence's internal reset.  A
        violated plan assertion raises ``AssertionError`` out of its checker
        coroutine, failing the enclosing cocotb test at once (CONTRACT.md
        §8/§11.2).
        """
        super().build_phase()
        self.agent = Aes128Agent("aes128_agent", self)
        self.scoreboard = Aes128Scoreboard("aes128_scoreboard", self)
        self.coverage = Aes128Coverage("aes128_coverage", self)
        # Always-running assertion checkers (CONTRACT.md §11.2).
        self.assertions = launch_assertions()
        self.logger.info(
            "%s build_phase: agent + scoreboard + coverage built; %d "
            "assertion checker coroutine(s) started",
            self.get_name(),
            len(self.assertions.tasks),
        )

    def connect_phase(self) -> None:
        """Wire the monitor analysis port into the scoreboard and coverage.

        CONTRACT.md §9.2/§10.1/§11.1: ``agent.analysis_port`` re-broadcasts
        every transaction the monitor publishes; subscribing it to the
        scoreboard's analysis FIFO (in-order grader) and to the coverage
        subscriber's ``analysis_export`` (cocotb-coverage sampler) fans each
        completed transaction out to both consumers.
        """
        super().connect_phase()
        self.scoreboard.connect_monitor(self.agent.analysis_port)
        self.coverage.connect_monitor(self.agent.analysis_port)
        self.logger.info(
            "%s connect_phase: agent.analysis_port -> scoreboard fifo "
            "and coverage subscriber",
            self.get_name(),
        )

    def report_phase(self) -> None:
        """Log the end-of-test summaries (informational; grading is owned
        by the test classes)."""
        super().report_phase()
        if self.scoreboard is not None:
            self.logger.info("%s", self.scoreboard.get_summary())
        if self.assertions is not None:
            self.logger.info("%s", self.assertions.summarize())
        cov = coverage_summary_dict()
        self.logger.info(
            "COVERAGE: %d/%d bins covered (%.1f%% total)",
            cov["total_covered"], cov["total_size"], cov["total_percent"],
        )