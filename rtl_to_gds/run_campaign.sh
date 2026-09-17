#!/usr/bin/env bash
# Fresh end-to-end rtl_to_gds evaluation over several designs, archiving every artifact.
#   nohup setsid rtl_to_gds/run_campaign.sh > /dev/null 2>&1 &
# Results: eval_results/<campaign>/  (progress: eval_results/<campaign>/campaign.log)
eval "$("${CONDA_EXE:-$HOME/miniconda3/bin/conda}" shell.bash hook)"
conda activate chia_env
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESIGNS=(${DESIGNS:-hamming_encoder i2c_benchmark aes_benchmark})
CAMPAIGN="${CAMPAIGN:-paper_eval_$(date +%Y%m%d_%H%M%S)}"
OUT="$REPO/eval_results/$CAMPAIGN"
UVM_MAX_ITERS="${UVM_MAX_ITERS:-20}"
DESIGN_TIMEOUT="${DESIGN_TIMEOUT:-72h}"
ORFS_ARGS=(${ORFS_ARGS:---model nvidia/nvidia/nemotron-3-super-120b-a12b --objective area --max-iterations 3 --batch-size 3 --stage-timeout-seconds 7200})

declare -A EXTRA=(
    [hamming_encoder]="--core-utilization 10"   # ~20 cells: PDN-0185 at 40%
)

export CHIA_PROJECT_ROOT="$REPO/uvm_loop"
export CHIA_ORFS_REPO="${CHIA_ORFS_REPO:-$HOME/Desktop/chia-orfs}"
export LLM_MODEL="${LLM_MODEL:-opencode/big-pickle}"
export PYTHONUNBUFFERED=1

mkdir -p "$OUT"
LOG="$OUT/campaign.log"
log() { printf '[%s] %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" | tee -a "$LOG"; }

# ---- campaign metadata ------------------------------------------------------
{
    echo "campaign: $CAMPAIGN"
    echo "started_at: $(date -Iseconds)"
    echo "designs: ${DESIGNS[*]}"
    echo "uvm_llm_model: $LLM_MODEL"
    echo "uvm_max_improvement_iters: $UVM_MAX_ITERS"
    echo "design_timeout: $DESIGN_TIMEOUT"
    echo "orfs_args: ${ORFS_ARGS[*]}"
    for d in "${DESIGNS[@]}"; do echo "extra_args_$d: ${EXTRA[$d]:-}"; done
    echo "chia_orfs_repo: $CHIA_ORFS_REPO"
    echo "hackathon_git_rev: $(git -C "$REPO" rev-parse HEAD)"
    echo "chia_orfs_git_rev: $(git -C "$CHIA_ORFS_REPO" rev-parse HEAD 2>/dev/null)"
    echo "orfs_submodule_rev: $(git -C "$CHIA_ORFS_REPO/orfs-native-build" rev-parse HEAD 2>/dev/null)"
    echo "host: $(hostname) cpus=$(nproc) mem=$(free -g | awk '/Mem:/{print $2}')G"
    echo "python: $(python3 --version 2>&1) ray: $(python3 -c 'import ray;print(ray.__version__)' 2>/dev/null)"
} > "$OUT/metadata.yaml"
git -C "$REPO" status --short > "$OUT/git_status.txt"
git -C "$REPO" diff > "$OUT/git_diff.patch"
cp "$REPO/rtl_to_gds/cluster.yaml" "$REPO/rtl_to_gds/rtl_to_gds.py" "$OUT/"
docker images --digests --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Digest}}' | grep chia > "$OUT/docker_images.txt"
chia status > "$OUT/ray_status_start.txt" 2>&1

# ---- archive previous UVM results so the run starts fresh -------------------
ARCHIVE="$REPO/eval_results/pre_${CAMPAIGN}_uvm_generated"
for d in "${DESIGNS[@]}"; do
    src="$REPO/uvm_loop/generated/designs/$d"
    if [[ -e "$src" ]]; then
        mkdir -p "$ARCHIVE"
        mv "$src" "$ARCHIVE/$d"
        log "archived previous UVM results: $src -> $ARCHIVE/$d"
    fi
done

# ---- per design ---------------------------------------------------------------
collect() {
    local d="$1" dout="$OUT/$1"
    cp -r --preserve=timestamps "$REPO/uvm_loop/generated/designs/$d" "$dout/uvm_generated" 2>>"$LOG"
    local design_dir run_dir
    design_dir=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('orfs_design_dir') or '')" "$dout/rtl_to_gds.json" 2>/dev/null)
    run_dir=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('orfs_run_dir') or '')" "$dout/rtl_to_gds.json" 2>/dev/null)
    [[ -n "$design_dir" && -d "$design_dir" ]] && cp -r --preserve=timestamps "$design_dir" "$dout/orfs_design" 2>>"$LOG"
    [[ -n "$run_dir" && -d "$run_dir" ]] && cp -r --preserve=timestamps "$run_dir" "$dout/orfs_run" 2>>"$LOG"
    [[ -f "$dout/orfs_run/final.gds" ]] && cp "$dout/orfs_run/final.gds" "$dout/$d.final.gds"
    log "$d: artifacts collected in $dout ($(du -sh "$dout" | cut -f1))"
}

for d in "${DESIGNS[@]}"; do
    dout="$OUT/$d"
    mkdir -p "$dout"
    log "===== $d: starting (UVM -> handoff -> ORFS) ====="
    # shellcheck disable=SC2086
    timeout --signal=INT --kill-after=10m "$DESIGN_TIMEOUT" \
        python3 "$REPO/rtl_to_gds/rtl_to_gds.py" \
            --design-config "pipeline/designs/$d.yaml" \
            --orfs-repo "$CHIA_ORFS_REPO" \
            --uvm-supervised "$UVM_MAX_ITERS" \
            --result-json "$dout/rtl_to_gds.json" \
            ${EXTRA[$d]:-} \
            -- "${ORFS_ARGS[@]}" \
        > "$dout/pipeline.log" 2>&1
    rc=$?
    echo "$rc" > "$dout/exit_code"
    log "$d: finished with exit code $rc"
    collect "$d"
done

chia status > "$OUT/ray_status_end.txt" 2>&1
echo "finished_at: $(date -Iseconds)" >> "$OUT/metadata.yaml"
log "===== campaign complete: $OUT ====="
