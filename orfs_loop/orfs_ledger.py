"""Measured knob-effect ledger for orfs_loop.py's closure loop.

This records what each configuration change *actually did* to the metrics,
accumulated across every run and every parallel slot, and renders it back
into the prompt. It is the loop's memory of its own experiments.

**This is not a decision-maker.** It never proposes a value, never picks a
knob, never gates a slot. That distinction matters: this project previously
had an `orfs_advisor.py` that computed moves from a fixed rule table, and it
was removed after a live trial showed it filling every batch slot itself for
five consecutive rounds with no LLM involvement and no ability to notice it
was bisecting a dead knob (see CLAUDE.md's "Parallel batches"). A ledger of
observations is the opposite thing: it hands the model *evidence* and lets
the model do the judging. Keep it that way -- if you ever find yourself
adding a `suggest_*` function here, that's the advisor growing back.

Two honesty rules the rendering depends on:

1. **Confounded moves are labelled, never averaged into a per-knob effect.**
   When a run changes two knobs at once, the resulting delta belongs to the
   combination, not to either knob. Silently attributing it to one would
   manufacture evidence that doesn't exist.
2. **CLOCK_PERIOD changes are flagged.** Relaxing the clock improves setup
   slack essentially by definition -- it moves the target rather than the
   design. Left unflagged, the ledger would read as "raising CLOCK_PERIOD
   reliably fixes timing", which is true and useless, and is exactly the
   trade the iteration objective exists to prevent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# Metrics tracked as deltas. Sign convention is raw (new - old); the renderer
# is what explains whether up or down is good for each one.
_METRIC_PATHS = {
    "setup_wns": ("violations", "setup_wns_slack"),
    "hold_wns": ("violations", "hold_wns_slack"),
    "setup_tns": ("violations", "setup_tns_slack"),
    "drc": ("violations", "drc_error_count"),
    "area": ("physical_metrics", "core_area"),
    "util": ("physical_metrics", "core_utilization_percent"),
}

# Moving this doesn't improve the design, it changes what "closed" means.
_TARGET_MOVING_KNOB = "CLOCK_PERIOD"


def new_ledger(design: Optional[str] = None) -> dict:
    return {"design": design, "observations": []}


def seed_from(path: str | Path, design: str) -> tuple:
    """Warm-start a ledger from a previous run's `ledger.json`.

    Returns (ledger, note). Refuses a ledger recorded for a *different*
    design and starts empty instead: a knob's measured effect is a property
    of one design on one platform at one baseline config, and importing
    another design's numbers would be worse than having none -- it would look
    like evidence.

    Same-design carryover is the point of the ledger existing on disk at all.
    Without it every run re-derives what it already paid flow-run minutes to
    learn; observed live, a fresh run's first round immediately re-proposed a
    knob a previous run had already measured as actively harmful.
    """
    prior = load(path)
    prior_design = prior.get("design")
    n = len(prior.get("observations") or [])
    if not n:
        return new_ledger(design), f"no usable observations in {path}"
    if prior_design and prior_design != design:
        return (new_ledger(design),
                f"ignored {path}: recorded for design {prior_design!r}, not {design!r}")
    prior["design"] = design
    for o in prior["observations"]:
        o["from_earlier_run"] = True
    return prior, f"seeded {n} observation(s) from {path}"


def _metric(entry: dict, group: str, key: str) -> Optional[float]:
    try:
        v = (entry.get(group) or {}).get(key)
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def observe(ledger: dict, baseline: Optional[dict], entry: dict) -> Optional[dict]:
    """Record one baseline -> entry transition.

    `baseline` is whatever this run was actually branched from: the previous
    run in serial mode, or the round's shared starting point for every slot
    of a batch round (which is what makes a batch round a controlled
    comparison rather than two unrelated samples).

    Returns the observation, or None when there's nothing measurable (no
    baseline, or no config change).
    """
    if baseline is None:
        return None
    changed = entry.get("tunables_changed") or {}
    if not changed:
        return None

    keys = sorted(changed)
    obs = {
        "run": entry.get("run"),
        "slot": entry.get("slot"),
        "iteration": entry.get("iteration"),
        "from_run": baseline.get("run"),
        "changed": changed,
        "keys": keys,
        # One knob moved -> the delta is attributable to it. More than one ->
        # it belongs to the combination and must not be split (see module
        # docstring, honesty rule 1).
        "confounded": len(keys) > 1,
        "moves_target": _TARGET_MOVING_KNOB in keys,
        "crashed": bool(entry.get("crashed")),
        "closed": (not entry.get("crashed")
                   and str(entry.get("status", "")).startswith("CLOSED")),
    }
    if entry.get("crashed"):
        obs["crashed_stage"] = entry.get("stage")
    else:
        for name, (group, key) in _METRIC_PATHS.items():
            before, after = _metric(baseline, group, key), _metric(entry, group, key)
            if before is not None and after is not None:
                obs[f"d_{name}"] = round(after - before, 6)
    ledger["observations"].append(obs)
    return obs


def observe_round(ledger: dict, baseline: Optional[dict], entries: list) -> None:
    """Record a whole batch round against its shared starting point."""
    for e in entries:
        observe(ledger, baseline, e)


def _fmt_change(changed: dict) -> str:
    bits = []
    for k, v in changed.items():
        if isinstance(v, dict):
            f, t = v.get("from"), v.get("to")
            bits.append(f"{k} {'baseline' if f is None else f}->{'baseline' if t is None else t}")
        else:
            bits.append(f"{k}={v}")
    return ", ".join(bits)


def _knob_step(obs: dict) -> Optional[float]:
    """Magnitude of a single-knob numeric move, for normalising its effect.

    None for confounded moves (no single knob to attribute to) and for
    non-numeric knobs (enums/flags, where "per unit" is meaningless).
    """
    if obs.get("confounded"):
        return None
    spec = (obs.get("changed") or {}).get(obs["keys"][0])
    if not isinstance(spec, dict):
        return None
    try:
        f, t = float(spec.get("from")), float(spec.get("to"))
    except (TypeError, ValueError):
        return None
    step = abs(t - f)
    return step or None


def _fmt_deltas(obs: dict) -> str:
    if obs.get("crashed"):
        return f"CRASHED at {obs.get('crashed_stage') or 'unknown stage'}"
    bits = []
    for name, label in (("setup_wns", "setup_wns"), ("hold_wns", "hold_wns"),
                        ("drc", "drc"), ("area", "area"), ("util", "util")):
        d = obs.get(f"d_{name}")
        if d is None or d == 0:
            continue
        bits.append(f"{label} {d:+g}")
    if obs.get("closed"):
        bits.append("CLOSED")
    out = ", ".join(bits) or "no measurable change"

    # Raw deltas alone hide diminishing returns: a bigger step naturally
    # produces a bigger delta, so two steps of different sizes cannot be
    # compared by eye. Observed live -- CLOCK_PERIOD steps of 0.14 and 0.24
    # returned +0.284 and +0.307 WNS, which reads as "still returning" until
    # normalised, at which point the marginal rate has collapsed ~9x. Stating
    # the rate is what makes a flattening curve visible without the reader
    # doing arithmetic. Only meaningful WITHIN one knob; the units differ
    # between knobs, so these are not cross-knob comparable.
    step = _knob_step(obs)
    d_wns = obs.get("d_setup_wns")
    if step and d_wns:
        out += f"  [step {step:g}, so {d_wns / step:+.3g} setup_wns per unit]"
    return out


def render(ledger: dict, max_per_knob: int = 4, max_combos: int = 6) -> str:
    """Compact evidence digest for the prompt.

    Single-knob moves are grouped per knob so a trend is visible at a glance;
    multi-knob moves are listed separately and never folded into a knob's
    numbers.
    """
    obs = ledger.get("observations") or []
    if not obs:
        return "(nothing measured yet -- this is the first change of the run)"

    clean: dict = {}
    combos: list = []
    for o in obs:
        if o["confounded"]:
            combos.append(o)
        else:
            clean.setdefault(o["keys"][0], []).append(o)

    lines = []
    for knob in sorted(clean):
        entries = clean[knob][-max_per_knob:]
        total = len(clean[knob])
        head = f"{knob} ({total} single-knob move{'s' if total != 1 else ''} measured)"
        if knob == _TARGET_MOVING_KNOB:
            head += "  [relaxing this moves the timing target itself, it does not " \
                    "make the design faster -- weigh accordingly]"
        lines.append(head)
        for o in entries:
            run = f"run {o['run']}" + (f", slot {o['slot']}" if o.get("slot") is not None else "")
            # Flagged rather than silently merged: an earlier run's numbers are
            # real measurements on this design, but from a separate search that
            # may have started somewhere else, so they deserve slightly less
            # weight than something measured this run.
            if o.get("from_earlier_run"):
                run += ", earlier run"
            lines.append(f"  {_fmt_change(o['changed'])} ({run}): {_fmt_deltas(o)}")

    if combos:
        lines.append("")
        lines.append("Combined moves (two or more knobs at once -- the effect belongs to the "
                     "combination and cannot be split between them):")
        for o in combos[-max_combos:]:
            run = f"run {o['run']}" + (f", slot {o['slot']}" if o.get("slot") is not None else "")
            lines.append(f"  {_fmt_change(o['changed'])} ({run}): {_fmt_deltas(o)}")

    return "\n".join(lines)


def save(ledger: dict, path: str | Path) -> None:
    try:
        Path(path).write_text(json.dumps(ledger, indent=2))
    except OSError:
        # The ledger is an optimisation, never a correctness dependency --
        # a run must not die because its evidence file couldn't be written.
        pass


def load(path: str | Path) -> dict:
    try:
        d = json.loads(Path(path).read_text())
        if isinstance(d, dict) and isinstance(d.get("observations"), list):
            return d
    except (OSError, ValueError):
        pass
    return new_ledger()
