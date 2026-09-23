"""The pre-extracted pyuvm API surface that generation prompts inline.

Lives in its own module because both `run14` (testbench generation) and
`tb_feedback` (repair) need it, and `run14` imports `tb_feedback` -- putting
the loader in either one would make that a cycle.

Regenerate `config/pyuvm_api_reference.md` with
`scripts/gen_pyuvm_api_reference.py` after any pyuvm upgrade; see
docs/TROUBLESHOOTING.md#12.
"""

from __future__ import annotations

import functools
from pathlib import Path

REFERENCE_FILE = (
    Path(__file__).resolve().parent.parent / "config" / "pyuvm_api_reference.md"
)

_HEADER = """
PYUVM API REFERENCE (authoritative for the pyuvm installed in the simulator
worker -- trust it over anything you remember, and do NOT spend tool calls
reading pyuvm's source to re-confirm it):
"""


@functools.lru_cache(maxsize=1)
def pyuvm_api_reference() -> str:
    """The reference block for a prompt, or "" if it has not been generated.

    Absence is not fatal: the agent falls back to reading the library at
    runtime, which is what it did before this existed. It is only slow.
    """
    try:
        text = REFERENCE_FILE.read_text().strip()
    except OSError:
        print(
            f"NOTE: {REFERENCE_FILE} is missing; generation prompts will omit "
            "the pyuvm API reference and the agent will re-derive it from "
            "library source (slow). Regenerate with "
            "scripts/gen_pyuvm_api_reference.py."
        )
        return ""
    return f"\n{_HEADER.strip()}\n\n{text}\n"
