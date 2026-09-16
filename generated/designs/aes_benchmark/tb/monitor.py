"""Stage 3 (observation) artifact of the CHIA generator: the pyuvm monitor.

``AES128Monitor`` is the passive observer of the ``aes128`` DUT.  It samples
the DUT pins exclusively through the ConfigDB-shared ``AES128DUTHelper``
(CONTRACT.md section 5, keys ``"dut"`` / ``"dut_helper"``) and publishes
complete :class:`~tb.transaction.AES128Transaction` items through a
``uvm_analysis_port`` so later stages (scoreboard / coverage / environment)
can subscribe without touching the pins themselves.

How a transaction is reconstructed (CONTRACT.md section 4):

* **Stimulus capture -- the latching edge.**  The DUT accepts a request on a
  ``posedge clk`` while idle (``start == 1``, ``busy == 0`` in the preceding
  cycle); on that same edge it latches ``key`` / ``plaintext`` and asserts
  ``busy`` (RTL ``always_ff``, IDLE branch).  The monitor detects the offer
  with three probes (see ``_wait_transaction_start``):

  1. mid-cycle falling-edge probe -- ``start==1``, ``busy==0``, ``rst_n==1``
     (the stimulus driver holds the offer stable through the whole offer
     cycle, so the values are identical to what the DUT latches);
  2. latching rising-edge probe -- ``start==1`` with ``prev_busy==0``: the
     normal driver holds the offer across the latching edge, and cocotb
     resumes this permanently-registered edge wait before the driver's
     same-edge release, so the stimulus pins still carry the values the DUT
     just latched;
  3. busy-rise fallback -- ``busy`` rising ``0 -> 1``, publishing only when
     the captured ``start`` is still 1 (this is the guard that keeps a
     "start while busy" poke from ever being mistaken for an acceptance).

* **Output sampling -- the ``done`` pulse.**  The monitor waits for the
  single-cycle ``done`` pulse (12 cycles after start acceptance per
  CONTRACT.md section 4) and samples ``ciphertext``, ``busy``, ``done``
  post-edge while ``dut.done == 1``: ``ciphertext`` holds the valid result,
  ``busy`` is 0 (deasserted on the same edge), ``done`` is 1.

* **Reset / hang aborts.**  A reset injection mid-transaction (plan
  ``randomized_testing_strategy``) clears the FSM back to IDLE, so no
  ``done`` pulse ever arrives; the monitor detects the abort (``rst_n==0``,
  or ``busy`` falling **from 1** without ``done``) and **drops** the in-flight
  transaction instead of publishing a phantom completion.  A bounded
  ``done_timeout_cycles`` also drops a transaction that never completes.
  An offer withdrawn while ``busy`` never left 0 (no acceptance edge ever
  occurred) is neither published nor dropped; the monitor simply re-arms.
  Later stages (scoreboard) must therefore **not** expect a one-to-one
  monitor-item <-> sequence-item pairing when reset injection is enabled.

Design notes:

* The monitor is observation-only: it never drives pins and it never fails
  the test by itself.  An abnormal observation (``busy`` falling without a
  ``done`` pulse, or a transaction that never completes) is logged; the
  always-running watchdog (environment/test stage) is what fails a genuinely
  hung test.
* Acceptance and abort detection are **transition-based on ``busy``**, never
  level-based, so the monitor is robust to the acceptance edge landing on
  either the first or the second ``clk`` posedge after the offer appears
  (input-write to DUT-sampling skew observed under some simulators): the
  only hard facts used are "``done`` pulsed" (complete), "``busy`` went
  1 -> 0 without ``done``" (abort) and "``busy`` stayed 0 while ``start``
  was withdrawn" (no acceptance).
* Sampling is synchronized on ``RisingEdge(dut.clk)`` (CONTRACT.md section
  3), reading post-edge values directly -- the canonical cocotb replacement
  for a SystemVerilog clocking-block monitor.  No ``ReadOnly()`` wait is
  inserted: stimulus capture at the latching edge must observe the offer
  *before* the driver's same-edge release.
"""

from cocotb.triggers import FallingEdge, RisingEdge
from pyuvm import ConfigDB, uvm_analysis_port, uvm_monitor

from tb.transaction import AES128Transaction

__all__ = ["AES128Monitor"]

#: Bounded wait (clock cycles) for the completion pulse after a captured
#: start.  The AES-128 latency is 12 cycles, so this is a generous bound
#: for a hung FSM, not a timing requirement.
DONE_TIMEOUT_CYCLES = 1000

