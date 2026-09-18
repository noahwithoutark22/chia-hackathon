# SHA-256 Combined 50-Fault Manifest

This RTL intentionally contains all 50 faults simultaneously.

All faults are semantic. The RTL remains syntactically valid SystemVerilog.

The `correct_version` field gives the golden expression that should replace the corrupted expression.

## Fault 01 — SEMANTIC

- Location: K[2] round constant
- Description: Change K[2] by one value.
- Corrupted: `32'hb5c0fbce`
- Correct: `32'hb5c0fbcf`

## Fault 02 — SEMANTIC

- Location: K[10] round constant
- Description: Change K[10].
- Corrupted: `32'h243185bf`
- Correct: `32'h243185be`

## Fault 03 — SEMANTIC

- Location: K[31] round constant
- Description: Change K[31].
- Corrupted: `32'h14292977`
- Correct: `32'h14292967`

## Fault 04 — SEMANTIC

- Location: K[45] round constant
- Description: Change K[45].
- Corrupted: `32'h90befffb`
- Correct: `32'h90befffa`

## Fault 05 — SEMANTIC

- Location: K[55] round constant
- Description: Change K[55].
- Corrupted: `32'h8cc70218`
- Correct: `32'h8cc70208`

## Fault 06 — SEMANTIC

- Location: message word extraction
- Description: Reverse the direction of the 32-bit message-word extraction.
- Corrupted: `block[i*32 +: 32]`
- Correct: `block[511 - i*32 -: 32]`

## Fault 07 — SEMANTIC

- Location: message word byte ordering
- Description: Reverse the byte order of each extracted 32-bit message word.
- Corrupted: `{message_word[7:0], message_word[15:8], message_word[23:16], message_word[31:24]}`
- Correct: `message_word`

## Fault 08 — SEMANTIC

- Location: schedule sigma1 dependency
- Description: Use W[t-3] instead of W[t-2].
- Corrupted: `SmallSigma1(W[round-3])`
- Correct: `SmallSigma1(W[round-2])`

## Fault 09 — SEMANTIC

- Location: schedule W[t-7] dependency
- Description: Use W[t-8] instead of W[t-7].
- Corrupted: `W[round-8]`
- Correct: `W[round-7]`

## Fault 10 — SEMANTIC

- Location: schedule sigma0 dependency
- Description: Use W[t-14] instead of W[t-15].
- Corrupted: `SmallSigma0(W[round-14])`
- Correct: `SmallSigma0(W[round-15])`

## Fault 11 — SEMANTIC

- Location: schedule W[t-16] dependency
- Description: Use W[t-17] instead of W[t-16].
- Corrupted: `W[round-17]`
- Correct: `W[round-16]`

## Fault 12 — SEMANTIC

- Location: BigSigma0 ROTR2 term
- Description: Use ROTR3 instead of ROTR2.
- Corrupted: `rotr(x,3)`
- Correct: `rotr(x,2)`

## Fault 13 — SEMANTIC

- Location: BigSigma0 ROTR13 term
- Description: Use ROTR12 instead of ROTR13.
- Corrupted: `rotr(x,12)`
- Correct: `rotr(x,13)`

## Fault 14 — SEMANTIC

- Location: BigSigma0 ROTR22 term
- Description: Use ROTR21 instead of ROTR22.
- Corrupted: `rotr(x,21)`
- Correct: `rotr(x,22)`

## Fault 15 — SEMANTIC

- Location: BigSigma1 ROTR6 term
- Description: Use ROTR7 instead of ROTR6.
- Corrupted: `rotr(x,7)`
- Correct: `rotr(x,6)`

## Fault 16 — SEMANTIC

- Location: BigSigma1 ROTR11 term
- Description: Use ROTR12 instead of ROTR11.
- Corrupted: `rotr(x,12)`
- Correct: `rotr(x,11)`

## Fault 17 — SEMANTIC

- Location: BigSigma1 ROTR25 term
- Description: Use ROTR24 instead of ROTR25.
- Corrupted: `rotr(x,24)`
- Correct: `rotr(x,25)`

## Fault 18 — SEMANTIC

- Location: SmallSigma0 ROTR7 term
- Description: Use ROTR8 instead of ROTR7.
- Corrupted: `rotr(x,8)`
- Correct: `rotr(x,7)`

## Fault 19 — SEMANTIC

- Location: SmallSigma0 ROTR18 term
- Description: Use ROTR17 instead of ROTR18.
- Corrupted: `rotr(x,17)`
- Correct: `rotr(x,18)`

## Fault 20 — SEMANTIC

- Location: SmallSigma0 SHR3 term
- Description: Use SHR2 instead of SHR3.
- Corrupted: `(x >> 2)`
- Correct: `(x >> 3)`

## Fault 21 — SEMANTIC

- Location: SmallSigma1 ROTR17 term
- Description: Use ROTR16 instead of ROTR17.
- Corrupted: `rotr(x,16)`
- Correct: `rotr(x,17)`

## Fault 22 — SEMANTIC

- Location: SmallSigma1 ROTR19 term
- Description: Use ROTR20 instead of ROTR19.
- Corrupted: `rotr(x,20)`
- Correct: `rotr(x,19)`

## Fault 23 — SEMANTIC

- Location: SmallSigma1 SHR10 term
- Description: Use SHR9 instead of SHR10.
- Corrupted: `(x >> 9)`
- Correct: `(x >> 10)`

## Fault 24 — SEMANTIC

