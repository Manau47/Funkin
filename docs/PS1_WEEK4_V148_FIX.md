# Week 4 composition and GF scale fix — v148

## Cause identified from v147

The v147 compositor requested the `bgLimo` source at 222×39 although the official frame is 2218×384. That made the distant car about half the intended width. It also requested the 517×410 hench dancer at 29×22, reducing the four background dancers to tiny marks and distorting their aspect ratio. v148 uses 455×79 for the car and 40×32 for the dancers, preserves the approved horizontal anchors, and places the dancers' feet on the distant-car roof line. The foreground-car placement remains untouched.

GF's two original Week 4 cels use 87×79 frames, while the eight v143 sampled cels use 64×64 rectangles. `draw_week4_visual_frame()` used each rectangle as the destination size, so the dance cycle visibly pulsed in scale. The Week 4 GF draw path now uses a fixed 87×79 destination envelope while retaining each frame's real UV rectangle. This changes no gameplay or animation timing and adds no atlas pages.

## Reproduction and resource costs

- Branch: `ps1-port`; local source base `7057882fa4c481fb878de4cc27d3a827179f7ddd`, with the existing local v142–v147 worktree changes retained.
- Assets: pinned Week 4 files at submodule commit `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Input package: `ps1/build/atlas-audit-v146/optimized/week4/week4-scene.bin`, SHA-256 `9d1a67e8661b1c9a505442057871d83d0b1807b2af7be60be75cf6486bd8d296`.
- Generator: [`../ps1/compose_week4_background_v148.py`](../ps1/compose_week4_background_v148.py). It writes a new directory and refuses to overwrite an existing output.
- SHA-256 of the v148 compositor source: `83fde36e35386003d51c05978e4ff891884b5f2726e03386e9d0f47e1c2f8d24`; SHA-256 of the local compiled `spu_probe.c`: `76355ddb0ea6309003527dd4dedfdb0c98018bf10ef3e6933f819bfc259afdec`.
- Output package SHA-256: `63839dd9e5f9e04f72e9ebea723eb190f897b900d74aeb31871be59aff3ae0d2` (328,192 bytes). It remains five 8bpp pages plus the existing 512-byte CLUT; actor pages and CLUT are unchanged. No new RAM/VRAM cost or CD reads.
- The 87×79 GF destination uses existing atlas UVs, with no texture regeneration or extra pages.

The fresh Ninja dry-run contained five actions: regeneration of the existing BF sing-pose sidecar (same output content), compilation of `spu_probe.c` and the SDK stream source, link, and disc creation. It did not include audio, chart, or full graphics conversion. Build: PSn00bSDK 0.24, GCC 12.3, Debug; diagnostics and arrow QA off, Dad lanes on.

## Build and validation

- Build directory: `ps1/build/week4-composition-v148/build-ninja/`.
- Executable: 1,028,096 bytes; SHA-256 `413897cbf47b0519121fcd1f8bd71181581895e86d7af24cb409d82e071ce6bf`.
- Delivered BIN: 339,118,416 bytes; SHA-256 `3bb766b54f0a37dab90dfa749cd20b80f6d63dc718d4a87e34ade703acca6b26`.
- Delivered CUE SHA-256: `839892e4d3763709377a97c2ac459ebcc49bc57d7f6dfc8ccc24b8d34a7e919c`.
- Delivery folder: `ps1/build/week4-composition-v148/delivery-v148-mother-composition/`.
- The separate delivery ISO was checked with the root-order tool: `SYSTEM.CNF` is entry 1 and `FUNKIN.EXE` is entry 2. Previous v147 files were not overwritten.

Compilation, package hashes, and static ISO checks succeeded. The PNG under the preconverted directory is only a scenery-page preview. No emulator execution or console test has occurred for v148; the user must verify the actual composition and GF size transitions in DuckStation.

