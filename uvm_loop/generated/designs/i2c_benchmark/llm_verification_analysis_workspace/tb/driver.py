"""Stage 2 (stimulus) artifact of the CHIA generator: the pyuvm driver.

``I2CDriver`` is the only component that offers transaction requests on the
DUT stimulus pins in normal operation.  It pulls ``I2CTransaction`` items
from the ``I2CSequencer`` (through the standard ``seq_item_port``), waits
for the DUT to report idle (``busy == 0``), and then holds ``start = 1``
together with all transaction fields stable for a single clock cycle so the
RTL FSM latches the request on the next rising edge (CONTRACT.md section
6)::

    IDLE + start==1  --(RisingEdge)-->  START_PHASE (busy rises, fields latched)

After the latching edge the driver deasserts ``start`` and returns the
stimulus pins to decorrelated defaults, then calls ``item_done()``.

The driver deliberately does **not** wait for ``done``:

* Completion is observed by the monitor (later stage) and/or by the
  sequences themselves, keeping this component decoupled from completion
  timing.
* It makes the driver immune to the randomized "reset during transaction"
  injection (plan ``randomized_testing_strategy``): a mid-flight reset
  aborts the in-flight transaction (no ``done`` pulse ever arrives), yet the
  driver can never hang because it has already handed the item back.

Stimulus gating: while the DUT is busy, ``start`` must not be asserted by
the normal stimulus path (``start`` is only sampled while idle);
``_wait_until_idle`` enforces that here in the driver.  The sole exception
is the documented "start while busy" scenario (I2C_10 and its corner
counterpart), which pokes ``start`` directly from the sequence while the
driver is parked on ``get_next_item`` -- see ``tb/sequences.py``.
"""

import cocotb
from cocotb.triggers import RisingEdge
from pyuvm import uvm_driver, ConfigDB

from tb.dut_helper import KEY_DUT_PINS, KEY_CLK_RST, _to_int

__all__ = ["I2CDriver"]


class I2CDriver(uvm_driver):
    """Drives an :class:`~tb.transaction.I2CTransaction` on the DUT pins.

    Pin access goes exclusively through the ConfigDB-shared ``I2CDutPins``
    helper (keys from ``tb/dut_helper.py`` / CONTRACT.md section 5).  The
    item fields map 1:1 to the stimulus pins (CONTRACT.md section 4) and
    are validated with ``I2CTransaction.check_inputs_valid()`` before
    driving.
    """

    def __init__(self, name="i2c_driver", parent=None):
        super().__init__(name, parent)
        self.pins = None
        self.clkrs = None

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        self.pins = ConfigDB().get(self, "", KEY_DUT_PINS)
        self.clkrs = ConfigDB().get(self, "", KEY_CLK_RST)

    async def run_phase(self):
        """Continuous: get an item -> offer it on the DUT -> item_done."""
        while True:
            req = await self.seq_item_port.get_next_item()
            # Validate before touching any pin so a malformed item fails
            # fast (raising is caught by pyuvm and fails the test).
            req.check_inputs_valid()
            await self._offer(req)
            self.seq_item_port.item_done()

    # ------------------------------------------------------------------
    # Driving
    # ------------------------------------------------------------------
    async def _offer(self, item):
        """Present ``item`` to the DUT for exactly one idle cycle.

        Returns once the request has been latched (after the latching
        RisingEdge) and the pins have been released; the transaction is
        then in flight until the ``done`` pulse.
        """
        await self._wait_until_idle()
        # drive_transaction() writes start=1 plus rw/slave_addr/reg_addr/
        # write_data from the item (masked to the port widths).
        self.pins.drive_transaction(item)
        # The FSM samples `start` on this next rising edge while in IDLE.
        await RisingEdge(self.pins.clk)
        # Request latched; return inputs to idle defaults.
        self.pins.release_inputs()

    async def _wait_until_idle(self):
        """Wait until the DUT reports idle (``busy == 0``).

        ``busy`` is high from the latching edge to the ``done`` cycle, so a
        transaction is only offered when the previous one has finished
        (serializing driver requests; back-to-back offers latch on the
        edge immediately following the previous ``done``, which the RTL
        accepts -- CONTRACT.md section 6).
        """
        while _to_int(self.pins.busy.value, 1) != 0:
            await RisingEdge(self.pins.clk)