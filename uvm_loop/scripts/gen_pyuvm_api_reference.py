#!/usr/bin/env python3
"""Extract a pyuvm API reference from the installed library.

The in-loop agent used to rediscover these facts at runtime: ~71% of its shell
tool calls were `grep`/`sed`/`inspect` against pyuvm's source in site-packages,
re-run on every LLM call, every iteration, every design. They are static facts
about one pinned library version, so we extract them once and put them in the
prompt instead.

Run it inside a worker (that is where pyuvm is installed), not on the host:

    docker exec chia-sim-$USER-0 python3 /workspace/scripts/gen_pyuvm_api_reference.py \\
        > uvm_loop/config/pyuvm_api_reference.md

Regenerate it whenever pyuvm is upgraded. A reference that describes a version
the workers no longer have is worse than no reference at all -- it is the same
stale-guidance trap as a dead orchestrator snapshot (Troubleshooting #7).
"""

import inspect
import re
import sys

import pyuvm

# The classes the generated testbench actually instantiates or subclasses.
# Everything else in pyuvm's 200-symbol namespace is noise for this loop.
CLASSES = [
    "uvm_object", "uvm_transaction", "uvm_sequence_item",
    "uvm_component", "uvm_driver", "uvm_monitor", "uvm_agent",
    "uvm_scoreboard", "uvm_subscriber", "uvm_env", "uvm_test", "uvm_root",
    "uvm_sequence", "uvm_sequence_base", "uvm_sequencer", "uvm_sequencer_base",
    "uvm_analysis_port", "uvm_analysis_export", "uvm_analysis_imp",
    "uvm_tlm_analysis_fifo", "uvm_tlm_fifo",
    "ConfigDB", "uvm_config_db", "ObjectionHandler", "uvm_factory",
]

# Dunders and inherited object/Singleton plumbing carry no information for the
# agent; phase methods and the TLM surface do.
SKIP = {
    "__init__subclass__", "__subclasshook__", "__init_subclass__",
    "__reduce__", "__reduce_ex__", "__sizeof__", "__dir__", "__format__",
    "__getattribute__", "__setattr__", "__delattr__", "__new__",
}


def signature(obj):
    try:
        text = str(inspect.signature(obj))
    except (ValueError, TypeError):
        return "(...)"
    # pyuvm uses a bare `object()` as the "no default" sentinel; its repr
    # carries a heap address that would churn on every regeneration.
    return re.sub(r"<object object at 0x[0-9a-f]+>", "<no-default>", text)


def first_line(obj):
    doc = inspect.getdoc(obj) or ""
    if doc.startswith("Initialize self."):
        return ""   # object.__init__ boilerplate, no information
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def members(cls):
    """Methods defined on cls itself, split into real ones and the stubs
    pyuvm documents as "Not implemented".

    Inherited methods are deliberately excluded: repeating uvm_component's
    surface under all nine of its subclasses grew the reference to 87KB, which
    is more prompt budget than the tool calls it replaces. Each class states
    its base instead.
    """
    real, stubs = [], []
    for name, member in inspect.getmembers(cls):
        if name in SKIP or (name.startswith("_") and name != "__init__"):
            continue  # private, and name-mangled `_Cls__x` helpers
        if not (inspect.isfunction(member) or inspect.ismethod(member)):
            continue
        if next((k for k in cls.__mro__ if name in vars(k)), None) is not cls:
            continue
        doc = first_line(member)
        if doc.lower().startswith("not implemented"):
            stubs.append(name)
        else:
            real.append((name, signature(member), doc,
                         inspect.iscoroutinefunction(member)))
    return real, stubs


