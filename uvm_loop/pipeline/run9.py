from pathlib import Path
import json
import subprocess
import re
import time
import shutil
import os

import ray

import yaml


from chia.base.ChiaFunction import ChiaFunction, get

from chia.base.tools.BashTool import BashTool

from chia.models.opencode import OpenCodeLLM

from pipeline.functions import extract_rtl, generate_uvm_in_worker, simulate, analyze_results
from pipeline.tb_feedback import ensure_simulation_manifest, build_diagnosis_prompt, build_repair_prompt
from pipeline.verification_improvement import (
    analyze_verification_state,
    prepare_sanitized_workspace,
    collect_tb_changes,
    build_improvement_prompt,
)
from src.schema import VerificationPlan



# =========================================================

# Workspace

# =========================================================

HOST_WORKSPACE = Path(__file__).resolve().parent.parent

CONTAINER_WORKSPACE = "/workspace"



# =========================================================

# Project inputs

# =========================================================

RTL = "examples/adder/adder.sv"

RTL_INFO = "generated/rtl/rtl_info.json"

SPEC = "examples/adder/spec.md"

REF_MODEL = "examples/adder/ref_model.py"

PLAN = "generated/plans/verification_plan.yaml"

CANDIDATE_PLAN = "generated/plans/candidate_verification_plan.yaml"

# Keep repair disabled until generation + review are stable.

MAX_REPAIR_ATTEMPTS = 2
MAX_TB_REPAIR_ATTEMPTS = 3
MAX_IMPROVEMENT_ITERATIONS = int(os.environ.get("MAX_VERIFICATION_IMPROVEMENT_ITERATIONS", "5"))
SIM_TEST_TIMEOUT = int(os.environ.get("SIM_TEST_TIMEOUT", "60"))
SIM_BUILD_TIMEOUT = 1800



# =========================================================
# Checkpoints
# =========================================================
#
# Stage 1 (RTL extraction) and Stage 2/3 (plan generation + review) each
# have a single well-defined, fixed-path output artifact (rtl_info.json,
# candidate_verification_plan.yaml, verification_plan.yaml) so resuming
# those stages is just "does that file already exist on disk".
#
# Stage 4 (staged UVM generation) is different: each of its six
# sub-stages writes LLM-authored files under generated_tb/ whose names
# aren't fixed in advance. Checkpoint markers are used for precise
# sub-stage resumption during an in-progress generation, but a complete
# generated_tb/ is also treated as persistent Stage-4 state. This means
# a later run will NEVER regenerate a complete existing environment merely
# because its checkpoint markers are absent.
#
# Same for Stage 5 (closed-loop
# simulation) — "did this already pass" isn't visible from a file
# listing either. For those we drop an explicit marker file the moment
# a stage completes successfully, and check for it before re-running
# that stage on a later invocation.
#
# To force a full re-run of a given stage, just delete its marker file
# (or the whole generated/checkpoints directory to start clean).
# =========================================================

CHECKPOINT_DIR = HOST_WORKSPACE / "generated/checkpoints"


def checkpoint_path(name):
    return CHECKPOINT_DIR / f"{name}.done"


def is_stage_done(name):
    return checkpoint_path(name).exists()


def mark_stage_done(name, detail=None):
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage": name,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if detail is not None:
        payload["detail"] = detail
    checkpoint_path(name).write_text(json.dumps(payload, indent=2))


def clear_stage(name):
    """Force a stage to re-run on the next invocation."""
    path = checkpoint_path(name)
    if path.exists():
        path.unlink()


def has_existing_generated_tb():
    """
    Return True when a previously generated Stage-4 cocotb+pyuvm
    environment is present and looks complete enough to continue from
    Stage 5.

    This intentionally checks for concrete Stage-4 artifacts rather than
    merely checking whether generated_tb/ exists. That prevents an
    interrupted/partial Stage-4 generation from being mistaken for a
    complete environment.

    The check is deliberately independent of Stage-4 checkpoint files:
    an existing TB is a valid starting point even when checkpoint markers
    were lost, copied, or never created.
    """
    tb_dir = HOST_WORKSPACE / "generated_tb"
    if not tb_dir.is_dir():
        return False

    required = [
        tb_dir / "CONTRACT.md",
        tb_dir / "generation_manifest.yaml",
        tb_dir / "test_top.py",
    ]

    if not all(path.is_file() for path in required):
        return False

    # A generated environment must contain at least one Python source
    # beyond the top-level cocotb entry point.
    return any(
        path.suffix == ".py" and path.name != "test_top.py"
        for path in tb_dir.iterdir()
        if path.is_file()
    )



# =========================================================

# Helper: create OpenCode + Bash

# =========================================================

def create_improvement_agent(work_dir):
    """Create an LLM agent whose filesystem contains only sanitized inputs."""
    bash = BashTool(
        "verification_improvement_workspace",
        work_dir=work_dir,
        timeout_seconds=1200,
        task_options={"resources": {"opencode_tools": 1}},
    )
    llm = OpenCodeLLM(
        model="opencode/big-pickle",
        work_dir=work_dir,
        timeout_seconds=1200,
        retries=1,
    )
    return llm, bash


def create_agent():

    bash = BashTool(

        "verification_workspace",

        work_dir=CONTAINER_WORKSPACE,

        timeout_seconds=1200,

        task_options={

            "resources": {"opencode_tools": 1}

        },

    )

    llm = OpenCodeLLM(

        model="opencode/big-pickle",

        work_dir=CONTAINER_WORKSPACE,

        timeout_seconds=1200,

        retries=1,

    )

    return llm, bash


# =========================================================

# Helper: clean LLM YAML output

# =========================================================

def clean_yaml_response(text):

    """Clean common Markdown fencing around YAML."""

    if not text:

        return ""

    text = text.strip()

    if "```yaml" in text:

        start = text.find("```yaml") + len("```yaml")

        end = text.find("```", start)

        if end != -1:

            return text[start:end].strip()

    if "```" in text:

        start = text.find("```") + 3

        end = text.find("```", start)

        if end != -1:

            candidate = text[start:end].strip()

            if candidate.startswith("yaml"):

                candidate = candidate[4:].strip()

            return candidate

    if text.startswith("yaml\\n"):
        return text[5:].strip()

    if text.startswith("yaml\\r\\n"):
        return text[7:].strip()

    return text



def parse_review_status(text):
    """
    Determine whether the reviewer found issues.

    The reviewer must emit NO_ISSUES or ISSUES_FOUND as a standalone status.
    The remainder of the response is free-form feedback and is passed to the
    repair LLM unchanged.
    """

    if not text or not text.strip():
        raise RuntimeError("Reviewer returned an empty response.")

    matches = []

    for line in text.splitlines():
        status = line.strip().upper()

        if status in {"NO_ISSUES", "ISSUES_FOUND"}:
            matches.append(status)

    if not matches:
        # Be tolerant of the model adding Markdown emphasis/headings.
        normalized = text.upper()
        if "ISSUES_FOUND" in normalized:
            return "issues_found"
        if "NO_ISSUES" in normalized:
            return "no_issues"

        raise RuntimeError(
            "Reviewer did not return NO_ISSUES or ISSUES_FOUND.\n\n"
            f"Raw reviewer response:\n{text}"
        )

    # If the model accidentally mentions both while reasoning, use the last
    # explicit status because it is most likely the final decision.
    return (
        "issues_found"
        if matches[-1] == "ISSUES_FOUND"
        else "no_issues"
    )



# Stage 2: Generate verification plan

# =========================================================

