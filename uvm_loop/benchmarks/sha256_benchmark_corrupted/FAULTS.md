# SHA-256 Combined 50-Fault Manifest

This RTL intentionally contains all 50 faults simultaneously.

The `correct_version` field gives the golden expression/line that should replace the corrupted version.

## Fault 01 — SEMANTIC
- Location: K[2] round constant
- Description: Change K[2] by one bit/value.
- Corrupted: `32'hb5c0fbce`
- Correct: `32'hb5c0fbcf`
- Approx. line(s): [12]

## Fault 02 — SEMANTIC
- Location: K[10] round constant
- Description: Change K[10].
- Corrupted: `32'h243185bf`
- Correct: `32'h243185be`
- Approx. line(s): [14]

## Fault 03 — SEMANTIC
- Location: K[31] round constant
- Description: Change K[31].
- Corrupted: `32'h14292977`
- Correct: `32'h14292967`
- Approx. line(s): [19]

## Fault 04 — SEMANTIC
- Location: K[45] round constant
- Description: Change K[45].
- Corrupted: `32'h90befffb`
- Correct: `32'h90befffa`
- Approx. line(s): [26]

## Fault 05 — SEMANTIC
- Location: K[55] round constant
- Description: Change K[55].
- Corrupted: `32'h8cc70218`
- Correct: `32'h8cc70208`
- Approx. line(s): [26]

## Fault 06 — SEMANTIC
- Location: message word endianness
- Description: Reverse the extraction direction.
- Corrupted: `block[i*32 +: 32]`
- Correct: `block[511 - i*32 -: 32]`
- Approx. line(s): [96]

## Fault 07 — SEMANTIC
- Location: message word extraction offset
- Description: Shift the part-select by one bit.
- Corrupted: `block[510 - i*32 -: 32]`
- Correct: `block[511 - i*32 -: 32]`
- Approx. line(s): [96]

## Fault 08 — SEMANTIC
- Location: schedule sigma1 dependency
- Description: Use the wrong prior schedule word.
- Corrupted: `SmallSigma1(W[round-3])`
- Correct: `SmallSigma1(W[round-2])`
- Approx. line(s): [122]

## Fault 09 — SEMANTIC
- Location: schedule dependency W[t-7]
- Description: Use W[t-8].
- Corrupted: `W[round-8]`
- Correct: `W[round-7]`
- Approx. line(s): [123]

## Fault 10 — SEMANTIC
- Location: schedule sigma0 dependency
- Description: Use W[t-14].
- Corrupted: `SmallSigma0(W[round-14])`
- Correct: `SmallSigma0(W[round-15])`
- Approx. line(s): [124]

## Fault 11 — SEMANTIC
- Location: schedule dependency W[t-16]
- Description: Use W[t-17].
- Corrupted: `W[round-17]`
- Correct: `W[round-16]`
- Approx. line(s): [125]

## Fault 12 — SEMANTIC
- Location: BigSigma0 ROTR2
- Description: Use the wrong rotation amount.
- Corrupted: `rotr(x,3)`
- Correct: `rotr(x,2)`
- Approx. line(s): [50]

## Fault 13 — SEMANTIC
- Location: BigSigma0 ROTR13
- Description: Use ROTR12.
- Corrupted: `rotr(x,12)`
- Correct: `rotr(x,13)`
- Approx. line(s): [50, 54]

## Fault 14 — SEMANTIC
- Location: BigSigma0 ROTR22
- Description: Use ROTR21.
- Corrupted: `rotr(x,21)`
- Correct: `rotr(x,22)`
- Approx. line(s): [50]

## Fault 15 — SEMANTIC
- Location: BigSigma1 ROTR6
- Description: Use ROTR7.
- Corrupted: `rotr(x,7)`
- Correct: `rotr(x,6)`
- Approx. line(s): [54]

## Fault 16 — SEMANTIC
- Location: BigSigma1 ROTR11
- Description: Use ROTR12.
- Corrupted: `rotr(x,12)`
- Correct: `rotr(x,11)`
- Approx. line(s): [50, 54]

