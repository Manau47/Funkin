# Week 4 GF animation restoration — v149

## Cause addressed

The v148 package contained only 10 positions from the official 30-frame
`gfCar` Animate timeline. Eight added positions were rasterized at 64×64 and
then drawn inside an 87×79 destination, while the two base poses used their
full 87×79 source rectangles. That reduced detail and skipped most of the
official animation cells.

v149 regenerates the 28 intermediate timeline cells at 87×79 using the same
anchoring, indexed palette, and 8bpp format as the two existing endpoint
cells. The renderer selects 15 successive cells per beat and alternates the
two 15-cell halves on successive beats, driven by the current song's audio
clock. At 120 BPM this advances at 30 cells/s. The 30 cells include 27 unique
raster poses; three timeline cells render identically in the source rig.

## Resource cost and checks

- Week 4 page count: 5 → 8 8bpp pages; the shared page table has 9 8bpp slots.
- `W4SCENE.BIN`: 328,192 → 524,800 bytes (+196,608 bytes, three pages).
- Runtime page transfer buffer remains 65,536 bytes; no new resident main-RAM
  animation buffer is added. The scene remains preloaded before music starts.
- The existing RGB555 CLUT is byte-identical. New GF pixels are quantized to
  that existing CLUT; no palette is recalculated or mixed with another atlas.
- Lossless repack verification: 46 referenced frame rectangles checked;
  texels remained identical during repacking, the two stage pages remained
  byte-identical, and all 30 GF cells are 87×79.
- Charts, audio, gameplay rules, camera coordinates, and the current scene
  composition are unchanged. This pass does not resolve the user's separate
  composition feedback on the distant limousine and background dancers.

## Reproduction

The official asset source remains outside Git at the pinned checkout's
`assets/shared/images/characters/gfCar`. Start from the preserved v148
preconverted directory and run:

```powershell
python ps1/build_week4_gf_full_v149.py `
  --source ps1/build/week4-composition-v148/preconverted/week4 `
  --assets assets `
  --ffmpeg 'T:\Docker\MGTV Playlist Gen\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe' `
  --output ps1/build/week4-composition-v149/preconverted/week4
```

Configure the separate v149 build with
`FUNKIN_PS1_PRECONVERTED_WEEK4_DIR` pointing at that output, then build target
`ps1-bopeebo-playable-disc`. The v149 Ninja build was cloned from the v148
configuration to reuse unchanged conversions. Its dry-run showed the existing
BF sing-pose generation (caused by the new build-directory command path), C
compilation, link, and disc creation; no Week 4 audio, chart, or scene-source
conversion ran.

The delivered ISO contains 144,279 sectors and 117 files. The executable is
1,028,096 bytes (SHA-256
`3ce926cb2571d30ad024d24d0abc48095857f45b10aec6d6b5a3089e1a32a249`).
Delivery hashes: BIN `a86a3083217c2f45358a2436cdc79b5e367cef11a007bffdcfb1a27ad5630e0d`,
CUE `8579eef0e6966afd78659f364593e560c8384148e9258d14fa88b196a842b340`.

## Validation status

The PSn00bSDK build and disc creation succeeded. Static checks confirmed the
30 full-size GF descriptors, 8-page package, unchanged Week 1 BF pose package,
and same CLUT. DuckStation was not run by the developer; the user must load the
delivered CUE and judge the animation and scene composition. No real-console
test is claimed.