# Facts the agent was observed re-deriving from library source on almost every
# call. They are checked against the live library below, so a pyuvm upgrade
# that invalidates one makes this script fail loudly instead of shipping a lie.
PREAMBLE = """\
Rules that cost the most to rediscover:

- **Logging.** There are no `uvm_info` / `uvm_warning` / `uvm_error`
  functions in this pyuvm. Use the component's own logger:
  `self.logger.info(msg)`, `.warning(msg)`, `.error(msg)`, `.critical(msg)`.
- **Phases.** `build_phase`, `connect_phase`, `end_of_elaboration_phase`,
  `start_of_simulation_phase`, `extract_phase`, `check_phase`,
  `report_phase` and `final_phase` are **plain `def`**. Only `run_phase` is
  `async def`. Declaring `run_phase` non-async, or any other phase async, is
  silently wrong -- the phase either never awaits or never runs.
- **Objections.** Raise and drop on the component, not on a phase object:
  `self.raise_objection()` / `self.drop_objection()` -- both plain calls, no
  argument required, no `phase` parameter. A `run_phase` that does not raise
  an objection can be cut short.
- **ConfigDB** is a singleton *instance*: `ConfigDB().set(...)`, with the
  parentheses. The separate `uvm_config_db` class is a SystemVerilog-style
  shim whose methods are **classmethods**: `uvm_config_db.set(...)`, with no
  parentheses, forwarding to the same store. Both spellings work and share
  data; `ConfigDB.set(...)` (class, no parens) does **not** -- it is an
  unbound method and raises. Pick one spelling and use it everywhere.
  Argument order is the same for both: `(context, inst_name, field_name,
  value)` for set, `(context, inst_name, field_name)` for get. `context` is a
  component or `None` (meaning uvm_root); `inst_name` is a path glob such as
  `"*"`.
- **Sequences.** `await seq.start(sequencer)`; inside `body`, use
  `await self.start_item(item)` ... `await self.finish_item(item)`. `body`,
  `start`, `start_item` and `finish_item` are all coroutines.
- **Drivers** get items with `await self.seq_item_port.get_next_item()` and
  must pair every one with `self.seq_item_port.item_done()`.
- **Constructors.** `uvm_component.__init__(self, name, parent)` -- both
  arguments are required for components. `uvm_object.__init__(self, name='')`
  takes a name only. Always forward them with `super().__init__(name, parent)`.

Do not shell out to read pyuvm's source to confirm any of the above.
"""

# Every claim the PREAMBLE makes, as a predicate checked against the live
# library. These are exercised, not just introspected -- `raise_objection()`
# is actually called, ConfigDB actually round-trips a value -- because a
# signature can match while the call still fails. If any fails, the generator
# refuses to emit rather than shipping a reference that lies.
def _checks():
    import cocotb

    def logger_ok():
        c = pyuvm.uvm_component("_probe_component", None)
        return all(callable(getattr(c.logger, m, None))
                   for m in ("info", "warning", "error", "critical"))

    def objections_ok():
        c = pyuvm.uvm_component("_probe_objection", None)
        c.raise_objection()
        c.drop_objection()
        return "phase" not in inspect.signature(
            pyuvm.uvm_component.raise_objection).parameters

    def configdb_ok():
        if pyuvm.ConfigDB() is not pyuvm.ConfigDB():
            return False
        pyuvm.ConfigDB().set(None, "*", "_probe_key", 42)
        return pyuvm.ConfigDB().get(None, "", "_probe_key") == 42

    def configdb_shim_ok():
        pyuvm.uvm_config_db.set(None, "*", "_probe_shim", 7)
        if pyuvm.ConfigDB().get(None, "", "_probe_shim") != 7:
            return False
        # ConfigDB.set without parentheses must NOT silently work, or the
        # preamble's warning is wrong.
        try:
            pyuvm.ConfigDB.set(None, "*", "_probe_unbound", 1)
        except TypeError:
            return True
        return False

    def seq_item_port_ok():
        d = pyuvm.uvm_driver("_probe_driver", None)
        port = getattr(d, "seq_item_port", None)
        return (port is not None
                and inspect.iscoroutinefunction(
                    getattr(port, "get_next_item", None))
                and callable(getattr(port, "item_done", None))
                and not inspect.iscoroutinefunction(port.item_done))

    def super_init_ok():
        class _Probe(pyuvm.uvm_env):
            def __init__(self, name, parent):
                super().__init__(name, parent)
        _Probe("_probe_env", None)
        return True

    sync_phases = ("build_phase", "connect_phase", "end_of_elaboration_phase",
                   "start_of_simulation_phase", "extract_phase", "check_phase",
                   "report_phase", "final_phase")

    return [
        # The prompt's HARD version constraint names cocotb 2.1.0; if the
        # worker ever carries another version the whole prompt is wrong, not
        # just this reference.
        ("cocotb installed in this worker is 2.1.0",
         lambda: cocotb.__version__ == "2.1.0"),
        ("no uvm_info / uvm_warning / uvm_error functions",
         lambda: not any(hasattr(pyuvm, n)
                         for n in ("uvm_info", "uvm_warning", "uvm_error"))),
        ("a component exposes .logger with info/warning/error/critical",
         logger_ok),
        ("every phase but run_phase is plain def",
         lambda: all(not inspect.iscoroutinefunction(
             getattr(pyuvm.uvm_component, p)) for p in sync_phases)),
        ("run_phase is async def",
         lambda: inspect.iscoroutinefunction(pyuvm.uvm_component.run_phase)),
        ("raise_objection()/drop_objection() take no required argument",
         objections_ok),
        ("ConfigDB is a singleton and round-trips with the documented arity",
         configdb_ok),
        ("uvm_config_db classmethods share ConfigDB's store",
         configdb_shim_ok),
        ("body/start/start_item/finish_item are all coroutines",
         lambda: all(inspect.iscoroutinefunction(getattr(pyuvm.uvm_sequence, m))
                     for m in ("body", "start", "start_item", "finish_item"))),
        ("uvm_sequence.start's first argument is the sequencer",
         lambda: list(inspect.signature(
             pyuvm.uvm_sequence.start).parameters)[:2] == ["self", "seqr"]),
        ("a driver has seq_item_port with async get_next_item + sync item_done",
         seq_item_port_ok),
        ("uvm_component.__init__(self, name, parent)",
         lambda: list(inspect.signature(pyuvm.uvm_component.__init__).parameters)
         == ["self", "name", "parent"]),
        ("uvm_object.__init__(self, name='')",
         lambda: list(inspect.signature(pyuvm.uvm_object.__init__).parameters)
         == ["self", "name"]),
        ("super().__init__(name, parent) works in a subclass", super_init_ok),
    ]


