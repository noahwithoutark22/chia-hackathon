#!/usr/bin/env bash
set -euo pipefail
# Build the DPI bridge for the generated environment. Run from the generated TB directory.
python3-config --embed --cflags >/dev/null
cxxflags=$(python3-config --embed --cflags)
ldflags=$(python3-config --embed --ldflags)
g++ -std=c++17 -fPIC -shared $cxxflags ref_model_adapter.cpp $ldflags -o libchia_ref_model.so
echo "Built libchia_ref_model.so"
