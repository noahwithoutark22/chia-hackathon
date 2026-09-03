"""
Golden reference model for examples/adder/adder.v.

This is intentionally plain Python — the LLM reads it as ground truth for
what "correct" means when it writes test_scenarios and scoreboard_strategy
in verification_plan.yaml. Wiring this into the *generated* SV scoreboard
(e.g. via DPI-C) is left as the TODO called out in
templates/scoreboard.sv.j2.
"""


def adder_ref(a: int, b: int, cin: int, width: int = 8) -> tuple[int, int]:
    """Returns (sum, cout) exactly as the RTL should on the next clock edge."""
    mask = (1 << width) - 1
    total = (a & mask) + (b & mask) + (cin & 1)
    sum_out = total & mask
    cout = (total >> width) & 1
    return sum_out, cout


if __name__ == "__main__":
    # Quick self-check
    assert adder_ref(0, 0, 0) == (0, 0)
    assert adder_ref(255, 1, 0, width=8) == (0, 1)
    assert adder_ref(0, 0, 1) == (1, 0)
    print("ref_model self-checks passed")
