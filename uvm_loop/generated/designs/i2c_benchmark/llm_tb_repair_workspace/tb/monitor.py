"""Stage 3 (observation) artifact of the CHIA generator: the pyuvm monitor.

``I2CMonitor`` is the passive observer of the i2c_master DUT.  It samples
the DUT pins (exclusively through the ConfigDB-shared ``I2CDutPins``
helper from ``tb/dut_helper.py``) and publishes complete
:class:`~tb.transaction.I2CTransaction` items through a
``uvm_analysis_port`` so later stages (scoreboard / environment) can
subscribe without touching the pins themselves.

How a transaction is reconstructed (CONTRACT.md section 6):

* **Transaction start (stimulus capture).**  The monitor waits for the DUT
  to accept a request (``start == 1`` while ``busy == 0`` -- ``start`` is
  sampled only while idle, CONTRACT.md section 6) and captures the four
  stimulus inputs at that request-latching point, exactly where the RTL FSM
  latches ``rw``/``slave_addr``/``reg_addr``/``write_data``:

    ```
    IDLE + start=1  --RisingEdge-->  START_PHASE (fields latched; busy rises one cycle later)
    ```

  Two clock-edge sampling points are used so that the offer is captured
  deterministically no matter which clock phase the driver happens to drive
  in:

  1. **Falling-edge probe.**  The driver holds ``start=1`` plus all fields
     stable for the whole offer cycle.  If the driver drove in the *high*
     phase of the clock, the mid-cycle falling edge still observes
     ``start==1`` with ``busy==0`` and the stimulus is captured there.
  2. **Rising-edge request-latch probe.**  If the driver drove in the
     *low* phase (immediately before the latching edge), the offer is only
     visible at the latching rising edge itself.  At that edge cocotb
     resumes the monitor's standing ``RisingEdge`` wait *before* the
     driver's ``release_inputs()`` (the monitor keeps a permanently
     registered edge wait, while the driver only registers its latching
     edge wait right after driving), so the stimulus pins still carry the
     values the DUT just latched when the monitor samples them.

  The DUT asserts ``busy`` one clock cycle *after* the request-latching
  edge, so by the time a ``0 -> 1`` busy transition is observed the driver
  has already deasserted ``start`` and released the stimulus pins; a
  capture at that edge would fabricate an all-zero stimulus.  A guarded
  busy-rise fallback is kept purely as a safety net and never publishes a
  fabricated all-zero item (see ``_wait_transaction_start``).

* **Transaction end (output sampling).**  The monitor waits for the single
  cycle ``done`` pulse and samples ``read_data``, ``busy``, ``done`` and
  ``ack_error`` while ``dut.done == 1`` -- the exact sampling rule of
  CONTRACT.md section 6.  ``sample_outputs()`` / ``sample_into_item`` of
  the pin helper are reused verbatim.

* **Reset aborts.**  The randomized stimulus injects *reset during
  transaction* (plan ``randomized_testing_strategy``).  When that happens a
  ``done`` pulse never arrives (the async reset clears the FSM to IDLE).
  The monitor detects the abort (``rst_n == 0``, or ``busy`` falling to 0
  without ``done``) and **drops** the transaction instead of hanging or
  publishing a phantom completion.  Later stages (scoreboard) must not
  expect a one-to-one monitor item <-> sequence item when reset injection
  is enabled.

Design notes:

* The monitor is observation-only: it never drives pins and never fails
  the test by itself.  A hung transaction is reported as a logged error
  after a bounded cycle count; the always-running watchdog (environment
  stage) is what actually fails a hung test.
* Per CONTRACT.md section 8, ``start`` asserted while ``busy`` is *not*
  flagged as an error here (stimulus is gated by the driver; the busy-time
  ``start`` poke of scenario I2C_10 is expected behaviour).
"""

from cocotb.triggers import FallingEdge, RisingEdge
from pyuvm import uvm_analysis_port, uvm_monitor, ConfigDB

from tb.dut_helper import (
    KEY_CLK_RST,
    KEY_DUT_PINS,
    W_REG_ADDR,
    W_SLAVE_ADDR,
    W_WRITE_DATA,
    _to_int,
)
from tb.transaction import I2CTransaction

__all__ = ["I2CMonitor"]

# Field groups are authoritative (CONTRACT.md section 4).
STIMULUS_FIELDS = ("start", "rw", "slave_addr", "reg_addr", "write_data")
OUTPUT_FIELDS = ("read_data", "busy", "done", "ack_error")


