# CONTRACT — i2c_master (corrupted) cocotb + pyuvm verification environment

Stage 1 of 6 (CONTRACT) of the CHIA cocotb+pyuvm environment generator.

**This file is the authoritative convention record for every later stage
(stimulus, observation/scoreboard, coverage/assertions, env/test,
integration).**  Later stages MUST read it instead of re-deriving pin names,
widths, transaction fields, ConfigDB keys, or clock/reset semantics from the
RTL or plan.  If a later stage believes something here is wrong, it may
extend this file minimally (append, do not rewrite) and explain why -- it
must not silently diverge.

Generated artifact location:
`/workspace/generated/designs/i2c_benchmark_corrupted/tb/`

Authoritative inputs this contract is derived from:

- RTL:            `benchmarks/i2c_benchmark_corrupted/i2c_master.sv`
- RTL info:       `generated/designs/i2c_benchmark_corrupted/rtl/rtl_info.json`
- Specification:  `benchmarks/i2c_benchmark_corrupted/i2c_spec.md`
- Reference model:`benchmarks/i2c_benchmark_corrupted/i2c_reference_model.py`
- Verification plan:
  `generated/designs/i2c_benchmark_corrupted/plans/verification_plan.yaml`

---

## 1. Stack / version contract (hard)

- Testbench is implemented entirely in Python: **Cocotb 2.1.0** + **pyuvm
  5.0.0**.  No SystemVerilog UVM, no SV `interface`, no SV covergroups/SVA.
  The only SystemVerilog in the project is the DUT RTL (`i2c_master.sv`),
  which is never modified or duplicated.
- Public Cocotb 2.1.0 APIs only (verified against the cocotb-2.1.0 wheel):
  - triggers `RisingEdge`, `FallingEdge`, `ClockCycles`, `Timer`,
    `Combine`, `with_timeout` from `cocotb.triggers`;
  - `cocotb.clock.Clock(signal, period, unit=...)` (the 2.x spelling;
    `units` was renamed `unit` in cocotb 2.0) and `clock.start()`;
  - `cocotb.start_soon(...)` and `await` (never deprecated `cocotb.fork`);
  - read: `int(dut.<pin>.value)`; write: `dut.<pin>.value = <int>`.
    Never `int(dut.<pin>)` (deprecated in 2.x) and never import
    `cocotb.handle.ModifiableObject` (removed from cocotb 2.1.0).
- pyuvm classes used: `uvm_sequence_item`, `uvm_sequence`, `uvm_sequencer`,
  `uvm_driver`, `uvm_monitor`, `uvm_agent`, `uvm_scoreboard`, `uvm_env`,
  `uvm_test`, `uvm_analysis_port`, `uvm_tlm_analysis_fifo`, `ConfigDB`.
  pyuvm 5.0.0 has no `uvm_object_utils`/field-automation macros -- all
  fields are plain Python attributes.
- Functional coverage uses `cocotb-coverage`
  (`cocotb_coverage.coverage.CoverPoint` / `CoverCross`, sampled via the
  shared `coverage_db`).  Assertions are plain Python `assert`/raise checks
  inside always-running coroutines started with `cocotb.start_soon`.  A
  deterministic watchdog guards the whole test (bounded cycles /
  `with_timeout`) and must NOT replace functional completion checks.

## 2. Top module and file layout

- Top module name: **`i2c_master`** (file
  `benchmarks/i2c_benchmark_corrupted/i2c_master.sv`).
- Module parameter: `CLK_DIV` (default `4`; plan `test_values` 4/8/16).
  The generated TB runs with the default `CLK_DIV = 4` unless a later stage
  documents parameterized per-test overrides (worker `-G` mechanism).
- Generated TB files are **flat Python modules** in this `tb/` directory
  (the sim worker adds `tb/` to `PYTHONPATH`, so modules import by bare
  name, e.g. `from i2c_transaction import I2CTransaction`, and
  `benchmarks/` is importable from the workspace root).  There is
  deliberately **no** `__init__.py`; modules are top-level.
- The cocotb entry point is a single flat module `test_top.py` in this
  directory (fixed name required by the sim worker).

## 3. DUT pin map (authoritative)

Every pin is accessed through the cocotb `dut` handle.  Widths and
directions come from `rtl_info.json` and the verification plan and match
`i2c_master.sv`.  `I2CPins` (`i2c_pins.py`) wraps `dut.<pin>` 1:1 and is
the recommended way to touch pins; direct `dut.<pin>` access is equally
valid and must use exactly the names below.

### 3.1 Clock and reset (structural, not transaction fields)

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `clk` | input | 1 | `dut.clk` | Rising-edge system clock; all DUT state changes on `posedge clk`. |
| `rst_n` | input | 1 | `dut.rst_n` | Active-LOW, **synchronous** reset (RTL sensitivity is `always_ff @(posedge clk)`; `if (!rst_n)`). |

### 3.2 Stimulus inputs (map 1:1 to transaction fields)

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `start` | input | 1 | `dut.start` | Transaction request; honored only while the controller is idle. |
| `slave_addr` | input | 7 | `dut.slave_addr` | 7-bit I2C slave address (0x00..0x7F). |
| `rw` | input | 1 | `dut.rw` | Direction bit: 0 = write, 1 = read. |
| `tx_data` | input | 8 | `dut.tx_data` | Data byte to transmit during a write transaction. |
| `sda_in` | input | 1 | `dut.sda_in` | Sampled SDA bus value; used for ACK sampling and read-data reception. The TB drives it (slave side of the shared bus). |
| `scl_in` | input | 1 | `dut.scl_in` | Sampled SCL bus value. **The corrupted RTL never samples `scl_in`** (it appears only in the port list); the TB holds it at 1 (released high). |

### 3.3 Outputs (monitored)

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `rx_data` | output | 8 | `dut.rx_data` | Received byte for a read transaction. |
| `done` | output | 1 | `dut.done` | One-cycle completion pulse on a correct RTL (corrupted: permanently high, see §7/§9). |
| `busy` | output | 1 | `dut.busy` | High while a transaction is active (corrupted: cleared mid-transaction, see §9). |
| `ack_error` | output | 1 | `dut.ack_error` | High when an expected slave ACK is not observed (corrupted: forced high in IDLE, see §9). |
| `sda_out` | output | 1 | `dut.sda_out` | Data value for the open-drain SDA output. |
| `sda_oe` | output | 1 | `dut.sda_oe` | SDA drive-enable; 1 = drive, 0 = release (pull-up drives high). |
| `scl_out` | output | 1 | `dut.scl_out` | Clock value for the open-drain SCL output. |
| `scl_oe` | output | 1 | `dut.scl_oe` | SCL drive-enable. |

No inouts exist on this DUT (`inouts: []`).

### 3.4 Read/write conventions (Cocotb 2.1.0)

```python
# Drive:
dut.start.value = 1
dut.slave_addr.value = 0x50
dut.rw.value = 0
dut.tx_data.value = 0xA5
dut.sda_in.value = 1
dut.scl_in.value = 1

# Sample:
start_val   = int(dut.start.value)
rx_data_val = int(dut.rx_data.value)
```

`I2CPins` provides named helpers (`drive_start`, `read_rx_data`,
`resolve_sda_level`, ...) and deterministic X/Z handling (`_to_int` treats
X/Z bits as 0; `sample_outputs_strict()` rejects X/Z at the completion
point).

## 4. Clock and reset semantics (from RTL)

