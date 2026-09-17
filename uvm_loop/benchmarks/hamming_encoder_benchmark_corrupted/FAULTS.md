# Hamming Encoder — 10 Injected Faults

All 10 faults below are present simultaneously in `hamming_encoder.sv`.

The clean implementation is `hamming_encoder_golden.sv`.

## Fault 1: data_mapping
- Description: Skip Hamming position 3 when inserting data, causing the data-position mapping to shift.
- Correct version: `for (pos = 1; pos <= 71; pos = pos + 1)`
- Faulty version: `for (pos = 1; pos <= 71; pos = pos + 1) begin // FAULT 1: position-3 mapping error`

## Fault 2: data_mapping
- Description: Use data_in[data_idx+1] instead of data_in[data_idx], shifting all encoded data bits by one.
- Correct version: `hamming_bits[pos] = data_in[data_idx];`
- Faulty version: `hamming_bits[pos] = data_in[data_idx+1];`

## Fault 3: parity_coverage
- Description: Use the wrong coverage condition for P1.
- Correct version: `if (pos & 1)`
- Faulty version: `if (pos & 2)`

## Fault 4: parity_coverage
- Description: Use the wrong coverage condition for P2.
- Correct version: `if (pos & 2)`
- Faulty version: `if (pos & 4)`

## Fault 5: parity_coverage
- Description: Use the wrong coverage condition for P8.
- Correct version: `if (pos & 8)`
- Faulty version: `if (pos & 16)`

## Fault 6: parity_calculation
- Description: Invert P16 after calculating its parity, changing even parity to odd parity.
- Correct version: `hamming_bits[16] = p16;`
- Faulty version: `hamming_bits[16] = ~p16;`

## Fault 7: parity_calculation
- Description: Assign P32 from the wrong parity accumulator.
- Correct version: `hamming_bits[32] = p32;`
- Faulty version: `hamming_bits[32] = p16;`

## Fault 8: output_mapping
- Description: Map Hamming position 10 to the wrong output position.
- Correct version: `codeword[pos] = hamming_bits[pos];`
- Faulty version: `codeword[pos+1] = hamming_bits[pos];`

## Fault 9: overall_parity
- Description: Invert the computed overall parity before placing it in codeword[0].
- Correct version: `codeword[0] = overall_parity;`
- Faulty version: `codeword[0] = ~overall_parity;`

## Fault 10: loop_boundary
- Description: Stop the overall parity loop at position 70 instead of 71.
- Correct version: `for (pos = 1; pos <= 71; pos = pos + 1)`
- Faulty version: `for (pos = 1; pos <= 70; pos = pos + 1)`
