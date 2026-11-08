# PS1 asset and scene audit — v183 baseline

Date: 2026-11-08. This is a static audit of the already-built v183 resource packages and pinned source data. It does not alter gameplay, scene assets, charts, audio, or the build outputs.

## Reference and scope

- Port branch: `ps1-port`; source commit recorded by v183: `7057882fa4c481fb878de4cc27d3a827179f7ddd`.
- Pinned `assets` submodule: `724eba9de9e76761d9cefd52169926bc51c760a5`.
- v183 BIN SHA-256: `63EAD9541EA8690C40DD2866E3DA976EC115BAC4D967C6F063D6DB52011C5B6E`.
- Exact v183 build configuration and source snapshot: `C:/Users/Manau47/Documents/Codex/week5-lower-crowd-v183-delivery/BUILD.txt` and `source-snapshot/`.
- Inputs audited are the already-produced scene packages and generated headers in `C:/Users/Manau47/Documents/Codex/week5-lower-crowd-v183-build/`. No image, audio, or chart converter was run.

The user's “v183 is okay” is treated as acceptance of the current working reference, not as a new full-game test result. No emulator or console run occurred during this audit. The retry behavior remains untouched.

## Results: package and page inventory

The scanner measures 256×256 indexed texture pages, generated frame rectangles, index-zero transparency, and rectangle unions. The table's package sizes include the palette bytes stored after the pages. These are per-scene package sizes, not all simultaneously resident VRAM.

| Resource set | Indexed pages | Encoded package | Frame rectangles |
|---|---:|---:|---:|
| Shared/W1 base | 9×8bpp + 2×4bpp | 655,360 B | 225 |
| Week 2 | 7×8bpp | 459,264 B | 45 |
| Week 3 | 8×8bpp | 524,800 B | 40 |
| Week 4 | 9×8bpp | 590,336 B | 66 |
| Week 5 | 12×8bpp | 792,576 B | 79 |
| Week 6 | 7×8bpp | 459,264 B | 77 |
| Week 7 | 4×8bpp | 262,656 B | 34 |
| Weekend 1 | 9×8bpp | 590,336 B | 48 |

The encoded scene sets total 4,334,592 B across CD packages; this is storage, not RAM or VRAM residency. The v183 Week 5 pack is the largest at 12 pages plus 6,144 B for 12 CLUT rows. Its runtime loader aliases the two mall backplates to one physical slot and loads only the selected variant. Static code therefore uploads 10 texture pages for Christmas Mall or 8 for Monster, then the 12-row CLUT: respectively 661,504 B or 530,432 B of `LoadImage` payload. The corresponding CD read ranges use 323 or 259 sectors (661,504 B or 530,432 B). These are calculated from the loader and package layout, not runtime measurements.

The current physical VRAM budget remains 1 MiB at 1024×512×16bpp. Two 320×240 framebuffers occupy 307,200 B. The texture page slots and CLUT area are shared/replaced across screen transitions; they are not the sum of all week packages. The common static menu/death graphics in the base generated header account for 644,528 B: buttons 55,296 B, row backgrounds 18,432 B, 22 death frames 168,960 B, DJ art 65,536 B, five title pages 327,680 B, and character icons 8,624 B. This is compiled image data, not a claim that every item is resident in VRAM at once.

### Occupancy interpretation

For W1–W4, W6–W7 and Weekend 1, the report distinguishes rectangle-area sum, rectangle union, transparent index-zero pixels inside frames, duplicates, UV bounds, and free texels outside the rectangle union. The W1 frame rectangles overlap in time and cover 564,255 texels by union; their summed rectangle area is 1,230,927 texels. The large difference is animation-frame overlap, not a page of free space. W2/W3/W4/W6/W7/Weekend1 rectangle unions are 357,794 / 476,391 / 540,526 / 329,364 / 262,144 / 501,760 texels respectively. None of those values alone demonstrates that a page can be freed.

The generic atlas scanner did not understand Week 5's seven-field frame records, so its first Week 5 row was empty and must not be used. A supplementary parser read all 79 records and the actual per-page CLUT rows. It found 613,346 texels in the union of W5 frame rectangles across 12 pages, 264,043 index-zero texels inside those rectangles, and 173,086 texels outside the union. These are non-overlapping categories except that transparent texels are contained within the rectangle union. The 173,086 scattered texels are not a free page. The accurate Week 5 contact sheet and frame legend use the correct page palettes.

