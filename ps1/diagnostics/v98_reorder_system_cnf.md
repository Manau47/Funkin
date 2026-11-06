# v98 v76 root-order-only startup test — build record

## Diagnostic question

Does the original v76 executable boot when the exact same disc and root contents keep their original LBAs, but `SYSTEM.CNF` is moved from the 41st visible file entry (offset 2460) to the first visible file entry (offset 96)? This tests the root-directory lookup hypothesis in the actual v76 disc, not the v94 marker executable.

## Transformation and static checks

- Input BIN: `outputs/FNF-PS1-v76-week2-week3-loading/funkin-ps1-bopeebo-playable.bin`, SHA-256 `828489413342768586115C99AD5C1A6B82FC65F88800A17F16308A3BC9E08402`.
- Input and output contain 48 visible root files; root extent remains LBA 22, 4,096 bytes. All files retain their original LBAs, sizes, and content hashes.
- The only changed bytes are within the two raw sectors covering the root directory: 2,347 bytes differ. Mode 2/Form 1 EDC/ECC for both root sectors was verified after the patch.
- Original v76 FUNKIN.EXE SHA-256: `2E8E07F77EF62055636A49514B6DB9A16AD3C14E16F8B7F90ECAD7B2F6028356` (unchanged). SYSTEM.CNF SHA-256 `47F527BE2BB4A755DEE290388416D7133FFD88D6053035D1BF40728D03645A63` (unchanged).
- Root order after patch: SYSTEM.CNF first visible entry, byte offset 96; the directory remains otherwise ordered as before.
- Patch tool: `ps1/diagnostics/v98_reorder_system_cnf.py`, published on `ps1-port` in commit `0b7739a509adc5f3dd20f45064a2171d596f2835`.
- No compiler, linker, asset converter, or file re-encoder was run. The tool rejects a mismatched input BIN and refuses to overwrite output paths.

## Artifacts

- BIN `funkin-ps1-v98-root-order-v76.bin`: 131,942,496 bytes; SHA-256 `243B80B8D21F61ED5D497A6A65FF64297FDFF481D7BC1BD89163623F56175755`.
- CUE `funkin-ps1-v98-root-order-v76.cue`: 92 bytes; SHA-256 `6458E9445E417BF7665389B610E05AF643CDB9E72B8D7C4F9C365FF544852316`.

## Runtime status

**Validated by the user in DuckStation:** v98 is functional. This is the original v76 image and executable with only the ISO root directory order changed, so the late SYSTEM.CNF entry is confirmed as the practical boot regression. No duration, detailed gameplay/audio recheck, or real-console test was reported.
