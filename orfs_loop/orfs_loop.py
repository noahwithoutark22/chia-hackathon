from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import ray

import orfs_ledger
from chia.base.ChiaFunction import get
from chia.models.opencode import OpenCodeLLM
from orfs_config_bridge import load_schema, validate_tunables
from orfs_tool import (
    _apply_locked_tunables_remote,
    _prep_working_config_remote,
    _read_baseline_clock_period_remote,
    _diff_tunables,
    _read_baseline_floorplan_remote,
    _violation_score,
    apply_tunables_remote,
    read_tunables_remote,
    run_flow_remote,
    run_signoff_remote,
)

DEFAULT_FLOW_DIR = "/root/OpenROAD-flow-scripts/flow"
REPO_ROOT = Path(__file__).parent.resolve()
DEFAULT_SCHEMA_PATH = str(REPO_ROOT / "orfs_tunables_schema.json")
MINIMAL_SCHEMA_PATH = str(REPO_ROOT / "orfs_tunables_schema_minimal.json")
DEFAULT_PROMPT_PATH = str(REPO_ROOT / "prompts" / "orfs_propose.md")
DEFAULT_DIAGNOSE_PROMPT_PATH = str(REPO_ROOT / "prompts" / "orfs_diagnose.md")
DEFAULT_REFEREE_PROMPT_PATH = str(REPO_ROOT / "prompts" / "orfs_referee.md")
# How many consecutive REGRESSED/UNCHANGED runs (see _detect_stall below)
# trigger a stall-diagnosis turn, and how many further stalled runs must pass
# before diagnosing again -- without the second number a stall that never
# resolves would pay for a diagnosis turn on every single run from then on.
STALL_THRESHOLD = 3
STALL_REDIAGNOSE_EVERY = 3
DEFAULT_LD_LIBRARY_PATH = "/opt/miniconda/lib"
# The whole repo is bind-mounted here inside the orfs_run worker container
# (see cluster.yaml) -- used to translate a host-side run_dir under the repo
# into the path the worker needs to write run artifacts to the same place.
CONTAINER_REPO_ROOT = "/root/chia-orfs"

def _container_run_dir(run_dir: Path) -> Optional[str]:
    run_dir = run_dir.resolve()
    try:
        rel = run_dir.relative_to(REPO_ROOT)
    except ValueError:
        return None
    return f"{CONTAINER_REPO_ROOT}/{rel.as_posix()}"

def _format_locked_tunables(locked_tunables: dict) -> str:
    if not locked_tunables:
        return "(none -- all tunables in the schema are yours to adjust)"
    return "\n".join(f"- `{key}` is fixed at `{value}`." for key, value in sorted(locked_tunables.items()))

OBJECTIVES = ("clock", "area")

def _iteration_goal_text(iteration: int, objective: str, target: Optional[float]) -> str:
    """What this iteration is for, in the model's own terms.

    Iteration 1 is always "close it", but NOT "close it at any cost" -- an
    earlier version said area/clock don't count at all in iteration 1, and in
    practice that meant the model's first fix for a stubborn violation was a
    single jump like CORE_UTILIZATION 38 -> 20, nearly doubling the die to
    force closure. Closure still matters most, but every iteration (including
    the first) expects moderate, staged moves on the physical/timing target
    knobs -- see the prompt's own STRATEGY section for the actual step-size
    rule. Every iteration after the first takes the closed design from the one
    before and pushes a single user-chosen figure of merit -- faster clock or
    smaller area -- then has to close again; that staging matters, since
    asking for speed/area before anything closes just produces an aggressive
    config that never converges.
    """
    if iteration == 1:
        return (
            "**CLOSE THE DESIGN.** Get setup slack >= 0, hold slack >= 0 and zero DRC "
            "violations. Closure is the priority -- but a closed design that ballooned "
            "the area or gave back most of the clock speed to get there is not a good "
            "result either. Reach for the free repair knobs first (flags, margins -- see "
            "STRATEGY below); if you do need to relax `CORE_UTILIZATION`/`PLACE_DENSITY` or "
            "loosen `CLOCK_PERIOD`, move them moderately, in the small steps STRATEGY "
            "describes, not straight to an extreme value. You should rarely need to give up "
            "more than a modest fraction of either just to get a first closure.\n\n"
            "This iteration ends the moment a run comes back CLOSED."
        )
    if objective == "clock":
        return (
            f"**MAKE THE CLOCK FASTER.** The design already closes at "
            f"`CLOCK_PERIOD = {target}`. Lower it (shorter period = higher frequency) and "
            f"get the design closed again at the new, tighter target.\n\n"
            f"This iteration ends only when a run is CLOSED **and** `CLOCK_PERIOD < {target}`.\n\n"
            "Lower CLOCK_PERIOD in one of the moderate steps described in STRATEGY, then "
            "use the timing-repair knobs (`ENABLE_PLACE_REPAIR_TIMING`, `OPT_POST_GRT_WNS`, "
            "`SKIP_LAST_GASP`, `SETUP_SLACK_MARGIN`) to close at it -- those are free, reach "
            "for them before relaxing area back. If a step won't close, ease off toward the "
            "value that did rather than trying a bigger cut."
        )
    return (
        f"**MAKE THE DESIGN SMALLER.** It already closes at `core_area = {target}`. "
        f"Shrink it and get it closed again.\n\n"
        f"This iteration ends only when a run is CLOSED **and** `core_area < {target}`.\n\n"
        "Raise `CORE_UTILIZATION` (and `PLACE_DENSITY`) in the moderate steps STRATEGY "
        "describes to pack the same logic into less area; if `DIE_AREA_SCALE` is in your "
        "schema, shrinking it moderately is the most direct lever. Expect timing to get "
        "harder as you tighten -- lean on the free repair knobs to hold closure rather than "
        "giving the area back."
    )


def objective_value(entry: dict, objective: str) -> Optional[float]:
    """The figure of merit being optimized. Both are lower-is-better: a
    shorter clock period means a faster clock, a smaller core area means a
    smaller die."""
    if objective == "clock":
        return entry.get("clock_period")
    return (entry.get("physical_metrics") or {}).get("core_area")


def iteration_done(iteration: int, entry: dict, objective: str,
                   target: Optional[float]) -> bool:
    """Whether this run ends its iteration.

    Always requires a CLOSED design. From iteration 2 on it must ALSO beat the
    target carried over from the previous iteration -- closing again at the
    same speed or size is not progress, it is just the previous answer
    re-derived, and accepting it would let the loop spin forever without
    improving anything.
    """
    if not str(entry.get("status", "")).startswith("CLOSED"):
        return False
    if iteration == 1 or target is None:
        return True
    value = objective_value(entry, objective)
    return value is not None and value < target - 1e-9


def _load_prompt(
    prompt_path: str,
    design_name: str,
    closure_criteria: str,
    locked_tunables: Optional[dict],
    schema: dict,
    current_tunables: dict,
    latest_result: dict,
    history: list,
    iteration_goal: str = "",
) -> str:
    """Render one turn's prompt. Everything the model needs is substituted in
    as text -- it has no tools and cannot look anything up itself."""
    template = Path(prompt_path).read_text()
    return (
        template
        .replace("$DESIGN_NAME", design_name)
        .replace("$ITERATION_GOAL", iteration_goal)
        .replace("$CLOSURE_CRITERIA", closure_criteria)
        .replace("$LOCKED_TUNABLES", _format_locked_tunables(locked_tunables or {}))
        .replace("$SCHEMA", json.dumps(schema, indent=2))
        .replace("$CURRENT_TUNABLES", json.dumps(current_tunables, indent=2))
        .replace("$LATEST_RESULT", json.dumps(latest_result, indent=2))
        .replace("$HISTORY", json.dumps(history, indent=2) if history else "(no previous runs)")
    )


def _load_diagnose_prompt(prompt_path: str, design_name: str, stall_history: list, raw_excerpt: str) -> str:
    template = Path(prompt_path).read_text()
    return (
        template
        .replace("$DESIGN_NAME", design_name)
        .replace("$STALL_HISTORY", json.dumps(stall_history, indent=2))
        .replace("$RAW_LOG_EXCERPT", raw_excerpt or "(nothing beyond the metrics above)")
    )


def _objective_note(objective: str) -> str:
    """How the referee should weigh a CLOCK_PERIOD relaxation.

    This depends entirely on what's being optimised, and getting it wrong in
    either direction is costly. Under `clock`, relaxing the period improves
    setup slack by definition while destroying the objective itself. Under
    `area` it costs the objective nothing and is the cheapest route to
    closure -- and an objective-blind "never relax the clock" rule actively
    steers the loop into buying slack with die area instead. Observed live:
    a gcd run under --objective area spent 33% extra die area across nine
    runs without once trying the clock, while the referee's knob audit never
    even mentioned it.
    """
    if objective == "clock":
        return ("The objective is CLOCK SPEED. A change that improved setup slack **by "
                "relaxing `CLOCK_PERIOD`** did not make the design better -- it moved the "
                "goalposts, and it moved them away from the very thing being optimised. "
                "Judge such a win as no win at all, and say so.")
    return ("The objective is AREA. Relaxing `CLOCK_PERIOD` costs nothing against that "
            "objective, so it is a legitimate and comparatively cheap way to reach closure "
            "-- unlike **area relief**, which spends the objective directly. Be precise "
            "about what 'area relief' means, because these knobs are not one-directional: "
            "*lowering* `CORE_UTILIZATION`/`PLACE_DENSITY` (or *raising* `DIE_AREA_SCALE`) "
            "grows the die and spends the objective; *raising* `CORE_UTILIZATION`/"
            "`PLACE_DENSITY` (or *lowering* `DIE_AREA_SCALE`) shrinks it and WINS the "
            "objective back. Never describe touching these knobs as costing area without "
            "saying which way they moved -- and if an earlier round already grew the die "
            "to buy closure, recovering that is progress on the objective, not a cost. "
            "It does still move the timing target "
            "rather than improving the design, and the design keeps whatever clock it "
            "closes at, so it is a real cost -- just not one measured by this objective. "
            "If die area is being spent while the clock has room, say so plainly.")


def _load_referee_prompt(prompt_path: str, design_name: str, comparison: dict,
                          ledger_text: str, objective: str = "area",
                          current_config: Optional[dict] = None) -> str:
    template = Path(prompt_path).read_text()
    return (
        template
        .replace("$DESIGN_NAME", design_name)
        .replace("$OBJECTIVE_NOTE", _objective_note(objective))
        .replace("$ROUND_COMPARISON", json.dumps(comparison, indent=2))
        .replace("$LEDGER", ledger_text or "(nothing measured yet)")
        .replace("$CURRENT_CONFIG", json.dumps(current_config or {}, indent=2)
                 if current_config else "(not available)")
    )


def _round_comparison(baseline: Optional[dict], entries: list) -> dict:
    """The round as a controlled experiment: one shared starting point, then
    what each slot changed from it and what that measurably did.

    Without this the model sees a flat run list and cannot tell that two runs
    were siblings branched from the same config rather than two sequential
    attempts -- which is the whole information advantage of running them in
    parallel, and it was previously being thrown away.
    """
    def _metrics(e: dict) -> dict:
        if e.get("crashed"):
            return {"crashed_at_stage": e.get("stage")}
        v, p = e.get("violations") or {}, e.get("physical_metrics") or {}
        return {
            "setup_wns": v.get("setup_wns_slack"), "hold_wns": v.get("hold_wns_slack"),
            "setup_tns": v.get("setup_tns_slack"), "drc": v.get("drc_error_count"),
            "core_area": p.get("core_area"), "util_percent": p.get("core_utilization_percent"),
        }

    def _delta(e: dict) -> dict:
        if baseline is None or e.get("crashed") or baseline.get("crashed"):
            return {}
        b, c = _metrics(baseline), _metrics(e)
        out = {}
        for k in ("setup_wns", "hold_wns", "setup_tns", "drc", "core_area"):
            if b.get(k) is not None and c.get(k) is not None:
                out[f"d_{k}"] = round(c[k] - b[k], 6)
        return out

    ranked = sorted(entries, key=_round_rank_key)
    return {
        "note": "All candidates below were run in parallel from the SAME starting "
                "configuration, so their differences are directly comparable.",
        "started_from": {
            "run": baseline.get("run") if baseline else None,
            "metrics": _metrics(baseline) if baseline else None,
        },
        "candidates": [{
            "slot": e.get("slot"),
            "run": e.get("run"),
            "changed": e.get("tunables_changed"),
            "result": _metrics(e),
            "change_vs_start": _delta(e),
            "verdict": e.get("_verdict"),
        } for e in entries],
        "won_this_round": {"run": ranked[0].get("run"), "slot": ranked[0].get("slot")} if ranked else None,
    }

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)

