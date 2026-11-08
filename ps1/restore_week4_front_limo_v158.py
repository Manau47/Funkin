#!/usr/bin/env python3
"""Restore the front-limo rectangle lost in the v157 Week 4 repack.

Copies only that already-converted indexed rectangle from the archived v156c
package. No official assets, palette, audio, or other scene pixels are rebuilt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PAGE_BYTES = 256 * 256
PAGE_COUNT_V157 = 9
PAGE_COUNT_V156C = 10
SRC = (8, 32, 240, 76)
DST = (8, 176, 240, 76)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v156c", type=Path, required=True,
                        help="archived v156c preconverted-week4 directory")
    parser.add_argument("--v157", type=Path, required=True,
                        help="v157 preconverted Week 4 package directory")
    parser.add_argument("--output", type=Path, required=True,
                        help="new output directory; must not already exist")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    old_path = args.v156c / "week4-scene.bin"
    new_path = args.v157 / "week4-scene.bin"
    old, new = old_path.read_bytes(), new_path.read_bytes()
    if len(old) != PAGE_COUNT_V156C * PAGE_BYTES + 512:
        raise ValueError(f"unexpected v156c package size: {len(old)}")
    if len(new) != PAGE_COUNT_V157 * PAGE_BYTES + 512:
        raise ValueError(f"unexpected v157 package size: {len(new)}")

    old_page = old[7 * PAGE_BYTES:8 * PAGE_BYTES]
    new_page = bytearray(new[7 * PAGE_BYTES:8 * PAGE_BYTES])
    sx, sy, width, height = SRC
    dx, dy, dst_width, dst_height = DST
    if (width, height) != (dst_width, dst_height):
        raise ValueError("source and destination rectangles must match")
    for row in range(height):
        source = old_page[(sy + row) * 256 + sx:(sy + row) * 256 + sx + width]
        start = (dy + row) * 256 + dx
        new_page[start:start + width] = source

    patched = bytearray(new)
    patched[7 * PAGE_BYTES:8 * PAGE_BYTES] = new_page
    args.output.mkdir(parents=True)
    (args.output / "week4-scene.bin").write_bytes(patched)
    report = {
        "version": "v158-front-limo-restore",
        "source_v156c_sha256": sha256(old),
        "input_v157_sha256": sha256(new),
        "output_v158_sha256": sha256(patched),
        "source_page": 7,
        "source_rect": SRC,
        "destination_page": 7,
        "destination_rect": DST,
        "restored_nonzero_indices": sum(value != 0 for row in range(height)
            for value in new_page[(dy + row) * 256 + dx:
                                  (dy + row) * 256 + dx + width]),
        "only_page_7_rect_changed": True,
        "other_resources_reconverted": False,
    }
    (args.output / "front-limo-v158.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
