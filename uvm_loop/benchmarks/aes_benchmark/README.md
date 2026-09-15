# Functionally Correct AES-128 Benchmark

```text
aes_benchmark_correct/
├── README.md
├── rtl/
│   └── aes128.sv
├── reference_model/
│   └── aes_reference_model.py
└── spec/
    └── aes_spec.md
```

The SystemVerilog DUT is a synthesizable-style iterative AES-128 encryption
core. It performs the standard 10 AES rounds and uses a registered key and
state.

The Python reference model is independent and is the source of expected
results.

Known-answer test:

```text
Key        = 000102030405060708090a0b0c0d0e0f
Plaintext  = 00112233445566778899aabbccddeeff
Ciphertext = 69c4e0d86a7b0430d8cdb78070b4c55a
```
