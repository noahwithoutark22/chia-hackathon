"""
Lightweight, regex-based Verilog/SystemVerilog module header parser.

This is NOT a full HDL parser — it only extracts the module name, its
parameters, and its port list well enough to hand structured hints to the
LLM in plan_generator.py. It supports both ANSI-style port declarations
(`module foo #(param W=8)(input clk, output [W-1:0] y);`) and simple
non-ANSI headers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Port:
    name: str
    direction: str  # input | output | inout
    width: str = "1"  # e.g. "8" or "[7:0]" simplified to "8"


@dataclass
class Parameter:
    name: str
    default: str = ""


@dataclass
class RTLModule:
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    ports: list[Port] = field(default_factory=list)


_MODULE_RE = re.compile(
    r"module\s+(\w+)\s*(#\s*\((?P<params>.*?)\))?\s*\((?P<ports>.*?)\)\s*;",
    re.DOTALL,
)
_PARAM_RE = re.compile(r"parameter\s+(?:\w+\s+)?(\w+)\s*=\s*([^,]+)")
_PORT_RE = re.compile(
    r"(input|output|inout)\s+(?:reg|wire|logic)?\s*(\[\s*[^\]]+\s*\])?\s*(\w+)"
)


def _width_to_str(width_match: str | None) -> str:
    if not width_match:
        return "1"
    # normalize "[7:0]" -> "8", best-effort; falls back to raw text
    m = re.match(r"\[\s*(\d+)\s*:\s*0\s*\]", width_match)
    if m:
        return str(int(m.group(1)) + 1)
    return width_match.strip()


def parse_rtl_file(path: str) -> RTLModule:
    with open(path, "r") as f:
        text = f.read()

    # Strip line/block comments so they don't confuse the regexes.
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    m = _MODULE_RE.search(text)
    if not m:
        raise ValueError(f"Could not locate a `module ... ( ... );` header in {path}")

    name = m.group(1)
    mod = RTLModule(name=name)

    params_block = m.group("params") or ""
    for pm in _PARAM_RE.finditer(params_block):
        mod.parameters.append(Parameter(name=pm.group(1), default=pm.group(2).strip()))

    ports_block = m.group("ports") or ""
    for pm in _PORT_RE.finditer(ports_block):
        direction, width, pname = pm.groups()
        mod.ports.append(Port(name=pname, direction=direction, width=_width_to_str(width)))

    return mod


if __name__ == "__main__":
    import sys
    import json

    mod = parse_rtl_file(sys.argv[1])
    print(json.dumps(
        {
            "name": mod.name,
            "parameters": [p.__dict__ for p in mod.parameters],
            "ports": [p.__dict__ for p in mod.ports],
        },
        indent=2,
    ))
