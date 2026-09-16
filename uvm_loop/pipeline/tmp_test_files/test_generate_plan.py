import ray

from chia.base.ChiaFunction import get
from chia.models.opencode import OpenCodeLLM
from chia.base.tools.BashTool import BashTool

from pipeline.functions import extract_rtl


if __name__ == "__main__":
    ray.init()

    # ---------------------------------------------------------
    # 1. Extract RTL information using the dedicated RTL worker
    # ---------------------------------------------------------

    rtl_info = get(
        extract_rtl.chia_remote(
            "examples/adder/adder.sv",
            "generated/rtl/rtl_info.json",
        )
    )

    print("\nRTL extraction result:")
    print(rtl_info)

    # ---------------------------------------------------------
    # 2. Create a Bash tool deployed with the OpenCode worker
    # ---------------------------------------------------------

    bash = BashTool(
        "verification_workspace",
        work_dir="/workspace",
        timeout_seconds=120,
        task_options={
            "resources": {"opencode_creds": 1}
        },
    )

    # ---------------------------------------------------------
    # 3. Create the OpenCode LLM
    # ---------------------------------------------------------

    llm = OpenCodeLLM(
        model="opencode/nemotron-3.5-lightning-free",
        work_dir="/workspace",
    )

    # ---------------------------------------------------------
    # 4. Ask the LLM to inspect the project using Bash
    # ---------------------------------------------------------

    prompt = """
You are a senior SystemVerilog and UVM verification engineer.

We need to create a verification plan for the DUT in this
repository.

Your working directory is:

/workspace

First inspect the repository using the Bash tool.

You MUST read these files:

1. examples/adder/adder.sv
2. generated/rtl/rtl_info.json
3. examples/adder/spec.md
4. examples/adder/ref_model.py

Use Bash commands such as `cat` or `sed` to inspect them.

Analyze the RTL, the Verible-derived RTL information,
the specification, and the reference model together.

The RTL is the implementation under verification.

The specification and reference model describe the intended
behavior.

Create a practical UVM verification plan containing:

- DUT/module name
- parameters
- ports and widths
- clock and reset
- functional behavior
- directed test scenarios
- corner cases
- randomized testing
- functional coverage
- scoreboard/reference-model strategy
- useful assertions

Do NOT invent ports, signals, clocks, resets, or behavior.

Use the actual RTL as the source of truth for the DUT structure.

Use the reference model to determine expected behavior.

Return ONLY the verification plan as YAML.

Do not modify any project files.
Do not create any files.
"""

    response = get(
        llm.prompt.chia_remote(
            llm,
            prompt,
            tools=[bash],
        )
    )

    # ---------------------------------------------------------
    # 5. Check result
    # ---------------------------------------------------------

    if not response.success:
        raise RuntimeError(
            "OpenCode failed:\n"
            f"{response.stderr}"
        )

    print("\n===== RESULT =====")
    print(response.result)
    
    print("\n===== STREAM RESULT =====")
    print(response.stream_result)
    
    print("\n===== STDERR =====")
    print(response.stderr)
    
    print("\n===== RETURN CODE =====")
    print(response.returncode)

    # ---------------------------------------------------------
    # 6. Clean up the deployed Bash tool
    # ---------------------------------------------------------

    bash.stop()

    ray.shutdown()