#!/usr/bin/env bash
# Run the whole pipeline on a new design: RTL + spec + reference model in,
# a UVM-verified, place-and-routed GDS out. This is the one command a user
# should need after dropping in their own RTL.
#
# Usage:
#   scripts/run_full_flow.sh <design_name> <rtl_file> <spec_file> <ref_model_file> [output_dir]
#
# Example:
#   scripts/run_full_flow.sh my_fifo path/to/my_fifo.sv path/to/spec.md path/to/ref_model.py
#
# What it does:
#   1. Copies the 3 input files into uvm_loop/benchmarks/<design_name>/ (if not already there).
#   2. Writes uvm_loop/pipeline/designs/<design_name>.yaml (the design config rtl_to_gds.py needs).
#   3. Runs rtl_to_gds.py under the run_forever.sh supervisor (--uvm-supervised), so the LLM
#      model fallback pool actually engages on a rate limit instead of the whole run dying.
#   4. Writes results/<design_name>/pipeline.log (full unbuffered log) and rtl_to_gds.json
#      (stage timings, UVM verification state, ORFS/signoff outcome).
#
# Defaults (override via env vars before calling):
#   UVM_MAX_ITERS=20 CORE_UTILIZATION=40 CLOCK_PERIOD=10 OBJECTIVE=area
#   ORFS_MAX_ITERATIONS=3 ORFS_BATCH_SIZE=3 ORFS_STAGE_TIMEOUT=7200
set -euo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
    echo "Usage: $0 <design_name> <rtl_file> <spec_file> <ref_model_file> [output_dir]" >&2
    exit 2
fi

DESIGN_NAME="$1"
RTL_FILE="$2"
SPEC_FILE="$3"
REF_MODEL_FILE="$4"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${5:-$REPO/results/$DESIGN_NAME}"

for f in "$RTL_FILE" "$SPEC_FILE" "$REF_MODEL_FILE"; do
    [[ -f "$f" ]] || { echo "ERROR: not a file: $f" >&2; exit 1; }
done

BENCH_DIR="$REPO/uvm_loop/benchmarks/$DESIGN_NAME"
mkdir -p "$BENCH_DIR" "$OUT_DIR"

RTL_BASENAME="$(basename "$RTL_FILE")"
SPEC_BASENAME="$(basename "$SPEC_FILE")"
REF_MODEL_BASENAME="$(basename "$REF_MODEL_FILE")"

cp -n "$RTL_FILE" "$BENCH_DIR/$RTL_BASENAME" 2>/dev/null || true
cp -n "$SPEC_FILE" "$BENCH_DIR/$SPEC_BASENAME" 2>/dev/null || true
cp -n "$REF_MODEL_FILE" "$BENCH_DIR/$REF_MODEL_BASENAME" 2>/dev/null || true

DESIGN_CONFIG="$REPO/uvm_loop/pipeline/designs/$DESIGN_NAME.yaml"
cat > "$DESIGN_CONFIG" <<EOF
name: $DESIGN_NAME
rtl: benchmarks/$DESIGN_NAME/$RTL_BASENAME
spec: benchmarks/$DESIGN_NAME/$SPEC_BASENAME
ref_model: benchmarks/$DESIGN_NAME/$REF_MODEL_BASENAME
output_parent: generated/designs
EOF
echo "Wrote design config: $DESIGN_CONFIG"

eval "$("${CONDA_EXE:-$HOME/miniconda3/bin/conda}" shell.bash hook)"
conda activate chia_env

export CHIA_PROJECT_ROOT="$REPO/uvm_loop"
export CHIA_ORFS_REPO="${CHIA_ORFS_REPO:-$HOME/Desktop/chia-orfs}"
export PYTHONUNBUFFERED=1

UVM_MAX_ITERS="${UVM_MAX_ITERS:-20}"
CORE_UTILIZATION="${CORE_UTILIZATION:-40}"
CLOCK_PERIOD="${CLOCK_PERIOD:-10}"
OBJECTIVE="${OBJECTIVE:-area}"
ORFS_MAX_ITERATIONS="${ORFS_MAX_ITERATIONS:-3}"
ORFS_BATCH_SIZE="${ORFS_BATCH_SIZE:-3}"
ORFS_STAGE_TIMEOUT="${ORFS_STAGE_TIMEOUT:-7200}"

echo "Design config       : pipeline/designs/$DESIGN_NAME.yaml"
echo "ORFS repo            : $CHIA_ORFS_REPO"
echo "Output               : $OUT_DIR"
echo "UVM max iterations   : $UVM_MAX_ITERS"
echo "Core utilization %   : $CORE_UTILIZATION"
echo "Clock period (ns)    : $CLOCK_PERIOD"
echo "Starting..."

cd "$REPO"
python3 rtl_to_gds/rtl_to_gds.py \
    --design-config "pipeline/designs/$DESIGN_NAME.yaml" \
    --orfs-repo "$CHIA_ORFS_REPO" \
    --uvm-supervised "$UVM_MAX_ITERS" \
    --core-utilization "$CORE_UTILIZATION" \
    --clock-period "$CLOCK_PERIOD" \
    --result-json "$OUT_DIR/rtl_to_gds.json" \
    -- --objective "$OBJECTIVE" --max-iterations "$ORFS_MAX_ITERATIONS" \
       --batch-size "$ORFS_BATCH_SIZE" --stage-timeout-seconds "$ORFS_STAGE_TIMEOUT" \
    2>&1 | tee "$OUT_DIR/pipeline.log"

echo
echo "Done. Log: $OUT_DIR/pipeline.log"
echo "Result JSON (UVM state, ORFS outcome, signoff): $OUT_DIR/rtl_to_gds.json"
