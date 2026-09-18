#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

DESIGN_CONFIG="${DESIGN_CONFIG:-pipeline/designs/adder.yaml}"

python3 -m pipeline.run14 --design-config "$DESIGN_CONFIG"

echo
echo "Done. Generated benchmark artifacts are under the benchmark output directory configured in:"
echo "  $DESIGN_CONFIG"