## Source resolution findings

The source images intentionally have different pixel densities, canvas sizes, aspect ratios, and world-space scales. A single raw output width would not harmonize them. The useful comparison is source-frame dimensions and trim/pivot, converted rectangle dimensions, authored stage scale, camera zoom, and final displayed pixel dimensions at 320×240.

Examples from the pinned stage JSON and source images:

| Scene/source layer | Official source image size | Official transform from pinned JSON | Static conversion/runtime observation |
|---|---:|---|---|
| Week 1 stage | back and curtains 2,560×1,400; front 2,560×581 | camera zoom 1.1; layer scales 1/1.1/0.9; layer scroll 0.9/1.3 | PS1 packs the stage across indexed 256×256 pages; it is not a single 320×240 bitmap. |
| Week 2 Halloween stage | AnimateAtlas `spritemap1.png` 3,924×2,256; sequence metadata in `Animation.json` | stage position `(-395,-505)`, scale 1, camera zoom 1.0 | PS1 represents the room as two tiled 256-wide stage frames and draws lightning separately; the full atlas animation is not the same data shape as a static scene plate. |
| Week 3 sky/city/train | sky 1,729×955; city 2,271×809; train 4,096×512 | sky scroll 0.1; city/windows 0.3; behind-train/dock 1.0; camera zoom 1.1 | PS1 retains separate city/front tiles and a separately positioned train, but the bridge pixels are baked into the city layer. Its camera zoom is 640/256 (2.5), with custom city origin offsets; this differs from the original stage zoom and should be compared in screen-space, not by matching source pixel dimensions. |
| Week 4 limo | sunset 1,968×1,313; background limo 4,096×2,048; front limo and hench atlas 2,048×2,048 | camera zoom 0.9; background limo and dancers scroll 0.4; front limo scroll 1.0 | PS1 has individually placed/animated front and far layers; its generated character frame dimensions are fixed-size crops, while the final stage/camera coordinates include user-tuned Week 4 offsets. |
| Week 5 Christmas mall | walls 3,102×1,840; upper/lower crowd atlases 4,096×2,048; escalator 3,700×1,775 | camera zoom 0.8; walls scroll 0.2; upper crowd 0.28; escalator 0.3; lower crowd 0.9 | The v171 conversion makes the backplate 256×192 using aspect-fill and a centered crop (about 21% of source width removed). Runtime applies a 460/256 camera zoom and separate art-scale compensation. Other props are independent indexed frames with separate offsets and scales. |
| Week 6 school | native pixel-art layers include 466×161 sky, 511×161 school, 3,591×1,538 trees | authored layer scale 6; parallax varies 0.2–1.0 | PS1 currently renders a precomposed full-screen 320×240 plate and fixed-size character rectangles. The layer structure and pixel-art density cannot be compared by raw source file size alone. |
| Week 7 tank | sky 1×954 plus 1,951×531 mountains, 1,597×726 buildings and 1,920×1,080 ground | camera and layer parallax range from 0 to >1; source audience uses separate high-Z props | PS1 uses two 256×240 stage tiles as a precomposed 4:3 battlefield. Source foreground/audience depth and PS1 composition are not one-to-one layers. |
| Weekend 1 streets/Blazin | streets skyline 2,654×1,040, foreground 2,901×1,299; Blazin sky 1,387×495 and street 1,629×779 | street stage has multiple parallax factors; Blazin plate uses 1.75 scale | PS1 currently draws two fixed 256×240 plates for each variation and a small selected set of character frames; it does not reproduce every source street layer independently. |

Week 1 images resolve from `assets/shared/images/` rather than `assets/preload/images/`; Week 2 uses AnimateAtlas rather than a simple PNG/XML pair. The corrected inventory searches these paths and includes their source dimensions. A naive `assets/preload/images` scan would miss both; that is not evidence their source art is absent.

### Concrete Week 5 resolution ratio

