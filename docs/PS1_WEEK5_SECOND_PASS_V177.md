# Week 5 second-pass capture (v177)

## Source and captured scene values

Source checkout: branch `ps1-port`, baseline commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`; build includes the uncommitted changes recorded in `source-snapshot/`. The values below were read from the live DuckStation Memory Analyzer during the user's second composition pass. The enum order in `spu_probe.c` is: background, camera, tree, snow, GF, opponent, BF, upper crowd, escalator, lower crowd, Santa.

| Layer | DX | DY |
|---|---:|---:|
| Background | -65 | -65 |
| Camera | -25 | -20 |
| Tree | -20 | -35 |
| Snow | +35 | 0 |
| GF | 0 | 0 |
| Opponent (Mom/Dad) | 0 | 0 |
| BF | +10 | +5 |
| Upper crowd | -85 | -65 |
| Escalator | -115 | -80 |
| Lower crowd | -15 | -5 |
| Santa | -5 | 0 |

These are the Christmas Mall values. The Monster/Evil variant was left at its prior zero offsets. The normal game build now uses the captured values with the editor disabled; enabling the optional editor still starts from the same captured values.

## Camera

BF focus changed from `bf_y / 10 - 20` to `bf_y / 10 - 17`. Given the current scene scale, this is expected to move the scene framing upward by about 5 screen pixels. This is a static calculation; visual confirmation is pending.

## Sprite detail investigation

The current package `week5-scene-v171-package/week5-scene.bin` was reused unchanged (SHA-256 `DE59276EBB73631ACB2188013096DF06DD1B51F687549D30B9EDB74D4F25BC17`). No sprite, audio, chart, or scene resource was regenerated for the delivered build.

The v171 package has six common character pages and two Christmas variant pages. The active scene also uses a background page; the physical mapping has ten usable 8bpp page slots, leaving at most seven common pages when the background and two Christmas pages are resident. The common atlas already uses roughly 248–254 palette indices per page, so changing these assets to 4bpp would not preserve their colors exactly.

A higher-detail raster matched to the current zoom was tested with the existing packer but exceeds the available common-page area: target common trimmed sprite area is 527,769 pixels versus 458,752 pixels in seven 256×256 pages, before packing gaps. Even using the otherwise unused 64 background rows adds only 16,384 pixels, leaving a deficit of 52,633 pixels before packing overhead. The exploratory 1.05× parent-only package fit, but does not satisfy the requested detail increase for every sprite and was not used. Full-resolution regeneration therefore needs a deliberate VRAM/resource strategy; no frames or colors were discarded in this build.

## Build and artifact

- Build directory: `week5-second-pass-v177-build/`.
- Configuration: gameplay build; scene demo OFF; composition editor OFF; diagnostics OFF; Dad lanes ON.
- Incremental dry-run listed four build actions (two source compiles, executable link, disc image); it did not run asset conversions.
- Compilation and ISO generation succeeded. Image size: 339,864,000 bytes (144,500 sectors).
- ISO boot files were checked: `SYSTEM.CNF` precedes `FUNKIN.EXE`; boot path is `cdrom:\FUNKIN.EXE;1`; executable begins with PS-X EXE magic.
- No DuckStation execution was performed for this build in this turn; positions and camera remain pending user visual confirmation. No console test is claimed.

Use `funkin-ps1-bopeebo-playable.cue` from this delivery folder. Prior build folders were preserved.
