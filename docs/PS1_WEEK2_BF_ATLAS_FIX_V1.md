# Week 2 BF atlas fix — v1

Date: 2026-11-08  
Branch: `ps1-asset-harmonization-v1`  
Source base: `de871e2` (`Tidy Week 2 pass report formatting`)

## Symptom and cause

The user reports that Week 2's Girlfriend, Spooky Kids and Monster now look
good, while BF's sprites are corrupted. Static inspection identifies a VRAM
page lifetime conflict: the Week 2 package uploads all nine shared 8bpp
texture pages, including the slot used by the base BF atlas (page 7). The BF
CLUT remains present, but the indexed texels in that page have been replaced
by Week 2 artwork. BF therefore samples unrelated pixels. This is a texture
page overwrite, not a chart, animation-timing, or palette-generation issue.

## Change

`ps1/relocate_week2_bf_atlas.py` copies already-converted, indexed BF texels
from the existing Week 1 package into collision-free bottom strips of Week 2
character pages. It does not decode/re-quantize images or change the shared
palette. The generated `week2_bf_overlay_data.h` points BF's Week 2 draw path
to those copies while Week 2 is active; Week 2's original frames and all
other weeks keep their existing descriptors. The 4bpp miss poses remain on a
separate page and keep using their existing renderer.

| Content | Source | Destination in W2 package | Size |
|---|---|---|---|
| BF base idle/sing frames | Existing W1 page 7, CLUT 2 | W2 character pages 2–8, free strip y=204–255 | 13 × 52×52 indexed pixels |
| BF sampled singing poses | Existing W1 page 7, CLUT 2 | Remaining free slots in W2 character pages 2–8, y=204–255 | 4 × 52×52 indexed pixels |

The generator fails if descriptors, page count, palette tail, source pixels,
or free-rectangle assumptions do not match. It checks that copied indices are
bit-identical, that every destination rectangle is collision-free, and that
the W2 package changes only inside those rectangles. The final W2 payload is
the one consumed by the ISO build rule; an earlier internal candidate wired
the unpatched staging payload and was discarded before delivery.

## Resource and regression checks

- Week 2 remains 9 8bpp pages plus the existing 512-byte palette tail:
  **590,336 bytes**, unchanged. Texture upload remains nine pages; no page,
  CLUT, CD-read, or transfer-volume increase.
- 45,968 indexed bytes (17 × 52 × 52) that were previously unused padding in
  those allocated rectangles now carry exact BF texels. This is not a package
  size reduction.
- ELF `.text` increased by 88 bytes and `.rodata` by 232 bytes. `.data`,
  `.sbss`, and `.bss` are unchanged (2,112 / 428 / 39,692 bytes respectively);
  no new runtime allocation is introduced.
- A SHA-256 comparison of matching generated `.vag` and `.bin` files outside
  the Week 2 package found **118/118 identical**, with no added or missing
  files. Charts, audio, and other scene packages were reused.
- The incremental Ninja dry-run contained only overlay generation, game
  compile, link, and disc creation. No general art/audio/chart conversion ran.
- Static ISO checks confirmed `SYSTEM.CNF;1` then `FUNKIN.EXE;1`, the embedded
  executable matches the linked executable, and embedded `W2SCENE.BIN;1`
  matches the corrected final package.

## Build and delivery

Build directory (separate from earlier builds):
`C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-week2-bf-fix-v1-build/`

Delivery directory:
`C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-week2-bf-fix-v1-final-delivery/`

- BIN `funkin-ps1-week2-bf-fix-v1.bin`, 340,016,880 bytes, SHA-256
  `6539B6D5B3FC1137B2B8F7A79DF62DD117272A1C9810C3DAD150B0C3D977D4F6`
- CUE `funkin-ps1-week2-bf-fix-v1.cue`, SHA-256
  `FBF29B4A907E93D10B311036CBE88BEB6EEFB5D6C46B585BFF59369485547BDF`
- Linked/embedded EXE SHA-256
  `CD13954FA2E89F7DABC8A99A0EA061BBDAEEF0C797DA231AD506CF0CF7978261`
- Final W2 scene package SHA-256
  `7C9F1980852A3C16F79936CFC8AB99C3D77C82CFADAD3E0F82A4FB5A260C4FD8`

The previous delivery and source resource directories were preserved. The
build completed; the existing two SDK `volatile` warnings remain. This is
compile and static-image evidence only: DuckStation execution, visual/audio
behavior, and real-console behavior still require testing. The user's
previous approval of the other Week 2 visuals is retained; BF in this build
is not yet user-validated.
