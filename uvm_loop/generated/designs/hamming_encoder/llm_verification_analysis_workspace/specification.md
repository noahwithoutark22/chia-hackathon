# Parameterized Hamming Encoder — Specification

## 1. Overview

This block encodes `DATA_WIDTH` data bits into a Hamming codeword. It is
fully combinational and generic: the number of parity bits and the total
codeword width are derived automatically from `DATA_WIDTH` at elaboration
time, so the same RTL supports any Hamming(N,K) code, e.g. Hamming(7,4),
Hamming(12,8), Hamming(15,11), Hamming(21,16), etc. An optional extra
overall-parity bit can be added to turn the code into a SECDED
(Single-Error-Correction, Double-Error-Detection) code.

Deliverables:

| File | Description |
|---|---|
| `rtl/hamming_encoder.sv` | Synthesizable SystemVerilog RTL (package + module) |
| `model/hamming_encoder_model.py` | Bit-exact Python golden/reference model |
| `spec.md` | This document |

## 2. Module Interface

```systemverilog
module hamming_encoder
  import hamming_pkg::*;
#(
  parameter  int unsigned DATA_WIDTH  = 4,
  parameter  bit          SECDED      = 1'b0,
  localparam int unsigned PARITY_BITS = num_parity_bits(DATA_WIDTH),
  localparam int unsigned BASE_WIDTH  = DATA_WIDTH + PARITY_BITS,
  localparam int unsigned CODE_WIDTH  = BASE_WIDTH + (SECDED ? 1 : 0)
)(
  input  logic [DATA_WIDTH-1:0] data_in,
  output logic [CODE_WIDTH-1:0] code_out
);
```

### 2.1 Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| `DATA_WIDTH` | `int unsigned` | 4 | Number of input data bits (K). Must be > 0. |
| `SECDED` | `bit` | 0 | 1 = append an extra overall even-parity bit for double-error detection. |

### 2.2 Derived Parameters (localparam, computed automatically)

| Name | Formula | Description |
|---|---|---|
| `PARITY_BITS` (R) | smallest R such that `2^R >= DATA_WIDTH + R + 1` | Number of Hamming parity bits |
| `BASE_WIDTH` | `DATA_WIDTH + PARITY_BITS` | Width of the base (non-SECDED) Hamming codeword (N) |
| `CODE_WIDTH` | `BASE_WIDTH + (SECDED ? 1 : 0)` | Total output codeword width |

The caller does not set `PARITY_BITS` / `CODE_WIDTH` directly — they are
derived automatically, but they are still visible as elaboration-time
constants (e.g. `hamming_encoder #(.DATA_WIDTH(8))::CODE_WIDTH`) for use in
surrounding logic (e.g. sizing a decoder or a storage register).

### 2.3 Ports

| Port | Direction | Width | Description |
|---|---|---|---|
| `data_in` | input | `DATA_WIDTH` | Data word to encode |
| `code_out` | output | `CODE_WIDTH` | Encoded Hamming (or SECDED) codeword |

The module is purely combinational — there is no clock or reset.

## 3. Algorithm / Bit-Ordering Convention

The classic "power-of-two position" Hamming construction is used:

1. Codeword bit **positions** are numbered `1 .. BASE_WIDTH` (1-indexed).
2. Any position that is an exact power of two (1, 2, 4, 8, 16, ...) is a
   **parity bit** position.
3. Every other position is a **data bit** position, and is filled with data
   bits taken **in order starting from `data_in[0]`**. I.e. the first free
   (non-power-of-two) position gets `data_in[0]`, the next free position
   gets `data_in[1]`, and so on.
4. Each parity bit at position `2^p` is the XOR of every position `pos`
   (excluding itself) for which `(pos & 2^p) != 0` — i.e. the standard
   Hamming covering sets.
5. If `SECDED = 1`, one additional overall parity bit is computed as the
   XOR of **all** bits of the base codeword (step 1-4 result), and is
   placed as the new least-significant bit of `code_out`; the base
   codeword is shifted up by one bit position.

### 3.1 Mapping positions to `code_out` bit indices

- **Non-SECDED** (`SECDED = 0`): Hamming position `pos` (1-indexed) maps to
  `code_out[pos - 1]`. So `code_out[0]` is Hamming position 1 (the first
  parity bit), and `code_out[CODE_WIDTH-1]` is the last data bit.
