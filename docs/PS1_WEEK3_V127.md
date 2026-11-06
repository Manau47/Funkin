# Week 3 v127 — match the approved Philly composition

## What was wrong

The in-game renderer used Q8 zoom 640 (2.5×), while the approved 320×240
official-assets mockup used Q8 zoom 384 (1.5×) and a transition camera centered
between Pico and BF. At 2.5× the city was cropped, BF was pushed off the right
edge on Pico-focused sections, and the moving train looked like oversized
fragments. v127 applies the mockup's 1.5× scene transform and keeps the chart's
horizontal focus transitions.

The user confirmed Pico's gameplay pixel size from v124 is correct. Therefore
v127 does not resize Pico's on-screen sprite: Week 3 character frames use a
compensated world rectangle so the wider camera changes their positions in the
composition without shrinking their rendered pixel dimensions. The vertical
camera is held at y=75 for Week 3 so the floor-anchored actors stay in frame at
that retained size. Notes and HUD remain in their separate screen-space pass.

Stage assets and depth order are unchanged: official rear city layers, train,
official front street, then GF/Pico/BF. The train remains behind the street and
characters. This change does not add the deferred `train_passes` audio or GF
hairBlow/hairFall reaction.

## Build and verification

- Branch: `ps1-port`; previous local source commit: `e753c699057fbd8097c336b0a145faacc258d902`.
- PSn00bSDK 0.24 / MIPS GCC 12.3 / CMake 4.5 / Ninja.
- Existing configured build directory: `C:/Users/Manau47/Documents/Codex/b125w3a`.
- Dry-run: `spu_probe.c`, executable link, CD image only. Converted Week 3
  scene, charts, audio, and other week packages were reused; no asset converter
  ran. Prior v125/v126 deliveries remain in their own folders.
- Compilation and image generation succeeded. Static ISO check: 117 files;
  `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second; 338,506,896 bytes.
- Delivery: `ps1/build/week3-v127-scene-compose-20261031/delivery-v127-rootfix/`.
- BIN SHA-256: `77F6B66A84872BDA34EAD996F9C0B9A09A844B4B7EDC770870DA52226A1A6DA7`.
- CUE SHA-256: `05E5FEF6470275300BFA5EED92096B4CEACD423AC2983AD3908E823AED94ABB3`.

DuckStation validation is pending the user's manual test. No emulator runtime or
real-console result is claimed.