def _extract_proposal(text: Optional[str]) -> tuple:
    """Parse an LLM reply into (sentinel, proposal, error).

    Exactly one of the three is meaningful: `sentinel` is "PASS"/"GIVE_UP",
    `proposal` is the parsed change dict, `error` explains why neither could
    be read (handed back to the model verbatim next turn). Deliberately
    tolerant -- a model that wraps its JSON in prose still gets understood,
    since the alternative is throwing away a whole multi-minute turn over
    formatting.
    """
    if not text or not text.strip():
        return None, None, "Empty reply."
    for line in (l.strip() for l in text.strip().splitlines()):
        if line == "CLOSURE: PASS":
            return "PASS", None, None
        if line == "CLOSURE: GIVE_UP":
            return "GIVE_UP", None, None

    blob = None
    m = _JSON_FENCE_RE.search(text)
    if m:
        blob = m.group(1)
    else:
        # No fence -- fall back to the outermost {...} span in the reply.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            blob = text[start:end + 1]
    if blob is None:
        return None, None, (
            "No JSON object found in your reply. Reply with ONLY a ```json "
            "fenced object of the tunables to change."
        )
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError as exc:
        return None, None, f"Your JSON did not parse ({exc}). Reply with a single valid JSON object."
    if not isinstance(parsed, dict):
        return None, None, "Your JSON must be an object mapping tunable names to values."
    if not parsed:
        return None, None, "Your JSON object was empty -- propose at least one change, or reply CLOSURE: PASS."
    return None, parsed, None

class _Heartbeat:
    def __init__(self, label: str, interval_seconds: float = 15.0):
        self.label = label
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._t0 = None

    def _run(self):
        while not self._stop_event.wait(self.interval_seconds):
            elapsed = time.time() - self._t0
            print(f"  ... still waiting on {self.label} ({elapsed:.0f}s elapsed) ...", flush=True)

    def __enter__(self):
        self._t0 = time.time()
        self._thread.start()
        return self

    def __exit__(self, *exc_info):
        self._stop_event.set()
        self._thread.join(timeout=1.0)
        return False

LLM_TRANSIENT_RETRIES = 3
LLM_BACKOFF_SECONDS = 30
FALLBACK_MODELS_FILE = REPO_ROOT / "llm_fallback_models.txt"


_MODEL_UNAVAILABLE_MARKERS = (
    "RateLimitError", "Rate limit exceeded",
    # Provider/model itself broken or gone, not just throttled (observed live:
    # opencode/nemotron-3-ultra-free returning a bare 404 via uvm_loop, same
    # OpenCode account/routing this pool draws from) -- retrying the same
    # model would fail identically forever, so switch away from it too.
    "InvalidRequestError", "Upstream request failed", "Provider returned error",
)


def _is_rate_limited(exc_or_text) -> bool:
    text = repr(exc_or_text) if isinstance(exc_or_text, BaseException) else str(exc_or_text)
    return any(marker in text for marker in _MODEL_UNAVAILABLE_MARKERS)


