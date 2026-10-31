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
MENU_DJ_SOURCE_CANVAS_W = 82
MENU_DJ_FRAME_H = 90
MENU_DJ_SOURCE_FRAMES = tuple(range(0, 17, 2)) + tuple(range(17, 31, 2))
WEEK2_CHAR_W = 72
WEEK2_CHAR_H = 84
WEEK2_MONSTER_FRAME_W = WEEK2_CHAR_W
WEEK2_MONSTER_FRAME_H = WEEK2_CHAR_H
WEEK2_STAGE_DIVISOR = 7
WEEK2_LIGHTNING_CROP = (92, 81, 255, 211)
WEEK2_LIGHTNING_TEX_W = 104
WEEK2_LIGHTNING_TEX_H = 83

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


def png_size(source: pathlib.Path) -> tuple[int, int]:
    data = source.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"not a PNG with a leading IHDR: {source}")
    return struct.unpack(">II", data[16:24])


def fit_anchored_rig(rig: Rig, frame_ids: list[int], out_w: int, out_h: int,
                     canvas: int = 1200) -> dict[int, bytearray]:
    """Fit a rig's poses together, keeping their source-space origin and floor."""
    rendered = {frame: rig.render_positioned(frame, canvas) for frame in frame_ids}
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


def extract_menu_cover(ffmpeg: str, png: pathlib.Path, width: int, height: int) -> bytearray:
    """Fill the 4:3 menu viewport by cropping the sides, never stretching art."""
    filters = (f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=area,"
               f"crop={width}:{height}:(iw-ow)/2:(ih-oh)/2,format=rgba")
    return run_ffmpeg(ffmpeg, png, filters, width, height)


def vcr_letter_atlas(ffmpeg: str, font_path: pathlib.Path) -> bytearray:
    """Rasterize the mockup's VCR face into 6x9 cells for Freeplay titles."""
    filters = ["format=rgba"]
    for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        x, y = (index % 8) * 6, (index // 8) * 9
        filters.append(
            f"drawtext=fontfile=vcr-bold.ttf:text={letter}:fontsize=7:"
            f"fontcolor=white:borderw=1:bordercolor=0x090810@1:x={x}:y={y}"
        )
    command = [ffmpeg, "-v", "error", "-f", "lavfi", "-i",
               "color=c=black@0.0:s=48x36:d=1", "-vf", ",".join(filters),
               "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1"]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, cwd=font_path.parent)
    if len(result.stdout) != 48 * 36 * 4:
        raise ValueError(f"unexpected VCR letter atlas size: {len(result.stdout)}")
    return bytearray(result.stdout)


def mirror_rgba(pixels: bytearray, width: int, height: int) -> bytearray:
    mirrored = bytearray(len(pixels))
    for y in range(height):
        for x in range(width):
            src = (y * width + x) * 4
            dst = (y * width + (width - 1 - x)) * 4
            mirrored[dst:dst + 4] = pixels[src:src + 4]
    return mirrored


