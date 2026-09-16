# FIFO cocotb+pyuvm Testbench — Contract (Stage 1)

This file is the single source of truth for conventions used by every later
stage (sequences, driver, monitor, agent, scoreboard, coverage, assertions,
env, test, tb_top).  Later stages MUST read this file and MUST NOT re-derive
or invent new conventions.  All RTL facts below were extracted from
`/workspace/benchmarks/fifo/fifo.sv` and `/workspace/generated/designs/fifo/rtl/rtl_info.json`.

---

## 1. Top module

- **Top module name:** `fifo`
- **RTL file (read-only, must not be modified or duplicated):** `benchmarks/fifo/fifo.sv`
- **Parameters (with defaults):**
  - `DATA_WIDTH` (default `8`) — width of `din` / `dout` in bits
  - `DEPTH` (default `4`) — number of entries the FIFO can hold; pointers advance modulo `DEPTH`

ConfigDB carries the *elaborated* parameter values (see §4).  Widths in the
pin table below are therefore concrete at runtime.

## 2. Pin map (exact names, directions, widths, and access)

Clock and reset are structural signals and are NOT transaction fields.

| Pin    | Direction | Width    | Type  | Access                     | Notes |
|--------|-----------|----------|-------|----------------------------|-------|
| `clk`  | input     | 1        | logic | `dut.clk`                  | Master clock, rising-edge triggered. |
| `rst_n`| input     | 1        | logic | `dut.rst_n`                | Active-low asynchronous reset.       |
| `wr_en`| input     | 1        | logic | `dut.wr_en`                | Write request.                       |
| `rd_en`| input     | 1        | logic | `dut.rd_en`                | Read request.                        |
| `din`  | input     | `DATA_WIDTH` | logic | `dut.din`            | Input data bus, `[DATA_WIDTH-1:0]`.  |
| `dout` | output    | `DATA_WIDTH` | logic | `dut.dout`           | Registered output data, `[DATA_WIDTH-1:0]`; latency 1. |
| `full` | output    | 1        | logic | `dut.full`                 | Combinational: `count == DEPTH`.     |
| `empty`| output    | 1        | logic | `dut.empty`                | Combinational: `count == 0`.         |

There are no inout ports.  All pins are killed/knowable ordinary `logic` pins.

**Driving convention (driver stage):** apply stimulus synchronously for the
rising edge, e.g. `dut.wr_en.value = 1`, `dut.rd_en.value = 0`,
`dut.din.value = val` (or `setimmediatevalue` for already-scheduled
injection).  Preferred central access: the `FifoDutHelper` in `dut_helper.py`
(`helper.drive(wr_en, rd_en, din)`, `helper.sample()`).

**Sampling convention (monitor/scoreboard stage):** sample `dut.dout`,
`dut.full`, `dut.empty` after each rising edge (post-edge values).  `dout`
is a registered output with **latency 1**: the value appearing after the edge
of an accepted read is the entry that was popped; scoreboard comparisons must
use the reference model with the declared latency.

## 3. Reference model (behavioral oracle)

- **File:** `/workspace/benchmarks/fifo/ref_model.py` (must not be duplicated or reimplemented).
- **API:**
  - `reset() -> {"queue": deque(), "dout": 0}`
  - `step(state, wr_en, rd_en, din, depth) -> {"queue": deque, "dout": int}`
- The scoreboard MUST call `step()` with argument order exactly
  `state, wr_en, rd_en, din, depth`; `wr_en`/`rd_en` come from the
  transaction's driven input fields and `depth` from the `DEPTH` ConfigDB
  value.  Full/empty are derived inside the model from `len(queue)` and are
  therefore checked implicitly.
- **Argument/return mapping:**
  - transaction `wr_en` -> ref-model `wr_en`; transaction `rd_en` -> `rd_en`;
    transaction `din` -> `din`; ConfigDB `"DEPTH"` -> `depth`.
  - ref-model return `dout` -> checked against `dut.dout` (latency 1);
    model-derived `full`/`empty` -> checked against `dut.full`/`dut.empty`.

