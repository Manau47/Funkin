# Week 4 composition test v155 — values copied from DuckStation

## Purpose

v155 is the first test build with the user's current Week 4 layer adjustments
loaded by default. It is based on the v154e scene-composition tuner. The only
runtime change is the initial transform values below; scene art, layering,
camera behavior, chart, gameplay rules and audio data are unchanged.

## Values observed

The values were read from DuckStation's Memory Scanner while the v154e build
was running. The scanner addresses are physical RAM offsets; the matching
MIPS KSEG0 symbols are given for reference. Signed offsets are 16-bit values;
scale is unsigned Q8 (`256 = 100%`, `512 = 200%`).

| Layer | X offset | Y offset | Scale |
|---|---:|---:|---:|
| Stage | +18 | 0 | 100% |
| Camera | +6 | 0 | 100% |
| Far Limo (combined far limo + dancers) | -14 | -8 | 200% |
| GF | -24 | +6 | 100% |
| Front Limo | +4 | +26 | 100% |
| Mom | -2 | 0 | 100% |
| BF | -30 | +22 | 100% |

Memory addresses:

- `week4_edit_dy`: physical `0x00111448`, KSEG0 `0x80111448`;
- `week4_edit_dx`: physical `0x00111458`, KSEG0 `0x80111458`;
- `week4_edit_scale_q8`: physical `0x00108DC8`, KSEG0 `0x80108DC8`.

Each table is seven consecutive halfwords in the layer order shown above.
These are live values copied from the active v154e process, not values inferred
from a generated mockup. No DuckStation memory values were written by the
scanner during capture.

## Far-layer quality follow-up

The values above make the current far-plane sprite twice its v153 base scale;
they do not restore detail already lost during conversion. Static inspection
of `ps1/compose_week4_layers_v153.py` shows the combined far layer is packed as
one `240x64` frame, with the official distant limo extracted into `240x42`
and each dancer into `40x32`. The pinned source atlas metadata reports the
distant limo cel as `2199x379` within a `4096x2048` PNG and the hench cel as
`394x394` within a `2048x2048` PNG. Thus the current converted art was reduced
substantially before it was enlarged for this test. Its shared `240x64` atlas
rectangle and Week 4 CLUT are reused unchanged here.

A later quality pass should re-export the far limo and dancer cels at a larger
native working size, preferably as separately addressable primitives so their
placement/scale can be tuned independently. That will require a measured atlas
packing and VRAM/CLUT budget; no such conversion or layout change is included
in v155. The current distant-scroll factor remains `102/256` (~0.4), matching
the pinned stage data, so this build does not move the far plane closer in Z.

## Build and validation

- Base build: v154e, preserved under `C:/Users/Manau47/Documents/Codex/week4-composition-tuner-v154/`.
- Source base commit: `7057882fa4c481fb878de4cc27d3a827179f7ddd`, plus the exact
  pre-existing local work captured by the v154e source archive.
- Toolchain/configuration: PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake/Ninja,
  Debug, Week 4 composition editor ON, scene demo ON, diagnostics OFF.
- Incremental dry-run: one C compilation, link and ISO generation only; no
  asset, chart or audio conversion was scheduled. ISO generation repackages
  the existing resources into the disc image.
- Week 4 package SHA-256: `C7B0B033426833CC0A6F054F31C3987FCE2C77A8B82F15337743702EC55CB6D6`.
- BIN SHA-256: `4952F4EA3DD84A2218EF2FEA1E586C2BD5FF2ECB01F7532C097C3510FD9624C0`.
- CUE SHA-256: `6F13A11528DC1C9F1BEE8AE54532862F7C7B9158429ECAC1AFF244CC89BBA48A`.
- ISO root directory check: 117 files; `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second.
- Source/configuration snapshot: `C:/Users/Manau47/Documents/Codex/week4-composition-tuner-v154/source-v155/`;
  `spu_probe.c` SHA-256 `64EDBF56CF9DC266498C51B4DFE8870188B208C08604FDF01D51E950D43F50CB`.

Compilation and static ISO checks succeeded. The newly generated v155 CUE has
not been loaded or run in DuckStation. The displayed v154e session supplied the
live values, but that is not a runtime validation of the v155 build. No console
hardware test was performed.

## Manual test

Load `C:/Users/Manau47/Documents/Codex/week4-composition-tuner-v154/delivery-v155-values/funkin-ps1-v155-week4-values.cue`.
It opens with the composition editor hidden. During Week 4 gameplay, Select
opens the tuner; Triangle shows the transform summary, and Start pauses/resumes
the song and scene. The next check should compare the Far Limo/dancers at the
200% starting scale and confirm the full scene composition before changing art.
