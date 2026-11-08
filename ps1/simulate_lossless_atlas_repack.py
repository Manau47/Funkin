#!/usr/bin/env python3
"""Estimate lossless page counts after exact-cel aliasing and MaxRects packing.

Consumes the generated frame-fiche CSV; it never writes or changes assets.
Full-page stage layers remain fixed in their original page slots.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from repack_indexed_week_atlas import maxrects


DEFAULT_FIXED_PAGES = {
    "base-w1": 9,
    "week2": 2,
    "week3": 4,
    "week4": 2,
    "week5": 2,
    "week6": 2,
    "week7": 2,
    "weekend1": 2,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fiches", type=Path)
    parser.add_argument("--include", nargs="*", default=list(DEFAULT_FIXED_PAGES))
    parser.add_argument("--fixed-pages", nargs="*", default=[])
    args = parser.parse_args()
    fixed = dict(DEFAULT_FIXED_PAGES)
    for item in args.fixed_pages:
        name, value = item.split("=", 1)
        fixed[name] = int(value)

    with args.fiches.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    results = []
    for package in args.include:
        group = [r for r in rows if r["package"] == package and int(r["uv_w"]) > 0 and int(r["uv_h"]) > 0]
        if not group:
            continue
        old_pages = max(int(r["page"]) for r in group) + 1
        pinned = fixed.get(package, 0)
        uniques: dict[tuple[str, int, int], dict] = {}
        for r in group:
            if int(r["page"]) < pinned:
                continue
            key = (r["indexed_sha256"], int(r["uv_w"]), int(r["uv_h"]))
            uniques.setdefault(key, {"label": r["label"], "w": int(r["uv_w"]), "h": int(r["uv_h"])})
        packed, _ = maxrects(list(uniques.values()))
        results.append((package, old_pages, pinned, len(uniques), pinned + len(packed)))

    print("package,old_pages,fixed_stage_pages,unique_moving_cels,estimated_new_pages,page_delta")
    for package, old, pinned, unique, new in results:
        print(f"{package},{old},{pinned},{unique},{new},{new-old:+d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
