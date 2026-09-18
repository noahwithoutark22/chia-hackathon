#!/usr/bin/env bash
# One-shot new-machine setup: submodules, credential files, and a clear
# "what to do next" printout. Safe to re-run -- never overwrites a
# credential file that already exists, and skips submodule steps that are
# already done.
#
# Usage: ./startup.sh
set -uo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

ok()   { printf '  [ok] %s\n' "$*"; }
warn() { printf '  [!!] %s\n' "$*"; }
step() { printf '\n== %s ==\n' "$*"; }

step "Checking prerequisites"
missing=0
for cmd in docker conda git; do
    if command -v "$cmd" >/dev/null 2>&1; then
        ok "$cmd found"
    else
        warn "$cmd not found on PATH"
        missing=1
    fi
done
if command -v chia >/dev/null 2>&1; then
    ok "chia found"
else
    warn "chia not found on PATH -- activate your chia_env conda environment first: conda activate chia_env"
    missing=1
fi
if command -v ray >/dev/null 2>&1; then
    ok "ray found"
else
    warn "ray not found on PATH (also comes from chia_env)"
fi
[[ "$missing" -eq 1 ]] && warn "some prerequisites are missing -- fix those before continuing, the rest of this script will still run"

step "ORFS submodule (orfs_loop/orfs-native-build)"
if [[ -f "orfs_loop/orfs-native-build/.git" || -d "orfs_loop/orfs-native-build/.git" ]]; then
    ok "already initialized"
else
    git submodule update --init orfs_loop/orfs-native-build
    ok "initialized"
fi

if git -C orfs_loop/orfs-native-build apply --reverse --check ../orfs-native-build.patch 2>/dev/null; then
    ok "local sky130hd LVS/CDL patch already applied"
elif git -C orfs_loop/orfs-native-build apply --check ../orfs-native-build.patch 2>/dev/null; then
    git -C orfs_loop/orfs-native-build apply ../orfs-native-build.patch
    ok "applied local sky130hd LVS/CDL patch"
else
    warn "couldn't verify or apply orfs-native-build.patch -- check it by hand (git -C orfs_loop/orfs-native-build apply ../orfs-native-build.patch)"
fi

step "LLM credential files"
AUTH_JSON="$HOME/.local/share/opencode/auth.json"
OC_CONFIG="$HOME/.config/opencode/opencode.jsonc"
mkdir -p "$(dirname "$AUTH_JSON")" "$(dirname "$OC_CONFIG")"

NEEDS_AUTH_EDIT=0
NEEDS_OC_EDIT=0

if [[ -f "$AUTH_JSON" ]]; then
    ok "$AUTH_JSON already exists -- left untouched"
else
    cp templates/opencode_auth.json.example "$AUTH_JSON"
    ok "created $AUTH_JSON from template"
    NEEDS_AUTH_EDIT=1
fi

if [[ -f "$OC_CONFIG" ]]; then
    ok "$OC_CONFIG already exists -- left untouched"
else
    cp templates/opencode.jsonc.example "$OC_CONFIG"
    ok "created $OC_CONFIG from template"
    NEEDS_OC_EDIT=1
fi

step "Done -- what's left"
if [[ "$NEEDS_AUTH_EDIT" -eq 1 || "$NEEDS_OC_EDIT" -eq 1 ]]; then
    echo "Edit the placeholder keys before running anything:"
    [[ "$NEEDS_AUTH_EDIT" -eq 1 ]] && echo "  - $AUTH_JSON  (at least the \"opencode\" or \"nvidia\" key)"
    [[ "$NEEDS_OC_EDIT" -eq 1 ]]   && echo "  - $OC_CONFIG  (optional for a first run -- extra quota buckets)"
fi
echo
echo "Then, from the repo root:"
echo "  conda activate chia_env"
echo "  cd uvm_loop && docker build -t chia-rtl-worker:local -f workers/rtl/Dockerfile . && make build-sim-image && cd .."
echo "  cd orfs_loop && docker build -f Dockerfile.orfs-run -t chia-orfs-run:local . && cd .."
echo "  export CHIA_PROJECT_ROOT=\$PWD/uvm_loop CHIA_ORFS_REPO=\$PWD/orfs_loop"
echo "  chia up rtl_to_gds/cluster.yaml -y && chia status && ray status"
echo
echo "See README.md for the full walkthrough, and uvm_loop/scripts/add_llm_provider.sh"
echo "to add more provider keys once the cluster is up."
