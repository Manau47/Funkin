# Week 2 backdrop crop and lightning — v115

## Changes

This pass follows the v114 screenshot: the user marked the lower portion of the room as content that should fall below the camera frame, and reported that lightning was still not visible.

- The shared Week 2 backdrop/lightning zoom remains 1.5×. Its world Y offset changes from +16 to +85. Relative to v114, that moves the marked region down about 103 screen pixels at this zoom; its observed top near y=137 should land at the bottom edge (y≈240) and below. This is a coordinate prediction from the submitted screenshot, not an emulator observation.
- The stage starts around screen y=52 at the Dad/BF camera targets after this shift. A 320×240 rectangle in the scene's flat base color fills the exposed strip behind it. Characters, notes, camera focus targets and gameplay are unchanged.
- Root cause for the invisible lightning crop: the old extraction sampled source rectangle `(92, 81)–(255, 211)`, which omitted the official window flash at the top-left of the rendered `halloween_bg` rig. The new source crop `(10, 0)–(173, 130)` includes the lit window and floor reflection. The generated 104×83 patches use the already loaded Week 2 palette and reserved page-1 slots; no new VRAM page, palette, CD read, or SPU allocation is added.
- Lightning schedule, 30-tick visible interval, thunder sounds and the prior audio timing rollback are unchanged. The first Spookeez strike remains silent as in the pinned script.

## Reproducible, targeted asset update

`ps1/rebuild_week2_lightning.py` copies the existing converted base into a new directory, reads the pinned Week 2 Animate source, and replaces only the three reserved lightning patches plus their generated header anchors. It refuses to overwrite an existing output directory. The week2 payload differs from its base only inside those three reserved rectangles; the RGB555 palette is byte-identical. Week 1/3 scene files, catalog, menu and game-over audio files are byte-identical to the existing base. The main converter uses the same crop and corrected world anchor for future complete conversions.

Assets source revision: `Funkin.assets` `724eba9de9e76761d9cefd52169926bc51c760a5`.

## Build and verification

- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake/Ninja, Debug, same toolchain and gameplay configuration as v114; diagnostics off by default.
- Dry-run: compile `spu_probe.c` and SDK `stream.c`, link and create the CD image. No chart/audio conversion or full visual conversion was scheduled.
- Compilation and ISO creation succeeded. Static boot-directory reorder/check reports `SYSTEM.CNF` at entry 1 and `FUNKIN.EXE` at entry 2. The image contains 117 root files and is 338,203,488 bytes.
- BIN SHA-256: `AC663F620F6C3E33B34A78F5D8FCB3CE5059FBFC18634EE9A1B229C0E6DD3FFA`.
- CUE SHA-256: `F9AC44CEC24EAC8E37AA71B00F90DD844F9B2902BCF965254CF4FC80C27B40E4`.
- A PNG reconstructed from the generated texture patch shows the window dark in samples 0/1 and visibly lit in sample 2. This verifies conversion data only, not rendering in the game.
- v115 has not been run in DuckStation or on console. Please check that the marked lower décor is below the viewport, the permanent room remains filled, and the window flash is visible during Spookeez, South and Monster. Existing menus/gameplay/audio have not been runtime-tested in this pass.

BIN/CUE: `ps1/build/week2-scene-fix-v115-20261031/delivery-v115-final/`.
