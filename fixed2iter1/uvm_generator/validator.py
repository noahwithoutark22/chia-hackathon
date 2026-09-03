from __future__ import annotations

import re
from pathlib import Path

from src.schema import VerificationPlan
from .generation_schema import GenerationSpec

_SVA_KEYWORDS = {
    "posedge", "negedge", "edge", "and", "or", "not", "iff", "if", "else",
    "until", "until_with", "s_until", "s_until_with", "throughout", "within",
    "intersect", "first_match", "always", "s_always", "eventually",
    "s_eventually", "nexttime", "s_nexttime", "disable", "true", "false",
    "isunknown", "stable", "rose", "fell", "past", "countones", "onehot",
    "onehot0", "assertfailed", "sampled", "changed",
}

def _tokens(expr: str) -> list[str]:
    expr = re.sub(r"\$[A-Za-z_][A-Za-z0-9_]*", "", expr)
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr)

def _resolve_worker_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    return (Path("/workspace") / p).resolve()

def validate_generation_spec(
    spec: GenerationSpec,
    plan: VerificationPlan,
    rtl_path: str,
    ref_model_path: str,
) -> None:
    if spec.dut_name != plan.dut_name:
        raise ValueError(
            f"Generation DUT {spec.dut_name!r} != plan DUT {plan.dut_name!r}"
        )
    if spec.clock_signal != plan.clock_signal or spec.reset_signal != plan.reset_signal:
        raise ValueError("Generation clock/reset does not match verification plan")
    if spec.reset_active_low != plan.reset_active_low:
        raise ValueError("Generation reset_active_low does not match verification plan")
    if spec.reset_type != plan.reset_type:
        raise ValueError(
            f"Generation reset_type {spec.reset_type!r} != plan reset type {plan.reset_type!r}"
        )

    actual = {p.name: p for p in plan.ports.all}
    structural = {plan.clock_signal, plan.reset_signal}
    directions = plan.port_directions

    for signal in spec.transaction_inputs + spec.transaction_outputs:
        if signal.signal not in actual:
            raise ValueError(f"Unknown DUT signal in generation spec: {signal.signal}")
        if signal.signal in structural:
            raise ValueError(f"Clock/reset cannot be a transaction field: {signal.signal}")

        expected_width = plan.resolve_width(actual[signal.signal].width)
        if expected_width is None:
            raise ValueError(
                f"Cannot resolve width for {signal.signal}: "
                f"{actual[signal.signal].width!r} is not a literal width or a "
                "known parameter with a numeric default"
            )
        if signal.width != expected_width:
            raise ValueError(
                f"Width mismatch for {signal.signal}: {signal.width} != "
                f"{expected_width} (plan width: {actual[signal.signal].width!r})"
            )

    for signal in spec.driver.inputs:
        if signal.signal not in actual:
            raise ValueError(f"Driver references unknown DUT signal: {signal.signal}")
        if directions.get(signal.signal) not in ("input", "inout"):
            raise ValueError(f"Driver cannot drive DUT output: {signal.signal}")

    for signal in spec.monitor.outputs:
        if signal.signal not in actual:
            raise ValueError(f"Monitor references unknown DUT signal: {signal.signal}")
        if directions.get(signal.signal) not in ("output", "inout"):
            raise ValueError(f"Monitor cannot observe non-output: {signal.signal}")

    for name in spec.scoreboard.input_signals:
        if name not in actual:
            raise ValueError(f"Scoreboard references unknown DUT signal: {name}")
        if directions.get(name) not in ("input", "inout"):
            raise ValueError(f"Scoreboard input is not a DUT input: {name}")

    for name in spec.scoreboard.output_signals:
        if name not in actual:
            raise ValueError(f"Scoreboard references unknown DUT signal: {name}")
        if directions.get(name) not in ("output", "inout"):
            raise ValueError(f"Scoreboard output is not a DUT output: {name}")

    plan_latencies = set()
    if plan.reference_model and isinstance(plan.reference_model.latency, int):
        plan_latencies.add(plan.reference_model.latency)

    for name in spec.scoreboard.output_signals:
        port_latency = actual[name].latency
        if isinstance(port_latency, int):
            plan_latencies.add(port_latency)

    if plan_latencies and len(plan_latencies) == 1:
        expected_latency = next(iter(plan_latencies))
        if spec.scoreboard.latency_cycles != expected_latency:
            raise ValueError(
                "Generation scoreboard.latency_cycles "
                f"({spec.scoreboard.latency_cycles}) does not match the "
                f"latency stated in the verification plan ({expected_latency})"
            )
    elif len(plan_latencies) > 1:
        raise ValueError(
            "Verification plan states inconsistent latencies across "
            f"reference model / output ports: {sorted(plan_latencies)}"
        )

    rtl = _resolve_worker_path(rtl_path)
    ref_model = _resolve_worker_path(ref_model_path)

    if not rtl.exists():
        raise ValueError(f"RTL does not exist: {rtl}")
    if not ref_model.exists():
        raise ValueError(f"Reference model does not exist: {ref_model}")

    rm = spec.scoreboard.reference_model
    supplied_ref_model = _resolve_worker_path(ref_model_path)
    generated_ref_model = _resolve_worker_path(rm.path)

    if generated_ref_model != supplied_ref_model:
        raise ValueError(
            "Generation spec reference-model path must resolve to the "
            "supplied reference model: "
            f"{generated_ref_model} != {supplied_ref_model}"
        )

    if not rm.function.isidentifier():
        raise ValueError(
            "Reference model function must be a Python identifier: "
            f"{rm.function}"
        )

    for argument in rm.arguments:
        if argument.source == "transaction" and argument.signal not in spec.scoreboard.input_signals:
            raise ValueError(
                f"Reference argument {argument.signal} is not a scoreboard input"
            )

    for output in rm.outputs:
        if output.signal not in spec.scoreboard.output_signals:
            raise ValueError(
                f"Reference output {output.signal} is not scoreboard output"
            )

    parameter_names = {parameter.name for parameter in plan.parameters}

    for assertion in spec.assertions:
        for token in _tokens(assertion.property):
            if (
                token in actual
                or token in structural
                or token in parameter_names
                or token in _SVA_KEYWORDS
            ):
                continue
            raise ValueError(
                f"Assertion {assertion.name!r} references unknown identifier "
                f"{token!r} (not a DUT signal, parameter, or recognized SVA keyword)"
            )

    for coverage in spec.coverage:
        if coverage.signal not in actual and coverage.signal not in parameter_names:
            raise ValueError(
                f"Coverage references unknown signal: {coverage.signal}"
            )
