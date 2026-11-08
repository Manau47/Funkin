# Week 4 v162 — GF and distant dancers adjustment

Starting from v161, GF moves down about 4 screen pixels and the four distant
dancers move right about 40 screen pixels. At the fixed W4 zoom of 524/256
(2.046875×), these are `dy=+2` world units for GF and `dx=+20` world units for
the dancers. GF's camera focus target continues to follow her adjusted anchor.

| Layer | v161 offset | v162 offset | Approximate visual delta |
|---|---:|---:|---:|
| GF Y | +6 | +8 | 4.1 px down |
| Distant dancers X | -14 | +6 | 40.9 px right |

All other v161 positions, camera settings, sprites, animation, gameplay, charts,
and audio are preserved. The editor/demo/diagnostic overlays remain disabled.
The build is not runtime-validated until the user loads it in DuckStation.
Source, configuration, assets, and hashes are archived in the external v162
snapshot and manifest.
