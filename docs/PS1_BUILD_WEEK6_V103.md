# FNF PS1 Week 6 — v103 build manifest

- Source branch: `ps1-port`
- Source commit: `ee0bbd668eead59b1e77d06a0b3ab5a63e69b823` (`Add classic Week 6 playable content`)
- Parent build source: Week 5 v101, `e396110b6569a89263b5687c50750e3e62636d3a`
- Pinned assets submodule: `724eba9de9e76761d9cefd52169926bc51c760a5`
- Toolchain: PSn00bSDK 0.24, GCC MIPS 12.3, CMake 4.5, Ninja
- Build directory: `ps1/build/week6-v103`
- Converted Week 6 package: `ps1/build/week6-assets-v102` (outside Git)
- Diagnostic overlays: disabled by default

## Inputs and build plan

The Week 6 package was generated from the pinned `senpai`, `roses`, and `thorns` song charts/stems and the official pixel stage, character, icon, and arrow assets. The ADPCM/VAGi and decoded WAV outputs were generated once in `week6-assets-v102`, then reused with the generator's `--reuse-audio` option for the final scene/header rebuild. The nine chart binaries were regenerated from the pinned chart JSON. No proprietary SDK files or generated assets were added to Git.

The CMake build reuses these already converted package paths:

- `ps1/build/main-entry-marker-v90-fcd8040` for base/menu/Weeks 1–3
- `ps1/build/week4-assets-preview` for Week 4
- `ps1/build/week5-assets-v101` for Week 5
- `ps1/build/week6-assets-v102` for Week 6

The Ninja dry-run for `ps1-bopeebo-playable-disc` contained two C compilations, link, and ISO creation only. It did not run an asset converter. The SDK `cdstream/stream.c` emitted two existing `volatile` qualifier warnings.

## Week 6 data

All music is VAGi, 4 channels at 43,008 Hz, with a common time origin: instrumental L/R, BF mono, and the opposing voice mono. Circle keeps muting BF independently.

| Song | Samples | Duration | Easy / Normal / Hard notes | VAGi bytes |
|---|---:|---:|---:|---:|
| Senpai | 4,227,360 | 98.292 s | 285 / 341 / 385 | 9,717,760 |
| Roses | 3,956,736 | 92.000 s | 255 / 382 / 465 | 9,095,168 |
| Thorns | 4,454,724 | 103.579 s | 309 / 417 / 557 | 10,242,048 |

Chart output files are `SENE/SENN/SENH.BIN`, `ROSE/ROSN/ROSH.BIN`, and `THOE/THON/THOH.BIN`. Maximum chart count remains 674 (M.I.L.F Hard from Week 4); Week 6's largest chart has 557 notes.

`W6SCENE.BIN`: 328,192 bytes (five 65,536-byte 8bpp pages plus a 512-byte CLUT), SHA-256 `251B525DCB437314A4ABB269B1D324AD8C48E5169035590209B4CDF2157AC730`. It contains two static school backdrops, a compact character-pose atlas, official pixel arrows/receptors, and three Week 6 portraits. Characters use a limited selection of official poses; GF alternates two idle poses on the beat. Hold bodies are simple colored outlined bars; the pixel hold-head/end artwork has not yet been integrated. This is a first playable conversion, not a complete reproduction of the source animations.

## Memory and streaming

- Main RAM: ELF `.text=862,856`, `.data=2,442`, `.bss=39,612`, total 904,910 bytes. Existing audio ring remains 96 KiB. Page upload uses a 64 KiB temporary buffer that is freed after transfer. The runtime peak including stack/heap has not been measured.
- VRAM: Week 6 leases five existing 8bpp scene pages (320 KiB) and the shared 512-byte CLUT. Other week/menu assets reuse the same slots after the page contents are restored from disc.
- SPU: existing four music-stream voices, 16 KiB stream double buffer, and existing SFX voice pool are unchanged; no additional full-song preload was added.
- CD: the three VAGi files total 29,054,976 bytes, averaging about 99 kB/s over their durations. Scene transfers are serialized before the song stream starts; there is no concurrent scene read during playback.

## Disc and checks

- Delivery CUE: `funkin-ps1-week6-test-v103.cue`, 89 bytes, SHA-256 `926B6307DD0A57E894F2E7C83EFB0F70822BFC8C4E78DC3F7EC8E26A4BAAC25F`
- Delivery BIN: `funkin-ps1-week6-test-v103.bin`, 242,070,192 bytes (102,921 sectors), SHA-256 `B70F551664AEBA18EA80F38DE0E9ACF37E65F162BB2D7F6BF80A123345B5411B`
- Raw CMake BIN SHA-256: `969AEC432235CC45B7C7C13EB610495DD43B95C1597B3801FD121B6BFE38B29B`
- ISO root: 87 files; `SYSTEM.CNF` reordered to first file entry using the existing sector-preserving utility, with directory EDC/ECC verified.
- `SYSTEM.CNF`: `BOOT=cdrom:\FUNKIN.EXE;1`, `STACK=801FFFF0`.
- Extracted `FUNKIN.EXE` is byte-identical to the compiled EXE, 868,352 bytes; PS-X EXE PC `0x8001EEFC`, load address `0x80010000`, text size `0xD3800`.

Build compilation, ISO generation, directory/order checks, PS-X EXE equality, and hashes succeeded. This CUE has not been run in DuckStation by Codex; the user must check Freeplay, all three songs/difficulties, music, voice mute, chart/hold behavior, and return/retry. No console test is claimed.
