from pathlib import Path
import json
import subprocess
import re

import ray

import yaml


from chia.base.ChiaFunction import ChiaFunction, get

from chia.base.tools.BashTool import BashTool

from chia.models.opencode import OpenCodeLLM

from pipeline.functions import extract_rtl



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

# =========================================================
# JSON boundary: clean + validate + repair
# =========================================================

def clean_json_response(text):
    """Clean common Markdown/explanatory wrappers around JSON."""
    if not text:
        return ""

    text = text.strip()

    # Prefer a fenced JSON block if present.
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # If the model added prose around a JSON object, extract the outermost
    # balanced object without trying to interpret or rewrite its contents.
    start = text.find("{")
    if start != -1:
        depth = 0
        in_string = False
        escape = False

        for i in range(start, len(text)):
            ch = text[i]

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1].strip()

    return text


def validate_json(text):
    """Python performs structural JSON validation before the artifact moves on."""
    text = clean_json_response(text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"Invalid JSON: {exc}"

    if not isinstance(parsed, dict):
        return False, "GenerationSpec must be a JSON object."

    return True, parsed


def ensure_valid_json(llm, text, context, max_attempts=2):
    """
    Every LLM-produced GenerationSpec JSON document passes through this
    boundary. Python validates first; a small dedicated LLM repair call is
    used only when the JSON is malformed.
    """

    candidate = clean_json_response(text)

    valid, parsed = validate_json(candidate)

    if valid:
        return candidate

    last_error = parsed

    for attempt in range(1, max_attempts + 1):
        print(f"\n⚠ Invalid JSON from {context}:")
        print(last_error)
        print(
            f"JSON syntax repair attempt "
            f"{attempt}/{max_attempts}..."
        )

        prompt = f"""
You are a JSON syntax repair tool.

Repair ONLY the JSON syntax and formatting of the document below.

Do NOT change its meaning.
Do NOT change values.
Do NOT add or remove GenerationSpec content.
Do NOT fix semantic verification errors.
Do NOT invent anything.

Parser error:

---BEGIN PARSER ERROR---
{last_error}
---END PARSER ERROR---

Malformed JSON:

---BEGIN MALFORMED JSON---
{candidate}
---END MALFORMED JSON---

Return ONLY the complete corrected JSON object.
Do NOT use Markdown fences.
Do NOT add explanations.
Do NOT add text before or after the JSON.
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
                f"OpenCode JSON repair failed for {context}:\n"
                f"{response.stderr}"
            )

        repaired = response.result

        if not repaired or not repaired.strip():
            raise RuntimeError(
                f"OpenCode JSON repair returned an empty response "
                f"for {context}."
            )

        candidate = clean_json_response(repaired)

        valid, parsed = validate_json(candidate)

        if valid:
            print(f"✓ JSON repaired successfully for {context}.")
            return candidate

        last_error = parsed

    raise RuntimeError(
        f"Unable to produce valid JSON for {context} after "
        f"{max_attempts} syntax-repair attempts.\n\n"
        f"Last JSON error:\n{last_error}"
    )


# =========================================================
# Stage 4 worker: run the containerized UVM generator
# =========================================================

@ChiaFunction(resources={"rtl_extract": 1})
def generate_uvm_in_worker(
    plan_path: str,
    generation_spec_path: str,
    rtl_path: str,
    spec_path: str,
    ref_model_path: str,
    out_dir: str,
) -> str:
    """Run validation + deterministic Jinja rendering in the RTL worker."""
    command = [
        "python3",
        "/opt/uvm-generator/scripts/generate_tb.py",
        "--plan", plan_path,
        "--generation-spec", generation_spec_path,
        "--rtl", rtl_path,
        "--spec", spec_path,
        "--ref-model", ref_model_path,
        "--out-dir", out_dir,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Containerized UVM generation failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    return result.stdout.strip() or f"Generated UVM environment at {out_dir}"


# =========================================================
# Stage 4: Generate GenerationSpec with existing OpenCode
# =========================================================

def generate_generation_spec(llm, bash, candidate):
    """Ask the existing CHIA OpenCodeLLM for a structured GenerationSpec."""

    generation_schema = (
        HOST_WORKSPACE / "uvm_generator/generation_schema.py"
    ).read_text()
    capabilities = (
        HOST_WORKSPACE / "uvm_generator/capabilities.yaml"
    ).read_text()
    rules = (
        HOST_WORKSPACE / "uvm_generator/rules.yaml"
    ).read_text()

    prompt = f"""
You are the CHIA UVM environment generation planner.

Work in /workspace.

Return ONLY one JSON object matching the GenerationSpec contract.
You are NOT generating SystemVerilog source code.

Never invent DUT ports, parameters, signals, clocks, resets,
reference-model functions, or algorithms.

The supplied Python reference model is the behavioral oracle.
Use ONLY the capabilities and rules supplied below.

## GENERATION SCHEMA
{generation_schema}

## CAPABILITIES
{capabilities}

## RULES
{rules}

## ACCEPTED VERIFICATION PLAN
{candidate}

Use Bash to inspect ALL FOUR source files before answering:
1. {RTL}
2. {RTL_INFO}
3. {SPEC}
4. {REF_MODEL}

Preserve the plan's DUT facts.

Explicitly map driver inputs, monitor outputs, scoreboard
inputs/outputs, reference-model arguments/returns, clock/reset
semantics, and input-to-output latency.

Use concrete scenario values only when supported by the plan/source
evidence; otherwise use constraints.

Do not duplicate the reference-model algorithm.
Do not write SystemVerilog.
Do not use unsupported capabilities.

Return ONLY valid JSON.
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
            "OpenCode GenerationSpec generation failed:\n"
            f"{response.stderr}"
        )

    result = response.result
    if not result or not result.strip():
        raise RuntimeError("OpenCode returned an empty GenerationSpec.")

    raw = ensure_valid_json(
        llm,
        result,
        "GenerationSpec generation",
        max_attempts=2,
    )

    parsed = json.loads(raw)

    generation_spec_path = (
        HOST_WORKSPACE / "generated/plans/generation_spec.json"
    )
    generation_spec_path.parent.mkdir(parents=True, exist_ok=True)
    generation_spec_path.write_text(json.dumps(parsed, indent=2))

    return generation_spec_path


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

    prompt = f"""

You are a senior SystemVerilog and UVM verification engineer.

Work in /workspace.

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

OUTPUT:
Return ONLY the complete YAML document.
Do NOT use Markdown fences.
Do NOT explain the changes.
Do NOT add text before or after YAML.
Do NOT modify or create files.
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

        print("\n[1/3] Extracting RTL information...")

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

        print("\n[2/3] Generating verification plan...")

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
                    f"\n[3/3] Reviewing verification plan "
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

                    plan_path = HOST_WORKSPACE / PLAN

                    plan_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    plan_path.write_text(cleaned_candidate)

                    print("\n✓ Verification plan accepted.")
                    print(f"✓ Final plan saved to: {plan_path}")


                    # =================================================
                    # Stage 4: Generate UVM environment
                    # OpenCode creates GenerationSpec; the RTL worker
                    # validates it and performs deterministic rendering.

                    print("\n[4/4] Generating UVM environment...")

                    generation_spec_path = generate_generation_spec(
                        llm,
                        bash,
                        cleaned_candidate,
                    )

                    print(
                        "✓ GenerationSpec saved to: "
                        f"{generation_spec_path}"
                    )

                    generation_result = get(
                        generate_uvm_in_worker.chia_remote(
                            "/workspace/generated/plans/"
                            "verification_plan.yaml",
                            "/workspace/generated/plans/"
                            "generation_spec.json",
                            f"/workspace/{RTL}",
                            f"/workspace/{SPEC}",
                            f"/workspace/{REF_MODEL}",
                            "/workspace/generated_tb",
                        )
                    )

                    print(generation_result)

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