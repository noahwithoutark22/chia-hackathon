"""i2c_master UVM monitor for the cocotb + pyuvm bench (observation stage).

Stage-3 artifact of the CHIA cocotb+pyuvm environment generator (see
CONTRACT.md in this directory; it is the authoritative convention record).

``I2CMonitor`` is a pyuvm ``uvm_monitor`` that observes the i2c_master DUT in
purely passive fashion -- it only *reads* pins through the shared ``I2CPins``
handle (never drives) and publishes what it observes:

* completed ``I2CTransaction`` items on the analysis port ``ap``,
* hung-transaction reports (``I2CHungTransaction``) on ``hung_ap``,
* reset edge events (``I2CResetEvent``) on ``reset_ap``.

The consumer components (scoreboard, coverage, assertions, env) connect
directly to ``agent.monitor.<port>``; this module defines no agent-level
forwarding ports to keep the wiring explicit.

Observation model (CONTRACT.md §7, binding):

  * Transaction offer   == the ``start`` input sampled high while the monitor
    is idle (the TB drives it while the DUT is idle, CONTRACT.md §7.1).
  * Start acceptance    == ``busy`` rising 0 -> 1, waited with a bounded
    budget (``START_TIMEOUT_CYCLES``).  A ``busy`` high level observed while
    idle is treated as an already-accepted transaction (inexorable offer).
  * Completion point    == the rising clock edge on which ``done`` makes a
    0 -> 1 pulse after acceptance (CONTRACT.md §7.2), waited with a bounded
    budget (``DONE_TIMEOUT_CYCLES``).  At that edge the observed outputs are
    sampled *strictly* (``I2CPins.sample_outputs_strict()`` rejects X/Z).
  * Reset assertion (``rst_n`` 1 -> 0) drops an in-flight transaction -- no
    item is published on ``ap`` for it (CONTRACT.md §11) -- and a reset event
    is published instead; deassertion also publishes a reset event.
  * A bounded-wait expiry publishes an ``I2CHungTransaction`` (a structured
    "hung transaction" report, never a pass) on ``hung_ap``.  The monitor
    alone does *not* abort the test: the driver's bounded-wait exceptions,
    the always-running watchdog, and the scoreboard/assertion stages own
    failing the test (CONTRACT.md §7.3/§11); this monitor only reports the
    hang with structured data.

Published ``I2CTransaction`` items carry exactly the fields defined in
CONTRACT.md §5 (stimulus fields sampled from the DUT inputs, observed-output
fields sampled at the completion point, and the ``txn_id`` /
``latency_cycles`` metadata).  ``slave_ack`` and ``read_data`` are
TB-side *intent* fields that cannot be observed from DUT pins, so the
monitor leaves them at their constructor defaults; the scoreboard must not
derive ACK expectations from monitor items alone (CONTRACT.md records this
below in the stage-3 appendix).

In addition, both completed and hung items carry a monitor-only *side*
attribute ``item._stream_trace``: one dict per clock cycle from acceptance
onward with the externally resolved open-drain bus levels
(``I2CPins.resolve_sda_level()`` / ``resolve_scl_level()``) and the raw
drive controls (``sda_out``/``sda_oe``/``scl_out``/``scl_oe``).  This feeds
the plan's ``stream_checker`` reconstruction (scoreboard stage) and is NOT a
CONTRACT.md §5 field.

Cocotb 2.1.0 public-API notes honored throughout (verified against the
cocotb-2.1.0 wheel):

* Sampling is an ``async def`` coroutine synchronized on the clock with
  ``await RisingEdge(self.pins.clk)`` (only ``cocotb.triggers.RisingEdge``).
* Pin reads use the ``I2CPins.read_*`` helpers (``int(dut.<pin>.value)``
  semantics) and ``_to_int`` for deterministic X/Z handling; ``rst_n`` is a
  structural pin so it is read through ``i2c_pins._to_int`` directly.
* ``cocotb.simtime.get_sim_time("ns")`` for event timestamps (the 2.x
  documented location, same as the driver).
* ``cocotb.handle.ModifiableObject`` is never imported (removed in 2.1.0).
"""

