#!/usr/bin/env python3
"""Convert classic WeekEnd 1 charts, four-channel audio, and compact scenes."""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys
import wave

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from animate_preview import Rig  # noqa: E402
from convert_bopeebo_visuals import (  # noqa: E402
    blend_at, fit_anchored_rig, median_palette, png_size, quantize, rgb555, run_ffmpeg,
)
from generate_ps1_song_catalog import (  # noqa: E402
    DIFFICULTIES, DIFFICULTY_EXT, RATE, collect_events, collect_notes,
    collect_tempos, decode, encode_four_channel_vagi, read_wav,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE
SONGS = (
    ("darnell", "DARNELL", "DARNELL.VAG", "DNL", "Voices-pico.ogg", "Voices-darnell.ogg", 8),
    ("lit-up", "LIT UP", "LITUP.VAG", "LIT", "Voices-pico.ogg", "Voices-darnell.ogg", 8),
    ("2hot", "2HOT", "2HOT.VAG", "2HT", "Voices-pico.ogg", "Voices-darnell.ogg", 8),
    ("blazin", "BLAZIN", "BLAZIN.VAG", "BLZ", None, None, 9),
)


def chart_file(path: pathlib.Path, chart: dict, metadata: dict, difficulty: str,
               samples: int, song_id: str) -> int:
    notes = collect_notes(chart, difficulty)
    tempos = collect_tempos(chart, metadata)
    events = collect_events(chart, song_id)
    data = bytearray(struct.pack("<4sHHHHI", b"FNC1", len(notes), len(tempos), len(events), 0, samples))
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
        "/* Generated from the pinned classic WeekEnd 1 chart JSON and stems. */",
        "#ifndef PS1_WEEKEND1_CATALOG_H", "#define PS1_WEEKEND1_CATALOG_H",
        '#include "week7_catalog.h"',
        "#define PS1_WEEK7_TOTAL_SONG_COUNT (PS1_WEEK6_TOTAL_SONG_COUNT + PS1_WEEK7_SONG_COUNT)",
        "#undef PS1_SONG_COUNT", "#define PS1_WEEKEND1_SONG_COUNT 4u",
        "#define PS1_SONG_COUNT (PS1_WEEK7_TOTAL_SONG_COUNT + PS1_WEEKEND1_SONG_COUNT)",
        "#define PS1_OPPONENT_DARNELL 11u",
        "#undef PS1_MAX_NOTE_COUNT", f"#define PS1_MAX_NOTE_COUNT {max(1035, max_notes)}u",
        "static const Ps1Song ps1_weekend1_song_catalog[PS1_WEEKEND1_SONG_COUNT] = {",
    ]
    for song_id, label, audio_name, code, _player, _opponent, stage in SONGS:
        charts = ", ".join(f'"\\\\{code}{DIFFICULTY_EXT[d]}..BIN"' for d in DIFFICULTIES)
        charts = charts.replace("..BIN", ".BIN")
        lines.append(f'\t{{ "{label}", "\\\\{audio_name}", {samples[song_id]}u, PS1_OPPONENT_DARNELL, {stage}u, {{ {charts} }} }},')
    lines.extend(["};", "#endif", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")


def rgba_layer(ffmpeg: str, source: pathlib.Path, filters: str, width: int, height: int) -> bytearray:
    if not source.is_file():
        raise FileNotFoundError(source)
    return run_ffmpeg(ffmpeg, source, filters + ",format=rgba", width, height)


def make_street_stage(assets: pathlib.Path, ffmpeg: str) -> bytearray:
    root = assets / "weekend1/images/phillyStreets"
    canvas = bytearray(512 * 256 * 4)
    layers = (
        ("phillySkybox.png", "scale=512:256:force_original_aspect_ratio=increase:flags=area,crop=512:256:(iw-ow)/2:(ih-oh)/2", 0, 0, 512, 256),
        ("phillySkyline.png", "scale=512:88:force_original_aspect_ratio=increase:flags=area,crop=512:88:(iw-ow)/2:(ih-oh)/2", 0, 35, 512, 88),
        ("phillyHighway.png", "scale=512:100:force_original_aspect_ratio=decrease:flags=area,pad=512:100:(ow-iw)/2:(oh-ih)/2:color=black@0", 0, 91, 512, 100),
        ("phillyForegroundCity.png", "scale=512:100:force_original_aspect_ratio=decrease:flags=area,pad=512:100:(ow-iw)/2:(oh-ih)/2:color=black@0", 0, 91, 512, 100),
        ("phillyConstruction.png", "scale=300:100:force_original_aspect_ratio=decrease:flags=area,pad=300:100:(ow-iw)/2:(oh-ih)/2:color=black@0", 106, 124, 300, 100),
        ("phillyForeground.png", "scale=512:134:force_original_aspect_ratio=decrease:flags=area,pad=512:134:(ow-iw)/2:(oh-ih)/2:color=black@0", 0, 122, 512, 134),
    )
    for name, filt, x, y, width, height in layers:
        rgba = rgba_layer(ffmpeg, root / name, filt, width, height)
        blend_at(canvas, (512, 256), rgba, (width, height), (x, y))
    nene = Rig(assets / "shared/images/characters/nene", ffmpeg)
    nene_pose = fit_anchored_rig(nene, [0], 64, 64)[0]
    blend_at(canvas, (512, 256), nene_pose, (64, 64), (259, 57))
    return canvas


def make_blazin_stage(assets: pathlib.Path, ffmpeg: str) -> bytearray:
    root = assets / "weekend1/images/phillyBlazin"
    canvas = bytearray(512 * 256 * 4)
    for name, y, height in (("skyBlur.png", 0, 200), ("streetBlur.png", 96, 160)):
        rgba = rgba_layer(ffmpeg, root / name,
            f"scale=512:{height}:force_original_aspect_ratio=increase:flags=area,crop=512:{height}:(iw-ow)/2:(ih-oh)/2",
            512, height)
        blend_at(canvas, (512, 256), rgba, (512, height), (0, y))
    return canvas


def icon_frame(ffmpeg: str, path: pathlib.Path) -> bytearray:
    width, height = png_size(path)
    w = width // 2 if width >= height * 2 else width
    return run_ffmpeg(ffmpeg, path,
        f"crop={w}:{height}:0:0,scale=64:64:force_original_aspect_ratio=decrease:flags=neighbor,pad=64:64:(ow-iw)/2:(oh-ih)/2:color=black@0,format=rgba", 64, 64)


def make_scene(assets: pathlib.Path, ffmpeg: str, output: pathlib.Path, header: pathlib.Path) -> None:
    # Four pages hold two wide static backdrops; then actor, fighter and icon
    # atlases are separate pages so their UVs remain compact and non-overlapping.
    rgba_pages: list[bytearray] = []
    frames: list[tuple[str, int, int, int, int, int]] = []
    for label, stage in (("STREET", make_street_stage(assets, ffmpeg)),
                         ("BLAZIN", make_blazin_stage(assets, ffmpeg))):
        for half in range(2):
            page = bytearray(PAGE_BYTES * 4)
            for y in range(PAGE):
                src = (y * 512 + half * PAGE) * 4
                dst = y * PAGE * 4
                page[dst:dst + PAGE * 4] = stage[src:src + PAGE * 4]
            rgba_pages.append(page)
            frames.append((f"STAGE_{label}_{half}", len(rgba_pages) - 1, 0, 0, 256, 256))

    common = bytearray(PAGE_BYTES * 4)
    pico = Rig(assets / "shared/images/characters/pico/basic-animations", ffmpeg)
    darnell = Rig(assets / "shared/images/characters/darnell", ffmpeg)
    # Frame indices are the pinned Animate timelines: Pico Idle/Left/Right/Up/Down;
    # Darnell Idle/Left/Down/Right/Up. These source rigs are 2D composites.
    pico_ids = {"PICO_IDLE": 0, "PICO_LEFT": 14, "PICO_RIGHT": 31, "PICO_UP": 48, "PICO_DOWN": 62}
    darnell_ids = {"DARNELL_IDLE": 0, "DARNELL_LEFT": 14, "DARNELL_DOWN": 26,
                   "DARNELL_RIGHT": 38, "DARNELL_UP": 50}
    common_specs: list[tuple[str, bytearray]] = []
    for rig, mapping, size in ((pico, pico_ids, (64, 80)), (darnell, darnell_ids, (64, 80))):
        fitted = fit_anchored_rig(rig, list(mapping.values()), *size)
        common_specs.extend((name, fitted[index]) for name, index in mapping.items())
    for index, (name, pixels) in enumerate(common_specs):
        cell_w, cell_h = 64, 80
        x, y = (index % 4) * 64, (index // 4) * 80
        blend_at(common, (256, 256), pixels, (cell_w, cell_h), (x, y))
        frames.append((name, 4, x, y, cell_w, cell_h))
    rgba_pages.append(common)

    for page_index, (folder, char, frame_map) in enumerate((
        ("picoBlazin", "PICO", {"IDLE": 0, "BLOCK": 14, "DODGE": 19, "PUNCH_HIGH": 24,
            "PUNCH_LOW": 36, "HIT_LOW": 40, "HIT_HIGH": 44, "UPPERCUT": 48}),
        ("darnellBlazin", "DARNELL", {"IDLE": 0, "UPPERCUT_PREP": 14, "UPPERCUT": 19,
            "FAKE_HIT": 24, "BLOCK": 29, "PUNCH_HIGH": 33, "PUNCH_LOW": 48, "DODGE": 53}),
    )):
        rig = Rig(assets / "shared/images/characters" / folder, ffmpeg)
        fitted = fit_anchored_rig(rig, list(frame_map.values()), 64, 96)
        page = bytearray(PAGE_BYTES * 4)
        for index, (suffix, source_index) in enumerate(frame_map.items()):
            x, y = (index % 4) * 64, (index // 4) * 96
            blend_at(page, (256, 256), fitted[source_index], (64, 96), (x, y))
            frames.append((f"{char}_BLAZIN_{suffix}", 5 + page_index, x, y, 64, 96))
        rgba_pages.append(page)

    icons = bytearray(PAGE_BYTES * 4)
    for i, (label, filename) in enumerate((("ICON_PICO", "icon-pico.png"),
                                            ("ICON_DARNELL", "icon-darnell.png"))):
        pixels = icon_frame(ffmpeg, assets / "preload/images/icons" / filename)
        x = i * 64
        blend_at(icons, (256, 256), pixels, (64, 64), (x, 0))
        frames.append((label, 7, x, 0, 64, 64))
    rgba_pages.append(icons)

    palette = median_palette(rgba_pages, 255)
    indices = [quantize(page, palette) for page in rgba_pages]
    if len(indices) != 8 or any(len(page) != PAGE_BYTES for page in indices):
        raise ValueError("WeekEnd 1 scene package must contain eight 8bpp pages")
    clut = [0] + [rgb555(color) for color in palette[:255]]
    clut += [0] * (256 - len(clut))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(indices) + struct.pack("<256H", *clut))
    lines = ["/* Generated from pinned classic WeekEnd 1 assets. */",
             "#ifndef PS1_WEEKEND1_VISUAL_DATA_H", "#define PS1_WEEKEND1_VISUAL_DATA_H",
             "#define BOPEEBO_WEEKEND1_PAGE_COUNT 8u",
             "typedef struct { uint8_t page, u, v; uint16_t w, h; } WeekEnd1VisualFrame;", "enum {"]
    for i, (name, *_rest) in enumerate(frames): lines.append(f"\tWEND_FRAME_{name} = {i},")
    lines.extend(["};", f"#define WEEKEND1_VISUAL_FRAME_COUNT {len(frames)}u",
                  "static const WeekEnd1VisualFrame weekend1_visual_frames[WEEKEND1_VISUAL_FRAME_COUNT] = {"])
    for name, page, x, y, w, h in frames:
        lines.append(f"\t{{ {page}u, {x}u, {y}u, {w}u, {h}u }}, /* {name} */")
    lines.extend(["};", "#endif", ""])
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text("\n".join(lines), encoding="ascii")
    print(f"WeekEnd 1 scene: {len(indices)} pages, {output.stat().st_size} bytes, {len(frames)} frames")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", type=pathlib.Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--output-dir", type=pathlib.Path, required=True)
    ap.add_argument("--header", type=pathlib.Path, required=True)
    ap.add_argument("--chart-dir", type=pathlib.Path, required=True)
    ap.add_argument("--scene", type=pathlib.Path, required=True)
    ap.add_argument("--visual-header", type=pathlib.Path, required=True)
    ap.add_argument("--reuse-audio", action="store_true")
    args = ap.parse_args()
    samples: dict[str, int] = {}
    max_notes = 0
    decoded = args.output_dir / "decoded"
    for song_id, _label, audio_name, code, player_name, opponent_name, _stage in SONGS:
        root = args.assets / "preload/data/songs" / song_id
        chart = json.loads((root / f"{song_id}-chart.json").read_text(encoding="utf-8"))
        metadata = json.loads((root / f"{song_id}-metadata.json").read_text(encoding="utf-8"))
        stems = [args.assets / "songs" / song_id / "Inst.ogg"]
        if player_name:
            stems.extend((args.assets / "songs" / song_id / player_name,
                          args.assets / "songs" / song_id / opponent_name))
        if not all(path.is_file() for path in stems):
            raise FileNotFoundError(f"Missing pinned classic WeekEnd 1 stem for {song_id}: {stems}")
        wavs = [decoded / song_id / f"{name}.wav" for name in ("inst", "player", "opponent")]
        output = args.output_dir / audio_name.lower()
        if not args.reuse_audio:
            decode(args.ffmpeg, stems[0], wavs[0])
            if player_name:
                decode(args.ffmpeg, stems[1], wavs[1]); decode(args.ffmpeg, stems[2], wavs[2])
            else:
                wavs[0].parent.mkdir(parents=True, exist_ok=True)
                frame_count = read_wav(wavs[0], RATE)[1]
                with wave.open(str(wavs[1]), "wb") as silent:
                    silent.setnchannels(2); silent.setsampwidth(2); silent.setframerate(RATE)
                    silent.writeframes(b"\0\0\0\0" * frame_count)
                with wave.open(str(wavs[2]), "wb") as silent:
                    silent.setnchannels(2); silent.setsampwidth(2); silent.setframerate(RATE)
                    silent.writeframes(b"\0\0\0\0" * frame_count)
            samples[song_id] = encode_four_channel_vagi(wavs[0], wavs[1], wavs[2], output, song_id)
        else:
            if not output.is_file() or not all(p.is_file() for p in wavs):
                raise FileNotFoundError(f"--reuse-audio requires VAGi and decoded PCM for {song_id}")
            samples[song_id] = max(read_wav(p, RATE)[1] for p in wavs)
        chart_info = chart
        for difficulty in DIFFICULTIES:
            out = args.chart_dir / f"{code}{DIFFICULTY_EXT[difficulty]}.BIN"
            count = chart_file(out, chart_info, metadata, difficulty, samples[song_id], song_id)
            max_notes = max(max_notes, count)
            print(f"{song_id}/{difficulty}: {count} notes")
    save_catalog(args.header, samples, max_notes)
    make_scene(args.assets, args.ffmpeg, args.scene, args.visual_header)


if __name__ == "__main__":
    main()
