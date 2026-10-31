#!/usr/bin/env python3
"""Build the pinned Tutorial/Week 1/Week 2 chart catalog and streamed VAGi stems."""
from __future__ import annotations
import argparse
import json
import math
import struct
import subprocess
import sys
import wave
from array import array
from pathlib import Path

from convert_bopeebo_to_vagi import (
    INTERLEAVE, SAMPLES_PER_CHUNK, TAIL_CHUNKS, encode_channel, read_wav, write_vagi,
)

RATE = 43008
DIFFICULTIES = ("easy", "normal", "hard")
DIFFICULTY_EXT = {"easy": "E", "normal": "N", "hard": "H"}
SONGS = (
    ("tutorial", "TUTORIAL", "\\\\TUTORIAL.VAG", "gf", "Voices-gf.ogg", 1, 0),
    ("bopeebo", "BOPEEBO", "\\\\STREAM.VAG", "dad", "Voices-dad.ogg", 1, 3509453),
    ("fresh", "FRESH", "\\\\FRESH.VAG", "dad", "Voices-dad.ogg", 1, 0),
    ("dadbattle", "DADBATTLE", "\\\\DADBAT.VAG", "dad", "Voices-dad.ogg", 1, 0),
    ("spookeez", "SPOOKEEZ", "\\\\SPOOKEEZ.VAG", "spooky", "Voices-spooky.ogg", 2, 0),
    ("south", "SOUTH", "\\\\SOUTH.VAG", "spooky", "Voices-spooky.ogg", 2, 0),
    ("monster", "MONSTER", "\\\\MONSTER.VAG", "monster", "Voices-monster.ogg", 2, 0),
    ("pico", "PICO", "\\\\PICO.VAG", "pico", "Voices-pico.ogg", 3, 0),
    ("philly-nice", "PHILLY NICE", "\\\\PHILLY.VAG", "pico", "Voices-pico.ogg", 3, 0),
    ("blammed", "BLAMMED", "\\\\BLAMMED.VAG", "pico", "Voices-pico.ogg", 3, 0),
)


def round_sample(ms: float) -> int:
    if not math.isfinite(ms) or ms < 0:
        raise ValueError(f"invalid time value: {ms}")
    return math.floor(ms * RATE / 1000.0 + 0.5)


def decode(ffmpeg: str, source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(source), "-map", "0:a:0",
                    "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s16le", str(target)],
                   check=True)


