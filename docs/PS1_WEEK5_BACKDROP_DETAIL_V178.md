# Week 5 backdrop sprite detail — v178

## Scope

This pass responds to the user's correction: the character sprites are not the
target. BF remains unchanged; Mom, Dad and GF are also untouched. The detail
work applies only to the Christmas Mall balcony crowd and escalator. Scene
positions, camera offsets, animation cadence, charts, gameplay and audio remain
as in the v177 working build.

The source is the existing official Week 5 art set in the pinned `assets`
checkout. The targeted converter reads `upperBop.png`/`upperBop.xml` and
`bgEscalator.png`; no other graphics, charts, or audio are regenerated. The
high-resolution source art is resampled with Lanczos to 1.5 times the old
texture density. It is split into page-safe tiles, while frame offsets and
inverse scale compensation preserve the previous on-screen dimensions and
anchors. Existing four crowd poses and their timing are retained. This does
not introduce extra animation frames.

## Atlas and budget delta

The v171 source package used 11 logical 8bpp pages (726,528 bytes including
CLUTs). The new package uses 12 logical pages (792,576 bytes): an increase of
65,536 texture bytes plus 512 CLUT bytes. It packs the balcony/escalator tiles
into the existing Christmas page and one additional page; the old lower-crowd
record is repacked without changing its pixels. The Evil Mall page is copied
byte-identically to logical page 11. Existing pages 0–7, page 9, all their
palettes, and the Evil page/palette are byte-identical to the source package.
New pages reuse the original Christmas CLUT; no character palette is changed.

For Christmas Mall, the loader uploads 10 logical texture pages into the same
10 physical 8bpp page slots already used by this scene. The variant remains
mutually exclusive with Evil Mall. The CLUT upload remains 3 sectors (6,144
bytes), exactly enough for 12 palette rows. The scene file grows by 66,048
bytes on CD; runtime upload count remains 10 full texture pages. The one-page
increment does not increase the active physical VRAM footprint.

The balcony crowd and escalator each change from one textured quad to three;
the active Christmas scene adds four quads per rendered frame. The frame table
adds 10 records (80 bytes when represented by the current eight-byte entries).
The code allocates the same temporary 64 KiB page buffer and palette buffer as
before. No full-resolution PNG is loaded into game RAM. UV bounds for all 79
frame records were checked against the 256×256 page limits; unchanged package
pages/palettes were hash-compared against v171.

## Build and validation

- Source checkout HEAD at build: `7057882fa4c481fb878de4cc27d3a827179f7ddd`;
  the checkout also contained earlier uncommitted port changes. The exact
  working source and CMake cache are hashed in the external delivery manifest.
- Package-generation command and CMake configuration are preserved in the
  external directory `C:/Users/Manau47/Documents/Codex/week5-backdrop-hires-v178-rootfixed-delivery/`.
- Dry-run for `ps1-bopeebo-playable-disc`: compile `spu_probe.c`, compile the
  SDK cdstream unit, link the executable, build the BIN/CUE. No unrelated
  asset/chart/audio conversion was scheduled.
- PSn00bSDK 0.24 build completed. The build emitted two pre-existing
  `volatile` qualifier warnings in the SDK's `stream.c`; linking and ISO
  creation succeeded.
- The raw `mkpsxiso` output placed root files alphabetically, so it is not the
  delivered test image. The final BIN/CUE applies the existing root-order
  repair utility after ISO generation. It verifies EDC/ECC, places
  `SYSTEM.CNF` then `FUNKIN.EXE` as root entries 1 and 2, and leaves every byte
  outside the root-directory sectors unchanged.
- No DuckStation or real-console run has been observed for this version. The
  new sprite detail, image quality, audio stability, and scene transitions are
  awaiting the user's CUE test. Compilation is not visual validation.


## Correction v179 — post-v178 composition regression

The user's DuckStation captures rejected v178 visually. A source audit found two concrete causes in the targeted generator. First, the output page list duplicated the newly packed Christmas detail page into logical page 11 instead of preserving the original Evil Mall page 10 moved to logical page 11. This corrupted the Monster/Evil variant. Second, the custom Sparrow extractor vertically centered frames while the v171/v177 extractor bottom-registered them; Lanczos fringe alpha was also included in trim bounds even though runtime quantization discards alpha below 128. Both differences could move or resize the balcony artwork relative to its v177 anchor.

v179 keeps the 1.5x texture density and split layout, but restores the original bottom registration, trims to the runtime-visible alpha threshold, and copies the original Evil texture into logical page 11. A static projection comparison against v177 now gives normalized crowd/escalator bounds within 0.34 logical source pixels on each measured dimension/offset. The Evil texture page hash matches v177 exactly. These are static checks; a DuckStation run is still required to confirm the rendered composition.
v178 contained two regressions found after delivery: the Evil texture page was overwritten by a duplicate Christmas detail page, and the custom Sparrow extraction used centered instead of v177 bottom registration (plus an alpha trim threshold mismatch). The previous v178 documentation statement claiming the moved Evil page was hash-identical was incorrect. v179 fixes these issues; see PS1_WEEK5_BACKDROP_DETAIL_V179.md.
