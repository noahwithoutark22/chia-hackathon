"""i2c_master UVM environment (stage-6 INTEGRATION artifact).

Assembles every earlier-stage verification component into a single pyuvm
``uvm_env`` that each test class instantiates in ``build_phase``:

* ``I2CAgent``              (stage 2/3: sequencer + driver + monitor)
* ``I2CScoreboard``         (stage 4: in-order reference-model + stream +
                             control grader)
* ``I2CCoverage``           (stage 5: cocotb-coverage sampler, always-on)
* ``I2CAssertions``         (stage 5: the 15 plan assertion checkers, launched
                             via ``launch_assertions``)

WIRING (CONTRACT.md §13/§14/§15/§16):

* ``build_phase`` fetches the shared ``"dut"`` / ``"i2c_pins"`` ConfigDB keys
  (CONTRACT.md §6), creates the agent, scoreboard and coverage component, and
  launches the plan assertion checkers (CONTRACT.md §16).  The checkers are
  plain-Python coroutines started with public Cocotb 2.1.0
  ``cocotb.start_soon``; a violation logs and raises ``AssertionError`` so the
  enclosing cocotb test fails immediately (fail-fast).
* ``connect_phase`` performs exactly two wiring tasks:

  1. sets the shared driver handle ConfigDB key ``"i2c_driver"``
     (``KEY_I2C_DRIVER``, CONTRACT.md §13.1) from ``agent.driver``;
  2. subscribes the monitor analysis ports to the scoreboard and coverage
     FIFOs through ``connect_monitor(self.agent)`` (both accept the agent and
     resolve it via ``.monitor``; CONTRACT.md §14/§15/§16).

  Phase-ordering note (recorded in CONTRACT.md §17): pyuvm executes
  ``build_phase`` top-down, so ``I2CEnv.build_phase`` runs *before* the
  agent's ``build_phase`` constructs ``agent.driver``.  The ``"i2c_driver"``
  key is therefore set in ``connect_phase`` (which runs after every
  ``build_phase``), a justified clarification of the §13.1 "in build_phase"
  wording.  No other new ConfigDB keys are introduced.

WATCHDOG OWNERSHIP (CONTRACT.md §8/§13.7/§16): by design the env owns the
*structural checkers* and the *watchdog primitive*, while each TEST owns its
*watchdog budget*.  ``arm_watchdog(budget)`` / ``disarm_watchdog()`` wrap the
``launch_watchdog()`` / ``task.kill()`` primitives; every test's ``run_phase``
arms its budget and disarms it in a ``finally``.  ``test_top.py``
additionally guards the whole run with a coarse ``with_timeout``
simulation-time bound.
"""

try:  # I2CCoverage is defined only when both pyuvm and cocotb-coverage are
    # importable (i2c_coverage.py guards the class definition); at simulation
    # time both are always present.  The fallback keeps the module importable
    # in a coverage-less context and disables the coverage component only.
    from i2c_coverage import I2CCoverage
except ImportError:  # pragma: no cover - coverage-less sandbox only
    I2CCoverage = None

from pyuvm import ConfigDB, uvm_env

from i2c_agent import I2CAgent
from i2c_assertions import launch_assertions, launch_watchdog
from i2c_driver import KEY_I2C_DRIVER
from i2c_pins import I2CPins, KEY_DUT_PINS, WATCHDOG_CYCLES
from i2c_scoreboard import I2CScoreboard

#: Per-test watchdog margin in clock cycles (CONTRACT.md §17).  Each directed
#: scenario must fit comfortably inside this budget on a REPAIRED RTL; the
#: corner and randomized tests override with proportionally larger budgets
#: (see i2c_test.py).
WATCHDOG_MARGIN_CYCLES = 10000


