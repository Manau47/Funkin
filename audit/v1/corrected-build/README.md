# Corrected v1 build audit

This directory is authoritative for the corrected v1 BIN/CUE delivered on 2026-11-08. The prior `audit/v1/final-build/` content records the first candidate, which incorrectly repacked Week 6; it is retained as historical evidence only. The corrected build repacks Week 2 and Weekend 1, and restores Week 6 to the v183 reference. See `docs/PS1_ASSET_HARMONIZATION_V1.md` for scope, results and user-test status.

- `repack-simulation.csv`: static MaxRects estimate for all independent packages.
- `repack-week2.json`, `repack-weekend1.json`: exact package sizes, hashes, retained references, pixel/CLUT verification and static savings.
- `resource-hashes.csv`: active scene package/header comparison to v183.
- `build-manifest.csv`: exact build cache and final delivery artifact hashes.

The corrected build also has regenerated frame fiches and annotated page sheets under `atlases/`, based on the actual corrected headers and binaries. Its atlas audit includes page occupancy, transparent index-0 texels, rectangle union, holes and duplicate payloads. `converted-frame-fiches.csv` and `source-layer-fiches.csv` cover 529 converted frames and 76 stage layers. `dedup-pack-simulation.csv` is an alias-only shelf estimate; use `repack-simulation.csv` for the fixed-stage MaxRects results that were actually applied.
