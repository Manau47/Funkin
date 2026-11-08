# Week 5 v168 — composition correction

## Reference comparison

The supplied v167 captures were compared with the user's Week 5 reference video,
the pinned assets at revision `724eba9de9e76761d9cefd52169926bc51c760a5`, and
`mallXmas.json` / `mallEvil.json`.

Observed implementation errors in v167:

- A 256x192 plate drawn at 1.5x is 384x288. Its intended origin for centered
  32x24 overscan is `(-32,-24)` on screen, which corresponds to world offset
  `(-192,-144)` from the camera center. The v167 offsets were `(-128,-96)`, so
  the plate appeared at screen `(+32,+24)`, shifted down/right.
- `evilBG.png` has transparent areas. The original Mall Evil stage declares a
  full-screen solid `#23062D` behind it. The PS1 renderer left those pixels at
  the framebuffer clear color, causing the large black region in the capture.
- `evilTree` from the official stage JSON was not drawn.
- Mall's `upperBoppers` are z=20, before the escalator at z=30 and tree at z=40;
  v167 drew them after those props.
- The official snow-under fill at z=59 was absent.
- Camera focus used character center positions and ignored the pinned Dad/BF
  camera offsets.

## v168 correction

Only `ps1/spu_probe.c` changes the scene. The render order now follows the
pinned stage's depth order. Mall Evil draws its solid backdrop before the PNG
and includes the separate evil tree. The Mall snow fill and foreground snow
are drawn before character layers. The plate origin now matches its 1.5x size
and overscan. Dad and BF camera targets apply the official source offsets using
the port's existing coordinate scale.

The scene atlas, audio, charts, character frames, dimensions, palette and
animation timing are unchanged. In particular, no gameplay or pause/retry logic
was modified.

## Build inputs and checks

- Source snapshot base: local commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`
  plus the existing working-tree state; relevant change is the Week 5 drawing
  and focus-target code in `ps1/spu_probe.c`.
- Assets: pinned revision `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Build directory: `C:\Users\Manau47\Documents\Codex\week5-scene-v168-build`.
- Previous build preserved: `C:\Users\Manau47\Documents\Codex\week5-scene-v167g-build`.
- Converted Week 5 scene `W5SCENE.BIN`: same hash as v167; audio payload hash
  also same. No image, audio, chart, or atlas converter ran.
- Dry-run: 4 tasks only (2 C compilations, link, ISO creation).
- Build: success. The SDK stream source emitted two existing volatile qualifier
  warnings.
- ISO root ordering check: `SYSTEM.CNF` entry 1, `FUNKIN.EXE` entry 2.
- Delivered BIN SHA-256:
  `A9CBDD0133CAB85284925AC9D06F5C73261F39F9976AC141BB151A650352D908`.

## Validation status

Compiled and packaged, but not executed in DuckStation by Codex. The user will
load the CUE and report the visual result. Therefore the plate alignment,
Winter Horrorland fill/tree, camera framing, cross-song transitions and any
remaining composition issues are still unverified in execution. Real hardware
has not been tested.