class I2CEnv(uvm_env):
    """Top-level verification environment for the ``i2c_master`` DUT.

    Instantiates the agent (stimulus + observation), the scoreboard
    (reference-model grading), the functional-coverage sampler and the
    structural assertion checker controller, and wires them together.  Also
    owns the per-test watchdog primitive (arming/disarming) while the tests
    own their budgets.
    """

    def __init__(self, name: str = "i2c_env", parent=None) -> None:
        super().__init__(name, parent)
        self.pins = None            # type: I2CPins
        self.agent = None           # type: I2CAgent
        self.scoreboard = None      # type: I2CScoreboard
        self.coverage = None        # type: I2CCoverage | None
        self.assertions = None      # type: I2CAssertions
        self._watchdog_task = None          # running cocotb watchdog task
        self._watchdog_budget = None        # budget of the armed watchdog

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Build the agent + scoreboard + coverage, then launch assertions.

        The assertion checkers and the coverage sampler start here
        (CONTRACT.md §16) so they observe the entire test -- including every
        sequence-internal reset.  They are background cocotb coroutines; the
        cocotb test manager ends them when the test finishes, and a checker
        violation fails the test immediately (fail-fast).
        """
        super().build_phase()
        self.pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        if not isinstance(self.pins, I2CPins):
            self.logger.warning(
                "I2CEnv: ConfigDB['%s'] is not an I2CPins: %r",
                KEY_DUT_PINS, self.pins,
            )
        self.agent = I2CAgent("i2c_agent", self)
        self.scoreboard = I2CScoreboard("i2c_scoreboard", self)
        if I2CCoverage is not None:
            self.coverage = I2CCoverage("i2c_coverage", self)
        # Launch the 15 plan assertion checkers (plain-Python coroutines,
        # CONTRACT.md §16; fail-fast on any violation).
        self.assertions = launch_assertions(pins=self.pins, log=self.logger)
        self.logger.info(
            "I2CEnv build_phase: agent + scoreboard built%s; %d assertion "
            "checker coroutine(s) started",
            " + coverage" if self.coverage is not None else " (coverage off)",
            len(self.assertions.tasks) if self.assertions is not None else 0,
        )

    def connect_phase(self) -> None:
        """Set the shared driver handle and wire the monitor analysis ports.

        1. ``"i2c_driver"`` (CONTRACT.md §13.1): the single set of the
           flow-sequence driver handle, placed here because pyuvm runs
           ``build_phase`` top-down (agent.driver is constructed inside
           ``agent.build_phase``, which runs after the env's build_phase;
           see CONTRACT.md §17).
        2. ``connect_monitor(self.agent)`` subscribes the monitor's
           ``ap``/``hung_ap``/``reset_ap`` (scoreboard) and ``ap``/
           ``reset_ap`` (coverage) to the component FIFOs under pyuvm
           5.0.0's broadcast model (CONTRACT.md §14.1/§15/§16).
        """
        super().connect_phase()
        if self.agent is None:
            raise RuntimeError("I2CEnv.connect_phase: agent was never built")
        if self.agent.driver is None:
            self.logger.error(
                "I2CEnv: agent.driver is None (passive agent?); 'i2c_driver' "
                "key cannot be set and flow sequences will fail",
            )
        else:
            ConfigDB().set(None, "*", KEY_I2C_DRIVER, self.agent.driver)
        self.scoreboard.connect_monitor(self.agent)
        if self.coverage is not None:
            self.coverage.connect_monitor(self.agent)
        self.logger.info(
            "I2CEnv connect_phase: 'i2c_driver' set; monitor ap/hung_ap/"
            "reset_ap wired into scoreboard%s",
            " and coverage sampler" if self.coverage is not None else "",
        )

    # ------------------------------------------------------------------
    # Watchdog primitive (budgets are owned by the tests, CONTRACT.md §17)
    # ------------------------------------------------------------------
    def arm_watchdog(self, budget_cycles=None) -> None:
        """Arm the bounded clock-cycle watchdog (idempotent per test).

        ``budget_cycles`` defaults to the global ``WATCHDOG_CYCLES`` bound.
        A hung FSM with a live clock raises ``AssertionError`` once the
        budget elapses, failing the test.  Must be paired with
        :meth:`disarm_watchdog` (the tests do so in a ``finally``).
        """
        if self._watchdog_task is not None:
            self.logger.warning("I2CEnv: watchdog already armed; ignoring")
            return
        budget = WATCHDOG_CYCLES if budget_cycles is None else int(budget_cycles)
        self._watchdog_budget = max(1, budget)
        self._watchdog_task = launch_watchdog(
            pins=self.pins,
            timeout_cycles=self._watchdog_budget,
            log=self.logger,
        )

    def disarm_watchdog(self) -> None:
        """Kill the armed watchdog task (safe to call when not armed)."""
        if self._watchdog_task is None:
            return
        try:
            self._watchdog_task.kill()
        except Exception:  # pragma: no cover - defensive teardown
            pass
        self._watchdog_task = None
        self._watchdog_budget = None

    # ------------------------------------------------------------------
    # End-of-test reporting helper
    # ------------------------------------------------------------------
    def summarize(self) -> str:
        """One-line summary of scoreboard + coverage + assertions."""
        parts = []
        if self.scoreboard is not None:
            parts.append(self.scoreboard.get_summary())
        if self.coverage is not None:
            parts.append(self.coverage.get_summary())
        if self.assertions is not None:
            parts.append(self.assertions.summarize())
        return "; ".join(parts) if parts else "no summary data"