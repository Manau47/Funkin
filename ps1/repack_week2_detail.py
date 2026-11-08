#!/usr/bin/env python3
"""Trade a small amount of Week 2 Spooky Kids size for denser BF cels.

The existing Week 2 8bpp CLUT and nine-page package are kept. Character-page
rectangles are deterministically repacked; Spooky Kids is re-rasterized at 90%
of its former texture and display dimensions, while BF is re-rasterized from
the pinned official atlas at 62x62 and remains displayed at 52x52.
"""

from __future__ import annotations

import argparse
import pathlib
import random
import re
import struct
import sys

from augment_bf_sing_poses import palette_from_header
from convert_bopeebo_visuals import atlas_frames, extract_sparrow_frame, quantize


SIDE = 256
PAGE_BYTES = SIDE * SIDE
SPOOKY_SIZE = (76, 90)
BF_SIZE = (62, 62)
BF_DIRECTIONS = ("left", "down", "up", "right")
SPOOKY_SELECTION = [
    (f"week2_spooky_idle_{pose}", "spooky dance idle", frame)
    for pose, frame in enumerate((0, 2, 4, 6, 8, 10, 12, 14))
]
SPOOKY_SELECTION += [
    (f"week2_spooky_sing_{direction}_{pose}", group, frame)
    for direction, group, frames in (
        ("left", "note sing left", (0, 7)),
        ("down", "spooky DOWN note", (0, 12)),
        ("up", "spooky UP NOTE", (0, 2)),
        ("right", "spooky sing right", (0, 12)),
    )
    for pose, frame in enumerate(frames)
]


def parse_header(text: str) -> tuple[list[tuple[str, dict[str, int]]], dict[str, int], list[int]]:
    match = re.search(
        r"static const BopeeboVisualFrame bopeebo_visual_frames\[.*?\] = \{(.*?)\n\};",
        text,
        re.S,
    )
    if not match:
        raise ValueError("visual header has no frame table")
    frames = []
    for row, name in re.findall(r"\{([^}]+)\}, /\* ([^*]+) \*/", match.group(1)):
        values = [int(value.strip()) for value in row.split(",")[:6]]
        if len(values) != 6:
            raise ValueError(f"malformed visual descriptor {name}")
        frames.append((name.strip(), dict(zip(("page", "palette", "u", "v", "w", "h"), values))))
    ids = {name: int(value) for name, value in re.findall(
        r"^#define VIS_([A-Z0-9_]+) (\d+)u$", text, re.M)}
    slot_match = re.search(
        r"bopeebo_week2_page_slots\[BOPEEBO_WEEK2_PAGE_COUNT\] = \{([^}]+)\}", text)
    if not slot_match:
        raise ValueError("visual header has no Week 2 page map")
    slots = [int(value) for value in re.findall(r"\d+", slot_match.group(1))]
    return frames, ids, slots


def parse_count(text: str, name: str) -> int:
    match = re.search(rf"^#define {name} (\d+)u$", text, re.M)
    if not match:
        raise ValueError(f"missing {name}")
    return int(match.group(1))


def parse_extras(text: str) -> int:
    match = re.search(r"bopeebo_bf_sing_extra_frames\[BOPEEBO_BF_SING_EXTRA_COUNT\] = \{(.*?)\n\};", text, re.S)
    if not match or len(re.findall(r"\{([^}]+)\}", match.group(1))) != 4:
        raise ValueError("expected the four existing BF sing-extra descriptors")
    return 4