class _LLMPool:
    """Ordered model fallback: `--model` first, then llm_fallback_models.txt.

    Free-tier providers rate-limit long runs; on a rate limit the pool moves to
    the next model and stays there (sticky) so one run doesn't flip-flop.
    """

    def __init__(self, primary: str, timeout_seconds: int):
        models = [primary]
        if FALLBACK_MODELS_FILE.exists():
            for line in FALLBACK_MODELS_FILE.read_text().splitlines():
                m = line.split("#", 1)[0].strip()
                if m and m not in models:
                    models.append(m)
        self.models = models
        self.index = 0
        self.used = [primary]
        self._timeout = timeout_seconds
        self._llms: dict = {}
        self.on_trace = None

    @property
    def model(self) -> str:
        return self.models[self.index]

    def current(self):
        if self.model not in self._llms:
            self._llms[self.model] = OpenCodeLLM(
                model=self.model, timeout_seconds=self._timeout,
                log_dir="/tmp", logging_name="orfs_closure",
            )
        return self._llms[self.model]

    def advance(self, reason: str) -> bool:
        if self.index + 1 >= len(self.models):
            return False
        old = self.model
        self.index += 1
        if self.model not in self.used:
            self.used.append(self.model)
        msg = f"LLM model {old} rate-limited ({reason[:160]}); switching to {self.model}"
        print(f"  ({msg})")
        if self.on_trace:
            self.on_trace(f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: {msg}\n" + "-" * 60 + "\n")
        return True


def _prompt_with_backoff(llm, prompt_text, on_trace):
    """Run one LLM turn, retrying transient provider failures with real backoff.

    No tools are passed. The model's entire job is to read the report already
    embedded in the prompt and reply with JSON, so a turn takes seconds --
    which is the whole point: the old design had the model invoke the flow
    over MCP, and every one of those calls blew past opencode's ~60s client
    timeout (`MCP error -32001`), causing retries that started a second flow
    on top of the first.

    chia's own OpenCodeLLM.prompt() docs say RateLimitError/AuthenticationError/
    BillingError/InvalidRequestError "propagate immediately" rather than being
    retried internally -- by design, chia leaves handling those to the caller.
    Left unhandled here, any of them (observed live: InvalidRequestError,
    "Requests ending with a model turn are not supported", on a batch-decision
    call) crashes get() and takes the whole driver down over what a fresh
    `opencode run` invocation next attempt might not even reproduce. Folded
    into the same retry-with-backoff loop as an ordinary failed turn rather
    than treated as fatal, since a retry starts an entirely new opencode
    session and this class of error looks exactly like the kind of transient
    session-state hiccup the existing backoff message already describes.
    """
    pool = llm if isinstance(llm, _LLMPool) else None
    result = None
    attempt = 0
    while attempt < LLM_TRANSIENT_RETRIES:
        attempt += 1
        active = pool.current() if pool else llm
        try:
            result = get(active.prompt.chia_remote(active, prompt_text, tools=[]))
        except Exception as exc:
            result = SimpleNamespace(success=False, result=f"LLM call raised: {exc}")
        if not result.success and pool:
            result_text = getattr(result, "result", "") or ""
            stderr_text = getattr(result, "stderr", "") or ""
            # After chia's own internal retries exhaust on a subprocess timeout,
            # it returns success=False with BOTH result and stderr empty --
            # no exception, no message, nothing for a text match to catch.
            # Observed live: 3 concurrent big-pickle calls each burned ~90min
            # this way, and the empty result also carries no signal for pass 2
            # to avoid retrying the same exhausted model. Treat a silently
            # empty failure the same as a detected rate limit/unavailability.
            silent_timeout = not result_text.strip() and not stderr_text.strip()
            if (silent_timeout or _is_rate_limited(f"{result_text} {stderr_text}")) \
                    and pool.advance("(silent timeout, empty result)" if silent_timeout else result_text):
                attempt -= 1
                continue
        if result.success or attempt == LLM_TRANSIENT_RETRIES:
            return result
        wait = LLM_BACKOFF_SECONDS * attempt
        msg = (
            f"LLM turn failed (attempt {attempt}/{LLM_TRANSIENT_RETRIES}); waiting "
            f"{wait}s before retrying. This is usually transient provider overload, "
            "not a problem with the config or the flow."
        )
        print(f"  ({msg})")
        on_trace(f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: {msg}\n" + "-" * 60 + "\n")
        time.sleep(wait)
    return result


def _rank_key(entry: dict) -> tuple:
    """Sort key for closed runs: timing margin first, area only as tie-break.

    Every CLOSED run already meets slack >= 0 and zero router DRC, but "barely
    closed" and "closed with headroom" are not equally trustworthy going into
    signoff -- a razor-thin margin is far likelier to flip to a real DRC/LVS
    failure under the standalone KLayout checks than a roomier one, whatever
    their relative areas.
    """
    v = entry["violations"]
    return (-min(v["setup_wns_slack"], v["hold_wns_slack"]),
            entry["physical_metrics"]["core_area"])


def _round_rank_key(entry: dict) -> tuple:
    """Canonical best-first "which candidate won this round" ordering.

    One function, because three places need this answer and they must never
    disagree: the round's carried-forward anchor (`history[-1]`, which is what
    next round's prompts see as `latest`), the iteration winner (`closed_entry`),
    and the `won_this_round` field the referee reads.

    Tier first (closed < violating < crashed), then the tier's *own*
    discriminator. That second part is the whole point: `_violation_score` is
    identically 0.0 for every closed run -- it measures violations, and a closed
    run by definition has none -- so ranking closed candidates by it is a total
    tie broken by list order. Observed live on riscv32i iteration 2: five of six
    slots closed, `won_this_round` reported slot 0 (CORE_UTILIZATION 47, area
    133458) purely for being listed first, while the driver actually carried
    slot 5 forward (CORE_UTILIZATION 50, area 125408 -- 6% smaller *and* better
    slack). The referee then wrote its cross-slot insight crediting the wrong
    candidate. Closed runs are ordered by `_rank_key` (margin, then area) here.
    """
    if entry.get("crashed"):
        return (2, 0.0, 0.0)
    v = entry.get("violations") or {}
    if str(entry.get("status", "")).startswith("CLOSED"):
        margin = min(v.get("setup_wns_slack", 0.0), v.get("hold_wns_slack", 0.0))
        area = (entry.get("physical_metrics") or {}).get("core_area")
        return (0, -margin, float(area) if area is not None else 0.0)
    return (1, _violation_score(v), 0.0)


def _best_run(history: list) -> Optional[dict]:
    """Best run so far: a closed one if any exists, else whichever got closest."""
    scored = [e for e in history if not e.get("crashed") and e.get("violations")]
    if not scored:
        return None
    closed = [e for e in scored if str(e.get("status", "")).startswith("CLOSED")]
    if closed:
        return min(closed, key=_rank_key)
    return min(scored, key=lambda e: _violation_score(e["violations"]))


def _detect_stall(history: list, verdict_history: list, n: int = 3) -> bool:
    """True when either:

    * the last *n* verdicts are all REGRESSED/UNCHANGED -- the obvious case, or
    * none of the last `n * 2` runs in the current iteration actually beat
      the best violation score seen *before* that window, even though no
      single pairwise verdict in it says REGRESSED.

    The second check exists because pairwise verdicts can look fine while
    the search as a whole goes nowhere: knob A nudges the score down a
    little, then knob B nudges it down a little more from a different
    angle, then knob C undoes both -- each step reads as IMPROVED or
    REGRESSED against the *immediately preceding* run, so a streak
    requirement never fires, yet several runs later the design is no closer
    to closing than it was at the start of the window. That is a real stall
    (thrashing between knobs instead of committing to one), just invisible
    to a same/better-than-last-run comparison.
    """
    if len(verdict_history) >= n and all(v in ("REGRESSED", "UNCHANGED") for v in verdict_history[-n:]):
        return True

    window = n * 2
    if len(history) < window:
        return False
    current_iteration = history[-1].get("iteration")
    recent = [e for e in history[-window:] if e.get("iteration") == current_iteration]
    is_closed = lambda e: not e.get("crashed") and str(e.get("status", "")).startswith("CLOSED")
    if len(recent) < window or any(is_closed(e) for e in recent):
        return False
    before = history[: len(history) - window]
    before_best = min((_violation_score(e["violations"]) for e in before if e.get("violations")), default=None)
    window_best = min((_violation_score(e["violations"]) for e in recent if e.get("violations")), default=None)
    if before_best is None or window_best is None:
        return False
    return window_best >= before_best - 1e-9


def _verdict(prev: Optional[dict], curr: dict) -> dict:
    """Explicit IMPROVED/REGRESSED/... judgement against the previous run, so
    the model never has to derive a trend from raw numbers itself."""
    CLOSED = "CLOSED"
    if prev is None:
        return {"verdict": "FIRST_RUN", "note": "No prior run to compare against."}
    if curr.get("crashed"):
        return {"verdict": "CRASHED", "note": (
            f"This configuration crashed the flow (stage: {curr.get('stage')}). "
            "Do not retry these exact values -- treat this as the 'bad' boundary "
            "and bisect back toward your last working value.")}
    if prev.get("crashed"):
        return {"verdict": "RECOVERED", "note": "Previous config crashed; this one completed."}

    prev_closed = str(prev.get("status", "")).startswith(CLOSED)
    curr_closed = str(curr.get("status", "")).startswith(CLOSED)
    if curr_closed and not prev_closed:
        return {"verdict": "IMPROVED", "note": "Violations are now fully resolved."}
    if prev_closed and not curr_closed:
        return {"verdict": "REGRESSED", "note": (
            "This change reintroduced violations after the design was closed. "
            "Revert the tunables you changed this run.")}

    if not curr_closed:
        pv, cv = prev["violations"], curr["violations"]
        out = {"violation_deltas": {
            k: {"previous": pv[k], "current": cv[k], "delta": round(cv[k] - pv[k], 6)}
            for k in ("setup_wns_slack", "setup_tns_slack", "hold_wns_slack", "drc_error_count")
        }}
        ps, cs = _violation_score(pv), _violation_score(cv)
        if cs < ps - 1e-9:
            out["verdict"] = "IMPROVED"
        elif cs > ps + 1e-9:
            out["verdict"] = "REGRESSED"
            out["note"] = ("This change made violations worse overall. Revert it and try a "
                           "different knob rather than pushing further the same way.")
        else:
            out["verdict"] = "UNCHANGED"
        return out

    pm, cm = prev["physical_metrics"], curr["physical_metrics"]
    out = {"physical_deltas": {
        k: {"previous": pm[k], "current": cm[k], "delta": round(cm[k] - pm[k], 6)}
        for k in ("core_utilization_percent", "total_power", "core_area")
    }}
    if cm["core_area"] <= pm["core_area"] and cm["total_power"] <= pm["total_power"]:
        out["verdict"] = "IMPROVED"
    elif cm["core_area"] >= pm["core_area"] and cm["total_power"] >= pm["total_power"]:
        out["verdict"] = "REGRESSED"
        out["note"] = "Area and power both got worse -- revert this change."
    else:
        out["verdict"] = "MIXED"
    return out


def _slot_paths(reports_root: str, working_config_mk: Path, slot: int) -> dict:
    """Container-native reports_root/results_root/working_config_mk/flow_variant
    for one --batch-size parallel slot. Pure string substitution -- no
    filesystem access here. FLOW_VARIANT literally is the trailing path
    segment of ORFS's own reports_root (flow/scripts/variables.mk scopes
    LOG_DIR/OBJECTS_DIR/REPORTS_DIR/RESULTS_DIR by it, default "base" --
    today's single-run --reports-root already ends in ".../base"), so this
    reuses that existing ORFS mechanism rather than inventing a new one.
    """
    variant = f"slot{slot}"
    rr = Path(reports_root)
    slot_reports_root = str(rr.parent / variant)
    return {
        "flow_variant": variant,
        "working_config_mk": working_config_mk.parent / f"config.chia.{variant}.mk",
        "reports_root": slot_reports_root,
        "results_root": slot_reports_root.replace("/reports/", "/results/", 1),
    }


def _promote_best_gds(run_dir: Path, best_index: int, on_trace) -> None:
    """Point final.gds / final_layout.webp at the best run rather than the last.

    Every run archives its own copy under gds/run_N_*, while the `final.*`
    copies are overwritten on every run -- so without this they show whatever
    was tried last, even if the loop wandered past a better result earlier.
    """
    gds_dir = run_dir / "gds"
    pairs = [(gds_dir / f"run_{best_index}_final.gds", run_dir / "final.gds"),
             (gds_dir / f"run_{best_index}_layout.webp", run_dir / "final_layout.webp")]
    promoted = []
    for src, dst in pairs:
        if not src.exists():
            continue
        try:
            # dst was written by the container as root; run_dir itself is ours,
            # so unlink-then-copy works where opening dst for write would not.
            if dst.exists():
                dst.unlink()
            shutil.copy2(src, dst)
            promoted.append(dst.name)
        except OSError:
            pass
    if promoted:
        msg = f"Promoted run {best_index} (best result) to {', '.join(promoted)}."
        print(f"\n{msg}")
        on_trace(f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: {msg}\n" + "-" * 60 + "\n")


def run_closure_loop(
    design_name: str,
    flow_dir: str,
    design_config_mk: str,
    reports_root: str,
    run_dir: Path,
    max_iterations: int = 3,
    objective: str = "area",
    model: str = "google/gemini-3.6-flash",
    closure_criteria: Optional[str] = None,
    stage_timeout_seconds: int = 3600,
    llm_timeout_seconds: int = 1800,
    prompt_path: str = DEFAULT_PROMPT_PATH,
    diagnose_prompt_path: str = DEFAULT_DIAGNOSE_PROMPT_PATH,
    referee_prompt_path: str = DEFAULT_REFEREE_PROMPT_PATH,
    schema_path: str = DEFAULT_SCHEMA_PATH,
    ld_library_path: str = DEFAULT_LD_LIBRARY_PATH,
    locked_tunables: Optional[dict] = None,
    fresh_config: bool = True,
    run_signoff: bool = True,
    batch_size: int = 1,
    skip_referee: bool = False,
    seed_ledger: Optional[str] = None,
) -> dict:
    """Driver-owned closure loop, two levels deep.

    * A **run** is one flow execution (synth -> ... -> metadata) plus the LLM
      turn that proposes what to change next. The driver executes the flow on
      its own blocking Ray call and hands the parsed metrics to the LLM as
      text; the LLM has no tools and never executes anything, which removes
      MCP timeouts, overlapping flows, and "the model claimed a result it
      never ran" in one go.
    * An **iteration** is a sequence of runs with a single goal, and ends only
      when a run comes back CLOSED. Iteration 1's goal is always just closure.
      Every iteration after that takes the previous one's closed design and
      pushes `objective` -- "clock" (shorter CLOCK_PERIOD = faster) or "area"
      (smaller core_area) -- then has to close again at the tighter target.
      Closing again without beating the target does not count as progress.

    Ordering matters: chasing speed or area before anything closes just yields
    an aggressive config that never converges, so the objective is only
    introduced once there is a closed design to trade against.

    `batch_size` > 1 runs that many flow executions concurrently per round
    instead of one at a time (see _decide_batch and README.md's "Parallel
    batches" section) -- each parallel slot gets its
    own ORFS FLOW_VARIANT so `make clean_all` in one never touches another's
    in-flight files, even though all slots share the same design/checkout.
    batch_size=1 (the default) takes the exact same code path as before this
    feature existed; every artifact path/naming is byte-identical.
    """
    if objective not in OBJECTIVES:
        raise ValueError(f"objective must be one of {OBJECTIVES}, got {objective!r}")
    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size!r}")
    run_dir.mkdir(parents=True, exist_ok=True)

    if closure_criteria is None:
        # No hardcoded utilization/area target: that is entirely design
        # dependent, and a stale number from another design would quietly
        # steer the model at the wrong goal.
        closure_criteria = (
            "Worst setup slack >= 0 (timing met). Zero DRC violations. "
            "Zero LVS violations. Once violations are first resolved, treat "
            "the resulting core utilization/area as the baseline for this "
            "design and avoid inflating it further than necessary just to "
            "make timing/DRC pass."
        )

    extra_env = {}
    if ld_library_path:
        extra_env["LD_LIBRARY_PATH"] = ld_library_path

    container_run_dir = _container_run_dir(run_dir)
    if container_run_dir is None:
        print(
            f"  (warning: run_dir {run_dir} is outside the repo, so it isn't visible "
            "inside the orfs_run container -- per-run artifacts (GDS, flow logs, "
            "tool_trace.log) won't be collected for this run.)"
        )

    trace_log_path = run_dir / "tool_trace.log"

    def _append_trace(text: str) -> None:
        # Best-effort: the container may have created this file as root, and a
        # logging hiccup must never kill an otherwise-working closure loop.
        try:
            with trace_log_path.open("a") as f:
                f.write(text)
        except OSError as exc:
            print(f"  (warning: could not write trace log: {exc})")

    # ---------------------------------------------------------------- setup
    schema = load_schema(schema_path)

    # CLOCK_PERIOD lives in constraint.sdc, not config.mk, and its sane range
    # is design-specific -- so its bounds are computed per design at startup
    # rather than fixed in the schema file.
    baseline_clock_period = None
    if "CLOCK_PERIOD" in schema:
        baseline_clock_period = get(
            _read_baseline_clock_period_remote.chia_remote(design_config_mk))
        if baseline_clock_period is None:
            schema.pop("CLOCK_PERIOD", None)
        else:
            schema["CLOCK_PERIOD"]["min"] = round(baseline_clock_period * 0.3, 6)
            schema["CLOCK_PERIOD"]["max"] = round(baseline_clock_period * 3.0, 6)

    # DIE_AREA_SCALE only applies to designs whose baseline already uses an
    # explicit die/core area. ORFS treats DIE_AREA+CORE_AREA and
    # CORE_UTILIZATION as mutually exclusive floorplan methods and hard-exits
    # if both are set, so for utilization-based designs the key is removed
    # entirely rather than offered and rejected later.
    if "DIE_AREA_SCALE" in schema:
        floorplan = get(_read_baseline_floorplan_remote.chia_remote(design_config_mk))
        if floorplan.get("method") != "explicit_area":
            schema.pop("DIE_AREA_SCALE", None)

    # The reverse of the DIE_AREA_SCALE check above: CORE_UTILIZATION is the
    # utilization-method design's own area lever, but nothing previously
    # stopped it from ALSO being offered on an explicit-area design (its
    # baseline config.mk's DIE_AREA/CORE_AREA lines are always copied
    # verbatim into the working config regardless of what else is set) --
    # so touching CORE_UTILIZATION there sets both floorplan methods at
    # once and hits the exact same ORFS hard-exit, even with DIE_AREA_SCALE
    # never involved. Observed live on ihp-sg13g2's i2c-gpio-expander (an
    # explicit-area design): "Floorplan initialization methods are mutually
    # exclusive, pick one." the first time a batch slot proposed a
    # CORE_UTILIZATION change on its own.
    if "CORE_UTILIZATION" in schema:
        floorplan = get(_read_baseline_floorplan_remote.chia_remote(design_config_mk))
        if floorplan.get("method") == "explicit_area":
            schema.pop("CORE_UTILIZATION", None)

    # Enum-typed tunables (currently just MAX_ROUTING_LAYER) assume a fixed
    # set of platform-native values ("met1".."met5", sky130hd/nangate45's
    # naming). A platform with different layer names -- observed live on
    # ihp-sg13g2, whose baseline config.mk already has MAX_ROUTING_LAYER =
    # "TopMetal2" -- has a legal current value the schema's enum doesn't
    # recognize. Without this check, EVERY apply_tunables_remote call for
    # such a design fails re-validating this untouched baseline value, even
    # on rounds that never ask to change it. Drop any such key entirely
    # rather than offer one guaranteed to break on first use.
    enum_keys = [k for k, spec in schema.items() if spec.get("type") == "enum"]
    if enum_keys:
        current_enum_values = get(
            read_tunables_remote.chia_remote(design_config_mk, json.dumps(schema)))
        for key in enum_keys:
            current_val = current_enum_values.get(key)
            if current_val is not None and current_val not in schema[key]["values"]:
                schema.pop(key, None)

    locked = validate_tunables(locked_tunables or {}, schema)

    baseline_path = Path(design_config_mk)
    working_config_mk = baseline_path.parent / "config.chia.mk"
    get(_prep_working_config_remote.chia_remote(
        str(baseline_path),
        str(baseline_path.parent / "chia_backups"),
        str(working_config_mk),
        fresh_config,
    ))
    if locked:
        # Baked into the working config up front, overriding the baseline, so
        # a locked value holds even on the very first run.
        get(_apply_locked_tunables_remote.chia_remote(
            str(baseline_path), str(working_config_mk),
            json.dumps(schema), json.dumps(locked),
        ))

    results_root = str(reports_root).replace("/reports/", "/results/", 1)
    schema_json = json.dumps(schema)

    # Each --batch-size slot needs its own working config.mk, prepped from
    # baseline exactly like the canonical one above (apply_tunables_remote
    # requires the file to already exist) -- done once up front rather than
    # lazily per round, since it's cheap file I/O and keeps the round loop
    # simple.
    slot_paths_cache: dict = {}
    if batch_size > 1:
        for slot in range(batch_size):
            paths = _slot_paths(reports_root, working_config_mk, slot)
            get(_prep_working_config_remote.chia_remote(
                str(baseline_path),
                str(baseline_path.parent / "chia_backups"),
                str(paths["working_config_mk"]),
                fresh_config,
            ))
            if locked:
                get(_apply_locked_tunables_remote.chia_remote(
                    str(baseline_path), str(paths["working_config_mk"]),
                    json.dumps(schema), json.dumps(locked),
                ))
            slot_paths_cache[slot] = paths

    llm = _LLMPool(model, llm_timeout_seconds)
    llm.on_trace = _append_trace
    if len(llm.models) > 1:
        print(f"  LLM models (fallback order): {llm.models}")

    history: list = []          # every flow run, flat, in order
    iterations: list = []       # one record per iteration (the major unit)
    final_status = "max_iterations_reached"
    feedback: Optional[str] = None          # parse/apply error to relay next turn
    objective_target: Optional[float] = None   # value the next iteration must beat
    last_diagnosis_run: Optional[int] = None   # len(history) at the last stall diagnosis
    # Accumulated measurements of what each knob change actually did, across
    # every run and every parallel slot (orfs_ledger). Evidence for the model,
    # never a decision-maker -- see that module's docstring.
    ledger: dict = orfs_ledger.new_ledger(design_name)
    if seed_ledger:
        ledger, seed_note = orfs_ledger.seed_from(seed_ledger, design_name)
        print(f"  ledger: {seed_note}")
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Ledger seed\n"
            f"{seed_note}\n" + "-" * 60 + "\n"
        )
    # Written by _run_flow_batch / _run_round_referee and read by the prompt
    # builders. A plain dict rather than two `nonlocal` names purely so the
    # inner functions can assign without a nonlocal declaration each.
    nonlocal_state: dict = {"last_round_comparison": None, "round_insight": None}

    def _objective_value(entry: dict) -> Optional[float]:
        return objective_value(entry, objective)

    def _iteration_done(iteration: int, entry: dict) -> bool:
        return iteration_done(iteration, entry, objective, objective_target)

    def _build_history_entry(result: dict, run_index: int, iteration: int,
                              config_under_test: dict, prev: Optional[dict],
                              trace_label: str = "", slot: Optional[int] = None) -> dict:
        """Turn one flow result into a history entry (verdict/diff against
        `prev`, appended to `history`) plus its trace payload. Shared by the
        serial path (`prev` = the actual previous run) and --batch-size's
        `_run_flow_batch` (`prev` = the round's shared starting point, NOT a
        sibling slot -- each slot's verdict is judged against what the round
        started from, not against other slots tried in parallel).
        """
        # from->to against the previous run's actual config, not the raw
        # proposal: the proposal alone has no "from" side, and this also
        # catches anything the apply step adjusted (locked keys forced back).
        tunables_changed = _diff_tunables(prev["config"] if prev else None, config_under_test)
        comparison = _verdict(prev, result)
        clock_period = config_under_test.get("CLOCK_PERIOD", baseline_clock_period)
        try:
            clock_period = float(clock_period) if clock_period is not None else None
        except (TypeError, ValueError):
            clock_period = baseline_clock_period

        entry = dict(result)
        entry.update({
            "run": run_index,
            "iteration": iteration,
            "tunables_changed": tunables_changed,
            "config": config_under_test,
            "clock_period": clock_period,
            # None in serial mode. In batch mode this is what lets the round
            # comparison and the ledger say *which* parallel branch produced
            # a result, rather than presenting siblings as a flat sequence.
            "slot": slot,
            # Cheap to recompute from `comparison`, but stored directly so
            # _detect_stall can read a plain verdict string across runs
            # without re-deriving it from raw metrics.
            "_verdict": comparison.get("verdict"),
        })
        history.append(entry)

        best = _best_run(history)
        payload = dict(result)
        payload.update({
            "iteration": iteration,
            "clock_period": clock_period,
            "tunables_changed_this_run": tunables_changed or "(baseline run -- nothing changed yet)",
            "comparison_to_previous_run": comparison,
            # Underscore keys are internal bookkeeping (notably _payload, which
            # would otherwise nest each run's whole report inside the next).
            "recent_history": [
                {k: v for k, v in e.items()
                 if k not in ("config", "details") and not k.startswith("_")}
                for e in history[-6:]
            ],
        })
        if best is not None and best["run"] != run_index:
            payload["best_run_so_far"] = {
                "run": best["run"], "status": best.get("status"),
                "violations": best.get("violations"),
                "physical_metrics": best.get("physical_metrics"),
            }
        kind = "ERROR" if result.get("crashed") else "SUCCESS"
        label = f"{trace_label} " if trace_label else ""
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] RETURN {kind}: "
            f"{label}run_full_flow_and_summarize\n{json.dumps(payload, indent=2)}\n" + "-" * 60 + "\n"
        )
        entry["_payload"] = payload
        return entry

    def _run_flow_once(run_index: int, iteration: int) -> dict:
        """One flow execution at the canonical (non-slotted) path, recorded
        into history and traced for the GUI."""
        config_under_test = get(read_tunables_remote.chia_remote(
            str(working_config_mk), schema_json))
        # Written before the (possibly minutes-long) blocking call below, not
        # after: the dashboard's _parse_run watches for an unresolved CALL
        # with no matching RETURN yet to show a live "flow running..." row
        # with a loading spinner. Without this the row only ever appears
        # once the run is already done, and the whole point is to show the
        # change being tested while it's still in flight.
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] CALL: run_full_flow_and_summarize\n\n"
            + "-" * 60 + "\n"
        )
        t0 = time.time()
        with _Heartbeat(f"Flow run {run_index} (synth -> route -> finish)"):
            result = get(run_flow_remote.chia_remote(
                flow_dir, str(working_config_mk), str(reports_root), results_root,
                extra_env, stage_timeout_seconds, container_run_dir, run_index,
            ))
        print(f"  run {run_index} finished in {time.time()-t0:.0f}s "
              f"-- {result.get('status') or result.get('fatal_error')}")
        prev = history[-1] if history else None
        entry = _build_history_entry(result, run_index, iteration, config_under_test, prev)
        # Serial runs feed the same ledger as batch rounds -- the evidence is
        # just as valid when it comes one run at a time.
        orfs_ledger.observe(ledger, prev, entry)
        orfs_ledger.save(ledger, run_dir / "ledger.json")
        return entry

    def _run_stall_diagnosis() -> Optional[str]:
        """One extra, short LLM turn for the case the model's own attempts
        have failed to move the needle (see _detect_stall): a focused
        root-cause read on the raw failure detail, fed into the *next*
        normal decision turn as `stall_diagnosis`. Throttled by
        STALL_REDIAGNOSE_EVERY so a stall
        that never resolves doesn't pay for a diagnosis turn every run.
        """
        stall_slice = [
            {k: v for k, v in e.items() if k in
             ("run", "tunables_changed", "status", "violations", "physical_metrics", "_verdict", "stage")}
            for e in history[-STALL_THRESHOLD:]
        ]
        latest_entry = history[-1]
        raw_excerpt = (latest_entry.get("details") or {}).get("log_tail") or ""
        if not raw_excerpt:
            raw_excerpt = json.dumps({
                "violations": latest_entry.get("violations"),
                "physical_metrics": latest_entry.get("physical_metrics"),
                "qor_rule_failures": latest_entry.get("qor_rule_failures"),
            }, indent=2)
        prompt_text = _load_diagnose_prompt(diagnose_prompt_path, design_name, stall_slice, raw_excerpt)
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Stall detected "
            f"(last {STALL_THRESHOLD} runs made no progress) -- running diagnosis turn\n"
            + "-" * 60 + "\n"
        )
        t0 = time.time()
        with _Heartbeat("Stall diagnosis turn"):
            cli = _prompt_with_backoff(llm, prompt_text, _append_trace)
        print(f"  diagnosis turn finished in {time.time()-t0:.1f}s (success={cli.success})")
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Stall diagnosis result | "
            f"Success: {cli.success}\n{cli.result}\n" + "-" * 60 + "\n"
        )
        return cli.result if cli.success and cli.result else None

    def _run_round_referee(iteration: int, comparison: dict) -> None:
        """One extra LLM turn per batch round that reads all N slots' results
        side by side and writes a short note every slot sees next round.

        This is the only place anything reasons *across* slots. Without it the
        slots are genuinely independent sessions that merely happen to share a
        starting config -- each one sees the others' runs in `recent_history`
        as an undifferentiated flat list, with no signal that they were
        siblings from one baseline, and nobody ever concludes "area relief
        bought more slack than clock relief here" or "that knob has stopped
        doing anything". Cheap relative to what it guards: one LLM call against
        a round that costs `batch_size` full flow runs.

        Best-effort: a failed or empty referee turn just leaves the previous
        insight in place rather than blocking the round.
        """
        if skip_referee or len(comparison.get("candidates") or []) < 2:
            return
        # The round winner's config -- what the next round actually branches
        # from. Without it the referee recommends knobs already sitting at the
        # value it wants (observed: "try CORE_UTILIZATION alone" when it had
        # been 33 for eight runs), and a no-op attempt leaves no trace in the
        # ledger to warn it off, since it changed nothing to measure.
        cur_cfg = dict((history[-1].get("config") or {})) if history else {}
        cp = history[-1].get("clock_period") if history else None
        if cp is not None:
            cur_cfg.setdefault("CLOCK_PERIOD", cp)
        prompt_text = _load_referee_prompt(
            referee_prompt_path, design_name, comparison,
            orfs_ledger.render(ledger), objective, cur_cfg)
        t0 = time.time()
        with _Heartbeat(f"Round referee (iteration {iteration})"):
            cli = _prompt_with_backoff(llm, prompt_text, _append_trace)
        print(f"  round referee finished in {time.time()-t0:.1f}s (success={cli.success})")
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Iteration {iteration} "
            f"Round Referee | Success: {cli.success}\n{cli.result}\n" + "-" * 60 + "\n"
        )
        if cli.success and cli.result and cli.result.strip():
            nonlocal_state["round_insight"] = cli.result.strip()[:2000]

    def _drift_from_baseline() -> Optional[dict]:
        """How far the current config has drifted from the design's ORIGINAL
        baseline, cumulatively.

        The prompt caps each target-knob step at ~10-15%, but that cap does not
        compose: several individually-legal steps in the same direction add up.
        Observed live -- CORE_UTILIZATION 38->33->28, both steps inside the cap,
        grew the die 33% while the second step actually made WNS *worse*. And
        because iteration 2's objective target is whatever iteration 1 happens
        to close at, area given away chasing that first close is not
        automatically won back later; it silently becomes the new normal. A
        per-step delta cannot show any of that, so the cumulative number is
        stated explicitly.
        """
        if not history:
            return None
        base = history[0]
        # history[-1], not _best_run: in batch mode the last entry is the
        # round's winner, which is exactly the config the next round branches
        # from (see _run_flow_batch's winner_config). Drift should describe
        # where the search actually stands, not a better run it has left.
        cur = history[-1]
        out = {}
        for label, getter in (("core_area", lambda e: (e.get("physical_metrics") or {}).get("core_area")),
                              ("clock_period", lambda e: e.get("clock_period"))):
            b, c = getter(base), getter(cur)
            try:
                b, c = float(b), float(c)
            except (TypeError, ValueError):
                continue
            if b == 0:
                continue
            out[label] = {"original_baseline": b, "now": c,
                          "change_percent": round((c - b) / b * 100.0, 1)}
        if not out:
            return None
        out["note"] = (
            "Cumulative drift from the design's original configuration, not a per-step "
            "delta. Iteration 1 only has to close -- but whatever it closes at becomes the "
            "value later iterations must beat, so area or clock speed given away here is "
            "not automatically won back. If a target knob has drifted a long way and the "
            "recent steps stopped paying for themselves, step it back rather than further."
        )
        # A knob the objective doesn't measure looks free and will be spent
        # freely -- CLOCK_PERIOD under --objective area is the standing example,
        # and its schema bound is ~3x the original period, so "within bounds" is
        # not much of a brake. Escalate once the drift is large enough that a
        # person would want to have been asked about it.
        heavy = [f"{k} {v['change_percent']:+g}%" for k, v in out.items()
                 if isinstance(v, dict) and abs(v.get("change_percent") or 0) >= 25]
        if heavy:
            out["warning"] = (
                f"LARGE cumulative drift: {', '.join(heavy)}. This is a real concession the "
                "design keeps, even where the current objective does not measure it. Justify "
                "any further step on these specifically, and prefer giving some back if the "
                "recent steps have stopped paying for themselves."
            )
        return out

    def _shared_context(latest: dict) -> None:
        """Attach the cross-run evidence every decision turn gets, in both
        serial and batch mode: what has been measured so far, how far the
        config has cumulatively drifted, and (batch only) how the last round's
        parallel candidates compared."""
        latest["measured_effects_so_far"] = orfs_ledger.render(ledger)
        drift = _drift_from_baseline()
        if drift:
            latest["drift_from_original_baseline"] = drift
        if nonlocal_state.get("last_round_comparison"):
            latest["last_round_comparison"] = nonlocal_state["last_round_comparison"]
        if nonlocal_state.get("round_insight"):
            latest["round_insight"] = nonlocal_state["round_insight"]

    def _ask_and_apply(iteration: int, latest_payload: dict, label: str) -> str:
        """One LLM turn: propose a change and apply it.

        Returns "applied" / "pass" / "give_up" / "retry" -- "retry" meaning the
        turn produced nothing usable and `feedback` now explains why, to be
        handed back verbatim on the next attempt.
        """
        nonlocal feedback, final_status, last_diagnosis_run
        current_tunables = get(read_tunables_remote.chia_remote(
            str(working_config_mk), schema_json))
        latest = dict(latest_payload)
        clock_now = latest.get("clock_period")
        if clock_now is not None:
            current_tunables.setdefault("CLOCK_PERIOD", clock_now)
        if feedback:
            latest["your_previous_reply_was_rejected"] = feedback
            feedback = None
        _shared_context(latest)

        # A stall (no real progress for STALL_THRESHOLD runs running) is
        # a case worth an extra, focused LLM turn root-causing it before the
        # next normal attempt.
        verdicts = [e.get("_verdict") for e in history]
        if history and _detect_stall(history, verdicts, STALL_THRESHOLD) and (
            last_diagnosis_run is None or len(history) - last_diagnosis_run >= STALL_REDIAGNOSE_EVERY
        ):
            diagnosis = _run_stall_diagnosis()
            if diagnosis:
                latest["stall_diagnosis"] = diagnosis
            last_diagnosis_run = len(history)

        prompt_text = _load_prompt(
            prompt_path, design_name, closure_criteria, locked,
            schema, current_tunables, latest,
            [{k: v for k, v in e.items() if k in
              ("run", "iteration", "tunables_changed", "status", "violations",
               "physical_metrics", "stage")}
             for e in history[-6:]],
            _iteration_goal_text(iteration, objective, objective_target),
        )

        t0 = time.time()
        with _Heartbeat(f"Agent turn ({label})"):
            cli = _prompt_with_backoff(llm, prompt_text, _append_trace)
        print(f"  LLM turn finished in {time.time()-t0:.1f}s (success={cli.success})")
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Iteration {iteration} "
            f"LLM Reasoning | Success: {cli.success}\n{cli.result}\n" + "-" * 60 + "\n"
        )
        if not cli.success:
            final_status = "llm_failed"
            feedback = None
            print("  (warning: LLM turn failed)")
            return "retry"

        sentinel, proposal, parse_error = _extract_proposal(cli.result)
        if sentinel == "PASS":
            return "pass"
        if sentinel == "GIVE_UP":
            return "give_up"
        if parse_error:
            feedback = parse_error
            print(f"  (warning: could not read a proposal: {parse_error})")
            return "retry"

        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] CALL: set_tunables\n"
            f"{json.dumps(proposal)}\n" + "-" * 60 + "\n"
        )
        applied = get(apply_tunables_remote.chia_remote(
            str(baseline_path), str(working_config_mk), schema_json,
            json.dumps(locked), json.dumps(proposal),
        ))
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] RETURN "
            f"{'SUCCESS' if applied.get('ok') else 'ERROR'}: set_tunables\n"
            f"{json.dumps(applied)}\n" + "-" * 60 + "\n"
        )
        if not applied.get("ok"):
            feedback = (f"Your proposed change was rejected: {applied.get('error')}. "
                        "Check the schema bounds and try a valid value.")
            print(f"  (warning: {feedback})")
            return "retry"
        print(f"  applied: {json.dumps(proposal)}")
        return "applied"

    def _build_proposal_prompt(iteration: int, other_candidates: list) -> str:
        """The prompt for one batch slot's decision turn.

        Split out from _propose_via_llm so a whole round's prompts can be
        built up front and their LLM calls dispatched concurrently -- the
        calls only need `opencode_creds: 0.01` each (chia's OpenCodeLLM.prompt),
        so a default capacity of 1.0 already admits ~100 at once and they do
        not serialise on that resource.
        """
        nonlocal feedback
        # NOT a read of the canonical `working_config_mk` -- batch mode never
        # writes a round's winner back to that file mid-run (only each slot's
        # own config.chia.slotN.mk changes; the canonical file is only synced
        # once, in wrap-up, before signoff). Reading it here showed every
        # slot's decision prompt a config frozen at the pre-loop baseline for
        # the entire run, silently defeating the prompt's own "a knob already
        # sitting at the value you were going to suggest cannot be tried"
        # freshness check. `history` is always non-empty by the time this is
        # called (the batch path's opening move runs before `_decide_batch`
        # ever fires), so the round's actual winning config is always
        # available here -- same source the referee prompt already uses
        # correctly via `history[-1].get("config")`.
        current_tunables = dict(history[-1]["config"]) if history else get(
            read_tunables_remote.chia_remote(str(working_config_mk), schema_json))
        latest = dict(history[-1]["_payload"]) if history else {}
        clock_now = latest.get("clock_period")
        if clock_now is not None:
            current_tunables.setdefault("CLOCK_PERIOD", clock_now)
        if feedback:
            latest["your_previous_reply_was_rejected"] = feedback
            feedback = None
        _shared_context(latest)
        if other_candidates:
            # Tells the model what other slots in this same round are already
            # trying, so independent LLM calls within one round diversify
            # instead of converging on the same idea -- prompts/orfs_propose.md
            # documents this key's meaning. Empty on the concurrent first pass
            # (nothing has been proposed yet), populated for the sequential
            # top-up calls that fill slots the first pass lost.
            latest["other_candidates_this_round"] = [c["suggested_changes"] for c in other_candidates]

        return _load_prompt(
            prompt_path, design_name, closure_criteria, locked,
            schema, current_tunables, latest,
            [{k: v for k, v in e.items() if k in
              ("run", "iteration", "tunables_changed", "status", "violations",
               "physical_metrics", "stage")}
             for e in history[-6:]],
            _iteration_goal_text(iteration, objective, objective_target),
        )

    def _parse_proposal_reply(cli, iteration: int, slot: int) -> tuple:
        """Turn one decision turn's raw reply into (candidate_or_None, gave_up)."""
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Iteration {iteration} "
            f"Batch LLM Slot {slot} Reasoning | Success: {cli.success}\n{cli.result}\n"
            + "-" * 60 + "\n"
        )
        if not cli.success:
            return None, False
        sentinel, proposal, parse_error = _extract_proposal(cli.result)
        if sentinel == "GIVE_UP":
            return None, True
        if sentinel == "PASS" or parse_error or not proposal:
            return None, False
        return {"suggested_changes": proposal, "reasoning": "LLM proposal (batch slot)."}, False

    def _propose_via_llm(iteration: int, other_candidates: list, slot: int = 0) -> tuple:
        """One LLM turn proposing ONE --batch-size candidate, reusing
        _ask_and_apply's prompt-building/parsing but never calling
        apply_tunables_remote itself -- the caller (_decide_batch) applies
        the proposal to its own slot.

        `slot` is the slot index this proposal will occupy if it succeeds
        (i.e. the caller's current candidate count, NOT its loop counter --
        a failed call leaves the slot free for the next one). It only labels
        the trace/console output, so the dashboard can attribute each turn's
        reasoning to the slot that actually ran it instead of guessing from
        ordering.

        Returns (candidate_or_None, gave_up). A parse failure or CLOSURE:
        PASS just drops this slot (gave_up=False) rather than blocking the
        round; only an explicit CLOSURE: GIVE_UP sets gave_up=True.
        """
        nonlocal feedback
        prompt_text = _build_proposal_prompt(iteration, other_candidates)
        t0 = time.time()
        with _Heartbeat(f"Batch LLM slot {slot} (iteration {iteration})"):
            cli = _prompt_with_backoff(llm, prompt_text, _append_trace)
        print(f"  [slot {slot}] batch LLM slot finished in {time.time()-t0:.1f}s "
              f"(success={cli.success})")
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Iteration {iteration} "
            f"Batch LLM Slot {slot} Reasoning | Success: {cli.success}\n{cli.result}\n"
            + "-" * 60 + "\n"
        )
        if not cli.success:
            return None, False
        sentinel, proposal, parse_error = _extract_proposal(cli.result)
        if sentinel == "GIVE_UP":
            return None, True
        if sentinel == "PASS" or parse_error or not proposal:
            return None, False
        return {"suggested_changes": proposal, "reasoning": "LLM proposal (batch slot)."}, False

    def _decide_batch(iteration: int) -> Optional[list]:
        """Up to `batch_size` DISTINCT candidates for the next parallel round,
        or None if nothing usable came back at all. Every candidate is its own
        real LLM call; nothing here decides a tunable value without asking the
        model.

        Two passes (see the comments inline): all `batch_size` decision turns
        fire CONCURRENTLY, then any slot lost to a bad reply, a no-op or a
        duplicate is topped up by sequential calls that can see what was
        already accepted. That keeps the decision phase from scaling with
        batch width -- it was the dominant cost of a wide round -- while still
        giving the slots that actually collided a chance to differentiate.

        Duplicates and no-ops are rejected in code, not left to the prompt: the
        `other_candidates_this_round` hint is advisory and models do ignore it
        (observed live, both slots of a round independently returned an
        identical SETUP_SLACK_MARGIN=2.0), and either mistake spends a whole
        flow run -- minutes -- reproducing a result already in hand. If the
        bounded top-up can't find anything new the round simply runs narrower,
        which is strictly better than running the same config twice.
        """
        nonlocal feedback

        def _is_noop(changes: dict) -> bool:
            """True when every proposed value already equals the current one.

            Sibling-dedup only compares candidates against each other, so it
            cannot catch this: a proposal that re-sets a knob to the value it
            already holds is unique within the round yet produces a bit-identical
            result, burning a full flow run to reproduce the round's own
            starting point. Observed live -- a slot proposed CORE_UTILIZATION=33
            when the config was already at 33, and the run came back with
            "(baseline run -- nothing changed yet)".

            A `null` (revert-to-baseline) is always treated as a real change:
            whether it differs depends on the design's original value, which
            isn't worth resolving here, and wrongly rejecting a genuine revert
            is worse than occasionally allowing a redundant one.
            """
            if not history:
                return False
            cur = dict(history[-1].get("config") or {})
            cp = history[-1].get("clock_period")
            if cp is not None:
                cur.setdefault("CLOCK_PERIOD", cp)
            for k, v in (changes or {}).items():
                if v is None or k not in cur:
                    return False
                try:
                    if float(cur[k]) != float(v):
                        return False
                except (TypeError, ValueError):
                    if str(cur[k]).strip() != str(v).strip():
                        return False
            return bool(changes)

        candidates: list = []
        seen: set = set()

        def _accept(proposal: Optional[dict]) -> bool:
            """Vet one proposal and keep it if it's worth a flow run.

            Rejects the two ways a round can spend minutes reproducing a
            result it already has: a value that's already set (no-op) and a
            change another slot is already testing (duplicate). Both set
            `feedback` so a follow-up call is told why, which matters because
            the advisory `other_candidates_this_round` hint demonstrably does
            not stop a model repeating itself.
            """
            nonlocal feedback
            if not proposal:
                return False
            key = json.dumps(proposal["suggested_changes"], sort_keys=True)
            if _is_noop(proposal["suggested_changes"]):
                _append_trace(
                    f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: No-op batch candidate "
                    f"rejected (every value already set)\n{key}\n" + "-" * 60 + "\n"
                )
                print(f"  (no-op candidate {key} -- already the current value)")
                feedback = (
                    f"Your proposal {key} sets values the configuration already has, so running "
                    "it would spend a full flow run reproducing the result you were just given. "
                    "Propose a change that actually differs from the current configuration."
                )
                return False
            if key in seen:
                _append_trace(
                    f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Duplicate batch "
                    f"candidate rejected (another slot this round is already testing it)\n"
                    f"{key}\n" + "-" * 60 + "\n"
                )
                print(f"  (duplicate candidate {key})")
                feedback = (
                    f"Your proposal {key} is already being tested by another slot in this "
                    "same round, so running it again would waste a full flow run "
                    "reproducing a result you are about to get anyway. Propose a change "
                    "targeting a DIFFERENT knob than the ones listed in "
                    "other_candidates_this_round."
                )
                return False
            seen.add(key)
            candidates.append(proposal)
            return True

        # Pass 1: fire every slot's decision turn CONCURRENTLY.
        #
        # These were sequential so each slot could see earlier picks and
        # diversify, but that made the decision phase scale with width while
        # the flow phase stayed flat: at 62s median per call, width 6 spent
        # ~371s deciding against ~90s running, i.e. 82% of the round not doing
        # physical design. Concurrency is free here -- chia's
        # OpenCodeLLM.prompt asks for opencode_creds: 0.01, so a default
        # capacity of 1.0 admits ~100 at once and they never queued on it.
        #
        # The cost is that no slot sees any other's pick, so convergence (and
        # therefore duplicate rejection) rises. Pass 2 repairs exactly that,
        # and only for the slots actually lost.
        if batch_size > 1:
            prompt_text = _build_proposal_prompt(iteration, [])
            t0 = time.time()
            active_llm = llm.current()
            futures = [active_llm.prompt.chia_remote(active_llm, prompt_text, tools=[])
                       for _ in range(batch_size)]
            with _Heartbeat(f"Batch decisions ({batch_size} concurrent LLM calls, "
                            f"iteration {iteration})"):
                try:
                    replies = get(futures)
                except Exception as exc:
                    # Same fix as _run_flow_batch's WORKER_DIED handling below,
                    # applied here: get() on a list re-raises the first failure
                    # it finds regardless of the other N-1 futures, which are
                    # often succeeding normally (observed live: InvalidRequestError,
                    # "Requests ending with a model turn are not supported", from
                    # one concurrent call on the single hello_opencode container
                    # -- crashed the whole driver mid-run rather than costing just
                    # that one slot). Re-fetch each future on its own instead; an
                    # already-failed one re-raises immediately (Ray caches it, no
                    # re-run), an already-succeeded one returns just as fast.
                    print(f"  (warning: a batch LLM call failed: {exc} -- "
                          "salvaging the round's other replies instead of losing all of them)")
                    replies = []
                    for fut in futures:
                        try:
                            replies.append(get(fut))
                        except Exception as fut_exc:
                            replies.append(SimpleNamespace(
                                success=False, result=f"LLM call raised: {fut_exc}"))
            print(f"  {batch_size} concurrent LLM decisions finished in {time.time()-t0:.1f}s")
            for cli in replies:
                proposal, _gave_up = _parse_proposal_reply(cli, iteration, len(candidates))
                _accept(proposal)

        # Pass 2: sequentially top up whatever pass 1 failed to fill -- a
        # dropped reply, a no-op or a duplicate. These calls DO see the
        # already-accepted candidates, so they are the ones positioned to
        # deliberately pick something different. Bounded so a model stuck
        # repeating itself cannot spin the round.
        attempts = 0
        while len(candidates) < batch_size and attempts < batch_size * 3:
            attempts += 1
            # len(candidates) is the slot this proposal lands in if it works
            # -- a failed call leaves that slot open for the next attempt,
            # so the label always matches the slot that actually runs it.
            proposal, _gave_up = _propose_via_llm(iteration, candidates, len(candidates))
            _accept(proposal)

        # A rejection message left unconsumed (the retry budget ran out on one)
        # is about a round that's now over -- carrying it into the next round
        # would scold the next call for something it never did.
        if feedback and ("already being tested by another slot" in feedback
                         or "values the configuration already has" in feedback):
            feedback = None

        if not candidates:
            # Every slot's LLM call this round produced nothing usable.
            return None
        return candidates

    def _run_flow_batch(candidates: list, iteration: int) -> list:
        """Apply each candidate to its own slot's config, dispatch all of
        them as concurrent Ray futures, then collect the whole round with
        ONE get([...]) call -- the driver still never lets the LLM call
        anything, it just now deliberately runs several of its OWN blocking
        calls at once instead of one at a time (see README.md's "Parallel
        batches" section for why this doesn't reintroduce the old MCP
        overlapping-call hazard).
        """
        nonlocal feedback
        # The round's starting point must be the most recent entry with a
        # real, usable config -- history[-1] alone breaks this the moment a
        # WHOLE round crashes (every slot), because that round's own two
        # crashed entries are then the newest history has, and a crashed
        # entry's "config" is exactly the crash-triggering values. Anchoring
        # the next round on it doesn't recover, it just re-applies the same
        # bad value again under whatever new change is layered on top --
        # observed live on ihp-sg13g2's i2c-gpio-expander: DIE_AREA_SCALE=0.92
        # crashed floorplan once, never got reverted because the round it
        # crashed in had no survivor, and five consecutive rounds after it
        # crashed the same way regardless of which other knob was touched,
        # since every one of them still carried that same 0.92 forward.
        # Skipping back to the most recent non-crashed entry (closed or
        # merely violating -- both have real metrics and a real config,
        # only "crashed" means neither) is the same recovery the wrap-up
        # code already does when restoring the best run before signoff,
        # just applied one round earlier.
        starting_prev = next((e for e in reversed(history) if not e.get("crashed")), None)
        if starting_prev is None:
            starting_prev = history[-1] if history else None
        winner_config = dict(starting_prev["config"]) if starting_prev else {}
        base_run_index = len(history) + 1

        slots = []
        for i, cand in enumerate(candidates):
            run_index = base_run_index + i
            paths = slot_paths_cache[i]
            # A slot that LOST an earlier round still has that attempt's
            # tunables sitting in its own config.chia.slotN.mk -- reset it to
            # the round's actual starting point (the previous round's
            # winner) before layering this round's candidate on top, or a
            # losing slot's abandoned knobs would silently keep compounding
            # into every later round it's reused for (same "restore" pattern
            # the wrap-up code below already uses to reset the canonical
            # config to the best run's exact tunables).
            slot_current = get(read_tunables_remote.chia_remote(
                str(paths["working_config_mk"]), schema_json))
            request = dict(winner_config)
            for key in slot_current:
                request.setdefault(key, None)
            request.update(cand["suggested_changes"])
            _append_trace(
                f"\n[{datetime.datetime.now().isoformat()}] CALL: set_tunables (slot {i}, run {run_index})\n"
                f"{json.dumps(cand['suggested_changes'])}\n" + "-" * 60 + "\n"
            )
            applied = get(apply_tunables_remote.chia_remote(
                str(baseline_path), str(paths["working_config_mk"]), schema_json,
                json.dumps(locked), json.dumps(request),
            ))
            _append_trace(
                f"\n[{datetime.datetime.now().isoformat()}] RETURN "
                f"{'SUCCESS' if applied.get('ok') else 'ERROR'}: set_tunables (slot {i})\n"
                f"{json.dumps(applied)}\n" + "-" * 60 + "\n"
            )
            if not applied.get("ok"):
                # Drop the slot instead of running it. The config on disk is
                # unchanged, so dispatching would spend a full flow run
                # (minutes) re-deriving the round's own starting point and then
                # record it as if it were a real experiment. The serial path
                # has always checked this before running; the batch path did
                # not, which made an invalid proposal cost a flow run rather
                # than a retry. Reachable in practice: the referee's note is
                # free text and can name a knob that doesn't exist (observed:
                # "OPT_POST_GRT_WASP" for OPT_POST_GRT_WNS), and a slot copying
                # that name gets rejected by the schema whitelist.
                print(f"  [slot {i}] apply rejected ({applied.get('error')}) -- slot dropped")
                feedback = (f"Your proposed change was rejected: {applied.get('error')}. "
                            "Check the schema bounds and use exact key names from it.")
                continue
            slots.append((run_index, paths, cand, i))
            print(f"  [slot {i}] applying: {json.dumps(cand['suggested_changes'])}")

        if not slots:
            # Every candidate failed to apply -- nothing to run this round.
            return []

        futures = []
        for run_index, paths, cand, _slot_i in slots:
            _append_trace(
                f"\n[{datetime.datetime.now().isoformat()}] CALL: run_full_flow_and_summarize "
                f"(slot {paths['flow_variant']}, run {run_index})\n\n" + "-" * 60 + "\n"
            )
            futures.append(run_flow_remote.chia_remote(
                flow_dir, str(paths["working_config_mk"]), paths["reports_root"], paths["results_root"],
                extra_env, stage_timeout_seconds, container_run_dir, run_index, paths["flow_variant"],
            ))
        with _Heartbeat(f"Batch round ({len(futures)} parallel flow runs, iteration {iteration})"):
            try:
                results = get(futures)
            except Exception as exc:
                # A single dead Ray worker (observed live: OOM-killed mid
                # detailed-route on a large design at wide batch-size, Ray
                # marks the task FAILED/WORKER_DIED) used to take the whole
                # driver down here -- get() on a list re-raises the first
                # failure it finds with no regard for the other N-1 futures,
                # which were succeeding normally. Re-fetch each one on its
                # own instead: a future that already failed re-raises the
                # same error immediately (Ray caches it, doesn't re-run the
                # task) and gets turned into a crashed entry for just that
                # slot; a future that already succeeded returns its cached
                # result just as fast. This is the only thing that changes --
                # it does not retry or resubmit any flow run.
                print(f"  (warning: a flow run in this round failed at the Ray level: {exc} "
                      "-- salvaging the round's other results instead of losing all of them)")
                results = []
                for fut in futures:
                    try:
                        results.append(get(fut))
                    except Exception as fut_exc:
                        results.append({
                            "crashed": True,
                            "fatal_error": f"Ray task failed (worker died or crashed): {fut_exc}",
                        })

        entries = []
        # slot_index comes from the tuple, NOT from enumerate: a slot dropped
        # above (failed apply) would otherwise shift every later slot's label
        # down one and misattribute its results in the ledger and the GUI.
        for (run_index, paths, cand, slot_index), result in zip(slots, results):
            print(f"  [slot {paths['flow_variant']}] run {run_index} finished "
                  f"-- {result.get('status') or result.get('fatal_error')}")
            try:
                config_under_test = get(read_tunables_remote.chia_remote(
                    str(paths["working_config_mk"]), schema_json))
            except Exception as exc:
                # Purely informational (what got baked into this slot's working
                # config, for the trace/ledger payload) -- a transient Ray-level
                # error here must not cost the whole round's already-completed
                # flow results the way an unguarded get() previously did (this
                # call sat right after the salvage logic above but wasn't
                # itself covered by it). Fall back to the candidate's own
                # requested diff, which is the next best description available.
                print(f"  (warning: could not re-read slot {paths['flow_variant']}'s config "
                      f"after the run ({exc}) -- falling back to the requested diff)")
                config_under_test = cand.get("suggested_changes", {})
            entries.append((run_index, config_under_test, result, slot_index))

        # Sorted worst-first so history[-1] ends up as the round's best
        # result -- that's what the next round's LLM calls see as "latest"
        # (via history[-1]["_payload"]), so each new round is anchored on
        # the winning config from the last one, not an arbitrary slot.
        # `_round_rank_key` (not a local tier-only key) so this anchor is the
        # same run `closed_entry` and `won_this_round` name; when several slots
        # close, a tier-only key ties them all and hands `history[-1]` to
        # whichever slot happened to be listed last.
        entries.sort(key=lambda item: _round_rank_key(item[2]), reverse=True)
        built = []
        for run_index, config_under_test, result, slot_index in entries:
            built.append(_build_history_entry(
                result, run_index, iteration, config_under_test, starting_prev,
                trace_label=f"(batch run {run_index})", slot=slot_index,
            ))

        # The round as a controlled experiment, recorded once and reused by
        # every consumer: the ledger (measured knob effects), the referee
        # (cross-slot synthesis) and next round's prompts.
        comparison = _round_comparison(starting_prev, built)
        orfs_ledger.observe_round(ledger, starting_prev, built)
        orfs_ledger.save(ledger, run_dir / "ledger.json")
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Round comparison "
            f"(iteration {iteration})\n{json.dumps(comparison, indent=2)}\n" + "-" * 60 + "\n"
        )
        _run_round_referee(iteration, comparison)
        nonlocal_state["last_round_comparison"] = comparison
        return built

    last_closed: Optional[dict] = None

    for it in range(1, max_iterations + 1):
        goal_label = "close the design" if it == 1 else (
            f"raise clock frequency (beat CLOCK_PERIOD {objective_target})" if objective == "clock"
            else f"reduce area (beat core_area {objective_target})")
        print(f"\n{'='*60}\nIteration {it}/{max_iterations} -- {goal_label}\n{'='*60}")
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Starting Iteration {it} "
            f"| Model: {model} | Goal: {goal_label}\n\n" + "-" * 60 + "\n"
        )

        closed_entry = None
        stop_everything = False
        step = 0

        # No run cap: this iteration keeps going until it closes, or the model
        # itself calls it (CLOSURE: GIVE_UP / a PASS that doesn't beat the
        # objective). Deliberate -- "the iteration ends when it closes" is the
        # whole point, and a numeric ceiling would just cut that off early on
        # a design that's still making genuine progress. A model that never
        # converges and never gives up will run indefinitely; that's a model
        # problem to notice and stop by hand, not a case to special-case here.
        if batch_size == 1:
            # ---------------------------------------------------- serial path
            # Deliberately kept as its own branch rather than generalized
            # into the batch path below: this encodes several hard-won,
            # subtle sequencing fixes (the opening-move special case, the
            # retry-without-burning-a-flow-run loop, stall-diagnosis
            # throttling) that would be risky to blindly widen to K-wide
            # rounds in one pass. batch_size=1 is provably byte-identical to
            # this project's behavior before --batch-size existed.

            # From iteration 2 on the config already closes, so running it
            # again first would just reproduce the previous iteration's
            # answer -- ask for the opening move toward the new objective
            # before spending a flow run.
            need_opening_move = it > 1
            while True:
                step += 1
                if need_opening_move:
                    latest = history[-1]["_payload"] if history else {}
                    outcome = _ask_and_apply(it, latest, f"iteration {it} opening move")
                    if outcome == "give_up":
                        final_status = "agent_gave_up"
                        stop_everything = True
                        break
                    if outcome in ("retry", "pass"):
                        # "pass" here means the model saw nothing worth trying
                        # for this objective -- treat it as the iteration
                        # being unable to improve, not as overall success.
                        if outcome == "pass":
                            print("  agent sees no further improvement for this objective.")
                            stop_everything = True
                            break
                        continue
                    need_opening_move = False

                entry = _run_flow_once(len(history) + 1, it)

                if _iteration_done(it, entry):
                    closed_entry = entry
                    break

                # A "retry" outcome (empty/unparseable reply) means nothing was
                # applied and the config is unchanged -- re-prompt with the
                # rejection feedback instead of burning a whole extra flow run
                # (60s-15min) just to give the model another chance to reply.
                while True:
                    outcome = _ask_and_apply(it, entry["_payload"], f"iteration {it} run {step}")
                    if outcome != "retry":
                        break
                if outcome == "give_up":
                    final_status = "agent_gave_up"
                    stop_everything = True
                    break
                if outcome == "pass":
                    if str(entry.get("status", "")).startswith("CLOSED"):
                        # Closed, but did not beat the objective (or this is
                        # iteration 1, where closing is the whole point).
                        if it == 1 or objective_target is None:
                            closed_entry = entry
                        else:
                            print("  agent sees no further improvement for this objective.")
                            stop_everything = True
                        break
                    feedback = ("You replied CLOSURE: PASS but the latest run is "
                                f"{entry.get('status') or 'a crash'}, not closed. Keep tuning.")
                    print(f"  (warning: {feedback})")
        else:
            # ----------------------------------------------------- batch path
            # Iteration 1's very first ever run (history completely empty) is
            # always a single plain baseline run at the canonical path --
            # there's no metric/violation data yet for any LLM call to react
            # to. Every round after that (including every round of iteration
            # 2+, which sees the previous iteration's already-CLOSED entry as
            # `latest` and reasons about it via the prompt's own "Status is
            # CLOSED" DECISION TABLE row -- no separate opening-move
            # special-case needed) runs `batch_size`-wide.
            if not history:
                entry = _run_flow_once(1, it)
                if _iteration_done(it, entry):
                    closed_entry = entry

            while closed_entry is None:
                step += 1
                candidates = _decide_batch(it)
                if candidates is None:
                    final_status = "agent_gave_up"
                    stop_everything = True
                    break
                entries = _run_flow_batch(candidates, it)
                closed = [e for e in entries if _iteration_done(it, e)]
                if closed:
                    closed_entry = min(closed, key=_rank_key)

        record = {
            "iteration": it,
            "goal": "close" if it == 1 else objective,
            "target_to_beat": objective_target,
            "runs": [e["run"] for e in history if e.get("iteration") == it],
            "closed": closed_entry is not None,
        }
        if closed_entry is not None:
            last_closed = closed_entry
            final_status = "closed"
            objective_target = _objective_value(closed_entry)
            record.update({
                "closed_on_run": closed_entry["run"],
                "achieved": objective_target,
                "physical_metrics": closed_entry.get("physical_metrics"),
                "violations": closed_entry.get("violations"),
            })
            print(f"  iteration {it} closed on run {closed_entry['run']} "
                  f"({objective} = {objective_target})")
        iterations.append(record)

        if stop_everything:
            # The model itself ended this iteration without closing (gave up,
            # or saw no further improvement toward the objective). If nothing
            # has ever closed across the whole run, that is a real failure;
            # if an earlier iteration DID close, its result is still the
            # final answer -- this iteration just couldn't improve on it.
            #
            # final_status was left at whatever this iteration's abort path set
            # it to ("agent_gave_up") in BOTH cases -- it needs correcting back
            # to "closed" here when an earlier iteration's result is the real
            # final answer, or run_signoff's `final_status == "closed"` gate
            # (and the reported top-level status) wrongly call a run that
            # closed cleanly a give-up, and skip signoff on a real result.
            if last_closed is None:
                final_status = "no_closure"
            else:
                final_status = "closed"
            break

    # ------------------------------------------------------------- wrap up
    # The final answer is the last iteration that actually closed -- not
    # _best_run's closest-to-closing fallback, and not whatever the last
    # (possibly failed) iteration left behind.
    best = last_closed or _best_run(history)
    summary = {
        "status": final_status,
        "objective": objective,
        "iterations_run": len(iterations),
        "iterations_closed": sum(1 for r in iterations if r["closed"]),
        "runs_executed": len(history),
        "run_dir": str(run_dir),
        "best_run": best["run"] if best else None,
        "final_objective_value": objective_target,
        "llm_models_used": llm.used,
        "iterations": [{k: v for k, v in r.items() if k != "config"} for r in iterations],
    }

    # Signoff runs against the BEST configuration, not whatever was tried
    # last -- restore it and rebuild at the canonical path first unless that
    # path already holds the best run's own output.
    #
    # Two separate ways it can be stale, and batch mode needs both. The obvious
    # one is serial: some later run overwrote the canonical path. The other is
    # that the best run was executed in a *slot* -- its artifacts are in
    # `<design>/slotN/`, and the canonical `base/` directory still holds
    # whatever last ran there, which in batch mode is iteration 1's baseline
    # run. Checking only `best["run"] != history[-1]["run"]` misses that
    # entirely: `_run_flow_batch` sorts each round worst-first precisely so
    # `history[-1]` IS the round winner, so the run-number test is False exactly
    # when the slot test needs to fire. Observed live on riscv32i 6-wide --
    # signoff reported DRC/LVS for run 1's baseline layout while the promoted
    # `final.gds` was run 25's (md5-confirmed as two different layouts), i.e.
    # the signoff verdict described a design that was never the answer.
    #
    # A rebuild is only needed when the best run's own artifacts are gone. A
    # batch winner's slot tree still holds its exact GDS unless a LATER run
    # reused that slot (whose `make clean_all` is scoped to that FLOW_VARIANT
    # and wipes it) -- run indices increase monotonically, so "reused" is just
    # "some higher-numbered run has the same slot", answerable from `history`
    # with no filesystem access. When the tree survives, signoff runs against
    # that variant directly: no extra flow run, and no question of whether a
    # rebuild reproduces the same layout bit-for-bit.
    best_slot = best.get("slot") if best is not None else None
    slot_still_holds_best = best_slot is not None and not any(
        e.get("slot") == best_slot and (e.get("run") or 0) > best["run"] for e in history
    )
    canonical_is_stale = best is not None and history and (
        best["run"] != history[-1]["run"]     # serial: something else ran last
        or best_slot is not None              # batch: best was built in slotN/
    )
    if canonical_is_stale and not slot_still_holds_best:
        print(f"\nRestoring best config (run {best['run']}) before signoff...")
        # Traced (not just printed) because this rebuild can take as long as any
        # other flow run -- without a marker the dashboard shows a dead table for
        # minutes with no indication which run is being prepared for signoff.
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] "
            f"SYSTEM: Restoring best config (run {best['run']}) before signoff\n"
            + "-" * 60 + "\n"
        )
        # `apply_tunables_remote` MERGES onto whatever the target config already
        # holds, so every schema key the best run didn't set is explicitly sent
        # as null (= revert to baseline). Nulling only the keys in
        # `history[-1]["config"]` was enough while the last run and the canonical
        # path were the same thing; in batch mode they aren't, and the canonical
        # config is whatever was last written there rather than the previous
        # run's. Keying off the schema instead makes the restored config exactly
        # the best run's, whatever the target happened to contain.
        restore = dict(best["config"])
        for key in json.loads(schema_json):
            if not key.startswith("_"):      # skip the schema's own _comment
                restore.setdefault(key, None)
        get(apply_tunables_remote.chia_remote(
            str(baseline_path), str(working_config_mk), schema_json,
            json.dumps(locked), json.dumps(restore),
        ))
        get(run_flow_remote.chia_remote(
            flow_dir, str(working_config_mk), str(reports_root), results_root,
            extra_env, stage_timeout_seconds, container_run_dir, best["run"],
        ))
    if best is not None:
        _promote_best_gds(run_dir, best["run"], _append_trace)

    # `make` (synth through metadata) never runs drc/lvs itself -- "flow
    # completed" and "DRC/LVS clean" are separate claims. Only worth the
    # KLayout runtime once the design actually closed.
    if run_signoff and final_status == "closed":
        print("\nRunning signoff (make drc / make lvs)...")
        signoff_log_dir = f"{container_run_dir}/signoff_logs" if container_run_dir else None

        # Point the checks at the tree that actually holds the best run's GDS,
        # and hand the worker the checksum of the GDS we promoted so it can
        # confirm that's what it read. The driver can't stat the worker's
        # filesystem, so this is the only way the verdict can be tied to a
        # specific layout rather than assumed.
        sign_config_mk, sign_reports, sign_results = (
            str(working_config_mk), str(reports_root), results_root)
        sign_variant = None
        if slot_still_holds_best:
            sp = _slot_paths(str(reports_root), working_config_mk, best_slot)
            sign_config_mk = str(sp["working_config_mk"])
            sign_reports, sign_results = str(sp["reports_root"]), sp["results_root"]
            sign_variant = sp["flow_variant"]
            print(f"  (signing off run {best['run']} in its own {sign_variant} tree)")
        final_gds = run_dir / "final.gds"
        expect_md5 = None
        if final_gds.exists():
            _h = hashlib.md5()
            with final_gds.open("rb") as _fh:
                for _chunk in iter(lambda: _fh.read(1 << 20), b""):
                    _h.update(_chunk)
            expect_md5 = _h.hexdigest()
        # Emitted *before* the call so the dashboard can highlight the run being
        # signed off while KLayout is still grinding, not only once it returns.
        _append_trace(
            f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Signoff starting on run "
            f"{best['run'] if best is not None else 'unknown'} (drc/lvs)\n" + "-" * 60 + "\n"
        )
        try:
            signoff = get(run_signoff_remote.chia_remote(
                flow_dir, sign_config_mk, sign_reports,
                sign_results, extra_env, stage_timeout_seconds, signoff_log_dir,
                sign_variant, expect_md5,
            ))
            summary["signoff"] = signoff
            print(f"  signoff: {json.dumps(signoff, indent=2)}")
            # Loud, and recorded in summary.json: a verdict for the wrong layout
            # is worse than no verdict, because it reads exactly like a real one.
            if signoff.get("signed_off_gds", {}).get("matches_best") is False:
                print(f"  *** WARNING: {signoff.get('warning')}")
            _append_trace(
                f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Signoff (drc/lvs) result\n"
                f"{json.dumps(signoff, indent=2)}\n" + "-" * 60 + "\n"
            )
        except Exception as exc:
            summary["signoff_error"] = str(exc)
            print(f"  (warning: signoff failed to run: {exc})")
            # Also traced, or the dashboard leaves the row pinned as
            # "signoff running" forever on a signoff that already died.
            _append_trace(
                f"\n[{datetime.datetime.now().isoformat()}] SYSTEM: Signoff (drc/lvs) failed\n"
                f"{exc}\n" + "-" * 60 + "\n"
            )

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--design-name", default="gcd",
        help="Name of the design being tuned. This is a LABEL, not a path -- "
             "the design itself comes from --design-config-mk/--reports-root -- "
             "but it keys the ledger's identity (--seed-ledger refuses to carry "
             "a ledger across designs by comparing this) and fills $DESIGN_NAME "
             "in every prompt, so a stale value mislabels both. Pass it "
             "explicitly whenever you aren't running gcd.",
    )
    ap.add_argument("--flow-dir", default=DEFAULT_FLOW_DIR)
    ap.add_argument("--design-config-mk", required=True)
    ap.add_argument("--reports-root", required=True)
    ap.add_argument("--run-dir", default=None)
    ap.add_argument(
        "--max-iterations", type=int, default=3,
        help="Number of ITERATIONS. Iteration 1 closes the design; each one "
             "after that pushes --objective further and must close again.",
    )
    ap.add_argument(
        "--objective", choices=OBJECTIVES, default="area",
        help="What to optimize once the design first closes: 'clock' drives "
             "CLOCK_PERIOD down (higher frequency), 'area' drives core_area down. "
             "Ignored by iteration 1, which only cares about closing.",
    )
    ap.add_argument("--model", default="google/gemini-3.6-flash")
    ap.add_argument(
        "--closure-criteria", default=None,
        help="Overrides the closure target given to the LLM (e.g. a specific "
             "utilization/area bound for this design). Defaults to a "
             "design-agnostic 'no violations, don't over-inflate area' target.",
    )
    ap.add_argument(
        "--minimal-schema", action="store_true",
        help="Use the reduced 12-tunable schema (orfs_tunables_schema_minimal.json) "
             "instead of the full 24-tunable one, to test whether fewer options "
             "improves model reliability.",
    )
    ap.add_argument(
        "--prompt-path", default=DEFAULT_PROMPT_PATH,
        help="Path to the proposal prompt template "
             "(default: prompts/orfs_propose.md). The LLM reads the flow "
             "report from this prompt and replies with a JSON change set; "
             "it has no tools and never runs the flow itself.",
    )
    ap.add_argument(
        "--diagnose-prompt-path", default=DEFAULT_DIAGNOSE_PROMPT_PATH,
        help="Path to the stall-diagnosis prompt template "
             "(default: prompts/orfs_diagnose.md). Only used when the last "
             f"{STALL_THRESHOLD} runs made no real progress (all REGRESSED/"
             "UNCHANGED) -- see _detect_stall.",
    )
    ap.add_argument(
        "--referee-prompt-path", default=DEFAULT_REFEREE_PROMPT_PATH,
        help="Path to the parallel-round referee prompt template "
             "(default: prompts/orfs_referee.md). Only used with --batch-size "
             "> 1: one extra LLM turn per round that reads every slot's result "
             "side by side and writes the cross-slot note the next round's "
             "calls all see.",
    )
    ap.add_argument(
        "--seed-ledger", default=None, metavar="LEDGER_JSON",
        help="Warm-start the measured-effects ledger from a previous run's "
             "ledger.json (e.g. orfs_runs/<earlier-run>/ledger.json). Without "
             "this, every run re-learns from zero what earlier runs already "
             "paid flow-run minutes to measure. Refused if that ledger was "
             "recorded for a different design -- a knob's effect belongs to "
             "one design at one baseline, and importing another's would look "
             "like evidence while being noise.",
    )
    ap.add_argument(
        "--skip-referee", action="store_true",
        help="Don't run the per-round referee turn. Saves one LLM call per "
             "round, at the cost of nothing ever reasoning ACROSS the parallel "
             "slots -- they go back to being independent sessions that merely "
             "share a starting config.",
    )
    ap.add_argument(
        "--resume-config", action="store_true",
        help="Continue from the tunables the previous run left in "
             "config.chia.mk instead of resetting to the design's pristine "
             "baseline. Off by default: every run starts clean so its "
             "baseline measurement is reproducible.",
    )
    ap.add_argument(
        "--skip-signoff", action="store_true",
        help="Don't run standalone KLayout DRC/LVS (`make drc`/`make lvs`) after "
             "a successful close. On by default -- 'flow completed' and 'DRC/LVS "
             "clean' are different claims, and `make` alone never runs the second. "
             "Skip this if the platform has no KLayout DRC/LVS deck configured, "
             "or to save the extra runtime while iterating.",
    )
    ap.add_argument("--ld-library-path", default=DEFAULT_LD_LIBRARY_PATH)
    ap.add_argument(
        "--stage-timeout-seconds", type=int, default=3600,
        help="Per-stage (synth/floorplan/place/cts/route/finish) timeout passed to "
             "run_flow_remote. The default (3600s) was sized around gcd-scale designs; a "
             "larger design's route stage can still be genuinely converging when it fires "
             "(observed on aes/sky130hd: still improving, down to 41 violations, when the "
             "default killed it at exactly 3600s) -- raise this for anything bigger than a "
             "small example design rather than let every attempt burn a full hour on a crash.",
    )
    ap.add_argument("--ray-address", default="auto")
    ap.add_argument(
        "--lock", action="append", default=[], metavar="KEY=VALUE",
        help="Hard-constrain a tunable to a fixed value the LLM can never change "
             "(repeatable, e.g. --lock CORE_UTILIZATION=38 --lock MAX_ROUTING_LAYER=met5).",
    )
    ap.add_argument(
        "--batch-size", type=int, default=1,
        help="Run this many flow executions concurrently per round instead of "
             "one at a time (see README.md's 'Parallel batches' section). "
             "Requires that many 'orfs_run' Ray workers (cluster.yaml's "
             "hello_orfs.num_workers) to actually run in parallel rather than "
             "queue. Default 1 preserves today's exact serial behavior.",
    )
    args = ap.parse_args()
    if args.batch_size < 1:
        ap.error("--batch-size must be >= 1")

    locked_tunables: dict = {}
    for entry in args.lock:
        if "=" not in entry:
            ap.error(f"--lock expects KEY=VALUE, got {entry!r}")
        key, value = entry.split("=", 1)
        locked_tunables[key.strip()] = value.strip()

    ray.init(address=args.ray_address, ignore_reinit_error=True)
    run_dir = Path(args.run_dir) if args.run_dir else Path("orfs_runs") / str(int(time.time()))
    result = run_closure_loop(
        design_name=args.design_name,
        flow_dir=args.flow_dir,
        design_config_mk=args.design_config_mk,
        reports_root=args.reports_root,
        run_dir=run_dir,
        max_iterations=args.max_iterations,
        objective=args.objective,
        model=args.model,
        closure_criteria=args.closure_criteria,
        stage_timeout_seconds=args.stage_timeout_seconds,
        prompt_path=args.prompt_path,
        diagnose_prompt_path=args.diagnose_prompt_path,
        referee_prompt_path=args.referee_prompt_path,
        schema_path=MINIMAL_SCHEMA_PATH if args.minimal_schema else DEFAULT_SCHEMA_PATH,
        fresh_config=not args.resume_config,
        ld_library_path=args.ld_library_path,
        locked_tunables=locked_tunables,
        run_signoff=not args.skip_signoff,
        batch_size=args.batch_size,
        skip_referee=args.skip_referee,
        seed_ledger=args.seed_ledger,
    )
    print(f"\nresult: {json.dumps(result, indent=2)}")
    return 0 if result["status"] == "closed" else 1

if __name__ == "__main__":
    raise SystemExit(main())