def generate_candidate_plan(llm, bash):

    canonical_schema = json.dumps(
        VerificationPlan.model_json_schema(),
        indent=2,
    )

    prompt = f"""

You are a senior digital-verification engineer.

Work in /workspace.

The plan you produce here is DUT/behavior-level and independent of the
target testbench implementation language. It will later be handed to a
downstream generator that implements the testbench in cocotb + pyuvm
(Python), not SystemVerilog UVM — so do not assume or require any
SystemVerilog-only verification features (e.g. do not depend on
covergroups, SVA, or classes existing in the plan itself; those are
concepts, and the downstream generator will realize them in Python).

CRITICAL OUTPUT CONTRACT:
Your YAML MUST conform exactly to the canonical VerificationPlan
Pydantic schema supplied below.

Do NOT invent an alternative YAML structure.
Do NOT rename fields.
Do NOT change mappings into lists or lists into mappings.
Do NOT use semantically similar field names when the schema specifies
a different name.

For example:
- reset MUST use "polarity" and "type" as defined by the schema.
- ports MUST be a mapping containing "inputs", "outputs", and "inouts".
- functional_behavior MUST be a mapping.
- each scenario's stimulus MUST match StimulusSequence.
- randomized_testing_strategy.constraints MUST contain RandomConstraint
  objects.
- functional_coverage MUST be a mapping containing covergroups.
- discrepancies MUST contain id, severity, and title.

## CANONICAL VerificationPlan JSON SCHEMA
{canonical_schema}


Use the Bash tool to inspect ALL FOUR source files:

1. {RTL}

2. {RTL_INFO}

3. {SPEC}

4. {REF_MODEL}

You MUST inspect all four files before answering.

SOURCE AUTHORITY:

- RTL is the authoritative source for actual DUT structure

  and implemented behavior.

- rtl_info.json provides extracted structural information.

- spec.md describes intended behavior.

- ref_model.py describes expected functional behavior.

Generate a practical verification plan for a later cocotb+pyuvm

testbench generator.

The plan must contain:

- dut

- parameters

- clock_and_reset

- ports

- functional_behavior

- directed_test_scenarios

- corner_cases

- randomized_testing_strategy

- functional_coverage

- scoreboard_reference_model_strategy

- useful_assertions

- discrepancies

IMPORTANT DISTINCTION:

The plan is allowed to DESIGN verification activities.

Therefore, it is valid to introduce:

- directed stimulus values

- corner cases

- randomized testing strategies

- coverage points

- coverage crosses

- assertions

- scoreboard architecture

- test scenarios

These do NOT need to literally appear in the RTL/spec/reference

model because they are proposed verification strategies.

However, these proposed strategies MUST be consistent with

the source files.

Do NOT invent DUT facts.

Never invent:

- ports

- parameters

- signals

- clocks

- resets

- DUT functionality

- reference-model behavior

Use the RTL as the source of truth whenever describing the

implemented DUT.

Use the specification and reference model to describe

intended behavior and expected results.

If RTL and specification disagree, explicitly record the

discrepancy instead of silently choosing one.

Preserve parameterization wherever applicable.

GOAL: produce a plan that is correct and usable as-is by a

downstream testbench generator. It does not need to be

exhaustive or maximally elaborate — a smaller, unambiguous,

fully-consistent plan is preferred over a larger plan that

reaches for extra coverage at the cost of precision.

Return ONLY valid YAML.

Do not use markdown fences.

Do not explain your answer.

Do not modify or create files.

"""

    response = get(

        llm.prompt.chia_remote(

            llm,

            prompt,

            tools=[bash],

        )

    )

    if not response.success:

        raise RuntimeError(

            f"OpenCode generation failed:\n{response.stderr}"

        )

    result = response.result

    if not result or not result.strip():

        raise RuntimeError(

            "OpenCode returned an empty verification plan."

        )

    return result



# =========================================================

# Stage 3: Review verification plan

# =========================================================

def review_candidate_plan(llm, bash, candidate):

    """

    Independent semantic review.

    The reviewer checks source-grounded DUT facts and the

    semantic correctness of proposed verification strategies.

    It does NOT require every proposed test, coverage point,

    or assertion to literally exist in the source files.

    """

    prompt = f"""

You are an independent verification-plan auditor.

Work in /workspace.

A different LLM generated the candidate verification plan below.

Your job is to independently audit the candidate against

the source files.

Use Bash to inspect ALL FOUR:

1. {RTL}

2. {RTL_INFO}

3. {SPEC}

4. {REF_MODEL}

Candidate plan:

---BEGIN CANDIDATE---

{candidate}

---END CANDIDATE---

============================================================

WHAT THIS REVIEW IS FOR

============================================================

Your job is NOT to make the plan maximally exhaustive or

stylistically ideal. Your job is only to catch genuine,

verifiable defects that would cause a downstream testbench

generator to produce technically incorrect code (wrong

ports, wrong widths, wrong expected values, wrong reset

semantics, contradictions with the RTL, etc.).

A plan that is correct but could theoretically have MORE

coverage, MORE corner cases, or MORE elaborate assertions is

NOT a defect. Do not flag missing "nice to have" additions as

issues. If your only feedback is a suggestion for something

additional or a stylistic preference, that is not an issue —

respond NO_ISSUES.

============================================================

IMPORTANT REVIEW RULE

============================================================

Separate SOURCE FACTS from VERIFICATION DESIGN.

The candidate is ALLOWED to introduce new verification

activities that are not explicitly present in the sources.

For example, these are legitimate plan content:

- directed test scenarios

- chosen stimulus values

- corner cases

- randomized testing

- coverage bins

- coverage crosses

- scoreboard architecture

- assertions

- reset stress tests

- parameter sweep strategies

Do NOT mark those as hallucinations merely because they

were not written in the RTL or specification.

Instead, determine whether the proposed verification activity

is logically consistent with the DUT and reference behavior.

============================================================

CHECK SOURCE-GROUNDED DUT FACTS

============================================================

You MUST flag actual factual errors involving:

1. DUT/module identity

2. Parameters

3. Ports

4. Port directions

5. Port widths

6. Clock

7. Reset

8. Implemented DUT behavior

9. Reference-model behavior

10. RTL/specification discrepancies

============================================================

CHECK SEMANTIC CORRECTNESS

============================================================

You MUST also flag verification content when it is

semantically incorrect.

Examples:

- An expected arithmetic result is wrong.

- A reset test expects synchronous behavior from an

  asynchronous RTL reset.

- A scoreboard uses the wrong input/output cycle relationship.

- An assertion contradicts the actual RTL.

- A proposed coverage point is based on a nonexistent signal.

- A reference-model call is described incorrectly.

- A scenario claims overflow where the arithmetic cannot overflow.

- A test assumes combinational behavior from registered outputs.

============================================================

KNOWN RESET CHECK

============================================================

Pay special attention to asynchronous reset.

If the RTL contains:

    always @(posedge clk or negedge rst_n)

then rst_n assertion on negedge is asynchronous.

A plan saying reset only clears on posedge clk is incorrect.

If the specification says synchronous reset while the RTL

implements asynchronous reset, this MUST be reported as a

discrepancy.

Do not invent a required reset duration unless the sources

actually specify one.

============================================================

KNOWN REGISTERED-DATA CHECK

============================================================

Determine the actual relationship between input sampling and

registered outputs from the RTL.

Do not automatically call the DUT a "pipeline".

If the DUT simply samples inputs at posedge clk and registers

the result, describe that accurately.

============================================================

REFERENCE MODEL CHECK

============================================================

Compare arithmetic expectations against ref_model.py.

For every explicit numerical expected result in a directed

test, verify that it is mathematically correct.

============================================================

MATERIALITY BAR (READ CAREFULLY)

============================================================

Before reporting ISSUES_FOUND, ask yourself: "Would this

specific problem cause a testbench generated from this plan

to be functionally wrong, or to check against the wrong

expected behavior?"

If the honest answer is no — it's a matter of taste, added

thoroughness, phrasing, or a judgment call that is still

defensible given the sources — then it is NOT an issue.

When you are genuinely unsure whether something is a real

defect or just a stylistic nitpick, resolve the doubt in favor

of NO_ISSUES.

Only report ISSUES_FOUND for concrete, specific, checkable

problems you can point to directly in the candidate text.

============================================================

STRICT OUTPUT CONTRACT

Your response MUST begin with exactly one of these two lines:

NO_ISSUES

or:

ISSUES_FOUND

Do NOT put anything before the status line.

If there are no genuine, material, factual or semantic

problems, return:

NO_ISSUES

You may optionally provide a very short explanation after NO_ISSUES,
but do not provide unrelated analysis or suggestions for additions.

If there are one or more genuine, material problems, return:

ISSUES_FOUND

Then list ONLY the concrete problems that meet the materiality bar
above, and where useful, the correction needed to make the existing
candidate plan accurate.

Do NOT use YAML or JSON for the review response.

Do NOT rewrite the candidate plan.

Do NOT modify files.

Only report genuine, material factual or semantic problems.

Do NOT reject reasonable verification strategies merely because they
were newly designed by the generator.

Do NOT report an issue merely because the plan could be more thorough,
more exhaustive, or more elaborate — that is not a defect.

"""

    response = get(

        llm.prompt.chia_remote(

            llm,

            prompt,

            tools=[bash],

        )

    )

    if not response.success:

        raise RuntimeError(

            f"OpenCode review failed:\n{response.stderr}"

        )

    result = response.result

    if not result or not result.strip():

        raise RuntimeError(

            "OpenCode reviewer returned an empty response."

        )

    return result.strip()



