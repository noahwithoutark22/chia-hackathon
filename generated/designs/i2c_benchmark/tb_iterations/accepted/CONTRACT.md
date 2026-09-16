# i2c_master Verification Contract (CHIA stage 1)

Authoritative conventions for every later stage of the generated
cocotb + pyuvm testbench.  Later stages **must** read this file instead
of re-deriving conventions.  Any field/pin/key listed here is binding.

Everything below is derived from these authoritative inputs:

- RTL:            `benchmarks/i2c_benchmark/i2c_master.sv`
- RTL info:       `generated/designs/i2c_benchmark/rtl/rtl_info.json`
- Specification:  `benchmarks/i2c_benchmark/i2c_spec.md`
- Reference model:`benchmarks/i2c_benchmark/i2c_reference_model.py`
  (`I2CReferenceModel.transact(rw, slave_addr, reg_addr, write_data)`)

The testbench is implemented entirely in Python (cocotb + pyuvm).  There
is **no** SystemVerilog interface and **no** SystemVerilog UVM code.
The only SystemVerilog in the project is the DUT RTL, which is never
modified or duplicated.

---

## 1. Top module

- Top module name: **`i2c_master`**
- RTL file: `benchmarks/i2c_benchmark/i2c_master.sv`
- Parameters: none (`parameters: []`)
- cocotb top handle: the `dut` argument received by the Python
  entrypoint *is* `i2c_master`.

## 2. DUT pin map (direction, width, exact access)

Pin access is **always** through the cocotb `dut` handle, either directly
(`dut.<pin>`) or via the `I2CDutPins` helper in `dut_helper.py` (which
wraps `dut.<pin>` 1:1).  All under-2000-character signals use `dut.<name>`,
exactly as written below.

### Clock and reset (structural, not transaction fields)

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `clk` | input | 1 | `dut.clk` | Rising-edge system clock. |
| `rst_n` | input | 1 | `dut.rst_n` | Active-low **asynchronous** reset. |

### Stimulus inputs (map 1:1 to transaction fields)

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `start` | input | 1 | `dut.start` | Transaction request; sampled only while idle (`busy==0`). |
| `rw` | input | 1 | `dut.rw` | Latched at start. `0`=write, `1`=read. |
| `slave_addr` | input | 7 | `dut.slave_addr` | 7-bit I2C address; only `0x50` supported. |
| `reg_addr` | input | 8 | `dut.reg_addr` | Register / memory byte address. |
| `write_data` | input | 8 | `dut.write_data` | Data byte for a write transaction. |

### Outputs (monitored)

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `read_data` | output | 8 | `dut.read_data` | Data returned by a read. |
| `busy` | output | 1 | `dut.busy` | High while a transaction is active. |
| `done` | output | 1 | `dut.done` | Single-cycle completion pulse. |
| `ack_error` | output | 1 | `dut.ack_error` | Set for unsupported slave address; cleared on return to idle. |

### Inouts (open-drain)

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `scl` | inout | 1 | `dut.scl` | Open-drain clock line; driven low during transfer, released (Z) otherwise. |
| `sda` | inout | 1 | `dut.sda` | Open-drain data line; driven low during START-like phase, released (Z) otherwise. |

`scl`/`sda` are driven by the RTL as `0` or high-impedance.  Pull-ups are
modelled by the environment (tb_top/driver); a released line reads `1`
where pull-ups are applied, `z` otherwise.  Helper methods
`scl_is_released()` / `sda_is_released()` treat both `z` and `1` as
"released", and `scl_level()` / `sda_level()` return the raw value.

## 3. Clock and reset semantics (from RTL)

- FSM advances on **rising edge** of `clk`.
- Reset `rst_n` is **active-low** and **asynchronous** (RTL sensitivity
  list: `always_ff @(posedge clk or negedge rst_n)`).
- Reset values: `state=IDLE`, `busy=0`, `done=0`, `ack_error=0`,
  `read_data=0x00`, `scl`/`sda` released (Z).
- Known RTL discrepancy (documented, do **not** "fix" either side): the
  RTL **does not** clear its internal 256-byte memory on reset; the
  reference model **does** (`reset()`).  The scoreboard must compare only
  at `done` pulses and must account for this (e.g. apply a reset-equivalent
  clearing to the model when the bench runs a "reset memory" sequence, or
  restrict reset-crossing comparisons).