- FSM advances on **rising edge** of `clk`.
- Reset `rst_n` is **active-low** and **synchronous** (RTL sensitivity:
  `always_ff @(posedge clk)`, body `if (!rst_n)`).  Reset assertion takes
  effect on the next rising edge.
- Reset values: `state=IDLE`, `div_cnt=0`, `bit_cnt=0`, `shift_reg=0`,
  `rx_shift=0`, `rx_data=0`, `done=0`, `busy=0`, `ack_error=0`.
  After reset deassertion the controller is ready to accept a `start`.
- The TB applies reset by holding `rst_n=0` across `RESET_CYCLES` (8)
  rising edges then deasserting (`I2CPins.reset_dut()`); the initial reset
  in `test_top.py` uses the same helper.

## 5. Transaction / sequence_item (`i2c_transaction.py`)

Module: `i2c_transaction.py` (flat, bare-name import:
`from i2c_transaction import I2CTransaction`)
Class: **`I2CTransaction`** (`pyuvm.uvm_sequence_item` subclass).

All fields are plain Python `int` attributes, width-masked in `__init__`.
There are no clock/reset fields (structural signals).

### Stimulus fields (driven by the driver; each maps 1:1 to a DUT input)

| Field | Type | Width | Default | Meaning |
|---|---|---|---|---|
| `start` | int | 1 | `1` | Transaction request offered while idle. |
| `slave_addr` | int | 7 | `0x50` | 7-bit I2C slave address (0x00..0x7F). |
| `rw` | int | 1 | `0` | 0 = write, 1 = read. |
| `tx_data` | int | 8 | `0` | Data byte for a write transaction. |
| `sda_in` | int | 1 | `1` | Default SDA level the TB presents on `dut.sda_in` (1 = released high). The driver derives the per-cycle waveform from `slave_ack` + `read_data`. |
| `scl_in` | int | 1 | `1` | SCL level held on `dut.scl_in` (unused by the corrupted RTL). |

### Slave-response intent fields (NOT DUT pins)

| Field | Type | Width | Default | Meaning |
|---|---|---|---|---|
| `slave_ack` | int | 1 | `1` | 1 = slave drives ACK (SDA low) at ACK sample points; 0 = slave NACKs (SDA high). |
| `read_data` | int | 8 | `0` | Byte the slave drives MSB-first during a read transaction's data phase (ignored for writes). |

These are the stimulus inputs to the TB's slave-side bus model; the driver
maps them into the `sda_in` timeline (ACK/NACK levels and read-data bits).

### Observed-output fields (filled by the monitor; each maps 1:1 to a DUT output)

| Field | Type | Width | Meaning |
|---|---|---|---|
| `rx_data` | int | 8 | `dut.rx_data` sampled at the completion point. |
| `done` | int | 1 | `dut.done` at the completion point. |
| `busy` | int | 1 | `dut.busy` at the completion point. |
| `ack_error` | int | 1 | `dut.ack_error` at the completion point. |
| `sda_out` | int | 1 | `dut.sda_out` at the completion point. |
| `sda_oe` | int | 1 | `dut.sda_oe` at the completion point. |
| `scl_out` | int | 1 | `dut.scl_out` at the completion point. |
| `scl_oe` | int | 1 | `dut.scl_oe` at the completion point. |

### Metadata fields (testbench bookkeeping, NOT DUT pins)

| Field | Type | Width | Meaning |
|---|---|---|---|
| `txn_id` | int | — | Monotonic transaction id for in-order scoreboard matching and error reporting. |
| `latency_cycles` | int | — | Measured start-acceptance → completion cycle count. |

### Convenience API

- `item.address_byte` → `(slave_addr << 1) | rw` (identical to the
  reference model `make_address_byte()`).
- `item.is_read` → `bool(item.rw)`.
- `item.randomize(**constraints)` — uniform constrained randomization over
  the plan's `randomized_testing_strategy` ranges (`slave_addr` 0x00..0x7F,
  `rw` 0/1, `tx_data` 0x00..0xFF, `read_data` 0x00..0xFF, `slave_ack` 0/1,
  `start` always 1); keyword constraints override after generation and
  unknown names raise `AttributeError`.
- `item.check_inputs_valid()` — width validation mirroring the reference
  model's `ValueError` checks.
- `item.convert2string()` / `str(item)` — compact single-line report for
  `uvm_info()`.

## 6. ConfigDB keys (exact, shared between all components)

pyuvm `ConfigDB()` is the only sharing mechanism.  The two keys below are
set ONCE in `test_top.py` before the pyuvm tree is built, and are the
**only** keys defined in stage 1:

| Key | Value type | Set by | Read by |
|---|---|---|---|
| `"dut"` | cocotb top-level DUT handle (the `dut` argument passed to the cocotb test entry point). Do NOT import/assume `cocotb.handle.ModifiableObject`. | `test_top.py` | driver, monitor, scoreboard, assertions, coverage, env |
| `"i2c_pins"` | `I2CPins` instance (module `i2c_pins.py`) wrapping `dut`. | `test_top.py` (constructed as `I2CPins(dut)`) | driver, monitor, scoreboard, assertions, coverage, env |

No other keys may be invented; if a later stage needs more shared objects
it must extend this file with a documented key first.

### pyuvm 5.0.0 set/get forms (locked)

- Store: `ConfigDB().set(None, "*", key, value)` (wildcards are legal in
  the *stored* instance-name path).
- Retrieve: `ConfigDB().get(None, "", key)` (the requesting `inst_name`
  must be a concrete path with no wildcards -- pyuvm raises `UVMError` for
  `get(None, "*", ...)` and `TypeError` for `get(None, None, ...)`).
  The empty path `""` resolves to the root, which `fnmatch`-matches the
  stored `"*"` glob.  Components may also retrieve with
  `ConfigDB().get(self, "", key)`.
- `uvm_root().run_test(test_name, keep_singletons=True)` is MANDATORY:
  the default `keep_singletons=False` clears the ConfigDB singleton before
  `build_phase` and would silently discard the keys set in `test_top.py`.

## 7. Timing / completion model

### 7.1 Intended protocol timeline (spec §5/§6, correct RTL)

- Offer: the driver holds `start=1` with `slave_addr`/`rw`/`tx_data`
  stable for the cycle in which the DUT is idle (`busy==0`); the FSM
  captures the request on the next state advance.
- **Start acceptance = `busy` rising 0 → 1**.
- Completion = the `done` **pulse** (one cycle) after STOP; `busy` falls,
  controller returns to IDLE.
- Latency is **not a fixed cycle count** (spec §9): each FSM advance takes
  `CLK_DIV` system-clock cycles; total advance counts differ from the plan
  only through `done`.  Verification must key completion on the `done`
  pulse, never on a hard-coded latency.

### 7.2 Sampling rule (binding for the observation stage)

The monitor samples `rx_data`, `busy`, `ack_error` (and the open-drain
controls) at the completion point.  On the intended `done`-pulse model the
completion point is the high phase of the `done` pulse after start
acceptance.  No cycle-exact intermediate checking is required.

### 7.3 Corrupted-RTL reality (this DUT as-shipped) -- binding caveats

The verification plan documents 20 discrepancies (DIS-01..DIS-20, §9).
The ones that most constrain the TB design:

- **`done` is permanently high** (DIS-15): the `always_ff` body executes
  `done <= 1'b1` unconditionally every active cycle, so after the first
  post-reset cycle `done == 1` forever.  `done` is therefore **not** a
  completion pulse and a 0→1 `done` edge never occurs after start.
