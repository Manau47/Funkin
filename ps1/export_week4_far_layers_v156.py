#!/usr/bin/env python3
"""Re-export Week 4's distant limo and hench dancers as independent animations.

The input must be the preserved v155 Week 4 package. Only two new 8bpp pages
are appended, using its existing CLUT: four official limo frames and six
unique frames per dancer direction. Duplicate Sparrow frames remain represented
by the original 15-entry timing lookup written to the generated C header.
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
OLD_PAGE_COUNT = 8
LIMO_SIZE = (256, 44)
DANCER_SIZE = (48, 38)
LIMO_FRAMES = [0, 1, 2, 3]
DANCER_UNIQUE = [0, 2, 5, 7, 9, 11, 15, 17, 20, 22, 24, 26]
DANCER_SEQUENCE = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 5, 5,
                   6, 6, 7, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 11, 11]


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


def append_header(header: str) -> str:
    if "WEEK4_FRAME_FAR_LIMO_0" in header:
        raise ValueError("input header already contains v156 far animations")
    enum_marker = "\tWEEK4_FRAME_FAR_PLANE = 49,\n};"
    enum_add = "\tWEEK4_FRAME_FAR_PLANE = 49,\n" + "".join(
        f"\tWEEK4_FRAME_FAR_LIMO_{i} = {50+i},\n" for i in range(4)) + "".join(
        f"\tWEEK4_FRAME_HENCH_{i} = {54+i},\n" for i in range(12)) + "};"
    if enum_marker not in header:
        raise ValueError("v155 frame enum marker not found")
    header = header.replace(enum_marker, enum_add, 1)
    header = header.replace("#define BOPEEBO_WEEK4_PAGE_COUNT 8u",
                            "#define BOPEEBO_WEEK4_PAGE_COUNT 10u", 1)
    header = header.replace("#define WEEK4_VISUAL_FRAME_COUNT 50u",
                            "#define WEEK4_VISUAL_FRAME_COUNT 66u", 1)
    marker = "\t{ 7, 8, 112, 240, 64 }, /* FAR_PLANE */"
    if marker not in header:
        raise ValueError("v155 far-plane descriptor not found")
    rows = "\n" + "\n".join(
        f"\t{{ 8, 0, {i*48}, 256, 44 }}, /* FAR_LIMO_{i} */" for i in range(4))
    rows += "\n" + "\n".join(
        f"\t{{ 9, {(i%4)*48}, {(i//4)*38}, 48, 38 }}, /* HENCH_{i} */"
        for i in range(12))
    header = header.replace(marker, marker + rows, 1)
    header = header.replace("#define WEEK4_VISUAL_FRAME_COUNT 66u",
        "#define WEEK4_VISUAL_FRAME_COUNT 66u\n"
        "#define WEEK4_FAR_LIMO_FRAME_RATE 24u\n"
        "#define WEEK4_HENCH_FRAME_RATE 24u\n"
        "#define WEEK4_HENCH_SEQUENCE_LENGTH 30u\n"
        "static const uint8_t week4_hench_dance_sequence[30] = {" +
        ",".join(map(str, DANCER_SEQUENCE)) + "};", 1)
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
    source = source_path.read_bytes()
    header = header_path.read_text(encoding="ascii")
    expected = OLD_PAGE_COUNT * PAGE_BYTES + 512
    if len(source) != expected or "WEEK4_FRAME_FAR_PLANE = 49" not in header:
        raise ValueError("input is not the archived v155 eight-page package")
    clut = source[OLD_PAGE_COUNT * PAGE_BYTES:]
    palette = palette_rgb555(clut)
    root = args.assets / "week4" / "images" / "limo"
    limo_png, limo_xml = root / "bgLimo.png", root / "bgLimo.xml"
    hench_png, hench_xml = root / "henchmen.png", root / "henchmen.xml"
    limo_page, dancer_page = bytearray(PAGE_BYTES), bytearray(PAGE_BYTES)
    limo_meta, dancer_meta = [], []

    for i in LIMO_FRAMES:
        data = extract_sparrow_frame(args.ffmpeg, limo_png,
            find_frame(limo_xml, "background limo pink", i), LIMO_SIZE)
        place(limo_page, 0, i * 48, *LIMO_SIZE, data, palette)
        limo_meta.append({"source_index": i, "u": 0, "v": i * 48,
                          "width": LIMO_SIZE[0], "height": LIMO_SIZE[1]})
    for i, source_index in enumerate(DANCER_UNIQUE):
        data = extract_sparrow_frame(args.ffmpeg, hench_png,
            find_frame(hench_xml, "hench dancing", source_index), DANCER_SIZE)
        x, y = (i % 4) * DANCER_SIZE[0], (i // 4) * DANCER_SIZE[1]
        place(dancer_page, x, y, *DANCER_SIZE, data, palette)
        dancer_meta.append({"source_index": source_index, "u": x, "v": y,
                            "width": DANCER_SIZE[0], "height": DANCER_SIZE[1]})

    output = source[:OLD_PAGE_COUNT * PAGE_BYTES] + limo_page + dancer_page + clut
    new_header = append_header(header)
    shutil.copytree(args.input_dir, args.output_dir)
    (args.output_dir / "week4-scene.bin").write_bytes(output)
    (args.output_dir / "week4_visual_data.h").write_text(new_header, encoding="ascii")
    report = {
        "version": "v156-week4-far-animations",
        "input_week4_sha256": hashlib.sha256(source).hexdigest(),
        "output_week4_sha256": hashlib.sha256(output).hexdigest(),
        "clut_sha256": hashlib.sha256(clut).hexdigest(),
        "first_eight_pages_unchanged": hashlib.sha256(output[:OLD_PAGE_COUNT*PAGE_BYTES]).hexdigest()
            == hashlib.sha256(source[:OLD_PAGE_COUNT*PAGE_BYTES]).hexdigest(),
        "extra_pages": [
            {"logical_page": 8, "purpose": "four separate 24 fps bgLimo frames",
             "dimensions": "256x256 indexed 8bpp", "frames": limo_meta,
             "occupied_pixels": 4 * LIMO_SIZE[0] * LIMO_SIZE[1]},
            {"logical_page": 9, "purpose": "six unique danceLeft and six unique danceRight hench poses",
             "dimensions": "256x256 indexed 8bpp", "frames": dancer_meta,
             "occupied_pixels": 12 * DANCER_SIZE[0] * DANCER_SIZE[1]},
        ],
        "dancer_sequence_index_to_unique_frame": DANCER_SEQUENCE,
        "source_assets_revision": "724eba9de9e76761d9cefd52169926bc51c760a5",
    }
    (args.output_dir / "week4-far-assets-v156.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "week4-far-export-v156.txt").write_text(
        "v156 reuses the v155 CLUT and first eight page bytes unchanged.\n"
        "Added two 8bpp pages (128 KiB): 4 limo cels at 256x44 and 12 unique hench cels at 48x38.\n"
        "Palette colors are quantized against the unchanged pinned Week 4 CLUT; no palette is regenerated.\n",
        encoding="ascii")
    print(f"Input SHA-256: {report['input_week4_sha256']}")
    print(f"Output SHA-256: {report['output_week4_sha256']}")
    print(f"W4 package bytes: {len(output)} (10 pages + 512-byte CLUT)")
    print(f"Existing 8 pages unchanged: {report['first_eight_pages_unchanged']}")


if __name__ == "__main__":
    main()
