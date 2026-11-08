# Asset harmonization v1 audit outputs

These reports are generated from the pinned v183 converted data and the v1 Week 6 lossless repack. They are static analysis artifacts, not runtime captures.

- `source-layer-fiches.csv`: source stage dimensions and transform metadata.
- `converted-frame-fiches.csv`: frame UV/page/CLUT/trim/indexed-pixel data for v1.
- `atlases/`: annotated native 256×256 atlas pages and legends for scene atlas families; `static/` contains fixed menu/game-over resources where parsable.
- `resource-hashes.csv`: v183-to-v1 package product comparison. Header plus 131 products: 129 identical, 2 intentional Week 6 changes.
- `dedup-pack-simulation.csv`: static potential only; not a claim that all listed hypothetical layouts fit runtime page ownership.
- `atlas-page-measures.json`: page occupancy/transparent-index measurements for the actual v1 packages.
- `build-manifest.csv`: build options and delivered artifact hashes.

W1 is not transformed. It is the visual reference. Week 6 is the sole asset package changed in v1; its pixels and CLUT remain byte-identical in content, while page locations/UVs and exact duplicate-cel references are repacked.