# Stage 4: Repair verification plan

# =========================================================

def repair_candidate_plan(llm, bash, candidate, review, yaml_error=None):
    """Repair the existing candidate using reviewer findings only."""

    prompt = f"""
You are a verification-plan editor.

An independent reviewer has already audited the candidate against the RTL,
rtl_info.json, specification, and reference model.

MINIMALLY EDIT THE EXISTING PLAN to fix the reported issues.

Do NOT regenerate the plan from scratch.
Do NOT redesign correct sections.
Preserve all correct content and the existing YAML structure.

---BEGIN CURRENT PLAN---
{candidate}
---END CURRENT PLAN---

---BEGIN REVIEW FINDINGS---
{review}
---END REVIEW FINDINGS---

---BEGIN PREVIOUS YAML ERROR---
{yaml_error or "None"}
---END PREVIOUS YAML ERROR---

CANONICAL VerificationPlan SCHEMA:
{json.dumps(VerificationPlan.model_json_schema(), indent=2)}

The repaired document MUST conform exactly to this schema. Preserve the
existing plan's correct content, but when the current candidate uses a
structure that does not match the schema, convert it to the canonical
structure without changing its meaning.

Rules:
1. Go through the review findings one at a time. For each one, make a
   complete, unambiguous fix — not a partial edit or a hedge that only
   half-addresses the concern. A finding that is only partially fixed
   will very likely be flagged again on the next review pass, so resolve
   each one decisively using the sources you already have available in
   the current plan and findings text.
2. Make the smallest possible changes that still fully resolve every
   finding above.
3. Do not redesign or touch any section of the plan that the review
   findings did not mention.
4. Preserve correct tests, coverage, assertions, scoreboard details,
   parameters, ports, and DUT facts that were not flagged.
5. Do not invent DUT ports, parameters, clocks, resets, signals,
   functionality, or reference-model behavior.
6. Preserve genuine RTL/specification discrepancies.
7. If a YAML parser error is supplied, fix that syntax error.
8. Return the COMPLETE plan, not a patch.
9. Before finishing, re-read each review finding against your edited
   plan and confirm the exact concern raised no longer applies anywhere
   in the document.

ABSOLUTE OUTPUT REQUIREMENT:

Your response will be passed directly to yaml.safe_load().
Therefore the FIRST character of your response MUST be the first
character of the YAML document.

The response MUST begin with:

dut:

and MUST contain the complete verification plan.

Do not write:
- "Here is the corrected plan"
- "The fix is..."
- "I corrected..."
- explanations
- analysis
- Markdown
- code fences
- comments before the YAML
- Return ONLY the complete YAML document.
- Do NOT use Markdown fences.
- Do NOT explain the changes.
- Do NOT add text before or after YAML.
- Do NOT modify or create files.

If you need to reason about the fix, do that internally.
Your externally returned response must contain ONLY the YAML document.
"""

    response = get(
        llm.prompt.chia_remote(
            llm,
            prompt,
            tools=[],
        )
    )

    if not response.success:
        raise RuntimeError(
            f"OpenCode repair failed:\n{response.stderr}"
        )

    result = response.result

    if not result or not result.strip():
        raise RuntimeError(
            "OpenCode repair returned an empty plan."
        )

    return result.strip()



def validate_yaml(plan_text):

    """

    Python performs structural validation.

    Semantic correctness is handled by the LLM reviewer.

    """

    plan_text = clean_yaml_response(plan_text)

    try:

        parsed = yaml.safe_load(plan_text)

    except yaml.YAMLError as exc:

        return False, f"Invalid YAML: {exc}"

    if not isinstance(parsed, dict):

        return False, "Plan must be a YAML mapping."

    required_fields = [

        "dut",

        "parameters",

        "clock_and_reset",

        "ports",

        "functional_behavior",

        "directed_test_scenarios",

        "corner_cases",

        "randomized_testing_strategy",

        "functional_coverage",

        "scoreboard_reference_model_strategy",

        "useful_assertions",

        "discrepancies",

    ]

    for field in required_fields:

        if field not in parsed:

            return False, (

                f"Missing required top-level field: {field}."

            )

    return True, parsed



# =========================================================

# YAML boundary: clean + validate + repair

# =========================================================

def ensure_valid_yaml(llm, text, context, max_attempts=2):
    """
    Every LLM-produced YAML document passes through this boundary.

    Python first cleans and validates the response. If malformed, a small
    dedicated YAML-repair call is made. This helper fixes syntax/formatting
    only; semantic correctness remains the reviewer's responsibility.
    """

    candidate = clean_yaml_response(text)

    valid, error = validate_yaml(candidate)

    if valid:
        return candidate

    last_error = error

    for attempt in range(1, max_attempts + 1):

        print(f"\n⚠ Invalid YAML from {context}:")
        print(last_error)
        print(
            f"YAML syntax repair attempt "
            f"{attempt}/{max_attempts}..."
        )

        prompt = f"""
You are a YAML syntax repair tool.

Repair ONLY the YAML syntax and formatting of the document below.

Do NOT change its meaning.
Do NOT change values.
Do NOT add or remove verification-plan content.
Do NOT fix semantic verification errors.
Do NOT invent anything.

Parser error:

---BEGIN PARSER ERROR---
{last_error}
---END PARSER ERROR---

Malformed YAML:

---BEGIN MALFORMED YAML---
{candidate}
---END MALFORMED YAML---

Return ONLY the complete corrected YAML document.
Do NOT use Markdown fences.
Do NOT add explanations.
Do NOT add text before or after the YAML.
"""

        response = get(
            llm.prompt.chia_remote(
                llm,
                prompt,
                tools=[],
            )
        )

        if not response.success:
            raise RuntimeError(
                f"OpenCode YAML repair failed for {context}:\n"
                f"{response.stderr}"
            )

        repaired = response.result

        if not repaired or not repaired.strip():
            raise RuntimeError(
                f"OpenCode YAML repair returned an empty response "
                f"for {context}."
            )

        candidate = clean_yaml_response(repaired)

        valid, error = validate_yaml(candidate)

        if valid:
            print(f"✓ YAML repaired successfully for {context}.")
            return candidate

        last_error = error

    raise RuntimeError(
        f"Unable to produce valid YAML for {context} after "
        f"{max_attempts} syntax-repair attempts.\n\n"
        f"Last YAML error:\n{last_error}"
    )



# =========================================================
# Shared, compact constraint block used by every cocotb+pyuvm
# generation stage below (kept short and separate so it isn't
# re-deriving conventions from a giant prompt each time).
# =========================================================

