#!/usr/bin/env python3
"""Convert the pinned classic Week 6 charts, four-channel audio and pixel scene for PS1."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from convert_bopeebo_visuals import (  # noqa: E402
    blend_at, extract_sparrow_frame, median_palette, png_size, quantize, rgb555, run_ffmpeg,
)
from generate_ps1_song_catalog import (  # noqa: E402
    DIFFICULTIES, DIFFICULTY_EXT, RATE, collect_events, collect_notes,
    collect_tempos, decode, encode_four_channel_vagi, read_wav,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE
SONGS = (
    ("senpai", "SENPAI", "SENPAI.VAG", "SEN", "Voices-senpai.ogg", "senpai", 144),
    ("roses", "ROSES", "ROSES.VAG", "ROS", "Voices-senpai.ogg", "senpai-angry", 120),
    ("thorns", "THORNS", "THORNS.VAG", "THO", "Voices-spirit.ogg", "spirit", 190),
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
        "/* Generated from pinned classic Week 6 charts and official stems. */",
        "#ifndef PS1_WEEK6_CATALOG_H", "#define PS1_WEEK6_CATALOG_H",
        '#include "week5_catalog.h"',
        "#define PS1_WEEK5_TOTAL_SONG_COUNT (PS1_BASE_SONG_COUNT + PS1_WEEK4_SONG_COUNT + PS1_WEEK5_SONG_COUNT)",
        "#undef PS1_SONG_COUNT", "#define PS1_WEEK6_SONG_COUNT 3u",
        "#define PS1_SONG_COUNT (PS1_WEEK5_TOTAL_SONG_COUNT + PS1_WEEK6_SONG_COUNT)",
        "#define PS1_OPPONENT_SENPAI 7u", "#define PS1_OPPONENT_SENPAI_ANGRY 8u",
        "#define PS1_OPPONENT_SPIRIT 9u",
        "#undef PS1_MAX_NOTE_COUNT", f"#define PS1_MAX_NOTE_COUNT {max(674, max_notes)}u",
        "static const Ps1Song ps1_week6_song_catalog[PS1_WEEK6_SONG_COUNT] = {",
    ]
    for song_id, label, audio_name, code, _voice, opponent, _bpm in SONGS:
        opponent_kind = {"senpai": "PS1_OPPONENT_SENPAI",
                         "senpai-angry": "PS1_OPPONENT_SENPAI_ANGRY",
                         "spirit": "PS1_OPPONENT_SPIRIT"}[opponent]
        charts = ", ".join(f'"\\\\{code}{DIFFICULTY_EXT[d]}.BIN"' for d in DIFFICULTIES)
        lines.append(f'\t{{ "{label}", "\\\\{audio_name}", {samples[song_id]}u, {opponent_kind}, 6u, {{ {charts} }} }},')
    lines.extend(["};", "#endif", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")


def first_xml_frame(xml_path: pathlib.Path, prefix: str) -> dict[str, int | str]:
    matches = [item for item in ET.parse(xml_path).getroot().findall("SubTexture")
               if item.attrib.get("name", "").startswith(prefix)]
    if not matches:
        raise ValueError(f"Missing Sparrow frame prefix {prefix!r} in {xml_path}")
    node = matches[0]
    frame = {key: int(node.attrib.get(key, 0)) for key in
             ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
    frame["rotated"] = node.attrib.get("rotated", "false").lower() == "true"
    frame["name"] = node.attrib.get("name", prefix)
    return frame


def png_layer(ffmpeg: str, source: pathlib.Path, width: int, height: int) -> bytearray:
    filters = (f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=neighbor,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x00000000,format=rgba")
    return run_ffmpeg(ffmpeg, source, filters, width, height)


def make_stage(assets: pathlib.Path, ffmpeg: str, evil: bool) -> bytearray:
    root = assets / "week6/images/weeb"
    stage = bytearray(PAGE_BYTES * 4)
    if evil:
        # The classic schoolEvil stage uses a solid-black base and four official pixel layers.
        for y in range(PAGE):
            for x in range(PAGE):
                i = (y * PAGE + x) * 4
                stage[i:i + 4] = b"\x00\x00\x00\xff"
        layers = [
            (root / "evil/weebBackTrees.png", 256, 72, 0, 24),
            (root / "evil/weebSchool.png", 256, 95, 0, 16),
            (root / "evil/weebStreet.png", 256, 76, 0, 111),
            (root / "evil/weebTrees.png", 256, 58, 0, 113),
        ]
    else:
        sky = png_layer(ffmpeg, root / "weebSky.png", 256, 192)
        blend_at(stage, (256, 256), sky, (256, 192), (0, 0))
        layers = [
            (root / "weebBackTrees.png", 256, 76, 0, 37),
            (root / "weebSchool.png", 256, 92, 0, 39),
            (root / "weebStreet.png", 256, 82, 0, 111),
            (root / "weebTreesBack.png", 256, 55, 0, 119),
        ]
    for source, width, height, x, y in layers:
        pixels = png_layer(ffmpeg, source, width, height)
        blend_at(stage, (256, 256), pixels, (width, height), (x, y))
    if not evil:
        xml_path = root / "bgFreaks.xml"
        frame = first_xml_frame(xml_path, "BG girls group")
        girls = extract_sparrow_frame(ffmpeg, root / "bgFreaks.png", frame, (72, 58))
        blend_at(stage, (256, 256), girls, (72, 58), (92, 131))
    return stage


def make_scene(assets: pathlib.Path, ffmpeg: str, output: pathlib.Path,
               header: pathlib.Path) -> None:
    page_rgba = [make_stage(assets, ffmpeg, False), make_stage(assets, ffmpeg, True)]
    frame_defs: list[tuple[str, int, int, int, int, int]] = [
        ("STAGE_SCHOOL", 0, 0, 0, 256, 192),
        ("STAGE_EVIL", 1, 0, 0, 256, 192),
    ]
    frames_per_page = 16
    character_specs: list[tuple[str, pathlib.Path, pathlib.Path, str, int, int]] = []
    senpai_png = assets / "shared/images/characters/senpai.png"
    senpai_xml = assets / "shared/images/characters/senpai.xml"
    for prefix, label in (("Senpai Idle instance 10", "SENPAI_IDLE"),
                          ("SENPAI LEFT NOTE instance 10", "SENPAI_LEFT"),
                          ("SENPAI DOWN NOTE instance 10", "SENPAI_DOWN"),
                          ("SENPAI UP NOTE instance 10", "SENPAI_UP"),
                          ("SENPAI RIGHT NOTE instance 10", "SENPAI_RIGHT"),
                          ("Angry Senpai Idle instance 10", "ANGRY_IDLE"),
                          ("Angry Senpai LEFT NOTE instance 10", "ANGRY_LEFT"),
                          ("Angry Senpai DOWN NOTE instance 10", "ANGRY_DOWN"),
                          ("Angry Senpai UP NOTE instance 10", "ANGRY_UP"),
                          ("Angry Senpai RIGHT NOTE instance 10", "ANGRY_RIGHT")):
        character_specs.append((label, senpai_png, senpai_xml, prefix, 64, 64))
    bf_png = assets / "shared/images/characters/bfPixel.png"
    bf_xml = assets / "shared/images/characters/bfPixel.xml"
    for prefix, label in (("BF IDLE instance 10", "BF_IDLE"),
                          ("BF LEFT NOTE instance 10", "BF_LEFT"),
                          ("BF DOWN NOTE instance 10", "BF_DOWN"),
                          ("BF UP NOTE instance 10", "BF_UP"),
                          ("BF RIGHT NOTE instance 10", "BF_RIGHT"),
                          ("BF LEFT MISS instance 10", "BF_MISS_LEFT"),
                          ("BF DOWN MISS instance 10", "BF_MISS_DOWN"),
                          ("BF UP MISS instance 10", "BF_MISS_UP"),
                          ("BF RIGHT MISS instance 10", "BF_MISS_RIGHT")):
        character_specs.append((label, bf_png, bf_xml, prefix, 64, 64))
    gf_png = assets / "shared/images/characters/gfPixel.png"
    gf_xml = assets / "shared/images/characters/gfPixel.xml"
    for frame_number in (0, 15):
        nodes = ET.parse(gf_xml).getroot().findall("SubTexture")
        candidates = [n for n in nodes if n.attrib.get("name", "").startswith("GF IDLE")]
        node = candidates[min(frame_number, len(candidates) - 1)]
        character_specs.append((f"GF_DANCE_{frame_number // 15}", gf_png, gf_xml,
                                node.attrib["name"], 64, 64))
    spirit_png = assets / "shared/images/characters/spirit.png"
    spirit_regions: dict[str, tuple[int, int, int, int]] = {}
    for line in (assets / "shared/images/characters/spirit.txt").read_text(encoding="utf-8").splitlines():
        match = re.match(r"(.*?)\s*=\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$", line)
        if match and match.group(1) not in spirit_regions:
            spirit_regions[match.group(1)] = tuple(map(int, match.groups()[1:]))
    for prefix, label in (("idle spirit_", "SPIRIT_IDLE"), ("left_", "SPIRIT_LEFT"),
                          ("spirit down_", "SPIRIT_DOWN"), ("up_", "SPIRIT_UP"),
                          ("right_", "SPIRIT_RIGHT")):
        region = next((v for k, v in spirit_regions.items() if k.startswith(prefix)), None)
        if region is None:
            raise ValueError(f"Missing Spirit atlas region {prefix}")
        x, y, w, h = region
    ordered_chars: list[tuple[str, bytearray]] = []
    for label, png, xml_path, prefix, width, height in character_specs:
        ordered_chars.append((label, extract_sparrow_frame(ffmpeg, png, first_xml_frame(xml_path, prefix), (width, height))))
    # Spirit uses a text atlas rather than Sparrow XML; crop its official poses.
    for prefix, label in (("idle spirit_", "SPIRIT_IDLE"), ("left_", "SPIRIT_LEFT"),
                          ("spirit down_", "SPIRIT_DOWN"), ("up_", "SPIRIT_UP"),
                          ("right_", "SPIRIT_RIGHT")):
        x, y, w, h = next(v for k, v in spirit_regions.items() if k.startswith(prefix))
        pixels = run_ffmpeg(ffmpeg, spirit_png,
            f"crop={w}:{h}:{x}:{y},scale=64:64:force_original_aspect_ratio=decrease:flags=neighbor,"
            "pad=64:64:(ow-iw)/2:(oh-ih)/2:color=0x00000000,format=rgba", 64, 64)
        ordered_chars.append((label, pixels))
    for label, filename in (("ICON_SENPAI", "icon-senpai.png"),
                            ("ICON_SENPAI_ANGRY", "icon-senpai-angry.png"),
                            ("ICON_SPIRIT", "icon-spirit.png")):
        icon_path = assets / "preload/images/icons" / filename
        icon_w, icon_h = png_size(icon_path)
        face_w = icon_w // 2 if icon_w >= icon_h * 2 else icon_w
        pixels = run_ffmpeg(ffmpeg, icon_path,
            f"crop={face_w}:{icon_h}:0:0,scale=64:64:force_original_aspect_ratio=decrease:flags=neighbor,"
            "pad=64:64:(ow-iw)/2:(oh-ih)/2:color=0x00000000,format=rgba", 64, 64)
        ordered_chars.append((label, pixels))
    char_pages = [bytearray(PAGE_BYTES * 4), bytearray(PAGE_BYTES * 4)]
    for index, (label, pixels) in enumerate(ordered_chars):
        page_index, cell = divmod(index, frames_per_page)
        x, y = (cell % 4) * 64, (cell // 4) * 64
        if len(pixels) != 64 * 64 * 4:
            raise ValueError(f"Week 6 character frame {label} has {len(pixels)} bytes, expected 16384")
        blend_at(char_pages[page_index], (256, 256), pixels, (64, 64), (x, y))
        frame_defs.append((label, 2 + page_index, x, y, 64, 64))
    page_rgba.extend(char_pages)

    # Pixel arrow atlas: 4 gray receptors, 4 colored notes, 4 press frames and 8 confirms.
    arrow_png = assets / "week6/images/weeb/pixelUI/arrows-pixels.png"
    arrow_xml = assets / "week6/images/weeb/pixelUI/arrows-pixels.xml"
    nodes = {item.attrib["name"]: item for item in ET.parse(arrow_xml).getroot().findall("SubTexture")}
    arrow_page = bytearray(PAGE_BYTES * 4)
    arrow_names: list[str] = []
    for direction, letter in enumerate(("LEFT", "DOWN", "UP", "RIGHT")):
        arrow_names.extend([f"PIXEL_RECEIVER_{letter}", f"PIXEL_NOTE_{letter}",
                            f"PIXEL_PRESS_{letter}", f"PIXEL_CONFIRM_{letter}_0",
                            f"PIXEL_CONFIRM_{letter}_1"])
    for index, name in enumerate(arrow_names):
        direction = index // 5
        type_index = index % 5
        prefixes = ["static", "note", "pressed", "confirm", "confirm"]
        sequence = ["0001", "0001", "0001", "0001", "0002"]
        source_name = prefixes[type_index] + ("Left", "Down", "Up", "Right")[direction] + sequence[type_index]
        node = nodes[source_name]
        frame = {key: int(node.attrib.get(key, 0)) for key in ("x", "y", "width", "height")}
        frame.update({"frameX": 0, "frameY": 0, "frameWidth": frame["width"],
                      "frameHeight": frame["height"], "rotated": False, "name": source_name})
        pixels = extract_sparrow_frame(ffmpeg, arrow_png, frame, (17, 17))
        x, y = (index % 8) * 32, (index // 8) * 32
        blend_at(arrow_page, (256, 256), pixels, (17, 17), (x, y))
        frame_defs.append((name, 4, x, y, 17, 17))
    page_rgba.append(arrow_page)

    palette = median_palette(page_rgba, 255)
    indexed_pages = [quantize(page, palette) for page in page_rgba]
    if len(indexed_pages) != 5 or any(len(page) != PAGE_BYTES for page in indexed_pages):
        raise ValueError("Week 6 payload must contain exactly five 8bpp 256x256 pages")
    words = [0] + [rgb555(color) for color in palette[:255]]
    words += [0] * (256 - len(words))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(indexed_pages) + struct.pack("<256H", *words))

    lines = ["/* Generated from pinned classic Week 6 pixel assets. */",
             "#ifndef PS1_WEEK6_VISUAL_DATA_H", "#define PS1_WEEK6_VISUAL_DATA_H",
             "#define BOPEEBO_WEEK6_PAGE_COUNT 5u",
             "#define BOPEEBO_WEEK6_CHARACTER_FRAME_W 64u",
             "#define BOPEEBO_WEEK6_CHARACTER_FRAME_H 64u",
             "typedef struct { uint8_t page, u, v; uint16_t w, h; } Week6VisualFrame;", "enum {"]
    for index, (name, *_rest) in enumerate(frame_defs):
        lines.append(f"\tWEEK6_FRAME_{name} = {index},")
    lines.extend(["};", f"#define WEEK6_VISUAL_FRAME_COUNT {len(frame_defs)}u",
                  "static const Week6VisualFrame week6_visual_frames[WEEK6_VISUAL_FRAME_COUNT] = {"])
    for name, page, x, y, w, h in frame_defs:
        lines.append(f"\t{{ {page}u, {x}u, {y}u, {w}u, {h}u }}, /* {name} */")
    lines.extend(["};", "#endif", ""])
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text("\n".join(lines), encoding="ascii")
    print(f"Week 6 scene: {len(indexed_pages)} 8bpp pages, {output.stat().st_size} bytes; {len(ordered_chars)} character poses")


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
    for song_id, _label, audio_name, code, voice_name, _opponent, _bpm in SONGS:
        root = args.assets / "preload/data/songs" / song_id
        chart = json.loads((root / f"{song_id}-chart.json").read_text(encoding="utf-8"))
        metadata = json.loads((root / f"{song_id}-metadata.json").read_text(encoding="utf-8"))
        stems = [args.assets / "songs" / song_id / name for name in
                 ("Inst.ogg", "Voices-bf.ogg", voice_name)]
        if not all(path.is_file() for path in stems):
            raise FileNotFoundError(f"Missing official Week 6 classic stem for {song_id}")
        wavs = [decoded / song_id / f"{name}.wav" for name in ("inst", "bf", "opponent")]
        vagi_path = args.output_dir / audio_name.lower()
        if args.reuse_audio:
            if not vagi_path.is_file() or not all(path.is_file() for path in wavs):
                raise FileNotFoundError(f"--reuse-audio requires existing VAGi and decoded PCM for {song_id}")
            samples[song_id] = read_wav(wavs[0], RATE)[1]
            print(f"{song_id}: reusing {vagi_path} and decoded PCM ({samples[song_id]} samples)")
        else:
            for source, target in zip(stems, wavs):
                decode(args.ffmpeg, source, target)
            samples[song_id] = encode_four_channel_vagi(wavs[0], wavs[1], wavs[2],
                                                         vagi_path, song_id)
        for difficulty in DIFFICULTIES:
            chart_path = args.chart_dir / f"{code}{DIFFICULTY_EXT[difficulty]}.BIN"
            count = write_chart(chart_path, chart, metadata, difficulty, samples[song_id], song_id)
            max_notes = max(max_notes, count)
            print(f"{song_id}/{difficulty}: {count} notes, {chart_path.stat().st_size} bytes")
    save_catalog(args.header, samples, max_notes)
    make_scene(args.assets, args.ffmpeg, args.scene, args.visual_header)


if __name__ == "__main__":
    main()
