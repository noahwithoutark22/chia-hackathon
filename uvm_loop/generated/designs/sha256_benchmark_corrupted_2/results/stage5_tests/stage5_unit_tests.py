"""Unit tests for stage-5 coverage + assertions logic (no simulator needed).

Tests the pure per-edge decision functions in sha256_assertions and the
cocotb-coverage coverpoint/cross registration + sampling in
sha256_coverage.  Does NOT start cocotb coroutines (no simulator here).
The feed helpers below stop at the first violation, exactly like the real
checker coroutines do (an AssertionError kills the coroutine).
"""
import sys
import os

# results/stage5_tests -> tb/ (two levels up)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "tb"))

from sha256_pins import COMPLETION_MARGIN_CYCLES  # noqa: E402
from sha256_assertions import _step_digest_hold, _step_latency  # noqa: E402
from sha256_coverage import (  # noqa: E402
    MSG_LEN_CP_NAME,
    START_CP_NAME,
    DONE_CP_NAME,
    START_DONE_CROSS_NAME,
    MSG_LEN_BIN_LABELS,
    coverage_db,
    sample_msg_len,
    sample_control_signals,
    coverage_summary_dict,
    report_coverage,
)

FAILURES = []


def check(name, cond):
    if cond:
        print(f"  PASS: {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL: {name}")


print("== coverage registration ==")
expected_keys = {
    MSG_LEN_CP_NAME, START_CP_NAME, DONE_CP_NAME, START_DONE_CROSS_NAME,
}
check("all cover objects registered in shared coverage_db",
      expected_keys.issubset(coverage_db))

cp = coverage_db[MSG_LEN_CP_NAME]
check("msg_len bin labels match plan",
      list(cp.detailed_coverage) == MSG_LEN_BIN_LABELS)

print("== coverage sampling ==")
for val, binlabel in [(0, "zero_len"), (8, "short_len"), (88, "short_len"),
                      (200, "medium_len"), (344, "long_len"), (440, "max_len")]:
    sample_msg_len(val)
    hits = dict(cp.detailed_coverage)
    check(f"sample_msg_len({val}) hits {binlabel}",
          hits[binlabel] >= 1)

sample_control_signals(1, 1)
sample_control_signals(1, 0)
sample_control_signals(0, 1)
sample_control_signals(0, 0)
cross = dict(coverage_db[START_DONE_CROSS_NAME].detailed_coverage)
check("start_done_cross correlates exactly",
      all(cross[k] == 1 for k in
          [("asserted", "asserted"), ("asserted", "deasserted"),
           ("deasserted", "asserted"), ("deasserted", "deasserted")]))
check("start/done points both hit",
      dict(coverage_db[START_CP_NAME].detailed_coverage) ==
      {"asserted": 2, "deasserted": 2}
      and dict(coverage_db[DONE_CP_NAME].detailed_coverage) ==
      {"asserted": 2, "deasserted": 2})
sumd = coverage_summary_dict()
check("summary dict totals sane",
      sumd["total_size"] >= 13 and sumd["total_percent"] > 0)
report_coverage(bins=False)

print("== _step_digest_hold ==")


def feed_digest(steps, initial=None):
    """Step until the first violation (checker dies on first violation)."""
    state = {"cycle": 0, "prev_start": 0, "prev_digest": 0,
             "completion_cycle": None}
    if initial:
        state.update(initial)
    for (rst, start, digest) in steps:
        state, viol = _step_digest_hold(state, in_reset=(rst == 0),
                                        cur_start=start, cur_digest=digest)
        if viol:
            return state, (state["cycle"], viol)
    return state, None


# reset clears hold contract
st, viol = feed_digest([(0, 0, 0), (1, 0, 5), (1, 0, 9)])
check("hold: digest changes after reset release are ignored (no completion armed)",
      viol is None and st["prev_digest"] == 9)
# stable digest after completion -> no violation
st, viol = feed_digest([(1, 1, 0)] + [(1, 0, 0)] * 70 + [(1, 0, 0)])
check("hold: no violation for stable digest after completion", viol is None)
# violation: digest changes beyond completion window without new start
st, viol = feed_digest([(1, 1, 0)] + [(1, 0, 0)] * 70 + [(1, 0, 0xAB)])
check("hold: violation when digest changes outside completion window",
      viol is not None and viol[0] == 72
      and "digest_holds_until_next" in viol[1])
