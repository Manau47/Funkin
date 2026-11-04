#!/usr/bin/env python3
"""Build a Week 4 package with the complete, native-size GF car dance.

Inputs are the already-converted v148 package and the pinned GF car rig.
Only the Week 4 visual package/header are changed; music, charts and all
other converted packages are copied byte-for-byte by the caller.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from animate_preview import Rig  # noqa: E402
from convert_bopeebo_visuals import fit_anchored_rig  # noqa: E402
from augment_week_animations_v143 import put_frames  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--assets", type=Path, required=True)
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {args.output}")
    shutil.copytree(args.source, args.output)
    src = args.output / "week4_visual_data.h"
    header = src.read_text(encoding="ascii")
    old_labels = [f"GF_DANCE_V143_{i}" for i in range(8)]
    enum_match = re.search(r"enum \{(.*?)\n\};", header, re.S)
    table_match = re.search(
        r"static const Week4VisualFrame week4_visual_frames\[[^]]+\] = \{(.*?)\n\};",
        header, re.S)
    if not enum_match or not table_match:
        raise ValueError("Unexpected Week 4 generated header structure")
    enum_names = re.findall(r"WEEK4_FRAME_(\w+)\s*=\s*\d+", enum_match.group(1))
    rows = re.findall(r"(?m)^\s*\{[^{}]+\},\s*/\*\s*(.*?)\s*\*/\s*$", table_match.group(1))
    if len(enum_names) != len(rows):
        raise ValueError(f"enum/table mismatch before pruning: {len(enum_names)} vs {len(rows)}")
    keep = [(name, row) for name, row in zip(enum_names, rows)
            if not name.startswith("GF_DANCE_V143_")]
    enum_text = "\n" + "\n".join(
        f"\tWEEK4_FRAME_{name} = {i}," for i, (name, _row) in enumerate(keep))
    row_text = "\n" + "\n".join(
        line for line in table_match.group(1).splitlines()
        if not any(f"/* {name} */" in line for name in old_labels))
    header = header[:enum_match.start(1)] + enum_text + header[enum_match.end(1):]
    table_match = re.search(
        r"static const Week4VisualFrame week4_visual_frames\[[^]]+\] = \{(.*?)\n\};",
        header, re.S)
    assert table_match
    header = header[:table_match.start(1)] + row_text + header[table_match.end(1):]
    header = re.sub(r"(?m)^#define WEEK4_VISUAL_FRAME_COUNT \d+u$",
                    f"#define WEEK4_VISUAL_FRAME_COUNT {len(keep)}u", header)
    src.write_text(header, encoding="ascii", newline="")

    rig = Rig(args.assets / "shared/images/characters/gfCar", args.ffmpeg)
    ids = [*range(1, 15), *range(16, 30)]
    fitted = fit_anchored_rig(rig, [0, 15, *ids], 87, 79,
                              anchor_frame_ids=[0, 15])
    frames = [(f"GF_DANCE_FULL_{i:02d}", fitted[i], 87, 79) for i in ids]
    # Six 87x79 cels per temporary page. The following lossless repack
    # selects only referenced rectangles and removes the obsolete 64x64 cels.
    put_frames(args.output, "week4-scene.bin", "week4_visual_data.h", "WEEK4",
               frames, expected_pages=5, slots_per_page=6)

    packed = args.output / "packed"
    subprocess.run([
        sys.executable, str(HERE / "repack_indexed_week_atlas.py"),
        "--week", "4", "--header", str(args.output / "week4_visual_data.h"),
        "--package", str(args.output / "week4-scene.bin"),
        "--out-dir", str(packed),
    ], check=True)
    shutil.copy2(packed / "week4_visual_data.h", args.output / "week4_visual_data.h")
    shutil.copy2(packed / "week4-scene.bin", args.output / "week4-scene.bin")
    shutil.copy2(packed / "week4-repack-report.json", args.output / "week4-repack-report.json")

    # Assert the source frames are all full-sized and the packed page limit
    # leaves at least one 8bpp page slot unused in the existing 9-page pool.
    final_header = (args.output / "week4_visual_data.h").read_text(encoding="ascii")
    if "#define BOPEEBO_WEEK4_PAGE_COUNT 8u" not in final_header:
        raise ValueError("Expected the full-size GF package to occupy eight pages")
    for frame_id in ids:
        if f"GF_DANCE_FULL_{frame_id:02d}" not in final_header:
            raise ValueError(f"Missing full-size GF cel {frame_id}")
    print(f"Week 4 GF: 30 official poses, 87x79; package has 8 pages; output={args.output}")


if __name__ == "__main__":
    main()

