# Designs

One directory per design, holding everything that design needs: the RTL, the
specification, the Python reference model, and the config that ties them
together.

```text
benchmarks/fifo/
├── fifo.sv        # the RTL under verification
├── spec.md        # INTENDED behaviour (not what the RTL currently does)
├── ref_model.py   # Python model of expected behaviour, used for scoreboarding
└── design.yaml    # config — this is what you pass to the pipeline
```

Run it:

```bash
python3 -m pipeline.run14 --design-config benchmarks/fifo/design.yaml
```

## Adding your own

Copy `TEMPLATE.yaml` into a new directory as `design.yaml` and fill it in:

```yaml
name: my_fifo                              # names the output dir, must be unique
rtl: benchmarks/my_fifo/my_fifo.sv
spec: benchmarks/my_fifo/spec.md
ref_model: benchmarks/my_fifo/ref_model.py
output_parent: generated/designs
```

Paths inside the config are resolved relative to `uvm_loop/`, not to the
config's own location.

| Field | |
|---|---|
| `name` | Required. Output lands in `<output_parent>/<name>/`, so it must be unique. |
| `rtl`, `spec`, `ref_model` | Required. |
| `output_parent` | Optional parent for generated artifacts (default `generated/designs`). |
| `tb_dir` | Advanced override for the generated TB location; must stay inside the design's generated directory. |
| `generated_root` | Legacy. Prefer `output_parent`; if present it must equal `<output_parent>/<name>`. |

`spec.md` should describe **intended** behaviour — inputs/outputs, widths,
reset and clock behaviour, handshakes, expected outputs, corner cases, timing
and protocol requirements. The loop may modify the RTL to match the spec, so a
spec that just describes the current RTL defeats the point.

Don't copy an existing generated testbench into a design directory. The
verification environment is meant to be generated from the spec and reference
model, so that a mismatch is attributed to the RTL rather than baked into the
testbench.

Everything the run produces — generated plan, RTL extraction, the Cocotb +
pyUVM testbench, simulator build and results, checkpoints, diagnosis/repair
workspaces and improvement reports — stays under that design's generated
directory.

## What's here

`*_corrupted` designs have deliberate faults injected, documented in each
directory's `FAULTS.md`; they exist to prove the loop finds and repairs real
bugs rather than passing trivially.