# change exactly AT the completion sample edge (start+70) is allowed
st, viol = feed_digest([(1, 1, 0)] + [(1, 0, 0)] * 69 + [(1, 0, 0xAB)] +
                       [(1, 0, 0xAB)])
check("hold: change exactly at completion edge (start+70) allowed", viol is None)
# restart re-arms the window
st, viol = feed_digest([(1, 1, 0)] + [(1, 0, 0)] * 10 + [(1, 1, 3)] +
                       [(1, 0, 3)] * 70 + [(1, 0, 9)])
check("hold: change after restart's completion window is a violation",
      viol is not None and "digest_holds_until_next" in viol[1])

print("== _step_latency ==")


def feed_lat(steps):
    """Step until the first violation (checker dies on first violation)."""
    state = {"cycle": 0, "prev_start": 0, "pending": []}
    for (rst, start, digest) in steps:
        state, viol = _step_latency(state, in_reset=(rst == 0),
                                    cur_start=start, cur_digest=digest)
        if viol:
            return state, (state["cycle"], viol)
    return state, None


# corrupted-RTL-like: digest stays 0 -> violation one cycle after the band
st, viol = feed_lat([(1, 1, 0)] + [(1, 0, 0)] * 200)
check("latency: digest=0 forever -> violation right after band",
      viol is not None and viol[0] == 1 + COMPLETION_MARGIN_CYCLES + 1
      and "transaction_completes_within_latency" in viol[1])
# correct completion at cycle start+64 (in band) -> no violation
st, viol = feed_lat([(1, 1, 0)] + [(1, 0, 0)] * 63 + [(1, 0, 0x1111)] +
                    [(1, 0, 0x1111)] * 20)
check("latency: non-zero digest inside [64,70] satisfies window", viol is None)
# transient early non-zero digest that vanishes before the band -> violation
st, viol = feed_lat([(1, 1, 0)] + [(1, 0, 0x5)] * 5 + [(1, 0, 0)] * 100)
check("latency: transient early non-zero (gone before band) is a violation",
      viol is not None and viol[0] == 72)
# SVA-consistent: a non-zero digest that PERSISTS into the band satisfies
st, viol = feed_lat([(1, 1, 0)] + [(1, 0, 0x5)] * 5 + [(1, 0, 0x5)] * 100)
check("latency: persistent non-zero reaching the band satisfies (SVA semantics)",
      viol is None)
# reset clears windows (no spurious violation)
st, viol = feed_lat([(1, 1, 0)] + [(1, 0, 0)] * 30 + [(0, 0, 0)] +
                    [(1, 0, 0)] * 3)
check("latency: reset clears pending windows", viol is None)
# back-to-back: two starts; first completes, second completes in band
steps = [(1, 1, 0)]                      # T1 start at cycle 1
steps += [(1, 0, 0)] * 63                # cycles 2..64
steps += [(1, 0, 0xABCD)]                # cycle 65: T1 digest non-zero (band 65..71)
steps += [(1, 0, 0xABCD)] * 5            # cycles 66..70
steps += [(1, 1, 0)]                     # cycle 71: T2 start
steps += [(1, 0, 0xABCD)] * 130          # T2 completion at 71+64=135 (in band)
st, viol = feed_lat(steps)
check("latency: back-to-back both satisfied (no violation)", viol is None)
# start-while-busy restart: both windows satisfied (a non-zero digest inside
# each window's band satisfies it; SVA checks the output within [64:70])
steps = [(1, 1, 0)]                 # T1 at cycle 1
steps += [(1, 0, 0)] * 9            # cycles 2..10
steps += [(1, 1, 0)]                # cycle 11: T2 (restart while busy)
steps += [(1, 0, 0)] * 53           # cycles 12..64 (no digest yet)
steps += [(1, 0, 0xABCD)] * 80      # cycles 65..145: T1 band [65,71] and T2 band [75,81]
st, viol = feed_lat(steps)
check("latency: restart satisfied (non-zero in both windows' bands)", viol is None)

print()
if FAILURES:
    print("TESTS FAILED:", FAILURES)
    sys.exit(1)
print("ALL TESTS PASSED")