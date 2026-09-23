# CONTRACT — SHA-256 cocotb + pyuvm verification environment

Stage 1 of 6 (CONTRACT) of the CHIA cocotb+pyuvm environment generator.

**This file is the authoritative convention record for every later stage
(stimulus, monitor/scoreboard, coverage/assertions, env/test, integration).**
Later stages MUST read it instead of re-deriving pin names, widths,
transaction fields, or ConfigDB keys from the RTL or plan. If a later stage
believes something here is wrong, it may extend this file minimally (append,
do not rewrite) and explain why — it must not silently diverge.

Generated artifact location:
`/workspace/generated/designs/sha256_benchmark_corrupted/tb/`

---

## 1. Stack / version contract (hard)

- Testbench is implemented entirely in Python: **Cocotb 2.1.0** + **pyuvm 5.0.0**.
- No SystemVerilog UVM, no SV `interface`, no SV covergroups/SVA. The only
  SystemVerilog in the project is the DUT RTL (`sha256.sv`), which is never
  modified or duplicated.
- Public Cocotb 2.1.0 APIs only:
  - triggers `RisingEdge`, `FallingEdge`, `ClockCycles`, `Timer`,
    `Combine`, `with_timeout` (`cocotb.triggers`)
  - `cocotb.clock.Clock(signal, period, unit="ns")`, `clock.start()`
  - `cocotb.start_soon(...)` / `await`
  - read: `int(dut.<pin>.value)`; write: `dut.<pin>.value = <int>`.
    Never `int(dut.<pin>)` (deprecated) and never import
    `cocotb.handle.ModifiableObject`.
- pyuvm classes used: `uvm_sequence_item`, `uvm_sequence`, `uvm_sequencer`,
  `uvm_driver`, `uvm_monitor`, `uvm_agent`, `uvm_scoreboard`, `uvm_env`,
  `uvm_test`, `uvm_analysis_port`, `uvm_tlm_analysis_fifo`, `ConfigDB`.
  pyuvm 5.0.0 has no `uvm_object_utils`/field-automation macros — all fields
  are plain Python attributes.
- Functional coverage uses `cocotb-coverage`
  (`cocotb_coverage.coverage.CoverPoint` / `CoverCross`, sampled via the
  shared `coverage_db`). Assertions are plain Python `assert`/raise checks
  inside always-running coroutines started with `cocotb.start_soon`. A
  deterministic watchdog guards the whole test (bounded cycles / `with_timeout`)
  and must NOT replace functional completion checks.

## 2. Top module and file layout

- Top module name: `sha256` (file
  `benchmarks/sha256_benchmark_corrupted/sha256.sv`).
- No module parameters. (`K` in `rtl_info.json` is the RTL's internal
  `localparam` round-constant array, not a top-level parameter; do not
  parameterize drives.)
- Generated TB files are **flat Python modules** in this `tb/` directory (the
  sim worker adds `tb/` to `PYTHONPATH`, so modules import by bare name, e.g.
  `from sha256_transaction import Sha256Transaction`). There is deliberately
  **no** `__init__.py`; modules are top-level.
- The cocotb entry point is a single flat module `test_top.py` in this
  directory (fixed name required by the sim worker).

## 3. DUT pin map (authoritative)

Every pin is accessed through the cocotb `dut` handle. Widths and directions
come from `rtl_info.json` and the verification plan and match `sha256.sv`.

| Pin      | Direction | Width | Access expression              | Notes |
|----------|-----------|-------|--------------------------------|-------|
| `clk`    | input     | 1     | `dut.clk`                      | Rising-edge clock for all sequential logic. |
| `rst_n`  | input     | 1     | `dut.rst_n`                    | Active-low **asynchronous** reset. |
| `start`  | input     | 1     | `dut.start`                    | Pulse to begin a compression; `block` is captured on the same cycle. NOT gated by `busy` (RTL restarts the transaction on a start-while-busy). |
| `block`  | input     | 512   | `dut.block`                    | Pre-padded message block, big-endian word order: `block[511:480]` = first 32-bit word ... `block[31:0]` = last. As an int, its MSB is `block[511]`. |
| `done`   | output    | 1     | `dut.done`                     | **Corrupted RTL drives `done = 1` continuously**  after reset (DISC-001); it is NOT a completion pulse. Never use `done` as a completion indicator. |
| `digest` | output    | 256   | `dut.digest`                   | `H0||H1||...||H7`, each 32-bit word big-endian. As an int, `digest[255:224]` = H0. |

