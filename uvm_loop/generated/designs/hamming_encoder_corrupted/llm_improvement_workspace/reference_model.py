"""Golden reference model for the 64-bit extended Hamming SECDED encoder.

The encoder uses:
- 64 data bits
- 7 Hamming parity bits at positions 1,2,4,8,16,32,64
- 1 overall parity bit
- 72-bit total codeword

Hamming positions are numbered from 1 through 71.
The output's codeword[1] corresponds to Hamming position 1.
codeword[0] is the overall parity bit.

Even parity is used.
"""


PARITY_POSITIONS = {1, 2, 4, 8, 16, 32, 64}
HAMMING_BITS = 71
CODEWORD_BITS = 72


def is_parity_position(position: int) -> bool:
    return position in PARITY_POSITIONS


def encode(data: int) -> int:
    """Encode a 64-bit integer into a 72-bit extended Hamming codeword."""
    if not 0 <= data < (1 << 64):
        raise ValueError("data must be a 64-bit unsigned integer")

    hamming = [0] * (HAMMING_BITS + 1)  # positions 1..71
    data_idx = 0

    for pos in range(1, HAMMING_BITS + 1):
        if pos not in PARITY_POSITIONS:
            hamming[pos] = (data >> data_idx) & 1
            data_idx += 1

    for parity_pos in sorted(PARITY_POSITIONS):
        parity = 0
        for pos in range(1, HAMMING_BITS + 1):
            if pos & parity_pos:
                parity ^= hamming[pos]
        hamming[parity_pos] = parity

    overall = 0
    for pos in range(1, HAMMING_BITS + 1):
        overall ^= hamming[pos]

    codeword = overall
    for pos in range(1, HAMMING_BITS + 1):
        codeword |= hamming[pos] << pos

    return codeword


def data_to_codeword_hex(data: int) -> str:
    return f"{encode(data):018x}"


TEST_VECTORS = [
    0x0000000000000000,
    0x0000000000000001,
    0xffffffffffffffff,
    0x0123456789abcdef,
    0xdeadbeefcafebabe,
    0xaaaaaaaaaaaaaaaa,
    0x5555555555555555,
]


if __name__ == "__main__":
    for data in TEST_VECTORS:
        print(
            f"data=0x{data:016x}  "
            f"codeword=0x{encode(data):018x}"
        )

    # Basic invariants:
    for data in TEST_VECTORS:
        cw = encode(data)

        # Overall 72-bit codeword must have even parity.
        assert cw.bit_count() % 2 == 0

        # Every Hamming parity check must have even parity.
        for parity_pos in PARITY_POSITIONS:
            parity = 0
            for pos in range(1, HAMMING_BITS + 1):
                if pos & parity_pos:
                    parity ^= (cw >> pos) & 1
            assert parity == 0

    print("All Hamming encoder reference-model tests passed.")
