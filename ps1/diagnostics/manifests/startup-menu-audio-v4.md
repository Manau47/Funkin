# Startup menu audio probe v4

- Diagnostic question: after the v3 green-lime marker confirmed base W1 atlas loading returns, do menu resource state, menu SFX upload, and menu VAG stream startup return?
- Branch: `ps1-asset-harmonization-v1`.
- Source commit: `963fec9cf26bcc2a73978774d5824fded76e5a03`.
- Previous observation: user confirmed v3 LIME, meaning `load_bopeebo_visuals()` returned after W1 scene file reads and GPU page/CLUT uploads.
- Build cache/toolchain: same incremental CMake/Ninja cache `ps1-asset-harmonization-v1-week2-bf-detail-v1-build`; PSn00bSDK 0.24 Win32, MIPS `mipsel-none-elf`; no reset.
- Checkpoints after base atlas success: TEAL after `load_menu_visuals()`; PURPLE after the menu/title state setup and successful `upload_menu_sfx()` DMA transfer; PINK after `start_stream_file("\\MENU.VAG", MENU_MUSIC_CHANNELS, true, true)` returns, followed by stopping the stream. An explicit false return shows AMBER and holds; a blocking operation leaves the previous marker visible.
- The normal frontend render/input loop is not entered. No gameplay, chart read, scene load, asset conversion, audio conversion or chart conversion occurs.
- Dry-run and actual incremental build: only compile `spu_probe.c`, link, and ISO generation. No resource-generation tasks. Build succeeded.
- ISO root order checked: 117 entries; `SYSTEM.CNF;1` entry 1 and `FUNKIN.EXE;1` entry 2. Delivery is in a new directory; v3 remains preserved.
- Delivery directory: `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-startup-menu-audio-v4-delivery/`.
- BIN SHA-256: `EECBBF291FC751BD9A4DDB9970A70CFE85ADD5E7F3224769706825768EECBEA3`.
- CUE SHA-256: `23573AB1D031524834C8011F4EABAAE8C624074CAFAA2AC926CDDBAF967A91FE`.
- PS-X EXE SHA-256: `643D73918ACC89DAE865B65C14DE78FBF9D5A31CC9A9F4CF84939956F96DAE61`.
- Runtime status: awaiting user’s DuckStation result. The prior LIME result is observed; v4 menu/audio checkpoints are not. No assistant emulator run or real-console test is claimed.
