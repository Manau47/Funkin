#!/usr/bin/env python3
"""Patch only the Week 2 lightning crops in an existing converted asset set."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import struct
import sys

from animate_preview import Rig
from convert_bopeebo_visuals import (
    PAGE_H,
    PAGE_W,
    WEEK2_LIGHTNING_CROP,
    WEEK2_LIGHTNING_TEX_H,
    WEEK2_LIGHTNING_TEX_W,
    WEEK2_STAGE_DIVISOR,
    fit_nearest,
    nearest_palette_index,
    png_size,
)


def decode_palette(payload: bytes) -> list[tuple[int, int, int]]:
    if len(payload) < 512:
        raise ValueError("Week 2 package is missing its 256-entry RGB555 palette")
    words = struct.unpack_from("<256H", payload, len(payload) - 512)
    colors = []
    for word in words[1:]:  # palette entry zero is transparent on PS1
        rgb5 = (word & 31, (word >> 5) & 31, (word >> 10) & 31)
        colors.append(tuple((channel * 255 + 15) // 31 for channel in rgb5))
    return colors


def update_macro(header: str, name: str, value: int) -> str:
    pattern = rf"(^#define {re.escape(name)} \()(-?\d+)(\)$)"
    updated, count = re.subn(pattern, rf"\g<1>{value}\g<3>", header, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"expected exactly one {name} macro, found {count}")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=pathlib.Path,
                        help="root of the pinned official assets checkout")
    parser.add_argument("--ffmpeg", required=True,
                        help="FFmpeg executable used by the Animate renderer")
    parser.add_argument("--base", required=True, type=pathlib.Path,
                        help="preconverted base directory to copy without modifying")
    parser.add_argument("--output", required=True, type=pathlib.Path,
                        help="new directory for the patched header and payload")
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output directory: {args.output}")
    visual_files = ("bopeebo_visual_data.h", "week1-scene.bin", "week2-scene.bin", "week3-scene.bin")
    for name in visual_files:
        if not (args.base / name).is_file():
            raise SystemExit(f"missing base asset: {args.base / name}")

    atlas_json = args.assets / "week2/images/halloween_bg/spritemap1.json"
    atlas = json.loads(atlas_json.read_text(encoding="utf-8"))["ATLAS"]
    sprite = next(entry["SPRITE"] for entry in atlas["SPRITES"]
                  if entry["SPRITE"].get("name") == "0")
    raw_h = max(1, round(int(sprite["h"]) / WEEK2_STAGE_DIVISOR))
    scene_w = max(1, round(int(sprite["w"]) / WEEK2_STAGE_DIVISOR))
    scene_h = min(raw_h, PAGE_H)
    crop_y = (raw_h - scene_h) // 2
    x0, y0, x1, y1 = WEEK2_LIGHTNING_CROP
    crop_w, crop_h = x1 - x0, y1 - y0
    if x0 < 0 or y0 < 0 or x1 > scene_w or y1 > scene_h:
        raise SystemExit(f"lightning crop {WEEK2_LIGHTNING_CROP} exceeds {scene_w}x{scene_h}")

    payload = bytearray((args.base / "week2-scene.bin").read_bytes())
    page_bytes = PAGE_W * PAGE_H
    if len(payload) != 7 * page_bytes + 512:
        raise SystemExit(f"unexpected Week 2 payload size: {len(payload)}")
    palette = decode_palette(payload)

    rig = Rig(args.assets / "week2/images/halloween_bg", args.ffmpeg)
    root = rig.animation["AN"].get("STI", {}).get("SI", {})
    matrix = tuple(root.get("MX", (1, 0, 0, 1, 0, 0)))
    scale = 1.0 / WEEK2_STAGE_DIVISOR
    render_matrix = (scale, 0, 0, scale,
                     matrix[4] * scale, matrix[5] * scale - crop_y)
    page1 = page_bytes  # Week 2 stage page 1; the right strip is reserved for lightning.
    page_x = 112

    for index, source_frame in enumerate((0, 1, 2)):
        full = bytearray(scene_w * scene_h * 4)
        rig.walk(rig.animation["AN"]["N"], source_frame, render_matrix,
                 (scene_w, scene_h, full))
        crop = bytearray(crop_w * crop_h * 4)
        for y in range(crop_h):
            src = ((y0 + y) * scene_w + x0) * 4
            dst = y * crop_w * 4
            crop[dst:dst + crop_w * 4] = full[src:src + crop_w * 4]
        fitted = fit_nearest(crop, crop_w, crop_h,
                             WEEK2_LIGHTNING_TEX_W, WEEK2_LIGHTNING_TEX_H)
        indices = bytearray(WEEK2_LIGHTNING_TEX_W * WEEK2_LIGHTNING_TEX_H)
        for pixel in range(len(indices)):
            off = pixel * 4
            if fitted[off + 3] >= 128:
                rgb = tuple(fitted[off:off + 3])
                indices[pixel] = nearest_palette_index(rgb, palette)
        page_y = index * (WEEK2_LIGHTNING_TEX_H + 1)
        for y in range(WEEK2_LIGHTNING_TEX_H):
            src = y * WEEK2_LIGHTNING_TEX_W
            dst = page1 + (page_y + y) * PAGE_W + page_x
            payload[dst:dst + WEEK2_LIGHTNING_TEX_W] = indices[src:src + WEEK2_LIGHTNING_TEX_W]

    # Translate the cropped textures to the same world coordinates as the
    # corresponding source pixels in the permanent stage image.
    base_header = (args.base / "bopeebo_visual_data.h").read_text(encoding="utf-8")
    stage_x = int(re.search(r"^#define BOPEEBO_WEEK2_STAGE_X \((-?\d+)\)$", base_header, re.M).group(1))
    stage_y = int(re.search(r"^#define BOPEEBO_WEEK2_STAGE_Y \((-?\d+)\)$", base_header, re.M).group(1))
    header = update_macro(base_header, "BOPEEBO_WEEK2_LIGHTNING_X", stage_x + x0)
    header = update_macro(header, "BOPEEBO_WEEK2_LIGHTNING_Y", stage_y + y0)

    args.output.mkdir(parents=True)
    for child in args.base.iterdir():
        destination = args.output / child.name
        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)
    (args.output / "week2-scene.bin").write_bytes(payload)
    (args.output / "bopeebo_visual_data.h").write_text(header, encoding="utf-8", newline="")
    print(f"Patched only three Week 2 lightning crops ({crop_w}x{crop_h} -> "
          f"{WEEK2_LIGHTNING_TEX_W}x{WEEK2_LIGHTNING_TEX_H}); preserved all other converted files.")
    print(f"Stage {scene_w}x{scene_h}, source crop {WEEK2_LIGHTNING_CROP}, "
          f"world origin ({stage_x + x0}, {stage_y + y0}); output {args.output}")


if __name__ == "__main__":
    main()
