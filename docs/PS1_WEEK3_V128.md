# Week 3 v128 — preserve BF atlas during the Philly scene

## Issue and fix

User feedback on v127: the stage and passing train are now visible, but BF is
still corrupted while idle during the train animation.

The generated visual table places BF idle and singing frames on 8bpp texture
page 7 (`x=768, y=256`). Week 3 temporarily loads its eight scene pages into
shared slots 0–7, so slot 7 replaces those BF texels with the last Week 3
character/train page. The BF idle renderer then samples unrelated Week 3
pixels. This is a texture-page lease collision, not an idle-animation timing
or train-timing issue.

v128 copies the original BF page 7 from `W1SCENE.BIN` into page 8's VRAM
rectangle while Week 3 is active and routes BF idle/singing frame draws to that
page. Page 8 normally holds the menu logo and is unused during gameplay. On
leaving Week 3, the original page 8 is restored from `W1SCENE.BIN` before the
menu is shown. BF's CLUT remains unchanged. The Week 3 city/train/street order,
camera, character positions, chart, input, health, judgement and audio paths
are otherwise untouched.

## Build

- Branch: `ps1-port`; source base: local v127 commit `62d5a739a8abe407a02183b1bd458e2b99d25c8c`.
- PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja; existing build tree `C:/Users/Manau47/Documents/Codex/b125w3a`.
- Ninja dry-run contained only `spu_probe.c`, executable link and CD image generation. No asset conversion ran; Week 3 scene, charts, audio and the previous delivery were preserved.
- Compilation succeeded. The ISO has 117 files, with `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second after the root-directory repair; size 338,506,896 bytes.
- Delivery CUE: `ps1/build/week3-v128-bf-atlas-20261031/delivery-v128-rootfix/funkin-ps1-week3-v128.cue`.
- BIN SHA-256: `7C120F8D12728D5415ABCDFBF0C7BCC87C745C4F2DF8DB785F78BE4B50C63A57`.
- CUE SHA-256: `DC38F0D306754DC50BAC14B9C907AEB4A4E766D7F4B68EA2F485B2D2B874AA55`.

## Validation status

The VRAM collision and remap are verified from the generated frame/page table
and the Week 3 loader/draw code. Compilation and static ISO checks passed.
v128 has not yet been observed in DuckStation; the BF idle appearance during
the train passage and the transition back to the menu still need the user's
manual test. No real-console test is claimed.