#: Sentinel returned by ``_wait_done_pulse`` when the offer was withdrawn
#: before any acceptance edge (``busy`` never left 0): the monitor re-arms
#: the start wait without publishing or dropping anything.
_NOT_ACCEPTED = object()


class AES128Monitor(uvm_monitor):
    """Passive transaction monitor for the ``aes128`` DUT.

    Publishes :class:`~tb.transaction.AES128Transaction` items on
    ``self.analysis_port`` with:

    * stimulus fields (``start``, ``key``, ``plaintext``) captured when the
      DUT accepts the request (idle + ``start==1``),
    * observed-output fields (``ciphertext``, ``busy``, ``done``) sampled
      while ``dut.done == 1``.
    """

    def __init__(self, name="aes128_monitor", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.helper = None
        #: Analysis port for observed items (CONTRACT.md stage-3 addition).
        self.analysis_port = None
        #: Max clock cycles to wait for ``done`` after the start capture.
        self.done_timeout_cycles = DONE_TIMEOUT_CYCLES
        #: Bookkeeping counters (exposed for the environment report).
        self.published_count = 0
        self.dropped_count = 0

    # ------------------------------------------------------------------
    # Phases
    # ------------------------------------------------------------------
    def build_phase(self):
        super().build_phase()
        # The shared DUT handle and pin helper (CONTRACT.md section 5).
        # Retrieval uses the empty-scope path ``get(self, "", key)`` which
        # matches the ``set(None, "*", key, value)`` wildcard store under the
        # pinned pyuvm 5.0 runtime (see CONTRACT.md stage-3 appendix).
        self.dut = ConfigDB().get(self, "", "dut")
        self.helper = ConfigDB().get(self, "", "dut_helper")
        if self.helper is None:
            raise RuntimeError(
                "AES128Monitor: missing shared 'dut_helper' (CONTRACT.md "
                "section 5)"
            )
        #: Analysis port broadcast to scoreboard/coverage subscribers (UVM).
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
            if outputs is _NOT_ACCEPTED:
                # The start offer was withdrawn before the DUT ever sampled
                # it (no acceptance edge, busy never asserted): there is no
                # transaction to observe.  No counters move -- not a drop,
                # since nothing was ever in flight.
                self.logger.debug(
                    "%s: offer withdrawn before acceptance; re-arming "
                    "start wait",
                    self.get_name())
                continue
            if outputs is None:
                # Transaction aborted by a reset injection (or a protocol
                # anomaly / hang): a ``done`` pulse never arrives, so there
                # is nothing to publish.
                self.dropped_count += 1
                self.logger.debug(
                    "%s: dropping in-flight transaction",
                    self.get_name())
                continue
            self._publish(stimulus, outputs)

    # ------------------------------------------------------------------
    # Observation internals
    # ------------------------------------------------------------------
    async def _wait_transaction_start(self):
        """Wait until the DUT accepts the next encryption request.

        Returns the ``(start, key, plaintext)`` stimulus tuple captured at
        the acceptance point (before the driver releases the offer).  Idle
        is a permanent valid state, so there is no bounded timeout here; a
        hung DUT is caught by the watch dog, not by this observer.
        """
        helper = self.helper
        prev_busy = 0
        while True:
            # 1) Mid-cycle probe: the driver holds the offer for the whole
            #    offer cycle, so the values seen here are the values the DUT
            #    will latch on the next rising edge.
            await FallingEdge(self.dut.clk)
            if (int(helper.rst_n) == 1
                    and int(helper.start) == 1
                    and int(helper.busy) == 0):
                self.logger.debug(
                    "%s: offer captured at falling-edge probe",
                    self.get_name())
                return self._sample_stimulus()

            # 2) Latching rising edge: the DUT latches start/key/plaintext on
            #    this edge and asserts busy on the same edge, so the sampled
            #    `busy` is already 1 here and the previous cycle's busy (0,
            #    idle) is the acceptance guard.
            await RisingEdge(self.dut.clk)
            if int(helper.rst_n) == 0:
                # In reset: no acceptance can occur; re-sync the edge
                # tracker.
                prev_busy = 0
                continue
            if int(helper.start) == 1 and prev_busy == 0:
                self.logger.debug(
                    "%s: offer captured at latching rising edge",
                    self.get_name())
                return self._sample_stimulus()

            # 3) Busy-rise fallback (safety net): busy 0 -> 1 marks the
            #    acceptance edge even if `start` was already released by the
            #    time this coroutine sampled it.  Publish only when the
            #    captured stimulus is still a genuine (start==1) offer;
            #    otherwise keep scanning (a "start while busy" poke raises
            #    busy only when prev_busy is already 1, so it can never be
            #    mistaken for an acceptance either way).
            busy = int(helper.busy)
            if busy == 1 and prev_busy == 0:
                stimulus = self._sample_stimulus()
                if stimulus[0] == 1:
                    self.logger.debug(
                        "%s: offer captured at busy-rise fallback",
                        self.get_name())
                    return stimulus
                self.logger.debug(
                    "%s: busy rose without a visible offer; skipping the "
                    "fabricated all-zero stimulus capture",
                    self.get_name())
            prev_busy = busy

    async def _wait_done_pulse(self):
        """Wait for the completion pulse and sample the outputs.

        Returns one of:

        * the ``(ciphertext, busy, done)`` output tuple sampled while
          ``dut.done == 1`` -- the transaction completed and is publishable;
        * ``None`` -- the in-flight transaction was aborted (``rst_n``
          asserted, ``busy`` **falling from 1** without ``done``, or no
          ``done`` within ``done_timeout_cycles``); nothing to publish;
        * ``_NOT_ACCEPTED`` -- the offer was withdrawn while ``busy`` never
          left 0, i.e. no acceptance edge ever occurred; re-arm the start
          wait without moving any counter.

        The detector is **transition-based** on ``busy`` so it is robust to
        the acceptance edge landing either on the first or the second ``clk``
        posedge after the offer appears (write-to-DUT sampling skew under
        some simulators): a completion is only recognized by the ``done``
        pulse and an abort only by ``busy`` going 1 -> 0, never by the mere
        level of ``busy``.
        """
        helper = self.helper
        prev_busy = int(helper.busy)   # busy level at the capture point
        for _ in range(self.done_timeout_cycles):
            await RisingEdge(self.dut.clk)
            if int(helper.rst_n) == 0:
                # Async reset: the in-flight transaction is gone.
                self.logger.debug(
                    "%s: transaction aborted by reset",
                    self.get_name())
                return None
            if int(helper.done) == 1:
                # The done-pulse sample: post-edge values, so `ciphertext`
                # is the valid result, `busy` is 0 (deasserted on the same
                # edge) and `done` is 1.  Checked before the busy-fall
                # detection because busy falls together with done.
                return self._sample_outputs()
            busy = int(helper.busy)
            if prev_busy == 1 and busy == 0:
                # A real 1 -> 0 busy transition without a done pulse: the
                # in-flight transaction vanished (reset-style abort or a
                # protocol anomaly).
                self.logger.warning(
                    "%s: busy fell without done; dropping in-flight "
                    "transaction",
                    self.get_name())
                return None
            if busy == 0:
                if int(helper.start) == 0:
                    # Busy never left 0 and the offer is gone: there was no
                    # acceptance edge at all.  Re-arm the start wait; this
                    # is neither a publish nor a drop.
                    self.logger.debug(
                        "%s: offer withdrawn before acceptance",
                        self.get_name())
                    return _NOT_ACCEPTED
                # else: busy is still 0 but the offer is pending -- the
                # acceptance edge may be the very next one (sampling skew).
                # Keep waiting.
            prev_busy = busy
        self.logger.error(
            "%s: no done pulse within %d cycles after start capture "
            "(transaction suggests a hung FSM)",
            self.get_name(), self.done_timeout_cycles)
        return None

    # ------------------------------------------------------------------
    # Building / publishing
    # ------------------------------------------------------------------
    def _sample_stimulus(self):
        """Sample the three stimulus pins (``start``, ``key``,
        ``plaintext``) as plain ints (CONTRACT.md section 2)."""
        helper = self.helper
        return (int(helper.start), int(helper.key), int(helper.plaintext))

    def _sample_outputs(self):
        """Sample the three output pins (``ciphertext``, ``busy``,
        ``done``) as plain ints."""
        helper = self.helper
        return (int(helper.ciphertext), int(helper.busy), int(helper.done))

    def _publish(self, stimulus, outputs):
        """Build an :class:`AES128Transaction` and write it to the analysis
        port.  Fields map 1:1 to CONTRACT.md section 4."""
        item = AES128Transaction(f"{self.get_name()}_item")
        item.start, item.key, item.plaintext = stimulus
        item.ciphertext, item.busy, item.done = outputs
        self.analysis_port.write(item)
        self.published_count += 1
        self.logger.debug("%s: published %s", self.get_name(), item)
        return item