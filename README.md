# CHIA — LLM-Driven Hardware Automation

CHIA consists of **two independent LLM-driven loops** — `uvm_loop/` (RTL verification) and `orfs_loop/` (RTL-to-GDS PPA optimization) — plus `rtl_to_gds/`, an orchestrator that chains them end to end (verified RTL from `uvm_loop` flows straight into `orfs_loop`, producing a final GDS). See `CLAUDE.md` for the full architecture notes; each subdirectory also has its own `README.md`.

---

## Getting Started on a New Machine

### Prerequisites

- Linux (the flows shell out to Verilator, Yosys, OpenROAD, KLayout inside Docker — these images are Linux-only), with **Docker** installed and the daemon running (your user needs to be able to run `docker` without `sudo`, or adjust the commands below).
- **Conda/Miniconda**, with a `chia_env` environment that provides:
  - the **`chia`** CLI/agent framework and **`ray`** (this is a separate dependency, not part of this repo — obtain it from wherever your team distributes it, then `conda activate chia_env` and confirm `chia --help` and `ray --version` both work before continuing)
  - Python packages the loops import directly: `cocotb`, `pyuvm`, `pytest`, `pyyaml`, `pydantic` (install anything missing with `pip install` inside `chia_env` as errors surface — the loops will fail fast and name the missing module)
- Enough disk: a single design's ORFS run can produce hundreds of MB of build artifacts under `orfs_runs/`; `generated/designs/` on the UVM side is much smaller.
- No GPU required.

### 1. Clone and get submodules

```bash
git clone https://github.com/noahwithoutark22/chia-hackathon.git
cd chia-hackathon
git submodule update --init orfs_loop/orfs-native-build
git -C orfs_loop/orfs-native-build apply ../orfs-native-build.patch   # restores local sky130hd LVS/CDL fixes
```

### 2. LLM provider credentials

Every LLM call goes through `opencode`, configured via two files **outside this repo** (per-machine, never commit these). Templates with placeholder keys are in `templates/` — see `templates/README.md` for the copy-and-edit steps:

- `~/.local/share/opencode/auth.json` (from `templates/opencode_auth.json.example`) — keys for opencode's built-in providers (`opencode`, `nvidia`, and other opencode-catalog providers like the free `opencode/big-pickle`, `opencode/mimo-v2.5-free` all pick up their key from here automatically by provider name).

