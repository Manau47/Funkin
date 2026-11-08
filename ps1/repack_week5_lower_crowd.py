#!/usr/bin/env python3
"""Rebuild only the Week 5 lower-crowd cels with a shared logical canvas.

The existing Week 5 package, palettes, animation cadence, and all unrelated
frames are preserved.  The X-mas page 9 is repacked deterministically with
its existing CLUT and the same 176x54 nearest-neighbour lower-crowd cels.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from convert_bopeebo_visuals import extract_sparrow_frame, quantize  # noqa: E402
from rebuild_week5_backdrop_detail import old_frame_rgba, unpack_clut  # noqa: E402

PAGE = 256
PAGE_BYTES = PAGE * PAGE
CLUT_BYTES = 512
FRAME_RE = re.compile(
    r"^\s*\{\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,"
    r"\s*(-?\d+),\s*(-?\d+)\s*\},\s*/\*\s*(\w+)\s*\*/",
    re.MULTILINE,
)


def records(header: str) -> dict[str, dict[str, int]]:
    out = {}
    for m in FRAME_RE.finditer(header):
        page, u, v, w, h, dx, dy, name = m.groups()
        out[name] = dict(page=int(page), u=int(u), v=int(v), w=int(w),
                         h=int(h), dx=int(dx), dy=int(dy))
    return out


def set_record(header: str, name: str, rec: dict[str, int]) -> str:
    line = (f"\t{{ {rec['page']}u, {rec['u']}u, {rec['v']}u, "
            f"{rec['w']}u, {rec['h']}u, {rec['dx']}, {rec['dy']} }}, /* {name} */")
    updated, count = FRAME_RE.subn(
        lambda m: line if m.group(8) == name else m.group(0), header)
    if count == 0:
        raise ValueError(f"missing frame record {name}")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=pathlib.Path)
    parser.add_argument("--assets", required=True, type=pathlib.Path)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    src_header = args.package / "week5_visual_data.h"
    src_scene = args.package / "week5-scene.bin"
    header = src_header.read_text(encoding="ascii")
    raw = src_scene.read_bytes()
    pages_m = re.search(r"#define BOPEEBO_WEEK5_PAGE_COUNT (\d+)u", header)
    if not pages_m:
        raise ValueError("missing Week 5 page count")
    page_count = int(pages_m.group(1))
    if len(raw) != page_count * (PAGE_BYTES + CLUT_BYTES):
        raise ValueError("package size does not match page count")
    frame = records(header)
    required = ("TREE_XMAS", "SNOW_XMAS", "SANTA", "CROWD_LOWER_0",
                "CROWD_LOWER_1", "CROWD_LOWER_2", "CROWD_LOWER_3")
    if any(name not in frame for name in required):
        raise ValueError("package lacks one or more Week 5 lower-layer frames")
    if any(frame[name]["page"] != 9 for name in
           ("TREE_XMAS", "SNOW_XMAS", "SANTA", "CROWD_LOWER_0",
            "CROWD_LOWER_1", "CROWD_LOWER_3")):
        raise ValueError("X-mas lower-layer page ownership differs from expected page 9")

    textures = [raw[i * PAGE_BYTES:(i + 1) * PAGE_BYTES]
                for i in range(page_count)]
    cluts_start = page_count * PAGE_BYTES
    cluts = [raw[cluts_start + i * CLUT_BYTES:cluts_start + (i + 1) * CLUT_BYTES]
             for i in range(page_count)]
    palette = unpack_clut(raw, page_count, 9)

    def rgba_for(name: str) -> bytearray:
        return old_frame_rgba(raw, page_count, frame[name], palette)

    assets = args.assets / "week5" / "images" / "christmas"
    xml = ET.parse(assets / "bottomBop.xml").getroot()
    nodes = [n for n in xml.findall("SubTexture")
             if n.attrib.get("name", "").startswith("Bottom Level Boppers")]
    if len(nodes) < 8:
        raise ValueError("Bottom Level Boppers atlas is incomplete")

    # Slot four unique cels in a common 176x54 canonical rectangle. The shared
    # frameWidth/frameHeight metadata and offsets remain inside that canvas.
    lower = []
    for cel, index in enumerate((0, 2, 4, 6)):
        n = nodes[index]
        desc = {key: int(n.attrib.get(key, 0)) for key in
                ("x", "y", "width", "height", "frameX", "frameY",
                 "frameWidth", "frameHeight")}
        desc["rotated"] = n.attrib.get("rotated", "false").lower() == "true"
        desc["name"] = n.attrib.get("name", f"lower-{cel}")
        lower.append(extract_sparrow_frame(args.ffmpeg, assets / "bottomBop.png",
                                           desc, (176, 54)))

    # The six rectangles owned by page 9 plus the four fixed canvases fit in
    # this checked layout. No UV rectangle crosses the 256x256 page boundary.
    positions = {
        "SNOW_XMAS": (0, 0),
        "CROWD_LOWER_0": (0, 20),
        "CROWD_LOWER_1": (0, 74),
        "CROWD_LOWER_2": (0, 128),
        "CROWD_LOWER_3": (0, 182),
        "TREE_XMAS": (176, 20),
        "SANTA": (180, 137),
    }
    dimensions = {"SNOW_XMAS": (252, 19), "TREE_XMAS": (76, 117),
                  "SANTA": (72, 78)}
    canvases = {f"CROWD_LOWER_{i}": lower[i] for i in range(4)}
    dimensions.update({f"CROWD_LOWER_{i}": (176, 54) for i in range(4)})

    page_rgba = bytearray(PAGE_BYTES * 4)
    for name in required:
        w, h = dimensions[name]
        x, y = positions[name]
        if x + w > PAGE or y + h > PAGE:
            raise ValueError(f"page-9 placement out of bounds for {name}")
        rgba = canvases[name] if name in canvases else rgba_for(name)
        if len(rgba) != w * h * 4:
            raise ValueError(f"unexpected raster dimensions for {name}")
        for row in range(h):
            src = row * w * 4
            dst = ((y + row) * PAGE + x) * 4
            page_rgba[dst:dst + w * 4] = rgba[src:src + w * 4]

    page_indices = quantize(page_rgba, palette)
    if len(page_indices) != PAGE_BYTES:
        raise ValueError("page 9 quantizer returned an invalid page")
    textures[9] = bytes(page_indices)
    for name in required:
        x, y = positions[name]
        w, h = dimensions[name]
        rec = dict(page=9, u=x, v=y, w=w, h=h,
                   dx=0 if name.startswith("CROWD_LOWER_") else frame[name]["dx"],
                   dy=0 if name.startswith("CROWD_LOWER_") else frame[name]["dy"])
        header = set_record(header, name, rec)

    out = b"".join(textures) + b"".join(cluts)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "week5-scene.bin").write_bytes(out)
    (args.out / "week5_visual_data.h").write_text(header, encoding="ascii")
    print("Repacked Week 5 lower crowd: four 176x54 shared-canvas cels; "
          "same 12 pages, CLUT 9 retained; no art frames removed.")


if __name__ == "__main__":
    main()
