#!/usr/bin/env python3
"""Split the pinned Week 4 far limo/dancers from the backdrop for parallax.

Starts from the immutable v152 converted package. The scene background is
rebuilt from the same official sunset source; the distant limo and four
official hench cels are placed in a free rectangle on the existing eighth
Week 4 page. No extra page, palette, CD package, chart, or audio conversion is
introduced.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from animate_preview import save_png  # noqa: E402
from convert_bopeebo_visuals import (  # noqa: E402
    blend_at, extract_menu_cover, extract_sparrow_frame, quantize,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE
PAGE_COUNT = 8
STAGE_W, STAGE_H = 512, 256
STAGE_X, STAGE_Y = -64, 0
ZOOM_Q8 = 524
FAR_FRAME = (7, 8, 112, 240, 64)


def first_frame(xml_path: pathlib.Path, prefix: str) -> dict[str, object]:
    root = ET.parse(xml_path).getroot()
    node = next((n for n in root.findall("SubTexture")
                 if n.attrib.get("name", "").startswith(prefix)), None)
    if node is None:
        raise ValueError(f"Missing {prefix!r} in {xml_path}")
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
    return [tuple(((word >> shift) & 31) * 255 // 31 for shift in (0, 5, 10))
            for word in words[1:]]


def set_rgba_page_region(page: bytearray, x: int, y: int, width: int, height: int,
                         rgba: bytearray, palette: list[tuple[int, int, int]]) -> None:
    indices = quantize(rgba, palette)
    for row in range(height):
        start = (y + row) * PAGE + x
        page[start:start + width] = indices[row * width:(row + 1) * width]


def append_frame(header: str) -> str:
    if "WEEK4_FRAME_FAR_PLANE" in header:
        raise ValueError("Input header already contains the v153 far-plane frame")
    header = header.replace(
        "\tWEEK4_FRAME_LIMO_FRONT = 48,\n};",
        "\tWEEK4_FRAME_LIMO_FRONT = 48,\n"
        "\tWEEK4_FRAME_FAR_PLANE = 49,\n};", 1)
    header = header.replace("#define WEEK4_VISUAL_FRAME_COUNT 49u",
                            "#define WEEK4_VISUAL_FRAME_COUNT 50u", 1)
    header = header.replace(
        "#define BOPEEBO_WEEK4_LIMO_Y (88)",
        "#define BOPEEBO_WEEK4_LIMO_Y (88)\n"
        "#define BOPEEBO_WEEK4_FAR_X (63)\n"
        "#define BOPEEBO_WEEK4_FAR_Y (93)", 1)
    marker = "\t{ 7, 8, 32, 240, 76 }, /* LIMO_FRONT */"
    if marker not in header:
        raise ValueError("Expected v152 LIMO_FRONT atlas rectangle was not found")
    header = header.replace(marker, marker +
        "\n\t{ 7, 8, 112, 240, 64 }, /* FAR_PLANE */", 1)
    return header


def render_preview(stage: bytearray, far: bytearray, palette: list[tuple[int, int, int]],
                   output: pathlib.Path, camera: tuple[int, int]) -> None:
    cam_x, cam_y = camera
    parallax_x = 160 + (cam_x - 160) * 102 // 256
    parallax_y = 120 + (cam_y - 120) * 102 // 256
    pixels = bytearray(320 * 240 * 4)
    for sy in range(240):
        wy = 120 + (sy - 120) * 256 // ZOOM_Q8
        py = wy - STAGE_Y
        if not 0 <= py < STAGE_H:
            continue
        for sx in range(320):
            wx = 160 + (sx - 160) * 256 // ZOOM_Q8
            px = wx - STAGE_X
            if not 0 <= px < STAGE_W:
                continue
            idx = stage[py * STAGE_W + px]
            if idx:
                r, g, b = palette[idx - 1]
                off = (sy * 320 + sx) * 4
                pixels[off:off + 4] = bytes((r, g, b, 255))
    # Approximate the runtime's parallax FT4 at 1.02x effective size. This is
    # a resource preview, not a capture from the PS1 executable.
    world_x = 63  # v147/v152 approved far-plane screen anchor at neutral camera
    world_y = 93
    x0 = 160 + (world_x - parallax_x) * ZOOM_Q8 // 256
    y0 = 120 + (world_y - parallax_y) * ZOOM_Q8 // 256
    for dy in range(65):
        sy = y0 + dy
        if not 0 <= sy < 240:
            continue
        ty = min(63, dy * 256 // (ZOOM_Q8 // 2))
        for dx in range(245):
            sx = x0 + dx
            if not 0 <= sx < 320:
                continue
            tx = min(239, dx * 256 // (ZOOM_Q8 // 2))
            idx = far[ty * 240 + tx]
            if idx:
                r, g, b = palette[idx - 1]
                off = (sy * 320 + sx) * 4
                pixels[off:off + 4] = bytes((r, g, b, 255))
    save_png(output, 320, 240, pixels)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", type=pathlib.Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--input-dir", type=pathlib.Path, required=True)
    ap.add_argument("--output-dir", type=pathlib.Path, required=True)
    args = ap.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output_dir}")

    scene_path = args.input_dir / "week4-scene.bin"
    header_path = args.input_dir / "week4_visual_data.h"
    source = scene_path.read_bytes()
    header = header_path.read_text(encoding="ascii")
    if len(source) != PAGE_COUNT * PAGE_BYTES + 512:
        raise ValueError("Expected the v152 eight-page package and one unchanged CLUT")
    if "WEEK4_FRAME_LIMO_FRONT = 48" not in header:
        raise ValueError("Input is not the v152 Week 4 package")

    original_clut = source[PAGE_COUNT * PAGE_BYTES:]
    palette = palette_rgb555(original_clut)
    limo_root = args.assets / "week4/images/limo"

    # Keep the same 512x256 PS1 4:3 sunset background, but remove props that
    # must move independently. Re-use the already converted scene pages.
    stage_rgba = extract_menu_cover(args.ffmpeg, limo_root / "limoSunset.png",
                                    STAGE_W, STAGE_H)
    stage_indexed = quantize(stage_rgba, palette)

    # The far limousine and its four dancers share the official .4 scroll
    # factor/z band. Compose the limo at half width and four recognizable
    # 40x32 cels into one independent 240x64 frame on existing Week 4 page 7.
    far_rgba = bytearray(240 * 64 * 4)
    bg_limo = extract_sparrow_frame(
        args.ffmpeg, limo_root / "bgLimo.png",
        first_frame(limo_root / "bgLimo.xml", "background limo pink"), (240, 42))
    blend_at(far_rgba, (240, 64), bg_limo, (240, 42), (0, 22))
    dancer = extract_sparrow_frame(
        args.ffmpeg, limo_root / "henchmen.png",
        first_frame(limo_root / "henchmen.xml", "hench dancing"), (40, 32))
    for x in (4, 64, 136, 196):
        blend_at(far_rgba, (240, 64), dancer, (40, 32), (x, 0))
    far_indexed = quantize(far_rgba, palette)

    output = bytearray(source)
    for row in range(PAGE):
        output[row * PAGE:(row + 1) * PAGE] = stage_indexed[
            row * STAGE_W:row * STAGE_W + PAGE]
        output[PAGE_BYTES + row * PAGE:PAGE_BYTES + (row + 1) * PAGE] = stage_indexed[
            row * STAGE_W + PAGE:(row + 1) * STAGE_W]

    page7_start = 7 * PAGE_BYTES
    page7 = bytearray(output[page7_start:page7_start + PAGE_BYTES])
    set_rgba_page_region(page7, *FAR_FRAME[1:], far_rgba, palette)
    output[page7_start:page7_start + PAGE_BYTES] = page7
    new_header = append_frame(header)

    shutil.copytree(args.input_dir, args.output_dir)
    (args.output_dir / "week4-scene.bin").write_bytes(output)
    (args.output_dir / "week4_visual_data.h").write_text(new_header, encoding="ascii")
    (args.output_dir / "week4-scene.bin.v152-original").write_bytes(source)

    layer_preview = bytearray(240 * 64 * 4)
    for i, index in enumerate(far_indexed):
        if index:
            r, g, b = palette[index - 1]
            layer_preview[i * 4:i * 4 + 4] = bytes((r, g, b, 255))
    save_png(args.output_dir / "week4-far-plane-v153.png", 240, 64, layer_preview)
    render_preview(stage_indexed, far_indexed, palette,
                  args.output_dir / "week4-background-v153-preview.png", (80, 110))
    render_preview(stage_indexed, far_indexed, palette,
                  args.output_dir / "week4-background-v153-bf-preview.png", (153, 40))

    report = (
        "Week 4 composition v153\n"
        f"v152 input SHA-256: {hashlib.sha256(source).hexdigest()}\n"
        f"v153 package SHA-256: {hashlib.sha256(output).hexdigest()}\n"
        f"CLUT preserved byte-for-byte: {hashlib.sha256(original_clut).hexdigest()}\n"
        "Stage pages 0-1 contain the sunset only; no global art/audio/chart conversion.\n"
        "Far plane: 240x64, page 7 rectangle (8,112), four official 40x32 hench cels, .4 camera scroll.\n"
        "Main limo frame, actor pixels/anchors, camera zoom, charts, audio and gameplay unchanged.\n"
        "Texture package stays eight 8bpp pages plus one CLUT; no extra page or CD upload.\n"
    )
    (args.output_dir / "COMPOSITION-V153.txt").write_text(report, encoding="ascii")
    print(report, end="")


if __name__ == "__main__":
    main()
