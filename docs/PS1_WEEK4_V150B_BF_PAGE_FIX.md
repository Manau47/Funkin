# Week 4 BF atlas preservation — v150b

## Cause

The user reports that GF looks better in v149b but BF has disappeared. The
base atlas descriptor table places BF idle/sing/miss frames on 8bpp page 7
(`x=768,y=256`). The v149 Week 4 package has eight logical pages, and its
loader previously uploaded them into physical slots 0–7. That replaced BF's
page 7 with the final Week 4 page (which contains the Mom icon), explaining
the missing player sprite. This is a VRAM ownership collision, separate from
the remaining Week 4 composition feedback.

## Fix

Keep physical page 7 owned by the shared BF atlas. Map Week 4 logical pages
0–6 to physical slots 0–6 and logical page 7 to physical slot 8, used for
menu/death art outside normal gameplay. The Week 4 draw path maps page IDs
through the same table as the loader. On leaving Week 4, the loader restores
the borrowed physical page 8 from the base atlas. Because Game Over also uses
page 8, retry reloads Week 4 logical page 7 from `W4SCENE.BIN` after the
death sequence and before countdown. The palette remains managed by the
existing stage restore path.

This build does not alter stage composition, camera, sizes, animation timing,
charts, gameplay rules, or audio. It does not claim that the user's separate
composition concerns are solved.

## Build and checks

- Source base: remote `ps1-port` v149 state, updated on GitHub as commit
  `fad877db19d67e12912ab10f20a240f23427967f`.
- Only `FUNKIN.EXE;1` differs in the v150b ISO payload compared with v149;
  source assets and generated packages were reused.
- `W4SCENE.BIN` SHA-256:
  `A91F0C52422B59E3067A0A006A5C655D5F554B7FD1EB6D6C71E09E9D35F49505`
  (524,800 bytes), unchanged.
- Shared BF-pose package SHA-256:
  `D3C6F317C0B108233C5D81774FA97775AFE2B2D40D98F46528EAD70543B67310`,
  unchanged.
- PS-X EXE: 1,028,096 bytes; load address `0x80010000`; entry
  `0x800255f0`; text size `0x0fa800`; SHA-256
  `0DB81AE9F156415570C1CF3AC52D9A7BBA11B9F8BC60B412D0D0B0BD1E8F4972`.
- Final BIN SHA-256:
  `B33E8AB3CCBFB08BF2F7B8FDBA534315A8243514866C28781258282502D6683A`.
- CUE SHA-256:
  `9102F11219009D9D2544D6AA021741BC7851519A75FC5C6155107EC9EA60F970`.
- ISO root order was checked: `SYSTEM.CNF;1` and `FUNKIN.EXE;1` are the
  first file entries. The extracted W4 package hash matches the source package.

The build compiled and the ISO checks passed. DuckStation execution and console
hardware have not been tested for this build. The user should test the CUE;
the BF fix is not considered validated until then.
