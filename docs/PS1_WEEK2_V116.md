# Week 2 backdrop zoom and opponent framing — v116

## Changes from v115

- The Week 2 backdrop and its lightning overlay now render at 2.25×, a 1.5× increase over the 1.5× in v115. The backdrop origin is recomputed around the camera target so the extra zoom crops inward instead of scaling the art away from the scene. It is then raised by 5 world units, about 11 screen pixels at this zoom.
- On Spookeez and South only, the opponent camera target is lowered by 5 world units. With the existing 2.5× character camera, this places the opponent approximately 12.5 screen pixels lower. Other Week 2 focus targets and all other songs retain their previous framing.
- Scene composition, lightning timing, gameplay, chart data, audio streams, mix, controls, and judgment rules are unchanged. No textures, palettes, sprites, charts, or audio were regenerated.

These pixel amounts are derived from the renderer's fixed-point transforms; they have not been visually measured in DuckStation. The build is ready for the user's manual comparison with v115.

## Build and artifact

- Build: PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake/Ninja, Debug, configured with the v115 options and preconverted v115-v3 inputs.
- The Ninja dry-run listed only `spu_probe.c`, SDK `stream.c`, link, and CD-image steps. No asset conversion was scheduled.
- The build completed. The only compiler warnings were the existing PSn00bSDK `stream.c` volatile-qualifier warnings.
- Converted inputs were compared by SHA-256 against v115's `preconverted-base-v3`; the visual header, all matching audio/chart files and Week 1–3 packages were identical. In particular `week2-scene.bin` remains `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- The boot-order packaging check found 117 root files and put `SYSTEM.CNF` at root entry 1 and `FUNKIN.EXE` at entry 2. BIN size: 338,203,488 bytes.
- BIN: `ps1/build/week2-scene-framing-v116-20261031/delivery-v116-final/funkin-ps1-week2-v116.bin`
- BIN SHA-256: `B4EFAE8CD74D5104304FF8FDC7185D1315E7F337086DE9A695D2353B7A6DFAFB`
- CUE: `ps1/build/week2-scene-framing-v116-20261031/delivery-v116-final/funkin-ps1-week2-v116.cue`
- CUE SHA-256: `8A9614E7DF9C9331BA01C48EB60760B9B1E014074C6F1567AFB9533C9C33C029`

## Validation status

Compilation and static disc packaging checks passed. This build has not been run in DuckStation or on a real PS1. Please check the Week 2 backdrop scale/vertical placement and the opponent framing in Spookeez and South. Audio stability and gameplay have not been revalidated in this pass.

### User test result

The user reports that v116 framed the opponent/camera in the wrong vertical direction and that the permanent backdrop disappeared, leaving only the lightning animation visible. v116 is therefore rejected. The following v117 pass recenters the enlarged backdrop crop and reverses the Week 2 opponent camera-target adjustment; v116 and its delivery remain preserved for comparison.
