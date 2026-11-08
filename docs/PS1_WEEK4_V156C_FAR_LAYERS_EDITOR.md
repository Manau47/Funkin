# Week 4 v156c — far limo/dancers separated + scene editor

Base source: v155 archived snapshot, project commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`. Official assets revision: `724eba9de9e76761d9cefd52169926bc51c760a5`.

## What changed

The old far-plane graphic had the limousine and four dancers flattened into one low-resolution image. This build extracts the pinned official `week4/images/limo/bgLimo` and `week4/images/henchmen` assets into separate animation frames and separate 8bpp VRAM pages. The limousine has four cels at 24 fps. The dancers use the official left/right sequences: six distinct cels per direction, with repeated entries retained in the 15-step beat timing table. Both groups stay behind the front scene and use the same camera/parallax path; the editor can independently change their offsets and scale.

The source CLUT and the eight existing Week 4 pages are byte-identical to v155. The Week 4 payload grows by two 64 KiB pages: 524,800 → 655,872 bytes (+128 KiB, +64 CD sectors). The runtime page scratch allocation stays 64 KiB. Week 4 now loads ten page slots: two are borrowed from existing menu/base slots while the song owns the scene, and one uses a previously unused top-right VRAM page. The page count, palette sector, unload restoration and retry restoration are all updated together. No chart, gameplay rule, audio, camera target, or front-scene placement is changed.

## Scene editor controls

This build starts with diagnostics hidden. In Week 4 gameplay:

- `Select`: open/close the editor.
- `Start`: pause/resume the music/sample clock while the editor is open, so the scene can be adjusted at a fixed musical instant.
- D-pad up/down: choose Stage, Camera, Far Limo, Far Dancers, GF, Front Limo, Mom or BF.
- D-pad left/right: change selected layer X.
- `L1`/`R1`: change Y.
- `Cross`/`Circle`: increase/decrease scale.
- Hold `R2` for fast movement/scale steps; release it for fine steps.
- `Square`: reset the selected layer's offsets and scale.
- `Triangle`: show/hide the value summary page. Capture this page to record the current X/Y/scale for a follow-up pass.

The transform values are temporary for the current session; this test does not save them to disc. `Scene Demo` remains enabled to avoid scoring/health/game-over interfering with composition work. Dad's lanes are enabled. The normal diagnostics overlay and arrow QA board are disabled at startup.

## Build and verification

Build: PSn00bSDK 0.24, MIPS GCC 12.3.0, Debug. The dry-run for `ps1-bopeebo-playable-disc` listed only two C compilations, link and CD-image creation; it did not invoke asset/audio/chart converters. Existing menu, gameplay, chart and audio resources were reused. The only image change is W4SCENE.BIN.

Static ISO check: 117 root files; `SYSTEM.CNF;1` is entry 1 and `FUNKIN.EXE;1` is entry 2. Embedded executable bytes match the linked executable; header is PS-X EXE, entry PC `0x80024E54`, text address `0x80010000`, text size `0xFA000`. BIN SHA-256: `430dcadad6a817f76604746694b03c396d70b95a1a9074f89c52079138f2bd8`; CUE SHA-256: `59eaabea613a0e25c62698ef8999c2b256107b6f477227e6657f2a6f0657d72a`.

Compilation and static ISO checks succeeded. The build has not yet been run in DuckStation by the user; independent scaling, animation appearance, scene-editor interaction and Week 4 retry still need that test. No console test is claimed.

Delivery: `delivery-v156c/fnf-ps1-week4-far-layers-v156c.cue` and matching BIN. Exact source, configuration, patch and hashes are archived in `source-v156c/` outside the repository. The previous v155 delivery remains untouched.
