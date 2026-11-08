# Week 4 official stage anchor correction — v152

## Comparison and cause

The user reported that the v151 Week 4 scene still did not match the intended composition. The two supplied in-game captures show the foreground limousine as a large cropped shape across the bottom, while Mom/BF do not read as standing on its hood/roof. This is consistent with v151 placing its foreground limo at `(16,152)` in the PS1 world.

The pinned official stage file `assets/preload/data/stages/limoRide.json` provides the original layout and depth:

| Element | Official position | Scroll | zIndex |
|---|---:|---:|---:|
| Sunset | (-120, -50) | 0.1 | 10 |
| Background limo | (-200, 480) | 0.4 | 20 |
| Hench dancers | x=100,400,700,1000,1300; y=100 | 0.4 | 30 |
| GF | (787, 779) | character | 100 |
| Main limo | (-120, 528) | 1.0 | 150 |
| Mom/opponent | (329.5, 913) | character | 200 |
| BF | (1217.5, 592) | character | 300 |

The active PS1 character anchors already correspond to the original positions divided by six: Mom `(55,152)`, GF `(131,130)`, BF `(203,99)`. Applying that same conversion to the official main-limo position gives `(-20,88)`. v151 used `(16,152)`, an offset of 36 world units right and 64 down. At the Week 4 zoom `524/256`, that corresponds to roughly 74 screen pixels right and 131 pixels down, explaining the misplaced foreground car in the supplied screenshots.

## Change

The v152 compositor `ps1/compose_week4_layers_v152.py` parses the pinned official `limoRide.json`, asserts the main-limo source anchor is `[-120,528]`, and derives the PS1 position `(-20,88)` by the existing 1/6 coordinate conversion. It rebuilds from the immutable v149 package and retains the accepted far-plane placement and v151 texture composition. It changes only the generated `BOPEEBO_WEEK4_LIMO_X/Y` macros; package pixels, CLUT, frame rectangles, animations, chart, audio, actor positions, camera and gameplay remain unchanged.

The renderer order continues to follow the official depth order: far scene/dancers, GF (z=100), main limo (z=150), Mom/opponent (z=200), BF (z=300). This makes the car mask GF while leaving Mom and BF in front. The foreground car remains a static sampled frame in this pass; animated wheels, wind-blown hair and passing foreground effects are not added here.

## Static and build verification

- Assets revision: `724eba9de9e76761d9cefd52169926bc51c760a5`.
- v149 input W4 package SHA-256: `A91F0C52422B59E3067A0A006A5C655D5F554B7FD1EB6D6C71E09E9D35F49505`.
- v152 W4 package SHA-256: `CE3872A1C10E14AEDE358F3D9824000C7DC4199E1EEF58298B4E65AE7B23F743`, byte-identical to v151.
- Scene remains 8 8bpp pages plus the same CLUT (524,800 bytes); no extra VRAM page or CD read.
- v151 and final v152 PS-X executables are both 1,028,096 bytes. A byte comparison finds exactly 3 changed bytes, all in the two immediates for the limo x/y macros.
- Dry-run predicted 5 actions: known BF sidecar generation, two C object compilations, link and ISO. No chart/audio conversion or general art conversion was scheduled. BF sidecar hash stayed `D3C6F317C0B108233C5D81774FA97775AFE2B2D40D98F46528EAD70543B67310`.
- PSn00bSDK 0.24 / GCC MIPS 12.3.0, `Debug`, diagnostics OFF, Dad lanes ON. Compilation and ISO generation succeeded. The SDK `stream.c` emitted its existing volatile-qualifier warnings.
- Static ISO check: source root had `SYSTEM.CNF;1` at index 93; delivered image has it at index 1 and `FUNKIN.EXE;1` at index 2.
- Executable SHA-256: `9D8D3F399CC5A8CF8655D5612AE19047191530F8F3D48BA1B6967D4C980DCB93`.
- Delivery BIN SHA-256: `44CDD729D30F920FA7F77CAB30E29932EB2EE6ABB0DB311E57808E49BF72698C`.
- Delivery CUE SHA-256: `4998D0C3DA85740DFE82B5154918BAF34259EE8BED181F29F1445AE36FC87EB6`.
- Build tree: `C:/Users/Manau47/Documents/Codex/week4-v152-debug-build/`.
- Delivery: `ps1/build/week4-composition-v152/delivery-v152-official-stage-position/`.

A first, non-`Debug` configure was caught by comparing its executable to v151 before selecting the delivery. Its output remains in a separate directory and is not the CUE supplied for testing. The final image uses the v151 `Debug` configuration.

## Validation status

Compilation and static package/ISO checks passed. v152 has not been run in DuckStation or on real hardware. The screenshots motivated this correction but are not proof that v152 is visually correct. The user should load the supplied CUE and check the main limo beneath Mom/BF, GF occlusion, far dancers, both camera focuses, and Week 4 tracks. No gameplay or audio behavior is newly claimed as validated.

The renderer call used by this build is the v151 ps1-port source commit 86258a27c9bce66a4565f5b868a46dec5d1e53cf; v152 changes only the generated limo position macros and retains that draw-order code.
