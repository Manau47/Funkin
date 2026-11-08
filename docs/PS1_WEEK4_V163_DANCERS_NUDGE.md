# Week 4 v163 — dancers 10 pixels farther right

Starting from v162, the four distant dancers move another 10 screen pixels to
the right. At W4 zoom 524/256 (2.046875×), the change is `dx=+5` world units,
projecting to about 10.2 screen pixels. Their cumulative X offset is now +11
world units from the original scene anchor.

All other v162 composition, camera, sprites, animation, gameplay, charts, and
audio are preserved. Editor/demo/diagnostics remain disabled. Build and static
ISO checks are recorded in the source manifest. DuckStation validation is
pending; no runtime or console test is claimed.