- **The transaction engine never advances for CLK_DIV ∈ {4, 8, 16}**
  (DIS-18 + DIS-19): the divider compares `div_cnt == CLK_DIV` while
  `div_cnt` is `$clog2(CLK_DIV)` bits wide and increments by 2, so the
  terminal count is unreachable (e.g. CLK_DIV=4: 2-bit counter 0→2→0→…,
  never 4).  The FSM stays in IDLE; `start` is never honored and `busy`
  never rises.
- **`ack_error` is forced high in IDLE** (DIS-11).
- **`busy` is cleared at the address-ACK phase** (DIS-12) -- when the FSM
  *does* advance (non-plan CLK_DIV values on a repaired variant), so busy
  does not span the transaction.
- **SDA/SCL drive controls are hardwired** (DIS-20): `sda_oe=1`,
  `scl_oe=1`, `sda_out=0`, `scl_out=0` — the controller never releases the
  open-drain lines.

Consequence (so later stages do not re-derive it): on this RTL no
transaction ever reaches STOP and no `done` pulse occurs.  Every
bounded wait in the environment must therefore be exactly that — bounded:

| Constant (in `i2c_pins.py`) | Cycles | Meaning |
|---|---|---|
| `RESET_CYCLES` | 8 | reset hold duration (≥ plan's 4) |
| `SETTLE_CYCLES` | 2 | post-reset settle edges |
| `START_TIMEOUT_CYCLES` | 64 | started offer → `busy` rise wait bound |
| `DONE_TIMEOUT_CYCLES` | 2048 | acceptance → `done` pulse wait bound (correct single-byte transaction ≈ 21 advances × CLK_DIV ≤ ~340 @ CLK_DIV=16; 2048 is generous) |
| `WATCHDOG_CYCLES` | 300000 | global run bound (worker also enforces an OS timeout) |

The environment must wait for `busy` rise and then `done` (0→1, armed only
after acceptance) with the two bounds above, and report a **hung
transaction** (not a pass) when either bound elapses.  Data-path tests
against the as-shipped RTL are therefore expected to report hung
transactions / mismatches — that is the intended catch report; the
watchdog keeps the run bounded.

## 8. Functional behavior / reference model (behavioral oracle)

- Golden reference:
  `benchmarks/i2c_benchmark_corrupted/i2c_reference_model.py`.
- `address_byte = (slave_addr << 1) | rw`, transmitted MSB first
  (`make_address_byte`, `address_bits`, `byte_bits`).
- `write_transaction(slave_addr, data, slave_ack=True)` returns a dict:
  `start, address, address_byte, rw=0, tx_data, expected_slave_acks=2,
  slave_ack, expected_ack_error=(not slave_ack), stop`.
- `read_transaction(slave_addr, data_from_slave, slave_ack=True)` returns a
  dict: `start, address, address_byte, rw=1, tx_data=0, slave_data,
  expected_slave_acks=1, master_final_ack=False, slave_ack,
  expected_ack_error=(not slave_ack), expected_rx_data=data_from_slave,
  stop`.
- `expected_write_bytes(slave_addr, data)` → `[address_byte, data]`.
- The scoreboard MUST use these exact functions — never reimplement the
  algorithm in the TB.  Scoring (per the plan's
  `scoreboard_reference_model_strategy`): each completed transaction is
  compared against the reference-model dictionary; any deviation is
  reported as a DUT defect (see §9), attributed to the DUT, never to the
  reference model.

## 9. Known RTL discrepancies (from the plan; do not "fix" either side)

The plan's `discrepancies` list (id, RTL line, spec, impact): DIS-01 R/W
bit transmitted inverted (`{slave_addr, ~rw}`); DIS-02 address bit counter
init 6 instead of 7; DIS-03 address bit counter increments instead of
decrementing; DIS-04 address phase terminal off-by-one (`bit_cnt == 1`);
DIS-05 address-ACK sampling inverted (`sda_in == 0` ⇒ error); DIS-06
write-data-ACK sampling inverted; DIS-07 read/write path selection swapped;
DIS-08 write data complemented (`shift_reg <= ~tx_data`); DIS-09 rx_data
complemented (`rx_data <= ~rx_shift`); DIS-10 read-data phase terminal
off-by-one; DIS-11 `ack_error` forced high in IDLE; DIS-12 `busy` cleared at
address ACK; DIS-13 write completion loops into READ_DATA instead of STOP;
DIS-14 read completion loops back to DATA_ACK instead of STOP; DIS-15
`done` never a pulse; DIS-16 `busy` kept high at STOP; DIS-17 STOP re-enters
START_COND instead of IDLE; DIS-18 divider terminal off-by-one; DIS-19
divider increments by two; DIS-20 SDA/SCL drive controls hardwired active.
(Note: fault-07 `rx_shift[7-bit_cnt]` in the FAULTS manifest is already
present in the *correct* form in this RTL; the RTL text is authoritative.)

The verification environment detects these as structured catch reports
(scoreboard mismatches, assertion violations, hung-transaction reports)
rather than trying to pass against the as-shipped RTL.

## 10. Directed scenario ids / corner cases / randomized strategy (locked)

Every planned `directed_test_scenarios[].id` is implemented exactly once by
a sequence class carrying `SCENARIO_ID = "<exact plan id>"`:

- `reset_idle_check` (TC-01), `write_basic` (TC-02), `write_zero` (TC-03),
  `write_max` (TC-04), `read_basic` (TC-05), `read_max` (TC-06),
  `write_addr_nack` (TC-07), `write_data_nack` (TC-08),
  `read_addr_nack` (TC-09), `start_while_busy` (TC-10),
  `reset_during_transaction` (TC-11), `done_pulse_check` (TC-12),
  `address_msb_first_check` (TC-13).

Plan corner cases (get NO `SCENARIO_ID`): `addr_zero_write`,
`addr_max_write`, `addr_max_read`, `data_zero_write`, `data_max_write`,
`rx_all_ones_read`, `rx_all_zeros_read`, `missing_addr_ack`,
`missing_data_ack`, `start_one_cycle`, `back_to_back_transactions`,
`reset_mid_transaction`, `clk_div_min`, `released_bus_no_ack`.

Randomized strategy (`randomized_testing_strategy`): uniform
`slave_addr` 0..127, `tx_data` 0..255, `rw` 0/1, `slave_ack` 0/1,
`read_data` 0..255; reset injection at run start and occasionally
mid-transaction.  Reference-model vectors: `write_basic(0x50,0xA5)`,
`write_zero(0x00,0x00)`, `write_max(0x7F,0xFF)`, `read_basic(0x50,0x3C)`,
`read_max(0x2A,0xFF)`.

## 11. Cross-cutting rules for later stages

- **No SystemVerilog UVM**: no SV `interface`, no SV classes, no SV
  covergroups, no SVA.  Only Python.  Do not modify, duplicate, or wrap the
  DUT RTL; the benchmark RTL stays the only compiled HDL.
- Functional coverage uses `cocotb-coverage`
  (`cocotb_coverage.coverage.CoverPoint` / `CoverCross`, sampled through
  the shared `coverage_db`), never SV covergroups.
- Assertions are plain Python `assert`/raise checks in always-running
  checker coroutines started with `cocotb.start_soon`, running concurrently
  with the environment, failing the test immediately (fail-fast).
- A watchdog is required: an always-running coroutine (or a bounded
  `cocotb.triggers.with_timeout` wrapper around the test body) that fails
  the test if it does not finish within a bounded number of clock cycles
  (`WATCHDOG_CYCLES`).  It must NOT replace functional completion checks.
- Env-var knobs (family convention, read by `test_top.py`):
  `I2C_CLK_PERIOD_NS` (default 10), `I2C_WATCHDOG_CYCLES` (default
  300000), `I2C_SEED` (randomized-test replay).
- X/Z handling: pin reads coerce X/Z to 0 deterministically (`_to_int`);
  at the completion point `I2CPins.sample_outputs_strict()` rejects X/Z
  instead of silently scoring an undriven output as the reference result.
- Reset-injection sequencing: when a scenario injects `rst_n=0`
  mid-transaction, the monitor drops the in-flight transaction (no item is
  published); later stages must not assume a 1:1 monitor-item ↔
  sequence-item pairing.

## 12. Files written in this stage

- `i2c_transaction.py` — `I2CTransaction(uvm_sequence_item)` (class, widths,
  randomize, validation, reporting).
- `i2c_pins.py` — `I2CPins` pin-access helper, ConfigDB key constants,
  structural/timing constants, `make_clock`, deterministic X/Z-safe pin
  sampling.
- `CONTRACT.md` — this file.

Later stages append to this file (sections for stimulus, observation,
checking, coverage/assertions, integration) without altering the binding
fields, pins, keys, or semantics above.

---

## 13. Stimulus stage (STIMULUS) additions — appended record

Stage 2 of 6 (STIMULUS).  Files written: `i2c_driver.py`, `i2c_sequencer.py`,
`i2c_sequences.py`.  The RTL, spec, reference model, plan, and stage-1 files
(`i2c_pins.py`, `i2c_transaction.py`) were not modified.  The following items
EXTEND this contract; none alter the §1..§12 binding fields.

### 13.1 New ConfigDB key: `"i2c_driver"` (KEY_I2C_DRIVER)

Stage 1 locked exactly two keys (§6).  The stimulus stage adds one more
(because it shares a single component handle with flow/orchestrated
sequences); the §6 rule "no other keys may be invented without extending this
file" is satisfied by this record:

| Key | Value type | Set by | Read by |
|---|---|---|---|
| `"i2c_driver"` (`KEY_I2C_DRIVER`, module `i2c_driver.py`) | the `I2CDriver` instance | env/test stage (`ConfigDB().set(None, "*", KEY_I2C_DRIVER, self.driver)` in build_phase) | `I2CSequenceBase._get_driver()` in every flow sequence; optional convenience copy on `I2CSequencer.driver` set in connect_phase |

### 13.2 Driver exception semantics (bounded waits only)

`I2CDriver` never waits unboundedly.  Two exceptions implement the §7.3
"hung transaction" reporting (the corrupted RTL triggers them for every
data-path transaction — that is the intended catch path, not a bench bug):

- `I2CDriverTimeout(stage, message, item)` — stage `"start-acceptance"`
  (busy did not rise within `START_TIMEOUT_CYCLES`) or `"done-pulse"` (no
  done 0→1 edge within `DONE_TIMEOUT_CYCLES`).  In item mode
  (`run_phase`) the driver unblocks the requesting sequence via
  `seq_item_port.item_done()` before re-raising so the test fails loudly
  instead of stalling.
- `ScenarioCheckFailure(message, expected, observed)` — raised by
  `I2CDriver.expect_outputs()` when a plan `expect` action does not hold at
  its sample point.  This is a stimulus-stage scenario expectation,
  distinct from the always-running protocol checker coroutines the
  checking stage adds.

### 13.3 Driver public flow task API (timed scenarios)

Directed scenario (TC-01..TC-13), timed corner cases, and the randomized
sequence call the driver's async tasks directly rather than sending items:

`assert_reset(hold_cycles)`, `deassert_reset(settle_cycles)`,
`reset_phase(hold_cycles, settle_cycles)`, `settle(cycles)`,
`start_transaction(item, offer_cycles)`, `drive_slave_response(item, *,
addr_ack, data_ack, mid_transaction)`, `run_transaction(item, *, addr_ack,
data_ack, mid_transaction)`, `complete_transaction(item)`,
`pulse_start_while_busy(item, hold_cycles)`, `expect_outputs(levels, *,
wait_cycles, description)`.

- Completion is keyed on the done 0→1 pulse (wire = `busy` rise, §7.1/§7.3);
  the done watcher is armed ONLY after acceptance and never before, and for
  `run_transaction`/`drive_transaction` it is armed before the slave
  timeline is driven so the pulse cannot be missed on a repaired RTL.
- `addr_ack`/`data_ack` per-phase overrides exist for directed TC-08 and
  corner `missing_data_ack` (item-level NACK alone cannot distinguish
  phases).  `mid_transaction` is an `async def hook(driver)` invoked right
  after the address-ACK window (TC-10 illegal start-while-busy; randomized
  mid-resets are implemented directly by the random sequence instead).
- The slave-side `sda_in` timeline is placed against the intended FSM
  advance schedule (spec §5/§6, reference model) with one FSM advance per
  `CLK_DIV` cycles: acceptance at advance 0, address bits advances 1..9,
  ADDR_ACK sample at advance 10, data phase advances 11..18, write
  DATA_ACK / read READ_ACK sample at advance 19, STOP at advance 20
  (module constants `ADV_ACCEPT`/`ADV_ADDR_ACK`/`ADV_DATA_PHASE_START`/
  `ADV_DATA_ACK`/`ADV_STOP`).  This is an estimative timeline, NOT a locked
  cycle contract: completion is always the done pulse.

### 13.4 Flow vs item execution split

- Item mode: plain `I2CTransaction`s through the sequencer
  (`start_item`/`finish_item`) are pulled by the driver's `run_phase` and
  run to completion (`drive_transaction`).  Used by the corner cases that
  need no per-phase control or reset injection.
- Flow mode: sequences call the driver tasks directly for reset injection,
  per-phase ACK control, mid-transaction hooks, and scenario `expect`
  actions.  Used by all directed scenarios and the synchronized corners
  (`missing_data_ack`, `reset_mid_transaction`, `clk_div_min`).

`I2CSequencer` (`i2c_sequencer.py`) fetches `dut`/`i2c_pins` from ConfigDB
in `build_phase` and holds the shared driver reference as `I2CSequencer.driver`
(set by the env in connect_phase; the ConfigDB `"i2c_driver"` key remains the
authoritative path).

### 13.5 Env-var knobs consumed by stimulus (family convention, §11)

| Variable | Default | Meaning |
|---|---|---|
| `I2C_CLK_DIV` | `CLK_DIV_DEFAULT` (4) | DUT divider used to place the slave timeline (one FSM advance per CLK_DIV cycles; planning embedding; worker `-G` overrides may feed it) |
| `I2C_CLK_PERIOD_NS` | 10.0 | clock period used for `latency_cycles` measurement |
| `I2C_RANDOM_ITEMS` | 100 | number of generated transactions in `I2CRandomSequence` |
| `I2C_SEED` | unseeded | replay seed for the randomized sequence (plan §9-ish replay requirement) |
| `I2C_MID_RESET_PB` | 0.05 | per-transaction probability of injecting a mid-transaction reset (1..8 cycles) in the randomized sequence |

### 13.6 Directed scenario registration (self-checked)

`i2c_sequences.py` maps `PLANNED_DIRECTED_IDS` (TC-01..TC-13) 1:1 onto
`DIRECTED_SEQUENCE_CLASSES` via `SCENARIO_ID` class attributes;
`assert_directed_scenario_ids()` verifies the exact set match (duplicates,
missing, or extra ids raise `ValueError`).  Corner-case classes and
`I2CRandomSequence` deliberately carry `SCENARIO_ID = None`.

### 13.7 Watchdog placement (deferred by design)

The global watchdog (§11, `WATCHDOG_CYCLES` / `I2C_WATCHDOG_CYCLES`) is NOT
created in this stage.  Every driver wait is individually bounded (§13.2), so
stimulus alone cannot stall the simulator; the always-running watchdog is a
test_top/integration-stage responsibility and must remain that way.  Note
`I2CPins` only defines `RESET_CYCLES`/`SETTLE_CYCLES`/`START_TIMEOUT_CYCLES`/
`DONE_TIMEOUT_CYCLES`/`WATCHDOG_CYCLES`; the driver reads the first four via
`i2c_pins` imports and `I2C_CLK_DIV`/`I2C_CLK_PERIOD_NS` via os.environ, as
documented above.

---

## 14. Observation stage (OBSERVATION) additions — appended record

Stage 3 of 6 (OBSERVATION).  Files written: `i2c_monitor.py`, `i2c_agent.py`.
The RTL, spec, reference model, plan, and the stage-1/stage-2 files were not
modified.  The following items EXTEND this contract; none alter the binding
§1..§13 fields, pins, keys, or semantics.

### 14.1 Monitor analysis ports (published events)

`I2CMonitor` (`i2c_monitor.py`) is a passive pyuvm `uvm_monitor` that only
*reads* pins via the shared `I2CPins` handle (never drives) and publishes on
three `uvm_analysis_port`s (consumers connect directly to
`agent.monitor.<port>`; the agent defines no forwarding ports):

| Port | Value type | Payload |
|---|---|---|
| `ap` | `I2CTransaction` | One published item per **completed** transaction, in completion order.  Fields are exactly CONTRACT.md §5: stimulus fields sampled from the DUT inputs at the offer; observed-output fields strictly sampled at the completion point; `txn_id` (monitor-local, see §14.3) and `latency_cycles`.  `slave_ack`/`read_data` are TB-side *intent* fields, NOT pin-observable, and are left at their constructor defaults — the scoreboard must not derive ACK expectations from monitor items alone (it owns the reference-model comparison). |
| `hung_ap` | `I2CHungTransaction` | Structured "hung transaction" report (never a pass): a bounded wait elapsed (`HUNG_STAGE_START_ACCEPTANCE` = busy never rose within `START_TIMEOUT_CYCLES` of an offer; `HUNG_STAGE_DONE_PULSE` = no done 0→1 pulse within `DONE_TIMEOUT_CYCLES` of acceptance) or the completion sample carried X/Z (`HUNG_STAGE_COMPLETION_SAMPLE`).  Observed fields hold the DUT outputs sampled when the bound elapsed (non-strict).  Later stages must convert these into test failures / defect reports; the monitor itself does not abort the test (driver bounded-wait exceptions + watchdog + scoreboard/assertions own failing). |
| `reset_ap` | `I2CResetEvent` | Reset edge notifications: `kind` `"asserted"` (rst_n 1→0) and `"deasserted"` (0→1); `in_flight`/`dropped_transaction` record whether a transaction was active at assertion (CONTRACT.md §11: an in-flight transaction is **dropped** — no `ap` item is published for it); `edge_ns` is sim time of the sampled edge.  These are the plan's "reset events raised by the monitor" (coverage `cg_control_protocol`). |

### 14.2 Monitor observation model (binding interpretation of §7)

- **Offer** = the `start` input sampled high while the monitor is idle.  If
  `busy` is already high when idle, the monitor treats that as an
  already-accepted transaction (inexorable offer) and snaps `start=1`.
- **Acceptance** = `busy` rising 0→1, bounded by `START_TIMEOUT_CYCLES`.
- **Completion point** = the rising edge on which `done` makes a 0→1 pulse
  after acceptance (armed only after acceptance, never before);
  `I2CPins.sample_outputs_strict()` rejects X/Z there.
- Sampling is an `async def` coroutine synchronized via
  `await RisingEdge(pins.clk)`; no cycle-exact intermediate checking is done
  (CONTRACT.md §7.2).
- A reset assertion during any wait publishes the reset event and abandons
  the current offer/in-flight item (no `ap` item).

### 14.3 Additional metadata / side attributes on published items

- `txn_id`: the **monitor owns its own monotonic counter** (independent of
  sequence-side ids), because monitor items are reconstructed from pins and
  cannot know the requesting sequence's id.  The scoreboard must treat
  monitor `ap` items as an in-order stream keyed by these ids; hung/reset
  events create gaps (no 1:1 monitor-item ↔ sequence-item pairing, §11).
- `item._stream_trace`: monitor-only side attribute (NOT a §5 field) — a
  list with one dict per clock cycle from acceptance onward
  (`sda`, `scl` resolved bus levels; `sda_out`, `sda_oe`, `scl_out`,
  `scl_oe` raw drive controls).  Present on both completed and hung items;
  feeds the plan's `stream_checker` (scoreboard stage).

### 14.4 `I2CAgent` (`i2c_agent.py`)

Encapsulates the stimulus stage's `I2CDriver`/`I2CSequencer` and this
stage's `I2CMonitor`:

- `is_active` follows the standard `uvm_agent` convention (base
  `uvm_agent.build_phase` reads the ConfigDB `"is_active"` key, default
  `UVM_ACTIVE`).  Active agents build sequencer + driver + monitor; passive
  agents build only the monitor (monitoring is always on).
- `connect_phase`: `driver.seq_item_port.connect(sequencer.seq_item_export)`
  and the §13.1 convenience copy `sequencer.driver = driver`.
- The ConfigDB key `"i2c_driver"` (`KEY_I2C_DRIVER`) is still set exactly
  once by the env/test stage (§13.1) — the agent does not set it.

### 14.5 Env-var knobs added by this stage

| Variable | Default | Meaning |
|---|---|---|
| `I2C_START_TIMEOUT_CYCLES` | `START_TIMEOUT_CYCLES` (64) | monitor's bounded wait for `busy` rise after an offer |
| `I2C_DONE_TIMEOUT_CYCLES` | `DONE_TIMEOUT_CYCLES` (2048) | monitor's bounded wait for the `done` pulse after acceptance |

## 15. Scoreboard stage (SCOREBOARD) additions — appended record

(no §1–§14 changes; still only the `"dut"` and `"i2c_pins"` ConfigDB keys,
§6)

Files added in this stage (flat Python modules in this `tb/` directory, same
import convention as stage 1):

- `i2c_scoreboard.py` — `I2CScoreboard(uvm_scoreboard)`, the plan's
  `scoreboard_reference_model_strategy` implementation.
- `i2c_reference_model.py` — **verbatim copy** of the golden reference
  `benchmarks/i2c_benchmark_corrupted/i2c_reference_model.py`
  (byte-identical; `md5sum 0d24096f0795fee2897209ee426c3080` checked at copy
  time).  Copied so the TB imports the reference by bare name under the
  flat-module convention and never depends on runtime filesystem paths; the
  benchmark file remains the canonical source (re-copy if it ever changes).
  `write_transaction`, `read_transaction`, `make_address_byte`,
  `address_bits`, `byte_bits`, and `expected_write_bytes` are the ONLY
  protocol expectations in the environment — nothing in the TB reimplements
  I2C (§8 holds unchanged).

Scoreboard behavior (implements `scoreboard_reference_model_strategy`):

- `build_phase` reads the shared `"dut"` and `"i2c_pins"` ConfigDB keys
  (§6) and builds three unbounded `uvm_tlm_analysis_fifo`s: `obs_fifo`
  (completed items), `hung_fifo` (hung reports), `reset_fifo` (reset
  events).  A missing `"i2c_pins"` handle raises (the pin sampler and
  intent recovery cannot run without it).
- Wiring (done by the ENV in its connect phase, stage 6):
  `scoreboard.connect_monitor(monitor)` accepts the agent's monitor or an
  agent object (resolved via `.monitor`) and connects the three monitor
  analysis ports `ap` / `hung_ap` / `reset_ap` to the three FIFO
  `analysis_export`s under pyuvm 5.0.0's §14.1 broadcast model.
- `run_phase` starts four background coroutines with public Cocotb 2.1.0
  `cocotb.start_soon` — completed-item consumer, hung consumer, reset
  consumer, and a per-cycle pin sampler into a bounded ring
  (`RING_SIZE = max(8192, 4*DONE_TIMEOUT_CYCLES + 128)`) — and `await`s the
  completed-item consumer (which runs for the whole simulation).  The
  sampler records `sda_in`, `sda_out`, `sda_oe`, `scl_out`, `scl_oe`,
  resolved `sda_level`/`scl_level`, `done`, `busy`, `ack_error`,
  `rx_data`, `rst` on every rising edge; it feeds completion-edge
  detection, alignment, intent recovery, and hung-report bus symptoms.
- Per completed item (must be an `I2CTransaction`; anything else on `ap`
  is an explicit non-I2CTransaction error):
  1. order integrity — monitor `txn_id` must be strictly increasing;
     duplicates/reorders are `order_error_count` + `error_count`; gaps are
     debug-logged, not errors (ids are also consumed by hung reports and
     reset-dropped items, §14.3);
  2. completion edge — the newest unconsumed `done` 0→1 edge in the ring
     (retried across a few clock edges so the sampler can catch up); the
     acceptance global index is `cc - item.latency_cycles`;
  3. alignment — the acceptance index is cross-validated against the
     monitor's `_stream_trace` (six DUT-sourced fields per frame,
     trace[t] ↔ ring[accept_gi+1+t]) over offsets (0,-1,1,-2,2); if even
     the best offset exceeds the 2 % frame-mismatch tolerance
     (`ALIGNMENT_MAX_BAD_FRACTION`) the item is `intent_ungraded` and is
     never graded against a guessed intent;
  4. intent recovery (TB slave side, from the scoreboard's own `sda_in`
     sampler, majority window ±CLK_DIV/2): address ACK at advance 10,
     read-data bits at advances 11..18, write-data ACK at advance 19;
     `slave_ack`/`read_data` are never read from monitor items (§14.1);
  5. reference model (the ONLY oracle) — `read_transaction(...)` /
     `write_transaction(...)` called with the recovered intent; a
     `ValueError` is a `reference_rejected` error (ungraded);
  6. grading — transaction scoreboard (reference-dict diff on `start`,
     `address`, `address_byte`, `rw`, `tx_data`, `expected_ack_error`,
     `rx_data`, bool-vs-int normalized), stream checker (address bits at
     advances 2..9, write-data bits at 11..18, read-data drive-release
     via `sda_oe`), and control monitor (done one-cycle pulse, busy span
     + return-to-idle, `ack_error` low in the idle window before
     acceptance, STOP = SDA 0→1 while SCL high near the completion edge).
