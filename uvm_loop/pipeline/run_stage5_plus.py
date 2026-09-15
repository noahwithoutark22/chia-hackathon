"""Run Stage 5+ on one benchmark's existing generated verification environment."""
from __future__ import annotations

import argparse
import ray

import pipeline.run14 as pipeline14


def main():
    parser = argparse.ArgumentParser(description="Run Stage 5+ for one benchmark")
    parser.add_argument(
        "--design-config",
        default="pipeline/designs/adder.yaml",
        help="Project-relative benchmark configuration",
    )
    args = parser.parse_args()

    pipeline14.configure_design(args.design_config)

    plan_path = pipeline14.HOST_WORKSPACE / pipeline14.PLAN
    rtl_info = pipeline14.HOST_WORKSPACE / pipeline14.RTL_INFO
    if not plan_path.exists():
        raise SystemExit(f"Missing accepted verification plan: {plan_path}")
    if not rtl_info.exists():
        raise SystemExit(f"Missing RTL extraction artifact: {rtl_info}")
    if not pipeline14.TB_DIR.is_dir():
        raise SystemExit(
            f"Missing generated TB: {pipeline14.TB_DIR}; complete Stage 4 first."
        )

    ray.init()
    llm, bash = pipeline14.create_agent()
    try:
        pipeline14.generate_and_validate_uvm(llm, bash, plan_path.read_text())
    finally:
        bash.stop()
        ray.shutdown()


if __name__ == "__main__":
    main()
