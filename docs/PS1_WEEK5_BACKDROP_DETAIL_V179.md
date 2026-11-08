# Week 5 v179 correction

This correction addresses the user's report that v178's higher-density art broke the composition. The v178 generator had copied the new Christmas texture page over the relocated Evil Mall texture page; its custom Sparrow extraction also used a different vertical registration than v177 and retained alpha fringes that the game later treats as transparent.

v179 keeps the detail-density experiment but preserves the original Evil page, matches v177's bottom registration, and trims to the runtime alpha threshold. Static normalized frame bounds now match v177 within 0.34 design pixels. The PS1 build and ISO are new and separate. User DuckStation validation is pending; this is not yet a visually approved fix.

Build v179

- Source base: `7057882fa4c481fb878de4cc27d3a827179f7ddd`; built source snapshot and CMake cache are preserved under `C:/Users/Manau47/Documents/Codex/week5-backdrop-hires-v179-delivery/source-snapshot/`.
- Dry-run: only `spu_probe.c`, the SDK cdstream source, link and ISO target were scheduled. No audio, chart, or other image conversion ran.
- Compilation and ISO creation succeeded with PSn00bSDK 0.24. Two existing `volatile` warnings remain in SDK `stream.c`.
- ISO checks: `SYSTEM.CNF` and `FUNKIN.EXE` are visible as root entries 1 and 2; `SYSTEM.CNF` boots `cdrom:\\FUNKIN.EXE;1`; the embedded PS-X EXE matches the compiled EXE byte-for-byte (`CCB567D5...21C3DB37`).
- BIN SHA-256: `9F3880640E755407E9DBE01271F85B56FF14E2DDD72F1582A0C345C6EDCAB45B`; CUE SHA-256: `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`.
- User execution in DuckStation is pending. The correction is not yet visually validated; no console test was run.
