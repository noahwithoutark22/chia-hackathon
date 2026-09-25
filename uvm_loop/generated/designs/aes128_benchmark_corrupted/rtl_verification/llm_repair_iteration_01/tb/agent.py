"""AES-128 agent (pyuvm ``uvm_agent``).

Stage-3 (OBSERVATION) artifact of the CHIA cocotb+pyuvm generator for the
``aes128`` DUT ``aes128_benchmark_corrupted/aes128.sv``.

:class:`Aes128Agent` is the hierarchical container that encapsulates the
complete stimulus/observation path of the bench:

    Aes128Sequencer --seq_item_export <-> seq_item_port--> Aes128Driver
                                                           (drives DUT pins)
    Aes128Driver / sequences          ->  DUT pins      -> Aes128Monitor
                                                           (samples DUT pins)
    Aes128Monitor.analysis_port --connect--> agent.analysis_port (to env)

It combines:

* the stage-2 stimulus components (:class:`~driver.Aes128Driver`,
  :class:`~sequencer.Aes128Sequencer`) produced in the stimulus stage, and
* the stage-3 monitor (:class:`~monitor.Aes128Monitor}) produced in this
  stage.

Component attributes consumed by later stages (env / scoreboard):
``agent.driver``, ``agent.sequencer``, ``agent.monitor``,
``agent.analysis_port``.

Construction (``build_phase``):

* The agent is used in its default UVM active mode (pyuvm 5.0.0's
  ``uvm_agent.build_phase`` sets ``is_active = UVM_ACTIVE``, overridable via
  the ConfigDB key ``"is_active"``).
* ``analysis_port`` and the passive ``monitor`` are always built; in active
  mode the ``driver`` and ``sequencer`` are built as well.  A passive agent
  (``is_active == UVM_PASSIVE``) builds only the monitor — useful if the env
  reuses this agent purely for observation.

Wiring (``connect_phase`` — pyuvm phase ordering is bottom-up, so the
children's ``build_phase`` has already run):

    driver.seq_item_port.connect(sequencer.seq_item_export)
    monitor.analysis_port.connect(agent.analysis_port)

The hierarchical analysis connection is the standard pyuvm 5.0.0 pattern:
``uvm_analysis_port.connect(export)`` appends ``export`` to the port's
``subscribers`` list, and a ``uvm_analysis_port`` is itself a subclass of
``uvm_export_base`` (``uvm_port_base(uvm_export_base)``) with a ``write``
method, so ``monitor.analysis_port.connect(agent.analysis_port)`` is a valid
subscriber registration.  When the monitor writes, it broadcasts to
``agent.analysis_port``, which re-broadcasts to the subscribers the
environment attaches in its own ``connect_phase`` (e.g. scoreboard /
coverage analysis exports).  A downstream component subscribes with
``agent.analysis_port.connect(<analysis_export>)`` and receives every
transaction the monitor publishes.

No SystemVerilog anywhere: pure pyuvm (5.0.0) composition of cocotb-based
components.  All APIs used here are public pyuvm 5.0.0 APIs.
"""

from pyuvm import uvm_agent, uvm_analysis_port

# The stage-2 stimulus components live in tb/driver.py / tb/sequencer.py
# (see the uvm_stimulus stage checkpoint).  They are imported defensively so
# this module stays importable even in a workspace where the stimulus stage
# has not been materialized yet; building an ACTIVE agent without them fails
# loudly in build_phase (a passive, monitor-only agent does not need them).
try:
    from driver import Aes128Driver
    _STAGE2_DRIVER_OK = True
except ImportError as _err:  # pragma: no cover - depends on workspace state
    Aes128Driver = None
    _STAGE2_DRIVER_OK = False
try:
    from sequencer import Aes128Sequencer
    _STAGE2_SEQUENCER_OK = True
except ImportError as _err:  # pragma: no cover - depends on workspace state
    Aes128Sequencer = None
    _STAGE2_SEQUENCER_OK = False

from monitor import Aes128Monitor

__all__ = ["Aes128Agent"]


class Aes128Agent(uvm_agent):
    """Active AES-128 agent: driver + sequencer + monitor, one exported
    analysis port."""

    def __init__(self, name="aes128_agent", parent=None):
        super().__init__(name, parent)
        self.driver = None
        self.sequencer = None
        self.monitor = None
        self.analysis_port = None

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self):
        # pyuvm's uvm_agent.build_phase establishes is_active (default
        # UVM_ACTIVE, overridable via the ConfigDB key "is_active").
        super().build_phase()
        #: Analysis port exported to the environment: receives every
        #: transaction observed by the monitor.
        self.analysis_port = uvm_analysis_port("analysis_port", self)
        #: Passive observer -- always present.
        self.monitor = Aes128Monitor("monitor", self)
        if self.active():
            if not _STAGE2_DRIVER_OK or not _STAGE2_SEQUENCER_OK:
                raise RuntimeError(
                    "Aes128Agent: the stage-2 stimulus components "
                    "(tb/driver.py / tb/sequencer.py) are missing; cannot "
                    "build an ACTIVE agent.  Use a passive agent or "
                    "materialise the stimulus stage files first."
                )
            #: Stimulus path -- present only in active mode.
            self.driver = Aes128Driver("driver", self)
            self.sequencer = Aes128Sequencer("sequencer", self)
        else:
            self.logger.info(
                "%s is passive: no driver/sequencer built", self.get_name())

    def connect_phase(self):
        super().connect_phase()
        if self.active():
            # Standard pyuvm driver <-> sequencer pull connection
            # (uvm_driver.seq_item_port <-> uvm_sequencer.seq_item_export).
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
        # Monitor observation flows out through the agent-level port
        # (uvm_analysis_port -> uvm_analysis_port subscriber broadcast;
        # see the module docstring for the pyuvm 5.0.0 connection model).
        self.monitor.analysis_port.connect(self.analysis_port)