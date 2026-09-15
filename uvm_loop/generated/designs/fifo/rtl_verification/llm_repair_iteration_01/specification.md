# FIFO Specification

## Purpose
A synchronous FIFO stores DATA_WIDTH-bit values in first-in-first-out order.

## Interface
- `clk`: active clock, rising-edge triggered.
- `rst_n`: active-low asynchronous reset.
- `wr_en`: request a write.
- `rd_en`: request a read.
- `din`: input data.
- `dout`: registered output data.
- `full`: asserted when the FIFO contains DEPTH entries.
- `empty`: asserted when the FIFO contains zero entries.

## Behavior
- Reset asynchronously clears the FIFO state, makes `empty=1`, `full=0`,
  and clears `dout`.
- A write is accepted on a rising clock edge only when `wr_en=1` and
  `full=0`.
- A read is accepted on a rising clock edge only when `rd_en=1` and
  `empty=0`.
- Accepted writes append data to the FIFO.
- Accepted reads return the oldest stored value on `dout`.
- A read while empty is ignored.
- A write while full is ignored.
- When both read and write are accepted in the same cycle, both operations
  occur and the occupancy remains unchanged.
- Data ordering must remain FIFO.
