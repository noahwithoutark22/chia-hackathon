# rtl_to_gds — UVM verification → ORFS closure

`rtl_to_gds.py` chains the two loops into one run:

1. **UVM stage.** Runs `uvm_loop`'s `pipeline.run14` on a design YAML. The loop builds a testbench and repairs the RTL until it is verified.
2. **Handoff.** Reads `generated/designs/<design>/rtl_verification/rtl_verification_state.json`. Only RTL marked `verified` (or `complete` with `rtl_outcome: no_repair`) is passed on, unless you give `--allow-unverified`. The RTL passed on is the accepted snapshot in `rtl_verification/accepted/`, never the original benchmark file.
3. **ORFS onboarding.** Writes `config.mk`, `constraint.sdc`, the RTL and `rtl_handoff.json` (provenance, including the RTL's md5) to `$CHIA_ORFS_REPO/rtl_to_gds_designs/<platform>/chia_<design>/`. The top module and clock port come from the UVM loop's `rtl_info.json`. Designs with no clock get a virtual-clock SDC. `.sv` files are synthesized with the slang frontend.
4. **ORFS stage.** Runs `orfs_loop.py` on that design. The final GDS is written to `orfs_runs/chia_<design>-<ts>/final.gds`, along with `rtl_to_gds.json`, a record linking the GDS back to the verified RTL.
5. **Log collection.** Once the run finishes (success, failure, or `--prepare-only`), every log/report/state file it produced -- UVM (`generated/designs/<design>/`: `rtl_verification/`, `results/`, `checkpoints/*.done`) and ORFS (`orfs_runs/<run>/`: `flow_logs/`, `signoff_logs/`, `reports/`, `summary.json`) -- is copied into one `logs/` directory, alongside a `console.log` teeing this run's entire stdout/stderr (both stages, not just this script's own `log()` lines) and a `manifest.json` listing what was collected from where. Originals are left in place; this is a convenience copy, not a move. Disable with `--no-logs-collect`; override the destination with `--logs-dir`.

## Cluster

Both stages need their workers up at the same time, so use the combined `cluster.yaml` in this directory:

```bash
conda activate chia_env
export CHIA_PROJECT_ROOT=$PWD/uvm_loop
export CHIA_ORFS_REPO=$PWD/orfs_loop      # or wherever orfs-native-build/ is checked out
chia down <old cluster.yaml> -y           # whichever per-loop cluster is running
docker rm -f chia-opencode-$USER-0 chia-rtl-$USER-0 chia-sim-$USER-0   # once: old mounts
chia up rtl_to_gds/cluster.yaml -y
```

Before starting any work, the script checks that the needed Ray resources exist and that each container mounts the directories this run uses.

## Run

```bash
python3 rtl_to_gds/rtl_to_gds.py --design-config pipeline/designs/fifo.yaml --clock-period 10 \
    -- --max-iterations 3 --objective area --model opencode/big-pickle --stage-timeout-seconds 7200
```

Arguments after `--` are passed straight to `orfs_loop.py`.

| Flag | Purpose |
|---|---|
| `--skip-uvm` | Use an existing verified result instead of re-running the UVM loop |
| `--uvm-supervised N` | Run the UVM stage under `run_forever.sh` (auto-restart, N improvement iterations) |
| `--allow-unverified` | Send unverified RTL to ORFS anyway |
| `--prepare-only` | Stop after writing the ORFS design and print the `orfs_loop.py` command |
| `--top`, `--clock-port` (`none` = combinational) | Override auto-detection |
| `--clock-period` | Starting period in the platform's SDC units (ns on sky130hd); the ORFS loop can tune it |
| `--core-utilization`, `--place-density` | Starting floorplan values (default 40 / 0.6) |
| `--synth-frontend auto\|slang\|yosys` | HDL reader for synthesis |
| `--orfs-repo` | ORFS repo the `orfs_run` workers mount (default `$CHIA_ORFS_REPO`, else `orfs_loop/`) |
| `--logs-dir` | Where to collect this run's logs (default: `<result-json's dir>/logs`, else `<orfs-repo>/orfs_runs/<design>-logs-<ts>`) |
| `--no-logs-collect` | Skip log collection and the console tee entirely |

**Tiny designs** (tens of cells, e.g. `hamming_encoder`) fail PDN at the default 40% utilization with `PDN-0185 Insufficient width`, because the die is narrower than the met4 strap pitch. Start them at `--core-utilization 10`.
