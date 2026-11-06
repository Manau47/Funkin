# PS1 Week 2 and menu corrections — v108

Date: 2026-10-31  
Branch: `ps1-port`  
Source base: `1060a396e68af8e32732bd4f9328f6260e13e46d`  
Implementation commit: `4b5e1206d78f5afe04fe4e808f97dbd1e5e17045`

This is a test candidate, not a user-validated build. It addresses the reported Week 2 presentation issues and two menu defects while leaving gameplay rules and audio unchanged.

## Changes

- **Week 2 stage:** composite the pinned Halloween stage's permanent Animate frame (frame 30) over the base before palette conversion. The stage is therefore present between strikes. The three existing lightning samples remain separately timed visual overlays, driven from the chart's audio-sample clock. The strike schedule is still a deterministic approximation of the original random schedule.
- **Spookeez/South idle:** retain the eight official sampled idle poses, but hold each for one full chart beat instead of half a beat. Singing poses and chart timing are unchanged.
- **Monster:** render its official character symbols (`monster idle`, `Monster left note`, `Monster Right note`, `monster up note`, `monster down`) directly instead of using the Christmas stage composition that clips the character. Fit each pose independently into the existing 72×84 frame, aspect-preserving and bottom-anchored. The frame size and page count do not increase.
- **Week 2 camera:** use the same base zoom constant as Week 1 (Q8 640); existing chart focus targets, interpolation and beat pulse remain shared. This copies the Week 1 zoom baseline, not a new camera implementation.
- **Menus:** Fresh uses Dad's icon. The approved custom OPTIONS idle graphic is drawn from an explicit reserved region on the main-menu texture page (the same page reload preserves it); the selection animation stays on its existing atlas region. The navigation hint is moved to a small separate line at the bottom so it no longer overlaps Credits.
- Add the pinned Monster character metadata to the conversion dependency list. No chart, judgment, health, input, gameplay, audio, SFX or streaming code was changed.

## Resource and memory notes

The v108 scene package sizes remain Week 1 655,360 bytes, Week 2 328,192 bytes and Week 3 262,656 bytes. Week 2 still uses 2 stage and 3 character texture pages; the permanent background is baked into its existing stage pages, and no VRAM page or concurrent CD read was added. Week 2 conversion still reports 5 pages and 26 character/icon frames. The shared generated visual header remains 2,355,626 bytes.

The linked ELF reports `.text` 880,984 bytes, `.data` 2,518 bytes and `.bss` 40,148 bytes, 923,650 bytes combined. This is linked section size, not a runtime RAM high-water measurement; heap/stack peak and remaining free RAM were not measured. Audio sample count and music input are unchanged; the reused four-channel 43,008 Hz VAG is 8,079,360 bytes with SHA-256 `205EA3A13D2EBA739E250F4DA41AA44E5EABF78202EE0A1F81AB02B8647026D0`.

The generated packages are outside Git under `ps1/build/week2-scene-bpm-v108-20261031/preconverted-base/`. Compared with v107, the Week 1 and Week 2 visual package hashes change because the shared converter also rebuilds those packages; Week 3 stays byte-identical. Earlier v107 files and deliveries were preserved.

## Build and checks

Toolchain: PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, Python 3.13 and FFmpeg 7.1.1. SDK, source assets, music conversion input and generated assets remain outside Git. Diagnostics are off by default.

The visual conversion command was:

```powershell
python ps1/convert_bopeebo_visuals.py `
  --assets assets `
  --ffmpeg 'T:\Docker\MGTV Playlist Gen\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe' `
  --options-art outputs/menu-options-concept-v2.png `
  --output ps1/build/week2-scene-bpm-v108-20261031/preconverted-base/bopeebo_visual_data.h `
  --week1-pages-output ps1/build/week2-scene-bpm-v108-20261031/preconverted-base/week1-scene.bin `
  --week2-pages-output ps1/build/week2-scene-bpm-v108-20261031/preconverted-base/week2-scene.bin `
  --week3-pages-output ps1/build/week2-scene-bpm-v108-20261031/preconverted-base/week3-scene.bin
```

The game build points `FUNKIN_PS1_PRECONVERTED_BASE_DIR` at that v108 directory, uses the pinned chart `assets/preload/data/songs/bopeebo/bopeebo-chart.json`, the external VAG below, and `FUNKIN_PS1_AUDIO_4CH_SAMPLE_COUNT=3509453u`. Existing preconverted Week 4–Weekend 1 packages are reused from `week4-assets-preview`, `week5-assets-v101`, `week6-assets-v102`, `week7-assets-v104`, and `weekend1-assets-v105`. `FUNKIN_PS1_DAD_LANES_DEFAULT=ON`; diagnostic/test switches are OFF. Targets: `funkin-ps1-bopeebo-playable` and `ps1-bopeebo-playable-disc`. The raw ISO is copied through `ps1/diagnostics/reorder_iso_system_cnf.py --exe-after-system-cnf` into a new delivery folder. The build tree was `C:\Users\Manau47\Documents\Codex\w2v108b-game-cmake`.

- Python syntax check passed for `animate_preview.py` and `convert_bopeebo_visuals.py`.
- The visual converter completed and checked all 186 atlas rectangles. It reported Week 2 palette RMSE 3.75 RGB levels and valid VRAM bounds (9 8bpp + 2 4bpp pages, plus the existing framebuffer, CLUT and font regions).
- CMake configure, MIPS compile/link and ISO generation succeeded. The build retained the existing 117-file disc layout and 337,902,432-byte image size.
- The delivery copy puts `SYSTEM.CNF` first and `FUNKIN.EXE` second in the ISO root. The reordering utility verified the original root-sector EDC/ECC and recalculated checksums for the modified directory sectors. It leaves all other image bytes intact.
- No DuckStation session was run by Codex. Week 1 regression, menu visibility/navigation, the permanent Week 2 décor, idle cadence, Monster framing, lightning presentation, audio stability and real-console behavior remain for the user's test. No emulator or console validation is claimed.

## Deliverable

Load the CUE in DuckStation for the agreed manual test:

- `ps1/build/week2-scene-bpm-v108-20261031/delivery-v108-final/fnf-ps1-week2-presentation-v108.cue`
- Matching BIN: `fnf-ps1-week2-presentation-v108.bin`

| Artifact | Size | SHA-256 |
|---|---:|---|
| BIN | 337,902,432 bytes | `103D041A573BAC918B0F296F7183867DA9B6A7FA50F910F33E301C2CD52E2DDC` |
| CUE | 94 bytes | `882381B7AB419D25095A1AF5C1BCA0CA8ACE38CDD2EC5103DF0BBA53AEF9233D` |
| FUNKIN.EXE | 886,784 bytes | `9569CA94995EE79A7751FD6D00F1E1A5A1CE7EA0AC36AA510204DC5667CF0B9F` |

After loading, please check the main-menu OPTIONS row and hint, Fresh's icon, Week 1, then Spookeez, South and Monster. For Week 2, specifically report whether the background stays present between lightning, Spooky idle feels slower, the camera matches Week 1's framing more closely, Monster is no longer cut off, and whether music/CD errors or underruns appear. This source/build record is committed locally; no remote push or PR update is claimed here.
