#!/usr/bin/env python3
"""Render contact sheets for the fixed menu/game-over texture arrays.

Reads generated headers only; does not modify/re-quantize any resource.
The arrays are packed as little-endian uint16 words containing two 8bpp texels.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from audit_graphic_atlases import png, rgb555, draw_text


def array_words(source: str, name: str) -> list[int]:
    m = re.search(rf"static const uint16_t\s+{re.escape(name)}\s*\[[^]]*\]\s*[^=]*=\s*\{{(.*?)\}};", source, re.S)
    if not m:
        raise ValueError(f"array not found: {name}")
    return [int(v, 16 if v.lower().startswith("0x") else 10)
            for v in re.findall(r"0x[\da-fA-F]+|\b\d+\b", m.group(1))]


def palette_words(source: str, name: str) -> list[int]:
    return array_words(source, name)


def unpack8(words: list[int]) -> list[int]:
    out: list[int] = []
    for v in words:
        out.extend((v & 0xff, v >> 8))
    return out


def rgba_for(indices: list[int], pal: list[int]) -> bytes:
    out = bytearray(len(indices) * 4)
    for i, idx in enumerate(indices):
        if idx == 0:
            continue
        c = pal[idx] if idx < len(pal) else 0x7fff
        out[i*4:i*4+4] = bytes((*rgb555(c), 255))
    return bytes(out)


def contact_sheet(name: str, frames: list[tuple[str, int, int, list[int]]], palette: list[int], out: Path) -> None:
    max_w = max((f[1] for f in frames), default=0)
    max_h = max((f[2] for f in frames), default=0)
    if max_w >= 256 or max_h >= 256:
        cell_w, cell_h, cols = 264, 282, 2
    else:
        cell_w, cell_h, cols = 144, 126, 4
    rows = (len(frames) + cols - 1) // cols
    width, height = cell_w * cols, cell_h * rows
    canvas = bytearray(width * height * 4)
    for i, (label, w, h, words) in enumerate(frames):
        ox, oy = (i % cols) * cell_w + 8, (i // cols) * cell_h + 20
        draw_text(canvas, width, ox, oy - 15, f"{name} {label}"[:20])
        pix = unpack8(words)
        rgba = rgba_for(pix, palette)
        for y in range(h):
            for x in range(w):
                src = (y*w+x)*4
                dst = ((oy+y)*width + ox+x)*4
                if oy+y < height and ox+x < width:
                    canvas[dst:dst+4] = rgba[src:src+4]
    png(out, width, height, bytes(canvas))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--header", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    text = args.header.read_text(encoding="utf-8")
    args.out.mkdir(parents=True, exist_ok=True)
    visual_pal = palette_words(text, "bopeebo_visual_palette8")
    death_pal = palette_words(text, "bopeebo_death_palette8")
    catalog = [
        ("menu-buttons", "bopeebo_menu_button_frames", 128, 36, visual_pal),
        ("menu-row-backgrounds", "bopeebo_menu_row_backgrounds", 128, 36, visual_pal),
        ("gameover-death-frames", "bopeebo_death_frames", 80, 96, death_pal),
        ("freeplay-dj-page", "bopeebo_menu_dj_pages", 256, 256, visual_pal),
        ("menu-title-pages", "bopeebo_menu_screen_pages", 256, 256, visual_pal),
        ("freeplay-character-icons", "bopeebo_menu_character_icons", 28, 28, visual_pal),
    ]
    report = []
    for filename, symbol, w, h, pal in catalog:
        words = array_words(text, symbol)
        frame_words = w * h // 2
        if len(words) % frame_words:
            raise ValueError(f"{symbol}: {len(words)} words not divisible by {frame_words}")
        count = len(words) // frame_words
        frames = [(f"{i:02}", w, h, words[i*frame_words:(i+1)*frame_words]) for i in range(count)]
        contact_sheet(filename.upper().replace("-", " "), frames, pal, args.out / f"{filename}.png")
        report.append({"name": filename, "symbol": symbol, "width": w, "height": h,
                       "frames": count, "words_per_frame": frame_words,
                       "bytes": len(words)*2, "palette_entries": len(pal),
                       "transparent_index0_policy": "rendered transparent in contact sheet"})
    (args.out / "static-assets.json").write_text(__import__("json").dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {len(report)} static asset sheets to {args.out}")


if __name__ == "__main__":
    main()

