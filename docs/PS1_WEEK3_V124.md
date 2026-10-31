# Week 3 / Philly train — v124

## Scope

This build adapts the classic Week 3 stage (Pico, Philly Nice and Blammed) to
the PS1 scene renderer. It keeps the validated gameplay and four-channel music
path, aligns Pico's camera target vertically with BF, restores the sampled GF
dance cycle, and adds the official moving train between the city backdrop and
the street/platform foreground.

## Findings from the pinned source

- `assets/preload/data/stages/phillyTrain.json` defines the depth order as
  sky, city, lights, behindTrain, train, then street. The train therefore
  belongs between the rear city and front street layers.
- `assets/preload/scripts/stages/phillyTrain.hxc` does not specify fixed
  song timestamps. It attempts a train start at beat `4 mod 8`, with a 30%
  chance after a cooldown greater than eight beats. On start, the original
  plays `train_passes`; the image begins moving once that sound reaches
  4700 ms, then advances at 24 updates per second. The source subtracts 400
  source pixels per update and loops through eight cars.
- The three classic Week 3 charts have fixed BPMs in their pinned metadata:
  Pico 150, Philly Nice 175, and Blammed 165. Their train opportunities are
  therefore musical and probabilistic, not authored timestamps.
- Before v124 the PS1 converter composited the street into the same two tiles
  as the rear layers, leaving no insertion point for the train. It also kept
  only two GF dance poses. The 10 selected official poses (five per alternating
  side) match the Week 2 sampling density.
- Pico and BF have the same stage anchor and camera offset in the official
  stage JSON. The PS1 camera uses frame centers; Pico's 84-pixel frame is 20
  pixels taller than BF's 64-pixel frame. With the 1/6 conversion scale this
  shifted Pico's target 10 world units upward. v124 adds 10 to Pico's converted
  camera Y offset, giving the same center target as BF.

## Changes in v124

- Convert the official background/city/lights/behindTrain props into two rear
  tiles and the official street into two separate transparent foreground
  tiles. Draw the rear tiles, train, foreground tiles, then the characters.
- Convert the official 4096×512 train sprite at the same 1/6 stage scale and
  split it into three texture-safe pieces. Its position and movement use the
  source's 24 Hz cadence, 4.7-second sound-relative visual delay, 400-pixel
  source step, and eight-car reset pattern.
- Reproduce the source's 30% beat-gated train chance with a deterministic
  per-song pseudo-random sequence, so retries are reproducible. This is an
  adaptation of the source randomness, not a fixed train timestamp.
- Sample 10 official GF dance poses across two beats and select them from the
  streamed music beat phase.
- The official `train_passes` audio and GF hair-blow/hair-fall poses are not
  included in this first PS1 train pass; they remain follow-up work. The
  moving image is delayed by the original sound-relative 4700 ms threshold.

## Memory and resource handling

- Week 3 scene package: 4 rear/front stage pages + 4 Pico/GF/train character
  pages = 8 8bpp pages, plus one 256-word RGB555 CLUT. Payload size: 524,800
  bytes on disc.
- The global VRAM map provides 9 8bpp pages. Week 3 overlays slots 0–7 while
  active and restores their normal contents on exit; the ninth 8bpp page,
  both framebuffers, the font and CLUT reservations remain outside the overlay.
- Week 1 and Week 2 payloads were copied byte-for-byte from the existing
  preconverted base package. Week 4, 5, 6, 7 and Weekend 1 packages were reused.
- The v124 converter also generated a fresh full base package outside the
  repository, then the retained Week 1/2 packages and catalog/audio files were
  restored from the pinned preconverted package before configuration. The
  build dry-run contained only C compilation, link and ISO creation.

## Build and test status

- Source base: commit `3944c52` plus the v124 source changes in the commit
  recorded alongside this document in Git history.
- PSn00bSDK 0.24, MIPS GCC 12.3, CMake/Ninja Debug build succeeded.
- Dry-run: `spu_probe.c`, SDK `stream.c`, link and CD image only; no asset
  conversion in the build step.
- Static converter checks: no atlas rectangle overlap; 9 8bpp + 2 4bpp pages
  remain within the authored VRAM layout. Week 3 overlay itself uses 8/9 8bpp
  pages.
- ISO root directory was reordered with `reorder_iso_system_cnf.py`; it has
  117 files, `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second. This is a
  compilation/static-disc check only.
- Delivered BIN size: 338,506,896 bytes; SHA-256
  `BCDAE9C21D128952F3AF6C2B0861C0625F2FA6548919931A39E064298EC73D55`.
  CUE SHA-256 `ADBA74115FF0BF2B45509B1F5804E7BCB6CDF5B875D6F0629C87A4931EF570A6`.
- New Week 3 payload SHA-256 `4887C63C159574D853C330BB1F07EA738B469BEB363F79F5B0ED7038C5373A14`.
  Reused Week 1 payload SHA-256
  `C2444F178F0A9A7F28B4B24476B9058E74FB15237DDD4BB786907F73A6CD0E8F`;
  Week 2 payload SHA-256
  `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- DuckStation runtime validation is pending the user's two-handed test. No
  console test is claimed.

## Later-week GF audit

The asset generators for Weeks 4–7 also currently sample only two GF poses
(the left/right endpoints) despite their source rigs exposing more animation
frames. This v124 correction is limited to Week 3; later-week atlases have
separate layouts and page budgets and need individual repacking before their
cycles can be expanded safely. Week 1 and Week 2 already use the 10-pose cycle.

## Manual test requested

1. Load `ps1/build/week3-v124-philly-20261031/delivery-v124-r2-rootfix/funkin-ps1-week3-v124.cue` in DuckStation.
2. In Freeplay, play Pico, Philly Nice and Blammed in Normal.
3. Check that the rear city remains visible throughout, the street/platform
   stays in front, Pico and BF share a camera height, and GF cycles through
   more than two poses.
4. Let each song run for a few bars to observe whether the train starts; its
   first movement begins 4700 ms after an eligible, deterministic train start.
5. Recheck Week 1 and Week 2 after leaving Week 3 for texture restoration.

Build hashes and source/resource revisions are also recorded in
[`PS1_WEEK3_V124_MANIFEST.json`](PS1_WEEK3_V124_MANIFEST.json).
