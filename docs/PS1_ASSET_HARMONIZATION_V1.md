# PS1 asset harmonization — build v1

Date: 2026-11-08
Branch: `ps1-asset-harmonization-v1`

## Reference

The user selected v183 as the accepted baseline. Its source base is local commit `7057882fa4c481fb878de4cc27d3a827179f7ddd`, assets submodule `724eba9de9e76761d9cefd52169926bc51c760a5`, and the original BIN/CUE plus source snapshot remain preserved under `C:/Users/Manau47/Documents/Codex/week5-lower-crowd-v183-delivery/`. BIN SHA-256: `63EAD9541EA8690C40DD2866E3DA976EC115BAC4D967C6F063D6DB52011C5B6E`; CUE SHA-256: `B86117223C353E77BF7AD9312C9835D65DA7A30986B3A1DCCB7A17D785BE33A6`.

The user's validation makes v183 the working visual/gameplay reference. The earlier v183 note that runtime testing was pending is superseded for the user's test; no new runtime or console test is claimed here.

## What this first build changes

This is the first delivery on a dedicated asset-harmonization line, restarting build numbering at **v1**. It uses the v183 source/package baseline and builds with the temporary Week 4/Week 5 composition editors and scene-demo mode disabled. Diagnostics stay disabled at boot. The settings remove editing/demo-only paths from the normal executable; charts, scene positions, art, animation timing, gameplay, audio, and CD packages are intended to remain unchanged.

The atlas audit in [`PS1_ASSET_SCENE_AUDIT_V183.md`](PS1_ASSET_SCENE_AUDIT_V183.md) found no further page reduction that is safe to apply automatically: scattered transparent texels are not a recoverable page, and palettes/page layouts are coupled to live UV/CLUT references. The previously measured lossless W4/W7 repacks are already part of the source lineage. Therefore v1 does **not** resize/recolor or repack scene graphics. This avoids changing the validated composition while the all-week source-to-screen table is used to select later groups.

## Reproducibility and results

- SDK/toolchain: PSn00bSDK 0.24, MIPS GCC 12.3.0, Ninja.
- Base generated packages: reused from the archived v183 build/package; no general graphics, audio, or chart conversion is part of v1.
- Build cache differs from v183 only in `FUNKIN_PS1_WEEK5_COMPOSITION_EDITOR=OFF` and `FUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF` (Week 4 editor and diagnostics already OFF); all other v183 options are retained.
- The build's dry-run and actual task list, ELF/EXE/BIN/CUE hashes, sizes, and section comparison are recorded after compilation below.
- User DuckStation test is pending. Build success does not validate runtime. No real-console test is claimed.

## Follow-up asset work

Use the per-layer audit data to select one coherent atlas family per iteration. Keep pixel indices and CLUTs paired, compare 320×240 output bounds including trim/pivot offsets, and retain independent week packages. Any new page reduction must show exact texel/CLUT equivalence and page/transfer savings before it is built into a gameplay image.

### v1 build result (2026-11-08)

The copied v183 build cache was retargeted inside the new v1 build directory; the original v183 cache/build was not edited. CMake dry-run listed exactly four tasks for the disc target: compile `spu_probe.c`, compile SDK `cdstream/stream.c`, link, and make the CD image. No atlas, audio, or chart generator appeared. The real Ninja build completed successfully; only the two existing `volatile` qualifier warnings in SDK `stream.c` appeared.

The 133 compared generated `.bin`, `.vag`, and `.h` resource products match the v183 build byte-for-byte (0 mismatches). Scene packages, palettes, charts, audio, and page counts were reused; no new graphics/audio conversion or atlas-page gain is claimed.

The compiler output is 1,388,652-byte ELF and 1,017,856-byte PS-X EXE. ELF section sizes: text 1,013,048 B, data 2,638 B, BSS 40,120 B. Compared with the archived v183 build ELF (text 1,008,920 B, data 2,766 B, BSS 40,104 B), the v1 code/data/BSS total is **4,016 B larger**, not smaller. Disabling the editor/demo compile paths did not produce a measured memory saving; this pass therefore makes no RAM optimization claim.

The raw mkpsxiso image placed `SYSTEM.CNF` at root entry 93. The existing PS1 root-order repair produced a distinct final BIN/CUE, with `SYSTEM.CNF` at entry 1 and `FUNKIN.EXE` at entry 2. The embedded EXE was extracted from the final image and its SHA-256 matches the linked EXE.

- Final BIN: 339,939,264 B; SHA-256 `DDF9FF1782A6D6286EEB9A427BB33180F739CC20134D74AA2E4D7F67BC338E55`.
- Final CUE SHA-256 `5684CE682125CF690946107B8B1F299CC49D6385E6CCB62D7118162CBA5B1E5D`.
- EXE SHA-256 `2A7B600A3DECEE06CCFF0D8A28747A14D22D6801C69D67D13DE3B39B5EFF4895`.
- ELF SHA-256 `25D12D3A19D1A4B46BB3F4EA594714C2700FBAF66221030101EBBBC56FB8DD43`.
- Final directory checks: 117 files; boot files are entries 1 and 2; embedded EXE matches the linker output.

The build has **not** been run in DuckStation or on a console in this pass. v183 remains the user-validated reference; v1 awaits the user's manual load and visual/audio test. The current evidence supports build reproducibility and unchanged resource payloads only.