- Hung reports (`I2CHungTransaction`) are never graded as a pass:
  `hung_count` + `error_count` plus a structured report (stage, latency,
  outputs at expiry, and a bus-symptom summary of the last 64 ring cycles
  — which diagnoses the corrupted RTL's permanently-high `done` (DIS-15)
  and idle-flat `busy` (DIS-18/19)).  Reset events (`I2CResetEvent`) are
  counted (`reset_assert_count`/`reset_deassert_count`), never scored as
  transactions (an in-flight transaction is dropped, §11/§14.1).

Public counters (read by the env/test stage and `get_summary()` /
`get_summary_dict()`): `txn_count`, `graded_count`, `intent_ungraded_count`,
`match_count`, `mismatch_count`, `stream_error_count`,
`control_error_count`, `ack_error_count`, `order_error_count`, `hung_count`,
`reset_assert_count`, `reset_deassert_count`, `error_count`
(= order + hung + intent_ungraded + reference_rejected +
non-I2CTransaction).  Structured `discrepancy_reports` (capped at 1000)
hold per-defect records.  `run_phase` and all grading are plain Python on
public Cocotb 2.1.0 APIs (`cocotb.start_soon`, `RisingEdge`,
`get_sim_time`); no SystemVerilog anywhere.

**Grading semantic (locked):** on the corrupted RTL as-shipped `done`
never pulses (DIS-15) and the divider never advances (DIS-18/19), so the
completed-item path is correct-by-construction for a repaired variant, and
on the as-shipped RTL the environment observes mainly hung/reset events.
Where completed items ARE published, `mismatch_count > 0` is a *catch
report*, not by itself a test failure — the env/test stage (stage 6) grades
the plan's pass criteria from the counters above, treating
`order_error_count`, `hung_count`, `intent_ungraded_count`, and
`error_count` as real contract violations.

