"""Submit the lightweight plan/TB generator as isolated Ray tasks.

The legacy Ray wrapper is retained for environments that use it directly.
All generated outputs are benchmark-scoped: <output-parent>/<benchmark>/.
The full CHIA Stage 1-5+ flow is in pipeline/run14.py.
"""
import argparse
import subprocess
from pathlib import Path
import ray
import yaml


def load_design(config_path: str) -> dict:
    cfg = yaml.safe_load(Path(config_path).read_text()) or {}
    if not isinstance(cfg, dict):
        raise ValueError("Design config must be a mapping")
    name = str(cfg.get("name", "")).strip()
    if not name:
        raise ValueError("Design config requires name")
    parent = str(cfg.get("output_parent", "generated/designs")).strip().rstrip("/")
    return cfg | {"output_parent": parent, "generated_root": f"{parent}/{name}"}


@ray.remote(resources={"llm_uvm_tb_gen": 1})
def generate_plan(rtl: str, spec: str, ref_model: str, out: str) -> str:
    subprocess.run(
        ["python3", "scripts/generate_plan.py", "--rtl", rtl, "--spec", spec,
         "--ref-model", ref_model, "--out", out],
        check=True,
    )
    return out


@ray.remote(resources={"llm_uvm_tb_gen": 1})
def generate_tb(plan_path: str, generation_spec: str, rtl: str, spec: str, ref_model: str, out_dir: str) -> str:
    subprocess.run(
        ["python3", "scripts/generate_tb.py", "--plan", plan_path,
         "--generation-spec", generation_spec, "--rtl", rtl, "--spec", spec,
         "--ref-model", ref_model, "--out-dir", out_dir],
        check=True,
    )
    return out_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--design-config", default="pipeline/designs/adder.yaml")
    parser.add_argument("--generation-spec", default="generation_spec.json")
    args = parser.parse_args()

    cfg = load_design(args.design_config)
    root = cfg["generated_root"]
    plan = f"{root}/plans/verification_plan.yaml"
    tb = f"{root}/tb"

    ray.init(address="auto")
    plan_path = ray.get(
        generate_plan.remote(cfg["rtl"], cfg["spec"], cfg["ref_model"], plan)
    )
    tb_dir = ray.get(
        generate_tb.remote(
            plan_path, args.generation_spec, cfg["rtl"], cfg["spec"],
            cfg["ref_model"], tb,
        )
    )
    print(f"Generated plan: {plan_path}")
    print(f"Generated testbench: {tb_dir}")


if __name__ == "__main__":
    main()
