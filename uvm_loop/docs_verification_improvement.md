# Stage 5+ Verification Improvement Loop

The Stage-4 generated cocotb+pyuvm environment becomes the persistent artifact.
Stages 5+ validate it, measure weaknesses, and iteratively improve it.

## Information boundary

The simulation worker receives the RTL. The improvement/repair LLM does not.
Its sanitized workspace contains only:

- specification
- reference model
- accepted verification plan
- current generated TB
- simulation-derived weakness report

The pipeline copies only TB changes back to `the benchmark-local `tb/` directory and never copies
RTL or `rtl_info.json` into the LLM workspace.

## Stages

1. **Stage 5 — TB validation**: compile/run the generated environment. If it is
   broken, diagnose and repair using the same RTL-blind boundary.
2. **Stage 6 — baseline campaign**: run the complete manifest regression and
   collect deterministic measurements.
3. **Stage 7 — weakness analysis**: produce
   `<output_parent>/<benchmark>/results/verification_improvement/iteration_0.yaml`.
4. **Stage 8 — LLM improvement**: the model edits a sanitized copy of the
   existing TB to address the highest-value weaknesses.
5. **Stage 9 — regression and acceptance**: run the modified TB and accept it
   only if the objective quality score does not decrease and the number of
   failed tests does not increase. Otherwise restore the previous TB.

## Artifacts

- `<output_parent>/<benchmark>/results/verification_improvement/iteration_N.yaml`
- `<output_parent>/<benchmark>/tb_iterations/iteration_NN/`
- `<output_parent>/<benchmark>/llm_improvement_workspace/`
- `<output_parent>/<benchmark>/checkpoints/verification_improvement_complete.done`

## Run Stage 5+

After Stage 4 has produced the benchmark-local `tb/` directory and an accepted plan:

```bash
python3 pipeline/run_stage5_plus.py --design-config pipeline/designs/adder2.yaml
```

The active implementation is `pipeline/run14.py`; use the same `--design-config` for the benchmark you want to improve.

Set the iteration budget with:

```bash
MAX_VERIFICATION_IMPROVEMENT_ITERATIONS=10 python3 pipeline/run_stage5_plus.py --design-config pipeline/designs/adder2.yaml
```

## Important limitation

The current implementation treats mutation score as a future measurement
hook; it does not yet mutate arbitrary RTL. This is intentional. First make
coverage/requirements/assertion evidence and the RTL-blind edit/rollback loop
stable. Mutation testing can then be added as another simulator-side weakness
provider without changing the LLM boundary.
