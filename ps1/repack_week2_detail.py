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
    lines.extend(("};", "static const BopeeboVisualFrame bopeebo_week2_bf_sing_extra_frames[BOPEEBO_BF_SING_EXTRA_COUNT] = {"))
    for frame in bf_extras:
        lines.append(f"\t{{{frame['page']}u, 2u, {frame['u']}u, {frame['v']}u, {frame['w']}u, {frame['h']}u, 0, 0, 0}},")
    lines.extend(("};", "#endif", ""))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=pathlib.Path)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--visual-header", required=True, type=pathlib.Path)
    parser.add_argument("--bf-pose-header", required=True, type=pathlib.Path)
    parser.add_argument("--week2-input", required=True, type=pathlib.Path)
    parser.add_argument("--output-header", required=True, type=pathlib.Path)
    parser.add_argument("--output-scene", required=True, type=pathlib.Path)
    args = parser.parse_args()

    visual_text = args.visual_header.read_text(encoding="ascii")
    all_frames, frame_ids, slots = parse_header(visual_text)
    frame_index_by_name = {name: index for index, (name, _) in enumerate(all_frames)}
    page_count = parse_count(visual_text, "BOPEEBO_WEEK2_PAGE_COUNT")
    stage_count = parse_count(visual_text, "BOPEEBO_WEEK2_STAGE_PAGE_COUNT")
    if len(slots) != page_count or page_count != 9 or stage_count != 2:
        raise ValueError("expected the validated nine-page Week 2 layout (two stage + seven character pages)")
    global_to_package = {global_page: package_page for package_page, global_page in enumerate(slots)}

    source_payload = args.week2_input.read_bytes()
    expected_size = page_count * PAGE_BYTES + 512
    if len(source_payload) != expected_size:
        raise ValueError(f"Week 2 payload is {len(source_payload)} bytes, expected {expected_size}")
    week2_palette = page_palette(source_payload)
    bf_palette = palette_from_header(visual_text)

    frame_by_name = dict(all_frames)
    week2_rows = [(name, frame) for name, frame in all_frames
                  if name.startswith("week2_") and frame["page"] in global_to_package and
                  global_to_package[frame["page"]] >= stage_count]
    if len(week2_rows) != 40:
        raise ValueError(f"expected 40 Week 2 character/icon descriptors, found {len(week2_rows)}")
    if any(name not in frame_by_name for name, _, _ in SPOOKY_SELECTION):
        raise ValueError("a Spooky Kids descriptor is missing")
    spooky_names = {name for name, _, _ in SPOOKY_SELECTION}

    # Existing Week 2 rasters are copied byte-for-byte except Spooky Kids.
    images: dict[str, tuple[bytes, int, int, int]] = {}
    for name, frame in week2_rows:
        source_page = global_to_package[frame["page"]]
        pixels = read_rect(source_payload, source_page, frame)
        width, height = frame["w"], frame["h"]
        if name in spooky_names:
            # Rebuild from the official source at 90% texture density using
            # the already-pinned Week 2 CLUT; don't regenerate or recolor it.
            continue
        images[name] = (pixels, width, height, frame["palette"])

    chars = args.assets / "shared/images/characters"
    spooky_groups = atlas_frames(chars / "SpookyKids.xml")
    spooky_png = chars / "SpookyKids.png"
    for name, group, source_index in SPOOKY_SELECTION:
        rows = spooky_groups.get(group, [])
        if source_index >= len(rows):
            raise ValueError(f"missing official SpookyKids frame {group}[{source_index}]")
        rgba = extract_sparrow_frame(args.ffmpeg, spooky_png, rows[source_index], SPOOKY_SIZE, resample="lanczos")
        images[name] = (bytes(quantize(rgba, week2_palette)), *SPOOKY_SIZE, 1)

    # Recreate the identical unique-id mapping used by the existing 52px
    # BF converter, then render those same source poses at 62px for Week 2.
    bf_groups = atlas_frames(chars / "BOYFRIEND.xml")
    bf_png = chars / "BOYFRIEND.png"
    idle_sources: list[int] = []
    idle_unique: dict[bytes, int] = {}
    for index, row in enumerate(bf_groups.get("BF idle dance", [])):
        old = extract_sparrow_frame(args.ffmpeg, bf_png, row, (52, 52))
        key = bytes(old)
        if key not in idle_unique:
            idle_unique[key] = index
        idle_sources.append(idle_unique[key])
    idle_unique_sources = [None] * len(idle_unique)
    seen: set[bytes] = set()
    for index, row in enumerate(bf_groups.get("BF idle dance", [])):
        key = bytes(extract_sparrow_frame(args.ffmpeg, bf_png, row, (52, 52)))
        if key not in seen:
            idle_unique_sources[len(seen)] = index
            seen.add(key)
    if len(idle_sources) != 14 or not idle_unique_sources:
        raise ValueError("BF idle deduplication no longer matches the current atlas layout")

    bf_core_sources: list[tuple[str, int, bytes]] = []
    for index, source_index in enumerate(idle_unique_sources):
        row = bf_groups["BF idle dance"][source_index]
        bf_core_sources.append((f"bf_idle_{index}", frame_ids.get(f"BF_IDLE_{index}", -1),
            bytes(quantize(extract_sparrow_frame(args.ffmpeg, bf_png, row, BF_SIZE, resample="lanczos"), bf_palette))))
    sing_sources: list[tuple[str, int, bytes]] = []
    extra_sources: list[bytes] = []
    for direction in BF_DIRECTIONS:
        rows = bf_groups.get(f"BF NOTE {direction.upper()}", [])
        if len(rows) < 3:
            raise ValueError(f"official BF {direction} animation has fewer than three poses")
        for pose, source_index in enumerate((0, (len(rows) - 1) // 2)):
            name = f"bf_{direction}_{pose}"
            frame_id = frame_ids.get(f"BF_{direction.upper()}_{pose}", -1)
            pixels = bytes(quantize(extract_sparrow_frame(args.ffmpeg, bf_png, rows[source_index], BF_SIZE, resample="lanczos"), bf_palette))
            sing_sources.append((name, frame_id, pixels))
        final = rows[-1]
        extra_sources.append(bytes(quantize(extract_sparrow_frame(args.ffmpeg, bf_png, final, BF_SIZE, resample="lanczos"), bf_palette)))
    bf_core_sources += sing_sources
    if len(bf_core_sources) != 13 or any(frame_id < 0 for _, frame_id, _ in bf_core_sources):
        raise ValueError("BF frame IDs differ from the existing 13-pose overlay interface")
    if parse_extras(args.bf_pose_header.read_text(encoding="ascii")) != 4:
        raise ValueError("BF extra pose layout changed")

    # Items include a one-pixel transparent gutter around each source rect.
    sizes = [(name, width, height) for name, (_, width, height, _) in images.items()]
    sizes += [(name, BF_SIZE[0], BF_SIZE[1]) for name, _, _ in bf_core_sources]
    sizes += [(f"bf_extra_{i}", BF_SIZE[0], BF_SIZE[1]) for i in range(4)]
    placements = pack_rectangles(sizes)
    placement_map = {name: (page, x, y) for name, page, x, y in placements}

    output = bytearray(source_payload)
    # Clear only the character pages. Static stage/lightning pages are kept.
    for package_page in range(stage_count, page_count):
        start = package_page * PAGE_BYTES
        output[start:start + PAGE_BYTES] = bytes(PAGE_BYTES)

    package_page_rows: dict[int, list[tuple[int, int, int, int, int, str]]] = {}
    for name, (pixels, width, height, palette_id) in images.items():
        package_page, x, y = placement_map[name]
        write_rect(output, package_page + stage_count, x, y, width, height, pixels)
        package_page_rows.setdefault(package_page + stage_count, []).append((x, y, width, height, palette_id, name))

    def write_bf(name: str, pixels: bytes) -> dict[str, int]:
        package_page, x, y = placement_map[name]
        write_rect(output, package_page + stage_count, x, y, BF_SIZE[0], BF_SIZE[1], pixels)
        package_page_rows.setdefault(package_page + stage_count, []).append((x, y, BF_SIZE[0], BF_SIZE[1], 2, name))
        return {"page": slots[package_page + stage_count], "palette": 2, "u": x, "v": y,
                "w": BF_SIZE[0], "h": BF_SIZE[1]}

    bf_core_rows = [(frame_id, write_bf(name, pixels)) for name, frame_id, pixels in bf_core_sources]
    bf_extra_rows = [write_bf(f"bf_extra_{i}", pixels) for i, pixels in enumerate(extra_sources)]

    # All descriptors (including aliases) point to the same newly packed set.
    remapped_by_name = {}
    for name, (_, width, height, palette_id) in images.items():
        page, x, y = placement_map[name]
        remapped_by_name[name] = {"page": slots[page + stage_count], "palette": palette_id,
                                  "u": x, "v": y, "w": width, "h": height}
    remapped_rows = [(frame_index_by_name[name], remapped_by_name[name]) for name in images]

    if len(set((p, x, y) for _, p, x, y in placements)) != len(placements):
        raise AssertionError("duplicate rectangle placement")
    for page, rows in package_page_rows.items():
        for i, (x, y, w, h, _, name) in enumerate(rows):
            if x + w > SIDE or y + h > SIDE:
                raise AssertionError(f"{name} exceeds its texture page")
            for ox, oy, ow, oh, _, other in rows[i + 1:]:
                if x < ox + ow and ox < x + w and y < oy + oh and oy < y + h:
                    raise AssertionError(f"packed rectangles overlap: {name} and {other}")
    if output[-512:] != source_payload[-512:]:
        raise AssertionError("Week 2 CLUT changed")

    args.output_scene.parent.mkdir(parents=True, exist_ok=True)
    args.output_header.parent.mkdir(parents=True, exist_ok=True)
    args.output_scene.write_bytes(output)
    args.output_header.write_text(header_text(remapped_rows, bf_core_rows, bf_extra_rows,
                                              len(all_frames)),
                                  encoding="ascii", newline="\n")
    print(f"Packed {len(images)} Week 2 sprites + 17 BF cels into the existing seven character pages")
    print("Spooky Kids: 85x100 -> 76x90 texture; display 72x84 -> 65x76. BF: 52x52 -> 62x62 texture; remains 52x52 displayed.")
    print(f"Package remains {len(output)} bytes; 9 pages and the existing Week 2 CLUT are unchanged.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Week 2 detail repack failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
