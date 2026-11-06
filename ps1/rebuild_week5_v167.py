#!/usr/bin/env python3
"""Rebuild Week 5 visuals only, preserving the v166 audio and chart package.

This offline asset step uses the pinned official assets and does not invoke
audio or chart conversion. It emits a 9-page 8bpp scene atlas and its C header.
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from animate_preview import Rig  # noqa: E402
from convert_bopeebo_visuals import (  # noqa: E402
    extract_sparrow_frame, fit_anchored_rig, median_palette, png_size,
    quantize, rgb555, run_ffmpeg,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE
MAX_PAGES = 9


def trim(rgba: bytearray, width: int, height: int, anchor_x: int = 0,
         anchor_y: int = 0) -> tuple[bytearray, int, int, int, int]:
    xs, ys = [], []
    for y in range(height):
        for x in range(width):
            if rgba[(y * width + x) * 4 + 3]:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise ValueError("refusing to pack an empty frame")
    x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    w, h = x1 - x0, y1 - y0
    out = bytearray(w * h * 4)
    for y in range(h):
        a = ((y + y0) * width + x0) * 4
        out[y * w * 4:(y + 1) * w * 4] = rgba[a:a + w * 4]
    return out, w, h, x0 - anchor_x, y0 - anchor_y


def frame_from_sparrow(xml_path: pathlib.Path, png_path: pathlib.Path,
                       prefix: str, sample: int, size: tuple[int, int]) -> bytearray:
    nodes = [n for n in ET.parse(xml_path).getroot().findall("SubTexture")
             if n.attrib.get("name", "").startswith(prefix)]
    unique = []
    seen = set()
    for node in nodes:
        key = tuple(node.attrib.get(k, "0") for k in
                    ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight"))
        if key not in seen:
            seen.add(key)
            unique.append(node)
    if not unique:
        raise ValueError(f"missing official Sparrow sequence {prefix!r}")
    node = unique[min(sample, len(unique) - 1)]
    desc = {k: int(node.attrib.get(k, 0)) for k in
            ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
    desc["rotated"] = node.attrib.get("rotated", "false").lower() == "true"
    return extract_sparrow_frame(str(FFMPEG), png_path, desc, size)


def packed_pages(items: list[dict], first_page: int) -> tuple[list[bytearray], dict[str, tuple[int, int, int]]]:
    """MaxRects-pack trimmed frames without rotation; PS1 uses point sampling."""
    pages: list[bytearray] = []
    free: list[list[tuple[int, int, int, int]]] = []
    placements: dict[str, tuple[int, int, int]] = {}

    def new_page() -> None:
        pages.append(bytearray(PAGE_BYTES * 4))
        free.append([(0, 0, PAGE, PAGE)])

    def intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
        return not (a[0] >= b[0] + b[2] or a[0] + a[2] <= b[0] or
                    a[1] >= b[1] + b[3] or a[1] + a[3] <= b[1])

    def split_free(rects: list[tuple[int, int, int, int]], used: tuple[int, int, int, int]):
        out = []
        ux, uy, uw, uh = used
        for rx, ry, rw, rh in rects:
            if not intersects((rx, ry, rw, rh), used):
                out.append((rx, ry, rw, rh))
                continue
            if ux > rx: out.append((rx, ry, ux - rx, rh))
            if ux + uw < rx + rw: out.append((ux + uw, ry, rx + rw - ux - uw, rh))
            if uy > ry: out.append((rx, ry, rw, uy - ry))
            if uy + uh < ry + rh: out.append((rx, uy + uh, rw, ry + rh - uy - uh))
        out = [r for r in out if r[2] > 0 and r[3] > 0]
        keep = []
        for i, a in enumerate(out):
            ax, ay, aw, ah = a
            if any(i != j and ax >= bx and ay >= by and ax + aw <= bx + bw and ay + ah <= by + bh
                   for j, (bx, by, bw, bh) in enumerate(out)):
                continue
            keep.append(a)
        return keep

    new_page()
    for item in sorted(items, key=lambda it: (-(it["w"] * it["h"]), -max(it["w"], it["h"]), it["name"])):
        w, h = item["w"], item["h"]
        if w > PAGE or h > PAGE:
            raise ValueError(f"frame exceeds a PS1 atlas page: {item['name']} {w}x{h}")
        choice = None
        for pi, rects in enumerate(free):
            for ri, (rx, ry, rw, rh) in enumerate(rects):
                if w <= rw and h <= rh:
                    score = (min(rw - w, rh - h), max(rw - w, rh - h), pi, ry, rx, ri)
                    if choice is None or score < choice[0]: choice = (score, pi, ri, rx, ry)
        if choice is None:
            if first_page + len(pages) >= MAX_PAGES:
                area = sum(it["w"] * it["h"] for it in items)
                raise ValueError(f"Week 5 visual assets need more than {MAX_PAGES} pages; "
                                 f"trimmed area={area} pixels, frame count={len(items)}")
            new_page()
            pi, ri, rx, ry = len(pages) - 1, 0, 0, 0
        else:
            _score, pi, ri, rx, ry = choice
        used = (rx, ry, w, h)
        free[pi] = split_free(free[pi], used)
        placements[item["name"]] = (first_page + pi, rx, ry)
        for row in range(item["h"]):
            src = row * item["w"] * 4
            dst = ((ry + row) * PAGE + rx) * 4
            pages[pi][dst:dst + item["w"] * 4] = item["rgba"][src:src + item["w"] * 4]
    return pages, placements


def make_assets(assets: pathlib.Path, output: pathlib.Path, header: pathlib.Path) -> None:
    global FFMPEG
    christmas = assets / "week5/images/christmas"
    work: list[dict] = []
    records: list[tuple[str, int, int, int, int, int, int]] = []
    fixed_pages = [bytearray(PAGE_BYTES * 4), bytearray(PAGE_BYTES * 4)]

    def add(name: str, rgba: bytearray, w: int, h: int, anchor: tuple[int, int] = (0, 0)) -> None:
        pixels, tw, th, dx, dy = trim(rgba, w, h, *anchor)
        work.append({"name": name, "rgba": pixels, "w": tw, "h": th, "dx": dx, "dy": dy})

    # Dedicated full-bleed background plates, one per mall variant.
    for page, source in enumerate(("bgWalls.png", "evilBG.png")):
        sw, sh = png_size(christmas / source)
        filters = ("scale=256:192:force_original_aspect_ratio=increase:flags=area," 
                   "crop=256:192:(iw-ow)/2:(ih-oh)/2,format=rgba")
        plate = run_ffmpeg(FFMPEG, christmas / source, filters, 256, 192)
        fixed_pages[page][:256 * 4 * 192] = plate[:256 * 4 * 192]
        records.append(("STAGE_XMAS" if page == 0 else "STAGE_EVIL", page, 0, 0, 256, 192, 0))

    def resized_prop(name: str, source: str, size: tuple[int, int], contain: bool = True) -> None:
        w, h = size
        if contain:
            filters = (f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=area,"
                       f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black@0,format=rgba")
        else:
            filters = (f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=area,"
                       f"crop={w}:{h}:(iw-ow)/2:(ih-oh)/2,format=rgba")
        add(name, run_ffmpeg(FFMPEG, christmas / source, filters, w, h), w, h)

    # Props remain independent so their official depth/parallax can be applied.
    resized_prop("ESCALATOR", "bgEscalator.png", (224, 112))
    resized_prop("TREE_XMAS", "christmasTree.png", (76, 118))
    resized_prop("TREE_EVIL", "evilTree.png", (70, 118))
    resized_prop("SNOW_XMAS", "fgSnow.png", (252, 30))
    resized_prop("SNOW_EVIL", "evilSnow.png", (252, 30))

    upper_xml, upper_png = christmas / "upperBop.xml", christmas / "upperBop.png"
    lower_xml, lower_png = christmas / "bottomBop.xml", christmas / "bottomBop.png"
    for i, index in enumerate((0, 2, 4, 6)):
        nodes = [n for n in ET.parse(upper_xml).getroot().findall("SubTexture")
                 if n.attrib.get("name", "").startswith("Upper Crowd Bob")]
        f = nodes[index]
        d = {k: int(f.attrib.get(k, 0)) for k in
             ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
        d["rotated"] = f.attrib.get("rotated", "false").lower() == "true"
        add(f"CROWD_UPPER_{i}", extract_sparrow_frame(str(FFMPEG), upper_png, d, (176, 38)), 176, 38)
    for i, index in enumerate((0, 2, 4, 6)):
        nodes = [n for n in ET.parse(lower_xml).getroot().findall("SubTexture")
                 if n.attrib.get("name", "").startswith("Bottom Level Boppers")]
        f = nodes[index]
        d = {k: int(f.attrib.get(k, 0)) for k in
             ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
        d["rotated"] = f.attrib.get("rotated", "false").lower() == "true"
        add(f"CROWD_LOWER_{i}", extract_sparrow_frame(str(FFMPEG), lower_png, d, (176, 54)), 176, 54)

    # Santa is now its own official foreground cel rather than painted into
    # the backdrop. Keep the source proportions and register its feet.
    santa_xml = ET.parse(christmas / "santa.xml").getroot()
    santa = next(n for n in santa_xml.findall("SubTexture")
                 if n.attrib.get("name", "").startswith("santa idle in fear"))
    sf = {k: int(santa.attrib.get(k, 0)) for k in
          ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
    sf["rotated"] = santa.attrib.get("rotated", "false").lower() == "true"
    santa_pixels = extract_sparrow_frame(str(FFMPEG), christmas / "santa.png", sf, (72, 84))
    add("SANTA", santa_pixels, 72, 84, (36, 84))

    # Regenerate every official character cel at higher source resolution,
    # then trim transparent margins while keeping the common foot/center anchor.
    # 80x96 is a 25% larger, tall character cell than the old square 64x64,
    # while remaining within the seven leased character/prop pages.
    cell_w, cell_h = 80, 96
    parents = Rig(assets / "shared/images/characters/parents-christmas", FFMPEG)
    parent_base = [112, 0, 28, 54, 83, 14, 41, 68, 97]
    parent_alt = [116, 7, 34, 61, 89, 21, 47, 75, 102]
    parent_names = ["PARENTS_IDLE", "PARENTS_MOM_DOWN", "PARENTS_MOM_UP", "PARENTS_MOM_RIGHT",
                    "PARENTS_MOM_LEFT", "PARENTS_DAD_DOWN", "PARENTS_DAD_UP", "PARENTS_DAD_RIGHT",
                    "PARENTS_DAD_LEFT", "PARENTS_IDLE_1", "PARENTS_MOM_DOWN_ALT", "PARENTS_MOM_UP_ALT",
                    "PARENTS_MOM_RIGHT_ALT", "PARENTS_MOM_LEFT_ALT", "PARENTS_DAD_DOWN_ALT",
                    "PARENTS_DAD_UP_ALT", "PARENTS_DAD_RIGHT_ALT", "PARENTS_DAD_LEFT_ALT"]
    for idx, pixels in fit_anchored_rig(parents, parent_base + parent_alt, cell_w, cell_h,
                                        anchor_frame_ids=parent_base).items():
        add(parent_names[(parent_base + parent_alt).index(idx)], pixels, cell_w, cell_h,
            (cell_w // 2, cell_h))

    monster = Rig(assets / "shared/images/characters/monster", FFMPEG)
    monster_base, monster_alt = [0, 16, 26, 36, 48], [8, 12, 20, 30, 42, 54]
    monster_names = ["MONSTER_IDLE", "MONSTER_RIGHT", "MONSTER_LEFT", "MONSTER_UP", "MONSTER_DOWN",
                     "MONSTER_IDLE_1", "MONSTER_IDLE_2", "MONSTER_RIGHT_ALT", "MONSTER_LEFT_ALT",
                     "MONSTER_UP_ALT", "MONSTER_DOWN_ALT"]
    for idx, pixels in fit_anchored_rig(monster, monster_base + monster_alt, cell_w, cell_h,
                                        anchor_frame_ids=monster_base).items():
        add(monster_names[(monster_base + monster_alt).index(idx)], pixels, cell_w, cell_h,
            (cell_w // 2, cell_h))

    gf = Rig(assets / "shared/images/characters/gf-christmas", FFMPEG)
    gf_ids = [0, 3, 6, 9, 12, 14, 17, 20, 23, 27]
    gf_names = ["GF_DANCE_0", "GF_DANCE_V143_0", "GF_DANCE_V143_1", "GF_DANCE_V143_2",
                "GF_DANCE_V143_3", "GF_DANCE_1", "GF_DANCE_V143_4", "GF_DANCE_V143_5",
                "GF_DANCE_V143_6", "GF_DANCE_V143_7"]
    for idx, pixels in fit_anchored_rig(gf, gf_ids, cell_w, cell_h,
                                        anchor_frame_ids=[0, 14]).items():
        add(gf_names[gf_ids.index(idx)], pixels, cell_w, cell_h, (cell_w // 2, cell_h))

    # The official Christmas Boyfriend art replaces the generic shared BF
    # cels for this stage. Two idle, two chant poses per lane, one miss per lane.
    bf_xml = assets / "shared/images/characters/bfChristmas.xml"
    bf_png = assets / "shared/images/characters/bfChristmas.png"
    bf_specs = [("BF_IDLE_0", "BF idle dance", 0), ("BF_IDLE_1", "BF idle dance", 2),
                ("BF_LEFT_0", "BF NOTE LEFT", 0), ("BF_LEFT_1", "BF NOTE LEFT", 4),
                ("BF_DOWN_0", "BF NOTE DOWN", 0), ("BF_DOWN_1", "BF NOTE DOWN", 4),
                ("BF_UP_0", "BF NOTE UP", 0), ("BF_UP_1", "BF NOTE UP", 4),
                ("BF_RIGHT_0", "BF NOTE RIGHT", 0), ("BF_RIGHT_1", "BF NOTE RIGHT", 4),
                ("BF_MISS_LEFT", "BF NOTE LEFT MISS", 16), ("BF_MISS_DOWN", "BF NOTE DOWN MISS", 14),
                ("BF_MISS_UP", "BF NOTE UP MISS", 12), ("BF_MISS_RIGHT", "BF NOTE RIGHT MISS", 20)]
    for name, prefix, sample in bf_specs:
        rgba = frame_from_sparrow(bf_xml, bf_png, prefix, sample, (cell_w, cell_h))
        add(name, rgba, cell_w, cell_h, (cell_w // 2, cell_h))

    # Crowd and snow frame assets are not all character anchored.
    dynamic, placements = packed_pages(work, 2)
    all_pages = fixed_pages + dynamic
    if len(all_pages) > MAX_PAGES:
        raise ValueError(f"atlas uses {len(all_pages)} pages; PS1 Week 5 budget is {MAX_PAGES}")

    # Add the fixed backgrounds to the palette sample and place records for
    # each dynamically packed frame.
    rgba_pages = [bytearray(PAGE_BYTES * 4) for _ in all_pages]
    for page_index in range(2):
        rgba_pages[page_index][:PAGE_BYTES * 4] = fixed_pages[page_index]
    for i, page in enumerate(dynamic):
        rgba_pages[i + 2][:] = page
    for item in work:
        page_index, u, v = placements[item["name"]]
        # placements are absolute page indices (2+); record dx/dy preserves
        # the original rig registration point after transparent-edge trimming.
        records.append((item["name"], page_index, u, v,
                        item["w"], item["h"], (item["dx"] & 0xFFFF) << 16 | (item["dy"] & 0xFFFF)))

    palette = median_palette(rgba_pages, 255)
    indexed_pages = [quantize(page, palette) for page in rgba_pages]
    clut = [0] + [rgb555(color) for color in palette[:255]]
    clut += [0] * (256 - len(clut))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(indexed_pages) + struct.pack("<256H", *clut))

    names = [r[0] for r in records]
    lines = ["/* Generated from pinned classic Week 5 assets by rebuild_week5_v167.py. */",
             "#ifndef PS1_WEEK5_VISUAL_DATA_H", "#define PS1_WEEK5_VISUAL_DATA_H",
             f"#define BOPEEBO_WEEK5_PAGE_COUNT {len(all_pages)}u",
             "#define BOPEEBO_WEEK5_CAMERA_ZOOM_Q8 460u",
             "#define BOPEEBO_WEEK5_CHARACTER_SCALE_Q8 171u",
             "#define BOPEEBO_WEEK5_BF_X 203", "#define BOPEEBO_WEEK5_BF_Y 163",
             "#define BOPEEBO_WEEK5_GF_X 131", "#define BOPEEBO_WEEK5_GF_Y 151",
             "#define BOPEEBO_WEEK5_OPP_X 57", "#define BOPEEBO_WEEK5_OPP_Y 153",
             "#define BOPEEBO_WEEK5_BASE_CAMERA_X 57", "#define BOPEEBO_WEEK5_BASE_CAMERA_Y 125",
             "typedef struct { uint8_t page, u, v; uint16_t w, h; int16_t dx, dy; } Week5VisualFrame;",
             "enum {"]
    for i, name in enumerate(names):
        lines.append(f"\tWEEK5_FRAME_{name} = {i},")
    lines.extend(["};", f"#define WEEK5_VISUAL_FRAME_COUNT {len(records)}u",
                  "static const Week5VisualFrame week5_visual_frames[WEEK5_VISUAL_FRAME_COUNT] = {"])
    for name, page, u, v, w, h, packed_off in records:
        dx = (packed_off >> 16) & 0xFFFF
        dy = packed_off & 0xFFFF
        if dx >= 32768: dx -= 65536
        if dy >= 32768: dy -= 65536
        lines.append(f"\t{{ {page}u, {u}u, {v}u, {w}u, {h}u, {dx}, {dy} }}, /* {name} */")
    lines.extend(["};", "#endif", ""])
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text("\n".join(lines), encoding="ascii")
    print(f"Week 5 visual atlas: {len(all_pages)} 8bpp pages, {len(records)} frames, {output.stat().st_size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=pathlib.Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--header", type=pathlib.Path, required=True)
    args = parser.parse_args()
    global FFMPEG
    FFMPEG = args.ffmpeg
    make_assets(args.assets, args.output, args.header)


if __name__ == "__main__":
    FFMPEG = "ffmpeg"
    main()

