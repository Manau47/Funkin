# WeekEnd 1 PS1 test build v105b

Date: 2026-10-30  
Branch: `ps1-port`  
Implementation commit: `ca6eb54157c257b2d3dd9cd9ca1fda1ff0d97142`  
Parent: `d01096a561c44188a46cf956af672e19157ac931` (Week 7 v104)  
Pinned assets submodule: `724eba9de9e76761d9cefd52169926bc51c760a5`

## Scope

Adds the four classic WeekEnd 1 songs to Freeplay after the existing Week 7 catalog: Darnell, Lit Up, 2Hot, and Blazin. Each offers Easy, Normal, and Hard. Pico Erect charts/stems and the Spaghetti collaboration are excluded. The existing catalog already held these four labels as locked rows; this change makes those rows playable and does not duplicate them.

The source charts retain note timings, lanes, hold lengths, tempo changes, and camera-focus events supported by the port's chart format. Blazin's custom combat note types are not yet interpreted as combat mechanics; their source chart types are reduced to the ordinary lane/timing/hold representation. Blazin therefore plays as a rhythm chart with provisional beat-driven combat poses, not as a complete port of its original battle rules.

## Audio and scene

Audio uses the existing four-channel VAGi stream format at 43,008 Hz: instrumental L/R, opponent mono, player mono, aligned to the same sample origin. For Darnell, Lit Up, and 2Hot, Circle mutes the player voice (Pico); Darnell remains audible. Blazin has only the official instrumental in the pinned asset revision, so its two voice channels are silent and muting has no audible effect.

The scenes use the pinned Philly Streets and Philly Blazin backgrounds plus official Pico, Darnell, Nene, and icon assets. The streets scene is a static layer composite with selected directional poses; Blazin uses selected idle/punch poses. Full character animation, Nene movement, Philly traffic/effects, and Blazin-specific combat timing remain deferred. Each scene package is read from `WEND1.BIN` on song load; the shared gameplay VRAM pages and palette are restored when returning to other scenes. WeekEnd resources are not converted into a single always-resident memory payload.

## Charts

| Song | Easy | Normal | Hard |
| --- | ---: | ---: | ---: |
| Darnell | 550 | 620 | 725 |
| Lit Up | 663 | 756 | 830 |
| 2Hot | 821 | 906 | 1,035 |
| Blazin | 422 | 426 | 440 |

All twelve chart files total 101,136 bytes. Maximum chart capacity is now 1,035 notes, 130 above v104 Stress Hard. The VAGi files total 47,816,704 bytes on disc. Individual songs stream from CD one at a time; their average encoded rate remains about 99 kB/s. The existing audio ring (96 KiB), SPU stream voices, SFX pool, and 16 KiB music double buffer are unchanged.

## Memory estimates

- Linked ELF sections reported by `mipsel-none-elf-size`: text 866,736 B, data 2,442 B, BSS 40,080 B; total 909,258 B, +2,144 B from v104. This is a static section count, not a runtime peak.
- One selected chart is loaded at a time (largest source chart 12,800 B); chart state capacity increases by 130 note entries.
- CD scene staging remains 64 KiB and is released after upload. Audio RAM remains 96 KiB.
- `WEND1.BIN` is 524,800 B: eight 8bpp pages (512 KiB) and a 512-byte CLUT. It reuses the existing shared gameplay VRAM slots; it is not added on top of every other week's VRAM scene.
- A rough sum of linked sections + audio ring + scene staging + largest serialized chart is about 1.04 MiB, before stack, allocator/runtime overhead, and other live allocations. No runtime peak RAM or frame-time measurement was made.

## Build and delivery

Toolchain: PSn00bSDK 0.24, GCC MIPS 12.3, CMake 4.5, Ninja. The WeekEnd package was generated once in `ps1/build/weekend1-assets-v105`; the final source-matching build reuses that converted package and the existing base/Week 4–7 packages. The dry run for the disc target contained only two C compilations, link, and ISO creation. No other week or menu resource conversion was scheduled. Two `volatile` qualifier warnings come from the external PSn00bSDK `cdstream/stream.c`.

The original v105 outputs remain untouched. The final source-matching rebuild is under `ps1/build/weekend1-v105b`. The raw mkpsxiso image is preserved in that directory; the delivery copy has only its root directory record order changed so `SYSTEM.CNF` is the first visible file. The existing checked EDC/ECC reorder tool updates those root sectors and the CUE points at the delivery BIN.

- CUE: `ps1/build/weekend1-v105b/delivery/funkin-ps1-weekend1-test-v105b.cue`
- BIN: adjacent `funkin-ps1-weekend1-test-v105b.bin`, 337,885,968 bytes
- BIN SHA-256: `CC491F701307EEAC16938611432797FCE8FB867658F0E43769CBEDD0F42A0BF1`
- CUE SHA-256: `0025E04D2469D412797415D5085BA1AF0A5F51DB5E94CAA502C1F74BC8124180`
- Linked `FUNKIN.EXE`: 872,448 bytes, SHA-256 `0531DA66E28CAEC6DE7E7EEE57DEE2138954BC888B8897889FC1E4B32D480628`
- Static ISO audit: 117 root files; `SYSTEM.CNF` first; all 12 WeekEnd charts, all four VAGi files, `WEND1.BIN`, and `FUNKIN.EXE` present; extracted EXE byte hash matches the linked EXE.

## Test status

Compilation and static BIN/CUE/ISO checks succeeded. This build has not been run in DuckStation by Codex and has not yet been tested by the user. Please load the CUE and check Freeplay navigation, Normal/Easy/Hard for all four songs, audio and Pico mute, note holds/judgments, Blazin behavior, retry, and return to Freeplay. No real-console test is claimed.

Publication status: source and build documentation are committed locally on `ps1-port` (implementation `ca6eb54157c257b2d3dd9cd9ca1fda1ff0d97142`; build record `61234072b04d83040ddae38cc958b65a3c696170`). A push attempt failed because Git Credential Manager could not acquire GitHub credentials (`SEC_E_NO_CREDENTIALS`). The remote draft PR was left unchanged; no force push or merge was done.
