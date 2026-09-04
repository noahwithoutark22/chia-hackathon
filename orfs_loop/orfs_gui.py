"""Local web dashboard for the ORFS closure loop.

Start it once and drive everything from the browser: pick a design and a
model, launch a run, and watch the flow stages, per-run metrics, tunable
changes and crash diagnostics update live. Replaces juggling terminal
windows and grepping tool_trace.log by hand.

    python3 orfs_gui.py          # then open http://127.0.0.1:8080

The loop itself still runs as a normal `orfs_loop.py` subprocess, so
anything started here behaves exactly like a CLI run (same run_dir layout,
same artifacts) and survives the browser being closed.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

REPO_ROOT = Path(__file__).parent.resolve()
RUNS_DIR = REPO_ROOT / "orfs_runs"
DESIGNS_DIR = REPO_ROOT / "orfs-native-build" / "flow" / "designs"
CONTAINER_FLOW = "/root/OpenROAD-flow-scripts/flow"
# cluster.yaml names every worker container "chia-<type>-${USER}-<n>", so the
# username has to come from the environment -- hardcoding one made the model
# dropdown (which shells out to `docker exec <this> opencode models`) fail
# silently for every user but the author. ORFS_GUI_OPENCODE_CONTAINER overrides
# it outright for a non-standard cluster.
_CLUSTER_USER = os.environ.get("USER") or os.environ.get("LOGNAME") or getpass.getuser()
OPENCODE_CONTAINER = os.environ.get(
    "ORFS_GUI_OPENCODE_CONTAINER", f"chia-opencode-{_CLUSTER_USER}-0"
)

app = FastAPI(title="ORFS Closure Dashboard")

# Single active run. The loop holds the cluster's only `orfs_run` slot, so
# running two at once would deadlock on the resource anyway.
#
# _proc is only set when THIS process spawned the subprocess -- it's a real
# Popen handle, needed for .poll()/exit_code. _proc_pid is the pid of record
# regardless of who spawned it: also set when we *adopt* an orfs_loop.py left
# running by a previous instance of this GUI (e.g. restarted to pick up a
# code change while a run was mid-flight -- otherwise the dashboard shows
# "starting..." forever even though the loop is progressing fine, since a
# fresh process has no memory of the old one's in-memory state).
_proc: Optional[subprocess.Popen] = None
_proc_pid: Optional[int] = None
_run_dir: Optional[Path] = None
_started_at: Optional[float] = None
_cmdline: list = []

_PROC_INFO_FILE = ".gui_proc.json"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just not owned by us -- can't happen here in practice


def _discover_active_run() -> None:
    """Called once at startup: re-adopt an orfs_loop.py this GUI process
    didn't spawn itself but that's still alive and holding the orfs_run
    resource, so a GUI restart mid-run doesn't strand the dashboard on
    "starting..." forever."""
    global _proc_pid, _run_dir, _started_at, _cmdline
    if not RUNS_DIR.is_dir():
        return
    candidates = sorted(
        (p for p in RUNS_DIR.glob(f"*/{_PROC_INFO_FILE}") if p.is_file()),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    for info_path in candidates:
        try:
            info = json.loads(info_path.read_text())
            pid = int(info["pid"])
        except (OSError, ValueError, KeyError):
            continue
        if not _pid_alive(pid):
            continue
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace")
        except OSError:
            continue
        if "orfs_loop.py" not in cmdline:
            continue  # pid got reused by an unrelated process
        _proc_pid = pid
        _run_dir = info_path.parent
        _started_at = info.get("started_at")
        _cmdline = info.get("cmd", [])
        return


_discover_active_run()


# ---------------------------------------------------------------- discovery

def _list_designs() -> list:
    out = []
    if not DESIGNS_DIR.is_dir():
        return out
    for cfg in sorted(DESIGNS_DIR.glob("*/*/config.mk")):
        platform, design = cfg.parent.parent.name, cfg.parent.name
        out.append({
            "label": f"{platform} / {design}",
            "platform": platform,
            "design": design,
            "config_mk": f"{CONTAINER_FLOW}/designs/{platform}/{design}/config.mk",
            "reports_root": f"{CONTAINER_FLOW}/reports/{platform}/{design}/base",
        })
    return out


def _list_models() -> list:
    """Ask opencode what it can actually reach, so the dropdown never offers
    a model the credentials don't cover."""
    try:
        r = subprocess.run(
            ["docker", "exec", OPENCODE_CONTAINER, "sh", "-c",
             "export PATH=$PATH:/root/.opencode/bin; opencode models"],
            capture_output=True, text=True, timeout=30,
        )
        models = [m.strip() for m in r.stdout.splitlines() if "/" in m]
    except Exception:
        models = []
    # Models confirmed in practice to make real tool calls through this
    # pipeline float to the top; the rest stay available but unranked.
    # NOTE: google/gemini-3.5-flash doesn't exist in opencode's catalog and
    # a run against it hangs indefinitely instead of failing fast (confirmed
    # by hand: `opencode run --model google/gemini-3.5-flash` never returns,
    # while an actually-invalid/deprecated model errors in ~2s) -- burned a
    # whole run silently for an hour this way. gemini-3.6-flash is the real,
    # current model one major version up.
    preferred = [
        "openrouter/deepseek/deepseek-v4-pro",
        "openrouter/anthropic/claude-sonnet-5",
        "opencode/big-pickle",
        "opencode/nemotron-3-ultra-free",
        "google/gemini-3.6-flash",
    ]
    ranked = [m for m in preferred if m in models]
    return ranked + [m for m in models if m not in ranked]


