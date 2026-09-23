# Troubleshooting

Failure modes observed while running the loops unattended, with the signature
that identifies each one and the fix. Ordered by how much time they cost.

| # | Symptom | Area | Root cause |
|---|---|---|---|
| 1 | Pipeline alive, zero progress for hours; host out of RAM | infra | verilator wrapper recursing |
| 2 | Log stalls mid-LLM-call, never recovers | infra | provider stalls; now auto-switches model |
| 3 | `PROCESS FAILURE` restart loop on YAML errors | UVM | unguarded `ensure_valid_yaml()` |
| 4 | RTL reaches ORFS without passing tests | UVM | `no_repair` treated as verified |
| 5 | Repeated regeneration of the same testbench | UVM | scenario-manifest mismatch |
| 6 | Run stops with `stop_reason: template_bug` | UVM | analysis LLM misclassified a fixable defect |
| 7 | LLM validates against stale orchestrator code | UVM | dead `run15.py` snapshot outranked `run14.py` |
| 8 | LVS "fails" but the design is fine | ORFS | benign netgen fold vs genuine mismatch |
| 9 | `PDN-0185 Insufficient width` | ORFS | tiny die, default utilization |
| 10 | Live run breaks after a git command | workflow | branch switch reset the working tree |
| 11 | Every iteration scores the same, nothing converges | UVM | uncompilable RTL accepted by a score-only gate |
| 12 | A single LLM call burns millions of tokens | UVM | agent fell into re-deriving the pyuvm API from library source (rare) |
| 13 | Model never switches despite repeated provider failures | UVM | retry loops swallowed the provider error |

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

## 2. LLM provider stalls mid-call

**Signature.** The log stops mid-iteration and artifacts stop appearing, but
the process stays alive. Confirm by checking whether the agent's output file
is still growing — frozen means deadlocked, not slow:

```bash
docker exec <opencode-worker> sh -c '
  F=$(ls -t /tmp/opencode_out_*.out | head -1)
  s1=$(stat -c %s $F); sleep 15; s2=$(stat -c %s $F)
  echo "$F: $s1 -> $s2"; tail -c 200 $F'
```

A frozen size whose last record is `"type":"step_finish"` with
`"reason":"tool-calls"` is the deadlock: the model asked for a tool call and
the round-trip never came back. CPU sitting at a few percent is a poll loop,
not progress.

**Cause.** The provider stops responding without erroring. Two shapes seen
live: a silent rate limit (empty result, no exception), and a tool-call
deadlock where the agent emits `step_finish` with `reason: tool-calls` and the
round-trip to the MCP tool server never returns — the opencode output file
freezes mid-stream while the process spins at a few percent CPU.

Because chia's `get()` blocks indefinitely, neither case raised anything, so
the model was never cooled down and the supervisor never got the non-zero exit
it needs to switch models.

**Fix, part 1 — the ceiling.** `llm_get()` in `run14.py` bounds every LLM call
with `LLM_CALL_TIMEOUT_S` (default 1800 s) and converts a timeout into a
`RuntimeError` matching `_MODEL_UNAVAILABLE_MARKERS`. That cools the model
down, exits non-zero, and the supervisor restart picks the next candidate from
`config/llm_models.txt` — automatically. Without it a hung opencode runs for
`LLM_TIMEOUT_SECONDS x LLM_RETRIES` = 2400 x 5 = **3.3 hours**, since chia
retries its own subprocess timeout.

**Fix, part 2 — failing fast.** The ceiling is correct but expensive: on
2026-09-23 `opencode/big-pickle` logged `Rate limit exceeded` **one second**
into a call and then hung, three separate times, each costing the full 30
minutes. The verdict was knowable immediately — it was in opencode's own log
the whole time.

So `llm_get()` now polls while it waits. Every `LLM_FAILFAST_POLL_S` (20 s),
after a `LLM_FAILFAST_GRACE_S` (60 s) grace period, `_opencode_log_failure()`
reads each opencode container's log for a `level=ERROR` `stream error` that is
both **newer than this call** and **names the model this call is using**. On a
hit it cancels the Ray task and raises `Provider returned error ...`, which is
already in the marker list — so the same cooldown-and-switch path runs, in
seconds instead of half an hour.

