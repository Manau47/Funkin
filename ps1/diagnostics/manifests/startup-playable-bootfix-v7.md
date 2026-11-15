# Playable boot-order correction v7

- Purpose: provide the normal playable build after the user observed the v6b fuchsia checkpoint. The fuchsia observation means the BIOS launched the EXE and it reached the first title frame. The remaining diagnostic hold is disabled in this build.
- Branch: `ps1-asset-harmonization-v1`.
- Source commit: `dcdf53c3fa2aab734d6f2b8c05c4cf1d23f07f0a` (framebuffer-aware probe code; no gameplay/source edits for v7).
- Build configuration delta from v6b: only `FUNKIN_PS1_STARTUP_MAIN_MARKER=OFF`. Diagnostics, scene demo and composition editors remain OFF; Dad autoplay lanes remain ON; playable 4-channel configuration remains enabled.
- Build cache/toolchain: existing `ps1-asset-harmonization-v1-week2-bf-detail-v1-build`, PSn00bSDK 0.24 Win32 MIPS CMake/Ninja. `PSN00BSDK_LIBS` for configure points to the SDK `lib/libpsn00b` directory.
- Dry-run after configure: compile `spu_probe.c`, compile SDK `stream.c`, link, package ISO. No scene, graphics, audio or chart conversion. The SDK stream source was recompiled after CMake regenerated the build graph; it reports the same existing discarded-volatile-qualifier warnings.
- Actual build: succeeded. All scene/audio/chart source files reused from the cache. ISO was reordered with `reorder_iso_system_cnf.py --exe-after-system-cnf`: `SYSTEM.CNF;1` at root entry 1, `FUNKIN.EXE;1` at entry 2.
- Delivery: `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-playable-bootfix-v7-delivery/`.
- ISO size: 340,016,880 bytes. PS-X EXE size: 1,021,952 bytes.
- BIN SHA-256: `13EDEDA4010C3B2B146A70FEC802F10AD405E7EF54ACD71813D2C2934428A5E6`.
- CUE SHA-256: `C5AE901D116441C2C84DC58B658545624168F87FADA4376B543090D51ACCA926`.
- PS-X EXE SHA-256: `8B2047AEECF0EDC318D6E485C7D2EEE5F1CE1A4DDC60E23EBB72B2C6FF5EAB02`.
- Runtime: compilation/package checks passed. Not yet loaded in DuckStation by the user. No emulator or console result is claimed.
