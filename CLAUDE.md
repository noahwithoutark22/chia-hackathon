# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

CHIA hackathon monorepo holding **two independent LLM-driven hardware loops**, both built on the `chia` agent framework (Ray cluster of Docker workers, remote calls via `@ChiaFunction(resources={...})`, LLM via `chia.models.opencode.OpenCodeLLM`). They share no code and are not yet interfaced; treat each subdirectory as its own project with its own `cluster.yaml`, and run commands from inside that subdirectory.

- `uvm_loop/` — spec + reference model → generated Cocotb/pyUVM testbench → Verilator simulation → iterative TB/RTL improvement.
- `orfs_loop/` — LLM tunes whitelisted OpenROAD-flow-scripts (ORFS) knobs until timing/DRC closure, then DRC/LVS signoff.

Both require `conda activate chia_env` (provides `chia`, `ray`) and a running cluster (`chia up cluster.yaml -y`; check with `chia status` / `ray status`).

## uvm_loop

```bash
cd uvm_loop
docker build -t chia-rtl-worker:local -f workers/rtl/Dockerfile .
make build-sim-image                                               # chia-sim-worker:chia-local
./setup.sh                                                         # checks prereqs, picks LLM provider, runs chia up
python3 -m pipeline.run14 --design-config benchmarks/fifo/design.yaml   # or: make pipeline BENCHMARK=fifo
./run_forever.sh benchmarks/fifo/design.yaml 25                     # supervisor: restarts run14 on failure, arg 2 = iteration cap
python3 -m pytest tests/                                           # single: python3 -m pytest tests/test_verilator_compat.py::test_comment_examples_are_ignored
```

pytest is not installed in the system Python (install it into `chia_env`); `python3 -m` puts `uvm_loop/` on `sys.path`, which the tests need. Likewise run the pipeline as a module (`python3 -m pipeline.run14`) from `uvm_loop/` — imports are `pipeline.*`, `src.*`, `uvm_generator.*` and design YAML paths are repo-relative.