import os

try:  # cocotb is always present at simulation time; the fallback exists
    # only so the module's pure-Python self-check (__main__) can run in a
    # sandbox that does not have cocotb installed (see i2c_pins.py).
    from cocotb.simtime import get_sim_time
    from cocotb.triggers import RisingEdge
except ImportError:  # pragma: no cover - direct-run sandbox check only
    if __name__ != "__main__":
        raise
    get_sim_time = None
    RisingEdge = None

from pyuvm import ConfigDB, uvm_analysis_port, uvm_monitor, uvm_sequence_item

from i2c_pins import (
    DONE_TIMEOUT_CYCLES,
    I2CPins,
    KEY_DUT,
    KEY_DUT_PINS,
    START_TIMEOUT_CYCLES,
    _to_int,
)
from i2c_transaction import I2CTransaction

# ---------------------------------------------------------------------------
# Hung stages (CONTRACT.md §7.3): the two binding bounded-wait expiry sites,
# plus one abnormal-completion site the monitor may hit internally.
# ---------------------------------------------------------------------------
HUNG_STAGE_START_ACCEPTANCE = "start-acceptance"
HUNG_STAGE_DONE_PULSE = "done-pulse"
HUNG_STAGE_COMPLETION_SAMPLE = "completion-sample"


class I2CResetEvent(uvm_sequence_item):
    """Monitor-raised reset edge notification (coverage / control events).

    ``kind`` is ``"asserted"`` (rst_n 1 -> 0) or ``"deasserted"`` (0 -> 1).
    ``in_flight`` and ``dropped_transaction`` record whether a transaction
    was active at assertion and whether the monitor therefore discarded its
    in-flight item (CONTRACT.md §11).  ``edge_ns`` is the simulation time of
    the sampled edge.
    """

    def __init__(
        self,
        name: str = "i2c_reset_event",
        kind: str = "",
        in_flight: bool = False,
        dropped_transaction: bool = False,
        edge_ns: float = None,
    ) -> None:
        super().__init__(name)
        self.kind = str(kind)
        self.in_flight = bool(in_flight)
        self.dropped_transaction = bool(dropped_transaction)
        self.edge_ns = edge_ns

    def convert2string(self) -> str:
        extra = " in_flight" if self.in_flight else ""
        final_dot = ". dropped" if self.dropped_transaction else ""
        return (
            f"{self.get_name()}[reset {self.kind}{extra}{final_dot} "
            f"edge_ns={self.edge_ns}]"
        )

    def __str__(self) -> str:
        return self.convert2string()


