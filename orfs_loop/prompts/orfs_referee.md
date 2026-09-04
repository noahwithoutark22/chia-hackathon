# PARALLEL ROUND REFEREE -- $DESIGN_NAME

Several configuration changes were just tested **in parallel, all branched
from the identical starting configuration**. That makes this a controlled
comparison, not a sequence: every difference in the results below is caused
by the change that slot made, and nothing else.

Your job is to read that comparison and say what it means. You are not
proposing the next configuration -- other calls do that. You are writing the
short note they will all read first.

## THE ROUND

$ROUND_COMPARISON

## WHAT EVERY CHANGE HAS MEASURABLY DONE SO FAR

$LEDGER

## THE CONFIGURATION AS IT STANDS RIGHT NOW

$CURRENT_CONFIG

Check this before recommending anything. A knob already sitting at the value
you were going to suggest cannot be "tried" -- re-applying it produces a
bit-identical result and spends a full flow run doing it. Such attempts leave
no trace in the measurements above, precisely because they changed nothing, so
this is the only place you can see them coming.

## HOW TO REPLY

Plain prose, no JSON, at most 150 words. Cover, in this order:

1. **Which change actually won, and by how much.** Name the metric and the
   number. If the winner only won on noise, say so.
2. **What that implies about the levers themselves** -- e.g. "area relief is
   buying far more slack per step than clock relief here", or "both repair
   knobs are now doing nothing, the die is out of room".
3. **What to try next, and what to stop trying.** Be specific about knobs.
   Explicitly call out any knob whose measured effect has flattened to
   nothing across several attempts -- that is the single most useful thing
   you can surface, because a plateau is invisible from any one slot's own
   view.
4. **When a knob's effect is quantifiable across two or more values, estimate
   how far it still has to move -- computed from the two most RECENT values,
   never from the original baseline.** A rate averaged over the whole span
   hides deceleration that already happened inside this run; the most recent
   segment is the only honest read of where the curve is now. If that local
   rate is slower than an earlier segment's, say so explicitly -- a linear
   projection of a decelerating curve is an optimistic floor, not a
   prediction, and must be stated as one. Use the estimate for two things
   only: saying roughly how many more capped steps this needs ("closes in
   about 2 more steps of this size" beats "try 1.8 or 1.9"), and telling the
   round to spread its slots across a bracket of values spanning the
   reachable range instead of clustering near one guess. **It is never
   grounds to recommend a step bigger than the per-turn cap already in
   force** -- that cap exists because a past version of exactly this
   mistake, on a different target knob, closed a design by ballooning its
   die 6x in one leap.

Name every knob **exactly** as it appears in the data above -- these names are
copied verbatim into the next round's proposals and checked against a closed
whitelist, so an invented or misspelled one costs a whole turn. If you are not
certain of a name, describe the knob instead of guessing at its spelling.

Two things to be hard-nosed about:

* $OBJECTIVE_NOTE
* If a knob has been moved repeatedly with no measurable change in the
  metrics, say plainly that it is exhausted and something else has to move.
  Do not encourage another step on it.

If every measurable knob has plateaued, do not stop at saying so. Name the
cheapest lever that has **not** been tried yet against the current objective,
and say explicitly what it would cost. A design with untried levers is not out
of options, however flat the tried ones have gone.

**Asking to "isolate" a knob is not enough to un-confound a past combined
move.** Every change is measured against the *current* configuration, which
already contains the earlier move. So "test knob B alone next round" measures
B's *further* effect on top of A, not B's share of the A+B result. If you want
to know how a past A+B gain actually split, say so precisely: **revert A to its
previous value while holding B where it is**, and name both values. If the
result barely drops, B was carrying the gain and A's cost can be given back --
which is the only way to reclaim what a combined move spent.
