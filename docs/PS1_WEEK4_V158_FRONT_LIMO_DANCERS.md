# Week 4 v158 — restore front limo, raise dancers, disable editor

## Changes

The v157 layer positions are retained. The front limousine disappeared because
the v157 exporter copied its source rectangle from a newly zeroed page instead
of from the v156c atlas. The destination rectangle was consequently transparent.
The new reproducible repair script copies only the already-converted front-limo
rectangle from the archived v156c package into the v157 destination rectangle.
It restores 12,531 nonzero palette indices; it does not regenerate other art,
palettes, charts, or audio.

The four distant dancers are raised by 10 world units, approximately 20.5 screen
pixels at the current 2.05x scene zoom. Their texture size, animation sequence,
and frame timing are unchanged. The existing scene editor is compiled out, and
the camera-demo mode is disabled for this normal playable build.

## Build and static verification

The build reuses the v157 package, all existing audio/charts, and the prior
converted scene assets. The dry-run contained only two C object builds, the link,
and ISO creation. Compilation succeeded with PSn00bSDK 0.24 and MIPS GCC 12.3.0;
the SDK cdstream source emitted two existing `volatile` qualifier warnings.

The disc contains 117 root files. The project ISO reorder step put
`SYSTEM.CNF;1` at visible index 1 and `FUNKIN.EXE;1` at index 2, and validated
the edited Mode 2 sector EDC/ECC. The build is not yet observed in DuckStation;
front-limo visibility, dancer placement, and normal-menu navigation await the
user's test. No console test is claimed.

## Reproduction and artifacts

The repair script is `ps1/restore_week4_front_limo_v158.py`. It requires the
archived v156c and v157 converted packages and refuses to overwrite its output.
The image was built with `FUNKIN_PS1_WEEK4_COMPOSITION_EDITOR=OFF` and
`FUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF`; all startup diagnostics remain disabled.

The final ordered BIN/CUE is under
`C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/delivery-v158-ordered/`.
The raw mkpsxiso output is preserved under `delivery-v158/`. The final source
snapshot, CMake cache, build outputs, and hashes are stored outside Git under
`C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/source-v158/`.
Prior v157 and earlier deliveries remain unchanged.
