# v97 early SYSTEM.CNF with 48 root files — build record

## Diagnostic question

Does the exact v94 EXE boot through `SYSTEM.CNF` when the ISO still has 48 root entries and a two-sector root directory, but `SYSTEM.CNF` is among the first entries? v94 had `SYSTEM.CNF` at directory offset 2460 (record 41); this test moves it to offset 156 (record 2) while preserving the EXE and SYSTEM.CNF bytes.

## Build

- Reused EXE SHA-256: `CEF9783F7692982C29B4BF3D60D0D729AA83F369057BE8C25599EED02B13B986`.
- Reused SYSTEM.CNF SHA-256: `47F527BE2BB4A755DEE290388416D7133FFD88D6053035D1BF40728D03645A63`.
- 46 one-byte `ZPAD####.BIN` entries bring the visible root file count to 48; `mkpsxiso` sorts `FUNKIN.EXE` and `SYSTEM.CNF` before these padding names.
- Recipe: `ps1/diagnostics/v97_system_cnf_early_many_entries.xml` (commit `036b0becd53ca82f03ac830afb8bd14ba988acff`); one-byte fixture `ps1/diagnostics/v97_pad.bin` (commit `c8214ba6ea3b25ad101351d7db37c728f2884938`), both on `ps1-port`.
- Tool: PSn00bSDK `mkpsxiso 2.03`. Package-only; no compilation, linking, or game asset conversion.
- ISO root directory: 4,096 bytes, 48 visible files. `FUNKIN.EXE;1` at LBA 25; `SYSTEM.CNF;1` at LBA 24. `SYSTEM.CNF` is directory record 2 at byte offset 156.
- Static extraction of both files matches the source hashes exactly.

## Artifacts

- BIN `funkin-ps1-v97-root-entry-test.bin`: 1,154,832 bytes; SHA-256 `D68E248BE55FCBEBCE8C1BFCA5E4C10A09E56AAB166A0141EB007D7F2C829A33`.
- CUE `funkin-ps1-v97-root-entry-test.cue`: 96 bytes; SHA-256 `2432294BEC13641C6EF0E427E25200D52CAC8CBD9D7CDDA9139AA7B0CBD29C88`.

## Runtime status

Compiled and statically inspected; awaiting user DuckStation observation. If the yellow marker appears, early `SYSTEM.CNF` lookup succeeds even with 48 root files/two directory sectors, implicating late entry position in v94/v76. If it does not, the root count/extent or another BIOS search limit remains implicated. The screen marker is only the v94 diagnostic loop; this is not a playable build and not a real-console test.
