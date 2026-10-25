#!/usr/bin/env python3
"""Convert a small, deterministic PS1 Bopeebo scene from the pinned assets."""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from animate_preview import Rig


SCENE_W = 320
STAGE_BACK_H = 176
STAGE_FRONT_H = 56
FRAME_W = 64
FRAME_H = 96
GF_W = 80
GF_H = 80
PAGE_W = 256
PAGE_H = 256
PAGE_BYTES = PAGE_W * PAGE_H // 2

BF_ANIMS = [
    ("idle", "BF idle dance"),
    ("left", "BF NOTE LEFT"),
    ("down", "BF NOTE DOWN"),
    ("up", "BF NOTE UP"),
    ("right", "BF NOTE RIGHT"),
    ("miss_left", "BF NOTE LEFT MISS"),
    ("miss_down", "BF NOTE DOWN MISS"),
    ("miss_up", "BF NOTE UP MISS"),
    ("miss_right", "BF NOTE RIGHT MISS"),
]


def run_ffmpeg(ffmpeg: str, source: pathlib.Path, filters: str, width: int, height: int) -> bytearray:
    command = [
        ffmpeg, "-v", "error", "-i", str(source), "-vf", filters,
        "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1",
    ]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    expected = width * height * 4
    if len(result.stdout) != expected:
        raise ValueError(f"unexpected RGBA size from {source}: {len(result.stdout)} != {expected}")
    return bytearray(result.stdout)


def atlas_frames(xml_path: pathlib.Path) -> dict[str, list[dict[str, int | str]]]:
    groups: dict[str, list[dict[str, int | str]]] = collections.defaultdict(list)
    for elem in ET.parse(xml_path).getroot().findall("SubTexture"):
        name = elem.attrib["name"]
        match = re.fullmatch(r"(.*?)(\d+)", name)
        if not match:
            continue
        frame = {k: int(elem.attrib.get(k, "0")) for k in ("x", "y", "width", "height")}
        frame["frameX"] = int(elem.attrib.get("frameX", "0"))
        frame["frameY"] = int(elem.attrib.get("frameY", "0"))
        frame["frameWidth"] = int(elem.attrib.get("frameWidth", str(frame["width"])))
        frame["frameHeight"] = int(elem.attrib.get("frameHeight", str(frame["height"])))
        frame["rotated"] = elem.attrib.get("rotated", "false").lower() == "true"
        frame["index"] = int(match.group(2))
        frame["name"] = name
        groups[match.group(1)].append(frame)
    for frames in groups.values():
        frames.sort(key=lambda frame: int(frame["index"]))
    return groups


def extract_sparrow_frame(ffmpeg: str, png: pathlib.Path, frame: dict, size: tuple[int, int]) -> bytearray:
    if frame["rotated"]:
        raise ValueError(f"selected Sparrow frame is rotated and unsupported: {frame['name']}")
    w, h = size
    fw = max(int(frame["frameWidth"]), int(frame["width"]))
    fh = max(int(frame["frameHeight"]), int(frame["height"]))
    pad_x = max(0, -int(frame["frameX"]))
    pad_y = max(0, -int(frame["frameY"]))
    filters = (
        f"crop={frame['width']}:{frame['height']}:{frame['x']}:{frame['y']},"
        f"pad={fw}:{fh}:{pad_x}:{pad_y}:color=0x00000000,"
        f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=neighbor,"
        f"pad={w}:{h}:(ow-iw)/2:oh-ih:color=0x00000000,format=rgba"
    )
    return run_ffmpeg(ffmpeg, png, filters, w, h)


def extract_stage(ffmpeg: str, png: pathlib.Path, width: int, height: int) -> bytearray:
    # The source stage is 8x larger than the PS1 output. Area downsampling
    # preserves thin architecture and curtains without runtime bilinear blur.
    filters = f"scale={width}:{height}:flags=area,format=rgba"
    return run_ffmpeg(ffmpeg, png, filters, width, height)


def alpha_over(background: bytearray, foreground: bytearray) -> bytearray:
    if len(background) != len(foreground) or len(background) % 4:
        raise ValueError("layer dimensions do not match")
    result = bytearray(background)
    for i in range(0, len(result), 4):
        alpha = foreground[i + 3]
        if not alpha:
            continue
        if alpha == 255:
            result[i:i + 4] = foreground[i:i + 4]
            continue
        inv = 255 - alpha
        for c in range(3):
            result[i + c] = (foreground[i + c] * alpha + result[i + c] * inv) // 255
        result[i + 3] = alpha + result[i + 3] * inv // 255
    return result


