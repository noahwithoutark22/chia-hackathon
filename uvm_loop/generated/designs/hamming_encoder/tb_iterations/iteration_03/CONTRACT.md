# hamming_encoder Verification Contract (CHIA stage 1)

Authoritative conventions for every later stage of the generated
cocotb + pyuvm testbench.  Later stages **must** read this file instead of
re-deriving conventions.  Any pin, field, key, width, or timing rule listed
here is binding.

Everything below is derived from these authoritative inputs:

- RTL:            `benchmarks/hamming_encoder/hamming_encoder.sv`
- RTL info:       `generated/designs/hamming_encoder/rtl/rtl_info.json`
- Specification:  `benchmarks/hamming_encoder/spec.md`
- Reference model:`benchmarks/hamming_encoder/ref_model.py`
  (`hamming_encode(data_in, data_width, secded=False)` and
  `HammingParams.compute(data_width, secded)`)
- Verification plan: `generated/designs/hamming_encoder/plans/verification_plan.yaml`

The testbench is implemented entirely in Python (cocotb + pyuvm).  There is
**no** SystemVerilog interface and **no** SystemVerilog UVM code (no SV
classes, no covergroups, no SVA).  The only SystemVerilog in the project is
the DUT RTL, which is never modified or duplicated.

---

## 1. Top module

- Top module name: **`hamming_encoder`**
- RTL file: `benchmarks/hamming_encoder/hamming_encoder.sv`
- cocotb top handle: the `dut` argument received by the Python entrypoint
  *is* `hamming_encoder`, elaborated with the test's `DATA_WIDTH` /
  `SECDED` parameter values.
- Parameter-default metadata caveat (plan `DISC-1`): `rtl_info.json`
  reports `SECDED` default `'1'` and `CODE_WIDTH` default `'1'`, which do
  **not** match the RTL (`parameter bit SECDED = 1'b0`) or spec.md (default
  0).  The RTL and spec are authoritative.  Every test must set both
  `DATA_WIDTH` and `SECDED` explicitly at elaboration and read the active
  geometry from `HammingConf` (ConfigDB), never from `rtl_info.json`
  defaults.

## 2. DUT pin map (direction, width, exact access)

Pin access is **always** through the cocotb `dut` handle, either directly
(`dut.<pin>`) or via the `HammingDutPins` helper in `tb/dut_helper.py`
(which wraps `dut.<pin>` 1:1).  The DUT has exactly two pins.

| Pin | Direction | Width | Access | Notes |
|---|---|---|---|---|
| `data_in` | input | `DATA_WIDTH` | `dut.data_in` | Data word to encode; any `DATA_WIDTH`-bit pattern is valid. |
| `code_out` | output | `CODE_WIDTH` | `dut.code_out` | Encoded Hamming (or SECDED) codeword; purely combinational, latency 0. |

Derived widths (spec.md §2.2, ref model `HammingParams`):

- `PARITY_BITS` (R) = smallest R with `2**R >= DATA_WIDTH + R + 1`.
- `BASE_WIDTH` = `DATA_WIDTH + PARITY_BITS`.
- `CODE_WIDTH` = `BASE_WIDTH + (SECDED ? 1 : 0)`.

Default elaboration `DATA_WIDTH=4, SECDED=0` (Hamming(7,4)): `data_in` is 4
bits, `code_out` is 7 bits.  `DATA_WIDTH=4, SECDED=1` (Hamming(8,4)
SECDED): `code_out` is 8 bits.

There are **no inouts** and **no other pins**.  In particular the DUT has
**no `clk` and no reset port**, so `dut.clk` and `dut.tb_reset` do not
exist and must never be referenced.

## 3. Clock and reset semantics (testbench-virtual)

The DUT is purely combinational: `code_out` is a pure function of the
current `data_in` and is never affected by any reset.  The plan's clock and
reset are testbench-only scaffolding:

### `clk` — virtual testbench reference clock

- Name `clk`, type `posedge`, **not a DUT pin** (`clk_is_virtual = True`).
- Purpose: sequence stimulus application and output sampling only.
- Implementation (binding for later stages): there is no `dut.clk` to run a
  cocotb `Clock` on and no `RisingEdge(dut.clk)` to wait for.  A reference
  *cycle* is one `cocotb.triggers.Timer(clock_period_ns, units="ns")` wait.
  The shared helper is `await wait_clock_cycles(clkrs, n)` in
  `tb/dut_helper.py` (lazily imports cocotb).
