# Week 2 Monster animation and audio-clock correction (v111)

## Changes

- Week 2 Monster now uses four distinct official idle poses sampled from the pinned rig and two poses for each of the four singing directions. Idle cycles through the four poses over two chart beats; singing switches between its two poses on the chart beat phase.
- The SPU streaming helper primes two chunks before key-on. Those queueing callbacks incremented `Stream_GetSamplesPlayed()` before the first queued sample was audible. `start_stream_file()` now calls `Stream_ResetSamplesPlayed()` immediately after `Stream_Start()` succeeds, rebasing the chart, note scroll, judgement and beat-animation clock at playback start. This affects the shared stream startup for songs, not the chart contents.

## Timing investigation

The pinned Normal charts have no metadata offsets. Their first opponent/player notes are:

| Song | BPM at start | Opponent first note | Player first note |
| --- | ---: | ---: | ---: |
| Spookeez | 150 | 6,400 ms (beat 16, bar 4) | 9,600 ms (beat 24, bar 6) |
| South | 165 | 11,636 ms (beat 32, bar 8) | 17,454 ms (beat 48, bar 12) |
| Monster | 95 | 2,526 ms (beat 4, bar 1) | 7,578 ms (beat 12, bar 3) |

The official instrument stems contain nonzero audio from the start, and the chart head times land on their expected beat grid. This supports separate musical intros of four/eight/one bars and does not show a common one-bar chart offset. The source-level stream-counter correction removes a fixed 14,336-sample lead from the reported clock (two 7,168-sample chunks, about 333 ms at 43,008 Hz). It is shorter than a bar at all three songs' starting BPMs; it does **not** by itself explain or prove the user's perceived one-bar discrepancy. The new disc needs the user's listening check to establish whether a further song-specific timing problem remains. No arbitrary measure offset was added.

## Build and resource budget

- PSn00bSDK 0.24 / MIPS GCC 12.3.0, Debug CMake/Ninja build; target `ps1-bopeebo-playable-disc` succeeded. Diagnostics, arrow QA sheet and startup markers are off; Dad autoplay lanes remain on.
- The Week 2 visual converter emitted 40 character/icon frames and retained the existing two stage pages plus five character pages. Its bounds/overlap check passed. The on-disc Week 2 package remains 459,264 bytes; no additional CD streaming was introduced.
- The six added 72×84 8bpp poses represent 36,288 pixels of frame data. They fit within the already reserved five 8bpp pages, so the Week 2 VRAM page count and 64 KiB scene staging buffer do not grow. Full runtime RAM high-water usage remains unmeasured.
- Instrumental/voice VAGs and Normal charts for all three Week 2 songs were copied byte-for-byte from the v110 converted catalog. Their hashes are recorded below. SPU allocation and mix are unchanged.
- Linked ELF sections: text 1,011,388 bytes; data 2,542 bytes; BSS 40,148 bytes. The added poses do not add runtime allocations; the sample-clock reset uses the existing stream context.

## Reproducibility and hashes

Generated inputs remain outside Git under `ps1/build/week2-monster-sync-v111-20261031/preconverted-base/`. The audio/chart inputs were reused from v110; only the visual atlas/header/package were regenerated with FFmpeg 7.1.1. Week 1 and Week 3 scene payload hashes remained unchanged.

| File | SHA-256 |
| --- | --- |
| `catalog-audio/spookeez.vag` | `15559160783AC6667554F0F8F984188636D6618347CB51A45753AB14CB82F2B0` |
| `catalog-audio/south.vag` | `1EDC521334715EF912866A79810473B6AF0070AB51EE15DD55FC93A43F575F7E` |
| `catalog-audio/monster.vag` | `E240894F1A63E85B791973BD939FB1B2B71E3ADC09A28741A5276709E396F107` |
| `catalog-audio/charts/SPON.BIN` | `E4CAE00E3EE34CDA1BCA48873E508D48ABA7F735FF17535909F31393A803EACF` |
| `catalog-audio/charts/SOUN.BIN` | `D7276355B1C84B1F4AF65FFB55593F1341802ADF842A1D00C1408C282AF2711F` |
| `catalog-audio/charts/MONN.BIN` | `44EF83EF00230F1E0081583CAB0C7664ACAB4DF5AD9C5D76F82EE79C37AE6AFB` |
| `week1-scene.bin` | `C2444F178F0A9A7F28B4B24476B9058E74FB15237DDD4BB786907F73A6CD0E8F` |
| `week2-scene.bin` | `4AACCB673E0E2687B8C0321D6761DA3B73B9D54C205577E245FF6EB195D7E00A` |
| `week3-scene.bin` | `D2AF3C2CD14BD556FDED04E8EE224E6D254113BA0AA87A0FC4039A2B59A29D6D` |
| `funkin-ps1-bopeebo-playable.bin` | `3572333869AFA6AAE45560CE94FC00A9B88450BE7D6CAD285AAEA9B21384371F` |
| `funkin-ps1-bopeebo-playable.cue` | `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340` |

## Validation status

Compilation and static atlas/build checks succeeded. The BIN is 338,203,488 bytes. The CUE and BIN are in `ps1/build/week2-monster-sync-v111-20261031/delivery-v111-final/`. This image has **not** been run in DuckStation by Codex or tested on real hardware. Await the user's manual DuckStation check for the relative music/chart timing and Monster animation cadence; no gameplay validation is claimed.

## Boot-order correction (v111b)

The user reported that v111 remained at the Sony PlayStation logo. Comparing the delivered ISO root directory with the previously bootable v110b delivery identified the cause: the v111 `SYSTEM.CNF;1` record was the 93rd file entry (record index 95 when the two ISO directory-special records are counted), while `FUNKIN.EXE;1` was entry 36. The v110b delivery put `SYSTEM.CNF` first and `FUNKIN.EXE` second. The v111 CMake ISO output had not passed through the existing root-order correction step.

v111b is a copy of the v111 BIN with only the ISO root-directory file records reordered. The existing helper verified the original root-sector EDC/ECC, regenerated checks for the changed sectors, and asserts that every byte outside the root-directory sectors is preserved. The `SYSTEM.CNF` and `FUNKIN.EXE` directory records are byte-identical to their v111 versions; the executable remains at LBA 27 and 1,017,856 bytes. On v111b, the files are entries 1 and 2 respectively. No code, chart, audio, scene, or texture was rebuilt or modified.

v111b is statically checked but **awaits user execution in DuckStation**. This ISO fix addresses the Sony-logo boot failure only; it does not itself validate the Monster animations or music/chart alignment.

| v111b delivery file | SHA-256 |
| --- | --- |
| `funkin-ps1-bopeebo-playable-v111b.bin` (338,203,488 bytes) | `D5B3423E38E78B794BFABD40D229F3CC54E229716CF3B37CBACE53B417304C3B` |
| `funkin-ps1-bopeebo-playable-v111b.cue` (96 bytes) | `DD44981C6385B66FA0DAE16A49FD7C965701DFDFAE2C870BCF220C1CD772FA2F` |

Delivery directory: `ps1/build/week2-monster-sync-v111-20261031/delivery-v111b-bootfix/`. The original v111 delivery is retained unchanged for comparison.
