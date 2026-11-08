#!/usr/bin/env python3
"""Rebuild only the pinned Week 5 visual package, preserving charts and audio.

The destination must be a new directory. Official assets are read from the
existing pinned assets checkout; the preconverted package supplies the exact
catalog, charts, and VAG files to carry forward unchanged.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
from types import SimpleNamespace

from generate_ps1_week5_assets import make_scene
from augment_week_animations_v143 import week5 as append_character_frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=pathlib.Path)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--base-package", required=True, type=pathlib.Path)
    parser.add_argument("--output-package", required=True, type=pathlib.Path)
    args = parser.parse_args()
    source = args.base_package.resolve()
    output = args.output_package.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing package: {output}")
    if not source.is_dir():
        raise SystemExit(f"base package does not exist: {source}")
    shutil.copytree(source, output)
    scene = output / "week5-scene.bin"
    header = output / "week5_visual_data.h"
    make_scene(args.assets.resolve(), args.ffmpeg, scene, header)
    append_character_frames(SimpleNamespace(
        assets=args.assets.resolve(), ffmpeg=args.ffmpeg, week5=output))
    print(f"Week 5 visual package ready: {output}")
    print("Audio VAGs, charts, and catalog were copied unchanged from base package.")


if __name__ == "__main__":
    main()
