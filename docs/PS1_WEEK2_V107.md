# PS1 Week 2 visual candidate v107

Date: 2026-10-31  
Branch: `ps1-port`  
Source base: `2fb39849d1884bc635b70f05b591bdbe3c432b17`  
Source implementation commit: `b1fbcf6ca93826c7e7bc869a8f25963fcae16692`

This candidate responds to the user's Week 2 feedback: Spookeez/South opponent idle appeared too fast, the stage décor and lightning were absent, Week 2 framing felt distant, and Monster appeared cut off. It is a visual/stage pass only; it does not claim user or emulator validation.

## Changes

- Reuses the pinned official `halloween_bg` Animate rig instead of only the nearly-flat `Sprite 0` background. The converter pre-renders three samples and packs only the changing window/lightning crop as small patches in free space on an existing Week 2 stage texture page.
- Shows the first visual strike at beat 4 for Spookeez and beat 12 for South/Monster, then uses a deterministic interval in the official 8–24 beat range. Animation timing is derived from the active chart's audio-sample tempo map. This is a reproducible visual approximation of the source's random strike scheduling; it does not add thunder audio.
- Selects eight distinct official Spooky idle poses, advancing every half beat. The previous four-frame selection crossed the paired left/right poses too quickly. The animation remains synchronized to the song clock.
- Fits each selected official Monster pose from its own alpha bounds into the existing 72×84 frame, preserving aspect and bottom anchoring. The prior shared rig envelope shrank/narrowed poses. The frame dimensions were deliberately kept to avoid adding a fourth character page; the user's DuckStation check must determine whether the apparent cut-off is resolved.
- Tightens Week 2 camera zoom from Q8 384 (1.5×) to 448 (1.75×) for the 4:3 viewport. Other weeks and camera focus rules are unchanged.
- CMake now tracks the Spooky character metadata and Halloween background animation file, so edits to those source assets trigger conversion.

Charts, judgment rules, health, controls, song audio, SPU streaming, popups, score, and SFX were not changed. Existing per-song resource loading remains in place.

## Memory and package impact

- Week 2 retains 2 stage plus 3 character 8bpp pages: 5 × 65,536 = 327,680 bytes of indexed texture data, plus a 512-byte 256-entry CLUT allocation. The three lightning patches occupy unused pixels on stage page 1; they add no VRAM page and no CD read.
- Week 2 scene package: 328,192 bytes. Week 1 shared visual package: 655,360 bytes. Week 3 package: 262,656 bytes.
- The complete ISO package is 337,902,432 bytes (117 files). The music stream is reused byte-for-byte: 8,079,360 bytes, SHA-256 `205EA3A13D2EBA739E250F4DA41AA44E5EABF78202EE0A1F81AB02B8647026D0`.
- Linked resident ELF sections total 923,502 bytes (text 880,840; data 2,514; BSS 40,148), versus 922,442 bytes in v106. This is a linker size, not a runtime high-water measurement; heap/stack peaks and remaining main RAM were not measured.
- The conversion command regenerates the shared visual header and Week 1/2/3 packages together. Consequently, Week 1's 8bpp page data is different from the older v106 output although no Week 1 rendering logic was intentionally changed. Week 1 hash is `CF9E27525F8E4BF09D909BDB159CFCD93B3813AFED11766997AFAC8AFD2B895C` (v106: `FBDA242B07285698E6D54FA60FDB0BB84D618B1AF547DDE4772E08D401B26C36`). Week 3 is unchanged from v106: `D2AF3C2CD14BD556FDED04E8EE224E6D254113BA0AA87A0FC4039A2B59A29D6D`. A Week 1 visual non-regression check is required.

## Reproduction and validation

Toolchain: PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, Python converter, and FFmpeg 7.1.1. The SDK and official source assets remain external to Git. Diagnostics are disabled by default.

The visual converter completed and reported 186 valid frame rectangles, the three stage plus two character page layout, and Week 2 palette RMSE 3.69. C compilation, linking, and ISO generation succeeded. `mipsel-none-elf-size` reported the resident section totals above. The delivery ISO was checked to place `SYSTEM.CNF` and then `FUNKIN.EXE` first in its root directory for BIOS boot. No emulator session was run by Codex, and no console test was run.

Reusable generated inputs and earlier candidates were preserved under the ignored `ps1/build/week2-scene-bpm-v107-20261031/` tree. The final delivery is in `delivery-v107-final/`:

| Artifact | Size | SHA-256 |
|---|---:|---|
| `fnf-ps1-v107-week2-stage.bin` | 337,902,432 bytes | `4BAECB81320746AFA65DDA88F0489377C55506873E5CD1E34B396B27FAAB0C16` |
| `fnf-ps1-v107-week2-stage.cue` | 87 bytes | `BA393E2E57CB82EE9EACCB6BD733630A5D2380A26CC9B9219910653CF679D558` |

Generated visual inputs: header `09BC85D3371266E9A724B1CEF56633B6A2A43558EA28562C7B51065B9266FF83`; Week 2 `0C83DCA52AEE6997B71FB279637A247D06E592DADA1D2203BF92B9FD6D6674FE`; Week 1 and Week 3 hashes are recorded above.

## User test requested

Load the v107 CUE in DuckStation and check Spookeez, South, and Monster. In particular report: idle cadence, recognizable animated décor/window lightning, camera distance, whether Monster's full intended sprite is visible, any Week 1 regression, and CD/underrun/audio behavior. The result remains a candidate until that manual test; drift and real-console behavior are unmeasured.
