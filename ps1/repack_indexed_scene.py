#!/usr/bin/env python3
"""Losslessly repack one 8bpp indexed scene package without source conversion.

Pinned leading pages remain byte-identical. Remaining frame rectangles are
shelf-packed; exact duplicate indexed cels alias the first descriptor's UV
while all frame IDs remain present, so callers keep their original timings.
The package's trailing CLUT is copied byte-for-byte.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

PAGE = 256
PAGE_BYTES = PAGE * PAGE


def parse_frames(text: str, array: str) -> list[dict]:
    m = re.search(rf"static const [^;]+?\s+{re.escape(array)}\s*\[[^]]*\]\s*=\s*\{{(.*?)\n\}};", text, re.S)
    if not m:
        raise ValueError(f"frame array {array} not found")
    out = []
    for line in m.group(1).splitlines():
        row = re.search(r"\{([^{}]+)\}\s*,?\s*/\*\s*(.*?)\s*\*/", line)
        if not row:
            continue
        vals = [int(x.rstrip("uU"), 0) for x in re.findall(r"(?<![A-Za-z_])(?:0x[\da-fA-F]+|\d+)[uU]?", row.group(1))]
        if len(vals) != 5:
            raise ValueError(f"expected page,u,v,w,h for {row.group(2)}; got {vals}")
        page, u, v, w, h = vals
        if not (0 <= page and 0 <= u < PAGE and 0 <= v < PAGE and 0 < w <= PAGE and 0 < h <= PAGE and u + w <= PAGE and v + h <= PAGE):
            raise ValueError(f"source rectangle outside a page: {row.group(2)} {vals}")
        out.append(dict(label=row.group(2), page=page, u=u, v=v, w=w, h=h))
    return out


def pixels(page: bytes | bytearray, f: dict) -> bytes:
    return b"".join(page[(f["v"] + y) * PAGE + f["u"]:
                         (f["v"] + y) * PAGE + f["u"] + f["w"]]
                    for y in range(f["h"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-bin", type=Path, required=True)
    ap.add_argument("--input-header", type=Path, required=True)
    ap.add_argument("--output-bin", type=Path, required=True)
    ap.add_argument("--output-header", type=Path, required=True)
    ap.add_argument("--array", default="week6_visual_frames")
    ap.add_argument("--page-count-macro", default="BOPEEBO_WEEK6_PAGE_COUNT")
    ap.add_argument("--pin-pages", type=int, default=2)
    args = ap.parse_args()

    old_data = args.input_bin.read_bytes()
    old_header = args.input_header.read_text(encoding="ascii")
    count_m = re.search(rf"^#define\s+{re.escape(args.page_count_macro)}\s+(\d+)u?\s*$", old_header, re.M)
    if not count_m:
        raise ValueError(f"page-count macro {args.page_count_macro} not found")
    page_count = int(count_m.group(1))
    old_tex_bytes = page_count * PAGE_BYTES
    if len(old_data) != old_tex_bytes + 512:
        raise ValueError(f"expected {old_tex_bytes + 512} bytes for indexed pages plus CLUT; found {len(old_data)}")
    if not 0 <= args.pin_pages < page_count:
        raise ValueError("pin-pages must be in [0, page_count)")
    old_pages = [old_data[i * PAGE_BYTES:(i + 1) * PAGE_BYTES] for i in range(page_count)]
    source_frames = parse_frames(old_header, args.array)
    if any(f["page"] >= page_count for f in source_frames):
        raise ValueError("a descriptor references a missing source page")

    pinned_pages = [bytearray(p) for p in old_pages[:args.pin_pages]]
    pinned_frames = [f.copy() for f in source_frames if f["page"] < args.pin_pages]
    items = [f for f in source_frames if f["page"] >= args.pin_pages]
    pages: list[bytearray] = []
    placements: dict[str, tuple[int, int, int]] = {}
    exact: dict[bytes, tuple[bytes, int, int, int, str]] = {}
    aliases: dict[str, str] = {}
    x = y = row_h = local_page = 0

    # Descending-height shelves are deterministic and keep larger actor cels together.
    for f in sorted(items, key=lambda q: (-q["h"], -q["w"], q["label"])):
        data = pixels(old_pages[f["page"]], f)
        key = hashlib.sha256(data).digest()
        prior = exact.get(key)
        if prior and prior[0] == data:
            placements[f["label"]] = prior[1:4]
            aliases[f["label"]] = prior[4]
            continue
        if x + f["w"] > PAGE:
            x, y, row_h = 0, y + row_h, 0
        if y + f["h"] > PAGE:
            local_page += 1
            x = y = row_h = 0
        while len(pages) <= local_page:
            pages.append(bytearray(PAGE_BYTES))
        page_index = args.pin_pages + local_page
        page = pages[local_page]
        for dy in range(f["h"]):
            page[(y + dy) * PAGE + x:(y + dy) * PAGE + x + f["w"]] = data[dy * f["w"]:(dy + 1) * f["w"]]
        placements[f["label"]] = (page_index, x, y)
        exact[key] = (data, page_index, x, y, f["label"])
        x += f["w"]
        row_h = max(row_h, f["h"])

    final_pages = pinned_pages + pages
    if len(final_pages) >= page_count:
        raise ValueError(f"no demonstrated page reduction ({page_count} -> {len(final_pages)}); no output written")
    final_frames = []
    for old in source_frames:
        f = old.copy()
        if f["label"] in placements:
            f["page"], f["u"], f["v"] = placements[f["label"]]
        final_frames.append(f)

    # Verify all indexed pixels before writing any artifacts.
    for old, new in zip(source_frames, final_frames):
        if pixels(old_pages[old["page"]], old) != pixels(final_pages[new["page"]], new):
            raise ValueError(f"indexed pixels changed for {old['label']}")

    arr_re = re.compile(rf"(static const [^;]+?\s+{re.escape(args.array)}\s*\[[^]]*\]\s*=\s*\{{)(.*?)(\n\}};)", re.S)
    match = arr_re.search(old_header)
    if not match:
        raise ValueError("could not find descriptor array for update")
    body = "\n" + "\n".join(f"\t{{ {f['page']}u, {f['u']}u, {f['v']}u, {f['w']}u, {f['h']}u }}, /* {f['label']} */" for f in final_frames)
    new_header = old_header[:match.start()] + match.group(1) + body + match.group(3) + old_header[match.end():]
    new_header, n = re.subn(rf"(^#define\s+{re.escape(args.page_count_macro)}\s+)\d+u?\s*$",
                            rf"\g<1>{len(final_pages)}u", new_header, count=1, flags=re.M)
    if n != 1:
        raise ValueError("failed to update page count")

    args.output_bin.parent.mkdir(parents=True, exist_ok=True)
    args.output_header.parent.mkdir(parents=True, exist_ok=True)
    new_data = b"".join(final_pages) + old_data[old_tex_bytes:]
    args.output_bin.write_bytes(new_data)
    args.output_header.write_text(new_header, encoding="ascii", newline="\n")
    # Independent read-back verifies the paired palette and descriptors.
    read_header = args.output_header.read_text(encoding="ascii")
    read_frames = parse_frames(read_header, args.array)
    read_data = args.output_bin.read_bytes()
    if read_data[len(final_pages) * PAGE_BYTES:] != old_data[old_tex_bytes:]:
        raise ValueError("CLUT changed during repack")
    read_pages = [read_data[i * PAGE_BYTES:(i + 1) * PAGE_BYTES] for i in range(len(final_pages))]
    for old, new in zip(source_frames, read_frames):
        if pixels(old_pages[old["page"]], old) != pixels(read_pages[new["page"]], new):
            raise ValueError(f"read-back mismatch for {old['label']}")
    print(f"Lossless repack verified: {page_count}->{len(final_pages)} 8bpp pages; "
          f"{len(aliases)} exact duplicate cels aliased; {len(final_frames)} descriptors/timings retained; "
          "512-byte CLUT identical")


if __name__ == "__main__":
    main()
