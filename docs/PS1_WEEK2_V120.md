# Week 2 background zoom — v120

## Change

v119 was confirmed by the user to show the Week 2 background with lightning working. v120 applies the requested additional 1.5× zoom to the background and its aligned lightning layer: the static background base scale changes from Q8 `384` (1.5×) to Q8 `576` (2.25× total). The existing beat pulse remains additive. The existing background Y offset (`85`) and camera transform/origin are preserved.

No character camera targets, character or note transforms, charts, timing, gameplay rules, audio, tint (`192`), lightning timing, or source assets changed. Reusing the v119 origin means this is a tighter crop around the existing transform; edge clipping is expected to increase. Whether the new crop is visually preferable must be confirmed in DuckStation.

## Build and retained inputs

- Source branch: `ps1-port`, based on `64e87d8` (`Increase Week 2 background contrast`); the v120 source snapshot is committed on this branch as `Zoom Week 2 background for v120`.
- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, Debug.
- A new build directory (`C:/Users/Manau47/Documents/Codex/b120w2`) was used. Ninja dry-run listed only `spu_probe.c`, SDK `stream.c`, link, and CD image creation; no conversion jobs.
- Reused `week2-scene.bin` unchanged from `preconverted-base-v3`; SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`.
- Compilation and ISO generation succeeded. The SDK `stream.c` emitted its existing two discarded-`volatile`-qualifier warnings.
- The raw CMake ISO is preserved in `delivery-v120-pre-rootfix/`. As in v119, its root directory listed `SYSTEM.CNF;1` at position 93. The delivered copy was made by `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`; static checks report 117 root files, `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second, image size 338,203,488 bytes.

Delivered files:

- [`funkin-ps1-bopeebo-playable.cue`](../ps1/build/week2-background-v120-zoom-20261031/delivery-v120-rootfix/funkin-ps1-bopeebo-playable.cue)
- [`funkin-ps1-bopeebo-playable.bin`](../ps1/build/week2-background-v120-zoom-20261031/delivery-v120-rootfix/funkin-ps1-bopeebo-playable.bin)
- BIN SHA-256: `6B483984B4C6D96AEF4055A8E8AC1BA962A21A7C97240A0DE1BC69F5460D8D73`
- CUE SHA-256: `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`
- Executable SHA-256 before ISO packaging: `816BC11D3EFB879D585CAF5370095C3A32EF75D39888FA331F1C0D84768EEAAF`

## Validation status

Compilation and static disc layout checks succeeded. The user subsequently tested v120 in DuckStation and reported that the static background disappeared again while lightning remained visible. Therefore v120 is not visually accepted. The crop calculation explains the regression: at the Dad focus, the 2.25× scale with the unchanged origin showed approximately source x=52–194, cutting off most of the distinctive left window. v121 preserves the larger zoom but moves the backdrop and lightning together to restore the previous left crop boundary. No real-console behavior is claimed.
