# Startup title checkpoint v6b (framebuffer-persistent)

- Diagnostic question: did the v5 title-render/present path return, or was the visible dark screen caused by a checkpoint drawn into a framebuffer that DuckStation was not displaying?
- Branch: `ps1-asset-harmonization-v1`.
- Source commit: `dcdf53c3fa2aab734d6f2b8c05c4cf1d23f07f0a`.
- Change from v5: the same startup stages and calls are retained. Only the checkpoint macro changes: raw GP0 fill commands paint both 320x240 framebuffer regions (VRAM y=0 and y=240), then wait for GPU completion, set the active display environment, unmask display and wait for VSync. This is intended to make the last stage visible across `display_frame()` swaps. No scene, gameplay, audio, chart, or asset data changes.
- User observation of v5: screenshot showed a dark navy screen with scanlines and no clear solid-color checkpoint. It does not identify which v5 stage ran. The double-buffer explanation is a plausible probe defect, not a confirmed cause of the application's startup problem.
- Build cache/toolchain: reused PSn00bSDK 0.24 Win32 MIPS CMake/Ninja cache in `ps1-asset-harmonization-v1-week2-bf-detail-v1-build`; playable target still has `GAME_STARTUP_MAIN_MARKER=1`, diagnostics/editor/demo defaults disabled.
- Dry-run for `ps1-bopeebo-playable-disc`: exactly compile `spu_probe.c`, link executable, and package CD image. No resource/audio/chart conversion was scheduled. The build output confirms only those 3 actions.
- Actual build: compile and link succeeded; ISO packaging succeeded. Root-order helper then placed `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second (source order had SYSTEM.CNF at entry 93). The first local packaging pass omitted the helper's `--exe-after-system-cnf` option; those outputs are preserved in the separate `...v6-delivery` folder and are not the test CUE. The corrected test is the v6b delivery below.
- Reused resources: all scene/audio/chart data came from the existing build cache; no regeneration. ISO size 340,019,232 bytes. PS-X EXE size 1,021,952 bytes.
- Delivery: `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-startup-title-frame-v6b-delivery/`.
- BIN SHA-256: `DDCE9B917188632FBEC5D2B570F4980E7F9C97DF903914ACE0B3C5434B7027F1`.
- CUE SHA-256: `4ACF8BBDB684FAB19611474F3D2E0D8F9EC9B826A1CFF18CB0EE506FCFCC9F3E`.
- PS-X EXE SHA-256: `54923C79015BF2B52ACF89EA3983A2580317475D51174904E3B3F1A3B62FE895`.
- Runtime: not executed in DuckStation by the assistant. Awaiting the user's manual observation. No console test claimed.
