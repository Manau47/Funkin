# PS1 Week 2 framing / audio-synced GF — v106 candidate

## Source and scope

- Branch: `ps1-port`
- Source commit: `e8482b401fcb1e266c63214b6c8bb9d81314159b`
- Previous source: `a12b515`
- Changed source file: `ps1/spu_probe.c`
- Diagnostics: disabled by default; no diagnostic sheet or autoplay.
- This build changes only Week 2 camera zoom (Q8 582 → 384) and title-screen GF timing (frame-loop estimate → `Stream_GetSamplesPlayed()` at Freaky Menu's official 102 BPM). Character placements, charts, input, gameplay judgements, health, audio stream content, and camera focus events are preserved.

The Week 2 chart renderer already uses each selected chart's tempo map for GF's animation. That includes Monster's in-song BPM changes. The title menu uses the pinned `assets/preload/music/freakyMenu/freakyMenu-metadata.json` value of 102 BPM. Week 2 character anchor values remain those derived from `assets/preload/data/stages/spookyMansion.json`; this change does not add an art layer or alter their relative positions.

## Build and reuse

- PSn00bSDK 0.24, GCC MIPS 12.3, CMake 4.5, Ninja.
- Dedicated build directory: `ps1/build/week2-scene-bpm-v106-20261031/` (ignored by Git).
- The dry-run had only two C compilations (`spu_probe.c`, PSn00bSDK `stream.c`) and a link. The actual target additionally generated the ISO. No image/audio/chart conversion ran.
- Week 1–3 base packages were copied from `ps1/build/main-entry-marker-v90-fcd8040/`; hashes of `bopeebo_visual_data.h`, `week1-scene.bin`, `week2-scene.bin`, `week3-scene.bin`, `week1_catalog.h`, `menu.vag` and `menu_audio_data.h` matched the prior v105b package exactly. For example, `week2-scene.bin` SHA-256: `3A4399DB5E58F05FD3902702960791D9134FF92EA3C97A845F7B574AF08B9439`.
- Preconverted Week 4–7 and Weekend 1 packages were also reused. No SDK, official assets, or generated resource payloads were added to Git.

## Delivered image

- CUE: `ps1/build/week2-scene-bpm-v106-20261031/delivery/fnf-ps1-v106-week2-bpm.cue`
- BIN: `ps1/build/week2-scene-bpm-v106-20261031/delivery/fnf-ps1-v106-week2-bpm.bin`
- BIN: 337,900,080 bytes, SHA-256 `85A4C9AA43D10CBDBB916116A2FB093888C26ED0248301A04D2949187B9ABFFC`.
- CUE: 85 bytes, SHA-256 `590747A7B5E4B31A6F052976D9DCDA95A7ACD579A0F29A04B8F2866A45673476`.
- `SYSTEM.CNF` contains `BOOT=cdrom:\FUNKIN.EXE;1`. The raw mkpsxiso root directory had `SYSTEM.CNF` at record 93; the new, separate delivery copy places it first and `FUNKIN.EXE` second using `ps1/diagnostics/reorder_iso_system_cnf.py`. The raw build BIN remains preserved.

## Resource budget and validation

The ELF resident sections total 922,442 bytes: `.text` 83,596, `.rodata` 796,204, `.data` 2,112, `.sdata` 382, `.sbss` 456, `.bss` 39,692. The 96 KiB audio ring, one-song-at-a-time chart/audio loading, SPU allocations, and 655,360-byte gameplay texture map are unchanged from v105b. These are linked/static figures, not measured runtime peak RAM or frame time.

Compilation succeeded, and the ISO directory was checked/reordered. Codex did not run this build in DuckStation. The user will load the supplied CUE and confirm boot, all three Week 2 compositions, GF synchronization on Spookeez/South/Monster and the title screen, then check that other weeks/gameplay remain intact. No user validation or real-console test is claimed yet.

The reference screenshots were available in chat and the existing contact sheet was used. The supplied video was not accessible at its local path during this session, so no new timestamped frame/video analysis is claimed.
