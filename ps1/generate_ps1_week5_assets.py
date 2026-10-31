#!/usr/bin/env python3
"""Generate only classic Week 5 charts, four-channel music, and a compact stage atlas."""
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
    blend_at, extract_sparrow_frame, fit_anchored_rig, median_palette,
    quantize, rgb555, run_ffmpeg,
)
from generate_ps1_song_catalog import (  # noqa: E402
    DIFFICULTIES, DIFFICULTY_EXT, RATE, collect_events, collect_notes,
    collect_tempos, decode, encode_four_channel_vagi,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE
SONGS = (
    ("cocoa", "COCOA", "COCOA.VAG", "COC", "Voices-parents-christmas.ogg", "parents", 100),
    ("eggnog", "EGGNOG", "EGGNOG.VAG", "EGG", "Voices-parents-christmas.ogg", "parents", 150),
    ("winter-horrorland", "WINTER H", "WINTER.VAG", "WIN", "Voices-monster.ogg", "monster", 159),
)


def write_chart(path: pathlib.Path, chart: dict, metadata: dict,
                difficulty: str, samples: int, song_id: str) -> int:
    notes = collect_notes(chart, difficulty)
    tempos = collect_tempos(chart, metadata)
    events = collect_events(chart, song_id)
    packed = bytearray(struct.pack("<4sHHHHI", b"FNC1", len(notes), len(tempos),
                                   len(events), 0, samples))
    for head, tail, lane in notes:
        packed.extend(struct.pack("<IIB3x", head, tail, lane))
    for sample, beat, bpm in tempos:
        packed.extend(struct.pack("<IIH2x", sample, beat, bpm))
    for sample, focus in events:
        packed.extend(struct.pack("<Ib3x", sample, focus))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(packed)
    return len(notes)


def save_catalog(path: pathlib.Path, samples: dict[str, int], max_notes: int) -> None:
    lines = [
        "/* Generated from the pinned classic Week 5 charts and stems. */",
        "#ifndef PS1_WEEK5_CATALOG_H", "#define PS1_WEEK5_CATALOG_H",
        '#include "week4_catalog.h"',
        "#define PS1_WEEK4_TOTAL_SONG_COUNT (PS1_BASE_SONG_COUNT + PS1_WEEK4_SONG_COUNT)",
        "#undef PS1_SONG_COUNT", "#define PS1_WEEK5_SONG_COUNT 3u",
        "#define PS1_SONG_COUNT (PS1_WEEK4_TOTAL_SONG_COUNT + PS1_WEEK5_SONG_COUNT)",
        "#undef PS1_MAX_NOTE_COUNT", f"#define PS1_MAX_NOTE_COUNT {max(674, max_notes)}u",
        "#define PS1_OPPONENT_PARENTS 6u",
        "static const Ps1Song ps1_week5_song_catalog[PS1_WEEK5_SONG_COUNT] = {",
    ]
    for song_id, label, audio_name, code, _voice, opponent, _bpm in SONGS:
        opponent_kind = "PS1_OPPONENT_PARENTS" if opponent == "parents" else "PS1_OPPONENT_MONSTER"
        chart_paths = ", ".join(f'"\\\\{code}{DIFFICULTY_EXT[d]}.BIN"' for d in DIFFICULTIES)
        lines.append(f'\t{{ "{label}", "\\\\{audio_name}", {samples[song_id]}u, {opponent_kind}, 5u, {{ {chart_paths} }} }},')
    lines.extend(["};", "#endif", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")


def make_scene(assets: pathlib.Path, ffmpeg: str, output: pathlib.Path,
               header: pathlib.Path) -> None:
    christmas = assets / "week5/images/christmas"
    page_pixels: list[bytearray] = []
    frame_defs: list[tuple[str, int, int, int, int, int]] = []

    # Stage backdrops are cropped to 4:3, with official decorative layer art
    # retained at 320x240 composition scale. Character proportions are handled
    # independently in the animated atlas.
    for page_index, background, tree, snow in (
        (0, "bgWalls.png", "christmasTree.png", "fgSnow.png"),
        (1, "evilBG.png", "evilTree.png", "evilSnow.png"),
    ):
        page = bytearray(PAGE_BYTES * 4)
        bg_path = christmas / background
        bg = run_ffmpeg(ffmpeg, bg_path,
            "scale=256:192:force_original_aspect_ratio=increase:flags=area,"
            "crop=256:192:(iw-ow)/2:(ih-oh)/2,format=rgba", 256, 192)
        blend_at(page, (256, 256), bg, (256, 192), (0, 32))
        if page_index == 0:
            escalator = run_ffmpeg(ffmpeg, christmas / "bgEscalator.png",
                "scale=190:100:force_original_aspect_ratio=decrease:flags=area,"
                "pad=190:100:(ow-iw)/2:(oh-ih)/2:color=black@0,format=rgba", 190, 100)
            blend_at(page, (256, 256), escalator, (190, 100), (32, 54))
        tree_path = christmas / tree
        tree_pixels = run_ffmpeg(ffmpeg, tree_path,
            "scale=52:112:force_original_aspect_ratio=decrease:flags=area,"
            "pad=52:112:(ow-iw)/2:(oh-ih)/2:color=black@0,format=rgba", 52, 112)
        blend_at(page, (256, 256), tree_pixels, (52, 112), (193, 42))
        if page_index == 0:
            santa_xml = ET.parse(christmas / "santa.xml").getroot()
            node = next(item for item in santa_xml.findall("SubTexture")
                        if item.attrib.get("name", "").startswith("santa idle in fear"))
            santa_frame = {key: int(node.attrib.get(key, 0)) for key in
                ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
            santa_frame["rotated"] = node.attrib.get("rotated", "false").lower() == "true"
            santa = extract_sparrow_frame(ffmpeg, christmas / "santa.png", santa_frame, (42, 50))
            blend_at(page, (256, 256), santa, (42, 50), (12, 137))
        snow_path = christmas / snow
        snow_pixels = run_ffmpeg(ffmpeg, snow_path,
            "scale=256:30:force_original_aspect_ratio=increase:flags=area,"
            "crop=256:30:(iw-ow)/2:(ih-oh)/2,format=rgba", 256, 30)
        blend_at(page, (256, 256), snow_pixels, (256, 30), (0, 194))
        page_pixels.append(page)
        frame_defs.append(("STAGE_XMAS" if page_index == 0 else "STAGE_EVIL",
                           page_index, 0, 0, 256, 256))

    parents = Rig(assets / "shared/images/characters/parents-christmas", ffmpeg)
    monster = Rig(assets / "shared/images/characters/monster", ffmpeg)
    gf = Rig(assets / "shared/images/characters/gf-christmas", ffmpeg)
    parent_frames = {
        "PARENTS_IDLE": 112,
        "PARENTS_MOM_DOWN": 0, "PARENTS_MOM_UP": 28,
        "PARENTS_MOM_RIGHT": 54, "PARENTS_MOM_LEFT": 83,
        "PARENTS_DAD_DOWN": 14, "PARENTS_DAD_UP": 41,
        "PARENTS_DAD_RIGHT": 68, "PARENTS_DAD_LEFT": 97,
    }
    monster_frames = {"MONSTER_IDLE": 0, "MONSTER_RIGHT": 16, "MONSTER_LEFT": 26,
                      "MONSTER_UP": 36, "MONSTER_DOWN": 48}
    fitted_parents = fit_anchored_rig(parents, list(parent_frames.values()), 64, 64)
    fitted_monster = fit_anchored_rig(monster, list(monster_frames.values()), 64, 64)
    fitted_gf = fit_anchored_rig(gf, [0, 14], 64, 64)
    character_page = bytearray(PAGE_BYTES * 4)
    for index, (name, frame) in enumerate(parent_frames.items()):
        x, y = (index % 4) * 64, (index // 4) * 64
        blend_at(character_page, (256, 256), fitted_parents[frame], (64, 64), (x, y))
        frame_defs.append((name, 2, x, y, 64, 64))
    for name, frame in monster_frames.items():
        index = 9 + list(monster_frames).index(name)
        x, y = (index % 4) * 64, (index // 4) * 64
        blend_at(character_page, (256, 256), fitted_monster[frame], (64, 64), (x, y))
        frame_defs.append((name, 2, x, y, 64, 64))
    for index, frame in enumerate((0, 14)):
        x, y = (14 + index) * 64 % 256, ((14 + index) // 4) * 64
        blend_at(character_page, (256, 256), fitted_gf[frame], (64, 64), (x, y))
        frame_defs.append((f"GF_DANCE_{index}", 2, x, y, 64, 64))
    page_pixels.append(character_page)

    palette = median_palette(page_pixels, 255)
    indexed = []
    for page in page_pixels:
        result = quantize(page, palette)
        if len(result) != PAGE_BYTES:
            raise ValueError("Week 5 atlas page did not quantize to 256x256")
        indexed.append(result)
    words = [0] + [rgb555(color) for color in palette[:255]]
    words += [0] * (256 - len(words))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(indexed) + struct.pack("<256H", *words))

    lines = ["/* Generated from pinned classic Week 5 assets. */",
             "#ifndef PS1_WEEK5_VISUAL_DATA_H", "#define PS1_WEEK5_VISUAL_DATA_H",
             "#define BOPEEBO_WEEK5_PAGE_COUNT 3u",
             "#define BOPEEBO_WEEK5_CAMERA_ZOOM_Q8 460u",
             "#define BOPEEBO_WEEK5_BF_X 203", "#define BOPEEBO_WEEK5_BF_Y 163",
             "#define BOPEEBO_WEEK5_GF_X 131", "#define BOPEEBO_WEEK5_GF_Y 151",
             "#define BOPEEBO_WEEK5_OPP_X 57", "#define BOPEEBO_WEEK5_OPP_Y 153",
             "typedef struct { uint8_t page, u, v; uint16_t w, h; } Week5VisualFrame;",
             "enum {"]
    for index, (name, *_rest) in enumerate(frame_defs):
        lines.append(f"\tWEEK5_FRAME_{name} = {index},")
    lines.extend(["};", f"#define WEEK5_VISUAL_FRAME_COUNT {len(frame_defs)}u",
                  "static const Week5VisualFrame week5_visual_frames[WEEK5_VISUAL_FRAME_COUNT] = {"])
    for name, page, x, y, w, h in frame_defs:
        lines.append(f"\t{{ {page}u, {x}u, {y}u, {w}u, {h}u }}, /* {name} */")
    lines.extend(["};", "#endif", ""])
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text("\n".join(lines), encoding="ascii")
    print(f"Week 5 static Christmas mall + character atlas: {len(page_pixels)} 8bpp pages, {output.stat().st_size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=pathlib.Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--header", type=pathlib.Path, required=True)
    parser.add_argument("--chart-dir", type=pathlib.Path, required=True)
    parser.add_argument("--scene", type=pathlib.Path, required=True)
    parser.add_argument("--visual-header", type=pathlib.Path, required=True)
    parser.add_argument("--reuse-audio", action="store_true")
    args = parser.parse_args()
    samples: dict[str, int] = {}
    chart_inputs: dict[str, tuple[dict, dict]] = {}
    max_notes = 0
    decoded = args.output_dir / "decoded"
    for song_id, _label, audio_name, code, opponent_stem, _opponent, _bpm in SONGS:
        root = args.assets / "preload/data/songs" / song_id
        chart = json.loads((root / f"{song_id}-chart.json").read_text(encoding="utf-8"))
        metadata = json.loads((root / f"{song_id}-metadata.json").read_text(encoding="utf-8"))
        chart_inputs[song_id] = (chart, metadata)
        stems = [args.assets / "songs" / song_id / name for name in
                 ("Inst.ogg", "Voices-bf.ogg", opponent_stem)]
        if not all(path.is_file() for path in stems):
            raise FileNotFoundError(f"Missing official Week 5 classic stem for {song_id}")
        wavs = [decoded / song_id / f"{name}.wav" for name in ("inst", "bf", "opponent")]
        output_audio = args.output_dir / audio_name.lower()
        if args.reuse_audio:
            if not output_audio.is_file() or not all(path.is_file() for path in wavs):
                raise FileNotFoundError(f"Missing reusable Week 5 audio or decoded WAV for {song_id}")
            from convert_bopeebo_to_vagi import read_wav
            lengths = [read_wav(path, RATE)[1] for path in wavs]
            samples[song_id] = max(lengths)
        else:
            for source, target in zip(stems, wavs):
                decode(args.ffmpeg, source, target)
            samples[song_id] = encode_four_channel_vagi(wavs[0], wavs[1], wavs[2], output_audio, song_id)
        for difficulty in DIFFICULTIES:
            chart_path = args.chart_dir / f"{code}{DIFFICULTY_EXT[difficulty]}.BIN"
            count = write_chart(chart_path, chart, metadata, difficulty, samples[song_id], song_id)
            max_notes = max(max_notes, count)
            print(f"{song_id}/{difficulty}: {count} notes, {chart_path.stat().st_size} bytes")
    save_catalog(args.header, samples, max_notes)
    make_scene(args.assets, args.ffmpeg, args.scene, args.visual_header)


if __name__ == "__main__":
    main()
