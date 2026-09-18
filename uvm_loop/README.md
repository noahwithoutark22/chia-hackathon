# CHIA — Cocotb + pyUVM Verification Pipeline

This is an automated hardware verification pipeline. Give it an RTL design, its specification, and a Python reference model this loop builds, runs, and iteratively improves a Cocotb + pyUVM verification environment around it, using Verilator as the simulator.

```bash
python3 -m pipeline.run14 --design-config pipeline/designs/<design>.yaml
```

That single command takes a design from "just RTL" to a working, checked verification environment.

---

## How It Works

The loop takes three inputs per design:

| Input | Description |
|---|---|
| **RTL** | The SystemVerilog implementation to be verified |
| **Specification** | A description of the design's *intended* behavior |
| **Reference model** | A Python model of the expected behavior |

From these, the pipeline generates a verification plan, builds a Cocotb + pyUVM testbench, runs it against the RTL under Verilator, checks results against the reference model, and — when weaknesses are found — iterates to improve the verification environment.

All generated files live under `generated/designs/<design>/`, kept separate from the original benchmark inputs.

---

## Repository Structure

```text
uvm_loop/
├── benchmarks/          # RTL designs used as verification benchmarks
│   └── <design>/
│       ├── <design>.sv
│       ├── spec.md
│       └── ref_model.py
├── examples/             # Small example designs (e.g. adder)
├── pipeline/
│   ├── run14.py          # Main verification orchestrator
│   ├── functions.py      # Pipeline operations
│   ├── tb_feedback.py     # Testbench diagnosis/repair support
│   ├── verification_improvement.py
│   └── designs/           # YAML config per benchmark
├── src/                   # Core generation and planning logic
├── uvm_generator/         # Verification environment generation
├── workers/
│   ├── rtl/               # RTL processing worker
│   ├── llm/               # Model / OpenCode worker
│   └── sim/               # Simulation worker
├── templates/             # Templates for generated verification files
├── generated/              # All generated benchmark artifacts
├── cluster.yaml            # CHIA/Ray cluster configuration
├── setup.sh                 # Environment and cluster setup
└── Makefile                  # Common build/run commands
```

You'll typically only touch: `benchmarks/`, `pipeline/designs/`, `setup.sh`, `cluster.yaml`, and `pipeline/run14.py`. Everything else is pipeline internals.

---

## Prerequisites

- A Linux environment (recommended)
- Docker
- CHIA
- SSH access between the cluster host and CHIA workers

All simulation and verification tools run inside Docker workers — no need to install Verilator or the pipeline's Python dependencies on the host.

Verify your setup:

```bash
docker --version
chia --help
```

Make sure your CHIA conda environment is active, e.g.:

```bash
conda activate chia_env
```

---

## Quickstart

### 1. Clone and enter the repository

```bash
git clone <repository-url>
cd uvm_loop
conda activate chia_env
```

### 2. Build the Docker workers

```bash
docker build -t chia-rtl-worker:local -f workers/rtl/chia.Dockerfile .
make build-sim-image
```

This produces `chia-rtl-worker:local` and `chia-sim-worker:chia-local`. Verify with:

```bash
docker images | grep chia
```

*(The LLM/OpenCode worker image is pulled automatically per `cluster.yaml`.)*

### 3. Configure the cluster

Open `cluster.yaml` and check:

```yaml
auth:
    ssh_user: ${USER}
    ssh_private_key: ~/.ssh/<ssh_key_name>
```

Set `<ssh_key_name>` to the SSH key you use on your system.

If you're using the OpenCode worker, confirm its auth-file mount points to your actual OpenCode credentials:

```yaml
-v ${HOME}/snap/code/259/.local/share/opencode/auth.json:/home/ray/.local/share/opencode/auth.json:ro
```

Update the host-side path if your credentials live elsewhere.

### 4. Start the cluster

```bash
./setup.sh
```

`setup.sh` verifies CHIA, Docker, the Docker daemon, `cluster.yaml`, and both worker images before proceeding, then prompts you to choose an LLM provider:

```text
Select LLM provider:
  1) OpenCode
  2) Google Gemini
```

**Recommended: OpenCode**, model `opencode/big-pickle` — long verification runs make many model requests, and a provider with generous usage limits keeps a run from stalling partway through.

If you choose Gemini instead, export your key first:

```bash
export GOOGLE_GENERATIVE_AI_API_KEY="your-api-key"
```

`setup.sh` finishes by bringing the cluster up via `chia up cluster.yaml`.

### 5. Confirm the cluster is running

```bash
chia status
ray status
```

You should see workers for RTL processing, model/OpenCode operations, simulation, and Verilator.

### 6. Run a benchmark

Several benchmarks ship with the repo: `axi_handshake`, `fifo`, `adder2`, `aes_benchmark`, `i2c_benchmark`, `hamming_encoder`.

