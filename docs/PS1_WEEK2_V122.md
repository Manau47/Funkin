# Week 2 room GPU clipping — v122

## Change

The user reports that v121 still shows lightning without the static room. Since the X repositioning had no effect, v121's crop-only hypothesis was insufficient. v122 keeps v121's 2.25× zoom and shared background/lightning world transform, but changes how the two static room tiles are submitted: CPU code clips each tile to the 320×240 display rectangle and computes matching cropped UVs, so the GPU receives only the visible FT4 instead of a 576×576 textured polygon extending beyond the viewport. This specifically tests the rendering path for oversized clipped textures; it does not change the source assets, CLUT, tint, camera, lightning primitive, audio or gameplay.

## Build and validation

Build with PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, Debug, in the fresh directory `C:/Users/Manau47/Documents/Codex/b122w2`. Ninja dry-run listed only `spu_probe.c`, SDK `stream.c`, link and CD image; no conversion jobs. Reused `week2-scene.bin` with SHA-256 `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`. Preserve raw ISO output in `delivery-v122-pre-rootfix/`; the delivered image uses `reorder_iso_system_cnf.py --exe-after-system-cnf`.

Compilation succeeded; only the SDK's existing `volatile` qualifier warnings appeared. Static disc checks report 117 root files, `SYSTEM.CNF;1` first, `FUNKIN.EXE;1` second, and 338,203,488 bytes.

- BIN SHA-256: `A2F133346B1A636D56E42CE2AB621D6339F89062E1B13FD88775E8EF3CCCBA7A`
- CUE SHA-256: `ED7CD8E31BACDDD2F536505D5D25E763FD93C3F254CC2C5003A2F239A9E8CD2D`
- Executable SHA-256: `354F5F594087370A53EFCAC50589F7F3BE54D496B1C44678328A2F78F3C2CC21`

Delivered files:

- [`funkin-ps1-week2-v122.cue`](../ps1/build/week2-background-v122-gpuclip-20261031/delivery-v122-rootfix/funkin-ps1-week2-v122.cue)
- [`funkin-ps1-week2-v122.bin`](../ps1/build/week2-background-v122-gpuclip-20261031/delivery-v122-rootfix/funkin-ps1-week2-v122.bin)

User validation: the user confirms that the static decor is visible again and the lightning animation appears correct in DuckStation. The decor still needs to move about 20–25 screen pixels right; v123 applies that framing adjustment while moving the lightning in lockstep. No real-console test is claimed.
