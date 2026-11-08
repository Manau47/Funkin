# Week 5 scene editor build v180

This build restores the in-memory Week 5 layer editor on top of the corrected
v179 scene package. It is a separate CUE; it does not overwrite v179 or change
the current scene positions, sprites, gameplay assets, charts, or audio.

## Controls

Launch any Week 5 song from Freeplay, then press **Select** to show or hide the
editor. It is hidden at startup. Up/down selects a layer; left/right changes X;
L1/R1 changes Y; Cross/Circle changes scale; R2 increases the adjustment step;
Square resets the selected layer; Triangle displays its transform summary;
Start pauses/resumes the music and sample-driven animation.

The editor requires the scene-demo mode. In that mode the chart continues to
animate, but scoring, health loss, misses, and game over are bypassed so the
player can adjust the composition without racing the song. Edits are temporary
for the current run and are not written back to the disc. No arrow sheet or
always-on diagnostic overlay is enabled.

## Build record

- Checkout HEAD at build: `7057882fa4c481fb878de4cc27d3a827179f7ddd`.
- The working tree already contained local modifications. Exact build inputs
  (`spu_probe.c`, `CMakeLists.txt`, ISO XML, CMake cache and relevant source diff)
  are archived beside the delivery in `source-snapshot`.
- CMake: `FUNKIN_PS1_WEEK5_COMPOSITION_EDITOR=ON`,
  `FUNKIN_PS1_SCENE_DEMO_DEFAULT=ON`.
- Dry-run scheduled only `spu_probe.c` and SDK stream compilation, executable
  link, and ISO generation. No image/audio/chart conversion was scheduled.
- The Week 5 scene package and generated visual-data header are byte-identical
  to v179: `week5-scene.bin` SHA-256
  `3640CBFAAE4FC03BBB717E45DBCCAD43051346AB1022E98A65D9760B1D895A08`;
  `week5_visual_data.h` SHA-256
  `2669F8B28FECB74566B9E115BDF6DB8A11C4B96E7EC365B11D25C2A9DB96F7F1`.
- The disc root was repaired and statically checked: `SYSTEM.CNF;1` is first,
  `FUNKIN.EXE;1` second. System config points at the embedded executable.
- Compilation and ISO creation completed. No DuckStation run or user validation
  has yet been observed for v180; the editor interaction still needs your test.

Delivery directory: `C:/Users/Manau47/Documents/Codex/week5-scene-editor-v180-delivery/`.
