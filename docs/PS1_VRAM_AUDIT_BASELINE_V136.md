# v136 baseline archived before memory/loading audit

- Baseline local Git commit: 71274dc3441d9d4c6e4e9330ef3e504ca5bc22c1 (Document per-track VRAM resource policy).
- v136 code change commit: `f3106b5b72d699b072a479f86925e2e68b405137`.
- Source tree was clean before this archive.
- Original CMake build directory: ps1/build/week3-v136-vram-reset-cmake/.
- Exact CMake cache copy: ps1/build/archive-v136-vram-memopt/CMakeCache-v136.txt (local build archive, ignored by Git).
- CMake cache SHA-256: `32582C70D813D207F459EE6F11A916BB45C02374BDD7DC5D47AD1B27F9230A5F`.
- Build type: Debug; generator: Ninja; SDK: PSn00bSDK 0.24; compiler: MIPS GCC 12.3.
- FUNKIN_PS1_DIAGNOSTICS_DEFAULT=OFF; judgement, arrow, health-bar and scene-demo QA options are OFF; Dad autoplay lanes ON.
- Preconverted base/Weeks 4–7/WeekEnd 1 directories and audio/chart input paths are recorded verbatim in the archived CMake cache. No converted assets are copied into Git.
- v136 BIN/CUE are retained in `ps1/build/week3-v136-vram-reset-cmake/delivery-v136-rootfix/`.
- Original ELF SHA-256: `490DB803798DBCAE4168FD60BC380437BC6C9B72608BFDCBFD94A9D1E570D58F`.
- Original build BIN SHA-256: `FCA8A0A52F6A0070F824F0A8C9415B1EF84F4092B4DD0465CF42066ADB08D860`; CUE SHA-256: `8579EEF0E6966AFD78659F364593E560C8384148E9258D14FA88B196A842B340`.
- Delivered BIOS-order BIN SHA-256: `15A53475CC050D60B884D5A5B8572AD41F3788A185BF38406C51C859E61BCE1B`; CUE SHA-256: `054E3A25865253AB5009649E5F3607BA382DFF8811DB8B4882B2A3828F7B22A4`.

This manifest and the current commit identify the source/configuration snapshot before audit changes. The retained cache is machine-specific; reproduce on this host with the installed SDK and the original asset/audio inputs.

