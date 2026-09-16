"""
hamming_encoder_model.py

Bit-exact Python reference model for the parameterized SystemVerilog
`hamming_encoder` module (see rtl/hamming_encoder.sv and spec.md).

The algorithm and bit-ordering convention here are deliberately kept in
lock-step with the RTL so this module can be used as a golden reference in a
verification testbench (e.g. compare against RTL simulation output for
randomized data_in vectors).

Convention recap:
  - Hamming positions are numbered 1..(DATA_WIDTH+PARITY_BITS).
  - Positions that are exact powers of two (1, 2, 4, 8, ...) hold parity
    bits; every other position holds a data bit, consumed in order from
    data_in bit 0 upward.
  - code bit 0 == Hamming position 1 (i.e. position `pos` maps to code bit
    `pos - 1` in the non-SECDED codeword).
  - If SECDED is requested, an extra overall even-parity bit is computed
    over the whole base codeword and placed at code bit 0; the base
    codeword is shifted up by one bit (position `pos` -> code bit `pos`).
"""

from dataclasses import dataclass


def num_parity_bits(k: int) -> int:
    """Minimum number of parity bits r such that 2**r >= k + r + 1."""
    if k <= 0:
        raise ValueError("DATA_WIDTH (k) must be > 0")
    r = 0
    while (1 << r) < (k + r + 1):
        r += 1
    return r


def is_power_of_two(n: int) -> bool:
    return n != 0 and (n & (n - 1)) == 0


@dataclass(frozen=True)
class HammingParams:
    data_width: int
    secded: bool
    parity_bits: int
    base_width: int   # data_width + parity_bits
    code_width: int   # base_width (+1 if secded)

    @staticmethod
    def compute(data_width: int, secded: bool) -> "HammingParams":
        r = num_parity_bits(data_width)
        base_width = data_width + r
        code_width = base_width + (1 if secded else 0)
        return HammingParams(
            data_width=data_width,
            secded=secded,
            parity_bits=r,
            base_width=base_width,
            code_width=code_width,
        )


def hamming_encode(data_in: int, data_width: int, secded: bool = False):
    """
    Encode `data_in` (an int holding `data_width` bits, LSB-first) into a
    Hamming codeword.

    Returns:
        (code_out, params) where code_out is an int holding `params.code_width`
        bits and params is a HammingParams instance describing the geometry
        used.
    """
    if data_in < 0 or data_in >= (1 << data_width):
        raise ValueError(f"data_in does not fit in {data_width} bits")

    params = HammingParams.compute(data_width, secded)
    n = params.base_width

    # 1-indexed Hamming positions: ham[0] is unused/padding.
    ham = [0] * (n + 1)

    # 1) Scatter data bits into non-power-of-two positions, in order.
    data_idx = 0
    for pos in range(1, n + 1):
        if is_power_of_two(pos):
            continue
        ham[pos] = (data_in >> data_idx) & 1
        data_idx += 1

    # 2) Compute each parity bit.
    for p in range(params.parity_bits):
        parity_pos = 1 << p
        par = 0
        for pos in range(1, n + 1):
            if pos != parity_pos and (pos & parity_pos):
                par ^= ham[pos]
        ham[parity_pos] = par

    # 3) Assemble the output codeword.
    if secded:
        overall_par = 0
        for pos in range(1, n + 1):
            overall_par ^= ham[pos]
        code = overall_par  # bit 0
        for pos in range(1, n + 1):
            code |= (ham[pos] << pos)
    else:
        code = 0
        for pos in range(1, n + 1):
            code |= (ham[pos] << (pos - 1))

    return code, params


def _bits_str(value: int, width: int) -> str:
    """MSB-first binary string of `value` truncated/padded to `width` bits."""
    return format(value, f"0{width}b")


if __name__ == "__main__":
    # ------------------------------------------------------------------
    # Minimal self-check: DATA_WIDTH=4 is the textbook Hamming(7,4) code.
    # Known-good table (d1 d2 d3 d4 -> p1 p2 d1 p4 d2 d3 d4), MSB-first,
    # taken from the standard Hamming(7,4) reference table.
    # ------------------------------------------------------------------
    reference_7_4 = {
        0b0000: 0b0000000,
        0b0001: 0b1101000,
        0b1000: 0b1000000,  # placeholder overwritten below with full table
    }

    # Build the reference table programmatically instead of hand-typing all
    # 16 entries: for Hamming(7,4), position order (MSB->LSB) is
    # p1 p2 d1 p4 d2 d3 d4, where d1..d4 are data_in bits 0..3 respectively
    # (data_in bit 0 is the first data bit placed, i.e. position 3 = d1).
    def brute_force_7_4(data_in: int) -> int:
        d = [(data_in >> i) & 1 for i in range(4)]  # d[0]=bit0 ... d[3]=bit3
        d1, d2, d3, d4 = d[0], d[1], d[2], d[3]
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p4 = d2 ^ d3 ^ d4
        # positions 1..7 = p1 p2 d1 p4 d2 d3 d4 (position 1 is MSB here only
        # for this manual cross-check ordering; see note below)
        bits_by_pos = {1: p1, 2: p2, 3: d1, 4: p4, 5: d2, 6: d3, 7: d4}
        code = 0
        for pos, bit in bits_by_pos.items():
            code |= (bit << (pos - 1))
        return code

    print("Self-check: Hamming(7,4), DATA_WIDTH=4, SECDED=False")
    all_ok = True
    for val in range(16):
        got, params = hamming_encode(val, data_width=4, secded=False)
        expected = brute_force_7_4(val)
        ok = (got == expected)
        all_ok &= ok
        print(f"  data_in={_bits_str(val, 4)}  "
              f"code_out={_bits_str(got, params.code_width)}  "
              f"expected={_bits_str(expected, 7)}  {'OK' if ok else 'MISMATCH'}")
    print("ALL PASS" if all_ok else "SOME MISMATCHES FOUND")

    print()
    print("Example: DATA_WIDTH=4, SECDED=True (Hamming(8,4) SECDED)")
    for val in [0, 1, 5, 15]:
        code, params = hamming_encode(val, data_width=4, secded=True)
        print(f"  data_in={_bits_str(val, 4)} -> "
              f"code_out={_bits_str(code, params.code_width)} "
              f"(parity_bits={params.parity_bits}, code_width={params.code_width})")