HARD_CONSTRAINTS = """
COCOTB + PYUVM COMPATIBILITY REQUIREMENTS (HARD, apply to every file you write):
- The testbench is implemented entirely in Python using cocotb + pyuvm.
  Do NOT generate any SystemVerilog UVM code: no SystemVerilog
  `interface`, no SV classes derived from uvm_driver/uvm_monitor/etc.,
  no SV covergroups, no SVA. The only SystemVerilog in this project is
  the DUT RTL itself, which already exists and must NOT be modified or
  duplicated.
- Target cocotb's async/await coroutine style (`async def`,
  `cocotb.start_soon`, and triggers such as `RisingEdge`, `FallingEdge`,
  `ClockCycles`, `Timer`, `Combine` from `cocotb.triggers`) together with
  pyuvm as the UVM class library (`uvm_component`, `uvm_driver`,
  `uvm_monitor`, `uvm_agent`, `uvm_scoreboard`, `uvm_env`, `uvm_test`,
  `uvm_sequence`, `uvm_sequence_item`, `uvm_sequencer`,
  `uvm_analysis_port`/`uvm_tlm_analysis_fifo`, `ConfigDB`, etc.).
- There is no SystemVerilog `interface`. Drive and sample DUT pins
  directly through the `dut` handle cocotb provides (e.g.
  `dut.a.value = 1`, `dut.sum.value`), using exactly the pin names and
  widths recorded in CONTRACT.md.
- Share objects between UVM components (the `dut` handle, clock/reset
  signal names, any helper bus object) using pyuvm's
  `ConfigDB().set(...)` / `ConfigDB().get(...)`, keyed exactly as defined
  in CONTRACT.md. Do not invent alternative keys per component.
- Functional coverage must use the `cocotb-coverage` library
  (`cocotb_coverage.coverage.CoverPoint` / `CoverCross`, sampled through
  the shared `coverage_db`), not SystemVerilog covergroups.
- Assertions must be implemented as plain Python checks (an `assert`
  statement, or explicitly raising/flagging a failure) inside
  always-running checker coroutines started with `cocotb.start_soon`.
  These run concurrently with the rest of the environment and must fail
  the test immediately when a check does not hold. This replaces SVA.
- A watchdog is still required: an always-running coroutine (or a
  bounded `cocotb.triggers.with_timeout` wrapper around the test body)
  that fails the test if it does not finish within a bounded number of
  clock cycles, so a hung test cannot silently exhaust the whole
  simulation run.
- Do NOT invent DUT ports, parameters, clocks, resets, widths, or
  behavior. The RTL and rtl_info.json are authoritative for implemented
  DUT structure.
- Write all generated files under /workspace/generated_tb, as Python
  modules (.py) plus the build/run configuration described in the
  integration stage.
- Do not modify the RTL, specification, reference model, or generated
  plan.
"""

# Every later stage reads this instead of re-deriving pin/transaction
# conventions from scratch. It is written by Stage 4.1 (contract) and must
# be treated as authoritative by every subsequent stage.
CONTRACT_PATH = "generated_tb/CONTRACT.md"

CONSULT_CONTRACT = f"""
BEFORE WRITING ANYTHING:
Read /workspace/{CONTRACT_PATH}. It defines the DUT pin names, widths,
and directions (and how each is accessed via the `dut` handle), the
transaction/sequence-item field list, the exact ConfigDB key(s) used to
share the `dut` handle (and any helper object) between components, and
the top module name that were already fixed in an earlier generation
stage.

Do NOT redefine, rename, or reinterpret anything in the contract. If you
believe the contract is wrong or incomplete for what this stage needs,
extend it minimally (append, do not rewrite) and explain why in your
summary — do not silently diverge from it in code.
"""


def plan_section(canonical_plan, keys):
    """Return only the requested top-level keys of the plan, as YAML.

    Keeps each stage's prompt proportional to what it actually needs
    instead of always carrying the entire plan around.
    """
    parsed = yaml.safe_load(clean_yaml_response(canonical_plan))
    subset = {k: parsed[k] for k in keys if k in parsed}
    return yaml.safe_dump(subset, sort_keys=False, allow_unicode=True)


def run_stage(llm, bash, prompt, stage_name, tools=None):
    """Run one staged generation call and surface its summary."""
    response = get(
        llm.prompt.chia_remote(
            llm,
            prompt,
            tools=[bash] if tools is None else tools,
        )
    )
    if not response.success:
        raise RuntimeError(
            f"OpenCode UVM generation stage '{stage_name}' failed:\n"
            f"{response.stderr}"
        )
    print(f"\n===== UVM GENERATION: {stage_name.upper()} =====")
    print((response.result or "").strip())
    return response


# =========================================================
# Stage 4.1 — Contract: transaction/sequence item + pin map
# =========================================================
def build_contract_prompt(canonical_plan, capabilities, rules, templates_note):
    plan_bits = plan_section(
        canonical_plan,
        ["dut", "parameters", "clock_and_reset", "ports", "functional_behavior"],
    )
    return f"""
You are the CHIA cocotb+pyuvm environment generator, stage 1 of 6: CONTRACT.

Work in /workspace.

Establish the foundation every later stage will build on:
1. The transaction / sequence_item class, as a pyuvm `uvm_sequence_item`
   subclass with plain Python attributes for each field.
2. (Optional) a small Python helper module that centralizes direct DUT
   pin access via the `dut` handle, if that makes later stages cleaner.
   This is plain Python, NOT a SystemVerilog interface.
3. A short contract file at /workspace/{CONTRACT_PATH} that later stages
   will read instead of re-deriving conventions. It must state:
   - top module name
   - every DUT pin, with direction + width, and exactly how it is
     accessed (e.g. `dut.a`, `dut.sum`)
   - transaction/sequence_item field names + types
   - the exact ConfigDB key(s)/type(s) used to share the `dut` handle
     (and any helper object) between components
   - clock and reset signal names and reset polarity/type

{HARD_CONSTRAINTS}

## RELEVANT VERIFICATION PLAN SECTIONS
{plan_bits}

## SOURCE FILES
RTL: {RTL}
RTL INFO: {RTL_INFO}
SPECIFICATION: {SPEC}

## UVM CAPABILITIES
{capabilities}

## UVM RULES
{rules}

{templates_note}

Use Bash to inspect the RTL and rtl_info.json before writing anything —
the pin map in CONTRACT.md must exactly match the DUT.

Do not generate the driver, monitor, sequencer, agent, scoreboard,
coverage, assertions, environment, tests, or top-level testbench in this
stage. Only the transaction/sequence_item class, the optional pin-access
helper, and CONTRACT.md.

Return a concise summary of what you wrote. Do not return source code in
your response — write it to disk.
"""


# =========================================================
# Stage 4.2 — Stimulus: sequencer, driver, sequences
# =========================================================
def build_stimulus_prompt(canonical_plan):
    plan_bits = plan_section(
        canonical_plan,
        ["directed_test_scenarios", "corner_cases", "randomized_testing_strategy"],
    )
    return f"""
You are the CHIA cocotb+pyuvm environment generator, stage 2 of 6: STIMULUS.

Work in /workspace.

{CONSULT_CONTRACT}

{HARD_CONSTRAINTS}

Generate the pyuvm sequencer (`uvm_sequencer`), driver (`uvm_driver`),
and sequences (`uvm_sequence` subclasses — directed, corner-case, and
randomized) that realize the following plan sections:

{plan_bits}

The driver must drive the DUT pins exactly as defined in CONTRACT.md,
synchronized to clock edges using cocotb triggers (e.g.
`await RisingEdge(dut.clk)`). Sequences must produce sequence_item
fields exactly as defined in CONTRACT.md — do not add, rename, or drop
fields.

Do not generate the transaction class, monitor, agent, scoreboard,
coverage, assertions, environment, tests, or top-level testbench in this
stage.

Return a concise summary of what you wrote. Do not return source code in
your response — write it to disk.
"""


