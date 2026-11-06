# Week 2 background crop correction — v121

## Change

The user reported that v120 showed lightning but no static Week 2 decor. At the common Dad camera focus (`camera_x=67`), the v120 background origin and 2.25× zoom put the left edge at approximately screen x=-117, so the viewport began around source x=52. That crop removed much of the distinctive window at the left of the official backdrop and emphasized a dark, low-detail area.

v121 retains the 2.25× zoom, tint 192, vertical offset 85, beat pulse, character cameras, and all game/audio behavior. It offsets the static backdrop and lightning together by +36 world units on X. At the same camera and zoom, the backdrop's left edge moves to approximately screen x=-36, restoring source x≈16 at the viewport's left edge, matching v119's previous crop boundary. The lightning retains its relative alignment with the room. This is a crop/framing correction, not a character camera change.

## Build and retained inputs

- Branch `ps1-port`; parent is the local v120 commit `Zoom Week 2 background for v120`.
- PSn00bSDK 0.24, MIPS GCC 12.3.0, CMake 4.5, Ninja, Debug.
- Fresh build directory: `C:/Users/Manau47/Documents/Codex/b121w2`.
- Reuses all converted asset packages from v119/v120. The dry-run should contain only source compilation, link, and disc image creation; no conversion.
- Static ISO root order is repaired with `reorder_iso_system_cnf.py`: `SYSTEM.CNF;1` first and `FUNKIN.EXE;1` second.

The raw CMake ISO is preserved in `delivery-v121-pre-rootfix/`; the corrected output is in `delivery-v121-rootfix/`.

- Image size: 338,203,488 bytes; 117 root files.
- BIN SHA-256: `72D7312CC1FA0CCF61CD3693DDF68E0EFE8A7F725EA6A9721F094DADB01AA3BD`
- CUE SHA-256: `BDA46FD0A026D16A0676E12571FB4D6AA20543D022A974902780EE999771D653`
- Executable SHA-256: `3CA99FBD4B7133B197B88B237319F8A5CFC99C74887DE924771F5ED6E5689C48`
- Reused `week2-scene.bin` SHA-256: `BA93EC25BDAEABFDC21AA4BF32D2E7910367517DD4CEF863A3EB9259137F11D4`

Delivered files:

- [`funkin-ps1-bopeebo-playable.cue`](../ps1/build/week2-background-v121-cropfix-20261031/delivery-v121-rootfix/funkin-ps1-bopeebo-playable.cue)
- [`funkin-ps1-bopeebo-playable.bin`](../ps1/build/week2-background-v121-cropfix-20261031/delivery-v121-rootfix/funkin-ps1-bopeebo-playable.bin)

## Validation status

The user tested v121 and reports the static background is still absent while lightning remains. Therefore the X-crop correction did not solve the issue. v122 keeps v121's transform but changes the static room draw path: it clips the oversized room quads to the 320×240 viewport and adjusts their UVs before submitting them to the GPU. This isolates whether the PS1/DuckStation textured-quad clipping path caused the missing backdrop. No runtime fix is claimed until the next manual test.
