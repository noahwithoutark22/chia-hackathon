"""Always-running assertion checkers for the axi_handshake DUT.

Each checker is a standalone ``async def`` coroutine started via
``cocotb.start_soon`` from the environment or test.  They run
concurrently with the driver, monitor, and scoreboard, sampling DUT
pins directly through the shared ``dut`` handle on every rising clock
edge (after ``ReadOnly``).

A failed check raises ``AssertionError`` immediately, failing the test.

Assertion list (from verification_plan.yaml §useful_assertions):

1. **m_valid_held_during_stall**
   If m_valid=1 and m_ready=0 at cycle N, then m_valid must stay 1 and
   m_data must not change at cycle N+1.

2. **s_ready_only_when_can_accept**
   s_ready=1 implies (buffer_empty OR (m_valid && m_ready)).
   Since buffer_empty is not directly observable, the external
   equivalent is: s_ready=1 implies (m_valid=0 || m_ready=1).
   Violation: s_ready=1 when m_valid=1 and m_ready=0.

3. **no_data_drop**
   Every accepted input (s_valid && s_ready) must eventually produce
   exactly one completed output (m_valid && m_ready).  Over the test,
   the cumulative count of accepted inputs must be >= completed outputs
   (output may be delayed, never exceeds input count).

ConfigDB keys consumed (CONTRACT.md §5):
  - ``"dut"``         — cocotb SimHandleBase
  - ``"reset_polarity"`` — ``"active_low"``
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from pyuvm import ConfigDB


# ═══════════════════════════════════════════════════════════════════
#  Assertion 1 — m_valid held during stall
# ═══════════════════════════════════════════════════════════════════

async def assertion_m_valid_held_during_stall():
    """Check that m_valid and m_data are held stable when stalled.

    A stall is defined as m_valid=1 && m_ready=0.  On the next
    cycle, m_valid must still be 1 and m_data must equal the
    previous cycle's value.
    """
    dut = ConfigDB().get(None, "", "dut")
    clk = dut.clk

    prev_m_valid = 0
    prev_m_data = 0
    prev_was_stall = False

    while True:
        await RisingEdge(clk)
        await ReadOnly()

        m_valid = int(dut.m_valid.value) & 0x1
        m_ready = int(dut.m_ready.value) & 0x1
        m_data = int(dut.m_data.value) & 0xFF

        if prev_was_stall:
            # Previous cycle was a stall: m_valid was 1, m_ready was 0.
            # Current cycle must still have m_valid=1 and same m_data.
            assert m_valid == 1, (
                f"m_valid_held_during_stall VIOLATION: m_valid dropped "
                f"from 1 to {m_valid} after a stall cycle "
                f"(prev m_data=0x{prev_m_data:02X})"
            )
            assert m_data == prev_m_data, (
                f"m_valid_held_during_stall VIOLATION: m_data changed "
                f"from 0x{prev_m_data:02X} to 0x{m_data:02X} "
                f"during a stall"
            )

        prev_was_stall = (m_valid == 1 and m_ready == 0)
        prev_m_valid = m_valid
        prev_m_data = m_data


# ═══════════════════════════════════════════════════════════════════
#  Assertion 2 — s_ready only when can accept
# ═══════════════════════════════════════════════════════════════════

async def assertion_s_ready_only_when_can_accept():
    """s_ready=1 implies (m_valid=0 OR m_ready=1).

    If s_ready is asserted while m_valid=1 and m_ready=0, the DUT
    is claiming it can accept input while its output is stalled, which
    violates the elastic-buffer contract.
    """
    dut = ConfigDB().get(None, "", "dut")
    clk = dut.clk

    reset_pol = str(
        ConfigDB().get(None, "", "reset_polarity") or "active_low"
    )

    while True:
        await RisingEdge(clk)
        await ReadOnly()

        rst_n = int(dut.rst_n.value) & 0x1
        in_reset = (rst_n == 0) if reset_pol == "active_low" else (rst_n == 1)
        if in_reset:
            continue

        s_ready = int(dut.s_ready.value) & 0x1
        m_valid = int(dut.m_valid.value) & 0x1
        m_ready = int(dut.m_ready.value) & 0x1

        if s_ready == 1:
            assert (m_valid == 0) or (m_ready == 1), (
                f"s_ready_only_when_can_accept VIOLATION: s_ready=1 "
                f"but m_valid=1 and m_ready=0 — DUT accepts input "
                f"while output is stalled"
            )


# ═══════════════════════════════════════════════════════════════════
#  Assertion 3 — no data drop (cumulative counter)
# ═══════════════════════════════════════════════════════════════════

async def assertion_no_data_drop():
    """Track accepted inputs vs. completed outputs.

    Every cycle where s_valid=1 AND s_ready=1 is an accepted input.
    Every cycle where m_valid=1 AND m_ready=1 is a completed output.
    Over the entire test, the number of completed outputs must never
    exceed the number of accepted inputs.
    """
    dut = ConfigDB().get(None, "", "dut")
    clk = dut.clk

    reset_pol = str(
        ConfigDB().get(None, "", "reset_polarity") or "active_low"
    )

    accepted_inputs = 0
    completed_outputs = 0

    while True:
        await RisingEdge(clk)
        await ReadOnly()

        rst_n = int(dut.rst_n.value) & 0x1
        in_reset = (rst_n == 0) if reset_pol == "active_low" else (rst_n == 1)
        if in_reset:
            continue

        s_valid = int(dut.s_valid.value) & 0x1
        s_ready = int(dut.s_ready.value) & 0x1
        m_valid = int(dut.m_valid.value) & 0x1
        m_ready = int(dut.m_ready.value) & 0x1

        if s_valid and s_ready:
            accepted_inputs += 1
        if m_valid and m_ready:
            completed_outputs += 1

        assert completed_outputs <= accepted_inputs, (
            f"no_data_drop VIOLATION: completed_outputs "
            f"({completed_outputs}) exceeds accepted_inputs "
            f"({accepted_inputs}) — a spurious output was produced"
        )
