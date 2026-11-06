# Week 7 v104 build manifest

## Contents

- Classic Week 7: Ugh, Guns, Stress.
- Difficulties: Easy, Normal, Hard for each song. They are included in the actual menu/playable catalog.
- Not included: Pico Mix/Erect variations or their separate visual/audio treatments.
- Input behavior remains inherited from the earlier game build: Circle mutes BF’s vocal stem; no Week 7 gameplay rules were changed.

## Pinned inputs and conversion

- Source commit used for this build: `505e6038eb0a685afd725b450d5050417c7a3aa6` on `ps1-port` (parent/base `c86044629cd1fd0332a8ce66615b4b15be0e534c`).
- Official assets submodule: `724eba9de9e76761d9cefd52169926bc51c760a5`.
- Charts and metadata: `assets/preload/data/songs/{ugh,guns,stress}/`.
- Music: official `Inst.ogg`, `Voices-bf.ogg`, `Voices-tankman.ogg` for each song.
- Audio conversion: existing corrected VAGi encoder, four channels at 43,008 Hz; per-song sample origin and duration alignment are retained by the shared converter.
- Visual sources: pinned Week 7 battlefield layers; Tankman/BF rigs; GF Tankmen Sparrow atlas; official Tankman/BF icons.
- All proprietary/offline sources and generated conversions remain outside Git in ignored `ps1/build/` directories.

## Charts and audio payload

| Song | Easy notes | Normal notes | Hard notes | Samples / seconds | VAG bytes |
|---|---:|---:|---:|---:|---:|
| Ugh | 284 | 469 | 525 | 3,725,233 / 86.617 s | 8,570,880 |
| Guns | 488 | 766 | 903 | 6,041,462 / 140.473 s | 13,862,912 |
| Stress | 715 | 830 | 905 | 5,333,387 / 124.009 s | 12,257,280 |

The nine chart files total 72,288 bytes. The three audio files total 34,691,072 bytes. Average VAG CD throughput is approximately 99 kB/s per song. Songs and charts are loaded on demand; the catalog’s complete audio is not copied to RAM.

Individual generated-file SHA-256:

| File | SHA-256 |
|---|---|
| `UGH.VAG` | `20E2390B25DC4ED70FD71CA8DDE75607E28ED1A4EB8FCEB3CA1F569CCBF7593C` |
| `GUNS.VAG` | `068EC52D0DBDCAB7864C67E8D6EFC11167FAE41F140A40C10503932796B884F7` |
| `STRESS.VAG` | `0A186585F29A518DEF6E2F47786879381C23AD2AB116E606E338CF97F52C779F` |
| `W7SCENE.BIN` | `AA8054B57661832F0D282409417A13939C945FB57FD1AB726143B4DAF81D5ECA` |

## Visual scope and budgets

`W7SCENE.BIN` is three 256×256 8bpp pages (196,608 bytes) plus one 256-entry RGB555 palette (512 bytes). Two pages contain a static wide Battlefield composition; the third contains 64×64 character frames and icons. GF uses official `GF Dancing at Gunpoint` atlas frames 0 and 15. Tankman and BF each use idle plus four directional poses. This is intentionally a first playable adaptation: battlefield elements are static, the actor set is reduced, camera movement and the complete character animations are deferred for later refinement.

- Main RAM, ELF `.text + .data + .bss`: 907,114 bytes (`.text` 864,780; `.data` 2,442; `.bss` 39,892), +2,204 bytes versus v103.
- Note-state capacity rises from 674 to 905 bytes (+231 bytes); the largest chart file is 11,080 bytes and is loaded one at a time.
- Existing audio ring: 96 KiB. Stage transfer allocates one 64 KiB temporary page buffer, then frees it.
- Known-item estimate: about 1.08 MiB combining the ELF image, ring, largest chart blob and temporary scene buffer. This is not a runtime peak measurement and excludes precise stack/allocator overhead.
- VRAM: three shared 8bpp pages (192 KiB) plus the shared 512-byte CLUT. The loader restores the previous scene pages/palette when leaving Week 7.
- SPU: existing 16 KiB music double buffer and streaming/SFX voice allocation remain unchanged. Scene loads do not overlap music streaming.

## Build and delivery

- Toolchain: PSn00bSDK 0.24, GCC MIPS `mipsel-none-elf` 12.3, CMake 4.5, Ninja; ISO writer MKPSXISO 2.03.
- Build directory: `ps1/build/week7-v104`.
- Converted package cache: `ps1/build/week7-assets-v104`.
- Preconverted packages for the base and Weeks 4–7 were reused. The final Ninja dry-run contained only compilation of `spu_probe.c`, executable link and disc image generation. It did not schedule audio, chart or visual conversions.
- Raw ISO was kept in place. A distinct delivery BIN/CUE was made with `ps1/diagnostics/reorder_iso_system_cnf.py`; this only reorders the root directory record for `SYSTEM.CNF` and recalculates checksums for the affected directory sectors. No file extents or payloads change.
- ISO contains 100 files; `SYSTEM.CNF` is root entry 1. Extracted `FUNKIN.EXE` at LBA 26 is byte-identical to the linked executable and has a valid `PS-X EXE` header. Entry `0x8001F500`; load address `0x80010000`; text length `0xD4000`.

Delivery paths:

- [CUE](../ps1/build/week7-v104/delivery/funkin-ps1-week7-test-v104.cue)
- [BIN](../ps1/build/week7-v104/delivery/funkin-ps1-week7-test-v104.bin)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| delivered BIN | 282,232,944 | `66B2A773DD981BF987FAC50B54286461CDFB2BAECD177A497D300A3F9D6C57E5` |
| delivered CUE | 89 | `9C151AB23E78834CD2A624B037AC4AE5EAA2187E508956855C17647943839AC1` |
| linked ELF | 1,161,160 | `258C192A9287B59E99056F6CC44657A4458601678E2930DE8562661A6D7A9B5E` |

## Verification state

Compilation succeeded. Static checks confirm the ISO directory ordering, file count, PS-X EXE header, load/entry fields and byte identity between the EXE in the disc and the linked EXE. No emulator session or console execution was performed for this build.

Please test by loading the delivered CUE in DuckStation. Check that Freeplay opens, Ugh/Guns/Stress and all three difficulties launch, charts and vocals stay synchronized, Circle mutes BF only, the Week 7 scene and character poses render correctly, and end-of-song/return-to-Freeplay/retry do not corrupt audio or graphics. Week 7 is not user-validated yet; console hardware has not been tested.
