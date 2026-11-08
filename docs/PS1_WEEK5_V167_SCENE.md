# Week 5 scene pass — v167

## Scope

v167 is a focused visual rebuild for Week 5 (Mall / Mall Evil) based on the user-provided recording `Screen_Recording_20261105_210840.mp4`. The prior v165 scene package flattened stage elements into a single plate, embedded Santa into the background, and represented characters at 64×64. This pass separates the layers needed by the renderer and restores larger official character frames. It does not change charts, audio encoding, gameplay rules, or other weeks' compositions.

The source assets are from the pinned `assets` revision `724eba9de9e76761d9cefd52169926bc51c760a5`. Stage references examined: `assets/preload/data/stages/mallXmas.json` and `mallEvil.json`; character sources include the pinned GF Christmas, Parents, Monster, BF Christmas rigs and the stage props. The original stage data places the background and crowd props on separate depth layers; Santa is a foreground stage prop for Mall Christmas and is absent from Winter Horrorland.

## Changes in the v167 build

- Week 5 now has independent Christmas and Evil stage plates, separate escalator/tree and snow layers, and separately animated upper/lower crowd layers.
- Camera parallax is applied per layer. Crowd animation is selected from the audio-sample clock at 24 frames/s rather than the video frame count.
- Santa is drawn as its own stage prop for the Christmas songs, in front of Parents and behind BF. It is omitted from Winter Horrorland.
- Parents, Monster, and GF Christmas frames are extracted from the official rigs at 80×96 source-frame scale (the previous package used 64×64 character frames). Trim offsets are carried in each frame descriptor so trimming transparent borders does not move the artwork's anchor.
- Week 5 uses the official BF Christmas idle, four directional singing poses, and misses for that scene. Existing four-channel song streaming, charts, HUD, judged popups, score, health, SFX, pause/retry behavior, and other week render paths are kept in the executable.
- The previewed pause/resume handling from v166 remains included; the user reported v166 appeared to resolve the pause issue. v167 itself has not been user-tested yet.

## Reproducible asset/build inputs

The new script is `ps1/rebuild_week5_v167.py`. It rebuilds only the Week 5 visual scene payload/header from the pinned assets, and takes an explicit output directory. The v167 build reused the existing converted base, Weeks 4/6/7/Weekend 1 packages, song audio, and chart data; it did not run audio/chart conversion.

Build directory: `C:\Users\Manau47\Documents\Codex\week5-scene-v167g-build`
Week 5 package: `C:\Users\Manau47\Documents\Codex\week5-scene-v167b-package`
SDK/toolchain: PSn00bSDK 0.24 with the MIPS toolchain already installed outside this repository.
Source branch/HEAD at build: `ps1-port`, `7057882fa4c481fb878de4cc27d3a827179f7ddd` plus the uncommitted source changes archived alongside the build.
Build target: `ps1-bopeebo-playable-disc`.

The CMake/Ninja dry-run listed only `spu_probe.c` and `cdstream/stream.c` compilation, executable link, and disc image creation. It listed no resource-conversion command. Ninja then reported `no work to do` on the repeat invocation because those targets had completed in the preceding build operation.

## Static resource budget

| Resource | v167 static amount | Notes |
|---|---:|---|
| Week 5 visual pages | 9 × 65,536 = 589,824 bytes | Nine 8bpp 256×256 pages; v165 used seven, so this adds two pages (131,072 bytes). One coherent 256-entry RGB555 CLUT follows the pages. |
| Week 5 payload | 590,336 bytes | Exact generated `W5SCENE.BIN` length: 9 pages plus 512-byte CLUT. |
| Week 5 frame descriptors | 69 entries | Runtime metadata in generated header; atlas rectangles and trim offsets are shared by frames. |
| Scene upload scratch RAM | 65,536 bytes | One page-sized temporary buffer in the existing loader; freed after loading. |
| CD scene reads | 9 × 32 sectors = 288 sectors | Scene is loaded before starting music; no new concurrent CD reads were added. |
| SPU / music / charts | unchanged | Existing four-channel music and song/chart packages were reused byte-for-byte from the preceding package. |

The 9-page count and payload size are static build facts, not runtime performance measurements. Compared with v165, the larger character cels and separated layers cost two additional 8bpp pages; no VRAM reduction is claimed, and Week 5 now uses the full nine-page scene allocation. Actual RAM high-water mark, GPU upload time, audio underruns, and render cadence require runtime observation and have not been measured for v167.

## Build artifact

Delivered separately at `C:\Users\Manau47\Documents\Codex\week5-scene-v167-delivery\`:

- `funkin-ps1-week5-scene-v167.bin` — 339,727,584 bytes, SHA-256 `2C688068BBAE5A9F2F1F09A09FF9E5A414D1D45BD8870C26690A26AA24841D0B`
- `funkin-ps1-week5-scene-v167.cue` — points to the BIN above.

The ISO root directory was reordered with the repository's `ps1/diagnostics/reorder_iso_system_cnf.py`: `SYSTEM.CNF` is entry 1 and `FUNKIN.EXE` entry 2. Its input BIN hash was `827F90888F69B0A6662A8DDF42EFA7E3E98AD1E09E8DC259F357FED4F413CA89`. The reorder utility verified the original root-sector EDC/ECC and preserves all bytes outside the ISO root directory sectors.

## Validation status

- **Inspected:** the reference recording, pinned stage JSON and official character/stage source rigs, current Week 5 renderer and visual package.
- **Implemented:** separated stage layers, larger official character frame extraction with anchor offsets, per-layer camera parallax, 24fps audio-clock crowd animation, separate Santa prop, and Week 5 BF Christmas poses.
- **Compiled:** the playable ELF/EXE and BIN/CUE with the configured PSn00bSDK toolchain. The disc root boot-order rewrite also completed.
- **Executed in emulator:** not yet. DuckStation interaction remains with the user, as agreed.
- **User validation:** pending. In particular, verify Mall, Cocoa, Eggnog, Winter Horrorland, BF/GF/Parents scale and placement, crowd motion, parallax, pause/resume, audio and retry.
- **Real console:** not tested.

The supplied v167 BIN/CUE is an integration build for review, not a claim that Week 5 composition or runtime stability is validated.
