"""PyUVM monitor for the parameterized adder DUT.

The monitor passively samples the DUT's pins every clock cycle and
publishes the resulting ``AdderTransaction`` items through a
``uvm_analysis_port`` (``self.ap``) so downstream components (scoreboard,
coverage collectors) can observe the DUT's actual behavior.

Timing / correlation (per CONTRACT.md Sections 3, 4 and 8):
  - The DUT registers ``{cout, sum} <= a + b + cin`` on every ``posedge
    clk`` while ``rst_n`` is high, so the outputs present at a given
    rising edge reflect the inputs that were presented *during the
    previous* cycle (1-cycle registered latency).
  - The driver presents new data inputs right *after* a ``posedge clk``
    and holds them stable for the following cycle.

To associate the observed registered outputs with the inputs that
produced them (CONTRACT Section 10.1), the monitor captures the *settled*
inputs once per cycle at the ``FallingEdge`` of the clock (mid-cycle,
guaranteed stable because the driver only ever updates inputs in the
rising-edge region) and pairs them with the outputs observed at the next
``ReadOnly`` region after the following rising edge:

    1. On ``FallingEdge(clk)`` sample the current (settled) inputs and
       remember them as "the inputs the DUT will register at the next
       posedge".
    2. On the next ``RisingEdge(clk)`` sample the registered outputs in
       the ``ReadOnly`` region and pair them with those remembered inputs.

This is deterministic regardless of the relative scheduling of the driver
and monitor tasks at the rising edge (the driver updates inputs in the
rising-edge region; the falling-edge sampling point is half a period
later, so it always observes the cycle's held inputs).

Each pair is published as a transaction that carries exactly the
CONTRACT-defined fields (``a``, ``b``, ``cin``) for the applied inputs and
stores the observed DUT outputs into ``exp_sum`` / ``exp_cout`` (the
transaction's only output-capable fields).  A later-stage scoreboard
(re)computes ``adder_ref`` expectations and compares against these
observed values.
"""

from __future__ import annotations

from pyuvm import uvm_monitor, ConfigDB, uvm_analysis_port
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly

from adder_transaction import AdderTransaction
from dut_helper import DUTHelper


class AdderMonitor(uvm_monitor):
    """Passively sample the adder DUT pins and publish transactions.

    Parameters
    ----------
    name : str
        Instance name (default ``"adder_monitor"``).
    parent : uvm_component
        Parent component, normally the agent.
    """

    def __init__(self, name="adder_monitor", parent=None):
        super().__init__(name, parent)
        # Analysis port: every observed transaction is written here.
        self.ap = uvm_analysis_port("ap", self)

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------

    def build_phase(self):
        """Retrieve the shared DUT accessor / config from the ConfigDB."""
        super().build_phase()
        # ConfigDB accessors per CONTRACT.md Section 6 (keys set by tb_top).
        self.dut = ConfigDB.get(None, "", "dut")
        self.helper: DUTHelper = ConfigDB.get(None, "", "dut_helper")
        self.width = ConfigDB.get(None, "", "width")
        self.clock_name = ConfigDB.get(None, "", "clock_name")
        self.reset_name = ConfigDB.get(None, "", "reset_name")
        self.reset_active_low = ConfigDB.get(None, "", "reset_active_low")

    # ------------------------------------------------------------------
    # Value helpers
    # ------------------------------------------------------------------

    def _read_rst_high(self) -> bool:
        """Return ``True`` if the reset signal is currently de-asserted (high).

        The reset polarity is read from the ConfigDB (``reset_active_low``);
        for this adder it is active-low, so a high ``rst_n`` means the DUT is
        out of reset.  Handles the value robustly (never raises on X/Z — an
        unknown reset is treated as *not* out-of-reset).
        """
        pol = self.reset_active_low  # True => active-low
        as_str = str(self.helper._rst_n.value)
        if any(ch in as_str for ch in "XZxz"):
            return False
        val = int(self.helper._rst_n.value)
        # Active-low: de-asserted (high) => value 1.  Active-high: value 0.
        return bool(val) if pol else not bool(val)

    # ------------------------------------------------------------------
    # Monitor main loop
    # ------------------------------------------------------------------

    async def run_phase(self) -> None:
        """Continuously sample DUT pins and publish observed transactions.

        The loop runs for the entire simulation.  Correlation is made
        deterministic by sampling the settled cycle inputs on the falling
        edge and the registered outputs on the next rising edge's
        read-only region (see module docstring / CONTRACT Section 10.1).
        """
        clk = self.helper._clk

        while True:
            # 1. Mid-cycle: capture the inputs that the DUT will register at
            #    the next posedge.  These are guaranteed stable because the
            #    driver only updates inputs in the rising-edge region.
            await FallingEdge(clk)
            a = int(self.helper._a.value)
            b = int(self.helper._b.value)
            cin = int(self.helper._cin.value)

            # 2. Next posedge: read the registered outputs (which reflect
            #    exactly the inputs captured in step 1, due to the DUT's
            #    1-cycle latency).
            await RisingEdge(clk)
            await ReadOnly()

            # If reset is asserted at this edge, the DUT's outputs are forced
            # to zero by the async reset (CONTRACT Section 2), NOT by the
            # addition — so this is not an arithmetic transaction the
            # scoreboard can validate against adder_ref.  The reset-clearing
            # behavior itself is verified by the assertion checkers, so we
            # simply do not publish here.
            if not self._read_rst_high():
                continue

            sum_val, cout_val = await self.helper.sample_outputs()

            tr = AdderTransaction()
            tr.a = a
            tr.b = b
            tr.cin = cin
            # Store the observed DUT outputs in the transaction's output
            # fields (contract defines no separate "observed" fields).
            tr.exp_sum = sum_val
            tr.exp_cout = cout_val

            self.logger.info(
                "Observe a=0x%0*X b=0x%0*X cin=%d -> sum=0x%0*X cout=%d",
                (self.width + 3) // 4, a,
                (self.width + 3) // 4, b,
                cin,
                (self.width + 3) // 4, sum_val,
                cout_val,
            )

            # Broadcast to any connected analysis-export subscribers
            # (scoreboard, coverage, etc.).
            self.ap.write(tr)
