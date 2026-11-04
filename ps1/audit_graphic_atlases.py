#!/usr/bin/env python3
"""Audit indexed PS1 texture pages and emit annotated PNG contact sheets.

Only Python's standard library is used. The tool reads already-converted page
packages and their generated C headers; it never re-quantizes image data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import struct
import zlib
from pathlib import Path


def read_define(text: str, name: str) -> int:
    m = re.search(rf"^#define\s+{re.escape(name)}\s+(\d+)u?\s*$", text, re.M)
    if not m:
        raise ValueError(f"missing define {name}")
    return int(m.group(1))


def read_u16_array(text: str, name: str) -> list[int]:
    m = re.search(rf"static const uint16_t\s+{re.escape(name)}\s*\[[^]]*\]\s*=\s*\{{(.*?)\}};", text, re.S)
    if not m:
        raise ValueError(f"missing uint16 array {name}")
    return [int(v, 16 if v.lower().startswith("0x") else 10) for v in re.findall(r"0x[\da-fA-F]+|\b\d+\b", m.group(1))]


def parse_frames(text: str, type_name: str, array_name: str) -> list[dict]:
    m = re.search(rf"static const {re.escape(type_name)}\s+{re.escape(array_name)}\s*\[[^]]*\]\s*=\s*\{{(.*?)\n\}};", text, re.S)
    if not m:
        raise ValueError(f"missing frame array {array_name}")
    out = []
    for line in m.group(1).splitlines():
        row = re.search(r"\{([^{}]+)\}\s*,?\s*(?:/\*\s*(.*?)\s*\*/)?", line)
        if not row:
            continue
        vals = [int(x.rstrip("uU"), 0) for x in re.findall(r"(?<![A-Za-z_])(?:0x[\da-fA-F]+|\d+)[uU]?", row.group(1))]
        if len(vals) in (5, 9):
            if len(vals) == 5:
                page, u, v, w, h = vals
                palette = 0
            else:
                page, palette, u, v, w, h = vals[:6]
            out.append({"page": page, "palette": palette, "u": u, "v": v, "w": w, "h": h,
                        "label": row.group(2) or f"frame_{len(out)}"})
    return out


def rgb555(c: int) -> tuple[int, int, int]:
    return (((c >> 0) & 31) * 255 // 31,
            ((c >> 5) & 31) * 255 // 31,
            ((c >> 10) & 31) * 255 // 31)


def decode_page(raw: bytes, depth: int) -> list[int]:
    if depth == 1:  # PS1 8bpp: two texels per VRAM word
        if len(raw) != 65536:
            raise ValueError(f"8bpp page must be 65536 bytes, got {len(raw)}")
        return list(raw)
    if depth == 0:  # PS1 4bpp: four texels per VRAM word
        if len(raw) != 32768:
            raise ValueError(f"4bpp page must be 32768 bytes, got {len(raw)}")
        pixels = []
        for b in raw:
            pixels.extend((b & 15, b >> 4))
        return pixels
    raise ValueError(f"unsupported page depth {depth}")


def png(path: Path, width: int, height: int, rgba: bytes) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    stride = width * 4
    scan = b"".join(b"\0" + rgba[y * stride:(y + 1) * stride] for y in range(height))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress(scan, 9)) + chunk(b"IEND", b""))


FONT = {
    "A": [14,17,17,31,17,17,17], "B": [30,17,17,30,17,17,30], "C": [14,17,16,16,16,17,14],
    "D": [30,17,17,17,17,17,30], "E": [31,16,16,30,16,16,31], "F": [31,16,16,30,16,16,16],
    "G": [14,17,16,23,17,17,15], "H": [17,17,17,31,17,17,17], "I": [14,4,4,4,4,4,14],
    "J": [7,2,2,2,18,18,12], "K": [17,18,20,24,20,18,17], "L": [16,16,16,16,16,16,31],
    "M": [17,27,21,21,17,17,17], "N": [17,25,21,19,17,17,17], "O": [14,17,17,17,17,17,14],
    "P": [30,17,17,30,16,16,16], "Q": [14,17,17,17,21,18,13], "R": [30,17,17,30,20,18,17],
    "S": [15,16,16,14,1,1,30], "T": [31,4,4,4,4,4,4], "U": [17,17,17,17,17,17,14],
    "V": [17,17,17,17,17,10,4], "W": [17,17,17,21,21,21,10], "X": [17,17,10,4,10,17,17],
    "Y": [17,17,10,4,4,4,4], "Z": [31,1,2,4,8,16,31], "0": [14,17,19,21,25,17,14],
    "1": [4,12,4,4,4,4,14], "2": [14,17,1,2,4,8,31], "3": [30,1,1,14,1,1,30],
    "4": [2,6,10,18,31,2,2], "5": [31,16,16,30,1,1,30], "6": [14,16,16,30,17,17,14],
    "7": [31,1,2,4,8,8,8], "8": [14,17,17,14,17,17,14], "9": [14,17,17,15,1,1,14],
    "_": [0,0,0,0,0,0,31], "-": [0,0,0,31,0,0,0], " ": [0]*7,
}


def draw_text(buf: bytearray, width: int, x: int, y: int, text: str, color=(255, 255, 255, 255)) -> None:
    for i, char in enumerate(text.upper()):
        glyph = FONT.get(char, FONT["_"])
        for gy, bits in enumerate(glyph):
            for gx in range(5):
                if bits & (1 << (4 - gx)):
                    px, py = x + i * 6 + gx, y + gy
                    if 0 <= px < width and py >= 0:
                        o = (py * width + px) * 4
                        if o + 3 < len(buf):
                            buf[o:o+4] = bytes(color)


def build_atlas(name: str, package: Path, page_count: int, depths: list[int], frames: list[dict],
                palette: list[int], output: Path, extra_pages: list[bytes] | None = None) -> dict:
    raw = package.read_bytes()
    expected = sum(65536 if d else 32768 for d in depths)
    if len(raw) < expected:
        raise ValueError(f"{name}: package too short {len(raw)} < {expected}")
    pages = []
    offset = 0
    for i, depth in enumerate(depths):
        size = 65536 if depth else 32768
        chunk = raw[offset:offset+size]
        offset += size
        pages.append({"raw": chunk, "depth": depth, "pixels": decode_page(chunk, depth)})
    if extra_pages:
        for chunk in extra_pages:
            pages.append({"raw": chunk, "depth": 1, "pixels": decode_page(chunk, 1)})
    by_page = [[] for _ in pages]
    for f in frames:
        if f["page"] >= len(pages):
            continue
        if f["u"] + f["w"] > 256 or f["v"] + f["h"] > 256:
            f["invalid_uv"] = True
        by_page[f["page"]].append(f)

    page_metrics = []
    annotated = []
    for pidx, page in enumerate(pages):
        depth, pixels = page["depth"], page["pixels"]
        used = bytearray(65536)
        exact_rects: dict[tuple, bytes] = {}
        rect_dups = []
        covered_area = 0
        zero_in_rect = 0
        rects = by_page[pidx]
        for f in rects:
            key = (f["u"], f["v"], f["w"], f["h"])
            crop = bytearray()
            for y in range(f["v"], min(256, f["v"] + f["h"])):
                start = y * 256 + f["u"]
                row = pixels[start:start + min(f["w"], 256 - f["u"])]
                crop.extend(row)
                zero_in_rect += sum(1 for val in row if val == 0)
                for x in range(f["u"], min(256, f["u"] + f["w"])):
                    used[y * 256 + x] = 1
            if key in exact_rects and exact_rects[key] == bytes(crop):
                rect_dups.append(f["label"])
            exact_rects[key] = bytes(crop)
        covered_area = sum(used)
        duplicate_pixels = 0
        seen_payloads: dict[bytes, str] = {}
        for f in rects:
            crop = b"".join(bytes(pixels[y * 256 + f["u"]:y * 256 + f["u"] + f["w"]])
                            for y in range(f["v"], f["v"] + f["h"]))
            if crop in seen_payloads:
                duplicate_pixels += f["w"] * f["h"]
            else:
                seen_payloads[crop] = f["label"]
        zero_page = sum(1 for val in pixels if val == 0)
        boxes = [(f["u"], f["v"], f["w"], f["h"]) for f in rects]
        max_x = max((x+w for x,y,w,h in boxes), default=0)
        max_y = max((y+h for x,y,w,h in boxes), default=0)
        bounding_area = max_x * max_y
        page_metrics.append({"name": name, "page": pidx, "depth_bpp": 8 if depth else 4,
            "allocated_bytes": 65536 if depth else 32768, "rect_count": len(rects),
            "rect_area_sum_pixels": sum(f["w"]*f["h"] for f in rects), "rect_union_pixels": covered_area,
            "transparent_index0_page_pixels": zero_page, "transparent_index0_in_rects": zero_in_rect,
            "bounding_box_pixels": bounding_area, "holes_inside_frame_union_bbox_pixels": max(0, bounding_area-covered_area),
            "free_pixels_outside_frame_rect_union": 65536-covered_area,
            "duplicate_frame_payload_pixels": duplicate_pixels, "duplicate_rect_labels": rect_dups,
            "invalid_uv_labels": [f["label"] for f in rects if f.get("invalid_uv")],
            "frames": [f["label"] for f in rects]})

        # A contact sheet uses one palette for the whole package. Base W1 has
        # multiple CLUTs; index visualization is explicitly labeled there.
        rgba = bytearray(256 * 256 * 4)
        for i, idx in enumerate(pixels):
            if idx == 0:
                rgba[i*4:i*4+4] = b"\0\0\0\0"
            elif idx < len(palette):
                rgba[i*4:i*4+4] = bytes((*rgb555(palette[idx]), 255))
            else:
                rgba[i*4:i*4+4] = bytes((idx, idx, idx, 255))
        annotated.append(rgba)

    cols, cell_h, cell_w = 2, 282, 264
    rows = math.ceil(len(pages) / cols)
    sheet_w, sheet_h = cols * cell_w, rows * cell_h
    sheet = bytearray(sheet_w * sheet_h * 4)
    # dark background
    for i in range(0, len(sheet), 4): sheet[i:i+4] = b"\x10\x10\x18\xff"
    for i, page in enumerate(pages):
        ox, oy = (i % cols) * cell_w + 4, (i // cols) * cell_h + 20
        draw_text(sheet, sheet_w, ox, oy - 15, f"{name} PAGE {i} {8 if page['depth'] else 4}BPP")
        img = annotated[i]
        for y in range(256):
            src = y * 256 * 4
            dst = ((oy + y) * sheet_w + ox) * 4
            sheet[dst:dst + 256*4] = img[src:src + 256*4]
        # Rectangles are outlined in direction/palette color, numbering is a
        # stable index into the CSV legend and does not modify the source.
        for fi, f in enumerate(by_page[i]):
            color = ((255, 96, 64, 255) if f["palette"] == 0 else (64, 220, 255, 255))
            x0, y0, x1, y1 = ox + f["u"], oy + f["v"], ox + f["u"] + f["w"] - 1, oy + f["v"] + f["h"] - 1
            for x in range(max(ox, x0), min(ox+255, x1)+1):
                for y in (y0, y1):
                    if oy <= y < oy+256:
                        o=(y*sheet_w+x)*4; sheet[o:o+4]=bytes(color)
            for y in range(max(oy, y0), min(oy+255, y1)+1):
                for x in (x0, x1):
                    if ox <= x < ox+256:
                        o=(y*sheet_w+x)*4; sheet[o:o+4]=bytes(color)
            draw_text(sheet, sheet_w, min(x0, ox+220), max(oy, y0-8), str(fi % 100), color)
    png(output / f"{name.lower()}-atlas.png", sheet_w, sheet_h, bytes(sheet))
    return {"atlas": name, "package": str(package), "package_bytes": len(raw),
            "palette_bytes": len(palette)*2, "frame_count": len(frames), "pages": page_metrics}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-header", type=Path, required=True)
    ap.add_argument("--base-bin", type=Path, required=True)
    ap.add_argument("--w2-bin", type=Path, required=True)
    ap.add_argument("--w3-bin", type=Path, required=True)
    ap.add_argument("--w4-header", type=Path, required=True)
    ap.add_argument("--w4-bin", type=Path, required=True)
    ap.add_argument("--w5-header", type=Path, required=True)
    ap.add_argument("--w5-bin", type=Path, required=True)
    ap.add_argument("--w6-header", type=Path, required=True)
    ap.add_argument("--w6-bin", type=Path, required=True)
    ap.add_argument("--w7-header", type=Path, required=True)
    ap.add_argument("--w7-bin", type=Path, required=True)
    ap.add_argument("--wend-header", type=Path, required=True)
    ap.add_argument("--wend-bin", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    base = args.base_header.read_text(encoding="utf-8")
    base_pages = read_define(base, "BOPEEBO_VISUAL_PAGE_COUNT")
    base_8 = read_define(base, "BOPEEBO_VISUAL_PAGE8_COUNT")
    base_4 = read_define(base, "BOPEEBO_VISUAL_PAGE4_COUNT")
    base_frames = parse_frames(base, "BopeeboVisualFrame", "bopeebo_visual_frames")
    base_pal = read_u16_array(base, "bopeebo_visual_palette8")
    manifests = []
    manifests.append(build_atlas("BASE_W1", args.base_bin, base_pages,
        [1]*base_8+[0]*base_4, base_frames, base_pal, args.out))
    for label, hp, bp in [("WEEK2", args.base_header, args.w2_bin), ("WEEK3", args.base_header, args.w3_bin),
                          ("WEEK4", args.w4_header, args.w4_bin), ("WEEK5", args.w5_header, args.w5_bin),
                          ("WEEK6", args.w6_header, args.w6_bin), ("WEEK7", args.w7_header, args.w7_bin),
                          ("WEEKEND1", args.wend_header, args.wend_bin)]:
        text = hp.read_text(encoding="utf-8")
        macro = {"WEEK2":"BOPEEBO_WEEK2_PAGE_COUNT", "WEEK3":"BOPEEBO_WEEK3_PAGE_COUNT",
                 "WEEK4":"BOPEEBO_WEEK4_PAGE_COUNT", "WEEK5":"BOPEEBO_WEEK5_PAGE_COUNT",
                 "WEEK6":"BOPEEBO_WEEK6_PAGE_COUNT", "WEEK7":"BOPEEBO_WEEK7_PAGE_COUNT",
                 "WEEKEND1":"BOPEEBO_WEEKEND1_PAGE_COUNT"}[label]
        count = read_define(text, macro)
        type_name, array_name = {
            "WEEK2":("Week2VisualFrame","week2_visual_frames"), "WEEK3":("Week3VisualFrame","week3_visual_frames"),
            "WEEK4":("Week4VisualFrame","week4_visual_frames"), "WEEK5":("Week5VisualFrame","week5_visual_frames"),
            "WEEK6":("Week6VisualFrame","week6_visual_frames"), "WEEK7":("Week7VisualFrame","week7_visual_frames"),
            "WEEKEND1":("WeekEnd1VisualFrame","weekend1_visual_frames")}[label]
        if label in ("WEEK2", "WEEK3"):
            frames = [f for f in base_frames if f["label"].lower().startswith(label.lower())]
        else:
            frames = parse_frames(text, type_name, array_name)
        raw = bp.read_bytes()
        pal = list(struct.unpack("<256H", raw[count*65536:count*65536+512]))
        manifests.append(build_atlas(label, bp, count, [1]*count, frames, pal, args.out))
    (args.out / "atlas-audit.json").write_text(json.dumps(manifests, indent=2), encoding="utf-8")
    with (args.out / "atlas-pages.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["name", "page", "depth_bpp", "allocated_bytes", "rect_count", "rect_area_sum_pixels",
                  "rect_union_pixels", "transparent_index0_page_pixels", "transparent_index0_in_rects",
                  "bounding_box_pixels", "holes_inside_frame_union_bbox_pixels", "free_pixels_outside_frame_rect_union",
                  "duplicate_frame_payload_pixels", "invalid_uv_labels"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for atlas in manifests:
            for row in atlas["pages"]:
                writer.writerow({k: row[k] if k != "invalid_uv_labels" else ";".join(row[k]) for k in fields})
    print(f"Wrote {len(manifests)} atlas manifests and sheets to {args.out}")


if __name__ == "__main__":
    main()

