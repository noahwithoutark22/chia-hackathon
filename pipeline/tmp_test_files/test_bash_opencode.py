import ray

from chia.base.ChiaFunction import get
from chia.models.opencode import OpenCodeLLM
from chia.base.tools.BashTool import BashTool


if __name__ == "__main__":
    ray.init()

    bash = BashTool(
    "verification_workspace",
    work_dir="/workspace",
    timeout_seconds=120,
    task_options={
        "resources": {"opencode_tools": 1}
    },
    )   

    llm = OpenCodeLLM(
        model="opencode/nemotron-3.5-lightning-free",
        work_dir="/workspace",
    )

    prompt = """
You are a senior SystemVerilog and UVM verification engineer.

You are working in /workspace.

Use the Bash tool to inspect these four files:

1. examples/adder/adder.sv
2. generated/rtl/rtl_info.json
3. examples/adder/spec.md
4. examples/adder/ref_model.py

You MUST actually inspect all four files before creating the plan.

The RTL is the implementation under verification.

The specification describes the intended behavior.

The reference model describes the expected behavior and should
be used to determine how the DUT should be checked.

The Verible-derived RTL information provides structural information
about the DUT.

Analyze all four sources together.

Create a practical verification plan containing:

- DUT/module name
- parameters
- clock and reset
- ports, directions, and widths
- functional behavior
- directed test scenarios
- corner cases
- randomized testing strategy
- functional coverage
- scoreboard/reference-model strategy
- useful assertions

Important requirements:

- Do not invent ports, signals, parameters, clocks, resets, or behavior.
- Use the actual RTL as the source of truth for DUT structure.
- Use the specification and reference model to determine intended behavior.
- If the sources disagree, explicitly identify the discrepancy.
- The plan should be suitable as input to a later UVM testbench generator.

Return ONLY valid YAML.

Do not modify any files.
Do not create any files.
"""

    print("Sending request to OpenCode...")

    response = get(
        llm.prompt.chia_remote(
            llm,
            prompt,
            tools=[bash],
        )
    )

    print("\n===== RESULT =====")
    print(response.result)

    print("\n===== STREAM =====")
    print(response.stream_result)

    print("\n===== STDERR =====")
    print(response.stderr)

    bash.stop()
    ray.shutdown()