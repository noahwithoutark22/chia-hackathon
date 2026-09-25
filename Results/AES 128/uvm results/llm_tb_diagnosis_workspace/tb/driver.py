"""AES-128 stimulus driver (pyuvm ``uvm_driver``).

Transfers :class:`Aes128Transaction` items, one at a time, from the
sequencer to the DUT pins.  Pin names, widths, directions, and access
conventions are frozen in CONTRACT.md §2:

    start      -> dut.start      (1 bit)
    key        -> dut.key        (128 bits)
    plaintext  -> dut.plaintext  (128 bits)
    done       -> dut.done       (output, sampled by monitor/sequences)
    ciphertext -> dut.ciphertext (output, sampled by monitor/sequences)
    clk  / rst_n  structural; clock generation and reset policy are owned
    by the tb_top / sequences respectively (NOT transaction fields).

Drive/sample convention (CONTRACT.md §2, §6): all stimulus is applied
synchronously with ``setimmediatevalue`` so the values are stable for the
*next* rising clock edge (the DUT samples inputs and updates outputs on the
positive edge).  Per item the driver performs:

    1. ``get_next_item()`` — block until the sequence has released an item
       (pyuvm 5.0.0 blocking API: returns the item itself),
    2. setup edge: drive ``key``/``plaintext`` with ``start`` low,
    3. strobe edge: drive ``start = item.start`` for exactly one rising
       edge (the DUT captures key/plaintext on this edge while idle),
    4. deassert ``start`` (``key``/``plaintext`` stay stable),
    5. assign the monotonic ``txn_id`` (CONTRACT.md §5),
    6. ``item_done()`` to release the sequence's ``finish_item()``.

Protocol note: the driver is intentionally a *dumb* pin driver.  It does
not wait for the ``done`` pulse and it does not refuse a ``start`` while
the DUT is busy.  Protocol correctness (start only while idle, one ``done``
per accepted start, etc.) is enforced by the sequences (they always wait
for ``done`` between transactions — CONTRACT.md §7) and by the always-on
assertion checkers of the assertions stage.  This split is required by the
busy-window scenarios (TC09, ``cc_start_while_busy``, ``cc_reset_mid_transaction``),
where the *sequence* must inject pin activity while the driver is between
items.

All APIs used here are public Cocotb 2.1.0 (``cocotb.triggers``,
handle ``setimmediatevalue``) and public pyuvm APIs.
"""

from cocotb.triggers import RisingEdge, Timer
from pyuvm import ConfigDB, uvm_driver

MASK128 = (1 << 128) - 1


def _config_get(field, default=None):
    """Retrieve a ConfigDB key using the CONTRACT §4 retrieval convention.

    Primary form is ``ConfigDB().get(None, "*", field)`` — the project-wide
    form documented in CONTRACT.md §4.  Some pinned pyuvm releases reject
    wildcard characters in a ``get()`` retrieval path (the integration /
    tb_top stage owns the official shim for that); when the primary form
    raises, we fall back to the equivalent ``inst_name=""`` retrieval
    against the same wildcard-stored key, so components resolve the shared
    ``"dut"``/``"Aes128DutHelper"`` config on every supported runtime
    without changing any key or value type.
    """
    try:
        return ConfigDB().get(None, "*", field, default=default)
    except Exception:
        return ConfigDB().get(None, "", field, default=default)


class Aes128Driver(uvm_driver):
    """Drives AES-128 stimulus pins from sequence items."""

    def __init__(self, name="aes128_driver", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self._helper = None
        self._txn_count = 0

    def build_phase(self):
        """Resolve the shared DUT handle and the optional helper.

        Keys are read exactly as documented in CONTRACT.md §4: ``"dut"``
        and the optional ``"Aes128DutHelper"``.
        """
        super().build_phase()
        self.dut = _config_get("dut")
        if self.dut is None:
            raise RuntimeError(
                "Aes128Driver: 'dut' not found in ConfigDB (KEY 'dut' must be "
                "set by the tb_top layer before build_phase)"
            )
        try:
            from dut_helper import Aes128DutHelper
        except Exception:  # pragma: no cover - helper lives next to driver
            Aes128DutHelper = None
        helper = _config_get("Aes128DutHelper")
        if helper is None and Aes128DutHelper is not None:
            helper = Aes128DutHelper(self.dut)
        self._helper = helper

    # -- Pin driving ---------------------------------------------------
    def _drive(self, start, key, plaintext):
        """Apply one set of stimulus values (``start`` 1 bit, buses 128 bit)."""
        if self._helper is not None:
            self._helper.drive(
                int(start) & 0x1, int(key) & MASK128, int(plaintext) & MASK128
            )
        else:
            self.dut.start.setimmediatevalue(int(start) & 0x1)
            self.dut.key.setimmediatevalue(int(key) & MASK128)
            self.dut.plaintext.setimmediatevalue(int(plaintext) & MASK128)

    # -- Main loop ------------------------------------------------------
    async def run_phase(self):
        """Pull items from the sequencer and drive one transaction each."""
        # Hold stimulus idle while waiting for the first item.
        self._drive(0, 0, 0)
        while True:
            # Blocking API (pyuvm 5.0.0): returns the item itself, never a
            # bool/tuple (sibling-fix W-DRIVER-TRY-NEXT-CRASH).
            item = await self.seq_item_port.get_next_item()
            # The releasing sequence may still be executing inside a cocotb
            # GPI callback frame (e.g. `ReadOnly`, when it sampled `done`
            # before releasing this item).  Yielding to the simulator here
            # leaves that frame so the immediate setimmediatevalue pin writes
            # in _drive_item() are legal (cocotb forbids writes during the
            # ReadOnly phase).
            await Timer(1, "step")
            await self._drive_item(item)
            self.seq_item_port.item_done()

    async def _drive_item(self, item):
        """Drive one ``Aes128Transaction`` as a start-to-idle strobe.

        ``key``/``plaintext`` are stabilised for one edge with ``start``
        low, then ``start`` is asserted for exactly one rising edge (the
        DUT captures the data on that edge while idle) and deasserted.
        ``txn_id`` is assigned here (CONTRACT.md §5); ``done``,
        ``ciphertext``, ``dut_cycle`` are filled by the monitor stage and
        intentionally left untouched.
        """
        key = int(item.key) & MASK128
        plaintext = int(item.plaintext) & MASK128
        strobe = int(item.start) & 0x1

        # Setup edge: data stable, start low.
        self._drive(0, key, plaintext)
        await RisingEdge(self.dut.clk)

        # Strobe edge: DUT samples start (and key/plaintext).
        self._drive(strobe, key, plaintext)
        await RisingEdge(self.dut.clk)

        # Deassert start; keep key/plaintext stable.
        self._drive(0, key, plaintext)

        item.txn_id = self._txn_count
        self._txn_count += 1
        self.logger.debug(
            "drove txn_id=%d start=%d key=%032x plaintext=%032x",
            item.txn_id, strobe, key, plaintext,
        )