## 4. ConfigDB keys (exact — do not invent alternatives)

Everything is shared via `ConfigDB()`.  Keys are set once by the test / tb_top
layer and shared read-only by all components.

| Key             | Python type   | Value/Content                                              |
|-----------------|---------------|------------------------------------------------------------|
| `"dut"`         | cocotb Handle | The top-level handle for module `fifo` (e.g. `dut` passed to `cocotb.test`). |
| `"DATA_WIDTH"`  | `int`         | Elaborated `DATA_WIDTH` parameter of the DUT (default 8).  |
| `"DEPTH"`       | `int`         | Elaborated `DEPTH` parameter of the DUT (default 4).       |
| `"CLK_HALF_PERIOD_NS"` | `int`  | Half-period for the clock generator in ns (default 5).     |
| `"FifoDutHelper"` | `FifoDutHelper` | Optional shared instance of the pin-access helper (see `dut_helper.py`). |

Example usage in later stages:

```python
dut = ConfigDB().get("dut")
data_width = ConfigDB().get("DATA_WIDTH")
depth = ConfigDB().get("DEPTH")
```

`"FifoDutHelper"` is optional sugar; `"dut"` + `"DATA_WIDTH"` + `"DEPTH"` are
sufficient and authoritative.  If the helper is used it must be built as
`FifoDutHelper(ConfigDB().get("dut"), data_width)`.

## 5. Transaction / sequence_item

- **Class:** `FifoTransaction` in `tb/transaction.py`
- **Base class:** `pyuvm.uvm_sequence_item` (`uvm_sequence_item`)
- **Field -> attribute mapping (plain Python attributes, int values):**

| Field        | Attribute | Type  | Width       | Direction of data flow      |
|--------------|-----------|-------|-------------|------------------------------|
| Write enable | `wr_en`   | `int` | 1           | sequence -> driver -> DUT    |
| Read enable  | `rd_en`   | `int` | 1           | sequence -> driver -> DUT    |
| Input data   | `din`     | `int` | `DATA_WIDTH`| sequence -> driver -> DUT    |
| Output data  | `dout`    | `int` | `DATA_WIDTH`| DUT -> monitor -> scoreboard |
| Full flag    | `full`    | `int` | 1           | DUT -> monitor -> scoreboard |
| Empty flag   | `empty`   | `int` | 1           | DUT -> monitor -> scoreboard |
| Cycle stamp  | `dut_cycle` | `int` or `None` | n/a | monitor bookkeeping (sampled edge index) |

Clock/reset are NOT transaction fields.

`FifoTransaction` provides `copy(other)` and `clone()`; the driver stage sets
`wr_en`/`rd_en`/`din`, the monitor stage fills `dout`/`full`/`empty` and
`dut_cycle` before broadcasting on the analysis port.

## 6. Clock and reset semantics

- **Clock name:** `clk`, **posedge**, `dut.clk`.  Clock generation is owned by
  the tb_top stage (a `cocotb.start_soon` coroutine toggling `dut.clk` at
  `CLK_HALF_PERIOD_NS`), with `reset_async_active_low()` provided in
  `dut_helper.py` for the reset pulse.
- **Reset name:** `rst_n`, **active-low**, **asynchronous** (sensitivity list:
  `always_ff @(posedge clk or negedge rst_n)`).  Asserting `rst_n == 0`
  asynchronously clears `wr_ptr`, `rd_ptr`, `count`, and `dout`, so the FIFO
  becomes empty: `empty == 1`, `full == 0`, `dout == 0`.
- The asynchronous (**negedge**) assert path must be exercised and checked
  explicitly by the assertions stage, since the RTL's sensitivity list is
  asynchronous.

## 7. Behavior summary (for reference; NOT to be re-derived)

- On a rising edge a write is accepted when `wr_en==1 && full==0`; it stores
  `din` at `wr_ptr` and advances `wr_ptr` modulo `DEPTH`.
