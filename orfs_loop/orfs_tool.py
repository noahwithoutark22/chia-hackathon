from __future__ import annotations
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import datetime
from pathlib import Path
from typing import Optional

from chia.base.ChiaFunction import ChiaFunction, get
from chia.base.tools.ChiaTool import ChiaTool

from orfs_config_bridge import (
    backup_config_mk,
    load_current_tunables_from_config_mk,
    load_schema,
    render_config_mk,
    validate_tunables,
)

DEFAULT_TRACE_LOG_PATH = Path("/root/OpenROAD-flow-scripts/tool_trace.log")

def _log_trace(log_path: Path, event: str, payload: str = ""):
    timestamp = datetime.datetime.now().isoformat()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(f"[{timestamp}] {event}\n{payload}\n" + "-"*60 + "\n")

@ChiaFunction(resources={"orfs_run": 1})
def _prep_working_config_remote(
    baseline_config_mk: str, backup_dir: str, working_config_mk: str, fresh: bool = True,
) -> str:
    import shutil
    import time
    bl = Path(baseline_config_mk)
    bd = Path(backup_dir)
    wc = Path(working_config_mk)
    bd.mkdir(parents=True, exist_ok=True)
    dest = bd / f"config.mk.baseline.{int(time.time())}"
    shutil.copy2(bl, dest)
    # `fresh` (the default) resets the working config to the pristine
    # baseline. Otherwise a new run silently inherits whatever tunables the
    # *previous* run happened to leave behind, so its "baseline" measurement
    # is really some half-explored config -- results aren't reproducible and
    # comparing two runs means nothing. Pass fresh=False only to deliberately
    # continue where a previous run stopped.
    if fresh and wc.exists():
        wc.unlink()
    if not wc.exists():
        wc.write_text(bl.read_text())
    return str(wc)

@ChiaFunction(resources={"orfs_run": 1})
def _read_baseline_clock_period_remote(baseline_config_mk: str) -> Optional[float]:
    # Runs on the orfs_run worker for the same reason as the other _remote
    # helpers here: constraint.sdc is only visible from that filesystem, not
    # the driver's. Returns None if the file is missing or doesn't match
    # either clk_period pattern this checkout uses -- setup() treats that as
    # "this design can't offer a CLOCK_PERIOD knob" rather than guessing.
    import re
    from pathlib import Path as _Path
    sdc_path = _Path(baseline_config_mk).parent / "constraint.sdc"
    if not sdc_path.exists():
        return None
    text = sdc_path.read_text()
    m = re.search(r"set\s+clk_period\s+([0-9.]+)", text)
    if not m:
        m = re.search(r"create_clock\b[^\n]*?-period\s+([0-9.]+)", text)
    return float(m.group(1)) if m else None

_CONFIG_MK_LINE_RE = re.compile(r"^\s*(?:export\s+)?([A-Z0-9_]+)\s*[:+?]?=\s*(.+?)\s*(?:#.*)?$")

@ChiaFunction(resources={"orfs_run": 1})
def _read_baseline_floorplan_remote(baseline_config_mk: str) -> dict:
    # ORFS's floorplan.tcl picks exactly one of 4 mutually-exclusive
    # initialization methods from which env vars are non-empty (FLOORPLAN_DEF
    # / FOOTPRINT / DIE_AREA+CORE_AREA / CORE_UTILIZATION) and hard-exits if
    # more than one is set. A DIE_AREA_SCALE tunable is only safe to offer
    # when the baseline already uses the explicit die/core area method --
    # for a CORE_UTILIZATION-based design (the common case), introducing
    # DIE_AREA/CORE_AREA into the managed block would make both methods
    # "set" simultaneously and crash floorplan the moment the model touches
    # it. CORE_UTILIZATION is already that design's equivalent lever (already
    # in the schema, already bounded), so nothing is lost by not offering it.
    found: dict = {}
    for line in Path(baseline_config_mk).read_text().splitlines():
        m = _CONFIG_MK_LINE_RE.match(line)
        if m:
            found[m.group(1)] = m.group(2).strip()
    die_area, core_area = found.get("DIE_AREA", ""), found.get("CORE_AREA", "")
    if die_area and core_area:
        return {"method": "explicit_area", "die_area": die_area, "core_area": core_area}
    return {"method": "other"}

_NOT_SUPPORTED_RE = re.compile(r"not supported on this platform", re.I)
# The lvs.lylvs macros (see e.g. platforms/sky130hd/lvs/sky130hd.lylvs) print
# exactly one of these two lines to stdout/the klayout log after `compare`.
# There is no separate machine-readable pass/fail marker for LVS -- unlike
# DRC's grep-friendly 6_drc_count.rpt, this text is the actual signal.
_LVS_PASS_RE = re.compile(r"Congratulations! Netlists match", re.I)
_LVS_FAIL_RE = re.compile(r"Netlists don't match", re.I)
# Some platforms (asap7 in this checkout, confirmed via `make --eval` variable
# dump: KLAYOUT_LVS_FILE and CDL_FILE both resolve empty) never got LVS wired
# up at all -- but the Makefile's own "LVS not supported on this platform"
# fallback lives in the *recipe* of the lvs target, which is never reached
# because building its prerequisite (6_final_concat.cdl, via cdl.tcl) reads
# $::env(CDL_FILE) unconditionally and crashes first. Same underlying "not
# configured for this platform" situation, just surfacing one step earlier
# than ORFS's own guard anticipates -- report it the same honest way instead
# of a scary-looking crash.
_LVS_UNCONFIGURED_RE = re.compile(r'can\'t read "::env\((?:CDL_FILE|KLAYOUT_LVS_FILE)\)"', re.I)

