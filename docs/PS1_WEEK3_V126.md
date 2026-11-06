# Week 3 v126 — restore Pico's gameplay scale

## Correction

The v125 change misread the user's feedback about the static concept mockup as
feedback about Pico in the game. The requested size correction applied to the
mockup only. v126 restores the gameplay rendering and Pico camera formula
exactly to the v124 source: original 72×84 frame display size and the original
frame-center camera target. No sprite, stage, chart, timing, audio, or gameplay
data is changed.

The Week 3 scene itself remains the layered official Philly scene introduced
in v124: rear city, train between depth planes, front platform, GF, Pico and
BF. This build's only source change relative to v125 is the reversion of the
two Pico-only rendering edits.

## Build

- Branch: `ps1-port`.
- Source baseline: v125 local commit `ffa3e25592b134840a57f02c18870f9966f628f5`;
  Pico display and camera values restored to v124 (`f7ef9e2`).
- PSn00bSDK 0.24 / MIPS GCC 12.3 / CMake 4.5 / Ninja.
- Existing configured build directory: `C:/Users/Manau47/Documents/Codex/b125w3a`.
- Dry-run contained only `spu_probe.c`, executable link, and ISO creation;
  no asset converters. Existing converted scene/audio/chart packages were
  reused; the previous v125 delivery folder remains intact.
- Compilation and ISO creation succeeded. Static ISO check found 117 files
  and placed `SYSTEM.CNF;1` and `FUNKIN.EXE;1` at root entries 1 and 2.
- Delivered files:
  `ps1/build/week3-v126-pico-size-restore-20261031/delivery-v126-rootfix/`.
- BIN size: 338,506,896 bytes; SHA-256:
  `B78DF300FA9FE78ACAF0898107AC2CA3DAFEC3145F8A5BD98FB02DAD1E9056C0`.
- CUE SHA-256:
  `40DB78B42D7F83E07EC6911F992D45F23FD361E1084DE35AE977477131E8E8D9`.

This is a compiled build with static disc checks only. DuckStation validation
is pending the user's test; no console result is claimed.
