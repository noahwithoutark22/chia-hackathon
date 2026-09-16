# CONTRACT — axi_handshake cocotb+pyuvm Testbench

> **Every later stage reads this file instead of re-deriving conventions.**
> All values below are authoritative and must not be overridden.

---

## 1. Top Module

| Item | Value |
|------|-------|
| Top module name | `axi_handshake` |
| Top RTL file | `benchmarks/axi_handshake/axi_handshake.sv` |
| Parameters | *(none)* |

---

## 2. Clock & Reset

| Signal | DUT pin | Direction | Width | Type | Polarity / Edge |
|--------|---------|-----------|-------|------|-----------------|
| Clock | `clk` | input | 1 | logic | **posedge** (rising edge) |
| Reset | `rst_n` | input | 1 | logic | **active-low**, synchronous |

- `clk` is driven by the cocotb `Clock` helper (period to be set by test).
- `rst_n` is asserted low to reset, deasserted high to release.
- After reset the buffer is empty: `m_valid = 0`, `m_data = 0x00`, `s_ready = 1`.

---

## 3. DUT Pin Map

Every pin below is accessed via the cocotb `dut` handle exactly as written.

### Inputs

| Pin name | Width | cocotb access | Description |
|----------|-------|---------------|-------------|
| `clk` | 1 | `dut.clk` | System clock *(driven by cocotb Clock helper)* |
| `rst_n` | 1 | `dut.rst_n` | Active-low synchronous reset |
| `s_valid` | 1 | `dut.s_valid` | Source valid — asserted when s_data carries a valid payload |
| `s_data` | 8 | `dut.s_data` | 8-bit input payload `[7:0]` |
| `m_ready` | 1 | `dut.m_ready` | Downstream ready — asserted when consumer can accept output |

### Outputs

| Pin name | Width | cocotb access | Description |
|----------|-------|---------------|-------------|
| `s_ready` | 1 | `dut.s_ready` | DUT ready for input transfer |
| `m_valid` | 1 | `dut.m_valid` | Output valid — asserted when buffer holds valid output |
| `m_data` | 8 | `dut.m_data` | 8-bit output payload `[7:0]`, latency = 0 cycles |

---

## 4. Transaction / Sequence-Item Fields

Class: `AxiHandshakeTxn` (subclass of `pyuvm.uvm_sequence_item`)
Module: `transaction.py`

| Field | Direction | Type | Width | Maps to DUT pin |
|-------|-----------|------|-------|-----------------|
| `s_valid` | driver → DUT | `int` | 1 bit | `dut.s_valid` |
| `s_data` | driver → DUT | `int` | 8 bits | `dut.s_data` |
| `m_ready` | driver → DUT | `int` | 1 bit | `dut.m_ready` |
| `s_ready` | DUT → monitor | `int` | 1 bit | `dut.s_ready` |
| `m_valid` | DUT → monitor | `int` | 1 bit | `dut.m_valid` |
| `m_data` | DUT → monitor | `int` | 8 bits | `dut.m_data` |

Reference-model call signature (inputs must match these exact field names):

```python
s_ready, m_valid, m_data = ref_model.step(s_valid, s_data, m_ready)
```

---

## 5. ConfigDB Keys

All components obtain shared objects through pyuvm `ConfigDB` with these
exact key strings and value types:

| Key string | Value type | Set by | Used by |
|------------|------------|--------|---------|
| `"dut"` | `cocotb.handle.SimHandleBase` (the cocotb `dut` handle) | tb_top | driver, monitor, scoreboard |
| `"dut_helper"` | `dut_helper.DutHelper` instance | tb_top | driver, monitor, scoreboard, coverage |
| `"clock_period"` | `int` (nanoseconds) | tb_top / test | driver, sequences |
| `"clk_name"` | `str` — value `"clk"` | tb_top | driver |
| `"rst_name"` | `str` — value `"rst_n"` | tb_top | driver |
| `"reset_polarity"` | `str` — value `"active_low"` | tb_top | driver, scoreboard |
| `"ref_model"` | module reference to `ref_model` | tb_top | scoreboard |

ConfigDB hierarchy scope: `uvm_test` (i.e. `"", ""` root scope) unless
overridden in a derived environment.

---

## 6. Reference Model

| Item | Value |
|------|-------|
| File | `benchmarks/axi_handshake/ref_model.py` |
| Function | `step(s_valid, s_data, m_ready) → (s_ready, m_valid, m_data)` |
| Reset function | `reset()` — clears internal state |
| Latency | 0 cycles (outputs are for the **same** cycle as the inputs) |

The scoreboard calls `ref_model.step(txn.s_valid, txn.s_data, txn.m_ready)`
with the *sampled* DUT inputs and compares the returned `(s_ready, m_valid,
m_data)` against the *sampled* DUT outputs.

---

## 7. Intentional DUT Bugs (for verification reference)

The RTL is intentionally broken. Key violations the testbench must catch:

1. **`s_ready` is always 1** — should deassert when buffer is full and output
   is stalled.
2. **`m_valid` is driven combinationally from `rst_n`** — once reset is
   released, `m_valid` is immediately 1 even when the buffer is empty.
3. **`data_reg` updates whenever `s_valid` is high** — it should only update
   on an eligible input transfer (`s_valid && s_ready`).

These bugs are *not* present in the reference model.