- A read is accepted when `rd_en==1 && empty==0`; it places the oldest entry on
  registered `dout` and advances `rd_ptr` modulo `DEPTH`, with output latency 1.
- A read when empty, or write when full, is ignored.
- When both are accepted in the same cycle both complete and occupancy is
  unchanged.  `count` increments on write-only, decrements on read-only, and is
  unchanged otherwise, staying within `[0, DEPTH]`.
- `full`/`empty` are combinational functions of `count`.

## 8. Cross-stage obligations (hard)

- ONLY Python (cocotb + pyuvm). No SystemVerilog UVM code, no SV interfaces,
  no SV covergroups, no SVA.
- Functional coverage via `cocotb_coverage` (`CoverPoint`/`CoverCross`) through
  the shared `coverage_db`; the earlier stage-3 layer owns the samples.
- Assertions as plain Python checks inside always-running coroutines started
  with `cocotb.start_soon`; they must fail the test immediately when violated.
- A watchdog is required: an always-running coroutine (or a bounded
  `cocotb.triggers.with_timeout` wrapper) that fails the test if it does not
  finish within a bounded number of clock cycles.
- Do not modify RTL, spec, reference model, or the plan.

---

## 9. Stage-2 appendix (stimulus: sequencer, driver, sequences) — additions

These entries are appended by the stimulus stage; they clarify how the
earlier sections are realized and MUST be observed by all later stages.
They do not change any key, pin, field, or value defined above.

### 9.1 ConfigDB access signature (pyuvm API)

The pyuvm library (v2.0 through v5.0, the versions installable for this
project) implements `ConfigDB` with the full signature
`get(context, inst_name, field_name, default=None)` /
`set(context, inst_name, field_name, value)`.  The §4 example
`ConfigDB().get("dut")` is an abbreviation of the *key usage*; every stage
must actually call:

```python
dut = ConfigDB().get(None, "*", "dut")
data_width = ConfigDB().get(None, "*", "DATA_WIDTH")
depth = ConfigDB().get(None, "*", "DEPTH")
helper = ConfigDB().get(None, "*", "FifoDutHelper", default=None)  # optional
```

Keys and value types remain exactly as listed in §4.  The test/tb_top layer
must store them with `ConfigDB().set(None, "*", "<key>", value)`.

### 9.2 Stimulus ownership split

- `tb/driver.py` (`FifoDriver`, a `uvm_driver`) drives the *transaction*
  inputs only: `wr_en`, `rd_en`, `din` (exactly the three driven fields of
  `FifoTransaction`).  It is connected to the sequencer by the agent stage via
  `driver.seq_item_port.connect(sequencer.seq_item_export)`.
- Reset (`rst_n`) is NOT a transaction field, so the *sequences* in
  `tb/sequences.py` drive `dut.rst_n` directly (asynchronous active-low),
  using `setimmediatevalue`, always with `wr_en/rd_en/din` held at 0 while
  reset is asserted.  Sequences access `dut`/`DATA_WIDTH`/`DEPTH` via §4 key
  names.
- `check` actions from the directed scenarios are realized as inline Python
  `assert`s inside the sequences (sampled DUT outputs compared to the plan's
  expected values).  The assertion/scoreboard stages add continuous checking;
  the sequence-local checks do not replace them.

### 9.3 Driver/sequence timing convention (must be preserved by tb_top/tests)

- The driver applies each item for exactly one DUT clock cycle: it aligns to
  a falling edge, drives the item's pins (`setimmediatevalue`), lets the
  following rising edge sample them, returns pins to idle at the next falling
  edge, and only then calls `item_done()`.
- Therefore, when a sequence's `finish_item()` returns, the item has been
  sampled and `dut.dout/dut.full/dut.empty` (and, when reachable, the
  internal `dut.count`) are settled.  Sequences can sample/assert immediately
  afterwards, or after an explicit `wait N` (during which pins are idle, so no
  extra transaction occurs).
