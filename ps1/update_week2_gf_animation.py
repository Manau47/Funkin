#!/usr/bin/env python3
"""Replace only Week 2's ten GF dance cels with key poses from both sides.

The existing W2 package, page allocation, CLUT, and BF atlas fix are preserved.
New source cels are rendered from the pinned official GF rig and quantized to
the already-loaded W2 CLUT, then copied into the existing ten UV rectangles.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import struct
import sys


PAGE_SIDE = 256
PAGE_BYTES = PAGE_SIDE * PAGE_SIDE
W2_PAGE_COUNT = 9
SOURCE_FRAMES = (0, 3, 6, 9, 12, 15, 18, 21, 24, 27)
FRAME_SIZE = (94, 85)


def rgb555_to_rgb(word: int) -> tuple[int, int, int]:
    return tuple((((word >> shift) & 31) * 255 + 15) // 31
                 for shift in (0, 5, 10))


def parse_descriptors(text: str) -> dict[str, dict[str, int]]:
    match = re.search(
        r"static const BopeeboVisualFrame bopeebo_visual_frames\[.*?\] = \{(.*?)\n\};",
        text, re.S)
    if not match:
        raise ValueError("visual header has no frame table")
    result: dict[str, dict[str, int]] = {}
    for row, name in re.findall(r"\{([^}]+)\}, /\* ([^*]+) \*/", match.group(1)):
        values = [int(value.strip()) for value in row.split(",")[:6]]
        if len(values) != 6:
            raise ValueError(f"malformed descriptor for {name}")
        result[name.strip()] = dict(zip(("page", "palette", "u", "v", "w", "h"), values))
    return result


def read_rect(scene: bytes, frame: dict[str, int]) -> bytes:
    page_start = frame["page"] * PAGE_BYTES
    return b"".join(
        scene[page_start + (frame["v"] + y) * PAGE_SIDE + frame["u"]:
             page_start + (frame["v"] + y) * PAGE_SIDE + frame["u"] + frame["w"]]
        for y in range(frame["h"]))


def write_rect(scene: bytearray, frame: dict[str, int], pixels: bytes) -> None:
    if len(pixels) != frame["w"] * frame["h"]:
        raise ValueError("quantized GF frame has unexpected byte count")
    page_start = frame["page"] * PAGE_BYTES
    for y in range(frame["h"]):
        src = y * frame["w"]
        dst = page_start + (frame["v"] + y) * PAGE_SIDE + frame["u"]
        scene[dst:dst + frame["w"]] = pixels[src:src + frame["w"]]


def assert_nonoverlap(frames: list[dict[str, int]]) -> None:
    for index, frame in enumerate(frames):
        if frame["page"] < 2 or frame["page"] >= W2_PAGE_COUNT:
            raise ValueError(f"GF texture is outside a Week 2 character page: {frame}")
        if (frame["w"], frame["h"], frame["palette"]) != (*FRAME_SIZE, 0):
            raise ValueError(f"unexpected GF texture dimensions or palette: {frame}")
        if frame["u"] + frame["w"] > PAGE_SIDE or frame["v"] + frame["h"] > PAGE_SIDE:
            raise ValueError(f"GF UV rectangle exceeds its page: {frame}")
        for other in frames[:index]:
            if frame["page"] != other["page"]:
                continue
            if (frame["u"] < other["u"] + other["w"] and other["u"] < frame["u"] + frame["w"] and
                    frame["v"] < other["v"] + other["h"] and other["v"] < frame["v"] + frame["h"]):
                raise ValueError("two GF destinations overlap")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=pathlib.Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--visual-header", type=pathlib.Path, required=True)
    parser.add_argument("--input-scene", type=pathlib.Path, required=True)
    parser.add_argument("--output-scene", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from animate_preview import Rig
    from convert_bopeebo_visuals import fit_anchored_rig, quantize

    descriptors = parse_descriptors(args.visual_header.read_text(encoding="ascii"))
    names = [f"week2_gf_dance_{index}" for index in range(10)]
    if any(name not in descriptors for name in names):
        raise ValueError("W2 visual header is missing the ten allocated GF cels")
    frames = [descriptors[name] for name in names]
    assert_nonoverlap(frames)

    scene = bytearray(args.input_scene.read_bytes())
    expected_size = W2_PAGE_COUNT * PAGE_BYTES + 512
    if len(scene) != expected_size:
        raise ValueError(f"Week 2 package is {len(scene)} bytes, expected {expected_size}")
    original = bytes(scene)
    palette_offset = W2_PAGE_COUNT * PAGE_BYTES
    palette_words = struct.unpack_from("<256H", scene, palette_offset)
    palette = [rgb555_to_rgb(word) for word in palette_words[1:] if word & 0x7FFF]
    if len(palette) != 255 or palette_words[0] != 0:
        raise ValueError("unexpected Week 2 RGB555 palette layout")

    assets = args.assets.resolve()
    rig = Rig(assets / "shared" / "images" / "characters" / "gf", args.ffmpeg)
    # Fit the ten stored poses against the complete 30-frame Idle timeline.
    # This gives every pose the same floor and scale, including both sides.
    rendered = fit_anchored_rig(rig, list(SOURCE_FRAMES), *FRAME_SIZE,
                                anchor_frame_ids=list(range(30)))
    written = []
    for index, (source_frame, target) in enumerate(zip(SOURCE_FRAMES, frames)):
        rgba = rendered[source_frame]
        indices = quantize(rgba, palette)
        old_pixels = read_rect(bytes(scene), target)
        write_rect(scene, target, indices)
        written.append((source_frame, index, old_pixels, indices))

    # Restrict all changed bytes to the ten pre-existing GF rectangles and
    # require the CLUT and every other scene texel to remain byte-identical.
    expected = bytearray(original)
    for _source, _index, _old, indices in written:
        write_rect(expected, frames[_index], indices)
    if bytes(scene) != bytes(expected):
        raise AssertionError("package changed outside the ten allocated GF rectangles")
    if scene[palette_offset:] != original[palette_offset:]:
        raise AssertionError("Week 2 palette changed")

    args.output_scene.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_scene.write_bytes(scene)
    lines = [
        "Week 2 GF sampled dance cycle",
        "Pinned source character: shared/images/characters/gf",
        "Official Idle: 30 timeline frames; danceLeft 0..14, danceRight 15..29",
        "Stored source frames: " + ", ".join(map(str, SOURCE_FRAMES)),
        "Runtime: five cels per side per beat, alternating side on each audio-clocked beat",
        "Destination descriptors: existing week2_gf_dance_0..9, unchanged UV/page/CLUT",
        "Palette: existing W2 CLUT retained byte-for-byte; new frames quantized to it",
        f"Input W2 SHA-256: {hashlib.sha256(original).hexdigest().upper()}",
        f"Output W2 SHA-256: {hashlib.sha256(scene).hexdigest().upper()}",
        f"Changed texels: {sum(len(row[3]) for row in written)} bytes across ten allocated rectangles",
    ]
    args.manifest.write_text("\n".join(lines) + "\n", encoding="ascii")
    print("Week 2 GF: 10 key poses sampled from both official 15-frame dance halves")
    print("Source sequence: " + ",".join(map(str, SOURCE_FRAMES)))
    print("Updated only ten existing GF UV rectangles; W2 CLUT and all other texels unchanged")
    print(f"Package size unchanged: {len(scene)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
