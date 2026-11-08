# Week 5 v170b — character detail and mall upper level

## User feedback and scope

The user's v169c DuckStation feedback was that the scene positions looked much
better, while Mom/Dad and GF scales, the mall upper level/crowd visibility, and
sprite detail still needed work. This is treated as feedback, not final visual
approval. v169c remains preserved as the known comparison disc.

This pass changes only Week 5 scene rendering data: it preserves character
poses and anchors, scene composition/camera positions, charts, gameplay, audio,
and all other week packages.

## Changes

- Mom/Dad and GF frames are resampled from the pinned official rigs into
  96x112 cells (previously 80x96). This increases their source texel budget and
  their displayed dimensions by 20% horizontally and about 16.7% vertically
  under the unchanged renderer scale. Anchor registration is still the same
  centered-foot anchor. BF and Monster stay at 80x96 for this pass.
- A trial with every character at 96x112 exceeded the nine-page atlas limit
  and was rejected before writing the package. The final mixed sizing fits the
  existing nine 8bpp pages; no extra texture page is reserved.
- The nine texture pages now have independent 255-color palettes instead of a
  single shared palette. The palette rows are uploaded to VRAM y=481..489;
  the existing base palette at y=496 and other gameplay rules are unchanged.
- The mall escalator/platform is drawn before the upper crowd, and the crowd
  uses the larger existing scene scale value 420 to make that level legible.
  World positions and camera transforms remain the same. This is a rendering
  hypothesis to check in DuckStation, not an observed visual fix.

## Static resource budget

| Resource | v169c package | v170b package | Change |
|---|---:|---:|---:|
| 8bpp texture pages | 9 (589,824 B) | 9 (589,824 B) | 0 |
| Palette data | 512 B | 4,608 B | +4,096 B |
| W5 scene file | 590,336 B | 594,432 B | +4,096 B |
| W5 scene CD sectors | 289 | 291 | +2 |
| Texture upload to VRAM | 589,824 B | 589,824 B | 0 |
| Palette upload to VRAM | 512 B | 4,608 B | +4,096 B |
| Largest temporary CD buffer | 65,536 B | 65,536 B | 0 |

These are static file/layout calculations, not runtime measurements. The palette
read uses a 6,144-byte temporary buffer (three CD sectors); it is released
before music streaming. The nine rows occupy 4,608 bytes of VRAM CLUT storage.
No new CD reads occur during playback. The rest of the game content is still
loaded per scene.

All Week 5 audio, chart files, and catalog were copied from the existing
preconverted v167b package and verified byte-for-byte by SHA-256. No audio or
chart conversion was run.

## Build and validation

- Local source base: branch `ps1-port`, commit `7057882` plus the existing
  worktree state. The worktree already contains unrelated edits; this report
  does not claim that all of them are committed.
- Toolchain: PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake/Ninja.
- Dry-run listed only compilation of `spu_probe.c` and SDK `cdstream/stream.c`,
  linking, and disc creation. No graphics/audio/chart generation was planned.
- Compilation and ISO creation succeeded. The final ISO root records were
  reordered with the existing validator: `SYSTEM.CNF;1` is first and
  `FUNKIN.EXE;1` second. The utility reported root LBA 22, 117 visible files,
  and valid source integrity checks.
- BIN SHA-256:
  `D7CC97424C98AF233D34B9EECEC2B7C85BE853F7F177017DEFBAC14CC2937709`
- CUE SHA-256:
  `31992FEC0A7795285531EAEE3083F7DDE8D4D1BB4223D71B58F15AF6748FBC5A`
- Delivery: `C:\Users\Manau47\Documents\Codex\week5-scene-v170b-delivery`.
- No DuckStation execution or console test was performed by Codex. The user
  should compare Cocoa/Eggnog for Mom/Dad, GF, upper-level crowd, and color
  separation; Winter Horrorland should be checked for unchanged Monster/BF
  scale. Game behaviour and audio were compiled into this image but not
  runtime-regression-tested.

Rebuild the scene package without touching audio/chart assets:

```powershell
py ps1/rebuild_week5_v170_assets.py `
  --assets assets `
  --ffmpeg 'T:\Docker\MGTV Playlist Gen\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe' `
  --output 'C:\Users\Manau47\Documents\Codex\week5-scene-v170b-package\week5-scene.bin' `
  --header 'C:\Users\Manau47\Documents\Codex\week5-scene-v170b-package\week5_visual_data.h'
```

Then configure using the saved v170b CMake cache/toolchain paths and set
`FUNKIN_PS1_PRECONVERTED_WEEK5_DIR` to the generated package. Inspect the Ninja
dry-run before building; the expected work is compile, link, and ISO creation
only. Apply `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`
to the resulting BIN/CUE for the final delivery image.