## Fault 17 — SEMANTIC
- Location: BigSigma1 ROTR25
- Description: Use ROTR24.
- Corrupted: `rotr(x,24)`
- Correct: `rotr(x,25)`
- Approx. line(s): [54]

## Fault 18 — SEMANTIC
- Location: SmallSigma0 ROTR7
- Description: Use ROTR8.
- Corrupted: `rotr(x,8)`
- Correct: `rotr(x,7)`
- Approx. line(s): [58]

## Fault 19 — SEMANTIC
- Location: SmallSigma0 ROTR18
- Description: Use ROTR17.
- Corrupted: `rotr(x,17)`
- Correct: `rotr(x,18)`
- Approx. line(s): [58]

## Fault 20 — SEMANTIC
- Location: SmallSigma0 SHR3
- Description: Use SHR2.
- Corrupted: `(x >> 2)`
- Correct: `(x >> 3)`
- Approx. line(s): [58]

## Fault 21 — SEMANTIC
- Location: SmallSigma1 ROTR17
- Description: Use ROTR16.
- Corrupted: `rotr(x,16)`
- Correct: `rotr(x,17)`
- Approx. line(s): [62]

## Fault 22 — SEMANTIC
- Location: SmallSigma1 ROTR19
- Description: Use ROTR20.
- Corrupted: `rotr(x,20)`
- Correct: `rotr(x,19)`
- Approx. line(s): [62]

## Fault 23 — SEMANTIC
- Location: SmallSigma1 SHR10
- Description: Use SHR9.
- Corrupted: `(x >> 9)`
- Correct: `(x >> 10)`
- Approx. line(s): [62]

## Fault 24 — SEMANTIC
- Location: Ch function
- Description: Replace ~x & z with x & z.
- Corrupted: `(x & y) ^ (x & z)`
- Correct: `(x & y) ^ (~x & z)`
- Approx. line(s): [42]

## Fault 25 — SEMANTIC
- Location: Maj function
- Description: Remove one Maj term.
- Corrupted: `(x & y) ^ (x & z)`
- Correct: `(x & y) ^ (x & z) ^ (y & z)`
- Approx. line(s): [46]

## Fault 26 — SEMANTIC
- Location: T1 h operand
- Description: Use g instead of h.
- Corrupted: `g + BigSigma1(e)`
- Correct: `h + BigSigma1(e)`
- Approx. line(s): [130]

## Fault 27 — SEMANTIC
- Location: T1 Ch operands
- Description: Swap Ch's final operands.
- Corrupted: `Ch(e,g,f)`
- Correct: `Ch(e,f,g)`
- Approx. line(s): [130]

## Fault 28 — SEMANTIC
- Location: T1 round constant
- Description: Use the next constant with wraparound.
- Corrupted: `K[(round+1) & 7'd63]`
- Correct: `K[round]`
- Approx. line(s): [130]

## Fault 29 — SEMANTIC
- Location: T2 Sigma function
- Description: Use Σ1 instead of Σ0.
- Corrupted: `BigSigma1(a) + Maj(a,b,c)`
- Correct: `BigSigma0(a) + Maj(a,b,c)`
- Approx. line(s): [131]

## Fault 30 — SEMANTIC
- Location: T2 Maj operands
- Description: Permute Maj operands.
- Corrupted: `Maj(a,c,b)`
- Correct: `Maj(a,b,c)`
- Approx. line(s): [131]

## Fault 31 — SEMANTIC
- Location: new a calculation
- Description: Use XOR instead of addition.
- Corrupted: `na = next_t1 ^ next_t2;`
- Correct: `na = next_t1 + next_t2;`
- Approx. line(s): [133]

## Fault 32 — SEMANTIC
- Location: new d calculation
- Description: Break the working-variable shift.
- Corrupted: `nd = d;`
- Correct: `nd = c;`
- Approx. line(s): []

