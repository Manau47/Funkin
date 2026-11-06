#!/usr/bin/env python3
"""Generate a short, rights-safe one-shot VAG and C header for a PS1 probe."""

from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

from convert_bopeebo_to_vagi import encode_block

RATE = 22050
SAMPLES_PER_BLOCK = 28
BLOCK_BYTES = 16
TARGET_SECONDS = 0.12
AMPLITUDE = 6000


def make_sample() -> bytes:
    sample_count = math.ceil(RATE * TARGET_SECONDS)
    blocks = (sample_count + SAMPLES_PER_BLOCK - 1) // SAMPLES_PER_BLOCK
    blocks = (blocks + 3) & ~3  # DMA and SPU sample bank allocation: 64-byte multiple.
    samples: list[int] = []
    for index in range(blocks * SAMPLES_PER_BLOCK):
        time = index / RATE
        if index >= sample_count:
            value = 0
        else:
            envelope = min(1.0, time / 0.004) * math.exp(-time * 20.0)
            frequency = 880.0 if time < 0.06 else 1174.66
            value = round(AMPLITUDE * envelope * (
                0.78 * math.sin(2.0 * math.pi * frequency * time) +
                0.22 * math.sin(2.0 * math.pi * frequency * 2.0 * time)
            ))
        samples.append(value)

    encoded = bytearray()
    history = (0, 0)
    for block_index in range(blocks):
        chunk = samples[block_index * 28:(block_index + 1) * 28]
        block, history = encode_block(chunk, history, False)
        if block_index == blocks - 1:
            block = block[:1] + b"\x01" + block[2:]  # one-shot end, no repeat flag
        encoded.extend(block)
    assert len(encoded) % 64 == 0
    return bytes(encoded)


def write_vag(path: Path, data: bytes) -> None:
    header = bytearray(b"VAGp")
    header.extend(struct.pack(">I", 0x20))
    header.extend(struct.pack(">I", 0))
    header.extend(struct.pack(">I", len(data)))
    header.extend(struct.pack(">I", RATE))
    header.extend(bytes(10))
    header.extend(bytes(2))
    header.extend(b"FNF_TEST_BEEP\0\0\0")
    assert len(header) == 48
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header", type=Path, required=True)
    parser.add_argument("--vag", type=Path, required=True)
    args = parser.parse_args()
    data = make_sample()
    write_vag(args.vag, data)
    args.header.parent.mkdir(parents=True, exist_ok=True)
    values = ",\n\t".join(", ".join(f"0x{byte:02x}" for byte in data[i:i + 16])
        for i in range(0, len(data), 16))
    args.header.write_text(
        "#ifndef FUNKIN_PS1_SFX_DATA_H\n#define FUNKIN_PS1_SFX_DATA_H\n"
        f"#define SFX_SAMPLE_RATE {RATE}u\n#define SFX_SAMPLE_SIZE {len(data)}u\n"
        "static const unsigned char sfx_sample[SFX_SAMPLE_SIZE] __attribute__((aligned(64))) = {\n\t"
        f"{values}\n}};\n#endif\n",
        encoding="ascii",
    )
    print(f"Generated {len(data)} ADPCM bytes ({len(data) / 16 * 28 / RATE:.3f} s allocation), "
        f"{args.vag} and {args.header}")


if __name__ == "__main__":
    main()
