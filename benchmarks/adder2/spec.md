# adder2 — Specification

A registered, parameterized `WIDTH`-bit adder with carry-in and carry-out.

- On the rising edge of `clk`, if `rst_n` is low, `sum` and `cout` are
  cleared to 0 (active-low, synchronous reset).
- Otherwise, `{cout, sum} <= a + b + cin` — i.e. the (WIDTH+1)-bit result
  of `a + b + cin` is registered, with `cout` holding the overflow bit.
- `a`, `b` are unsigned `WIDTH`-bit values; `cin` is a single bit.
- Default `WIDTH = 8`.

## Things worth verifying

- Basic addition with no carry.
- Carry propagation across all bit positions.
- Overflow (`cout` correctly set) at the maximum representable sum.
- Behavior of `cin` in isolation (a = b = 0, cin = 1).
- Reset behavior: `sum`/`cout` clear immediately on `rst_n` deassertion,
  regardless of what was being added at the time.
- Randomized addition across the full input space for `WIDTH = 8`.