`bgWalls.png` is 3,102×1,840 (aspect 1.686). The PS1 source plate is a 256×192 frame (aspect 1.333), generated with `force_original_aspect_ratio=increase` and a centered crop. It is not stretched, but it discards horizontal source content to fit the 4:3 plate. Current scene code then multiplies the frame by art-scale 368/256 and camera zoom 460/256, giving a nominal 660×495 destination quad before screen clipping and beat pulse. This figure describes the quad; it does not claim the full quad is visible. It is a high-priority source-to-screen comparison point for any later resolution pass.

## Original-stage data versus PS1 scene code

The original files are `assets/preload/data/stages/*.json`; runtime rendering lives chiefly in `ps1/spu_probe.c`. The PS1 code uses explicit per-week renderers, not a common stage JSON interpreter. It preserves some source positions/parallax and manually adapts or precomposes other scene layers.

- **W1–W3:** original stages define their own camera zooms, prop origins and scroll factors. W2 is a one-atlas room with a separate lightning overlay. W3's original city/train depth is partially consolidated; the PS1 train and dock remain separate but the city/bridge composition is baked together.
- **W4:** the PS1 scene retains the main limo, distant limo and dancers as separate elements and uses separate camera offsets. The generated header contains the current user-tuned anchors. These values are adapted 4:3 coordinates, not raw original-stage coordinates.
- **W5:** source `mallXmas.json` has camera zoom 0.8 and props at walls `(-630,-492)`, upper crowd `(-396,-98)`, escalator `(-1100,-540)`, tree `(370,-250)`, lower crowd `(-300,120)`, and Santa `(-840,150)`, each with authored scroll and scale. Runtime maps positions by 1/10, uses Q8 scroll factors and camera zoom 460/256, then applies independent art-scale and editor transforms. The position and size pipeline therefore has multiple conversion factors; auditing only the header offsets misses the dominant scale/crop contribution.
- **W6/W7/Weekend 1:** current PS1 code uses full-screen or paired precomposed plates with hard-coded screen rectangles. The original stage JSON describes multiple independently parallaxed props. The adaptations are intentionally simpler and are the largest structural differences to account for before harmonizing visual density.

### Audit conclusion

There is no single “asset resolution” defect shared by all weeks. The build has several distinct pipelines: trimmed packed sprites, aspect-filled 4:3 backplates, tiled rooms, and precomposed full-screen scenes. Applying one uniform resize would erase intentionally different depth and pixel-art styles. A useful next comparison should report, per visible layer: source canvas/trim/pivot, converted UV rectangle and CLUT, conversion crop or padding, authored stage scale/scroll/z, PS1 scale factors and anchor, and predicted 320×240 destination bounds. Changes should follow that table one scene family at a time.

## Editor state

The v183 CMake cache has `FUNKIN_PS1_WEEK5_COMPOSITION_EDITOR=ON` and `FUNKIN_PS1_SCENE_DEMO_DEFAULT=ON`. The repository CMake defaults for both the Week 4 and Week 5 editors and scene demo are OFF, but the delivered v183 build cache explicitly enabled the Week 5 editor. The normal non-editor build configuration should set:

```text
-DFUNKIN_PS1_WEEK5_COMPOSITION_EDITOR=OFF
-DFUNKIN_PS1_WEEK4_COMPOSITION_EDITOR=OFF
-DFUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF
```

No build cache, source, or BIN was changed in this audit. These flags should be applied to a new uniquely named build/output only when a follow-up build is requested; previous deliveries must remain untouched.

## Reproducible audit outputs

Static files were written outside the repository under `C:/Users/Manau47/Documents/Codex/ps1-asset-scene-audit-v183/`:

- `atlases/atlas-audit.json`, `atlases/atlas-pages.csv`, and annotated sheets for base/W2–W7/Weekend 1;
- `week5-accurate-clut-atlas.png` and `week5-frame-legend.csv` (supplemental W5 parser with all 79 seven-field records and the actual per-page CLUTs);
- `week5-v183-page-metrics.csv` (W5 rectangle union, transparent index-zero texels and free area);
- `static/` menu/death/DJ/icon sheets and `static-assets.json`;
- `official-stage-source-inventory.csv` (pinned JSON transforms plus source PNG dimensions).

The graphics outputs are contact sheets, not a build or an emulator capture. No source or asset conversion, compilation, DuckStation run, runtime memory measurement, or console test was performed.
