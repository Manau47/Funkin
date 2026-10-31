#!/usr/bin/env python3
"""Generate only the pinned Week 4 chart/audio catalog and scene package.

Existing Week 1–3 generated assets are deliberately not touched by this tool.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from animate_preview import Rig  # noqa: E402
from convert_bopeebo_visuals import (  # noqa: E402
    blend_at, extract_crop, extract_sparrow_frame, fit_anchored_rig,
    median_palette, png_size, quantize, rgb555, run_ffmpeg,
)
from generate_ps1_song_catalog import (  # noqa: E402
    DIFFICULTIES, DIFFICULTY_EXT, RATE, collect_events, collect_notes,
    collect_tempos, decode, encode_four_channel_vagi, round_sample,
)

PAGE_W = PAGE_H = 256
PAGE_BYTES = PAGE_W * PAGE_H
SONGS = (
    ("satin-panties", "SATIN P", "SATIN.VAG", "SAT", "Mom", 110),
    ("high", "HIGH", "HIGH.VAG", "HIG", "Mom", 125),
    ("milf", "MILF", "MILF.VAG", "MIL", "Mom", 180),
)


def write_chart(path: pathlib.Path, chart: dict, metadata: dict,
                difficulty: str, audio_samples: int, song_id: str) -> int:
    notes = collect_notes(chart, difficulty)
    events = collect_events(chart, song_id)
    tempos = collect_tempos(chart, metadata)
    data = bytearray(struct.pack("<4sHHHHI", b"FNC1", len(notes), len(tempos),
                                 len(events), 0, audio_samples))
    for head, tail, lane in notes:
        data.extend(struct.pack("<IIB3x", head, tail, lane))
    for sample, beat_q16, bpm_centi in tempos:
        data.extend(struct.pack("<IIH2x", sample, beat_q16, bpm_centi))
    for sample, focus in events:
        data.extend(struct.pack("<Ib3x", sample, focus))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return len(notes)


def save_catalog_header(path: pathlib.Path, samples: dict[str, int]) -> None:
    lines = [
        "/* Generated from the pinned Week 4 chart JSON and official stems. */",
        "#ifndef PS1_WEEK4_CATALOG_H", "#define PS1_WEEK4_CATALOG_H",
        '#include "week1_catalog.h"',
        "#define PS1_BASE_SONG_COUNT 10u",
        "#undef PS1_SONG_COUNT", "#define PS1_WEEK4_SONG_COUNT 3u",
        "#define PS1_SONG_COUNT (PS1_BASE_SONG_COUNT + PS1_WEEK4_SONG_COUNT)",
        "#undef PS1_MAX_NOTE_COUNT",
        "#define PS1_MAX_NOTE_COUNT 674u /* MILF Hard in the pinned Week 4 chart */",
        "#define PS1_OPPONENT_MOM 5u",
        "static const Ps1Song ps1_week4_song_catalog[PS1_WEEK4_SONG_COUNT] = {",
    ]
    for song_id, label, audio_name, code, opponent, _bpm in SONGS:
        charts = ", ".join(f'"\\\\{code}{DIFFICULTY_EXT[d]}.BIN"' for d in DIFFICULTIES)
        lines.append(
            f'\t{{ "{label}", "\\\\{audio_name}", {samples[song_id]}u, '
            f'PS1_OPPONENT_MOM, 4u, {{ {charts} }} }},')
    lines.extend(["};", "#endif", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")


def _png_rgba(ffmpeg: str, source: pathlib.Path, width: int, height: int,
              filters: str) -> bytearray:
    return run_ffmpeg(ffmpeg, source, filters, width, height)


def make_scene(assets: pathlib.Path, ffmpeg: str, output: pathlib.Path,
              header: pathlib.Path) -> None:
    # Compose the official sunset, animated-limo source frame, and background
    # limousine into the two-page world used by the existing W2/W3 renderer.
    stage = _png_rgba(
        ffmpeg, assets / "week4/images/limo/limoSunset.png", 512, 256,
        "scale=512:256:force_original_aspect_ratio=increase:flags=area,"
        "crop=512:256:(iw-ow)/2:(ih-oh)/2,format=rgba")
    stage_size = (512, 256)

    def first_sparrow(xml_path: pathlib.Path, prefix: str) -> dict:
        root = ET.parse(xml_path).getroot()
        matches = [node for node in root.findall("SubTexture")
                   if node.attrib.get("name", "").startswith(prefix)]
        if not matches:
            raise ValueError(f"missing official Week 4 frame {prefix} in {xml_path}")
        node = matches[0]
        return {
            "x": int(node.attrib["x"]), "y": int(node.attrib["y"]),
            "width": int(node.attrib["width"]), "height": int(node.attrib["height"]),
            "frameX": int(node.attrib.get("frameX", 0)),
            "frameY": int(node.attrib.get("frameY", 0)),
            "frameWidth": int(node.attrib.get("frameWidth", node.attrib["width"])),
            "frameHeight": int(node.attrib.get("frameHeight", node.attrib["height"])),
            "rotated": node.attrib.get("rotated", "false").lower() == "true",
            "name": node.attrib.get("name", prefix),
        }

    bg_limo = extract_sparrow_frame(
        ffmpeg, assets / "week4/images/limo/bgLimo.png",
        first_sparrow(assets / "week4/images/limo/bgLimo.xml", "background limo pink"),
        (370, 64))
    limo = extract_sparrow_frame(
        ffmpeg, assets / "week4/images/limo/limoDrive.png",
        first_sparrow(assets / "week4/images/limo/limoDrive.xml", "Limo stage"),
        (341, 108))
    blend_at(stage, stage_size, bg_limo, (370, 64), (31, 80))
    blend_at(stage, stage_size, limo, (341, 108), (44, 88))

    mom_rig = Rig(assets / "shared/images/characters/momCar", ffmpeg)
    # Main timeline frame IDs follow the official Mom Car Animate atlas:
    # Up=0, Right=14, Down=23, Left=37, Idle=46.
    mom_source = {"idle": 46, "left": 37, "down": 23, "up": 0, "right": 14}
    mom_poses = fit_anchored_rig(mom_rig, list(mom_source.values()), 72, 84)
    gf_rig = Rig(assets / "shared/images/characters/gfCar", ffmpeg)
    gf_poses = fit_anchored_rig(gf_rig, [0, 15], 87, 79)
    icon = extract_crop(ffmpeg, assets / "preload/images/icons/icon-mom.png",
                        0, 0, 150, 150, (24, 24))

    images: list[tuple[str, bytearray, int, int]] = [
        ("stage0", stage[:PAGE_BYTES * 4], 256, 256),
        ("stage1", stage[PAGE_BYTES * 4:], 256, 256),
    ]
    frames: list[tuple[str, int, int, int, int, int]] = [
        ("STAGE_0", 0, 0, 0, 256, 256), ("STAGE_1", 1, 0, 0, 256, 256),
    ]
    char_page_rgba = bytearray(PAGE_BYTES * 4)
    # Integer-placed tight atlas; each rectangle is disjoint and page bounded.
    placements = {
        "MOM_IDLE": (0, 0, 72, 84, mom_poses[mom_source["idle"]]),
        "MOM_LEFT": (72, 0, 72, 84, mom_poses[mom_source["left"]]),
        "MOM_DOWN": (144, 0, 72, 84, mom_poses[mom_source["down"]]),
        "MOM_UP": (0, 84, 72, 84, mom_poses[mom_source["up"]]),
        "MOM_RIGHT": (72, 84, 72, 84, mom_poses[mom_source["right"]]),
        "GF_DANCE_0": (144, 84, 87, 79, gf_poses[0]),
        "GF_DANCE_1": (0, 168, 87, 79, gf_poses[15]),
        "MOM_ICON": (88, 168, 24, 24, icon),
    }
    for name, (x, y, w, h, pixels) in placements.items():
        blend_at(char_page_rgba, (256, 256), pixels, (w, h), (x, y))
        frames.append((name, 2, x, y, w, h))
    images.append(("characters", char_page_rgba, 256, 256))

    palette = median_palette([pixels for _, pixels, _, _ in images], 255)
    page_indices: list[bytearray] = []
    for _name, pixels, width, height in images:
        indexed = quantize(pixels, palette)
        page = bytearray(PAGE_BYTES)
        if width == 256 and height == 256:
            page[:] = indexed
        else:
            raise ValueError("Week 4 page dimensions must be complete 256x256 images")
        page_indices.append(page)
    words = [0] + [rgb555(c) for c in palette[:255]]
    words += [0] * (256 - len(words))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(page_indices) + struct.pack("<256H", *words))

    lines = [
        "/* Generated by generate_ps1_week4_assets.py; do not edit. */",
        "#ifndef PS1_WEEK4_VISUAL_DATA_H", "#define PS1_WEEK4_VISUAL_DATA_H",
        "#define BOPEEBO_WEEK4_PAGE_COUNT 3u",
        "#define BOPEEBO_WEEK4_STAGE_X (-64)", "#define BOPEEBO_WEEK4_STAGE_Y (0)",
        "#define BOPEEBO_WEEK4_CAMERA_ZOOM_Q8 524u",
        "#define BOPEEBO_WEEK4_CHARACTER_FRAME_W 72u",
        "#define BOPEEBO_WEEK4_CHARACTER_FRAME_H 84u",
        "#define BOPEEBO_WEEK4_MOM_X (55)", "#define BOPEEBO_WEEK4_MOM_Y (152)",
        "#define BOPEEBO_WEEK4_MOM_CAMERA_X (25)", "#define BOPEEBO_WEEK4_MOM_CAMERA_Y (0)",
        "#define BOPEEBO_WEEK4_BF_X (203)", "#define BOPEEBO_WEEK4_BF_Y (99)",
        "#define BOPEEBO_WEEK4_BF_CAMERA_X (-50)", "#define BOPEEBO_WEEK4_BF_CAMERA_Y (-17)",
        "#define BOPEEBO_WEEK4_GF_X (131)", "#define BOPEEBO_WEEK4_GF_Y (130)",
        "typedef struct { uint8_t page, u, v; uint16_t w, h; } Week4VisualFrame;",
        "enum {",
    ]
    for index, (name, *_rest) in enumerate(frames):
        lines.append(f"\tWEEK4_FRAME_{name} = {index},")
    lines.extend(["};", f"#define WEEK4_VISUAL_FRAME_COUNT {len(frames)}u",
                  "static const Week4VisualFrame week4_visual_frames[WEEK4_VISUAL_FRAME_COUNT] = {"])
    for name, page, x, y, w, h in frames:
        lines.append(f"\t{{ {page}u, {x}u, {y}u, {w}u, {h}u }}, /* {name} */")
    lines.extend(["};", "#endif", ""])
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text("\n".join(lines), encoding="ascii")
    print(f"Week 4 scene: {len(page_indices)} 8bpp pages + 256-word CLUT, {output.stat().st_size} bytes")
    print(f"Week 4 source frames: Mom idle/four directions from official Animate rig; GF idle poses; Mom icon; static official limo stage")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=pathlib.Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--header", type=pathlib.Path, required=True)
    parser.add_argument("--chart-dir", type=pathlib.Path, required=True)
    parser.add_argument("--scene", type=pathlib.Path, required=True)
    parser.add_argument("--visual-header", type=pathlib.Path, required=True)
    parser.add_argument("--reuse-audio", action="store_true",
                        help="reuse existing Week 4 VAG and decoded WAV outputs; regenerate charts/scene only")
    args = parser.parse_args()

    samples: dict[str, int] = {}
    chart_info: dict[str, tuple[dict, dict]] = {}
    decoded = args.output_dir / "decoded"
    for song_id, _label, audio_name, code, _opp, _bpm in SONGS:
        chart_root = args.assets / "preload/data/songs" / song_id
        chart = json.loads((chart_root / f"{song_id}-chart.json").read_text(encoding="utf-8"))
        metadata = json.loads((chart_root / f"{song_id}-metadata.json").read_text(encoding="utf-8"))
        chart_info[song_id] = (chart, metadata)
        stems = [args.assets / "songs" / song_id / filename for filename in
                 ("Inst.ogg", "Voices-bf.ogg", "Voices-mom.ogg")]
        if not all(path.is_file() for path in stems):
            raise FileNotFoundError(f"Missing official Week 4 audio stem: {song_id}")
        wavs = [decoded / song_id / f"{stem}.wav" for stem in ("inst", "player", "opponent")]
        if not args.reuse_audio:
            for source, target in zip(stems, wavs):
                decode(args.ffmpeg, source, target)
            samples[song_id] = encode_four_channel_vagi(
                wavs[0], wavs[1], wavs[2], args.output_dir / audio_name.lower(), song_id)
        else:
            if not all(path.is_file() for path in wavs):
                raise FileNotFoundError(f"Cannot reuse missing decoded audio for {song_id}")
            from convert_bopeebo_to_vagi import read_wav
            lengths = [read_wav(path, RATE)[1] for path in wavs]
            if len(set(lengths)) != 1:
                raise ValueError(f"reused decoded stems do not align for {song_id}: {lengths}")
            samples[song_id] = lengths[0]
            if not (args.output_dir / audio_name.lower()).is_file():
                raise FileNotFoundError(f"Cannot reuse missing VAGi for {song_id}")
        for difficulty in DIFFICULTIES:
            out = args.chart_dir / f"{code}{DIFFICULTY_EXT[difficulty]}.BIN"
            count = write_chart(out, chart, metadata, difficulty, samples[song_id], song_id)
            print(f"{song_id}/{difficulty}: {count} official chart notes, {out.stat().st_size} bytes")
    save_catalog_header(args.header, samples)
    make_scene(args.assets, args.ffmpeg, args.scene, args.visual_header)


if __name__ == "__main__":
    main()
