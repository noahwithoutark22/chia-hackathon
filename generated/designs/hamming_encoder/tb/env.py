"""hamming_encoder environment (stage 6: INTEGRATION).

This module assembles the stage 1-5 verification components into a single
pyuvm ``uvm_env`` that every test class instantiates:

    * ``HammingAgent``       (active: sequencer + driver + monitor)
    * ``HammingScoreboard``  (golden predictor vs ``hamming_encode``)
    * ``HammingCoverage``    (cocotb-coverage ``cg_hamming_encoding`` collector)
    * stage-5 always-on assertion checkers (``start_assertions``)

Wiring owned by this stage (CONTRACT.md sections 3, 8, 10-11):

    agent.monitor_ap.connect(scoreboard.analysis_export)   # 1 item per settle
    agent.monitor_ap.connect(coverage.analysis_export)     # uvm_subscriber

so every monitor transaction is consumed by the scoreboard and the coverage
subscriber simultaneously (uvm_analysis_port fan-out).

Design rules honoured here (CONTRACT.md section 9):

* No SystemVerilog anywhere; the only HDL in the project is the DUT RTL,
  which this stage never touches.
* The always-on assertions are started by the environment with
  ``start_assertions()`` -- exactly once per simulation, before any
  sequence starts driving (assertions.py documents this contract).  The
  spawned checker coroutines run forever, so ``final_phase`` kills them to
  keep the run cycle clean.
* The DUT is purely combinational with no ``clk``/reset port; the env does
  not create a cocotb ``Clock`` and never references ``dut.clk`` /
  ``dut.tb_reset`` (pacing is virtual -- ``wait_clock_cycles``).
* The tb_reset logical phase is owned by the test/sequence layer, which is
  responsible for calling ``HammingScoreboard.reset_checker()`` once per
  tb_reset phase (CONTRACT.md section 11.4); the env itself performs no
  resets.
"""

from pyuvm import uvm_env

from tb.agent import HammingAgent
from tb.assertions import start_assertions
from tb.coverage import HammingCoverage
from tb.scoreboard import HammingScoreboard

__all__ = ["HammingEnv"]


class HammingEnv(uvm_env):
    """Top-level environment for the ``hamming_encoder`` DUT.

    Attributes
    ----------
    agent : HammingAgent | None
        Stimulus + observation agent (built with name ``hamming_agent``).
    scoreboard : HammingScoreboard | None
        Golden-predictor scoreboard (name ``hamming_scoreboard``).
    coverage : HammingCoverage | None
        Functional-coverage subscriber (name ``hamming_coverage``).
    assertions : HammingAssertions | None
        The stage-5 assertion bundle started in ``build_phase``; its
        ``.tasks`` are killed in ``final_phase``.
    """

    def __init__(self, name="hamming_env", parent=None):
        super().__init__(name, parent)
        self.agent = None
        self.scoreboard = None
        self.coverage = None
        self.assertions = None

    def build_phase(self):
        """Create the agent, scoreboard and coverage subscriber, and start
        the always-running assertion checkers.

        ``start_assertions()`` resolves the shared ConfigDB entries
        (CONTRACT.md section 6, exact keys) that ``tb_top`` populated, so
        the environment must be built after those keys are shared.  It is
        invoked exactly once here, before the run phase lets any sequence
        drive the DUT (assertions.py documents this call contract).
        """
        super().build_phase()
        self.agent = HammingAgent("hamming_agent", self)
        self.scoreboard = HammingScoreboard("hamming_scoreboard", self)
        self.coverage = HammingCoverage("hamming_coverage", self)
        self.assertions = start_assertions()
        self.logger.info(
            "HammingEnv build_phase complete "
            "(agent + scoreboard + coverage + %d assertion task(s))",
            len(self.assertions.tasks),
        )

    def connect_phase(self):
        """Wire the monitor's analysis port to the scoreboard and coverage.

        ``agent.monitor_ap`` is the agent's alias for the monitor's
        ``uvm_analysis_port`` (CONTRACT.md section 10); connecting it to
        both consumers broadcasts every monitored transaction to the
        scoreboard FIFO and the coverage subscriber.
        """
        super().connect_phase()
        self.agent.monitor_ap.connect(self.scoreboard.analysis_export)
        self.agent.monitor_ap.connect(self.coverage.analysis_export)
        self.logger.info(
            "HammingEnv connect_phase: monitor_ap -> scoreboard + coverage"
        )

    def final_phase(self):
        """Stop the always-running assertion checker coroutines.

        The checkers were spawned with ``cocotb.start_soon`` and loop
        forever; ``final_phase`` (run after ``report_phase``) cancels them
        so no task outlives the run.
        """
        if self.assertions is not None and getattr(self.assertions, "tasks", None):
            for task in list(self.assertions.tasks):
                try:
                    task.kill()
                except Exception:  # pragma: no cover - defensive teardown
                    self.logger.warning(
                        "HammingEnv final_phase: failed to kill assertion "
                        "task %r", task,
                    )
        super().final_phase()