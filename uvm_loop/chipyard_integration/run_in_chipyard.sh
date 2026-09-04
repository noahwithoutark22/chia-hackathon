#!/usr/bin/env bash
# Drop the generated UVM testbench into a Chipyard checkout and run it
# through Chipyard's Verilator flow.
#
# Usage: ./chipyard_integration/run_in_chipyard.sh <chipyard_dir> <config> [top_module]
set -euo pipefail

CHIPYARD_DIR="${1:?usage: run_in_chipyard.sh <chipyard_dir> <config> [top_module]}"
CONFIG="${2:?usage: run_in_chipyard.sh <chipyard_dir> <config> [top_module]}"
TOP="${3:-}"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GEN_TB_DIR="${PROJECT_DIR}/generated_tb"

if [ ! -d "${GEN_TB_DIR}" ]; then
  echo "No generated_tb/ found — run scripts/generate_tb.py first." >&2
  exit 1
fi

if [ -z "${TOP}" ]; then
  # Infer top module name from filelist.f's *_tb_top.sv entry.
  TOP=$(grep '_tb_top\.sv' "${GEN_TB_DIR}/filelist.f" | sed 's/_tb_top\.sv//')
fi

DEST="${CHIPYARD_DIR}/sims/verilator/generated-tb/${TOP}"
mkdir -p "${DEST}"
cp "${GEN_TB_DIR}"/*.sv "${DEST}/"
cp "${GEN_TB_DIR}/filelist.f" "${DEST}/"

echo "Copied generated TB for '${TOP}' into ${DEST}"
echo "Running Chipyard's Verilator flow for CONFIG=${CONFIG} ..."

(
  cd "${CHIPYARD_DIR}/sims/verilator"
  # Extend the build's file list with the generated UVM sources. Chipyard's
  # Makefile picks up extra sources via EXTRA_SIM_SOURCES; adjust here if
  # your Chipyard version names this variable differently.
  make CONFIG="${CONFIG}" EXTRA_SIM_SOURCES="$(cat "${DEST}/filelist.f" | sed "s|^|${DEST}/|" | tr '\n' ' ')"
)

echo "Chipyard run complete."