- `~/.config/opencode/opencode.jsonc` (from `templates/opencode.jsonc.example`) — **extra NVIDIA models / extra quota buckets** (recommended — a single free-tier key rate-limits fast). Custom providers here do *not* pick up `auth.json` keys automatically; each needs its own key inlined in `options.apiKey`. Don't hand-edit this beyond an initial test — once the cluster is up, add providers with:
  ```bash
  uvm_loop/scripts/add_llm_provider.sh <base_url> <api_key> <model_name> [slug]
  ```
  This registers the provider, copies the file into every running opencode container (it isn't bind-mounted from the host, so a host-only edit never reaches a container), smoke-tests it live, and only adds it to the fallback list below on success.

- Both loops have a fallback-model list (`uvm_loop/config/llm_models.txt`, `orfs_loop/llm_fallback_models.txt`) tried in order when the current model rate-limits, errors, or times out. Comment out any model you've confirmed doesn't work for your account, and put your fastest/most reliable models first. `add_llm_provider.sh` maintains `uvm_loop/config/llm_models.txt` for you; `orfs_loop/llm_fallback_models.txt` still needs manual edits.

### 3. Run a loop

Each loop is self-contained with its own `cluster.yaml`, Docker image(s), and run commands — see `uvm_loop/README.md` and `orfs_loop/README.md` for full detail. Short version:

```bash
conda activate chia_env

# uvm_loop
cd uvm_loop
docker build -t chia-rtl-worker:local -f workers/rtl/Dockerfile .
make build-sim-image
./setup.sh                     # checks prereqs, picks LLM provider, brings the cluster up
python3 -m pipeline.run14 --design-config pipeline/designs/fifo.yaml
cd ..

# orfs_loop
cd orfs_loop
docker build -f Dockerfile.orfs-run -t chia-orfs-run:local .
export CHIA_ORFS_REPO=$(pwd)
chia up cluster.yaml -y
python3 orfs_loop.py --design-name riscv32i \
  --design-config-mk /root/OpenROAD-flow-scripts/flow/designs/sky130hd/riscv32i/config.mk \
  --reports-root /root/OpenROAD-flow-scripts/flow/reports/sky130hd/riscv32i/base \
  --max-iterations 6 --objective area --model opencode/big-pickle
cd ..
```

### 4. Run the combined RTL → GDS pipeline

```bash
conda activate chia_env
export CHIA_PROJECT_ROOT=$PWD/uvm_loop
export CHIA_ORFS_REPO=$PWD/orfs_loop        # or wherever orfs-native-build/ is checked out
chia up rtl_to_gds/cluster.yaml -y          # combined cluster — needed because both loops' containers must be up together

python3 rtl_to_gds/rtl_to_gds.py --design-config pipeline/designs/fifo.yaml --clock-period 10 \
  -- --max-iterations 3 --objective area --model opencode/big-pickle --stage-timeout-seconds 7200
```

See `rtl_to_gds/README.md` for the full flag reference (e.g. `--core-utilization` for tiny designs, `--skip-uvm` to reuse an existing verified result, `--prepare-only` to test the handoff without a cluster).

### Where things land

- `uvm_loop/generated/designs/<design>/` — generated testbench, verification plan, RTL-repair iterations, `rtl_verification/rtl_verification_state.json` (the gate `rtl_to_gds` checks before handing RTL to ORFS).
- `orfs_loop/orfs_runs/<id>/` (root-owned inside the container) — flow logs, `summary.json`, signoff logs, and `final.gds` once closed.
- `rtl_to_gds`'s combined run additionally writes `rtl_to_gds.json` linking the final GDS back to the exact verified RTL snapshot it came from.

---

## 1. LLM-Driven RTL Verification Loop

The verification loop first generates the **verification infrastructure from the specification and reference model**. The generated environment is then used to verify the RTL. Verification failures can be used to guide **RTL modification**, followed by another verification cycle.

```text
        Specification
              │
        Reference Model
              │
              ▼
         CHIA + LLM
              │
              ▼
   Generate Verification
       Infrastructure
              │
              ▼
      Cocotb + PyUVM
       Verification TB
              │
              ▼
          Verify RTL
              │
        ┌─────┴─────┐
        │           │
      PASS        FAIL
        │           │
        ▼           ▼
 Verification   Analyze Failure
   Complete          │
                     ▼
                Modify RTL
                     │
                     └──────────► Verify RTL
```

### Key capabilities

* Specification and reference-model-driven verification generation
* Automatic Cocotb + PyUVM infrastructure generation
* Reference-model-based scoreboarding
* Directed and randomized testing
* Functional coverage
* Assertions and corner-case checking
* Automatic regression
* Verification failure analysis
* RTL modification and re-verification
* Distributed execution through CHIA/Ray

### Objective

Enable **RTL-independent verification infrastructure generation**, so that the verification environment can be created before the final RTL is available and subsequently used to validate and iteratively improve the RTL.

---

## 2. LLM-Driven RTL-to-GDS Optimization Loop

The second loop independently focuses on **physical implementation and PPA optimization**. It repeatedly runs ORFS, analyzes implementation results, and uses the LLM to propose constrained changes to physical-design parameters.

```text
          RTL
           │
           ▼
      ORFS Flow
           │
           ▼
    PPA / Timing /
       DRC Results
           │
           ▼
       CHIA + LLM
           │
           ▼
  Optimize Flow Parameters
           │
           ▼
       Next ORFS Run
           │
           └──────────────► Repeat
                              │
                              ▼
                     Closure / Best GDS
```

The CHIA driver controls execution while the LLM proposes changes to a predefined, constrained set of tunable parameters.

### Key capabilities

* LLM-guided PPA optimization
* Timing and area optimization
* Constrained/whitelisted tunables
* Hard parameter locking
* Parallel implementation experiments
* Optimization-effect tracking
* Stall diagnosis
* DRC/LVS signoff
* GDS generation and reporting
* Ray-based distributed execution
* Docker-based ORFS environment

---

## Future Integration

The two loops remain **independent during development**:

```text
┌─────────────────────────────────┐
│     RTL VERIFICATION LOOP       │
│                                 │
│ Spec + Reference Model          │
│          ↓                      │
│ Verification Infrastructure     │
│          ↓                      │
│       RTL Verification          │
│          ↓                      │
│   RTL Modification ↺            │
└───────────────┬─────────────────┘
                │
                │ Future Interface
                │
┌───────────────▼─────────────────┐
│      RTL-to-GDS LOOP            │
│                                 │
│          RTL                    │
│          ↓                      │
│        ORFS                     │
│          ↓                      │
│   PPA / Timing / DRC            │
│          ↓                      │
│   LLM Optimization ↺            │
│          ↓                      │
│        Best GDS                 │
└─────────────────────────────────┘
```

The final objective is to interface the two loops so that a **verified RTL can enter the physical-design optimization loop**, while implementation feedback can eventually be incorporated into the broader hardware development process.

**Status:** Active development
