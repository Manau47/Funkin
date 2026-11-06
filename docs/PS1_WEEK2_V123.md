# Week 2 backdrop horizontal adjustment — v123

## Change

The user confirms that v122 restored the static room and that the lightning animation looks correct. The room should move approximately 20–25 screen pixels to the right. At the 2.25× background scale, v123 increases the shared background/lightning world-X offset by 10 units, corresponding to 22.5 screen pixels. The static room and lightning remain aligned. The clipped-quad rendering path, UV handling, background zoom/tint/Y placement, character cameras, charts, timing, gameplay and audio remain unchanged.

## Build and validation

Build in fresh directory `C:/Users/Manau47/Documents/Codex/b123w2` with PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, Debug. Dry-run showed only `spu_probe.c`, SDK `stream.c`, link and ISO creation; no conversion. Reused the existing converted packages, especially `week2-scene.bin` (SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`). Raw ISO is preserved separately; final root-fixed image has 117 files, `SYSTEM.CNF;1` then `FUNKIN.EXE;1`, and size 338,203,488 bytes. Compilation succeeded with only the SDK's existing `volatile` qualifier warnings.

- BIN SHA-256: `C1F13CEBF9FBCCA842BFC44032B8B62AD74389110F1C3E11922F77C1D0226222`
- CUE SHA-256: `3FA0273674A9AF41597C487913C6100B71E16E2B66E9A92EA7B72635372C1C1CDC`
- Executable SHA-256: `E9B3044BC94E96A171B2B53C5980B515EF769E864BF5E58083FD7A6FF0753991`

- [`funkin-ps1-week2-v123.cue`](../ps1/build/week2-background-v123-shift-20261031/delivery-v123-rootfix/funkin-ps1-week2-v123.cue)
- [`funkin-ps1-week2-v123.bin`](../ps1/build/week2-background-v123-shift-20261031/delivery-v123-rootfix/funkin-ps1-week2-v123.bin)

DuckStation validation remains pending user confirmation; no real-console test is claimed.
