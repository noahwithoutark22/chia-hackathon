"""SHA-256 UVM environment (stage-6 ENV artifact).

Assembles every earlier-stage verification component into a single pyuvm
``uvm_env`` that each test class instantiates in ``build_phase``:

* ``Sha256Agent``              (stage 2/3: sequencer + driver + monitor)
* ``Sha256Scoreboard``         (stage 4: in-order golden-reference comparator)
* ``Sha256FunctionalCoverage`` (stage 5: cocotb-coverage sampler, always-on)
* ``Sha256Assertions``         (stage 5: the three plan assertion checkers)

WIRING (CONTRACT.md §12/§14/§15):

* ``connect_phase`` subscribes the agent's analysis port -- the *same
  object* as the monitor's ``ap`` (CONTRACT.md §12 broadcast model) -- to
  the scoreboard's analysis FIFO through the documented stable entry point
  ``scoreboard.connect_monitor(agent.ap)`` (CONTRACT.md §14).  Every
  completed transaction the monitor publishes is therefore graded in order.
* ``build_phase`` starts the functional-coverage sampler
  (``start_coverage()``) and the three structural assertion checkers
  (``start_assertions()``) with the public Cocotb 2.1.0
  ``cocotb.start_soon`` API (CONTRACT.md §15).  They are plain-Python
  coroutines that read the shared ``Sha256Pins`` helper (ConfigDB key
  ``"sha256_pins"``, §5/§13 retrieval form); they are not UVM components.

WATCHDOG OWNERSHIP (CONTRACT.md §7/§15) -- by design the env owns the
*structural checkers* while each TEST owns its *watchdog budget*: the
directed KAT scenarios fit in ``WATCHDOG_MARGIN_CYCLES`` (500) but the
corner and randomized runs are longer, so each test's ``run_phase`` calls
``env.assertions.start_watchdog(budget)`` / ``disarm_watchdog()`` around
its scenario.  ``test_top.py`` additionally guards the whole run with a
coarse ``cocotb.triggers.with_timeout`` bound.

No new ConfigDB keys are introduced (still only ``"dut"`` and
``"sha256_pins"``, CONTRACT.md §5).
"""

from pyuvm import uvm_env

from sha256_agent import Sha256Agent
from sha256_assertions import Sha256Assertions, start_assertions
from sha256_coverage import Sha256FunctionalCoverage, start_coverage
from sha256_scoreboard import Sha256Scoreboard


class Sha256Env(uvm_env):
    """Top-level verification environment for the ``sha256`` DUT.

    Instantiates the agent (stimulus + observation), the scoreboard
    (golden-reference grading), the functional-coverage sampler and the
    structural assertion checker controller, and wires them together.
    """

    def __init__(self, name: str = "sha256_env", parent=None) -> None:
        super().__init__(name, parent)
        self.agent = None          # type: Sha256Agent
        self.scoreboard = None     # type: Sha256Scoreboard
        self.coverage = None       # type: Sha256FunctionalCoverage
        self.assertions = None     # type: Sha256Assertions

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Build the agent + scoreboard, then start coverage and checkers.

        The coverage sampler and the three plan-assertion checkers are
        started here (CONTRACT.md §15) so they observe the entire test --
        including every sequence's internal reset.  They are background
        cocotb coroutines; the cocotb test manager ends them when the test
        finishes (and fails the test immediately if one raises).
        """
        super().build_phase()
        self.agent = Sha256Agent("sha256_agent", self)
        self.scoreboard = Sha256Scoreboard("sha256_scoreboard", self)
        # Start the always-running sampler + the three plan assertions.
        self.coverage = start_coverage()
        self.assertions = start_assertions()
        self.logger.info(
            "Sha256Env build_phase: agent + scoreboard built; coverage "
            "sampler and %d assertion checker(s) started",
            len(self.assertions.tasks),
        )

    def connect_phase(self) -> None:
        """Wire the monitor analysis port into the scoreboard FIFO.

        CONTRACT.md §12/§14: ``agent.ap`` is the monitor's own analysis
        port; subscribing it to the scoreboard FIFO broadcasts every
        completed transaction to the in-order grader.
        """
        super().connect_phase()
        self.scoreboard.connect_monitor(self.agent.ap)
        self.logger.info(
            "Sha256Env connect_phase: agent.ap -> scoreboard analysis fifo"
        )