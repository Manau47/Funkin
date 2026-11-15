# Startup title frame probe v5

- Diagnostic question: after the user-observed v4 pink marker, do the first normal frontend feed, title render/art upload, and frame presentation return?
- Branch: `ps1-asset-harmonization-v1`.
- Source commit: `c7124f0ffb43302a358559df81c8195573a0549b`.
- Previous observation: user confirmed v4 PINK. This means `start_stream_file("\\MENU.VAG", ...)` returned. It does not establish sustained playback or a rendered title screen.
- Build cache/toolchain: existing PSn00bSDK 0.24 Win32 / MIPS `mipsel-none-elf` CMake/Ninja cache. No reset.
- Sequence after v4: keep the menu stream active; call `feed_stream()` once and show ORANGE-RED if it returns; call the actual title `draw_menu_screen(samples, rate)` and show INDIGO if it returns; call `display_frame()` and show FUCHSIA if the first frame is presented. CD/stream error shows AMBER and holds. A blocking step leaves the prior color. Stop the stream after the first presented frame, then hold.
- Title draw includes the actual `load_menu_screen_art(SCREEN_TITLE)` path and title/GF/text draw commands. No menu navigation, Freeplay interaction, chart, song scene, or gameplay runs.
- Dry-run and actual build: compile `spu_probe.c`, link ELF, generate ISO only. No resource conversion. Compilation succeeded.
- ISO ordering verified: 117 root entries, `SYSTEM.CNF;1` first, `FUNKIN.EXE;1` second. New delivery directory; previous v1–v4 outputs were not overwritten.
- Delivery directory: `C:/Users/Manau47/Documents/Codex/ps1-asset-harmonization-v1-startup-title-frame-v5-delivery/`.
- BIN SHA-256: `CB19337AB49F780F0437E7BBFD7350A7A142CA05DE7BF0C81C43ADE7DCF23455`.
- CUE SHA-256: `6C315ACF29AA77E5C453324A61C0B5CDD8E513EC500B7EEEDC28CEA8B67B9092`.
- PS-X EXE SHA-256: `B5A31F16E903E978AC79FD37DACB3176BC97DF5F9DE04A53E6EAEFE9685E84A6`.
- Runtime status: user confirmed v4 pink; v5 awaits the user's DuckStation observation. No emulator execution or real-console test is claimed.
