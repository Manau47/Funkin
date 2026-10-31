# Week 2 timing and backdrop framing — v112

## Changes

The user reported that Week 2 arrows reached the receptors about one second **before** their matching music, and that the static stage backdrop was not apparent between lightning flashes.

- The Normal charts for Spookeez, South and Monster now receive a runtime-only `+43,008` sample delay (`+1,000 ms` at the 43,008 Hz chart/audio clock). Note heads, hold tails, and camera focus events move together. Tempo-map samples and streamed audio stay at their original time origin. No judgement windows, note rules, scoring, health, or SPU stream behavior changed.
- The backdrop itself was already present in the converted Week 2 page. A 320×240 crop calculation at the existing Q8 zoom 640 showed that the camera viewport sampled approximately source x=59–187, y=82–178: mostly the dim floor, below and right of the window/room details in the static source. The Week 2 stage and its lightning overlay are both shifted by +70 world pixels on x and y. At the Dad focus target (67,55), the crop moves to about x=0–117, y=12–108, revealing the source window and upper room while preserving their alignment during lightning. Character positions, notes, camera targets, and zoom are unchanged.

The earlier test assignment to `alpha_over()`'s background-image call was discarded: the converter's `alpha_over()` returns a new buffer, but the input sprite at that call is an opaque flat-color background matching the existing fill. The generated `W2SCENE.BIN` hash was identical before and after that no-op. It was reverted; v112 does not regenerate visual resources. The already-correct static Animate decor composition from v110 is reused.

## Build and reused inputs

- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja; Debug configuration, diagnostics off, Dad autoplay lanes on, all QA/startup-marker options off.
- CMake points at the v111 converted package set and the existing 43,008 Hz four-channel audio VAGi. Ninja dry-run listed exactly four actions: compile `spu_probe.c`, compile SDK `stream.c`, link the executable, create the disc. No asset or audio conversion was scheduled.
- The delivered ISO root was post-processed with `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`, preserving the boot ordering that the user confirmed working in v111b. The root records are `SYSTEM.CNF` #1 and `FUNKIN.EXE` #2.
- Week 2 scene package: 459,264 bytes, SHA-256 `4AACCB673E0E2687B8C0321D6761DA3B73B9D54C205577E245FF6EB195D7E00A`, byte-identical to v111. Week 1/3 scenes, visual header, menu/game-over audio, VAGs and charts are reused from v111 unchanged.
- Week 2 Normal chart tail margins after the +1 s delay, relative to source audio end: Spookeez 2.60 s, South 6.52 s, Monster 4.55 s. This is a fixed timing adjustment based on the user's directional listening report, not a measured drift estimate.
- Linked ELF sections: `.text` 1,011,680 bytes, `.data` 2,542 bytes, `.bss` 40,148 bytes; total 1,054,370 bytes. Peak runtime RAM remains unmeasured.

## Artifacts and verification

Build workspace: `C:/Users/Manau47/Documents/Codex/w2v112-sync-bg-cmake/`.

Delivery folder: `ps1/build/week2-sync-bg-v112-20261031/delivery-v112-final/`.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `funkin-ps1-bopeebo-playable-v112.bin` | 338,203,488 | `720C29AAC48164AA08DEA5DEE02008D447D1575BCF1A1160F7937058ED8F6633` |
| `funkin-ps1-bopeebo-playable-v112.cue` | 95 | `9EF5AC273E10AF18962CC12177191AF1691FC02E1004DF3B6BB8753EDC09C6DE` |
| Embedded `FUNKIN.EXE` | 1,017,856 | `5C5EA4E3D998B4D227E6BD4FD6D3B87E57D0A1D487B455D8E2CBD9C3688CA22E` |

Compilation, dry-run review, hashes, chart bounds/tail calculations, and ISO root ordering were verified. The new disc has **not** been run in DuckStation or on a real console. The user will load the CUE for the agreed two-person test. In particular, the +1 s correction and improved off-lightning backdrop still await that observation.
