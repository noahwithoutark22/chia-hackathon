"""orfs_onboard.py -- generate an ORFS config.mk + starter SDC from a
Tiny-Tapeout-style design repo (info.yaml + src/), so the existing
ORFSTool / orfs_loop.py closure pipeline can run against ANY RTL you're
handed, not just the FFT baseline it was originally validated against.

Why this exists: ORFSTool/orfs_loop.py both assume a config.mk already
exists for the design. It never does for a fresh Tiny Tapeout repo -- TT's
own GitHub Action builds via OpenLane directly from info.yaml, it never
produces an ORFS config.mk. This script is the missing bridge: run it once
per new design, before orfs_loop.py, to produce that config.mk.

v2 change (this revision): the first version wrote host-absolute paths into
VERILOG_FILES/SDC_FILE. That's fine if you run ORFS directly on the host,
but the actual working setup (chia-orfs-run:local, built FROM
openroad/orfs:latest) has its toolchain baked into the CONTAINER at
/OpenROAD-flow-scripts, not on the host -- host paths in the generated
config.mk are meaningless once copied in. Confirmed by hand against the
real FFT-tiny-tapeout repo: needed a manual `docker cp` of the RTL, a
`docker cp` of config.mk/constraint.sdc, and two `sed` passes to rewrite
VERILOG_FILES and SDC_FILE from host paths to container paths, before
`make synth` finally worked. This revision automates all of that:

  1. RTL source is now COPIED into <output-root>/designs/<platform>/
     <design>/rtl-src/ alongside config.mk (not referenced from wherever
     --design-repo happens to live), so the whole design dir is one
     self-contained, copyable unit.
  2. config.mk/constraint.sdc are written using --container-flow-dir
     (the path ORFS's Makefile will actually see once inside the
     container) instead of the host output path, so no path-rewriting
     sed pass is needed after copying in.
  3. With --docker-container given, the script runs `docker cp` itself to
     land the whole design dir at the right spot inside the running
     container, end to end, one command.

Usage (against any Tiny-Tapeout-style repo):
    git clone https://github.com/<you>/<your-tt-repo>.git ~/<your-tt-repo>

    python orfs_onboard.py \
        --design-repo ~/<your-tt-repo> \
        --output-root ./generated-flow-configs \
        --container-flow-dir /root/OpenROAD-flow-scripts/flow \
        --platform sky130hd \
        --docker-container chia-orfs-$USER-0

This writes, on the HOST (staging area, not used by ORFS directly):
    <output-root>/designs/<platform>/<design_name>/config.mk
    <output-root>/designs/<platform>/<design_name>/constraint.sdc
    <output-root>/designs/<platform>/<design_name>/rtl-src/...

...with config.mk/constraint.sdc referencing paths as they will appear
INSIDE the container (under --container-flow-dir), and then -- because
--docker-container was given -- copies that whole design directory into
the container at:
    <container-flow-dir>/designs/<platform>/<design_name>/

If you omit --docker-container, the script just prints the exact `docker
cp` command to run yourself instead of running it, and stops there.

If you're running ORFS directly on the host with no container involved,
pass the same path to both --output-root and --container-flow-dir's
parent (i.e. treat "container" paths as just "the real paths" and skip
--docker-container) -- the script doesn't assume a container is involved.

NOTE ON CONFIG.MK VARIABLE NAMES: as flagged in orfs_tunables_schema.json's
_comment, ORFS's variable names can drift between releases/platforms. This
script writes the commonly-stable core set (PLATFORM, DESIGN_NAME,
VERILOG_FILES, SDC_FILE, CLOCK_PORT, CLOCK_PERIOD, CORE_UTILIZATION,
CORE_ASPECT_RATIO, CORE_MARGIN, PLACE_DENSITY). Run a `make synth` dry-run
after generating (printed at the end of this script's output) to confirm
your specific ORFS checkout accepts these as-is before trusting the
closure loop on top of it.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Missing dependency: pip install pyyaml", file=sys.stderr)
    raise

DEFAULT_CORE_UTILIZATION = 40.0   # conservative starting point; the closure
                                   # loop's PLACE_DENSITY/CORE_UTILIZATION
                                   # tunables refine this, it doesn't need to
                                   # be right on the first try.
DEFAULT_PLACE_DENSITY = 0.6
DEFAULT_CORE_ASPECT_RATIO = 1.0
DEFAULT_CORE_MARGIN = 2.0

RTL_SUBDIR_NAME = "rtl-src"

# Ports commonly used for clock/reset across Tiny Tapeout designs (TT's own
# templates standardize on these names). Overridable via CLI since not every
# repo will match.
DEFAULT_CLOCK_PORT_CANDIDATES = ["clk", "clock", "clk_i", "i_clk"]


def load_info_yaml(design_repo: Path) -> dict[str, Any]:
    info_path = design_repo / "info.yaml"
    if not info_path.exists():
        raise FileNotFoundError(
            f"No info.yaml at {info_path}. This repo isn't Tiny-Tapeout-shaped -- "
            f"use --top/--clock-hz/--verilog-files to specify the design manually "
            f"instead of relying on info.yaml auto-detection."
        )
    with open(info_path) as f:
        data = yaml.safe_load(f)
    # TT's schema nests everything under a top-level "project:" key.
    return data.get("project", data)


def resolve_source_files(design_repo: Path, source_files: list[str]) -> list[Path]:
    """Resolve info.yaml's source_files list to real paths under design_repo/src/.
    Returns paths RELATIVE TO design_repo/src/ (as Path objects) -- caller
    decides where they end up copied to."""
    src_dir = design_repo / "src"
    resolved = []
    missing = []
    for fname in source_files:
        p = src_dir / fname
        if p.exists():
            resolved.append(Path(fname))
        else:
            missing.append(fname)
    if missing:
        raise FileNotFoundError(
            f"info.yaml lists source_files not found under {src_dir}: {missing}. "
            f"Check for typos or files info.yaml expects but that weren't committed."
        )
    if not resolved:
        raise ValueError(f"No verilog source files resolved under {src_dir}")
    return resolved


def copy_rtl_into_design_dir(design_repo: Path, rel_source_files: list[Path], design_dir: Path) -> list[Path]:
    """Copy design_repo/src/<rel> for every rel in rel_source_files into
    design_dir/rtl-src/src/<rel>, preserving structure, plus anything those
    files `include (since Yosys will need includes on disk too, and
    info.yaml's source_files list often only names the top-level file --
    confirmed against FFT-tiny-tapeout, where project.v `includes 5 other
    files not separately listed). Returns the list of copied file paths
    (absolute, on the host) for the *directly listed* files only -- the
    includes just need to exist alongside them, they don't go in
    VERILOG_FILES themselves.
    """
    src_root = design_repo / "src"
    dest_root = design_dir / RTL_SUBDIR_NAME / "src"
    dest_root.mkdir(parents=True, exist_ok=True)

    # Copy the whole src/ tree, not just the listed files -- simplest way to
    # guarantee `include-d files (and anything else Yosys's preprocessor
    # reaches for) are present without re-implementing a Verilog include
    # resolver here. Cheap: these are small RTL source trees, not IP
    # libraries with generated content.
    for item in src_root.rglob("*"):
        if item.is_file():
            rel = item.relative_to(src_root)
            dest = dest_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)

    copied_listed = [dest_root / rel for rel in rel_source_files]
    missing = [p for p in copied_listed if not p.exists()]
    if missing:
        raise RuntimeError(f"Internal error: expected copied files missing: {missing}")
    return copied_listed


def detect_clock_port(design_repo: Path, top_module: str, hint: str | None) -> str:
    if hint:
        return hint
    # Best-effort: grep the top module's port list for a common clock-port
    # name. This is a heuristic, not a Verilog parser -- if it picks wrong,
    # override with --clock-port.
    src_dir = design_repo / "src"
    for vfile in src_dir.rglob("*.v"):
        text = vfile.read_text(errors="ignore")
        if f"module {top_module}" not in text and f"module\t{top_module}" not in text:
            continue
        for candidate in DEFAULT_CLOCK_PORT_CANDIDATES:
            if re.search(rf"\b{re.escape(candidate)}\b", text):
                return candidate
    raise ValueError(
        f"Could not auto-detect a clock port for top module {top_module!r}. "
        f"Pass --clock-port explicitly (check the module's port list yourself)."
    )


def render_config_mk(
    *,
    platform: str,
    design_name: str,
    container_verilog_files: list[str],
    clock_port: str,
    clock_period_ns: float,
    core_utilization: float,
    place_density: float,
    core_aspect_ratio: float,
    core_margin: float,
    container_sdc_abspath: str,
) -> str:
    files_str = " \\\n\t".join(container_verilog_files)
    return f"""\
