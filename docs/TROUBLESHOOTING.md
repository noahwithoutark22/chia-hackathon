# Troubleshooting

Failure modes observed while running the loops unattended, with the signature
that identifies each one and the fix. Ordered by how much time they cost.

| # | Symptom | Area | Root cause |
|---|---|---|---|
| 1 | Pipeline alive, zero progress for hours; host out of RAM | infra | verilator wrapper recursing |
| 2 | Log stalls mid-LLM-call, never recovers | infra | provider rate limit, no fallback in UVM stage |
| 3 | `PROCESS FAILURE` restart loop on YAML errors | UVM | unguarded `ensure_valid_yaml()` |
| 4 | RTL reaches ORFS without passing tests | UVM | `no_repair` treated as verified |
| 5 | Repeated regeneration of the same testbench | UVM | scenario-manifest mismatch |
| 6 | Run stops with `stop_reason: template_bug` | UVM | analysis LLM misclassified a fixable defect |
| 7 | LLM validates against stale orchestrator code | UVM | dead `run15.py` snapshot outranked `run14.py` |
| 8 | LVS "fails" but the design is fine | ORFS | benign netgen fold vs genuine mismatch |
| 9 | `PDN-0185 Insufficient width` | ORFS | tiny die, default utilization |
| 10 | Live run breaks after a git command | workflow | branch switch reset the working tree |

---

## 1. Verilator wrapper recursion (host OOM)

**Signature.** The pipeline process is alive but writes nothing for hours.
State files stop updating. `free -h` shows almost no free RAM *and* no free
swap. Thousands of live `verilator` processes in a parent→child chain:

```bash
ps -eo stat,comm | awk '$2=="verilator" && $1 !~ /Z/' | wc -l    # expect 0, not thousands
```

**Cause.** `pip install verilator` (the PyPI wrapper package) inside a worker
container replaces `bin/verilator` with a symlink to its own Python console
script. That wrapper locates the real compiler with `which("verilator")`,
intending to fall back to its bundled binary only when no system verilator
exists — but the install put *itself* on `PATH` under that exact name, so
`which()` returns the wrapper, which `Popen`s the wrapper, forever. Its
`while process.poll() is None: sleep(0.1)` busy-wait keeps every ancestor
resident holding a Python interpreter, so memory grows linearly with depth
until the host dies.

**Fix.** Point the `PATH` entry at the real binary:

```bash
docker exec <worker> ln -sf \
  /home/ray/anaconda3/lib/python3.10/site-packages/verilator/bin/verilator \
  /home/ray/anaconda3/bin/verilator
docker exec <worker> sh -c 'readlink -f $(which verilator)'   # must NOT be verilator-cli
```

**Notes.** `docker restart` does *not* fix this — the symlink lives in the
container's writable layer and survives restart. Kill the chain with
`pkill -STOP -x verilator && pkill -KILL -x verilator` (freeze first, or it
outruns the kill). Because containers are created from the same image but
modified at runtime, one worker can be broken while its siblings are fine,
and which one a run lands on is a scheduling lottery — so verify every worker,
not just the one that failed.

## 2. LLM provider rate limit hangs the UVM stage

**Signature.** The log stops mid-iteration, often after `Timeout on attempt
N/5`. The process stays alive at ~0% CPU with its LLM-call subprocesses
already exited.

**Cause.** A provider silently rate-limits under load (empty result, no
error). `orfs_loop.py` handles this correctly — it logs the condition and
switches models. The UVM stage does **not**: `_load_llm_model()` /
`_prompt_with_backoff` in `run14.py` retry the same model indefinitely.
This is a known gap, not yet fixed in code.

**Workaround.** Cool the model down and restart the process. Each process
caches its model selection once at startup, so editing state alone does
nothing until restart:

```jsonc
// uvm_loop/generated/llm_model_state.json  (shared across designs, not per-design)
{ "cooldown_until": { "<model>": <epoch + 3600> }, "current": "<other model>" }
```

Preference order lives in `uvm_loop/config/llm_models.txt`.

## 3. `ensure_valid_yaml()` crash loop

**Signature.** Several consecutive `Missing required top-level field` errors,
then an uncaught `RuntimeError`, `PROCESS FAILURE`, and a supervisor restart
that repeats the same sequence.

**Cause.** `ensure_valid_yaml()` raises when a low-tier model can't produce
schema-valid YAML within `max_attempts`. Three call sites invoked it with no
`try/except`, so one bad generation killed the whole process instead of
costing one retry: candidate-plan generation/resume, the RTL-repair
`no_functional_evidence` path, and the plan-review loop's schema-repair and
semantic-repair branches.

**Fix.** All three now catch the exception, keep the error text as context for
the next attempt, and `continue` — folding the failure into the loop's
existing `MAX_REPAIR_ATTEMPTS` budget rather than crashing.

