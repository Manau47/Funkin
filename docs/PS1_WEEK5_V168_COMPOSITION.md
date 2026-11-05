# Week 5 v168 — composition correction

## Reference comparison

Compared the supplied v167 DuckStation captures with the user's Week 5 reference video and pinned assets at `724eba9de9e76761d9cefd52169926bc51c760a5` (`mallXmas.json`, `mallEvil.json`).

Identified v167 scene errors:
- The 256x192 background plate is rendered at 1.5x (384x288). For centered 32x24 overscan its top-left must be screen (-32,-24), i.e. world offset (-192,-144) from the camera center. v167 used (-128,-96), moving the plate down/right by 64x48 screen pixels at 1.5x.
- `evilBG.png` contains transparency; the official `mallEvil` stage has solid `#23062D` behind it. The renderer exposed the clear color as a large black region.
- The official Evil Tree was omitted.
- In the Christmas Mall, upper crowd z=20 must draw before escalator z=30/tree z=40. v167 reversed that order. It also omitted the snow-under fill at z=59.
- Dad/BF camera targets did not apply their stage camera offsets.

## Changes in v168

Only the Week 5 composition and focus target paths in `ps1/spu_probe.c` changed. The plate is centered for its overscan, Winter Horrorland receives its solid backing and tree layer, Mall layers follow their stage depth order, and the snow-under/fog layer is drawn before the character sprites. Dad/BF camera targets use adapted source camera offsets; notes and HUD remain screen-space.

No scene image, palette, audio, chart, character frame, animation duration, gameplay rule, or pause/retry code was regenerated or modified. The existing scene package and music payload hashes match v167.

## Build and validation record

- Source base: PR branch `ps1-port`, commit `05a7f5250b730991f02c9b730043099236c4f3a3`; composition patch committed separately for v168.
- Pinned assets: `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Build folder: `C:\Users\Manau47\Documents\Codex\week5-scene-v168-build`; SDK/toolchain unchanged from v167.
- Dry-run included two C compilations, link, and ISO generation; no image/audio/chart converter ran.
- Build and ISO packaging completed. Two existing SDK volatile-qualifier warnings remain.
- ISO root order checked: SYSTEM.CNF entry 1, FUNKIN.EXE entry 2.
- Delivered BIN SHA-256: `A9CBDD0133CAB85284925AC9D06F5C73261F39F9976AC141BB151A650352D908`.
- CUE SHA-256: `BA00F22DF825369BF72D2AD4EA37ECD8D67D44E2489657078FCC64703A0AE079`.

## Validation status

This build has not been run in DuckStation by Codex or on a real console. The corrected framing, Evil background fill/tree, layer order, menu-to-song transition, and audio stability await the user's test. The reference comparison and source inspection identify the faults; they do not establish runtime validation.