@ChiaFunction(resources={"orfs_run": 1})
def run_signoff_remote(
    flow_dir: str, working_config_mk: str, reports_root: str, results_root: str,
    extra_env: dict, timeout_seconds: int, log_dir: Optional[str] = None,
    flow_variant: Optional[str] = None, expect_gds_md5: Optional[str] = None,
) -> dict:
    """Runs `make drc` and `make lvs` against the design's final GDS -- the
    standalone KLayout checks `make` (finish through metadata) never runs on
    its own. Called directly by the driver after a run closes, independent
    of the LLM/MCP path entirely: signoff isn't a config knob to bisect, it's
    a final gate, so there's nothing for the 3-tool config-editor interface
    to do here.

    `flow_variant` points the checks at one slot's own `FLOW_VARIANT` tree, so a
    batch winner can be signed off exactly where it was built instead of being
    rebuilt at the canonical path first. `expect_gds_md5` is the driver's
    checksum of the GDS it actually promoted: the result always reports the
    checksum of the GDS these checks really read, and flags a mismatch, so a
    verdict can never be silently attributed to a different layout (it once
    was -- see README.md's "Signoff (DRC / LVS)" section).
    """
    env = os.environ.copy()
    env["DESIGN_CONFIG"] = working_config_mk
    if flow_variant:
        env["FLOW_VARIANT"] = flow_variant
    env.update(extra_env or {})

    # Recorded BEFORE the checks run, from the same results_root `make drc`/
    # `make lvs` will read their GDS from.
    gds_path = Path(results_root) / "6_final.gds"
    signed_off: dict = {"path": str(gds_path), "exists": gds_path.exists()}
    if gds_path.exists():
        h = hashlib.md5()
        with gds_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        signed_off["md5"] = h.hexdigest()
    if expect_gds_md5:
        signed_off["expected_md5"] = expect_gds_md5
        signed_off["matches_best"] = signed_off.get("md5") == expect_gds_md5
    logs_root = Path(str(reports_root).replace("/reports/", "/logs/", 1))
    log_dir_path = Path(log_dir) if log_dir else None

    def _run(stage: str) -> dict:
        try:
            proc = subprocess.run(
                ["make", "-C", flow_dir, stage],
                env=env, cwd=flow_dir, capture_output=True, text=True, timeout=timeout_seconds,
            )
            if log_dir_path is not None:
                log_dir_path.mkdir(parents=True, exist_ok=True)
                (log_dir_path / f"{stage}.log").write_text(
                    (proc.stdout or "") + "\nSTDERR:\n" + (proc.stderr or "")
                )
            return {
                "returncode": proc.returncode,
                "log_tail": _failure_excerpt(proc.stdout, proc.stderr),
            }
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "error": f"Timeout after {timeout_seconds}s"}

    result: dict = {}

    drc_run = _run("drc")
    drc_lyrdb = Path(reports_root) / "6_drc.lyrdb"
    drc_count_rpt = Path(reports_root) / "6_drc_count.rpt"
    if drc_lyrdb.exists() and _NOT_SUPPORTED_RE.search(drc_lyrdb.read_text(errors="replace")):
        result["drc"] = {"supported": False, "note": "DRC not supported on this platform (no KLAYOUT_DRC_FILE)."}
    elif drc_run.get("returncode") == 0 and drc_count_rpt.exists():
        try:
            violation_count = int(drc_count_rpt.read_text().strip().splitlines()[0])
        except (ValueError, IndexError):
            violation_count = None
        result["drc"] = {
            "supported": True, "violation_count": violation_count,
            "clean": violation_count == 0 if violation_count is not None else None,
            "report": str(drc_lyrdb),
        }
    else:
        result["drc"] = {"supported": True, "clean": False, "error": "drc run failed", "details": drc_run}

    lvs_run = _run("lvs")
    lvs_lvsdb = Path(results_root) / "6_lvs.lvsdb"
    lvs_log = logs_root / "6_lvs.log"
    lvs_text = lvs_lvsdb.read_text(errors="replace") if lvs_lvsdb.exists() else ""
    log_text = lvs_log.read_text(errors="replace") if lvs_log.exists() else ""
    if _NOT_SUPPORTED_RE.search(lvs_text) or _LVS_UNCONFIGURED_RE.search(lvs_run.get("log_tail", "")):
        result["lvs"] = {"supported": False, "note": "LVS not configured for this platform (CDL_FILE/KLAYOUT_LVS_FILE not set)."}
    elif _LVS_PASS_RE.search(log_text):
        result["lvs"] = {"supported": True, "clean": True, "report": str(lvs_lvsdb)}
    elif _LVS_FAIL_RE.search(log_text):
        result["lvs"] = {"supported": True, "clean": False, "report": str(lvs_lvsdb)}
    elif lvs_run.get("returncode") == 0:
        result["lvs"] = {
            "supported": True, "clean": None,
            "note": "lvs ran but no pass/fail marker found in 6_lvs.log -- inspect manually.",
            "report": str(lvs_lvsdb),
        }
    else:
        result["lvs"] = {"supported": True, "clean": False, "error": "lvs run failed", "details": lvs_run}

    # The reports these checks produced, not just their stdout. `6_drc.lyrdb`
    # and `6_lvs.lvsdb` are the only artifacts carrying *what* failed -- the
    # logs say "Netlists don't match" and nothing more -- and they sit in the
    # ORFS tree where the next run of this variant deletes them.
    if log_dir_path is not None:
        try:
            log_dir_path.mkdir(parents=True, exist_ok=True)
            for src in (drc_lyrdb, drc_count_rpt, lvs_lvsdb, lvs_log):
                if src.exists() and src.is_file():
                    shutil.copy2(src, log_dir_path / src.name)
        except OSError:
            pass

    result["lvs_netgen"] = _run_netgen_lvs(
        flow_dir, reports_root, results_root, env, timeout_seconds, log_dir_path)

    # netgen is authoritative, not KLayout (result["lvs"] above): it has both
    # series and parallel MOS combination, where KLayout's LVS deck only ever
    # does parallel -- see README.md's signoff section for why that's the wrong
    # way round to gate on. `result["lvs"]["clean"]` stays informational only.
    ng = result["lvs_netgen"]
    if not ng.get("supported"):
        result["lvs_verdict"] = {"clean": None, "reason": "netgen not available: " + ng.get("note", "")}
    elif ng.get("clean"):
        result["lvs_verdict"] = {"clean": True, "reason": "netgen: netlists match"}
    elif ng.get("effectively_clean"):
        result["lvs_verdict"] = {
            "clean": True,
            "reason": "netgen mismatch(es) all match a known, individually verified fold "
                      f"exception: {[m['cell'] for m in ng.get('subcircuit_mismatches', [])]}",
        }
    else:
        result["lvs_verdict"] = {
            "clean": False,
            "reason": "netgen: " + (ng.get("verdict") or "no verdict") +
                      (f" -- unexplained mismatch(es): "
                       f"{[m['cell'] for m in ng.get('subcircuit_mismatches', [])]}"
                       if ng.get("subcircuit_mismatches") else ""),
        }

    # Always attached, so "what was actually checked" is answerable from
    # summary.json alone rather than by md5-ing files afterwards.
    result["signed_off_gds"] = signed_off
    if signed_off.get("matches_best") is False:
        result["warning"] = (
            "signoff ran against a GDS that is NOT the promoted best run's "
            f"({signed_off.get('md5')} vs expected {expect_gds_md5}) -- treat these "
            "DRC/LVS verdicts as describing a different layout."
        )
    return result

@ChiaFunction(resources={"orfs_run": 1})
def _apply_locked_tunables_remote(
    baseline_config_mk: str, working_config_mk: str, schema_json: str, locked_json: str,
) -> str:
    # Runs on the orfs_run worker (same place set_tunables/get_tunables run),
    # unlike setup() itself which runs on the driver -- config.mk paths are
    # only valid from inside that worker's filesystem. Takes the schema as
    # JSON rather than a path for the same reason: schema_path is a host
    # path from setup()'s perspective and may not resolve inside the worker.
    schema = json.loads(schema_json)
    locked = json.loads(locked_json)
    current = load_current_tunables_from_config_mk(working_config_mk, schema)
    merged = {**current, **locked}
    render_config_mk(baseline_config_mk, merged, working_config_mk, schema)
    return "ok"

DEFAULT_STAGE_TIMEOUT_SECONDS = 3600


# ---------------------------------------------------------------------------
# Driver-side flow execution (no LLM, no MCP)
#
# The LLM used to drive the flow itself by calling run_full_flow_and_summarize
# over MCP. That is structurally broken: MCP is request/response with a client
# timeout (opencode's fires at ~60s), while a flow takes 90s for gcd and 15+
# minutes for something like riscv32i. Every call therefore came back to the
# model as `MCP error -32001: Request timed out` even though the flow was
# running fine, the model retried, and the retry's `make clean_all` deleted
# results/ out from under the still-running flow -- surfacing as a bogus
# "Flow crashed during route" against a config that never actually crashed.
#
# These run on the driver's own Ray call instead (`get(...chia_remote(...))`),
# which blocks as long as it needs to with no timeout and no second caller.
# They are deliberately standalone rather than ORFSTool methods: the tool's
# actor holds the cluster's single `orfs_run` unit for its whole lifetime, so
# anything needing that resource has to run outside it.
# ---------------------------------------------------------------------------

@ChiaFunction(resources={"orfs_run": 1})
def read_tunables_remote(working_config_mk: str, schema_json: str) -> dict:
    """Current schema-visible values from the working config.mk, read on the
    worker (the only filesystem where that path resolves)."""
    return load_current_tunables_from_config_mk(working_config_mk, json.loads(schema_json))


@ChiaFunction(resources={"orfs_run": 1})
def apply_tunables_remote(
    baseline_config_mk: str, working_config_mk: str, schema_json: str,
    locked_json: str, requested_json: str,
) -> dict:
    """Validate and apply a proposed tunable change set, returning what was
    actually written. `null` for a key reverts it to the design's baseline.
    Locked keys are force-written to their fixed value regardless of what was
    requested -- enforcement lives here, in code, never in the prompt."""
    schema = json.loads(schema_json)
    locked = json.loads(locked_json)
    requested = json.loads(requested_json)

    unset_keys = [k for k, v in requested.items() if v is None]
    unknown = [k for k in requested if k not in schema]
    set_requested = {k: v for k, v in requested.items() if v is not None and k in schema}

    current = load_current_tunables_from_config_mk(working_config_mk, schema)
    merged = {**current, **set_requested}
    for key in unset_keys:
        merged.pop(key, None)

    rejected = []
    for key, locked_value in locked.items():
        if key in requested:
            try:
                requested_rendered = validate_tunables({key: requested[key]}, schema)[key]
            except Exception:
                requested_rendered = str(requested[key])
            if requested_rendered != locked_value:
                rejected.append({
                    "key": key, "requested": requested[key], "locked_value": locked_value,
                })
        merged[key] = locked_value

    try:
        written = render_config_mk(baseline_config_mk, merged, working_config_mk, schema)
    except Exception as exc:
        # An out-of-range/ill-typed proposal must not kill the loop -- report
        # it so the driver can hand the reason back to the model next turn.
        return {"ok": False, "error": str(exc)}

    result = {"ok": True, "written": written}
    applied_unsets = [k for k in unset_keys if k in schema]
    if applied_unsets:
        result["reverted_to_baseline"] = applied_unsets
    if unknown:
        result["ignored_unknown_keys"] = unknown
    if rejected:
        result["rejected_locked_tunables"] = rejected
    return result


