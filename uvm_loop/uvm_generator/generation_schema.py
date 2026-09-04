from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

class SignalRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signal: str
    width: int = Field(1, ge=1, le=64)

class ReferenceArgument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    source: Literal["transaction", "constant"]
    signal: str | None = None
    value: int | None = None

    @model_validator(mode="after")
    def valid_source(self):
        if self.source == "transaction" and not self.signal:
            raise ValueError("transaction reference argument requires signal")
        if self.source == "constant" and self.value is None:
            raise ValueError("constant reference argument requires value")
        return self

class ReferenceModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    function: str
    arguments: list[ReferenceArgument]
    outputs: list[SignalRef] = Field(min_length=1, max_length=2)
    integration: Literal["embedded_python_dpi_c"] = "embedded_python_dpi_c"

class DriverSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample_event: str = "posedge"
    drive_before_edge: bool = True
    inputs: list[SignalRef]

class MonitorSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample_event: str = "posedge"
    outputs: list[SignalRef]
    inputs: list[SignalRef] = Field(default_factory=list)

class ScoreboardSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    latency_cycles: int = Field(0, ge=0, le=64)
    input_signals: list[str]
    output_signals: list[str]
    reference_model: ReferenceModelSpec

class ScenarioSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    directed: bool
    repeat: int = Field(1, ge=1, le=100000)
    constraints: list[str] = Field(default_factory=list)
    values: dict[str, int | str] = Field(default_factory=dict)

class AssertionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    property: str
    severity: Literal["info", "warning", "error", "fatal"] = "error"

class CoverageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    signal: str
    bins: list[dict[str, str]]

class CoverageCrossSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    # Names of CoverageSpec entries (by CoverageSpec.name) being crossed,
    # not raw signal names -- a cross is a cross of coverpoints, and this
    # keeps the same one-hop reference discipline as the rest of the
    # schema (validator checks these resolve to real coverage entries).
    coverpoints: list[str] = Field(min_length=2)

class GenerationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.1"
    dut_name: str
    clock_signal: str
    reset_signal: str
    reset_active_low: bool
    # Carries the plan's reset timing semantics through to the concrete
    # config so the driver/monitor templates can generate a correct
    # reset waveform (e.g. assert asynchronously, deassert on a clock
    # edge) instead of assuming a single fixed reset style.
    reset_type: Literal[
        "asynchronous",
        "synchronous",
        "asynchronous_assert_synchronous_deassert",
    ] = "asynchronous"
    transaction_inputs: list[SignalRef]
    transaction_outputs: list[SignalRef]
    driver: DriverSpec
    monitor: MonitorSpec
    scoreboard: ScoreboardSpec
    scenarios: list[ScenarioSpec]
    assertions: list[AssertionSpec] = Field(default_factory=list)
    coverage: list[CoverageSpec] = Field(default_factory=list)
    coverage_crosses: list[CoverageCrossSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_and_consistent(self):
        ins = {x.signal for x in self.transaction_inputs}
        outs = {x.signal for x in self.transaction_outputs}
        if len(ins) != len(self.transaction_inputs) or len(outs) != len(self.transaction_outputs):
            raise ValueError("duplicate transaction signals")
        if {x.signal for x in self.driver.inputs} - ins:
            raise ValueError("driver inputs must be transaction inputs")
        if {x.signal for x in self.monitor.outputs} - outs:
            raise ValueError("monitor outputs must be transaction outputs")
        if set(self.scoreboard.input_signals) - ins:
            raise ValueError("scoreboard inputs must be transaction inputs")
        if set(self.scoreboard.output_signals) - outs:
            raise ValueError("scoreboard outputs must be transaction outputs")

        coverage_names = {c.name for c in self.coverage}
        if len(coverage_names) != len(self.coverage):
            raise ValueError("duplicate coverage entry names")
        for cross in self.coverage_crosses:
            unknown = set(cross.coverpoints) - coverage_names
            if unknown:
                raise ValueError(
                    f"coverage cross {cross.name!r} references unknown "
                    f"coverpoint(s): {sorted(unknown)}"
                )

        return self