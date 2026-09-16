"""hamming_encoder passive pyuvm monitor (stage 3: OBSERVATION).

``HammingMonitor`` observes the two DUT pins -- ``data_in`` (input) and
``code_out`` (output); there are **no** other pins (CONTRACT.md section 2) --
and publishes one :class:`~tb.transaction.HammingTransaction` per driven
encode operation through its ``uvm_analysis_port`` (``ap``).  Exactly the
fields of CONTRACT.md section 5 are filled::

    data_in     int, DATA_WIDTH bits  sampled from the ``data_in`` pin
    code_out    int, CODE_WIDTH bits  sampled from the ``code_out`` pin
    data_width / secded / code_width  from the active ``HammingConf``

== Sampling cadence (virtual reference clock) ==
The DUT is purely combinational and has **no** ``clk`` / reset pins
(CONTRACT.md section 3): ``dut.clk`` and ``dut.tb_reset`` do not exist and
are never referenced here.  A reference *cycle* is one
``Timer(clkrs.clock_period_ns)`` wait (``wait_clock_cycles``); its expiry is
the virtual "posedge" at which stimulus is applied and, after the
combinational settle, outputs are sampled.  The monitor therefore paces
itself with ``await wait_clock_cycles(self.clkrs, 1)`` -- never
``RisingEdge(dut.clk)`` / ``ClockCycles``.

== Phasing to the driver (per-drive publication) ==
The stage-2 driver (CONTRACT.md section 8) performs one encode operation
every two virtual cycles: align (1 cycle) -> drive ``data_in`` -> settle
(1 cycle) -> ``item_done``, and after each ``item_done`` it records the
completed drive on the shared ``HammingDutPins.drive_count`` counter
(exactly once per item, driver.py).  The monitor samples both pins at
**every** virtual cycle boundary and applies one rule:

* *Event source = the drive counter.*  A publish happens only when
  ``pins.drive_count`` has advanced since the previous sample.  Because the
  driver increments the counter only for completed drives, the pre-stimulus
  primed ``(data_in=0, code_out=0)`` idle pair -- which is X/Z-free from
  time 0 and therefore X/Z-free at the first sample -- is never mistaken
  for a real transaction: skipped/no-stimulus scenarios publish **0 items**
  instead of a phantom ``'1 item checked, 1 passed'``.
* *Payload = the settle-boundary pair.*  The captured ``(data_in,
  code_out)`` pair is the one held on the pins when the increment is
  observed.  The DUT is purely combinational, so a newly settled pair stays
  on the pins until the next drive boundary; even when the increment is
  observed one reference cycle after its settle boundary the captured pair
  is still the correct one (the monitor's per-boundary sample precedes that
  boundary's drive, so it never reads the *next* item's pair).
* *No coalescing.*  Back-to-back drives of the *identical* data word each
  advance the counter and each publish one item, so the passive
  scoreboard re-checks every driven vector (plan criterion) and coverage
  samples per drive (CONTRACT.md section 8).

Every published ``code_out`` goes through
``HammingDutPins.sample_into_item`` / ``sample_code_out_strict``, so X/Z on
the output after settle raises :class:`AssertionError` and fails the test
immediately (plan pass criterion "no X/Z values on code_out after settle");
``data_in`` is sampled strictly as well so an undriven or 4-state input can
never be silently coerced to 0.

ConfigDB keys consumed (CONTRACT.md section 6, exact keys and value types):

    KEY_DUT_PINS   HammingDutPins  -- canonical pin access
    KEY_CLK_RST    ClockReset      -- virtual clock/reset descriptor
    KEY_CONF       HammingConf     -- active DATA_WIDTH/SECDED geometry

The monitor is passive: it raises no objections, so the UVM test controls
the run duration; pyuvm/cocotb terminate the ``run_phase`` loop when the
test's objections drop.
"""

from pyuvm import ConfigDB, uvm_analysis_port, uvm_monitor

from tb.dut_helper import (
    KEY_CLK_RST,
    KEY_CONF,
    KEY_DUT_PINS,
    wait_clock_cycles,
)
from tb.transaction import HammingTransaction

__all__ = ["HammingMonitor"]


