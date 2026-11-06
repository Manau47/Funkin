#!/usr/bin/env python3
"""Rebuild only the Week 2 static backdrop tiles in a copied asset package."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import shutil
import struct

from animate_preview import Rig
from convert_bopeebo_visuals import (
    PAGE_H,
    PAGE_W,
    WEEK2_STAGE_DIVISOR,
    alpha_over,
    nearest_palette_index,
    run_ffmpeg,
)


PAGE_BYTES = PAGE_W * PAGE_H
SCENE_TILE_W = 256


def decode_palette(payload: bytes) -> list[tuple[int, int, int]]:
    if len(payload) != 7 * PAGE_BYTES + 512:
        raise ValueError(f"unexpected Week 2 payload size: {len(payload)}")
    words = struct.unpack_from("<256H", payload, 7 * PAGE_BYTES)
    return [tuple((((word >> shift) & 31) * 255 + 15) // 31
                  for shift in (0, 5, 10)) for word in words[1:]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=pathlib.Path)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--base", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output directory: {args.output}")
    names = ("bopeebo_visual_data.h", "week1-scene.bin", "week2-scene.bin", "week3-scene.bin")
    for name in names:
        if not (args.base / name).is_file():
            raise SystemExit(f"missing reusable converted file: {args.base / name}")

    assets = args.assets
    stage = json.loads((assets / "preload/data/stages/spookyMansion.json").read_text(encoding="utf-8"))
    prop = next(p for p in stage["props"] if p["name"] == "halloweenBG")
    atlas = json.loads((assets / "week2/images/halloween_bg/spritemap1.json").read_text(encoding="utf-8"))["ATLAS"]
    sprite = next(item["SPRITE"] for item in atlas["SPRITES"] if item["SPRITE"].get("name") == "0")
    width = max(1, round(int(sprite["w"]) / WEEK2_STAGE_DIVISOR))
    raw_height = max(1, round(int(sprite["h"]) / WEEK2_STAGE_DIVISOR))
    height = min(raw_height, PAGE_H)
    crop_y = (raw_height - height) // 2

    png = assets / "week2/images/halloween_bg/spritemap1.png"
    background = run_ffmpeg(args.ffmpeg, png,
        f"crop={sprite['w']}:{sprite['h']}:{sprite['x']}:{sprite['y']},"
        f"scale={width}:{raw_height}:flags=area,crop={width}:{height}:0:{crop_y}", width, height)

    rig = Rig(assets / "week2/images/halloween_bg", args.ffmpeg)
    root = rig.animation["AN"].get("STI", {}).get("SI", {})
    matrix = tuple(root.get("MX", (1, 0, 0, 1, 0, 0)))
    scale = 1.0 / WEEK2_STAGE_DIVISOR
    root_dx = math.floor(matrix[4] * scale + 0.5)
    root_dy = math.floor(matrix[5] * scale + 0.5)

    # Recreate the converter's base fill and root-transformed Sprite 0.
    canvas = bytearray(width * height * 4)
    for offset in range(0, len(canvas), 4):
        canvas[offset:offset + 4] = bytes((36, 35, 54, 255))
    shifted = bytearray(width * height * 4)
    for sy in range(height):
        dy = sy + root_dy
        if not 0 <= dy < height:
            continue
        for sx in range(width):
            dx = sx + root_dx
            if 0 <= dx < width:
                src = (sy * width + sx) * 4
                dst = (dy * width + dx) * 4
                shifted[dst:dst + 4] = background[src:src + 4]
    canvas = alpha_over(canvas, shifted)

    # Bake the permanent Animate stage layers with only the transient flash
    # removed, exactly as the main converter does.
    render_matrix = (scale, 0, 0, scale, matrix[4] * scale, matrix[5] * scale - crop_y)
    decor = bytearray(width * height * 4)
    lightning = rig.symbols["halloweem bg lightning strike"]
    original_layers = lightning["TL"]["L"]
    lightning["TL"]["L"] = [layer for layer in original_layers if layer.get("LN") != "flash"]
    try:
        rig.walk(rig.animation["AN"]["N"], 30, render_matrix, (width, height, decor))
    finally:
        lightning["TL"]["L"] = original_layers
    canvas = alpha_over(canvas, decor)

    source_payload = (args.base / "week2-scene.bin").read_bytes()
    colors = decode_palette(source_payload)
    payload = bytearray(source_payload)
    source_hash = hashlib.sha256(source_payload).hexdigest().upper()
    for tile, x0 in enumerate((0, SCENE_TILE_W)):
        tile_width = min(SCENE_TILE_W, width - x0)
        if tile_width <= 0:
            raise ValueError(f"missing source width for scene tile {tile}")
        page_base = tile * PAGE_BYTES
        for y in range(height):
            for x in range(tile_width):
                src = ((y * width + x0 + x) * 4)
                if canvas[src + 3] < 128:
                    value = 0
                else:
                    value = nearest_palette_index(tuple(canvas[src:src + 3]), colors)
                payload[page_base + y * PAGE_W + x] = value

    args.output.mkdir(parents=True)
    for child in args.base.iterdir():
        destination = args.output / child.name
        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)
    (args.output / "week2-scene.bin").write_bytes(payload)

    changed = [p.name for p in args.base.iterdir()
               if p.is_file() and p.name != "week2-scene.bin" and
               hashlib.sha256(p.read_bytes()).digest() != hashlib.sha256((args.output / p.name).read_bytes()).digest()]
    if changed:
        raise ValueError(f"unexpected modified converted files: {changed}")
    print(f"Static Week 2 backdrop rebuilt: {width}x{height}; Sprite 0 compositing retained.")
    print(f"Existing palette reused unchanged; other converted files copied unchanged.")
    print(f"week2-scene.bin SHA-256: {source_hash} -> {hashlib.sha256(payload).hexdigest().upper()}")
    print(f"Copied package: {args.output}")


if __name__ == "__main__":
    main()
