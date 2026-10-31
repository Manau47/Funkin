# Week 2 backdrop framing and lightning — v114

## Changes

This pass responds to the v113 DuckStation report: Week 2's room still looked too small/high, its source edges were visible, and the lightning effect was not apparent. The audio/chart timing rollback from v113 is unchanged.

- Increased the Week 2 backdrop and lightning transform from Q8 320 (1.25x) to Q8 384 (1.5x), and shifted both down 16 world units. This is a crop/placement change only; character and note camera transforms are unchanged.
- The converted stage frame is 362×256 after reduction from the official 2536×1837 atlas sprite. At 1.5x it covers about 543×384 screen pixels before camera crop. At the Dad/BF focus targets it overfills the 320×240 viewport, so the original rectangle edges should stay outside the visible area. The source sprite itself is not 16:9; the PS1 composition fills 4:3 by cropping the larger scene while preserving its proportions.
- The previous lightning presentation ended after 18 ticks at 24 ticks/second (0.75 s). It now uses the full 30-tick stage sequence (1.25 s). All three Week 2 songs get their first visual strike at beat 4; later strikes retain the deterministic 8–24 beat spacing. Thunder audio selection and pool are unchanged, including the official silent first Spookeez strike.

No timing offset, chart, judgement, gameplay rule, audio stream, SFX data, sprite, scene payload, or asset conversion was changed. The static room and lightning overlay still use the same existing Week 2 pages and CLUT.

## Build and reused inputs

- Branch: `ps1-port`, based on source commit `e6108e3`.
- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja; Debug configuration matching v113.
- Diagnostics, arrow QA, and scene demo are off at startup.
- Build folder: `C:/Users/Manau47/Documents/Codex/w2v114-week2-stage-cmake/`.
- The dry-run contained only compilation of `spu_probe.c` and SDK `stream.c`, link, and CD-image creation. No conversion command was scheduled.
- Week 2 scene package SHA-256 is `4AACCB673E0E2687B8C0321D6761DA3B73B9D54C205577E245FF6EB195D7E00A`; 4-channel 43,008 Hz music SHA-256 is `205EA3A13D2EBA739E250F4DA41AA44E5EABF78202EE0A1F81AB02B8647026D0`. Both match the v113 build inputs. Week 1/3/4/5/6/7/Weekend1 scenes, menu/game-over audio, Spookeez/South/Monster VAG files and Normal chart files were also compared byte-for-byte with the v113 build and match.

## Artifact and checks

Normal Debug BIN/CUE: `ps1/build/week2-scene-fix-v114-20261031/delivery-v114-debug-final/`.

| File | Size | SHA-256 |
| --- | ---: | --- |
| `funkin-ps1-week2-v114.bin` | 338,203,488 bytes | `0374FF0BD452481D40553C5994B2A88022B586371DAC1D8128EAB8763A20E34D` |
| `funkin-ps1-week2-v114.cue` | 84 bytes | `4D7E778B6F05DDBE7F84BE3FCCE2F15DB76C56F6A06F075C9EE95190F115B1EF` |

Compilation and ISO generation succeeded. The boot directory was reordered and checked: `SYSTEM.CNF` is entry 1 and `FUNKIN.EXE` entry 2. The build emitted two non-fatal volatile-qualifier warnings from the SDK's `stream.c`.

No DuckStation execution or console test is claimed for v114. Please check that the décor stays filled during camera focus changes, the room framing is larger/lower, and the lightning plus thunder are observable during all three Week 2 songs. The first Spookeez thunder sound remains intentionally silent.
