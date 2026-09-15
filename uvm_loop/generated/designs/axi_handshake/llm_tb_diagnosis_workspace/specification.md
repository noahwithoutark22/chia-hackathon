# AXI-Stream Handshake Benchmark

## Purpose

This benchmark models a one-entry AXI4-Stream elastic buffer. The DUT is intentionally
incorrect. The supplied Python reference model and this specification define the
intended behavior and must be treated as the functional authority.

The benchmark is specifically designed to verify that a generated verification
environment detects an RTL implementation that violates AXI VALID/READY handshaking.

## Interface

Module: `axi_handshake`

Clock:
- `clk`: rising-edge clock.

Reset:
- `rst_n`: active-low synchronous reset.
- When `rst_n == 0` at a rising edge, the buffer becomes empty.

AXI-Stream input:
- `s_valid`: source asserts this when `s_data` is valid.
- `s_ready`: DUT asserts this when it can accept an input transfer.
- `s_data[7:0]`: 8-bit input payload.

AXI-Stream output:
- `m_valid`: DUT asserts this when `m_data` is valid.
- `m_ready`: downstream asserts this when it can accept an output transfer.
- `m_data[7:0]`: 8-bit output payload.

## Functional behavior

The DUT is a one-entry elastic buffer.

An input transfer occurs on a rising edge when:

    s_valid && s_ready

An output transfer occurs on a rising edge when:

    m_valid && m_ready

The intended behavior is:

1. The buffer is empty after reset.
2. When empty, `s_ready` is asserted so that one input item can be accepted.
3. An accepted input item becomes the output item and `m_valid` becomes asserted.
4. While `m_valid == 1` and `m_ready == 0`, the output transaction is stalled.
5. During a stall, `m_data` MUST remain unchanged and `m_valid` MUST remain asserted.
6. When `m_valid && m_ready` occurs, the current output item is consumed.
7. If a new input transfer occurs on the same edge that the old output is consumed,
   the new item may replace it immediately and `m_valid` remains asserted.
8. If the output is consumed and no new input is accepted, `m_valid` becomes deasserted.
9. Payload ordering must be preserved exactly: accepted input items must emerge in
   the same order.
10. No input item may be dropped or duplicated.

## Handshake invariants

The verification environment should check at least:

- A transfer occurs only on `VALID && READY`.
- The producer may keep `s_valid` asserted while `s_ready` is low.
- The DUT must not consume an input merely because `s_valid` is high.
- If `m_valid && !m_ready`, the DUT must hold both `m_valid` and `m_data`.
- Every accepted input must eventually produce exactly one output, in order.

## Important benchmark property

The RTL supplied with this benchmark is deliberately wrong. It is NOT the
behavioral oracle.

Expected behavior must come from this specification and `ref_model.py`. The
verification environment must not weaken its checks or change expected outputs
to match the supplied RTL.
