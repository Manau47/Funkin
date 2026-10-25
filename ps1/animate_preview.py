#!/usr/bin/env python3
"""Small offline renderer for the Animate symbol rigs used by Dad and GF."""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import subprocess
import zlib


def mul(a, b):
    return (a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
            a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
            a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5])


IDENTITY = (1, 0, 0, 1, 0, 0)


def png_rgba(path: pathlib.Path) -> tuple[int, int, bytearray]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    pos, width, height, bit_depth, color_type = 8, 0, 0, 0, 0
    compressed = bytearray()
    while pos < len(data):
        size = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + size]
        if kind == b"IHDR":
            width, height, bit_depth, color_type, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            if (bit_depth, color_type, interlace) != (8, 6, 0):
                raise ValueError(f"expected non-interlaced RGBA8 PNG, got {bit_depth}/{color_type}/{interlace}")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
        pos += 12 + size
    raw = zlib.decompress(compressed)
    stride = width * 4
    pixels = bytearray(height * stride)
    prev = bytearray(stride)
    offset = 0
    for y in range(height):
        filt = raw[offset]
        offset += 1
        row = bytearray(raw[offset:offset + stride])
        offset += stride
        for i in range(stride):
            left = row[i - 4] if i >= 4 else 0
            up = prev[i]
            upper_left = prev[i - 4] if i >= 4 else 0
            if filt == 1: row[i] = (row[i] + left) & 255
            elif filt == 2: row[i] = (row[i] + up) & 255
            elif filt == 3: row[i] = (row[i] + ((left + up) >> 1)) & 255
            elif filt == 4:
                p = left + up - upper_left
                pa, pb, pc = abs(p-left), abs(p-up), abs(p-upper_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                row[i] = (row[i] + predictor) & 255
            elif filt != 0: raise ValueError(f"unsupported PNG filter {filt}")
        pixels[y * stride:(y + 1) * stride] = row
        prev = row
    return width, height, pixels


def save_png(path: pathlib.Path, width: int, height: int, pixels: bytearray):
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * stride:(y + 1) * stride])
    content = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    content += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    path.write_bytes(content)


