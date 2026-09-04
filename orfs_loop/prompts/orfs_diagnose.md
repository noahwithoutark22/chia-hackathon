# ORFS STALL DIAGNOSIS -- $DESIGN_NAME

The closure loop has made no real progress for several turns in a row --
each recent run came back REGRESSED or UNCHANGED against the one before it.
Repeating the same kind of move clearly isn't working. You are **not**
proposing a config change here; a separate turn does that right after this
one, using what you say here. Your only job is a short, honest root-cause
diagnosis.

## RECENT RUN HISTORY (tunables changed, outcome, each turn)

$STALL_HISTORY

## RAW DETAIL FROM THE MOST RECENT RUN

$RAW_LOG_EXCERPT

## YOUR JOB

In 3-5 sentences:

1. What is actually going wrong -- not just restating the metric (e.g. not
   "setup slack is negative"), but *why* the moves tried so far haven't
   fixed it. Look for a pattern across the history: the same knob pushed
   repeatedly with no effect, two knobs fighting each other, a symptom that
   doesn't match any knob available in the schema, a value oscillating back
   and forth between two settings.
2. Which specific tunable(s) -- ones **not yet meaningfully tried** per the
   history above, or tried but in the wrong direction/magnitude -- are most
   likely to actually help, and why.

Plain prose only. No JSON, no `CLOSURE:` sentinel, nothing for a program to
parse -- this goes to a human-readable diagnosis field the next turn reads,
not to the config.