def page_palette(payload: bytes) -> list[tuple[int, int, int]]:
    words = struct.unpack("<256H", payload[-512:])
    if words[0] != 0:
        raise ValueError("Week 2 palette transparency entry changed")
    return [tuple((((word >> shift) & 31) * 255 + 15) // 31 for shift in (0, 5, 10))
            for word in words[1:]]


def read_rect(payload: bytes, package_page: int, frame: dict[str, int]) -> bytes:
    result = bytearray(frame["w"] * frame["h"])
    page_start = package_page * PAGE_BYTES
    for y in range(frame["h"]):
        src = page_start + (frame["v"] + y) * SIDE + frame["u"]
        dst = y * frame["w"]
        result[dst:dst + frame["w"]] = payload[src:src + frame["w"]]
    return bytes(result)


def write_rect(payload: bytearray, package_page: int, x: int, y: int,
               width: int, height: int, pixels: bytes) -> None:
    page_start = package_page * PAGE_BYTES
    for row in range(height):
        src = row * width
        dst = page_start + (y + row) * SIDE + x
        payload[dst:dst + width] = pixels[src:src + width]


def pack_rectangles(rectangles: list[tuple[str, int, int]]) -> list[tuple[str, int, int, int]]:
    """MaxRects best-short-side fit with deterministic order retries and 1px gutters."""
    for seed in range(512):
        rng = random.Random(seed)
        items = sorted(rectangles, key=lambda item: (
            -(item[1] + 2) * (item[2] + 2) + rng.randrange(0, 10000),
            -max(item[1], item[2]), item[0]))
        free = [[(0, 0, SIDE, SIDE)] for _ in range(7)]
        placed: list[tuple[str, int, int, int]] = []
        failed = False
        for name, width, height in items:
            width += 1
            height += 1
            best = None
            for page, rects in enumerate(free):
                for x, y, fw, fh in rects:
                    if width <= fw and height <= fh:
                        score = (min(fw - width, fh - height), max(fw - width, fh - height),
                                 fw * fh - width * height, y, x, page)
                        if best is None or score < best[0]:
                            best = (score, page, x, y)
            if best is None:
                failed = True
                break
            _, page, x, y = best
            placed.append((name, page, x, y))
            split = []
            for fx, fy, fw, fh in free[page]:
                if x >= fx + fw or x + width <= fx or y >= fy + fh or y + height <= fy:
                    split.append((fx, fy, fw, fh))
                    continue
                if x > fx:
                    split.append((fx, fy, x - fx, fh))
                if x + width < fx + fw:
                    split.append((x + width, fy, fx + fw - x - width, fh))
                if y > fy:
                    split.append((fx, fy, fw, y - fy))
                if y + height < fy + fh:
                    split.append((fx, y + height, fw, fy + fh - y - height))
            unique = list(dict.fromkeys(split))
            free[page] = [rect for i, rect in enumerate(unique) if not any(
                i != j and rect[0] >= other[0] and rect[1] >= other[1] and
                rect[0] + rect[2] <= other[0] + other[2] and
                rect[1] + rect[3] <= other[1] + other[3]
                for j, other in enumerate(unique))]
        if not failed:
            return placed
    raise ValueError("Week 2 sprites do not fit the existing seven character pages")


def header_text(remapped: list[tuple[int, dict[str, int]]],
                bf_core: list[tuple[int, dict[str, int]]],
                bf_extras: list[dict[str, int]], frame_count: int) -> str:
    frame_map = [255] * frame_count
    for index, (frame_id, _) in enumerate(remapped):
        frame_map[frame_id] = index
    lines = [
        "/* Generated by repack_week2_detail.py; do not edit. */",
        "#ifndef WEEK2_BF_OVERLAY_DATA_H",
        "#define WEEK2_BF_OVERLAY_DATA_H",
        f"#define BOPEEBO_WEEK2_REPACKED_FRAME_COUNT {len(remapped)}u",
        "static const uint8_t bopeebo_week2_repacked_index[BOPEEBO_VISUAL_FRAME_COUNT] = {",
        "\t" + ",".join(f"{index}u" for index in frame_map) + ",", "};",
        "static const uint16_t bopeebo_week2_repacked_source_frames[BOPEEBO_WEEK2_REPACKED_FRAME_COUNT] = {",
        "\t" + ",".join(f"{frame_id}u" for frame_id, _ in remapped) + ",", "};",
        "static const BopeeboVisualFrame bopeebo_week2_repacked_frames[BOPEEBO_WEEK2_REPACKED_FRAME_COUNT] = {",
    ]
    for _, frame in remapped:
        lines.append(f"\t{{{frame['page']}u, {frame['palette']}u, {frame['u']}u, {frame['v']}u, {frame['w']}u, {frame['h']}u, 0, 0, 0}},")
    lines.extend(("};", f"#define BOPEEBO_WEEK2_BF_OVERLAY_COUNT {len(bf_core)}u",
        "static const uint16_t bopeebo_week2_bf_source_frames[BOPEEBO_WEEK2_BF_OVERLAY_COUNT] = {",
        "\t" + ",".join(f"{frame_id}u" for frame_id, _ in bf_core) + ",", "};",
        "static const BopeeboVisualFrame bopeebo_week2_bf_overlay_frames[BOPEEBO_WEEK2_BF_OVERLAY_COUNT] = {"))
    for _, frame in bf_core:
        lines.append(f"\t{{{frame['page']}u, 2u, {frame['u']}u, {frame['v']}u, {frame['w']}u, {frame['h']}u, 0, 0, 0}},")
    lines.extend(("};", "static const BopeeboVisualFrame bopeebo_week2_bf_sing_extra_frames[BOP