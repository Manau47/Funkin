# Week 4 v159 — editor-tuned layout in normal gameplay

## Why v158 looked wrong

The scene editor's saved transforms were declared as defaults, but the normal
renderer applied them only inside `GAME_WEEK4_COMPOSITION_EDITOR` blocks. v158
correctly disabled the temporary editor, so those transforms silently stopped
affecting gameplay. This reset the far limousine to half size and lost the
saved shifts for the stage, camera, characters, and foreground limousine.

## Change

The saved transform values now remain active in the normal Week 4 rendering
path. The editor and camera demo remain compiled out; no controls or overlay
were added. Layer order and the v158 front-limo texture restoration remain
unchanged. The dancer offset is `dy=-10` world units, the requested roughly
20-pixel upward shift at the current camera scale.

| Layer | X offset | Y offset | Scale |
|---|---:|---:|---:|
| Stage | +18 | 0 | 1.00× |
| Camera | +6 | 0 | 1.00× |
| Distant limousine | -14 | -8 | 2.00× |
| Distant dancers | -14 | -10 | 1.00× |
| Girlfriend | -24 | +6 | 1.00× |
| Foreground limousine | +4 | +26 | 1.00× |
| Mom | -2 | 0 | 1.00× |
| Boyfriend | -30 | +22 | 1.00× |

These are the exact v157 scene-editor defaults carried into the normal build,
except dancers use v158's additional upward adjustment. No scene asset,
animation, chart, timing, gameplay, or audio was changed for v159.

## Build and validation

- Editor: OFF; scene demo: OFF; startup diagnostics: OFF.
- Incremental dry-run: one `spu_probe.c` compile, link, and ISO creation; no
  converters or resource generation were scheduled.
- PSn00bSDK 0.24 and MIPS GCC 12.3. Build completed. Static disc check confirms
  `SYSTEM.CNF` is root entry 1 and the executable is entry 2; sector checksums
  were validated by the existing ISO reorder tool.
- The user has not yet tested this build in DuckStation. Layout, gameplay and
  audio are therefore not claimed as runtime-validated. No real-console test.

Source snapshot, cache, build outputs, and hashes are in the external
`source-v159/manifest-v159.json` archive. Delivery is the ordered BIN/CUE in
`delivery-v159-ordered/` under the same build archive root.

- BIN SHA-256: `f1e0de607a9e8a8460747c30e388943f09e6baff06d17fa82792bd90095983ed`
- CUE SHA-256: `de0c9b62df81571e521121a020098bdcd8dc67cfc7b773e3c1f85456a1a528ef`
- Executable SHA-256: `e4ab0cc0e8eab4697105f5997c6d9e6a832caec35b7c2aa63c423f51500fe418`

The final CUE was generated with the existing root-order tool:
`python ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf <raw.bin> <raw.cue> <ordered.bin> <ordered.cue>`.