- Walls exist between items (pins idle for one cycle before the next item is
  applied); the FIFO semantics of every scenario are unaffected because idle
  cycles are no-ops.

### 9.4 Directed-sequence identity

`tb/sequences.py` defines one `uvm_sequence` subclass per
`directed_test_scenarios` entry.  Each class has a class-level
`SCENARIO_ID` string that exactly equals the plan id:

| Plan id | Sequence class (tb/sequences.py)      |
|---------|----------------------------------------|
| TC001   | `ResetCheckSeq`                        |
| TC002   | `WriteReadBasicSeq`                    |
| TC003   | `WriteUntilFullSeq`                    |
| TC004   | `ReadUntilEmptySeq`                    |
| TC005   | `SimultaneousReadWriteSeq`             |
| TC006   | `SimultaneousReadWriteFullSeq`         |
| TC007   | `SimultaneousReadWriteEmptySeq`        |
| TC008   | `PointerWrapOrderingSeq`               |
| TC009   | `ResetDuringOpSeq`                     |
| TC010   | `BoundaryRoundtripSeq`                 |

Corner-case sequences and `FifoRandomizedSeq` intentionally carry no
`SCENARIO_ID` (they realize the separate `corner_cases` /
`randomized_testing_strategy` plan sections).

### 9.5 Parameterized scenario bodies

The elaborated `DEPTH` and `DATA_WIDTH` (ConfigDB `"DEPTH"` / `"DATA_WIDTH"`)
are authoritative.  Occupancy-relative scenario bodies scale with `DEPTH` so
they are valid at every planned DEPTH (2/4/8); at DEPTH=4 the stimulus
reproduces the plan literally (TC003 fills with 0x0A..0x0D, TC010 alternates
0x00/0xFF, etc.).  TC010's extremal data values scale to `(1<<DATA_WIDTH)-1`
per its plan note.  Internally the testbench may read the RTL `integer
count` as `int(dut.count.value)` (reachability tool-dependent; checks are
skipped when the signal is not exposed).

## 10. Stage-3 appendix (observation: monitor, agent) — additions

These entries are appended by the observation stage; they clarify how the
earlier sections are realized and MUST be observed by all later stages
(env, scoreboard, tests, tb_top).  They do not change any key, pin, field,
or value defined above.

### 10.1 Components

- `tb/monitor.py` defines `FifoMonitor`, a `pyuvm.uvm_monitor` subclass
  named `fifo_monitor`.  It samples the DUT on every rising clock edge and
  publishes one `FifoTransaction` per cycle.
- `tb/agent.py` defines `FifoAgent`, a `pyuvm.uvm_agent` subclass named
  `fifo_agent`.  When active (the default, per pyuvm's `uvm_agent`
  `build_phase`) it creates and owns `FifoSequencer` (`fifo_sequencer`),
  `FifoDriver` (`fifo_driver`) and `FifoMonitor` (`fifo_monitor`); when
  passive it creates only the monitor.

### 10.2 Monitor sampling contract

- `FifoMonitor.run_phase()` loops forever: `await RisingEdge(dut.clk)`,
  then `await ReadOnly()` (cocotb read-only phase: all nonblocking RTL
  updates and the combinational `full`/`empty` re-derivation have settled),
  then samples and broadcasts on `FifoMonitor.ap` — a `uvm_analysis_port`
  named `fifo_analysis_port`.
- "Post-edge values" per §2: `dut.dout` is the latency-1 registered output,
  `dut.full`/`dut.empty` the combinational post-edge flags, and `wr_en` /
  `rd_en` / `din` are the stimulus inputs exactly as the DUT sampled them on
  that edge (the driver holds them for the whole cycle, §9.3).
- One item per edge; fields filled: `wr_en`, `rd_en`, `din`, `dout`,
  `full`, `empty`, and `dut_cycle` (0-based rising-edge index, §5).
- The monitor publishes during reset cycles too; reset is not a transaction
  field (§5), so scoreboard/tests MUST observe `dut.rst_n` directly to
  align their reference-model state across the asynchronous resets injected
  by the sequences.
