import argparse
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--prompt",
        required=True,
    )

    parser.add_argument(
        "--model",
        default="opencode/nemotron-3.5-lightning-free",
    )

    args = parser.parse_args()

    workspace = Path("/workspace")

    if not workspace.exists():
        raise RuntimeError("Workspace does not exist")

    command = [
        "opencode",
        "run",
        "-m",
        args.model,
        args.prompt,
    ]

    print("Running OpenCode...")
    print(f"Model: {args.model}")
    print(f"Workspace: {workspace}")

    result = subprocess.run(
        command,
        cwd=workspace,
        text=True,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("OpenCode completed successfully.")


if __name__ == "__main__":
    main()