# Week 2: trade Spooky Kids texels for BF detail

Date: 2026-11-09  
Branch: `ps1-asset-harmonization-v1`  
Source base before this pass: `35b2f6f04997d1bc2365edf740bc6fc60835f3f8`  
Pinned official assets: `724eba9de9e76761d9cefd52169926bc51c760a5`

## Change

This test build applies the user's proposed compromise to Week 2 only:

- Spooky Kids' 16 selected idle/singing cels are rebuilt from the pinned
  official atlas at 76×90 instead of 85×100. Their scene footprint is reduced
  by about 10% (72×84 to 65×76), bottom anchored at the same floor position.
- BF's same 13 idle/singing cels and four sampled singing extras are rebuilt
  from the official atlas at 62×62 instead of 52×52. Runtime display remains
  52×52, preserving BF placement and animation cadence.
- Existing GF poses, Monster poses, directions, chart, health/gameplay rules,
  music, SFX and all other weeks are retained.

Both conversions use the already established palettes: Spooky Kids uses the
existing Week 2 CLUT; BF uses the existing BF CLUT. Neither palette is
recomputed. The 40 Week 2 character/icon rectangles and 17 BF rectangles are
repacked into the existing seven character pages, with a one-pixel gutter and
collision checks. The two stage pages remain byte-identical.

The pixel-area trade is:

| Set | Before | After | Change |
|---|---:|---:|---:|
| Spooky Kids (16 cels) | 136,000 texels | 109,440 texels | −26,560 texels |
| BF (17 cels) | 45,968 texels | 65,348 texels | +19,380 texels |
| Combined actor rectangles | 181,968 texels | 174,788 texels | −7,180 texels |

These are packed rectangle areas, not a page-count reduction. The package
still contains nine 8bpp pages plus a 512-byte CLUT tail (590,336 bytes).
Thus the CD read and GPU upload remain 590,336 bytes per Week 2 package load,
including 589,824 bytes of texture pages. No VRAM page or CLUT is freed at
runtime; the recovered texel area makes room for denser BF cels within the
same allocated pages.

## Build and memory checks

The build was cloned into a new directory from the prior clean v1 build. The
incremental Ninja dry-run contained only the targeted GF rectangle refresh,
this Week 2 repack, game and SDK stream compilation, ELF link and ISO creation.
No general graphics, audio, or chart conversion was scheduled. The targeted
GF refresh used the existing pinned source and palette and reproduced the
validated GF cycle.

Static memory comparison of the prior clean build and this build:

| ELF section | Prior | This build | Change |
|---|---:|---:|---:|
| `.text` | 1,013,332 B | 1,014,296 B | +964 B |
| `.data` | 2,630 B | 2,630 B | 0 B |
| `.bss` | 40,120 B | 40,120 B | 0 B |

The loader's 64 KiB staging buffer and other runtime allocations are
unchanged. No additional scene read or upload was added. The SDK's two
existing `volatile` qualifier warnings remain.

Checks performed:

- exact package length and nine-page layout;
- stage pages and Week 2 CLUT byte-identical to the GF-refreshed input;
- 40 Week 2 descriptors and 13+4 BF descriptors generated;
- BF rectangles all 62×62; Spooky Kids rectangles 76×90;
- UV bounds and non-overlap, including the packing gutter;
- compile and ISO creation succeeded; diagnostics are disabled by default;
- mkpsxiso lists `SYSTEM.CNF` and `FUNKIN.EXE` first in the disc tree.

These are static/build checks. DuckStation execution, sound/gameplay regression
checks, visual quality comparison, and real-console testing remain pending.

## Delivery

Build directory:
`C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-week2-bf-detail-v1-build/`

Delivery directory:
`C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-week2-bf-detail-v1-delivery-v2/`

- CUE: `funkin-ps1-bopeebo-playable.cue`
- BIN: 340,016,880 bytes, SHA-256
  `8F405B4EC58A61B5C99FB84E25679334DBE1A4A9A774CAC975793A392BB0FB45`
- CUE SHA-256:
  `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`
- EXE SHA-256:
  `8B2047AEECF0EDC318D6E485C7D2EEE5F1CE1A4DDC60E23EBB72B2C6FF5EAB02`
- Week 2 package SHA-256:
  `E011912106CF63E9AABE0C7F73B28204BA63882A67AA204C637DA087E6B79EA6`

The prior GF-cycle and BF-fix BIN/CUE files were not overwritten. The test
build awaits the user's DuckStation check; this report does not claim visual
or runtime validation.
