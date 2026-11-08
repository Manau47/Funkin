#!/usr/bin/env python3
"""Add sampled official idle/singing/dance frames to cached PS1 scene packs.

This is a post-conversion step: it reuses each package's existing 8bpp CLUT,
adds only bounded 64x64/64x80 cel pages, and does not touch charts or audio.
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from animate_preview import Rig  # noqa: E402
from convert_bopeebo_visuals import (  # noqa: E402
    extract_sparrow_frame, fit_anchored_rig, quantize,
)

PAGE = 256
PAGE_BYTES = PAGE * PAGE


def palette_from_scene(scene: bytes) -> list[tuple[int, int, int]]:
    words = struct.unpack_from("<256H", scene, len(scene) - 512)
    if words[0] != 0:
        raise ValueError("expected transparent CLUT entry at index zero")
    out = []
    for word in words[1:]:
        out.append(tuple((((word >> shift) & 31) << 3) | (((word >> shift) & 31) >> 2)
                         for shift in (0, 5, 10)))
    return out


def blit(page: bytearray, x: int, y: int, width: int, height: int,
         rgba: bytearray, palette: list[tuple[int, int, int]]) -> None:
    if len(rgba) < width * height * 4 or x + width > PAGE or y + height > PAGE:
        raise ValueError(f"invalid cel extent {x},{y} {width}x{height}, rgba={len(rgba)}")
    rgba = rgba[:width * height * 4]
    indexed = quantize(rgba, palette)
    for row in range(height):
        dst = (y + row) * PAGE + x
        page[dst:dst + width] = indexed[row * width:(row + 1) * width]


def xml_frames(path: pathlib.Path, prefix: str) -> list[dict]:
    matches = []
    for n in ET.parse(path).getroot().findall("SubTexture"):
        if not n.attrib.get("name", "").startswith(prefix):
            continue
        f = {k: int(n.attrib.get(k, 0)) for k in
             ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
        f["rotated"] = n.attrib.get("rotated", "false").lower() == "true"
        f["name"] = n.attrib["name"]
        if (f["x"], f["y"], f["width"], f["height"]) not in {
                (v["x"], v["y"], v["width"], v["height"]) for v in matches}:
            matches.append(f)
    if not matches:
        raise ValueError(f"no official frames for {prefix!r} in {path}")
    return matches


def put_frames(directory: pathlib.Path, scene_name: str, header_name: str,
               prefix: str, frames: list[tuple[str, bytearray, int, int]],
               expected_pages: int, slots_per_page: int = 16) -> None:
    scene_path, header_path = directory / scene_name, directory / header_name
    scene = scene_path.read_bytes()
    if len(scene) != expected_pages * PAGE_BYTES + 512:
        raise ValueError(f"{scene_path} has unexpected size {len(scene)}")
    header = header_path.read_text(encoding="ascii")
    if f"{prefix}_V143_" in header:
        raise ValueError(f"{header_path} already contains v143 frames")
    palette = palette_from_scene(scene)
    page_count = (len(frames) + slots_per_page - 1) // slots_per_page
    pages = [bytearray(PAGE_BYTES) for _ in range(page_count)]
    descriptors: list[tuple[str, int, int, int, int, int]] = []
    for i, (name, rgba, width, height) in enumerate(frames):
        page_i, cell = divmod(i, slots_per_page)
        cols = PAGE // width
        x, y = (cell % cols) * width, (cell // cols) * height
        if y + height > PAGE:
            raise ValueError(f"too many {width}x{height} frames for a page")
        blit(pages[page_i], x, y, width, height, rgba, palette)
        descriptors.append((name, expected_pages + page_i, x, y, width, height))
    scene_path.write_bytes(scene[:-512] + b"".join(pages) + scene[-512:])

    enum_end = header.find("\n};", header.find("enum {"))
    table_start = header.find("static const", enum_end)
    table_end = header.find("\n};", table_start)
    count_line = next((line for line in header.splitlines()
                       if line.startswith(f"#define {prefix}_VISUAL_FRAME_COUNT ")), None)
    page_line = f"#define BOPEEBO_{prefix}_PAGE_COUNT {expected_pages}u"
    if min(enum_end, table_start, table_end) < 0 or not count_line or page_line not in header:
        raise ValueError(f"unexpected generated header shape: {header_path}")
    count = int(count_line.rsplit(" ", 1)[1].removesuffix("u"))
    enum_text = "\n" + "\n".join(f"\t{prefix}_FRAME_{name} = {count + i},"
                                      for i, (name, *_rest) in enumerate(frames))
    header = header[:enum_end] + enum_text + header[enum_end:]
    table_start = header.find("static const", header.find("enum {"))
    table_end = header.find("\n};", table_start)
    desc_text = "\n" + "\n".join(
        f"\t{{ {p}u, {x}u, {y}u, {w}u, {h}u }}, /* {name} */"
        for name, p, x, y, w, h in descriptors)
    header = header[:table_end] + desc_text + header[table_end:]
    header = header.replace(count_line, f"#define {prefix}_VISUAL_FRAME_COUNT {count + len(frames)}u", 1)
    header = header.replace(page_line, f"#define BOPEEBO_{prefix}_PAGE_COUNT {expected_pages + page_count}u", 1)
    header_path.write_text(header, encoding="ascii")
    print(f"{prefix}: +{len(frames)} frames, +{page_count} page(s), scene={scene_path.stat().st_size} bytes")


def rig_cels(rig: Rig, base_ids: list[int], extra_ids: list[int], width=64, height=64):
    all_ids = list(dict.fromkeys(base_ids + extra_ids))
    rendered = fit_anchored_rig(rig, all_ids, width, height, anchor_frame_ids=base_ids)
    return {i: rendered[i] for i in extra_ids}


def week4(args):
    assets, ffmpeg, directory = args.assets, args.ffmpeg, args.week4
    mom = Rig(assets / "shared/images/characters/momCar", ffmpeg)
    gf = Rig(assets / "shared/images/characters/gfCar", ffmpeg)
    mom_base = [46, 37, 23, 0, 14]
    # Sample the pinned root timeline at intermediate points. These indices
    # are inside its official 0-14/14-23/23-37/37-46/46-59 action spans.
    # Keep every Mom cel in the same 72x84 anchored box as the original cels.
    mom_extra = [50, 55, 40, 43, 28, 33, 5, 10, 17, 20]
    mom_pixels = rig_cels(mom, mom_base, mom_extra, 72, 84)
    dance_ids = list(range(0, 30, 3))
    gf_pixels = fit_anchored_rig(gf, dance_ids, 64, 64, anchor_frame_ids=[0, 15])
    gf_extra_ids = [source for source in dance_ids if source not in (0, 15)]
    extras = [(f"GF_DANCE_V143_{i}", gf_pixels[source], 64, 64)
              for i, source in enumerate(gf_extra_ids)]
    put_frames(directory, "week4-scene.bin", "week4_visual_data.h", "WEEK4", extras, 3)

    mom_names = [
        "MOM_IDLE_1", "MOM_IDLE_2",
        "MOM_LEFT_ALT_1", "MOM_LEFT_ALT_2",
        "MOM_DOWN_ALT_1", "MOM_DOWN_ALT_2",
        "MOM_UP_ALT_1", "MOM_UP_ALT_2",
        "MOM_RIGHT_ALT_1", "MOM_RIGHT_ALT_2",
    ]
    mom_extras = [(name, mom_pixels[source], 72, 84)
                  for name, source in zip(mom_names, mom_extra)]
    # Nine 72x84 cels fit in a 3x3 grid on one page; the tenth uses one
    # cel on a second page. These remain separate from GF's 64x64 dance page.
    put_frames(directory, "week4-scene.bin", "week4_visual_data.h", "WEEK4",
               mom_extras, 4, slots_per_page=9)


def week5(args):
    assets, ffmpeg, directory = args.assets, args.ffmpeg, args.week5
    gf = Rig(assets / "shared/images/characters/gf-christmas", ffmpeg)
    gf_ids = [0, 3, 6, 9, 12, 14, 17, 20, 23, 27]
    gf_pixels = fit_anchored_rig(gf, gf_ids, 64, 64, anchor_frame_ids=[0, 14])
    gf_extra_ids = [src for src in gf_ids if src not in (0, 14)]
    extras = [(f"GF_DANCE_V143_{i}", gf_pixels[src], 64, 64)
              for i, src in enumerate(gf_extra_ids)]
    parents = Rig(assets / "shared/images/characters/parents-christmas", ffmpeg)
    parent_bases = [112, 0, 28, 54, 83, 14, 41, 68, 97]
    parent_mid = [116, 7, 34, 61, 89, 21, 47, 75, 102]
    p = rig_cels(parents, parent_bases, parent_mid)
    p_names = ["PARENTS_IDLE_1", "PARENTS_MOM_DOWN_ALT", "PARENTS_MOM_UP_ALT",
               "PARENTS_MOM_RIGHT_ALT", "PARENTS_MOM_LEFT_ALT", "PARENTS_DAD_DOWN_ALT",
               "PARENTS_DAD_UP_ALT", "PARENTS_DAD_RIGHT_ALT", "PARENTS_DAD_LEFT_ALT"]
    extras += [(name, p[src], 64, 64) for name, src in zip(p_names, parent_mid)]
    monster = Rig(assets / "shared/images/characters/monster", ffmpeg)
    m_ids = [8, 12, 20, 30, 42, 54]
    m = rig_cels(monster, [0, 16, 26, 36, 48], m_ids)
    extras += [(name, m[src], 64, 64) for name, src in zip(
        ["MONSTER_IDLE_1", "MONSTER_IDLE_2", "MONSTER_RIGHT_ALT", "MONSTER_LEFT_ALT",
         "MONSTER_UP_ALT", "MONSTER_DOWN_ALT"], m_ids)]
    # The current Week 5 base extractor emits two animated mall-crowd pages
    # after its three original stage/character pages.
    put_frames(directory, "week5-scene.bin", "week5_visual_data.h", "WEEK5", extras, 5)


def week6(args):
    assets, ffmpeg, directory = args.assets, args.ffmpeg, args.week6
    gf_png, gf_xml = assets / "shared/images/characters/gfPixel.png", assets / "shared/images/characters/gfPixel.xml"
    gf = xml_frames(gf_xml, "GF IDLE")
    # Preserve the existing poses at entries 0 and 15 and sample distinct in-between cels.
    gf_samples = [gf[min(i, len(gf)-1)] for i in [3, 6, 9, 12, 18, 21, 24, 27]]
    extras = [(f"GF_DANCE_{i+2}", extract_sparrow_frame(ffmpeg, gf_png, node, (64, 64)), 64, 64)
              for i, node in enumerate(gf_samples)]
    senpai_png, senpai_xml = assets / "shared/images/characters/senpai.png", assets / "shared/images/characters/senpai.xml"
    for prefix, label in (("Senpai Idle instance 10", "SENPAI_IDLE_ALT"),
                          ("Angry Senpai Idle instance 10", "ANGRY_IDLE_ALT")):
        nodes = xml_frames(senpai_xml, prefix)
        extras.append((label, extract_sparrow_frame(ffmpeg, senpai_png, nodes[-1], (64, 64)), 64, 64))
    for prefix, name in (("SENPAI LEFT NOTE instance 10", "SENPAI_LEFT_ALT"),
                         ("SENPAI DOWN NOTE instance 10", "SENPAI_DOWN_ALT"),
                         ("SENPAI UP NOTE instance 10", "SENPAI_UP_ALT"),
                         ("SENPAI RIGHT NOTE instance 10", "SENPAI_RIGHT_ALT"),
                         ("Angry Senpai LEFT NOTE instance 10", "ANGRY_LEFT_ALT"),
                         ("Angry Senpai DOWN NOTE instance 10", "ANGRY_DOWN_ALT"),
                         ("Angry Senpai UP NOTE instance 10", "ANGRY_UP_ALT"),
                         ("Angry Senpai RIGHT NOTE instance 10", "ANGRY_RIGHT_ALT")):
        nodes = xml_frames(senpai_xml, prefix)
        extras.append((name, extract_sparrow_frame(ffmpeg, senpai_png, nodes[-1], (64, 64)), 64, 64))
    put_frames(directory, "week6-scene.bin", "week6_visual_data.h", "WEEK6", extras, 5)


def week7(args):
    assets, ffmpeg, directory = args.assets, args.ffmpeg, args.week7
    gf_base = assets / "shared/images/characters/gfTankmen"
    gf_nodes = {int(n.attrib["name"][-4:]): n for n in ET.parse(gf_base.with_suffix(".xml")).getroot().findall("SubTexture")
                if n.attrib.get("name", "").startswith("GF Dancing at Gunpoint")}
    gf_schedule = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27]
    extras = []
    extra_index = 0
    for pose_index, source in enumerate(gf_schedule):
        if source in (0, 15):
            continue
        n = gf_nodes[source]
        f = {k: int(n.attrib.get(k, 0)) for k in ("x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight")}
        f.update({"rotated": n.attrib.get("rotated", "false").lower() == "true", "name": n.attrib["name"]})
        extras.append((f"GF_DANCE_V143_{extra_index}", extract_sparrow_frame(ffmpeg, gf_base.with_suffix(".png"), f, (64, 64)), 64, 64))
        extra_index += 1
    tank = Rig(assets / "shared/images/characters/tankman/basic", ffmpeg)
    tank_bases = [0, 25, 30, 20, 14]
    tank_extra = [7, 12, 27, 32, 22, 16]
    fitted = rig_cels(tank, tank_bases, tank_extra)
    extras += [(name, fitted[src], 64, 64) for name, src in zip(
        ["TANK_IDLE_1", "TANK_IDLE_2", "TANK_LEFT_ALT", "TANK_DOWN_ALT", "TANK_UP_ALT", "TANK_RIGHT_ALT"],
        tank_extra)]
    put_frames(directory, "week7-scene.bin", "week7_visual_data.h", "WEEK7", extras, 4)


def weekend1(args):
    assets, ffmpeg, directory = args.assets, args.ffmpeg, args.weekend1
    specs = []
    pico = Rig(assets / "shared/images/characters/pico/basic-animations", ffmpeg)
    pico_base = [0, 14, 62, 48, 31]
    pico_extra = [7, 11, 26, 30, 59, 73]
    pp = rig_cels(pico, pico_base, pico_extra, 64, 80)
    specs += [(name, pp[src], 64, 80) for name, src in zip(
        ["PICO_IDLE_1", "PICO_IDLE_2", "PICO_LEFT_END", "PICO_DOWN_END", "PICO_UP_END", "PICO_RIGHT_END"],
        pico_extra)]
    darnell = Rig(assets / "shared/images/characters/darnell", ffmpeg)
    darnell_base = [0, 14, 26, 38, 50]
    darnell_extra = [6, 11, 22, 34, 46, 58]
    dp = rig_cels(darnell, darnell_base, darnell_extra, 64, 80)
    specs += [(name, dp[src], 64, 80) for name, src in zip(
        ["DARNELL_IDLE_1", "DARNELL_IDLE_2", "DARNELL_LEFT_ALT", "DARNELL_DOWN_ALT",
         "DARNELL_RIGHT_ALT", "DARNELL_UP_ALT"], darnell_extra)]
    put_frames(directory, "weekend1-scene.bin", "weekend1_visual_data.h", "WEEKEND1", specs, 8, 12)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", type=pathlib.Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    for week in ("week4", "week5", "week6", "week7", "weekend1"):
        ap.add_argument(f"--{week}", type=pathlib.Path, required=True)
    args = ap.parse_args()
    if not args.assets.is_dir() or not pathlib.Path(args.ffmpeg).is_file():
        raise FileNotFoundError("official asset checkout or FFmpeg not found")
    for fn in (week4, week5, week6, week7, weekend1):
        fn(args)


if __name__ == "__main__":
    main()
