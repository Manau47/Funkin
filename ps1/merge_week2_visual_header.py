#!/usr/bin/env python3
"""Merge only regenerated Week 2 descriptors into a preserved visual header.

The main visual converter also emits Week 1 and Week 3 data. This utility
keeps those sections byte-for-byte from the selected baseline header while
updating only Week 2 page counts, page mapping, and frame descriptors.
"""

from __future__ import annotations

import argparse
import pathlib
import re


REQUIRED_MACROS = ("BOPEEBO_WEEK2_CHARACTER_PAGE_COUNT", "BOPEEBO_WEEK2_PAGE_COUNT")
OPTIONAL_MACROS = ("BOPEEBO_WEEK2_GF_FRAME_W", "BOPEEBO_WEEK2_GF_FRAME_H")
OPTIONAL_MACROS += tuple(
    f"BOPEEBO_WEEK2_{character}_{field}"
    for character in ("DAD", "GF", "BF")
    for field in ("X", "Y", "CAMERA_X", "CAMERA_Y")
)
MACROS = REQUIRED_MACROS + OPTIONAL_MACROS
FRAME_RE = re.compile(r"/\*\s*(week2_[A-Za-z0-9_]+)\s*\*/")


def macro_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for name in MACROS:
        match = re.search(rf"^#define\s+{name}\s+([^\r\n]+)", text, re.MULTILINE)
        if not match and name in REQUIRED_MACROS:
            raise ValueError(f"missing required macro {name}")
        if match:
            values[name] = match.group(1).strip()
    return values


def frames(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        match = FRAME_RE.search(line)
        if match:
            result[match.group(1)] = line
    return result


def merge(baseline: str, converted: str) -> str:
    old_values = macro_values(baseline)
    new_values = macro_values(converted)
    old_frames = frames(baseline)
    new_frames = frames(converted)
    if not old_frames or old_frames.keys() != new_frames.keys():
        missing = sorted(old_frames.keys() - new_frames.keys())
        added = sorted(new_frames.keys() - old_frames.keys())
        raise ValueError(f"Week 2 descriptor set changed (missing={missing}, added={added})")

    lines = baseline.splitlines()
    converted_lines = converted.splitlines()
    converted_macro_lines = {
        name: next(line for line in converted_lines if line.startswith(f"#define {name} "))
        for name in MACROS
    }
    converted_slots = next((line for line in converted_lines
        if line.startswith("static const uint8_t bopeebo_week2_page_slots[")), None)
    if converted_slots is None:
        raise ValueError("converted header is missing the Week 2 page map")

    missing_macros = set(new_values) - set(old_values)
    for index, line in enumerate(lines):
        for name in MACROS:
            if name in new_values and line.startswith(f"#define {name} "):
                lines[index] = converted_macro_lines[name]
                break
        if line.startswith("static const uint8_t bopeebo_week2_page_slots["):
            lines[index] = converted_slots
            continue
        match = FRAME_RE.search(line)
        if match:
            lines[index] = new_frames[match.group(1)]

    if missing_macros:
        anchor = "#define BOPEEBO_WEEK2_GF_FRAME_H"
        insertion = next((i + 1 for i, line in enumerate(lines)
                          if line.startswith(anchor + " ")), None)
        if insertion is None:
            raise ValueError("cannot place additional Week 2 macros in baseline header")
        lines[insertion:insertion] = [converted_macro_lines[name]
            for name in OPTIONAL_MACROS if name in missing_macros]

    merged = "\n".join(lines) + "\n"
    if macro_values(merged) != new_values or frames(merged) != new_frames:
        raise ValueError("merged header failed its Week 2 consistency check")
    # Guard the ownership boundary: the shared/global palette must come from
    # the baseline, never the converter's regenerated palette set.
    for name in ("bopeebo_visual_palette8", "bopeebo_visual_palette4"):
        def declaration(text: str) -> str:
            return next((line for line in text.splitlines()
                if line.startswith(f"static const uint16_t {name}[")), "")
        if declaration(merged) != declaration(baseline):
            raise ValueError(f"baseline palette unexpectedly changed: {name}")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=pathlib.Path, required=True)
    parser.add_argument("--converted", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = merge(args.baseline.read_text(encoding="ascii"),
                   args.converted.read_text(encoding="ascii"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="ascii", newline="\n")
    print(f"Merged Week 2 only: {len(frames(result))} descriptors; "
          f"{macro_values(result)['BOPEEBO_WEEK2_PAGE_COUNT']} pages")


if __name__ == "__main__":
    main()
