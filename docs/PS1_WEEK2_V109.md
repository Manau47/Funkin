# Week 2 permanent décor and thunder audio (v109b)

Date: 2026-10-31  
Branch: `ps1-port`  
Source base: `7821414` (v108 build configuration)
Implementation source commit: `d37b7c078423d4c0b14cb67c3e288bffc81997d2`

> **Erratum (v110b):** Although v109b's intermediate Animate preview showed the static window, its page package did not contain the composited static layers. `alpha_over()` returned a new buffer whose result was discarded. The user's report that the décor remained absent was correct. The v110b conversion assigns the composite, aligns it with the root-transformed atlas, and validates the packed stage pixels; see [`PS1_WEEK2_V110.md`](PS1_WEEK2_V110.md).

This is a new user-test candidate. It changes the Week 2 scene conversion and adds official thunder effects. Gameplay rules, charts, camera, timing, idle cadence, music stems, note rendering, and menu/gameplay transitions are unchanged.

## Fixes

The v108 converter attempted to draw the permanent Halloween stage by scaling the full atlas dimensions to the 362×256 scene. The Animate root instance transform (`AN.STI.SI.MX`, translation -538.7/-496.1) was omitted. As a result, the room/window/detail layers were misplaced or outside the useful stage image, leaving only the nearly flat background between flashes. v109b applies the authored root transform and the existing 1/7 stage scale to both the permanent composition and transient flash samples. The permanent base excludes the rig's transient `flash` layer, so the room and window stay visible without leaving the lightning illumination on between strikes. The added artwork is baked into the existing Week 2 stage pages; it does not add a VRAM page or a CD read.

The pinned Week 2 script precaches and randomly selects `thunder_1` or `thunder_2` when it plays a thunder strike. Those official OGG sources are now decoded to 22,050 Hz mono and encoded as one-shot SPU ADPCM payloads in the resident SFX bank. The audio trigger follows the same audio-sample/chart-beat strike schedule as the visual flash, so a render frame cannot retrigger one strike. The source script's first Spookeez strike at beat 4 is intentionally silent; subsequent strikes play a thunder variant. South and Monster use the port's existing deterministic visual schedule, with sound attached to those scheduled strikes. This is an approximation of the original randomized timing, not a port of its random interval selection.

Thunder uses the existing four-voice miss/SFX pool (voices 4–7), with a requested level of `0x2800`. The existing pool-wide `0x3000` volume ceiling scales overlapping effects to preserve mix headroom. Thunder is uploaded with the other resident SFX before gameplay; no concurrent CD access is introduced. Retry/state reset clears the last-strike guard.

## Resource and memory accounting

- Week 2 package remains 328,192 bytes, two stage pages plus three character pages. Only `week2-scene.bin` changed. Week 1's 655,360-byte scene, Week 3's 262,656-byte scene, the visual header, menu music and both game-over VAGi files were byte-identical to v108.
- The resident SPU SFX bank grows from 139,008 bytes to 269,056 bytes (two thunder payloads add 130,048 bytes). At SPU address `0x22000`, this uses 269,056 of the reserved 385,024-byte range through `0x7FFFF`, leaving 115,968 bytes in that region.
- Linked ELF sections: `.text` 1,011,212 bytes, `.data` 2,538 bytes, `.bss` 40,148 bytes; total 1,053,898 bytes. Relative to v108's 923,650-byte linked total, the increase is 130,248 bytes, mostly the resident SFX bank. The runtime RAM high-water mark, stack peak and remaining free RAM were not measured.
- The 96 KiB CD stream ring and music format (four channels, 43,008 Hz) are unchanged. No new CD bandwidth is consumed while the music streams.

## Build and verification

The v108 base was copied into new v109 and v109b directories; all earlier build outputs remain intact. The shared visual converter was rerun only into v109b; Week 1 and Week 3 scene package hashes were confirmed unchanged. The menu/audio generator added thunder payloads in v109; v109b reused those generated audio files byte-for-byte. Menu music and game-over VAGi outputs were byte-identical to v108.

Build: PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, FFmpeg 7.1.1. CMake configure, MIPS compilation/link, disc generation and ISO root reordering completed. Diagnostics remain off by default. The converted Week 2 package reports two stage and three character pages and remains within the existing VRAM map.

Compilation and static package checks succeeded. **No DuckStation run was performed by Codex, no user observation of v109b is recorded yet, and no real-console test is claimed.** Please load the CUE and check that the mansion/window details remain visible outside lightning flashes, thunder is audible on strikes, and existing music, gameplay, misses, popups and retry behavior remain intact.

## Delivery

Directory: `ps1/build/week2-scene-bpm-v109b-20261031/delivery-v109b-final/`

- BIN: `fnf-ps1-week2-lightning-v109b.bin` — 338,052,960 bytes, SHA-256 `BA1B46C6BD3450DDFA7406F25E84EB6041AB236BD99AEA8F08BD7B6C3691872F`
- CUE: `fnf-ps1-week2-lightning-v109b.cue` — 92 bytes, SHA-256 `AB50080B5F29C16FAB62E0ECD897DD201F5D9BBD2447A9FDBEF135B91D498B9A`
- Linked PS-X EXE: 1,017,856 bytes, SHA-256 `ECB19466A417E22DA154E323922236042F4B896869BEFBFDCAC26B59148DCEA7`
- Converted Week 2 package SHA-256: `4BE2DC0AB0D33190967F870C070BCE90276472785FA0FC4994D5B5453788610F`
