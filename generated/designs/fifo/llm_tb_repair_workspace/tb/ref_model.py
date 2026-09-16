from collections import deque

def reset():
    return {"queue": deque(), "dout": 0}

def step(state, wr_en, rd_en, din, depth):
    q = state["queue"]
    dout = state["dout"]

    full = len(q) == depth
    empty = len(q) == 0

    write_accepted = bool(wr_en and not full)
    read_accepted = bool(rd_en and not empty)

    if write_accepted:
        q.append(int(din))

    if read_accepted:
        dout = q.popleft()

    return {
        "queue": q,
        "dout": dout,
    }
