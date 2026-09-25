# AES-128 cocotb+pyuvm Testbench — Contract (Stage 1)

This file is the single source of truth for conventions used by every later
stage (sequences, driver, monitor, agent, scoreboard, coverage, assertions,
env, test, tb_top).  Later stages MUST read this file and MUST NOT re-derive
or invent new conventions.  All RTL facts below were extracted from
`/workspace/benchmarks/aes128_benchmark_corrupted/aes128.sv` and
`/workspace/generated/designs/aes128_benchmark_corrupted/rtl/rtl_info.json`.

---

## 1. Top module

- **Top module name:** `aes128`
- **RTL file (read-only, must not be modified or duplicated):**
  `benchmarks/aes128_benchmark_corrupted/aes128.sv`
- **Parameters:** NONE.  The RTL declares no module parameters.  The
  `SBOX`/`RCON` entries in `rtl_info.json` are internal `localparam` arrays
  (constant lookup tables inside the module), not configurable top-level
  parameters.  All pin widths below are literal and fixed.

## 2. Pin map (exact names, directions, widths, and access)

Clock and reset are structural signals and are NOT transaction fields.

| Pin         | Direction | Width  | Type  | Access              | Notes |
|-------------|-----------|--------|-------|---------------------|-------|
| `clk`       | input     | 1      | logic | `dut.clk`           | Master clock, rising-edge triggered; inputs sampled and outputs updated on the positive edge. |
| `rst_n`     | input     | 1      | logic | `dut.rst_n`         | Active-low **synchronous** reset (see §6). |
| `start`     | input     | 1      | logic | `dut.start`         | Transaction start strobe; honored on the clock edge while the DUT is idle. |
| `key`       | input     | 128    | logic | `dut.key`           | 128-bit AES-128 encryption key `[127:0]`; MSB is AES state byte 0. |
| `plaintext` | input     | 128    | logic | `dut.plaintext`     | 128-bit plaintext block `[127:0]`; MSB is AES state byte 0. |
| `done`      | output    | 1      | logic | `dut.done`          | Pulses high for exactly one clock cycle when `ciphertext` is valid. |
| `ciphertext`| output    | 128    | logic | `dut.ciphertext`    | 128-bit ciphertext `[127:0]`, valid to sample while `done` is high. |

There are no inout ports.  Python-side values are plain non-negative `int`s
(0 .. 2**128 - 1 for the 128-bit buses; 0/1 for the 1-bit pins).

**Driving convention (driver stage):** apply stimulus synchronously for the
rising edge, e.g. `dut.start.value = 1`, `dut.key.value = key`,
`dut.plaintext.value = pt` (or `setimmediatevalue` for already-scheduled
injection).  Preferred central access: the `Aes128DutHelper` in
`dut_helper.py` (`helper.drive(start, key, plaintext)`, `helper.idle()`,
`helper.sample()`).

**Sampling convention (monitor/scoreboard stage):** sample `dut.done` and
`dut.ciphertext` after each rising edge (post-edge values).  `done` is the
completion pulse; `ciphertext` is only meaningful while `done == 1`.

## 3. Reference model (behavioral oracle)

- **File:** `/workspace/benchmarks/aes128_benchmark_corrupted/aes128_reference_model.py`
  (must not be duplicated or reimplemented).
- **API:** `aes128_encrypt(plaintext: int, key: int) -> int` — returns the
  128-bit ciphertext integer.  Argument order is exactly `(plaintext, key)`.
  `TEST_VECTORS` in that module provides the mandatory known answers
  (FIPS-197 `69c4e0d86a7b0430d8cdb78070b4c55a`, all-zero
  `66e94bd4ef8a2c3b884cfa59ca342b2e`, incrementing
  `0a940bb5416ef045f1c39458c653ea5a`).
- **Argument/return mapping:** transaction `plaintext` -> `plaintext`;
  transaction `key` -> `key`; reference-model return value -> checked against
  the DUT `ciphertext` sampled while `done` is high.
- **Byte ordering:** the most-significant byte of the 128-bit vectors is AES
  state byte 0, state arranged column-major (FIPS-197 conventional ordering).
  Driving/reading `dut.key`/`dut.plaintext`/`dut.ciphertext` as Python ints
  already preserves this convention — no byte reordering is performed by the
  testbench.

## 4. ConfigDB keys (exact — do not invent alternatives)