## 4. Transaction / sequence_item (`tb/transaction.py`)

Class: **`I2CTransaction`** (pyuvm `uvm_sequence_item`; import as
`from tb.transaction import I2CTransaction`).  All fields are plain Python
`int` attributes; there are no clock/reset fields (structural signals).

### Stimulus fields (driven by the driver from the item)

| Field | Type | Width | Default after `randomize()` |
|---|---|---|---|
| `start` | int | 1 | `1` (item always represents a request offered while idle) |
| `rw` | int | 1 | 0 or 1, uniform |
| `slave_addr` | int | 7 | 40 % `0x50`, else uniform `0x00..0x7F` |
| `reg_addr` | int | 8 | uniform `0x00..0xFF` |
| `write_data` | int | 8 | uniform `0x00..0xFF` |

### Observed-output fields (filled by the monitor at the `done` pulse)

| Field | Type | Width | Meaning |
|---|---|---|---|
| `read_data` | int | 8 | `dut.read_data` sampled while `done==1` |
| `busy` | int | 1 | `dut.busy` sampled while `done==1` |
| `done` | int | 1 | `dut.done` (observed `1`) |
| `ack_error` | int | 1 | `dut.ack_error` sampled while `done==1` |

API: `randomize(**constraints)` (keyword constraints override generated
fields; unknown names raise `AttributeError`);
`check_inputs_valid()` (width validation mirroring the reference model);
`__str__` for logging.

## 5. ConfigDB keys (exact keys, exact value types)

pyuvm `ConfigDB()` is the only sharing mechanism.  Keys below are defined
as constants in `tb/dut_helper.py` and are the **only** keys used.

Set from tb_top/test:

```python
ConfigDB().set(None, "*", KEY_DUT, dut)                 # -> cocotb handle
ConfigDB().set(None, "*", KEY_DUT_PINS, I2CDutPins(dut))
ConfigDB().set(None, "*", KEY_CLK_RST, ClockReset(...))
```

Get from any component:

```python
dut   = ConfigDB().get(self, "", KEY_DUT)
pins  = ConfigDB().get(self, "", KEY_DUT_PINS)
clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
```

| Key constant | Key string | Value type | Contents |
|---|---|---|---|
| `KEY_DUT` | `"dut"` | cocotb module handle | The top-level `dut` for `i2c_master`. |
| `KEY_DUT_PINS` | `"i2c_master.dut_pins"` | `I2CDutPins` | Wrapper giving canonical pin access (`drive_transaction`, `sample_outputs`, `sample_into_item`, `scl/sda` helpers, reset helpers). |
| `KEY_CLK_RST` | `"i2c_master.clk_rst"` | `ClockReset` (frozen dataclass) | `clock_name="clk"`, `reset_name="rst_n"`, `reset_polarity="active_low"`, `reset_type="asynchronous"`, `clock_period_ns` (tb_top-chosen, default 10), `reset_assert_value=0`. |

No other ConfigDB keys may be invented by later stages.

## 6. Transaction timing / sampling rules

Both derived from the RTL FSM (`IDLE -> START_PHASE -> ACCESS ->
STOP_PHASE -> COMPLETE -> IDLE`):

- A transaction is offered by holding `start=1` (with `rw`,
  `slave_addr`, `reg_addr`, `write_data` stable) for the cycle in which
  the DUT is idle; the DUT latches at the next rising edge.
- From the sampling edge, `done` pulses high for exactly one clock cycle
  four edges later (busy rises with request acceptance, `read_data`
  becomes valid for reads in the transfer phase, and `done` fires in
  `COMPLETE` while `busy` falls).
- **Sampling rule (transaction-level, spec §8):** the monitor samples
  `read_data`, `busy`, `ack_error` while `dut.done == 1`, and the
  scoreboard compares those samples against the reference model result
  for that transaction.  No cycle-exact intermediate checking is required.
- A new transaction may be offered as soon as the DUT is idle again
  (back-to-back allowed).
- An unsupported `slave_addr` completes with `done=1`, `ack_error=1`,
  `read_data=0x00`.  Reads of never-written registers return `0x00`.

