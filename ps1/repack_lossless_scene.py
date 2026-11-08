#!/usr/bin/env python3
"""Losslessly alias duplicate indexed cels and repack a week package.

This operates only on existing 8bpp BIN/header pairs; it does not reconvert
source art. The first two full-page stage layers stay pinned. All frame IDs,
durations, dimensions, palettes, and opaque texels are preserved. Supports the
simple five-field week headers and the combined Bopeebo visual header.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from repack_indexed_week_atlas import maxrects

PAGE = 256
PAGE_BYTES = PAGE * PAGE


def crop(page: bytes | bytearray, u: int, v: int, w: int, h: int) -> bytes:
    return b"".join(page[(v+y)*PAGE+u:(v+y)*PAGE+u+w] for y in range(h))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-bin", type=Path, required=True)
    ap.add_argument("--input-header", type=Path, required=True)
    ap.add_argument("--output-bin", type=Path, required=True)
    ap.add_argument("--output-header", type=Path, required=True)
    ap.add_argument("--array", required=True)
    ap.add_argument("--page-count-macro", required=True)
    ap.add_argument("--pin-pages", type=int, default=2)
    ap.add_argument("--format", choices=("simple", "bopeebo"), default="simple")
    ap.add_argument("--label-prefix", default="")
    ap.add_argument("--slot-array", default="")
    args = ap.parse_args()

    if any(p.exists() for p in (args.output_bin, args.output_header)):
        raise FileExistsError("Refusing to overwrite existing repack outputs")
    header = args.input_header.read_text(encoding="ascii")
    raw = args.input_bin.read_bytes()
    count_m = re.search(rf"(?m)^#define\s+{re.escape(args.page_count_macro)}\s+(\d+)u?\s*$", header)
    if not count_m:
        raise ValueError(f"Missing page-count macro {args.page_count_macro}")
    old_count = int(count_m.group(1))
    if len(raw) != old_count * PAGE_BYTES + 512:
        raise ValueError(f"Expected {old_count * PAGE_BYTES + 512} bytes, received {len(raw)}")
    old_pages = [raw[i*PAGE_BYTES:(i+1)*PAGE_BYTES] for i in range(old_count)]
    arr = re.compile(rf"(static const [^;]+?\s+{re.escape(args.array)}\s*\[[^]]*\]\s*=\s*\{{)(.*?)(\n\}};)", re.S)
    match = arr.search(header)
    if not match:
        raise ValueError(f"Missing frame array {args.array}")
    lines = match.group(2).splitlines()
    frame_rows = []
    page_i, u_i, v_i, w_i, h_i = (0,1,2,3,4) if args.format == "simple" else (0,2,3,4,5)
    for line in lines:
        row = re.search(r"\{([^{}]+)\}\s*,?\s*/\*\s*(.*?)\s*\*/", line)
        if not row:
            frame_rows.append({"line": line, "label": None})
            continue
        vals = [int(x.rstrip("uU"), 0) for x in re.findall(r"(?<![A-Za-z_])-?(?:0x[\da-fA-F]+|\d+)[uU]?", row.group(1))]
        label = row.group(2)
        frame_rows.append({"line": line, "label": label, "vals": vals, "row": row.group(0)})
    target = [f for f in frame_rows if f.get("label") and f["label"].startswith(args.label_prefix)]
    if not target:
        raise ValueError(f"No frames matched prefix {args.label_prefix!r}")
    for f in target:
        vals = f["vals"]
        if len(vals) <= max(page_i,u_i,v_i,w_i,h_i):
            raise ValueError(f"Unexpected descriptor shape for {f['label']}: {vals}")
        page,u,v,w,h=(vals[page_i],vals[u_i],vals[v_i],vals[w_i],vals[h_i])
        if w == 0 or h == 0:
            continue  # retain explicitly unused sentinel frames unchanged
        if page >= old_count or u+w > PAGE or v+h > PAGE:
            raise ValueError(f"Invalid source rectangle {f['label']}: {vals}")

    items = [f for f in target if f["vals"][w_i] and f["vals"][h_i] and f["vals"][page_i] >= args.pin_pages]
    unique: dict[bytes, dict] = {}
    alias_key: dict[str, bytes] = {}
    payload_by_key: dict[bytes, bytes] = {}
    for f in items:
        vals=f["vals"]; data=crop(old_pages[vals[page_i]],vals[u_i],vals[v_i],vals[w_i],vals[h_i])
        digest=hashlib.sha256(data).digest()
        key=digest
        if key in payload_by_key and payload_by_key[key] != data:
            key=hashlib.sha256(data+b"\x00"+f["label"].encode()).digest()
        unique.setdefault(key,{"label":f["label"],"w":vals[w_i],"h":vals[h_i]})
        payload_by_key[key]=data
        alias_key[f["label"]]=key
    packed, placements = maxrects(list(unique.values()))
    placement_by_label={p["label"]:p for p in placements}
    final_pages=[bytearray(p) for p in old_pages[:args.pin_pages]]+[bytearray(PAGE_BYTES) for _ in packed]
    for key,item in unique.items():
        p=placement_by_label[item["label"]]; data=payload_by_key[key]
        dst=final_pages[p["page"]]
        for y in range(item["h"]):
            dst[(p["v"]+y)*PAGE+p["u"]:(p["v"]+y)*PAGE+p["u"]+item["w"]] = data[y*item["w"]:(y+1)*item["w"]]

    frame_updates={}
    for f in target:
        vals=f.get("vals")
        if not vals or vals[w_i] == 0 or vals[h_i] == 0:
            continue
        page,u,v,w,h=vals[page_i],vals[u_i],vals[v_i],vals[w_i],vals[h_i]
        if page < args.pin_pages:
            continue
        item=unique[alias_key[f["label"]]]
        p=placement_by_label[item["label"]]
        expected=crop(old_pages[page],u,v,w,h)
        actual=crop(final_pages[p["page"]],p["u"],p["v"],w,h)
        if expected != actual:
            raise AssertionError(f"Indexed pixels changed: {f['label']}")
        new=vals.copy(); new[page_i],new[u_i],new[v_i]=p["page"],p["u"],p["v"]
        frame_updates[f["label"]]=new

    new_lines=[]
    for f in frame_rows:
        if f.get("label") not in frame_updates:
            new_lines.append(f["line"]); continue
        vals=frame_updates[f["label"]]
        indent=re.match(r"^\s*",f["line"]).group(0)
        row=re.search(r"\{([^{}]+)\}\s*,?\s*/\*\s*(.*?)\s*\*/", f["line"])
        fields=[v.strip() for v in row.group(1).split(",")]
        for index in (page_i,u_i,v_i): fields[index]=f"{vals[index]}u"
        new_lines.append(f"{indent}{{ {', '.join(fields)} }}, /* {f['label']} */")
    body="\n"+"\n".join(new_lines)
    new_header=header[:match.start()]+match.group(1)+body+match.group(3)+header[match.end():]
    new_count=len(final_pages)
    new_header,n=re.subn(rf"(?m)(^#define\s+{re.escape(args.page_count_macro)}\s+)\d+u?\s*$",rf"\g<1>{new_count}u",new_header,count=1)
    if n!=1: raise ValueError("Failed to update page count")
    if args.slot_array:
        slots=re.compile(rf"(?m)^static const uint8_t {re.escape(args.slot_array)}\[[^]]*\]\s*=\s*\{{[^}}]*\}};")
        new_header,n=slots.subn(f"static const uint8_t {args.slot_array}[{new_count}] = {{"+",".join(map(str,range(new_count)))+"};",new_header,count=1)
        if n!=1: raise ValueError(f"Failed to update slot table {args.slot_array}")
    if new_count >= old_count:
        raise ValueError(f"No page reduction ({old_count} -> {new_count}); outputs not written")

    args.output_bin.parent.mkdir(parents=True,exist_ok=True); args.output_header.parent.mkdir(parents=True,exist_ok=True)
    out_data=b"".join(bytes(p) for p in final_pages)+raw[old_count*PAGE_BYTES:]
    args.output_bin.write_bytes(out_data); args.output_header.write_text(new_header,encoding="ascii",newline="\n")
    if out_data[new_count*PAGE_BYTES:]!=raw[old_count*PAGE_BYTES:]: raise AssertionError("CLUT changed")
    report={"old_pages":old_count,"new_pages":new_count,"fixed_stage_pages":args.pin_pages,"target_frames":len(target),"repacked_unique_cels":len(unique),"aliased_exact_duplicates":len(items)-len(unique),"old_bytes":len(raw),"new_bytes":len(out_data),"saved_bytes":len(raw)-len(out_data),"clut_sha256":hashlib.sha256(raw[-512:]).hexdigest(),"clut_preserved":out_data[-512:]==raw[-512:],"all_target_pixels_verified":True}
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
