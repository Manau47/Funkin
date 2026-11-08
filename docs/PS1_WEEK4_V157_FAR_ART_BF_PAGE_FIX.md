# Week 4 v157 — far-layer art and BF VRAM fix

## User report motivating this pass

The user reported that the far limousine/dancers still looked unreworked, could
not be enlarged enough in the scene editor, and BF showed the wrong sprite.
Current layer positions were judged mostly acceptable, so this build preserves
the v156c X/Y offsets and camera values.

## Asset audit and correction

The pinned official assets are at revision `724eba9de9e76761d9cefd52169926bc51c760a5`.
The earlier export had taken a 2218x384 limousine canvas down to 256x44 and a
517x410 dancer canvas down to 48x38. v157 exports the 12 unique dance cels at
72x57 (1.5x linear resolution, 2.25x texel area) and keeps the official
30-step left/right timing table. The far limousine retains four 24 fps cels
at 256x44 due to the 256-pixel texture-page width.

The editor scale ceiling is raised from 200% to 400%; its current layer values
and coordinates are unchanged. This permits further composition adjustments
without changing the default placement.

## BF sprite root cause

v156c mapped Week 4 logical page 8 (the far-limo atlas) onto physical texture
page 7 at VRAM `(768,256)`. That is the active BF atlas page in the common
visual table. Drawing BF afterward read that overwritten page, explaining the
incorrect character image. v157 packs the far-limo cels into the unused area
of Week 4 page 7, moves the foreground limo rectangle to the lower strip of
that page, and places the dancers alone on spare page `(896,0)`. Week 4
logical page 8 maps there; unload clears it, and the BF page is never leased.

The unused baked far-plane rectangle was removed from the repacked Week 4 page.
Pages 0–6 and the 512-byte CLUT are byte-identical to v156c. Package size drops
from 655,872 to 590,336 bytes (one 64 KiB page / 32 CD sectors less than v156c).
This is a storage and VRAM-page reduction; it does not change RAM scratch size,
SPU use, audio, chart, note layout, camera, gameplay rules, or current scene
positions.

## Controls

The Week 4 scene editor remains on Select. Start pauses/resumes the sample
clock; up/down selects a layer; left/right adjusts X; L1/R1 adjusts Y;
Cross/Circle adjusts scale; R2 selects fast steps; Square resets the selected
layer; Triangle shows the summary page. Scale can now reach 400%. Diagnostics
remain hidden at startup and scene demo remains enabled for composition work.

## Build and verification

Assets were regenerated only for the two far layers from the pinned official
PNGs/XML using the existing CLUT. Other converted resources, charts, and audio
were reused from the archived v156c package. Dry-run listed only C compilation,
link, and ISO creation. Build succeeded with PSn00bSDK 0.24 and MIPS GCC 12.3.0.
Static disc verification found 117 root files, with `SYSTEM.CNF;1` first and
`FUNKIN.EXE;1` second. No DuckStation or real-console run has occurred for
v157; sprite appearance, larger zoom range, and BF rendering await the user's
manual test.

Final test BIN/CUE: `C:/Users/Manau47/Documents/Codex/week4-composition-editor-v156b/delivery-v157b/`.
The previous v156c and first v157 deliveries/source snapshots remain untouched.
The final v157b source, config, package, and hashes are archived outside the
repository in `source-v157b/`.

Final recompile after source/archive alignment: v157b is the CUE to test. v157a remains preserved as the preceding generated image; it is superseded by v157b. The final v157b image has the same scene/resource changes and was rebuilt after the source comment and archive snapshot were aligned.
