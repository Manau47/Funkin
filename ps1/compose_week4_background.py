#!/usr/bin/env python3
"""Rebuild the Week 4 scenery pages from the pinned official Limo assets.

The existing W4 atlas, CLUT, character frames, charts and audio are preserved.
Only the two stage pages are replaced. New scenery is quantized against the
existing W4 CLUT, so character palette indices and animation metadata do not
change. This is an integration pass for the accepted Mother composition v7.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from convert_bopeebo_visuals import (  # noqa: E402
    blend_at, extract_menu_cover, extract_sparrow_frame, quantize, run_ffmpeg,
)
from animate_preview import save_png  # noqa: E402

PAGE = 256
PAGE_BYTES = PAGE * PAGE
STAGE_X = -64
STAGE_Y = 0
ZOOM_Q8 = 524


def first_sparrow(xml_path: pathlib.Path, prefix: str) -> dict[str, object]:
    root = ET.parse(xml_path).getroot()
    node = next((n for n in root.findall("SubTexture")
                 if n.attrib.get("name", "").startswith(prefix)), None)
    if node is None:
        raise ValueError(f"Missing {prefix!r} frame in {xml_path}")
    return {
        "x": int(node.attrib["x"]), "y": int(node.attrib["y"]),
        "width": int(node.attrib["width"]), "height": int(node.attrib["height"]),
        "frameX": int(node.attrib.get("frameX", 0)),
        "frameY": int(node.attrib.get("frameY", 0)),
        "frameWidth": int(node.attrib.get("frameWidth", node.attrib["width"])),
        "frameHeight": int(node.attrib.get("frameHeight", node.attrib["height"])),
        "rotated": node.attrib.get("rotated", "false").lower() == "true",
        "name": node.attrib.get("name", prefix),
    }


def palette_rgb555(data: bytes) -> list[tuple[int, int, int]]:
    words = struct.unpack("<256H", data)
    result = []
    for word in words[1:]:
        channels = (word & 31, (word >> 5) & 31, (word >> 10) & 31)
        result.append(tuple((channel << 3) | (channel >> 2) for channel in channels))
    return result


def world_pixel(screen_coord: int, screen_center: int) -> int:
    return screen_center + (screen_coord - screen_center) * 256 // ZOOM_Q8


def to_stage(screen_x: int, screen_y: int) -> tuple[int, int]:
    return (world_pixel(screen_x, 160) - STAGE_X,
            world_pixel(screen_y, 120) - STAGE_Y)


def rgba_for_indexed(page: bytes, clut: list[tuple[int, int, int]]) -> bytearray:
    out = bytearray(PAGE_BYTES * 4)
    for i, index in enumerate(page):
        if index:
            r, g, b = clut[index - 1]
            off = i * 4
            out[off:off + 4] = bytes((r, g, b, 255))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", type=pathlib.Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--input-dir", type=pathlib.Path, required=True,
                    help="immutable Week 4 preconverted atlas directory")
    ap.add_argument("--output-dir", type=pathlib.Path, required=True,
                    help="new directory; existing output is refused")
    ap.add_argument("--header", type=pathlib.Path, required=True)
    ap.add_argument("--scene", type=pathlib.Path, required=True)
    args = ap.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output_dir}")

    source_package = args.input_dir / args.scene
    source_header = args.input_dir / args.header
    raw = source_package.read_bytes()
    text = source_header.read_text(encoding="utf-8")
    match = re.search(r"(?m)^#define\s+BOPEEBO_WEEK4_PAGE_COUNT\s+(\d+)u\s*$", text)
    if not match:
        raise ValueError("Week 4 page count is missing from the visual header")
    page_count = int(match.group(1))
    if len(raw) != page_count * PAGE_BYTES + 512:
        raise ValueError(f"Unexpected package size {len(raw)} for {page_count} pages")
    palette_bytes = raw[page_count * PAGE_BYTES:]
    palette = palette_rgb555(palette_bytes)

    limo_root = args.assets / "week4/images/limo"
    stage = extract_menu_cover(args.ffmpeg, limo_root / "limoSunset.png", 512, 256)

    # Convert v7 screen-space coordinates to the current W4 world tile. These
    # values produce the approved x=-38/y=65 distant limo and four dancers at
    # 320x240 under the existing 524/256 camera zoom. The first-plane limo
    # retains its existing source frame, size, and world placement.
    bg_limo = extract_sparrow_frame(
        args.ffmpeg, limo_root / "bgLimo.png",
        first_sparrow(limo_root / "bgLimo.xml", "background limo pink"),
        (222, 39))
    x, y = to_stage(-38, 65)
    blend_at(stage, (512, 256), bg_limo, (222, 39), (x, y))

    hench = extract_sparrow_frame(
        args.ffmpeg, limo_root / "henchmen.png",
        first_sparrow(limo_root / "henchmen.xml", "hench dancing"),
        (29, 22))
    for screen_x in (41, 95, 204, 257):
        x, y = to_stage(screen_x, 20)
        blend_at(stage, (512, 256), hench, (29, 22), (x, y))

    # Preserve the already-integrated foreground car untouched, after the
    # distant layer and dancers in the painter order.
    front_limo = extract_sparrow_frame(
        args.ffmpeg, limo_root / "limoDrive.png",
        first_sparrow(limo_root / "limoDrive.xml", "Limo stage"), (44, 88))
    blend_at(stage, (512, 256), front_limo, (44, 88), (341, 108))

    indices = quantize(stage, palette)
    stage_pages = [bytearray(PAGE_BYTES), bytearray(PAGE_BYTES)]
    for row in range(PAGE):
        stage_pages[0][row * PAGE:(row + 1) * PAGE] = indices[
            row * 512:row * 512 + PAGE]
        stage_pages[1][row * PAGE:(row + 1) * PAGE] = indices[
            row * 512 + PAGE:(row + 1) * 512]

    output = args.output_dir
    shutil.copytree(args.input_dir, output)
    out_package = output / args.scene
    out_header = output / args.header
    out_raw = bytearray(raw)
    out_raw[:PAGE_BYTES] = stage_pages[0]
    out_raw[PAGE_BYTES:PAGE_BYTES * 2] = stage_pages[1]
    out_package.write_bytes(out_raw)
    shutil.copy2(source_header, out_header)

    preview = bytearray(320 * 240 * 4)
    for sy in range(240):
        world_y = 120 + (sy - 120) * 256 // ZOOM_Q8
        stage_y = world_y - STAGE_Y
        for sx in range(320):
            world_x = 160 + (sx - 160) * 256 // ZOOM_Q8
            stage_x = world_x - STAGE_X
            if 0 <= stage_x < 512 and 0 <= stage_y < 256:
                color_index = indices[stage_y * 512 + stage_x]
                if color_index:
                    r, g, b = palette[color_index - 1]
                    dst = (sy * 320 + sx) * 4
                    preview[dst:dst + 4] = bytes((r, g, b, 255))
    save_png(output / "week4-stage-v147-native-preview.png", 320, 240, preview)

    # A tiny manifest records exactly what changed and keeps the older input
    # package immutable for direct A/B comparison.
    import hashlib
    manifest = [
        "Week 4 composition integration v147",
        f"source package sha256: {hashlib.sha256(raw).hexdigest()}",
        f"output package sha256: {hashlib.sha256(out_raw).hexdigest()}",
        f"source pages: {page_count}; output pages: {page_count}",
        "changed: stage pages 0 and 1 only; existing CLUT and character texels retained",
        "added official art: bgLimo first cel and hench dancing first cel (four instances)",
        "retained: foreground limo extraction/size/world placement; charts/audio/frames unchanged",
        "palette: existing Week 4 RGB555 CLUT, nearest-color mapping for the new opaque texels",
    ]
    (output / "COMPOSITION-V147.txt").write_text("\n".join(manifest) + "\n", encoding="ascii")
    print("Week 4 stage rebuilt: 2 scenery pages replaced; package page count and CLUT unchanged")
    print(f"source={hashlib.sha256(raw).hexdigest()} output={hashlib.sha256(out_raw).hexdigest()}")


if __name__ == "__main__":
    main()