```bash
python3 -m pipeline.run14 --design-config pipeline/designs/fifo.yaml
# or
make pipeline BENCHMARK=fifo
```

---

## Verifying Your Own RTL

**The one-command path** (spec + reference model + RTL -> UVM verification
-> place-and-route -> signed-off GDS): see `scripts/run_full_flow.sh` at the
repo root. It does everything below (benchmark directory, design YAML) plus
runs the whole `rtl_to_gds.py` flow under the model-fallback supervisor:

```bash
scripts/run_full_flow.sh my_fifo path/to/my_fifo.sv path/to/spec.md path/to/ref_model.py
```

The steps below are what it automates, useful if you want to run only the
UVM stage, or need more control than the script's env-var overrides give.

**1. Create a benchmark directory:**

```text
benchmarks/my_fifo/
├── my_fifo.sv     # SystemVerilog RTL
├── spec.md        # Intended behavior — not what the current RTL happens to do
└── ref_model.py   # Python reference implementation of expected behavior
```

`spec.md` should cover: inputs/outputs, signal widths, reset and clock behavior, valid/ready handshakes, expected outputs, corner cases, and any timing/protocol requirements.

**2. Add a config YAML** at `pipeline/designs/my_fifo.yaml`:

```yaml
name: my_fifo
rtl: benchmarks/my_fifo/my_fifo.sv
spec: benchmarks/my_fifo/spec.md
ref_model: benchmarks/my_fifo/ref_model.py
output_parent: generated/designs
```

Paths are relative to the repository root.

**3. Run it:**

```bash
python3 -m pipeline.run14 --design-config pipeline/designs/my_fifo.yaml
```

Generated files land in `generated/designs/my_fifo/`, including:

```text
generated/designs/my_fifo/
├── rtl/rtl_info.json
├── plans/
│   ├── candidate_verification_plan.yaml
│   └── verification_plan.yaml
├── tb/
│   ├── driver.py
│   ├── monitor.py
│   ├── sequences.py
│   ├── test.py
│   ├── env.py
│   ├── agent.py
│   └── scoreboard.py
├── results/verification_improvement/
├── tb_iterations/
└── checkpoints/
```

> **Note:** Re-running the same command doesn't start from scratch — the loop resumes from any valid artifacts already produced in `generated/designs/<design>/`. This makes it safe to re-run after an interruption.

---

## Long-Running Verification

For extended runs, use the built-in supervisor instead of calling `run14` directly:

```bash
./run_forever.sh pipeline/designs/fifo.yaml 25
```

The second argument caps the number of verification-improvement iterations. The supervisor starts `run14`, logs output, restarts on unexpected failure, preserves generated state between attempts, and stops automatically once `run14` exits successfully (or on `Ctrl+C`).

Logs: `generated/designs/<design>/results/verification_improvement/logs/`

---

## Multi-Model LLM Fallback

Long verification runs make hundreds of LLM calls. A single free-tier
provider — `opencode/big-pickle` in particular — is a **shared pool across
every free-tier opencode-zen-gateway user**, not a private per-account
quota. That means a manual one-off prompt in your terminal can succeed at
the exact same time a pipeline run gets `429 Too Many Requests`: the
pipeline is making far more concurrent, back-to-back requests than a single
interactive test, so it's much more likely to land when the shared pool is
saturated. To keep a run from stalling for good on one rate limit, `run14`
picks its model from an ordered fallback list instead of a single
hard-coded provider.

**How it works:**

| File | Role |
|---|---|
| `config/llm_models.txt` | Ordered list of `provider/model` candidates, one per line. `#`-comments document why any model is excluded (hangs, 404s, etc.). |
| `generated/llm_model_state.json` | Persisted state: `"current"` (the model in use) and `"cooldown_until"` (a per-model UNIX timestamp map). Safe to hand-edit — delete `"current"` or clear an entry's cooldown to force a re-pick. |
| `generated/llm_model_usage.jsonl` | Append-only log of every model selection, for auditing which model produced which run. |

On each `run14` startup, `_load_llm_model()` (`pipeline/run14.py`) picks
`state["current"]` if it isn't in cooldown, otherwise the first candidate
in `llm_models.txt` that isn't cooled down. On a rate limit or provider
error, the current model's cooldown is set (`LLM_RATE_LIMIT_COOLDOWN_S`,
default 1 hour) and the process exits non-zero.

**This is why fallback only actually engages under the supervisor.** A
bare `python3 -m pipeline.run14` process reads the model once at startup
and keeps it for its whole lifetime — a rate limit just kills the run. The
supervisor (`./run_forever.sh`, or `rtl_to_gds.py --uvm-supervised N`)
restarts on non-zero exit, and each restart re-reads the state file, which
is the only point a different model actually gets picked. ORFS's
`orfs_loop.py` takes a simpler, single-shot `--model` flag instead — it
doesn't share this fallback mechanism.

