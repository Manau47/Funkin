#!/usr/bin/env python3
"""Patch only the Week 5 background pages to match official stage transforms.

All character/prop pages, catalogs, charts, and audio are copied unchanged
from the v171 package. The backgrounds preserve their source aspect ratio;
runtime positions/scales are handled by spu_probe.c using mallXmas/mallEvil.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from convert_bopeebo_visuals import median_palette, quantize, rgb555, run_ffmpeg  # noqa: E402

PAGE = 256
PAGE_BYTES = PAGE * PAGE
CLUT_BYTES = 512


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-package", type=pathlib.Path, required=True)
    parser.add_argument("--assets", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    args = parser.parse_args()

    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    shutil.copytree(args.base_package, args.output)
    scene_path = args.output / "week5-scene.bin"
    header_path = args.output / "week5_visual_data.h"
    scene = bytearray(scene_path.read_bytes())
    header = header_path.read_text(encoding="ascii")
    page_count_match = re.search(r"#define BOPEEBO_WEEK5_PAGE_COUNT (\d+)u", header)
    if not page_count_match:
        raise ValueError("page count missing from base header")
    page_count = int(page_count_match.group(1))
    if len(scene) != page_count * PAGE_BYTES + page_count * CLUT_BYTES:
        raise ValueError("unexpected Week 5 package layout")

    source_dir = args.assets / "week5" / "images" / "christmas"
    layers = ((0, "STAGE_XMAS", "bgWalls.png", 3102, 1840, 0.8),
              (1, "STAGE_EVIL", "evilBG.png", 2625, 1613, 0.8))
    for page_index, name, filename, source_w, source_h, stage_scale in layers:
        out_w = PAGE
        out_h = max(1, round(source_h * out_w / source_w))
        rgba = run_ffmpeg(args.ffmpeg, source_dir / filename,
                          f"scale={out_w}:{out_h}:flags=area,setsar=1", out_w, out_h)
        rgba_page = bytearray(PAGE_BYTES * 4)
        for row in range(out_h):
            rgba_page[row * PAGE * 4:row * PAGE * 4 + out_w * 4] = rgba[row * out_w * 4:(row + 1) * out_w * 4]
        palette = median_palette([rgba_page], 255)
        indexed = quantize(rgba_page, palette)
        scene[page_index * PAGE_BYTES:(page_index + 1) * PAGE_BYTES] = indexed
        words = [0] + [rgb555(color) for color in palette[:255]]
        words += [0] * (256 - len(words))
        clut_offset = page_count * PAGE_BYTES + page_index * CLUT_BYTES
        scene[clut_offset:clut_offset + CLUT_BYTES] = struct.pack("<256H", *words)

        # Preserve the official top-left anchor while changing the frame's
        # source rectangle to the fitted, undistorted 16:9-ish dimensions.
        pattern = (rf"(\{{\s*{page_index}u,\s*0u,\s*0u,\s*256u,\s*)\d+u"
                   rf"(,\s*0,\s*0\s*\}},\s*/\* {name} \*/)" )
        header, count = re.subn(pattern, rf"\g<1>{out_h}u\g<2>", header)
        if count != 1:
            raise ValueError(f"could not update {name} frame dimensions in header")
        print(f"{name}: {source_w}x{source_h} -> {out_w}x{out_h}, stage scale {stage_scale}")

    header = header.replace("rebuild_week5_v171_assets.py", "patch_week5_background_v172.py")
    scene_path.write_bytes(scene)
    header_path.write_text(header, encoding="ascii", newline="\n")
    print(f"patched only background pages 0/1; {len(scene)} bytes; other package files copied byte-for-byte")


if __name__ == "__main__":
    main()