@ChiaFunction(resources={"orfs_run": 1})
def run_flow_remote(
    flow_dir: str, working_config_mk: str, reports_root: str, results_root: str,
    extra_env: dict, timeout_seconds: int,
    run_dir: Optional[str] = None, run_index: int = 1,
    flow_variant: Optional[str] = None,
) -> dict:
    """Run the full ORFS pipeline once and return parsed metrics.

    Stateless: run history, verdicts and best-run tracking are the driver's
    job now, so this does exactly one thing and can't get out of sync with
    the caller's bookkeeping.

    `flow_variant`, when given, sets ORFS's own FLOW_VARIANT env var (default
    "base" -- flow/Makefile:97). flow/scripts/variables.mk scopes LOG_DIR/
    OBJECTS_DIR/REPORTS_DIR/RESULTS_DIR by FLOW_VARIANT, so distinct variants
    let multiple concurrent calls (from orfs_loop.py's --batch-size) run
    against the SAME design/checkout without their `make clean_all`s touching
    each other -- `reports_root`/`results_root` must already point at that
    variant's own subtree (see orfs_loop.py's _slot_paths), this only sets
    the env var `make` itself reads.
    """
    env = os.environ.copy()
    env["DESIGN_CONFIG"] = working_config_mk
    if flow_variant:
        env["FLOW_VARIANT"] = flow_variant
    env.update(extra_env or {})
    run_dir_path = Path(run_dir) if run_dir else None
    log_dir = (run_dir_path / "flow_logs" / f"run_{run_index}") if run_dir_path else None
    # Same tool_trace.log the driver writes to (via the /root/chia-orfs bind
    # mount). Stage markers land here so the dashboard can show which stage is
    # live, exactly as it did when the flow ran inside the MCP tool.
    trace_path = (run_dir_path / "tool_trace.log") if run_dir_path else DEFAULT_TRACE_LOG_PATH
    stage_label_prefix = f"[{flow_variant}] " if flow_variant else ""

    def _stage(stage: str) -> dict:
        # With --batch-size > 1, multiple slots append these small lines to
        # the SAME tool_trace.log concurrently -- the prefix keeps an
        # interleaved trace readable instead of ambiguous (the big CALL/
        # RETURN JSON blocks are written single-threadedly by the driver
        # before/after the whole batch, so they don't have this issue).
        _log_trace(trace_path, f"SYSTEM: {stage_label_prefix}Executing internal stage: {stage}")
        try:
            proc = subprocess.run(
                ["make", "-C", flow_dir, stage],
                env=env, cwd=flow_dir, capture_output=True, text=True,
                timeout=timeout_seconds,
            )
            combined = (proc.stdout or "") + "\nSTDERR:\n" + (proc.stderr or "")
            rc = proc.returncode
            rule_failures = []
            if stage == "metadata" and rc != 0:
                if _is_missing_rules_file_only_failure(combined):
                    rc = 0
                elif _is_metadata_rule_gate_failure(combined):
                    # A QoR threshold from the design's own rules file, not a
                    # crash: metadata.json is valid, so surface the failing
                    # rules as data instead of discarding the whole run.
                    rule_failures = _parse_metadata_rule_failures(combined)
                    rc = 0
            if log_dir is not None:
                log_dir.mkdir(parents=True, exist_ok=True)
                (log_dir / f"{stage}.log").write_text(combined)
            out = {"stage": stage, "returncode": rc,
                   "log_tail": _failure_excerpt(proc.stdout, proc.stderr)}
            if rule_failures:
                out["rule_failures"] = rule_failures
            return out
        except subprocess.TimeoutExpired:
            return {"stage": stage, "returncode": -1,
                    "error": f"Timeout after {timeout_seconds}s"}

    # `make <stage>` decides what to rebuild from file timestamps, and
    # DESIGN_CONFIG's *contents* aren't a tracked dependency -- without a
    # clean first, a second run silently no-ops and re-reports stale metrics.
    clean = _stage("clean_all")
    if clean.get("returncode") != 0:
        return {"crashed": True, "stage": "clean_all",
                "fatal_error": "clean_all failed before rebuild", "details": clean}

    rule_failures: list = []
    for stage in ("synth", "floorplan", "place", "cts", "route", "finish", "metadata"):
        res = _stage(stage)
        rule_failures = res.get("rule_failures", rule_failures)
        if res.get("returncode") != 0:
            # Archive whatever reports the stages that DID pass produced. This
            # is the case they matter most for -- a crash leaves no metadata to
            # parse, so the partial reports are the only quantitative record of
            # how far the flow got, and the next run's `clean_all` deletes them.
            if run_dir_path is not None:
                _save_orfs_reports(run_dir_path, Path(reports_root), run_index)
            return {"crashed": True, "stage": stage,
                    "fatal_error": f"Flow crashed during {stage}", "details": res}

    for path in (Path(reports_root) / "metadata.json",
                 Path(reports_root).parent / "metadata.json"):
        if not path.exists():
            continue
        raw = json.loads(path.read_text())
        setup_wns = raw.get("finish__timing__setup__ws", 0.0)
        hold_wns = raw.get("finish__timing__hold__ws", 0.0)
        drc_errors = raw.get("detailedroute__route__drc_errors", 0)
        utilization = raw.get("finish__design__instance__utilization", 0.0)
        is_closed = setup_wns >= 0 and hold_wns >= 0 and drc_errors == 0

        summary = {
            "crashed": False,
            "status": "CLOSED - READY FOR OPTIMIZATION" if is_closed else "VIOLATIONS_DETECTED",
            "violations": {
                "setup_wns_slack": setup_wns,
                "setup_tns_slack": raw.get("finish__timing__setup__tns", 0.0),
                "hold_wns_slack": hold_wns,
                "drc_error_count": drc_errors,
            },
            "physical_metrics": {
                "core_utilization_percent": round(utilization * 100, 2),
                "total_power": raw.get("finish__power__total", 0.0),
                "core_area": raw.get("finish__design__core__area", 0),
            },
        }
        util_pct = summary["physical_metrics"]["core_utilization_percent"]
        if util_pct >= 85:
            summary["area_headroom_warning"] = (
                f"Achieved utilization is {util_pct}% -- the die is nearly full, "
                "regardless of what CORE_UTILIZATION is set to. Area-consuming knobs "
                "(CELL_PAD_IN_SITES_GLOBAL_PLACEMENT, CELL_PAD_IN_SITES_DETAIL_PLACEMENT, "
                "and raising SETUP_SLACK_MARGIN, which inserts repair buffers) will very "
                "likely crash placement or routing here. Create room first by lowering "
                "CORE_UTILIZATION or PLACE_DENSITY before reaching for them."
            )
        if rule_failures:
            summary["qor_rule_failures"] = rule_failures
        _save_flow_artifacts(run_dir_path, Path(reports_root), Path(results_root),
                             run_index, summary)
        return summary

    return {"crashed": False, "status": "PARSE_ERROR",
            "error": "Failed to parse reports. metadata.json missing."}


def _save_flow_artifacts(run_dir: Optional[Path], reports_root: Path, results_root: Path,
                         run_index: int, summary: dict) -> None:
    """Archive this run's GDS/layout/summary/reports under run_dir. Every run
    keeps its own copy (gds/run_N_*, reports/run_N/), and the `final.*` copies
    track the latest -- the driver promotes the *best* run's copies over them
    when the loop ends."""
    if run_dir is None:
        return
    _save_orfs_reports(run_dir, reports_root, run_index)
    try:
        gds_dir = run_dir / "gds"
        src_gds = results_root / "6_final.gds"
        if src_gds.exists():
            gds_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_gds, gds_dir / f"run_{run_index}_final.gds")
            shutil.copy2(src_gds, run_dir / "final.gds")
        # GDS is binary; ORFS already rasterizes the finished layout as part
        # of its own reporting, so reuse that for the dashboard thumbnail.
        src_webp = reports_root / "final_all.webp"
        if src_webp.exists():
            gds_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_webp, gds_dir / f"run_{run_index}_layout.webp")
            shutil.copy2(src_webp, run_dir / "final_layout.webp")
        summaries = run_dir / "summaries"
        summaries.mkdir(parents=True, exist_ok=True)
        (summaries / f"run_{run_index}.json").write_text(json.dumps(summary, indent=2))
        (run_dir / "latest_summary.json").write_text(json.dumps(summary, indent=2))
    except OSError:
        pass  # artifact archiving must never fail an otherwise-good run


_NETGEN_SETUP = "/root/chia-orfs/lvs/sky130hd_netgen_setup.tcl"
# Anchored on netgen's FINAL verdict line, not on any "Netlists match" in the
# body: it prints a per-subcircuit result for every cell it compares, so an
# unanchored match reports a passing *standard cell* as a passing *design*.
# Same for the counts -- they appear once per compared subcircuit, and only the
# last pair is the top-level one, so these are matched with findall()[-1].
_NETGEN_RESULT_RE = re.compile(r"^Result:\s*(.+?)\s*$", re.M)
_NETGEN_DEV_RE = re.compile(
    r"Circuit 1 contains (\d+) devices?,\s+Circuit 2 contains (\d+) devices?")
_NETGEN_NET_RE = re.compile(
    r"Circuit 1 contains (\d+) nets?,\s+Circuit 2 contains (\d+) nets?")
# Per-subcircuit mismatch tables ("Subcircuit summary:" blocks) only appear in
# netgen's -batch lvs 4th-argument LOG FILE, never in stdout -- stdout only
# carries the terse top-level "Circuit 1/2 contains N devices"/"Result:"
# lines the three regexes above match. A subcircuit that matched cleanly
# prints no counts at all ("Device classes X and Y are equivalent."), so any
# block containing "Mismatch" is a real per-cell discrepancy.
_NETGEN_SUBCKT_NAME_RE = re.compile(r"Circuit 1:\s*(\S+)\s*\|Circuit 2:\s*\S+")
_NETGEN_SUBCKT_DEV_RE = re.compile(
    r"Number of devices:\s*(\d+)[^|]*\|\s*Number of devices:\s*(\d+)")
_NETGEN_SUBCKT_NET_RE = re.compile(
    r"Number of nets:\s*(\d+)[^|]*\|\s*Number of nets:\s*(\d+)")

