# Startup base atlas probe v3

- Question: after the user-observed red checkpoint (successful `CdControlB(CdlPause)`), does the real base Week 1 atlas loader return?
- Branch: `ps1-asset-harmonization-v1`.
- Source commit with code: `60baf8af4b319b45b2458da9d025e8a9367dd623`.
- Previous checkpoint result: user reported v2 remains RED. In v2 red means `CdControlB(CdlPause)` returned 1.
- Build cache/toolchain: existing `ps1-asset-harmonization-v1-week2-bf-detail-v1-build`; PSn00bSDK 0.24 Win32, MIPS `mipsel-none-elf`, CMake/Ninja. No cache reset.
- Options preserved from v2: main startup marker ON; before/after-BSS markers OFF; diagnostics and scene demo OFF; editors OFF; Dad lanes ON.
- Single new step after red: GRAY marker, call `load_bopeebo_visuals()` (reads `W1SCENE.BIN` pages, uploads base texture pages and CLUTs to VRAM, waits for GPU transfers, releases one temporary page buffer); LIME on successful return; AMBER on false return. Gray remaining means this loader did not return. The probe then holds permanently.
- Nothing after this loader is executed: no menu loading, music streaming, chart loading, scene/gameplay loop.
- Dry-run/actual build: three tasks only—compile `spu_probe.c`, link ELF, create ISO. No asset conversion. Build succeeded. Static disassembly confirms calls to `CdControlB` and `load_bopeebo_visuals` in the diagnostic path.
- ISO root order verified by the reorder tool: 117 entries, `SYSTEM.CNF;1` entry 1 and `FUNKIN.EXE;1` entry 2. Delivery produced in a distinct directory; v2 was not overwritten.
- Delivery directory: `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-startup-base-atlas-v3-delivery/`.
- BIN SHA-256: `77F5F950264472EFE4C0C092E35696098833B86324947CB97068AC52C1CEF80A`.
- CUE SHA-256: `58E8D0E7D012312AEBF990D03962951AFB32BED6C0B072A3AF76B4A564CEEF38`.
- PS-X EXE SHA-256: `4241B17E17923656B786A7CC520B75729AE263B19C570C5ED227C676D4DEFEF4`.
- Runtime status: awaiting the user to load this CUE in DuckStation and report the final persistent color. No emulator execution or console test is claimed by the assistant.