- The "posedge of `clk`" is the instant a cycle Timer expires.  Stimulus is
  applied at a cycle boundary; outputs are sampled at a later boundary
  after the combinational settle (section 8).  Driver/monitor/sequences
  must **not** use `RisingEdge`/`FallingEdge`/`ClockCycles` on `dut.clk`.

### `tb_reset` — virtual environment reset

- Name `tb_reset`, polarity **active-low**, type **asynchronous**, **not a
  DUT pin** (`reset_is_virtual = True`); `reset_assert_value = 0`.
- Purpose: initialize the verification environment (predictor, scoreboard,
  functional coverage) at the start of each test / configuration block.
  It never drives or clears the DUT: `code_out` must not be used as a
  reset oracle.
- Implementation: asserting `tb_reset` is a *logical phase* — components
  reinitialize their own state (per the test/sequence flow defined by later
  stages) while the environment paces `reset_cycles` reference cycles
  (`wait_clock_cycles(clkrs, reset_cycles)`, plan uses 2 cycles).  There is
  no pin to toggle.

### `ClockReset` descriptor (ConfigDB `KEY_CLK_RST`)

Frozen dataclass in `tb/dut_helper.py`, the single shared description:
`clock_name="clk"`, `reset_name="tb_reset"`,
`reset_polarity="active_low"`, `reset_type="asynchronous"`,
`clock_period_ns` (tb_top-chosen, default 10), `reset_assert_value=0`,
`clk_is_virtual=True`, `reset_is_virtual=True`.

## 4. Elaboration parameters and geometry

| Parameter | Type | Default | Test values (plan) | Notes |
|---|---|---|---|---|
| `DATA_WIDTH` | int | 4 | 1, 4, 8, 11, 16 | Number of data bits K; must be > 0. |
| `SECDED` | int (0/1) | 0 | 0, 1 | 1 = add overall-parity bit (SECDED). |

`PARITY_BITS`, `BASE_WIDTH`, `CODE_WIDTH` are derived localparams — never
set directly.  The bench obtains the active geometry through
`HammingConf` (ConfigDB `KEY_CONF`, computed by the reference model's
`HammingParams.compute`, so the geometry is never re-derived by hand).
Plan geometry table (spec §4.3):

| DATA_WIDTH | PARITY_BITS | CODE_WIDTH (SECDED=0) | CODE_WIDTH (SECDED=1) |
|---|---|---|---|
| 1 | 2 | 3 | 4 |
| 4 | 3 | 7 | 8 |
| 8 | 4 | 12 | 13 |
| 11 | 4 | 15 | 16 |
| 16 | 5 | 21 | 22 |

## 5. Transaction / sequence_item (`tb/transaction.py`)

Class: **`HammingTransaction`** (pyuvm `uvm_sequence_item`; import as
`from tb.transaction import HammingTransaction`).  All fields are plain
Python attributes.

### Stimulus field (driven by the driver from the item)

| Field | Type | Width | Default after `randomize()` |
|---|---|---|---|
| `data_in` | int | `DATA_WIDTH` | uniform `0 .. (1 << DATA_WIDTH) - 1` |

### Observed-output field (filled by the monitor after combinational settle)

| Field | Type | Width | Meaning |
|---|---|---|---|
| `code_out` | int | `CODE_WIDTH` | `dut.code_out` sampled after settle |

### Elaboration-configuration attributes (NOT DUT-port fields)

Recorded on every item so the scoreboard can call the reference model with
the right generator constants:

| Attribute | Type | Meaning |
|---|---|---|
| `data_width` | int | `DATA_WIDTH` of the elaboration that created the item |
| `secded` | int (0/1) | `SECDED` of the elaboration |
| `code_width` | int | derived `CODE_WIDTH` (used for sampling masks) |

No clock/reset fields (structural signals, UVM rules).  Items are 1:1 with
DUT encode operations, so a monitor item pairs 1:1 with its sequence item
(no handshake, no aborted transactions).

API:

- `HammingTransaction(data_width=..., secded=...)` — optional per-item
  geometry override.
- `HammingTransaction.configure(data_width=..., secded=...)` — classmethod
  setting class defaults for an elaboration (call once per test).
- `randomize(**constraints)` — generates `data_in`; constraints override
  `data_in`/`code_out`; unknown or non-randomizable names raise
  `AttributeError`.
- `check_inputs_valid()` — mirrors the reference model's width validation
  (`0 <= data_in < 2**data_width`, `data_width > 0`).
- `__str__` — human-readable binary + hex dump for logging.

## 6. ConfigDB keys (exact keys, exact value types)

pyuvm `ConfigDB()` is the only sharing mechanism.  Keys are defined as
constants in `tb/dut_helper.py` and are the **only** keys used.

Set from tb_top/test:

```python
ConfigDB().set(None, "*", KEY_DUT, dut)                    # cocotb handle
ConfigDB().set(None, "*", KEY_DUT_PINS, HammingDutPins(dut))
ConfigDB().set(None, "*", KEY_CLK_RST, ClockReset(...))
ConfigDB().set(None, "*", KEY_CONF, HammingConf.compute(data_width, secded))
```

Get from any component:

```python
dut   = ConfigDB().get(self, "", KEY_DUT)
pins  = ConfigDB().get(self, "", KEY_DUT_PINS)
clkrs = ConfigDB().get(self, "", KEY_CLK_RST)
conf  = ConfigDB().get(self, "", KEY_CONF)
```

| Key constant | Key string | Value type | Contents |
|---|---|---|---|
| `KEY_DUT` | `"dut"` | cocotb module handle | Top-level `dut` for `hamming_encoder`. |
| `KEY_DUT_PINS` | `"hamming_encoder.dut_pins"` | `HammingDutPins` | Canonical pin access (`drive_data_in`, `sample_code_out[_strict]`, `sample_into_item`, pin properties). |
| `KEY_CLK_RST` | `"hamming_encoder.clk_rst"` | `ClockReset` (frozen dataclass) | Virtual clock/reset descriptor (section 3). |
| `KEY_CONF` | `"hamming_encoder.conf"` | `HammingConf` (frozen dataclass) | Active elaboration geometry (`data_width`, `secded`, `parity_bits`, `base_width`, `code_width`). |

No other ConfigDB keys may be invented by later stages.  The concrete
`set`/`get` call form depends on the installed pyuvm version (the pyuvm-5.x
no-shim flow shown above is the target; if the simulator image pins pyuvm
3.0.0, the integration stage applies the same shims the FIFO bench uses) —
the keys and value types above are fixed regardless.

## 7. Reference model (behavioral oracle)

- File: `benchmarks/hamming_encoder/ref_model.py`.
- Function: `hamming_encode(data_in: int, data_width: int, secded: bool = False)
  -> (code_out: int, params: HammingParams)`, plus
  `HammingParams.compute(data_width, secded)`.
- The scoreboard must call this function directly (or through a thin
  `tb/ref_model.py` adapter that only forwards `(data_in, data_width,
  secded)` and returns `(code_out, params)`).  It must **not** reimplement
  or reverse-engineer the algorithm, and a mismatch must never cause the
  model to be adapted.
- Expected `code_out` is compared bit-for-bit against the sampled DUT value
  after masking to `conf.code_width` (or `params.code_width`).
- `data_in` and `data_width`/`secded` (generator constants) are the exact
  reference-model arguments; argument order is `(data_in, data_width,
  secded)`.

## 8. Timing / sampling rules

Derived from the purely combinational, latency-0 DUT (plan CLOCK_RESET and
`scoreboard_reference_model_strategy`):

- A transaction is one encode operation.  The driver writes `data_in` at a
  virtual-cycle boundary (`wait_clock_cycles(1)` to reach the next
  boundary); `code_out` settles combinationally (latency 0).
- **Sampling rule:** the monitor samples `code_out` after the driver's
  drive has had one full reference cycle to settle
  (`sample_into_item(item)` / `sample_code_out_strict`), i.e. one-cycle
  sampling latency relative to the drive.  This matches the plan's "wait
  one testbench clock for combinational settle before sampling" and the
  directed scenario check step.
