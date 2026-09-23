"""SHA-256 UVM agent (stage-3 OBSERVATION artifact).

Encapsulates the stimulus half (sequencer + driver from stage 2) and this
stage's observer (monitor) into a single reusable pyuvm component:

* ``Sha256Agent(uvm_agent)`` hosts, in ``build_phase``:
    - ``sequencer`` = ``Sha256Sequencer("sequencer", self)``
    - ``driver``    = ``Sha256Driver("driver", self)``
    - ``monitor``   = ``Sha256Monitor("monitor", self)``
* ``connect_phase`` performs the exact stimulus wiring mandated by
  CONTRACT.md §11: ``driver.seq_item_port`` is connected to
  ``sequencer.seq_item_export`` so item transfer works through the standard
  pyuvm get/put handshake.
* ``ap`` is the agent-level analysis port.  In pyuvm 5.0.0 (verified
  against the project's pinned sources) ``uvm_analysis_port.write(datum)``
  broadcasts to the port's ``subscribers`` list, and
  ``uvm_analysis_port.connect(export)`` appends ``export`` to that list.
  ``ap`` is therefore assigned the *same object* as ``monitor.ap`` -- a
  downstream component subscribes with
  ``agent.ap.connect(<fifo_analysis_export>)`` and directly receives every
  transaction the monitor publishes through ``monitor.ap.write(...)``.
  Creating a distinct agent port and forwarding would silently drop writes
  under this broadcast model, so the alias is the correct wiring.

Component attribute names consumed by later stages (env / scoreboard):
``agent.sequencer``, ``agent.driver``, ``agent.monitor``, ``agent.ap``.

No SystemVerilog anywhere: pure pyuvm (5.0.0) composition of cocotb-based
components.
"""

from pyuvm import uvm_agent

from sha256_driver import Sha256Driver
from sha256_monitor import Sha256Monitor
from sha256_sequencer import Sha256Sequencer


class Sha256Agent(uvm_agent):
    """Active agent: sequencer + driver (stimulus) + monitor (observation)."""

    def __init__(self, name: str = "sha256_agent", parent=None) -> None:
        super().__init__(name, parent)
        self.sequencer = None  # type: Sha256Sequencer
        self.driver = None     # type: Sha256Driver
        self.monitor = None    # type: Sha256Monitor
        self.ap = None         # type: alias of self.monitor.ap

    def build_phase(self) -> None:
        """Build the sequencer, driver and monitor as children."""
        super().build_phase()
        self.sequencer = Sha256Sequencer("sequencer", self)
        self.driver = Sha256Driver("driver", self)
        self.monitor = Sha256Monitor("monitor", self)

    def connect_phase(self) -> None:
        """Wire stimulus transport and expose the monitor analysis port.

        ``connect_phase`` is bottom-up in pyuvm, so the monitor's
        ``build_phase`` has already run by the time this executes and
        ``monitor.ap`` exists.
        """
        super().connect_phase()
        # CONTRACT.md §11: connect the driver's seq_item_port to the
        # sequencer's seq_item_export (driver consumes items, sequencer
        # provides them from the running sequence).
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
        # Agent-level analysis port = the monitor's own port (same object).
        # Later stages subscribe downstream fifos/scoreboards with
        # agent.ap.connect(<analysis_export>) (see module docstring).
        self.ap = self.monitor.ap