- Location: Ch function
- Description: Remove the complement from x in the second term.
- Corrupted: `(x & y) ^ (x & z)`
- Correct: `(x & y) ^ (~x & z)`

## Fault 25 — SEMANTIC

- Location: Maj function
- Description: Remove the third majority term.
- Corrupted: `(x & y) ^ (x & z)`
- Correct: `(x & y) ^ (x & z) ^ (y & z)`

## Fault 26 — SEMANTIC

- Location: T1 h operand
- Description: Use g instead of h.
- Corrupted: `g + BigSigma1(e)`
- Correct: `h + BigSigma1(e)`

## Fault 27 — SEMANTIC

- Location: T1 Ch operands
- Description: Swap the final two Ch operands.
- Corrupted: `Ch(e,g,f)`
- Correct: `Ch(e,f,g)`

## Fault 28 — SEMANTIC

- Location: T1 round constant
- Description: Use the next round constant.
- Corrupted: `K[(round+1) & 7'd63]`
- Correct: `K[round]`

## Fault 29 — SEMANTIC

- Location: T2 Sigma function
- Description: Use BigSigma1 instead of BigSigma0.
- Corrupted: `BigSigma1(a)`
- Correct: `BigSigma0(a)`

## Fault 30 — SEMANTIC

- Location: T2 combination operator
- Description: Subtract the majority term instead of adding it.
- Corrupted: `BigSigma1(a) - Maj(a,c,b)`
- Correct: `BigSigma0(a) + Maj(a,b,c)`

## Fault 31 — SEMANTIC

- Location: new a calculation
- Description: Use XOR instead of addition.
- Corrupted: `na = next_t1 ^ next_t2;`
- Correct: `na = next_t1 + next_t2;`

## Fault 32 — SEMANTIC

- Location: new d calculation
- Description: Use b instead of c for the new d value.
- Corrupted: `nd = b;`
- Correct: `nd = c;`

## Fault 33 — SEMANTIC

- Location: new e calculation
- Description: Use T2 instead of T1.
- Corrupted: `ne = d + next_t2;`
- Correct: `ne = d + next_t1;`

## Fault 34 — SEMANTIC

- Location: new b calculation
- Description: Do not shift a into b.
- Corrupted: `nb = b;`
- Correct: `nb = a;`

## Fault 35 — SEMANTIC

- Location: new c calculation
- Description: Do not shift b into c.
- Corrupted: `nc = c;`
- Correct: `nc = b;`

## Fault 36 — SEMANTIC

- Location: H3 digest feed-forward
- Description: Use the new c value instead of the new d value.
- Corrupted: `32'ha54ff53a + nc`
- Correct: `32'ha54ff53a + nd`

## Fault 37 — SEMANTIC

- Location: new f calculation
- Description: Do not shift e into f.
- Corrupted: `nf = f;`
- Correct: `nf = e;`

## Fault 38 — SEMANTIC

- Location: new g calculation
- Description: Do not shift f into g.
- Corrupted: `ng = g;`
- Correct: `ng = f;`

## Fault 39 — SEMANTIC

- Location: new h calculation
- Description: Do not shift g into h.
- Corrupted: `nh = h;`
- Correct: `nh = g;`

## Fault 40 — SEMANTIC

- Location: terminal round condition
- Description: Terminate one round early.
- Corrupted: `if (round == 62)`
- Correct: `if (round == 63)`

## Fault 41 — SEMANTIC

- Location: round increment
- Description: Advance the round counter by two instead of one.
- Corrupted: `round <= round + 2'd2;`
- Correct: `round <= round + 1'b1;`

## Fault 42 — SEMANTIC

- Location: start/busy gating
- Description: Accept a new start request while already busy.
- Corrupted: `if (start)`
- Correct: `if (start && !busy)`

## Fault 43 — SEMANTIC

- Location: default done assignment
- Description: Keep done asserted during normal operation.
- Corrupted: `done <= 1'b1;`
- Correct: `done <= 1'b0;`

## Fault 44 — SEMANTIC

- Location: busy completion assignment
- Description: Keep busy asserted after completion.
- Corrupted: `busy <= 1'b1;`
- Correct: `busy <= 1'b0;`

## Fault 45 — SEMANTIC

- Location: digest H0 feed-forward
- Description: Use b instead of a.
- Corrupted: `32'h6a09e667 + nb`
- Correct: `32'h6a09e667 + na`

## Fault 46 — SEMANTIC

- Location: digest H4 feed-forward
- Description: Use f instead of e.
- Corrupted: `32'h510e527f + nf`
- Correct: `32'h510e527f + ne`

## Fault 47 — SEMANTIC

- Location: digest H7 feed-forward
- Description: Use g instead of h.
- Corrupted: `32'h5be0cd19 + ng`
- Correct: `32'h5be0cd19 + nh`

## Fault 48 — SEMANTIC

- Location: reset done value
- Description: Leave done asserted after reset.
- Corrupted: `done <= 1'b1;`
- Correct: `done <= 1'b0;`

## Fault 49 — SEMANTIC

- Location: initial round index
- Description: Start processing from round 1 instead of round 0.
- Corrupted: `round <= 7'd1;`
- Correct: `round <= 7'd0;`

## Fault 50 — SEMANTIC

- Location: digest H2 feed-forward
- Description: Use b instead of c.
- Corrupted: `32'h3c6ef372 + nb`
- Correct: `32'h3c6ef372 + nc`