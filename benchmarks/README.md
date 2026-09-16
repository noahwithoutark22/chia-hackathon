# RTL benchmark inputs

Place each design's RTL, specification, and Python reference model in its own
directory. The pipeline consumes these through a design YAML configuration.

Example:
```text
benchmarks/alu/
├── alu.sv
├── specification.md
└── ref_model.py
```

Do not copy an existing generated testbench into a benchmark. The verification
environment should be generated from the specification/reference model inputs.