# =========================================================
# Stage 4.3 — Observation: monitor, agent
# =========================================================
def build_observation_prompt(canonical_plan):
    plan_bits = plan_section(canonical_plan, ["functional_behavior"])
    return f"""
You are the CHIA cocotb+pyuvm environment generator, stage 3 of 6: OBSERVATION.

Work in /workspace.

{CONSULT_CONTRACT}

{HARD_CONSTRAINTS}

Generate the pyuvm monitor (`uvm_monitor`) and agent (`uvm_agent`,
encapsulating driver/sequencer from the previous stage and this stage's
monitor). The monitor must sample the DUT pins, using an
`async def` coroutine synchronized on the clock (e.g.
`await RisingEdge(dut.clk)`), using exactly the pins and timing
relationship described in CONTRACT.md and the functional behavior
below, and must publish transactions with exactly the fields defined in
CONTRACT.md via a `uvm_analysis_port`.

## RELEVANT VERIFICATION PLAN SECTIONS
{plan_bits}

Do not generate the transaction class, sequencer, driver, sequences,
scoreboard, coverage, assertions, environment, tests, or top-level
testbench in this stage.

Return a concise summary of what you wrote. Do not return source code in
your response — write it to disk.
"""


# =========================================================
# Stage 4.4 — Scoreboard + reference-model integration
# =========================================================
def build_scoreboard_prompt(canonical_plan):
    plan_bits = plan_section(
        canonical_plan, ["scoreboard_reference_model_strategy", "functional_behavior"]
    )
    return f"""
You are the CHIA cocotb+pyuvm environment generator, stage 4 of 6: SCOREBOARD.

Work in /workspace.

{CONSULT_CONTRACT}

{HARD_CONSTRAINTS}

Generate the scoreboard (`uvm_scoreboard`) and its reference-model
integration, following:

{plan_bits}

REFERENCE MODEL (behavioral oracle for expected results):
{REF_MODEL}

Use Bash to read ref_model.py before writing the scoreboard. The
reference model is already plain Python, so the scoreboard MUST import
and call it directly rather than reimplementing, regenerating, or
translating its logic. Either add the reference model's directory to
`sys.path` and `import` it, or copy ref_model.py verbatim into
/workspace/generated_tb and import it from there — do not hand-write a
second copy of its arithmetic/behavior. If you copy the file, note its
new path in your summary.

The scoreboard must consume monitor transactions (via a
`uvm_tlm_analysis_fifo` or an analysis export) with exactly the fields
defined in CONTRACT.md, and must apply the correct input/output cycle
relationship (combinational vs. registered) as established in CONTRACT.md
and functional_behavior above — do not assume a pipeline unless the DUT
actually is one.

Do not generate the transaction class, sequencer, driver, sequences,
monitor, agent, coverage, assertions, environment, tests, or top-level
testbench in this stage.

Return a concise summary of what you wrote. Do not return source code in
your response — write it to disk.
"""


# =========================================================
# Stage 4.5 — Coverage + assertions
# =========================================================
def build_coverage_assertions_prompt(canonical_plan):
    plan_bits = plan_section(canonical_plan, ["functional_coverage", "useful_assertions"])
    return f"""
You are the CHIA cocotb+pyuvm environment generator, stage 5 of 6: COVERAGE & ASSERTIONS.

Work in /workspace.

{CONSULT_CONTRACT}

{HARD_CONSTRAINTS}

Generate functional coverage and assertions per:

{plan_bits}

Functional coverage MUST be implemented with the `cocotb-coverage`
library (`cocotb_coverage.coverage.CoverPoint` / `CoverCross`, sampled
through the shared `coverage_db`), driven off transactions/fields
published by the monitor from stage 3. Do not invent coverage points on
pins or fields that do not exist in CONTRACT.md.

Assertions MUST be implemented as Python checker coroutines started with
`cocotb.start_soon` that run continuously (synchronized on clock edges
via cocotb triggers) and use plain `assert` statements (or an equivalent
explicit failure) to flag a violation immediately — this replaces SVA.
Each assertion coroutine should have a clear name/docstring tying it back
to the plan item it implements.

Do not generate the transaction class, sequencer, driver, sequences,
monitor, agent, scoreboard, environment, tests, or top-level testbench in
this stage.

Return a concise summary of what you wrote. Do not return source code in
your response — write it to disk.
"""


# =========================================================
# Stage 4.6 — Integration: env, tests, top-level cocotb entry point,
# build/run config, manifest
# =========================================================
def build_integration_prompt(canonical_plan, capabilities, rules, templates_note):
    return f"""
You are the CHIA cocotb+pyuvm environment generator, stage 6 of 6: INTEGRATION.

Work in /workspace.

{CONSULT_CONTRACT}

{HARD_CONSTRAINTS}

Start by running `ls -la /workspace/generated_tb` (and inspect files as
needed) to see everything the previous five stages already wrote:
transaction class, sequencer/driver/sequences, monitor/agent,
scoreboard, coverage, assertions.

Now assemble the complete environment:
- environment (`uvm_env`) instantiating agent + scoreboard + coverage +
  the assertion checker coroutines from stage 5
- test classes (`uvm_test` subclasses) per the plan's
  directed/corner/randomized scenarios
- a top-level Python cocotb entry point (e.g.
  `generated_tb/test_top.py`) containing one or a small number of
  `@cocotb.test()` coroutines that:
  - read which UVM test class to run from an environment variable
    (e.g. `os.environ.get("UVM_TESTNAME", ...)`), mirroring how SV UVM
    is normally driven by `+UVM_TESTNAME`
  - start the clock with `cocotb.clock.Clock` and apply reset per
    CONTRACT.md's clock/reset signal names and polarity
  - call `await uvm_root().run_test(<test_class_name>)`
  - are wrapped by the watchdog described in HARD_CONSTRAINTS
- build/run configuration for the cocotb flow MUST use a cocotb
  `Makefile` with `SIM = verilator`, `TOPLEVEL = <top module>`,
  `MODULE = <top-level python test module, without .py>`,
  and `VERILOG_SOURCES` pointing only at the DUT RTL file(s).
  Do not use `cocotb.runner` or `get_runner`. There is no generated
  SystemVerilog to compile — only the existing DUT RTL is passed to
  the simulator as an HDL source.

## UVM CAPABILITIES
{capabilities}

## UVM RULES
{rules}

{templates_note}

MANDATORY SIMULATION MANIFEST:
Create/update /workspace/generated_tb/generation_manifest.yaml with:

top_module: <exact top module name, matching CONTRACT.md>
top_file: <RTL-relative .sv file containing that module>
compile_files:
  - <HDL source file(s) that must be passed directly to the simulator —
    this is only the existing DUT RTL; there must be no generated
    SystemVerilog listed here>
test_classes:
  - <exact pyuvm uvm_test class names, selectable via the UVM_TESTNAME
    environment variable read by the top-level cocotb entry point>
python_test_module:
  <the top-level Python cocotb test module to run, e.g.
  generated_tb.test_top, without the .py extension>

Do not list the reference model, driver, monitor, scoreboard, coverage,
or any other generated Python file in compile_files — those are not HDL
sources and must not be passed to the simulator.

FINAL CONSISTENCY PASS (do this after assembling everything):
Inspect ALL generated files together for:
- undeclared or misnamed DUT pins
- wrong DUT pin names or widths (cross-check against CONTRACT.md)
- missing UVM component construction or ConfigDB wiring
- incorrect reset handling
- incorrect scoreboard latency
- incorrect reference-model invocation (must call the real ref_model.py,
  not a reimplementation)
- missing files referenced by other generated files
- field-name mismatches between transaction, driver, monitor, scoreboard,
  and coverage (all must match CONTRACT.md exactly)
- any accidental SystemVerilog UVM code that should not exist
Fix anything you find before finishing.

Do not return generated source code in your response. Return a concise
summary of the files created/modified and any remaining concerns.
"""