def extract_menu_contain(ffmpeg: str, png: pathlib.Path, width: int, height: int,
                         background: tuple[int, int, int]) -> bytearray:
    """Fit complete menu artwork inside 4:3 with simple dark letterboxing."""
    color = "0x%02x%02x%02x" % background
    filters = (f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=area,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={color},format=rgba")
    return run_ffmpeg(ffmpeg, png, filters, width, height)


def menu_label_states(ffmpeg: str, png: pathlib.Path) -> tuple[bytearray, list[bytearray]]:
    """Fit approved OPTIONS lettering to the menu label box and animate its ink."""
    base = run_ffmpeg(ffmpeg, png,
        "scale=128:36:force_original_aspect_ratio=decrease:flags=neighbor,"
        "pad=128:36:(ow-iw)/2:(oh-ih)/2:color=0x00000000,format=rgba", 128, 36)
    source_mask = [base[i + 3] >= 128 for i in range(0, len(base), 4)]
    width, height = 128, 36
    xs = [x for y in range(height) for x in range(width) if source_mask[y * width + x]]
    ys = [y for y in range(height) for x in range(width) if source_mask[y * width + x]]
    if not xs:
        raise ValueError(f"OPTIONS artwork has no visible pixels: {png}")
    left, top, right, bottom = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    source_w, source_h = right - left, bottom - top
    # Atlas rows are 36px tall; fit the custom art to a similar visible height
    # and width as Merch while preserving its lettering proportions.
    target_w = min(116, source_w + 10)
    target_h = min(31, max(1, round(source_h * target_w / source_w * 1.22)))
    mask = [False] * (width * height)
    dest_x, dest_y = (width - target_w) // 2, (height - target_h) // 2
    for y in range(target_h):
        sy = top + min(source_h - 1, (y * source_h) // target_h)
        for x in range(target_w):
            sx = left + min(source_w - 1, (x * source_w) // target_w)
            mask[(dest_y + y) * width + dest_x + x] = source_mask[sy * width + sx]
    # Give the idle OPTIONS label a slightly heavier white contour.
    # The selected-state frames below redraw the black outline independently.
    idle_dilated = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            if not mask[y * width + x]:
                continue
            for oy in range(-3, 4):
                for ox in range(-3, 4):
                    nx, ny = x + ox, y + oy
                    if 0 <= nx < width and 0 <= ny < height:
                        idle_dilated[ny * width + nx] = 1
    idle = bytearray(width * height * 4)
    for i, inside in enumerate(mask):
        border = bool(idle_dilated[i]) and not inside
        offset = i * 4
        if inside:
            idle[offset:offset + 4] = bytes((0, 0, 0, 255))
        elif border:
            idle[offset:offset + 4] = bytes((255, 255, 255, 255))
    selected_frames = []
    # Keep the white letter fill fixed and redraw only its black contour in
    # three small, irregular shape variations, like the selected frames on the other rows.
    # A deterministic pixel hash adds a little roughness without changing the lettering.
    for frame_index, (radius_x, radius_y) in enumerate(((3, 3), (4, 3), (3, 4))):
        outline = bytearray(width * height)
        for y in range(height):
            for x in range(width):
                if not mask[y * width + x]:
                    continue
                for oy in range(-radius_y, radius_y + 1):
                    for ox in range(-radius_x, radius_x + 1):
                        nx, ny = x + ox, y + oy
                        if not 0 <= nx < width or not 0 <= ny < height:
                            continue
                        # Keep the inner outline solid; let only the new outer
                        # pixel fringe flicker in small deterministic clusters.
                        outer = abs(ox) == radius_x or abs(oy) == radius_y
                        noise = (nx * 17 + ny * 31 + frame_index * 13 + ox * 7 + oy * 19) & 7
                        if not outer or noise < 6:
                            outline[ny * width + nx] = 1
        selected = bytearray(width * height * 4)
        for i, inside in enumerate(mask):
            offset = i * 4
            if inside:
                selected[offset:offset + 4] = bytes((255, 255, 255, 255))
            elif outline[i]:
                selected[offset:offset + 4] = bytes((0, 0, 0, 255))
        selected_frames.append(selected)
    return idle, selected_frames


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


def ink_on_yellow(pixels: bytearray, width: int, height: int) -> bytearray:
    """Trace the official pose's color/alpha edges as ink on the yellow card."""
    result = bytearray(len(pixels))
    for y in range(height):
        for x in range(width):
            i = (y * width + x) * 4
            if pixels[i + 3] < 96:
                continue
            edge = x == 0 or y == 0 or x == width - 1 or y == height - 1
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if not (0 <= nx < width and 0 <= ny < height):
                    edge = True
                    continue
                ni = (ny * width + nx) * 4
                if pixels[ni + 3] < 96 or max(abs(pixels[i + c] - pixels[ni + c])
                                               for c in range(3)) >= 56:
                    edge = True
            if edge:
                result[i:i + 4] = bytes((18, 12, 17, 255))
    return result


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


def reserve_palette_color(palette: list[tuple[int, int, int]], color: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    """Keep the official right-note red in the 4bpp CLUT without tinting idle art."""
    if not palette:
        return [color]
    # Replace the nearest color, retaining palette ordering and capacity.
    # This pins the red hue through RGB555 conversion; gray idle pixels still
    # map to their own gray entries because quantization is per source pixel.
    nearest = min(range(len(palette)), key=lambda i: sum(
        (palette[i][channel] - color[channel]) ** 2 for channel in range(3)))
    return palette[:nearest] + [color] + palette[nearest + 1:]


def write_header(output: pathlib.Path,
                 palette8: list[tuple[int, int, int]],
                 palette4: list[tuple[int, int, int]],
                 palette_bf8: list[tuple[int, int, int]],
                 palette_ui4: list[list[tuple[int, int, int]]],
                 palette_popup4: list[tuple[int, int, int]],
                 stage_layout: dict[str, int], scene_bounds: tuple[int, int, int, int],
                 pages8: list[bytearray], pages4: list[bytearray],
                 page_table: list[tuple[int, int, int]], bf_idle_sequence: list[int],
                 descriptors: dict[str, dict], menu_screen_pages: list[bytearray],
                 menu_dj_pages: list[bytearray], menu_dj_frame_names: list[str],
                 menu_dj_first_page: int,
                 menu_dj_frame_size: tuple[int, int],
                 week2_stage_pages: list[bytearray],
                 week2_character_pages: list[bytearray],
                 week2_palette: list[tuple[int, int, int]],
                 week2_stage_origin: tuple[int, int],
                 week2_camera_zoom_q8: int,
                 week2_lightning_origin: tuple[int, int],
                 week2_lightning_world_size: tuple[int, int],
                 week2_character_first_page: int,
                 week3_stage_pages: list[bytearray],
                 week3_character_pages: list[bytearray],
                 week3_palette: list[tuple[int, int, int]],
                 week3_stage_origin: tuple[int, int],
                 week3_camera_zoom_q8: int,
                 week3_char_layout: dict[str, int],
                 menu_character_icons: list[list[int]],
                 menu_icon_bounds: list[tuple[int, int, int, int]],
                 death_palette8: list[tuple[int, int, int]],
                 death_frames: list[bytearray],
                 menu_button_frames: list[bytearray],
                 menu_row_backgrounds: list[bytearray]) -> None:
    lines = ["/* Generated by convert_bopeebo_visuals.py; do not edit. */",
             "#ifndef BOPEEBO_VISUAL_DATA_H", "#define BOPEEBO_VISUAL_DATA_H",
             "#include <stdint.h>",
             "typedef struct { uint8_t page, palette, u, v; uint16_t w, h; } BopeeboVisualFrame;",
             "typedef struct { uint16_t x, y; uint8_t depth; } BopeeboVisualPage;",
             f"#define BOPEEBO_VISUAL_PAGE_COUNT {len(page_table)}u",
             f"#define BOPEEBO_VISUAL_PAGE8_COUNT {len(pages8)}u",
             f"#define BOPEEBO_VISUAL_PAGE4_COUNT {len(pages4)}u",
             f"#define BOPEEBO_MENU_SCREEN_COUNT {len(menu_screen_pages)}u",
             f"#define BOPEEBO_MENU_DJ_FRAME_COUNT {len(menu_dj_frame_names)}u",
             f"#define BOPEEBO_MENU_DJ_PAGE_COUNT {len(menu_dj_pages)}u",
             f"#define BOPEEBO_MENU_DJ_FIRST_PAGE {menu_dj_first_page}u",
             f"#define BOPEEBO_MENU_DJ_FRAME_W {menu_dj_frame_size[0]}u",
             f"#define BOPEEBO_MENU_DJ_FRAME_H {menu_dj_frame_size[1]}u",
             f"#define BOPEEBO_WEEK2_STAGE_X ({week2_stage_origin[0]})",
             f"#define BOPEEBO_WEEK2_STAGE_Y ({week2_stage_origin[1]})",
             f"#define BOPEEBO_WEEK2_CAMERA_ZOOM_Q8 {week2_camera_zoom_q8}u",
             f"#define BOPEEBO_WEEK2_LIGHTNING_X ({week2_lightning_origin[0]})",
             f"#define BOPEEBO_WEEK2_LIGHTNING_Y ({week2_lightning_origin[1]})",
             f"#define BOPEEBO_WEEK2_LIGHTNING_WORLD_W {week2_lightning_world_size[0]}u",
             f"#define BOPEEBO_WEEK2_LIGHTNING_WORLD_H {week2_lightning_world_size[1]}u",
             f"#define BOPEEBO_WEEK2_LIGHTNING_TEX_W {WEEK2_LIGHTNING_TEX_W}u",
             f"#define BOPEEBO_WEEK2_LIGHTNING_TEX_H {WEEK2_LIGHTNING_TEX_H}u",
             f"#define BOPEEBO_WEEK2_MONSTER_FRAME_W {WEEK2_MONSTER_FRAME_W}u",
             f"#define BOPEEBO_WEEK2_MONSTER_FRAME_H {WEEK2_MONSTER_FRAME_H}u",
             f"#define BOPEEBO_WEEK2_CHARACTER_FIRST_PAGE {week2_character_first_page}u",
             f"#define BOPEEBO_WEEK2_STAGE_PAGE_COUNT {len(week2_stage_pages)}u",
             f"#define BOPEEBO_WEEK2_CHARACTER_PAGE_COUNT {len(week2_character_pages)}u",
             f"#define BOPEEBO_WEEK2_PAGE_COUNT {len(week2_stage_pages) + len(week2_character_pages)}u",
             f"#define BOPEEBO_WEEK2_CHARACTER_FRAME_W {WEEK2_CHAR_W}u",
             f"#define BOPEEBO_WEEK2_CHARACTER_FRAME_H {WEEK2_CHAR_H}u",
             f"#define BOPEEBO_WEEK3_STAGE_X ({week3_stage_origin[0]})",
             f"#define BOPEEBO_WEEK3_STAGE_Y ({week3_stage_origin[1]})",
             f"#define BOPEEBO_WEEK3_CAMERA_ZOOM_Q8 {week3_camera_zoom_q8}u",
             f"#define BOPEEBO_WEEK3_STAGE_PAGE_COUNT {len(week3_stage_pages)}u",
             f"#define BOPEEBO_WEEK3_CHARACTER_PAGE_COUNT {len(week3_character_pages)}u",
             f"#define BOPEEBO_WEEK3_PAGE_COUNT {len(week3_stage_pages) + len(week3_character_pages)}u",
             "#define BOPEEBO_WEEK3_CHARACTER_FRAME_W 72u",
             "#define BOPEEBO_WEEK3_CHARACTER_FRAME_H 84u",
             "#define BOPEEBO_MENU_CAPSULE_W 148u",
             "#define BOPEEBO_MENU_CAPSULE_H 32u",
             "#define BOPEEBO_MENU_ICON_COUNT 11u",
             "#define BOPEEBO_MENU_ICON_WORDS 392u",
             f"#define BOPEEBO_VISUAL_FRAME_COUNT {len(descriptors)}u",
             f"#define BOPEEBO_STAGE_SCENE_X ({scene_bounds[0]})",
             f"#define BOPEEBO_STAGE_SCENE_Y ({scene_bounds[1]})",
             f"#define BOPEEBO_STAGE_SCENE_W {scene_bounds[2]}u",
             f"#define BOPEEBO_STAGE_SCENE_H {scene_bounds[3]}u",
             f"#define BOPEEBO_STAGE_CAMERA_ZOOM_Q8 {stage_layout['camera_zoom_q8']}u",
             "#define BOPEEBO_DAD_FRAME_W 53u", "#define BOPEEBO_DAD_FRAME_H 96u",
             "#define BOPEEBO_GF_FRAME_W 87u", "#define BOPEEBO_GF_FRAME_H 79u",
             "#define BOPEEBO_GF_DANCE_FRAMES_PER_BEAT 5u",
             "#define BOPEEBO_DEATH_FRAME_W 80u", "#define BOPEEBO_DEATH_FRAME_H 96u",
             "#define BOPEEBO_DEATH_INTRO_COUNT 10u",
             "#define BOPEEBO_DEATH_LOOP_COUNT 6u",
             "#define BOPEEBO_DEATH_CONFIRM_COUNT 6u",
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
    # Week 2 temporarily replaces seven existing 8bpp slots, then restores
    # their Week 1 contents on exit. This keeps the global VRAM map unchanged
    # while allowing the complete GF dance cycle its own Week 2 CLUT/page data.
    w2_page_slots = [0, 1] + [2, 3, 4, 5, 6][:len(week2_character_pages)]
    lines.append("static const uint8_t bopeebo_week2_page_slots[BOPEEBO_WEEK2_PAGE_COUNT] = {" +
                 ",".join(str(slot) for slot in w2_page_slots) + "};")
    w3_page_slots = [0, 1] + [2, 3][:len(week3_character_pages)]
    lines.append("static const uint8_t bopeebo_week3_page_slots[BOPEEBO_WEEK3_PAGE_COUNT] = {" +
                 ",".join(str(slot) for slot in w3_page_slots) + "};")
    for name, value in week3_char_layout.items():
        lines.append(f"#define BOPEEBO_WEEK3_{name.upper()} ({value})")
    values = [0] + [rgb555(c) for c in palette_popup4[:15]]
    values += [0] * (16 - len(values))
    lines.append("static const uint16_t bopeebo_visual_palette_popup4[16] = {" +
                  ",".join(f"0x{x:04x}" for x in values) + "};")
    values = [0] + [rgb555(c) for c in palette8[:255]]
    values += [0] * (256 - len(values))
    lines.append("static const uint16_t bopeebo_visual_palette8[256] = {" +
                  ",".join(f"0x{x:04x}" for x in values) + "};")
    values = [0] + [rgb555(c) for c in death_palette8[:255]]
    values += [0] * (256 - len(values))
    lines.append("static const uint16_t bopeebo_death_palette8[256] = {" +
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
    lines.append(f"#define BOPEEBO_BF_IDLE_SEQUENCE_LENGTH {len(bf_idle_sequence)}u")
    lines.append("static const uint8_t bopeebo_bf_idle_sequence[BOPEEBO_BF_IDLE_SEQUENCE_LENGTH] = {" +
                 ",".join(str(frame) for frame in bf_idle_sequence) + "};")
    lines.append(f"static const uint16_t bopeebo_menu_button_frames[{len(menu_button_frames)}][2304] __attribute__((aligned(4))) = {{")
    for frame in menu_button_frames:
        words = [frame[i] | (frame[i + 1] << 8) for i in range(0, len(frame), 2)]
        lines.append("\t{" + ",".join(f"0x{v:04x}" for v in words) + "},")
    lines.append("};")
    lines.append("static const uint16_t bopeebo_menu_row_backgrounds[4][2304] __attribute__((aligned(4))) = {")
    for pixels in menu_row_backgrounds:
        words = [pixels[i] | (pixels[i + 1] << 8) for i in range(0, len(pixels), 2)]
        lines.append("{")
        for i in range(0, len(words), 16):
            lines.append("\t" + ",".join(f"0x{v:04x}" for v in words[i:i + 16]) + ",")
        lines.append("},")
    lines.append("};")
    lines.append(f"static const uint16_t bopeebo_death_frames[{len(death_frames)}][3840] __attribute__((aligned(4))) = {{")
    for frame in death_frames:
        words = [frame[i] | (frame[i + 1] << 8) for i in range(0, len(frame), 2)]
        lines.append("\t{")
        for i in range(0, len(words), 16):
            lines.append("\t\t" + ",".join(f"0x{v:04x}" for v in words[i:i + 16]) + ",")
        lines.append("\t},")
    lines.append("};")
    lines.append(f"static const uint16_t bopeebo_menu_dj_pages[{len(menu_dj_pages)}][32768] __attribute__((aligned(4))) = {{")
    for page in menu_dj_pages:
        words = [page[i] | (page[i + 1] << 8) for i in range(0, len(page), 2)]
        lines.append("\t{")
        for i in range(0, len(words), 16):
            lines.append("\t\t" + ",".join(f"0x{v:04x}" for v in words[i:i + 16]) + ",")
        lines.append("\t},")
    lines.append("};")
    lines.append(f"static const uint16_t bopeebo_menu_screen_pages[{len(menu_screen_pages)}][32768] = {{")
    for page in menu_screen_pages:
        words = [page[i] | (page[i + 1] << 8) for i in range(0, len(page), 2)]
        lines.append("\t{")
        for i in range(0, len(words), 16):
            lines.append("\t\t" + ",".join(f"0x{v:04x}" for v in words[i:i + 16]) + ",")
        lines.append("\t},")
    lines.append("};")
    lines.append(f"static const uint16_t bopeebo_menu_character_icons[{len(menu_character_icons)}][BOPEEBO_MENU_ICON_WORDS] __attribute__((aligned(4))) = {{")
    for icon in menu_character_icons:
        lines.append("\t{" + ",".join(f"0x{v:04x}" for v in icon) + "},")
    lines.append("};")
    lines.append(f"static const uint8_t bopeebo_menu_icon_bounds[{len(menu_icon_bounds)}][4] = {{")
    for left, top, right, bottom in menu_icon_bounds:
        lines.append(f"\t{{{left}, {top}, {right}, {bottom}}},")
    lines.append("};")
    lines.append("/* 8bpp/4bpp gameplay pages are stored in W1SCENE.BIN and loaded on demand. */")
    lines.extend(("#endif",))
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

    # Official Week 2 stage background and opponent rigs. Spooky Kids are a
    # Sparrow duet; Monster is an Animate rig. Keep their pages separate from
    # Week 1 palettes and temporarily reuse VRAM pages 0..2 during Week 2.
    week2_stage_json = json.loads(
        (assets / "preload" / "data" / "stages" / "spookyMansion.json").read_text(encoding="utf-8"))
    # Match the existing Week 1 world-to-screen calibration: its authored
    # cameraZoom 1.1 maps to Q8 640 (2.5x), after the scene art is downscaled.
    week2_camera_zoom_q8 = max(1, int(float(week2_stage_json["cameraZoom"]) * 640.0 / 1.1 + 0.5))
    week2_prop = next(prop for prop in week2_stage_json["props"] if prop["name"] == "halloweenBG")
    week2_atlas_path = assets / "week2" / "images" / "halloween_bg" / "spritemap1.json"
    week2_atlas = json.loads(week2_atlas_path.read_text(encoding="utf-8"))["ATLAS"]
    week2_bg_sprite = next(item["SPRITE"] for item in week2_atlas["SPRITES"]
                           if item["SPRITE"]["name"] == "0")
    week2_source_size = png_size(assets / "week2" / "images" / "halloween_bg" / "spritemap1.png")
    week2_bg_w = max(1, round(int(week2_bg_sprite["w"]) / WEEK2_STAGE_DIVISOR))
    week2_bg_raw_h = max(1, round(int(week2_bg_sprite["h"]) / WEEK2_STAGE_DIVISOR))
    week2_bg_h = min(week2_bg_raw_h, PAGE_H)
    week2_crop_y = (week2_bg_raw_h - week2_bg_h) // 2
    week2_stage_origin = (
        math.floor(float(week2_prop["position"][0]) / WEEK2_STAGE_DIVISOR + 0.5),
        math.floor(float(week2_prop["position"][1]) / WEEK2_STAGE_DIVISOR + 0.5) - week2_crop_y)
    week2_bg = run_ffmpeg(ffmpeg, assets / "week2" / "images" / "halloween_bg" / "spritemap1.png",
        f"crop={week2_bg_sprite['w']}:{week2_bg_sprite['h']}:{week2_bg_sprite['x']}:{week2_bg_sprite['y']},"
        f"scale={week2_bg_w}:{week2_bg_raw_h}:flags=area,crop={week2_bg_w}:{week2_bg_h}:0:{week2_crop_y},"
        f"format=rgba", week2_bg_w, week2_bg_h)
    week2_stage_rig = Rig(assets / "week2" / "images" / "halloween_bg", ffmpeg)
    # The Animate root instance matrix applies to both the exported base atlas
    # artwork and the timeline layers. Keep both in the same local coordinate
    # space before baking the static scene; shifting only the timeline layers
    # made the permanent room/window drift away from the background prop.
    week2_scale = 1.0 / WEEK2_STAGE_DIVISOR
    week2_root = week2_stage_rig.animation["AN"].get("STI", {}).get("SI", {})
    week2_root_matrix = tuple(week2_root.get("MX", (1, 0, 0, 1, 0, 0)))
    week2_root_dx = math.floor(week2_root_matrix[4] * week2_scale + 0.5)
    week2_root_dy = math.floor(week2_root_matrix[5] * week2_scale + 0.5)
    week2_bg_base = bytearray(week2_bg_w * week2_bg_h * 4)
    for i in range(0, len(week2_bg_base), 4):
        week2_bg_base[i:i + 4] = bytes((36, 35, 54, 255))
    week2_bg_shifted = bytearray(week2_bg_w * week2_bg_h * 4)
    for sy in range(week2_bg_h):
        dy = sy + week2_root_dy
        if dy < 0 or dy >= week2_bg_h:
            continue
        for sx in range(week2_bg_w):
            dx = sx + week2_root_dx
            if dx < 0 or dx >= week2_bg_w:
                continue
            src = (sy * week2_bg_w + sx) * 4
            dst = (dy * week2_bg_w + dx) * 4
            week2_bg_shifted[dst:dst + 4] = week2_bg[src:src + 4]
    alpha_over(week2_bg_base, week2_bg_shifted)
    # Bake the permanent room/window state once. Lightning samples remain
    # separate transient overlays and still use this same root transform.
    week2_render_scale = (week2_scale, 0, 0, week2_scale,
                          week2_root_matrix[4] * week2_scale,
                          week2_root_matrix[5] * week2_scale - week2_crop_y)
    week2_static_decor = bytearray(week2_bg_w * week2_bg_h * 4)
    # Frame 29 still contains the rig's transient `flash` layer. Exclude only
    # that layer from the baked base so the room/window stay decorated but do
    # not remain brightly lit between scheduled thunder strikes.
    week2_lightning_symbol = week2_stage_rig.symbols["halloweem bg lightning strike"]
    week2_layers = week2_lightning_symbol["TL"]["L"]
    week2_static_layers = [layer for layer in week2_layers if layer.get("LN") != "flash"]
    week2_lightning_symbol["TL"]["L"] = week2_static_layers
    week2_stage_rig.walk(week2_stage_rig.animation["AN"]["N"], 30,
                         week2_render_scale,
                         (week2_bg_w, week2_bg_h, week2_static_decor))
    week2_lightning_symbol["TL"]["L"] = week2_layers
    # alpha_over returns a new buffer; assigning the return is essential. The
    # old discarded return was why the converted disk kept the flat Sprite 0
    # background and showed the room/window only in the transient flash patch.
    week2_bg_base = alpha_over(week2_bg_base, week2_static_decor)
    week2_stage_names = []
    for tile, x0 in enumerate((0, STAGE_TILE_W)):
        width = min(STAGE_TILE_W, week2_bg_w - x0)
        crop = bytearray()
        for y in range(week2_bg_h):
            start = (y * week2_bg_w + x0) * 4
            crop.extend(week2_bg_base[start:start + width * 4])
        name = f"week2_stage_scene_{tile}"
        temp_images[name] = crop
        frame_sizes[name] = (width, week2_bg_h)
        week2_stage_names.append(name)

    # Bake three samples from the pinned halloween_bg Animate rig. The original
    # prop animation is a full-scene composite; only its changing window area
    # is needed at runtime. These small patches fit in the unused right strip
    # of Week 2 stage page 1, avoiding extra VRAM pages or CD reads.
    week2_lightning_names: list[str] = []
    week2_lightning_crop = (92, 81, 255, 211)  # measured on the 362x262 PS1 scene
    week2_lightning_x0, week2_lightning_y0, week2_lightning_x1, week2_lightning_y1 = week2_lightning_crop
    week2_lightning_world_w = week2_lightning_x1 - week2_lightning_x0
    week2_lightning_world_h = week2_lightning_y1 - week2_lightning_y0
    week2_lightning_origin = (
        week2_stage_origin[0] + week2_lightning_x0,
        week2_stage_origin[1] + week2_lightning_y0 - week2_crop_y)
    for i, source_frame in enumerate((0, 1, 2)):
        full = bytearray(week2_bg_w * week2_bg_h * 4)
        # Use the same root instance transform as the permanent décor so the
        # flash patches land over that window rather than an atlas-scaled copy.
        week2_stage_rig.walk(week2_stage_rig.animation["AN"]["N"], source_frame,
                             week2_render_scale, (week2_bg_w, week2_bg_h, full))
        crop = bytearray(week2_lightning_world_w * week2_lightning_world_h * 4)
        for y in range(week2_lightning_world_h):
            src = ((week2_lightning_y0 + y) * week2_bg_w + week2_lightning_x0) * 4
            dst = y * week2_lightning_world_w * 4
            crop[dst:dst + week2_lightning_world_w * 4] = full[src:src + week2_lightning_world_w * 4]
        name = f"week2_lightning_{i}"
        temp_images[name] = fit_nearest(crop, week2_lightning_world_w,
                                        week2_lightning_world_h,
                                        WEEK2_LIGHTNING_TEX_W, WEEK2_LIGHTNING_TEX_H)
        frame_sizes[name] = (WEEK2_LIGHTNING_TEX_W, WEEK2_LIGHTNING_TEX_H)
        week2_lightning_names.append(name)

    week2_character_names: list[str] = []
    spooky_groups = atlas_frames(chars / "SpookyKids.xml")
    spooky_png = chars / "SpookyKids.png"
    spooky_selection = [
        (f"week2_spooky_idle_{pose}", "spooky dance idle", frame_index)
        for pose, frame_index in enumerate((0, 2, 4, 6, 8, 10, 12, 14))
    ]
    spooky_selection += [
        (f"week2_spooky_sing_left_{pose}", "note sing left", frame_index)
        for pose, frame_index in enumerate((0, 7))
    ]
    spooky_selection += [
        (f"week2_spooky_sing_down_{pose}", "spooky DOWN note", frame_index)
        for pose, frame_index in enumerate((0, 12))
    ]
    spooky_selection += [
        (f"week2_spooky_sing_up_{pose}", "spooky UP NOTE", frame_index)
        for pose, frame_index in enumerate((0, 2))
    ]
    spooky_selection += [
        (f"week2_spooky_sing_right_{pose}", "spooky sing right", frame_index)
        for pose, frame_index in enumerate((0, 12))
    ]
    for name, group, frame_index in spooky_selection:
        frames = spooky_groups.get(group)
        if not frames or frame_index >= len(frames):
            raise ValueError(f"missing Week 2 Spooky Kids frame {group}[{frame_index}]")
        temp_images[name] = extract_sparrow_frame(ffmpeg, spooky_png, frames[frame_index],
                                                 (WEEK2_CHAR_W, WEEK2_CHAR_H))
        frame_sizes[name] = (WEEK2_CHAR_W, WEEK2_CHAR_H)
        week2_character_names.append(name)

    monster_rig = Rig(chars / "monster", ffmpeg)
    # Render the official character symbols directly. The top-level Christmas
    # stage export positions Monster partly outside its composition viewport;
    # using it as a character sprite cuts the face/body at a vertical edge.
    monster_selections = (
        ("week2_monster_idle", "monster idle", 0),
        ("week2_monster_idle_hold", "monster idle", 6),
        ("week2_monster_sing_left", "Monster left note", 2),
        ("week2_monster_sing_right", "Monster Right note", 2),
        ("week2_monster_sing_up", "monster up note", 2),
        ("week2_monster_sing_down", "monster down", 2),
    )
    for name, symbol, source_frame in monster_selections:
        _, _, width, height, pixels = monster_rig.render_symbol_positioned(symbol, source_frame)
        if not pixels:
            raise ValueError(f"empty Week 2 Monster symbol frame {symbol}[{source_frame}]")
        temp_images[name] = fit_nearest(pixels, width, height,
            WEEK2_MONSTER_FRAME_W, WEEK2_MONSTER_FRAME_H, anchor_bottom=True)
        frame_sizes[name] = (WEEK2_MONSTER_FRAME_W, WEEK2_MONSTER_FRAME_H)
        week2_character_names.append(name)
    for name, png in (("week2_spooky_icon", assets / "preload" / "images" / "icons" / "icon-spooky.png"),
                      ("week2_monster_icon", assets / "preload" / "images" / "icons" / "icon-monster.png")):
        temp_images[name] = extract_crop(ffmpeg, png, 0, 0, 150, 150, (24, 24))
        frame_sizes[name] = (24, 24)
        week2_character_names.append(name)
    week2_character_palette_names = week2_stage_names + week2_character_names + week2_lightning_names

    bf_groups = atlas_frames(chars / "BOYFRIEND.xml")
    bf_png = chars / "BOYFRIEND.png"
    bf_idle_sequence: list[int] = []
    for anim, prefix in BF_ANIMS:
        frames = bf_groups.get(prefix)
        if not frames:
            raise ValueError(f"missing BF animation prefix in pinned atlas: {prefix}")
        if anim == "idle":
            # The official Sparrow idle contains 14 animation entries. Several
            # are duplicate atlas rectangles; keep all timeline steps but pack
            # each distinct raster only once into the texture pages.
            unique: dict[bytes, int] = {}
            for frame in frames:
                pixels = extract_sparrow_frame(ffmpeg, bf_png, frame, (FRAME_W, FRAME_H))
                key = bytes(pixels)
                index = unique.get(key)
                if index is None:
                    index = len(unique)
                    unique[key] = index
                    name = f"bf_idle_{index}"
                    temp_images[name] = pixels
                    frame_sizes[name] = (FRAME_W, FRAME_H)
                bf_idle_sequence.append(index)
            if len(bf_idle_sequence) != 14:
                raise ValueError(f"expected 14 official BF idle frames, got {len(bf_idle_sequence)}")
            continue
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

    # Week 1 GF defines danceLeft frames 0..14 and danceRight 15..29.
    # Sample five genuine source poses per side. This preserves the official
    # left/right alternation and 8 Hz pose cadence at 100 BPM while leaving
    # 8bpp VRAM room for Tutorial's GF singing directions.
    gf_source_ids = (0, 3, 6, 9, 12, 15, 18, 21, 24, 27)
    gf_anchored = fit_anchored_rig(gf_rig, list(gf_source_ids), 87, 79)
    for i, source_frame in enumerate(gf_source_ids):
        temp_images[f"gf_dance_{i}"] = gf_anchored[source_frame]
        frame_sizes[f"gf_dance_{i}"] = (87, 79)
    # Week 2 uses its own CLUT for the additional character atlas. Keep the
    # complete five-pose left/right dance cycle so changing to the Week 2
    # palette cannot recolor GF or collapse her dance to two repeated poses.
    week2_gf_names = []
    for pose, source_index in enumerate(range(10)):
        name = f"week2_gf_dance_{pose}"
        temp_images[name] = bytearray(temp_images[f"gf_dance_{source_index}"])
        frame_sizes[name] = frame_sizes[f"gf_dance_{source_index}"]
        week2_gf_names.append(name)
        week2_character_names.append(name)
    week2_character_palette_names.extend(week2_gf_names)

    # Week 3's train platform is composed from the pinned stage props at the
    # same 1/6 world scale used for its character anchors. The moving train is
    # deliberately left out of this first static scene package; it will be an
    # independently streamed animation layer in a later pass.
    week3_stage_json = json.loads(
        (assets / "preload" / "data" / "stages" / "phillyTrain.json").read_text(encoding="utf-8"))
    week3_camera_zoom_q8 = max(1, int(float(week3_stage_json["cameraZoom"]) * 640.0 / 1.1 + 0.5))
    week3_stage_divisor = 6
    week3_stage_w, week3_stage_h = 512, 256
    week3_stage_origin = (-64, 0)
    def week3_world(value: float) -> int:
        return math.floor(float(value) / week3_stage_divisor + 0.5)
    week3_stage_chars = week3_stage_json["characters"]
    week3_char_layout = {}
    for out_name, stage_name in (("pico", "dad"), ("bf", "bf"), ("gf", "gf")):
        source_char = week3_stage_chars[stage_name]
        week3_char_layout[f"{out_name}_x"] = week3_world(source_char["position"][0])
        week3_char_layout[f"{out_name}_y"] = week3_world(source_char["position"][1])
        camera_offset = source_char.get("cameraOffsets", [0, 0])
        week3_char_layout[f"{out_name}_camera_x"] = week3_world(camera_offset[0])
        week3_char_layout[f"{out_name}_camera_y"] = week3_world(camera_offset[1])
    week3_stage_rgba = bytearray(week3_stage_w * week3_stage_h * 4)
    for i in range(0, len(week3_stage_rgba), 4):
        week3_stage_rgba[i:i + 4] = bytes((14, 13, 27, 255))
    week3_props = sorted(week3_stage_json["props"], key=lambda prop: int(prop.get("zIndex", 0)))
    week3_layer_names = {"sky": "sky", "city": "city", "lights": "win",
                         "behindTrain": "behindTrain", "street": "street"}
    for prop in week3_props:
        if prop.get("name") not in week3_layer_names:
            continue
        layer_name = week3_layer_names[prop["name"]]
        source = assets / "week3" / "images" / "philly" / f"{layer_name}.png"
        src_w, src_h = png_size(source)
        scale = prop.get("scale", [1.0, 1.0])
        if not isinstance(scale, list):
            scale = [scale, scale]
        width = max(1, round(src_w * float(scale[0]) / week3_stage_divisor))
        height = max(1, round(src_h * float(scale[1]) / week3_stage_divisor))
        layer = run_ffmpeg(ffmpeg, source, f"scale={width}:{height}:flags=area,format=rgba",
                           width, height)
        px = math.floor(float(prop["position"][0]) / week3_stage_divisor + 0.5) - week3_stage_origin[0]
        py = math.floor(float(prop["position"][1]) / week3_stage_divisor + 0.5) - week3_stage_origin[1]
        blend_at(week3_stage_rgba, (week3_stage_w, week3_stage_h), layer, (width, height), (px, py))
    week3_stage_names = []
    for tile in range(2):
        name = f"week3_stage_scene_{tile}"
        pixels = bytearray()
        for y in range(week3_stage_h):
            start = (y * week3_stage_w + tile * 256) * 4
            pixels.extend(week3_stage_rgba[start:start + 256 * 4])
        temp_images[name] = pixels
        frame_sizes[name] = (256, week3_stage_h)
        week3_stage_names.append(name)

    pico_rig = Rig(assets / "shared" / "images" / "characters" / "pico" / "basic-animations", ffmpeg)
    week3_pico_sources = {
        "week3_pico_idle_0": 0, "week3_pico_idle_1": 7,
        "week3_pico_sing_left_0": 31, "week3_pico_sing_left_1": 35,
        "week3_pico_sing_down_0": 62, "week3_pico_sing_down_1": 66,
        "week3_pico_sing_up_0": 48, "week3_pico_sing_up_1": 52,
        "week3_pico_sing_right_0": 14, "week3_pico_sing_right_1": 18,
    }
    pico_poses = fit_anchored_rig(pico_rig, list(week3_pico_sources.values()), 72, 84)
    week3_character_names = []
    for name, source_frame in week3_pico_sources.items():
        temp_images[name] = mirror_rgba(pico_poses[source_frame], 72, 84)
        frame_sizes[name] = (72, 84)
        week3_character_names.append(name)
    for pose, source_index in enumerate((0, 5)):
        name = f"week3_gf_dance_{pose}"
        temp_images[name] = bytearray(temp_images[f"gf_dance_{source_index}"])
        frame_sizes[name] = frame_sizes[f"gf_dance_{source_index}"]
        week3_character_names.append(name)
    pico_icon = assets / "preload" / "images" / "icons" / "icon-pico.png"
    temp_images["week3_pico_icon"] = extract_crop(ffmpeg, pico_icon, 0, 0, 150, 150, (24, 24))
    frame_sizes["week3_pico_icon"] = (24, 24)
    week3_character_names.append("week3_pico_icon")
    week3_palette_names = week3_stage_names + week3_character_names

    # Tutorial uses Girlfriend as the opponent; keep her official four singing
    # poses available so opponent charts do not animate Dad over GF vocals.
    gf_sing_sources = {"left": 64, "down": 47, "up": 33, "right": 79}
    gf_sing_frames = fit_anchored_rig(gf_rig, list(gf_sing_sources.values()), 87, 79)
    for direction, source_frame in gf_sing_sources.items():
        temp_images[f"gf_sing_{direction}"] = gf_sing_frames[source_frame]
        frame_sizes[f"gf_sing_{direction}"] = (87, 79)

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

    # The original PopUpStuff uses three individual official combo-number
    # sprites (least-significant digit on the right), while PlayState uses the
    # VCR bitmap font for its score line. Keep both on the shared popup CLUT.
    combo_names: list[str] = []
    for digit in range(10):
        source = popup_dir / f"num{digit}.png"
        src_w, src_h = png_size(source)
        size = (max(1, round(src_w * 0.12)), max(1, round(src_h * 0.12)))
        name = f"ui_combo_num_{digit}"
        temp_images[name] = extract_crop(ffmpeg, source, 0, 0, src_w, src_h, size)
        frame_sizes[name] = size
        combo_names.append(name)

    score_glyph_names: dict[str, str] = {}
    score_font_png = assets / "fonts" / "vcr-bmp.png"
    score_font_desc = ET.parse(assets / "fonts" / "vcr-bmp.fnt").getroot()
    score_glyphs = {int(glyph.attrib["id"]): glyph.attrib for glyph in score_font_desc.findall("./chars/char")}
    for char in "Score: ,0123456789-":
        if char == " ":
            continue
        glyph = score_glyphs.get(ord(char))
        if not glyph or int(glyph["width"]) <= 0 or int(glyph["height"]) <= 0:
            raise ValueError(f"missing visible VCR bitmap glyph for score character {char!r}")
        src_w, src_h = int(glyph["width"]), int(glyph["height"])
        size = (max(1, round(src_w * 0.5)), max(1, round(src_h * 0.5)))
        name = f"ui_score_glyph_{ord(char)}"
        temp_images[name] = extract_crop(ffmpeg, score_font_png,
            int(glyph["x"]), int(glyph["y"]), src_w, src_h, size)
        frame_sizes[name] = size
        score_glyph_names[char] = name
        popup_names.append(name)
    popup_names.extend(combo_names)
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
    # Tutorial's GF portrait uses the existing 4bpp popup page and CLUT. This
    # avoids allocating another full 8bpp page for a single 24x24 icon.
    gf_icon_name = "ui_icon_gf"
    temp_images[gf_icon_name] = extract_crop(ffmpeg,
        icon_dir / "icon-gf.png", 0, 0, 150, 150, (24, 24))
    frame_sizes[gf_icon_name] = (24, 24)
    popup_names.append(gf_icon_name)

    # Official menu artwork shares the portrait texture page, so title/menu
    # navigation adds no additional page to the fixed VRAM map.
    logo_xml = assets / "preload" / "images" / "logoBumpin.xml"
    logo_png = assets / "preload" / "images" / "logoBumpin.png"
    logo_frames = atlas_frames(logo_xml).get("logo bumpin")
    if not logo_frames:
        raise ValueError("missing official logo bumpin frame in pinned assets")
    temp_images["menu_logo"] = extract_sparrow_frame(ffmpeg, logo_png, logo_frames[0], (160, 120))
    frame_sizes["menu_logo"] = (160, 120)
    freeplay_button_png = assets / "preload" / "images" / "mainmenu" / "freeplay.png"
    freeplay_button_xml = assets / "preload" / "images" / "mainmenu" / "freeplay.xml"
    menu_idle_art: dict[str, bytearray] = {}
    menu_selected_art: dict[str, list[bytearray]] = {}
    for label in ("storymode", "freeplay", "credits"):
        png = assets / "preload" / "images" / "mainmenu" / f"{label}.png"
        groups = atlas_frames(png.with_suffix(".xml"))
        idle_frames = groups.get(f"{label} idle")
        selected_frames = groups.get(f"{label} selected")
        if not idle_frames or not selected_frames:
            raise ValueError(f"missing official {label} idle/selected menu artwork")
        menu_idle_art[label] = extract_sparrow_frame(ffmpeg, png, idle_frames[0], (128, 36))
        menu_selected_art[label] = [extract_sparrow_frame(ffmpeg, png, frame, (128, 36))
                                    for frame in selected_frames[:3]]
        if len(menu_selected_art[label]) != 3:
            raise ValueError(f"expected three selected {label} animation frames")
        for frame_index, pixels in enumerate(menu_selected_art[label]):
            name = f"menu_{label}_button_{frame_index}"
            temp_images[name] = pixels
            frame_sizes[name] = (128, 36)
    options_png = pathlib.Path(args.options_art).resolve() if args.options_art else \
        assets / "preload" / "images" / "mainmenu" / "options.png"
    if not options_png.is_file():
        raise ValueError(f"Options lettering image not found: {options_png}")
    options_idle, options_selected = menu_label_states(ffmpeg, options_png)
    temp_images["menu_options_idle"] = options_idle
    frame_sizes["menu_options_idle"] = (128, 36)
    menu_selected_art["options"] = options_selected
    for frame_index, pixels in enumerate(options_selected):
        name = f"menu_options_button_{frame_index}"
        temp_images[name] = pixels
        frame_sizes[name] = (128, 36)
    # Full-screen menu art is composed offline at its source aspect ratio and
    # reuses one existing 8bpp VRAM page, loaded only while the front-end runs.
    menu_bg_source = assets / "preload" / "images" / "menuBG.png"
    menu_bg = extract_menu_cover(ffmpeg, menu_bg_source, 256, 192)
    title_screen = bytearray((8, 7, 16, 255) * (256 * 192))
    logo_overlay = extract_sparrow_frame(ffmpeg, logo_png, logo_frames[0], (184, 138))
    blend_at(title_screen, (256, 192), logo_overlay, (184, 138), (36, 8))
    main_screen = bytearray(menu_bg)
    # Four evenly spaced rows use the same 128x36 source bounds and common
    # center. Keep a clean background patch for whichever row is selected.
    menu_labels = ("storymode", "freeplay", "options", "credits")
    menu_row_y = (19, 58, 96, 134)
    for label, y in zip(menu_labels, menu_row_y):
        if label == "options":
            # Draw this label at runtime from its own texture frame. Keeping it
            # out of the baked screen avoids stale/fallback icon pixels behind it.
            continue
        blend_at(main_screen, (256, 192), menu_idle_art[label], (128, 36), (64, y))
    menu_row_backgrounds_rgba = [bytearray(128 * 36 * 4) for _ in menu_labels]
    for row, y in enumerate(menu_row_y):
        for py in range(36):
            src = ((y + py) * 256 + 64) * 4
            dst = py * 128 * 4
            menu_row_backgrounds_rgba[row][dst:dst + 128 * 4] = menu_bg[src:src + 128 * 4]
    # Freeplay keeps the official week-one artwork, but crops to Dad so GF from
    # the source image cannot appear behind the song list. The 4:3 crop keeps
    # the source proportions; it does not stretch the original illustration.
    freeplay_bg = assets / "preload" / "images" / "freeplay" / "freeplayBGweek1-bf.png"
    # Keep the 821x516 source aspect ratio (306x192 here), then pan it right so
    # GF stays beyond the 4:3 viewport. The prior 430x322 crop magnified the
    # artwork and made Dad's proportions diverge from the approved composition.
    freeplay_base = bytearray(256 * 192 * 4)
    dad_background = run_ffmpeg(ffmpeg, freeplay_bg,
        "scale=306:192:flags=area,format=rgba", 306, 192)
    blend_at(freeplay_base, (256, 192), dad_background, (306, 192), (25, 0))
    freeplay_label_frames = atlas_frames(
        assets / "preload" / "images" / "mainmenu" / "freeplay.xml").get("freeplay selected")
    capsule_png = assets / "preload" / "images" / "freeplay" / "freeplayCapsule" / "capsule" / "freeplayCapsule.png"
    capsule_xml = assets / "preload" / "images" / "freeplay" / "freeplayCapsule" / "capsule" / "freeplayCapsule.xml"
    capsule_frames = atlas_frames(capsule_xml).get("mp3 capsule w backing")
    idle_capsule_frames = atlas_frames(capsule_xml).get("mp3 capsule w backing NOT SELECTED")
    if not freeplay_label_frames or not capsule_frames or not idle_capsule_frames:
        raise ValueError("missing official Freeplay label or selected song capsule")
    freeplay_label = extract_sparrow_frame(ffmpeg,
        assets / "preload" / "images" / "mainmenu" / "freeplay.png",
        freeplay_label_frames[0], (72, 20))
    temp_images["menu_freeplay_capsule_selected"] = extract_sparrow_frame(
        ffmpeg, capsule_png, capsule_frames[0], (148, 32))
    temp_images["menu_freeplay_capsule_idle"] = extract_sparrow_frame(
        ffmpeg, capsule_png, idle_capsule_frames[0], (148, 32))
    frame_sizes["menu_freeplay_capsule_selected"] = (148, 32)
    frame_sizes["menu_freeplay_capsule_idle"] = (148, 32)

    # Build the approved 4:3 Freeplay composition and extract the pinned BF DJ
    # intro/idle Animate frames. The runtime temporarily uses three gameplay
    # texture pages as a menu-only atlas and restores them before song loading.
    freeplay_difficulty_names = ("easy", "normal", "hard")
    freeplay_menu_names = [f"menu_screen_freeplay_{name}" for name in freeplay_difficulty_names]
    dj_rig = Rig(assets / "preload" / "images" / "freeplay" / "freeplay-boyfriend", ffmpeg)
    dj_target_w, dj_target_h = MENU_DJ_SOURCE_CANVAS_W, MENU_DJ_FRAME_H
    dj_animation_rgba = fit_anchored_rig(
        dj_rig, list(MENU_DJ_SOURCE_FRAMES), dj_target_w, dj_target_h)
    menu_dj_frame_names: list[str] = []
    for frame_index in MENU_DJ_SOURCE_FRAMES:
        name = f"menu_freeplay_dj_frame_{frame_index:03d}"
        frame = dj_animation_rgba[frame_index]
        if len(frame) != dj_target_w * dj_target_h * 4:
            raise ValueError(f"unexpected Freeplay DJ frame size at source frame {frame_index}")
        menu_dj_frame_names.append(name)

    screen = bytearray(freeplay_base)
    # Yellow paper panel: its left edge is fixed, its right edge widens toward
    # the bottom exactly as in the accepted mockup. No black scan lines are
    # painted over the official decorative words.
    panel_top, panel_h = 19, 173
    for y in range(panel_top, 192):
        local_y = y - panel_top
        right = 102 + (13 * local_y // max(1, panel_h - 1))
        for x in range(right):
            offset = (y * 256 + x) * 4
            shade = ((x * 7 + local_y * 3) % 13) - 6
            screen[offset:offset + 4] = bytes((
                max(0, min(255, 255 + shade)),
                max(0, min(255, 218 + shade)),
                max(0, min(255, 45 + shade // 2)), 255))

    # Preserve the official glowingText shapes while recoloring separate rows
    # with visible gold, yellow-orange and orange inks. Different intensity
    # keeps them legible as background decoration behind the DJ figure.
    glowing_png = assets / "preload" / "images" / "freeplay" / "glowingText.png"
    hype_rows = (
        (4, 0, 419, 55, 96, 13, (230, 172, 20), 188, 2, 10),
        (4, 63, 419, 107, 96, 25, (231, 132, 24), 190, 4, 31),
        (3, 178, 421, 68, 87, 15, (241, 187, 32), 205, 6, 72),
        (4, 254, 440, 101, 78, 18, (224, 105, 23), 180, 22, 111),
    )
    for sx, sy, sw, sh, rw, rh, ink, strength, dx, dy in hype_rows:
        row = extract_crop(ffmpeg, glowing_png, sx, sy, sw, sh, (rw, rh))
        for i in range(0, len(row), 4):
            alpha = row[i + 3] * strength // 255
            row[i:i + 4] = bytes((*ink, alpha))
        blend_at(screen, (256, 192), row, (rw, rh), (dx, panel_top + dy))

    # VCR-like title strip and official Freeplay lettering; best-score text is
    # drawn at runtime from session records, never from mockup sample values.
    for y in range(27):
        for x in range(256):
            offset = (y * 256 + x) * 4
            screen[offset:offset + 4] = bytes((9, 8, 18, 255))
    # Leave a small top-safe margin: the user's DuckStation capture clipped
    # the upper edge of both the title strip and its runtime score line.
    blend_at(screen, (256, 192), freeplay_label, (72, 20), (7, 7))
    # The approved 320x240 mockup uses this exact VCR font family. Rasterize
    # uppercase glyphs at converter time to avoid BIOS-font substitution and
    # tiny, distorted 5x7 reductions of the unrelated Freeplay alphabet art.
    letter_atlas = vcr_letter_atlas(ffmpeg, assets / "fonts" / "vcr-bold.ttf")
    temp_images["menu_freeplay_letters"] = letter_atlas
    frame_sizes["menu_freeplay_letters"] = (48, 36)

    # Tight-crop the rig's shared horizontal bounds while preserving its
    # common floor and transparent background. The previous 82x90 rectangle
    # contained only a 31px-wide character during idle, making BF look tiny.
    # Drawing this 31x90 sprite at 1.75x gives the figure useful scale without
    # stretching or repainting the yellow menu art.
    opaque_x = []
    for frame in dj_animation_rgba.values():
        for y in range(dj_target_h):
            for x in range(dj_target_w):
                if frame[(y * dj_target_w + x) * 4 + 3] >= 96:
                    opaque_x.append(x)
    dj_crop_left, dj_crop_right = min(opaque_x), max(opaque_x) + 1
    dj_frame_w = dj_crop_right - dj_crop_left
    if not 0 < dj_frame_w <= dj_target_w:
        raise ValueError(f"invalid shared DJ rig width {dj_frame_w}")
    for frame_index, name in zip(MENU_DJ_SOURCE_FRAMES, menu_dj_frame_names):
        cropped = bytearray(dj_frame_w * MENU_DJ_FRAME_H * 4)
        for row in range(dj_target_h):
            src = (row * dj_target_w + dj_crop_left) * 4
            dst = row * dj_frame_w * 4
            cropped[dst:dst + dj_frame_w * 4] = \
                dj_animation_rgba[frame_index][src:src + dj_frame_w * 4]
        temp_images[name] = cropped
        frame_sizes[name] = (dj_frame_w, MENU_DJ_FRAME_H)
    # Palette sampling uses only a few transparent rig poses, not every opaque
    # composited frame; repeated yellow background pixels must not crowd Dad's
    # or the gameplay stage colors out of the shared 8bpp CLUT.
    menu_dj_palette_names = []
    for sample_index in (0, 9, 12):
        frame_index = MENU_DJ_SOURCE_FRAMES[sample_index]
        name = f"menu_freeplay_dj_palette_{frame_index:03d}"
        temp_images[name] = dj_animation_rgba[frame_index]
        frame_sizes[name] = (dj_target_w, dj_target_h)
        menu_dj_palette_names.append(name)

    # Difficulty selector uses the official label artwork and selector arrows
    # seen in the approved mockup. Each complete 256x192 screen is stored as a
    # separate front-end page and loaded through the already-used full-page path.
    selector_png = assets / "preload" / "images" / "freeplay" / "freeplaySelector.png"
    selector_xml = assets / "preload" / "images" / "freeplay" / "freeplaySelector.xml"
    selector_frame = atlas_frames(selector_xml).get("arrow pointer loop")
    if not selector_frame:
        raise ValueError("missing official Freeplay selector arrow")
    selector_left = extract_sparrow_frame(ffmpeg, selector_png, selector_frame[0], (12, 22))
    selector_right = mirror_rgba(selector_left, 12, 22)
    freeplay_menu_screens: list[bytearray] = []
    for difficulty_name in freeplay_difficulty_names:
        difficulty_png = assets / "preload" / "images" / "freeplay" / f"freeplay{difficulty_name}.png"
        if not difficulty_png.is_file():
            raise ValueError(f"missing official Freeplay difficulty art: {difficulty_png}")
        difficulty_label = run_ffmpeg(ffmpeg, difficulty_png,
            "scale=46:15:flags=area,format=rgba", 46, 15)
        temp_images[f"menu_freeplay_difficulty_{difficulty_name}"] = difficulty_label
        variant = bytearray(screen)
        # Coordinates are the approved 320x240 positions scaled to the 256x192
        # backing texture, not independent positional retuning.
        blend_at(variant, (256, 192), selector_left, (12, 22), (9, 25))
        blend_at(variant, (256, 192), difficulty_label, (46, 15), (24, 28))
        blend_at(variant, (256, 192), selector_right, (12, 22), (72, 25))
        freeplay_menu_screens.append(variant)
    temp_images["menu_freeplay_selector_left"] = selector_left
    temp_images["menu_freeplay_selector_right"] = selector_right

    # Tiny official pixel heads: 28px boxes are a 16.7% increase over the
    # previous 24px icons. Runtime placement uses each icon's opaque bounds.
    menu_icon_files = ("gfpixel", "dadpixel", "spookypixel", "picopixel",
                       "mompixel", "monsterpixel", "parents-christmaspixel",
                       "senpaipixel", "spiritpixel", "tankmanpixel", "darnellpixel")
    menu_icon_images: list[str] = []
    for icon in menu_icon_files:
        icon_png = assets / "preload" / "images" / "freeplay" / "icons" / f"{icon}.png"
        icon_xml = assets / "preload" / "images" / "freeplay" / "icons" / f"{icon}.xml"
        frames = atlas_frames(icon_xml).get("idle")
        if not frames:
            raise ValueError(f"missing official idle portrait for {icon}")
        image_name = f"menu_character_{icon}"
        temp_images[image_name] = extract_sparrow_frame(ffmpeg, icon_png, frames[0], (28, 28))
        frame_sizes[image_name] = (28, 28)
        menu_icon_images.append(image_name)

    # Song titles remain runtime UI; difficulty art is composed offline into
    # each complete Freeplay screen page.
    menu_screen_names = ["menu_screen_title", "menu_screen_main", *freeplay_menu_names]
    menu_screen_pixels = [title_screen, main_screen, *freeplay_menu_screens]
    for name, pixels in zip(menu_screen_names, menu_screen_pixels):
        temp_images[name] = pixels
        frame_sizes[name] = (256, 192)
    menu_button_names = [f"menu_{label}_button_{i}"
        for label in ("storymode", "freeplay", "options", "credits") for i in range(3)]
    # Menu selection frames are uploaded from ROM to the reserved menu strip;
    # packing copies into the permanent texture pages would waste a full page.
    menu_names = ["menu_logo"]

    # Game over replaces the menu page at runtime. Its animation frames are
    # kept in main RAM, using the pinned Animate rig rather than a still pose.
    death_ids = (0, 6, 12, 18, 24, 30, 36, 42, 48, 57,
                 58, 64, 70, 76, 82, 91,
                 92, 99, 106, 113, 120, 125)
    death_rig = Rig(chars / "bf-death", ffmpeg)
    death_source = fit_anchored_rig(death_rig, list(death_ids), 80, 96)
    death_images = [death_source[index] for index in death_ids]
    death_palette8 = median_palette(death_images, 255)
    death_frames = [quantize(pixels, death_palette8) for pixels in death_images]

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
    # The three DJ idle variants reuse the same Week 1 backdrop and capsule
    # colors; sample one variant so repetition does not bias the shared CLUT.
    menu_palette_names = (menu_names + menu_button_names + menu_screen_names + menu_dj_palette_names +
                          ["menu_options_idle", "menu_freeplay_capsule_selected",
                           "menu_freeplay_capsule_idle", "menu_freeplay_letters",
                           "menu_freeplay_selector_left", "menu_freeplay_selector_right",
                           "menu_freeplay_difficulty_easy", "menu_freeplay_difficulty_normal",
                           "menu_freeplay_difficulty_hard"] +
                          menu_icon_images)
    palette8 = median_palette([temp_images[n] for n in stage_names + dad_names + gf_names + menu_palette_names], 255)
    week2_palette = median_palette([temp_images[n] for n in week2_character_palette_names], 255)
    week3_palette = median_palette([temp_images[n] for n in week3_palette_names], 255)
    palette4 = median_palette([temp_images[n] for n in bf_miss_names], 15)
    palette_ui4 = [median_palette([temp_images[n] for n in ui4_by_direction[d]], 15)
                   for d in directions]
    # The note and receptor primitives must use the same verified CLUT path.
    # Reserve the official right-note red inside the right-lane palette so the
    # GPU cannot lose that sprite through a separate palette address. Requantize
    # all right-lane states against it and report the resulting color error.
    palette_ui4[3] = reserve_palette_color(
        median_palette([temp_images[n] for n in ui4_by_direction["right"]], 15),
        (249, 57, 63))
    palette_bf8 = median_palette([temp_images[n] for n in bf_core_names], 255)
    palette_popup4 = median_palette([temp_images[n] for n in popup_names], 15)
    quantized8 = {name: quantize(pixels, palette8) for name, pixels in temp_images.items()
                  if not name.startswith(("bf_", "ui_", "week2_", "week3_"))}
    quantized_week2 = {name: quantize(temp_images[name], week2_palette)
                       for name in week2_character_palette_names}
    quantized_week3 = {name: quantize(temp_images[name], week3_palette)
                       for name in week3_palette_names}
    menu_dj_frames = [quantized8[name] for name in menu_dj_frame_names]
    quantized4 = {name: quantize(temp_images[name], palette4) for name in bf_miss_names}
    quantized_ui4 = {
        name: quantize(temp_images[name], palette_ui4[lane])
        for lane, direction in enumerate(directions)
        for name in ui4_by_direction[direction]
    }
    right_source = temp_images["ui_note_right"]
    right_indices = quantized_ui4["ui_note_right"]
    right_red = 0
    for pixel, palette_index in enumerate(right_indices):
        source = pixel * 4
        if right_source[source + 3] < 128 or right_source[source] < 180 or \
                right_source[source + 1] > 110 or right_source[source + 2] > 135:
            continue
        right_red += 1
        decoded = rgb555_roundtrip(palette_ui4[3][palette_index - 1])
        if decoded[0] < 150 or decoded[1] > 130 or decoded[2] > 155:
            raise ValueError(f"official right-note red was lost in the generated CLUT: {decoded}")
    if right_red == 0:
        raise ValueError("official right-note extraction contains no opaque red pixels")
    quantized_bf8 = {name: quantize(temp_images[name], palette_bf8) for name in bf_core_names}
    quantized_popup4 = {name: quantize(temp_images[name], palette_popup4) for name in popup_names}
    quantized_icon8 = {
        name: quantize(temp_images[name],
                       palette8 if name in ("ui_icon_dad", "ui_icon_gf") else palette_bf8)
        for name in icon_names
    }
    menu_screen_pages: list[bytearray] = []
    menu_page_regions = [
        ("capsule_selected", 0, 192, 148, 32),
        ("capsule_idle", 0, 224, 148, 32),
        ("vcr_glyph_atlas", 148, 192, 48, 36),
        ("icon_slot_0", 196, 192, 28, 28),
        ("icon_slot_1", 224, 192, 28, 28),
        ("icon_slot_2", 196, 220, 28, 28),
        ("icon_slot_3", 224, 220, 28, 28),
    ]
    for index, (name, x, y, width, height) in enumerate(menu_page_regions):
        if x < 0 or y < 0 or x + width > PAGE_W or y + height > PAGE_H:
            raise ValueError(f"Freeplay VRAM region {name} exceeds the texture page")
        for other_name, ox, oy, ow, oh in menu_page_regions[:index]:
            if x < ox + ow and ox < x + width and y < oy + height and oy < y + height:
                raise ValueError(f"Freeplay VRAM regions {name} and {other_name} overlap")
    for index in range(26):
        x, y = 148 + (index % 8) * 6, 192 + (index // 8) * 9
        if x + 5 > 148 + 48 or y + 8 > 192 + 36:
            raise ValueError(f"VCR glyph {index} exceeds its 48x36 atlas")
    for name, x, y, width, height in (
            ("left selector", 9, 25, 12, 22),
            ("difficulty label", 24, 28, 46, 15),
            ("right selector", 72, 25, 12, 22)):
        if x < 0 or y < 0 or x + width > 256 or y + height > 192:
            raise ValueError(f"{name} exceeds the 256x192 Freeplay screen")
    for name in menu_screen_names:
        indices = quantize(temp_images[name], palette8)
        page = bytearray(PAGE_W * PAGE_H)
        page[:256 * 192] = indices
        if name.startswith("menu_screen_freeplay_"):
            def page_blit(source_name: str, x: int, y: int) -> None:
                width, height = frame_sizes[source_name]
                if x < 0 or y < 0 or x + width > PAGE_W or y + height > PAGE_H:
                    raise ValueError(f"menu page blit {source_name} is out of bounds")
                source = quantized8[source_name]
                for row in range(height):
                    dst = (y + row) * PAGE_W + x
                    src = row * width
                    page[dst:dst + width] = source[src:src + width]
            page_blit("menu_freeplay_capsule_selected", 0, 192)
            page_blit("menu_freeplay_capsule_idle", 0, 224)
            page_blit("menu_freeplay_letters", 148, 192)
        elif name == "menu_screen_main":
            # Reserve the right half of the main-menu texture's unused lower
            # strip for the approved custom label. The selected-label upload
            # occupies x=0..127 on the same row, so both states can coexist.
            width, height = frame_sizes["menu_options_idle"]
            if width != 128 or height != 36:
                raise ValueError("OPTIONS label must fit its 128x36 reserved strip")
            for row in range(height):
                dst = (192 + row) * PAGE_W + 128
                src = row * width
                page[dst:dst + width] = quantized8["menu_options_idle"][src:src + width]
        menu_screen_pages.append(page)
    menu_character_icon_words: list[list[int]] = []
    menu_character_icon_bounds: list[tuple[int, int, int, int]] = []
    for name in menu_icon_images:
        indices = quantized8[name]
        menu_character_icon_words.append([
            indices[i] | (indices[i + 1] << 8) for i in range(0, len(indices), 2)])
        width, height = frame_sizes[name]
        opaque = [(i % width, i // width) for i, alpha in enumerate(
            temp_images[name][3::4]) if alpha >= 128]
        if not opaque:
            raise ValueError(f"menu portrait has no opaque pixels: {name}")
        menu_character_icon_bounds.append((min(x for x, _ in opaque),
                                           min(y for _, y in opaque),
                                           max(x for x, _ in opaque) + 1,
                                           max(y for _, y in opaque) + 1))
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
    pack_8bpp([(n, quantized_bf8[n], *frame_sizes[n]) for n in bf_core_names] +
              [(n, quantized_icon8[n], *frame_sizes[n]) for n in icon_names],
              bf8_first, 2, pages8, descriptors)
    portrait_first_page = len(pages8)
    pack_8bpp(
        [(name, quantized8[name], *frame_sizes[name]) for name in menu_names],
        portrait_first_page, 0, pages8, descriptors)
    for name in icon_names:
        descriptors[name]["palette"] = 0 if name in ("ui_icon_dad", "ui_icon_gf") else 2
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
    descriptors["ui_note_right"]["palette"] = 6

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
                    ("palette_bf8", 0, 480, 256, 1), ("palette_popup4", 288, 480, 16, 1),
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

    # Week 2 reuses gameplay texture pages 0..2 while loaded. Its dedicated
    # palette and full-page payloads leave the validated Week 1 CLUT untouched.
    week2_stage_pages = [bytearray(PAGE_W * PAGE_H) for _ in range(2)]
    for tile, name in enumerate(week2_stage_names):
        width, height = frame_sizes[name]
        indices = quantized_week2[name]
        for py in range(height):
            src = py * width
            dst = py * PAGE_W
            week2_stage_pages[tile][dst:dst + width] = indices[src:src + width]
        descriptors[name] = {"page": tile, "palette": 0, "u": 0, "v": 0,
                             "w": width, "h": height}

    # Page 1's background tile is only 106 pixels wide. Pack the three small
    # lightning frames into its otherwise-unused right-hand strip.
    for i, name in enumerate(week2_lightning_names):
        indices = quantized_week2[name]
        x, y = 112, i * (WEEK2_LIGHTNING_TEX_H + 1)
        if x + WEEK2_LIGHTNING_TEX_W > PAGE_W or y + WEEK2_LIGHTNING_TEX_H > PAGE_H:
            raise ValueError("Week 2 lightning patch exceeds reserved stage-page space")
        for py in range(WEEK2_LIGHTNING_TEX_H):
            src = py * WEEK2_LIGHTNING_TEX_W
            dst = (y + py) * PAGE_W + x
            week2_stage_pages[1][dst:dst + WEEK2_LIGHTNING_TEX_W] = indices[src:src + WEEK2_LIGHTNING_TEX_W]
        descriptors[name] = {"page": 1, "palette": 0, "u": x, "v": y,
                             "w": WEEK2_LIGHTNING_TEX_W, "h": WEEK2_LIGHTNING_TEX_H}

    week2_character_pages: list[bytearray] = []
    week2_character_local: dict[str, dict] = {}
    pack_8bpp([(name, quantized_week2[name], *frame_sizes[name])
               for name in week2_character_names], 0, 8,
              week2_character_pages, week2_character_local)
    if len(week2_character_pages) != 5:
        raise ValueError(f"Week 2 character atlas needs {len(week2_character_pages)} pages; expected five")
    week2_character_page_slots = (2, 3, 4, 5, 6)
    for name, frame in week2_character_local.items():
        descriptors[name] = {**frame,
            "page": week2_character_page_slots[int(frame["page"])], "palette": 0}
    for name in week2_stage_names:
        descriptors[name]["palette"] = 0

    week3_stage_pages = [bytearray(PAGE_W * PAGE_H) for _ in range(2)]
    for tile, name in enumerate(week3_stage_names):
        indices = quantized_week3[name]
        for py in range(PAGE_H):
            src = py * PAGE_W
            week3_stage_pages[tile][src:src + PAGE_W] = indices[src:src + PAGE_W]
        descriptors[name] = {"page": tile, "palette": 0, "u": 0, "v": 0,
                             "w": PAGE_W, "h": PAGE_H}

    week3_character_pages: list[bytearray] = []
    week3_character_local: dict[str, dict] = {}
    pack_8bpp([(name, quantized_week3[name], *frame_sizes[name])
               for name in week3_character_names], 0, 8,
              week3_character_pages, week3_character_local)
    if not week3_character_pages or len(week3_character_pages) > 2:
        raise ValueError(f"Week 3 character atlas needs {len(week3_character_pages)} pages; expected one or two")
    week3_character_page_slots = (2, 3)
    for name, frame in week3_character_local.items():
        descriptors[name] = {**frame,
            "page": week3_character_page_slots[int(frame["page"])], "palette": 0}
    for name in week3_stage_names:
        descriptors[name]["palette"] = 0

    # Check every packed frame, not only the page's outer rectangle. This
    # catches allocator overlap, invalid UV rectangles and page-depth errors.
    occupied: dict[int, list[tuple[str, int, int, int, int]]] = collections.defaultdict(list)
    for name, desc in descriptors.items():
        if name.startswith(("week2_", "week3_")):
            continue  # Week-specific overlay pages reuse Week 1 VRAM slots.
        page_index = int(desc["page"])
        depth4 = name.startswith(("ui_note_", "ui_receptor_", "ui_hold_", "ui_icon_gf",
                                  "ui_judgement_", "ui_combo_num_", "ui_score_glyph_", "bf_miss_"))
        page_count = len(page_table)
        if not 0 <= page_index < page_count:
            raise ValueError(f"{name} references invalid texture page {page_index}")
        expected_depth = 0 if depth4 else 1
        if page_table[page_index][2] != expected_depth:
            raise ValueError(f"{name} depth {expected_depth} disagrees with page {page_index}")
        x, y, w, h = (int(desc[k]) for k in ("u", "v", "w", "h"))
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > PAGE_W or y + h > PAGE_H:
            raise ValueError(f"{name} UV rectangle {(x, y, w, h)} exceeds its 256x256 texture page")
        for other, ox, oy, ow, oh in occupied[page_index]:
            if x < ox + ow and ox < x + w and y < oy + oh and oy < y + h:
                raise ValueError(f"packed frames {name} and {other} overlap on page {page_index}")
        occupied[page_index].append((name, x, y, w, h))

    # In Freeplay only, the 8bpp page immediately before the dedicated menu
    # page becomes a complete DJ-frame atlas. Upload/restore it as a whole
    # pages, using the full-page transfer path that was already exercised.
    menu_page_index = int(descriptors["menu_logo"]["page"])
    if menu_page_index != len(pages8) - 1 or menu_page_index < 1:
        raise ValueError("the menu texture page must remain the final 8bpp page")
    menu_dj_first_page = menu_page_index - 1
    menu_dj_pages: list[bytearray] = []
    menu_dj_local_frames: dict[str, dict] = {}
    pack_8bpp([(name, quantized8[name], *frame_sizes[name])
               for name in menu_dj_frame_names],
              0, 0, menu_dj_pages, menu_dj_local_frames)
    if len(menu_dj_pages) != 1:
        raise ValueError(f"expected one packed DJ page, got {len(menu_dj_pages)}")
    menu_dj_local_occupied: dict[int, list[tuple[str, int, int, int, int]]] = collections.defaultdict(list)
    for name, frame in menu_dj_local_frames.items():
        page_no = int(frame["page"])
        x, y, width, height = (int(frame[k]) for k in ("u", "v", "w", "h"))
        if not 0 <= page_no < len(menu_dj_pages) or x + width > PAGE_W or y + height > PAGE_H:
            raise ValueError(f"Freeplay DJ frame {name} exceeds its complete texture pages")
        for other, ox, oy, ow, oh in menu_dj_local_occupied[page_no]:
            if x < ox + ow and ox < x + width and y < oy + oh and oy < y + height:
                raise ValueError(f"Freeplay DJ frames {name} and {other} overlap")
        menu_dj_local_occupied[page_no].append((name, x, y, width, height))
        descriptors[name] = {**frame, "page": menu_dj_first_page + page_no, "palette": 0}
    for name in menu_dj_frame_names:
        frame = descriptors[name]
        page_index = int(frame["page"])
        if not 0 <= page_index < len(page_table) or page_table[page_index][2] != 1:
            raise ValueError(f"Freeplay DJ frame {name} is not on a valid 8bpp page")

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
    print(f"Right-note red shares the right-lane CLUT with receptors/holds: {right_red} opaque source pixels; palette RMSE includes the full right-lane set")
    print(f"All {len(descriptors)} atlas rectangles have valid page depth/UV bounds with no packed-frame overlap")
    print(f"Official judgement art/health icons: 4bpp shared CLUT RMSE {rmse(popup_names, palette_popup4):.2f} RGB levels")
    print("Official combo digits and VCR score glyphs: nearest-neighbor 4bpp in shared popup CLUT")
    print("Official health portraits at 24x24 use the 8bpp character CLUTs (Dad/main, BF/BF)")
    print("Freeplay page checks: 6x9 VCR glyph cells, capsules, icon slots and difficulty art fit without overlap")
    print(f"Freeplay DJ checks: 9 sampled Intro frames + 7 sampled Idle frames, anchored to one floor; crop {dj_frame_w}x{MENU_DJ_FRAME_H} has transparent margins and scales 1.75x at runtime")
    print(f"Freeplay DJ atlas: {len(menu_dj_pages)} full-page 8bpp texture ({len(menu_dj_pages) * 65536} bytes resident); underlying menu background remains a separate layer")
    print(f"Freeplay DJ color check: shared 8bpp CLUT RMSE {rmse(menu_dj_frame_names, palette8):.2f} RGB levels; palette sampled from 3 transparent poses only")
    print(f"Week 2 art: {week2_bg_w}x{week2_bg_h} stage, aligned root background/decor, 8 Spooky idle poses, 10 GF dance poses, per-pose {WEEK2_MONSTER_FRAME_W}x{WEEK2_MONSTER_FRAME_H} Monster, {len(week2_lightning_names)} official lightning frames, {len(week2_character_names)} character/icon frames, {len(week2_stage_pages)} stage + {len(week2_character_pages)} character pages, dedicated 255-color CLUT, RMSE {rmse(week2_character_palette_names, week2_palette):.2f} RGB levels")
    week2_payload_path = pathlib.Path(args.week2_pages_output)
    week2_payload_path.parent.mkdir(parents=True, exist_ok=True)
    palette_words = [0] + [rgb555(c) for c in week2_palette[:255]]
    palette_words += [0] * (256 - len(palette_words))
    week2_payload_path.write_bytes(
        b"".join(bytes(page) for page in week2_stage_pages + week2_character_pages) +
        struct.pack("<256H", *palette_words))
    print(f"Week 2 package: {len(week2_stage_pages)} stage + {len(week2_character_pages)} character pages, {week2_payload_path.stat().st_size} bytes on disc")
    week1_payload_path = pathlib.Path(args.week1_pages_output)
    week1_payload_path.parent.mkdir(parents=True, exist_ok=True)
    week1_payload_path.write_bytes(b"".join(bytes(page) for page in pages8 + pages4))
    print(f"Week 1 shared gameplay package: {len(pages8)} 8bpp + {len(pages4)} 4bpp pages, {week1_payload_path.stat().st_size} bytes on disc; page arrays are no longer resident in executable data")
    week3_payload_path = pathlib.Path(args.week3_pages_output)
    week3_payload_path.parent.mkdir(parents=True, exist_ok=True)
    week3_palette_words = [0] + [rgb555(c) for c in week3_palette[:255]]
    week3_palette_words += [0] * (256 - len(week3_palette_words))
    week3_payload_path.write_bytes(
        b"".join(bytes(page) for page in week3_stage_pages + week3_character_pages) +
        struct.pack("<256H", *week3_palette_words))
    print(f"Week 3 package: {len(week3_stage_pages)} stage + {len(week3_character_pages)} Pico/GF character pages, {week3_payload_path.stat().st_size} bytes on disc")
    menu_row_background_indices = [quantize(pixels, palette8) for pixels in menu_row_backgrounds_rgba]
    write_header(pathlib.Path(args.output), palette8, palette4, palette_bf8, palette_ui4,
                 palette_popup4, stage_layout, scene_bounds,
                 pages8, pages4, page_table, bf_idle_sequence, descriptors,
                 menu_screen_pages, menu_dj_pages, menu_dj_frame_names,
                 menu_dj_first_page, (dj_frame_w, MENU_DJ_FRAME_H),
                 week2_stage_pages, week2_character_pages, week2_palette,
                 week2_stage_origin, week2_camera_zoom_q8, week2_lightning_origin,
                 (week2_lightning_world_w, week2_lightning_world_h), 2,
                 week3_stage_pages, week3_character_pages, week3_palette,
                 week3_stage_origin, week3_camera_zoom_q8, week3_char_layout,
                 menu_character_icon_words,
                 menu_character_icon_bounds, death_palette8, death_frames,
                 [quantized8[f"menu_{label}_button_{i}"]
                  for label in ("storymode", "freeplay", "options", "credits")
                  for i in range(3)],
                 menu_row_background_indices)
    print(f"Animate frames: Dad {len(dad_names)} (idle + 4 sings), GF {len(gf_names)} dance/sing; BF {len(bf_names)} official Sparrow frames")
    print(f"VRAM map verified: {len(pages8)}x8bpp + {len(pages4)}x4bpp, framebuffers, CLUTs and font reserve are in bounds without overlap")
    print(f"VRAM textures: {len(pages8)}x8bpp + {len(pages4)}x4bpp = {len(pages8)*65536+len(pages4)*32768} bytes; generated header {pathlib.Path(args.output).stat().st_size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, help="root of the pinned assets submodule")
    parser.add_argument("--ffmpeg", required=True, help="path to ffmpeg")
    parser.add_argument("--options-art", help="approved local OPTIONS lettering PNG; falls back to pinned source art")
    parser.add_argument("--output", required=True, help="generated C header (kept in the build directory)")
    parser.add_argument("--week2-pages-output", required=True,
                        help="raw Week 2 stage/character pages and CLUT payload for the CD image")
    parser.add_argument("--week1-pages-output", required=True,
                        help="raw Week 1 gameplay pages for demand loading from the CD image")
    parser.add_argument("--week3-pages-output", required=True,
                        help="raw Week 3 stage/Pico pages followed by its RGB555 palette")
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
