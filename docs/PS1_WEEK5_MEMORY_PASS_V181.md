# Week 5 memory pass v181

Date: 2026-11-08
Source baseline: local `ps1-port` checkout at `7057882fa4c481fb878de4cc27d3a827179f7ddd`, with the pre-existing dirty working tree preserved.
Previous scene-editor baseline: v180.
Runtime source of the new placement values: DuckStation Memory Scanner, user-adjusted Week 5 Christmas Mall scene.

## Changes

The Christmas Mall editor's eleven layer offsets were read from the active RAM values, signed as 16-bit values, and copied into both the scene defaults and the editor's initial values. Layer order is the `W5_EDIT_*` enum in `ps1/spu_probe.c`:

| Layer | X | Y |
|---|---:|---:|
| Background | -45 | -70 |
| Camera offset | -25 | -20 |
| Tree | -30 | -35 |
| Snow | 35 | 0 |
| Girlfriend | 10 | 5 |
| Opponent | 5 | 0 |
| BF | 35 | 0 |
| Upper crowd | -75 | -55 |
| Escalator | -125 | -80 |
| Lower crowd | -10 | -5 |
| Santa | -5 | 0 |

The Evil Mall variant remains at its previous zero offsets. Existing per-layer Q8 scales were retained unchanged; this pass captured and applied positions, not new scale values. The scene editor remains enabled and starts from these transforms.

The BF-focus camera target alone was raised by 11 world units (camera Y target changes from `BF_Y / 10 - 17` to `BF_Y / 10 - 28`). With the Week 5 zoom of `460/256`, this is a predicted screen displacement of about 19.8 pixels downward for BF. This is derived from the renderer's camera projection; it is not an observed screenshot measurement. Opponent and GF focus targets are unchanged.

## Validation status

- Memory values: read from DuckStation's scanner during the user's current scene-editor session.
- Static code values: verified in both defaults and editor initialization.
- Build: successful with PSn00bSDK 0.24. The dry-run scheduled only `spu_probe.c`, the SDK's `stream.c`, link, and ISO generation; no asset/audio/chart conversion. All 133 compared `.bin`, `.vag`, and `.h` resource outputs match v180 byte-for-byte.
- ISO: the raw CMake image placed `SYSTEM.CNF` at root record 93. The existing ISO root-order repair produced a separate delivery image with `SYSTEM.CNF` and `FUNKIN.EXE` at records 1 and 2; no previous image was overwritten.
- Output hashes: BIN `8EBF6D57C672D6F80B6A8F7F0382B31F999360BF72206674B1928539E55ABF28`; CUE `04BB688B251B080EB1BBD62603574ECC7EBC03393E895CF6C16D05EA1267BAAE`; EXE `3B94B3CED38002E2F2C04DD8D4D020F85A777647A8E40DA77969DFA9032554E9`; ELF `D44CA21220FDA7D4160095A0740912D295E1716E670A8325A809F0A0B001D3A4`.
- Exact build options, source diff, source files, resource hashes, and artifacts are in `C:/Users/Manau47/Documents/Codex/week5-memory-pass-v181-delivery/`.
- DuckStation visual result: pending user load and confirmation.
- Real PlayStation hardware: not tested.

## Scope

No scene assets, scales, animations, charts, scoring, gameplay rules, audio, or streaming code were changed. Earlier BIN/CUE deliveries remain untouched. This is a new build directory and delivery directory, separate from v180.
