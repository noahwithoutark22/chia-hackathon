# Correct behavioral reference model for the AXI-Stream one-entry buffer.
# This file is the functional oracle for the benchmark.

from collections import deque

_QUEUE = deque(maxlen=1)


def reset():
    """Reset the reference model to the empty state."""
    _QUEUE.clear()


def step(s_valid, s_data, m_ready):
    """
    Advance one clock cycle.

    Returns:
        (s_ready, m_valid, m_data)

    The returned values represent the DUT-visible handshake/output signals for
    the current cycle. State is updated at the clock edge according to the
    AXI-Stream VALID/READY transfers.
    """
    s_valid = int(bool(s_valid))
    m_ready = int(bool(m_ready))
    s_data = int(s_data) & 0xFF

    # One-entry elastic buffer:
    # it can accept when empty or when the current output is being consumed.
    s_ready = int((len(_QUEUE) == 0) or m_ready)

    m_valid = int(len(_QUEUE) != 0)
    m_data = int(_QUEUE[0]) if _QUEUE else 0

    input_transfer = s_valid and s_ready
    output_transfer = m_valid and m_ready

    if output_transfer:
        _QUEUE.popleft()

    if input_transfer:
        # Because s_ready is true whenever a simultaneous output transfer
        # frees the entry, there is room for the replacement item.
        _QUEUE.append(s_data)

    return s_ready, m_valid, m_data
