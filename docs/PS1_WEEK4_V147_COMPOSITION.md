# Week 4 Mother composition integration — v147

## Scope

Integrates the accepted v7 Mother/Limo composition reference into the playable Week 4 stage package. Only scenery pages 0 and 1 of `W4SCENE.BIN` are replaced. The existing foreground-limo source cel, dimensions and source placement `(341,108)` are retained. Mom, GF and BF positions, scales, camera, animations, charts, controls, gameplay and audio are unchanged.

The official `bgLimo` cel is added as the distant limousine at the v7 screen-space target `(-38,65)`, translated through the existing 524/256 scene zoom and Week 4 world origin. Four instances of the official first `hench dancing` cel are placed at v7 targets `(41,20)`, `(95,20)`, `(204,20)`, `(257,20)`. Painter order is distant car, dancers, foreground car. The dance cels are **static** in this pass; train/car pass motion and animated dancer cycles are not claimed as integrated.

## Reproducibility

- Source branch: `ps1-port`.
- Git base when this build was made: `7057882fa4c481fb878de4cc27d3a827179f7ddd`; the worktree also contained the earlier v142–v146 source/documentation changes, which must be included in the source snapshot to reproduce the exact executable.
- Official assets submodule: `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Input Week 4 package: `ps1/build/atlas-audit-v146/optimized/week4/`.
- Reproducible composition script: `ps1/compose_week4_background.py`.
- Output package: `ps1/build/week4-composition-v147/preconverted/week4/`.
- It copies the input package to a new directory, refuses to overwrite an existing output directory, decodes the pinned official `limoSunset`, `bgLimo`, `henchmen` and `limoDrive` art, and quantizes only the newly composed scene with the existing Week 4 CLUT. It does not rebuild audio, charts, or character atlases.
- Script invocation:

```powershell
python ps1/compose_week4_background.py `
  --assets assets `
  --ffmpeg "T:\Docker\MGTV Playlist Gen\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe" `
  --input-dir ps1/build/atlas-audit-v146/optimized/week4 `
  --output-dir ps1/build/week4-composition-v147/preconverted/week4 `
  --header week4_visual_data.h --scene week4-scene.bin
```

- PSn00bSDK 0.24, GCC MIPS 12.3, CMake 4.5, Ninja 1.11.1, Debug; diagnostics and arrow QA defaults OFF, Dad lanes ON. A separate CMake build directory was used. The package was selected through `FUNKIN_PS1_PRECONVERTED_WEEK4_DIR`.
- The build dry-run predicted one existing BF-pose augmentation, two C compilations and the link. It did not predict full graphics/audio/chart conversion. The BF augmentation output was reused from the preceding build by hash, but Ninja rebuilt it because the fresh build had no `.ninja_log` history. It regenerated the same files byte-for-byte.

## Resource and memory accounting

The W4 package remains 328,192 bytes: five 8bpp pages (327,680 bytes) plus the 512-byte CLUT. Before and after hashes are `9d1a67e8661b1c9a505442057871d83d0b1807b2af7be60be75cf6486bd8d296` and `935c6ba992c62754e1fa3a4d12ebc90e670a715479d9d647e5fd56215284d711`. Bytes after the first two pages, including the entire character atlas and CLUT, compare byte-for-byte equal; the visual metadata header is also unchanged.

Static transition budget is unchanged: five page uploads = 327,680 bytes, one CLUT upload = 512 meaningful bytes (one 2,048-byte sector read), and approximately 329,728 bytes read from CD for the package. The loader still uses its existing 64 KiB page staging allocation and the package still leases five W4 texture pages. No runtime RAM, VRAM, SPU, CD-streaming, or frame-time measurement was made. The background uses the existing CLUT; new artwork is nearest-mapped to its colors, so color matching is approximate rather than a newly optimized palette.

## Build and delivery

- Build tree: `ps1/build/week4-composition-v147/build-ninja/`.
- Raw BIN/CUE remain there; the delivered copies are in `ps1/build/week4-composition-v147/delivery-v147-mother-composition/`.
- Delivered BIN: 339,118,416 bytes, SHA-256 `f7aeb4fc10cc203f911bada47eb8f07ecf7a5e1b5e306d9a8699bce708449e90`.
- Delivered CUE SHA-256: `65f87ef028d245423aec7256f23cc689fd17e55fdd71e7c6c0cb0f8d5fa0981e`.
- The ISO root was checked and reordered in a separate delivery copy: `SYSTEM.CNF` is entry 1 and `FUNKIN.EXE` entry 2. The executable is 1,028,096 bytes; SHA-256 `c11c19cf363980f35def528536660c3cc33fdb496851b6216fb99c3891788cd0`.
- Converted stage preview (background pages only; not a game screenshot): `ps1/build/week4-composition-v147/preconverted/week4/stage-preview.png`.

## Validation state

Compilation, ISO creation, root-order verification and package/hash checks succeeded. No DuckStation or real-console execution has occurred in this pass. The user will load the delivered CUE. In particular, verify that the distant limousine and four dancers are visible without covering the main performers, and report any needed composition adjustment. This build is not yet visually validated.
