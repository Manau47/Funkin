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
    args = parser.parse_args()
    chart = json.loads(args.source.read_text(encoding="utf-8"))
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
    print(f"{len(notes)} notes, {holds} holds, last tail {max(t for _, t, _ in notes)} samples")


if __name__ == "__main__":
    main()
