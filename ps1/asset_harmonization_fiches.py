#!/usr/bin/env python3
"""Make source-to-atlas fiches from pinned source inventory and built outputs.

The tool is read-only with respect to its inputs. It reads existing indexed
packages and headers; it does not run image/audio conversion or mutate assets.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from collections import defaultdict
from pathlib import Path


def png_size(path: Path) -> tuple[int, int] | tuple[str, str]:
    try:
        data = path.read_bytes()[:24]
        if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            return ("", "")
        return struct.unpack(">II", data[16:24])
    except OSError:
        return ("", "")


def frame_rows(header: Path, array_name: str) -> list[dict]:
    text = header.read_text(encoding="utf-8")
    m = re.search(rf"static const [^;]+?\s+{re.escape(array_name)}\s*\[[^]]*\]\s*=\s*\{{(.*?)\n\}};", text, re.S)
    if not m:
        raise ValueError(f"missing {array_name} in {header}")
    out = []
    for line in m.group(1).splitlines():
        row = re.search(r"\{([^{}]+)\}\s*,?\s*/\*\s*(.*?)\s*\*/", line)
        if not row:
            continue
        nums = [int(v.rstrip("uU"), 0) for v in re.findall(r"(?<![A-Za-z_])(?:0x[\da-fA-F]+|\d+)[uU]?", row.group(1))]
        if len(nums) >= 5:
            # Week 1 has page/CLUT/UV/size/trim/anchor. W4/6/7/WEnd1 omit CLUT.
            if len(nums) >= 9:
                page, clut, u, v, w, h, trim_x, trim_y, anchor = nums[:9]
            else:
                page, u, v, w, h = nums[:5]
                clut, trim_x, trim_y, anchor = 0, 0, 0, 0
            out.append(dict(label=row.group(2), page=page, clut=clut, u=u, v=v,
                            w=w, h=h, trim_x=trim_x, trim_y=trim_y, anchor=anchor))
    return out


def groups(label: str) -> str:
    low = label.lower()
    prefixes = ("stage_scene", "dad_", "gf_", "bf_", "ui_", "menu_", "week2_", "week3_")
    for prefix in prefixes:
        if low.startswith(prefix):
            return prefix.rstrip("_")
    return label.split("_", 1)[0]


def read_pages(package: Path, header: Path, array_name: str, page_count: int,
               depths: list[int]) -> tuple[list[bytes], list[list[int]]]:
    raw = package.read_bytes()
    pages, offsets = [], []
    offset = 0
    for depth in depths[:page_count]:
        size = 65536 if depth == 8 else 32768
        page = raw[offset:offset + size]
        if len(page) != size:
            raise ValueError(f"short page {len(page)} bytes in {package}")
        offsets.append(page)
        if depth == 8:
            pixels = list(page)
        else:
            pixels = [n for b in page for n in (b & 15, b >> 4)]
        pages.append(bytes(pixels))
        offset += size
    return offsets, [list(p) for p in pages]


def analyze_frames(rows: list[dict], page_pixels: list[list[int]], depths: list[int],
                   package_name: str) -> list[dict]:
    seen: dict[tuple[int, int, bytes], str] = {}
    out = []
    for f in rows:
        if f["page"] >= len(page_pixels):
            continue
        page = page_pixels[f["page"]]
        crop = bytearray()
        visible = []
        for y in range(f["v"], min(256, f["v"] + f["h"])):
            row = page[y * 256 + f["u"]:y * 256 + min(256, f["u"] + f["w"])]
            crop.extend(row)
            visible.extend((x, y) for x, val in enumerate(row) if val != 0)
        pix = bytes(crop)
        key = (depths[f["page"]], f["clut"], pix)
        prior = seen.get(key)
        if prior is None:
            seen[key] = f["label"]
        xs = [x for x, _ in visible]
        ys = [y for _, y in visible]
        if xs:
            local_min_x, local_max_x = min(xs), max(xs) + 1
            local_min_y, local_max_y = min(ys), max(ys) + 1
        else:
            local_min_x = local_max_x = local_min_y = local_max_y = 0
        out.append({
            "package": package_name, "group": groups(f["label"]), "label": f["label"],
            "bpp": depths[f["page"]], "page": f["page"], "clut": f["clut"],
            "uv_x": f["u"], "uv_y": f["v"], "uv_w": f["w"], "uv_h": f["h"],
            "rect_pixels": f["w"] * f["h"], "index0_pixels": f["w"] * f["h"] - sum(v != 0 for v in crop),
            "nonzero_bbox_x": local_min_x, "nonzero_bbox_y": local_min_y,
            "nonzero_bbox_w": local_max_x - local_min_x, "nonzero_bbox_h": local_max_y - local_min_y,
            "trim_x": f["trim_x"], "trim_y": f["trim_y"], "anchor": f["anchor"],
            "exact_indexed_duplicate_of": prior or "",
            "indexed_sha256": hashlib.sha256(pix).hexdigest(),
        })
    return out


def shelf_count(items: list[tuple[int, int, str]]) -> int:
    """Simple stable shelf-pack lower-bound experiment, not the runtime packer."""
    pages = 1 if items else 0
    x = y = row_h = 0
    for w, h, _ in sorted(items, key=lambda t: (-t[1], -t[0], t[2])):
        if w > 256 or h > 256:
            return -1
        if x + w > 256:
            x, y, row_h = 0, y + row_h, 0
        if y + h > 256:
            pages += 1
            x = y = row_h = 0
        x += w
        row_h = max(row_h, h)
    return pages


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-inventory", type=Path, required=True)
    ap.add_argument("--assets", type=Path, required=True)
    ap.add_argument("--build-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)

    with a.source_inventory.open(newline="", encoding="utf-8-sig") as f:
        source_rows = list(csv.DictReader(f))
    with (a.out_dir / "source-layer-fiches.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["group", "stage", "cameraZoom", "prop", "assetPath", "source_png",
                  "source_width", "source_height", "position", "scale", "scroll", "zIndex"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in source_rows:
            path = row.get("source_png", "")
            rel = path.split(":", 1)[0] if ":" in path else ""
            if rel.startswith("assets/"):
                rel = rel[len("assets/"):]
            dims = ("", "")
            if rel and rel.lower().endswith(".png"):
                dims = png_size(a.assets / rel.replace("/", "/"))
            w.writerow({**{k: row.get(k, "") for k in fields},
                        "source_width": dims[0], "source_height": dims[1]})

    jobs = [
        ("base-w1", "bopeebo_visual_data.h", "bopeebo_visual_frames", "week1-scene.bin", 11, [8]*9+[4]*2),
        ("week2", "bopeebo_visual_data.h", "bopeebo_visual_frames", "week2-scene.bin", 7, [8]*7),
        ("week3", "bopeebo_visual_data.h", "bopeebo_visual_frames", "week3-scene.bin", 8, [8]*8),
        ("week4", "week4_visual_data.h", "week4_visual_frames", "week4-scene.bin", 9, [8]*9),
        ("week5", "week5_visual_data.h", "week5_visual_frames", "week5-scene.bin", 12, [8]*12),
        # Week 6 may be losslessly repacked; use the page count recorded in its header.
        ("week6", "week6_visual_data.h", "week6_visual_frames", "week6-scene.bin", None, None),
        ("week7", "week7_visual_data.h", "week7_visual_frames", "week7-scene.bin", 4, [8]*4),
        ("weekend1", "weekend1_visual_data.h", "weekend1_visual_frames", "weekend1-scene.bin", 9, [8]*9),
    ]
    all_rows = []
    actual_counts = {}
    for name, header_name, array, package_name, count, depths in jobs:
        header = a.build_dir / header_name
        package = a.build_dir / package_name
        if count is None:
            text = header.read_text(encoding="utf-8")
            count_match = re.search(r"^#define\s+BOPEEBO_WEEK6_PAGE_COUNT\s+(\d+)u?\s*$", text, re.M)
            if not count_match:
                raise ValueError(f"missing Week 6 page count in {header}")
            count = int(count_match.group(1))
            depths = [8] * count
        actual_counts[name] = count
        if name == "base-w1":
            # Week1 package order is 9 8bpp pages, then two 4bpp pages.
            depths = [8] * 9 + [4] * 2
        pages_raw, pages = read_pages(package, header, array, count, depths)
        rows = frame_rows(header, array)
        if name == "base-w1":
            rows = [row for row in rows if not row["label"].startswith(("week2_", "week3_"))]
        elif name == "week2":
            rows = [row for row in rows if row["label"].startswith("week2_")]
        elif name == "week3":
            rows = [row for row in rows if row["label"].startswith("week3_")]
        all_rows.extend(analyze_frames(rows, pages, depths, name))

    fields = list(all_rows[0]) if all_rows else []
    with (a.out_dir / "converted-frame-fiches.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    # Quantify what exact duplicate aliases alone could recover. The sorted
    # shelf estimate ignores fixed page roles/slots, so it is only a packing
    # experiment; it is not claimed as a build/runtime saving.
    package_counts = {"base-w1": 11, "week2": 7, "week3": 8, "week4": 9,
                      "week5": 12, "week6": actual_counts["week6"], "week7": 4, "weekend1": 9}
    simulation = []
    for package in package_counts:
        prows = [r for r in all_rows if r["package"] == package]
        for bpp in (4, 8):
            candidates = [r for r in prows if int(r["bpp"]) == bpp]
            unique = {}
            for r in candidates:
                unique.setdefault((r["clut"], r["indexed_sha256"]), r)
            pages_dedup = shelf_count([(int(r["uv_w"]), int(r["uv_h"]), r["label"])
                                       for r in unique.values()])
            simulation.append({"package": package, "bpp": bpp,
                "currently_allocated_pages": (package_counts[package] if package != "base-w1" else (9 if bpp == 8 else 2)) if candidates else 0,
                "frames_in_source_header": len(candidates), "exact_unique_images": len(unique),
                "shelf_pages_after_exact_aliasing": pages_dedup,
                "note": "static shelf experiment; fixed runtime page roles and UV references not modeled"})
    with (a.out_dir / "dedup-pack-simulation.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(simulation[0]))
        w.writeheader()
        w.writerows(simulation)

    # Existing page audit includes W2 and the detailed W5 seven-field parser.
    # Keep its counts attached to this run rather than re-quantizing any page.
    audit = Path(a.source_inventory).parent / "atlases" / "atlas-audit.json"
    if audit.exists():
        data = json.loads(audit.read_text(encoding="utf-8"))
        (a.out_dir / "atlas-page-measures.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {len(source_rows)} source layer rows and {len(all_rows)} converted frame rows to {a.out_dir}")


if __name__ == "__main__":
    main()
