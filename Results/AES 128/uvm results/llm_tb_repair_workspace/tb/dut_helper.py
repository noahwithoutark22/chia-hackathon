"""Aes128DutHelper: centralized direct pin access to the ``aes128`` DUT.

This is plain Python (NOT a SystemVerilog interface).  It wraps the
cocotb ``dut`` handle so that every DUT pin is accessed through exactly
one place, using the pin names and widths recorded in CONTRACT.md.

``dut`` itself is shared across components via ConfigDB under the key
``"dut"`` (see CONTRACT.md §4).  The helper is optional sugar; later
stages may drive ``dut.<pin>`` directly, but should prefer this module so
access conventions never drift.

Pins (direction / width / access):
    clk         input  / 1     -> dut.clk
    rst_n       input  / 1     -> dut.rst_n
    start       input  / 1     -> dut.start
    key         input  / 128   -> dut.key
    plaintext   input  / 128   -> dut.plaintext
    done        output / 1     -> dut.done
    ciphertext  output / 128   -> dut.ciphertext

Stimulus applied through the helper is always injected *synchronously*:
value drives are performed with ``setimmediatevalue`` inside the
``cocotb.test``/driver coroutine context, so they are in effect for the
next rising clock edge without waiting on a signal-change trigger.
Callers that want HDL-level timing should use clock-aligned coroutines
(reset helper below; clock generation is owned by the tb_top stage).

All APIs used here are public Cocotb 2.1.0 APIs (``cocotb.triggers``,
handle ``value``/``setimmediatevalue``).
"""

from cocotb.triggers import ClockCycles


class Aes128DutHelper:
    """Thin wrapper around the cocotb ``dut`` handle for the ``aes128`` DUT.

    Args:
        dut: the cocotb handle for the top-level module ``aes128``.
    """

    def __init__(self, dut):
        self.dut = dut
        self._validate()

    # -- Validation ----------------------------------------------------
    def _validate(self) -> None:
        """Fail eagerly if the dut handle lacks any contracted pin."""
        for pin in ("clk", "rst_n", "start", "key", "plaintext",
                    "done", "ciphertext"):
            assert hasattr(self.dut, pin), f"DUT missing pin '{pin}'"

    # -- Structural accessors ------------------------------------------
    @property
    def clk(self):
        return self.dut.clk

    @property
    def rst_n(self):
        return self.dut.rst_n

    @property
    def start(self):
        return self.dut.start

    @property
    def key(self):
        return self.dut.key

    @property
    def plaintext(self):
        return self.dut.plaintext

    @property
    def done(self):
        return self.dut.done

    @property
    def ciphertext(self):
        return self.dut.ciphertext

    # -- Drive / sample conveniences ------------------------------------
    def drive(self, start: int, key: int, plaintext: int) -> None:
        """Synchronously drive stimulus inputs.

        Uses ``setimmediatevalue`` so values are in effect for the next
        rising clock edge without waiting on a signal-trigger event.
        ``key``/``plaintext`` are masked to 128 bits and ``start`` to 1 bit.
        """
        mask128 = (1 << 128) - 1
        self.dut.start.setimmediatevalue(int(start) & 0x1)
        self.dut.key.setimmediatevalue(int(key) & mask128)
        self.dut.plaintext.setimmediatevalue(int(plaintext) & mask128)

    def idle(self) -> None:
        """Return stimulus pins to their idle values (``start=0``)."""
        self.dut.start.setimmediatevalue(0)

    def sample(self) -> dict:
        """Sample all DUT outputs combinationally.

        Returns ints: ``{"done": ..., "ciphertext": ...}``.  ``done`` is
        the single-cycle completion pulse and ``ciphertext`` is valid to
        sample while ``done`` is high; sample post-edge (CONTRACT.md §2).
        """
        return {
            "done": int(self.dut.done.value),
            "ciphertext": int(self.dut.ciphertext.value),
        }

    # -- Reset helper ----------------------------------------------------
    async def reset_sync_active_low(
        self,
        assert_cycles: int = 3,
        idle_cycles: int = 2,
    ) -> None:
        """Apply the synchronous active-low reset (CONTRACT.md §6).

        Asserts ``rst_n == 0`` for ``assert_cycles`` rising edges while all
        stimulus pins are held idle, deasserts ``rst_n``, then waits
        ``idle_cycles`` rising edges so the DUT settles back to the idle
        state with ``done == 0`` and ``ciphertext == 0``.
        """
        self.idle()
        self.dut.rst_n.setimmediatevalue(0)
        await ClockCycles(self.dut.clk, max(1, int(assert_cycles)))
        self.dut.rst_n.setimmediatevalue(1)
        await ClockCycles(self.dut.clk, max(0, int(idle_cycles)))