# =========================================================

# Stage 4 + 5: UVM environment generation and validation

# =========================================================
#
# Factored out of main() so it can be reached either after a freshly
# accepted verification plan, or directly when a verification plan and
# rtl_info.json already exist on disk (see main()).
#
# Stage 4 (generation) is broken into six focused calls that share a
# single CONTRACT.md instead of one giant prompt trying to hold every
# component + the full plan + full capabilities/rules at once. The
# testbench produced by these stages is cocotb + pyuvm (Python) driving
# the existing DUT RTL directly — no SystemVerilog UVM code is
# generated. Stage 5 (closed-loop simulate/diagnose/repair) is unchanged
# from the original SV-based flow structurally, but now operates over
# the generated Python cocotb+pyuvm environment.
#
# RESUMABILITY: each of the six sub-stages below, plus the closed-loop
# validation, is guarded by a checkpoint (see the Checkpoints section
# near the top of this file). If a checkpoint already exists from a
# previous run, that sub-stage is skipped entirely instead of being
# regenerated. This means re-running the pipeline after an interruption
# (crash, manual stop, quota limit, etc.) picks up exactly where it left
# off instead of redoing already-completed work.
#
def generate_and_validate_uvm(llm, bash, canonical_plan):

    # IMPORTANT: generated_tb/ is persistent verification state. If a
    # complete Stage-4 environment already exists, do NOT regenerate it
    # merely because the Stage-4 checkpoint markers are missing. This is
    # what allows `run8.py` to resume at Stage 5+ on a subsequent run.
    if has_existing_generated_tb():
        print(
            "\n✓ Existing generated cocotb+pyuvm environment found."
            "\n  Skipping Stage 4 generation and preserving the existing TB."
            "\n  Continuing directly with Stage 5+ validation/improvement."
        )
        run_verification_improvement_loop(llm, bash, canonical_plan)
        return

    print("\n[4/4] Generating cocotb+pyuvm environment (staged)...")

    capabilities = (HOST_WORKSPACE / "uvm_generator/capabilities.yaml").read_text()
    rules = (HOST_WORKSPACE / "uvm_generator/rules.yaml").read_text()
    templates_note = (
        "## TEMPLATE LIBRARY\n"
        "Inspect the available templates under /workspace/templates before "
        "writing files, and reuse them where applicable."
    )

    # Each entry: (checkpoint name, human label, prompt builder).
    # The prompt builder is only invoked if the stage isn't already done,
    # so we don't waste time re-reading the plan/capabilities/rules for
    # stages we're about to skip.
    stage_defs = [
        (
            "uvm_contract",
            "contract",
            lambda: build_contract_prompt(
                canonical_plan, capabilities, rules, templates_note
            ),
        ),
        (
            "uvm_stimulus",
            "stimulus",
            lambda: build_stimulus_prompt(canonical_plan),
        ),
        (
            "uvm_observation",
            "observation",
            lambda: build_observation_prompt(canonical_plan),
        ),
        (
            "uvm_scoreboard",
            "scoreboard",
            lambda: build_scoreboard_prompt(canonical_plan),
        ),
        (
            "uvm_coverage_assertions",
            "coverage_assertions",
            lambda: build_coverage_assertions_prompt(canonical_plan),
        ),
        (
            "uvm_integration",
            "integration",
            lambda: build_integration_prompt(
                canonical_plan, capabilities, rules, templates_note
            ),
        ),
    ]

    for checkpoint_name, stage_name, build_prompt in stage_defs:
        if is_stage_done(checkpoint_name):
            print(
                f"\n✓ Skipping UVM sub-stage '{stage_name}': checkpoint "
                f"found ({checkpoint_path(checkpoint_name)}), already "
                "completed in a previous run."
            )
            continue

        run_stage(llm, bash, build_prompt(), stage_name)
        mark_stage_done(checkpoint_name)

    print(
        "\n✓ cocotb+pyuvm environment generated directly under "
        "/workspace/generated_tb."
    )

    # =================================================
    # Stage 5: Closed-loop generated-TB validation
    # =================================================
    # The generator owns verification intent. The simulator
    # owns execution. The repair LLM is only allowed to make
    # DUT/TB-specific changes after a structured diagnosis.

    if is_stage_done("tb_validated"):
        print(
            "\n✓ Skipping TB validation: checkpoint found "
            f"({checkpoint_path('tb_validated')}) — the generated "
            "cocotb+pyuvm environment already passed simulation in a "
            "previous run."
        )
        run_verification_improvement_loop(llm, bash, canonical_plan)
        return

    print("\n[5/5] Validating generated cocotb+pyuvm environment...")

    tb_dir = HOST_WORKSPACE / "generated_tb"
    ensure_simulation_manifest(str(tb_dir))

    final_analysis = None

    for tb_attempt in range(MAX_TB_REPAIR_ATTEMPTS + 1):
        result_rel = (
            f"generated/results/tb_validation_"
            f"iteration_{tb_attempt}.json"
        )
        result_path = get(
            simulate.chia_remote(
                RTL,
                "generated_tb",
                result_rel,
                SIM_TEST_TIMEOUT,
                SIM_BUILD_TIMEOUT,
            )
        )

        local_result_path = HOST_WORKSPACE / result_rel
        if not local_result_path.exists():
            raise RuntimeError(f"Simulation result was not created: {local_result_path}")
        final_analysis = analyze_results(str(local_result_path))
        print("\n===== TB SIMULATION ANALYSIS =====")
        print(json.dumps(final_analysis, indent=2))

        if final_analysis["verdict"] == "pass":
            print("\n✓ Generated cocotb+pyuvm environment passed simulation.")
            mark_stage_done("tb_validated", detail={"result_path": result_rel})
            run_verification_improvement_loop(llm, bash, canonical_plan)
            return

        if final_analysis["verdict"] == "template_bug":
            raise RuntimeError(
                "Template/toolchain defect detected. "
                "Do not patch this generated TB with the LLM. "
                "Fix the shared cocotb/pyuvm/Verilator templates or "
                "simulation infrastructure instead.\n\n"
                + json.dumps(final_analysis["detail"], indent=2)
            )

        if tb_attempt >= MAX_TB_REPAIR_ATTEMPTS:
            raise RuntimeError(
                "Generated cocotb+pyuvm environment still fails after "
                f"{MAX_TB_REPAIR_ATTEMPTS} repair attempts.\n\n"
                + json.dumps(final_analysis, indent=2)
            )

        # -------------------------------
        # Diagnosis LLM: failure -> plan
        # -------------------------------
        print(
            f"\nDiagnosing TB failure "
            f"(attempt {tb_attempt + 1})..."
        )
        diagnosis_workspace = HOST_WORKSPACE / "generated" / "llm_tb_diagnosis_workspace"
        diagnosis_report = {
            "source": "tb_validation",
            "result_path": str(local_result_path),
            "rtl_exposed_to_llm": False,
        }
        prepare_sanitized_workspace(
            diagnosis_workspace,
            HOST_WORKSPACE / SPEC,
            HOST_WORKSPACE / REF_MODEL,
            HOST_WORKSPACE / PLAN,
            HOST_WORKSPACE / "generated_tb",
            diagnosis_report,
        )
        shutil.copy2(local_result_path, diagnosis_workspace / "simulation_result.json")
        diagnosis_llm, diagnosis_bash = create_improvement_agent(str(diagnosis_workspace))
        try:
            diagnosis_prompt = build_diagnosis_prompt(
                f"{diagnosis_workspace}/simulation_result.json",
                "specification.md", "reference_model.py", "verification_plan.yaml"
            )
            diagnosis_response = get(
                diagnosis_llm.prompt.chia_remote(
                    diagnosis_llm, diagnosis_prompt, tools=[diagnosis_bash]
                )
            )
        finally:
            diagnosis_bash.stop()
        if not diagnosis_response.success:
            raise RuntimeError(
                "TB diagnosis LLM failed:\n"
                f"{diagnosis_response.stderr}"
            )

        update_plan_path = (
            HOST_WORKSPACE
            / "generated/results"
            / f"tb_update_plan_iteration_{tb_attempt}.yaml"
        )
        # Never let a previous pipeline invocation become the
        # diagnosis for the current simulation result.
        if update_plan_path.exists():
            update_plan_path.unlink()
        if not update_plan_path.exists():
            candidate_plan = clean_yaml_response(
                diagnosis_response.result or ""
            )
            try:
                parsed_plan = yaml.safe_load(candidate_plan)
            except yaml.YAMLError as exc:
                raise RuntimeError(
                    "TB diagnosis did not create a valid "
                    "tb_update_plan.yaml"
                ) from exc
            if not isinstance(parsed_plan, dict):
                raise RuntimeError(
                    "TB diagnosis returned no usable update plan."
                )
            update_plan_path.parent.mkdir(parents=True, exist_ok=True)
            update_plan_path.write_text(
                yaml.safe_dump(parsed_plan, sort_keys=False)
            )

        try:
            update_plan = yaml.safe_load(
                update_plan_path.read_text()
            )
        except yaml.YAMLError as exc:
            raise RuntimeError(
                f"Invalid TB update plan: {exc}"
            ) from exc

        if not isinstance(update_plan, dict):
            raise RuntimeError("TB update plan must be a YAML mapping")

        print("\n===== TB UPDATE PLAN =====")
        print(yaml.safe_dump(update_plan, sort_keys=False))

        if update_plan.get("verdict") == "template_bug":
            raise RuntimeError(
                "TB diagnosis classified this as a "
                "template/toolchain issue. Fix the shared "
                "template/infrastructure rather than applying "
                "a per-generation repair.\n\n"
                + yaml.safe_dump(update_plan, sort_keys=False)
            )
        if update_plan.get("verdict") != "generation_bug":
            raise RuntimeError(
                "TB diagnosis did not produce a generation_bug "
                "repair plan.\n\n"
                + yaml.safe_dump(update_plan, sort_keys=False)
            )

        # -------------------------------
        # Repair LLM: plan -> TB changes
        # -------------------------------
        print(
            f"\nRepairing generated TB "
            f"(attempt {tb_attempt + 1}/"
            f"{MAX_TB_REPAIR_ATTEMPTS})..."
        )
        repair_workspace = HOST_WORKSPACE / "generated" / "llm_tb_repair_workspace"
        repair_report = {
            "source": "tb_validation",
            "result": final_analysis,
            "repair_plan": update_plan,
            "rtl_exposed_to_llm": False,
        }
        prepare_sanitized_workspace(
            repair_workspace,
            HOST_WORKSPACE / SPEC,
            HOST_WORKSPACE / REF_MODEL,
            HOST_WORKSPACE / PLAN,
            tb_dir,
            repair_report,
        )
        shutil.copy2(update_plan_path, repair_workspace / "tb_update_plan.yaml")
        repair_llm, repair_bash = create_improvement_agent(str(repair_workspace))
        try:
            repair_response = get(
                repair_llm.prompt.chia_remote(
                    repair_llm,
                    build_repair_prompt(
                        str(repair_workspace / "tb_update_plan.yaml"),
                        str(repair_workspace),
                    ),
                    tools=[repair_bash],
                )
            )
        finally:
            repair_bash.stop()
        if not repair_response.success:
            raise RuntimeError(
                "TB repair LLM failed:\n"
                f"{repair_response.stderr}"
            )

        changed = collect_tb_changes(repair_workspace / "tb", tb_dir)
        if not changed:
            raise RuntimeError("TB repair LLM completed without modifying the generated TB.")

        # Ensure the manifest remains usable after a repair.
        ensure_simulation_manifest(str(tb_dir))
        print(repair_response.result.strip())

    raise RuntimeError(
        "TB validation loop ended unexpectedly: "
        + json.dumps(final_analysis, indent=2)
    )



