# Multi-RTL benchmark configurations

Each YAML file describes one RTL benchmark for `pipeline/run14.py`.

Required fields:
- `name`
- `rtl`
- `spec`
- `ref_model`

Optional:
- `output_parent`: parent directory for generated artifacts. The pipeline always creates an isolated `<output_parent>/<name>/` directory.
- `tb_dir`: advanced override for the generated TB location; it must remain inside the benchmark generated directory.
- `generated_root`: legacy compatibility key. Prefer `output_parent`; when present, it must equal `<output_parent>/<name>`.

For example:
```bash
python -m pipeline.run14 --design-config pipeline/designs/fifo.yaml
```

For a new benchmark, copy a YAML file, change the input paths and give it a
unique `name`. Set `output_parent` to the desired common parent. Generated
plans, RTL extraction, the complete Cocotb+pyUVM TB, simulator build/results,
checkpoints, diagnosis/repair workspaces, and verification-improvement reports
will all stay under that benchmark's directory.
