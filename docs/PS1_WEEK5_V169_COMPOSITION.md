# Week 5 composition pass v169

## Why v168 was rejected

The user's DuckStation check of v168 reported that the whole Week 5 scene still
looked wrong. Rechecking the renderer found two concrete transform errors that
were not caught by compilation:

1. `draw_week5_visual_frame()` multiplied the world-space offset by the
   per-asset scale. A sprite's size therefore also moved its anchor, so props
   using different art scales could not line up with the characters/camera.
2. Most props were placed at manually chosen screen targets. The placements
   did not come from `mallXmas.json` / `mallEvil.json`; only the comments cited
   those files. The v168 plate offset note also described screen-space values
   as if they were already world-space values.

## v169 source correction

- Keep the existing 1.797x camera composition and converted frames.
- Map stage design coordinates to the renderer world as `stage / 10`.
- Compute camera focus from the pinned stage character positions and camera
  offsets for each mall variant; retain the existing 28-world-unit vertical
  framing bias.
- Apply prop parallax as `stagePosition/10 + camera*(1-scroll)`.
- Separate camera transform from local art scale/trim in the Week 5 quad
  renderer. Asset size no longer changes its world anchor.
- Center the 256x192 background plate at 1.5x (384x288), with a (-32,-24)
  screen origin. During camera transitions it moves at the official 0.2
  parallax rate.
- Use the official JSON prop positions and scales for upper/lower crowd,
  escalator, trees, foreground snow, snow-under fill, Santa, and the evil mall.
  Preserve the JSON depth order and top-left origin for Santa.
- A final source audit caught that the generated `BOPEEBO_WEEK5_*_X/Y` macros
  are already adapted PS1 world coordinates; dividing those old macros by ten
  again was incorrect. Character anchors now come directly from the pinned
  `mallXmas.json` / `mallEvil.json` stage character positions and are mapped
  once with `stage / 10`: Dad `(42,882)` / `(290,869)`, GF `(808,854)`, and BF
  `(1177,871)` / `(1297,871)` for Xmas / Evil.

The coordinates are a deliberate 4:3 PS1 adaptation of the pinned data, not a
claim that every pixel now matches the reference. The build still needs the
user's visual check in DuckStation. No gameplay rules, chart data, audio,
animations, character frame dimensions, palettes, or scene atlas bytes changed.

## Build and inputs

- Local source base: commit `7057882` plus the existing working tree; only the
  Week 5 transform edits in `ps1/spu_probe.c` were made for this pass.
- Pinned content revision: `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Build configuration: PSn00bSDK 0.24, GCC 12.3, Ninja, target
  `ps1-bopeebo-playable-disc`; inherited from the v168 `CMakeCache.txt`.
- Dry-run: 3 tasks only (compile `spu_probe.c`, link, create ISO). No graphics,
  audio, or chart conversion was scheduled.
- Converted Week 5 scene package reused byte-for-byte:
  `week5-scene.bin` SHA-256
  `F728D0086461EFD649EED113D930CD33AE82CFA1F0BEE3CC7FB7D49F5846D840`.
- Compile/link/ISO creation succeeded. ISO size is 339,708,768 bytes.
- Final v169b BIN SHA-256:
  `8652835D4A2AB442C7298BE8431F0EF570920FB843F1159766D14B86F8D8BA4D`.
- Final CUE SHA-256:
  `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`.
- The final CUE/BIN and exact source/configuration snapshot are in
  `C:\Users\Manau47\Documents\Codex\week5-scene-v169b-delivery`.
- The earlier first-pass v169 build remains preserved in
  `C:\Users\Manau47\Documents\Codex\week5-scene-v169-delivery`; it is
  superseded and is not the requested final test image.
- v168 delivery remains preserved separately.

## Validation state

Compilation and packaging are observed. A final incremental Ninja invocation
reported `no work to do`; no assets were reconverted. No DuckStation execution
or console test was performed. The user will load v169b; scene placement,
character framing, transitions between focus targets, and visual coverage
remain pending that check. No visual validation is claimed.

## v169b boot failure and v169c ISO root fix

The user reported that v169b remains at the Sony PlayStation logo. Static ISO
inspection found `SYSTEM.CNF;1` as root file entry 93 and `FUNKIN.EXE;1` as
entry 36; the BIOS boot files therefore were not in the early root records.
Both file contents were present and valid, but this matches the known ISO root
ordering failure documented for earlier PS1 builds.

v169c is derived from the exact v169b BIN using the existing
`ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf` utility.
It places `SYSTEM.CNF;1` then `FUNKIN.EXE;1` as the first two file entries.
The utility verified source EDC/ECC, recalculated the four raw sectors
containing the 8 KiB root directory, and verified all bytes outside those
sectors were unchanged. `SYSTEM.CNF` and the embedded PS-X EXE contents are
unchanged. BIN SHA-256:
`AD82EA9B22ABA753EB0D2BFBC5592FC534FF9342EE187359DCB17B675A0C710A`; CUE
SHA-256: `0FD36D0C8454C756C6AC70B9CD5AED0662FD5F4F0960072D0C54862F86EA1AD1`.
This is a boot-order correction only, not a new compile. DuckStation boot is
still awaiting the user's test; no runtime success is claimed.