# --- Generated by orfs_onboard.py -- DO NOT hand-edit, regenerate instead ---
# Paths below are CONTAINER paths (as seen inside the ORFS toolchain
# image), not host paths -- this file is meant to be copied into the
# container as-is, no path rewriting needed.
export PLATFORM = {platform}
export DESIGN_NAME = {design_name}

export VERILOG_FILES = \\
\t{files_str}

export SDC_FILE = {container_sdc_abspath}

export CLOCK_PORT = {clock_port}
export CLOCK_PERIOD = {clock_period_ns}

export CORE_UTILIZATION = {core_utilization}
export CORE_ASPECT_RATIO = {core_aspect_ratio}
export CORE_MARGIN = {core_margin}
export PLACE_DENSITY = {place_density}
# --- end generated block ---
"""


def render_sdc(clock_port: str, clock_period_ns: float) -> str:
    return f"""\
# Generated by orfs_onboard.py -- minimal starter constraint file.
# Extend this manually if your design has I/O timing constraints beyond
# the clock definition (input/output delays, false paths, etc.) -- this
# only defines the clock, which is the bare minimum ORFS needs to run.
create_clock -name clk -period {clock_period_ns} [get_ports {clock_port}]
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--design-repo", required=True, type=Path,
                     help="Path to the cloned RTL repo (contains info.yaml + src/, "
                          "Tiny-Tapeout-style)")
    ap.add_argument("--output-root", required=True, type=Path,
                     help="HOST staging directory to write designs/<platform>/<design>/ "
                          "under. This is NOT necessarily where ORFS will run from -- "
                          "see --container-flow-dir.")
    ap.add_argument("--container-flow-dir", default=None,
                     help="The flow/ path as it will appear INSIDE the container ORFS "
                          "actually runs in (e.g. /root/OpenROAD-flow-scripts/flow). "
                          "config.mk/constraint.sdc are written referencing paths "
                          "under this prefix. If omitted, defaults to --output-root "
                          "itself (host-only mode, no container involved).")
    ap.add_argument("--docker-container", default=None,
                     help="If given, `docker cp` the generated design directory into "
                          "this running container at <container-flow-dir>/designs/"
                          "<platform>/<design>/ automatically. If omitted, the exact "
                          "docker cp command is printed instead of run.")
    ap.add_argument("--platform", default="sky130hd")
    ap.add_argument("--design-name", default=None,
                     help="Overrides info.yaml's top_module for the ORFS design dir name")
    ap.add_argument("--top", default=None, help="Override top_module from info.yaml")
    ap.add_argument("--clock-hz", type=float, default=None,
                     help="Override clock_hz from info.yaml")
    ap.add_argument("--clock-port", default=None,
                     help="Override auto-detected clock port name")
    ap.add_argument("--verilog-files", nargs="*", default=None,
                     help="Override source_files from info.yaml (relative to design-repo/src/)")
    ap.add_argument("--core-utilization", type=float, default=DEFAULT_CORE_UTILIZATION)
    ap.add_argument("--place-density", type=float, default=DEFAULT_PLACE_DENSITY)
    ap.add_argument("--core-aspect-ratio", type=float, default=DEFAULT_CORE_ASPECT_RATIO)
    ap.add_argument("--core-margin", type=float, default=DEFAULT_CORE_MARGIN)
    args = ap.parse_args()

    design_repo = args.design_repo.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()

    if args.top and args.clock_hz and args.verilog_files:
        # Fully manual mode -- no info.yaml needed at all.
        top_module = args.top
        clock_hz = args.clock_hz
        rel_source_files = resolve_source_files(design_repo, args.verilog_files)
    else:
        info = load_info_yaml(design_repo)
        top_module = args.top or info.get("top_module")
        clock_hz = args.clock_hz or info.get("clock_hz")
        source_files = args.verilog_files or info.get("source_files")
        if not top_module or not clock_hz or not source_files:
            raise ValueError(
                f"info.yaml missing one of top_module/clock_hz/source_files "
                f"(got top_module={top_module!r}, clock_hz={clock_hz!r}, "
                f"source_files={source_files!r}). Fill in the missing piece(s) "
                f"with --top/--clock-hz/--verilog-files."
            )
        rel_source_files = resolve_source_files(design_repo, source_files)

    if not top_module:
        raise ValueError("No top module resolved -- pass --top explicitly.")
    if not clock_hz or clock_hz <= 0:
        raise ValueError(f"Invalid clock_hz: {clock_hz!r} -- pass --clock-hz explicitly.")

    design_name = args.design_name or top_module
    clock_period_ns = round(1e9 / float(clock_hz), 3)
    clock_port = detect_clock_port(design_repo, top_module, args.clock_port)

    # --- host staging: write config.mk/constraint.sdc + copy RTL here ---
    design_dir = output_root / "designs" / args.platform / design_name
    design_dir.mkdir(parents=True, exist_ok=True)

    copy_rtl_into_design_dir(design_repo, rel_source_files, design_dir)

    # --- container-side paths used INSIDE config.mk/constraint.sdc ---
    container_flow_dir = args.container_flow_dir or str(output_root)
    container_design_dir = f"{container_flow_dir.rstrip('/')}/designs/{args.platform}/{design_name}"
    container_verilog_files = [
        f"{container_design_dir}/{RTL_SUBDIR_NAME}/src/{rel}" for rel in rel_source_files
    ]
    sdc_relname = "constraint.sdc"
    container_sdc_abspath = f"{container_design_dir}/{sdc_relname}"

    config_mk_text = render_config_mk(
        platform=args.platform,
        design_name=design_name,
        container_verilog_files=container_verilog_files,
        clock_port=clock_port,
        clock_period_ns=clock_period_ns,
        core_utilization=args.core_utilization,
        place_density=args.place_density,
        core_aspect_ratio=args.core_aspect_ratio,
        core_margin=args.core_margin,
        container_sdc_abspath=container_sdc_abspath,
    )
    sdc_text = render_sdc(clock_port, clock_period_ns)

    (design_dir / "config.mk").write_text(config_mk_text)
    (design_dir / sdc_relname).write_text(sdc_text)

    print(f"Design:        {design_name}")
    print(f"Top module:    {top_module}")
    print(f"Clock port:    {clock_port}  (period {clock_period_ns:.3f} ns, "
          f"{clock_hz/1e6:.3f} MHz)")
    print(f"Verilog files (VERILOG_FILES, container paths):")
    for f in container_verilog_files:
        print(f"  - {f}")
    print(f"All RTL files staged at (host):")
    print(f"  {design_dir / RTL_SUBDIR_NAME / 'src'}")
    print(f"\nWrote (host staging):")
    print(f"  {design_dir / 'config.mk'}")
    print(f"  {design_dir / sdc_relname}")

    dest_in_container = f"{container_flow_dir.rstrip('/')}/designs/{args.platform}/"
    docker_cp_cmd = ["docker", "cp", str(design_dir), f"{args.docker_container or '<CONTAINER_NAME>'}:{dest_in_container}"]

    if args.docker_container:
        print(f"\nCopying into container '{args.docker_container}' at {dest_in_container} ...")
        result = subprocess.run(docker_cp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"docker cp FAILED:\n{result.stderr}", file=sys.stderr)
            return 1
        print("Copied successfully.")
        synth_check_path = f"{container_design_dir}/config.mk"
        print(f"\nNext: sanity-check with a dry-run before trusting the closure loop on it:")
        print(f"  docker exec -it {args.docker_container} bash -c "
              f"'make -C {container_flow_dir} DESIGN_CONFIG={synth_check_path} synth'")
    else:
        print(f"\nNo --docker-container given -- run this yourself to copy into your container:")
        print(f"  {' '.join(docker_cp_cmd)}")
        print(f"\nThen sanity-check with a dry-run before trusting the closure loop on it:")
        print(f"  docker exec -it <CONTAINER_NAME> bash -c "
              f"'make -C {container_flow_dir} DESIGN_CONFIG={container_design_dir}/config.mk synth'")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())