# =========================================================
# Stages 6-9: metric-driven RTL-blind verification improvement
# =========================================================

def run_verification_improvement_loop(llm_unused, bash_unused, canonical_plan):
    """Iteratively improve the existing TB using only weakness evidence.

    The simulation worker sees RTL. The improvement LLM receives a sanitized
    copy containing no RTL, no rtl_info, and no simulator build artifacts.
    Candidate changes are applied only after the post-change regression is
    objectively at least as good and has no new test-health regressions.
    """
    tb_dir = HOST_WORKSPACE / "generated_tb"
    plan_path = HOST_WORKSPACE / PLAN
    improvement_root = HOST_WORKSPACE / "generated" / "llm_improvement_workspace"
    reports_dir = HOST_WORKSPACE / "generated" / "results" / "verification_improvement"
    reports_dir.mkdir(parents=True, exist_ok=True)
    snapshots = HOST_WORKSPACE / "generated" / "tb_iterations"
    snapshots.mkdir(parents=True, exist_ok=True)

    if is_stage_done("verification_improvement_complete"):
        print("\n✓ Verification-improvement loop already completed.")
        return

    previous_report = None
    # First measurement uses the already-validated generated TB.
    baseline_result_rel = "generated/results/verification_improvement_baseline.json"
    baseline = get(simulate.chia_remote(
        RTL, "generated_tb", baseline_result_rel,
        SIM_TEST_TIMEOUT, SIM_BUILD_TIMEOUT,
    ))
    baseline_path = HOST_WORKSPACE / baseline_result_rel
    report = analyze_verification_state(plan_path, tb_dir, baseline_path, 0, None)
    (reports_dir / "iteration_0.yaml").write_text(yaml.safe_dump(report, sort_keys=False))
    previous_report = report
    print("\n===== VERIFICATION BASELINE =====")
    print(yaml.safe_dump(report, sort_keys=False))

    for iteration in range(1, MAX_IMPROVEMENT_ITERATIONS + 1):
        if not report.get("weaknesses"):
            print("\n✓ No actionable weaknesses remain.")
            break

        # Snapshot the accepted TB before giving a copy to the LLM.
        snapshot = snapshots / f"iteration_{iteration-1:02d}"
        if snapshot.exists():
            shutil.rmtree(snapshot)
        shutil.copytree(tb_dir, snapshot, ignore=shutil.ignore_patterns(".chia_sim", "__pycache__", "*.so"))

        prepare_sanitized_workspace(
            improvement_root,
            HOST_WORKSPACE / SPEC,
            HOST_WORKSPACE / REF_MODEL,
            plan_path,
            tb_dir,
            report,
        )
        llm, bash = create_improvement_agent(str(improvement_root))
        try:
            response = get(llm.prompt.chia_remote(
                llm,
                build_improvement_prompt(improvement_root),
                tools=[bash],
            ))
            if not response.success:
                raise RuntimeError(f"Verification improvement LLM failed:\n{response.stderr}")
            changed = collect_tb_changes(improvement_root / "tb", tb_dir)
        finally:
            bash.stop()

        if not changed:
            print(f"\n✓ Improvement iteration {iteration}: LLM made no changes; stopping.")
            break

        ensure_simulation_manifest(str(tb_dir))
        candidate_result_rel = f"generated/results/verification_improvement_candidate_{iteration}.json"
        get(simulate.chia_remote(
            RTL, "generated_tb", candidate_result_rel,
            SIM_TEST_TIMEOUT, SIM_BUILD_TIMEOUT,
        ))
        candidate_path = HOST_WORKSPACE / candidate_result_rel
        candidate_report = analyze_verification_state(
            plan_path, tb_dir, candidate_path, iteration, previous_report
        )
        candidate_report["changed_files"] = changed
        (reports_dir / f"iteration_{iteration}.yaml").write_text(
            yaml.safe_dump(candidate_report, sort_keys=False)
        )

        old_score = float(previous_report.get("quality_score", 0.0))
        new_score = float(candidate_report.get("quality_score", 0.0))
        old_failed = int(previous_report.get("metrics", {}).get("tests_failed", 0))
        new_failed = int(candidate_report.get("metrics", {}).get("tests_failed", 0))
        accepted = new_score >= old_score and new_failed <= old_failed
        candidate_report["accepted"] = accepted

        if accepted:
            previous_report = candidate_report
            report = candidate_report
            print(f"\n✓ Accepted TB improvement iteration {iteration}: {old_score:.2f} -> {new_score:.2f}")
        else:
            # Roll back the complete TB, not just files reported by the model.
            if tb_dir.exists():
                shutil.rmtree(tb_dir)
            shutil.copytree(snapshot, tb_dir)
            print(f"\n✗ Rejected TB improvement iteration {iteration}: {old_score:.2f} -> {new_score:.2f}")
            break

    mark_stage_done("verification_improvement_complete", detail={
        "iterations": iteration if 'iteration' in locals() else 0,
        "final_quality_score": previous_report.get("quality_score") if previous_report else None,
        "report_dir": str(reports_dir),
    })


