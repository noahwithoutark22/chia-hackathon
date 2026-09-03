import json, sys
sys.path.insert(0, "/workspace/uvm_generator")

spec_json = json.load(open("/workspace/tmp/adder_generation_spec.json"))

# Try importing the schema from the repo first; fall back to inline contract.
try:
    from uvm_generator.schemas.generation_schema import GenerationSpec
except Exception as e1:
    print("repo import failed:", e1)
    from pydantic import BaseModel, Field, ConfigDict, model_validator
    from typing import Literal

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
    class GenerationSpec(BaseModel):
        model_config = ConfigDict(extra="forbid")
        schema_version: str = "1.0"
        dut_name: str
        clock_signal: str
        reset_signal: str
        reset_active_low: bool
        transaction_inputs: list[SignalRef]
        transaction_outputs: list[SignalRef]
        driver: DriverSpec
        monitor: MonitorSpec
        scoreboard: ScoreboardSpec
        scenarios: list[ScenarioSpec]
        assertions: list[AssertionSpec] = Field(default_factory=list)
        coverage: list[CoverageSpec] = Field(default_factory=list)
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
            return self

m = GenerationSpec.model_validate(spec_json)
print("VALIDATION OK")
print("scenarios:", len(m.scenarios), "| assertions:", len(m.assertions), "| coverage:", len(m.coverage))
print("latency:", m.scoreboard.latency_cycles, "| ref fn:", m.scoreboard.reference_model.function)
print("ref args:", [(a.name, a.source, a.signal, a.value) for a in m.scoreboard.reference_model.arguments])
print("ref outputs:", [(o.signal, o.width) for o in m.scoreboard.reference_model.outputs])
