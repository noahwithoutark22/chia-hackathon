# AES-128 Combined 50-Fault Manifest

This RTL intentionally contains all 50 faults simultaneously.

The `correct_version` field gives the golden expression/line that should replace
the corrupted version.

## Fault 01 — SEMANTIC

- Location: S-box entry SBOX[0]

- Description: Change the S-box value for input 0.

- Corrupted: `8'h62`

- Correct: `8'h63`

- Approx. line(s): []

## Fault 02 — SEMANTIC

- Location: S-box entry SBOX[1]

- Description: Change the S-box value for input 1.

- Corrupted: `8'h7d`

- Correct: `8'h7c`

- Approx. line(s): []

## Fault 03 — SEMANTIC

- Location: S-box entry SBOX[5]

- Description: Change the S-box value for input 5.

- Corrupted: `8'h6a`

- Correct: `8'h6b`

- Approx. line(s): []

## Fault 04 — SEMANTIC

- Location: S-box entry SBOX[10]

- Description: Change the S-box value for input 10.

- Corrupted: `8'h66`

- Correct: `8'h67`

- Approx. line(s): []

## Fault 05 — SEMANTIC

- Location: S-box entry SBOX[15]

- Description: Change the S-box value for input 15.

- Corrupted: `8'h77`

- Correct: `8'h76`

- Approx. line(s): []

## Fault 06 — SEMANTIC

- Location: S-box entry SBOX[32]

- Description: Change the S-box value for input 32.

- Corrupted: `8'hb6`

- Correct: `8'hb7`

- Approx. line(s): []

## Fault 07 — SEMANTIC

- Location: S-box entry SBOX[47]

- Description: Change the S-box value for input 47.

- Corrupted: `8'h14`

- Correct: `8'h15`

- Approx. line(s): []

## Fault 08 — SEMANTIC

- Location: S-box entry SBOX[64]

- Description: Change the S-box value for input 64.

- Corrupted: `8'h51`

- Correct: `8'h53`

- Approx. line(s): []

## Fault 09 — SEMANTIC

- Location: S-box entry SBOX[127]

- Description: Change the S-box value for input 127.

- Corrupted: `8'hd3`

- Correct: `8'hd2`

- Approx. line(s): []

## Fault 10 — SEMANTIC

- Location: S-box entry SBOX[200]

- Description: Change the S-box value for input 200.

- Corrupted: `8'hf9`

- Correct: `8'he8`

- Approx. line(s): []

## Fault 11 — SEMANTIC

- Location: RCON[2]

- Description: Change AES-128 round constant 2.

- Corrupted: `8'h03`

- Correct: `8'h02`

- Approx. line(s): []

## Fault 12 — SEMANTIC

- Location: RCON[8]

- Description: Change AES-128 round constant 8.

- Corrupted: `8'h81`

- Correct: `8'h80`

- Approx. line(s): []

## Fault 13 — SEMANTIC

- Location: gm2 / xtime

- Description: Shift the input by two bits instead of one.

- Corrupted: `{a[5:0],2'b00} ^ (8'h1b & {8{a[7]}})`

- Correct: `{a[6:0],1'b0} ^ (8'h1b & {8{a[7]}})`

- Approx. line(s): []

## Fault 14 — SEMANTIC

- Location: gm2 / reduction polynomial

- Description: Use the wrong AES reduction polynomial.

- Corrupted: `8'h1d`

- Correct: `8'h1b`

- Approx. line(s): [51]

## Fault 15 — SEMANTIC

- Location: gm3

- Description: Compute multiplication by 3 incorrectly.

- Corrupted: `gm2(a) ^ gm2(a)`

- Correct: `gm2(a) ^ a`

- Approx. line(s): [55]

## Fault 16 — SEMANTIC

- Location: ShiftRows o[1]

- Description: Use the wrong source byte for output byte 1.

- Corrupted: `o[1]=b[4];`

- Correct: `o[1]=b[5];`

- Approx. line(s): [76]

## Fault 17 — SEMANTIC

- Location: ShiftRows o[6]

- Description: Use the wrong source byte for output byte 6.

- Corrupted: `o[6]=b[13];`

- Correct: `o[6]=b[14];`

- Approx. line(s): [77]

## Fault 18 — SEMANTIC

- Location: ShiftRows o[11]

