# CHIA-oriented redesign

CHIA remains on the host. Docker isolates tools:

1. `workers/rtl` - Slang-based RTL semantic extraction
2. `workers/llm` - model-independent LLM reasoning
3. `workers/sim` - Verilator/UVM simulation

`chia/` is the orchestration layer and is the only place where the CHIA
API/decorators should be introduced.

Artifacts are the worker interfaces:

RTL -> `generated/rtl/rtl_info.json`
   -> `generated/plans/verification_plan.yaml`
   -> `generated/tb/*.sv`
   -> `generated/results/simulation_result.json`

The current worker implementations are scaffolds intentionally. The next
step is to wire the actual locally installed CHIA API, then implement the
Slang worker contract.
