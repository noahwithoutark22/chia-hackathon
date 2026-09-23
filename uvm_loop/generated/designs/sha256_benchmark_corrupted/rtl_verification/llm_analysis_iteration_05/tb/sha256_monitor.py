"""SHA-256 UVM monitor (stage-3 OBSERVATION artifact).

Observability component for the cocotb + pyuvm verification environment
described by CONTRACT.md.  ``Sha256Monitor`` continuously samples the DUT
pins through the shared ``Sha256Pins`` helper (ConfigDB key
``"sha256_pins"``, CONTRACT.md §5) and publishes one ``Sha256Transaction``
per detected ``start`` pulse through a ``uvm_analysis_port`` (attribute
``ap``).

TIMING / COMPLETION MODEL (CONTRACT.md §4, §7, §8 -- authoritative):

* The RTL samples ``start`` and ``block`` on the rising edge of ``clk``
  (the driver settles all inputs on falling edges, so a value read right
  after ``RisingEdge(clk)`` is exactly the value the RTL samples on that
  same edge).
* A transaction begins on the first rising edge where ``start == 1`` and
  the *previous* rising edge had ``start == 0`` (0->1 edge detection; a
  multi-cycle start pulse therefore produces exactly one transaction).
  On that same edge the monitor captures ``block``.
* The corrupted RTL never deasserts ``busy`` and drives ``done = 1``
  continuously (DISC-001/DISC-013), so completion is NEVER inferred from
  the ``done`` pin.  Instead, a per-transaction completion observer waits
  ``COMPLETION_MARGIN_CYCLES`` (70, CONTRACT.md §7) rising edges after the
  start edge, samples ``done``/``digest``, records
  ``latency_cycles = COMPLETION_MARGIN_CYCLES`` and publishes the
  transaction with all fields populated.
* One completion observer is spawned per start pulse via
  ``cocotb.start_soon`` (public Cocotb 2.1.0 API), so back-to-back and
  start-while-busy-restarts scenarios (``back_to_back_transactions``,
  ``start_while_busy_restarts``) are observed correctly: a new start is
  still detected while the previous completion is pending.  Observers
  finish in start order (equal wait length), so in-order scoreboard
  matching holds.

PUBLISHING CONTRACT:

* Exactly one ``Sha256Transaction`` per start pulse.
* ``block`` and ``start`` are sampled at the start edge; ``done``,
  ``digest`` and ``latency_cycles`` are sampled at the fixed-latency
  completion edge (``done`` after reset is 1 per DISC-001).
* ``txn_id`` is a monotonic, in-order, 1-based per-simulation counter.
* Samples are read through the documented Cocotb 2.1.0 read path
  ``int(dut.<pin>.value)`` (via ``Sha256Pins``).  If a pin resolves to
  X/Z at a sample point (e.g. before the driver/idle/reset have settled
  outputs), ``int(...)`` raises ``ValueError`` and the monitor logs a
  warning and samples 0 defensively -- it never lets an uninitialized
  simulation output kill the observation stream.

No SystemVerilog anywhere: pure pyuvm (5.0.0) + cocotb (2.1.0) coroutines.
"""

import cocotb

from pyuvm import ConfigDB, uvm_analysis_port, uvm_monitor

from cocotb.triggers import ClockCycles, RisingEdge

from sha256_pins import COMPLETION_MARGIN_CYCLES, Sha256Pins
from sha256_transaction import Sha256Transaction


