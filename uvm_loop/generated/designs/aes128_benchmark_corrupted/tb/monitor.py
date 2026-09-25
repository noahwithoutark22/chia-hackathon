"""AES-128 observation monitor (pyuvm ``uvm_monitor``).

Stage-3 (OBSERVATION) artifact of the CHIA cocotb+pyuvm generator for the
``aes128`` DUT (``benchmarks/aes128_benchmark_corrupted/aes128.sv``).

:class:`Aes128Monitor` is the passive observer of the DUT.  It samples the
DUT pins exclusively through the ConfigDB-shared ``"dut"`` handle (and the
optional ``"Aes128DutHelper"`` sugar; CONTRACT.md §4) and publishes complete
:class:`~transaction.Aes128Transaction` items through a ``uvm_analysis_port``
(attribute ``analysis_port``) so later stages (scoreboard / coverage /
environment) can subscribe without ever touching the pins themselves.

Pin / timing contract (CONTRACT.md §2, §6, §7 — not re-derived here):

* All pins are rising-edge synchronous: inputs are sampled by the DUT and
  outputs are updated on the positive edge of ``clk``.
* Output sampling (``done``, ``ciphertext``) is done *post-edge* in cocotb's
  read-only region (``await RisingEdge(...)`` then ``await ReadOnly()``) —
  the same sampling convention used by the sequences; ``ciphertext`` is only
  meaningful while ``done`` is high, so it is captured in that same region.
* Stimulus capture (``start``/``key``/``plaintext``) is done with a
  *mid-cycle falling-edge* probe: the driver holds the offer (``start==1``
  with ``key``/``plaintext`` stable) for exactly one whole clock cycle
  (CONTRACT.md §2 driving convention and ``driver.py``), so the values read
  at the falling edge are exactly the values the DUT latches on the following
  rising edge.  A rising-edge probe would be racy with the driver's same-edge
  deassert of ``start`` (cocotb resumes edge-waiting coroutines in
  registration order, which is not ordered against the driver), so the
  falling-edge probe is the reliable capture point.
* Completion is *done-pulse driven* (CONTRACT.md §7): the monitor never
  assumes a fixed latency; it waits for ``done`` to pulse high and samples
  ``ciphertext`` with it.  A bounded timeout is only a safety net for a hung
  FSM (and for the known busy-stuck reset DISCs in the plan) — it is not a
  timing expectation.

What the monitor publishes:

* Exactly one :class:`Aes128Transaction` per observed ``done`` pulse that is
  paired with a previously captured start offer.  Fields filled: ``start``
  (the observed strobe, 1), ``key``/``plaintext`` (captured at the offer),
  ``done`` (1), ``ciphertext`` (sampled while ``done`` is high),
  ``dut_cycle`` (monitor edge-index bookkeeping).  ``txn_id`` is left at its
  default (it is assigned by the driver in the stimulus path and is not
  observable by a passive monitor — CONTRACT.md §5).
* Aborted / never-completing transactions are **dropped** (a ``done`` pulse
  never arrives): a reset asserted while a transaction is in flight, or no
  ``done`` within ``done_timeout_cycles`` after the offer.  Drops are
  counted in ``dropped_count`` and logged but never published, so the
  scoreboard only ever receives complete, comparable transactions.  This is
  the same policy as the sibling ``aes_benchmark`` monitor.
* A ``done`` pulse with no preceding offer (a phantom/spurious pulse while
  the monitor is scanning) is *not* published (there is no stimulus to pair
  with it) and it blocks re-arming while it stays high; the always-running
  assertion checkers of the assertions stage own strict done-pulse counting.

The monitor is observation-only: it never drives pins and never fails the
test by itself.  A genuinely hung DUT is failed by the sequences' bounded
``done`` waits and the env-level watchdog, not by this observer.

All APIs used here are public Cocotb 2.1.0 (``cocotb.triggers``,
handle ``value`` reads) and public pyuvm 5.0.0 APIs
(``uvm_monitor``, ``uvm_analysis_port``).  No SystemVerilog anywhere.
"""

from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge
from pyuvm import ConfigDB, uvm_analysis_port, uvm_monitor

from transaction import Aes128Transaction

__all__ = ["Aes128Monitor"]

#: Width mask for all 128-bit buses (CONTRACT.md §2).
MASK128 = (1 << 128) - 1

#: Bounded wait (clock cycles) for the completion pulse after a captured
#: start offer.  For a correct DUT the completion comes ~10-12 cycles after
#: start; this is a generous bound for a hung FSM / stuck-busy DUT, NOT a
#: latency expectation (CONTRACT.md §7 — verification is driven by ``done``).
DONE_TIMEOUT_CYCLES = 1000