- Description: Use the wrong source byte for output byte 11.

- Corrupted: `o[11]=b[6];`

- Correct: `o[11]=b[7];`

- Approx. line(s): [78]

## Fault 19 — SEMANTIC

- Location: ShiftRows o[12]

- Description: Use the wrong source byte for output byte 12.

- Corrupted: `o[12]=b[13];`

- Correct: `o[12]=b[12];`

- Approx. line(s): [79]

## Fault 20 — SEMANTIC

- Location: ShiftRows o[15]

- Description: Use the wrong source byte for output byte 15.

- Corrupted: `o[15]=b[10];`

- Correct: `o[15]=b[11];`

- Approx. line(s): [79]

## Fault 21 — SEMANTIC

- Location: MixColumns row 0 coefficient

- Description: Use multiplication by 3 instead of 2 for the first coefficient.

- Corrupted: `gm3(b[4*c+0])`

- Correct: `gm2(b[4*c+0])`

- Approx. line(s): []

## Fault 22 — SEMANTIC

- Location: MixColumns row 0 coefficient

- Description: Use multiplication by 2 instead of 3 for the second coefficient.

- Corrupted: `gm2(b[4*c+1])`

- Correct: `gm3(b[4*c+1])`

- Approx. line(s): [96, 97]

## Fault 23 — SEMANTIC

- Location: MixColumns second output

- Description: Use the wrong coefficient for the second output.

- Corrupted: `gm3(b[4*c+1])`

- Correct: `gm2(b[4*c+1])`

- Approx. line(s): []

## Fault 24 — SEMANTIC

- Location: MixColumns third output

- Description: Use multiplication by 3 instead of 2 for the third coefficient.

- Corrupted: `gm3(b[4*c+2])`

- Correct: `gm2(b[4*c+2])`

- Approx. line(s): []

## Fault 25 — SEMANTIC

- Location: MixColumns fourth output

- Description: Use multiplication by 2 instead of 3 for the first coefficient.

- Corrupted: `gm2(b[4*c+0])`

- Correct: `gm3(b[4*c+0])`

- Approx. line(s): []

## Fault 26 — SEMANTIC

- Location: MixColumns second output coefficient

- Description: Change the third coefficient of the second output equation.

- Corrupted: `gm2(b[4*c+2])`

- Correct: `gm3(b[4*c+2])`

- Approx. line(s): [97]

## Fault 27 — SEMANTIC

- Location: MixColumns third output coefficient

- Description: Change the fourth coefficient of the third output equation.

- Corrupted: `gm2(b[4*c+3])`

- Correct: `gm3(b[4*c+3])`

- Approx. line(s): [98]

## Fault 28 — SEMANTIC

- Location: MixColumns fourth output

- Description: Corrupt both non-unit coefficients in the fourth output equation.

- Corrupted: `gm3(b[4*c+0]) ^ ... ^ gm3(b[4*c+3])`

- Correct: `gm3(b[4*c+0]) ^ ... ^ gm2(b[4*c+3])`

- Approx. line(s): [99]

## Fault 29 — SEMANTIC

- Location: Key expansion w0 extraction

- Description: Misalign the first AES-128 key word by one bit.

- Corrupted: `k[126:95]`

- Correct: `k[127:96]`

- Approx. line(s): [111]

## Fault 30 — SEMANTIC

- Location: Key expansion w1 extraction

- Description: Misalign the second AES-128 key word by one bit.

- Corrupted: `k[94:63]`

- Correct: `k[95:64]`

- Approx. line(s): [112]

## Fault 31 — SEMANTIC

- Location: Key expansion w2 extraction

- Description: Misalign the third AES-128 key word by one bit.

- Corrupted: `k[62:31]`

- Correct: `k[63:32]`

- Approx. line(s): [113]

## Fault 32 — SEMANTIC

- Location: Key expansion w3 extraction

- Description: Misalign the fourth AES-128 key word by one bit.

- Corrupted: `k[30:0]`

- Correct: `k[31:0]`

- Approx. line(s): [114]

## Fault 33 — SEMANTIC

- Location: Key expansion RCON transform

- Description: Inject an extra bit into the round-constant transformation.

- Corrupted: `t[31:24] ^ RCON[r] ^ 32'h00000001`

- Correct: `t[31:24] ^ RCON[r]`

- Approx. line(s): []