Everything is shared via pyuvm `ConfigDB()`.  Keys are set once by the test /
tb_top layer and shared read-only by all components.

| Key                  | Python type        | Value/Content                                               |
|----------------------|--------------------|-------------------------------------------------------------|
| `"dut"`              | cocotb Handle      | The top-level handle for module `aes128` (the `dut` passed to the cocotb test). |
| `"CLK_HALF_PERIOD_NS"` | `int`            | Half-period for the clock generator in ns (default 5 → 10 ns period, 100 MHz). |
| `"Aes128DutHelper"`  | `Aes128DutHelper`  | Optional shared instance of the pin-access helper (see `dut_helper.py`). |

Example usage in later stages (project-wide pyuvm access form, matching
sibling CHIA cocotb+pyuvm TBs):

```python
dut = ConfigDB().get(None, "*", "dut")
half_period_ns = int(ConfigDB().get(None, "*", "CLK_HALF_PERIOD_NS"))
helper = ConfigDB().get(None, "*", "Aes128DutHelper", default=None)  # optional
```

`"Aes128DutHelper"` is optional sugar; `"dut"` + `"CLK_HALF_PERIOD_NS"` are
sufficient and authoritative.  If the helper is used it must be built as
`Aes128DutHelper(ConfigDB().get(None, "*", "dut"))`.

**Runtime note (integration-stage owned):** the `inst_name="*"` wildcard
retrieval form above is this project's convention, matching sibling CHIA
generated TBs.  Some pinned pyuvm releases reject wildcard characters in
`get()` retrieval paths ("wildcards only allowed when storing").  As with the
sibling TBs, the integration/tb_top stage owns any runtime shim and MUST NOT
change the keys or value types listed in this table.

## 5. Transaction / sequence_item

- **Class:** `Aes128Transaction` in `tb/transaction.py`
- **Base class:** pyuvm `uvm_sequence_item`
- **Field → attribute mapping (plain Python attributes, `int` values):**

| Field       | Attribute    | Type/Width | Direction of data flow      |
|-------------|--------------|------------|------------------------------|
| Start strobe| `start`      | `int` / 1  | sequence → driver → DUT      |
| Encryption key | `key`     | `int` / 128| sequence → driver → DUT      |
| Plaintext   | `plaintext`  | `int` / 128| sequence → driver → DUT      |
| Done pulse  | `done`       | `int` / 1  | DUT → monitor → scoreboard   |
| Ciphertext  | `ciphertext` | `int` / 128| DUT → monitor → scoreboard   |
| Transaction id | `txn_id`  | `int`      | bookkeeping (assigned by driver when a start is accepted) |
| Cycle stamp | `dut_cycle`  | `int` or `None` | monitor bookkeeping (sampled edge index) |

Clock/reset are NOT transaction fields.

`Aes128Transaction` provides `copy(other)` and `clone()`.  The driver stage
sets `start`/`key`/`plaintext`; the monitor stage fills `done`/`ciphertext`
and `dut_cycle` before broadcasting on the analysis port.

## 6. Clock and reset semantics

- **Clock name:** `clk`, **posedge**, `dut.clk`.  Clock generation is owned
  by the tb_top stage (a `cocotb.start_soon` coroutine toggling `dut.clk`
  with half-period `CLK_HALF_PERIOD_NS`).  All inputs are sampled and all
  outputs are updated on the positive edge.
- **Reset name:** `rst_n`, **active-low**, **synchronous** (the sequential
  block is `always_ff @(posedge clk)` with `if (!rst_n)` — no asynchronous
  sensitivity).  Asserting `rst_n == 0` for at least one rising edge clears
  the internal transaction state and leaves the DUT idle: `done == 0`,
  `ciphertext == 0`, and the DUT is ready to accept a new `start`.
- `Aes128DutHelper.reset_sync_active_low()` (in `dut_helper.py`) provides the
  canonical reset pulse coroutine.

## 7. Behavior summary (for reference; NOT to be re-derived)

- A transaction starts when `start` is asserted on a rising edge while the
  DUT is idle; `key` and `plaintext` are captured at that edge.
- The DUT then performs AES-128 encryption: initial AddRoundKey, 10 rounds
  (SubBytes, ShiftRows, MixColumns, AddRoundKey; the final round omits
  MixColumns), using the advertised FIPS-197 semantics.
