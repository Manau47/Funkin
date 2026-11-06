# Week 2 static décor and BPM animation pass (v110b)

Date: 2026-10-31  
Branch: `ps1-port`  
Base: v109b source commit `d37b7c078423d4c0b14cb67c3e288bffc81997d2`  
Assets submodule: `724eba9de9e76761d9cefd52169926bc51c760a5`

This candidate addresses the user's report that Week 2's décor still appeared only during lightning, GF seemed to skip dance frames, and Spookeez/South opponent idle animations were too slow.

## Changes

The missing décor came from a discarded return value: `alpha_over()` creates and returns a new image buffer, but v109b called it without assigning that buffer back. The converter's direct Animate preview showed the room, while the Week 2 package embedded in the ISO still held only the flat base. The result is now assigned before palette conversion. The exported background atlas and the Animate timeline are both placed using the authored root instance translation, so the permanent background and window/room layers share one coordinate system. The static package was decoded from its actual 8bpp page data and RGB555 CLUT; it now contains non-flat permanent image pixels outside the reserved lightning patch. This is package-level evidence, not an emulator capture.

Week 2 GF previously had only two poses copied into its own palette atlas. It now has the same ten sampled source poses as the existing GF dance path: five poses for each alternating direction, selected from the chart's audio-sample-derived beat and phase. The opponent idle uses the eight available Spooky poses, advancing four poses per beat and alternating the four-pose direction groups on the following beat. This completes a cycle in two chart beats. `music_beat_q16()` reads the active chart's tempo map, so cadence follows Spookeez/South BPM and any mapped tempo changes. Singing poses, chart data, gameplay timing, scoring and camera are unchanged.

## Resources and memory

- Week 2 package grows from 328,192 to 459,264 bytes: two background pages, five character pages and the 512-byte RGB555 CLUT.
- The 9-page 8bpp / 2-page 4bpp VRAM allocation is unchanged. Week 2 temporarily occupies existing 8bpp slots 0–6; the remaining two 8bpp slots are untouched. The normal pages for overwritten slots are restored when leaving Week 2. The atlas validator confirmed all 194 frame rectangles and the complete VRAM layout.
- Scene loading still uses one 64 KiB page staging buffer. The extra 131,072 bytes are on disc and in two pre-existing VRAM slots; they do not require an extra main-RAM page buffer. Runtime RAM high-water and stack peak were not measured.
- Week 1 and Week 3 package hashes remain unchanged from v109b. The copied menu audio, menu VAG, game-over VAGs and catalogs are byte-identical to v109b. Music, four-channel 43,008 Hz streaming, SFX/SPU allocation and CD streaming during playback are unchanged.

## Build and verification

The old v109b build and delivery were preserved. The v110b preconverted base was copied to a new candidate directory; only the shared visual converter was rerun, and Ninja's command listing contained no visual/audio converter command. CMake was configured in `Debug` (`-Og`), matching the v109b CMake build configuration. SDK, GCC, FFmpeg, chart and external audio inputs remained the same. Diagnostics and QA overlays are off by default.

Compilation/link and ISO generation succeeded with PSn00bSDK 0.24, MIPS GCC 12.3, CMake 4.5 and Ninja. Final ELF resident sections: `.text=1,011,284`, `.data=2,534`, `.bss=40,148`, total `1,053,966` bytes. `SYSTEM.CNF`/`FUNKIN.EXE` root ordering was corrected and validated in the delivery copy. The W2 package inside the build source is SHA-256 `9C97B29FEE22EFFF129AB7B861A508B7A4BA9D8D99F48D492F9BB83C6F1A06F3`; executable SHA-256 `E1D7D81E2A6ACC472E27A2D45D7089E9D6AA2B6D6037AADCA6A67EF9D5BA4D20`.

**No DuckStation run was performed by Codex.** The user's feedback is still needed to confirm the scene's framing/visibility, GF animation, Spookeez/South idle pace, lightning audio, music stability and unaffected gameplay. No console test is claimed.

## Delivery

Directory: `ps1/build/week2-scene-bpm-v110-20261031/delivery-v110b-final/`

- BIN: `fnf-ps1-week2-bpm-decor-v110b.bin`, 338,203,488 bytes; SHA-256 `50348A417FCD7839D324C8214F4ACC48024E09B5A364B019F98427D602BE8414`
- CUE: `fnf-ps1-week2-bpm-decor-v110b.cue`; SHA-256 `ABF7C84F350D5B5B18C3856BBD6181C5D34FBFC9B2098FEAAFCB01A69928D082`

Use the CUE in the directory above for the user-led DuckStation test. Preserve the existing v109b delivery for rollback/comparison.
