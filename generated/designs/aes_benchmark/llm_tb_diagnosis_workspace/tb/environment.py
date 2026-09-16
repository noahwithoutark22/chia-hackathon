"""AES-128 UVM environment (stage 6 integration).

:class:`AES128Environment` assembles the stage-3..stage-5 components:

* :class:`tb.agent.AES128Agent` (stimulus + monitor; active arm),
* :class:`tb.scoreboard.AES128Scoreboard` (oracle comparison),
* :class:`tb.coverage.AES128Coverage` (functional coverage), and
* :class:`tb.assertions.AES128Assertions` (SVA-replacement checkers).

Wiring (``CONTRACT.md`` section 7.4): the agent's ``analysis_port`` fans out
to the scoreboard's ``analysis_export`` and the coverage subscriber's
``analysis_export`` (a single producer, two consumers; pyuvm TLM
``uvm_analysis_port.connect()`` supports multiple exports).

The environment owns the assertion checker lifecycle: they launch in
``build_phase`` (cocotb tasks) and are stopped in ``final_phase`` so no
checker outlives the UVM run (``CONTRACT.md`` section 6).

Pass/fail: the *test* stage derives the verdict from
``scoreboard.results()`` (and ``REQUIRES_TRANSACTIONS``).  This environment
only reports; it never fails the run itself, keeping the pass criteria in
one vocabulary (``tb/test.py``).
"""

from pyuvm import uvm_env

from tb.agent import AES128Agent
from tb.assertions import launch_assertions
from tb.coverage import AES128Coverage
from tb.scoreboard import AES128Scoreboard

__all__ = ["AES128Environment"]


class AES128Environment(uvm_env):
    """Top-level UVM environment for the ``aes128`` DUT."""

    def __init__(self, name="aes128_env", parent=None):
        super().__init__(name, parent)
        self.agent = None
        self.scoreboard = None
        self.coverage = None
        self.assertions = None

    def build_phase(self):
        super().build_phase()
        self.agent = AES128Agent("aes128_agent", self)
        self.scoreboard = AES128Scoreboard("aes128_scoreboard", self)
        self.coverage = AES128Coverage("aes128_coverage", self)
        self.assertions = launch_assertions()
        if self.assertions is None:
            raise RuntimeError(
                f"{self.get_full_name()}: launch_assertions() returned None "
                f"(tb.assertions import failure)"
            )
        self.logger.info(
            "%s: built agent, scoreboard, coverage and %d assertion "
            "checker(s)",
            self.get_full_name(),
            len(self.assertions.tasks),
        )

    def connect_phase(self):
        super().connect_phase()
        self.agent.analysis_port.connect(self.scoreboard.analysis_export)
        self.agent.analysis_port.connect(self.coverage.analysis_export)
        self.logger.info(
            "%s: agent.analysis_port -> scoreboard.analysis_export, "
            "coverage.analysis_export",
            self.get_full_name(),
        )

    def report_phase(self):
        super().report_phase()
        results = self.scoreboard.results()
        self.logger.info(
            "%s: scoreboard %s",
            self.get_full_name(),
            results,
        )
        if self.assertions is not None:
            self.logger.info(
                "%s: checks %s", self.get_full_name(), self.assertions.summarize()
            )
        coverage_pct = self.coverage.report()
        self.logger.info(
            "%s: functional coverage %.2f%%",
            self.get_full_name(),
            float(coverage_pct),
        )

    def final_phase(self):
        super().final_phase()
        if self.assertions is not None:
            self.assertions.stop()
        self.logger.info("%s: all checker tasks stopped", self.get_full_name())