- Clock/reset are never transaction fields; the monitored edges are merely
  referenced through the shared `dut.clk` handle.

### 10.3 Agent wiring

- `FifoAgent.connect_phase()` exposes `FifoAgent.ap = FifoMonitor.ap` (a
  pass-through of the monitor's analysis port; same object as
  `agent.monitor.ap`) and, when active, connects
  `FifoDriver.seq_item_port.connect(FifoSequencer.seq_item_export)`.
- Later stages (env/scoreboard/tests) may connect consumers to either
  `agent.ap` or `agent.monitor.ap`.  Sequence starts are addressed to
  `agent.sequencer`.
- `is_active` follows the pyuvm `uvm_agent` convention
  (ConfigDB key `is_active` for the agent instance path; default
  `UVM_ACTIVE`).  This stage neither forces nor reads it beyond the default.

### 10.4 ConfigDB retrieval as realized

All stage-3 components resolve shared objects with exactly the §9.1 access
form (keys/config identical to §4):

```python
dut = ConfigDB().get(None, "*", "dut")
data_width = int(ConfigDB().get(None, "*", "DATA_WIDTH"))
depth = int(ConfigDB().get(None, "*", "DEPTH"))
helper = ConfigDB().get(None, "*", "FifoDutHelper", default=None)  # optional
```

Observation for the integration/tb_top stage (do not "fix" it here): stock
pyuvm 3.0.0 (the pinned `requirements.txt` version) rejects wildcard
`inst_name` values on `get()` (`UVMError: "*" is illegal`), while the
testbench's tb_top layer stores under `set(None, "*", "<key>", value)`
per §9.1.  Every stage in this project uses the §9.1 form, so the runtime
that actually executes the testbench must honor the intended wildcard
store/retrieve pairing (e.g. an environment/toolchain shim or a pyuvm
release whose `ConfigDB.get` allows the store-side wildcard).  The
integration stage owns this decision and must keep the §9.1 call form
intact across all components.

## 11. Stage-4 appendix (scoreboard) — additions

These entries are appended by the scoreboard stage; they clarify how the
earlier sections are realized and MUST be observed by all later stages
(env, coverage, assertions, tests, tb_top).  They do not change any key,
pin, field, or value defined above.

### 11.1 Reference model copy

The behavioral oracle is copied verbatim from
`/workspace/benchmarks/fifo/ref_model.py` to
`/workspace/generated/designs/fifo/tb/ref_model.py` so it sits beside the
other `tb/` modules and is imported by simple project-relative
`import ref_model` (no `sys.path` surgery).  The copy is byte-for-byte
identical to the source and MUST NOT be edited; it is the single arithmetic/
behavior source for expected results.  `FifoScoreboard` uses only
`ref_model.reset()` and `ref_model.step(state, wr_en, rd_en, din, depth)`.

### 11.2 Scoreboard component / wiring

- `tb/scoreboard.py` defines `FifoScoreboard`, a `pyuvm.uvm_scoreboard`
  subclass named `fifo_scoreboard`.
- In `build_phase` it creates a `uvm_tlm_analysis_fifo` named
  `fifo_analysis_fifo` and exposes
  `FifoScoreboard.analysis_export = analysis_fifo.analysis_export`.
- `connect_phase` wiring is owned by the env stage:
  `agent.ap.connect(scoreboard.analysis_export)` (equivalently
  `agent.monitor.ap` — they are the same object, §10.3).  The scoreboard
  itself performs no additional connects.
- `run_phase` loops forever: `await analysis_fifo.get()`, read `dut.rst_n`
  directly (post-edge value; put and get share the read-only timestep), and
  advance/check one cycle.

### 11.3 Comparison alignment (single-cycle, registered output)

