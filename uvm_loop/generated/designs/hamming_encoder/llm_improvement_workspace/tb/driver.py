"""hamming_encoder stimulus driver (stage 2: STIMULUS).

``HammingDriver`` is the only component that offers transaction requests on
the DUT stimulus pins.  It pulls :class:`~tb.transaction.HammingTransaction`
items from :class:`~tb.sequencer.HammingSequencer` (through the standard
``seq_item_port``) and applies each item's ``data_in`` onto ``dut.data_in``
using the ConfigDB-shared :class:`~tb.dut_helper.HammingDutPins` helper.

The DUT is purely combinational (CONTRACT.md section 2):  ``code_out`` is a
pure function of the current ``data_in`` with latency 0, and the DUT has
**no** ``clk`` and **no** reset port.  The testbench reference clock ``clk``
and the environment reset ``tb_reset`` are virtual signals described by the
ConfigDB-shared :class:`~tb.dut_helper.ClockReset`; a reference *cycle* is
one ``Timer(clock_period_ns)`` wait (``wait_clock_cycles``).  The driver
therefore never uses ``RisingEdge(dut.clk)`` / ``ClockCycles``.

Per-item timing (CONTRACT.md section 8), for one encode operation:

    1. ``get_next_item()``         -- block until a sequence hands over an
                                       item (via ``finish_item``),
    2. ``wait_clock_cycles(1)``     -- reach the next virtual cycle boundary
                                       (the "posedge" of the virtual clk),
    3. ``pins.drive_data_in(...)``  -- apply ``item.data_in`` on the pin,
    4. ``wait_clock_cycles(1)``     -- one full reference cycle: the
                                       combinational ``code_out`` settles
                                       (latency 0) and the monitor/sequence
                                       sample it (one-cycle sampling latency
                                       relative to the drive),
    5. ``item_done()``              -- release the sequence's ``finish_item``
                                       (when it returns, ``code_out`` is
                                       settled and safe to sample),
    6. ``pins.note_drive()``        -- record the completed drive on the
                                       shared ``HammingDutPins.drive_count``
                                       counter (the monitor publishes one
                                       transaction per counter increment).

So each transaction occupies exactly two reference cycles
(one pre-drive alignment + one post-drive settle).  Back-to-back
transactions run back-to-back at this fixed cadence; the DUT never stalls
and there is no handshake, exactly as the plan requires.
"""

from pyuvm import ConfigDB, uvm_driver

from tb.dut_helper import (
    KEY_CLK_RST,
    KEY_CONF,
    KEY_DUT_PINS,
    wait_clock_cycles,
)

__all__ = ["HammingDriver"]


class HammingDriver(uvm_driver):
    """Drives one :class:`~tb.transaction.HammingTransaction` per encode.

    Pin access goes exclusively through the ConfigDB-shared
    ``HammingDutPins`` helper (keys from ``tb/dut_helper.py`` /
    CONTRACT.md section 6).  The item's ``data_in`` maps 1:1 to the
    ``dut.data_in`` input port and is masked to ``item.data_width`` bits.

    The driver deliberately does **not** sample ``code_out``: the monitor
    (later stage) owns output observation and fills ``item.code_out`` after
    the settle window.  The fixed 2-cycle cadence is the reference the
    monitor uses to align its one-cycle sampling latency.
    """

    def __init__(self, name="hamming_driver", parent=None):
        super().__init__(name, parent)
        self.pins = None   # HammingDutPins (ConfigDB KEY_DUT_PINS)
        self.clkrs = None  # ClockReset     (ConfigDB KEY_CLK_RST)
        self.conf = None   # HammingConf    (ConfigDB KEY_CONF)

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        """Resolve the shared DUT config (CONTRACT.md section 6, exact keys)."""
        super().build_phase()
        self.pins = ConfigDB().get(self, "", KEY_DUT_PINS)
        self.clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
        self.conf = ConfigDB().get(self, "", KEY_CONF)

    async def run_phase(self):
        """Continuous: get an item -> drive it -> item_done."""
        while True:
            item = await self.seq_item_port.get_next_item()
            if item is None:  # defensive: some pyuvm versions signal end
                break
            # Validate before touching any pin so a malformed item fails
            # fast (raising is caught by pyuvm and fails the test).
            item.check_inputs_valid()

            # 2. Align to the next virtual cycle boundary.
            await wait_clock_cycles(self.clkrs, 1)

            # 3. Drive the data word (masked to the elaboration width).
            self.pins.drive_data_in(item.data_in, data_width=item.data_width)

            # 4. Combinational settle window + monitor sampling window.
            await wait_clock_cycles(self.clkrs, 1)

            # 5. Release the sequence; `finish_item` now returns with
            #    code_out settled (CONTRACT.md section 8).
            self.seq_item_port.item_done()
            # 6. Record the completed drive exactly once per item_done on
            #    the shared pins helper.  The monitor publishes one
            #    transaction per drive_count increment, so this is the event
            #    source that separates genuine transactions from the primed
            #    idle pair and prevents identical re-drives from coalescing
            #    (monitor.py).
            self.pins.note_drive()
            self.logger.debug(
                "drove data_in=%#x (DATA_WIDTH=%d SECDED=%d)",
                item.data_in, item.data_width, item.secded,
            )