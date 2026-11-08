#!/usr/bin/env python3
"""Merge sampled Week 3 descriptors into the last validated shared atlas header.

The normal visual converter is intentionally broad: it rebuilds the base/menu
atlas as well as week packages. This helper preserves all base/menu tables and
their matching CLUT from a known-good header, while taking only Week 3 frame
descriptors and the expanded frame-index macros from a freshly converted
header. It prevents an updated W3 package from silently changing the palette
used by the still-resident W1 pages.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FRAME_TABLE_RE = re.compile(
    r"static const BopeeboVisualFrame bopeebo_visual_frames\[.*?\] = \{(.*?)\n\};",
    re.S,
)
PAGE_TABLE_RE = re.compile(
    r"static const BopeeboVisualPage bopeebo_visual_page_table\[.*?\] = \{(.*?)\n\};",
    re.S,
)
FRAME_ROW_RE = re.compile(r"\{([^{}]+)\},\s*/\*\s*([^*]+?)\s*\*/")
PAGE_ROW_RE = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}")


def parse_rows(header: str) -> dict[str, tuple[int, ...]]:
    match = FRAME_TABLE_RE.search(header)
    if not match:
        raise ValueError("missing bopeebo_visual_frames table")
    rows: dict[str, tuple[int, ...]] = {}
    for values, name in FRAME_ROW_RE.findall(match.group(1)):
        row = tuple(int(value.strip(), 0) for value in values.split(","))
        if len(row) not in (6, 8, 9):
            raise ValueError(f"unexpected frame row width for {name}: {len(row)}")
        rows[name.strip()] = row
    if not rows:
        raise ValueError("empty bopeebo_visual_frames table")
    return rows


def parse_page_table(header: str) -> tuple[tuple[int, int, int], ...]:
    match = PAGE_TABLE_RE.search(header)
    if not match:
        raise ValueError("missing bopeebo_visual_page_table")
    return tuple(tuple(map(int, row)) for row in PAGE_ROW_RE.findall(match.group(1)))


def parse_macros(header: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip()
        for line in header.splitlines()
        if (match := re.match(r"#define\s+(\w+)\s+(.+)$", line))
    }


def classify_anchor(name: str) -> int:
    if name.startswith("week3_pico_"):
        return 1
    if name.startswith("week3_gf_"):
        return 2
    return 0


def format_row(row: tuple[int, ...], name: str, use_week3: bool) -> str:
    values = list(row[:8])
    if len(values) < 8:
        values.extend([0] * (8 - len(values)))
    values = values[:8] + [classify_anchor(name) if use_week3 else 0]
    return "\t{" + ", ".join(map(str, values)) + f" }}, /* {name} */"


def merge(base: str, converted: str) -> str:
    if parse_page_table(base) != parse_page_table(converted):
        raise ValueError("base and converted VRAM page tables differ")
    base_macros = parse_macros(base)
    new_macros = parse_macros(converted)
    for name, value in base_macros.items():
        if name.startswith("VIS_") or name == "BOPEEBO_VISUAL_FRAME_COUNT":
            continue
        if new_macros.get(name) != value:
            raise ValueError(f"non-frame layout macro changed: {name}")

    base_rows = parse_rows(base)
    new_rows = parse_rows(converted)
    if not set(base_rows).issubset(new_rows):
        missing = sorted(set(base_rows) - set(new_rows))
        raise ValueError(f"converted header removed base frames: {missing[:4]}")
    added = set(new_rows) - set(base_rows)
    if any(not name.startswith("week3_") for name in added):
        raise ValueError(f"non-Week-3 frames were added: {sorted(added)[:4]}")

    # Use converter order because VIS_* macros are indexes into this table.
    merged_rows = []
    for name in new_rows:
        is_week3 = name.startswith("week3_")
        row = new_rows[name] if is_week3 else base_rows[name]
        merged_rows.append(format_row(row, name, is_week3))
    table = (
        "static const BopeeboVisualFrame bopeebo_visual_frames[BOPEEBO_VISUAL_FRAME_COUNT] = {\n"
        + "\n".join(merged_rows)
        + "\n};"
    )
    result, count = FRAME_TABLE_RE.subn(table, base, count=1)
    if count != 1:
        raise ValueError("could not replace base frame table")

    base_lines = result.splitlines()
    converted_lines = converted.splitlines()
    converted_vis = [line for line in converted_lines if line.startswith("#define VIS_")]
    first_vis = next((i for i, line in enumerate(base_lines)
                      if line.startswith("#define VIS_")), None)
    if first_vis is None or not converted_vis:
        raise ValueError("missing generated VIS_* index macros")
    last_vis = first_vis
    while last_vis + 1 < len(base_lines) and base_lines[last_vis + 1].startswith("#define VIS_"):
        last_vis += 1
    base_lines[first_vis:last_vis + 1] = converted_vis
    result = "\n".join(base_lines) + "\n"

    base_count = re.search(r"#define BOPEEBO_VISUAL_FRAME_COUNT\s+\d+u", result)
    converted_count = re.search(r"#define BOPEEBO_VISUAL_FRAME_COUNT\s+\d+u", converted)
    if not base_count or not converted_count:
        raise ValueError("missing visual frame count macro")
    result = result.replace(base_count.group(0), converted_count.group(0), 1)
    result = result.replace(
        "typedef struct { uint8_t page, palette, u, v; uint16_t w, h; } BopeeboVisualFrame;",
        "typedef struct { uint8_t page, palette, u, v; uint16_t w, h; "
        "int8_t trim_x, trim_y; uint8_t anchor; } BopeeboVisualFrame;",
        1,
    )
    if "uint8_t anchor; } BopeeboVisualFrame;" not in result:
        raise ValueError("could not upgrade frame metadata struct")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path,
                        help="last validated base/menu visual header")
    parser.add_argument("--week3", required=True, type=Path,
                        help="newly converted header containing Week 3 frames")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    base = args.base.read_text(encoding="utf-8")
    converted = args.week3.read_text(encoding="utf-8")
    result = merge(base, converted)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8", newline="\n")
    print(f"Merged {len(parse_rows(base))} base frames and "
          f"{len(parse_rows(converted)) - len(parse_rows(base))} new Week 3 frames")
    print("Preserved the base/menu CLUT, page data, and all non-Week-3 frame descriptors")
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