No new ConfigDB keys are introduced by this stage; no field in §1–§14 is
changed.  The scoreboard binds to the driver's ADV_* constants and the pins
helpers under guarded imports (a non-`__main__` import with cocotb/pyuvm
must succeed; the sandbox fallbacks serve only the plain-Python
self-check).

## 16. Coverage & assertions stage (COVERAGE_AND_ASSERTIONS) additions — appended record

(no §1–§15 changes; still only the `"dut"` and `"i2c_pins"` ConfigDB keys,
§6)

Files added in this stage (flat Python modules in this `tb/` directory, same
import convention as stage 1):

- `i2c_coverage.py` — `I2CCoverage(uvm_component)`, functional coverage on
  `cocotb_coverage.coverage` (`CoverPoint` / `CoverCross` / `coverage_db`).
- `i2c_assertions.py` — `I2CAssertions` plus module-level launchers: 15
  error-severity assertions as plain-Python checker coroutines (no SVA; a
  violation logs and raises `AssertionError`, failing the test at once) and
  the bounded clock-cycle watchdog.

### Coverage (`i2c_coverage.py`)

Covergroups, exactly per the plan's coverage section:

- `top.cg_transaction` — sampled once per completed (non-hung)
  `I2CTransaction` from the monitor `ap`:
  - `bin_slave_addr` bins `addr_min=0 / addr_mid=64 / addr_max=127`;
  - `bin_rw` bins `write=0 / read=1`;
  - `bin_tx_data` bins `data_zero=0 / data_mid=128 / data_max=255` —
    gated to writes; reads sample with `None` (matches no bin and clears
    `_new_hits`);
  - `bin_ack_error` bins `ack_ok=0 / ack_err=1`;
  - `bin_rx_data` bins `rx_zero=0 / rx_ones=255`;
  - crosses `cross_rw_ack_error`, `cross_addr_rw`, `cross_data_ack`.