# Verified 2026-09-03 by isolating the standalone sky130_fd_sc_hd library cell
# into its own single-top-cell GDS (zero full-chip context) and reading its
# own extracted netlist directly: sky130_fd_sc_hd__a21oi_2's NMOS AND-leg
# (A1 series A2) is laid out as two parallel half-width stacks (nodes $10/$11
# from the isolated extraction) rather than one full-width series pair the
# `m=2` schematic collapses to. This is a real, cell-intrinsic mask decision,
# not a missing `connect()` rule in the LVS deck: extraction is purely
# layer-geometry-driven (same-layer touching polygons merge regardless of any
# series/parallel LVS setting), and sky130's local-interconnect chain
# (NSD/PSD->LICON->LI->MCON->MET1->...) used by both our KLayout deck and this
# check is already complete, so if $10/$11 were physically strapped anywhere
# this extraction would already show one node, the same way it correctly
# merges the PMOS side (3=3, always matches). Nor is it something netgen's
# series-combine can fold on its own: that requires the two series devices to
# share a gate net, and here they don't (A1 vs A2) -- reconciling it needs
# recognizing the two stacks as isomorphic *compound* units and merging them
# as a pair, which is a graph-isomorphism step no standard LVS combiner
# (KLayout's or netgen's) performs. PMOS always matches (3=3); only the NMOS
# side folds this way. Keyed on the exact per-cell (layout, schematic) counts
# from that isolated extraction -- NOT the generic numbers in the upstream
# skywater-pdk#205 tracker issue, which describe a different cell.
KNOWN_NETGEN_FOLD_EXCEPTIONS = {
    "sky130_fd_sc_hd__a21oi_2": {"devices": (8, 6), "nets": (11, 10)},
}


def _netgen_subcircuit_mismatches(log_text: str) -> list:
    """Every subcircuit netgen flagged with a device/net count discrepancy,
    parsed from the per-cell 'Subcircuit summary:' tables in netgen's log
    file. Cells that matched cleanly print no such table and are absent.
    """
    out = []
    for block in log_text.split("Subcircuit summary:")[1:]:
        name_m = _NETGEN_SUBCKT_NAME_RE.match(block.lstrip())
        # The block's closing divider is a line of pure dashes with no `|`
        # (the header divider "---|---" has one, so plain "^-{10,}$" only
        # matches the closing line, never the header).
        end_m = re.search(r"^-{10,}\s*$", block, re.M)
        body = block[:end_m.start()] if end_m else block
        if not name_m or "Mismatch" not in body:
            continue
        dev_m, net_m = _NETGEN_SUBCKT_DEV_RE.search(body), _NETGEN_SUBCKT_NET_RE.search(body)
        if not (dev_m and net_m):
            continue
        out.append({
            "cell": name_m.group(1),
            "devices": (int(dev_m.group(1)), int(dev_m.group(2))),
            "nets": (int(net_m.group(1)), int(net_m.group(2))),
        })
    return out


def _netgen_known_exception_only(mismatches: list) -> bool:
    """True iff every flagged subcircuit matches a known, individually
    verified fold exception exactly (same cell, same device/net counts) --
    never a blanket "ignore LVS mismatches" escape hatch. False (not "don't
    know") when there are no mismatches at all: this only means something
    when there's a real discrepancy to compare against the known list.
    """
    if not mismatches:
        return False
    return all(
        KNOWN_NETGEN_FOLD_EXCEPTIONS.get(m["cell"]) == {"devices": m["devices"], "nets": m["nets"]}
        for m in mismatches
    )


def _run_netgen_lvs(flow_dir: str, reports_root: str, results_root: str,
                    env: dict, timeout_seconds: int,
                    log_dir_path: Optional[Path]) -> dict:
    """Second-opinion LVS via netgen, the comparator OpenLane/Tiny Tapeout use.

    Deliberately *additional* to KLayout's, not a replacement: it reads the
    `*_extracted.cir` KLayout has already written, so extraction is unchanged
    and this adds no PDK dependency. What it adds is series+parallel device
    combination (`lvs/sky130hd_netgen_setup.tcl`, ported from open_pdks'
    sky130_setup.tcl), which is what reconciles sky130's folded standard cells
    -- KLayout's combiner does the parallel step only, so cells declared `m=2`
    on a transistor stack can never match there.

    Best-effort and non-fatal: netgen missing, or no extracted netlist (KLayout
    LVS not configured for the platform), reports `supported: False` rather
    than failing signoff.
    """
    if not shutil.which("netgen-lvs"):
        return {"supported": False, "note": "netgen-lvs not installed in this image."}
    if not Path(_NETGEN_SETUP).is_file():
        return {"supported": False, "note": f"netgen setup file missing: {_NETGEN_SETUP}"}

    results, objects = Path(results_root), Path(str(results_root).replace("/results/", "/objects/", 1))
    extracted = next(iter(sorted(results.glob("*_extracted.cir"))), None)
    cdl = objects / "6_final_concat.cdl"
    if extracted is None or not cdl.is_file():
        return {"supported": False,
                "note": "no KLayout-extracted netlist / concat CDL to compare."}
    # The top cell is whatever .SUBCKT the extracted netlist declares first --
    # taking it from the file rather than the design name, which need not match.
    try:
        top = next(ln.split()[1] for ln in extracted.read_text(errors="replace").splitlines()
                   if ln.upper().startswith(".SUBCKT"))
    except (StopIteration, IndexError, OSError):
        return {"supported": False, "note": "could not determine top cell from extracted netlist."}

    out_log = (log_dir_path / "lvs_netgen.log") if log_dir_path else Path("/tmp/lvs_netgen.log")
    try:
        if log_dir_path is not None:
            log_dir_path.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["netgen-lvs", "-batch", "lvs",
             f"{extracted} {top}", f"{cdl} {top}", _NETGEN_SETUP, str(out_log)],
            env=env, cwd=flow_dir, capture_output=True, text=True, timeout=timeout_seconds,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"supported": True, "clean": None, "error": f"netgen failed to run: {exc}"}

    stdout = proc.stdout or ""
    verdicts = _NETGEN_RESULT_RE.findall(stdout)
    verdict = verdicts[-1] if verdicts else None
    out: dict = {"supported": True, "top_cell": top, "verdict": verdict,
                 # Only netgen's own final line may set this. No verdict line at
                 # all means "don't know", never "clean".
                 "clean": (verdict is not None
                           and verdict.lower().startswith("netlists match")),
                 "report": str(out_log)}
    devs, nets = _NETGEN_DEV_RE.findall(stdout), _NETGEN_NET_RE.findall(stdout)
    if devs and nets:
        out["devices"] = {"layout": int(devs[-1][0]), "schematic": int(devs[-1][1])}
        out["nets"] = {"layout": int(nets[-1][0]), "schematic": int(nets[-1][1])}
        # Worth separating: devices matching but nets not is a connectivity
        # story, the reverse is a device-recognition one.
        out["devices_match"] = out["devices"]["layout"] == out["devices"]["schematic"]
        out["nets_match"] = out["nets"]["layout"] == out["nets"]["schematic"]
    # Per-subcircuit detail lives in the log FILE (out_log), never in stdout --
    # read it back to check whether every flagged cell is a known, individually
    # verified fold exception rather than a real, unexplained mismatch. Top-
    # level count deltas (devices/nets above) don't reconcile cleanly against
    # per-instance counts when a design has more than one flagged instance
    # (observed on `gcd`: 2 flagged a21oi_2 instances implied by the device
    # delta, but the net delta only fit 1) -- matching per-subcircuit instead
    # of trying to reconstruct instance counts from top-level deltas sidesteps
    # that reconciliation entirely.
    if not out["clean"] and out_log.exists():
        try:
            # Exclude the top cell's own summary: it recurs multiple times in
            # the log (observed: 3x for one run, not just a single final
            # block), always mismatches when the overall verdict does (that's
            # what "Netlists do not match" means), and is the aggregate this
            # check is trying to explain -- never itself a per-cell fold
            # exception candidate.
            mismatches = [
                m for m in _netgen_subcircuit_mismatches(out_log.read_text(errors="replace"))
                if m["cell"] != top
            ]
            out["subcircuit_mismatches"] = mismatches
            out["known_exception_only"] = _netgen_known_exception_only(mismatches)
            # Effective verdict for the loop to gate on: real match, or every
            # discrepancy traced to a specific, evidenced, individually-listed
            # exception -- never a blanket "ignore mismatches" escape hatch.
            out["effectively_clean"] = out["known_exception_only"]
        except OSError:
            pass
    if log_dir_path is not None:
        try:
            (log_dir_path / "lvs_netgen_stdout.log").write_text(
                stdout + "\nSTDERR:\n" + (proc.stderr or ""))
        except OSError:
            pass
    return out


def _save_orfs_reports(run_dir: Path, reports_root: Path, run_index: int) -> None:
    """Archive ORFS's own report files for this run under `reports/run_N/`.

    These are the reports the flow itself writes into
    `flow/reports/<platform>/<design>/<variant>/` -- the per-stage `.rpt` files
    (floorplan/place/resizer/CTS/route), `6_finish.rpt`, `metadata.json`, the
    DRC database, and ORFS's own rendered webps (congestion, IR drop, routing,
    worst path). They live inside the container and, critically, are
    **overwritten by the next run** at the same path: `run_flow_remote` starts
    with `make clean_all`, so without copying them out here they exist only
    until the next flow execution of that variant and are unrecoverable
    afterwards. `flow_logs/run_N/` captures make's stdout, which is a different
    thing -- the tools' *narration*, not the reports they produced.

    Best-effort per file: a report that can't be copied is skipped rather than
    failing an otherwise-good run, same contract as the caller.
    """
    if not reports_root.is_dir():
        return
    dest = run_dir / "reports" / f"run_{run_index}"
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    for src in sorted(reports_root.iterdir()):
        if not src.is_file():
            continue
        try:
            shutil.copy2(src, dest / src.name)
        except OSError:
            continue