## 7. Reference model (behavioral oracle)

- File: `benchmarks/i2c_benchmark/i2c_reference_model.py`.
- Class/function: `I2CReferenceModel.transact(rw, slave_addr, reg_addr,
  write_data=0)` -> returns a dict with `done=1`, `busy_after=0`,
  `ack_error`, `read_data`.
- The scoreboard must call this model directly and must **not**
  reimplement or infer expected behavior from the DUT.
- Model memory (`dict[int,int]`, 256 bytes addressed `0x00..0xFF`) is
  cleared by `reset()`; the RTL memory is not cleared by reset (see §3).

## 8. Cross-cutting rules for later stages

- **No SystemVerilog UVM**: no SV `interface`, no SV classes, no SV
  covergroups, no SVA.  Only Python.
- Functional coverage uses `cocotb-coverage`
  (`cocotb_coverage.coverage.CoverPoint` / `CoverCross`, sampled through
  the shared `coverage_db`), never SV covergroups.
- Assertions are plain Python `assert`/failure flags in always-running
  checker coroutines started with `cocotb.start_soon`, running
  concurrently with the environment, failing the test immediately.
- A watchdog is required: an always-running coroutine (or a bounded
  `cocotb.triggers.with_timeout` wrapper around the test body) that fails
  the test if it does not finish within a bounded number of clock cycles.
- Inputs are only meaningful while idle; monitors must not treat `start`
  sampling while `busy==1` as an error by itself (stimulus is gated by
  the driver).
- Supported-address and boundary/scenario coverage follows spec §9.

---

## 9. Stage-3 observation additions (monitor + agent)

Appended by the observation stage; does **not** alter any earlier
binding field, pin, or key.

### 9.1 `tb/monitor.py` — `I2CMonitor` (`uvm_monitor`)

- Builds and publishes through its own `uvm_analysis_port` named
  `"analysis_port"` (attribute `self.analysis_port`), created in
  `build_phase`.
- Reconstructs each completed transaction entirely from the DUT pins via
  the ConfigDB-shared `I2CDutPins` (keys `KEY_DUT_PINS` / `KEY_CLK_RST`):
  - **Stimulus** (`start`, `rw`, `slave_addr`, `reg_addr`, `write_data`)
    is captured at the request-latch point — either the mid-cycle
    falling-edge probe (`start==1, busy==0`) or the latching rising edge
    where `busy` transitions `0 -> 1`.
  - **Observed outputs** (`read_data`, `busy`, `done`, `ack_error`) are
    sampled while `dut.done == 1` (exactly the §6/§8 sampling rule).
- Publication: one `I2CTransaction` per completed transaction with all
  §4 fields filled, written via `analysis_port.write(item)`.
- Reset aborts (`rst_n==0`, or `busy` falling without `done`) drop the
  in-flight transaction: no item is published.  Scoreboard stages must
  therefore **not** assume a 1:1 monitor-item ↔ sequence-item pairing when
  reset injection is enabled (`I2CRandomizedSequence`).
- The monitor is observation-only: it never drives pins and never fails
  the test by itself.  A hung transaction is logged as an error after a
  bounded cycle count (`done_timeout_cycles = 512`); the always-running
  watchdog (environment stage) is the failing mechanism.

### 9.2 `tb/agent.py` — `I2CAgent` (`uvm_agent`)

- Encapsulates the stage-2 `I2CDriver`/`I2CSequencer` and the stage-3
  `I2CMonitor`.  Exposes attributes `driver`, `sequencer`, `monitor`
  (children named `"driver"`, `"sequencer"`, `"monitor"`) and one
  `uvm_analysis_port` named `"analysis_port"`.
- `build_phase`: calls `super().build_phase()` (pyuvm sets
  `is_active = UVM_ACTIVE`, overridable via ConfigDB key `"is_active"`),
  then builds `analysis_port`, `monitor`, and — in active mode —
  `driver` and `sequencer`.
- `connect_phase`:
  `driver.seq_item_port.connect(sequencer.seq_item_export)` and
  `monitor.analysis_port.connect(agent.analysis_port)`.
- The environment builds this agent; sequences are started on
  `agent.sequencer` by the test stage.

---

## 10. Stage-4 check additions (scoreboard)

