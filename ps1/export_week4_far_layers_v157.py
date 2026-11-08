#!/usr/bin/env python3
"""Repack Week 4 far limo/dancers without occupying BF's live VRAM page.

Input: archived v156c package. Reuses its CLUT and pages 0..6 byte-for-byte,
re-packs the existing foreground limo plus the four far-limo cels into page 7,
and writes higher-resolution official henchmen cels to one dedicated page 8.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from convert_bopeebo_visuals import extract_sparrow_frame, quantize  # noqa: E402

PAGE = 256
PAGE_BYTES = PAGE * PAGE
INPUT_PAGE_COUNT = 10
OUTPUT_PAGE_COUNT = 9
LIMO_SIZE = (256, 44)
DANCER_SIZE = (72, 57)
LIMO_FRAME_IDS = [0, 1, 2, 3]
DANCER_UNIQUE = [0, 2, 5, 7, 9, 11, 15, 17, 20, 22, 24, 26]
DANCER_SEQUENCE = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 5, 5,
                   6, 6, 7, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 11, 11]
FRONT_LIMO_RECT = (8, 32, 240, 76)
FRONT_LIMO_DEST = (8, 176)


def find_frame(xml_path: pathlib.Path, prefix: str, index: int) -> dict[str, object]:
    root = ET.parse(xml_path).getroot()
    name = f"{prefix}{index:04d}"
    node = next((n for n in root.findall("SubTexture") if n.attrib.get("name") == name), None)
    if node is None:
        raise ValueError(f"missing official frame {name} in {xml_path}")
    a = node.attrib
    return {"name": name, "x": int(a["x"]), "y": int(a["y"]),
            "width": int(a["width"]), "height": int(a["height"]),
            "frameX": int(a.get("frameX", 0)), "frameY": int(a.get("frameY", 0)),
            "frameWidth": int(a.get("frameWidth", a["width"])),
            "frameHeight": int(a.get("frameHeight", a["height"])),
            "rotated": a.get("rotated", "false").lower() == "true"}


def palette_rgb555(data: bytes) -> list[tuple[int, int, int]]:
    words = struct.unpack("<256H", data)
    return [tuple(((word >> shift) & 31) * 255 // 31 for shift in (0, 5, 10))
            for word in words[1:]]


def place(page: bytearray, x: int, y: int, w: int, h: int,
          rgba: bytearray, palette: list[tuple[int, int, int]]) -> None:
    if x < 0 or y < 0 or x + w > PAGE or y + h > PAGE:
        raise ValueError("texture placement exceeds 256x256 page")
    indexed = quantize(rgba, palette)
    for row in range(h):
        start = (y + row) * PAGE + x
        page[start:start + w] = indexed[row * w:(row + 1) * w]


def copy_rect(page: bytearray, source: tuple[int, int, int, int],
              dest: tuple[int, int]) -> None:
    sx, sy, width, height = source
    dx, dy = dest
    if dx + width > PAGE or dy + height > PAGE:
        raise ValueError("copied foreground limo exceeds texture page")
    for row in range(height):
        src = (sy + row) * PAGE + sx
        dst = (dy + row) * PAGE + dx
        page[dst:dst + width] = page[src:src + width]


def append_header(header: str) -> str:
    if "WEEK4_FRAME_FAR_LIMO_0" not in header or "BOPEEBO_WEEK4_PAGE_COUNT 10u" not in header:
        raise ValueError("input header is not the v156c ten-page package")
    header = header.replace("#define BOPEEBO_WEEK4_PAGE_COUNT 10u",
                            "#define BOPEEBO_WEEK4_PAGE_COUNT 9u", 1)
    header = header.replace("{ 7, 8, 32, 240, 76 }, /* LIMO_FRONT */",
                            "{ 7, 8, 176, 240, 76 }, /* LIMO_FRONT */", 1)
    header = header.replace("{ 7, 8, 112, 240, 64 }, /* FAR_PLANE */",
                            "{ 7, 0, 0, 0, 0 }, /* FAR_PLANE unused in the split-layer scene */", 1)
    for i in range(4):
        header = header.replace(f"{{ 8, 0, {i*48}, 256, 44 }}, /* FAR_LIMO_{i} */",
                                f"{{ 7, 0, {i*44}, 256, 44 }}, /* FAR_LIMO_{i} */", 1)
    header = header.replace("{ 9, ", "{ 8, ")
    header = header.replace("#define WEEK4_VISUAL_FRAME_COUNT 66u",
                            "#define WEEK4_VISUAL_FRAME_COUNT 66u", 1)
    # Dancer cels are packed three across and four down at 72x57.
    for i in range(12):
        old_x, old_y = (i % 4) * 48, (i // 4) * 38
        new_x, new_y = (i % 3) * 72, (i // 3) * 57
        header = header.replace(f"{{ 8, {old_x}, {old_y}, 48, 38 }}, /* HENCH_{i} */",
                                f"{{ 8, {new_x}, {new_y}, 72, 57 }}, /* HENCH_{i} */", 1)
    return header


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", type=pathlib.Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--input-dir", type=pathlib.Path, required=True)
    ap.add_argument("--output-dir", type=pathlib.Path, required=True)
    args = ap.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")
    source_path = args.input_dir / "week4-scene.bin"
    header_path = args.input_dir / "week4_visual_data.h"
    source, header = source_path.read_bytes(), header_path.read_text(encoding="ascii")
    expected = INPUT_PAGE_COUNT * PAGE_BYTES + 512
    if len(source) != expected:
        raise ValueError(f"expected v156c package length {expected}, got {len(source)}")
    clut = source[INPUT_PAGE_COUNT * PAGE_BYTES:]
    palette = palette_rgb555(clut)
    limo_root = args.assets / "week4" / "images" / "limo"
    limo_png, limo_xml = limo_root / "bgLimo.png", limo_root / "bgLimo.xml"
    hench_png, hench_xml = limo_root / "henchmen.png", limo_root / "henchmen.xml"

    # Page 7 is repacked as the animated far limo followed by the foreground limo.
    # This removes the unused baked far-plane image and avoids leasing BF's atlas page.
    page7 = bytearray(PAGE_BYTES)
    original_page7 = bytearray(source[7 * PAGE_BYTES:8 * PAGE_BYTES])
    copy_rect(page7, FRONT_LIMO_RECT, FRONT_LIMO_DEST)
    limo_meta = []
    for i in LIMO_FRAME_IDS:
        rgba = extract_sparrow_frame(args.ffmpeg, limo_png,
            find_frame(limo_xml, "background limo pink", i), LIMO_SIZE)
        y = i * 44
        place(page7, 0, y, *LIMO_SIZE, rgba, palette)
        limo_meta.append({"source_index": i, "u": 0, "v": y,
                          "width": LIMO_SIZE[0], "height": LIMO_SIZE[1]})
    if original_page7[:32 * PAGE] == page7[:32 * PAGE]:
        raise ValueError("unexpected page copy: the far limo region was not written")

    dancer_page = bytearray(PAGE_BYTES)
    dancer_meta = []
    for i, source_index in enumerate(DANCER_UNIQUE):
        rgba = extract_sparrow_frame(args.ffmpeg, hench_png,
            find_frame(hench_xml, "hench dancing", source_index), DANCER_SIZE)
        x, y = (i % 3) * DANCER_SIZE[0], (i // 3) * DANCER_SIZE[1]
        place(dancer_page, x, y, *DANCER_SIZE, rgba, palette)
        dancer_meta.append({"source_index": source_index, "u": x, "v": y,
                            "width": DANCER_SIZE[0], "height": DANCER_SIZE[1]})

    output = source[:7 * PAGE_BYTES] + page7 + dancer_page + clut
    new_header = append_header(header)
    shutil.copytree(args.input_dir, args.output_dir)
    (args.output_dir / "week4-scene.bin").write_bytes(output)
    (args.output_dir / "week4_visual_data.h").write_text(new_header, encoding="ascii")
    report = {
        "version": "v157-week4-far-layers-hires-no-bf-page-overwrite",
        "input_week4_sha256": hashlib.sha256(source).hexdigest(),
        "output_week4_sha256": hashlib.sha256(output).hexdigest(),
        "clut_sha256": hashlib.sha256(clut).hexdigest(),
        "pages_0_through_6_unchanged": output[:7*PAGE_BYTES] == source[:7*PAGE_BYTES],
        "clut_unchanged": output[-512:] == clut,
        "page_7_repacked": {
            "far_limo": {"frames": limo_meta, "source_canvas": "2218x384",
                         "target": "256x44 per cel", "frame_rate": 24},
            "foreground_limo_moved_to": {"u": 8, "v": 176, "width": 240, "height": 76},
            "unused_baked_far_plane_removed": True,
            "BF_atlas_page_7_is_no_longer_overwritten": True,
        },
        "page_8_dancers": {"frames": dancer_meta, "source_canvas": "517x410",
                            "target": "72x57 per cel", "sequence": DANCER_SEQUENCE,
                            "frame_rate": 24},
        "package_bytes": len(output),
        "prior_v156c_bytes": len(source),
        "source_assets_revision": "724eba9de9e76761d9cefd52169926bc51c760a5",
    }
    (args.output_dir / "week4-far-assets-v157.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
