# I2C Combined 20-Fault Manifest

This RTL intentionally contains all 20 faults simultaneously.

The `correct_version` field gives the golden expression/line that should replace the corrupted version.

## Fault 01 — SEMANTIC

- Location: address R/W bit

- Description: Invert the transmitted I2C R/W bit.

- Corrupted: `shift_reg <= {slave_addr, ~rw};`

- Correct: `shift_reg <= {slave_addr, rw};`

- Approx. line(s): [74]

## Fault 02 — SEMANTIC

- Location: address bit counter initialization

- Description: Start the address transfer at bit 6 instead of bit 7.

- Corrupted: `bit_cnt <= 4'd6;`

- Correct: `bit_cnt <= 4'd7;`

- Approx. line(s): [65]

## Fault 03 — SEMANTIC

- Location: address ACK detection

- Description: Treat a low SDA level as an ACK error instead of recognizing it as a valid ACK.

- Corrupted: `if (sda_in == 1'b0)`

- Correct: `if (sda_in != 1'b0)`

- Approx. line(s): [93]

## Fault 04 — SEMANTIC

- Location: data ACK detection

- Description: Invert write-data ACK detection.

- Corrupted: `if (sda_in == 1'b0)`

- Correct: `if (sda_in != 1'b0)`

- Approx. line(s): [116]

## Fault 05 — SEMANTIC

- Location: read/write path selection

- Description: Select the write path when rw is asserted instead of selecting the read path.

- Corrupted: `if (rw) begin`

- Correct: `if (!rw) begin`

- Approx. line(s): [101]

## Fault 06 — SEMANTIC

- Location: write data loading

- Description: Complement the transmitted data byte before the write transfer.

- Corrupted: `shift_reg <= ~tx_data;`

- Correct: `shift_reg <= tx_data;`

- Approx. line(s): [102]

## Fault 07 — SEMANTIC

- Location: read data bit placement

- Description: Reverse the destination bit indexing while receiving a byte.

- Corrupted: `rx_shift[bit_cnt] <= sda_in;`

- Correct: `rx_shift[7-bit_cnt] <= sda_in;`

- Approx. line(s): [129]

## Fault 08 — SEMANTIC

- Location: address bit counter progression

- Description: Increment the address bit counter instead of decrementing it.

- Corrupted: `bit_cnt <= bit_cnt + 1'b1;`

- Correct: `bit_cnt <= bit_cnt - 1'b1;`

- Approx. line(s): [88]

## Fault 09 — SEMANTIC

- Location: address terminal condition

- Description: Terminate the address transfer one bit early.

- Corrupted: `if (bit_cnt == 1) begin`

- Correct: `if (bit_cnt == 0) begin`

- Approx. line(s): [85]

## Fault 10 — SEMANTIC

- Location: read-data terminal condition

- Description: Finish the read data phase before all eight bits have been received.

- Corrupted: `if (bit_cnt == 1) begin`

- Correct: `if (bit_cnt == 0) begin`

- Approx. line(s): [122]

## Fault 11 — SEMANTIC

- Location: received data output

- Description: Invert the received byte before presenting it on rx_data.

- Corrupted: `rx_data <= ~rx_shift;`

- Correct: `rx_data <= rx_shift;`

- Approx. line(s): [133]

## Fault 12 — SEMANTIC

- Location: idle ACK-error initialization

- Description: Set ack_error in the idle state instead of clearing it.

- Corrupted: `ack_error <= 1'b1;`

- Correct: `ack_error <= 1'b0;`

- Approx. line(s): [70]

## Fault 13 — SEMANTIC

- Location: busy handling during address ACK

- Description: Clear busy in the middle of an active transaction after address ACK sampling.

- Corrupted: `busy <= 1'b0;`

- Correct: `No busy assignment here; retain busy until STOP.`

- Approx. line(s): [100]

## Fault 14 — SEMANTIC

- Location: write data completion transition

- Description: Enter READ_DATA after a write-data ACK instead of proceeding to STOP.

- Corrupted: `state <= READ_DATA;`

- Correct: `state <= STOP_COND;`

- Approx. line(s): [100]

## Fault 15 — SEMANTIC

- Location: read ACK transition

- Description: Loop back to DATA_ACK instead of proceeding to STOP after the read NACK.

- Corrupted: `state <= DATA_ACK;`

- Correct: `state <= STOP_COND;`

- Approx. line(s): [110]

## Fault 16 — SEMANTIC

- Location: default done assignment

- Description: Keep done asserted by default instead of clearing it each active cycle.

- Corrupted: `done <= 1'b1;`

- Correct: `done <= 1'b0;`

- Approx. line(s): [62]

## Fault 17 — SEMANTIC

- Location: completion busy state

- Description: Keep busy asserted after STOP/completion.

- Corrupted: `busy <= 1'b1;`

- Correct: `busy <= 1'b0;`

- Approx. line(s): [138]

## Fault 18 — SEMANTIC

- Location: STOP state transition

- Description: Start another transaction instead of returning to IDLE after STOP.

- Corrupted: `state <= START_COND;`

- Correct: `state <= IDLE;`

- Approx. line(s): [140]

## Fault 19 — SEMANTIC

- Location: clock divider terminal count

- Description: Use CLK_DIV instead of CLK_DIV-1 as the divider terminal count.

- Corrupted: `if (div_cnt == CLK_DIV) begin`

- Correct: `if (div_cnt == CLK_DIV-1) begin`

- Approx. line(s): [64]

## Fault 20 — SEMANTIC

- Location: clock divider increment

- Description: Increment the divider by two instead of one.

- Corrupted: `div_cnt <= div_cnt + 2'd2;`

- Correct: `div_cnt <= div_cnt + 1'b1;`

- Approx. line(s): [149]