## 4. `no_repair` used as a loophole to reach ORFS

**Signature.** A design reaches the ORFS stage with `rtl_outcome: no_repair`
while tests were never all passing.

**Cause.** `no_repair` is an escape hatch that caps repair iterations. The
diagnosis LLM can reach that verdict without a single genuinely passing
simulation, and the handoff previously accepted it as equivalent to verified.

**Fix.** `rtl_to_gds.py` now requires `status == "verified"` *and*
`verified is True`. Anything else needs an explicit `--allow-unverified`.
Confirmed working: a run that reached `no_repair` after 11 accepted repairs
was correctly refused handoff.

## 5. Scenario-manifest mismatch

**Signature.** Either `undeclared scenario IDs` (a scenario exists that the
plan doesn't declare) or `declares SCENARIO_ID=None` (a sequence class left
the attribute unset), followed by testbench regeneration.

**Cause.** LLM output defects in the generated testbench, not a code bug.

**Behaviour.** `validate_scenario_manifest()` is checked twice: proactively at
the top of Stage 4, where an invalid manifest clears the `uvm_integration`
checkpoint and forces regeneration, and again as a hard gate after
integration that raises with no local catch. The pre-check plus supervisor
restart is what makes this self-heal. Several consecutive failures are normal
and usually converging — check whether each restart fixes *different* defects
before intervening. Observed resolving on its own after three cycles.

## 6. `template_bug` misclassification

**Signature.** `"status": "blocked", "stop_reason": "template_bug"` and a hard
stop.

**Cause.** The RTL-repair analysis LLM labels a genuinely fixable testbench
defect as a shared toolchain/template defect with an empty `changes` list.
Seen with deprecated pyuvm APIs (`uvm_info` / `uvm_warning` / `uvm_error`
instead of `self.logger.info` etc., which pyuvm 5.0.0 requires).

**Behaviour.** The hard stop is deliberate — it escalates to a human rather
than letting the loop thrash. But combined with a supervisor that restarts on
any failure, it can recur until the underlying condition changes. Observed
self-resolving on a later restart.

## 7. Dead snapshots mislead the in-loop LLM

**Signature.** Generated validator scripts under
`generated/designs/*/tb/.tmp_validate/run_validator.py` reading
`/workspace/pipeline/run15.py`.

**Cause.** `run14.py` is the orchestrator, but the repo also carried
`run14bak.py`, `run14copyprev.py` and `run15.py`. When the in-loop LLM
improvised a validator it listed `pipeline/` and picked the
highest-numbered file — validating against code that was never running.

**Fix.** Those snapshots are deleted. Keep exactly one orchestrator in
`pipeline/`; if you need a checkpoint, use a branch or tag, not a
`*bak.py` beside the live file.

## 8. Reading the LVS verdict

On sky130hd the authoritative verdict is `result["lvs_verdict"]` (netgen),
**not** KLayout's `result["lvs"]["clean"]`. Three distinct outcomes:

| Pattern | Meaning |
|---|---|
| `devices_match: true`, one net difference, no `subcircuit_mismatches` | **Benign** known fold artifact |
| `devices_match: false` with per-cell device-count mismatches (e.g. `sky130_fd_sc_hd__ha_4`: 18 vs 14) | **Genuine failure** — investigate |
| `"supported": false, "note": "could not determine top cell..."` | **Inconclusive** — verdict unavailable, not a pass |

Benign folds are gated by exact signature in `KNOWN_NETGEN_FOLD_EXCEPTIONS`
in `orfs_tool.py`.

## 9. `PDN-0185 Insufficient width` on tiny designs

Designs of a few tens of cells fail PDN at the default 40% core utilization,
because the die ends up narrower than the met4 strap pitch. Start them at
`--core-utilization 10`.

## 10. A git branch switch can break a live run

**Signature.** A running loop starts failing on a bug you already fixed.

**Cause.** Switching branches — including `git checkout -b <new> origin/main` —
resets every tracked file in the working tree to that branch's content,
including files a running process reads from disk on each restart.

**Rule.** Don't switch branches while a campaign is running. If you must,
verify afterwards that the fixes are still present before letting the
supervisor restart anything:

```bash
grep -c "<known fix marker>" uvm_loop/pipeline/run14.py
```

Related: `main` is protected and rejects force-pushes outright, so history
rewrites need a repo-admin change first.

---

## General checks

```bash
# Is a run actually progressing, or just alive?
find uvm_loop/generated/designs/<design> -newermt '20 minutes ago' -type f | head

# Cluster resource usage (0.0 across the board means nothing is running)
ray status

# Per-container memory — catches a single leaking worker
for c in $(docker ps --format '{{.Names}}'); do
  echo "$c $(cat /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' $c).scope/memory.current)"
done
```

An ORFS flow run that finishes in seconds means something is wrong — every run
does `make clean_all` first, so a real run is never that fast.