Both filters matter. Without the timestamp test every later call would trip
over an old error; without the model test a failure by one provider would
condemn another. The check is best-effort throughout — missing docker, a
missing container or an unreadable log all return `None` and leave the call on
its normal ceiling, because this must never turn a working call into a
failure. Set `LLM_FAILFAST_POLL_S=0` to disable it.

**Manual override**, if you need to force a switch sooner. Each process caches
its model at startup, so edit the state *and* restart:

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

## 11. RTL that does not compile gets accepted

**Signature.** Every RTL-verification iteration reports the same quality score
with `tests_passed: 0`, and `candidate_verification_result.yaml` shows every
test with `status: runtime_error` and `returncode: 2`. The run makes repairs
and accepts them, but nothing ever improves.

```bash
# confirm: does the accepted snapshot actually build?
docker exec <sim-worker> verilator --lint-only -Wno-lint \
  /workspace/generated/designs/<design>/rtl_verification/accepted/<top>.sv
```

**Cause.** A build failure makes every test exit with `returncode 2` *before
running*, so the candidate's quality score comes out identical to the
baseline's. The acceptance check was `candidate_score >= baseline_score`, which
reads that tie as "no regression" and promotes it. Since each iteration starts
from the accepted snapshot, one uncompilable promotion poisons every later
iteration.

Seen live: an S-box repair emitted C-style `0x77` literals into SystemVerilog
(`8'h63,8'h7c,0x77,...`). It was promoted, and the next three iterations all
scored an identical 55.00 with 0/16 passing.

**Fix.** `_candidate_rtl_built()` in `run14.py` rejects a candidate when
nothing ran, regardless of score. Anything less unambiguous still falls
through to the normal score comparison.

**`returncode 2` is NOT the discriminator**, although the first version of this
gate assumed it was. cocotb's make target exits 2 both when the build fails
*and* when the design builds fine but a test FAILS. Confirmed live on
`aes128_benchmark_corrupted`:

```
TESTS=1 PASS=0 FAIL=1
- :0: Verilog $finish
make: *** [...TestResetIdle.xml] Error 1        # -> returncode 2
```

Every test there reported `status: runtime_error`, `returncode: 2` — the exact
signature above — while having compiled and run perfectly. Since that design is
deliberately fault-injected, failing tests are its expected starting point, and
a returncode-only gate rejects every RTL repair as "failed to build" and stalls
the loop permanently.

Use `results_file_exists` instead: a test that ran writes its results XML, a
test whose build failed never gets that far. If **any** test produced results,
the design compiled, whatever it then did.

## 12. One LLM call costs millions of tokens

**Signature.** A single call runs to 80+ agent steps and several million
tokens. Most of the steps are shell commands reading installed library source:

```bash
# count what the agent's tool calls actually touched
grep -o '"command":"[^"]*"' <opencode output file> | grep -c site-packages
```

Measured on one call: 82 bash tool calls, of which **58 (71%)** were `grep` /
`sed` / `python3 -c "import inspect"` against pyuvm and cocotb in
`site-packages`, 18 (22%) read our own files under `/workspace`, and 6 were
housekeeping.

**How often this happens — read this before concluding anything.** A survey of
all 39 agent streams retained on the workers puts that call in perspective:

| Streams | site-packages hits |
|---|---|
| 1 (`opencode_out_julhoaye`, 2026-09-22) | 51 |
| the other 38, spanning a week | 0-6, mostly 0-2 |

So this is a **rare failure mode, not a steady drain**. An early version of this
entry generalised the one measurement to "every call, every iteration, every
design"; the data does not support that, and the claim is withdrawn. Most calls
never introspect the library at all.

The practical consequence: a run showing 0 site-packages hits is *not* evidence
the fix below worked, because runs scored 0 before it existed too. Confirming
the fix needs several long generation calls under the same model with and
without the reference, which no single run provides.

