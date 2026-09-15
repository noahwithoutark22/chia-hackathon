"""
Stage 1 of the pipeline: sends RTL + a natural-language spec + a
reference/golden model to Claude, and gets back a schema-validated
verification_plan.yaml.
"""
from __future__ import annotations

import argparse
import os

import yaml
from pydantic import ValidationError

from src.llm_client import LLMClient
from src.rtl_parser import parse_rtl_file
from src.schema import VerificationPlan

SYSTEM_PROMPT = """You are a senior verification engineer generating a \
UVM verification plan. You will be given: (1) RTL source for a DUT, (2) a \
natural-language specification, (3) a reference/golden model, and (4) a \
JSON schema. Respond with ONLY a single JSON object that validates against \
the schema — no markdown fences, no prose, no commentary before or after."""

USER_PROMPT_TEMPLATE = """## RTL (parsed hints)
Module: {module_name}
Parameters: {parameters}
Ports: {ports}

## RTL source
```
{rtl_source}
```

## Specification
{spec}

## Reference / golden model
```python
{ref_model}
```

## JSON schema to satisfy
{schema}

Produce a verification_plan JSON object with: dut_name, description, \
clock_signal, reset_signal, reset_active_low, parameters, ports (direction \
+ width for every port above), a useful set of test_scenarios (mix of \
directed edge cases and randomized sequences), coverage_groups tied to \
real signals, and a scoreboard_strategy referencing the reference model.
"""


def build_user_prompt(rtl_path: str, spec_path: str, ref_model_path: str) -> str:
    mod = parse_rtl_file(rtl_path)
    with open(rtl_path) as f:
        rtl_source = f.read()
    with open(spec_path) as f:
        spec = f.read()
    with open(ref_model_path) as f:
        ref_model = f.read()

    return USER_PROMPT_TEMPLATE.format(
        module_name=mod.name,
        parameters=[p.__dict__ for p in mod.parameters],
        ports=[p.__dict__ for p in mod.ports],
        rtl_source=rtl_source,
        spec=spec,
        ref_model=ref_model,
        schema=VerificationPlan.model_json_schema(),
    )


def generate_plan(rtl_path: str, spec_path: str, ref_model_path: str) -> VerificationPlan:
    client = LLMClient()
    user_prompt = build_user_prompt(rtl_path, spec_path, ref_model_path)
    raw = client.generate_json(SYSTEM_PROMPT, user_prompt)
    try:
        return VerificationPlan.model_validate(raw)
    except ValidationError as e:
        raise ValueError(
            f"LLM response did not match VerificationPlan schema:\n{e}\n\nRaw:\n{raw}"
        ) from e


def main():
    parser = argparse.ArgumentParser(description="Generate verification_plan.yaml from RTL + spec + ref model")
    parser.add_argument("--rtl", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--ref-model", required=True)
    parser.add_argument("--out", default=None, help="Output plan path; defaults to <out-parent>/<benchmark>/plans/verification_plan.yaml when --benchmark is set")
    parser.add_argument("--benchmark", default=None, help="Benchmark name used for isolated generated output")
    parser.add_argument("--out-parent", default="generated/designs", help="Parent for isolated benchmark output")
    args = parser.parse_args()

    plan = generate_plan(args.rtl, args.spec, args.ref_model)

    if args.out:
        output = args.out
    elif args.benchmark:
        output = os.path.join(args.out_parent, args.benchmark, "plans", "verification_plan.yaml")
    else:
        raise SystemExit("Specify --out or use --benchmark")

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w") as f:
        yaml.safe_dump(plan.model_dump(), f, sort_keys=False)

    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
