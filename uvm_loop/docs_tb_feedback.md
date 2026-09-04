# Generated UVM TB validation and repair loop

The active pipeline in `pipeline/run4.py` now performs:

1. Generate the VerificationPlan.
2. Review/repair the VerificationPlan.
3. Generate `generated_tb/`.
4. Deterministically prepare `generation_manifest.yaml`.
5. Run every manifest-listed UVM test with Verilator + UVM + the Python reference model.
6. Classify the result.
7. If the failure is generation-specific, ask the LLM for `tb_update_plan_iteration_N.yaml`.
8. Ask the LLM to apply only that plan to `generated_tb/`.
9. Rebuild and rerun, up to `MAX_TB_REPAIR_ATTEMPTS`.

## Simulation worker image

Build the Ray-compatible simulation image:

```bash
make build-sim-image
```

It is based on the CHIA runtime image and installs:

- Verilator 5.042
- UVM 1800.2-2020.3.1
- Python development headers
- PyYAML

The standalone simulation image remains available through `workers/sim/Dockerfile`.

## Ray cluster

`cluster.yaml` adds a `hello_sim` node with the `sim_worker` resource. It mounts the project at `/workspace`, so the simulator, OpenCode repair agent, and generated artifacts share the same files.

## Manifest contract

New TB generations must write these fields in `generated_tb/generation_manifest.yaml`:

```yaml
top_module: adder_tb_top
top_file: adder_tb_top.sv
compile_files:
  - adder_if.sv
  - adder_ref_model_pkg.sv
  - adder_transaction.sv
  # ...
  - adder_tb_top.sv
test_classes:
  - adder_test_randomized_full_space#(8)
```

`compile_files` contains only direct Verilator inputs. The Python reference model and C++ adapter are not listed there; the simulation worker compiles the adapter separately.

## Result artifacts

Each validation iteration produces:

```text
generated/results/tb_validation_iteration_0.json
generated/results/tb_update_plan_iteration_0.yaml
generated/results/tb_validation_iteration_1.json
...
```

A clean pass requires every listed test to exit without the OS timeout, without the CHIA watchdog expiring, and without UVM errors/fatals.