One monitor item represents exactly one rising edge (CONTRACT.md §10.2).
For a normal (rst_n==1) cycle the scoreboard applies a single
`ref_model.step(state, wr_en, rd_en, din, DEPTH)` producing `new_state` and
compares (same item):
- `new_state["dout"]`               vs `item.dout`   (latency-1 registered out)
- `len(new_state["queue"])==DEPTH` vs `item.full`
- `len(new_state["queue"])==0`     vs `item.empty`
- `len(new_state["queue"])`        vs `int(dut.count.value)` — only when the
  internal `count` signal is reachable; check is skipped otherwise (§9.5)
Because the predictor always pops the oldest queued entry, matching `dout`
is itself the strict FIFO-order / no-drop / no-dup check.

### 11.4 Reset handling in the scoreboard

Reset is NOT a transaction field (§5, §10.2).  When `dut.rst_n==0` the
scoreboard re-arms the predictor with `ref_model.reset()` and then checks
the same outputs (expected empty=1, full=0, dout=0) against the reset-cycle
item.  Because the monitor publishes during reset cycles too, this keeps the
predictor aligned across the asynchronous active-low resets injected by the
sequences (TC001, TC009, etc.).  On the edge after reset is released
(rst_n==1), the predictor advances normally from the reset state.

### 11.5 Failure reporting / pass criteria

Every mismatch is logged at error severity with: the cycle (`item.dut_cycle`),
the operation in flight (`wr_en`/`rd_en`/`din`), expected vs actual
`dout`/`full`/`empty`/`count`, the expected queue contents, and a short trace
of recent operations.  A running mismatch count is kept; `report_phase`
summarizes items checked / passed / mismatches / resets observed.  The env or
tests stage is responsible for failing the simulation when the mismatch count
is nonzero (and the assertions stage owns the always-on watchdog).  The
scoreboard intentionally does not `assert` (so it can collect all mismatches);
failure propagation is owned by later stages per this appendix.

---

## 12. Stage 5 — Functional coverage and always-on assertions (COVERAGE & ASSERTIONS)

Stage 5 adds `tb/coverage.py` and `tb/assertions.py`.  It generates **no**
SystemVerilog and no additional components; the env/tests/tb_top stages wire
and launch these modules.  This appendix documents what stage 5 delivers and
the conventions later stages MUST honor when integrating it.

### 12.1 `tb/coverage.py` — functional coverage (replaces SV covergroups)

- Implements the plan `functional_coverage` section with
  `cocotb-coverage` (`CoverPoint`/`CoverCross` registered in the shared
  `cocotb_coverage.coverage.coverage_db`).
- `build_fifo_coverage(depth, data_width)` registers three covergroups and
  returns `(sample_operation, sample_occupancy, sample_data)`; it is
  idempotent (cocotb-coverage re-uses existing `coverage_db` entries).
- Covergroup/bins/cross names match the plan exactly:
  - `fifo_operation_cg` — `wr_en_bins` (wr_idle/wr_active),
    `rd_en_bins` (rd_idle/rd_active), `full_bins` (not_full/is_full),
    `empty_bins` (not_empty/is_empty); crosses `wr_rd_combos`,
    `write_while_full`, `read_while_empty`, `op_against_flags`.
  - `fifo_occupancy_cg` — `count_levels` (empty_level=0, one_entry=1,
    mid_level=DEPTH/2, near_full_level=DEPTH-1, full_level=DEPTH), no
    crosses.  Bin **values** are deduplicated (first label wins) so the
    cover point is valid for every planned DEPTH (2/4/8).
  - `fifo_data_cg` — `write_data_bins` (data_zero=0, data_max=2^DATA_WIDTH-1),
    `read_data_bins` (data_zero_out/data_max_out), cross
    `boundary_data_roundtrip`.
- `FifoCoverage(uvm_subscriber)` named `fifo_coverage`: `build_phase` reads
  `ConfigDB().get(None, "*", "dut"|"DATA_WIDTH"|"DEPTH")`, `write(tr)` builds
  the sample payload `{wr_en, rd_en, din, dout, full, empty, count}` from one
  monitor item (post-edge values) and samples all three covergroups,
  `report_phase` prints `coverage_db.report_coverage(...)` and best-effort
  exports `fifo_coverage.yml`/`fifo_coverage.xml`.