- **SECDED** (`SECDED = 1`): `code_out[0]` is the extra overall-parity bit;
  Hamming position `pos` maps to `code_out[pos]` (i.e. shifted up by one).

This convention is identical between the RTL and the Python reference
model, so codewords produced by either can be compared bit-for-bit.

## 4. Worked Examples

### 4.1 `DATA_WIDTH = 4`, `SECDED = 0` → classic Hamming(7,4)

`PARITY_BITS = 3`, `CODE_WIDTH = 7`.

Position layout (MSB..LSB of `code_out`, i.e. position 7 down to 1):

```
position :  7   6   5   4   3   2   1
content  :  d4  d3  d2  p4  d1  p2  p1
```

where `d1..d4 = data_in[0..3]` and:

```
p1 = d1 ^ d2 ^ d4
p2 = d1 ^ d3 ^ d4
p4 = d2 ^ d3 ^ d4
```

Example: `data_in = 4'b0101` (d1=1, d2=0, d3=1, d4=0) → `code_out = 7'b0101101`.

### 4.2 `DATA_WIDTH = 4`, `SECDED = 1` → Hamming(8,4) SECDED

`PARITY_BITS = 3`, `CODE_WIDTH = 8`. Same base codeword as §4.1, with an
extra overall-parity bit `p0 = p1 ^ p2 ^ d1 ^ p4 ^ d2 ^ d3 ^ d4` placed at
`code_out[0]`; the base codeword occupies `code_out[7:1]`.

Example: `data_in = 4'b0101` → `code_out = 8'b01011010`.

### 4.3 Other widths

| DATA_WIDTH | PARITY_BITS | CODE_WIDTH (no SECDED) | CODE_WIDTH (SECDED) | Common name |
|---|---|---|---|---|
| 1 | 2 | 3 | 4 | — |
| 4 | 3 | 7 | 8 | Hamming(7,4) / (8,4) SECDED |
| 8 | 4 | 12 | 13 | Hamming(12,8) |
| 11 | 4 | 15 | 16 | Hamming(15,11) / (16,11) SECDED |
| 16 | 5 | 21 | 22 | Hamming(21,16) |

## 5. Reference Model (`model/hamming_encoder_model.py`)

`hamming_encode(data_in: int, data_width: int, secded: bool = False)`
returns `(code_out, params)`, where `code_out` is an integer holding
`params.code_width` bits and `params` is a `HammingParams` dataclass
exposing `parity_bits`, `base_width`, and `code_width`. The model implements
exactly the same 5-step algorithm described in §3 and uses the identical
bit-index convention described in §3.1, so it can be used directly as a
golden reference in a UVM/cocotb/directed testbench:

```python
from hamming_encoder_model import hamming_encode
code, params = hamming_encode(0b0101, data_width=4, secded=False)
assert code == 0b0101101
```

Running the file directly (`python3 hamming_encoder_model.py`) performs a
self-check of all 16 Hamming(7,4) codewords against an independently
hand-derived table, and prints a few SECDED examples.

## 6. Verification Notes

- The RTL and the Python model were cross-checked for `DATA_WIDTH = 4`
  (all 16 vectors, SECDED = 0 and 1) and `DATA_WIDTH = 8` (all 256
  vectors, SECDED = 0), with bit-exact agreement in every case.
- Recommended verification approach for new integrations: for a given
  `DATA_WIDTH`/`SECDED` configuration, exhaustively (for small widths) or
  randomly (for large widths) drive `data_in`, compute the expected
  `code_out` via `hamming_encode(...)`, and compare against the RTL
  simulation output.
- `PARITY_BITS` and `CODE_WIDTH` are elaboration-time constants and can be
  read back from an instantiated module (e.g.
  `hamming_encoder #(.DATA_WIDTH(K))::CODE_WIDTH`) to size adjacent logic
  such as a matching decoder, a storage register, or a bus.

## 7. Limitations / Non-Goals

- This module is an **encoder only**; no decoder/syndrome-checker or
  error-correction logic is included.
- `DATA_WIDTH` must be a positive integer known at elaboration time
  (compile-time parameter); it cannot change at runtime.
- The module is purely combinational; if `code_out` needs to be registered,
  add a flop at the output in the surrounding design.
- No input validation is performed on `data_in` beyond its declared width
  (any bit pattern within `DATA_WIDTH` bits is valid).