- `top.cg_control_protocol` — control/protocol-level bins:
  `bin_done` (`pulse_seen`), `bin_busy` (`asserted`),
  `bin_start_while_busy` (`hit`), `bin_reset_injected` (`hit`),
  `bin_master_nack` (`ack/nack`), `bin_addr_ack` (`ack/nack`),
  `bin_data_ack` (`ack/nack`, writes only), cross `cross_addr_data_ack`
  (writes only).

Cross-sampling rule (cocotb-coverage 1.2.0) is locked in the module:
coverpoints are always sampled first (recording their `_new_hits`), then
the crosses, in the same event; a `None` sample matches no equality bin and
clears `_new_hits` so stale hits never contaminate a later cross.  All
sampling functions take positional arguments only.

Public sampling API (used by the coverage component and, where useful, the
env/test stage): `sample_transaction_cg(item)`,
`sample_control_ack(addr_ack, data_ack, master_nack)`,
`sample_control_done_seen()`, `sample_control_busy_seen()`,
`sample_control_start_while_busy_seen()`, `sample_control_reset_seen()`.
Reporting API: `transaction_coverage_percentage()`,
`control_coverage_percentage()`, `coverage_percentage()`,
`report_transaction_coverage(logger, bins=False)`,
`report_control_coverage(logger, bins=False)`, `report_coverage(logger,
bins=False)`; instance `get_summary_dict()` / `get_summary()` /
`convert2string()`.