- **Count sampling rule (§9.5):** `count` comes from the internal RTL
  `integer count` via `int(dut.count.value)` when `dut.count` is exposed by
  the simulator; otherwise/on un-resolvable values the sample is `None` and
  simply misses every occupancy bin (never a false failure).

### 12.2 `tb/assertions.py` — always-on Python checkers (replaces SVA)

- Implements the plan `useful_assertions` seven items as plain-`assert`
  coroutines (no SVA, no interface) launched with `cocotb.start_soon`
  (cocotb 1.9.2), each synchronized on `RisingEdge(dut.clk)` +
  `ReadOnly()` and sampling the exact pin names of §2.  An `AssertionError`
  from any checker task fails the cocotb test immediately.
- Checker -> plan item: `check_reset_clean_state`, `check_no_overflow`,
  `check_no_underflow`, `check_occupancy_bounds`,
  `check_flags_mutually_exclusive`, `check_count_update_consistency`,
  `check_fifo_ordering`.
- `start_assertions(dut=None, depth=None, data_width=None)` resolves the
  ConfigDB keys of §4/§9.1 (wildcard access form) and returns the
  `FifoAssertions` instance (`.tasks` = spawned Tasks).  Exactly-once start.
- **Timing semantics (MUST NOT be re-derived):** the checker samples at
  cycle *k* hold the post-edge state after edge *k*; the DUT decided edge *k*
  acceptance with the *pre-edge* flags, i.e. the post-edge `full`/`empty`
  sampled at cycle *k-1*.  Hence an edge-*k* write is accepted iff
  `wr_en_k && !full_{k-1}`, a read iff `rd_en_k && !empty_{k-1}`, and
  `count_k == count_{k-1} + (wr_en_k && !full_{k-1}) - (rd_en_k && !empty_{k-1})`;
  `no_overflow`/`no_underflow` compare `count_k` against `count_{k-1}` when
  `full_{k-1}&&wr_en_k` / `empty_{k-1}&&rd_en_k` respectively.
- `check_fifo_ordering` advances the shared reference model with the exact
  call form `ref_model.step(state, wr_en, rd_en, din, depth)` (§3, §11) and
  compares `state["dout"]` with the sampled post-edge `dout`; `rst_n==0`
  re-arms with `ref_model.reset()` and requires `dout==0` (ordering implies
  strict FIFO/no-drop/no-dup, §11.3).
- **Count reachability (§9.5):** the four count-based checks skip their
  check for a cycle when `dut.count` is not reachable or its value is
  un-resolvable (one warning logged); all other checks always run.
  Un-resolvable pins (start-of-simulation X/Z) are skipped, never failed.

### 12.3 Watchdog (bounded run, plan rule)

- `FifoWatchdog` counts DUT rising edges and raises `AssertionError` if the
  `done` `cocotb.triggers.Event` is not set within `max_cycles`; this fails a
  hung simulation.
- `start_watchdog(dut, max_cycles, done=None, description=...) -> (task, done)`
  returns the spawned Task and the `done` Event; the test/tb_top layer MUST
  call `done.set()` when the test body finishes (e.g. in `finally`), allowing
  the watchdog to exit early.  `watchdog_event_for(max_cycles, ...)` is a
  ConfigDB-resolving one-shot convenience.

### 12.4 Ownership and pass/fail split (multi-stage)

- Stage 5 owns: coverage definition/sampling/report, always-on assertion
  checkers, and the watchdog.  It does NOT run the simulation, connect
  `agent.ap`, or declare the test.
- Env/tests/tb_top stage owns: instantiating `FifoCoverage`, connecting
  `agent.ap.connect(fifo_coverage.analysis_export)` (§10.3), calling
  `start_assertions()` and `start_watchdog(...)`, setting `done`, and failing
  the simulation on scoreboard mismatch count / assertion failure.
- Stage-5 output checkpoint: `checkpoints/uvm_coverage_assertions.done`.