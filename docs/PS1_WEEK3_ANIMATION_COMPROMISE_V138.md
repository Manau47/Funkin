# Week 3 animation sampling compromise — v138

## Goal and baseline

The user reported that Pico's animation and Girlfriend's hair reaction to the
passing train looked as if they were missing poses. v137b is the stable
reference for the currently accepted scene, audio, gameplay, and VRAM loading.
This iteration changes only Week 3 animation sampling/atlas packing and the
runtime frame selection. It has not been observed in DuckStation yet.

## Animation choices

- Pico idle now samples official source frames `0, 4, 8, 12` from the 14-frame
  idle. Four poses cycle evenly across a beat.
- Pico's four sing directions still use two representative official poses per
  direction, matching the compact BF singing treatment. Their samples are
  spaced farther apart through each original animation than the previous
  near-identical onset pair: left `31/39`, down `62/67`, up `48/55`, right
  `14/22`.
- GF's train hair-blow reaction uses four samples from the 30-frame official
  timeline (`124, 134, 143, 153`). The landing/hair-fall reaction uses six
  samples (`154, 160, 166, 172, 178, 183`). The original timelines are still
  sampled from the musical audio clock; their trigger and duration are
  unchanged.
- Transparent margins are cropped from the stored Pico/GF cels, while signed
  per-frame offsets preserve their original full-canvas anchors (Pico `72×84`,
  GF `87×79`). This is a storage optimization; the visible scale and pose
  placement are unchanged.

## Memory and conversion

The Week 3 character atlas remains four 8bpp pages. The separate BF backup
page is retained. `W3SCENE.BIN` remains `524,800` bytes, with four scene pages,
four character pages, and one CLUT. No additional VRAM page or audio buffer is
introduced.

The visual converter is monolithic, so one run regenerated its global header
and W1/W2/W3 packages in a new, isolated directory. The generated W1/W2 files
were not used. A copy of the existing preconverted base was made for this
build, replacing only `bopeebo_visual_data.h` and `week3-scene.bin`.

- W1 scene package remains byte-identical to v137b:
  `C2444F178F0A9A7F28B4B24476B9058E74FB15237DDD4BB786907F73A6CD0E8F`.
- W2 scene package remains byte-identical to v137b:
  `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- The four W3 stage pages and CLUT were copied from the approved base and are
  byte-identical. Only the four W3 character pages changed.
- Bopeebo's four-channel audio and Normal chart remain byte-identical to v137b
  (`stream-playable.vag` SHA-256
  `205EA3A13D2EBA739E250F4DA41AA44E5EABF78202EE0A1F81AB02B8647026D0`,
  `BOPN.BIN` SHA-256
  `371D38CA519219169BA195A31D1D805F94A52AA5F1F475AB0738EB316D175D27`).
- ELF text/data/BSS totals changed from `1,058,378` to `1,059,214` bytes
  (`+836` total); BSS remains `40,184` bytes. The added static frame trim
  metadata is compact (`int8_t` offsets) and no gameplay resource is made
  resident in RAM.

## Build and validation

Build: PSn00bSDK 0.24, GCC 12.3, CMake/Ninja, with the v137b settings and
diagnostics off. CMake uses the isolated preconverted base at
`ps1/build/week3-animation-compromise-v138/preconverted-base`. The dry-run
contained only `spu_probe.c`, link, and disc-image steps; it scheduled no asset,
chart, or audio conversion. The final incremental build compiled `spu_probe.c`,
linked, and created the CD image successfully. Existing SDK `stream.c` emitted
its two known `volatile` qualifier warnings during the initial build.

The ISO has 117 files; its delivery copy was checked with the project's
ISO9660 reordering tool: `SYSTEM.CNF;1` is root entry 1 and `FUNKIN.EXE;1` is
entry 2. The final BIN is `338,509,248` bytes.

- BIN SHA-256: `09CABCD4A323A7C662C5436E74994CD4C4669E5DE65E3AFC471A9F6C9CF3E375`
- CUE SHA-256: `29227A2C07AAE64828498B64FC24DBD85699561BD1E25AC1D1794A2C32F7ACB2`
- Delivery folder:
  `ps1/build/week3-animation-compromise-v138/delivery-v138-pico-gf-compromise-final/`

Compilation and static ISO checks pass. There has been no DuckStation run,
user listening/visual confirmation, or real-console test. The user will load
the CUE manually; animation pacing, Pico's poses, GF's train reaction, and
transition/audio regressions remain to be checked there.