Read/write conventions (Cocotb 2.1.0):
- Drive: `dut.start.value = 1`, `dut.block.value = <512-bit int>`,
  `dut.rst_n.value = 0/1`.
- Sample: `start_val = int(dut.start.value)`,
  `digest_val = int(dut.digest.value)`.

## 4. Transaction / sequence_item

Module: `sha256_transaction.py`
Class: `Sha256Transaction(uvm_sequence_item)`

All fields are plain Python attributes. Widths are enforced by masking in
`__init__` (`_mask`).

| Field           | Type | Width | Role |
|-----------------|------|-------|------|
| `start`         | int  | 1     | DUT input (driven by stimulus; 0/1). |
| `block`         | int  | 512   | DUT input (the 512-bit pre-padded block, big-endian word order as an int). |
| `done`          | int  | 1     | DUT output (observed by the monitor from `dut.done`). |
| `digest`        | int  | 256   | DUT output (observed by the monitor from `dut.digest`). |
| `txn_id`        | int  | —     | Metadata (NOT a DUT pin): monotonic transaction id for in-order scoreboard matching and error reporting. |
| `latency_cycles`| int  | —     | Metadata (NOT a DUT pin): measured start→completion cycle count for fixed-latency checks. |

Convenience (no new fields):
- `Sha256Transaction.block_bytes` → `block.to_bytes(64, "big")`, the exact
  input format of the golden reference `block_to_digest(bytes)`.
- `Sha256Transaction.digest_bytes` → `digest.to_bytes(32, "big")`.
- `convert2string()` gives a compact single-line report (txn id, block,
  digest, latency).

Sequence items are created directly in sequences (no factory
`create_by_name`); the class has no required recording/savable semantics.

## 5. ConfigDB keys (exact, shared between all components)

Both keys are set ONCE in `test_top.py`, before the pyuvm tree is built
(e.g. in the test's `build_phase` or immediately before
`ConfigDB().set(...)`; the pyuvm pattern is
`ConfigDB().set(None, "*", key, value)`, read with
`ConfigDB().get(None, "*", key)`).

| Key            | Value type                                       | Set by                     | Read by |
|----------------|--------------------------------------------------|----------------------------|---------|
| `"dut"`        | cocotb top-level DUT handle (the `dut` argument passed to the cocotb test entry point). Do NOT import/assume `cocotb.handle.ModifiableObject`. | `test_top.py` | env, driver, monitor, scoreboard, assertions, coverage |
| `"sha256_pins"`| `Sha256Pins` instance (module `sha256_pins.py`) wrapping `dut`. | `test_top.py` (constructed as `Sha256Pins(dut)`) | driver, monitor, env, test |

No other keys may be invented; if a later stage needs more shared objects it
must extend this file with a documented key first.

Example set/get:

```python
from pyuvm import ConfigDB
ConfigDB().set(None, "*", "dut", dut)
ConfigDB().set(None, "*", "sha256_pins", Sha256Pins(dut))
pins = ConfigDB().get(None, "*", "sha256_pins")
```

## 6. Clock and reset semantics

- Clock: `dut.clk`, positive-edge (posedge) clock for all sequential logic.
  Default period: `CLK_PERIOD_NS = 10.0` ns (constant in `sha256_pins.py`;
  `make_clock(dut)` builds the `cocotb.clock.Clock`, the test calls
  `clock.start()`).
- Reset: `dut.rst_n`, **active-low**, **asynchronous** (RTL sensitivity
  `@(posedge clk or negedge rst_n)`):
  - asserted when `rst_n == 0`,
  - deasserted when `rst_n == 1`,
  - `Sha256Pins.reset_dut(hold_cycles=5)` asserts low, holds N rising edges,
    then deasserts (async release; caller re-synchronizes on `clk`).
- Reset state (RTL behavior): `done=1` (DISC-001 — spec wanted `done=0`),
  `digest=0`, `busy=0`, `round=0`, H0..H7 = SHA-256 IVs, a..h and W = 0.

## 7. Timing / latency contract (completion model)