def fit_nearest(pixels: bytearray, width: int, height: int,
                out_w: int, out_h: int) -> bytearray:
    scale = min(out_w / width, out_h / height)
    scaled_w = max(1, min(out_w, round(width * scale)))
    scaled_h = max(1, min(out_h, round(height * scale)))
    xoff, yoff = (out_w - scaled_w) // 2, (out_h - scaled_h) // 2
    out = bytearray(out_w * out_h * 4)
    for y in range(scaled_h):
        sy = min(height - 1, y * height // scaled_h)
        for x in range(scaled_w):
            sx = min(width - 1, x * width // scaled_w)
            si = (sy * width + sx) * 4
            di = ((y + yoff) * out_w + x + xoff) * 4
            out[di:di + 4] = pixels[si:si + 4]
    return out


def new_canvas(width: int, height: int) -> bytearray:
    return bytearray(width * height * 4)


def fill_rect(pixels: bytearray, width: int, height: int, x0: int, y0: int,
              x1: int, y1: int, color: tuple[int, int, int]) -> None:
    for y in range(max(0, y0), min(height, y1)):
        for x in range(max(0, x0), min(width, x1)):
            i = (y * width + x) * 4
            pixels[i:i + 4] = bytes((*color, 255))


def fill_ellipse(pixels: bytearray, width: int, height: int, cx: int, cy: int,
                 rx: int, ry: int, color: tuple[int, int, int]) -> None:
    for y in range(max(0, cy - ry), min(height, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(width, cx + rx + 1)):
            if ((x - cx) * (x - cx) * ry * ry +
                    (y - cy) * (y - cy) * rx * rx <= rx * rx * ry * ry):
                i = (y * width + x) * 4
                pixels[i:i + 4] = bytes((*color, 255))


def fill_polygon(pixels: bytearray, width: int, height: int,
                 points: tuple[tuple[int, int], ...], color: tuple[int, int, int]) -> None:
    for y in range(max(0, min(p[1] for p in points)), min(height, max(p[1] for p in points) + 1)):
        intersections = []
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
            if (y0 <= y < y1) or (y1 <= y < y0):
                intersections.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
        intersections.sort()
        for left, right in zip(intersections[::2], intersections[1::2]):
            fill_rect(pixels, width, height, left, y, right + 1, y + 1, color)


def dad_pose(variation: int) -> bytearray:
    """Create a tiny, crisp stand-in from Dad's official palette and silhouette cues."""
    w, h = FRAME_W, FRAME_H
    p = new_canvas(w, h)
    purple, dark, skin, shirt = (143, 68, 180), (35, 25, 49), (246, 197, 220), (231, 226, 236)
    bob = variation & 1
    fill_polygon(p, w, h, ((12, 49), (51, 47), (59, 85), (47, 91), (17, 86)), dark)
    fill_polygon(p, w, h, ((15, 48), (48, 46), (54, 80), (43, 85), (18, 82)), purple)
    fill_polygon(p, w, h, ((23, 53), (42, 52), (37, 70), (27, 67)), shirt)
    fill_rect(p, w, h, 18, 80, 28, 95, dark)
    fill_rect(p, w, h, 39, 80, 48, 95, dark)
    fill_ellipse(p, w, h, 32, 30 + bob, 15, 19, dark)
    fill_ellipse(p, w, h, 32, 29 + bob, 13, 17, skin)
    fill_polygon(p, w, h, ((17, 26), (14, 13), (23, 18), (27, 7), (33, 16),
                           (43, 9), (43, 19), (51, 15), (47, 30), (39, 24), (23, 27)), purple)
    fill_rect(p, w, h, 22, 29 + bob, 29, 32 + bob, dark)
    fill_rect(p, w, h, 36, 29 + bob, 43, 32 + bob, dark)
    fill_rect(p, w, h, 30, 38 + bob, 36, 40 + bob, dark)
    # One arm and microphone read clearly at native resolution; alternate by chart-lane pose.
    arm_x = 7 if variation % 4 in (0, 2) else 46
    fill_polygon(p, w, h, ((18, 50), (24, 54), (arm_x + 7, 66), (arm_x, 62)), skin)
    fill_rect(p, w, h, arm_x, 54, arm_x + 6, 66, dark)
    fill_ellipse(p, w, h, arm_x + 3, 52, 5, 6, (95, 102, 119))
    return p


def gf_pose(variation: int) -> bytearray:
    """Create a small rhythm-dance stand-in with GF's pink hair and red outfit."""
    w, h = GF_W, GF_H
    p = new_canvas(w, h)
    pink, darkpink, skin, red, dark = (245, 60, 145), (156, 36, 92), (255, 202, 170), (203, 44, 91), (32, 20, 40)
    bob = (variation & 1) * 2
    # Seated pose over the iconic speaker pair.
    fill_rect(p, w, h, 5, 57, 39, 79, dark)
    fill_rect(p, w, h, 41, 57, 75, 79, dark)
    fill_ellipse(p, w, h, 22, 68, 8, 8, (88, 54, 115))
    fill_ellipse(p, w, h, 58, 68, 8, 8, (88, 54, 115))
    fill_ellipse(p, w, h, 42, 23 + bob, 22, 23, darkpink)
    fill_ellipse(p, w, h, 43, 23 + bob, 16, 18, skin)
    fill_ellipse(p, w, h, 42, 12 + bob, 21, 12, pink)
    hair_x = 12 if variation % 2 == 0 else 53
    fill_polygon(p, w, h, ((25, 12 + bob), (15, 4 + bob), (12, 28 + bob),
                           (17, 48), (25, 40), (30, 23 + bob)), pink)
    fill_polygon(p, w, h, ((56, 12 + bob), (69, 19), (68, 43), (58, 49),
                           (54, 33 + bob)), pink)
    fill_rect(p, w, h, 34, 24 + bob, 38, 27 + bob, dark)
    fill_rect(p, w, h, 47, 24 + bob, 51, 27 + bob, dark)
    fill_polygon(p, w, h, ((29, 43), (56, 42), (64, 59), (46, 64), (26, 58)), red)
    fill_polygon(p, w, h, ((30, 55), (43, 58), (33, 70), (21, 68)), skin)
    fill_polygon(p, w, h, ((47, 58), (61, 54), (69, 65), (54, 69)), skin)
    fill_ellipse(p, w, h, hair_x, 32 + bob, 6, 14, pink)
    return p


def median_palette(images: list[bytearray], max_colors: int = 15) -> list[tuple[int, int, int]]:
    histogram: collections.Counter[tuple[int, int, int]] = collections.Counter()
    for pixels in images:
        for i in range(0, len(pixels), 4):
            if pixels[i + 3] >= 128:
                histogram[(pixels[i], pixels[i + 1], pixels[i + 2])] += 1
    if not histogram:
        return [(1, 1, 1)]
    boxes = [list(histogram.items())]
    while len(boxes) < max_colors:
        candidates = [(max(max(c[k] for c, _ in box) - min(c[k] for c, _ in box) for k in range(3)), i)
                      for i, box in enumerate(boxes) if len(box) > 1]
        if not candidates:
            break
        _, index = max(candidates)
        box = boxes.pop(index)
        channel = max(range(3), key=lambda k: max(c[k] for c, _ in box) - min(c[k] for c, _ in box))
        box.sort(key=lambda item: item[0][channel])
        total = sum(n for _, n in box)
        running, split = 0, 1
        for split in range(1, len(box)):
            running += box[split - 1][1]
            if running * 2 >= total:
                break
        boxes.extend((box[:split], box[split:]))
    palette = []
    for box in boxes:
        total = sum(n for _, n in box)
        palette.append(tuple(sum(color[k] * n for color, n in box) // total for k in range(3)))
    return palette[:max_colors]


def nearest_palette_index(rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> int:
    return min(range(len(palette)), key=lambda i: sum((rgb[c] - palette[i][c]) ** 2 for c in range(3))) + 1


def quantize(pixels: bytearray, palette: list[tuple[int, int, int]]) -> bytearray:
    indices = bytearray(len(pixels) // 4)
    cache: dict[tuple[int, int, int], int] = {}
    for i in range(len(indices)):
        alpha = pixels[i * 4 + 3]
        if alpha < 128:
            continue
        rgb = (pixels[i * 4], pixels[i * 4 + 1], pixels[i * 4 + 2])
        if rgb not in cache:
            cache[rgb] = nearest_palette_index(rgb, palette)
        indices[i] = cache[rgb]
    return indices


def pack_page(images: list[tuple[str, bytearray, int, int]], first_page: int,
              palette_index: int, page_data: list[bytearray], descriptors: dict[str, dict]) -> int:
    page_no = first_page
    x = y = row_h = 0
    if not page_data or len(page_data) <= page_no:
        page_data.append(bytearray(PAGE_BYTES))
    for name, indices, width, height in images:
        if x + width > PAGE_W:
            x, y, row_h = 0, y + row_h, 0
        if y + height > PAGE_H:
            page_no += 1
            page_data.append(bytearray(PAGE_BYTES))
            x = y = row_h = 0
        page = page_data[page_no]
        for py in range(height):
            for px in range(width):
                value = indices[py * width + px]
                pos = (y + py) * PAGE_W + x + px
                byte_pos = pos >> 1
                if pos & 1:
                    page[byte_pos] |= value << 4
                else:
                    page[byte_pos] |= value
        descriptors[name] = {"page": page_no, "palette": palette_index, "u": x, "v": y, "w": width, "h": height}
        x += width
        row_h = max(row_h, height)
    return page_no + 1


def pack_8bpp(images: list[tuple[str, bytearray, int, int]], first_page: int,
              palette_index: int, pages: list[bytearray], descriptors: dict[str, dict]) -> int:
    page_no = first_page
    x = y = row_h = 0
    if len(pages) <= page_no:
        pages.append(bytearray(PAGE_W * PAGE_H))
    for name, indices, width, height in images:
        if x + width > PAGE_W:
            x, y, row_h = 0, y + row_h, 0
        if y + height > PAGE_H:
            page_no += 1
            pages.append(bytearray(PAGE_W * PAGE_H))
            x = y = row_h = 0
        page = pages[page_no]
        for py in range(height):
            src = py * width
            dst = (y + py) * PAGE_W + x
            page[dst:dst + width] = indices[src:src + width]
        descriptors[name] = {"page": page_no, "palette": palette_index,
                             "u": x, "v": y, "w": width, "h": height}
        x += width
        row_h = max(row_h, height)
    return page_no + 1


def rgb555(color: tuple[int, int, int]) -> int:
    r, g, b = (component >> 3 for component in color)
    packed = (b << 10) | (g << 5) | r
    return packed or 1  # RGB=0 is transparent on the PS1.


def rgb555_roundtrip(color: tuple[int, int, int]) -> tuple[int, int, int]:
	value = rgb555(color)
	return tuple((((value >> shift) & 31) * 255 + 15) // 31 for shift in (0, 5, 10))


def write_header(output: pathlib.Path,
                 palette8: list[tuple[int, int, int]],
                 palette4: list[tuple[int, int, int]],
                 palette_bf8: list[tuple[int, int, int]],
                 pages8: list[bytearray], pages4: list[bytearray],
                 page_table: list[tuple[int, int, int]],
                 descriptors: dict[str, dict]) -> None:
    lines = ["/* Generated by convert_bopeebo_visuals.py; do not edit. */",
             "#ifndef BOPEEBO_VISUAL_DATA_H", "#define BOPEEBO_VISUAL_DATA_H",
             "#include <stdint.h>",
             "typedef struct { uint8_t page, palette, u, v; uint16_t w, h; } BopeeboVisualFrame;",
             "typedef struct { uint16_t x, y; uint8_t depth; } BopeeboVisualPage;",
             f"#define BOPEEBO_VISUAL_PAGE_COUNT {len(page_table)}u",
             f"#define BOPEEBO_VISUAL_PAGE8_COUNT {len(pages8)}u",
             f"#define BOPEEBO_VISUAL_PAGE4_COUNT {len(pages4)}u",
             f"#define BOPEEBO_VISUAL_FRAME_COUNT {len(descriptors)}u"]
    for i, name in enumerate(descriptors):
        lines.append(f"#define VIS_{re.sub('[^A-Z0-9]+', '_', name.upper())} {i}u")
    lines.append("static const BopeeboVisualPage bopeebo_visual_page_table[BOPEEBO_VISUAL_PAGE_COUNT] = {")
    for x, y, depth in page_table:
        lines.append(f"\t{{{x}, {y}, {depth}}},")
    lines.append("};")
    values = [0] + [rgb555(c) for c in palette8[:255]]
    values += [0] * (256 - len(values))
    lines.append("static const uint16_t bopeebo_visual_palette8[256] = {" +
                  ",".join(f"0x{x:04x}" for x in values) + "};")
    values = [0] + [rgb555(c) for c in palette4[:15]]
    values += [0] * (16 - len(values))
    lines.append("static const uint16_t bopeebo_visual_palette4[16] = {" +
                  ",".join(f"0x{x:04x}" for x in values) + "};")
    values = [0] + [rgb555(c) for c in palette_bf8[:255]]
    values += [0] * (256 - len(values))
    lines.append("static const uint16_t bopeebo_visual_palette_bf8[256] = {" +
                  ",".join(f"0x{x:04x}" for x in values) + "};")
    lines.append("static const BopeeboVisualFrame bopeebo_visual_frames[BOPEEBO_VISUAL_FRAME_COUNT] = {")
    for name, frame in descriptors.items():
        lines.append(f"\t{{{frame['page']}, {frame['palette']}, {frame['u']}, {frame['v']}, {frame['w']}, {frame['h']}}}, /* {name} */")
    lines.append("};")
    lines.append(f"static const uint16_t bopeebo_visual_pages8[{len(pages8)}][32768] = {{")
    for page in pages8:
        words = [page[i] | (page[i + 1] << 8) for i in range(0, len(page), 2)]
        lines.append("\t{")
        for i in range(0, len(words), 16):
            lines.append("\t\t" + ",".join(f"0x{v:04x}" for v in words[i:i + 16]) + ",")
        lines.append("\t},")
    lines.append("};")
    lines.append(f"static const uint16_t bopeebo_visual_pages4[{len(pages4)}][16384] = {{")
    for page in pages4:
        words = [page[i] | (page[i + 1] << 8) for i in range(0, len(page), 2)]
        lines.append("\t{")
        for i in range(0, len(words), 16):
            lines.append("\t\t" + ",".join(f"0x{v:04x}" for v in words[i:i + 16]) + ",")
        lines.append("\t},")
    lines.extend(("};", "#endif"))
    output.write_text("\n".join(lines) + "\n", encoding="ascii")


def build(args: argparse.Namespace) -> None:
    assets = pathlib.Path(args.assets).resolve()
    shared_images = assets / "shared" / "images"
    chars = assets / "shared" / "images" / "characters"
    ffmpeg = str(pathlib.Path(args.ffmpeg).resolve())
    temp_images: dict[str, bytearray] = {}
    frame_sizes: dict[str, tuple[int, int]] = {}

    # Background and curtains are composited on the PC. Front rail remains a
    # separate layer; four 8bpp pages retain far more architectural detail.
    back = extract_stage(ffmpeg, shared_images / "stageback.png", SCENE_W, STAGE_BACK_H)
    curtains = extract_stage(ffmpeg, shared_images / "stagecurtains.png", SCENE_W, STAGE_BACK_H)
    for name, pixels, height in (("stage_back", alpha_over(back, curtains), STAGE_BACK_H),
                                 ("stage_front", extract_stage(ffmpeg, shared_images / "stagefront.png", SCENE_W, STAGE_FRONT_H), STAGE_FRONT_H)):
        for tile, x0 in enumerate((0, 256)):
            width = min(256, SCENE_W - x0)
            crop = bytearray()
            for y in range(height):
                start = (y * SCENE_W + x0) * 4
                crop.extend(pixels[start:start + width * 4])
            frame_name = f"{name}_{tile}"
            temp_images[frame_name] = crop
            frame_sizes[frame_name] = (width, height)

    bf_groups = atlas_frames(chars / "BOYFRIEND.xml")
    bf_png = chars / "BOYFRIEND.png"
    for anim, prefix in BF_ANIMS:
        frames = bf_groups.get(prefix)
        if not frames:
            raise ValueError(f"missing BF animation prefix in pinned atlas: {prefix}")
        for i in range(min(2, len(frames))):
            name = f"bf_{anim}_{i}"
            temp_images[name] = extract_sparrow_frame(ffmpeg, bf_png, frames[i], (FRAME_W, FRAME_H))
            frame_sizes[name] = (FRAME_W, FRAME_H)

    dad_rig = Rig(chars / "dad", ffmpeg)
    gf_rig = Rig(chars / "gf", ffmpeg)
    dad_pose_frames = [(f"dad_idle_{i}", frame) for i, frame in enumerate((0, 2, 4, 6, 8, 10))]
    for direction, first in (("up", 12), ("down", 18), ("left", 24), ("right", 30)):
        dad_pose_frames.extend(((f"dad_{direction}_0", first + 1), (f"dad_{direction}_1", first + 4)))
    for name, source_frame in dad_pose_frames:
        width, height, pixels = dad_rig.render(source_frame)
        if not pixels:
            raise ValueError(f"empty Dad Animate frame {source_frame}")
        temp_images[name] = fit_nearest(pixels, width, height, 72, 112)
        frame_sizes[name] = (72, 112)

    for i, source_frame in enumerate((0, 4, 8, 11, 15, 19, 22, 26)):
        width, height, pixels = gf_rig.render(source_frame)
        if not pixels:
            raise ValueError(f"empty Girlfriend Animate frame {source_frame}")
        temp_images[f"gf_dance_{i}"] = fit_nearest(pixels, width, height, 128, 120)
        frame_sizes[f"gf_dance_{i}"] = (128, 120)

    stage_names = [name for name in temp_images if name.startswith("stage_")]
    bf_names = [name for name in temp_images if name.startswith("bf_")]
    bf_core_names = [name for name in bf_names if not name.startswith("bf_miss_")]
    bf_miss_names = [name for name in bf_names if name.startswith("bf_miss_")]
    dad_names = [name for name in temp_images if name.startswith("dad_")]
    gf_names = [name for name in temp_images if name.startswith("gf_")]
    stage_palette_old = median_palette([temp_images[n] for n in stage_names], 15)
    # One shared 8bpp palette fits alongside the BF CLUT in the 320-word
    # strip below the framebuffers, avoiding texture/CLUT overlap in VRAM.
    palette8 = median_palette([temp_images[n] for n in stage_names + dad_names + gf_names], 255)
    palette4 = median_palette([temp_images[n] for n in bf_miss_names], 15)
    palette_bf8 = median_palette([temp_images[n] for n in bf_core_names], 255)
    quantized8 = {name: quantize(pixels, palette8) for name, pixels in temp_images.items()
                  if not name.startswith("bf_")}
    quantized4 = {name: quantize(temp_images[name], palette4) for name in bf_miss_names}
    quantized_bf8 = {name: quantize(temp_images[name], palette_bf8) for name in bf_core_names}
    descriptors: dict[str, dict] = {}
    pages8: list[bytearray] = []
    pages4: list[bytearray] = []
    # Pair the narrow 64px columns with the 256px columns on the same pages,
    # using the otherwise empty vertical space under the wide image.
    for _ in range(2):
        pages8.append(bytearray(PAGE_W * PAGE_H))
    stage_layout = (("stage_back_0", 0, 0, 0), ("stage_front_1", 0, 0, STAGE_BACK_H),
                    ("stage_back_1", 1, 0, 0), ("stage_front_0", 1, 0, STAGE_BACK_H))
    for name, page_no, x, y in stage_layout:
        indices = quantized8[name]
        width, height = frame_sizes[name]
        for py in range(height):
            src, dst = py * width, (y + py) * PAGE_W + x
            pages8[page_no][dst:dst + width] = indices[src:src + width]
        descriptors[name] = {"page": page_no, "palette": 0, "u": x, "v": y,
                             "w": width, "h": height}
    dad_first = len(pages8)
    pack_8bpp([(n, quantized8[n], *frame_sizes[n]) for n in dad_names], dad_first, 0, pages8, descriptors)
    gf_first = len(pages8)
    pack_8bpp([(n, quantized8[n], *frame_sizes[n]) for n in gf_names], gf_first, 0, pages8, descriptors)
    bf8_first = len(pages8)
    pack_8bpp([(n, quantized_bf8[n], *frame_sizes[n]) for n in bf_core_names],
              bf8_first, 2, pages8, descriptors)
    # Keep the less frequent miss poses 4bpp; the song-critical idle/sing poses
    # get a dedicated 8bpp CLUT and the two remaining 8bpp texture pages.
    pack_page([(n, quantized4[n], *frame_sizes[n]) for n in bf_miss_names],
              0, 1, pages4, descriptors)
    # Place aligned 8bpp pages right of the framebuffers (font at x=960,y=0).
    # 4bpp pages use the free strip x=320..383 beside both 320-word framebuffers.
    if len(pages8) > 9 or len(pages4) > 4:
        raise ValueError(f"visual page layout exceeds free VRAM: {len(pages8)}x8bpp, {len(pages4)}x4bpp")
    page_table: list[tuple[int, int, int]] = []
    row0 = [(384 + i * 128, 0) for i in range(4)]
    row1 = [(384 + i * 128, 256) for i in range(5)]
    for i in range(len(pages8)):
        x, y = row0[i] if i < 4 else row1[i - 4]
        page_table.append((x, y, 1))
    # 8bpp page bases align to 128 VRAM words. Four top-row and up to five
    # lower-row pages are available. 4bpp pages use the unused horizontal
    # strip immediately right of both 320-word framebuffers (x=320..383).
    first4x = 320
    for i in range(len(pages4)):
        x = first4x + i * 64
        if x + 64 > 1024:
            raise ValueError("4bpp pages collide with the framebuffer or exceed VRAM width")
        # Texture-page Y is quantized by getTPage to 0 or 256; keep the
        # 4bpp page aligned at 256 so runtime UVs address the uploaded data.
        page_table.append((x, 256, 0))
    if len(page_table) != len(pages8) + len(pages4):
        raise ValueError("generated VRAM page table does not cover all texture pages")

    # Validate the actual 1024x512-word VRAM rectangles, including both
    # framebuffers, all texture pages, CLUT rows and the SDK font reservation.
    vram_regions = [("framebuffer0", 0, 0, 320, 240), ("framebuffer1", 0, 240, 320, 240),
                    ("palette8", 0, 496, 256, 1), ("palette4", 256, 496, 16, 1),
                    ("palette_bf8", 0, 480, 256, 1), ("font_reservation", 960, 0, 64, 256)]
    for i, (x, y, depth) in enumerate(page_table):
        vram_regions.append((f"texture_page_{i}", x, y, 128 if depth else 64, 256))
    for i, (name, x, y, width, height) in enumerate(vram_regions):
        if x < 0 or y < 0 or x + width > 1024 or y + height > 512:
            raise ValueError(f"VRAM region {name} exceeds the 1024x512 map")
        for other_name, ox, oy, ow, oh in vram_regions[:i]:
            if x < ox + ow and ox < x + width and y < oy + oh and oy < y + height:
                raise ValueError(f"VRAM regions {name} and {other_name} overlap")
    for name in bf_miss_names:
        descriptors[name]["page"] += len(pages8)

    # Keep quantization losses visible in the build log to guide art choices.
    def rmse(names, palette):
        squared, count = 0, 0
        for name in names:
            source = temp_images[name]
            q = quantize(source, palette)
            for i, index in enumerate(q):
                if not index:
                    continue
                color = rgb555_roundtrip(palette[index - 1])
                base = i * 4
                squared += sum((source[base + c] - color[c]) ** 2 for c in range(3))
                count += 3
        return (squared / count) ** 0.5 if count else 0.0
    print(f"stage palette loss: 15-color RMSE {rmse(stage_names, stage_palette_old):.2f}; shared 255-color RMSE {rmse(stage_names, palette8):.2f} RGB levels")
    print(f"Dad/GF combined palette RMSE: Dad {rmse(dad_names, palette8):.2f}, GF {rmse(gf_names, palette8):.2f} RGB levels")
    print(f"BF core idle/sing at 64x96: dedicated 8bpp/255-color RMSE {rmse(bf_core_names, palette_bf8):.2f}; miss poses 4bpp/15-color RMSE {rmse(bf_miss_names, palette4):.2f} RGB levels (RGB555 decoded)")
    write_header(pathlib.Path(args.output), palette8, palette4, palette_bf8, pages8, pages4, page_table, descriptors)
    print(f"Animate frames: Dad {len(dad_names)} (idle + 4 sings), GF {len(gf_names)} dance; BF {len(bf_names)} official Sparrow frames")
    print(f"VRAM map verified: {len(pages8)}x8bpp + {len(pages4)}x4bpp, framebuffers, CLUTs and font reserve are in bounds without overlap")
    print(f"VRAM textures: {len(pages8)}x8bpp + {len(pages4)}x4bpp = {len(pages8)*65536+len(pages4)*32768} bytes; generated header {pathlib.Path(args.output).stat().st_size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, help="root of the pinned assets submodule")
    parser.add_argument("--ffmpeg", required=True, help="path to ffmpeg")
    parser.add_argument("--output", required=True, help="generated C header (kept in the build directory)")
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
