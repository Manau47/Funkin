#!/usr/bin/env python3
"""Convert classic Week 7 charts, four-channel music, and a compact battlefield scene."""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from animate_preview import Rig  # noqa: E402
from convert_bopeebo_visuals import (  # noqa: E402
    blend_at, extract_sparrow_frame, fit_anchored_rig, median_palette, png_size,
    quantize, rgb555, run_ffmpeg,
)
from generate_ps1_song_catalog import (  # noqa: E402
    DIFFICULTIES, DIFFICULTY_EXT, RATE, collect_events, collect_notes,
    collect_tempos, decode, encode_four_channel_vagi, read_wav,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE
SONGS = (
    ("ugh", "UGH", "UGH.VAG", "UGH", "Ugh", "Voices-bf.ogg", "Voices-tankman.ogg"),
    ("guns", "GUNS", "GUNS.VAG", "GUN", "Guns", "Voices-bf.ogg", "Voices-tankman.ogg"),
    ("stress", "STRESS", "STRESS.VAG", "STR", "Stress", "Voices-bf.ogg", "Voices-tankman.ogg"),
)


def write_chart(path: pathlib.Path, chart: dict, metadata: dict,
                difficulty: str, samples: int, song_id: str) -> int:
    notes = collect_notes(chart, difficulty)
    tempos = collect_tempos(chart, metadata)
    events = collect_events(chart, song_id)
    data = bytearray(struct.pack("<4sHHHHI", b"FNC1", len(notes), len(tempos),
                                 len(events), 0, samples))
    for head, tail, lane in notes:
        data.extend(struct.pack("<IIB3x", head, tail, lane))
    for sample, beat, bpm in tempos:
        data.extend(struct.pack("<IIH2x", sample, beat, bpm))
    for sample, focus in events:
        data.extend(struct.pack("<Ib3x", sample, focus))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return len(notes)


def save_catalog(path: pathlib.Path, samples: dict[str, int], max_notes: int) -> None:
    lines = [
        "/* Generated from the pinned classic Week 7 charts and stems. */",
        "#ifndef PS1_WEEK7_CATALOG_H", "#define PS1_WEEK7_CATALOG_H",
        '#include "week6_catalog.h"',
        "#define PS1_WEEK6_TOTAL_SONG_COUNT (PS1_WEEK5_TOTAL_SONG_COUNT + PS1_WEEK6_SONG_COUNT)",
        "#undef PS1_SONG_COUNT", "#define PS1_WEEK7_SONG_COUNT 3u",
        "#define PS1_SONG_COUNT (PS1_WEEK6_TOTAL_SONG_COUNT + PS1_WEEK7_SONG_COUNT)",
        "#define PS1_OPPONENT_TANKMAN 10u",
        "#undef PS1_MAX_NOTE_COUNT", f"#define PS1_MAX_NOTE_COUNT {max(674, max_notes)}u",
        "static const Ps1Song ps1_week7_song_catalog[PS1_WEEK7_SONG_COUNT] = {",
    ]
    for song_id, label, audio_name, code, _title, _bf, _tankman in SONGS:
        charts = ", ".join(f'"\\\\{code}{DIFFICULTY_EXT[d]}.BIN"' for d in DIFFICULTIES)
        lines.append(f'\t{{ "{label}", "\\\\{audio_name}", {samples[song_id]}u, PS1_OPPONENT_TANKMAN, 7u, {{ {charts} }} }},')
    lines.extend(["};", "#endif", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")


def stage_layer(ffmpeg: str, source: pathlib.Path, width: int, height: int) -> bytearray:
    filters = (f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=area,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x00000000,format=rgba")
    return run_ffmpeg(ffmpeg, source, filters, width, height)


def make_stage(assets: pathlib.Path, ffmpeg: str) -> bytearray:
    root = assets / "week7/images"
    canvas = bytearray(512 * 256 * 4)
    # Battlefield layers are composed once at 2x the game viewport. The game
    # scrolls/crops this static PS1 scene; no full-resolution art is resident.
    sky = stage_layer(ffmpeg, root / "tankSky.png", 512, 256)
    blend_at(canvas, (512, 256), sky, (512, 256), (0, 0))
    for filename, dims, offset in (
        ("mountains2.png", (512, 104), (0, 22)),
        ("tankBuildings.png", (512, 106), (0, 68)),
        ("cityruins2.png", (512, 112), (0, 82)),
        ("tankGround.png", (512, 132), (0, 122)),
        ("bricksGround.png", (512, 78), (0, 178)),
    ):
        layer = stage_layer(ffmpeg, root / filename, *dims)
        blend_at(canvas, (512, 256), layer, dims, offset)
    return canvas


def make_scene(assets: pathlib.Path, ffmpeg: str,
               output: pathlib.Path, header: pathlib.Path) -> None:
    # Two adjacent 256x256 pages cover the wide, precomposed battlefield.
    stage = make_stage(assets, ffmpeg)
    stage_pages = [bytearray(PAGE_BYTES * 4), bytearray(PAGE_BYTES * 4)]
    for page_index in range(2):
        for y in range(256):
            src = (y * 512 + page_index * 256) * 4
            dst = y * 256 * 4
            stage_pages[page_index][dst:dst + 256 * 4] = stage[src:src + 256 * 4]

    tankman = Rig(assets / "shared/images/characters/tankman/basic", ffmpeg)
    bf = Rig(assets / "shared/images/characters/bf", ffmpeg)
    tank_frames = {"TANK_IDLE": 0, "TANK_LEFT": 25, "TANK_DOWN": 30,
                   "TANK_UP": 20, "TANK_RIGHT": 14}
    bf_frames = {"BF_IDLE": 0, "BF_LEFT": 14, "BF_DOWN": 140,
                 "BF_UP": 109, "BF_RIGHT": 56}
    tank_fit = fit_anchored_rig(tankman, list(tank_frames.values()), 64, 64)
    bf_fit = fit_anchored_rig(bf, list(bf_frames.values()), 64, 64)
    gf_atlas = assets / "shared/images/characters/gfTankmen"
    gf_xml = ET.parse(gf_atlas.with_suffix(".xml")).getroot()
    gf_nodes = {int(node.attrib["name"][-4:]): node for node in gf_xml.findall("SubTexture")
                if node.attrib.get("name", "").startswith("GF Dancing at Gunpoint")}
    gf_frames = {"GF_DANCE_0": 0, "GF_DANCE_1": 15}
    gf_fit = {}
    for frame_index in gf_frames.values():
        node = gf_nodes[frame_index]
        frame = {key: int(node.attrib.get(key, 0)) for key in
                 ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
        frame["rotated"] = node.attrib.get("rotated", "false").lower() == "true"
        frame["name"] = node.attrib["name"]
        gf_fit[frame_index] = extract_sparrow_frame(ffmpeg, gf_atlas.with_suffix(".png"), frame, (64, 64))

    # One 8bpp page holds all three actors and leaves room for two portraits.
    character_page = bytearray(PAGE_BYTES * 4)
    frames: list[tuple[str, int, int, int, int, int]] = [
        ("STAGE_LEFT", 0, 0, 0, 256, 256), ("STAGE_RIGHT", 1, 0, 0, 256, 256)
    ]
    character_specs: list[tuple[str, bytearray]] = []
    character_specs.extend((name, tank_fit[frame]) for name, frame in tank_frames.items())
    character_specs.extend((name, bf_fit[frame]) for name, frame in bf_frames.items())
    character_specs.extend((name, gf_fit[frame]) for name, frame in gf_frames.items())
    for filename, label in (("icon-tankman.png", "ICON_TANKMAN"),
                            ("icon-bf.png", "ICON_BF")):
        source = assets / "preload/images/icons" / filename
        width, height = png_size(source)
        crop_width = width // 2 if width >= height * 2 else width
        pixels = run_ffmpeg(ffmpeg, source,
            f"crop={crop_width}:{height}:0:0,scale=64:64:force_original_aspect_ratio=decrease:flags=neighbor,"
            "pad=64:64:(ow-iw)/2:(oh-ih)/2:color=0x00000000,format=rgba", 64, 64)
        character_specs.append((label, pixels))
    for index, (name, pixels) in enumerate(character_specs):
        if len(pixels) != 64 * 64 * 4:
            raise ValueError(f"Week 7 frame {name} is not 64x64 RGBA")
        x, y = (index % 4) * 64, (index // 4) * 64
        blend_at(character_page, (256, 256), pixels, (64, 64), (x, y))
        frames.append((name, 2, x, y, 64, 64))

    rgba_pages = stage_pages + [character_page]
    palette = median_palette(rgba_pages, 255)
    indexed_pages = [quantize(page, palette) for page in rgba_pages]
    if len(indexed_pages) != 3 or any(len(page) != PAGE_BYTES for page in indexed_pages):
        raise ValueError("Week 7 payload must contain exactly three 8bpp pages")
    clut = [0] + [rgb555(color) for color in palette[:255]]
    clut += [0] * (256 - len(clut))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(indexed_pages) + struct.pack("<256H", *clut))

    lines = ["/* Generated from pinned classic Week 7 assets. */",
             "#ifndef PS1_WEEK7_VISUAL_DATA_H", "#define PS1_WEEK7_VISUAL_DATA_H",
             "#define BOPEEBO_WEEK7_PAGE_COUNT 3u",
             "typedef struct { uint8_t page, u, v; uint16_t w, h; } Week7VisualFrame;", "enum {"]
    for index, (name, *_rest) in enumerate(frames):
        lines.append(f"\tWEEK7_FRAME_{name} = {index},")
    lines.extend(["};", f"#define WEEK7_VISUAL_FRAME_COUNT {len(frames)}u",
                  "static const Week7VisualFrame week7_visual_frames[WEEK7_VISUAL_FRAME_COUNT] = {"])
    for name, page, x, y, width, height in frames:
        lines.append(f"\t{{ {page}u, {x}u, {y}u, {width}u, {height}u }}, /* {name} */")
    lines.extend(["};", "#endif", ""])
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text("\n".join(lines), encoding="ascii")
    print(f"Week 7 scene: {len(indexed_pages)} 8bpp pages, {output.stat().st_size} bytes; {len(character_specs)} character frames")


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
                        help="reuse existing decoded PCM and VAGi outputs; regenerate charts and visuals")
    args = parser.parse_args()
    samples: dict[str, int] = {}
    max_notes = 0
    decoded = args.output_dir / "decoded"
    for song_id, _label, audio_name, code, _title, player_name, opponent_name in SONGS:
        root = args.assets / "preload/data/songs" / song_id
        chart = json.loads((root / f"{song_id}-chart.json").read_text(encoding="utf-8"))
        metadata = json.loads((root / f"{song_id}-metadata.json").read_text(encoding="utf-8"))
        stems = [args.assets / "songs" / song_id / name for name in
                 ("Inst.ogg", player_name, opponent_name)]
        if not all(path.is_file() for path in stems):
            raise FileNotFoundError(f"Missing official classic Week 7 stem for {song_id}")
        wavs = [decoded / song_id / f"{name}.wav" for name in ("inst", "bf", "tankman")]
        vagi = args.output_dir / audio_name.lower()
        if args.reuse_audio:
            if not vagi.is_file() or not all(path.is_file() for path in wavs):
                raise FileNotFoundError(f"--reuse-audio requires VAGi and decoded PCM for {song_id}")
            samples[song_id] = max(read_wav(path, RATE)[1] for path in wavs)
        else:
            for source, target in zip(stems, wavs):
                decode(args.ffmpeg, source, target)
            samples[song_id] = encode_four_channel_vagi(wavs[0], wavs[1], wavs[2], vagi, song_id)
        for difficulty in DIFFICULTIES:
            out = args.chart_dir / f"{code}{DIFFICULTY_EXT[difficulty]}.BIN"
            count = write_chart(out, chart, metadata, difficulty, samples[song_id], song_id)
            max_notes = max(max_notes, count)
            print(f"{song_id}/{difficulty}: {count} notes, {out.stat().st_size} bytes")
    save_catalog(args.header, samples, max_notes)
    make_scene(args.assets, args.ffmpeg, args.scene, args.visual_header)


if __name__ == "__main__":
    main()
