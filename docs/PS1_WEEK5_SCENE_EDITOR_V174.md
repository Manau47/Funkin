# Week 5 scene editor v174

This is a dedicated temporary composition build based on the Week 4 v154
in-memory tuner. It does not save edited transforms into the game. It is meant
to make the Week 5 Christmas Mall and Evil Mall composition adjustable during
the user's DuckStation session.

## Use

Open Freeplay and launch a Week 5 song. Cocoa or Eggnog selects the Christmas
Mall layer set; Winter Horrorland selects the Evil Mall set. Press Select to
open or close the editor. The editor is hidden by default.

While the editor is open:

- Up/down selects a layer.
- Left/right moves the selected layer on X; L1/R1 moves it on Y.
- Cross/Circle adjusts scale, bounded from 50% to 400% of the current scene
  scale. Hold R2 for larger position and scale steps.
- Square resets the selected layer's temporary transform.
- Start pauses or resumes the music stream and sample-driven animation.
- Triangle shows the complete transform summary. Capture this screen to hand
  the values back for a reviewed production change.

Select temporarily takes over the pad while the editor is open, so it does not
toggle gameplay diagnostics. D-pad input does not judge notes in this build:
the existing scene-demo build mode follows the chart visually while skipping
score, health, misses, and game-over logic. This makes it safe to pause and
adjust the layout. No arrow-sheet or general diagnostic overlay is enabled.

Christmas Mall exposes Background, Camera, Upper Crowd, Escalator, Tree,
Lower Crowd, Snow, Santa, GF, Opponent, and BF. Evil Mall exposes Background,
Camera, Tree, Snow, GF, Opponent, and BF. Layer edits are independent between
the two variants. Camera edits are applied after the existing smooth camera
focus and affect the projected scene together; Mom/Monster and BF focus targets
also follow their edited anchors.

## Build and evidence

- Source base: local `ps1-port` worktree at Git HEAD
  `7057882fa4c481fb878de4cc27d3a827179f7ddd`, plus its pre-existing local
  modifications and the v174 editor changes. The exact `spu_probe.c`,
  `CMakeLists.txt`, CMake cache, and v173-to-v174 source diff are archived in
  the external delivery's `source-snapshot` directory.
- PSn00bSDK 0.24, GCC MIPS 12.3. CMake option
  `FUNKIN_PS1_WEEK5_COMPOSITION_EDITOR=ON` requires
  `FUNKIN_PS1_SCENE_DEMO_DEFAULT=ON`.
- The v174 target dry-run contains only compilation of `spu_probe.c` and the
  SDK `stream.c`, executable linking, and ISO creation. It schedules no asset,
  chart, or audio conversion.
- Week 5 scene package SHA-256 remains
  `827FC943FC0429785B3C61C0CA4740E9812063498B1568D1AFFB34D1DFA85245`;
  BF pose sidecar SHA-256 remains
  `D3C6F317C0B108233C5D81774FA97775AFE2B2D40D98F46528EAD70543B67310`, both
  byte-identical to v173.
- Compilation and ISO creation succeeded. The SDK's `stream.c` emitted its
  two existing discarded-`volatile` warnings.
- The ISO root was statically reordered and checked: `SYSTEM.CNF;1` is file
  entry 1 and `FUNKIN.EXE;1` is entry 2. EDC/ECC were recalculated for the
  modified directory sectors.
- No DuckStation run has been observed for v174, and no real-console test has
  been made. The controls, panel readability, and transform response await
  the user's test.

See `C:/Users/Manau47/Documents/Codex/week5-scene-editor-v174-delivery/` for
the BIN/CUE, ELF/MAP, source snapshot, and manifest.