- The scoreboard compares against
  `hamming_encode(item.data_in, item.data_width, item.secded)` at the same
  timestamp; any bit difference is an immediate failure.
- Back-to-back transactions are allowed (no handshake; the DUT never
  stalls).
- `code_out` must never contain X/Z after settle; the strict sampler
  raises `AssertionError` if it does (plan pass criteria "no X/Z values on
  code_out after settle").
- Functional coverage is sampled at the virtual `posedge` (cycle boundary)
  once per driven vector, matching plan `sample_on: posedge`.

## 9. Cross-cutting rules for later stages

- **No SystemVerilog UVM**: no SV `interface`, no SV UVM classes, no SV
  covergroups, no SVA.  Only Python.  Do not modify or duplicate the DUT
  RTL, the spec, or the plan.
- Pin access only via `dut.data_in` / `dut.code_out` or the shared
  `HammingDutPins`; never `dut.clk` / `dut.tb_reset`.
- Functional coverage uses `cocotb-coverage`
  (`cocotb_coverage.coverage.CoverPoint` / `CoverCross`, sampled through
  the shared `coverage_db`), covering the plan's `cg_hamming_encoding`
  bins and crosses.
- Assertions are plain Python `assert`/failure flags in always-running
  checker coroutines started with `cocotb.start_soon`, running
  concurrently with the environment and failing the test immediately.
  Plan `useful_assertions`: `data_width_positive`,
  `output_matches_reference_model`, `secded_overall_even_parity`,
  `data_bits_preserved_in_codeword`, `parity_cover_set_definition`.
- A watchdog is required: an always-running coroutine (or a bounded
  `cocotb.triggers.with_timeout` wrapper around the test body) that fails
  the test if it does not finish within a bounded number of reference
  cycles, so a hung test cannot silently exhaust the whole simulation run.
- Object sharing between components only through the section 6 ConfigDB
  keys.  Do not invent ports, parameters, widths, or clocks.

## 10. Addendum (stage 3, OBSERVATION): HammingDutPins extension

Stage 3 adds three public methods to `HammingDutPins` (`tb/dut_helper.py`,
no existing signature changed, backward-compatible):

- `sample_data_in(data_width=None) -> int` — mirror of `sample_code_out`
  for the stimulus pin: returns `data_in` as an int (X/Z read as 0 for
  determinism); `data_width` defaults to the default elaboration width (4).
- `sample_data_in_strict(data_width=None) -> int` — strict stimulus sampler:
  raises `AssertionError` if `data_in` carries any X/Z bit before coercion,
  closing the same false-pass hole the strict output sampler closes on
  `code_out` (an undriven input must not be silently coerced to 0).
- `pins_driven() -> bool` — True when both `data_in` and `code_out` carry
  no X/Z bit; the monitor polls this per cycle to skip the undriven
  pre-first-drive / reset window and to lock onto the first genuine drive.

The internal helper `_check_outputs_are_driven` was generalized to
`_check_pins_are_driven(raw_pins, source="output"|"input")`; callers and
the module self-check were updated accordingly.

Stage 3 also adds two components (imported as `tb.monitor.HammingMonitor`,
`tb.agent.HammingAgent`):

- `HammingMonitor` (passive `uvm_monitor`, own `uvm_analysis_port` `ap`):
  paces with `wait_clock_cycles(clkrs, 1)` (never `RisingEdge(dut.clk)`),
  skips un-driven windows, locks onto the first driven sample (the settle
  boundary of the first drive, i.e. the one-cycle sampling latency of
  section 8), and publishes exactly one `HammingTransaction` per settle
  boundary whose `(data_in, code_out)` pair differs from the previous
  cycle's pair.  `data_in` is filled with `sample_data_in_strict`,
  `code_out` with `sample_into_item` (strict).  ConfigDB keys as section 6.
- `HammingAgent` (active `uvm_agent`): owns `sequencer`, `driver`,
  `monitor`; connects `driver.seq_item_port` ->
  `sequencer.seq_item_export`; exposes `monitor_ap` as an alias of
  `monitor.ap`.

---

## 11. Addendum (stage 4, SCOREBOARD): HammingScoreboard

Stage 4 adds `tb/scoreboard.py` (`HammingScoreboard`, a pyuvm
`uvm_scoreboard`) and a byte-for-byte copy of the reference model at
`tb/ref_model.py`.  It does not change any key, pin, field, or value
defined above, and it invents **no** new ConfigDB keys or DUT ports.

### 11.1 Reference model copy (`tb/ref_model.py`)

`benchmarks/hamming_encoder/ref_model.py` is copied verbatim (byte-for-byte)
to `tb/ref_model.py` so the arithmetic/behavior oracle sits beside the
other `tb/` modules (same convention as the FIFO bench).  The copy is
never edited and is the single source for expected results.  The
scoreboard imports `hamming_encode` and `HammingParams` from it (falling
back to `benchmarks.hamming_encoder.ref_model` and then a bare
`ref_model` import for alternate run layouts) and calls
`hamming_encode(data_in, data_width, secded)` with the exact argument
order of section 7.  It never reimplements or reverse-engineers the
model, and a DUT mismatch never adapts it.

### 11.2 Scoreboard component and wiring

- `tb/scoreboard.py` defines `HammingScoreboard`, a `pyuvm.uvm_scoreboard`
  subclass default-named `hamming_scoreboard`.
- `build_phase` resolves the ConfigDB entries of section 6 with the exact
  section-6 call form (`ConfigDB().get(self, "", KEY_...)`) for
  `KEY_DUT_PINS`, `KEY_CLK_RST` and `KEY_CONF`; creates a
  `uvm_tlm_analysis_fifo` named **`hamming_analysis_fifo`** and exposes
  `HammingScoreboard.analysis_export = analysis_fifo.analysis_export`.
- Wiring is owned by the env stage (later stage):
  `agent.monitor_ap.connect(scoreboard.analysis_export)`; the scoreboard
  itself performs no connects.
- `run_phase` loops over `await analysis_fifo.get()` and checks each item
  immediately (no internal queueing beyond the FIFO).

### 11.3 Comparison alignment (combinational, latency 0)

One monitor item is exactly one settled encode operation: `data_in` and
`code_out` were sampled at the same virtual-cycle boundary (section 8,
one-cycle sampling latency).  The scoreboard therefore applies the
single-cycle combinational relationship -- **not** a pipeline::

    expected, params = hamming_encode(item.data_in, item.data_width, item.secded)
    mask = (1 << params.code_width) - 1
    compare (expected & mask)  vs  (item.code_out & mask)   # bit-exact

`params.code_width` width-checks and masks the sampled `code_out`
(plan `python_golden_predictor` / `sample_compare`).  Item geometry,
`HammingConf` (`KEY_CONF`) and `HammingParams` must all agree; any
disagreement raises `RuntimeError` (environment-setup bug).

### 11.4 Reset handling in the scoreboard

`tb_reset` is a logical phase with no DUT pin (section 3).  The predictor
is a pure function of each item and the monitor only publishes genuine
drives, so no reference state can go stale across a reset.  The
environment/tests stage MUST call `HammingScoreboard.reset_checker()`
once per tb_reset phase: it clears per-block accounting
(checked/passed/mismatch counters and the failure list) while preserving
the cumulative per-(DATA_WIDTH, SECDED) statistics that feed the
end-of-regression summary.  `code_out` is never used as a reset oracle.

### 11.5 Mismatch reporting and pass criteria

On any bit difference the scoreboard logs at error severity: `data_in`
(binary and hex), `DATA_WIDTH`, `SECDED`, expected `code_out`, actual
`code_out`, the differing bit indices (LSB-first) and a best-effort live
pin snapshot (same timestep as the item, so it shows the very pins the
item was sampled from); it then raises `AssertionError`, failing the
current test immediately (plan `error_reporting`: "count the error, fail
the current test").  `report_phase` emits the per-block summary plus the
cumulative per-configuration summary (checked / passed / mismatches) for
the whole regression.  Pass criterion: bit-exact match for 100% of
vectors in every exercised (DATA_WIDTH, SECDED) configuration, with no
X/Z after settle (enforced by the strict samplers of stage 3).

The always-running watchdog (section 9) remains owned by the stage-5
coverage/assertions module (as in the FIFO bench); the scoreboard does
not host it.