- The reference model performs one SHA-256 round per cycle → expected latency
  = 64 cycles. The RTL is corrupted (round increments by 2, completion check
  `round == 62` never true, `busy` stuck high, DISC-008/013/014), so **the
  environment must determine completion by fixed cycle count, never by the
  `done` pin**:
  - `EXPECTED_LATENCY_CYCLES = 64`
  - `COMPLETION_MARGIN_CYCLES = 70` — wait this many cycles after the start
    edge before sampling `digest` for scoreboard comparison.
  - `WATCHDOG_MARGIN_CYCLES = 500` — global run bound for the deterministic
    watchdog / `with_timeout` wrapper.
- Constants live in `sha256_pins.py` and are the single source of truth.
- `digest` holds its last value until reset or a new transaction; `done`
  stays 1 throughout. Directed scenarios in the plan follow this model
  (start → wait 70 → sample).

## 8. Functional behavior / reference model

- Golden reference: `benchmarks/sha256_benchmark_corrupted/sha256_reference_model.py`,
  function `block_to_digest(block: bytes) -> bytes` (hashlib SHA-256). It
  validates canonical one-block padding and returns `sha256(message).digest()`.
- The scoreboard MUST use this exact function (through its module) — never
  reimplement SHA-256 in the TB.
- Known fatal RTL bugs (drives the verification design): done not a pulse
  (DISC-001), wrong Ch/Maj/sigma constants and K indexing (DISC-002..009),
  wrong t2/state update (DISC-010/011), wrong digest feed-forward
  (DISC-012), busy never released (DISC-013), round seq 1,3,5,... and no
  completion (DISC-008/014), block word order/endianness reversal on load
  (DISC-015), `start` not gated by `busy` (DISC-017). Every generated test
  must therefore expect digest mismatches vs. the reference for legal
  blocks — the scoreboard's job is to *report* them (transaction id, block,
  expected, actual, cycle), and coverage/assertions must still check the
  structural contract (start capture, fixed-latency sampling, reset state,
  done=1 continuity).

## 9. Directed scenario / integrity conventions (locked)

- Every planned `directed_test_scenarios[].id` is implemented exactly once
  by a sequence class carrying `SCENARIO_ID = "<exact plan id>"`.
- Scenario ids (authoritative, from the verification plan):
  - `reset_initialization`
  - `empty_message`
  - `single_byte_a`
  - `abc_message`
  - `hello_world`
  - `quick_brown_fox`
  - `back_to_back_transactions`
  - `start_while_busy_restarts`
  - `done_behavior_continuous`
- Corner-case and randomized sequences get NO scenario id.
- Reference-model argument order: `block_to_digest(block_bytes)`; return maps
  directly to the checked DUT output `digest`.

## 10. Files written in this stage

- `sha256_transaction.py` — `Sha256Transaction(uvm_sequence_item)`.
- `sha256_pins.py` — `Sha256Pins` pin-access helper + structural constants.
- `CONTRACT.md` — this file.

## 11. Stage-2 STIMULUS additions (appended by stage 2; no §1–§9 changes)

Files added in this stage (flat Python modules in this `tb/` directory, same
import convention as stage 1):

- `sha256_sequencer.py` — `Sha256Sequencer(uvm_sequencer)`. No custom
  behavior; the agent connects `sequencer.seq_item_export` to
  `driver.seq_item_port`.
- `sha256_driver.py` — `Sha256Driver(uvm_driver)`. Reads the shared
  `"sha256_pins"` ConfigDB key in `build_phase`.
- `sha256_sequences.py` — all stimulus classes:
  - 9 directed sequences, one per `directed_test_scenarios[].id`, each
    declaring `SCENARIO_ID = "<exact plan id>"` (see §9). The module-level
    `DIRECTED_SCENARIO_SEQUENCES` registry maps id → class and
    `validate_scenario_ids()` asserts id-set equality and uniqueness.
  - 6 corner-case sequences and 1 randomized sequence (`corner_cases`,
    `randomized_testing_strategy`); **no** `SCENARIO_ID` on these.
  - `canonical_one_block_pad(message)` — canonical SHA-256 one-block
    padding → 512-bit int, byte-identical to the golden reference's
    `pad_one_block()`.

Driver protocol (documented convention, used by all sequences):

- Each item with `start == 1` becomes exactly ONE one-cycle `start` pulse
  with `block` held stable across the sampling edge (this satisfies the
  `start_deasserted_same_cycle` corner case). `start == 0` items are
  no-drive items.
