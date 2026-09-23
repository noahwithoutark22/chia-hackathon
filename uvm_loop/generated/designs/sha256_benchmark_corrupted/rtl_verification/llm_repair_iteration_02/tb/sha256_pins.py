"""SHA-256 DUT pin-access helper.

Stage-1 CONTRACT artifact.  This is plain Python -- NOT a SystemVerilog
interface -- that centralizes access to every SHA-256 DUT pin through the
cocotb top-level ``dut`` handle (see CONTRACT.md in this directory).

Why a helper at all: every later cocotb+pyuvm stage (driver, monitor,
env, test, ...) reads and writes exactly the same six pins with the same
value semantics.  Centralizing the raw ``dut.<pin>.value`` access here
keeps those conventions identical across components.

Cocotb 2.1.0 public-API notes honored throughout:

* Driving a pin: ``dut.<pin>.value = <int>`` (default Deposit action).
* Reading a pin: ``int(dut.<pin>.value)`` -- the documented 2.1.0 read
  path (``int(dut.<pin>)`` casts are deprecated and are never used).
* ``cocotb.handle.ModifiableObject`` is intentionally never imported;
  pin access only uses public handle attribute access and ``value``.
* Coroutine helpers use ``cocotb.triggers`` and ``async``/``await`` only.

The ``Sha256Pins`` instance (and the raw ``dut`` handle) are shared
between UVM components through pyuvm's ``ConfigDB`` -- exact keys:
``"dut"`` and ``"sha256_pins"`` (see CONTRACT.md).
"""

from cocotb.triggers import ClockCycles, RisingEdge

# ----------------------------------------------------------------------
# Pin names -- must match CONTRACT.md and the RTL (sha256.sv) exactly.
# ----------------------------------------------------------------------
CLK_NAME = "clk"
RST_NAME = "rst_n"
START_NAME = "start"
BLOCK_NAME = "block"
DONE_NAME = "done"
DIGEST_NAME = "digest"

# Pin widths in bits (from rtl_info.json / verification plan).
CLK_WIDTH = 1
RST_WIDTH = 1
START_WIDTH = 1
BLOCK_WIDTH = 512
DONE_WIDTH = 1
DIGEST_WIDTH = 256

# ----------------------------------------------------------------------
# Structural / timing conventions (authoritative, see CONTRACT.md).
# ----------------------------------------------------------------------
CLK_PERIOD_NS = 10.0      # default clock period used by the generated TB
CLK_EDGE = "posedge"      # all sequential logic is rising-edge

RST_POLARITY = "active_low"
RST_STYLE = "asynchronous"  # reset is sensitive to negedge of rst_n
RST_ACTIVE_VALUE = 0         # value that asserts reset on rst_n
RST_INACTIVE_VALUE = 1

# The corrupted RTL drives `done` continuously (DISC-001) and never
# deasserts `busy` (DISC-013), so completion is determined by a FIXED
# cycle count: 64 reference-model rounds plus margin -- never by `done`.
EXPECTED_LATENCY_CYCLES = 64   # reference model: one SHA-256 round/cycle
COMPLETION_MARGIN_CYCLES = 70  # cycles to wait after start before sampling
WATCHDOG_MARGIN_CYCLES = 500   # generous global run bound for the TB


# ----------------------------------------------------------------------
# Module-level conversion helpers (also mirrored on Sha256Transaction).
# ----------------------------------------------------------------------
def block_int_to_bytes(block: int) -> bytes:
    """512-bit block int -> 64 big-endian bytes (reference-model format)."""
    return int(block).to_bytes(BLOCK_WIDTH // 8, "big")


def digest_int_to_bytes(digest: int) -> bytes:
    """256-bit digest int -> 32 big-endian bytes (hashlib format)."""
    return int(digest).to_bytes(DIGEST_WIDTH // 8, "big")


def make_clock(dut, period_ns: float = CLK_PERIOD_NS, unit: str = "ns"):
    """Build a cocotb.clock.Clock for ``dut.clk``.

    The caller must ``clock.start()`` it (typically in the cocotb test).
    Public Cocotb 2.1.0 API: ``Clock(signal, period, unit=...)``.
    """
    from cocotb.clock import Clock

    return Clock(dut.clk, period_ns, unit=unit)


class Sha256Pins:
    """Named, centralized access to every SHA-256 DUT pin.

    ``dut`` is the cocotb top-level handle (the ``dut`` argument passed
    to the test entry point in ``test_top.py``).  Handles are cached as
    attributes so components can write ``pins.block.value = ...`` or use
    the named read/drive helpers below.
    """

    def __init__(self, dut) -> None:
        self.dut = dut
        # Structural pins.
        self.clk = dut.clk
        self.rst_n = dut.rst_n
        # Input pins.
        self.start = dut.start
        self.block = dut.block
        # Output pins.
        self.done = dut.done
        self.digest = dut.digest

    # ------------------------------------------------------------------
    # Drive helpers (input pins)
    # ------------------------------------------------------------------
    def drive_reset(self, active: bool) -> None:
        """Assert (``active=True``) or deassert the low-active reset."""
        self.rst_n.value = RST_ACTIVE_VALUE if active else RST_INACTIVE_VALUE

    def drive_start(self, value: int) -> None:
        self.start.value = int(value) & ((1 << START_WIDTH) - 1)

    def drive_block(self, value: int) -> None:
        self.block.value = int(value) & ((1 << BLOCK_WIDTH) - 1)

    # ------------------------------------------------------------------
    # Read helpers (input + output pins)
    # ------------------------------------------------------------------
    def read_start(self) -> int:
        return int(self.start.value)

    def read_block(self) -> int:
        return int(self.block.value)

    def read_done(self) -> int:
        return int(self.done.value)

    def read_digest(self) -> int:
        return int(self.digest.value)

    # ------------------------------------------------------------------
    # Aggregate helpers for driver / monitor convenience
    # ------------------------------------------------------------------
    def sample_inputs(self) -> tuple:
        """Return (start, block) as currently driven on the DUT pins."""
        return self.read_start(), self.read_block()

    def sample_outputs(self) -> tuple:
        """Return (done, digest) as currently sampled on the DUT outputs."""
        return self.read_done(), self.read_digest()

    async def reset_dut(self, hold_cycles: int = 5) -> None:
        """Assert active-low reset, hold it for ``hold_cycles`` edges, then
        deassert.

        Reset is asynchronous: the first negedge takes effect immediately;
        holding it across rising edges ensures a fully settled reset state.
        Callers should synchronize to ``clk`` afterwards (clocked contexts
        normally already are).
        """
        self.drive_reset(True)
        await ClockCycles(self.clk, max(1, int(hold_cycles)))
        self.drive_reset(False)
        await RisingEdge(self.clk)

    def __repr__(self) -> str:
        return f"Sha256Pins(dut={self.dut!r})"