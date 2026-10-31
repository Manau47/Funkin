# Week 2 static background visibility — v118

## Change

The user confirmed the character cameras are correct but the static Week 2 background is still not visible. v117 enlarged the background to 2.25× and centered that crop on the full 362×256 source canvas. The official background artwork is asymmetrical: its window and room details are not centered in that canvas, so the centered crop spends too much of the viewport on the mostly empty/dark part of the image. v118 restores the earlier v115 background-only transform: 1.5× zoom and the stage origin plus the existing +85 world-unit vertical placement. The opponent/player camera targets and character/note transforms remain those of v117. Lightning uses the same background transform and schedule.

This is a targeted framing rollback, not a conversion fix. The compositing line investigated during this pass was already known from v112 to have no effect on the opaque, flat-color base sprite; it is not included in v118. An isolated candidate texture package was generated in the ignored `ps1/build/week2-scene-fix-v118-20261031/preconverted-base-v4/` folder for comparison, using `ps1/rebuild_week2_static_backdrop.py`; it is not used by the delivered build. The delivered build reuses the original v115 package byte-for-byte, and no production scene, character, chart, or audio resources were regenerated.

## Build

- Based on commit `90cce78` plus the v118 background transform change.
- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake/Ninja, Debug.
- CMake used the preserved v115 preconverted base package, plus the already converted Week 4–Weekend 1 packages.
- Dry-run contained only `spu_probe.c` and SDK `stream.c` compilation, executable link, and disc-image creation. No resource conversion was scheduled.
- `week2-scene.bin` in the build is byte-identical to the v115 source package: SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- Compile and ISO creation succeeded. `SYSTEM.CNF` and `FUNKIN.EXE` remain the first two root entries; image size is 338,203,488 bytes.
- BIN: `ps1/build/week2-background-v118-20261031/delivery-v118-final/funkin-ps1-bopeebo-playable.bin`
- BIN SHA-256: `9661A7C08EE3B139B76E1A6B78B2052B0E1F206F265E75F3A026C43CB93B35FF`
- CUE: `ps1/build/week2-background-v118-20261031/delivery-v118-final/funkin-ps1-bopeebo-playable.cue`
- CUE SHA-256: `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`

## Validation

This build has not been executed in DuckStation or on a real console. The user should test Spookeez and South for static-room visibility, lightning alignment, and the already accepted character-camera framing. Compilation and static disc checks do not validate those runtime results. The manual two-person DuckStation workflow is preserved; wait for the user's observation before further changes.