- Inputs are changed on/just after falling edges of `dut.clk` so every
  value is settled half a clock period before the rising edge that samples
  it (no delta-cycle race at the RTL's sampling edge).
- Completion is never inferred from the broken `done` pin; sequences wait
  `COMPLETION_MARGIN_CYCLES` (70) after a start and the global watchdog
  bound stays `WATCHDOG_MARGIN_CYCLES` (§7).

Block-construction divergence (required): every `block` hex literal embedded
in the planning documents is corrupted (each is wider than 512 bits and fails
canonical one-block padding), while the associated scenario *descriptions*
state the intended message/length unambiguously (e.g. "Padded block for abc
(3 bytes = 24 bits = 0x18 ...)"). Stage 2 therefore builds directed-scenario
blocks programmatically with `canonical_one_block_pad()` from the described
message bytes; the reference-model `block_to_digest` then validates them.
Plan scenario ids, expected digests, priorities, and all other plan content
are preserved unchanged. Block construction is stimulus-side data creation
only and is not a SHA-256 digest computation (that stays exclusively in the
reference model).

No new ConfigDB keys are introduced by this stage (still only `"dut"` and
`"sha256_pins"`, §5).

## 12. Stage-3 OBSERVATION additions (appended by stage 3; no §1–§11 changes)

Files added in this stage (flat Python modules in this `tb/` directory, same
import convention as stage 1):

- `sha256_monitor.py` — `Sha256Monitor(uvm_monitor)`. Reads the shared
  `"sha256_pins"` ConfigDB key in `build_phase` (exact key from §5; never
  touches the raw `dut`) and builds `ap = uvm_analysis_port("ap", self)`.
  `run_phase` is an `async def` synchronized on `RisingEdge(dut.clk)`
  (§6/§7). A transaction begins on the first rising edge with `start == 1`
  whose previous rising edge had `start == 0` (0→1 edge detection ⇒ one
  transaction per start pulse regardless of pulse width); `block` is
  captured on that same edge. A completion observer is spawned per start
  pulse with `cocotb.start_soon` (public Cocotb 2.1.0 API), which awaits
  `ClockCycles(clk, COMPLETION_MARGIN_CYCLES)` (§7), samples `done`/`digest`,
  sets `latency_cycles = COMPLETION_MARGIN_CYCLES`, and publishes exactly
  one `Sha256Transaction` (monotonic `txn_id`, in-order) via
  `ap.write(txn)`. Completion is purely fixed-cycle — the broken `done` pin
  is never used to infer completion (DISC-001/DISC-013, §8). Observers
  finish in start order, so back-to-back and start-while-busy restarts are
  observed without loss. X/Z pin samples are logged and sampled as 0
  defensively (the `int(dut.<pin>.value)` read path of §3 is still used;
  this only guards time-zero/unresolved sampling).
- `sha256_agent.py` — `Sha256Agent(uvm_agent)`. `build_phase` creates
  `sequencer` = `Sha256Sequencer("sequencer", self)`, `driver` =
  `Sha256Driver("driver", self)`, `monitor` =
  `Sha256Monitor("monitor", self)`. `connect_phase` connects
  `driver.seq_item_port` to `sequencer.seq_item_export` (§11) and sets
  `self.ap = self.monitor.ap`. `ap` is intentionally the **same object** as
  the monitor's analysis port: pyuvm 5.0.0 broadcasts `ap.write(datum)` to
  `ap.subscribers` and `ap.connect(export)` appends `export` to that list,
  so a downstream component subscribes with
  `agent.ap.connect(<fifo_analysis_export>)` and directly receives the
  monitor's transactions. Component attributes for later stages:
  `agent.sequencer`, `agent.driver`, `agent.monitor`, `agent.ap`.

No new ConfigDB keys are introduced by this stage (still only `"dut"` and
`"sha256_pins"`, §5).

## 13. RUNTIME CORRECTION: ConfigDB get() form (appended by stage 3)

Verified directly against the pinned `pyuvm==5.0.0` sources (the project
cache used by the sim worker): `ConfigDB().get(None, "*", key)` **raises
`UVMError` at runtime** — `get()` forbids wildcards in the requesting
`inst_name` (`legal_chars` is alphanumerics + `_`/`.`; the `"*"` glob is
only legal in the *stored* key on `set()`). The §5 example
`ConfigDB().get(None, "*", key)` is therefore a documentation bug; the
§5 keys, the `set(None, "*", key, value)` storage form, and the semantics
(globbing the stored `"*"` path via `fnmatch`) are all unchanged and
correct.

Correct retrieval form that matches the stored `"*"` path, used by every
component in this environment (driver, monitor, sequences, and later
stages):

```python
from pyuvm import ConfigDB
ConfigDB().set(None, "*", "dut", dut)
ConfigDB().set(None, "*", "sha256_pins", Sha256Pins(dut))
pins = ConfigDB().get(None, "", "sha256_pins")   # requesting root path ""
```

Rationale: with `context=None`, an empty/absent requesting `inst_name`
resolves to the root component path `""`, which `fnmatch`-matches the
stored glob `"*"`. `get(None, None, ...)` raises `TypeError` and
`get(None, "*", ...)` raises `UVMError`; do not use either.

Impact on earlier stages: stage-2 `sha256_driver.py` and
`sha256_sequences.py` used the broken `get(None, "*", ...)` form; their
call sites were corrected (three one-line changes, `"*"` -> `""`, with no
behavioral change). No new ConfigDB keys were introduced.

## 14. Stage-4 SCOREBOARD additions (appended by stage 4; no §1–§13 changes)

Files added in this stage (flat Python modules in this `tb/` directory,
same import convention as stage 1):

- `sha256_scoreboard.py` — `Sha256Scoreboard(uvm_scoreboard)`, the
  plan's `scoreboard_reference_model_strategy` implementation.
- `sha256_reference_model.py` — **verbatim copy** of the golden reference
  `benchmarks/sha256_benchmark_corrupted/sha256_reference_model.py`
  (byte-identical, `md5sum`-checked at copy time).  Copied so the TB
  imports the reference by bare name under the flat-module convention and
  never depends on runtime filesystem paths; the benchmark file remains
  the canonical source (re-copy if it ever changes).  `block_to_digest`
  is the ONLY digest computation in the environment — nothing in the TB
  reimplements SHA-256 (§8 holds unchanged).

Scoreboard behavior (implements `scoreboard_reference_model_strategy`):

- `build_phase` reads the shared `"dut"` ConfigDB key (§5; the table
  lists the scoreboard as a `"dut"` consumer) and builds
  `self.fifo = uvm_tlm_analysis_fifo("sha256_sb_fifo", self)` (unbounded).
- Wiring (done by the ENV in its connect phase, stage 5): subscribe the
  agent/monitor analysis port with `scoreboard.connect_monitor(agent.ap)`,
  which performs `agent.ap.connect(scoreboard.fifo.analysis_export)`
  under pyuvm's §12 broadcast model.  `connect_monitor(...)` is the
  documented, stable entry point (`fifo.analysis_export` stays public).
- `run_phase`: infinite loop consuming `self.fifo.get_peek_export.get()`
  (blocking, in-order — the monitor publishes in start order, §12).  Per
  transaction it:
  1. enforces txn_id contiguity (`txn.txn_id` must be the next expected
     id); any gap/duplicate/reorder is an `order_error` — the scoreboard
     side of the "no extra/missing transactions" pass criterion;
  2. predicts the expected digest with `block_to_digest(txn.block_bytes)`
     (reference model, §8) and compares it to `txn.digest_bytes` — this
     applies the fixed input/output cycle relationship of §7 (digest
     sampled `COMPLETION_MARGIN_CYCLES` after the start edge);
  3. reports (logger.error + counters) transaction id, input block
     (`0x{block:0128x}`), expected digest, actual digest, and cycle of
     mismatch — cycle from `cocotb.utils.get_sim_time("ps")` /
     `CLK_PERIOD_NS` plus `txn.latency_cycles` (the sample offset).
- A reference-model `ValueError` (block fails canonical one-block
  padding) is reported as `invalid_block_count` (ungradable); the
  transaction is not compared.
- `done` is consumed as a data field; the scoreboard logs a *warning*
  if `done != 1`, but strict done-continuity (DISC-001) is asserted by
  the assertions stage, not the scoreboard (§8).

Public counters (read by the env/test stage and `get_summary()` /
`get_summary_dict()`): `txn_count`, `match_count`, `mismatch_count`,
`invalid_block_count`, `order_error_count`, `error_count`
(= order + invalid).  `run_phase` and all grading are plain Python on
public Cocotb 2.1.0 APIs (`get_sim_time`); no SystemVerilog anywhere.

**Grading semantic (locked):** for the corrupted RTL a digest mismatch
vs. the golden reference is EXPECTED (DISC-001..DISC-017, §8), so
`mismatch_count > 0` is a *catch report*, not by itself a test failure —
the env/test stage (stage 5) grades the plan's pass criteria from the
counters above, treating `order_error_count`/`invalid_block_count` as real
contract violations.

No new ConfigDB keys are introduced by this stage (still only `"dut"`
and `"sha256_pins"`, §5).

## 15. Stage-5 COVERAGE & ASSERTIONS additions (appended by stage 5; no §1–§14 changes)

Files added in this stage (flat Python modules in this `tb/` directory, same
import convention as stage 1):

- `sha256_coverage.py` — functional coverage with `cocotb-coverage`
  (pinned: `cocotb-coverage==1.2.0`, installed with `--no-deps`; it must
  run against the pinned Cocotb `2.1.0` and imports **no** cocotb symbols,
  verified OK). Coverage must be recorded via the shared module-level
  `coverage_db` (`from cocotb_coverage.coverage import coverage_db`) so the
  env/tests stage can evaluate it at test end; standalone
  `coverage_db_accumulating` instances are forbidden.
  - `message_length_cg` (module-level `@CoverGroup` instance
    `message_length_cg`): `msg_len_bits` CoverPoint sampling
    `block[63:0]` via `int(Sha256Pins.read_block(cfg)) & 0xFFFFFFFFFFFFFFFF`
    (async), with labeled bins `zero_len[0,0]`, `short_len[1,128]`,
    `medium_len[129,256]`, `long_len[257,384]`, `max_len[385,440]` —
    bin label contract exactly as in the verification plan.
  - `control_signals_cg`: coverpoints `start_pulse` and `done_pulse` each
    binned `asserted[1,1]` / `deasserted[0,0]`, plus paired cross
    `start_done_cross` over `start` × `done` with all four bins.
    **Decorator ordering (verified empirically, Cocotb 2.1.0 +
    cocotb-coverage 1.2.0):** CoverPoints are declared ABOVE the cross in
    the source and the cross is declared BELOW (innermost decorator), so
    the cross object is constructed last and its `sample()` call sees the
    points' fresh `_new_hits`. Keep this ordering; moving the cross above
    the points breaks cross correlation.
  - Module API for later stages: `start_coverage()`
    (`cocotb.start_soon` on a foreground sampler that awaits
    `RisingEdge(pins.dut.clk)`, samples both covergroups, and disarms via
    a `Forever` object from `cocotb.triggers`), and `report_coverage()`
    (`coverage_db.report_coverage(detail=False)`), exposed under
    `if __name__ == "__main__":` for standalone runs. No `test_` names and
    no pytest-style fixtures here.
- `sha256_assertions.py` — assertions ported to the plan's SVA specs as
  **continuous Python checker coroutines** (no SystemVerilog anywhere).
  - Class `Sha256Assertions(pins: Sha256Pins)`; `start()` runs the
    checkers with `cocotb.start_soon` (public Cocotb 2.1.0 API; no
    deprecated `cocotb.fork`).
  - `reset_sets_done_high (severity ERROR)`: on every `RisingEdge(clk)`
    outside reset (`rst_n == 1`), assert `done == 1`.
  - `digest_holds_until_next (severity ERROR)`: `completion_cycle` armed at
    `start` 0→1 edge + `COMPLETION_MARGIN_CYCLES` (70); on any edge with
    `cycle > completion_cycle`, first sample is allowed to change (digest
    set), any further change is a violation; reset clears armed state.
  - `transaction_completes_within_latency (severity ERROR)`: per start
    edge, a window `[start+64, start+70]` (`EXPECTED_LATENCY_CYCLES`..
    `COMPLETION_MARGIN_CYCLES`) must see `digest != 0`; a start-while-busy
    restart opens an additional window; edges after `start+71` with an
    unsatisfied window fire the violation message, which names the
    offending transaction start cycle.
  - Violations call `_fail(severity, message)` which logs `result.error`
    and raises `AssertionError` immediately (kills the coroutine and fails
    the test with `TEST FAIL via assertion error`), then the aggregator
    `_FAILED` flag; each violation increments `failure_count`. A
    simulation-time watchdog coroutine (`check_watchdog`, started by
    `start_watchdog()`) fires if the run exceeds
    `WATCHDOG_MARGIN_CYCLES` (500), with `disarm_watchdog()` to stop it
    when the sequence program completes.
- `results/stage5_tests/stage5_unit_tests.py` — simulator-free unit tests
  for the pure per-edge decision functions and coverage registration
  (run with plain `python3`, no pytest/cocotb). ALL 30 checks PASS.

**Design contract (locked):** checkers must fail the FIRST offending
concern immediately (fail-fast), so on this corrupted RTL
`transaction_completes_within_latency` is **expected to fire** ~72 cycles
after the first `start` (digest is only assigned under `round==62`, which
is never reached — the digest stays 0 on this RTL; DISC-008/014, §8).
This is an intended catch report, and the verdict still goes through the
scoreboard counters (§14) and the assertions counter
`assertion_failure_count`. `ConfigDB` is not touched by this stage (the
`"dut"`/`"sha256_pins"` consumers of §5 are unchanged); coverage and
assertions read `Sha256Pins` from nothing but their constructor argument
and the class's dedicated reference to the DUT handle. pip install note:
`pip install cocotb-coverage==1.2.0` without `--no-deps` downgrades
cocotb to `1.9.2`; the pinned Cocotb `2.1.0` must then be reinstalled
with `pip install --force-reinstall --no-deps cocotb==2.1.0`.

No new ConfigDB keys are introduced by this stage (still only `"dut"`
and `"sha256_pins"`, §5).

---

## 16. Stage 6 — ENV / TEST / INTEGRATION (locked)

This stage assembles the environment, test classes, cocotb entry point,
Makefile and generation manifest. Decisions recorded here are authoritative
for the final generated environment.

**Files added (all in `tb/`):**
- `sha256_env.py` — `Sha256Env(uvm_env)`: `build_phase` builds
  `Sha256Agent("sha256_agent", self)` + `Sha256Scoreboard("sha256_scoreboard",
  self)` then starts the coverage sampler and the assertion checker
  controller via `self.coverage = start_coverage()` and
  `self.assertions = start_assertions()` (public `cocotb.start_soon`,
  §15); `connect_phase` wires `self.scoreboard.connect_monitor(self.agent.ap)`
  (§12/§14 broadcast model). Exposes `agent`, `scoreboard`, `coverage`,
  `assertions`.
- `sha256_test.py` — `Sha256BaseTest(uvm_test)` plus **11 runnable
  subclasses**: the 9 directed tests named
  `Sha256<Scenario>Test` (each with a `@staticmethod get_sequence_class()`
  returning the corresponding `Sha256<Scenario>Sequence` **class symbol** —
  never a string — per plan `directed_test_scenarios`, §9), plus
  `Sha256CornerTest` (drives all six plan corner sequences, §9) and
  `Sha256RandomizedTest`. `DIRECTED_SCENARIO_TESTS` maps the 9 exact plan
  ids to the test classes.
- `test_top.py` — single `@cocotb.test()` `sha256_tb_top`: builds
  `Sha256Pins`, drives pre-clock idle (start=0, block=0, §3/§11), starts the
  master clock (`make_clock(dut)` + `clock.start()`, §6), applies the
  active-low asynchronous reset (3 rising edges held, §6), sets exactly the
  two ConfigDB keys `"dut"` / `"sha256_pins"` via the documented
  `ConfigDB().set(None, "*", key, value)` storage form (§5), and awaits
  `uvm_root().run_test(test_name, keep_singletons=True)` where `test_name`
  comes from the `UVM_TESTNAME` environment variable (worker sets it per
  manifest test class; fallback `Sha256ResetInitializationTest`).
- `Makefile` — cocotb flow (SIM=verilator, TOPLEVEL=sha256, MODULE=test_top,
  `VERILOG_SOURCES=/workspace/benchmarks/sha256_benchmark_corrupted/sha256.sv`,
  `COMPILE_ARGS += --timing -Wno-fatal -Wno-WIDTH -Wno-CASEINCOMPLETE
  -Wno-UNOPTFLAT -j 0`, `UVM_TESTNAME ?= Sha256ResetInitializationTest`,
  `include $(shell cocotb-config --makefiles)/Makefile.sim`).
- `generation_manifest.yaml` — worker-consumed runtime contract: `top_module`
  `sha256`, `top_file`/`compile_files` pointing at the read-only benchmark
  RTL, the exact 11 `test_classes`, `python_test_module: test_top`, and the
  `scenarios` mapping of the 9 plan ids to their sequence/test classes.

**Key integration decisions:**

1. **pyuvm 5.0.0 `run_test` semantics**: `keep_singletons=True` is MANDATORY
   here — the default `keep_singletons=False` clears the `ConfigDB` singleton
   (among others) before `build_phase`, which would silently discard the
   `"dut"`/`"sha256_pins"` keys set in `test_top.py`. `run_test` always
   clears run-phase objections via `ObjectionHandler().clear()`, so the
   test's own `raise_objection`/`drop_objection` bracket (in `Sha256BaseTest.
   run_phase`) is what keeps `run_test` from returning before the scenario
   completes.
2. **Watchdog ownership split**: the env starts the three structural
   assertion checkers (§15) in `build_phase`; each TEST arms the
   simulation-time watchdog with its own budget in `run_phase`
   (`env.assertions.start_watchdog(budget)` before the scenario,
   `disarm_watchdog()` in a `finally`) and then `drop_objection`. Budgets
   (cycles): directed tests `WATCHDOG_MARGIN_CYCLES` (500 — covers the
   longest directed KAT comfortably on a REPAIRED RTL), `Sha256CornerTest`
   2x (1000), `Sha256RandomizedTest` 8x (4000). `test_top.py` additionally
   wraps `run_test` in `with_timeout(OUTER_BUDGET_NS, "ns")`
   (`OUTER_BUDGET_CYCLES`=10000 x `CLK_PERIOD_NS`=10 ns) as the coarse
   upper bound (§1/§7 watchdog alternative).
3. **Grading semantic** (§8/§14/§15): `Sha256BaseTest.report_phase` fails
   on `order_error_count > 0`, on `invalid_block_count > 0` unless the test
   opts in (`Sha256CornerTest` sets `_allow_invalid_blocks=True`), and on an
   empty scoreboard stream unless the test opts out
   (`Sha256ResetInitializationTest` sets
   `_require_graded_transactions=False`). Digest `mismatch_count` is an
   EXPECTED catch report on this corrupted RTL and never fails a test by
   itself; the structural `transaction_completes_within_latency` checker
   (§15) is what fails data-path runs fail-fast ~72 cycles after the first
   `start`. On a repaired RTL all 11 tests pass (mismatch_count 0, no
   assertion fires).
4. **Stimulus selection is static-auditable**: every directed test exposes
   `get_sequence_class()` returning the class SYMBOL, and
   `DIRECTED_SCENARIO_TESTS` + `generation_manifest.yaml` `scenarios` pin
   each plan id to exactly one sequence and one test class; the stage-6
   consistency check
   (`results/stage6_integration/stage6_consistency_checks.py`, AST-based,
   runnable without cocotb installed) verifies all of it (125/125 checks
   PASS) plus the ConfigDB key whitelist (§5), `keep_singletons=True`,
   `with_timeout` form, Makefile flow and manifest/worker contract
   (`workers/sim/run.py` `validate_manifest` mirror).
5. **No DUT source changes**: the benchmark `sha256.sv` remains read-only
   and is the only compiled HDL; all stimulus/checking runs in Python
   (Verilator + cocotb VPI).
6. **Corner/randomized are separate strategies** (§9): they carry NO
   `SCENARIO_ID` anywhere (sequences, tests, manifest `test_classes` list
   only — no `scenarios` entries), matching the established convention.

This stage introduces no new ConfigDB keys. The manifest test class list is
the complete set of runnable pyuvm tests:
| test class | scenario |
|---|---|
| Sha256ResetInitializationTest | reset_initialization |
| Sha256EmptyMessageTest | empty_message |
| Sha256SingleByteATest | single_byte_a |
| Sha256AbcMessageTest | abc_message |
| Sha256HelloWorldTest | hello_world |
| Sha256QuickBrownFoxTest | quick_brown_fox |
| Sha256BackToBackTransactionsTest | back_to_back_transactions |
| Sha256StartWhileBusyRestartsTest | start_while_busy_restarts |
| Sha256DoneBehaviorContinuousTest | done_behavior_continuous |
| Sha256CornerTest | corner aggregate (6 plan corner sequences) |
| Sha256RandomizedTest | randomized strategy (20 txns, seed 24601 / RANDOM_SEED) |