def _config_get(field, default=None):
    """Retrieve a ConfigDB key using the CONTRACT.md §4 retrieval convention.

    Identical helper to ``driver.py``/``sequences.py``: the documented
    project-wide form is ``ConfigDB().get(None, "*", field)``, but the pinned
    pyuvm 5.0.0 runtime rejects wildcard characters in a *retrieval* path
    ("inst_name wildcards only allowed when storing"); when the primary form
    raises, we fall back to the equivalent ``inst_name=""`` retrieval against
    the same wildcard-stored key.  No key or value type is changed.
    """
    try:
        return ConfigDB().get(None, "*", field, default=default)
    except Exception:
        return ConfigDB().get(None, "", field, default=default)


class Aes128Monitor(uvm_monitor):
    """Passive transaction monitor for the ``aes128`` DUT.

    Publishes :class:`Aes128Transaction` items on ``self.analysis_port``
    with the stimulus fields (``start``/``key``/``plaintext``) captured while
    the DUT accepted the offer and the observed-output fields (``done``/
    ``ciphertext``) sampled while ``done`` is high, plus the monitor
    bookkeeping stamp ``dut_cycle``.
    """

    def __init__(self, name="aes128_monitor", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self._helper = None
        #: Analysis port for observed items (CONTRACT.md §5).
        self.analysis_port = None
        #: Max clock cycles to wait for ``done`` after a captured offer.
        self.done_timeout_cycles = DONE_TIMEOUT_CYCLES
        #: Bookkeeping counters (exposed for the env report phase).
        self.published_count = 0
        self.dropped_count = 0
        #: Running 0-based rising-edge index observed by this monitor
        #: (used for the ``dut_cycle`` stamp).
        self._cycle = 0
        #: True while the monitor is waiting for a ``done`` pulse after a
        #: captured offer (only one transaction is in flight at a time, so a
        #: single boolean is sufficient — the driver/sequences honour
        #: CONTRACT.md §7 and the monitor never overlays offers).
        self._in_flight = False

    # ------------------------------------------------------------------
    # UVM phases
    # ------------------------------------------------------------------
    def build_phase(self):
        """Resolve the shared ``dut`` handle (+ optional helper) and build
        the analysis port."""
        super().build_phase()
        self.dut = _config_get("dut")
        if self.dut is None:
            raise RuntimeError(
                "Aes128Monitor: 'dut' not found in ConfigDB (KEY 'dut' must "
                "be set by the tb_top layer before build_phase)"
            )
        try:
            from dut_helper import Aes128DutHelper
        except Exception:  # pragma: no cover - helper lives next to monitor
            Aes128DutHelper = None
        helper = _config_get("Aes128DutHelper")
        if helper is None and Aes128DutHelper is not None:
            helper = Aes128DutHelper(self.dut)
        self._helper = helper
        self.analysis_port = uvm_analysis_port("analysis_port", self)

    async def run_phase(self):
        """Continuously reconstruct and publish observed transactions."""
        self.logger.info(
            "%s: started (done_timeout_cycles=%d)",
            self.get_name(), self.done_timeout_cycles,
        )
        while True:
            stimulus = await self._wait_transaction_start()
            outputs = await self._wait_done_pulse()
            if outputs is None:
                # No done pulse: the in-flight transaction was aborted
                # (reset) or never completed (hung / stuck-busy DUT).
                self.dropped_count += 1
                self.logger.warning(
                    "%s: dropping in-flight transaction (no done pulse)",
                    self.get_name(),
                )
                continue
            self._publish(stimulus, outputs)

    # ------------------------------------------------------------------
    # Observation internals
    # ------------------------------------------------------------------
    async def _wait_transaction_start(self):
        """Block until the DUT accepts the next encryption request.

        Returns the ``(start, key, plaintext)`` stimulus tuple, sampled with
        the mid-cycle falling-edge probe while the offer is stable.  There is
        no bounded timeout here: idle is a permanent valid state and a test
        that never asserts ``start`` is a test-design issue caught by the
        watchdog, not by this observer.

        The DUT is considered idle (i.e., able to accept) when the monitor is
        not currently waiting for a ``done`` pulse (``_in_flight`` is False),
        reset is deasserted and ``done`` is currently low.  Because the
        monitor only re-arms after a published ``done`` pulse, a reset abort
        or a done timeout, a ``start`` poke issued while a transaction is in
        flight (e.g. the directed restart scenarios) can never be mistaken for
        a fresh acceptance.
        """
        while True:
            # Rising edge: advance the cycle stamp and re-synchronise the
            # in-flight flag on reset.
            await RisingEdge(self.dut.clk)
            self._cycle += 1
            if self._reset_active():
                self._in_flight = False
            # Mid-cycle probe: the offer (start/key/plaintext) is guaranteed
            # stable here (CONTRACT.md §2 driving convention).
            await FallingEdge(self.dut.clk)
            if self._reset_active():
                self._in_flight = False
                continue
            if self._in_flight:
                continue
            if self._read_pin("done") == 1:
                # done still high (protocol anomaly / stale pulse): do not
                # re-arm for acceptance until it falls.
                continue
            if self._read_pin("start") == 1:
                key = self._read_pin("key") & MASK128
                plaintext = self._read_pin("plaintext") & MASK128
                self._in_flight = True
                self.logger.debug(
                    "%s: start offer captured key=0x%032x plaintext=0x%032x",
                    self.get_name(), key, plaintext,
                )
                return (1, key, plaintext)

    async def _wait_done_pulse(self):
        """Wait for the completion pulse of the in-flight transaction.

        Returns either:

        * ``(ciphertext, done, dut_cycle)`` — ``done``/``ciphertext`` sampled
          in the read-only region while ``done == 1`` (ciphertext is valid
          exactly then), paired with the monitor edge index ``dut_cycle``;
        * ``None`` — the in-flight transaction was aborted (``rst_n``
          asserted) or no ``done`` pulse appeared within
          ``done_timeout_cycles`` (hung / stuck-busy FSM); nothing to publish.

        Because completion is only ever recognised by the ``done`` pulse,
        this is robust against the corrupted reset-branch (busy stuck high,
        DISC-01) and round-counter (DISC-02) behaviours of the target RTL:
        a transaction that never completes is simply dropped.
        """
        for _ in range(self.done_timeout_cycles):
            await RisingEdge(self.dut.clk)
            self._cycle += 1
            # Post-edge (read-only) sample: outputs updated on this edge are
            # settled here; ``ciphertext`` read together with ``done`` is the
            # value valid while ``done`` is high (CONTRACT.md §2).
            await ReadOnly()
            if self._reset_active():
                self._in_flight = False
                self.logger.warning(
                    "%s: in-flight transaction aborted by reset",
                    self.get_name(),
                )
                return None
            if self._read_pin("done") == 1:
                ciphertext = self._read_pin("ciphertext") & MASK128
                dut_cycle = self._cycle
                self._in_flight = False
                self.logger.debug(
                    "%s: done pulse observed at edge %d", self.get_name(), dut_cycle,
                )
                return (ciphertext, 1, dut_cycle)
        self._in_flight = False
        self.logger.error(
            "%s: no done pulse within %d cycles after start capture "
            "(suggests a hung or stuck-busy FSM)",
            self.get_name(), self.done_timeout_cycles,
        )
        return None

    # ------------------------------------------------------------------
    # Building / publishing
    # ------------------------------------------------------------------
    def _publish(self, stimulus, outputs):
        """Build an :class:`Aes128Transaction` and write it to the analysis
        port.  Fields map 1:1 to CONTRACT.md §5."""
        start, key, plaintext = stimulus
        ciphertext, done, dut_cycle = outputs
        item = Aes128Transaction(f"{self.get_name()}_item")
        item.start = int(start) & 0x1
        item.key = int(key) & MASK128
        item.plaintext = int(plaintext) & MASK128
        item.done = int(done) & 0x1
        item.ciphertext = int(ciphertext) & MASK128
        item.dut_cycle = dut_cycle
        # item.txn_id is intentionally left at its default (0): it is driver
        # bookkeeping on the stimulus path and is not observable here.
        self.analysis_port.write(item)
        self.published_count += 1
        self.logger.debug("%s: published %s", self.get_name(), item)
        return item

    # ------------------------------------------------------------------
    # Pin sampling helpers
    # ------------------------------------------------------------------
    def _reset_active(self):
        """True while the active-low reset is asserted (``rst_n == 0``)."""
        return self._read_pin("rst_n") == 0

    def _read_pin(self, name):
        """Read one DUT pin via the CONTRACT.md §2/§4 access path.

        Uses the shared helper handle when available, else the raw ``dut``
        handle.  Values are plain ints.  If a pin still resolves to X/Z at
        the sample point, ``int(...)`` raises ``ValueError``; that is logged
        and sampled as 0 so observation never dies on uninitialised
        simulation state (Cocotb 2.1.0 documented read path).
        """
        if self._helper is not None:
            try:
                handle = getattr(self._helper, name)
            except AttributeError:  # pragma: no cover - helper mirrors pins
                handle = getattr(self.dut, name)
        else:
            handle = getattr(self.dut, name)
        try:
            return int(handle.value)
        except ValueError:
            self.logger.warning(
                "%s: pin '%s' not resolvable (X/Z at sample point); sampling 0",
                self.get_name(), name,
            )
            return 0