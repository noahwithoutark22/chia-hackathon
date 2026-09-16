import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Extract concise SystemVerilog RTL information."
    )
    parser.add_argument("--rtl", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rtl = Path(args.rtl)
    output = Path(args.output)

    if not rtl.exists():
        raise FileNotFoundError(f"RTL file not found: {rtl}")

    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        cst_path = Path(tmp) / "rtl_cst.json"

        # Stage 1: Verible → CST JSON
        result = subprocess.run(
            [
                "verible-verilog-syntax",
                "--export_json",
                "--printtree",
                "--lang",
                "sv",
                str(rtl),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(result.stderr)
            raise SystemExit(result.returncode)

        cst_path.write_text(result.stdout)

        # Stage 2: CST → concise RTL information
        extractor = Path("/opt/rtl-worker/extract_concise.py")

        result = subprocess.run(
            [
                "python3",
                str(extractor),
                str(cst_path),
                str(output),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise SystemExit(result.returncode)

        print(result.stdout)


if __name__ == "__main__":
    main()