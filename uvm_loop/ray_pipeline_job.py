"""
Submit the LLM-UVM-TB-generator pipeline (Stage 1 + Stage 2, optionally
followed by the Chipyard sim) as Ray tasks pinned to the `llm_uvm_tb`
node type defined in cluster.yaml, via its custom `llm_uvm_tb_gen`
resource.

Usage (after `ray up cluster.yaml`):

    ray job submit --address http://<head_ip>:8265 \
        --working-dir . \
        -- python ray_pipeline_job.py \
             --rtl examples/adder/adder.v \
             --spec examples/adder/spec.md \
             --ref-model examples/adder/ref_model.py \
             --chipyard-dir /root/chipyard \
             --chipyard-config RocketConfig
"""
import argparse
import subprocess
import ray


@ray.remote(resources={"llm_uvm_tb_gen": 1})
def generate_plan(rtl: str, spec: str, ref_model: str) -> str:
    subprocess.run(
        [
            "python3", "scripts/generate_plan.py",
            "--rtl", rtl,
            "--spec", spec,
            "--ref-model", ref_model,
        ],
        check=True,
    )
    return "generated_plans/verification_plan.yaml"


@ray.remote(resources={"llm_uvm_tb_gen": 1})
def generate_tb(plan_path: str) -> str:
    subprocess.run(
        ["python3", "scripts/generate_tb.py", "--plan", plan_path],
        check=True,
    )
    return "generated_tb"


@ray.remote(resources={"verilator_run": 1})
def run_in_chipyard(chipyard_dir: str, chipyard_config: str) -> None:
    subprocess.run(
        ["./chipyard_integration/run_in_chipyard.sh", chipyard_dir, chipyard_config],
        check=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rtl", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--ref-model", required=True)
    parser.add_argument("--chipyard-dir", default=None,
                         help="If set, also run the generated TB in this Chipyard checkout")
    parser.add_argument("--chipyard-config", default="RocketConfig")
    args = parser.parse_args()

    ray.init(address="auto")

    plan_path = ray.get(generate_plan.remote(args.rtl, args.spec, args.ref_model))
    tb_dir = ray.get(generate_tb.remote(plan_path))
    print(f"Generated plan: {plan_path}")
    print(f"Generated testbench: {tb_dir}")

    if args.chipyard_dir:
        ray.get(run_in_chipyard.remote(args.chipyard_dir, args.chipyard_config))
        print("Chipyard sim run complete.")


if __name__ == "__main__":
    main()