class Rig:
    def __init__(self, root: pathlib.Path, ffmpeg: str):
        self.root = root
        self.animation = json.loads((root / "Animation.json").read_text(encoding="utf-8"))
        self.symbols = {item["SN"]: item for item in self.animation["SD"]["S"]}
        self.symbols[self.animation["AN"]["N"]] = {
            "SN": self.animation["AN"]["N"], "TL": self.animation["AN"]["TL"]
        }
        self.atlas = json.loads((root / "spritemap1.json").read_text(encoding="utf-8"))
        self.sprites = {item["SPRITE"]["name"]: item["SPRITE"] for item in self.atlas["ATLAS"]["SPRITES"]}
        image = root / "spritemap1.png"
        self.width, self.height = self.atlas["meta"]["size"]["w"], self.atlas["meta"]["size"]["h"]
        raw = subprocess.check_output([ffmpeg, "-v", "error", "-i", str(image), "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1"])
        self.atlas_pixels = bytearray(raw)
        if len(raw) != self.width * self.height * 4:
            raise ValueError("atlas RGBA decode size mismatch")

    @staticmethod
    def current_frame(frames, frame_index):
        active = None
        for key in frames:
            start = int(key.get("I", 0))
            if start <= frame_index:
                active = key
            else:
                break
        return active

    def walk(self, symbol_name, frame_index, matrix, out, recursion=0):
        if recursion > 16:
            raise ValueError(f"symbol recursion loop at {symbol_name}")
        symbol = self.symbols[symbol_name]
        layers = symbol.get("TL", {}).get("L", [])
        # Animate lists topmost layers first; draw back-to-front.
        for layer in reversed(layers):
            key = self.current_frame(layer.get("FR", []), frame_index)
            if not key:
                continue
            for event in key.get("E", []):
                if "ASI" in event:
                    item = event["ASI"]
                    sprite = self.sprites[item["N"]]
                    sm = tuple(item.get("MX", IDENTITY))
                    self.draw_sprite(sprite, mul(matrix, sm), out)
                elif "SI" in event:
                    item = event["SI"]
                    child = self.symbols[item["SN"]]
                    child_dur = max((int(f.get("I", 0)) + int(f.get("DU", 1))
                                     for layer2 in child.get("TL", {}).get("L", [])
                                     for f in layer2.get("FR", [])), default=1)
                    parent_key = int(key.get("I", 0))
                    ff = int(item.get("FF", 0))
                    child_frame = ff + frame_index - parent_key
                    if item.get("LP") == "LP" and child_dur:
                        child_frame %= child_dur
                    self.walk(item["SN"], child_frame, mul(matrix, tuple(item.get("MX", IDENTITY))), out, recursion + 1)

    def draw_sprite(self, sprite, matrix, out):
        x, y, w, h = (int(sprite[k]) for k in ("x", "y", "w", "h"))
        rotated = sprite.get("rotated", False)
        if rotated:
            w, h = h, w
        a, b, c, d, tx, ty = matrix
        det = a * d - b * c
        if abs(det) < 1e-8:
            return
        corners = [(tx, ty), (a*w+tx, b*w+ty), (c*h+tx, d*h+ty), (a*w+c*h+tx, b*w+d*h+ty)]
        minx, maxx = min(p[0] for p in corners), max(p[0] for p in corners)
        miny, maxy = min(p[1] for p in corners), max(p[1] for p in corners)
        xa, xb = max(0, int(minx)), min(out[0], int(maxx) + 1)
        ya, yb = max(0, int(miny)), min(out[1], int(maxy) + 1)
        ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
        for oy in range(ya, yb):
            for ox in range(xa, xb):
                dx, dy = ox + 0.5 - tx, oy + 0.5 - ty
                sx, sy = ia*dx + ic*dy, ib*dx + id_*dy
                if sx < 0 or sy < 0 or sx >= w or sy >= h:
                    continue
                if rotated:
                    source_x, source_y = x + h - 1 - int(sy), y + int(sx)
                else:
                    source_x, source_y = x + int(sx), y + int(sy)
                si = (source_y * self.width + source_x) * 4
                di = (oy * out[0] + ox) * 4
                alpha = self.atlas_pixels[si + 3]
                if not alpha:
                    continue
                if alpha == 255:
                    out[2][di:di + 4] = self.atlas_pixels[si:si + 4]
                else:
                    inv = 255 - alpha
                    olda = out[2][di + 3]
                    oa = alpha + olda * inv // 255
                    if oa:
                        for channel in range(3):
                            out[2][di + channel] = (self.atlas_pixels[si + channel] * alpha + out[2][di + channel] * olda * inv // 255) // oa
                    out[2][di + 3] = oa

    def render_positioned(self, frame_index, canvas=1200):
        pixels = bytearray(canvas * canvas * 4)
        center = canvas // 2
        # The source Animate stage is 1920x1080; its exported character rigs
        # are positioned in that coordinate system. Crop bounds come from the
        # actual transformed atlas fragments and are normalized below.
        self.walk(self.animation["AN"]["N"], frame_index, (1, 0, 0, 1, center, center), (canvas, canvas, pixels))
        occupied = [i for i in range(3, len(pixels), 4) if pixels[i]]
        if not occupied:
            return 0, 0, bytearray()
        xs, ys = [], []
        for y in range(canvas):
            for x in range(canvas):
                if pixels[(y * canvas + x) * 4 + 3]:
                    xs.append(x); ys.append(y)
        x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
        width, height = x1 - x0, y1 - y0
        crop = bytearray(width * height * 4)
        for y in range(height):
            a = ((y + y0) * canvas + x0) * 4
            crop[y * width * 4:(y + 1) * width * 4] = pixels[a:a + width * 4]
        return x0 - center, y0 - center, width, height, crop

    def render(self, frame_index, canvas=1200):
        """Render one rig frame, retaining the legacy tightly-cropped result."""
        _, _, width, height, pixels = self.render_positioned(frame_index, canvas)
        return width, height, pixels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("asset_dir", type=pathlib.Path)
    parser.add_argument("ffmpeg")
    parser.add_argument("frame", type=int)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    rig = Rig(args.asset_dir, args.ffmpeg)
    w, h, data = rig.render(args.frame)
    if not data:
        raise SystemExit("empty character frame")
    save_png(args.output, w, h, data)
    print(f"frame {args.frame}: {w}x{h} ({len(data)} RGBA bytes)")


if __name__ == "__main__":
    main()