def _list_schema_keys() -> list:
    try:
        s = json.loads((REPO_ROOT / "orfs_tunables_schema.json").read_text())
        return sorted(k for k in s if not k.startswith("_"))
    except Exception:
        return []


# _list_designs() is a filesystem scan that never changes while the GUI
# process is up, so it's cheap to snapshot once at startup. _list_models()
# is a `docker exec ... opencode models` call -- it used to be snapshotted
# the same way, but a snapshot means one transient failure at the exact
# moment the GUI starts (opencode container still coming up right after a
# `chia up`, etc) blanks the model dropdown for the GUI's whole lifetime.
# The command itself is fast (well under a second once the container is
# actually up), so there's no real cost to just running it live on every
# /api/init call instead of caching it -- that's the only way "on startup"
# reliably means "on startup", not "on startup, unless that one attempt
# happened to lose a race."
_CACHED_DESIGNS = _list_designs()


# ------------------------------------------------------------ run inspection

# One trace block: [timestamp] event-line, then zero or more payload lines, then
# the dashed separator. The payload must stop *before* a separator rather than
# being any lazy run of characters up to one -- an entry with no payload at all
# (`SYSTEM: Promoted run N ...`, and both signoff markers) is immediately
# followed by its separator, so a lazy `(.*?)\n-{20,}` skips straight past it
# and swallows the whole next block as that entry's payload. Observed: the
# `SYSTEM: Signoff (drc/lvs) result` block was consumed by the `Promoted run`
# block above it and never parsed at all.
_BLOCK_RE = re.compile(r"\[([\d\-T:.]+)\] ([^\n]+)\n((?:(?!-{20,}$)[^\n]*\n)*?)-{20,}", re.M)
_BASELINE_LABEL = "(baseline run -- nothing changed yet)"

# --batch-size run markers. Every one of these carries the slot it belongs to,
# which is the whole point: with N slots running concurrently their trace lines
# interleave, so the dashboard has to attribute each line rather than assume
# the newest one describes "the" current state (see orfs_loop.py's
# _run_flow_batch / _propose_via_llm).
_SLOT_STAGE_RE = re.compile(r"^SYSTEM: \[slot(\d+)\] Executing internal stage: (.+)$")
# The slot number is optional only to keep run_dirs written before it was
# added readable -- those still show their reasoning in the merged transcript,
# just without per-column attribution.
_SLOT_REASONING_RE = re.compile(r"^SYSTEM: Iteration (\d+) Batch LLM Slot (?:(\d+) )?Reasoning")
_SLOT_SET_RE = re.compile(r"^CALL: set_tunables \(slot (\d+), run (\d+)\)")
_SLOT_FLOW_CALL_RE = re.compile(r"^CALL: run_full_flow_and_summarize \(slot slot(\d+), run (\d+)\)")
_BATCH_RETURN_RE = re.compile(r"^RETURN \w+: \(batch run (\d+)\) run_full_flow_and_summarize")
# The signoff phase, which runs on the best config rather than the last one --
# both markers carry that run number so the UI can point at the right row while
# KLayout is still running, not only after summary.json lands.
_SIGNOFF_RESTORE_RE = re.compile(r"^SYSTEM: Restoring best config \(run (\d+)\) before signoff")
_SIGNOFF_START_RE = re.compile(r"^SYSTEM: Signoff starting on run (\d+|unknown) \(drc/lvs\)")
# The driver's own final word on which run won, written by _promote_best_gds.
# Authoritative where it exists, and present in run_dirs written before the two
# signoff markers above were added.
_PROMOTED_RE = re.compile(r"^SYSTEM: Promoted run (\d+) \(best result\)")