**Adding a new model/key:**

```bash
uvm_loop/scripts/add_llm_provider.sh <base_url> <api_key> <model_name> [slug]
```

Does all 4 steps below in one shot: picks the next free `nvidiaN` slot (or
use `slug` to name it explicitly), registers it in `opencode.jsonc`, syncs
it to every running opencode container, smoke-tests it live, and only adds
it to `config/llm_models.txt` if the smoke test passes. This exists because
doing this by hand across 3 files (host config + 2 containers) is exactly
the kind of thing that's easy to get subtly wrong under time pressure —
wrong slot number, a container missed, or an untested model landing
straight in the live fallback list.

The manual steps it automates, if you need to do one by hand:

1. Register it as a custom `opencode` provider in
   `~/.config/opencode/opencode.jsonc`:
   ```jsonc
   "nvidiaN": {
     "npm": "@ai-sdk/openai-compatible",
     "options": {
       "baseURL": "https://integrate.api.nvidia.com/v1",
       "apiKey": "nvapi-..."
     },
     "models": { "<vendor>/<model-name>": {} }
   }
   ```
   (`options.apiKey` is required for a *custom* provider — `auth.json`'s
   per-provider key injection only applies to opencode's built-in provider
   IDs like `"nvidia"`, not ones you add yourself.)
2. Copy the updated config into every opencode worker container — this
   path is **not** bind-mounted from the host (unlike `auth.json`), so
   edits need to be pushed explicitly:
   ```bash
   docker cp ~/.config/opencode/opencode.jsonc <container>:/home/ray/.config/opencode/opencode.jsonc
   ```
   Redo this if a container is ever recreated.
3. Smoke-test before trusting it in an unattended run:
   ```bash
   docker exec <container> opencode run -m nvidiaN/<vendor>/<model-name> "reply with exactly: PONG"
   ```
   Give it a generous timeout (60-90s) — some models are slow on a cold
   first call but fine afterward; don't exclude on a single timeout, retry
   once. Only exclude a model that hangs or errors *repeatedly*.
4. Add the verified `provider/model` line to `config/llm_models.txt`, with
   a comment noting when/how it was verified. Excluded candidates stay in
   `opencode.jsonc` (commented out of the fallback list, not deleted) so
   they can be re-tested later without re-registering.

Current pool composition and exclusions are documented in the comment
block at the top of `config/llm_models.txt`.

---

## Command Reference

| Task | Command |
|---|---|
| Run a benchmark | `python3 -m pipeline.run14 --design-config pipeline/designs/<design>.yaml` |
| Run via Make | `make pipeline BENCHMARK=<design>` |
| Run the supervisor | `./run_forever.sh pipeline/designs/<design>.yaml 25` |
| Build the sim image | `make build-sim-image` |
| Build the RTL worker | `docker build -t chia-rtl-worker:local -f workers/rtl/chia.Dockerfile .` |
| Check Docker images | `docker images \| grep chia` |
| Check the CHIA cluster | `chia status` |
| Check Ray | `ray status` |

---

## Troubleshooting

**`chia: command not found`**
Activate the CHIA conda environment: `conda activate chia_env`, then re-check with `chia --help`.

**Docker isn't accessible**
Run `docker info`. If the daemon isn't running, start it. If you get a permissions error, add your user to the Docker group.

**`chia-rtl-worker:local` or `chia-sim-worker:chia-local` not found**
Rebuild the missing image (see Command Reference above).

**Cluster workers can't connect**
Check `chia status` and `ray status`, then verify SSH access, the `ssh_private_key` path in `cluster.yaml`, Docker availability on the worker, and that both worker images exist. If your machine's IP changed, restart/reconcile the cluster so `THIS_MACHINE` updates.

**OpenCode authentication problems**
Confirm the host-side path in the `auth.json` volume mount in `cluster.yaml` points to your actual OpenCode credentials file.

**A long run stops unexpectedly**
Check the latest log under `generated/designs/<design>/results/verification_improvement/logs/`. Consider switching to `run_forever.sh` for automatic recovery.

---

## Summary Workflow

```bash
git clone <repository-url> && cd uvm_loop
conda activate chia_env

docker build -t chia-rtl-worker:local -f workers/rtl/chia.Dockerfile .
make build-sim-image

# Edit cluster.yaml: SSH key + OpenCode auth path
./setup.sh          # choose OpenCode -> opencode/big-pickle

python3 -m pipeline.run14 --design-config pipeline/designs/fifo.yaml
```

To verify your own design: create `benchmarks/<design>/` (RTL + spec + ref model) → add `pipeline/designs/<design>.yaml` → run `pipeline.run14` against it → check `generated/designs/<design>/` for results.