- When the result is ready, `done` pulses high for exactly one cycle and
  `ciphertext` holds the encrypted block.  A new transaction must only be
  started after the previous one completes (`done` observed).
- **Latency/discovery rule:** the implementation latency is ~10 rounds after
  start, but verification MUST be driven by the `done` pulse, not a
  hard-coded cycle count (spec §3).

## 8. Cross-stage obligations (hard)

- ONLY Python (cocotb 2.1.0 + pyuvm).  No SystemVerilog UVM code, no SV
  interfaces, no SV covergroups, no SVA.  The only SystemVerilog in the
  project is the DUT RTL itself, which must NOT be modified or duplicated.
- Use only public Cocotb 2.1.0 APIs (`cocotb.triggers`, `cocotb.clock.Clock`,
  `cocotb.start_soon`, handle `value`/`setimmediatevalue`).  Never import
  `ModifiableObject` from `cocotb.handle`.
- Functional coverage via cocotb-coverage (`CoverPoint`/`CoverCross`) through
  the shared `coverage_db`.
- Assertions as plain Python checks inside always-running coroutines started
  with `cocotb.start_soon`; they must fail the test immediately when
  violated.
- A watchdog is required: an always-running coroutine (or a bounded
  `cocotb.triggers.with_timeout` wrapper) that fails the test if it does not
  finish within a bounded number of clock cycles.
- Do not modify the RTL, specification, reference model, or the generated
  plan.

---

## 9. Stage-3 observation additions (monitor + agent) — appended by stage 3

This section documents the observation-side components produced by the
OBSERVATION generation stage.  It does not rewrite anything above; it only
records conventions the later stages (scoreboard, coverage, assertions, env,
test, tb_top) must follow.

### 9.1 `tb/monitor.py` — `Aes128Monitor` (`uvm_monitor`)

- Passive observer.  Resolves the shared handles in `build_phase` using the
  exact CONTRACT §4 keys (`"dut"`, optional `"Aes128DutHelper"`) and builds
  one `uvm_analysis_port` named `"analysis_port"` (attribute
  `self.analysis_port`).
- `run_phase` is a single clock-synchronized loop:
  - acceptance probe: mid-cycle `FallingEdge` probe requiring `rst_n==1`,
    `done==0`, `start==1` while not already tracking a transaction;
    captures `start`/`key`/`plaintext` (the driver holds the offer stable
    for one full clock cycle, so the sampled values are those the DUT
    latches on the following rising edge);
  - completion wait: `RisingEdge` + `ReadOnly` post-edge sampling of
    `done`/`ciphertext` (CONTRACT §2 convention); completion is driven by
    the `done` pulse only (CONTRACT §7 — no fixed latency).
- Publishes exactly one `Aes128Transaction` per observed `done` pulse that
  is paired with a captured offer.  Filled fields: `start` (1), `key`,
  `plaintext`, `done` (1), `ciphertext`, `dut_cycle`.
  `txn_id` is left at its default (driver bookkeeping, not observable by a
  passive monitor).
