"""AES-128 UVM driver (stage 6 integration; closes the stage-2 driver gap).

The :class:`AES128Driver` is the active (`UVM_ACTIVE`) stimulus arm of the
AES-128 testbench.  It pulls :class:`AES128Transaction` items from
:class:`tb.sequencer.AES128Sequencer` and offers them on the DUT pins in
exactly the timing the :class:`tb.monitor.AES128Monitor` expects
(``CONTRACT.md`` sections 4 and 7.5):

1. Wait until the DUT is idle *and* out of reset (``busy==0`` and
   ``rst_n==1`` sampled just after a clock edge).
2. Drive the offer: ``start=1`` together with ``key`` and ``plaintext``.
3. Hold the offer stable until one of three things happens:
   - ``busy`` rises (the DUT latched the input; edge-1 or edge-2 timing both
     handled because the monitor probes mid-cycle on the falling edge, and
     this driver merely has to keep the offer stable until acceptance),
   - ``rst_n`` falls (a reset aborts the offer; the item is abandoned and the
     DUT returns to idle), or
   - an acceptance-timeout elapses (bounded at ``OFFER_ACCEPT_MAX_CYCLES``;
     defensive guard, the DUT always accepts within 2 edges).
4. Release the ``start`` pulse.  ``key``/``plaintext`` are deliberately left
   at the offered values until the next offer so the monitor's busy-rise
   fallback probe never mis-captures a stale value.

The driver never touches ``rst_n`` (reset injection is the sequences' job).

NOTE ON CORRECTNESS (design-level): the target RTL ``aes128.sv`` is
intentionally buggy per verification-plan item ``DISC-001`` (the final-round
MixColumns guard ``if (round == 4'd10)`` can never fire because ``round``
tops out at 9 during ``ROUND_RUN``, so MixColumns runs in *all* rounds).
Scoreboard comparison (``tb/scoreboard.py``) is therefore expected to report
mismatches on every completed transaction; that failure is the intended bug
detection and is explicitly *not* papered over here (``CONTRACT.md``,
"Verification isolation").
"""

from pyuvm import ConfigDB, uvm_driver
from cocotb.triggers import RisingEdge

from tb.transaction import AES128Transaction

__all__ = ["AES128Driver"]


class AES128Driver(uvm_driver):
    """Offers :class:`AES128Transaction` items to the ``aes128`` DUT.

    Requires the ConfigDB entries mandated by ``CONTRACT.md`` section 7.3:
    ``"dut"`` (sim handle), ``"dut_helper"`` (shared
    :class:`tb.dut_helper.AES128DUTHelper`).
    """

    #: Bounded wait for the DUT to accept an offer (see step 3 above).
    OFFER_ACCEPT_MAX_CYCLES = 16

    def __init__(self, name="aes128_driver", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.helper = None

    def build_phase(self):
        super().build_phase()
        self.dut = ConfigDB().get(self, "", "dut")
        self.helper = ConfigDB().get(self, "", "dut_helper")
        if self.dut is None or self.helper is None:
            raise RuntimeError(
                f"{self.get_full_name()}: ConfigDB entries 'dut' and "
                f"'dut_helper' are required (CONTRACT.md section 7.3)"
            )
        self.logger.info(
            "%s: connected to DUT '%s' (%s)",
            self.get_full_name(),
            getattr(self.dut, "_name", "?"),
            type(self.helper).__name__,
        )

    async def run_phase(self):
        """Pull items from the sequencer and offer each one on the pins."""
        while True:
            req = await self.seq_item_port.get_next_item()
            await self._offer(req)
            self.seq_item_port.item_done()

    async def _offer(self, item: AES128Transaction):
        """Drive one transaction on the bus; never raises on DUT aborts."""
        self._validate_item(item)
        await self._wait_ready()
        if int(self.helper.rst_n) == 0:
            # Reset asserted while we were waiting: nothing can be offered.
            self.logger.warning(
                "%s: dropping offer for %s (reset asserted before offer)",
                self.get_full_name(),
                item.get_name(),
            )
            return

        # Step 2: drive the offer.
        self.helper.drive_command(
            int(item.start) if item.start is not None else 1,
            int(item.key) if item.key is not None else 0,
            int(item.plaintext) if item.plaintext is not None else 0,
        )

        # Step 3: hold the offer until acceptance, reset, or timeout.
        accepted = False
        for _ in range(self.OFFER_ACCEPT_MAX_CYCLES):
            await RisingEdge(self.dut.clk)
            if int(self.helper.rst_n) == 0:
                break
            if int(self.helper.busy) == 1:
                accepted = True
                break

        # Step 4: release the start pulse (key/plaintext remain stable until
        # the next offer; the monitor already captured the stimulus at the
        # acceptance latched-into-busy falling-edge probe).
        self.helper.start = 0

        if accepted:
            self.logger.debug(
                "%s: offered %s (start=1) - accepted",
                self.get_full_name(),
                item.get_name(),
            )
        else:
            self.logger.warning(
                "%s: offer for %s not accepted within %d cycles "
                "(reset abort?) - item abandoned",
                self.get_full_name(),
                item.get_name(),
                self.OFFER_ACCEPT_MAX_CYCLES,
            )

    async def _wait_ready(self):
        """Wait until the DUT is idle and out of reset."""
        while True:
            if (
                int(self.helper.rst_n) == 1
                and int(self.helper.busy) == 0
            ):
                return
            await RisingEdge(self.dut.clk)

    def _validate_item(self, item: AES128Transaction):
        """Range-check the item's input fields (CONTRACT.md section 3)."""
        if item.start not in (0, 1):
            raise ValueError(
                f"{self.get_full_name()}: item {item.get_name()} has "
                f"start={item.start!r} (must be 0 or 1)"
            )
        for field, value in (
            ("key", item.key),
            ("plaintext", item.plaintext),
        ):
            if value is None:
                continue
            if not (0 <= int(value) < (1 << 128)):
                raise ValueError(
                    f"{self.get_full_name()}: item {item.get_name()} "
                    f"{field}={value!r} out of the 128-bit range"
                )