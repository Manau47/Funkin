#!/usr/bin/env python3
"""Upsample only the Week 5 Christmas balcony crowd and escalator.

This reuses the v171 package for all unrelated pages, palettes, poses, audio,
and charts. The enlarged crowd/escalator frames are split into page-safe pieces
so their display size and positions can remain unchanged on the PS1.
"""
from __future__ import annotations

import argparse
import pathlib
import random
import re
import shutil
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rebuild_week5_v171_assets as base  # noqa: E402
from convert_bopeebo_visuals import run_ffmpeg  # noqa: E402

PAGE = 256
PAGE_BYTES = PAGE * PAGE
PAGE_CLUT_BYTES = 512
FRAME_RE = re.compile(
    r"^\s*\{\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,\s*(\d+)u,"
    r"\s*(-?\d+),\s*(-?\d+)\s*\},\s*/\*\s*(\w+)\s*\*/",
    re.MULTILINE,
)


def unpack_clut(raw: bytes, page_count: int, page: int) -> list[tuple[int, int, int]]:
    start = page_count * PAGE_BYTES + page * PAGE_CLUT_BYTES
    words = struct.unpack_from("<256H", raw, start)
    colors = []
    for word in words[1:]:
        r, g, b = word & 31, (word >> 5) & 31, (word >> 10) & 31
        colors.append(((r * 255 + 15) // 31, (g * 255 + 15) // 31,
                       (b * 255 + 15) // 31))
    return colors


def old_frame_rgba(raw: bytes, page_count: int, frame: dict,
                   palette: list[tuple[int, int, int]]) -> bytearray:
    if frame["page"] >= page_count:
        raise ValueError(f"old frame page out of range: {frame}")
    page_start = frame["page"] * PAGE_BYTES
    rgba = bytearray(frame["w"] * frame["h"] * 4)
    for y in range(frame["h"]):
        for x in range(frame["w"]):
            index = raw[page_start + (frame["v"] + y) * PAGE + frame["u"] + x]
            i = (y * frame["w"] + x) * 4
            if index:
                rgba[i:i + 4] = bytes((*palette[index - 1], 255))
    return rgba


def frame_desc(header: str) -> dict[str, dict[str, int]]:
    found = {}
    for m in FRAME_RE.finditer(header):
        page, u, v, w, h, dx, dy, name = m.groups()
        found[name] = dict(page=int(page), u=int(u), v=int(v), w=int(w),
                           h=int(h), dx=int(dx), dy=int(dy))
    return found


def add_split(items: list[dict], name: str, rgba: bytearray, width: int,
              height: int, split_at: int = 192,
              preserve_canvas: bool = False,
              canvas_origin: tuple[int, int] = (0, 0)) -> list[str]:
    # Animated cels must share the same logical frame rectangle. Trimming each
    # independently can turn small alpha-bound changes into visible 1px jumps
    # when integer PS1 scaling rounds their separate offsets and dimensions.
    # Static props still trim to their visible bounds to save atlas space.
    if preserve_canvas:
        cropped, w, h = rgba, width, height
        dx, dy = canvas_origin
    else:
        # Runtime quantization treats alpha < 128 as transparent. Trim to that
        # same visible boundary so Lanczos fringe pixels cannot move the anchor.
        cropped, w, h, dx, dy = trim_visible(rgba, width, height)
    if w > 3 * split_at:
        raise ValueError(f"{name} wider than three VRAM-safe parts: {w}px")
    names = []
    part = 0
    for x0 in range(0, w, split_at):
        pw = min(split_at, w - x0)
        pixels = bytearray(pw * h * 4)
        for y in range(h):
            src = (y * w + x0) * 4
            dst = y * pw * 4
            pixels[dst:dst + pw * 4] = cropped[src:src + pw * 4]
        part_name = f"{name}_PART_{part}"
        items.append({"name": part_name, "rgba": pixels, "w": pw, "h": h,
                      "dx": dx + x0, "dy": dy})
        names.append(part_name)
        part += 1
    if len(names) not in (2, 3):
        raise ValueError(f"expected two or three pieces for {name}, got {len(names)}")
    return names


def trim_visible(rgba: bytearray, width: int, height: int) -> tuple[bytearray, int, int, int, int]:
    x0, y0, x1, y1 = width, height, -1, -1
    for y in range(height):
        for x in range(width):
            if rgba[(y * width + x) * 4 + 3] < 128:
                continue
            x0, y0 = min(x0, x), min(y0, y)
            x1, y1 = max(x1, x + 1), max(y1, y + 1)
    if x1 < 0:
        raise ValueError("refusing to pack a fully transparent detail frame")
    w, h = x1 - x0, y1 - y0
    out = bytearray(w * h * 4)
    for y in range(h):
        src = ((y + y0) * width + x0) * 4
        dst = y * w * 4
        out[dst:dst + w * 4] = rgba[src:src + w * 4]
    return out, w, h, x0, y0


def extract_sparrow_lanczos(ffmpeg: str, png: pathlib.Path, frame: dict,
                            size: tuple[int, int]) -> bytearray:
    if frame["rotated"]:
        raise ValueError(f"selected Sparrow frame is rotated and unsupported: {frame['name']}")
    out_w, out_h = size
    fw = max(int(frame["frameWidth"]), int(frame["width"]))
    fh = max(int(frame["frameHeight"]), int(frame["height"]))
    pad_x = max(0, -int(frame["frameX"]))
    pad_y = max(0, -int(frame["frameY"]))
    filters = (
        f"crop={frame['width']}:{frame['height']}:{frame['x']}:{frame['y']},"
        f"pad={fw}:{fh}:{pad_x}:{pad_y}:color=0x00000000,"
        f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease:flags=lanczos,"
        # Match extract_sparrow_frame's bottom registration exactly. Centering
        # vertically here changed the crowd's anchor relative to v177.
        f"pad={out_w}:{out_h}:(ow-iw)/2:oh-ih:color=0x00000000,format=rgba"
    )
    return run_ffmpeg(ffmpeg, png, filters, out_w, out_h)


def pack_two_pages(items: list[dict]) -> tuple[list[bytearray], dict[str, tuple[int, int, int]]]:
    """Deterministic MaxRects attempts with alternate orders for two fixed pages."""
    rng = random.Random(0xF17E)
    orders = []
    sort_keys = (
        lambda it: (-(it["w"] * it["h"]), -max(it["w"], it["h"]), it["name"]),
        lambda it: (-max(it["w"], it["h"]), -(it["w"] * it["h"]), it["name"]),
        lambda it: (-it["h"], -it["w"], it["name"]),
        lambda it: (-it["w"], -it["h"], it["name"]),
        lambda it: (-(it["w"] + it["h"]), -(it["w"] * it["h"]), it["name"]),
    )
    for key in sort_keys:
        orders.append(sorted(items, key=key))
    for _ in range(1000):
        order = list(items)
        rng.shuffle(order)
        orders.append(order)

    def intersects(a, b):
        return not (a[0] >= b[0] + b[2] or a[0] + a[2] <= b[0] or
                    a[1] >= b[1] + b[3] or a[1] + a[3] <= b[1])

    def split_free(rects, used):
        out = []
        ux, uy, uw, uh = used
        for rx, ry, rw, rh in rects:
            if not intersects((rx, ry, rw, rh), used):
                out.append((rx, ry, rw, rh)); continue
            if ux > rx: out.append((rx, ry, ux - rx, rh))
            if ux + uw < rx + rw: out.append((ux + uw, ry, rx + rw - ux - uw, rh))
            if uy > ry: out.append((rx, ry, rw, uy - ry))
            if uy + uh < ry + rh: out.append((rx, uy + uh, rw, ry + rh - uy - uh))
        out = [r for r in out if r[2] > 0 and r[3] > 0]
        keep = []
        for i, a in enumerate(out):
            ax, ay, aw, ah = a
            if any(i != j and ax >= bx and ay >= by and ax + aw <= bx + bw and
                   ay + ah <= by + bh for j, (bx, by, bw, bh) in enumerate(out)):
                continue
            keep.append(a)
        return keep

    def attempt(order):
        free = [[(0, 0, PAGE, PAGE)], [(0, 0, PAGE, PAGE)]]
        pages = [bytearray(PAGE_BYTES * 4), bytearray(PAGE_BYTES * 4)]
        placements = {}
        rasters = {}
        for item in order:
            w, h = item["w"], item["h"]
            if w > PAGE or h > PAGE: return None
            key = (w, h, bytes(item["rgba"]))
            if key in rasters:
                placements[item["name"]] = rasters[key]
                continue
            best = None
            for pi, rects in enumerate(free):
                for ri, (rx, ry, rw, rh) in enumerate(rects):
                    if w <= rw and h <= rh:
                        score = (min(rw - w, rh - h), max(rw - w, rh - h), pi, ry, rx, ri)
                        if best is None or score < best[0]: best = (score, pi, ri, rx, ry)
            if best is None: return None
            _score, pi, _ri, x, y = best
            used = (x, y, w, h)
            free[pi] = split_free(free[pi], used)
            placements[item["name"]] = (8 + pi, x, y)
            rasters[key] = placements[item["name"]]
            for row in range(h):
                src = row * w * 4
                dst = ((y + row) * PAGE + x) * 4
                pages[pi][dst:dst + w * 4] = item["rgba"][src:src + w * 4]
        return pages, placements

    for order in orders:
        result = attempt(order)
        if result is not None:
            return result
    raise ValueError("background detail rectangles do not fit in two 256x256 pages")


def write_variant_package(base_dir: pathlib.Path, output_dir: pathlib.Path,
                          assets: pathlib.Path, ffmpeg: str,
                          detail_q8: int) -> None:
    if detail_q8 < 257 or detail_q8 > 512:
        raise ValueError("detail factor must be between just over 1x and 2x")
    header_path = base_dir / "week5_visual_data.h"
    scene_path = base_dir / "week5-scene.bin"
    header = header_path.read_text(encoding="ascii")
    raw = scene_path.read_bytes()
    m = re.search(r"#define BOPEEBO_WEEK5_PAGE_COUNT (\d+)u", header)
    if not m:
        raise ValueError("missing page count in source package header")
    old_pages = int(m.group(1))
    if len(raw) != old_pages * (PAGE_BYTES + PAGE_CLUT_BYTES):
        raise ValueError("source W5 package size does not match its page header")
    frames = frame_desc(header)
    for name in ("ESCALATOR", "CROWD_UPPER_0", "CROWD_UPPER_1",
                 "CROWD_UPPER_2", "CROWD_UPPER_3", "CROWD_LOWER_2"):
        if name not in frames:
            raise ValueError(f"source header is missing frame {name}")
    if any(frames[n]["page"] != 8 for n in
           ("ESCALATOR", "CROWD_UPPER_0", "CROWD_UPPER_1",
            "CROWD_UPPER_2", "CROWD_UPPER_3", "CROWD_LOWER_2")):
        raise ValueError("expected the source balcony/escalator frames on logical page 8")

    christmas = assets / "week5/images/christmas"
    palette8 = unpack_clut(raw, old_pages, 8)
    work: list[dict] = []
    replacement_parts: dict[str, list[str]] = {}

    # Preserve the existing lower-crowd frame that shared the old page with
    # the target sprites; it is moved losslessly with the same page palette.
    lower = frames["CROWD_LOWER_2"]
    lower_rgba = old_frame_rgba(raw, old_pages, lower, palette8)
    lower_cropped, lw, lh, ldx, ldy = base.trim(lower_rgba, lower["w"], lower["h"],
                                                lower["dx"], lower["dy"])
    work.append({"name": "CROWD_LOWER_2_KEEP", "rgba": lower_cropped,
                 "w": lw, "h": lh, "dx": ldx, "dy": ldy})

    # Use the official high-resolution source sheets. Lanczos reduces the
    # 4K source art to 1.5x the current in-game texture resolution.
    upper_xml = ET.parse(christmas / "upperBop.xml").getroot()
    upper_nodes = [n for n in upper_xml.findall("SubTexture")
                   if n.attrib.get("name", "").startswith("Upper Crowd Bob")]
    for pose, index in enumerate((0, 2, 4, 6)):
        node = upper_nodes[index]
        desc = {k: int(node.attrib.get(k, 0)) for k in
                ("x", "y", "width", "height", "frameX", "frameY",
                 "frameWidth", "frameHeight")}
        desc["rotated"] = node.attrib.get("rotated", "false").lower() == "true"
        desc["name"] = node.attrib.get("name", f"upper-{pose}")
        w = (256 * detail_q8 + 128) // 256
        h = (40 * detail_q8 + 128) // 256
        frame = extract_sparrow_lanczos(str(ffmpeg), christmas / "upperBop.png", desc,
                                        (w, h))
        # All four cels use the same 384x55 window (the final 55 rows of the
        # 384x60 canonical raster). Their metadata already shares a common
        # baseline; retaining this common window avoids per-pose trim/rounding
        # jitter while keeping the three page-safe 128px strips.
        stable_h = h - 5
        stable = bytearray(w * stable_h * 4)
        for row in range(stable_h):
            src = ((row + 5) * w) * 4
            dst = row * w * 4
            stable[dst:dst + w * 4] = frame[src:src + w * 4]
        names = add_split(work, f"CROWD_UPPER_{pose}", stable, w, stable_h,
                          split_at=128, preserve_canvas=True, canvas_origin=(0, 5))
        replacement_parts[f"CROWD_UPPER_{pose}"] = names

    escalator_w = (224 * detail_q8 + 128) // 256
    escalator_h = (112 * detail_q8 + 128) // 256
    escalator_rgba = run_ffmpeg(
        ffmpeg, christmas / "bgEscalator.png",
        f"scale={escalator_w}:{escalator_h}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={escalator_w}:{escalator_h}:(ow-iw)/2:(oh-ih)/2:color=black@0,format=rgba",
        escalator_w, escalator_h)
    replacement_parts["ESCALATOR"] = add_split(work, "ESCALATOR", escalator_rgba,
                                               escalator_w, escalator_h, split_at=128)

    packed_rgba, placements = pack_two_pages(work)

    # Keep base background/common pages 0..7 and the unrelated Xmas page 9
    # byte-identical. Logical page 10 leases the spare 8bpp page; the old Evil
    # page moves to logical 11. Both new page 8/10 CLUTs intentionally reuse
    # the old page 8 palette, protecting the existing stage colors.
    texture_pages = [raw[i * PAGE_BYTES:(i + 1) * PAGE_BYTES]
                     for i in range(old_pages)]
    cluts = [raw[old_pages * PAGE_BYTES + i * PAGE_CLUT_BYTES:
               old_pages * PAGE_BYTES + (i + 1) * PAGE_CLUT_BYTES]
             for i in range(old_pages)]
    new_texture_pages: dict[int, bytes] = {}
    new_page_records: dict[str, tuple[int, int, int, int, int, int, int]] = {}
    for pi, page_rgba in enumerate(packed_rgba):
        page_index = 8 if pi == 0 else 10
        indices = base.quantize(page_rgba, palette8)
        new_texture_pages[page_index] = bytes(indices)
    for item in work:
        old_page, u, v = placements[item["name"]]
        page_index = 8 if old_page == 8 else 10
        new_page_records[item["name"]] = (page_index, u, v, item["w"], item["h"],
                                           item["dx"], item["dy"])

    pages_out = texture_pages[:8] + [
        new_texture_pages[8], texture_pages[9], new_texture_pages[10], texture_pages[10]
    ]
    cluts_out = cluts[:8] + [cluts[8], cluts[9], cluts[8], cluts[10]]
    output_bytes = b"".join(pages_out) + b"".join(cluts_out)
    if pages_out[11] != texture_pages[10]:
        raise ValueError("Evil Mall source texture page was not preserved at logical page 11")
    if pages_out[10] == texture_pages[10]:
        raise ValueError("Xmas detail page unexpectedly aliases the Evil Mall texture")

    def record_line(name: str, record: tuple[int, int, int, int, int, int, int]) -> str:
        p, u, v, w, h, dx, dy = record
        return f"\t{{ {p}u, {u}u, {v}u, {w}u, {h}u, {dx}, {dy} }}, /* {name} */"

    # Replace records for target sprites and shift old Evil page references.
    updated = header
    for name, parts in replacement_parts.items():
        first = new_page_records[parts[0]]
        updated = FRAME_RE.sub(lambda m: record_line(name, first)
                               if m.group(8) == name else m.group(0), updated)
    lower_rec = new_page_records["CROWD_LOWER_2_KEEP"]
    updated = FRAME_RE.sub(lambda m: record_line("CROWD_LOWER_2", lower_rec)
                           if m.group(8) == "CROWD_LOWER_2" else m.group(0), updated)
    # Shift existing logical page 10 (Evil) to page 11, but leave fresh page-10
    # Christmas pieces and the repacked lower-crowd record untouched.
    def shift_evil(m: re.Match[str]) -> str:
        if (int(m.group(1)) == 10 and m.group(8) not in replacement_parts
                and m.group(8) != "CROWD_LOWER_2"):
            return record_line(m.group(8), (11, *(int(m.group(i)) for i in range(2, 8))))
        return m.group(0)
    updated = FRAME_RE.sub(shift_evil, updated)

    appended = []
    next_id = int(re.search(r"#define WEEK5_VISUAL_FRAME_COUNT (\d+)u", updated).group(1))
    for base_name, parts in replacement_parts.items():
        for part_index, part_name in enumerate(parts[1:], start=1):
            public_name = f"{base_name}_PART_{part_index}"
            appended.append((public_name, next_id, new_page_records[part_name]))
            next_id += 1

    # Add enum aliases after the existing entries and append records at the end,
    # keeping every pre-existing frame ID unchanged.
    enum_end = re.search(r"(\s*WEEK5_FRAME_BF_MISS_RIGHT\s*=\s*\d+,[ \t]*\n)(};)", updated)
    if not enum_end:
        raise ValueError("could not locate the end of the generated frame enum")
    enum_extra = "".join(f"\tWEEK5_FRAME_{name} = {idx},\n"
                         for name, idx, _rec in appended)
    updated = updated[:enum_end.end(1)] + enum_extra + updated[enum_end.end(1):]
    count_match = re.search(r"#define WEEK5_VISUAL_FRAME_COUNT (\d+)u", updated)
    old_count = int(count_match.group(1))
    updated = updated.replace(f"#define WEEK5_VISUAL_FRAME_COUNT {old_count}u",
                              f"#define WEEK5_VISUAL_FRAME_COUNT {next_id}u", 1)
    records_end = updated.rfind("};")
    updated = updated[:records_end] + "".join(record_line(name, record) + "\n"
                                               for name, _idx, record in appended) + updated[records_end:]
    updated = updated.replace(f"#define BOPEEBO_WEEK5_PAGE_COUNT {old_pages}u",
                              "#define BOPEEBO_WEEK5_PAGE_COUNT 12u", 1)
    updated = updated.replace("#define BOPEEBO_WEEK5_XMAS_PAGE_COUNT 2u",
                              "#define BOPEEBO_WEEK5_XMAS_PAGE_COUNT 3u", 1)
    updated = updated.replace(f"#define BOPEEBO_WEEK5_EVIL_FIRST_PAGE {old_pages - 1}u",
                              "#define BOPEEBO_WEEK5_EVIL_FIRST_PAGE 11u", 1)
    updated = updated.replace("#define BOPEEBO_WEEK5_PALETTE_SECTORS 3u",
                              "#define BOPEEBO_WEEK5_PALETTE_SECTORS 3u", 1)
    updated = updated.replace("#define BOPEEBO_WEEK5_CAMERA_ZOOM_Q8 460u",
        "#define BOPEEBO_WEEK5_BACKDROP_DETAIL_SPLIT 1\n" +
        "#define BOPEEBO_WEEK5_CAMERA_ZOOM_Q8 460u", 1)
    macro_anchor = "#define BOPEEBO_WEEK5_CAMERA_ZOOM_Q8 460u"
    updated = updated.replace(macro_anchor,
        f"#define BOPEEBO_WEEK5_UPPER_CROWD_DETAIL_Q8 {detail_q8}u\n"
        f"#define BOPEEBO_WEEK5_ESCALATOR_DETAIL_Q8 {detail_q8}u\n" + macro_anchor, 1)
    if len(output_bytes) != 12 * (PAGE_BYTES + PAGE_CLUT_BYTES):
        raise ValueError("unexpected final package length")

    output_dir.mkdir(parents=True, exist_ok=True)
    for path in base_dir.iterdir():
        dest = output_dir / path.name
        if path.is_dir():
            if dest.exists(): shutil.rmtree(dest)
            shutil.copytree(path, dest)
        elif path.name not in ("week5-scene.bin", "week5_visual_data.h"):
            shutil.copy2(path, dest)
    (output_dir / "week5-scene.bin").write_bytes(output_bytes)
    (output_dir / "week5_visual_data.h").write_text(updated, encoding="ascii")
    print(f"W5 background detail {detail_q8}/256: {len(packed_rgba)} packed pages, "
          f"12 logical pages, {len(output_bytes)} bytes, {len(appended)} extra draw frames")
    print("Unchanged common/background and side Christmas pages were copied from the base package.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-package", type=pathlib.Path, required=True)
    parser.add_argument("--assets", type=pathlib.Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--detail-q8", type=int, default=384,
                        help="source-raster multiplier; 384 is 1.5x")
    args = parser.parse_args()
    write_variant_package(args.base_package, args.output, args.assets,
                          args.ffmpeg, args.detail_q8)


if __name__ == "__main__":
    main()