`I2CCoverage` wiring and run contract:

- `connect_monitor(monitor)` subscribes the monitor's `ap` and `reset_ap`
  analysis ports (monitor or agent accepted, resolved via `.monitor`).  The
  hung stream (`hung_ap`) is NOT consumed by coverage — §14.3 semantics;
  the scoreboard owns it.
- `run_phase` starts three tasks with public Cocotb 2.1.0
  `cocotb.start_soon`: the completed-item consumer, the reset-event
  consumer (`sample_control_reset_seen` per `I2CResetEvent`), and a
  per-rising-edge pin sampler into a bounded ring using the scoreboard's
  layout (`RING_SIZE = max(8192, 4*DONE_TIMEOUT_CYCLES + 128)`, §15).
  `run_phase` awaits the primary consumer, which runs for the whole
  simulation (pyuvm terminates phase tasks at test end).
- ACK levels for `cg_control_protocol` are never read from monitor items
  (§14.1 same rule as the scoreboard); they are majority-sampled from
  `sda_in` in the ring at the driver's ADV_* slots (§13.8): address ACK at
  advance 10, write-data ACK at advance 19, master-NACK = `ack_error` at
  completion, using the same done-edge discovery and acceptance-index rule
  as §15 (`accept_gi = cc - item.latency_cycles`, done-edge search retried
  up to 3 clock edges).  A miss is counted as `ack_skipped` and logged, not
  an error.  A repaired-variant transaction with `item.latency_cycles`
  never completing within the simulation is dropped by the sample loop.

### Assertions (`i2c_assertions.py`)

`ASSERTION_SEVERITY` maps all 15 assertion names to `"error"` (asserted at
import time); `TXN_CHECKER_NAMES` (9) / `PIN_CHECKER_NAMES` (6) partition
them.  Any violation calls `_fail()` (log + raise `AssertionError`), so the
test fails at once; per-name violation counters feed `summarize()`
(`violations` dict).

- 6 always-on pin checkers (every relevant rising edge):
  `a_reset_clears_outputs` (busy/done/ack_error/rx_data zeroed on reset
  deassertion), `a_done_is_pulse` (done high for exactly one clock),
  `a_busy_spans_transaction` (busy rises at acceptance, holds through the
  done edge), `a_start_ignored_while_busy`, `a_stop_returns_idle`,
  `a_open_drain_release` (SDA/SCL released high in idle).
- 9 per-transaction checkers fed an internal `_CompletedTransaction` record
  (offer stimulus, offer/done global indices, monitor fields,
  majority-sampled ACK levels, `start_while_busy_observed`):
  `a_address_byte_correct`, `a_address_msb_first`, `a_rw_bit_correct`,
  `a_write_data_correct`, `a_rx_data_correct`, `a_addr_ack_error`,
  `a_data_ack_error`, `a_ack_error_clear_on_success`,
  `a_clk_div_advance_timing` (address-bit transition spacing must equal
  CLK_DIV per ADV_* slots).

`I2CAssertions` owns the same ring/edge machinery as the scoreboard and
coverage modules (one `_observe_stream` coroutine appends every rising edge;
accepted transactions are fanned out to the nine txn checkers via
`asyncio.Queue`s; reset aborts in-flight records, §11).  Launch contract
(stage 6): `launch_assertions(pins, log)` builds the instance from the
ConfigDB-shared pins unless given, calls `start()` (observer + every
checker via `cocotb.start_soon`), and returns it.  `stop()` / `summarize()`
are provided for the env/test stage.

Watchdog (provisioned here, armed by stage 6 per §13.7): `launch_watchdog(
pins=None, timeout_cycles=None, log=None)` returns a `cocotb.start_soon`
task (or `watchdog(pins, timeout_cycles, log)` for direct use) that counts
rising clock edges and raises `AssertionError` once the budget is exceeded,
so a hung FSM with a live clock cannot silently exhaust the simulation.
`timeout_cycles` defaults to `WATCHDOG_CYCLES` (global configured from
i2c_pins); the owner must `kill()` the task on normal completion.

**Grading semantic (locked):** as with §15, on the as-shipped corrupted RTL
the always-on pin checkers catch the injected defects directly —
`a_done_is_pulse` / `a_reset_clears_outputs` fire on DIS-15 (permanent
`done`), `a_busy_spans_transaction` / `a_open_drain_release` fire on
DIS-18/19 (divider stuck, busy idle-flat, outputs hardwired low) — while
the completed-item path (transaction covergroup + txn checkers, control
ACK bins) is correct-by-construction for a repaired variant.  Coverage
percentages are per-group numbers consumed by the env/test stage's plan
pass criteria; assertion violations are standalone pass/fail.

No new ConfigDB keys; no field in §1–§15 is changed.  Both modules bind to
the driver's ADV_* constants and the pins helpers under guarded imports (a
non-`__main__` import with cocotb/pyuvm/cocotb_coverage must succeed; the
sandbox fallbacks serve only the plain-Python `__main__` self-checks of
the pure helpers).

## 17. Integration stage (INTEGRATION) additions — appended record

### 17.1 Files written in this stage

| File | Purpose |
| --- | --- |
| `tb/i2c_env.py` | `I2CEnv(uvm_env)`: assembles agent + scoreboard + coverage + assertions; watchdog primitives; `WATCHDOG_MARGIN_CYCLES`. |
| `tb/i2c_test.py` | 15 pyuvm tests: `I2CBaseTest`, 13 directed scenario tests, `I2CCornerTest`, `I2CRandomTest`. |
| `tb/test_top.py` | cocotb entry (`MODULE = test_top`): clock/reset/ConfigDB, `run_test(..., keep_singletons=True)` under an outer bound. |
| `tb/Makefile` | Verilator + cocotb runnable flow; `UVM_TESTNAME` selects the test. |
| `tb/generation_manifest.yaml` | Runtime contract consumed by `workers/sim/run.py`. |
| `results/stage6_integration/stage6_consistency_checks.py` | Static consistency audit (no simulator required). |
| `checkpoints/uvm_integration.done` | Stage-completion marker. |

