"""Stage 6 (integration) artifact of the CHIA generator: the pyuvm environment.

``I2CEnv`` is the parallel-composition root of the i2c_master bench.  It is
instantiated by every :class:`~tb.test.I2CTestBase` subclass and owns the
three collaborating components:

* :class:`~tb.agent.I2CAgent`        -- sequencer + driver + monitor (the
  agent publishes every completed transaction on ``agent.analysis_port``);
* :class:`~tb.scoreboard.I2CScoreboard` -- the pass/fail oracle: scores each
  monitor item against the *independent* Python reference model
  (CONTRACT.md sections 7/10); when a mismatch occurs it raises, failing
  the enclosing cocotb test immediately;
* :class:`~tb.coverage.I2CCoverage`  -- cocotb-coverage functional
  coverage collector (CONTRACT.md section 11.1); observation only.

The environment additionally owns the always-running **assertion checkers**
(CONTRACT.md section 11.2): ``build_phase`` launches all six plan
``useful_assertions`` via :func:`tb.assertions.launch_assertions`.  The
**watchdog** stays in the test layer (``tb/test_top.py``), which arms and
kills it per CONTRACT.md sections 8/11.2.

Ownership split (CONTRACT.md): the env builds, connects, reports, and tears
down; it never drives stimulus itself.  Stimulus starts on
``agent.sequencer`` from the test layer.

Wiring conventions (CONTRACT.md section 9.2): ``agent.analysis_port`` is
connected in ``connect_phase`` with fan-out to both the scoreboard's
``analysis_export`` and the coverage subscriber's ``analysis_export``, so
every published transaction is scored *and* sampled exactly once.
"""

from pyuvm import uvm_env

from tb.agent import I2CAgent
from tb.assertions import launch_assertions
from tb.coverage import I2CCoverage
from tb.scoreboard import I2CScoreboard

__all__ = ["I2CEnv"]


class I2CEnv(uvm_env):
    """Top-level testbench environment for the ``i2c_master`` DUT.

    Attributes mirror the UVM child names coined by the earlier stages:
        agent      (``"i2c_agent"``, owns ``driver``/``sequencer``/``monitor``),
        scoreboard (``"i2c_scoreboard"``),
        coverage   (``"i2c_coverage"``),
        assertions (``I2CAssertions`` checker bundle, *not* a component).
    """

    def __init__(self, name="i2c_env", parent=None):
        super().__init__(name, parent)
        self.agent = None
        self.scoreboard = None
        self.coverage = None
        self.assertions = None

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        """Create the agent, scoreboard, coverage, and always-on checks.

        All shared objects (``I2CDutPins``, ``ClockReset``) are already in
        pyuvm's ConfigDB by the time ``build_phase`` traverses top-down
        (tb_top populates them before calling ``run_test``), so every child
        resolves them from ``KEY_DUT_PINS`` / ``KEY_CLK_RST``.
        """
        super().build_phase()
        self.agent = I2CAgent("i2c_agent", self)
        self.scoreboard = I2CScoreboard("i2c_scoreboard", self)
        self.coverage = I2CCoverage("i2c_coverage", self)

        # Plan "useful_assertions" (CONTRACT.md section 11.2): always-running
        # Python checkers, launched while the simulator is live.  Error
        # checkers raise on the first violation (failing the test); warning
        # checkers count into `violations` for the report phase.
        self.assertions = launch_assertions()
        self.logger.info(
            "%s: I2CAgent, I2CScoreboard, I2CCoverage built; %d assertion "
            "checkers launched",
            self.get_name(), len(self.assertions.tasks))

    def connect_phase(self):
        """Fan out the monitor stream to the scoreboard and the coverage."""
        super().connect_phase()
        self.agent.analysis_port.connect(self.scoreboard.analysis_export)
        self.agent.analysis_port.connect(self.coverage.analysis_export)
        self.logger.info(
            "%s: agent.analysis_port -> scoreboard.analysis_export and "
            "coverage.analysis_export", self.get_name())

    def report_phase(self):
        """Consolidated end-of-test report (scoreboard, coverage, checks).

        The scoreboard's comparison is *fail-fast*: a mismatch raises from
        the comparison callback and aborts the test before this phase.  This
        phase therefore reports (not re-checks) and is what the regression
        logs use to summarize each test run.
        """
        super().report_phase()
        self.logger.info("%s", self.scoreboard.summarize())
        if self.assertions is not None:
            self.logger.info("%s", self.assertions.summarize())
        coverage_pct = self.coverage.report(logger=self.logger.info)
        self.logger.info(
            "%s: functional coverage %.1f%% of transaction_cg",
            self.get_name(), float(coverage_pct))

    def final_phase(self):
        """Tear down the always-running checkers.

        ``final_phase`` runs only after the run/report phases completed
        without raising; after it, control returns to tb_top, which kills
        the test-layer watchdog.  The checker tasks are killed here so no
        background coroutine outlives the UVM phase traversal.
        """
        super().final_phase()
        if self.assertions is not None:
            self.assertions.stop()
            self.logger.info(
                "%s: assertion checkers stopped", self.get_name())