**Cause.** pyuvm 5.0.0's API differs from both older pyuvm and SystemVerilog
UVM in ways the model does not reliably know — no `uvm_info` function, only
`run_phase` is `async`, `ConfigDB()` is a singleton with four-argument
`set`/`get`. Rather than guess, the agent reverse-engineers the library. Those
are static facts about a pinned version, but the agent has no memory across
calls, so it rediscovers them on every call, every iteration, every design. The
cost is worse than linear: the agentic loop re-sends the accumulated context on
each step, so step count drives token spend quadratically.

This is also the root of [#6](#6-template_bug-misclassification) — the analysis
LLM saw deprecated pyuvm APIs and, unsure whether they were fixable, called it
a template defect.

**Fix.** `scripts/gen_pyuvm_api_reference.py` extracts the real signatures from
the pyuvm installed in the worker into `config/pyuvm_api_reference.md` (~12KB,
~3.1k tokens). `pipeline/pyuvm_reference.py` loads it, and it is inlined —
with an explicit instruction not to read library source to re-confirm it —
into every prompt that writes pyuvm code: the six testbench-generation stages
via `_hard_constraints()` in `run14.py`, and the repair prompt in
`tb_feedback.py`. Prompts that write no pyuvm, such as plan generation, do not
carry it; measured output files for those stages show 0% library introspection,
so there it would be pure added cost.

**Cost arithmetic.** The block is re-sent on every step of the agentic loop, so
it costs `3.1k x steps` — about 250k tokens if it changes nothing at all, on a
call that measured 6.08M. Since the failure it targets is rare, treat that as
the *expected* cost and the saving as insurance against a recurrence, not as a
routine gain. It is kept because it is cheap, because every fact in it is
verified against the live library, and because the one episode it targets was
expensive — not because it has been shown to reduce ordinary calls.

**Regenerate it after any pyuvm upgrade:**

```bash
docker exec chia-sim-$USER-0 python3 /workspace/scripts/gen_pyuvm_api_reference.py \
  > uvm_loop/config/pyuvm_api_reference.md
```

A reference describing a version the workers no longer have is the same
stale-guidance trap as [#7](#7-dead-snapshots-mislead-the-in-loop-llm), so the
generator hard-fails if the installed library contradicts its hand-written
preamble rather than emitting a reference that lies.

**Not fixed.** The remaining 22% — the agent re-reading files under
`/workspace` whose paths the orchestrator already knows — would need those
contents front-loaded into the prompts. Unmeasured, and a larger change.

## 13. A retry loop swallows the provider failure

**Signature.** The log repeats a stage attempt with a provider-shaped reason,
the model never changes, and `generated/llm_model_state.json` shows no new
cooldown:

```
⚠ Candidate plan structurally invalid on attempt 1/3 (syntax-repair exhausted):
  LLM call timed out after 1800s during LLM call; cooling down this model...
  Discarding it and generating a fresh candidate from scratch.

[2/4] Generating verification plan (attempt 2/3)...
```

Note the contradiction inside that message: the exception *says* it is cooling
the model down, and the very next line retries the same one.

**Cause.** The fixes for [#2](#2-llm-provider-stalls-mid-call) and
[#3](#3-ensure_valid_yaml-crash-loop) interact badly. #3 wrapped three
`ensure_valid_yaml()` call sites in `except RuntimeError` so one unusable
generation costs a retry instead of the process. #2 later made a dead provider
*also* surface as a `RuntimeError`. Those handlers cannot tell the two apart,
so provider death was absorbed as if it were bad model output: the exception
never reached `_record_llm_rate_limit()`, the model was never cooled down, and
the process never exited non-zero, which is the only thing that makes the
supervisor switch models.

Seen live 2026-09-23: `opencode/big-pickle` rate-limited **8 seconds** into a
call, opencode hung instead of erroring, and the 1800s timeout fired into this
handler — which retried the same rate-limited model. Three attempts would have
cost 90 minutes while nine usable models sat idle in the fallback list.

**Fix.** `_is_model_unavailable(exc)` in `run14.py` matches the exception
against `_MODEL_UNAVAILABLE_MARKERS`, and all three handlers re-raise when it
is true. Bad-output retries are unaffected — that is still exactly what those
loops absorb.

**Rule for new retry loops.** A handler that catches `RuntimeError` around an
LLM call must let provider failures through. Retrying a dead provider fails
identically every time, and catching it locally silently disables the whole
fallback mechanism.