## Fault 34 — SEMANTIC

- Location: Key expansion n1

- Description: Generate n1 from the wrong word.

- Corrupted: `w1 ^ w0`

- Correct: `w1 ^ n0`

- Approx. line(s): [120]

## Fault 35 — SEMANTIC

- Location: Key expansion n2

- Description: Generate n2 from the wrong word.

- Corrupted: `w2 ^ n0`

- Correct: `w2 ^ n1`

- Approx. line(s): [121]

## Fault 36 — SEMANTIC

- Location: Key expansion n3

- Description: Generate n3 from the wrong word.

- Corrupted: `w3 ^ n1`

- Correct: `w3 ^ n2`

- Approx. line(s): [122]

## Fault 37 — SEMANTIC

- Location: Key expansion RotWord/SubWord

- Description: Swap two bytes in the RotWord/SubWord transformation.

- Corrupted: `SBOX[w3[15:8]], SBOX[w3[23:16]]`

- Correct: `SBOX[w3[23:16]], SBOX[w3[15:8]]`

- Approx. line(s): [116]

## Fault 38 — SEMANTIC

- Location: Key expansion extra XOR

- Description: Inject an extra constant into the key schedule.

- Corrupted: `^ 32'h00000100`

- Correct: `no extra XOR`

- Approx. line(s): [117]

## Fault 39 — SEMANTIC

- Location: AES round SubBytes

- Description: Skip SubBytes and apply ShiftRows directly.

- Corrupted: `t = shift_rows(s);`

- Correct: `t = sub_bytes(s);`

- Approx. line(s): [135]

## Fault 40 — SEMANTIC

- Location: AES round transformation order

- Description: Swap SubBytes and ShiftRows.

- Corrupted: `t = sub_bytes(t);`

- Correct: `t = shift_rows(t);`

- Approx. line(s): [136]

## Fault 41 — SEMANTIC

- Location: AES round MixColumns condition

- Description: Invert the final-round condition controlling MixColumns.

- Corrupted: `if (final_round)`

- Correct: `if (!final_round)`

- Approx. line(s): [137]

## Fault 42 — SEMANTIC

- Location: AddRoundKey

- Description: Invert all round-key bits before XOR.

- Corrupted: `t ^ ~k`

- Correct: `t ^ k`

- Approx. line(s): [139]

## Fault 43 — SEMANTIC

- Location: AES round MixColumns input

- Description: Apply MixColumns to the pre-transformation state.

- Corrupted: `mix_columns(s)`

- Correct: `mix_columns(t)`

- Approx. line(s): [138]

## Fault 44 — SEMANTIC

- Location: Initial round key

- Description: Complement the initial key before storing it.

- Corrupted: `round_key <= ~key;`

- Correct: `round_key <= key;`

- Approx. line(s): [156]

## Fault 45 — SEMANTIC

- Location: Initial round counter

- Description: Start at round 0 instead of round 1.

- Corrupted: `round <= 4'd0;`

- Correct: `round <= 4'd1;`

- Approx. line(s): [147, 157]

## Fault 46 — SEMANTIC

- Location: Terminal round condition

- Description: Finish encryption one round early.

- Corrupted: `if (round == 4'd9)`

- Correct: `if (round == 4'd10)`

- Approx. line(s): [162]

## Fault 47 — SEMANTIC

- Location: Round counter increment

- Description: Advance the round counter by two.

- Corrupted: `round <= round + 2'b10;`

- Correct: `round <= round + 1'b1;`

- Approx. line(s): [169]

## Fault 48 — SEMANTIC

- Location: Completion pulse

- Description: Suppress the final done pulse.

- Corrupted: `done <= 1'b0;`

- Correct: `done <= 1'b1;`

- Approx. line(s): [165]

## Fault 49 — SEMANTIC

- Location: Busy completion state

- Description: Remain busy after completing the transaction.

- Corrupted: `busy <= 1'b1;`

- Correct: `busy <= 1'b0;`

- Approx. line(s): [148, 158]

## Fault 50 — SEMANTIC

- Location: Final-round state key

- Description: Use the old round key instead of the newly generated key.

- Corrupted: `aes_round(state, round_key, 1'b1)`

- Correct: `aes_round(state, next_round_key(round_key, round), 1'b1)`

- Approx. line(s): [163]

