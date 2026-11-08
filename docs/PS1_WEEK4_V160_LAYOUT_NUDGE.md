# Week 4 v160 — dancer and character placement adjustment

This is a focused follow-up to v159. The four distant dancers move up by a
further 40 screen pixels. Mom, GF, and BF move 30 screen pixels left. No scene
assets, scales, animation timing, gameplay, charts, or audio are changed.

The W4 camera zoom is 524/256 = 2.046875. Scene offsets are converted before
projection, so the changes are `-20` world units vertically for the dancers
and `-15` world units horizontally for each character. That projects to about
40.9 and 30.7 screen pixels respectively. The focus targets for Mom and BF
remain at their existing anchors, so camera-follow interpolation does not
cancel the requested visible leftward move. The camera's own saved transform
is unchanged.

| Layer | v159 offset | v160 offset | Visual delta |
|---|---:|---:|---:|
| Distant dancers Y | -10 | -30 | about 40.9 px up |
| GF X | -24 | -39 | about 30.7 px left |
| Mom X | -2 | -17 | about 30.7 px left |
| BF X | -30 | -45 | about 30.7 px left |

The front limousine restoration and all other v159 transforms remain intact.
The composition editor, scene demo, and startup diagnostics remain disabled.

## Build and verification

- Dry-run is checked before building; it must contain only the C source,
  link, and disc-image steps. Preconverted scene/music assets are reused.
- BIN/CUE root order and sector checksums are checked with the existing ISO
  reorder tool.
- The user must still load the delivered CUE in DuckStation. No visual runtime
  or real-console validation is claimed by this report.
- The source, CMake cache, compile commands, executable, map, scene package,
  and hashes are archived in `source-v160/manifest-v160.json` outside Git.

Delivery: `delivery-v160-ordered/fnf-ps1-week4-v160.cue` and corresponding BIN.

- BIN SHA-256: `7fd9ff0c3e84772622616218cc22a6edc9222e49cd98d49a005604dbcaa93be2`
- CUE SHA-256: `9e3f51eb9a6640d6c8508c0818fb743137cd79a2bb69e27322c873909a96755f`
- Executable SHA-256: `8c4c776426c03248041f10bf637db47e131acdfbaf27ffb053657f2e76938777`
