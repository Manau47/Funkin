#!/usr/bin/env python3
"""Losslessly repack converted 8bpp week atlas frames into fewer 256x256 pages.

The input package and generated header are read-only. Frame texels and the
trailing 256-entry RGB555 CLUT are copied byte-for-byte; only page/UV metadata
changes. Scene frames whose label starts with STAGE_ remain in pages 0 and 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_frames(text: str, type_name: str, array_name: str) -> tuple[str, list[dict]]:
    m = re.search(rf"static const {re.escape(type_name)}\s+{re.escape(array_name)}\s*\[[^]]*\]\s*=\s*\{{(.*?)\n\}};", text, re.S)
    if not m:
        raise ValueError(f"Could not find {array_name}")
    body = m.group(1)
    rows = []
    for match in re.finditer(r"(?m)^\s*\{([^{}]+)\}\s*,?\s*(/\*.*?\*/)?\s*$", body):
        raw_values = re.findall(r"(?<![A-Za-z_])(?:0x[\da-fA-F]+|\d+)[uU]?", match.group(1))
        values = [int(v.rstrip("uU"), 0) for v in raw_values]
        if len(values) != 5:
            raise ValueError(f"Expected five frame fields; got {len(values)} in: {match.group(0)}")
        comment = match.group(2) or ""
        label_m = re.search(r"/\*\s*(.*?)\s*\*/", comment)
        rows.append({"values": values, "label": label_m.group(1) if label_m else f"frame_{len(rows)}"})
    if not rows:
        raise ValueError(f"No frame rows found in {array_name}")
    return body, rows


def maxrects(rects: list[dict], max_pages: int = 16) -> tuple[list[list[dict]], list[dict]]:
    # Best-short-side-fit with free-rectangle splitting; no rotation, no
    # padding, and no palette/index changes.
    pages: list[list[dict]] = []
    free_by_page: list[list[tuple[int,int,int,int]]] = []
    pending = sorted(rects, key=lambda r: (-max(r["w"],r["h"]), -(r["w"]*r["h"]), r["label"]))
    placements = []
    for r in pending:
        best = None
        for pi, free_list in enumerate(free_by_page):
            for fi, (fx,fy,fw,fh) in enumerate(free_list):
                if r["w"] <= fw and r["h"] <= fh:
                    dw, dh = fw-r["w"], fh-r["h"]
                    score = (min(dw,dh), max(dw,dh), pi, fy, fx, fi)
                    if best is None or score < best[0]: best = (score,pi,fi,fx,fy)
        if best is None:
            if len(pages) >= max_pages:
                raise ValueError("MaxRects page limit exceeded")
            pages.append([]); free_by_page.append([(0,0,256,256)])
            pi, fi, fx, fy = len(pages)-1, 0, 0, 0
        else:
            _,pi,fi,fx,fy = best
        placed = dict(r, page=pi+2, u=fx, v=fy)
        pages[pi].append(placed); placements.append(placed)
        used = (fx,fy,r["w"],r["h"])
        new_free = []
        for free in free_by_page[pi]:
            ax,ay,aw,ah = free; ux,uy,uw,uh = used
            if ux >= ax+aw or ux+uw <= ax or uy >= ay+ah or uy+uh <= ay:
                new_free.append(free); continue
            if ux > ax: new_free.append((ax,ay,ux-ax,ah))
            if ux+uw < ax+aw: new_free.append((ux+uw,ay,ax+aw-(ux+uw),ah))
            if uy > ay: new_free.append((ax,ay,aw,uy-ay))
            if uy+uh < ay+ah: new_free.append((ax,uy+uh,aw,ay+ah-(uy+uh)))
        pruned = []
        for i,a in enumerate(new_free):
            ax,ay,aw,ah=a
            if aw <= 0 or ah <= 0: continue
            contained=False
            for j,b in enumerate(new_free):
                if i==j: continue
                bx,by,bw,bh=b
                if ax>=bx and ay>=by and ax+aw<=bx+bw and ay+ah<=by+bh:
                    contained=True; break
            if not contained and a not in pruned: pruned.append(a)
        free_by_page[pi] = pruned
    return pages, placements


def crop_page(page: bytes, u: int, v: int, w: int, h: int) -> bytes:
    return b"".join(page[(v+y)*256+u:(v+y)*256+u+w] for y in range(h))


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--week", choices=("4","7"), required=True)
    ap.add_argument("--header", type=Path, required=True)
    ap.add_argument("--package", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args=ap.parse_args()
    n=int(args.week)
    text=args.header.read_text(encoding="utf-8")
    macro=f"BOPEEBO_WEEK{n}_PAGE_COUNT"
    cm=re.search(rf"(?m)^#define\s+{macro}\s+(\d+)u\s*$",text)
    if not cm: raise ValueError(f"Missing {macro}")
    old_count=int(cm.group(1))
    type_name,array_name=(f"Week{n}VisualFrame",f"week{n}_visual_frames")
    frame_body,frames=parse_frames(text,type_name,array_name)
    raw=args.package.read_bytes()
    if len(raw)!=old_count*65536+512:
        raise ValueError(f"Expected {old_count*65536+512} bytes, got {len(raw)}")
    source_pages=[raw[i*65536:(i+1)*65536] for i in range(old_count)]
    palette=raw[old_count*65536:]
    stage=[f for f in frames if f["label"].upper().startswith("STAGE_")]
    moving=[f for f in frames if f not in stage]
    if len(stage)!=2 or any(f["values"][0] not in (0,1) for f in stage):
        raise ValueError("Expected exactly two stage frames in package pages 0 and 1")
    rects=[]
    for f in moving:
        page,u,v,w,h=f["values"]
        if page<2 or page>=old_count or w<=0 or h<=0 or u+w>256 or v+h>256:
            raise ValueError(f"Invalid original frame rectangle {f['label']}: {f['values']}")
        rects.append({"label":f["label"],"old_page":page,"old_u":u,"old_v":v,"w":w,"h":h})
    packed,placements=maxrects(rects)
    page_count=2+len(packed)
    new_pages=[source_pages[0],source_pages[1]]+[bytearray(65536) for _ in packed]
    placement_by_label={p["label"]:p for p in placements}
    frame_hashes=[]
    for r in rects:
        p=placement_by_label[r["label"]]
        before=crop_page(source_pages[r["old_page"]],r["old_u"],r["old_v"],r["w"],r["h"])
        dst=new_pages[p["page"]]
        for y in range(r["h"]):
            src=(r["old_v"]+y)*256+r["old_u"]
            target=(p["v"]+y)*256+p["u"]
            dst[target:target+r["w"]]=before[y*r["w"]:(y+1)*r["w"]]
        after=crop_page(bytes(dst),p["u"],p["v"],r["w"],r["h"])
        if before!=after: raise AssertionError(f"Texel mismatch: {r['label']}")
        frame_hashes.append({"frame":r["label"],"bytes":len(before),"sha256_before":sha(before),"sha256_after":sha(after),"equal":True})
    # Regenerate only the frame initializer body, retaining enum and comments.
    row_iter=iter(frames)
    new_rows=[]
    for f in frames:
        old=f["values"]
        if f in moving:
            p=placement_by_label[f["label"]]
            vals=[p["page"],p["u"],p["v"],old[3],old[4]]
        else:
            vals=old
        comment=f" /* {f['label']} */" if f["label"].startswith("frame_") else f" /* {f['label']} */"
        new_rows.append("\t{ %u, %u, %u, %u, %u },%s" % (*vals,comment))
    new_body="\n"+"\n".join(new_rows)+"\n"
    text=text.replace(frame_body,new_body)
    text=re.sub(rf"(?m)(^#define\s+{macro}\s+)\d+u\s*$",rf"\g<1>{page_count}u",text)
    out=args.out_dir
    out_header=out/args.header.name; out_package=out/args.package.name
    out_report=out/f"week{n}-repack-report.json"
    if any(path.exists() for path in (out_header,out_package,out_report)):
        raise FileExistsError(f"Refusing to overwrite existing repack outputs in {out}; choose a new output directory")
    out.mkdir(parents=True,exist_ok=True)
    out_header.write_text(text,encoding="utf-8",newline="")
    out_package.write_bytes(b"".join(bytes(p) for p in new_pages)+palette)
    report={"week":n,"input_header":str(args.header),"input_package":str(args.package),
      "input_pages":old_count,"output_pages":page_count,"repacked_pages":len(packed),
      "input_bytes":len(raw),"output_bytes":out_package.stat().st_size,
      "package_bytes_saved":len(raw)-out_package.stat().st_size,
      "input_sha256":sha(raw),"output_sha256":sha(out_package.read_bytes()),
      "palette_sha256_before":sha(palette),"palette_sha256_after":sha(out_package.read_bytes()[-512:]),
      "stage_pages_byte_identical":all(source_pages[i]==new_pages[i] for i in (0,1)),
      "frames_verified":len(frame_hashes),"frame_texels_identical":all(x["equal"] for x in frame_hashes),
      "placements":[{"frame":p["label"],"page":p["page"],"u":p["u"],"v":p["v"],"w":p["w"],"h":p["h"]} for p in placements],
      "frame_hashes":frame_hashes}
    out_report.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("placements","frame_hashes")},indent=2))


if __name__=="__main__": main()