class HammingMonitor(uvm_monitor):
    """Passive observer of the hamming_encoder DUT pins.

    Attributes
    ----------
    ap : uvm_analysis_port
        Publishes one ``HammingTransaction`` per settled encode operation.
    pins : HammingDutPins | None
        ConfigDB-shared pin helper, resolved in :meth:`build_phase`.
    clkrs : ClockReset | None
        ConfigDB-shared virtual clock/reset descriptor.
    conf : HammingConf | None
        ConfigDB-shared elaboration geometry.
    num_items : int
        Number of transactions published so far (diagnostics / reporting).
    """

    def __init__(self, name="hamming_monitor", parent=None):
        super().__init__(name, parent)
        self.ap = uvm_analysis_port("ap", self)
        self.pins = None
        self.clkrs = None
        self.conf = None
        self.num_items = 0

    # ------------------------------------------------------------------
    # build_phase: resolve the shared DUT config (CONTRACT.md section 6)
    # ------------------------------------------------------------------
    def build_phase(self):
        """Resolve the ConfigDB-shared DUT objects using the exact keys."""
        super().build_phase()
        self.pins = ConfigDB().get(self, "", KEY_DUT_PINS)
        self.clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
        self.conf = ConfigDB().get(self, "", KEY_CONF)
        if None in (self.pins, self.clkrs, self.conf):
            raise RuntimeError(
                f"{self.get_name()}: missing ConfigDB entries "
                f"(KEY_DUT_PINS={self.pins is not None}, "
                f"KEY_CLK_RST={self.clkrs is not None}, "
                f"KEY_CONF={self.conf is not None}) -- tb_top must share "
                "them before the environment is built")

    # ------------------------------------------------------------------
    # run_phase: per-cycle pin sampling + settle-boundary publishing
    # ------------------------------------------------------------------
    async def run_phase(self):
        """Sample the DUT pins on every virtual cycle boundary and publish
        exactly one item per completed drive.

        Publishing is driven by the shared ``HammingDutPins.drive_count``
        counter (incremented by the driver exactly once per ``item_done``),
        *not* by the sampled ``(data_in, code_out)`` pair changing::

            - the pre-stimulus primed (0, 0) idle pair is never a drive, so
              no phantom transaction is published before any stimulus;
            - back-to-back drives of the *identical* data word each record a
              counter increment and each publish an item, so the scoreboard
              re-checks every driven vector (no coalescing).

        At each boundary the monitor captures the settle-boundary pair that
        is still held on the pins (a newly settled pair stays on the pins
        until the next drive boundary).  ``drive_count`` therefore selects
        *when* to publish and the pins select *what* to publish.
        """
        last_count = self.pins.drive_count
        while True:
            # Virtual "posedge": one full reference-cycle wait.  There is no
            # dut.clk, so this Timer wait is the only clock synchronisation
            # the monitor may use (CONTRACT.md section 3).
            await wait_clock_cycles(self.clkrs, 1)

            current = self.pins.drive_count
            if current == last_count:
                # No drive completed since the previous boundary: nothing
                # new to publish.  This also suppresses the primed idle
                # (data_in=0, code_out=0) pair, which is not a drive.
                continue

            # Exactly one drive completes per two reference cycles (the
            # driver's fixed cadence) while this monitor samples every
            # cycle, so the per-boundary delta is at most 1.
            item = self._capture_item()
            self.ap.write(item)
            self.num_items += 1
            self.logger.debug(
                "%s published %s", self.get_name(), item)
            last_count = current

    # ------------------------------------------------------------------
    # Sampling helpers
    # ------------------------------------------------------------------
    def _capture_item(self):
        """Build a ``HammingTransaction`` carrying the current pin state.

        ``data_in`` is sampled strictly (an X/Z input after the first drive
        means the stimulus side is broken); ``code_out`` is sampled with
        ``sample_into_item`` (strict, X/Z after settle raises).  The item
        carries the active elaboration geometry so the scoreboard can call
        the reference model with the right ``data_width``/``secded``.
        """
        item = HammingTransaction(
            f"{self.get_name()}_tx{self.num_items}",
            data_width=self.conf.data_width,
            secded=self.conf.secded,
        )
        item.data_in = self.pins.sample_data_in_strict(
            data_width=item.data_width)
        # Fills item.code_out from the pin, raising on X/Z after settle.
        self.pins.sample_into_item(item)
        return item

    # ------------------------------------------------------------------
    # report_phase: per-run summary
    # ------------------------------------------------------------------
    def report_phase(self):
        """Report how many transactions were observed this run."""
        super().report_phase()
        self.logger.info(
            "%s: observed and published %d transaction(s)",
            self.get_name(), self.num_items)