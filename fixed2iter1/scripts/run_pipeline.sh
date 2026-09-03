#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/generate_plan.py \
  --rtl examples/adder/adder.v \
  --spec examples/adder/spec.md \
  --ref-model examples/adder/ref_model.py

python3 scripts/generate_tb.py \
  --plan generated_plans/verification_plan.yaml

echo
echo "Done. Inspect with:"
echo "  cat generated_plans/verification_plan.yaml"
echo "  ls generated_tb/"
