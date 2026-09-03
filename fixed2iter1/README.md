# LLM-Driven UVM Testbench Generator (Chipyard-integrated, Dockerized + Ray cluster)

Pipeline: RTL + spec + reference model -> Claude -> verification_plan.yaml
-> Jinja2 UVM templates -> generated UVM testbench (.sv) -> optional
Chipyard/Verilator run.

## Quick start (local, no Docker)

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # fill in ANTHROPIC_API_KEY
    export $(grep -v '^#' .env | xargs)
    ./scripts/run_pipeline.sh
    cat generated_plans/verification_plan.yaml
    ls generated_tb/

## Quick start (Docker)

    docker build -t llm-uvm-tb-generator:latest .
    docker run --rm -it --env-file .env \
      -v "$PWD/generated_plans:/opt/llm-uvm-tb-generator/generated_plans" \
      -v "$PWD/generated_tb:/opt/llm-uvm-tb-generator/generated_tb" \
      llm-uvm-tb-generator:latest \
      "./scripts/run_pipeline.sh"

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
              --rtl examples/adder/adder.v \
              --spec examples/adder/spec.md \
              --ref-model examples/adder/ref_model.py \
              --chipyard-dir /root/chipyard \
              --chipyard-config RocketConfig

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