def _is_missing_rules_file_only_failure(log_tail: str) -> bool:
    return any(marker in log_tail for marker in ("rules-base.json not found", "No rules"))

# checkMetadata.py prints one of these per rule it evaluates against the
# design's rules-<variant>.json, e.g.
#   [ERROR] detailedroute__route__wirelength fail test: 18569 <= 18000
_METADATA_RULE_FAILURE_RE = re.compile(
    r"^\s*\[ERROR\]\s+(\S+)\s+fail test:\s*(.+?)\s*$", re.M
)

def _parse_metadata_rule_failures(log: str) -> list:
    return [
        {"metric": m.group(1), "failed_check": m.group(2)}
        for m in _METADATA_RULE_FAILURE_RE.finditer(log)
    ]

# The sky130 toolchain floods stderr with these on every single shell
# invocation; they are harmless and would otherwise crowd out the real
# error in any fixed-size excerpt.
_LOG_NOISE_RE = re.compile(r"libtinfo\.so|no version information available", re.I)

# Lines that actually explain a failure: OpenROAD/ORFS tagged errors
# ("[ERROR DPL-0033] ..."), tcl errors ("Error: detail_place.tcl, 39 ..."),
# failed rule checks, and the make target that gave up.
_LOG_ERROR_RE = re.compile(r"\[ERROR[\s\]]|^\s*Error:|fail test:|\*\*\*\s+\[", re.I)

def _denoise_log(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not _LOG_NOISE_RE.search(l))

def _failure_excerpt(stdout: str, stderr: str, max_chars: int = 2000) -> str:
    """Build a log excerpt that actually explains why a stage failed.

    A plain tail of stdout+stderr is worse than useless here. stderr is
    appended last and is almost entirely `libtinfo.so.6` warnings, so the
    final 2000 characters are pure noise while the real cause -- e.g.
    "[ERROR FLW-0024] Place density exceeds 1.0" -- sits over a thousand
    lines earlier in stdout. The agent then has nothing to reason about and
    guesses blindly at its next move. So: surface the explicit error lines
    first, then pad with the tail of the de-noised stdout for context.
    """
    out, err = _denoise_log(stdout or ""), _denoise_log(stderr or "")
    seen, errors = set(), []
    for line in (out + "\n" + err).splitlines():
        s = line.strip()
        if s and _LOG_ERROR_RE.search(s) and s not in seen:
            seen.add(s)
            errors.append(s)

    parts = []
    if errors:
        parts.append("ERRORS:\n" + "\n".join(errors[-12:]))
    budget = max_chars - sum(len(p) for p in parts) - 16
    tail = out.strip()[-budget:] if budget > 200 else ""
    if tail:
        parts.append("LOG TAIL:\n" + tail)
    return "\n\n".join(parts) if parts else (out or err)[-max_chars:]

def _is_metadata_rule_gate_failure(log: str) -> bool:
    """True when the metadata stage failed *only* because checkMetadata.py
    found one or more rules-file thresholds unmet.

    This is a QoR quality gate, not a crash: metadata.json was generated
    fine and every metric in it is readable -- ORFS just judged the run
    against the design's golden rules-<variant>.json and one threshold
    (wirelength, cell count, ...) came in over budget. Treating that as
    "Flow crashed during metadata" throws away a completely valid result
    and leaves the agent with nothing to reason about, so the caller
    reports the failing rules alongside the real metrics instead.
    """
    return bool(_parse_metadata_rule_failures(log)) and "metadata-check]" in log

# TNS's contribution is squashed into [0, _TNS_TIEBREAK) so it can order two
# otherwise-equal candidates but can never outrank a real closure difference.
# _TNS_SCALE just sets where the squash is most sensitive (TNS routinely runs
# in the tens of ns on these designs).
_TNS_TIEBREAK = 0.01
_TNS_SCALE = 100.0


def _violation_score(violations: dict) -> float:
    """Lower is better. Ranks by what closure actually requires, with TNS as a
    pure tiebreak.

    Closure is defined solely by setup slack >= 0, hold slack >= 0 and zero
    router DRC (see orfs_loop.iteration_done) -- TNS appears nowhere in it. But
    TNS is a SUM over every violating path, so its magnitude scales with design
    size while WNS does not, and a flat weight lets it swamp the metrics that
    actually decide closure. Observed live on riscv32i: TNS ran -36 to -100
    against a WNS of -0.7, so at the previous 0.05 weight TNS outvoted WNS
    about 6:1 and a round elected a candidate that was worse on setup WNS AND
    12% larger, purely because its TNS was better. Both of those are the wrong
    direction, and the next round then branched from it.

    TNS is still real information -- fewer/less-violating paths generally means
    less work left -- so it is kept, just demoted to breaking ties between
    candidates whose closure-critical metrics match. The full per-metric deltas
    (including TNS) are reported to the model separately either way.
    """
    setup_wns = violations.get("setup_wns_slack", 0.0)
    hold_wns = violations.get("hold_wns_slack", 0.0)
    setup_tns = violations.get("setup_tns_slack", 0.0)
    drc = violations.get("drc_error_count", 0)

    closure = max(0.0, -setup_wns) + max(0.0, -hold_wns) + drc * 5.0
    tns = max(0.0, -setup_tns)
    tiebreak = _TNS_TIEBREAK * (tns / (tns + _TNS_SCALE)) if tns else 0.0
    return closure + tiebreak

def _diff_tunables(prev: Optional[dict], curr: dict) -> Optional[dict]:
    # None on the first run: there is no previous config to diff against, and
    # listing all ~22 tunables as "None -> value" is pure noise that buries
    # the real signal in every subsequent (genuinely small) diff.
    if prev is None:
        return None
    diff = {k: {"from": prev.get(k), "to": v} for k, v in curr.items() if prev.get(k) != v}
    # A key reverted to baseline (set_tunables' `null`) is absent from `curr`
    # entirely, so the comprehension above -- which only walks curr.items() --
    # never sees it: the revert silently vanishes from tunables_changed, and
    # therefore from recent_history too. That erases the model's only record
    # of "I tried this and gave up on it", which is exactly what let it
    # re-enable a flag several turns later that it had already reverted,
    # believing it had never touched it. Explicitly record every key present
    # in `prev` but missing from `curr` as {"from": <value>, "to": None}.
    for k, v in prev.items():
        if k not in curr:
            diff[k] = {"from": v, "to": None}
    return diff

