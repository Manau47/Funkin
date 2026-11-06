# Week 3 / Philly train — v125

## Scope

v125 turns the approved official-asset scene composition into the next playable
Week 3 build. It keeps the v124 layered Philly stage, source-driven train pass,
camera transitions, chart, music, judgment rules, and gameplay unchanged. The
one visual correction is Pico's display size and the matching camera target.

## Scene and Pico scale

- The official stage layers remain: sky, city, lights, and behind-train scenery
  in the rear; the official train between rear and front; street/platform in
  front of the train; GF, Pico, then BF on the singing plane. Notes and HUD
  remain in the screen-space gameplay pass.
- The official Pico rig is still stored in its existing 72×84 atlas cells, so
  no sprite conversion, texture-page packing, or resource was changed. At draw
  time only, its full source cell is fitted to a 56×60 world rectangle. This
  is derived from its official rig bounds (about 442×474) relative to BF's
  official 411×412 frame rendered at 52×52, instead of stretching Pico to fill
  the old 72×84 cell.
- Pico keeps the official stage floor anchor. His camera target is now y=105,
  matching BF's y=105 in the current 52×52 display setup. This prevents the
  smaller display box from changing the approved vertical framing.
- The stage package and all other visual/audio packages are reused byte for
  byte from the v124 preconverted base. Week 3 uses the same eight 8bpp pages
  out of nine available; no new VRAM page or SPU allocation is introduced.

## Source-derived train schedule

The existing v124 implementation remains in place: an opportunity at beat
`4 mod 8`, a deterministic 30% choice after the source cooldown, the visible
train beginning 4.7 seconds after the trigger, 24 movement updates per second,
and the eight-car reset sequence. The source `train_passes` sound and GF
hairBlow/hairFall response are still deferred; v125 does not claim those parts
of the original stage behavior.

## Build and checks

- Source branch: `ps1-port`; base HEAD before this change: `f7ef9e2`.
- Toolchain: PSn00bSDK 0.24, MIPS GCC 12.3, CMake 4.5.0-rc1, Ninja 1.11.1.
- Build directory: `C:/Users/Manau47/Documents/Codex/b125w3a`.
- The dry-run contained only `spu_probe.c`, SDK `stream.c`, the executable link,
  and CD-image creation. It did not invoke any asset converter.
- Compilation and image creation succeeded. The SDK `stream.c` emitted the
  same `volatile`-qualifier warnings as prior builds.
- ISO verification/reordering found 117 root files and placed `SYSTEM.CNF;1`
  first and `FUNKIN.EXE;1` second. BIN size: 338,506,896 bytes.
- Delivered CUE/BIN: `ps1/build/week3-v125-philly-pico-scale-20261031/delivery-v125-rootfix/`.
- BIN SHA-256: `628DA54381F19AD9BF655A3A90B1D00571BFE14E516D60496433627BFC8E00A5`.
- CUE SHA-256: `4DC26C86D6B5E8C415A01B410FBB44B71C7BF047F876F754FF0283F021A51E4D`.
- No DuckStation or real-console run has been observed for v125. The next
  check is the user's manual DuckStation run of the supplied CUE.

