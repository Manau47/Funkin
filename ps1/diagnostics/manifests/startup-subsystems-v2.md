# Startup subsystem checkpoints v2

- Purpose: isolate the next startup step after the user-observed green marker in `startup-video-init-v1`.
- Branch: `ps1-asset-harmonization-v1`.
- Source commit containing diagnostic code: `ecd4139394cbed622ba779c8cf901a8d1d0147fc`.
- Toolchain/build: existing PSn00bSDK 0.24 Win32 + MIPS `mipsel-none-elf` + CMake/Ninja cache in `ps1-asset-harmonization-v1-week2-bf-detail-v1-build`; incremental build, no cache reset.
- Relevant options: `FUNKIN_PS1_STARTUP_MAIN_MARKER=ON`; `FUNKIN_PS1_STARTUP_BEFORE_BSS_MARKER=OFF`; `FUNKIN_PS1_STARTUP_AFTER_BSS_MARKER=OFF`; `FUNKIN_PS1_DIAGNOSTICS_DEFAULT=OFF`; `FUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF`; Week 4 and Week 5 editors OFF; Dad lanes ON.
- Runtime sequence in `main()`: raw GP0 marker; `init_video()` then GREEN; loading screen returns then BLUE; `SpuInit()` then YELLOW; `reset_spu_channels()` then MAGENTA; `CdInit()` then CYAN; controller initialization then WHITE; `CdControlB(CdlPause)` returns 1 then RED, otherwise ORANGE. Each marker is an opaque full-screen color and the diagnostic holds at that stage.
- This build does not initialize scenes, read scene/chart/assets, or start music/gameplay. It does not alter art, audio, charts, or gameplay code/data.
- Dry-run: only `spu_probe.c` compile, executable link, and ISO generation. Actual incremental build succeeded. Disassembly confirms the staged calls and marker path. No resource conversion was run.
- ISO: 117 root payloads. `SYSTEM.CNF;1` entry 1, `FUNKIN.EXE;1` entry 2. Compared with the preceding video-init v1 ISO, all payloads match except `FUNKIN.EXE;1`.
- Delivered files (outside Git): `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-startup-subsystems-v2-delivery/`.
- BIN SHA-256: `2896E4199DAC98AA856B208FE47007F229C360D6FF9FD69F82945ED008DBED81`.
- CUE SHA-256: `74E40A5374250428F9BD382F9DB5A174E4389A483D09F65C8C216B71D41CF0DA`.
- PS-X EXE SHA-256: `AE7DFC9D2C11FC977C45671330625FDBF3E2F7E3BB27483FAAFFD0E1AA231681`.
- Runtime status: user confirmed the previous v1 green screen, establishing that `init_video()` returns. This v2 image is awaiting the user’s DuckStation observation. No emulator or console execution is claimed for v2.