class Sha256Monitor(uvm_monitor):
    """Samples the SHA-256 DUT pins and publishes transactions."""

    def __init__(self, name: str = "sha256_monitor", parent=None) -> None:
        super().__init__(name, parent)
        self.pins = None  # type: Sha256Pins  (populated in build_phase)
        self.ap = None    # type: uvm_analysis_port  (built in build_phase)
        self._next_txn_id = 0

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self) -> None:
        """Fetch the shared ``Sha256Pins`` helper and build the analysis port.

        Exact ConfigDB key: ``"sha256_pins"`` (CONTRACT.md §5).  The raw
        ``dut`` handle is never used directly.  Raising here fails the test
        early if the environment was assembled without the key.
        """
        super().build_phase()
        self.pins = ConfigDB().get(None, "", "sha256_pins")
        if self.pins is None:
            self.logger.error(
                "CONTRACT key 'sha256_pins' missing from ConfigDB: "
                "cannot observe the DUT."
            )
            raise RuntimeError(
                "Sha256Monitor.build_phase: ConfigDB key 'sha256_pins' not found"
            )
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self) -> None:
        """Sample the DUT pins on every rising edge and detect start pulses.

        Synchronized on ``RisingEdge(dut.clk)`` exactly (CONTRACT.md §6/§7).
        The first await syncs to the clock (no reads at time zero); the
        driver has already idled the inputs by the first sampled edge.
        """
        # Sync edge: establishes in-simulation sampling and a defined
        # ``prev_start`` (the driver drives start=0 at time zero, so this
        # first sample is 0 unless a pulse was already in flight).
        await RisingEdge(self.pins.clk)
        prev_start = self._read_pin("start")

        while True:
            await RisingEdge(self.pins.clk)
            start_val = self._read_pin("start")
            # 0->1 rising-edge detection: one transaction per start pulse,
            # regardless of pulse width (driver emits exactly one cycle).
            if start_val == 1 and prev_start == 0:
                self._begin_transaction()
            prev_start = start_val

    # ------------------------------------------------------------------
    # Transaction observation
    # ------------------------------------------------------------------
    def _begin_transaction(self) -> None:
        """Capture the start-edge values and launch the fixed-latency
        completion observer for this transaction."""
        block_val = self._read_pin("block")
        self._next_txn_id += 1
        txn = Sha256Transaction(
            name=f"mon_txn_{self._next_txn_id}",
            start=1,
            block=block_val,
            txn_id=self._next_txn_id,
        )
        self.logger.debug(
            "Start pulse detected, starting txn_id=%d block=0x%0128x",
            txn.txn_id,
            txn.block,
        )
        # Spawned observer runs concurrently with the sampling loop, so a
        # new start during the pending window is still detected.
        cocotb.start_soon(self._observe_completion(txn))

    async def _observe_completion(self, txn: Sha256Transaction) -> None:
        """Wait COMPLETION_MARGIN_CYCLES, sample outputs, publish.

        Completion is defined purely by the fixed cycle count (CONTRACT.md
        §7): the broken ``done`` pin is never used as a completion
        indicator (DISC-001/DISC-013).
        """
        await ClockCycles(self.pins.clk, COMPLETION_MARGIN_CYCLES)
        txn.done = self._read_pin("done")
        txn.digest = self._read_pin("digest")
        txn.latency_cycles = COMPLETION_MARGIN_CYCLES
        self.logger.debug("Publishing completed transaction: %s",
                          txn.convert2string())
        self.ap.write(txn)

    # ------------------------------------------------------------------
    # Pin sampling helpers
    # ------------------------------------------------------------------
    def _read_pin(self, what: str) -> int:
        """Read one DUT pin via the contract read path.

        ``Sha256Pins.read_*`` uses ``int(dut.<pin>.value)`` (Cocotb 2.1.0
        documented path).  If the value still contains X/Z at the sample
        point, ``int()`` raises ``ValueError``; that is logged and sampled
        as 0 so observation never dies on uninitialized simulation state.
        """
        reader = {
            "start": self.pins.read_start,
            "block": self.pins.read_block,
            "done": self.pins.read_done,
            "digest": self.pins.read_digest,
        }[what]
        try:
            return int(reader())
        except ValueError as exc:
            self.logger.warning(
                "Pin '%s' not resolvable (X/Z at sample time) -- sampling 0. %s",
                what,
                exc,
            )
            return 0