# =========================================================

# Main CHIA orchestration

# =========================================================

def main():

    ray.init()

    try:

        plan_path = HOST_WORKSPACE / PLAN
        rtl_info_path = HOST_WORKSPACE / RTL_INFO
        candidate_path = HOST_WORKSPACE / CANDIDATE_PLAN

        # =================================================
        # Fast path: verification plan + rtl_info already exist.
        #
        # Skip RTL extraction, plan generation, and plan review
        # entirely and go straight to UVM environment generation
        # (Stage 4) and its closed-loop validation (Stage 5), which
        # in turn skip any of their own sub-stages that already have
        # a checkpoint from a previous run.
        # =================================================
        if plan_path.exists() and rtl_info_path.exists():

            print(
                "\n✓ Found existing verification plan and rtl_info.json "
                "— skipping extraction, generation, and review."
            )
            print(f"  Plan:     {plan_path}")
            print(f"  RTL info: {rtl_info_path}")

            canonical_plan = plan_path.read_text()

            # If Stage 4 already produced a complete TB, it is persistent
            # state and must never be regenerated just because run8.py was
            # invoked again. generate_and_validate_uvm() performs the same
            # guard as a second line of defense.
            if has_existing_generated_tb():
                print(
                    "\n✓ Existing generated_tb detected — resuming from "
                    "Stage 5+ without regenerating the environment."
                )

            llm, bash = create_agent()

            try:

                generate_and_validate_uvm(llm, bash, canonical_plan)

            finally:

                bash.stop()

            return

        # =================================================
        # No accepted plan yet. Resume as far into stages 1-3 as
        # existing artifacts allow, then fall through into stage 4/5
        # once a plan is accepted.
        # =================================================

        llm, bash = create_agent()

        try:

            # -------------------------------------------------
            # Stage 1: RTL extraction
            # -------------------------------------------------
            if rtl_info_path.exists():
                print(
                    "\n✓ Found existing rtl_info.json — skipping RTL "
                    f"extraction.\n  RTL info: {rtl_info_path}"
                )
            else:
                print("\n[1/4] Extracting RTL information...")

                rtl_info = get(

                    extract_rtl.chia_remote(

                        RTL,

                        RTL_INFO,

                    )

                )

                print(f"RTL information: {rtl_info}")

            # -------------------------------------------------
            # Stage 2: Generate (or resume) candidate plan
            # -------------------------------------------------
            if candidate_path.exists():

                print(
                    "\n✓ Found existing candidate verification plan — "
                    f"skipping generation and resuming at review.\n"
                    f"  Candidate: {candidate_path}"
                )

                candidate = ensure_valid_yaml(
                    llm,
                    candidate_path.read_text(),
                    "resumed candidate",
                    max_attempts=2,
                )

                candidate_path.write_text(candidate)

            else:

                print("\n[2/4] Generating verification plan...")

                raw_candidate = generate_candidate_plan(

                    llm,

                    bash,

                )

                candidate = ensure_valid_yaml(

                    llm,

                    raw_candidate,

                    "candidate generation",

                    max_attempts=2,

                )

                print("\n✓ Candidate verification plan generated.")

                candidate_path.parent.mkdir(

                    parents=True,

                    exist_ok=True,

                )

                candidate = clean_yaml_response(

                    candidate

                )

                candidate_path.write_text(

                    candidate

                )

                print(

                    f"✓ Candidate saved to: {candidate_path}"

                )

            # =================================================

            # Stage 3

            # Independent LLM review

            # =================================================

            repair_yaml_error = None

            for attempt in range(MAX_REPAIR_ATTEMPTS + 1):

                print(
                    f"\n[3/4] Reviewing verification plan "
                    f"(attempt {attempt + 1})..."
                )

                review = review_candidate_plan(
                    llm,
                    bash,
                    candidate,
                )

                if not review or not review.strip():
                    raise RuntimeError(
                        "Reviewer produced no usable response."
                    )

                print("\n===== REVIEW =====")
                print(review)

                status = parse_review_status(review)

                if status == "no_issues":

                    cleaned_candidate = ensure_valid_yaml(
                        llm,
                        candidate,
                        "final candidate",
                        max_attempts=2,
                    )

                    valid, parsed = validate_yaml(cleaned_candidate)

                    if not valid:
                        raise RuntimeError(
                            "Reviewer accepted the plan, but the "
                            f"candidate failed YAML validation:\n{parsed}"
                        )

                    # The LLM YAML is only an intermediate representation.
                    # Validate it against the canonical VerificationPlan
                    # before promoting it to the downstream artifact.
                    try:
                        accepted_plan = VerificationPlan.model_validate(parsed)
                    except Exception as exc:
                        raise RuntimeError(
                            "Reviewer accepted the plan, but it failed "
                            "canonical VerificationPlan validation:\n"
                            f"{exc}"
                        ) from exc

                    # Serialize the validated model, not the raw LLM YAML.
                    canonical_plan = yaml.safe_dump(
                        accepted_plan.model_dump(mode="json"),
                        sort_keys=False,
                        allow_unicode=True,
                    )

                    plan_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    plan_path.write_text(canonical_plan)

                    print("\n✓ Verification plan accepted.")
                    print(f"✓ Final canonical plan saved to: {plan_path}")

                    # =================================================
                    # Stage 4 + 5: Generate UVM environment directly
                    # from the accepted plan, then validate it. Any
                    # sub-stage already checkpointed from a previous
                    # run is skipped automatically.
                    # =================================================

                    generate_and_validate_uvm(llm, bash, canonical_plan)

                    return

                print("\n✗ Verification plan rejected.")

                if attempt >= MAX_REPAIR_ATTEMPTS:

                    raise RuntimeError(
                        "\nVerification plan failed independent "
                        "semantic review.\n\n"
                        "The candidate has NOT been promoted to "
                        "verification_plan.yaml.\n\n"
                        f"Candidate remains available at:\n"
                        f"{candidate_path}\n\n"
                        f"Final review:\n{review}"
                    )

                print("\nRepairing candidate plan...")
                print(
                    f"Repair attempt {attempt + 1}/"
                    f"{MAX_REPAIR_ATTEMPTS}..."
                )

                raw_repaired_candidate = repair_candidate_plan(
                    llm,
                    bash,
                    candidate,
                    review,
                    repair_yaml_error,
                )

                candidate = ensure_valid_yaml(
                    llm,
                    raw_repaired_candidate,
                    "semantic repair",
                    max_attempts=2,
                )

                repair_yaml_error = None

                candidate_path.write_text(candidate)

                print(
                    f"Updated candidate saved to: "
                    f"{candidate_path}"
                )

        finally:

            bash.stop()

    finally:

        ray.shutdown()



if __name__ == "__main__":

    main()