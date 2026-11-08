# Week 5 v165 — Mall scene extraction pass

## Scope

Week 4 remains the user's accepted reference and was not changed in this pass.
Week 5's visual package was rebuilt from the pinned official assets at assets
submodule revision `724eba9de9e76761d9cefd52169926bc51c760a5`. The chart files,
catalog, three music VAGs, gameplay rules, and audio conversion were carried
over unchanged from `ps1/build/v143-animation-pass/preconverted/week5`.

The previous Week 5 extractor assembled a compact static Mall plate, reduced
the escalator to 190x100 and the tree to 52x112, placed Santa partly outside
the viewport, and omitted both official crowd props. Its snow was baked into
the static plate and clipped by the runtime crop. This explains the sparse,
incomplete scene; it was not an asset availability problem.

## Changes

- Re-extracted the Mall and evil Mall background plates for the 4:3 viewport.
- Increased the Christmas escalator and tree source rectangles while keeping
  their aspect ratios; Santa remains a separately extracted official pose.
- Added four distinct cels each for the official upper and lower Mall boppers.
  Their 13-frame source timing is sampled at 24fps from the playing audio
  sample clock; repeated source holds reuse the last extracted cel.
- Moved Christmas and evil snow into separate foreground cels drawn after the
  crowd layers.
- Corrected the 320x240 background fit so the scene plate and upper crowd cover
  the full width. Crowd layers retain separate parallax factors (0.28 upper,
  0.90 lower) during camera focus transitions.
- Requantized all Week 5 visual pages together against one 8bpp palette, then
  appended the existing Week 5 animation cels using that same palette.

The Week 5 scene package grows from five to seven 256x256 8bpp pages after the
existing character-frame augmentation: +131,072 bytes of scene texture data,
plus the unchanged 512-byte CLUT. These pages are leased only while Week 5 is
active. No extra persistent RAM or SPU allocation was introduced. The largest
runtime CD/page staging buffer remains the existing 64 KiB allocation; scene
reads complete before music streaming starts.

## Reproduction

From the repository root, run:

```powershell
python ps1/prepare_ps1_week5_visual_package.py `
  --assets assets `
  --ffmpeg "<ffmpeg.exe>" `
  --base-package ps1/build/v143-animation-pass/preconverted/week5 `
  --output-package "<new external package directory>"
```

The helper refuses to overwrite an existing destination. It copies the base
package, regenerates only `week5-scene.bin` and `week5_visual_data.h`, and
retains catalog/audio/chart files byte-for-byte. It then reapplies the existing
sampled character animation pass to the new common CLUT.

Build configuration for v165 used the PSn00bSDK 0.24 toolchain and the external
package `C:/Users/Manau47/Documents/Codex/week5-scene-v165-package`. The Ninja
dry-run contained only `spu_probe.c` compilation, executable link, and ISO
creation. No audio, chart, or other-week conversion ran.

## Validation status

- Static extraction/package generation: completed.
- Compilation and ISO generation: completed.
- ISO root ordering: checked; `SYSTEM.CNF` is root entry 1 and the executable
  is root entry 2; sector EDC/ECC validation passed in the reorder tool.
- DuckStation/console visual and audio test: pending the user's manual load.
- Week 4: accepted by the user before this Week 5 pass; no Week 4 files changed.

Build delivery and exact file hashes are recorded in the external v165 manifest
under `C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/`.
