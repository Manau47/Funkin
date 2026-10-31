# Week 2 timing rollback and background framing — v113

## What changed

The user reported that all sounds seemed about one second late in v112 and suspected the DuckStation-over-Parsec path might contribute. The user asked to roll back this specific timing adjustment and defer further timing work. v113 removes the v112 runtime `+43,008`-sample offset from Week 2 note heads, sustain tails, and camera events. The chart/audio clock, streamed audio, tempo map, judgement windows, score, health, and gameplay rules remain unchanged from v111/v112. This is a rollback of the chart-side offset only; it does not claim to correct any latency in DuckStation, Parsec, or audio output.

The user also reported that the Week 2 background was still absent outside lightning. The static scene package and its pixels are unchanged. To address the persistent black-looking background, v113 draws both static stage pages and the lightning overlay with the same `1.25x` background scale (`Q8=320`, plus the existing beat pulse), while retaining the normal singer camera targets and character/note transforms. At the Dad focus (`67,55`), the stage origin (`-56,-75`) maps to approximately `(6,-42)` and the first 256×256 page covers about 320×320 screen pixels; this should bring the static room/window area into the visible 320×240 viewport. This is a source-coordinate/crop calculation, not an emulator observation. The background's visibility and alignment still require the user's DuckStation test.

## Build inputs and reproducibility

- Source branch: `ps1-port`; v113 source change is the diff from the preceding v112 commit `5047849`.
- SDK/toolchain: PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja.
- Debug build; normal gameplay target; diagnostics, arrow QA, scene demo, and startup markers off; Dad autoplay lanes on.
- Existing converted packages from `ps1/build/week2-monster-sync-v111-20261031/preconverted-base` and the existing Week 4–Weekend 1 preconverted packages were reused. Existing 43,008 Hz four-channel VAGi and official chart JSON were reused.
- No visual/audio/chart conversion ran. The targeted Ninja dry-run listed only compilation of `spu_probe.c` and SDK `stream.c`, link, and ISO generation. The all-target dry-run also listed an SFX helper for a separate audio-only probe; that target was deliberately not built.
- New build directory: `C:/Users/Manau47/Documents/Codex/w2v113-background-cmake/`.
- New delivery directory: `ps1/build/week2-sync-bg-v113-20261031/delivery-v113-final/`.
- The generated ISO was reordered using `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf`, preserving the boot ordering previously confirmed by the user (`SYSTEM.CNF` record 1, `FUNKIN.EXE` record 2).

Reused resource checks:

| Resource | SHA-256 | Check |
| --- | --- | --- |
| Week 2 scene package (`week2-scene.bin`) | `4AACCB673E0E2687B8C0321D6761DA3B73B9D54C205577E245FF6EB195D7E00A` | v111 base package equals v112 build copy |
| Bopeebo 4-channel VAGi (`stream-playable.vag`) | `205EA3A13D2EBA739E250F4DA41AA44E5EABF78202EE0A1F81AB02B8647026D0` | source VAGi equals v112 build copy |

## Build and verification

The playable ISO target compiled and linked successfully, then produced a 338,203,488-byte BIN. The delivery copy has `SYSTEM.CNF` first and `FUNKIN.EXE` second. No DuckStation run was performed for v113; the user will load this CUE for the agreed manual test. No real-console test or measured synchronization result is claimed.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `funkin-ps1-week2-v113.bin` | 338,203,488 bytes | `6046A9038F423C679EE726BE90927C109D8A186BBE34191FCD4F09465B61AE53` |
| `funkin-ps1-week2-v113.cue` | 84 bytes | `26BCE8B63133A8221D216A1EEB94CAD2716C6CF8A29C565DCDF386C64F147CFE` |

The background-scale adjustment is a candidate correction only. Please check that static Week 2 décor is visible between lightning flashes, and whether the prior one-second chart adjustment's removal matches the sound/arrow timing better. If all audio still seems late, the Parsec/audio path remains an unisolated possibility.