class I2CHungTransaction(I2CTransaction):
    """A monitor-extended item marking a transaction that never completed.

    ``hung`` is always ``True`` and ``hung_stage`` is one of the
    ``HUNG_STAGE_*`` constants.  The observed-output fields hold the DUT
    outputs sampled when the bounded wait elapsed (never scored as a pass;
    the scoreboard/assertion stages turn these into structured defect
    reports).
    """

    def __init__(
        self,
        name: str = "i2c_hung_transaction",
        hung_stage: str = "",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.hung = True
        self.hung_stage = str(hung_stage)

    def convert2string(self) -> str:
        return f"{super().convert2string()} HUNG[stage={self.hung_stage}]"

    def __str__(self) -> str:
        return self.convert2string()


class I2CMonitor(uvm_monitor):
    """Passive observer of the i2c_master DUT (pins in, transactions out).

    Reads the shared ``dut`` and ``I2CPins`` handles from ConfigDB under the
    exact keys ``"dut"`` / ``"i2c_pins"`` (CONTRACT.md §6).

    Analysis ports (all ``uvm_analysis_port``):

    * ``self.ap``        -- completed ``I2CTransaction`` items (one per
      finished transaction, in completion order; ``txn_id`` is the
      monitor-local monotonic id).
    * ``self.hung_ap``   -- ``I2CHungTransaction`` items (bounded wait
      elapsed, or abnormal completion-point sample).
    * ``self.reset_ap``  -- ``I2CResetEvent`` items (assertion + deassertion).
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.ap = uvm_analysis_port("ap", self)
        self.hung_ap = uvm_analysis_port("hung_ap", self)
        self.reset_ap = uvm_analysis_port("reset_ap", self)

    def build_phase(self):
        super().build_phase()
        self.dut = ConfigDB().get(None, "", KEY_DUT)
        self.pins = ConfigDB().get(None, "", KEY_DUT_PINS)
        if not isinstance(self.pins, I2CPins):
            self.logger.warning(
                f"ConfigDB['{KEY_DUT_PINS}'] is not an I2CPins: {self.pins!r}"
            )
        # Bounded-wait budgets (CONTRACT.md §7.3).  Optional env overrides
        # follow the family env-var knob convention (CONTRACT.md §11); the
        # defaults are the i2c_pins constants.
        self._start_timeout = int(
            os.environ.get("I2C_START_TIMEOUT_CYCLES", START_TIMEOUT_CYCLES)
        )
        self._done_timeout = int(
            os.environ.get("I2C_DONE_TIMEOUT_CYCLES", DONE_TIMEOUT_CYCLES)
        )
        if self._start_timeout < 1:
            self._start_timeout = START_TIMEOUT_CYCLES
        if self._done_timeout < 1:
            self._done_timeout = DONE_TIMEOUT_CYCLES
        # Monitor-local monotonic transaction ids (CONTRACT.md §5 metadata).
        self._txn_counter = 0
        # Private observers' state.
        self._prev_rst = self._read_reset()
        self.logger.info(
            f"i2c_monitor ready (start_timeout={self._start_timeout} cycles, "
            f"done_timeout={self._done_timeout} cycles)"
        )

    # ------------------------------------------------------------------
    # run_phase: the monitoring state machine, synchronized on the clock
    # ------------------------------------------------------------------
    async def run_phase(self):
        """Observe the DUT pins for offers, completions, hangs and resets.

        Loop forever: wait for an offer (idle) -> wait for acceptance (busy
        rise) -> wait for the done 0 -> 1 pulse -> publish the item.  Any
        reset assertion aborts the current wait and (if a transaction was
        in flight) drops its item without publishing it.
        """
        await RisingEdge(self.pins.clk)
        self._prev_rst = self._read_reset()
        while True:
            offer_item = await self._watch_idle()
            if offer_item is None:
                continue  # interrupted by reset, back to idle
            accepted = await self._watch_acceptance(offer_item)
            if not accepted:
                continue  # reset or hung start; already reported
            await self._watch_completion(offer_item)

    # ------------------------------------------------------------------
    # Idle: wait for a transaction offer (start high, or busy already high)
    # ------------------------------------------------------------------
    async def _watch_idle(self):
        """Wait (idle) for a start offer or an inexorable busy; return the
        offer item, or ``None`` when a reset asserted during the wait."""
        while True:
            await RisingEdge(self.pins.clk)
            if self._publish_reset_events_if_any(in_flight=False):
                continue
            if self.pins.read_start() == 1 or self.pins.read_busy() == 1:
                ins = self.pins.sample_inputs()
                if self.pins.read_busy() == 1:
                    # Acceptance already latched even though ``start`` may
                    # have been released; a request had to precede it.
                    ins["start"] = 1
                return self._make_item_from_offer(ins)

    # ------------------------------------------------------------------
    # Acceptance: wait for busy 0 -> 1 within START_TIMEOUT_CYCLES
    # ------------------------------------------------------------------
    async def _watch_acceptance(self, item):
        """Wait for ``busy`` rising 0 -> 1 (start acceptance, CONTRACT.md
        §7.1) with the :data:`START_TIMEOUT_CYCLES` bound.  Returns True on
        acceptance; False when a reset dropped the offer or the bound elapsed
        (in which case a hung report was already published)."""
        if self.pins.read_busy() == 1:
            # Accepted before this watcher started (offer seen via busy).
            item._stream_trace = []
            return True
        cycles = 0
        while cycles < self._start_timeout:
            await RisingEdge(self.pins.clk)
            cycles += 1
            if self._publish_reset_events_if_any(in_flight=False):
                return False
            if self.pins.read_busy() == 1:
                item._stream_trace = []
                return True
        self._publish_hung(HUNG_STAGE_START_ACCEPTANCE, item, latency=None)
        return False

    # ------------------------------------------------------------------
    # Completion: wait for done 0 -> 1 (armed after acceptance), bounded,
    # then strictly sample the observed outputs and publish the item.
    # ------------------------------------------------------------------
    async def _watch_completion(self, item):
        """Wait for the ``done`` 0 -> 1 completion pulse with the
        :data:`DONE_TIMEOUT_CYCLES` bound (armed after acceptance, never
        before -- CONTRACT.md §7.3), sampling the completion point strictly.
        A reset assertion mid-transaction drops the item (no publish).
        """
        prev_done = self.pins.read_done()
        latency = 0
        while latency < self._done_timeout:
            await RisingEdge(self.pins.clk)
            latency += 1
            self._record_trace(item)
            if self._publish_reset_events_if_any(in_flight=True):
                # In-flight transaction dropped by reset; the reset event
                # (with dropped_transaction=True) was already published and
                # no completion item is emitted for this transaction.
                return
            cur = self.pins.read_done()
            if cur == 1 and prev_done == 0:
                self._complete_and_publish(item, latency)
                return
            prev_done = cur
        self._publish_hung(HUNG_STAGE_DONE_PULSE, item, latency=latency)

    # ------------------------------------------------------------------
    # Item construction / completion sampling / publishing helpers
    # ------------------------------------------------------------------
    def _make_item_from_offer(self, inputs):
        """Build a stimulus-only ``I2CTransaction`` from a pin input sample."""
        item = I2CTransaction(
            name=f"mon_txn_{self._peek_txn_id()}",
            start=inputs["start"],
            slave_addr=inputs["slave_addr"],
            rw=inputs["rw"],
            tx_data=inputs["tx_data"],
            sda_in=inputs["sda_in"],
            scl_in=inputs["scl_in"],
        )
        item._stream_trace = []  # monitor-only side attribute (see module doc)
        return item

    def _complete_and_publish(self, item, latency):
        """Strictly sample the completion point, fill the item's observed
        fields, and publish it on ``ap``."""
        try:
            self.pins.sample_outputs_strict()  # X/Z outputs are not scored
        except AssertionError:
            self.logger.error(
                "completion point sample carried X/Z on a DUT output; "
                "publishing as abnormal/hung report",
                exc_info=True,
            )
            self._publish_hung(HUNG_STAGE_COMPLETION_SAMPLE, item, latency=latency)
            return
        self.pins.sample_into_item(item)
        item.latency_cycles = int(latency)
        item.txn_id = self._next_txn_id()
        self.logger.info(f"transaction_end (monitor txn_id={item.txn_id}): {item}")
        self.ap.write(item)

    def _publish_hung(self, stage, item, latency=None):
        """Publish a structured hung-transaction report on ``hung_ap``."""
        outs = self.pins.sample_outputs()  # non-strict: an error observation
        hung = I2CHungTransaction(
            name="hung",
            hung_stage=stage,
            start=item.start,
            slave_addr=item.slave_addr,
            rw=item.rw,
            tx_data=item.tx_data,
            sda_in=item.sda_in,
            scl_in=item.scl_in,
            rx_data=outs["rx_data"],
            done=outs["done"],
            busy=outs["busy"],
            ack_error=outs["ack_error"],
            sda_out=outs["sda_out"],
            sda_oe=outs["sda_oe"],
            scl_out=outs["scl_out"],
            scl_oe=outs["scl_oe"],
        )
        if latency is not None:
            hung.latency_cycles = int(latency)
        hung.txn_id = self._next_txn_id()
        hung._stream_trace = list(getattr(item, "_stream_trace", []))
        self.logger.error(
            f"HUNG transaction detected [{stage}] "
            f"(monitor txn_id={hung.txn_id}): {hung}"
        )
        self.hung_ap.write(hung)

    def _record_trace(self, item):
        """Append one bus-level sample per completed clock cycle (acceptance
        onward).  NOT a CONTRACT.md field -- a monitor-side stream trace."""
        trace = getattr(item, "_stream_trace", None)
        if trace is None:
            trace = []
            item._stream_trace = trace
        trace.append(
            {
                "sda": self.pins.resolve_sda_level(),
                "scl": self.pins.resolve_scl_level(),
                "sda_out": self.pins.read_sda_out(),
                "sda_oe": self.pins.read_sda_oe(),
                "scl_out": self.pins.read_scl_out(),
                "scl_oe": self.pins.read_scl_oe(),
            }
        )

    # ------------------------------------------------------------------
    # Reset edge handling
    # ------------------------------------------------------------------
    def _publish_reset_events_if_any(self, *, in_flight):
        """Sample rst_n against its previous value and publish any edge
        events.  Returns True when rst_n *asserted* (1 -> 0) on this edge,
        which forces the caller to drop the current wait / in-flight item.
        """
        cur = self._read_reset()
        prev = self._prev_rst
        self._prev_rst = cur
        asserted = bool(prev == 1 and cur == 0)
        deasserted = bool(prev == 0 and cur == 1)
        if asserted:
            self._publish_reset_event(
                "asserted",
                in_flight=bool(in_flight),
                dropped=bool(in_flight),
            )
        if deasserted:
            self._publish_reset_event(
                "deasserted", in_flight=False, dropped=False
            )
        return asserted

    def _publish_reset_event(self, kind, *, in_flight, dropped):
        event = I2CResetEvent(
            name=f"reset_{kind}",
            kind=kind,
            in_flight=in_flight,
            dropped_transaction=dropped,
            edge_ns=get_sim_time("ns"),
        )
        self.logger.info(str(event))
        self.reset_ap.write(event)

    # ------------------------------------------------------------------
    # Small internal helpers
    # ------------------------------------------------------------------
    def _read_reset(self):
        """Deterministic read of the structural ``rst_n`` pin (X/Z -> 0)."""
        return _to_int(self.pins.rst_n.value, 1)

    def _peek_txn_id(self):
        return self._txn_counter

    def _next_txn_id(self):
        tid = self._txn_counter
        self._txn_counter += 1
        return tid


# ---------------------------------------------------------------------------
# TB-internal unit check for the two monitor-local classes (no cocotb/pyuvm
# available in a plain-Python sandbox).  Runs only when executed directly;
# under cocotb the module is imported, so this never interferes with a
# simulation.
# ---------------------------------------------------------------------------
def _self_test_publish_classes():
    try:
        reset = I2CResetEvent(
            name="r", kind="asserted", in_flight=True, dropped_transaction=True
        )
    except Exception as exc:  # noqa: BLE001 - sandbox may lack pyuvm
        raise AssertionError(f"I2CResetEvent construction failed: {exc}") from exc
    assert reset.kind == "asserted"
    assert reset.in_flight is True
    assert reset.dropped_transaction is True
    assert "asserted" in str(reset)

    try:
        hung = I2CHungTransaction(
            name="h",
            hung_stage=HUNG_STAGE_DONE_PULSE,
            start=1,
            slave_addr=0x50,
            rw=0,
            tx_data=0xA5,
            done=1,
            busy=0,
            ack_error=1,
        )
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"I2CHungTransaction construction failed: {exc}") from exc
    assert hung.hung is True
    assert hung.hung_stage == HUNG_STAGE_DONE_PULSE
    assert not hung.is_read
    assert "HUNG[stage=done-pulse]" in str(hung)
    print("i2c_monitor: event/hung class self-check OK")


if __name__ == "__main__":
    # Requires pyuvm (and therefore cocotb, which pyuvm imports) on the
    # PYTHONPATH; the cocotb-import guard above keeps this module importable
    # in a cocotb-less direct-run context up to this point.
    _self_test_publish_classes()