class I2CMonitor(uvm_monitor):
    """Passive transaction monitor for the i2c_master DUT.

    Publishes :class:`~tb.transaction.I2CTransaction` items on
    ``self.analysis_port`` with:

    * stimulus fields captured when the DUT accepts the request,
    * observed-output fields sampled while ``dut.done == 1``.
    """

    def __init__(self, name="i2c_monitor", parent=None):
        super().__init__(name, parent)
        self.pins = None
        self.clkrs = None
        #: Number of clock cycles allowed between the request-latch and the
        #: ``done`` pulse before the monitor gives up on the transaction
        #: (same bound the stimulus sequences use).
        self.done_timeout_cycles = 512

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        super().build_phase()
        self.pins = ConfigDB().get(self, "", KEY_DUT_PINS)
        self.clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
        #: Analysis port for observed items (CONTRACT.md stage-3 addition).
        self.analysis_port = uvm_analysis_port("analysis_port", self)

    async def run_phase(self):
        """Continuously reconstruct and publish observed transactions."""
        while True:
            stimulus = await self._wait_transaction_start()
            outputs = await self._wait_done_pulse()
            if outputs is None:
                # Transaction aborted by a reset injection: nothing to
                # publish (a done pulse never arrives).
                self.logger.debug(
                    "%s: dropping in-flight transaction (reset abort)",
                    self.get_name())
                continue
            self._publish(stimulus, outputs)

    # ------------------------------------------------------------------
    # Observation internals
    # ------------------------------------------------------------------
    async def _wait_transaction_start(self):
        """Wait until the DUT accepts the next request.

        Returns the stimulus dict captured at the request-latch point.
        Runs until an offer is found (idle is a permanent valid state, so
        there is no bounded timeout here; a hung DUT is caught by the
        watchdog, not by this observer).
        """
        pins = self.pins
        prev_busy = _to_int(pins.busy.value, 1)
        while True:
            # Mid-cycle probe: covers offers driven in the high clock phase.
            await FallingEdge(pins.clk)
            if (_to_int(pins.start.value, 1) == 1
                    and _to_int(pins.busy.value, 1) == 0):
                self.logger.debug(
                    "%s: offer captured at falling-edge probe", self.get_name())
                return self._sample_stimulus()

            # Request-latching edge: covers offers driven in the low clock
            # phase.  The DUT latches the request on this rising edge while
            # still idle (start==1, busy==0).  cocotb resumes this standing
            # RisingEdge wait before the driver releases the inputs, so the
            # stimulus pins still carry the values the DUT just latched.
            await RisingEdge(pins.clk)
            if (_to_int(pins.start.value, 1) == 1
                    and _to_int(pins.busy.value, 1) == 0):
                self.logger.debug(
                    "%s: offer captured at request-latch rising edge",
                    self.get_name())
                return self._sample_stimulus()

            # Busy-transition fallback (safety net).  The DUT asserts busy
            # one clock cycle after the request-latching edge, so by the
            # time a 0->1 busy transition is observed here the driver has
            # already deasserted start and released the stimulus pins;
            # sampling at this edge would fabricate an all-zero stimulus.
            # Publish only when the captured stimulus is still a genuine
            # (start==1) offer; otherwise keep scanning for the next valid
            # offer instead of publishing a fabricated all-zero item.
            busy = _to_int(pins.busy.value, 1)
            if busy == 1 and prev_busy == 0:
                stimulus = self._sample_stimulus()
                if stimulus["start"] == 1:
                    self.logger.debug(
                        "%s: offer captured at busy-rise fallback",
                        self.get_name())
                    return stimulus
                self.logger.debug(
                    "%s: busy rose without a visible offer; skipping the "
                    "fabricated all-zero stimulus capture",
                    self.get_name())
            prev_busy = busy

    async def _wait_done_pulse(self):
        """Wait for the completion pulse and sample the outputs.

        Returns the ``sample_outputs()`` dict when ``done == 1``, ``None``
        when the transaction was aborted by a reset before completion.
        """
        pins = self.pins
        for _ in range(self.done_timeout_cycles):
            await RisingEdge(pins.clk)
            if _to_int(pins.done.value, 1) == 1:
                return pins.sample_outputs()
            # Async reset, or a fall to idle without a done pulse: the
            # in-flight transaction is gone.
            if (_to_int(pins.rst_n.value, 1) == 0
                    or _to_int(pins.busy.value, 1) == 0):
                return None
        self.logger.error(
            "%s: no done pulse within %d cycles after request latch "
            "(transaction suggests a hung FSM)",
            self.get_name(), self.done_timeout_cycles)
        return None

    # ------------------------------------------------------------------
    # Building / publishing
    # ------------------------------------------------------------------
    def _sample_stimulus(self):
        """Sample the four stimulus input pins plus ``start``."""
        pins = self.pins
        return {
            "start": _to_int(pins.start.value, 1),
            "rw": _to_int(pins.rw.value, 1),
            "slave_addr": _to_int(pins.slave_addr.value, W_SLAVE_ADDR),
            "reg_addr": _to_int(pins.reg_addr.value, W_REG_ADDR),
            "write_data": _to_int(pins.write_data.value, W_WRITE_DATA),
        }

    def _publish(self, stimulus, outputs):
        """Build an :class:`I2CTransaction` and write it to the analysis
        port.  Fields map 1:1 to CONTRACT.md section 4."""
        item = I2CTransaction(f"{self.get_name()}_mon")
        for field in STIMULUS_FIELDS:
            setattr(item, field, int(stimulus[field]))
        for field in OUTPUT_FIELDS:
            setattr(item, field, int(outputs[field]))
        item.check_inputs_valid()
        self.analysis_port.write(item)
        self.logger.debug("%s: published %s", self.get_name(), item)
        return item