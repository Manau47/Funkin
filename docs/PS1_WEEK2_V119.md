# Week 2 static background contrast — v119

## Change

The user reports that the character cameras now look correct, but the room background is still not visible in DuckStation. The preserved `W2SCENE.BIN` does contain the room/window art in the two static scene tiles. Decoding those tiles with their Week 2 CLUT shows the art is unusually dark: the wall and room details are close in value to the game's dark clear color. v119 leaves the camera targets, background coordinates, zoom, asset pages, and lightning untouched; it raises GPU color modulation from 128 to 192 for the two permanent Week 2 scene frames only. This is an isolated contrast hypothesis, not yet confirmed in the emulator.

The RGB modulation does not affect Week 2 characters, other stages, lightning overlays, charts, audio, gameplay, or the camera. No scene or audio assets were converted.

## Build and disc checks

- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, Debug.
- Reused the v115 converted package and existing Week 4–Weekend 1 packages. Ninja dry-run contained only `spu_probe.c`, the SDK `stream.c`, link, and disc creation; no conversion step.
- Reused `W2SCENE.BIN` byte for byte: SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- C compilation and ISO creation succeeded. The SDK `stream.c` emitted its existing discarded-`volatile`-qualifier warnings.
- The first ISO produced by CMake had `SYSTEM.CNF;1` as root entry 93. It was preserved as an intermediate. The delivered image was made with `ps1/diagnostics/reorder_iso_system_cnf.py`, which recalculates the affected sector checksums and verifies unchanged data outside the root directory. The delivered root order is `SYSTEM.CNF;1`, `FUNKIN.EXE;1`; it contains 117 root files and is 338,203,488 bytes.

Delivered CUE/BIN:

- [`funkin-ps1-bopeebo-playable.cue`](../ps1/build/week2-background-v119-contrast-20261031/delivery-v119-rootfix/funkin-ps1-bopeebo-playable.cue)
- BIN SHA-256: `77460B1EAE38731BD57EC8C74D4D5653C84FBD51391AACAF2D0EF88A5D5066E2`
- CUE SHA-256: `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`

The un-reordered CMake output is retained separately in `delivery-v119-final/`; it is not the disc to load.

## Validation status

Compilation and static ISO checks succeeded. v119 has not yet been observed in DuckStation and has not been tested on a real console. The user should test a Week 2 song and report whether the permanent room/window is now visible, whether the current character camera framing is preserved, and whether lightning remains aligned. No runtime fix is claimed before that check.
