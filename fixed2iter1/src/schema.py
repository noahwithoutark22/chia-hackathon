"""Canonical, model-independent verification-plan contract."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DUT(BaseModel):
    name: str
    file: str = ""
    description: str = ""


class Parameter(BaseModel):
    name: str
    default: str | int | float | bool
    description: str = ""
    test_values: list[Any] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        self.default = str(self.default)

    @property
    def default_int(self) -> int | None:
        """Best-effort numeric resolution of the parameter default."""
        try:
            return int(self.default, 0)
        except (TypeError, ValueError):
            return None


class Clock(BaseModel):
    name: str
    type: str = "posedge"
    description: str = ""


class Reset(BaseModel):
    name: str
    polarity: Literal["active-low", "active-high"]
    type: Literal[
        "asynchronous",
        "synchronous",
        "asynchronous_assert_synchronous_deassert",
    ]
    description: str = ""
    reset_value: dict[str, Any] = Field(default_factory=dict)


class ClockAndReset(BaseModel):
    clock: Clock
    reset: Reset


class Port(BaseModel):
    """A DUT port.

    Direction is encoded structurally by Ports.inputs / outputs / inouts.
    """

    name: str
    width: int | str = 1
    description: str = ""
    type: str | None = None
    latency: str | int | None = None


class Ports(BaseModel):
    inputs: list[Port] = Field(default_factory=list)
    outputs: list[Port] = Field(default_factory=list)
    inouts: list[Port] = Field(default_factory=list)

    @property
    def all(self) -> list[Port]:
        return self.inputs + self.outputs + self.inouts

    @property
    def directions(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for p in self.inputs:
            out[p.name] = "input"
        for p in self.outputs:
            out[p.name] = "output"
        for p in self.inouts:
            out[p.name] = "inout"
        return out


class ReferenceModel(BaseModel):
    language: str
    file: str
    function: str = ""
    logic: str = ""
    latency: str | int | None = None


class FunctionalBehavior(BaseModel):
    description: str = ""
    reset_behavior: str = ""
    reference_model: ReferenceModel | None = None


class StimulusStep(BaseModel):
    """One deterministic, structured stimulus operation.

    `action` gives the generator a stable semantic handle. `signals` carries
    DUT signal/value assignments for drive/check-style operations. `cycles`
    is optional for operations such as reset or wait. A string step such as
    `reset` is accepted and normalized to `{"action": "reset"}` so older or
    simpler LLM plans remain compatible with the canonical schema.
    """

    action: str
    signals: dict[str, Any] = Field(default_factory=dict)
    cycles: int | None = None
    description: str = ""

    @classmethod
    def from_legacy_string(cls, value: str) -> "StimulusStep":
        return cls(action=value)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("stimulus step action must not be empty")
        return value


class StimulusSequence(BaseModel):
    sequence: list[StimulusStep] = Field(default_factory=list)

    @field_validator("sequence", mode="before")
    @classmethod
    def normalize_sequence(cls, value: Any) -> Any:
        """Preserve compatibility with simple LLM-generated action strings.

        Existing plans may contain:
            sequence:
              - reset

        Normalize that to a structured StimulusStep before normal Pydantic
        validation. Dictionary-based sequence entries continue to work.
        """
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("stimulus.sequence must be a list")

        normalized = []
        for step in value:
            if isinstance(step, str):
                normalized.append({"action": step})
            else:
                normalized.append(step)
        return normalized


class TestScenario(BaseModel):
    name: str
    description: str = ""
    priority: Literal["low", "medium", "high"] = "medium"
    stimulus: StimulusSequence | None = None
    expected: Any = None
    note: str = ""


class CornerCase(BaseModel):
    name: str
    description: str = ""
    expected: Any = None
    # Kept permissive for backward compatibility with existing plan fields.
    model_config = ConfigDict(extra="allow")


class RandomConstraint(BaseModel):
    variable: str
    range: list[Any] = Field(default_factory=list)


class ResetInjection(BaseModel):
    type: str
    frequency: str | None = None
    duration_cycles: list[int] | None = None
    description: str = ""


class RandomizedTestingStrategy(BaseModel):
    description: str = ""
    constraints: list[RandomConstraint] = Field(default_factory=list)
    injection: list[ResetInjection] = Field(default_factory=list)
    pass_criteria: str = ""


class CoverageBin(BaseModel):
    name: str
    range: list[Any] | None = None
    expression: str | None = None


class CoverageVariable(BaseModel):
    name: str
    variable: str
    bins: list[CoverageBin] = Field(default_factory=list)


class CoverageCross(BaseModel):
    name: str
    variables: list[str] = Field(default_factory=list)
    description: str = ""


class CoverageGroup(BaseModel):
    name: str
    description: str = ""
    clk: str | None = None
    sample_on: str | None = None
    bins: list[CoverageVariable] = Field(default_factory=list)
    crosses: list[CoverageCross] = Field(default_factory=list)


class FunctionalCoverage(BaseModel):
    covergroups: list[CoverageGroup] = Field(default_factory=list)


class ScoreboardArchitecture(BaseModel):
    type: str
    description: str = ""


class ScoreboardReferenceModelStrategy(BaseModel):
    description: str = ""
    architecture: list[ScoreboardArchitecture] = Field(default_factory=list)
    pass_criteria: str = ""
    error_reporting: str = ""


class AssertionSpec(BaseModel):
    name: str
    description: str = ""
    severity: str = "error"
    assertion: str = ""
    note: str = ""


class Discrepancy(BaseModel):
    id: str
    severity: str
    title: str
    rtl: str = ""
    spec: str = ""
    impact: str = ""
    recommendation: str = ""


class VerificationPlan(BaseModel):
    """Stable, DUT-generic contract consumed by the UVM generator."""

    dut: DUT
    parameters: list[Parameter] = Field(default_factory=list)
    clock_and_reset: ClockAndReset
    ports: Ports
    functional_behavior: FunctionalBehavior = Field(
        default_factory=FunctionalBehavior
    )
    directed_test_scenarios: list[TestScenario] = Field(default_factory=list)
    corner_cases: list[CornerCase] = Field(default_factory=list)
    randomized_testing_strategy: RandomizedTestingStrategy | None = None
    functional_coverage: FunctionalCoverage = Field(
        default_factory=FunctionalCoverage
    )
    scoreboard_reference_model_strategy: (
        ScoreboardReferenceModelStrategy | None
    ) = None
    useful_assertions: list[AssertionSpec] = Field(default_factory=list)
    discrepancies: list[Discrepancy] = Field(default_factory=list)

    @property
    def dut_name(self) -> str:
        return self.dut.name

    @property
    def description(self) -> str:
        return self.dut.description

    @property
    def clock_signal(self) -> str:
        return self.clock_and_reset.clock.name

    @property
    def reset_signal(self) -> str:
        return self.clock_and_reset.reset.name

    @property
    def reset_active_low(self) -> bool:
        return self.clock_and_reset.reset.polarity == "active-low"

    @property
    def reset_type(self) -> str:
        return self.clock_and_reset.reset.type

    @property
    def data_ports(self) -> list[Port]:
        return [
            p for p in self.ports.all
            if p.name not in {self.clock_signal, self.reset_signal}
        ]

    @property
    def input_ports(self) -> list[Port]:
        return [
            p for p in self.ports.inputs
            if p.name not in {self.clock_signal, self.reset_signal}
        ]

    @property
    def output_ports(self) -> list[Port]:
        return [
            p for p in self.ports.outputs
            if p.name not in {self.clock_signal, self.reset_signal}
        ]

    @property
    def port_directions(self) -> dict[str, str]:
        return self.ports.directions

    @property
    def parameter_defaults(self) -> dict[str, str]:
        return {p.name: p.default for p in self.parameters}

    def resolve_width(self, width: int | str) -> int | None:
        if isinstance(width, int):
            return width

        try:
            return int(width, 0)
        except (TypeError, ValueError):
            pass

        param = next(
            (p for p in self.parameters if p.name == width), None
        )
        if param is not None:
            return param.default_int

        return None

    @property
    def reference_model(self) -> ReferenceModel | None:
        return self.functional_behavior.reference_model

    @property
    def test_scenarios(self) -> list[TestScenario]:
        return self.directed_test_scenarios + [
            TestScenario(
                name=c.name,
                description=c.description,
                expected=c.expected,
            )
            for c in self.corner_cases
        ]

    @property
    def coverage_groups(self) -> list[CoverageGroup]:
        return self.functional_coverage.covergroups

    @property
    def scoreboard_strategy(self) -> str:
        if self.scoreboard_reference_model_strategy:
            return self.scoreboard_reference_model_strategy.description
        return (
            "Compare DUT outputs against the supplied reference model "
            "using the latency specified by the verification plan."
        )
