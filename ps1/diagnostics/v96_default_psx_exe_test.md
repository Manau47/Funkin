# v96 BIOS default `PSX.EXE` test — build record

## Question

With no `SYSTEM.CNF`, does the BIOS load the conventional root file `PSX.EXE`?
This separates BIOS fallback-name boot from the v95 path that used `SYSTEM.CNF` to launch `FUNKIN.EXE`.

## Inputs and build

- Reused byte-for-byte v94 PS-X EXE: `outputs/FNF-PS1-v94-direct-gp0/funkin-ps1-bopeebo-playable.exe`.
- PS-X EXE SHA-256: `CEF9783F7692982C29B4BF3D60D0D729AA83F369057BE8C25599EED02B13B986`.
- Source recipe: `ps1/diagnostics/v96_default_psx_exe_test.xml` (GitHub commit `49695f6c0aaa6f22f5f6ddae10b5d236b65e1652` on `ps1-port`).
- Packager: PSn00bSDK `mkpsxiso 2.03`.
- Package-only: no compiler, linker, gameplay assets, or resource conversions invoked.
- The ISO root contains one file, `PSX.EXE;1`, at LBA 23, 860,160 bytes. `SYSTEM.CNF` is absent.
- Root directory extent is 2,048 bytes.

## Artifacts

- BIN `funkin-ps1-v96-default-psx-exe.bin`: 1,041,936 bytes, SHA-256 `B0C96F7E04C13170B9975BC6B5DA222C4562AA6AAB16644D0C0252336160699D`.
- CUE `funkin-ps1-v96-default-psx-exe.cue`: 96 bytes, SHA-256 `1F6DF644A360E276FF5E93F5A1D824AD29369A7D6165D4C307854A68EB1F9FE4`.
- Static ISO extraction confirms the embedded `PSX.EXE` hash matches v94 exactly.

## Runtime status

Awaiting the user's DuckStation run. The yellow direct-GP0 marker would show that BIOS fallback-name boot reached the reused v94 executable. This is a diagnostic boot disc, not a playable build. No real-console result is claimed.