def emit(text=""):
    print(text)


def verify():
    """Fail loudly rather than emit a reference that contradicts the library."""
    broken = []
    for name, check in _checks():
        try:
            if not check():
                broken.append(name)
        except Exception as exc:                      # a claim that now raises
            broken.append(f"{name}  [{exc!r}]")
    if broken:
        version = getattr(pyuvm, "__version__", "unknown")
        raise SystemExit(
            f"pyuvm {version} contradicts the hand-written preamble:\n  "
            + "\n  ".join(broken)
            + "\n\nUpdate PREAMBLE in this script to match the installed "
              "library before regenerating the reference."
        )


def main():
    verify()
    version = getattr(pyuvm, "__version__", "unknown")
    emit(f"# pyuvm {version} API reference (generated -- do not hand-edit)")
    emit()
    emit("Extracted from the pyuvm installed in the simulation worker by")
    emit("`scripts/gen_pyuvm_api_reference.py`. These signatures are the real")
    emit("ones. Use them as written; do not introspect the library at runtime.")
    emit()
    emit(PREAMBLE)
    emit("Class surface (own methods only -- inherited ones live under the base):")
    emit()

    for name in CLASSES:
        cls = getattr(pyuvm, name, None)
        if cls is None or not inspect.isclass(cls):
            print(f"# MISSING in pyuvm {version}: {name}", file=sys.stderr)
            continue
        bases = ", ".join(
            b.__name__ for b in cls.__bases__ if b.__name__ != "object"
        )
        emit(f"### {name}" + (f" — base: {bases}" if bases else ""))
        real, stubs = members(cls)
        if real:
            emit("```python")
            for mname, sig, mdoc, is_async in real:
                prefix = "async def" if is_async else "def"
                line = f"{prefix} {mname}{sig}"
                if mdoc and not mdoc.startswith(":"):
                    line += f"   # {mdoc[:70]}"
                emit(line)
            emit("```")
        if stubs:
            emit(f"Present but not implemented (never call): {', '.join(stubs)}")
        emit()


if __name__ == "__main__":
    main()
