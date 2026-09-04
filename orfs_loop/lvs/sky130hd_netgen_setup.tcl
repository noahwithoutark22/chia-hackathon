#---------------------------------------------------------------
# Netgen LVS setup for ORFS sky130hd.
#
# Ported from open_pdks' own sky130/netgen/sky130_setup.tcl -- the file
# OpenLane (and therefore Tiny Tapeout) uses for sky130 signoff. Only the
# device *names* differ: open_pdks compares full-PDK netlists whose models are
# `sky130_fd_pr__nfet_01v8`, while ORFS's platform CDL and KLayout's extracted
# netlist both use the bare `nfet_01v8` / `pfet_01v8_hvt`. The rules below are
# the upstream ones verbatim, applied to those names.
#
# Why this exists at all: KLayout's LVS deck cannot reconcile sky130's folded
# standard cells. A cell like a21oi_2 declares `m=2` on a *series* transistor
# stack; the layout is two parallel copies of that stack (four 0.65um fingers
# and two internal nodes), the schematic is one stack of doubled-width devices
# (two 1.3um devices, one internal node). Reducing one to the other needs
# series combination (L adds, W critical) followed by parallel combination
# (W adds, L critical). KLayout's `combine_devices` does the parallel step only,
# so the cell can never match there. Netgen does both, which is exactly what
# `series enable` / `parallel enable` below turn on.
#---------------------------------------------------------------

if {[catch {set cells1 [cells list -all -circuit1]}]} { set cells1 {} }
if {[catch {set cells2 [cells list -all -circuit2]}]} { set cells2 {} }

permute default
property default
property parallel none

#---------------------------------------------------------------
# MOSFETs: allow series and parallel combination, and ignore the `m`
# multiplier as a comparison property (upstream: `property delete mult`).
# Source/drain are permutable (upstream: `permute ... 1 2`).
#---------------------------------------------------------------
set devices {nfet_01v8 nfet_01v8_lvt nfet_01v8_nvt nfet_g5v0d10v5
             pfet_01v8 pfet_01v8_hvt pfet_01v8_lvt pfet_g5v0d10v5}

foreach dev $devices {
    if {[lsearch $cells1 $dev] >= 0} {
        permute "-circuit1 $dev" 1 2
        property "-circuit1 $dev" series enable
        property "-circuit1 $dev" series {w critical}
        property "-circuit1 $dev" series {l add}
        property "-circuit1 $dev" parallel enable
        property "-circuit1 $dev" parallel {l critical}
        property "-circuit1 $dev" parallel {w add}
        property "-circuit1 $dev" tolerance {l 0.01} {w 0.01}
        property "-circuit1 $dev" delete mult m nf sa sb sd area perim
        property "-circuit1 $dev" delete as ad ps pd topography
    }
    if {[lsearch $cells2 $dev] >= 0} {
        permute "-circuit2 $dev" 1 2
        property "-circuit2 $dev" series enable
        property "-circuit2 $dev" series {w critical}
        property "-circuit2 $dev" series {l add}
        property "-circuit2 $dev" parallel enable
        property "-circuit2 $dev" parallel {l critical}
        property "-circuit2 $dev" parallel {w add}
        property "-circuit2 $dev" tolerance {l 0.01} {w 0.01}
        property "-circuit2 $dev" delete mult m nf sa sb sd area perim
        property "-circuit2 $dev" delete as ad ps pd topography
    }
}

#---------------------------------------------------------------
# Physical-only cells. Upstream ignores fill / tapvpwrvgnd / fakediode /
# condiode / tap because they carry no extractable devices (their CDL bodies
# literally say "Cell contains no devices"), so a layout side can never be
# produced for them. `conb_1` is added here for the same reason in kind: it is
# modelled with two tie *resistors*, and the KLayout deck that produced the
# layout netlist extracts MOSFETs only.
#---------------------------------------------------------------
foreach cell $cells1 {
    if {[regexp {sky130_fd_sc_[^_]+__fill_[[:digit:]]+} $cell match]} { ignore class "-circuit1 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__tapvpwrvgnd_[[:digit:]]+} $cell match]} { ignore class "-circuit1 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__tap_[[:digit:]]+} $cell match]} { ignore class "-circuit1 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__decap_[[:digit:]]+} $cell match]} { ignore class "-circuit1 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__diode_[[:digit:]]+} $cell match]} { ignore class "-circuit1 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__conb_[[:digit:]]+} $cell match]} { ignore class "-circuit1 $cell" }
    if {[regexp {sky130_ef_sc_[^_]+__fakediode_[[:digit:]]+} $cell match]} { ignore class "-circuit1 $cell" }
}
foreach cell $cells2 {
    if {[regexp {sky130_fd_sc_[^_]+__fill_[[:digit:]]+} $cell match]} { ignore class "-circuit2 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__tapvpwrvgnd_[[:digit:]]+} $cell match]} { ignore class "-circuit2 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__tap_[[:digit:]]+} $cell match]} { ignore class "-circuit2 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__decap_[[:digit:]]+} $cell match]} { ignore class "-circuit2 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__diode_[[:digit:]]+} $cell match]} { ignore class "-circuit2 $cell" }
    if {[regexp {sky130_fd_sc_[^_]+__conb_[[:digit:]]+} $cell match]} { ignore class "-circuit2 $cell" }
    if {[regexp {sky130_ef_sc_[^_]+__fakediode_[[:digit:]]+} $cell match]} { ignore class "-circuit2 $cell" }
}
