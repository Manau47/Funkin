# Week 4 layered composition — v151

## Scope and cause

The user confirmed the v150b BF correction, while reporting that the Week 4
composition remained wrong. Inspection found three concrete integration
problems in the v147/v148 compositor and renderer:

- The background-limo frame was extracted at 455×79 but composited as 222×39,
  cropping most of it.
- The foreground limo was extracted into a 44×88 box despite its 2048×646
  source aspect ratio, reducing it to a narrow stamp.
- GF, the two limousines and the scenery were flattened into the same stage
  texture, then GF was drawn on top. That could not represent the reference's
  depth order where the main limo occludes GF.

## Change

The reproducible compositor [`../ps1/compose_week4_layers_v151.py`](../ps1/compose_week4_layers_v151.py)
rebuilds the two existing scenery pages from the pinned official sunset,
background limousine and four official henchmen. It now composites the full
455×79 far-limo extraction at its intended dimensions. The foreground
`Limo stage` image is stored at 240×76 in free space on logical page 7, which
already contains the Mom icon.

The scene draw order is now: distant scene and dancers, GF, foreground limo,
Mom, BF. The foreground limo uses world position `(16,152)` and the existing
Week 4 camera/zoom. Its texture shares the existing Week 4 page and CLUT, so
this change adds no texture page or CD read. The v150b BF page mapping and retry
restore remain in place.

No gameplay, chart, audio, actor dimensions, camera targets, or animation
timings were changed. The distant henchmen remain static in this pass; wheel
rotation, wind-blown hair and foreground passing effects are not claimed as
implemented.

## Static package checks

- Input package: v149 `W4SCENE.BIN`, 524,800 bytes, 8 pages plus CLUT.
- Output package: 524,800 bytes, still 8 pages plus the same CLUT.
- Pages 2–6, Mom icon pixels, all page-7 texels outside the foreground-limo
  rectangle, and the CLUT compare byte-for-byte with the input.
- Only stage pages 0–1 and the new 240×76 rectangle on page 7 change.
- Output package SHA-256:
  `CE3872A1C10E14AEDE358F3D9824000C7DC4199E1EEF58298B4E65AE7B23F743`.
- Pinned assets submodule: `724eba9de9e76761d9cefd52169926bc51c760a5`.

The native 320×240 PNG in the generated package is a static background preview,
not a screenshot from the executable.

## Build and delivery

- PSn00bSDK 0.24 and GCC 12.3, Debug configuration; diagnostics are OFF by
  default and Dad lanes remain enabled.
- CMake dry-run: 5 actions (the known BF-pose sidecar generator, two C object
  compilations, link, ISO build). No audio, chart, or general art conversion
  was scheduled. The sidecar hash is unchanged.
- Compilation and ISO generation succeeded. The SDK `stream.c` emitted its
  existing volatile-qualifier warnings.
- Executable SHA-256:
  `503F5359B150327E1DF96667C591ADD8D6FF63B2A6001ED2F0E26A37DDD2EF95`.
- Delivery BIN SHA-256:
  `CF400E0915039BF69FE9790337DEC6ADF2282D0DE467D9B26C723B3CA2D57871`.
- Delivery CUE SHA-256:
  `A8DFF2001A5344E38916D95FE451A8307E574A1CB7165A36C9A2F20E90FCC3B7`.
- ISO root static check: `SYSTEM.CNF;1` is first and `FUNKIN.EXE;1` second.
- Build tree: `C:/Users/Manau47/Documents/Codex/week4-v151-build/`.
- Delivery directory: `ps1/build/week4-composition-v151/delivery-v151-composition-corrected/`.

No DuckStation execution or console test is claimed for v151. The user must
load the CUE to judge the composition; this correction is not visually
validated until that test.