- Transactions that never produce a `done` pulse (reset abort, hung /
  busy-stuck FSM — cf. the plan's DISC-01/DISC-02) are dropped: logged,
  counted in `dropped_count`, and NOT published.  `published_count` /
  `dropped_count` are exposed for the env report phase.
- A spurious `done` pulse with no captured offer is not published and
  blocks re-arming while it stays high (strict done-pulse accounting is
  owned by the assertions stage).

### 9.2 `tb/agent.py` — `Aes128Agent` (`uvm_agent`)

- Encapsulates the stage-2 stimulus components and the stage-3 monitor:
  children named `"driver"` (`Aes128Driver`), `"sequencer"` 
  (`Aes128Sequencer`), `"monitor"` (`Aes128Monitor`), plus one
  `uvm_analysis_port` named `"analysis_port"` (attribute
  `self.analysis_port`).
- Active by default (pyuvm 5.0.0 `uvm_agent.build_phase` sets
  `is_active = UVM_ACTIVE`; overridable via the ConfigDB key `"is_active"`).
  Active mode builds driver + sequencer + monitor; passive mode builds only
  the monitor.
- `connect_phase` wiring (bottom-up phase order):
  `driver.seq_item_port.connect(sequencer.seq_item_export)` and
  `monitor.analysis_port.connect(agent.analysis_port)`.
  Under the pinned pyuvm 5.0.0 this is a valid broadcast-model connection
  (`uvm_analysis_port` is a `uvm_export_base` subclass with `write`, so it
  is accepted as a subscriber).  The environment subscribes with
  `agent.analysis_port.connect(<analysis_export>)`.
- Component attributes consumed by later stages: `agent.driver`,
  `agent.sequencer`, `agent.monitor`, `agent.analysis_port`.

---

## 10. Stage-4 scoreboard additions — appended by stage 4

This section documents the scoring-side component produced by the
SCOREBOARD generation stage.  It does not rewrite anything above; it only
records conventions the later stages (coverage, assertions, env, test,
tb_top) must follow.

### 10.1 `tb/scoreboard.py` — `Aes128Scoreboard` (`uvm_scoreboard`)

- Item-driven reference-model scoreboard (plan
  `scoreboard_reference_model_strategy`): it consumes exactly one
  `Aes128Transaction` per completed (non-reset-aborted) transaction via a
  `uvm_tlm_analysis_fifo` and compares the DUT `ciphertext` (sampled by
  the monitor while `done` is high) against
  `aes128_reference_model.aes128_encrypt(plaintext, key)`.
- **Reference model:** the authoritative
  `benchmarks/aes128_benchmark_corrupted/aes128_reference_model.py` was
  copied **verbatim** to `tb/aes128_reference_model.py` (byte-identical;
  this is the sanctioned copy option).  The scoreboard imports the module
  `aes128_reference_model` (preferring the tb copy, falling back to the
  benchmarks directory on `sys.path`) and validates it reproduces its own
  `TEST_VECTORS` at import time.  Its arithmetic is never reimplemented.
- **Wiring (owned by the env stage):**
  `agent.analysis_port.connect(scoreboard.analysis_export)`, or the
  convenience `scoreboard.connect_monitor(agent.analysis_port)`.
  Public attributes: `analysis_fifo`, `analysis_export`.
- **Scoring semantics:** strictly in order (one transaction in flight at a
  time).  In-order integrity is verified with the monitor's monotonic
  `dut_cycle` stamp (**not** `txn_id`, which the passive monitor cannot
  observe and leaves at its default 0, CONTRACT.md §5/§9.1); the scoreboard
  assigns its own 1-based reporting index.
- **Counters/results:** `transactions`, `matches`, `mismatches`,
  `protocol_errors` (item-level protocol violations: `start != 1` =
  "done without a captured start", `done != 1` = corrupt completion
  record — reported separately from ciphertext mismatches),
  `order_errors`, `ungradable_errors`, `error_count`, `passing`
  (`mismatches == 0 and error_count == 0`), plus `results()` dict and
  `report_phase()` summary.  Pin-level protocol anomalies (phantom done,
  stuck done, done width) remain owned by the assertions stage (§9.1).
- ConfigDB: reads only the existing `"dut"` key (CONTRACT.md §4,
  diagnostic; scoring is item-driven and continues if absent).  No new
  ConfigDB keys are introduced.

---

## 11. Stage-5 coverage & assertions additions — appended by stage 5

This section documents the coverage and assertion-side artifacts produced by
the COVERAGE & ASSERTIONS generation stage.  It does not rewrite anything
above; it only records the conventions the later stages (environment, test,
tb_top) must follow.

### 11.1 `tb/coverage.py` — `Aes128Coverage` (`uvm_subscriber`)

- Functional coverage via the cocotb-coverage shared singleton
  `coverage_db` (CONTRACT.md §8); covergroups and bins match the plan's
  `functional_coverage` section exactly.  No SV covergroups anywhere.
- Three covergroups under the shared `coverage_db` root `top`:
  - `top.cg_start_done_handshake` — `start_state`
    (`deasserted`/`asserted`), `done_state` (`no_pulse`/`done_pulse`),
    cross `start_done_cross`.  **Pin-driven**: sampled every clock cycle in
    `run_phase` using the CONTRACT.md §9.1 mid-cycle falling-edge probe of
    `dut.start` / `dut.done`.
  - `top.cg_key_plaintext_patterns` — `key_pattern`, `plaintext_pattern`
    (bins `all_zero`/`all_ones`/`fips197`/`other`), cross
    `key_plaintext_cross`.  **Item-driven**: sampled from each published
    `Aes128Transaction` (`key`/`plaintext`, CONTRACT.md §5).
  - `top.cg_ciphertext_classes` — `ciphertext_class` (bins
    `fips197_ans`/`all_zero_ans`/`increment_ans`/`other`).  **Item-driven**:
    sampled from `item.ciphertext`.
- The plan's expression bins are implemented as bin classifiers (`xf`)
  returning small class ids matched by equality, with human-readable
  `bins_labels` equal to the plan bin names.
- **Wiring (owned by the env stage):** build the subscriber and call
  `coverage.connect_monitor(agent.analysis_port)` (equivalent to
  `agent.analysis_port.connect(coverage.analysis_export)`; the built-in
  pyuvm `uvm_subscriber.analysis_export` is the analysis sink).  The
  component also runs its `run_phase` handshake sampler for the whole
  simulation.
- **Reporting helpers** (all read the shared `coverage_db`):
  `report_coverage(logger=None, bins=False, node="")`,
  `coverage_percentage() -> float` (mean across the three covergroups),
  `coverage_summary_dict() -> dict` (per-leaf coverage),
  `export_coverage_yaml(filename)` / `export_coverage_xml(filename)`.
- ConfigDB: reads only the existing `"dut"` and the optional
  `"Aes128DutHelper"` keys (CONTRACT.md §4).  Observation-only — never
  drives the DUT and never fails the test.

### 11.2 `tb/assertions.py` — `Aes128Assertions` + watchdog

- SVA-replacement Python checkers (CONTRACT.md §8): every plan item in
  `useful_assertions` is implemented as a continuous checker *coroutine*
  launched with `cocotb.start_soon`; all six items are severity `error`
  and a violation logs + raises `AssertionError` out of the coroutine
  immediately (fails the enclosing cocotb test at once).
- Checkers (plan names exact): `reset_returns_dut_to_idle`,
  `start_requires_idle`, `done_pulse_width_one`, `transaction_terminates`,
  `ciphertext_matches_reference`, `fips197_known_answer`.
- **Sampling timing** (CONTRACT.md §2/§6/§9.1 — established, not
  re-derived): stimulus (`start`/`key`/`plaintext`) via the mid-cycle
  falling-edge probe; outputs (`done`/`ciphertext`) and reset (`rst_n`)
  sampled post-edge (`RisingEdge` + `ReadOnly`).  Each checker is an
  independent state machine; they may be started/stopped in any
  combination.
- **Reference model:** `_load_reference_encrypt()` resolves first the
  verbatim tb copy `tb/aes128_reference_model.py`, then the benchmarks
  directory (CONTRACT.md §3/§10.1), validated against `TEST_VECTORS` at
  load.  If the oracle is unavailable the equality checkers degrade to an
  informational warning (never reimplemented; the scoreboard stays the
  authoritative comparator).  Unpaired `done` pulses are informational
  notes only — strict done-pulse accounting belongs to the monitor /
  scoreboard (CONTRACT.md §9.1/§10.1).
- **Integration API (owned by the env stage):**
  `checks = launch_assertions(dut=None, helper=None, log=None)` builds an
  `Aes128Assertions` and starts all checker coroutines (`checks.start()` is
  idempotent); `checks.summarize()` reports violations/warnings for the
  end-of-test report.  Must be started while the cocotb simulation is
  running (never at import time).
- **Bounded-time constants:** `DONE_WINDOW_CYCLES = 80` (a correct DUT
  pulses `done` ca. 12-14 cycles after the start edge; 80 gives >5x
  margin and sits far below the sequences' 200-cycle waits, so the
  checkers are the first fence against a hung/stuck FSM —
  cf. DISC-01/DISC-02);
  `WATCHDOG_DEFAULT_CYCLES = 100000`.
- **Watchdog (CONTRACT.md §8):**
  `launch_watchdog(dut=None, timeout_cycles=WATCHDOG_DEFAULT_CYCLES)`
  returns a running cocotb task that raises `AssertionError` if more than
  `timeout_cycles` clock edges elapse; the env/test stage MUST `kill()`
  the returned task on normal completion.  `watchdog(dut, timeout_cycles)`
  is the coroutine itself.
- ConfigDB: reads only the existing `"dut"` and the optional
  `"Aes128DutHelper"` keys (CONTRACT.md §4).  No new ConfigDB keys are
  introduced by this stage.

---