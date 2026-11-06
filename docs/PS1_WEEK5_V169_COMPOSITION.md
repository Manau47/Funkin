# Week 5 composition pass v169

## Why v168 was rejected

The user's DuckStation check of v168 reported that the whole Week 5 scene still looked wrong. Rechecking the renderer found two concrete transform errors that were not caught by compilation:

1. `draw_week5_visual_frame()` multiplied the world-space offset by the per-asset scale. A sprite's size therefore also moved its anchor, so props using different art scales could not line up with the characters/camera.
2. Most props were placed at manually chosen screen targets. The placements did not come from `mallXmas.json` / `mallEvil.json`; only the comments cited those files. The v168 plate offset note also described screen-space values as if they were already world-space values.

## v169 source correction

- Keep the existing 1.797x camera composition and converted frames.
- Map stage design coordinates to the renderer world as `stage / 10`.
- Compute camera focus from the pinned stage character positions and camera offsets for each mall variant; retain the existing 28-world-unit vertical framing bias.
- Apply prop parallax as `stagePosition/10 + camera*(1-scroll)`.
- Separate camera transform from local art scale/trim in the Week 5 quad renderer. Asset size no longer changes its world anchor.
- Center the 256x192 background plate at 1.5x (384x288), with a (-32,-24) screen origin. During camera transitions it moves at the official 0.2 parallax rate.
- Use the official JSON prop positions and scales for upper/lower crowd, escalator, trees, foreground snow, snow-under fill, Santa, and the evil mall. Preserve the JSON depth order and top-left origin for Santa.

The coordinates are a deliberate 4:3 PS1 adaptation of the pinned data, not a claim that every pixel now matches the reference. The build still needs the user's visual check in DuckStation. No gameplay rules, chart data, audio, animations, character frame dimensions, palettes, or scene atlas bytes changed.

## Build and inputs

- Local build source base: commit `7057882` plus the existing working tree state. An exact `spu_probe.c` snapshot and CMake cache are archived alongside the delivered disc; the local checkout contains older/unpublished edits outside this Week 5 pass.
- Pinned content revision: `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Build configuration: PSn00bSDK 0.24, GCC 12.3, Ninja, target `ps1-bopeebo-playable-disc`; inherited from the v168 CMake cache.
- Dry-run: 3 tasks only (compile `spu_probe.c`, link, create ISO). No graphics, audio, or chart conversion was scheduled.
- Converted Week 5 scene package reused byte-for-byte: `week5-scene.bin` SHA-256 `F728D0086461EFD649EED113D930CD33AE82CFA1F0BEE3CC7FB7D49F5846D840`.
- Compile/link/ISO creation succeeded. ISO size is 339,708,768 bytes.
- BIN SHA-256: `661CE1D91A73A7E7B417A07D32E0232867245F542594947E8B2E3B16145486C2`.
- Branch source equivalent was published in commit `bd55029eb5f04297521fb74189046475f4dac728` on `ps1-port`. The BIN was built from the archived local snapshot described above; don't treat this remote commit as a byte-for-byte source checkout of the BIN.
- BIN/CUE are outside Git in `week5-scene-v169-delivery`; v168 delivery remains separately preserved.

## Validation state

Compilation and packaging are observed. No DuckStation execution or console test was performed. The user will load v169; scene placement, character framing, transitions between focus targets, and visual coverage remain pending that check. No visual validation is claimed.

## Final v169b pre-delivery audit

A final source audit found that the generated `BOPEEBO_WEEK5_*_X/Y` macros were already adapted PS1 world coordinates; dividing those values by ten again displaced the characters. v169b now takes character anchors from the pinned `mallXmas.json` / `mallEvil.json` stage positions and maps them once: Dad (42,882)/(290,869), GF (808,854), BF (1177,871)/(1297,871), Xmas/Evil respectively.

Final BIN SHA-256: `8652835D4A2AB442C7298BE8431F0EF570920FB843F1159766D14B86F8D8BA4D`. CUE SHA-256: `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`. Delivery and exact source/configuration snapshot: `C:\\Users\\Manau47\\Documents\\Codex\\week5-scene-v169b-delivery`. Previous v169 preflight is preserved separately. Incremental Ninja confirmed no pending work after successful compilation/package creation; assets were not reconverted. DuckStation and console checks are pending; no visual validation is claimed.
