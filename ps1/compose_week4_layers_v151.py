#!/usr/bin/env python3
"""Rebuild Week 4 stage layers without touching its actor atlas or CLUT.

The base sunset, distant limo and four official henchmen are rasterized into
the two existing stage pages. The foreground limo is packed into free space
on the Mom-icon page so it can be drawn after GF and before Mom/BF, preserving
the intended occlusion without adding a VRAM page or changing animation data.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
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
STAGE_X = -64
STAGE_Y = 0
ZOOM_Q8 = 524
LIMO_RECT = (8, 32, 240, 76)  # unused region of the Mom icon's logical page 7


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


def world_pixel(screen_coord: int, screen_center: int) -> int:
    return screen_center + (screen_coord - screen_center) * 256 // ZOOM_Q8


def to_stage(screen_x: int, screen_y: int) -> tuple[int, int]:
    return (world_pixel(screen_x, 160) - STAGE_X,
            world_pixel(screen_y, 120) - STAGE_Y)


def set_rgba_page_region(page: bytearray, x: int, y: int, width: int, height: int,
                         rgba: bytearray, palette: list[tuple[int, int, int]]) -> None:
    indices = quantize(rgba, palette)
    for row in range(height):
        start = (y + row) * PAGE + x
        page[start:start + width] = indices[row * width:(row + 1) * width]


def write_frame_metadata(header: str, name: str, page: int, x: int, y: int,
                         width: int, height: int) -> str:
    if f"WEEK4_FRAME_{name}" in header:
        raise ValueError(f"Frame {name} is already present")
    header = re.sub(r"#define BOPEEBO_WEEK4_PAGE_COUNT \d+u",
                    f"#define BOPEEBO_WEEK4_PAGE_COUNT {PAGE_COUNT}u", header, count=1)
    header = header.replace("#define BOPEEBO_WEEK4_GF_Y (130)",
                            "#define BOPEEBO_WEEK4_GF_Y (130)\n"
                            "#define BOPEEBO_WEEK4_LIMO_X (16)\n"
                            "#define BOPEEBO_WEEK4_LIMO_Y (152)", 1)
    header = header.replace("#define WEEK4_VISUAL_FRAME_COUNT 48u",
                            "#define WEEK4_VISUAL_FRAME_COUNT 49u", 1)
    header = header.replace("\tWEEK4_FRAME_GF_DANCE_FULL_29 = 47,\n};",
                            "\tWEEK4_FRAME_GF_DANCE_FULL_29 = 47,\n"
                            "\tWEEK4_FRAME_LIMO_FRONT = 48,\n};", 1)
    array_start = header.index("static const Week4VisualFrame week4_visual_frames[")
    array_end = header.index("\n};", array_start)
    descriptor = f"\t{{ {page}, {x}, {y}, {width}, {height} }}, /* {name} */"
    header = header[:array_end] + "\n" + descriptor + header[array_end:]
    if "WEEK4_FRAME_LIMO_FRONT = 48" not in header or "/* LIMO_FRONT */" not in header:
        raise ValueError("Could not append the foreground-limo descriptor")
    return header


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", type=pathlib.Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--input-dir", type=pathlib.Path, required=True)
    ap.add_argument("--output-dir", type=pathlib.Path, required=True)
    ap.add_argument("--scene", default="week4-scene.bin")
    ap.add_argument("--header", default="week4_visual_data.h")
    args = ap.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output_dir}")

    source_scene = args.input_dir / args.scene
    source_header = args.input_dir / args.header
    original = source_scene.read_bytes()
    header = source_header.read_text(encoding="ascii")
    if len(original) != PAGE_COUNT * PAGE_BYTES + 512:
        raise ValueError("Expected the v149 8-page Week 4 package and one CLUT")
    if "WEEK4_FRAME_MOM_ICON" not in header:
        raise ValueError("Input header is not the expected Week 4 atlas")
    clut_bytes = original[PAGE_COUNT * PAGE_BYTES:]
    palette = palette_rgb555(clut_bytes)

    limo_root = args.assets / "week4/images/limo"
    stage = extract_menu_cover(args.ffmpeg, limo_root / "limoSunset.png", 512, 256)
    far_limo = extract_sparrow_frame(
        args.ffmpeg, limo_root / "bgLimo.png",
        first_frame(limo_root / "bgLimo.xml", "background limo pink"), (455, 79))
    far_x, far_y = to_stage(-38, 65)
    # v148 extracted 455x79 but composited it as 222x39, cropping half the car.
    blend_at(stage, (512, 256), far_limo, (455, 79), (far_x, far_y))

    dancer = extract_sparrow_frame(
        args.ffmpeg, limo_root / "henchmen.png",
        first_frame(limo_root / "henchmen.xml", "hench dancing"), (40, 32))
    for screen_x in (41, 95, 204, 257):
        x, y = to_stage(screen_x, 33)  # feet on the far limousine roof line
        blend_at(stage, (512, 256), dancer, (40, 32), (x, y))

    indexed_stage = quantize(stage, palette)
    output_package = bytearray(original)
    for row in range(PAGE):
        output_package[row * PAGE:(row + 1) * PAGE] = indexed_stage[row * 512:row * 512 + PAGE]
        output_package[PAGE_BYTES + row * PAGE:PAGE_BYTES + (row + 1) * PAGE] = \
            indexed_stage[row * 512 + PAGE:(row + 1) * 512]

    # Store the first official limoDrive frame at its true wide aspect ratio.
    # The previous 44x88 target made the car effectively a tiny vertical stamp.
    front = extract_sparrow_frame(
        args.ffmpeg, limo_root / "limoDrive.png",
        first_frame(limo_root / "limoDrive.xml", "Limo stage"), (LIMO_RECT[2], LIMO_RECT[3]))
    page7 = bytearray(output_package[7 * PAGE_BYTES:8 * PAGE_BYTES])
    set_rgba_page_region(page7, *LIMO_RECT, front, palette)
    output_package[7 * PAGE_BYTES:8 * PAGE_BYTES] = page7

    new_header = write_frame_metadata(header, "LIMO_FRONT", 7, *LIMO_RECT)
    shutil.copytree(args.input_dir, args.output_dir)
    (args.output_dir / args.scene).write_bytes(output_package)
    (args.output_dir / args.header).write_text(new_header, encoding="ascii")

    # Package preview of the background and the full-size foreground sprite.
    preview = bytearray(320 * 240 * 4)
    for sy in range(240):
        world_y = 120 + (sy - 120) * 256 // ZOOM_Q8
        py = world_y - STAGE_Y
        for sx in range(320):
            world_x = 160 + (sx - 160) * 256 // ZOOM_Q8
            px = world_x - STAGE_X
            if 0 <= px < 512 and 0 <= py < 256:
                index = indexed_stage[py * 512 + px]
                if index:
                    r, g, b = palette[index - 1]
                    dst = (sy * 320 + sx) * 4
                    preview[dst:dst + 4] = bytes((r, g, b, 255))
    save_png(args.output_dir / "week4-background-v151-preview.png", 320, 240, preview)

    manifest = (
        "Week 4 separated foreground composition v151\n"
        f"input package sha256: {hashlib.sha256(original).hexdigest()}\n"
        f"output package sha256: {hashlib.sha256(output_package).hexdigest()}\n"
        f"unchanged CLUT sha256: {hashlib.sha256(clut_bytes).hexdigest()}\n"
        "changed: stage pages 0-1 and free texture region on page 7 only\n"
        "background: official Sunset + full-width background limo + four official dancers\n"
        "foreground: official Limo stage 240x76 stored on logical page 7 for in-game layering\n"
        "palette: pinned Week 4 RGB555 CLUT reused; actor atlas pixels untouched\n"
    )
    (args.output_dir / "COMPOSITION-V151.txt").write_text(manifest, encoding="ascii")
    print(manifest, end="")


if __name__ == "__main__":
    main()