def encode_four_channel_vagi(inst: Path, player: Path, opponent: Path,
                              output: Path, song_id: str) -> int:
    stems = [read_wav(path, RATE) for path in (inst, player, opponent)]
    # OGG stems can decode to slightly different tail lengths. They all start
    # at sample zero; pad the shorter tracks with silence to preserve that
    # shared origin and sample clock rather than clipping or shifting a stem.
    samples = max(frames for _, frames in stems)
    chunks = (samples + SAMPLES_PER_CHUNK - 1) // SAMPLES_PER_CHUNK + TAIL_CHUNKS
    padded = chunks * SAMPLES_PER_CHUNK
    encoded: list[bytes] = []
    labels = (("INST L", stems[0][0], 0), ("INST R", stems[0][0], 1),
              ("OPPONENT MONO", stems[2][0], -1), ("PLAYER MONO", stems[1][0], -1))
    for label, pcm, channel in labels:
        if channel >= 0:
            mono = [pcm[i * 2 + channel] for i in range(len(pcm) // 2)]
        else:
            mono = [(pcm[i * 2] + pcm[i * 2 + 1]) // 2 for i in range(len(pcm) // 2)]
        mono.extend([0] * (padded - len(mono)))
        print(f"{song_id}: encoding {label} ({len(mono)} samples)")
        encoded.append(encode_channel(mono, chunks))
    write_vagi(output, encoded, RATE, samples, name=("FNF " + song_id.upper()).encode("ascii"))
    return samples


def collect_notes(chart: dict, difficulty: str) -> list[tuple[int, int, int]]:
    notes = []
    for index, note in enumerate(chart["notes"][difficulty]):
        t, lane, length = float(note["t"]), int(note["d"]), float(note.get("l", 0))
        if lane < 0 or lane > 7 or lane != note["d"] or not math.isfinite(length) or length < 0:
            raise ValueError(f"invalid {difficulty} note {index}: {note!r}")
        head = round_sample(t)
        tail = round_sample(t + length)
        notes.append((head, tail, lane))
    notes.sort(key=lambda value: (value[0], value[2]))
    return notes


def collect_events(chart: dict, song_id: str) -> list[tuple[int, int]]:
    events = []
    for event in chart.get("events", []):
        if event.get("e") != "FocusCamera":
            continue
        value = event.get("v", 0)
        if isinstance(value, dict):
            value = value.get("char", 0)
        focus = int(value)
        if song_id == "tutorial" and focus == 1:
            focus = 2  # Tutorial's opponent is GF; Week 1's char 1 is Dad.
        if focus not in (-1, 0, 1, 2):
            continue
        events.append((round_sample(float(event.get("t", 0))), focus))
    events.sort()
    return events or [(0, 0)]


def collect_tempos(chart: dict, metadata: dict) -> list[tuple[int, int, int]]:
    raw = [(0.0, float(metadata["timeChanges"][0]["bpm"]))]
    raw.extend((float(point.get("t", 0)), float(point["bpm"]))
               for point in metadata.get("timeChanges", [])[1:])
    for event in chart.get("events", []):
        if event.get("e") not in ("BPMChange", "ChangeBPM"):
            continue
        value = event.get("v", {})
        bpm = value.get("bpm") if isinstance(value, dict) else value
        raw.append((float(event.get("t", 0)), float(bpm)))
    raw.sort()
    compact: list[tuple[int, float]] = []
    for ms, bpm in raw:
        if not math.isfinite(bpm) or bpm <= 0:
            raise ValueError(f"invalid BPM value {bpm}")
        sample = round_sample(ms)
        if compact and compact[-1][0] == sample:
            compact[-1] = (sample, bpm)
        elif not compact or compact[-1][1] != bpm:
            compact.append((sample, bpm))
    beat_q16 = 0
    result = []
    for index, (sample, bpm) in enumerate(compact):
        if index:
            prev_sample, prev_bpm = compact[index - 1]
            beat_q16 += int((sample - prev_sample) * prev_bpm * 65536 / (RATE * 60) + 0.5)
        result.append((sample, beat_q16, max(1, int(bpm * 100 + 0.5))))
    return result


def write_chart_header(path: Path, chart_dir: Path, chart_inputs: dict, audio_samples: dict) -> None:
    lines = ["/* Generated from pinned official chart JSON and audio; do not edit. */",
             "#ifndef PS1_SONG_CATALOG_H", "#define PS1_SONG_CATALOG_H", "#include <stdint.h>",
             f"#define PS1_CHART_RATE {RATE}u",
             "typedef struct { uint32_t head, tail; uint8_t lane; } Ps1Note;",
             "typedef struct { uint32_t sample, beat_q16; uint16_t bpm_centi; } Ps1Tempo;",
             "typedef struct { uint32_t sample; int8_t focus; } Ps1CameraEvent;",
             "typedef struct { const Ps1Note *notes; uint16_t note_count; const Ps1Tempo *tempos; uint8_t tempo_count; const Ps1CameraEvent *camera; uint8_t camera_count; } Ps1Chart;",
             "typedef struct { const char *name; const char *audio_path; uint32_t sample_count; uint8_t opponent_kind; uint8_t stage_id; const char *chart_paths[3]; } Ps1Song;",
             "#define PS1_OPPONENT_DAD 0u", "#define PS1_OPPONENT_GF 1u",
             "#define PS1_OPPONENT_SPOOKY 2u", "#define PS1_OPPONENT_MONSTER 3u",
             "#define PS1_OPPONENT_PICO 4u",
             f"#define PS1_DIFFICULTY_COUNT {len(DIFFICULTIES)}u",
             f"#define PS1_SONG_COUNT {len(SONGS)}u"]
    score_curve = []
    for ms in range(161):
        if ms < 5:
            value = 500
        else:
            factor = 1.0 - (1.0 / (1.0 + math.exp(-0.080 * (ms - 54.99))))
            value = int(500.0 * factor + 9.0)
        score_curve.append(value)
    lines.append("static const uint16_t pbot1_score_by_ms[161] = {")
    for start in range(0, len(score_curve), 12):
        lines.append("\t" + ", ".join(str(value) for value in score_curve[start:start + 12]) + ",")
    lines.append("};")
    max_notes = 0
    camera_by_song: dict[str, list[tuple[int, int]]] = {}
    tempo_by_song: dict[str, list[tuple[int, int, int]]] = {}
    chart_dir.mkdir(parents=True, exist_ok=True)
    for song_id, *_ in SONGS:
        chart, metadata = chart_inputs[song_id]
        camera_by_song[song_id] = collect_events(chart, song_id)
        tempo_by_song[song_id] = collect_tempos(chart, metadata)
        for difficulty in DIFFICULTIES:
            notes = collect_notes(chart, difficulty)
            max_notes = max(max_notes, len(notes))
            tempos = tempo_by_song[song_id]
            events = camera_by_song[song_id]
            # Disk chart format is little-endian and 4-byte aligned:
            # header 16 bytes; note 12 bytes; tempo 12 bytes; camera event 8 bytes.
            packed = bytearray(struct.pack("<4sHHHHI", b"FNC1", len(notes),
                                           len(tempos), len(events), 0,
                                           audio_samples[song_id]))
            for head, tail, lane in notes:
                packed.extend(struct.pack("<IIB3x", head, tail, lane))
            for sample, beat_q16, bpm_centi in tempos:
                packed.extend(struct.pack("<IIH2x", sample, beat_q16, bpm_centi))
            for sample, focus in events:
                packed.extend(struct.pack("<Ib3x", sample, focus))
            out = chart_dir / f"{song_id[:3].upper()}{DIFFICULTY_EXT[difficulty]}.bin"
            out.write_bytes(packed)
    lines.append(f"#define PS1_MAX_NOTE_COUNT {max_notes}u")
    lines.append("static const Ps1Song ps1_song_catalog[PS1_SONG_COUNT] = {")
    opponent_ids = {"dad": "PS1_OPPONENT_DAD", "gf": "PS1_OPPONENT_GF",
                    "spooky": "PS1_OPPONENT_SPOOKY", "monster": "PS1_OPPONENT_MONSTER",
                    "pico": "PS1_OPPONENT_PICO"}
    chart_codes = {song_id: song_id[:3].upper() for song_id, *_ in SONGS}
    for song_id, display_name, audio_path, opponent, _, stage_id, _ in SONGS:
        note_sample_count = audio_samples[song_id]
        chart_paths = ", ".join(f'"\\\\{chart_codes[song_id]}{DIFFICULTY_EXT[diff]}.BIN"' for diff in DIFFICULTIES)
        lines.append(f'\t{{ "{display_name}", "{audio_path}", {note_sample_count}u, {opponent_ids[opponent]}, {stage_id}u, {{ {chart_paths} }} }},')
    lines.extend(["};", "#endif", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")
    print(f"Catalog header: {path.stat().st_size} bytes; max notes/chart {max_notes}; {len(SONGS)} songs, {len(SONGS) * len(DIFFICULTIES)} charts remain separate files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--header", type=Path, required=True)
    parser.add_argument("--chart-dir", type=Path, required=True)
    parser.add_argument("--rate", type=int, default=RATE)
    args = parser.parse_args()
    if args.rate != RATE:
        raise SystemExit(f"catalog audio/chart clock is pinned to {RATE} Hz")
    temp = args.output_dir / "decoded"
    chart_inputs: dict[str, tuple[dict, dict]] = {}
    audio_samples: dict[str, int] = {}
    for song_id, _, _, opponent, player_voice, _, known_samples in SONGS:
        chart_dir = args.assets / "preload" / "data" / "songs" / song_id
        chart = json.loads((chart_dir / f"{song_id}-chart.json").read_text(encoding="utf-8"))
        metadata = json.loads((chart_dir / f"{song_id}-metadata.json").read_text(encoding="utf-8"))
        chart_inputs[song_id] = (chart, metadata)
        inst = args.assets / "songs" / song_id / "Inst.ogg"
        player = args.assets / "songs" / song_id / "Voices-bf.ogg"
        opponent_stem = args.assets / "songs" / song_id / player_voice
        if not all(path.is_file() for path in (inst, player, opponent_stem)):
            raise FileNotFoundError(f"missing official audio stem for {song_id}")
        wavs = [temp / song_id / (stem + ".wav") for stem in ("inst", "player", "opponent")]
        for source, target in zip((inst, player, opponent_stem), wavs):
            decode(args.ffmpeg, source, target)
        if song_id == "bopeebo":
            lengths = {read_wav(path, RATE)[1] for path in wavs}
            if len(lengths) != 1:
                raise ValueError("Bopeebo resampled stems no longer align")
            samples = lengths.pop()
            if samples != known_samples:
                raise ValueError(f"Bopeebo source decodes to {samples}, but the validated VAGi uses {known_samples} samples")
            audio_samples[song_id] = samples
        else:
            output = args.output_dir / f"{song_id}.vag"
            audio_samples[song_id] = encode_four_channel_vagi(*wavs, output, song_id)
    write_chart_header(args.header, args.chart_dir, chart_inputs, audio_samples)


if __name__ == "__main__":
    main()