## Fault 33 — SEMANTIC
- Location: new e calculation
- Description: Use T2 instead of T1.
- Corrupted: `ne = d + next_t2;`
- Correct: `ne = d + next_t1;`
- Approx. line(s): [137]

## Fault 34 — SEMANTIC
- Location: new b calculation
- Description: Do not shift a into b.
- Corrupted: `nb = b;`
- Correct: `nb = a;`
- Approx. line(s): [134]

## Fault 35 — SEMANTIC
- Location: new c calculation
- Description: Do not shift b into c.
- Corrupted: `nc = c;`
- Correct: `nc = b;`
- Approx. line(s): [135]

## Fault 36 — SEMANTIC
- Location: new d calculation (second independent edit)
- Description: Perturb d with an extra one.
- Corrupted: `nd = c + 32'd1;`
- Correct: `nd = d;`
- Approx. line(s): [136]

## Fault 37 — SEMANTIC
- Location: new f calculation
- Description: Do not shift e into f.
- Corrupted: `nf = f;`
- Correct: `nf = e;`
- Approx. line(s): [138]

## Fault 38 — SEMANTIC
- Location: new g calculation
- Description: Do not shift f into g.
- Corrupted: `ng = g;`
- Correct: `ng = f;`
- Approx. line(s): [139]

## Fault 39 — SEMANTIC
- Location: new h calculation
- Description: Do not shift g into h.
- Corrupted: `nh = h;`
- Correct: `nh = g;`
- Approx. line(s): [140]

## Fault 40 — SEMANTIC
- Location: terminal round condition
- Description: Finish one round early.
- Corrupted: `if (round == 62)`
- Correct: `if (round == 63)`
- Approx. line(s): [151]

## Fault 41 — SEMANTIC
- Location: round increment
- Description: Advance by two.
- Corrupted: `round <= round + 2'd2;`
- Correct: `round <= round + 1'b1;`
- Approx. line(s): [165]

## Fault 42 — SEMANTIC
- Location: start/busy gating
- Description: Accept start even while busy.
- Corrupted: `if (start)`
- Correct: `if (start && !busy)`
- Approx. line(s): [94]

## Fault 43 — SEMANTIC
- Location: default done assignment
- Description: Invert the default done value.
- Corrupted: `done <= 1'b1;`
- Correct: `done <= 1'b0;`
- Approx. line(s): [163]

## Fault 44 — SEMANTIC
- Location: busy completion assignment
- Description: Remain busy after completion.
- Corrupted: `busy <= 1'b1;`
- Correct: `busy <= 1'b0;`
- Approx. line(s): [162]

## Fault 45 — SEMANTIC
- Location: digest H0 feed-forward
- Description: Use final b for H0.
- Corrupted: `32'h6a09e667 + nb`
- Correct: `32'h6a09e667 + na`
- Approx. line(s): [153]

## Fault 46 — SEMANTIC
- Location: digest H4 feed-forward
- Description: Use final f for H4.
- Corrupted: `32'h510e527f + nf`
- Correct: `32'h510e527f + ne`
- Approx. line(s): [157]

## Fault 47 — SEMANTIC
- Location: digest H7 feed-forward
- Description: Use final g for H7.
- Corrupted: `32'h5be0cd19 + ng`
- Correct: `32'h5be0cd19 + nh`
- Approx. line(s): [160]

## Fault 48 — SEMANTIC
- Location: reset done value
- Description: Leave done asserted after reset.
- Corrupted: `done   <= 1'b1;`
- Correct: `done   <= 1'b0;`
- Approx. line(s): [72]

## Fault 49 — SYNTACTIC
- Location: missing semicolon on next_w declaration
- Description: Remove a declaration semicolon.
- Corrupted: `logic [31:0] next_w`
- Correct: `logic [31:0] next_w;`
- Approx. line(s): [66]

## Fault 50 — SYNTACTIC
- Location: missing semicolon on done assignment
- Description: Remove an assignment semicolon.
- Corrupted: `done <= 1'b0`
- Correct: `done <= 1'b0;`
- Approx. line(s): [92, 163]
