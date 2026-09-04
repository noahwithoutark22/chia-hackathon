TOP ?= adder_tb_top
GEN_TB_DIR := generated_tb
EXAMPLE_RTL := examples/adder/adder.sv
BUILD_DIR := build

.PHONY: pipeline sim clean build-sim-image sim-generated

pipeline:
	./scripts/run_pipeline.sh

# Quick structural smoke-test with plain Verilator.
# This target is intentionally separate from the full UVM worker flow.
sim:
	mkdir -p $(BUILD_DIR)
	verilator --binary -j 0 \
		-I$(GEN_TB_DIR) \
		--top-module $(TOP) \
		$(EXAMPLE_RTL) \
		$(GEN_TB_DIR)/*.sv \
		-Mdir $(BUILD_DIR) \
		--Wno-fatal
	./$(BUILD_DIR)/V$(TOP)

clean:
	rm -rf $(BUILD_DIR) generated_plans generated_tb generated/results
	mkdir -p generated_plans generated_tb generated/results

# Build the Ray/CHIA-based simulation worker image.
build-sim-image:
	docker build -f workers/sim/chia.Dockerfile -t chia-sim-worker:chia-local .

# Run the standalone UVM/Verilator simulation worker.
#
# IMPORTANT:
# chia-sim-worker:chia-local already has run.py as its ENTRYPOINT,
# so docker run must receive only run.py's command-line arguments.
sim-generated:
	mkdir -p generated/results
	docker run --rm \
		-v "$(PWD):/workspace" \
		chia-sim-worker:chia-local \
		--rtl /workspace/examples/adder/adder.sv \
		--tb /workspace/generated_tb \
		--output /workspace/generated/results/simulation_result.json \
		--test-timeout 60 \
		--build-timeout 1800