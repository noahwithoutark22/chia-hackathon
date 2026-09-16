# I2C Master Benchmark Specification

## 1. Purpose

This benchmark defines a small I2C-master transaction controller intended for
automated cocotb/pyUVM verification and iterative LLM-based verification.

The DUT is a transaction-level abstraction of a 7-bit-address I2C master with
an EEPROM-like byte-addressed target.

## 2. Clock and Reset

- `clk` is the synchronous clock.
- `rst_n` is an active-low asynchronous reset.
- While reset is asserted, the controller shall be idle.
- `busy=0`, `done=0`, and `ack_error=0` after reset.
- `read_data` shall reset to `0x00`.
- I2C `scl` and `sda` shall be released during reset.

## 3. Transaction Interface

Inputs:

| Signal | Width | Description |
|---|---:|---|
| `start` | 1 | Starts one transaction when idle |
| `rw` | 1 | `0` = write, `1` = read |
| `slave_addr` | 7 | I2C 7-bit slave address |
| `reg_addr` | 8 | Byte/register address |
| `write_data` | 8 | Data written for a write transaction |

Outputs:

| Signal | Width | Description |
|---|---:|---|
| `read_data` | 8 | Data returned by a read |
| `busy` | 1 | High while a transaction is active |
| `done` | 1 | One-clock completion pulse |
| `ack_error` | 1 | High when the target does not acknowledge |

## 4. Supported Slave

The benchmark models one EEPROM-like slave at address `0x50`.

A transaction addressed to any other 7-bit address shall complete with:
- `ack_error = 1`
- `done = 1`
- `busy = 0`
- `read_data = 0x00` for the transaction result

## 5. Write Behavior

For `rw=0` and `slave_addr=0x50`:

1. The controller accepts the transaction when idle and `start=1`.
2. `busy` becomes high.
3. The transaction completes.
4. `done` pulses for one clock.
5. `ack_error` remains low.
6. The byte at `memory[reg_addr]` becomes `write_data`.

## 6. Read Behavior

For `rw=1` and `slave_addr=0x50`:

1. The controller accepts the transaction when idle and `start=1`.
2. `busy` becomes high.
3. The transaction completes.
4. `done` pulses for one clock.
5. `ack_error` remains low.
6. `read_data` equals the most recently written value at `reg_addr`.
7. An address that has never been written returns `0x00`.

## 7. Bus Lines

`SCL` and `SDA` are open-drain style inouts.

- Driving `0` is permitted.
- Releasing the line shall produce high impedance (`Z`).
- The environment may provide pull-ups.
- A transaction should produce a START-like condition followed by an
  abstracted transfer and a STOP-like condition.

The benchmark intentionally abstracts away bit-level clocking, arbitration,
clock stretching, and multi-byte transfers.

## 8. Transaction Timing

The reference behavior is transaction-level rather than cycle-exact.

The environment shall wait for `done=1` before checking transaction results.
The scoreboard must compare against the Python reference model and must not
infer expected behavior from observed DUT outputs.

## 9. Verification Requirements

The verification environment should cover at least:

- reset
- write/read of multiple register addresses
- read-before-write
- repeated writes to the same register
- boundary addresses `0x00` and `0xFF`
- data values `0x00`, `0xFF`, `0x55`, and `0xAA`
- supported address `0x50`
- unsupported addresses such as `0x00`, `0x01`, and `0x7F`
- attempts to start while busy
- completion pulse behavior
- open-drain `SCL`/`SDA` release behavior

## 10. Important Verification Constraint

The verification environment must encode the behavior in this specification
and the independent Python reference model.

The candidate RTL is an implementation under test. It must never be used to
rewrite expected behavior, weaken assertions, change stimulus intent, or
modify the reference model merely because the RTL produces a different
result.

RTL changes, if enabled by the surrounding repair loop, must be applied to a
working copy/snapshot and must never modify the original benchmark input.
