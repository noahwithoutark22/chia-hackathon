# AES-128 Encryption Benchmark Specification

The DUT shall implement standard AES-128 encryption for one 128-bit block.

## Interface

- `clk`: synchronous clock.
- `rst_n`: active-low asynchronous reset.
- `start`: accepted only while idle; launches a transaction.
- `key[127:0]`: AES-128 key.
- `plaintext[127:0]`: 128-bit plaintext.
- `ciphertext[127:0]`: encrypted result.
- `busy`: high while a transaction is active.
- `done`: one-clock completion pulse.

## Functional behavior

When `start` is accepted, the DUT shall capture the key and plaintext.
Changes on the input ports after acceptance shall not affect the active
transaction.

The operation shall be exactly:

`ciphertext = AES-128-encrypt(key, plaintext)`

using the standard AES-128 algorithm:
- initial AddRoundKey
- 10 rounds
- SubBytes
- ShiftRows
- MixColumns in rounds 1-9
- AddRoundKey in every round
- no MixColumns in round 10

## Reset

During reset:
- `busy=0`
- `done=0`
- `ciphertext=0`

## Completion

After encryption completes:
- `ciphertext` is valid
- `done` pulses for exactly one clock
- `busy` returns low

## Required verification vectors

NIST AES-128 known-answer test:

Key:
`000102030405060708090a0b0c0d0e0f`

Plaintext:
`00112233445566778899aabbccddeeff`

Ciphertext:
`69c4e0d86a7b0430d8cdb78070b4c55a`

Also test:
- all-zero key/plaintext
- all-one key/plaintext
- alternating bit patterns
- random vectors
- repeated transactions
- input changes while busy
- reset during idle and between transactions
- exact done pulse behavior

## Verification isolation

The Python reference model is authoritative for expected ciphertext.
The candidate RTL must not be used to modify the specification, reference
model, scoreboard expectations, assertions, stimulus, or coverage.

If RTL repair is enabled, repair only a working copy. Never modify the
original benchmark input.
