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
