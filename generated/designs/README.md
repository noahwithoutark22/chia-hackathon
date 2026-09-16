# Generated benchmark artifacts

This directory is intentionally kept clean in source control.

At runtime, `pipeline/run14.py` creates one isolated directory per benchmark:

```text
<output_parent>/
  <benchmark>/
    rtl/
    plans/
    tb/
    results/
    checkpoints/
    llm_tb_diagnosis_workspace/
    llm_tb_repair_workspace/
    llm_verification_analysis_workspace/
    llm_improvement_workspace/
    tb_iterations/
```

Set `output_parent` in the benchmark YAML to choose the common parent.
