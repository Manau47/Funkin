# Startup video initialization diagnostic v1

- Source base: local `ps1-asset-harmonization-v1` commit `ab91222d6939a19c7323db1a3807090633775209`.
- Diagnostic source commit: `6e7684c1641e622fe3311c338b5cb191d06f403b`.
- GitHub branch source commit (same source change): `6e099c7d2f3c7a915b4d622945256b0278f14438`.
- PSn00bSDK: 0.24 Win32; MIPS target `mipsel-none-elf`; CMake/Ninja build.
- Build cache reused: `ps1-asset-harmonization-v1-week2-bf-detail-v1-build`.
- Options: `FUNKIN_PS1_STARTUP_MAIN_MARKER=ON`; before/after-BSS markers `OFF`; diagnostics, scene demo, health-bar QA, Week 4/5 editors `OFF`; Dad lanes `ON`.
- Startup path in this image: raw GP0 white rectangle at the beginning of `main()`; `init_video()`; solid green 320×240 GP0 SDK fill; `DrawSync`; wait in `VSync`. The normal startup path is compiled but the diagnostic gate stays active. No CD, SPU, chart, scene, menu, or gameplay initialization is reached.
- Dry-run of the original build predicted only `spu_probe.c` compile, executable link, and disc image generation. No resource-generation commands were in the dry-run. This was also observed in the actual Ninja output.
- Week 2 generated payloads were reused byte-for-byte: `week2-scene.bin` SHA-256 `E011912106CF63E9AABE0C7F73B28204BA63882A67AA204C637DA087E6B79EA6`; `week2-scene-bf-overlay.bin` SHA-256 `9242C6D5F7196E0C95A12CF2D64C4A13BD5372057FD8027516DD2D4D650B4700`; `week2_bf_overlay_data.h` SHA-256 `EA90C31AEEB54FA1856643538AC69B8A5E30D1178B40CCCB74179B0F46842970`; `week2-gf-animation-manifest.txt` SHA-256 `E9D5BC5BADF6C09BE9096F7C5C37BFB718CFCBAFAA6BCEE35B26F7C3AD438BDD`.
- The new ISO contains 117 root files, same names and payload hashes as the user-observed white-marker v2 image except `FUNKIN.EXE;1`. `SYSTEM.CNF;1` is root entry 1 and `FUNKIN.EXE;1` entry 2. The payload comparison was performed on extracted ISO file contents.
- Raw generated BIN SHA-256: `3B9EC4DA8C9B2AF74E5A7E90C1397CFFF18835E1B6617F339BDFC80FA77B8302`.
- Boot-order-fixed delivered BIN SHA-256: `4F01E1076E82C3638EAA800D4653E3B1DE795B5B14BFE2BFBE3EDFAD626FDF43`.
- Delivered CUE SHA-256: `3AD9FE35CDFDEC3EE78B3AFDA49DE5EA604663C29512A677610C6876ECA74B6F`.
- PS-X EXE SHA-256: `9F700BE27716BDAE232E8C7C0A00B9ACAB7FB09343517AA694594E262B29EC40`; its extracted ISO payload matches byte-for-byte. Entry point `0x80022f38`; load address `0x80010000`; executable payload size `0x0f8800`.
- ISO ordering correction changed only the root directory sectors; `ps1/diagnostics/reorder_iso_system_cnf.py` verified original sector EDC/ECC and regenerated them for the modified sectors.
- Runtime status: not yet tested by the user in DuckStation. Expected observation: BIOS-mode white marker followed by a green 320×240 frame if `init_video()` returns. A continuing white rectangle means execution reached `main()` but did not reach the post-video marker; no claim of game startup or gameplay validation.
- Delivery directory (outside Git): `ps1-asset-harmonization-v1-startup-video-init-v1-delivery`.


