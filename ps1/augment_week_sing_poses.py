#!/usr/bin/env python3
"""Add sampled player singing poses to the existing Week 6, 7 and Weekend 1 packs.

This narrow post-converter keeps each existing CLUT and all existing indexed
pixels intact. Week 6 and Weekend 1 use free areas in their current pages;
Week 7 appends one character page because its original character page is full.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from animate_preview import Rig  # noqa: E402
from convert_bopeebo_visuals import (  # noqa: E402
    extract_sparrow_frame, fit_anchored_rig, quantize,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE
DIRECTIONS = ("LEFT", "DOWN", "UP", "RIGHT")


def palette_from_scene(scene: bytes) -> list[tuple[int, int, int]]:
    if len(scene) < 512 or len(scene) % PAGE_BYTES != 512:
        raise ValueError(f"unexpected page+CLUT scene size: {len(scene)} bytes")
    words = struct.unpack_from("<256H", scene, len(scene) - 512)
    if words[0] != 0:
        raise ValueError("expected transparent CLUT entry at index zero")
    colors = []
    for word in words[1:]:
        colors.append(tuple((((word >> shift) & 31) << 3) | (((word >> shift) & 31) >> 2)
                            for shift in (0, 5, 10)))
    return colors


def indexed_blit(page: bytearray, x: int, y: int, width: int, height: int,
                 rgba: bytearray, palette: list[tuple[int, int, int]]) -> None:
    if x < 0 or y < 0 or x + width > PAGE or y + height > PAGE:
        raise ValueError(f"pose rectangle outside texture page: {x},{y} {width}x{height}")
    pixels = quantize(rgba, palette)
    for row in range(height):
        start = row * width
        dst = (y + row) * PAGE + x
        page[dst:dst + width] = pixels[start:start + width]


def source_frames(xml_path: pathlib.Path, prefix: str) -> list[dict[str, int | str | bool]]:
    matches = []
    for node in ET.parse(xml_path).getroot().findall("SubTexture"):
        if not node.attrib.get("name", "").startswith(prefix):
            continue
        frame: dict[str, int | str | bool] = {
            key: int(node.attrib.get(key, 0)) for key in
            ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")
        }
        frame["rotated"] = node.attrib.get("rotated", "false").lower() == "true"
        frame["name"] = node.attrib["name"]
        matches.append(frame)
    if not matches:
        raise ValueError(f"no official Sparrow poses match {prefix!r} in {xml_path}")
    return matches


def append_header_frames(header: str, *, guard_prefix: str, page_count_macro: str,
                         visual_count_macro: str, old_page_count: int, extra_names: list[str],
                         descriptors: list[tuple[int, int, int, int, int]],
                         page_count_after: int | None = None) -> str:
    count_macro = f"#define {visual_count_macro} "
    count_match = re.search(re.escape(count_macro) + r"(\d+)u", header)
    if not count_match:
        raise ValueError(f"missing {guard_prefix} visual frame count")
    old_count = int(count_match.group(1))
    enum_end = header.find("\n};", header.find("enum {"))
    table_start = header.find("static const", enum_end)
    table_end = header.find("\n};", table_start)
    if enum_end < 0 or table_start < 0 or table_end < 0:
        raise ValueError(f"cannot locate {guard_prefix} frame enum/table")
    enum_lines = "".join(f"\t{guard_prefix}_FRAME_{name} = {old_count + i},\n"
                          for i, name in enumerate(extra_names))
    header = header[:enum_end] + "\n" + enum_lines.rstrip("\n") + header[enum_end:]
    # Locate the table again after extending the enum.
    table_start = header.find("static const", header.find("enum {"))
    table_end = header.find("\n};", table_start)
    descriptor_lines = "".join(
        f"\t{{ {page}u, {x}u, {y}u, {w}u, {h}u }}, /* {name} */\n"
        for name, (page, x, y, w, h) in zip(extra_names, descriptors)
    )
    header = header[:table_end] + "\n" + descriptor_lines.rstrip("\n") + header[table_end:]
    header = re.sub(re.escape(count_macro) + r"\d+u",
                    f"{count_macro}{old_count + len(extra_names)}u", header, count=1)
    if page_count_after is not None:
        page_macro = f"#define {page_count_macro} {old_page_count}u"
        if page_macro not in header:
            raise ValueError(f"expected exact page count line {page_macro!r}")
        header = header.replace(page_macro,
                                f"#define {page_count_macro} {page_count_after}u", 1)
    return header


def week6(args: argparse.Namespace) -> None:
    # Pixel BF's atlas is shared by the pinned classic Week 6 converter.
    png = args.assets / "shared/images/characters/bfPixel.png"
    xml = args.assets / "shared/images/characters/bfPixel.xml"
    scene_path = args.week6 / "week6-scene.bin"
    header_path = args.week6 / "week6_visual_data.h"
    scene = bytearray(scene_path.read_bytes())
    if len(scene) != 5 * PAGE_BYTES + 512:
        raise ValueError("Week 6 base must remain five pages plus its 8bpp CLUT")
    palette = palette_from_scene(scene)
    page = bytearray(scene[4 * PAGE_BYTES:5 * PAGE_BYTES])
    coords = ((0, 128), (64, 128), (128, 128), (192, 128),
              (0, 192), (64, 192), (128, 192), (192, 192))
    names: list[str] = []
    descriptors = []
    for lane, direction in enumerate(DIRECTIONS):
        frames = source_frames(xml, f"BF {direction} NOTE instance 10")
        unique_frames = []
        seen_rects = set()
        for frame in frames:
            rect = tuple(int(frame[key]) for key in ("x", "y", "width", "height"))
            if rect not in seen_rects:
                seen_rects.add(rect)
                unique_frames.append(frame)
        frames = unique_frames
        if len(frames) < 2:
            raise ValueError(f"BF Pixel {direction} has too few official frames")
        middle_index = (len(frames) - 1) // 2
        final_index = len(frames) - 1
        if middle_index == final_index:
            raise ValueError(f"BF Pixel {direction} has no distinct end pose")
        for sample, source_index in (("MID", middle_index), ("END", final_index)):
            frame_name = f"BF_{direction}_{sample}"
            x, y = coords[len(names)]
            rgba = extract_sparrow_frame(args.ffmpeg, png, frames[source_index], (64, 64))
            indexed_blit(page, x, y, 64, 64, rgba, palette)
            names.append(frame_name)
            descriptors.append((4, x, y, 64, 64))
    scene[4 * PAGE_BYTES:5 * PAGE_BYTES] = page
    scene_path.write_bytes(scene)
    header = header_path.read_text(encoding="ascii")
    header = append_header_frames(header, guard_prefix="WEEK6", page_count_macro="BOPEEBO_WEEK6_PAGE_COUNT",
                                  visual_count_macro="WEEK6_VISUAL_FRAME_COUNT",
                                  old_page_count=5, extra_names=names, descriptors=descriptors)
    header_path.write_text(header, encoding="ascii")
    print(f"Week 6: patched eight BF samples into existing page 4; scene remains {len(scene)} bytes")


def rig_samples(rig: Rig, child_name: str) -> tuple[int, int]:
    """Return the first frame and a distinct later image in the official span."""
    root = rig.animation["AN"]["TL"]
    spans = []
    for layer in root.get("L", []):
        for key in layer.get("FR", []):
            for event in key.get("E", []):
                symbol = event.get("SI", {}).get("SN")
                if symbol == child_name:
                    start = int(key.get("I", 0))
                    duration = int(key.get("DU", 1))
                    spans.append((start, duration))
    if not spans:
        raise ValueError(f"missing official rig timeline span {child_name!r}")
    start, duration = spans[0]
    if duration < 3:
        raise ValueError(f"official timeline span {child_name!r} is shorter than three frames")
    candidates = (start, start + (duration - 1) // 2, start + duration - 1)
    hashes = []
    for frame in candidates:
        *_, pixels = rig.render_positioned(frame, 1200)
        hashes.append(hashlib.sha256(pixels).digest())
    if hashes[1] != hashes[0]:
        return start, candidates[1]
    if hashes[2] != hashes[0]:
        return start, candidates[2]
    raise ValueError(f"official timeline {child_name!r} has no distinct later singing pose")


def week7(args: argparse.Namespace) -> None:
    scene_path = args.week7 / "week7-scene.bin"
    header_path = args.week7 / "week7_visual_data.h"
    scene = scene_path.read_bytes()
    if len(scene) != 3 * PAGE_BYTES + 512:
        raise ValueError("Week 7 base must remain three pages plus its 8bpp CLUT")
    palette = palette_from_scene(scene)
    rig = Rig(args.assets / "shared/images/characters/bf", args.ffmpeg)
    directions = {"LEFT": "BF NOTE LEFT", "RIGHT": "BF NOTE RIGHT",
                  "UP": "BF NOTE UP", "DOWN": "BF NOTE DOWN"}
    old_indices = {"LEFT": 14, "DOWN": 140, "UP": 109, "RIGHT": 56}
    new_indices: list[tuple[str, int]] = []
    for direction in DIRECTIONS:
        sampled = rig_samples(rig, directions[direction])
        if sampled[0] != old_indices[direction]:
            raise ValueError(f"Week 7 {direction} official start changed: {sampled[0]}")
        new_indices.append((f"BF_{direction}_ALT", sampled[1]))
    all_indices = [0, *old_indices.values(), *(frame for _, frame in new_indices)]
    fitted = fit_anchored_rig(rig, all_indices, 64, 64,
                              anchor_frame_ids=[0, *old_indices.values()])
    page = bytearray(PAGE_BYTES)
    names = [name for name, _ in new_indices]
    descriptors = []
    for index, (name, source_index) in enumerate(new_indices):
        x, y = (index % 4) * 64, (index // 4) * 64
        indexed_blit(page, x, y, 64, 64, fitted[source_index], palette)
        descriptors.append((3, x, y, 64, 64))
    # Insert the new page before the original CLUT; preserve all original pages
    # and CLUT bytes bit-for-bit.
    extended_scene = scene[:3 * PAGE_BYTES] + bytes(page) + scene[3 * PAGE_BYTES:]
    scene_path.write_bytes(extended_scene)
    header = header_path.read_text(encoding="ascii")
    header = append_header_frames(header, guard_prefix="WEEK7", page_count_macro="BOPEEBO_WEEK7_PAGE_COUNT",
                                  visual_count_macro="WEEK7_VISUAL_FRAME_COUNT",
                                  old_page_count=3, extra_names=names, descriptors=descriptors,
                                  page_count_after=4)
    header_path.write_text(header, encoding="ascii")
    print(f"Week 7: added page 3 with four BF alternate poses; scene grew to {len(extended_scene)} bytes")


def weekend1(args: argparse.Namespace) -> None:
    scene_path = args.weekend1 / "weekend1-scene.bin"
    header_path = args.weekend1 / "weekend1_visual_data.h"
    scene = bytearray(scene_path.read_bytes())
    if len(scene) != 8 * PAGE_BYTES + 512:
        raise ValueError("Weekend 1 base must remain eight pages plus its 8bpp CLUT")
    palette = palette_from_scene(scene)
    rig = Rig(args.assets / "shared/images/characters/pico/basic-animations", args.ffmpeg)
    direction_symbols = {"LEFT": "Pico NOTE LEFT", "DOWN": "Pico Down Note",
                         "UP": "pico Up note", "RIGHT": "Pico Note Right"}
    old_indices = {"LEFT": 14, "RIGHT": 31, "UP": 48, "DOWN": 62}
    new_indices: list[tuple[str, int]] = []
    for direction in DIRECTIONS:
        sampled = rig_samples(rig, direction_symbols[direction])
        if sampled[0] != old_indices[direction]:
            raise ValueError(f"Weekend 1 Pico {direction} official start changed: {sampled[0]}")
        new_indices.append((f"PICO_{direction}_ALT", sampled[1]))
    all_indices = [0, *old_indices.values(), *(frame for _, frame in new_indices)]
    fitted = fit_anchored_rig(rig, all_indices, 64, 80,
                              anchor_frame_ids=[0, *old_indices.values()])
    # Page 7 contains two 64x64 portraits at (0,0) and (64,0). Its remaining
    # texels hold eight aligned 64x80 cels without changing page count/CLUT.
    coords = ((128, 0), (192, 0), (0, 80), (64, 80))
    page_offset = 7 * PAGE_BYTES
    page = bytearray(scene[page_offset:page_offset + PAGE_BYTES])
    names = [name for name, _ in new_indices]
    descriptors = []
    for index, (name, source_index) in enumerate(new_indices):
        x, y = coords[index]
        indexed_blit(page, x, y, 64, 80, fitted[source_index], palette)
        descriptors.append((7, x, y, 64, 80))
    scene[page_offset:page_offset + PAGE_BYTES] = page
    scene_path.write_bytes(scene)
    header = header_path.read_text(encoding="ascii")
    header = append_header_frames(header, guard_prefix="WEND", page_count_macro="BOPEEBO_WEEKEND1_PAGE_COUNT",
                                  visual_count_macro="WEEKEND1_VISUAL_FRAME_COUNT",
                                  old_page_count=8, extra_names=names, descriptors=descriptors)
    header_path.write_text(header, encoding="ascii")
    print(f"Weekend 1: patched four Pico alternate poses into page 7; scene remains {len(scene)} bytes")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", type=pathlib.Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--week6", type=pathlib.Path, required=True)
    ap.add_argument("--week7", type=pathlib.Path, required=True)
    ap.add_argument("--weekend1", type=pathlib.Path, required=True)
    args = ap.parse_args()
    # Refuse to patch an already augmented or partial package. Validate all
    # inputs before the first write so a rerun cannot append duplicate tables.
    expected = (
        (args.week6, "week6-scene.bin", "week6_visual_data.h", 5 * PAGE_BYTES + 512),
        (args.week7, "week7-scene.bin", "week7_visual_data.h", 3 * PAGE_BYTES + 512),
        (args.weekend1, "weekend1-scene.bin", "weekend1_visual_data.h", 8 * PAGE_BYTES + 512),
    )
    for directory, scene_name, header_name, scene_size in expected:
        scene = directory / scene_name
        header = directory / header_name
        if not scene.is_file() or scene.stat().st_size != scene_size:
            raise ValueError(f"{scene} must be an unaugmented {scene_size}-byte package")
        if not header.is_file() or "_ALT =" in header.read_text(encoding="ascii"):
            raise ValueError(f"{header} is missing or already contains sampled-pose additions")
    week6(args)
    week7(args)
    weekend1(args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI diagnostic
        print(f"Week singing-pose augmentation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
