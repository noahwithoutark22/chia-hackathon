# LLM-Driven UVM Testbench Generator (Chipyard-integrated, Dockerized + Ray cluster)

Pipeline: RTL + spec + reference model -> Claude -> verification_plan.yaml
-> Jinja2 UVM templates -> generated UVM testbench (.sv) -> optional
Chipyard/Verilator run.

## Quick start (local, no Docker)

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # fill in ANTHROPIC_API_KEY
    export $(grep -v '^#' .env | xargs)
    python -m pipeline.run14 --design-config pipeline/designs/adder.yaml
    find generated/designs/adder -maxdepth 2 -type f | sort

## Quick start (Docker)

    docker build -t llm-uvm-tb-generator:latest .
    docker run --rm -it --env-file .env \
      -v "$PWD:/opt/llm-uvm-tb-generator" \
      llm-uvm-tb-generator:latest \
      "python3 -m pipeline.run14 --design-config pipeline/designs/adder.yaml"

## Ray cluster (Chipyard-integrated Verilator runs)

1. Build the image above so it's available locally (or push it to a
   registry your cluster nodes can pull from).
2. Edit `cluster.yaml`: set `${THIS_MACHINE}`, `${USER}`, your SSH key
   name, and the `--env-file` / chipyard checkout `-v` mount paths under
   the `llm_uvm_tb` node type.
3. Bring the cluster up and submit the job:

       ray up cluster.yaml
       ray job submit --address http://<head_ip>:8265 --working-dir . \
         -- python ray_pipeline_job.py \
              --design-config pipeline/designs/adder2.yaml

   `ray_pipeline_job.py` schedules Stage 1 and Stage 2 on the
   `llm_uvm_tb_gen` custom resource, and (if `--chipyard-dir` is given)
   the Chipyard/Verilator run on `verilator_run` — matching the
   `hello_verilator` pattern in cluster.yaml.

## Project layout

    llm-uvm-tb-generator/
    ├── Dockerfile              # layers this pipeline on chia-verilator-run
    ├── cluster.yaml            # Ray cluster config (hello_verilator + llm_uvm_tb)
    ├── ray_pipeline_job.py     # Ray job: schedules Stage 1/2 (+ Chipyard run)
    ├── config/config.yaml      # LLM + path settings
    ├── src/
    │   ├── rtl_parser.py       # lightweight RTL port/param extraction
    │   ├── llm_client.py       # Anthropic API wrapper
    │   ├── schema.py           # pydantic schema for verification_plan.yaml
    │   ├── plan_generator.py   # Stage 1: RTL+spec+ref -> plan
    │   └── tb_generator.py     # Stage 2: plan -> UVM .sv files
    ├── templates/*.j2          # Jinja2 UVM templates
    ├── examples/adder/         # sample RTL + spec + ref model
    ├── chipyard_integration/   # run_in_chipyard.sh
    ├── scripts/                # CLI entry points + pipeline runner
    └── Makefile                # local Verilator smoke-test build/run

## Customizing

- **Templates** (`templates/*.j2`): edit to match your house UVM style,
  add coverage, hook the scoreboard's `predict_expected()` up to a real
  DPI-C reference model.
- **Schema** (`src/schema.py`): the contract between the LLM and the
  templates — extend together with the prompt in `src/plan_generator.py`.
- **Model**: set `LLM_MODEL` in `.env`.
- **Multi-benchmark output isolation**: set `output_parent` in each benchmark YAML.
  The pipeline creates `<output_parent>/<benchmark>/` and keeps all generated
  artifacts for that benchmark inside it, including the TB, simulation builds,
  reports, checkpoints, and LLM workspaces.

## Multi-benchmark output layout

Every benchmark has an isolated generated root. For example, with
`output_parent: generated/designs`:

```text
generated/designs/adder/
generated/designs/adder2/
generated/designs/fifo/
```

Inside each benchmark root, all generated state stays together: RTL extraction,
verification plans, the `tb/` environment, simulator `.chia_sim/` data, results,
checkpoints, LLM diagnosis/repair workspaces, improvement workspaces, and iteration
snapshots. The simulator loads that benchmark's `tb/test_top.py` directly, so the
benchmark directory name and chosen parent path do not affect Python imports.
Changing `output_parent` in a benchmark YAML moves that benchmark's entire generated
tree to `<output_parent>/<benchmark>/`.

Run a benchmark with:

```bash
python3 -m pipeline.run14 --design-config pipeline/designs/adder2.yaml
python3 -m pipeline.run14 --design-config pipeline/designs/fifo.yaml
```

## Stage 5+ RTL-blind verification improvement

After Stage 4, the generated Cocotb/PyUVM environment can be iteratively
improved without exposing RTL to the improvement LLM. Run:

```bash
python3 pipeline/run_stage5_plus.py --design-config pipeline/designs/adder2.yaml
```

The simulator sees RTL and emits structured evidence. The LLM sees only the
specification, reference model, verification plan, current TB, and a
verification-weakness report. Candidate TB edits are regression-tested and
rolled back if they reduce the objective quality score or increase failed
tests. See `docs_verification_improvement.md` for the stage-by-stage design.

## Gemini LLM mode

The active `run14.py` pipeline now resolves the LLM model from `LLM_MODEL` instead of hard-coding `opencode/big-pickle`. The default is Google Gemini through OpenCode's native Google provider, which preserves the existing CHIA/OpenCode tool-calling and workspace behavior.

Set the Gemini API key on the host before starting CHIA:

```bash
export GOOGLE_GENERATIVE_AI_API_KEY="your-gemini-api-key"
export LLM_MODEL="google/gemini-2.5-flash"
./setup.sh
```

To use the previous OpenCode model instead:

```bash
export LLM_MODEL="opencode/big-pickle"
./setup.sh
```

The Gemini key is passed to the `hello_opencode` CHIA worker through the environment and is not stored in the repository.
