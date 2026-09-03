from pathlib import Path
import json
import subprocess
import re

import ray

import yaml


from chia.base.ChiaFunction import ChiaFunction, get

from chia.base.tools.BashTool import BashTool

from chia.models.opencode import OpenCodeLLM

from pipeline.functions import extract_rtl, generate_uvm_in_worker, simulate, analyze_results
from pipeline.tb_feedback import ensure_simulation_manifest, build_diagnosis_prompt, build_repair_prompt
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

# Keep repair disabled until generation + review are stable.

MAX_REPAIR_ATTEMPTS = 2
MAX_TB_REPAIR_ATTEMPTS = 3
SIM_TEST_TIMEOUT = 60
SIM_BUILD_TIMEOUT = 1800



# =========================================================

# Helper: create OpenCode + Bash

# =========================================================

def create_agent():

    bash = BashTool(

        "verification_workspace",

        work_dir=CONTAINER_WORKSPACE,

        timeout_seconds=600,

        task_options={

            "resources": {"opencode_tools": 1}

        },

    )

    llm = OpenCodeLLM(

        model="opencode/big-pickle",

        work_dir=CONTAINER_WORKSPACE,

        timeout_seconds=600,

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

You are a senior SystemVerilog and UVM verification engineer.

Work in /workspace.

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

Generate a practical verification plan for a later UVM

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

# Main CHIA orchestration

# =========================================================


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


def main():

    ray.init()

    try:

        # =================================================

        # Stage 1

        # CHIA → RTL worker → Verible

        # =================================================

        print("\n[1/4] Extracting RTL information...")

        rtl_info = get(

            extract_rtl.chia_remote(

                RTL,

                RTL_INFO,

            )

        )

        print(f"RTL information: {rtl_info}")

        # =================================================

        # Stage 2

        # CHIA → OpenCode + Bash

        # =================================================

        print("\n[2/4] Generating verification plan...")

        llm, bash = create_agent()

        try:

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

            # Save candidate immediately.

            candidate_path = (

                HOST_WORKSPACE

                / "generated/plans/candidate_verification_plan.yaml"

            )

            candidate_path.parent.mkdir(

                parents=True,

                exist_ok=True,

            )

            candidate = clean_yaml_response(candidate)

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

                    plan_path = HOST_WORKSPACE / PLAN

                    plan_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    plan_path.write_text(canonical_plan)

                    print("\n✓ Verification plan accepted.")
                    print(f"✓ Final canonical plan saved to: {plan_path}")


                    # =================================================
                    # Stage 4: Generate UVM environment directly
                    #
                    # VerificationPlan is the sole structured planning
                    # artifact. There is no GenerationSpec contract.
                    # OpenCode receives the accepted plan together with
                    # the RTL, extracted RTL information, specification,
                    # reference model, capabilities, rules, and templates,
                    # and writes the UVM environment directly.
                    # =================================================

                    print("\n[4/4] Generating UVM environment...")

                    generation_prompt = f"""
You are the CHIA UVM environment generator.

Work in /workspace.

The accepted VerificationPlan below is the verification intent for the DUT.
Generate the complete UVM verification environment directly from this plan.

IMPORTANT:
- Do NOT create a GenerationSpec.
- Do NOT create another intermediate schema.
- Do NOT invent DUT ports, parameters, clocks, resets, widths, or behavior.
- The RTL is authoritative for implemented DUT structure and behavior.
- rtl_info.json is authoritative for extracted structural information.
- spec.md describes intended behavior.
- ref_model.py is the behavioral oracle for expected results.
- The VerificationPlan describes what the testbench must verify.
- Use the supplied UVM capabilities, rules, and templates.
- You may design implementation details needed to realize the plan, but they
  must remain consistent with the sources and plan.
- Generate actual SystemVerilog source files, not JSON describing them.
- Write all generated files under /workspace/generated_tb.
- Do not modify the RTL, specification, reference model, or generated plan.

## ACCEPTED VERIFICATION PLAN

{canonical_plan}

## SOURCE FILES

RTL:
{RTL}

RTL INFO:
{RTL_INFO}

SPECIFICATION:
{SPEC}

REFERENCE MODEL:
{REF_MODEL}

## UVM CAPABILITIES

{(HOST_WORKSPACE / "uvm_generator/capabilities.yaml").read_text()}

## UVM RULES

{(HOST_WORKSPACE / "uvm_generator/rules.yaml").read_text()}

## TEMPLATE LIBRARY

Inspect the available templates under:
 /workspace/templates

Use Bash to inspect ALL relevant source files and templates before generating.

## REQUIRED RESULT

Create a complete, compilable UVM environment under:

/workspace/generated_tb

The environment should implement the accepted plan, including where
applicable:

- interface
- sequence item / transaction
- sequences
- sequencer
- driver
- monitor
- agent
- scoreboard
- reference-model integration
- coverage
- assertions
- environment
- tests
- top-level testbench
- build/run configuration required by the available simulator flow

Preserve DUT parameterization from the RTL and plan, but do NOT parameterize
the generated interface type. The interface must render concrete signal widths
from the validated plan. This is required for the Verilator 5.042 flow.

VERILATOR/UVM COMPATIBILITY REQUIREMENTS (HARD):
- Target Verilator 5.042 + UVM 1800.2-2020.3.1.
- The simulator compiles UVM with +define+UVM_NO_DPI; do not depend on UVM DPI.
- The simulator uses --timing, a hard OS timeout, and a tb_top watchdog.
- Do NOT generate `virtual <dut>_if#(...)`. Declare virtual interfaces only as
  `virtual <dut>_if`.
- Do NOT specialize uvm_config_db with a parameterized virtual-interface type.
  Use `uvm_config_db#(virtual <dut>_if)` consistently for set/get.
- The concrete interface instance may be created normally; only the virtual
  interface/config_db type must be non-parameterized.
- Do not remove the watchdog, UVM_NO_DPI, --timing, or timeout wrapper to work
  around simulator behavior. These are fixed toolchain requirements.

MANDATORY SIMULATION MANIFEST:
Create/update /workspace/generated_tb/generation_manifest.yaml. It MUST
contain these additional fields:

top_module: <exact top module name>
top_file: <TB-relative .sv file containing that module>
compile_files:
  - <ordered .sv files that must be passed directly to Verilator>
test_classes:
  - <exact runtime test names accepted by +UVM_TESTNAME>

Do not list files in compile_files that are only reached through `include`.
The list must contain only files that should be passed directly to Verilator,
in valid compilation order. Include the generated reference-model package
SV file in that list when the scoreboard imports it. Do not put the Python
reference model or C++ adapter in compile_files.

After writing the files, inspect the generated files for obvious consistency
problems such as:
- undeclared signals
- wrong DUT port names
- wrong widths
- missing module/interface connections
- missing UVM component construction
- incorrect reset handling
- incorrect scoreboard latency
- incorrect reference-model invocation
- missing files referenced by other generated files

Do not return generated source code in your response. The generated files must
be written to /workspace/generated_tb.
Return a concise summary of the files created and any remaining concerns.
"""

                    response = get(
                        llm.prompt.chia_remote(
                            llm,
                            generation_prompt,
                            tools=[bash],
                        )
                    )

                    if not response.success:
                        raise RuntimeError(
                            "OpenCode UVM generation failed:\n"
                            f"{response.stderr}"
                        )

                    if not response.result or not response.result.strip():
                        raise RuntimeError(
                            "OpenCode UVM generation returned an empty response."
                        )

                    print("\n===== UVM GENERATION =====")
                    print(response.result.strip())

                    print(
                        "\n✓ UVM environment generated directly under "
                        "/workspace/generated_tb."
                    )

                    # =================================================
                    # Stage 5: Closed-loop generated-TB validation
                    # =================================================
                    # The generator owns verification intent. The simulator
                    # owns execution. The repair LLM is only allowed to make
                    # DUT/TB-specific changes after a structured diagnosis.
                    print("\n[5/5] Validating generated UVM environment...")

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
                            print("\n✓ Generated UVM environment passed simulation.")
                            return

                        if final_analysis["verdict"] == "template_bug":
                            raise RuntimeError(
                                "Template/toolchain defect detected. "
                                "Do not patch this generated TB with the LLM. "
                                "Fix the shared Verilator/UVM templates or "
                                "simulation infrastructure instead.\n\n"
                                + json.dumps(final_analysis["detail"], indent=2)
                            )

                        if tb_attempt >= MAX_TB_REPAIR_ATTEMPTS:
                            raise RuntimeError(
                                "Generated UVM environment still fails after "
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
                        diagnosis_prompt = build_diagnosis_prompt(
                            f"/workspace/{result_rel}", RTL, SPEC, REF_MODEL, PLAN
                        )
                        diagnosis_response = get(
                            llm.prompt.chia_remote(
                                llm, diagnosis_prompt, tools=[bash]
                            )
                        )
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
                        repair_response = get(
                            llm.prompt.chia_remote(
                                llm,
                                build_repair_prompt(str(update_plan_path)),
                                tools=[bash],
                            )
                        )
                        if not repair_response.success:
                            raise RuntimeError(
                                "TB repair LLM failed:\n"
                                f"{repair_response.stderr}"
                            )

                        # Ensure the manifest remains usable after a repair.
                        ensure_simulation_manifest(str(tb_dir))
                        print(repair_response.result.strip())

                    raise RuntimeError(
                        "TB validation loop ended unexpectedly: "
                        + json.dumps(final_analysis, indent=2)
                    )

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