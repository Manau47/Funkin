#!/usr/bin/env python3
"""Convert the pinned official FNF chart JSON to a compact PS1 C table."""
import argparse
import json
import math
from pathlib import Path


def sample_at_ms(value: float, rate: int) -> int:
    # Round half up, avoiding Python's banker rounding for deterministic data.
    return math.floor(value * rate / 1000.0 + 0.5)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rate", type=int, default=43008)
    parser.add_argument("--bpm", type=float, default=100.0,
                        help="song BPM when the chart file has no tempo map")
    args = parser.parse_args()
    chart = json.loads(args.source.read_text(encoding="utf-8"))
    if not math.isfinite(args.bpm) or args.bpm <= 0:
        raise SystemExit("BPM must be a finite positive number")
    raw = chart["notes"]["normal"]
    notes = []
    for index, note in enumerate(raw):
        t, lane, length = float(note["t"]), int(note["d"]), float(note.get("l", 0))
        if not math.isfinite(t) or not math.isfinite(length) or t < 0 or length < 0:
            raise SystemExit(f"invalid time or hold length at chart entry {index}")
        if lane < 0 or lane > 7:
            raise SystemExit(f"invalid lane {lane} at chart entry {index}")
        if lane != note["d"]:
            raise SystemExit(f"non-integral lane at chart entry {index}")
        notes.append((sample_at_ms(t, args.rate), sample_at_ms(t + length, args.rate), lane))
    notes.sort(key=lambda note: (note[0], note[2]))
    for previous, current in zip(notes, notes[1:]):
        if current[0] < previous[0]:
            raise SystemExit("chart sort failed")
        if current[0] == previous[0] and current[2] == previous[2]:
            raise SystemExit(f"duplicate same-lane notes at sample {current[0]}")

    body = [
        "/* Generated from pinned Bopeebo Normal chart; do not edit by hand. */",
        "#ifndef BOPEEBO_CHART_H", "#define BOPEEBO_CHART_H", "#include <stdint.h>",
        "typedef struct { uint32_t head; uint32_t tail; uint8_t lane; } BopeeboNote;",
        f"#define BOPEEBO_NOTE_COUNT {len(notes)}u",
        f"#define BOPEEBO_CHART_RATE {args.rate}u",
        "static const BopeeboNote bopeebo_notes[BOPEEBO_NOTE_COUNT] = {",
    ]
    body.extend(f"\t{{ {head}u, {tail}u, {lane}u }}," for head, tail, lane in notes)
    body.extend(["};", "typedef struct { uint32_t sample; int8_t focus; } BopeeboCameraEvent;"])
    camera_events = []
    for event in chart.get("events", []):
        if event.get("e") != "FocusCamera":
            continue
        try:
            time_ms = float(event["t"])
            focus = int(event["v"])
        except (KeyError, TypeError, ValueError):
            raise SystemExit(f"invalid FocusCamera event: {event!r}")
        if not math.isfinite(time_ms) or time_ms < 0 or focus not in (-1, 0, 1, 2):
            raise SystemExit(f"unsupported FocusCamera event: {event!r}")
        camera_events.append((sample_at_ms(time_ms, args.rate), focus))
    camera_events.sort()
    body.extend([f"#define BOPEEBO_CAMERA_EVENT_COUNT {len(camera_events)}u",
                 "static const BopeeboCameraEvent bopeebo_camera_events[BOPEEBO_CAMERA_EVENT_COUNT] = {"])
    body.extend(f"\t{{ {sample}u, {focus} }}," for sample, focus in camera_events)
    body.extend(["};"])

    # Keep the audio-clock beat phase continuous across tempo changes. Charts
    # with no map get the pinned song BPM supplied by the build configuration.
    tempo_changes = [(0.0, args.bpm)]
    raw_tempo_changes = list(chart.get("bpmChanges", []))
    raw_tempo_changes.extend(
        event for event in chart.get("events", [])
        if event.get("e") in ("BPMChange", "ChangeBPM"))
    for change in raw_tempo_changes:
        try:
            time_ms = float(change.get("t", change.get("time", 0)))
            bpm_value = change.get("bpm", change.get("v"))
            if isinstance(bpm_value, dict):
                bpm_value = bpm_value.get("bpm")
            bpm = float(bpm_value)
        except (AttributeError, TypeError, ValueError):
            raise SystemExit(f"invalid BPM change: {change!r}")
        if not math.isfinite(time_ms) or time_ms < 0 or not math.isfinite(bpm) or bpm <= 0:
            raise SystemExit(f"invalid BPM change: {change!r}")
        tempo_changes.append((time_ms, bpm))
    tempo_changes.sort()
    compact_tempo: list[tuple[int, float]] = []
    for time_ms, bpm in tempo_changes:
        sample = sample_at_ms(time_ms, args.rate)
        if compact_tempo and compact_tempo[-1][0] == sample:
            compact_tempo[-1] = (sample, bpm)
        elif not compact_tempo or compact_tempo[-1][1] != bpm:
            compact_tempo.append((sample, bpm))
    if not compact_tempo or compact_tempo[0][0] != 0:
        compact_tempo.insert(0, (0, args.bpm))
    beat_q16 = 0
    tempo_rows = []
    for i, (sample, bpm) in enumerate(compact_tempo):
        if i:
            previous_sample, previous_bpm = compact_tempo[i - 1]
            beat_q16 += int((sample - previous_sample) * previous_bpm * 65536 /
                            (args.rate * 60) + 0.5)
        tempo_rows.append((sample, beat_q16, max(1, int(bpm * 100 + 0.5))))
    body.extend(["typedef struct { uint32_t sample; uint32_t beat_q16; uint16_t bpm_centi; } BopeeboTempoChange;",
                 f"#define BOPEEBO_TEMPO_CHANGE_COUNT {len(tempo_rows)}u",
                 "static const BopeeboTempoChange bopeebo_tempo_changes[BOPEEBO_TEMPO_CHANGE_COUNT] = {"])
    body.extend(f"\t{{ {sample}u, {beat}u, {bpm}u }}," for sample, beat, bpm in tempo_rows)
    body.extend(["};", "static const uint16_t pbot1_score_by_ms[161] = {"])
    values = []
    for ms in range(161):
        if ms < 5:
            value = 500
        else:
            factor = 1.0 - (1.0 / (1.0 + math.exp(-0.080 * (ms - 54.99))))
            value = int(500.0 * factor + 9.0)
        values.append(value)
    for start in range(0, len(values), 12):
        body.append("\t" + ", ".join(str(value) for value in values[start:start + 12]) + ",")
    body.extend(["};", "#endif", ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(body), encoding="ascii")
    holds = sum(tail > head for head, tail, _ in notes)
    last_tail = max((tail for _, tail, _ in notes), default=0)
    print(f"{len(notes)} notes, {holds} holds, last tail {last_tail} samples; tempo points {len(tempo_rows)}")


if __name__ == "__main__":
    main()