def _fmt_value(v):
    # `null` here means "revert to this design's original baseline value"
    # (see set_tunables) -- rendering it as the literal word None looked
    # like a bug, not a real value.
    return "baseline" if v is None else v


def _format_tunables_diff(ch: dict) -> str:
    """Render tunables_changed_this_run.

    Normally {KEY: {"from": ..., "to": ...}}, but tolerate a flat
    {KEY: value} too -- a parse error here would blank the entire dashboard
    for a run that is otherwise perfectly fine, which is a bad trade for a
    formatting detail.
    """
    parts = []
    for k, v in (ch or {}).items():
        if isinstance(v, dict):
            parts.append(f"{k}: {_fmt_value(v.get('from'))} → {_fmt_value(v.get('to'))}")
        else:
            parts.append(f"{k} → {_fmt_value(v)}")
    return ", ".join(parts)


def _format_tunables_request(payload: dict) -> str:
    """A set_tunables CALL's raw request shape: {KEY: value_or_null}."""
    return ", ".join(f"{k} → {_fmt_value(v)}" for k, v in (payload or {}).items())


def _parse_run(run_dir: Path) -> dict:
    """Turn a run's tool_trace.log into structured state for the UI."""
    trace = run_dir / "tool_trace.log"
    state = {
        "iterations": 0, "flow_runs": [], "current_stage": None,
        "events": [], "llm_notes": [], "iteration_goal": None,
        "slots": [], "batch_size": 0, "signoff": None, "best_run": None,
    }
    if not trace.exists():
        return state

    try:
        text = trace.read_text(errors="replace")
    except OSError:
        return state

    # What the *next* run_full_flow_and_summarize call will actually test --
    # tracked as we go so a call still in flight (CALL seen, no RETURN yet)
    # can be shown as a "pending" row with its change already known, instead
    # of the table staying completely blank for the whole flow's runtime.
    pending_change = _BASELINE_LABEL
    pending_started = False

    # --batch-size bookkeeping. `slots` accumulates one record per parallel
    # slot so the UI can show what each one independently proposed and got
    # back; `run_to_slot` maps a run index onto its slot, because the RETURN
    # block only carries the run number, not the slot that produced it.
    slots: dict = {}
    run_to_slot: dict = {}

    def _slot(i: int) -> dict:
        return slots.setdefault(i, {
            "slot": i, "stage": None, "proposal": None, "proposal_run": None,
            "notes": [], "runs": [], "running": False,
        })

    for m in _BLOCK_RE.finditer(text):
        ts, event, payload = m.group(1), m.group(2).strip(), m.group(3)
        m_slot_stage = _SLOT_STAGE_RE.match(event)
        m_slot_reason = _SLOT_REASONING_RE.match(event)
        m_slot_set = _SLOT_SET_RE.match(event)
        m_slot_flow = _SLOT_FLOW_CALL_RE.match(event)
        m_batch_ret = _BATCH_RETURN_RE.match(event)
        m_signoff_restore = _SIGNOFF_RESTORE_RE.match(event)
        m_signoff_start = _SIGNOFF_START_RE.match(event)
        m_promoted = _PROMOTED_RE.match(event)

        if event.startswith("SYSTEM: Starting Iteration"):
            state["iterations"] += 1
            goal = event.split("| Goal:", 1)[1].strip() if "| Goal:" in event else None
            if goal:
                state["iteration_goal"] = goal
            state["current_stage"] = "thinking"
            state["events"].append({"t": ts, "kind": "iteration", "text": event})
        elif m_slot_stage:
            # Per-slot stage: never folded into the global current_stage --
            # with N slots at different stages at the same instant, a single
            # shared value would just flicker between them.
            sl = _slot(int(m_slot_stage.group(1)))
            sl["stage"] = m_slot_stage.group(2).strip()
            sl["running"] = True
        elif event.startswith("SYSTEM: Executing internal stage:"):
            state["current_stage"] = event.rsplit(":", 1)[-1].strip()
        elif m_promoted:
            state["best_run"] = int(m_promoted.group(1))
            state["events"].append({"t": ts, "kind": "signoff", "text": event[8:]})
        elif m_signoff_restore:
            state["signoff"] = {"run": int(m_signoff_restore.group(1)),
                                "phase": "restoring"}
            state["events"].append(
                {"t": ts, "kind": "signoff",
                 "text": f"restoring best config (run {m_signoff_restore.group(1)}) for signoff"})
        elif m_signoff_start:
            run_txt = m_signoff_start.group(1)
            state["signoff"] = {
                "run": int(run_txt) if run_txt != "unknown" else state.get("best_run"),
                "phase": "running",
            }
            state["events"].append({"t": ts, "kind": "signoff", "text": "signoff (drc/lvs) started"})
        elif event.startswith("SYSTEM: Signoff (drc/lvs)"):
            prev = state.get("signoff") or {}
            # run_dirs written before the "Signoff starting" marker existed have
            # no phase to inherit a run number from -- fall back to best_run,
            # which signoff is by definition run against.
            done = {"run": prev.get("run") or state.get("best_run"), "phase": "done"}
            if event.endswith("failed"):
                done.update({"phase": "failed", "error": payload.strip()[:300]})
            else:
                try:
                    d = json.loads(payload)
                    done["drc"] = d.get("drc")
                    done["lvs"] = d.get("lvs")
                except Exception:
                    pass
            state["signoff"] = done
            state["events"].append({"t": ts, "kind": "signoff", "text": f"signoff {done['phase']}"})
        elif m_slot_reason:
            idx = m_slot_reason.group(2)
            note = {"t": ts, "text": payload.strip()[:4000],
                    "slot": int(idx) if idx is not None else None}
            if idx is not None:
                _slot(int(idx))["notes"].append(note)
            state["llm_notes"].append(note)
        elif m_slot_set:
            sl = _slot(int(m_slot_set.group(1)))
            sl["proposal_run"] = int(m_slot_set.group(2))
            try:
                sl["proposal"] = _format_tunables_request(json.loads(payload)) or _BASELINE_LABEL
            except Exception:
                sl["proposal"] = payload.strip()[:200]
            state["events"].append({"t": ts, "kind": "set", "text": payload.strip()[:300]})
        elif m_slot_flow:
            sl = _slot(int(m_slot_flow.group(1)))
            run_no = int(m_slot_flow.group(2))
            run_to_slot[run_no] = sl["slot"]
            sl["running"] = True
            sl["stage"] = sl["stage"] or "starting"
        elif event.startswith("CALL: set_tunables"):
            state["events"].append({"t": ts, "kind": "set", "text": payload.strip()[:300]})
            try:
                pending_change = _format_tunables_request(json.loads(payload)) or _BASELINE_LABEL
            except Exception:
                pass
        elif event.startswith("CALL: run_full_flow_and_summarize"):
            pending_started = True
        elif "LLM Reasoning" in event:
            state["current_stage"] = None
            state["llm_notes"].append({"t": ts, "text": payload.strip()[:4000], "slot": None})
        elif event.startswith("RETURN") and "run_full_flow_and_summarize" in event:
            pending_started = False
            try:
                d = json.loads(payload)
            except Exception:
                continue
            if "blocked" in str(d.get("error", "")):
                state["events"].append(
                    {"t": ts, "kind": "blocked", "text": "re-run blocked (no config change)"})
                continue
            state["current_stage"] = None
            ch = d.get("tunables_changed_this_run")
            # The tool's own run counter (recent_history[-1].run), not the
            # row's position in this array -- those two only coincide when
            # nothing was ever skipped/blocked and this run_dir was never
            # reused across more than one orfs_loop.py launch. best_run_so_far
            # already cross-references this same number, so the table's own
            # "#" column needs to match it or "(best: N)" points nowhere.
            rh = d.get("recent_history") or []
            # A batch RETURN names its run in the event line ("(batch run 5)")
            # but not its slot, so it's matched back through the CALL that
            # started it. In batch mode `recent_history` is ordered
            # worst-first (see _run_flow_batch), so rh[-1] is the round's
            # winner rather than this row's own run -- take the run number
            # from the event line whenever it's there.
            run_no = int(m_batch_ret.group(1)) if m_batch_ret else (rh[-1]["run"] if rh else None)
            entry = {
                "t": ts,
                "run": run_no,
                "slot": run_to_slot.get(run_no),
                "iteration": d.get("iteration"),
                "verdict": (d.get("comparison_to_previous_run") or {}).get("verdict"),
                "changed": ch if isinstance(ch, str) else _format_tunables_diff(ch),
                "qor": d.get("qor_rule_failures") or [],
                "headroom": d.get("area_headroom_warning"),
                "best": (d.get("best_run_so_far") or {}).get("run"),
                "clock_period": d.get("clock_period"),
            }
            if d.get("fatal_error"):
                entry.update({
                    "crashed": True,
                    "stage": (d.get("details") or {}).get("stage"),
                    "errors": [l for l in (d.get("details") or {}).get("log_tail", "").split("\n")
                               if "ERROR" in l or "Error:" in l][:4],
                })
            else:
                v, p = d.get("violations", {}), d.get("physical_metrics", {})
                entry.update({
                    "crashed": False,
                    "status": d.get("status"),
                    "setup_wns": v.get("setup_wns_slack"),
                    "setup_tns": v.get("setup_tns_slack"),
                    "hold_wns": v.get("hold_wns_slack"),
                    "drc": v.get("drc_error_count"),
                    "util": p.get("core_utilization_percent"),
                    "power": p.get("total_power"),
                    "area": p.get("core_area"),
                })
            # Which run is best *so far*. The driver only writes
            # `best_run_so_far` when the best run is some OTHER run than the one
            # being reported -- so its absence on a usable run means this run is
            # itself the best, which is why the field can't just be read off the
            # newest row (run 25 closed as the best and therefore carries no
            # `best` at all). A crash leaves the previous answer standing.
            if entry["best"] is not None:
                state["best_run"] = entry["best"]
            elif not entry.get("crashed") and run_no is not None:
                state["best_run"] = run_no
            state["flow_runs"].append(entry)
            if entry["slot"] is not None:
                sl = _slot(entry["slot"])
                sl["runs"].append(entry)
                sl["running"] = False
                sl["stage"] = None

    if pending_started:
        state["flow_runs"].append({
            "pending": True, "changed": pending_change,
            "iteration": state["iterations"] or None,
        })

    if slots:
        ordered = [slots[k] for k in sorted(slots)]
        for sl in ordered:
            sl["notes"] = sl["notes"][-6:]
            sl["last"] = sl["runs"][-1] if sl["runs"] else None
            # Only the tail matters for the live view, but the count is worth
            # keeping: it's how the UI shows a slot that's been carrying the
            # round vs one that keeps failing to produce a usable proposal.
            sl["run_count"] = len(sl["runs"])
            sl.pop("runs", None)
        state["slots"] = ordered
        state["batch_size"] = len(ordered)

    state["events"] = state["events"][-40:]
    state["llm_notes"] = state["llm_notes"][-30:]
    return state