### 17.2 `I2CEnv` (`i2c_env.py`)

- `build_phase`: fetches the ConfigDB-shared pins (§6), creates
  `I2CAgent("i2c_agent", self)`, `I2CScoreboard("i2c_scoreboard", self)`,
  `I2CCoverage("i2c_coverage", self)` (import guarded: the class is defined
  only when both pyuvm and cocotb-coverage import; at simulation time it is
  always present), and calls `launch_assertions(pins=self.pins,
  log=self.logger)` to start the 15 plan assertion checkers (§16).
- `connect_phase`: (1) sets the `"i2c_driver"` key (§13.1) from
  `agent.driver` (with an error log if the driver is `None`), and
  (2) subscribes the monitor analysis ports to the scoreboard and coverage
  via `connect_monitor(self.agent)` (both accept the agent and resolve
  `.monitor`; §14.1/§15/§16).  It introduces **no** new ConfigDB keys.
- Watchdog primitives (budgets owned by the tests, §13.7/§17.4):
  `arm_watchdog(budget_cycles=None)` (defaults to the global
  `WATCHDOG_CYCLES`) and `disarm_watchdog()` wrap `launch_watchdog()`
  / `task.kill()`; arming is idempotent and disarming tolerates a missing
  task.

### 17.3 Clarification of §13.1 — driver key set in `connect_phase`

pyuvm 5.0.0 executes `build_phase` top-down: `I2CEnv.build_phase` runs
*before* `I2CAgent.build_phase`, so `agent.driver` does not exist yet when
the env builds.  The `"i2c_driver"` key is therefore set in
`connect_phase` (which runs after every `build_phase` has completed), a
justified clarification of the §13.1 wording ("exactly once in
build_phase").  It is still set **exactly once** per test, and no other code
writes the key.

### 17.4 Watchdog ownership and budgets

- The env owns the *watchdog primitive*; each TEST owns its *budget*.
- `I2CBaseTest.WATCHDOG_BUDGET_CYCLES` defaults to
  `WATCHDOG_MARGIN_CYCLES` (10000, defined in `i2c_env.py` — `i2c_pins.py`
  has no such constant for this design).  Directed scenarios arm it in
  `run_phase` and disarm in a `finally`.
- `I2CCornerTest` uses `6 * WATCHDOG_MARGIN_CYCLES` (60000); `I2CRandomTest`
  uses `20 * WATCHDOG_MARGIN_CYCLES` (200000).  These fit every legitimate
  scenario on a repaired RTL while still failing fast on a hang (the
  corrupted `div_cnt` stall grounds every data-path run well inside them).
- `test_top.py` additionally wraps `run_test` in a coarse
  `with_timeout(..., OUTER_BUDGET_NS, "ns")` bound with
  `OUTER_BUDGET_CYCLES = WATCHDOG_CYCLES` (300000) → 3000000 ns at
  `I2C_CLK_PERIOD_NS` = 10; a `SimTimeoutError` is re-raised after an error
  log.  This is independent of (and a superset of) the per-test cycle
  watchdog and the worker's OS timeout (§8/§13.7 backstops).

### 17.5 Test classes and scenario mapping (`i2c_test.py`)

- `I2CBaseTest(uvm_test)` implements the shared flow: `build_phase` creates
  `I2CEnv`; `run_phase` raises an objection, arms the budget, awaits
  `_run_scenario()`, disarms, drops the objection; `report_phase` grades the
  plan pass criteria from the scoreboard's public counters (§15:
  fail on `order_error_count`/`hung_count`/`intent_ungraded_count`/
  `error_count`, and on an empty graded stream unless
  `_require_graded_transactions` is False — TC-01), then logs coverage
  percentages, the assertions summary and the scoreboard summary.
  `mismatch_count` is a catch report only.
- The 13 directed classes map to `DIRECTED_SCENARIO_TESTS["TC-0x"]` and
  obey the **class-name parity rule**: `<Name>Test` ↔ `<Name>Sequence`;
  each implements `staticmethod get_sequence_class()` returning the sequence
  class **symbol**.  This is the single wiring point audited statically.
- `I2CCornerTest._run_scenario()` runs the 14 plan corner sequences
  (`I2C_CORNER_SEQUENCES` tuple) sequentially with a short drain between
  them.  `I2CRandomTest` uses `I2CRandomSequence()` and fixes deterministic
  defaults via `os.environ.setdefault("I2C_SEED", "24601")` and
  `("I2C_RANDOM_ITEMS", "100")` so failures are reproducible; explicit
  environment overrides still win.
- On the as-shipped corrupted RTL every data-path directed/corner/random
  scenario fails as designed: `I2CDriverTimeout` (§13.2) on the never-
  advancing `div_cnt`/IDLE-stuck FSM, `ScenarioCheckFailure` on the
  permanently-high `done` (§9 DIS-15) and idle `busy` expectations, and
  plan-assertion violations (§16) — the intended catch reports.

### 17.6 `test_top.py` entry point

Single `@cocotb.test()` coroutine: builds `I2CPins`, drives a pre-clock idle
state (`drive_reset(True)`, `release_inputs()`), starts `make_clock(dut)`,
applies the synchronous reset (`RESET_HOLD_CYCLES` = `RESET_CYCLES`, then
`RESET_SETTLE_CYCLES` = `SETTLE_CYCLES`), sets the two §6 ConfigDB keys
(`KEY_DUT`, `KEY_DUT_PINS`) with `ConfigDB().set(None, "*", key, value)`,
imports `i2c_test` for factory registration, then
`uvm_root().run_test(test_name, keep_singletons=True)` — **required** so
pyuvm 5.0.0 does not clear the ConfigDB singleton before `build_phase` —
under the §17.4 outer timeout; `report_coverage(logger=print)` runs in the
`finally`.  `UVM_TESTNAME` selects the test (default
`ResetIdleCheckTest`).

### 17.7 Build / run contract

`Makefile`: `SIM = verilator`, `TOPLEVEL = i2c_master`, `MODULE = test_top`,
`VERILOG_SOURCES = /workspace/benchmarks/i2c_benchmark_corrupted/i2c_master.sv`,
`COMPILE_ARGS += --timing -Wno-fatal -Wno-WIDTH -Wno-CASEINCOMPLETE
-Wno-UNOPTFLAT -j 0`, `UVM_TESTNAME ?= ResetIdleCheckTest` (exported).
`generation_manifest.yaml`: `top_module: i2c_master`, `top_file`/compile
files = DUT RTL only, `python_test_module: test_top`, `test_classes` = the
15 test classes, `scenarios` = exactly `TC-01..TC-13` with `sequence`/`test`
class names (corner/random classes intentionally have no scenario entry,
§10).  `workers/sim/run.py` consumes the manifest and launches each test
class via `UVM_TESTNAME`.

### 17.8 Grading notes (append-only record)

- Failures (assertion `AssertionError`, `SimTimeoutError`, exit code ≠ 0)
  are **expected** on the as-shipped corrupted RTL for every data-path test
  and for TC-01; the runbook for downstream stages (diagnosis/repair) treats
  each caught failure as a structured defect signal, not a harness bug.
- The static consistency audit (`results/stage6_integration/
  stage6_consistency_checks.py`) re-verifies §17.5/§17.7 mappings without a
  simulator; its checks and this section stay in sync.