class ORFSTool(ChiaTool):
    def setup(
        self,
        flow_dir: str,
        design_config_mk: str,
        schema_path: str,
        reports_root: str,
        stage_timeout_seconds: int = DEFAULT_STAGE_TIMEOUT_SECONDS,
        design_config_platform: Optional[str] = None,
        design_name: Optional[str] = None,
        extra_env: Optional[dict] = None,
        locked_tunables: Optional[dict] = None,
        run_dir: Optional[str] = None,
        results_root: Optional[str] = None,
        fresh_config: bool = True,
    ):
        self.flow_dir = Path(flow_dir)
        self.baseline_config_mk = Path(design_config_mk)
        self.schema = load_schema(schema_path)

        # CLOCK_PERIOD has no baseline value in config.mk to fall back on (see
        # _read_baseline_clock_period_remote) -- bounds have to be computed
        # per-design from the value this design's own constraint.sdc already
        # uses, since "ns vs ps" and "what's a sane period" both depend on the
        # PDK. If this design's SDC doesn't match a pattern we can patch,
        # drop the knob entirely rather than offer one that will fail on use.
        self._baseline_clock_period: Optional[float] = None
        if "CLOCK_PERIOD" in self.schema:
            self._baseline_clock_period = get(
                _read_baseline_clock_period_remote.chia_remote(str(self.baseline_config_mk))
            )
            if self._baseline_clock_period is None:
                self.schema.pop("CLOCK_PERIOD", None)
            else:
                spec = self.schema["CLOCK_PERIOD"]
                spec["min"] = round(self._baseline_clock_period * 0.3, 6)
                spec["max"] = round(self._baseline_clock_period * 3.0, 6)

        # DIE_AREA_SCALE is only safe when this design's baseline already
        # uses ORFS's explicit die/core-area floorplan method -- floorplan.tcl
        # picks exactly one of 4 mutually-exclusive init methods by which env
        # vars are non-empty, and hard-exits if more than one is set. A
        # CORE_UTILIZATION-based design (the common case) already has its own
        # equivalent lever in the schema; introducing DIE_AREA/CORE_AREA on
        # top of it would make both methods "set" at once and crash the
        # instant the model touches this knob. Drop it entirely rather than
        # offer something unsafe to use.
        self._baseline_die_area: Optional[str] = None
        self._baseline_core_area: Optional[str] = None
        if "DIE_AREA_SCALE" in self.schema:
            floorplan = get(
                _read_baseline_floorplan_remote.chia_remote(str(self.baseline_config_mk))
            )
            if floorplan.get("method") == "explicit_area":
                self._baseline_die_area = floorplan["die_area"]
                self._baseline_core_area = floorplan["core_area"]
            else:
                self.schema.pop("DIE_AREA_SCALE", None)

        self.reports_root = Path(reports_root)
        self.stage_timeout_seconds = stage_timeout_seconds
        self.extra_env = extra_env or {}
        # Hard user constraints: validated/rendered once here, then re-applied
        # to every set_tunables call regardless of what the LLM requests, so
        # these can never drift even if the model ignores the prompt's
        # instructions or a request tries to smuggle a change through.
        self._locked = validate_tunables(locked_tunables or {}, self.schema)

        # Where this run's artifacts (final GDS, full stage logs, summaries,
        # this run's own tool_trace.log) get collected. Must be a path valid
        # from inside this worker's filesystem (e.g. under the /root/chia-orfs
        # bind mount), not a host-only path -- setup() runs on the driver but
        # get_tunables/set_tunables/run_full_flow_and_summarize run on the
        # orfs_run worker.
        self._run_dir = Path(run_dir) if run_dir else None
        self._trace_log_path = (self._run_dir / "tool_trace.log") if self._run_dir else DEFAULT_TRACE_LOG_PATH
        # ORFS's own layout always puts "results" as a sibling of "reports"
        # (both under <platform>/<design_nickname>/<variant>) -- derive it
        # from reports_root unless the caller wants to override.
        self.results_root = Path(results_root) if results_root else Path(
            str(self.reports_root).replace("/reports/", "/results/", 1)
        )
        self._flow_run_count = 0
        # True while a run_full_flow_and_summarize call is mid-flight. The
        # tool actor accepts concurrent calls on purpose (max_concurrency=4,
        # see ORFS_TASK_OPTIONS) so a long flow can't starve get_tunables --
        # but two *flows* must never overlap: every call starts with `make
        # clean_all`, which would wipe results/ out from under a flow that's
        # still running and fail it with a spurious crash. See the guard in
        # run_full_flow_and_summarize.
        self._flow_in_progress = False
        # Snapshot of tunables in effect during the most recent
        # run_full_flow_and_summarize call. Set to a sentinel (not None) once
        # the first call has happened, so a second call with an unchanged
        # config can be refused -- see run_full_flow_and_summarize.
        self._config_at_last_run: Optional[dict] = None
        # Cross-call memory: every run_full_flow_and_summarize call appends
        # one compact entry here (tunables changed, outcome). Used to compute
        # an explicit better/worse verdict each call instead of relying on
        # the LLM to remember and re-derive trends from its own past tool
        # outputs -- see _compare_and_record.
        self._run_history: list = []

        self._backup_dir = self.baseline_config_mk.parent / "chia_backups"
        self._working_config_mk = self.baseline_config_mk.parent / "config.chia.mk"
        get(_prep_working_config_remote.chia_remote(
            str(self.baseline_config_mk),
            str(self._backup_dir),
            str(self._working_config_mk),
            fresh_config,
        ))

        if self._locked:
            # Bake locked values into the working config immediately, so
            # they're in effect even if the baseline disagreed with them and
            # no set_tunables call happens before the first flow run. Must go
            # through the orfs_run worker (chia_remote), same as the prep
            # step above -- setup() itself runs on the driver, which doesn't
            # have this config.mk path on its own filesystem.
            get(_apply_locked_tunables_remote.chia_remote(
                str(self.baseline_config_mk),
                str(self._working_config_mk),
                json.dumps(self.schema),
                json.dumps(self._locked),
            ))

        # The LLM is now strictly a Config Editor. It has exactly 3 tools.
        #
        # Registered WITHOUT a `{self.name}_` prefix, deliberately: opencode
        # namespaces every MCP tool as `{server_key}_{registered_name}`, and
        # chia registers this server under `self.name`. Prefixing here too
        # produced `orfs_gcd_ab12_orfs_gcd_ab12_get_tunables` -- while the
        # system prompt (see orfs_loop._load_prompt, which substitutes
        # $TOOL_NAME -> self.name) told the model to call
        # `orfs_gcd_ab12_get_tunables`, a name that did not exist. Strong
        # models silently recovered by reading the real names out of
        # tools/list; weaker ones (nemotron) called the documented name,
        # got "unavailable tool", and stalled the whole run. Bare names here
        # make opencode's final name match what the prompt advertises.
        self.mcp.add_tool(self.get_tunables, name="get_tunables")
        self.mcp.add_tool(self.set_tunables, name="set_tunables")
        self.mcp.add_tool(self.run_full_flow_and_summarize, name="run_full_flow_and_summarize")

    def _trace(self, event: str, payload: str = "") -> None:
        _log_trace(self._trace_log_path, event, payload)

    def get_tunables(self) -> str:
        """Returns the current active configuration, schema bounds, and any
        locked tunables the user has fixed (these cannot be changed)."""
        self._trace("CALL: get_tunables")
        current = load_current_tunables_from_config_mk(self._working_config_mk, self.schema)
        if "CLOCK_PERIOD" not in current and self._baseline_clock_period is not None:
            # Never explicitly set -- show this design's real starting point
            # rather than omitting the key, since (unlike every other
            # tunable) it has no representation in config.mk to read back.
            current["CLOCK_PERIOD"] = str(self._baseline_clock_period)
        if "DIE_AREA_SCALE" not in current and self._baseline_die_area is not None:
            current["DIE_AREA_SCALE"] = "1.0"  # unset == this design's own baseline die/core area
        res = json.dumps(
            {"current": current, "schema": self.schema, "locked": self._locked},
            indent=2,
        )
        self._trace("RETURN SUCCESS: get_tunables", res)
        return res

    def set_tunables(self, tunables_json: str) -> str:
        """Applies configuration edits. Pass a JSON object of key-value pairs.
        Pass `null` as a key's value to remove your override entirely and
        revert that key to the design's original baseline (useful when a
        change didn't help and you want to go back to "untouched" rather
        than guessing a value). Keys in the user's locked set are always
        forced back to their fixed value, no matter what is requested here,
        including an attempted unset."""
        self._trace("CALL: set_tunables", tunables_json)
        try:
            requested = json.loads(tunables_json)
            current = load_current_tunables_from_config_mk(self._working_config_mk, self.schema)

            unset_keys = [k for k, v in requested.items() if v is None]
            unknown_unset = [k for k in unset_keys if k not in self.schema]
            set_requested = {k: v for k, v in requested.items() if v is not None}

            merged = {**current, **set_requested}
            for key in unset_keys:
                merged.pop(key, None)

            # Hard enforcement: detect any requested change to a locked key
            # (for an honest error back to the caller), then force every
            # locked key to its fixed value regardless -- this line is the
            # actual safety boundary, not the detection above it.
            rejected = []
            for key, locked_value in self._locked.items():
                if key in requested:
                    try:
                        requested_rendered = validate_tunables({key: requested[key]}, self.schema)[key]
                    except Exception:
                        requested_rendered = str(requested[key])
                    if requested_rendered != locked_value:
                        rejected.append({
                            "key": key, "requested": requested[key], "locked_value": locked_value,
                        })
                merged[key] = locked_value

            written = render_config_mk(self.baseline_config_mk, merged, self._working_config_mk, self.schema)
            result = {"written_successfully": written}
            applied_unsets = [k for k in unset_keys if k not in unknown_unset]
            if applied_unsets:
                result["reverted_to_baseline"] = applied_unsets
            if unknown_unset:
                result["unknown_unset_keys"] = unknown_unset
                result.setdefault("warning", (
                    f"{unknown_unset} are not in the tunable schema, so there is no "
                    "override to remove -- ignored."
                ))
            if rejected:
                result["rejected_locked_tunables"] = rejected
                result["warning"] = (
                    "The tunables above are locked by the user and cannot be changed. "
                    "Their values were kept at the locked value; do not retry them."
                )
            res = json.dumps(result)
            self._trace("RETURN SUCCESS: set_tunables", res)
            return res
        except Exception as e:
            err = json.dumps({"error": str(e)})
            self._trace("RETURN ERROR: set_tunables", err)
            return err

    def _run_make_stage(self, stage: str, log_dir: Optional[Path] = None) -> dict:
        """Internal deterministic executor. Hidden from the LLM."""
        env = os.environ.copy()
        env["DESIGN_CONFIG"] = str(self._working_config_mk)
        env.update(self.extra_env)
        try:
            proc = subprocess.run(
                ["make", "-C", str(self.flow_dir), stage],
                env=env, cwd=str(self.flow_dir), capture_output=True, text=True, timeout=self.stage_timeout_seconds
            )
            combined = (proc.stdout or "") + "\nSTDERR:\n" + (proc.stderr or "")
            rc = proc.returncode
            rule_failures = []
            if stage == "metadata" and rc != 0:
                if _is_missing_rules_file_only_failure(combined):
                    rc = 0
                elif _is_metadata_rule_gate_failure(combined):
                    # Not a crash -- a QoR threshold in the design's rules
                    # file was missed. metadata.json is valid and parseable,
                    # so let the flow succeed and surface the failing rules
                    # as data rather than discarding the whole run.
                    rule_failures = _parse_metadata_rule_failures(combined)
                    rc = 0
            if log_dir is not None:
                # Full log, unlike the 2000-char tail below -- for a human
                # to actually debug a failed stage after the fact.
                log_dir.mkdir(parents=True, exist_ok=True)
                (log_dir / f"{stage}.log").write_text(combined)
            result = {
                "stage": stage,
                "returncode": rc,
                "log_tail": _failure_excerpt(proc.stdout, proc.stderr),
            }
            if rule_failures:
                result["rule_failures"] = rule_failures
            return result
        except subprocess.TimeoutExpired:
            return {"stage": stage, "returncode": -1, "error": f"Timeout after {self.stage_timeout_seconds}s"}

    def _best_run_so_far(self) -> Optional[dict]:
        """The best completed run seen so far, with the full config that
        produced it.

        Without this the agent has to reconstruct its own high-water mark by
        replaying `tunables_changed` deltas across `recent_history`, which in
        practice it does not do -- it finds a good config, wanders off, and
        never returns. Handing back the exact config to restore makes
        "go back to your best" a single `set_tunables` call.
        """
        scored = [e for e in self._run_history if e.get("violations")]
        if not scored:
            return None
        CLOSED = "CLOSED - READY FOR OPTIMIZATION"
        closed = [e for e in scored if e["status"] == CLOSED]
        if closed:
            # Timing margin first, area only as a tie-break. All CLOSED runs
            # already have setup/hold slack >= 0 and zero (router-reported)
            # DRC errors, but "just barely closed" and "closed with healthy
            # margin" are not equally trustworthy going into signoff -- a
            # razor-thin margin is far more likely to flip to a real
            # DRC/LVS failure under the standalone KLayout checks (which
            # catch things the router's own DRC count doesn't) than a run
            # with more headroom, regardless of which one is smaller. Rank
            # by the worst (binding) of setup/hold slack, descending, and
            # only fall back to smallest area when two runs tie on that.
            best = min(
                closed,
                key=lambda e: (
                    -min(e["violations"]["setup_wns_slack"], e["violations"]["hold_wns_slack"]),
                    e["physical_metrics"]["core_area"],
                ),
            )
        else:
            best = min(scored, key=lambda e: _violation_score(e["violations"]))
        return {
            "run": best["run"],
            "status": best["status"],
            "violations": best["violations"],
            "physical_metrics": best.get("physical_metrics"),
            "config_to_restore_it": best.get("_config"),
        }

    def _compare_and_record(
        self,
        tunables_changed: dict,
        status: str,
        config: Optional[dict] = None,
        violations: Optional[dict] = None,
        physical_metrics: Optional[dict] = None,
        crash_info: Optional[dict] = None,
    ) -> dict:
        """Computes an explicit verdict against the previous run and appends
        this run to self._run_history. Returns the fields to merge into the
        tool's response so the caller never has to re-derive trends from raw
        numbers across separate tool calls."""
        prev = self._run_history[-1] if self._run_history else None
        comparison: dict = {}
        CLOSED = "CLOSED - READY FOR OPTIMIZATION"

        if prev is None:
            comparison["verdict"] = "FIRST_RUN"
            comparison["note"] = "No prior run to compare against."
        elif status == "CRASHED":
            comparison["verdict"] = "CRASHED"
            comparison["note"] = (
                "This exact combination of tunables crashed the flow "
                f"(stage: {crash_info.get('stage') if crash_info else 'unknown'}). "
                "Do not retry these exact values -- change something."
            )
        elif prev["status"] == "CRASHED":
            comparison["verdict"] = "RECOVERED"
            comparison["note"] = "Previous change crashed the flow; this one at least completed."
        elif status == CLOSED and prev["status"] != CLOSED:
            comparison["verdict"] = "IMPROVED"
            comparison["note"] = "Violations are now fully resolved -- best state seen so far."
        elif status != CLOSED and prev["status"] == CLOSED:
            comparison["verdict"] = "REGRESSED"
            comparison["note"] = (
                "This change reintroduced violations after the design was "
                "previously closed. Revert the tunables changed this run."
            )
        elif status == "VIOLATIONS_DETECTED" and prev["status"] == "VIOLATIONS_DETECTED":
            prev_v, curr_v = prev["violations"], violations
            comparison["violation_deltas"] = {
                k: {
                    "previous": prev_v[k], "current": curr_v[k],
                    "delta": round(curr_v[k] - prev_v[k], 6),
                }
                for k in ("setup_wns_slack", "setup_tns_slack", "hold_wns_slack", "drc_error_count")
            }
            prev_score, curr_score = _violation_score(prev_v), _violation_score(curr_v)
            if curr_score < prev_score - 1e-9:
                comparison["verdict"] = "IMPROVED"
            elif curr_score > prev_score + 1e-9:
                comparison["verdict"] = "REGRESSED"
                comparison["note"] = (
                    "This change made violations worse overall (see "
                    "violation_deltas). Revert the tunables changed this run "
                    "and try a different knob instead of pushing further in "
                    "the same direction."
                )
            else:
                comparison["verdict"] = "UNCHANGED"
        elif status == CLOSED and prev["status"] == CLOSED:
            prev_m, curr_m = prev["physical_metrics"], physical_metrics
            comparison["physical_deltas"] = {
                k: {
                    "previous": prev_m[k], "current": curr_m[k],
                    "delta": round(curr_m[k] - prev_m[k], 6),
                }
                for k in ("core_utilization_percent", "total_power", "core_area")
            }
            if curr_m["core_area"] <= prev_m["core_area"] and curr_m["total_power"] <= prev_m["total_power"]:
                comparison["verdict"] = "IMPROVED"
            elif curr_m["core_area"] >= prev_m["core_area"] and curr_m["total_power"] >= prev_m["total_power"]:
                comparison["verdict"] = "REGRESSED"
                comparison["note"] = "Area and power both got worse -- revert this change."
            else:
                comparison["verdict"] = "MIXED"
        else:
            comparison["verdict"] = "DIFFERENT_OUTCOME"
            comparison["note"] = f"Previous run status was {prev['status']}, current is {status} -- not directly comparable."

        entry = {"run": self._flow_run_count, "status": status}
        if tunables_changed is not None:
            entry["tunables_changed"] = tunables_changed
        if violations is not None:
            entry["violations"] = violations
        if physical_metrics is not None:
            entry["physical_metrics"] = physical_metrics
        if crash_info is not None:
            entry["crash_stage"] = crash_info.get("stage")
        # Underscore-prefixed: kept for _best_run_so_far, stripped from
        # recent_history below so the response doesn't carry a full config
        # snapshot per run.
        entry["_config"] = config
        self._run_history.append(entry)

        result = {
            "tunables_changed_this_run": (
                tunables_changed if tunables_changed is not None
                else "(baseline run -- nothing changed yet)"
            ),
            "comparison_to_previous_run": comparison,
            "recent_history": [
                {k: v for k, v in e.items() if not k.startswith("_")}
                for e in self._run_history[-6:]
            ],
        }
        best = self._best_run_so_far()
        if best is not None and best["run"] != self._flow_run_count:
            result["best_run_so_far"] = best
            result["best_run_note"] = (
                "This earlier run is still the best result. If your recent "
                "changes have not beaten it, pass `config_to_restore_it` to "
                "set_tunables to return there before trying a different knob "
                "-- do not keep exploring away from your best result."
            )
        return result

    def _active_clock_period(self, current_snapshot: dict) -> Optional[float]:
        """The clock period in effect for this run: the LLM's override if it
        ever set one, else this design's own baseline (see setup()) -- CLOCK_PERIOD
        has no representation in config.mk to read back, unlike every other
        tunable, so it can't be derived from current_snapshot alone."""
        raw = current_snapshot.get("CLOCK_PERIOD")
        if raw is not None:
            try:
                return float(raw)
            except ValueError:
                pass
        return self._baseline_clock_period

    async def run_full_flow_and_summarize(self) -> str:
        """Executes the entire ORFS pipeline deterministically and returns a summarized parsing of violations."""
        self._trace("CALL: run_full_flow_and_summarize")

        if self._flow_in_progress:
            # A duplicate call while a flow is still running. Left to proceed,
            # its `make clean_all` deletes results/ under the in-flight flow,
            # which then fails on a missing stage output and reports a
            # "Flow crashed during route" that has nothing to do with the
            # tunables being tested -- poisoning the model's own bisection
            # (it records that config as a bad boundary) and wasting a full
            # rebuild. The blocked_no_config_change guard below does NOT
            # cover this: right after a real set_tunables the config genuinely
            # differs, so a duplicate sails past it.
            #
            # Setting the flag immediately below with no await in between
            # makes check-and-set atomic on the actor's event loop.
            err = json.dumps({
                "error": "blocked_flow_already_running",
                "message": (
                    "Refusing to run: a run_full_flow_and_summarize call is "
                    "already in progress and has not returned yet. Wait for "
                    "its result rather than issuing another call -- the flow "
                    "takes minutes and only one can run at a time. Do not "
                    "retry; the in-flight call will return on its own."
                ),
            })
            self._trace(
                "RETURN ERROR: run_full_flow_and_summarize (blocked, flow already running)", err)
            return err
        self._flow_in_progress = True
        try:
            return await self._run_full_flow_impl()
        finally:
            self._flow_in_progress = False

    async def _run_full_flow_impl(self) -> str:
        current_snapshot = load_current_tunables_from_config_mk(self._working_config_mk, self.schema)
        if self._config_at_last_run is not None and current_snapshot == self._config_at_last_run:
            # Refuse: forces a real decision instead of re-running an
            # unchanged config to "double check" a result that (now that
            # clean_all forces a genuine rebuild every time) is already
            # deterministic -- rerunning it again can only ever produce the
            # same numbers. Every call must be preceded by a set_tunables
            # call that actually changes at least one value.
            err = json.dumps({
                "error": "blocked_no_config_change",
                "message": (
                    "Refusing to run: the config is identical to the last "
                    "run_full_flow_and_summarize call, so this would just "
                    "reproduce the same result. Call set_tunables with a "
                    "genuine change to at least one tunable first -- use "
                    "the metrics from the last result (and get_tunables for "
                    "current values/bounds) to decide what to change."
                ),
            })
            self._trace("RETURN ERROR: run_full_flow_and_summarize (blocked, no config change)", err)
            return err
        prev_config = self._config_at_last_run
        tunables_changed = _diff_tunables(prev_config, current_snapshot)
        self._config_at_last_run = current_snapshot

        self._flow_run_count += 1
        log_dir = (self._run_dir / "flow_logs" / f"run_{self._flow_run_count}") if self._run_dir else None

        # 0. Force a real rebuild. `make <stage>` alone only reruns a stage
        # whose *file* prerequisites (Verilog, previous-stage outputs) are
        # stale -- it has no idea DESIGN_CONFIG's contents changed, since
        # that's an env var, not a tracked file. Without this, every call
        # after the first is a silent no-op ("Nothing to be done for
        # 'synth'.") that just re-reports the first run's stale metrics,
        # regardless of what set_tunables changed. Costs a full rebuild per
        # call, but a closure loop that doesn't actually re-run on every
        # tunable change isn't a closure loop.
        self._trace("SYSTEM: Executing internal stage: clean_all")
        clean_res = await asyncio.to_thread(self._run_make_stage, "clean_all", log_dir=log_dir)
        if clean_res.get("returncode") != 0:
            err_dict = {
                "fatal_error": "clean_all failed before rebuild", "details": clean_res,
                "clock_period": self._active_clock_period(current_snapshot),
            }
            err_dict.update(self._compare_and_record(
                tunables_changed, "CRASHED", config=current_snapshot,
                crash_info={"stage": "clean_all"},
            ))
            err = json.dumps(err_dict)
            self._trace("RETURN ERROR: run_full_flow_and_summarize", err)
            self._save_run_artifacts(err_dict)
            return err

        # 1. Deterministic Execution Sequence
        stages = ["synth", "floorplan", "place", "cts", "route", "finish", "metadata"]
        rule_failures = []
        for stage in stages:
            self._trace(f"SYSTEM: Executing internal stage: {stage}")
            res = await asyncio.to_thread(self._run_make_stage, stage, log_dir=log_dir)
            rule_failures = res.get("rule_failures", rule_failures)
            if res.get("returncode") != 0:
                err_dict = {
                    "fatal_error": f"Flow crashed during {stage}", "details": res,
                    "clock_period": self._active_clock_period(current_snapshot),
                }
                err_dict.update(self._compare_and_record(
                    tunables_changed, "CRASHED", config=current_snapshot,
                    crash_info={"stage": stage},
                ))
                err = json.dumps(err_dict)
                self._trace("RETURN ERROR: run_full_flow_and_summarize", err)
                self._save_run_artifacts(err_dict)
                return err

        # 2. Python Report Parser: Extract and summarize violations
        candidates = [self.reports_root / "metadata.json", self.reports_root.parent / "metadata.json"]
        for path in candidates:
            if path.exists():
                raw = json.loads(path.read_text())
                
                # Extract strict closure metrics
                setup_wns = raw.get("finish__timing__setup__ws", 0.0)
                setup_tns = raw.get("finish__timing__setup__tns", 0.0)
                hold_wns = raw.get("finish__timing__hold__ws", 0.0)
                drc_errors = raw.get("detailedroute__route__drc_errors", 0)
                utilization = raw.get("finish__design__instance__utilization", 0.0)
                power = raw.get("finish__power__total", 0.0)
                core_area = raw.get("finish__design__core__area", 0)

                # Determine if design has violations
                is_closed = setup_wns >= 0 and hold_wns >= 0 and drc_errors == 0
                
                summary = {
                    "status": "CLOSED - READY FOR OPTIMIZATION" if is_closed else "VIOLATIONS_DETECTED",
                    "violations": {
                        "setup_wns_slack": setup_wns,
                        "setup_tns_slack": setup_tns,
                        "hold_wns_slack": hold_wns,
                        "drc_error_count": drc_errors
                    },
                    "physical_metrics": {
                        "core_utilization_percent": round(utilization * 100, 2),
                        "total_power": power,
                        "core_area": core_area
                    },
                    "system_directive": "Optimize area/power by tweaking density/utilization/clock without causing violations." if is_closed else "Resolve violations using config variables.",
                    "clock_period": self._active_clock_period(current_snapshot),
                }
                # Achieved utilization is the binding physical constraint that
                # agents consistently miss: on a nearly-full die, any knob that
                # consumes area pushes placement past 100% and hard-crashes the
                # place/route stages (FLW-0024 / DPL-0011 / DPL-0033). The
                # numbers alone have not been enough -- say it explicitly, at
                # the moment it matters.
                util_pct = summary["physical_metrics"]["core_utilization_percent"]
                if util_pct >= 85:
                    summary["area_headroom_warning"] = (
                        f"Achieved utilization is {util_pct}% -- the die is nearly full, "
                        "regardless of what CORE_UTILIZATION is set to. Area-consuming "
                        "knobs (CELL_PAD_IN_SITES_GLOBAL_PLACEMENT, "
                        "CELL_PAD_IN_SITES_DETAIL_PLACEMENT, and raising SETUP_SLACK_MARGIN, "
                        "which inserts repair buffers) will very likely crash placement or "
                        "routing here. Create room first by lowering CORE_UTILIZATION or "
                        "PLACE_DENSITY before reaching for them."
                    )

                if rule_failures:
                    # Informational only -- deliberately does NOT feed into
                    # `status`. These are the design's own ORFS QoR rules
                    # (rules-<variant>.json), a separate gate from this
                    # loop's closure criteria (setup/hold/DRC above). The
                    # run completed and every metric here is real; these
                    # thresholds are extra quality signal worth acting on,
                    # not a reason to call the run failed.
                    summary["qor_rule_failures"] = rule_failures
                    summary["qor_rule_note"] = (
                        "The flow completed and all metrics above are real. These "
                        "ORFS quality-of-result thresholds (from the design's own "
                        "rules file) came in over budget. They do not block closure "
                        "on their own, but are worth improving if you can do so "
                        "without hurting timing/DRC."
                    )
                summary.update(self._compare_and_record(
                    tunables_changed, summary["status"], config=current_snapshot,
                    violations=summary["violations"], physical_metrics=summary["physical_metrics"],
                ))

                res = json.dumps(summary, indent=2)
                self._trace("RETURN SUCCESS: run_full_flow_and_summarize", res)
                self._save_run_artifacts(summary)
                return res

        err_summary = {"error": "Failed to parse reports. metadata.json missing."}
        err_summary.update(self._compare_and_record(
            tunables_changed, "PARSE_ERROR", config=current_snapshot))
        err = json.dumps(err_summary)
        self._trace("RETURN ERROR: run_full_flow_and_summarize", err)
        self._save_run_artifacts(err_summary)
        return err

    def _save_run_artifacts(self, summary: dict) -> None:
        """Collects this call's outputs into self._run_dir: the final GDS (if
        the flow got far enough to produce one) and the parsed summary,
        overwriting the "latest" copies so the run's top-level artifacts
        always reflect its most recent run_full_flow_and_summarize call."""
        if self._run_dir is None:
            return
        try:
            gds_dir = self._run_dir / "gds"
            src_gds = self.results_root / "6_final.gds"
            if src_gds.exists():
                gds_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_gds, gds_dir / f"run_{self._flow_run_count}_final.gds")
                shutil.copy2(src_gds, self._run_dir / "final.gds")

            # GDS itself is a binary layout format a browser can't render.
            # ORFS already rasterizes the finished layout as part of its own
            # report generation (a full-stack composite screenshot from
            # OpenROAD's GUI, one layer per net/metal) -- reuse that instead
            # of writing a GDS renderer. Only exists once the flow reaches
            # "finish", same condition as the GDS itself.
            src_webp = self.reports_root / "final_all.webp"
            if src_webp.exists():
                gds_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_webp, gds_dir / f"run_{self._flow_run_count}_layout.webp")
                shutil.copy2(src_webp, self._run_dir / "final_layout.webp")

            summaries_dir = self._run_dir / "summaries"
            summaries_dir.mkdir(parents=True, exist_ok=True)
            (summaries_dir / f"run_{self._flow_run_count}.json").write_text(json.dumps(summary, indent=2))
            (self._run_dir / "latest_summary.json").write_text(json.dumps(summary, indent=2))
        except OSError as e:
            self._trace("WARNING: failed to save run artifacts", str(e))