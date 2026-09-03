#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# CHIA project setup
# ------------------------------------------------------------

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CHIA_PROJECT_ROOT="$PROJECT_ROOT"
export THIS_MACHINE="$(hostname -I | awk '{print $1}')"

echo "========================================"
echo "CHIA LLM-UVM-TB Generator Setup"
echo "========================================"
echo
echo "Project root : $CHIA_PROJECT_ROOT"
echo "This machine: $THIS_MACHINE"
echo

# ------------------------------------------------------------
# Basic checks
# ------------------------------------------------------------

if ! command -v chia >/dev/null 2>&1; then
    echo "ERROR: 'chia' command not found."
    echo "Activate your CHIA environment first."
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not installed or not in PATH."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not accessible."
    exit 1
fi

if [[ ! -f "$PROJECT_ROOT/cluster.yaml" ]]; then
    echo "ERROR: cluster.yaml not found."
    exit 1
fi

# ------------------------------------------------------------
# Check required local RTL worker image
# ------------------------------------------------------------

if ! docker image inspect chia-rtl-worker:local >/dev/null 2>&1; then
    echo "ERROR: chia-rtl-worker:local image not found."
    echo
    echo "Build it first, for example:"
    echo
    echo "    docker build -t chia-rtl-worker:local workers/rtl"
    echo
    exit 1
fi

# ------------------------------------------------------------
# Check simulation worker image
# ------------------------------------------------------------

if ! docker image inspect chia-sim-worker:chia-local >/dev/null 2>&1; then
    echo "ERROR: chia-sim-worker:chia-local image not found."
    echo
    echo "Build it first:"
    echo
    echo "    make build-sim-image"
    echo
    exit 1
fi

# ------------------------------------------------------------
# Export variables for CHIA
# ------------------------------------------------------------

export CHIA_PROJECT_ROOT
export THIS_MACHINE

echo "Environment configured."
echo

# ------------------------------------------------------------
# Start CHIA cluster
# ------------------------------------------------------------

echo "Starting CHIA cluster..."
echo

chia up "$PROJECT_ROOT/cluster.yaml"