def _artifacts(run_dir: Path) -> dict:
    out = {"gds": [], "summary": None, "final_gds": None, "layout_image": False}
    gds_dir = run_dir / "gds"
    if gds_dir.is_dir():
        out["gds"] = sorted(p.name for p in gds_dir.glob("*.gds"))
    fg = run_dir / "final.gds"
    if fg.exists():
        out["final_gds"] = str(fg)
    if (run_dir / "final_layout.webp").exists():
        out["layout_image"] = True
    s = run_dir / "summary.json"
    if s.exists():
        try:
            out["summary"] = json.loads(s.read_text())
        except Exception:
            pass
    return out


# ------------------------------------------------------------------- routes

@app.get("/api/init")
def api_init():
    return {
        "designs": _CACHED_DESIGNS,
        "models": _list_models(),
        "tunables": _list_schema_keys(),
        "runs": sorted((p.name for p in RUNS_DIR.iterdir() if p.is_dir()), reverse=True)
        if RUNS_DIR.is_dir() else [],
    }


@app.post("/api/start")
async def api_start(body: dict):
    global _proc, _proc_pid, _run_dir, _started_at, _cmdline
    if _proc_pid is not None and _pid_alive(_proc_pid):
        return JSONResponse({"error": "A run is already active. Stop it first."}, status_code=409)

    name = (body.get("run_name") or f"run-{int(time.time())}").strip()
    name = re.sub(r"[^A-Za-z0-9_.-]", "-", name)
    run_dir = RUNS_DIR / name
    cmd = [
        sys.executable, str(REPO_ROOT / "orfs_loop.py"),
        "--design-name", body["design"],
        "--design-config-mk", body["config_mk"],
        "--reports-root", body["reports_root"],
        "--max-iterations", str(body.get("iterations", 3)),
        "--objective", body.get("objective", "area"),
        "--model", body["model"],
        "--run-dir", str(run_dir),
    ]
    # Batch width. Capped at the cluster's actual `orfs_run` capacity is the
    # user's job (cluster.yaml's hello_orfs.num_workers) -- a wider value just
    # queues the extra slots rather than failing, so it's not validated here.
    try:
        batch_size = max(1, int(body.get("batch_size", 1)))
    except (TypeError, ValueError):
        batch_size = 1
    if batch_size > 1:
        cmd += ["--batch-size", str(batch_size)]
    if body.get("resume_config"):
        cmd.append("--resume-config")
    if body.get("minimal_schema"):
        cmd.append("--minimal-schema")
    if body.get("skip_signoff"):
        cmd.append("--skip-signoff")
    for lk in body.get("locks", []):
        if lk.get("key") and str(lk.get("value", "")).strip():
            cmd += ["--lock", f"{lk['key']}={str(lk['value']).strip()}"]

    run_dir.mkdir(parents=True, exist_ok=True)
    logf = open(run_dir / "driver.log", "ab")
    _proc = subprocess.Popen(
        cmd, cwd=str(REPO_ROOT), stdout=logf, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    _run_dir, _started_at, _cmdline = run_dir, time.time(), cmd
    _proc_pid = _proc.pid
    # Recorded so a *later* instance of this GUI (e.g. restarted to pick up
    # a code change) can re-adopt this process instead of losing track of
    # it -- see _discover_active_run().
    (run_dir / _PROC_INFO_FILE).write_text(json.dumps(
        {"pid": _proc_pid, "started_at": _started_at, "cmd": cmd}
    ))
    return {"ok": True, "run_dir": str(run_dir), "cmd": " ".join(cmd)}


@app.post("/api/stop")
def api_stop():
    global _proc_pid
    if _proc_pid is None or not _pid_alive(_proc_pid):
        return {"ok": True, "note": "nothing running"}
    try:
        os.killpg(os.getpgid(_proc_pid), signal.SIGTERM)
    except Exception:
        os.kill(_proc_pid, signal.SIGTERM)
    return {"ok": True}


@app.get("/api/state")
def api_state(run: Optional[str] = None):
    target = (RUNS_DIR / run) if run else _run_dir
    running = _proc_pid is not None and _pid_alive(_proc_pid)
    payload = {
        "running": running,
        "run_dir": str(target) if target else None,
        "run_name": target.name if target else None,
        "elapsed": round(time.time() - _started_at) if (_started_at and running) else None,
        "cmd": " ".join(_cmdline) if _cmdline else None,
        # Only meaningful for a process THIS instance spawned (a Popen
        # handle) -- an adopted one (see _discover_active_run) has none,
        # since we never had a child-process relationship to poll.
        "exit_code": _proc.poll() if _proc is not None else None,
    }
    if target and target.is_dir():
        payload.update(_parse_run(target))
        payload["artifacts"] = _artifacts(target)
        trace = target / "tool_trace.log"
        if trace.exists():
            try:
                payload["driver_tail"] = trace.read_text(errors="replace")[-6000:]
            except OSError:
                pass
    return payload


@app.get("/api/layout-image")
def api_layout_image(run: Optional[str] = None):
    target = (RUNS_DIR / run) if run else _run_dir
    if target is None:
        return JSONResponse({"error": "no run"}, status_code=404)
    img = (target / "final_layout.webp").resolve()
    # `run` comes from the query string -- refuse anything that resolves
    # outside RUNS_DIR (e.g. "../../etc/passwd") before touching the filesystem.
    if RUNS_DIR.resolve() not in img.parents or not img.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(img, media_type="image/webp")


@app.get("/", response_class=HTMLResponse)
def index():
    return (REPO_ROOT / "gui" / "index.html").read_text()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("ORFS_GUI_PORT", "8080"))
    print(f"\n  ORFS dashboard -> http://127.0.0.1:{port}\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