Architecture:
- `pipeline/run14.py` is the (very large, ~7k line) orchestrator and current entrypoint. Keep it the *only* orchestrator in `pipeline/`: dead `run14bak.py` / `run15.py` snapshots used to live beside it, and the in-loop LLM picked the highest-numbered file when improvising validators, silently checking its work against code that was never running. Use a branch or tag for checkpoints instead.
- Failure modes seen in unattended runs, with signatures and fixes, are in `docs/TROUBLESHOOTING.md` — check there before debugging a stalled or crash-looping run.
- Remote work is dispatched by Ray resource: `pipeline/functions.py` runs RTL extraction on `rtl_extract` workers and simulation on `sim_worker`; LLM calls go to `opencode_creds`/`opencode_tools`; `verilator_run` is another worker type (see `cluster.yaml`).
- `src/` holds RTL parsing, plan generation, and the `VerificationPlan` schema; `uvm_generator/` renders `templates/*.j2` and validates output (`verilator_compat.py` rejects SV constructs Verilator can't handle, e.g. parameterized virtual interfaces; `rules.yaml`/`capabilities.yaml` constrain generation).
- `pipeline/verification_improvement.py`, `tb_feedback.py`, `llm_weakness_analyzer.py` drive the diagnose/repair/improve iterations.
- Per design, inputs live together in `benchmarks/<design>/`: `<design>.sv`, `spec.md`, `ref_model.py` and `design.yaml` (copy `benchmarks/TEMPLATE.yaml` for a new one). `rtl_to_gds.py --design-config` accepts a path, a directory name, or a design `name:`. All outputs go to `generated/designs/<design>/`; re-running **resumes** from valid artifacts there (including `improvement_state.json`), so delete that directory for a clean run (`make clean` wipes all designs).
- `spec.md` must describe *intended* behavior, not what the current RTL does — the loop may modify RTL based on mismatches.

## orfs_loop

```bash
cd orfs_loop
docker build -f Dockerfile.orfs-run -t chia-orfs-run:local .
export CHIA_ORFS_REPO=$(pwd)          # cluster.yaml bind mounts key off this
chia up cluster.yaml -y
python3 orfs_gui.py                   # dashboard at http://127.0.0.1:8080
python3 orfs_loop.py --design-name riscv32i \
  --design-config-mk /root/OpenROAD-flow-scripts/flow/designs/sky130hd/riscv32i/config.mk \
  --reports-root /root/OpenROAD-flow-scripts/flow/reports/sky130hd/riscv32i/base \
  --max-iterations 6 --objective area --model opencode/big-pickle [--batch-size 6] [--lock KEY=VALUE]
```

No test suite. `orfs_loop/README.md` is detailed and authoritative for flags, outputs, and troubleshooting.

`orfs-native-build/` is a submodule (ORFS checkout) registered at the repo root as `orfs_loop/orfs-native-build`: `git submodule update --init orfs_loop/orfs-native-build`, then `git -C orfs_loop/orfs-native-build apply ../orfs-native-build.patch` to restore the local sky130hd LVS/CDL fixes, which are not in the submodule pin or the Docker image.

Architecture (the non-obvious parts):
- `orfs_loop.py` (host) owns the entire loop and makes direct blocking Ray calls into `orfs_tool.py` functions on `orfs_run` workers (`run_flow_remote`, `apply_tunables_remote`, `read_tunables_remote`, `run_signoff_remote`). The LLM has **no tools**: each turn it replies with a fenced JSON tunable diff or `CLOSURE: PASS` / `CLOSURE: GIVE_UP`, parsed by the driver. This replaced an MCP-tool design that broke on client timeouts causing concurrent `make clean_all` corruption — don't reintroduce LLM tool-calling for flow runs. `ORFSTool` in `orfs_tool.py` is dead code from that design.
- Two-level loop: **iterations** (iteration 1 ends at first closure; each later one must close and beat the prior `--objective` value) contain uncapped **runs** (one flow + one LLM turn). With `--batch-size N`, each slot gets its own `FLOW_VARIANT` (`slotN`) and `config.chia.slotN.mk`, which is what keeps concurrent runs from sharing paths; width is capped by `hello_orfs.num_workers` in `cluster.yaml`.
- Tunables are a closed whitelist in `orfs_tunables_schema.json` (`_minimal.json` via `--minimal-schema`). `orfs_config_bridge.py` validates and writes a managed block into a *copy* (`config.chia.mk`); the baseline `config.mk` is never edited. `--lock` is enforced in code in `apply_tunables_remote`, not by the prompt. `CLOCK_PERIOD` is special: it patches a working copy of the design's `constraint.sdc` and repoints `SDC_FILE`.
- `orfs_ledger.py` records each knob change's measured effect across runs/slots and feeds it into prompts; multi-knob moves are quarantined as "combined" and `CLOCK_PERIOD` moves flagged.
- Prompts in `prompts/`: `orfs_propose.md` (per-slot proposal), `orfs_referee.md` (cross-slot note per round), `orfs_diagnose.md` (after 3 non-improving runs).
- Every flow run does `make clean_all` first, because ORFS make targets don't track `DESIGN_CONFIG` contents; a run finishing in seconds means something is wrong.
- Paths passed to `orfs_loop.py` must be **container-native** (`/root/OpenROAD-flow-scripts/...`, `/root/chia-orfs/...`), since work executes inside the worker. The repo is bind-mounted at `/root/chia-orfs` with `PYTHONPATH` set, so edits to `orfs_tool.py`/`orfs_config_bridge.py` are live without rebuilding.
- On sky130hd, the authoritative LVS verdict is `result["lvs_verdict"]` (netgen via `lvs/sky130hd_netgen_setup.tcl`), not KLayout's `result["lvs"]["clean"]`. Benign fold exceptions are gated by exact signature in `KNOWN_NETGEN_FOLD_EXCEPTIONS` in `orfs_tool.py`.
- Run artifacts land in `orfs_runs/<id>/` (root-owned; delete via `docker exec chia-orfs-$USER-0 rm -rf ...`). `.gitignore` ignores all runs except the `bp-sky-gcd` sample.

## rtl_to_gds (integration)

`rtl_to_gds/rtl_to_gds.py` chains the loops: it runs `pipeline.run14`, gates on `rtl_verification/rtl_verification_state.json`, writes an ORFS design from the accepted RTL snapshot into `$CHIA_ORFS_REPO/rtl_to_gds_designs/` (not `orfs-native-build/flow/designs`, which is root-owned), then runs `orfs_loop.py`. It requires the combined `rtl_to_gds/cluster.yaml`, because the per-loop cluster files share container names but use different mounts. Test the handoff without a cluster: `--skip-uvm --skip-preflight --prepare-only`. See `rtl_to_gds/README.md`.

## orfs_loop is a mirror

`orfs_loop/` is a sanitized copy of a separate private working repo (`~/Desktop/chia-orfs`). Code, prompts, schemas, and the sample run should stay byte-identical to it; intentionally excluded are `CLAUDE.md`, `SETUP.md`, `start_gui.sh` (and README references to them), full run history, and the vendored submodule contents (replaced by `orfs-native-build.patch`).
