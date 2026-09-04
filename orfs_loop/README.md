# chia-orfs

An LLM-driven RTL-to-GDS closure loop for [OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts)
(ORFS), built on the [chia](https://github.com/ucb-bar/chia) agent framework. An
LLM iteratively tunes a whitelisted set of `config.mk` knobs and re-runs the
flow until timing/DRC closure, subject to hard limits you set that it can
never override.

**First time on a machine that's never run this before?** You'll need Docker,
local SSH, a `chia_env` conda environment with the `chia` package installed,
the local Docker image built, and LLM provider auth configured -- everything
below assumes all of that already exists.

`orfs-native-build/` (the vendored ORFS toolchain) is a git submodule pinned
to the commit this was built and tested against. Initialize it, then apply
the included patch, which fixes sky130hd LVS signoff (KLayout's deck shipped
device-combination disabled and pointed at the wrong report call, and the
platform CDL had two netlist-format issues KLayout's netlist reader rejects)
so `make lvs` actually produces a usable result instead of erroring out or
reporting a false verdict:

```bash
git submodule update --init orfs_loop/orfs-native-build
cd orfs_loop
git apply orfs-native-build.patch --directory=orfs-native-build
```

`orfs_runs/bp-sky-gcd/` is a complete sample run (gcd on sky130hs, 6
iterations, closed, area-optimized) kept as a reference for what a finished
run's output looks like.

## How it fits together

```
orfs_loop.py  (driver, runs on the host, owns the whole loop)
  -> run_flow_remote / apply_tunables_remote     direct blocking Ray calls,
       (orfs_tool.py, on the "orfs_run" Ray        no MCP, no tool-calling
        worker -- exactly 1 unit cluster-wide)
       -> make -C flow clean_all synth/floorplan/place/cts/route/finish/metadata
  -> OpenCodeLLM.prompt(..., tools=[])   one LLM turn per run: the model reads
       the flow result as a prompt and replies with a JSON tunable diff (or
       CLOSURE: PASS / CLOSURE: GIVE_UP) as plain text -- no tools, it never
       runs anything itself
```

This used to be the more obvious "give the LLM MCP tools and let it call
`get_tunables`/`set_tunables`/`run_full_flow_and_summarize` itself" shape. It
broke: opencode's MCP client times out a call at ~60s, but a real flow run
takes 90s-15min, so the client would retry mid-run and a second concurrent
flow execution would `make clean_all` out from under the first one,
corrupting both. The fix was removing the LLM's ability to call anything --
the driver now owns every flow/tunable call directly, so two runs overlapping
is structurally impossible, and the model's only interface is replying with
text.

- **`orfs_loop.py`** -- the driver: connects to the Ray cluster, runs a
  two-level loop (**iterations** are the major unit -- iteration 1 ends the
  moment a run closes; each iteration after that must close again *and* beat
  the previous one's `--objective` value -- containing **runs**, the minor
  unit: one flow execution + one LLM turn, uncapped per iteration), and
  decides when to stop.
- **`orfs_tool.py`** -- home of the actual worker-side functions the driver
  calls: `read_tunables_remote`/`apply_tunables_remote` (read/validate/write
  the managed tunable block), `run_flow_remote` (the `make clean_all` +
  stage sequence), `run_signoff_remote` (standalone `make drc`/`make lvs`
  after a close). All `@ChiaFunction(resources={"orfs_run": 1})`. The file
  also still contains `ORFSTool`, an MCP-tool-server class from the old
  design -- unused by the current loop, kept around but dead code.
- **`orfs_config_bridge.py`** -- validates tunables against the schema and
  renders them into a managed block appended to a *copy* of your baseline
  `config.mk` (`config.chia.mk`). The baseline file is never edited in place.
- **`orfs_tunables_schema.json`** (and `orfs_tunables_schema_minimal.json`,
  a reduced 12-tunable variant, `--minimal-schema`) -- the closed whitelist:
  every key the LLM is allowed to touch, with type/range/enum bounds.
  Anything not listed here is invisible and unreachable to the LLM, full stop.
- **`prompts/orfs_propose.md`** -- the LLM's entire interface: reads the
  current goal/schema/config/flow-result/history and replies with a fenced
  JSON tunable diff or a `CLOSURE:` sentinel. Its strategy section moves
  "free" knobs (repair flags/margins) aggressively but caps "target" knobs
  (`CORE_UTILIZATION`, `PLACE_DENSITY`, `DIE_AREA_SCALE`, `CLOCK_PERIOD`) to
  ~10-15% relative steps per turn, always -- otherwise a model chasing
  closure will happily double the die area or give back most of the clock
  speed to get there.
- **`orfs_onboard.py`** -- one-time bridge to generate a `config.mk` for a
  fresh Tiny-Tapeout-style RTL repo that doesn't have one yet.
- **`orfs_gui.py`** / **`gui/index.html`** -- the dashboard. Runs
  `orfs_loop.py` as a subprocess per run and polls its `tool_trace.log`/
  `summary.json` for live progress.
- **`cluster.yaml`** -- the `chia` cluster topology: one Docker-backed Ray
  worker per resource type (`orfs_run`, `opencode_creds`, plus the chipyard/
  verilator example workers). `chia up`/`chia down` (from the `chia` package)
  read this, not raw `ray up`. Bind-mount paths are parameterized via
  `${CHIA_ORFS_REPO}`/`${HOME}`, not hardcoded to one person's machine.

## One-time setup

```bash
conda activate chia_env
cd ~/Desktop/chia-orfs
export CHIA_ORFS_REPO=$(pwd)     # cluster.yaml's bind-mount paths key off this
export THIS_MACHINE=$(hostname -I | awk '{print $1}')
chia up cluster.yaml -y
```

This brings up (or reconciles) the Ray head + one Docker worker per node type
in `cluster.yaml`, including `chia-orfs-auralab-0` -- the container with the
ORFS toolchain, bind-mounted at `/root/OpenROAD-flow-scripts` (from
`orfs-native-build/`) and `/root/chia-orfs` (the whole repo, live).

Check it's up: `chia status` or `ray status` should show `orfs_run: 1.0` total
capacity.

**Editing `orfs_tool.py` / `orfs_config_bridge.py`?** No extra step needed --
the whole repo is bind-mounted into the container with `PYTHONPATH` pointing
at it, so changes are live immediately. (This used to require a manual
`docker cp`; that's gone now -- see cluster.yaml's `hello_orfs.docker.run_options`
if you're curious how.)

## The dashboard (easiest way to drive this)

```bash
python3 orfs_gui.py   # then open http://127.0.0.1:8080
```

`orfs_gui.py` is a FastAPI app that launches `orfs_loop.py` as a subprocess per
run and polls its `tool_trace.log`/`summary.json` for live progress. If your
shell session predates being added to the `docker` group, prefix the command
with `sg docker -c "..."` or open a fresh terminal first -- otherwise every
`docker exec` the GUI does will silently fail with a permission error.

Everything the CLI does, without terminal juggling: pick a design and model
from dropdowns, set iterations, lock tunables, hit **Start**, and watch it
go. The page polls every 2.5s and shows:

- which flow stage is executing right now (`synth → floorplan → place → …`)
- a table of every flow run: what changed, the verdict
  (`IMPROVED`/`REGRESSED`/`CRASHED`), setup WNS/TNS, hold, DRC, utilization, area
- a WNS-vs-run chart with the zero line marked, so you can see closure approach
- crash banners showing the **real** OpenROAD error (e.g. `[ERROR FLW-0024]`),
  and the area-headroom warning when the die is too full to pad
- the agent's reasoning as one continuous transcript across the whole run,
  artifacts produced, and the tool trace log (`tool_trace.log`)

The run picker in the top right also opens any past run in `orfs_runs/`, so
you can review finished work with the same view.

Runs launch as ordinary `orfs_loop.py` subprocesses in their own session --
identical `run_dir` layout to a CLI run, and they keep going if you close
the browser. **Stop** terminates the active one.

Only one run at a time: the cluster has a single `orfs_run` slot, so a
second would just deadlock waiting for it.

## Running the closure loop (CLI)

Point it at a design that already has a `config.mk` under
`orfs-native-build/flow/designs/<platform>/<design>/` -- either one of ORFS's
built-in examples (`gcd`, `riscv32i`, `aes`, `jpeg`, `ibex`, `chameleon`,
`microwatt`, `tt_um_fft_adityaamehra`, ...) or one you onboarded (below).

```bash
conda activate chia_env
cd ~/Desktop/chia-orfs

DESIGN=/root/OpenROAD-flow-scripts/flow/designs/sky130hd/riscv32i

python3 orfs_loop.py \
  --design-name riscv32i \
  --design-config-mk $DESIGN/config.mk \
  --reports-root /root/OpenROAD-flow-scripts/flow/reports/sky130hd/riscv32i/base \
  --max-iterations 6 \
  --objective area \
  --model opencode/big-pickle
```

**Both paths must be container-native absolute paths** (`/root/OpenROAD-flow-scripts/...`),
not host paths -- the config-prep step and every remote call run inside the
`orfs_run` worker, which doesn't see your host filesystem except through the
two bind mounts above.

`--reports-root` is ORFS's own `reports/<platform>/<design>/<variant>`
directory (usually `.../base`), **not** a `results/` folder under the design's
own directory -- those are two different, sibling directories ORFS writes to.
Get this wrong and the flow runs fine but `run_flow_remote` reports
`"metadata.json missing"` at the end.

`--max-iterations` counts **iterations**, not runs: iteration 1 ends the
moment a run closes; each iteration after that must close again *and* beat
the previous one's `--objective` value. Runs within an iteration are
uncapped -- the model itself ends a non-closing iteration by replying
`CLOSURE: GIVE_UP`, or an un-improving `CLOSURE: PASS`.

### CLI reference

| Flag | Default | Notes |
|---|---|---|
| `--design-name` | `tt_um_fft_adityaamehra` | Used to label the tool + prompt. |
| `--flow-dir` | `/root/OpenROAD-flow-scripts/flow` | Rarely needs changing. |
| `--design-config-mk` | *required* | Container-native path to baseline `config.mk`. |
| `--reports-root` | *required* | Container-native path to `flow/reports/<platform>/<design>/base`. |
| `--run-dir` | `orfs_runs/<unix-ts>` | Where this run's artifacts land (see below). |
| `--max-iterations` | `3` | **Iterations**, not runs -- see above. |
| `--objective` | `area` | `area` or `clock`. What each iteration past the first must improve on. Ignored by iteration 1. |
| `--model` | `google/gemini-3.6-flash` | Any `opencode` model string. See "Choosing a model" below. |
| `--closure-criteria` | *(none)* | Overrides the closure target text given to the LLM. |
| `--minimal-schema` | off | Use the reduced 12-tunable schema instead of the full 22-tunable one. |
| `--prompt-path` | `prompts/orfs_propose.md` | The proposal prompt template. |
| `--resume-config` | off | Continue from the previous run's tunables instead of resetting to baseline. |
| `--skip-signoff` | off | Skip standalone `make drc`/`make lvs` after a successful close. |
| `--lock KEY=VALUE` | *(none)* | Repeatable. Hard-locks a tunable -- see next section. |
| `--ld-library-path` | `/opt/miniconda/lib` | Needed by some ORFS-bundled binaries; leave as-is. |
| `--ray-address` | `auto` | Ray cluster address. |

## Locking tunables the LLM can never change

Some knobs you don't want touched -- a utilization ceiling dictated by a
padframe, a routing layer budget, whatever. Pass `--lock` (repeatable):

```bash
python3 orfs_loop.py ... \
  --lock CORE_UTILIZATION=38 \
  --lock MAX_ROUTING_LAYER=met5 \
  --lock CLOCK_PERIOD=1.1
```

## Every run starts from a clean config

Each run resets the design's `config.chia.mk` back to its pristine
`config.mk` baseline before starting. Without that, a new run silently
inherits whatever tunables the *previous* run happened to leave behind, so
its "baseline" measurement is really some half-explored config -- results
aren't reproducible and comparing two runs means nothing.

Pass `--resume-config` (or tick *Resume previous config* in the dashboard)
to deliberately continue where a previous run stopped.

> **Note on the clock target.** `CLOCK_PERIOD` *is* a tunable, but it isn't
> a config.mk key -- ORFS has no such variable. Every design's
> `constraint.sdc` hardcodes its own `clk_period` (as `set clk_period <N>`
> or a literal `-period <N>` inside `create_clock`, depending on the
> design), so this repo patches a working copy of that file directly and
> points `SDC_FILE` at it, instead of writing an env var nothing reads.
> Units follow whatever that design's own SDC already uses (ns for most
> PDKs here, ps for asap7/gf180) -- the prompt always shows the current
> value first. Bounds are computed per-design at startup (roughly 0.3x-3x
> the design's original period), since a sane period for one PDK is
> nonsense for another. `--lock CLOCK_PERIOD=<value>` still works normally.

This is enforced **in code**, not just by asking nicely in the prompt:
- The locked value is baked into the working config immediately at startup,
  even if it disagrees with the baseline.
- Every proposed tunable diff goes through `apply_tunables_remote`, which
  forces locked keys back to their fixed value regardless of what was
  requested and reports back which keys it rejected into the trace log, so
  a curious reader can see it -- but the enforcement doesn't depend on the
  model reading that; the config file is always correct.
- Only keys already in `orfs_tunables_schema.json` can be locked (same
  whitelist the LLM itself is bound by).

### Reverting a tunable to baseline

The model's JSON reply can use `null` as a key's value, to remove its
override entirely, e.g. `{"CORE_UTILIZATION": null}` -- the key drops out of
the managed block and that setting falls back to whatever the design's own
baseline `config.mk` (or, for `CLOCK_PERIOD`, its `constraint.sdc`)
originally had. This is different from picking some new in-range value:
it's "go back to untouched," for when a change didn't help and the honest
move is to undo it rather than guess again. A locked key can't be unset
this way either -- same enforcement path as any other rejected change.

## Onboarding a new design

If your RTL doesn't have an ORFS `config.mk` yet (e.g. a fresh Tiny Tapeout
repo), generate one first:

```bash
git clone https://github.com/<you>/<your-tt-repo>.git ~/Desktop/<your-tt-repo>

python3 orfs_onboard.py \
  --design-repo ~/Desktop/<your-tt-repo> \
  --output-root ~/Desktop/chia-orfs/generated-flow-configs \
  --container-flow-dir /root/OpenROAD-flow-scripts/flow \
  --platform sky130hd \
  --docker-container chia-orfs-auralab-0
```

This copies the RTL + a generated `config.mk`/`constraint.sdc` into
`generated-flow-configs/designs/sky130hd/<design>/` on the host **and** into
`orfs-native-build/flow/designs/sky130hd/<design>/` inside the container
(because `--docker-container` was given) -- that second location, under
`orfs-native-build/flow/designs/...`, is the one you point `orfs_loop.py` at.
The host copy under `generated-flow-configs/` is just a staging area; ORFS
never reads it directly.

Run the dry-run `make synth` the script prints at the end before trusting the
closure loop on top of it -- ORFS variable names drift across releases, and
this catches a bad config before burning an LLM turn on it.

## What you get back

Every run writes to `--run-dir` (default `orfs_runs/<unix-ts>`):

```
orfs_runs/<run-id>/
  summary.json            final status: closed / no_closure / max_iterations_reached,
                           plus per-iteration records and the achieved objective value
  tool_trace.log          the single place to see exactly what happened, in order:
                           CALL:/RETURN: pairs for each flow run, the model's raw
                           "SYSTEM: Iteration N LLM Reasoning" replies, CALL:/RETURN:
                           for each tunable diff applied, "SYSTEM: Starting Iteration
                           N" markers, and the final signoff result
  final.gds                the best run's GDS
  final_layout.webp        the best run's layout preview
  gds/run_N_final.gds      one per flow run (a run is one flow execution + one LLM turn)
  gds/run_N_layout.webp
  summaries/run_N.json     the parsed closure summary for that run
  latest_summary.json      = summaries/<highest N>.json
  signoff_logs/            drc.log / lvs.log -- only present if signoff ran
                           (skipped by --skip-signoff, or never reached)
  flow_logs/run_N/
    synth.log, floorplan.log, place.log, cts.log, route.log,
    finish.log, metadata.log      full stdout+stderr per stage (not the
                                   truncated tail the LLM sees)
  driver.log               only present for GUI-launched runs -- the GUI's own
                           subprocess stdout/stderr capture
```

Files the container writes (everything except `summary.json` and the first
line of `tool_trace.log`) are root-owned -- readable by you, but not
writable/deletable directly. To remove a run folder:

```bash
docker exec chia-orfs-auralab-0 rm -rf /root/chia-orfs/orfs_runs/<run-id>
```

## Choosing a model

The LLM has no tools -- it just replies to a prompt with a fenced JSON
tunable diff or a `CLOSURE:` sentinel, and the driver parses that reply.
Reliability now hinges on whether a model actually *follows that reply
format*, not on tool-calling. Closure success is still **not independently
verified** -- it trusts the model's own `CLOSURE: PASS` reply. Cross-check
`tool_trace.log`: a real run has `CALL: run_full_flow_and_summarize` entries
with real metrics; a model that's just narrating prose instead of a valid
JSON/sentinel reply leaves the loop unable to parse a proposal at all, even
if its prose claims closure.

- `google/gemini-3.5-flash` doesn't exist in opencode's catalog and a run
  against it hangs indefinitely rather than failing fast -- confirmed by
  hand. `google/gemini-3.6-flash` (the current default) is the real model
  one version up; if a run against some model string never produces its
  first trace entry, suspect this before assuming a cluster problem.
- `opencode/big-pickle` reliably produces valid replies in testing, at the
  cost of being slow (each turn can take several minutes, since a real flow
  run executes the whole ORFS pipeline).

## Why every flow run does a full clean rebuild

`make <stage>` decides whether to rebuild by comparing file timestamps
between a target and its tracked prerequisites (Verilog sources, previous
stage's outputs) -- it has no way to know `DESIGN_CONFIG`'s *contents*
changed, since that's an env var, not a file ORFS's Makefile tracks as a
dependency. Without an explicit clean, every call after the first would
silently no-op (`make: Nothing to be done for 'synth'.`) and just re-report
the first run's stale metrics regardless of what tunables changed -- this
was a real bug here for a while, and is why `run_flow_remote` now runs
`make clean_all` before the stage sequence on every single call.

This means each call costs a genuine full rebuild (`gcd`: ~1-2 min;
`riscv32i`: 15+ min, mostly detailed routing) rather than the ~1s a no-op
would take. That's the actual cost of a working closure loop -- if a call
ever finishes in a couple seconds, something is wrong; check `flow_logs/run_N/*.log`
for `Nothing to be done` to confirm before trusting the result.

## Troubleshooting

**A run hangs forever / `ray status` shows `orfs_run` fully used with
nothing running.** A previous run was killed uncleanly (e.g. `timeout`,
`kill -9`, or a crash before `orfs_tool.stop()` ran in its `finally` block)
and left an orphaned actor holding the cluster's only `orfs_run` slot --
capacity is 1, so nothing new can ever schedule until it's freed:

```bash
ray status   # confirms orfs_run: 1.0/1.0 used, "Pending Demands" for orfs_run
python3 -c "
import ray
ray.init(address='auto')
import ray.util.state as st
for a in st.list_actors(filters=[('state','=','ALIVE')]):
    print(a['actor_id'], a['class_name'], a['pid'])
"
# find the orphaned _ToolServerActor's pid, then:
docker exec chia-orfs-auralab-0 kill -9 <pid>
```

**`FileNotFoundError` on `config.mk` or the schema at startup.** You passed a
host path instead of a container-native one, or `setup()`'s own file reads
(schema, baseline config) landed on the wrong filesystem. Re-check every path
argument is `/root/OpenROAD-flow-scripts/...` or `/root/chia-orfs/...`, never
a bare host path like `~/Desktop/chia-orfs/...`.

**CTS stage fails with `kepler-formal: ... libpython3.14.so.1.0: cannot open
shared object file`.** Missing `LD_LIBRARY_PATH=/opt/miniconda/lib` in the
worker's environment -- `orfs_loop.py --ld-library-path` already defaults to
this; if you're calling the remote functions directly, pass
`extra_env={"LD_LIBRARY_PATH": "/opt/miniconda/lib"}`. The same fix causes a
cosmetic `bash: /opt/miniconda/lib/libtinfo.so.6: no version information
available` warning on every shell `make` spawns (it shadows the system
`libtinfo` with conda's build) -- harmless, not a sign of anything slow or
broken.

**Edits to `orfs_tool.py` don't seem to take effect.** Confirm the container
actually has the new mount: `docker exec chia-orfs-auralab-0 python3 -c
"import orfs_tool; print(orfs_tool.__file__)"` should print
`/root/chia-orfs/orfs_tool.py`. If it prints somewhere under `site-packages`
instead, the container predates the `cluster.yaml` mount fix -- recreate it:
`docker stop chia-orfs-auralab-0 && docker rm chia-orfs-auralab-0 && chia up cluster.yaml -y`
(only recreates this one container; the other worker containers are untouched).

**The GUI's model dropdown is empty, or any `docker` command fails with
"permission denied".** Your shell session predates being added to the
`docker` group -- group membership changes don't retroactively apply to an
already-running session. Prefix the command with `sg docker -c "..."` or
open a fresh terminal.

**`make lvs` fails outright on sky130hd designs** (a parse error, not a
mismatch verdict). The vendored `orfs-native-build/flow/platforms/sky130hd/
cdl/sky130hd.cdl` has two upstream quirks KLayout's LVS netlist reader
doesn't accept: literal `short` values on 6 tie-cell resistor lines (needs to
be a numeric `0`), and a slash-delimited `net1 net2 ... / subcktname` format
on 7 `X`-instance lines inside `macro_sparecell` (the reader doesn't support
`/` as a delimiter -- it counts it as a spurious extra net). Both can be
hand-patched on this file; the patch lives only in this host's copy of
`orfs-native-build/` (not in `chia-orfs-run`'s Docker image, which is built
straight from public `openroad/orfs:latest` with nothing local baked in), so
it needs reapplying after a fresh clone/reset of that directory. Even
patched, LVS on sky130hd currently reports a genuine `Netlists don't match`
for the `conb_1`/`tapvpwrvgnd_1` tie cells specifically, because the deck's
device extraction only covers MOSFETs, not the resistor-modeled ties those
two cells use -- not yet fixed.