Appended by the check stage; does **not** alter any earlier binding
field, pin, or key.

### 10.1 `tb/scoreboard.py` — `I2CScoreboard` (`uvm_scoreboard`)

- Receives every completed monitor item through its own TLM sink
  `analysis_export` (a `uvm_analysis_export` subclass whose `write`
  forwards to the scoreboard's comparison callback).  The environment
  connects `agent.analysis_port` -> `scoreboard.analysis_export`.
- Maintains an **independent** `I2CReferenceModel` instance; expected
  values always come from `model.transact(item.rw, item.slave_addr,
  item.reg_addr, item.write_data)`, never from the DUT and never from a
  reimplementation.
- Compares, for each item sampled at the `done` pulse (§6/§9):
  - `item.done == 1` (sanity: the monitor publishes only done-completed
    transactions),
  - `item.busy == expected["busy_after"]` (`0`),
  - `item.ack_error == expected["ack_error"]`,
  - `item.read_data == expected["read_data"]`.
- **Reset-equivalent clearing** (the §3 remedy): an always-running
  `_watch_reset` coroutine taps the shared `I2CDutPins.rst_n` (key
  `KEY_DUT_PINS`) and calls `model.reset()` on every assertion of the
  active-low asynchronous reset, so oracle memory tracks the bench's
  resets (per-scenario start-up resets and the randomized sequence's
  mid-flight injection).
- Fail-fast: an expected/observed mismatch is logged as an error and
  raised (AssertionError) from the comparison callback, propagating to
  the monitor coroutine and failing the enclosing cocotb test
  immediately (§8).  Counters `item_count`, `matched_count`,
  `failed_count`, `reset_count` are exposed for the environment report.
- No 1:1 monitor-item <-> sequence-item pairing is assumed: aborted
  (reset-struck) transactions are dropped by the monitor (§9.1) and so
  never reach the scoreboard.  The scoreboard is purely comparative; the
  always-running watchdog (environment stage) remains the mechanism that
  fails the test when no `done` pulses arrive at all.

---

## 11. Stage-5 coverage & assertion additions

Appended by the coverage/assertions stage; does **not** alter any earlier
binding field, pin, or key.

### 11.1 `tb/coverage.py` — functional coverage (cocotb-coverage)

- Implements the plan's `functional_coverage` covergroup `transaction_cg`
  entirely with `cocotb_coverage.coverage.CoverPoint` / `CoverCross`
  registered in the shared singleton `coverage_db` under
  `top.transaction_cg.<name>`.  Coverage points: `rw_cp`,
  `slave_addr_cp`, `reg_addr_cp`, `write_data_cp`, `ack_error_cp`,
  `read_data_cp`; crosses: `rw_x_slave_addr`, `rw_x_reg_addr`,
  `slave_addr_x_ack_error`.  Ranged plan bins are implemented as bin
  classifiers (`xf`) mapping the variable to a class id, with
  `bins_labels` carrying the plan bin names.
- Sampling data source is *exclusively* the monitor stream from §9.1:
  `I2CCoverage` (a pyuvm `uvm_subscriber`, providing `analysis_export`)
  forwards every `I2CTransaction` written to it into
  `sample_transaction(item)`, which samples all coverpoints then the
  crosses.  Since the monitor only publishes completed transactions
  (sampled while `done==1`), coverage is inherently sampled on each
  `done` pulse exactly as the plan's `sample_on: done` requires.
- The environment (integration stage) connects
  `agent.analysis_port -> coverage.analysis_export` (a second fan-out,
  alongside `scoreboard.analysis_export`) and reports with
  `report_transaction_coverage(logger[, bins])` /
  `transaction_coverage_percentage()`.
- The collector is observation-only (like an SV covergroup): it never
  drives pins and never fails the test.

### 11.2 `tb/assertions.py` — SVA-replacement Python checkers

- Implements all six plan `useful_assertions` as plain-Python checker
  coroutines launched with `cocotb.start_soon` (no SVA anywhere):
  - error severity (`AssertionError`, fails the test immediately):
    `reset_clears_outputs`, `busy_deasserted_after_done`,
    `done_pulses_exactly_one_cycle`,
    `ack_error_implies_unsupported_address`;
  - warning severity (logged + counted in `violations`, non-fatal):
    `no_simultaneous_start_done`, `scl_sda_released_in_idle`.
- `I2CAssertions(pins=..., clkrs=...)` fetches the shared `I2CDutPins` /
  `ClockReset` from `KEY_DUT_PINS` / `KEY_CLK_RST` when not injected;
  `start()` launches all checkers via `cocotb.start_soon`
  (`launch_assertions(...)` is the one-call entry point for the
  environment stage); `violations` / `summarize()` feed the end-of-test
  report.
- **Sampling semantics (binding for stage 6):** all checkers sample pins
  at every rising clock edge *after* the edge (post-edge register values,
  what SVA on `posedge clk` sees).  Every checker skips sampling while
  `rst_n` is asserted or unknown, so the pre-reset X window and power-up
  cannot fabricate violations.  The `done` cycle itself (busy==0, done==1,
  both open-drain lines released) satisfies every rule.
- **Watchdog:** the always-running bounded-cycle watchdog required by §8
  is provided here as `launch_watchdog(pins, clkrs, timeout_cycles)` /
  `watchdog(...)`.  It counts rising clock edges and raises
  `AssertionError` once `timeout_cycles` elapse; the **environment stage
  (stage 6) starts it and `task.kill()`s it on normal completion** (the
  per-stage split kept the watchdog out of earlier observation/check
  stages as noted in §9.1/§10.1).

---

## 12. Stage-6 integration additions (environment, tests, entry point)

Appended by the integration stage; does **not** alter any earlier binding
field, pin, or key.

### 12.1 `tb/env.py` — `I2CEnv` (`uvm_env`)

- Instantiated by every test as `I2CEnv("i2c_env", self)`.  Owns the
  `I2CAgent` (`"i2c_agent"`), `I2CScoreboard` (`"i2c_scoreboard"`),
  `I2CCoverage` (`"i2c_coverage"`), and the always-running assertion
  bundle (`launch_assertions()`).
- `build_phase`: builds the three components and launches all six plan
  `useful_assertions` (error checkers fail the test on the first
  violation; warning checkers count into `I2CAssertions.violations`).
- `connect_phase`: `agent.analysis_port` fans out to
  `scoreboard.analysis_export` and `coverage.analysis_export`.
- `report_phase`: consolidated end-of-test report — scoreboard summary,
  assertion summary, full coverage dump + percentage.
- `final_phase`: `assertions.stop()` (kills the checker tasks).  The
  watchdog is owned by tb_top and killed there.

### 12.2 `tb/test.py` — `uvm_test` classes (`UVM_TESTNAME` values)

- `I2CTestBase` (`uvm_test`): `build_phase` builds `I2CEnv`; `run_phase`
  raises a run-phase objection, awaits `_run_scenario()`, and drops the
  objection (so the scenario, including the tail monitor drain, completes
  before the report phases); `report_phase` enforces pass/fail.
- Pass/fail (`report_phase`): `scoreboard.failed_count > 0` fails; and,
  for every *data-path* test (`REQUIRES_TRANSACTIONS = True`),
  `scoreboard.item_count == 0` fails (a test whose stimulus crashed before
  exercising any transaction must not silently pass).  The reset-only
  directed scenario `I2C_01` sets `REQUIRES_TRANSACTIONS = False`.
- Directed tests: `I2C01ResetBehaviorTest` .. `I2C14BackToBackTest`, one
  per plan id, each carrying `SCENARIO_ID` and `SEQUENCE_CLASS`
  (tb/sequences.py).  `verify_directed_test_scenario_ids()` runs at import
  time and cross-checks the test layer against the sequence layer and the
  plan ids.
- `I2CCornerCaseTest` runs every `CORNER_CASE_SEQUENCE_CLASSES` entry
  sequentially (each corner self-resets, keeping the model/DUT memories in
  lockstep).  `I2CRandomizedTest` starts `I2CRandomizedSequence`
  (`num_transactions=60`, `reset_injection_probability=0.05`); set the
  `I2C_SEED` environment variable (integer) to replay a run.

### 12.3 `tb/test_top.py` — cocotb entry point

- Single `@cocotb.test()` coroutine, `MODULE = test_top`.
- Starts `Clock(dut.clk, I2C_CLK_PERIOD_NS ns)` (default 10 ns), applies
  the active-low async reset for 3 cycles with all stimulus inputs
  deasserted, then deasserts and settles 2 cycles.
- Populates the §5 ConfigDB keys: `KEY_DUT` -> `dut`, `KEY_DUT_PINS` ->
  `I2CDutPins(dut)`, `KEY_CLK_RST` -> `ClockReset(...)`.
- Arms `launch_watchdog(clkrs=..., timeout_cycles=I2C_WATCHDOG_CYCLES)`
  (default 300 000 cycles), then `await uvm_root().run_test(
  UVM_TESTNAME, keep_singletons=True)` inside `try/finally` that kills the
  watchdog on normal completion.
- **pyuvm 5.0 flow (no shims needed):** `set(None, "*", key, value)` stores
  under the wildcard scope, and every component retrieves with
  `get(self, "", key)` / `get(None, "", key)`; the empty retrieve path
  resolves to the caller's scope and `fnmatch("", "*")` matches the
  wildcard store.  `keep_singletons=True` preserves the ConfigDB/factory
  singletons (the default rebuilds them and would discard the keys set
  here).  This differs from the FIFO bench, which needed explicit pyuvm
  3.0.0 shims.

### 12.4 `tb/Makefile` — build/run configuration

- `SIM = verilator`, `TOPLEVEL = i2c_master`, `MODULE = test_top`,
  `VERILOG_SOURCES = $(REPO_ROOT)/benchmarks/i2c_benchmark/i2c_master.sv`
  (REPO_ROOT = `$(abspath $(CURDIR)/../../../..)`, i.e. the repository
  root).  Only the DUT RTL is compiled; everything else is Python.
- `export PYTHONPATH := $(REPO_ROOT):$(TB_DIR):$(PYTHONPATH)` so both
  `benchmarks.*` and `tb.*` (and the `test_top` module) resolve on
  `sys.path`.
- `COMPILE_ARGS = --timing -DUVM_NO_DPI -Wno-WIDTH -Wno-CASEINCOMPLETE
  -Wno-UNOPTFLAT -j 0`.
- Exported test knobs: `UVM_TESTNAME`, `I2C_CLK_PERIOD_NS`,
  `I2C_WATCHDOG_CYCLES`, `I2C_SEED`.
- `make regression` runs every class listed in `generation_manifest.yaml`
  (per-test `SIM_BUILD` and `COCOTB_RESULTS_FILE`).

### 12.5 `tb/generation_manifest.yaml` — runtime manifest

- `top_module`/`top_file`/`compile_files` name `i2c_master` and the single
  RTL source; `python_test_module = test_top`; `test_classes` lists the 16
  exact `UVM_TESTNAME` values; `scenarios` maps I2C_01..I2C_14 to
  plan names, sequence classes, and test classes; corner/randomized
  strategies are listed for cross-reference.

### 12.6 Stage-6 consistency pass (bindings amended, not weakened)

- **`read_data` comparison scope.**  §10.1's "compare `read_data` for
  each item" is amended to the plan's authoritative
  ``scoreboard_reference_model_strategy`` rule: `read_data` is compared
  for **supported-address reads** (model memory value, `0x00` if never
  written) and for **unsupported-address transactions** (must be `0x00`);
  it is **not** compared for supported-address writes, where the spec
  leaves `read_data` unspecified ("data returned by a read") and the byte
  is instead verified through later reads.  `I2CScoreboard` and
  `I2CRandomizedSequence._random_transaction` both apply exactly this
  scope, so sampling the value the RTL retains across writes is *not* a
  defect.
- **Documented discrepancies keep their guards.**  I2C_DISC_001 (stale
  `read_data` on unsupported-address transactions) and I2C_DISC_002 (RTL
  memory not cleared on reset) remain detected per plan: the scoreboard and
  the randomized sequence still require `read_data == 0x00` for
  unsupported-address transactions (I2C_DISC_001) and reads stay restricted
  to registers written after the most recent reset (I2C_DISC_002).  In
  particular `I2CRandomizedTest` is the bench's detector for the major
  I2C_DISC_001 defect on the current RTL; the directed/corner scenarios
  reset first and therefore stay green.