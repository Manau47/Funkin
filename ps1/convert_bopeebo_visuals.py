#!/usr/bin/env python3
"""Convert a small, deterministic PS1 Bopeebo scene from the pinned assets."""

from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import re
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from animate_preview import Rig


WORLD_DIVISOR = 8
STAGE_TILE_W = 256
FRAME_W = 52
FRAME_H = 52
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
        # Keep alpha through crop/pad/scale. Adding format=rgba only at the
        # end lets FFmpeg negotiate an opaque intermediate for some filters,
        # turning transparent atlas pixels into black rectangles on the PS1.
        ffmpeg, "-v", "error", "-i", str(source), "-vf", f"format=rgba,{filters}",
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


def extract_crop(ffmpeg: str, png: pathlib.Path, x: int, y: int, width: int, height: int,
                 size: tuple[int, int]) -> bytearray:
    out_w, out_h = size
    filters = (f"crop={width}:{height}:{x}:{y},"
               f"scale={out_w}:{out_h}:flags=neighbor,format=rgba")
    return run_ffmpeg(ffmpeg, png, filters, out_w, out_h)


def fit_anchored_rig(rig: Rig, frame_ids: list[int], out_w: int, out_h: int) -> dict[int, bytearray]:
    """Fit a rig's poses together, keeping their source-space origin and floor."""
    rendered = {frame: rig.render_positioned(frame) for frame in frame_ids}
    min_x = min(item[0] for item in rendered.values())
    max_x = max(item[0] + item[2] for item in rendered.values())
    min_y = min(item[1] for item in rendered.values())
    floor_y = max(item[1] + item[3] for item in rendered.values())
    union_w, union_h = max_x - min_x, floor_y - min_y
    scale = min((out_w - 4) / union_w, (out_h - 2) / union_h)
    scaled_union_w = max(1, round(union_w * scale))
    left = (out_w - scaled_union_w) // 2
    result: dict[int, bytearray] = {}
    for frame, (x, y, width, height, source) in rendered.items():
        scaled_w = max(1, round(width * scale))
        scaled_h = max(1, round(height * scale))
        x0 = left + round((x - min_x) * scale)
        bottom_gap = round((floor_y - (y + height)) * scale)
        y0 = out_h - bottom_gap - scaled_h
        target = bytearray(out_w * out_h * 4)
        for dy in range(scaled_h):
            sy = min(height - 1, dy * height // scaled_h)
            for dx in range(scaled_w):
                sx = min(width - 1, dx * width // scaled_w)
                si = (sy * width + sx) * 4
                di = ((y0 + dy) * out_w + x0 + dx) * 4
                target[di:di + 4] = source[si:si + 4]
        result[frame] = target
    return result


def extract_stage(ffmpeg: str, png: pathlib.Path, width: int, height: int) -> bytearray:
    # The source stage is 8x larger than the PS1 output. Area downsampling
    # preserves thin architecture and curtains without runtime bilinear blur.
    filters = f"scale={width}:{height}:flags=area,format=rgba"
    return run_ffmpeg(ffmpeg, png, filters, width, height)


def blend_at(background: bytearray, back_size: tuple[int, int], foreground: bytearray,
             foreground_size: tuple[int, int], offset: tuple[int, int]) -> None:
    """Alpha-composite a stage prop at its official, camera-world position."""
    bw, bh = back_size
    fw, fh = foreground_size
    ox, oy = offset
    for sy in range(fh):
        dy = oy + sy
        if not 0 <= dy < bh:
            continue
        for sx in range(fw):
            dx = ox + sx
            if not 0 <= dx < bw:
                continue
            si = (sy * fw + sx) * 4
            di = (dy * bw + dx) * 4
            alpha = foreground[si + 3]
            if not alpha:
                continue
            if alpha == 255:
                background[di:di + 4] = foreground[si:si + 4]
                continue
            inv = 255 - alpha
            for channel in range(3):
                background[di + channel] = (foreground[si + channel] * alpha +
                                            background[di + channel] * inv) // 255
            background[di + 3] = alpha + background[di + 3] * inv // 255


def load_stage_layout(assets: pathlib.Path) -> tuple[dict, tuple[int, int, int, int]]:
    stage_path = assets / "preload" / "data" / "stages" / "mainStage.json"
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    props = {prop["name"]: prop for prop in stage["props"]}
    chars = stage["characters"]
    def rounded_world(value: float) -> int:
        return math.floor(value / WORLD_DIVISOR + 0.5)
    layout = {
        # The 1/8 art/world conversion is brought to the reference camera
        # scale for the 4:3 viewport; 2.5x includes mainStage's 1.1 zoom.
        "camera_zoom_q8": round(float(stage.get("cameraZoom", 1.0)) * 640 / 1.1),
    }
    for name, source in (("dad", "dad"), ("gf", "gf"), ("bf", "bf")):
        item = chars[source]
        layout[f"{name}_x"] = rounded_world(float(item["position"][0]))
        layout[f"{name}_y"] = rounded_world(float(item["position"][1]))
        layout[f"{name}_camera_x"] = rounded_world(float(item["cameraOffsets"][0]))
        layout[f"{name}_camera_y"] = rounded_world(float(item["cameraOffsets"][1]))
    # Compose stageback, stagefront and curtains in official z-order at the
    # same 1/8 world scale used for character placement. No aspect stretching.
    source_images = assets / "shared" / "images"
    back_png = source_images / "stageback.png"
    front_png = source_images / "stagefront.png"
    curtains_png = source_images / "stagecurtains.png"
    def prop_geom(name: str, image_size: tuple[int, int]):
        prop = props[name]
        scale = prop.get("scale", [1.0, 1.0])
        if not isinstance(scale, list):
            scale = [scale, scale]
        x = rounded_world(float(prop["position"][0]))
        y = rounded_world(float(prop["position"][1]))
        w = max(1, round(image_size[0] * float(scale[0]) / WORLD_DIVISOR))
        h = max(1, round(image_size[1] * float(scale[1]) / WORLD_DIVISOR))
        return x, y, w, h
    back_w, back_h = 320, 175
    front_w, front_h = 352, 80
    curtains_w, curtains_h = 288, 158
    geoms = {
        "stageBack": prop_geom("stageBack", (2560, 1400)),
        "stageFront": prop_geom("stageFront", (2560, 581)),
        "stageCurtains": prop_geom("stageCurtains", (2560, 1400)),
    }
    x0 = min(geoms[k][0] for k in geoms)
    y0 = min(geoms[k][1] for k in geoms)
    x1 = max(geoms["stageBack"][0] + back_w, geoms["stageFront"][0] + front_w,
             geoms["stageCurtains"][0] + curtains_w)
    y1 = max(geoms["stageBack"][1] + back_h, geoms["stageFront"][1] + front_h,
             geoms["stageCurtains"][1] + curtains_h)
    return {**layout, "scene_x": x0, "scene_y": y0}, (x0, y0, x1 - x0, y1 - y0)


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
                out_w: int, out_h: int, anchor_bottom: bool = False) -> bytearray:
    scale = min(out_w / width, out_h / height)
    scaled_w = max(1, min(out_w, round(width * scale)))
    scaled_h = max(1, min(out_h, round(height * scale)))
    xoff = (out_w - scaled_w) // 2
    yoff = out_h - scaled_h if anchor_bottom else (out_h - scaled_h) // 2
    out = bytearray(out_w * out_h * 4)
    for y in range(scaled_h):
        sy = min(height - 1, y * height // scaled_h)
        for x in range(scaled_w):
            sx = min(width - 1, x * width // scaled_w)
            si = (sy * width + sx) * 4
            di = ((y + yoff) * out_w + x + xoff) * 4
            out[di:di + 4] = pixels[si:si + 4]
    return out


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
                 palette_ui4: list[list[tuple[int, int, int]]],
                 palette_popup4: list[tuple[int, int, int]],
                 stage_layout: dict[str, int], scene_bounds: tuple[int, int, int, int],
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
             f"#define BOPEEBO_VISUAL_FRAME_COUNT {len(descriptors)}u",
             f"#define BOPEEBO_STAGE_SCENE_X ({scene_bounds[0]})",
             f"#define BOPEEBO_STAGE_SCENE_Y ({scene_bounds[1]})",
             f"#define BOPEEBO_STAGE_SCENE_W {scene_bounds[2]}u",
             f"#define BOPEEBO_STAGE_SCENE_H {scene_bounds[3]}u",
             f"#define BOPEEBO_STAGE_CAMERA_ZOOM_Q8 {stage_layout['camera_zoom_q8']}u",
             "#define BOPEEBO_DAD_FRAME_W 53u", "#define BOPEEBO_DAD_FRAME_H 96u",
             "#define BOPEEBO_GF_FRAME_W 87u", "#define BOPEEBO_GF_FRAME_H 79u",
             f"#define BOPEEBO_BF_FRAME_W {FRAME_W}u", f"#define BOPEEBO_BF_FRAME_H {FRAME_H}u"]
    for name in ("dad", "gf", "bf"):
        for component in ("x", "y", "camera_x", "camera_y"):
            lines.append(f"#define BOPEEBO_{name.upper()}_{component.upper()} ({stage_layout[f'{name}_{component}']})")
    for i, name in enumerate(descriptors):
        lines.append(f"#define VIS_{re.sub('[^A-Z0-9]+', '_', name.upper())} {i}u")
    lines.append("static const BopeeboVisualPage bopeebo_visual_page_table[BOPEEBO_VISUAL_PAGE_COUNT] = {")
    for x, y, depth in page_table:
        lines.append(f"\t{{{x}, {y}, {depth}}},")
    lines.append("};")
    values = [0] + [rgb555(c) for c in palette_popup4[:15]]
    values += [0] * (16 - len(values))
    lines.append("static const uint16_t bopeebo_visual_palette_popup4[16] = {" +
                  ",".join(f"0x{x:04x}" for x in values) + "};")
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
    lines.append("static const uint16_t bopeebo_visual_palette_ui4[4][16] = {")
    for palette in palette_ui4:
        values = [0] + [rgb555(c) for c in palette[:15]]
        values += [0] * (16 - len(values))
        lines.append("{" + ",".join(f"0x{x:04x}" for x in values) + "},")
    lines.append("};")
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
    stage_layout, scene_bounds = load_stage_layout(assets)
    temp_images: dict[str, bytearray] = {}
    frame_sizes: dict[str, tuple[int, int]] = {}

    # Composite the official stage props at their mainStage.json transforms
    # and z-order, then let one camera transform move/zoom the whole artwork.
    props = {prop["name"]: prop for prop in json.loads(
        (assets / "preload" / "data" / "stages" / "mainStage.json").read_text(encoding="utf-8"))["props"]}
    scene_x, scene_y, scene_w, scene_h = scene_bounds
    scene = bytearray(scene_w * scene_h * 4)
    back = extract_stage(ffmpeg, shared_images / "stageback.png", 320, 175)
    front = extract_stage(ffmpeg, shared_images / "stagefront.png", 352, 80)
    curtains = extract_stage(ffmpeg, shared_images / "stagecurtains.png", 288, 158)
    def prop_origin(name: str) -> tuple[int, int]:
        position = props[name]["position"]
        return (math.floor(float(position[0]) / WORLD_DIVISOR + 0.5),
                math.floor(float(position[1]) / WORLD_DIVISOR + 0.5))
    for name, pixels, size in (("stageBack", back, (320, 175)),
                               ("stageFront", front, (352, 80)),
                               ("stageCurtains", curtains, (288, 158))):
        px, py = prop_origin(name)
        blend_at(scene, (scene_w, scene_h), pixels, size, (px - scene_x, py - scene_y))
    for tile, x0 in enumerate((0, STAGE_TILE_W)):
        width = min(STAGE_TILE_W, scene_w - x0)
        crop = bytearray()
        for y in range(scene_h):
            start = (y * scene_w + x0) * 4
            crop.extend(scene[start:start + width * 4])
        frame_name = f"stage_scene_{tile}"
        temp_images[frame_name] = crop
        frame_sizes[frame_name] = (width, scene_h)

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
    dad_source_ids = [frame for _, frame in dad_pose_frames]
    dad_anchored = fit_anchored_rig(dad_rig, dad_source_ids, 53, 96)
    for name, source_frame in dad_pose_frames:
        temp_images[name] = dad_anchored[source_frame]
        frame_sizes[name] = (53, 96)

    gf_source_ids = (0, 4, 8, 11, 15, 19, 22, 26)
    gf_anchored = fit_anchored_rig(gf_rig, list(gf_source_ids), 87, 79)
    for i, source_frame in enumerate(gf_source_ids):
        temp_images[f"gf_dance_{i}"] = gf_anchored[source_frame]
        frame_sizes[f"gf_dance_{i}"] = (87, 79)

    # Bopeebo's standard note style uses these pinned official sprites, not
    # the older NOTE_assets chart-editor atlas or generated geometric arrows.
    directions = ("left", "down", "up", "right")
    note_png = shared_images / "notes.png"
    note_groups = atlas_frames(shared_images / "notes.xml")
    receptor_png = shared_images / "noteStrumline.png"
    receptor_groups = atlas_frames(shared_images / "noteStrumline.xml")
    ui4_by_direction: dict[str, list[str]] = {}
    popup_names: list[str] = []
    for lane, direction in enumerate(directions):
        note_frames = note_groups.get(f"note{direction.title()}")
        if not note_frames:
            raise ValueError(f"missing official note sprite for {direction}")
        note_name = f"ui_note_{direction}"
        temp_images[note_name] = extract_sparrow_frame(ffmpeg, note_png, note_frames[0], (32, 32))
        frame_sizes[note_name] = (32, 32)
        lane_names = [note_name]

        for state, source_names in (
            ("idle", (f"static{direction.title()}",)),
            ("press", (f"press{direction.title()}",)),
            ("confirm", (f"confirm{direction.title()}",)),
        ):
            source_frames = []
            for source_name in source_names:
                source_frames.extend(receptor_groups.get(source_name, []))
            if not source_frames:
                raise ValueError(f"missing official {state} receptor sprite for {direction}")
            if state == "idle":
                selected = source_frames[:1]
            elif state == "press":
                selected = source_frames[-1:]
            else:
                selected = source_frames[:4]
            for frame_index, source_frame in enumerate(selected):
                name = (f"ui_receptor_{direction}_{state}" if state != "confirm" else
                        f"ui_receptor_{direction}_confirm_{frame_index}")
                # Sparrow receptors use a large logical canvas with negative
                # frame offsets. Crop the visible atlas rectangle to the same
                # 32px box as notes instead of shrinking it inside that canvas.
                temp_images[name] = extract_crop(ffmpeg, receptor_png,
                    int(source_frame["x"]), int(source_frame["y"]),
                    int(source_frame["width"]), int(source_frame["height"]), (32, 32))
                frame_sizes[name] = (32, 32)
                lane_names.append(name)

        hold_png = assets / "preload" / "images" / "NOTE_hold_assets.png"
        hold_w, hold_h = 416, 87
        column_w = hold_w // 8
        for part, column, size in (("body", lane * 2, (16, 24)), ("tail", lane * 2 + 1, (16, 24))):
            name = f"ui_hold_{part}_{direction}"
            temp_images[name] = fit_nearest(
                run_ffmpeg(ffmpeg, hold_png, f"crop={column_w}:{hold_h}:{column * column_w}:0,format=rgba",
                           column_w, hold_h), column_w, hold_h, *size)
            frame_sizes[name] = size
            lane_names.append(name)
        ui4_by_direction[direction] = lane_names

    # Official Funkin judgement lettering uses a compact CLUT. Health icons
    # reuse the character palettes to preserve their color identity.
    popup_dir = assets / "preload" / "images" / "ui" / "popup" / "funkin"
    for name in ("sick", "good", "bad", "shit"):
        source = popup_dir / f"{name}.png"
        with source.open("rb") as image:
            image.seek(16)
            src_w, src_h = struct.unpack(">II", image.read(8))
        size = (max(1, round(src_w * 0.16)), max(1, round(src_h * 0.16)))
        temp_images[f"ui_judgement_{name}"] = extract_stage(ffmpeg, source, *size)
        frame_sizes[f"ui_judgement_{name}"] = size
        popup_names.append(f"ui_judgement_{name}")
    icon_names: list[str] = []
    icon_dir = assets / "preload" / "images" / "icons"
    for name, source, x in (("dad", "icon-dad.png", 0),
                            ("bf_win", "icon-bf.png", 0),
                            ("bf_lose", "icon-bf.png", 150)):
        icon_png = icon_dir / source
        icon_name = f"ui_icon_{name}"
        temp_images[icon_name] = extract_crop(ffmpeg, icon_png, x, 0, 150, 150, (24, 24))
        frame_sizes[icon_name] = (24, 24)
        icon_names.append(icon_name)

    stage_names = [name for name in temp_images if name.startswith("stage_")]
    bf_names = [name for name in temp_images if name.startswith("bf_")]
    bf_core_names = [name for name in bf_names if not name.startswith("bf_miss_")]
    bf_miss_names = [name for name in bf_names if name.startswith("bf_miss_")]
    ui_names = [name for names in ui4_by_direction.values() for name in names]
    dad_names = [name for name in temp_images if name.startswith("dad_")]
    gf_names = [name for name in temp_images if name.startswith("gf_")]
    stage_palette_old = median_palette([temp_images[n] for n in stage_names], 15)
    # One shared 8bpp palette fits alongside the BF CLUT in the 320-word
    # strip below the framebuffers, avoiding texture/CLUT overlap in VRAM.
    palette8 = median_palette([temp_images[n] for n in stage_names + dad_names + gf_names], 255)
    palette4 = median_palette([temp_images[n] for n in bf_miss_names], 15)
    palette_ui4 = [median_palette([temp_images[n] for n in ui4_by_direction[d]], 15)
                   for d in directions]
    palette_bf8 = median_palette([temp_images[n] for n in bf_core_names], 255)
    palette_popup4 = median_palette([temp_images[n] for n in popup_names], 15)
    quantized8 = {name: quantize(pixels, palette8) for name, pixels in temp_images.items()
                  if not name.startswith(("bf_", "ui_"))}
    quantized4 = {name: quantize(temp_images[name], palette4) for name in bf_miss_names}
    quantized_ui4 = {name: quantize(temp_images[name], palette_ui4[lane])
                     for lane, direction in enumerate(directions) for name in ui4_by_direction[direction]}
    quantized_bf8 = {name: quantize(temp_images[name], palette_bf8) for name in bf_core_names}
    quantized_popup4 = {name: quantize(temp_images[name], palette_popup4) for name in popup_names}
    quantized_icon8 = {
        name: quantize(temp_images[name], palette_bf8 if name != "ui_icon_dad" else palette8)
        for name in icon_names
    }
    descriptors: dict[str, dict] = {}
    pages8: list[bytearray] = []
    pages4: list[bytearray] = []
    # Pair the narrow 64px columns with the 256px columns on the same pages,
    # using the otherwise empty vertical space under the wide image.
    for _ in range(2):
        pages8.append(bytearray(PAGE_W * PAGE_H))
    stage_tiles = (("stage_scene_0", 0, 0, 0), ("stage_scene_1", 1, 0, 0))
    for name, page_no, x, y in stage_tiles:
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
    portrait_first_page = len(pages8)
    pack_8bpp([(name, quantized_icon8[name], *frame_sizes[name]) for name in icon_names],
              portrait_first_page, 0, pages8, descriptors)
    for name in icon_names:
        descriptors[name]["palette"] = 0 if name == "ui_icon_dad" else 2
    # Keep the less frequent miss poses 4bpp; the song-critical idle/sing poses
    # get a dedicated 8bpp CLUT and the two remaining 8bpp texture pages.
    pack_page([(n, quantized4[n], *frame_sizes[n]) for n in bf_miss_names] +
              [(n, quantized_popup4[n], *frame_sizes[n]) for n in popup_names],
              0, 1, pages4, descriptors)
    for name in popup_names:
        descriptors[name]["palette"] = 7
    ui_first_page = len(pages4)
    pack_page([(n, quantized_ui4[n], *frame_sizes[n]) for n in ui_names],
              ui_first_page, 1, pages4, descriptors)
    for lane, direction in enumerate(directions):
        for name in ui4_by_direction[direction]:
            descriptors[name]["palette"] = 3 + lane
    # Place aligned 8bpp pages right of the framebuffers (font at x=960,y=0).
    # 4bpp pages use the free strip x=320..383 beside both 320-word framebuffers.
    if len(pages8) > 9 or len(pages4) > 2:
        raise ValueError(f"visual page layout exceeds free VRAM: {len(pages8)}x8bpp, {len(pages4)}x4bpp")
    page_table: list[tuple[int, int, int]] = []
    row0 = [(384 + i * 128, 0) for i in range(4)]
    row1 = [(384 + i * 128, 256) for i in range(5)]
    for i in range(len(pages8)):
        x, y = row0[i] if i < 4 else row1[i - 4]
        page_table.append((x, y, 1))
    # 8bpp page bases align to 128 VRAM words. The 64-word strip beside the
    # framebuffers provides two vertically adjacent 4bpp pages.
    for i in range(len(pages4)):
        if i > 1:
            raise ValueError("only two 4bpp pages fit in the free VRAM strip")
        page_table.append((320, i * 256, 0))
    if len(page_table) != len(pages8) + len(pages4):
        raise ValueError("generated VRAM page table does not cover all texture pages")

    # Validate the actual 1024x512-word VRAM rectangles, including both
    # framebuffers, all texture pages, CLUT rows and the SDK font reservation.
    vram_regions = [("framebuffer0", 0, 0, 320, 240), ("framebuffer1", 0, 240, 320, 240),
                    ("palette8", 0, 496, 256, 1), ("palette4", 256, 496, 16, 1),
                    ("palette_bf8", 0, 480, 256, 1), ("palette_popup4", 272, 480, 16, 1),
                    ("font_reservation", 960, 0, 64, 256)]
    vram_regions.extend((f"palette_ui4_{i}", (256 if i == 3 else 272 + i * 16),
                         (480 if i == 3 else 496), 16, 1) for i in range(4))
    for i, (x, y, depth) in enumerate(page_table):
        vram_regions.append((f"texture_page_{i}", x, y, 128 if depth else 64, 256))
    for i, (name, x, y, width, height) in enumerate(vram_regions):
        if x < 0 or y < 0 or x + width > 1024 or y + height > 512:
            raise ValueError(f"VRAM region {name} exceeds the 1024x512 map")
        for other_name, ox, oy, ow, oh in vram_regions[:i]:
            if x < ox + ow and ox < x + width and y < oy + oh and oy < y + height:
                raise ValueError(f"VRAM regions {name} and {other_name} overlap")
    for name in bf_miss_names + ui_names + popup_names:
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
    print(f"BF core idle/sing at {FRAME_W}x{FRAME_H}: dedicated 8bpp/255-color RMSE {rmse(bf_core_names, palette_bf8):.2f}; miss poses 4bpp/15-color RMSE {rmse(bf_miss_names, palette4):.2f} RGB levels (RGB555 decoded)")
    print("Official arrows/receptors/holds: 4bpp per direction, 15-color CLUT each; " +
          ", ".join(f"{d} RMSE {rmse(ui4_by_direction[d], palette_ui4[i]):.2f}" for i, d in enumerate(directions)))
    print(f"Official judgement art/health icons: 4bpp shared CLUT RMSE {rmse(popup_names, palette_popup4):.2f} RGB levels")
    print("Official health portraits at 24x24 use the 8bpp character CLUTs (Dad/main, BF/BF)")
    write_header(pathlib.Path(args.output), palette8, palette4, palette_bf8, palette_ui4,
                 palette_popup4, stage_layout, scene_bounds,
                 pages8, pages4, page_table, descriptors)
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

