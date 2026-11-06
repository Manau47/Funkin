# Week 2 backdrop framing correction — v117

## Correction after v116

The user's DuckStation test found the camera moving the wrong way and the permanent backdrop missing while the lightning animation still appeared. Inspection of v116's transform found that it anchored the enlarged backdrop's upper-left position. At 2.25× this restricted the visible crop to roughly source x=43–185, y=0–89, losing too much of the room composition. The flash was a separate overlay, so it could remain visible.

v117 keeps the requested 2.25× total backdrop zoom but anchors the zoom around the center of the complete 362×256 scene instead of the top-left. The existing slight post-zoom raise remains 5 world units. At the Spookeez/South opponent focus, the camera target now moves 5 world units downward (increasing camera Y); this moves the scene contents up about 12.5 screen pixels, reversing the v116 direction. Other songs and Week 2 Monster retain their previous camera target.

These are calculations from the renderer's 2.25× background and 2.5× character transforms, not a visual emulator measurement. Static backdrop, crop, and overlay use the same camera and zoom transform. No art, charts, audio, gameplay rules, lightning schedule, or other assets changed.

## Build and artifact

- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake/Ninja, Debug, with v116's configuration and v115's preconverted asset inputs.
- Dry-run: `spu_probe.c`, PSn00bSDK `stream.c`, link, and image creation only; no conversion.
- Build completed. The existing SDK `stream.c` volatile-qualifier warnings remain.
- Week 2 scene package hash is unchanged from v115/v116: `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- Static disc check: 117 root files, `SYSTEM.CNF` entry 1, `FUNKIN.EXE` entry 2, BIN size 338,203,488 bytes.
- BIN: `ps1/build/week2-scene-framing-v117-20261031/delivery-v117-final/funkin-ps1-week2-v117.bin`
- BIN SHA-256: `3CFC6FB77368BD6C8A2CBF007E600E9BAE1EE41F513594A15EC07C462E7EF449`
- CUE: `ps1/build/week2-scene-framing-v117-20261031/delivery-v117-final/funkin-ps1-week2-v117.cue`
- CUE SHA-256: `FF4C0E0D7CB51B7B5946BE8E54925D987A9B82FD4F2D6FF2AC08DE966367727F`

## Validation status

Compilation and static disc checks passed. v117 has not been run in DuckStation or on a real PS1; the room visibility, lightning alignment, and camera direction still await the user's manual test. Audio and gameplay were not revalidated in this framing-only change.
