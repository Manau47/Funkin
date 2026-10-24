# PS1 technical probe

This directory is a small, native PlayStation 1 program kept separate from the Haxe/Flixel desktop game. It initializes the GPU, draws a low-resolution text screen, polls controller port 1, and displays digital button states. Its `PlayerInput players[2]` storage keeps the two player states independent for a later local multiplayer mode; only player 1 is presented in this first probe.

## Toolchain

The project targets [PSn00bSDK](https://github.com/Lameguy64/PSn00bSDK), an open source C/C++ toolchain with CMake integration. Its official installation guide recommends a prebuilt release and CMake 3.21 or newer. This preset also uses the Ninja generator. PsyQ 4.6 and CodeWarrior are present in the supplied `Psxdev.zip`, but are proprietary legacy tools; CodeWarrior's Windows IDE is a poor fit for a reproducible modern build, and neither package is needed for this probe. The archive was inventoried only; no installer or executable was run and no SDK files were copied here.

The supplied PSn00bSDK 0.24 archive and CMake 4.4.4 portable ZIP are installed outside the repository under `Documents\Codex\toolchains`. PSn00bSDK includes GCC 12.3.0 and Ninja 1.11.1; the separate GCC archive is not needed. Set the SDK library path and add both tool directories to `PATH`:

```powershell
$env:PSN00BSDK_LIBS = 'C:\toolchains\PSn00bSDK-0.24-win32\lib\libpsn00b'
$env:Path = 'C:\toolchains\PSn00bSDK-0.24-win32\bin;C:\toolchains\cmake-4.4.4-windows-x86_64\bin;' + $env:Path
$env:CMAKE_ROOT = 'C:\toolchains\cmake-4.4.4-windows-x86_64\share\cmake-4.4'
```

`CMAKE_ROOT` is needed for this portable CMake ZIP in the current environment; a standard CMake installation may locate its modules without it.

From this directory, configure and build the executable and CD image:

```powershell
cmake --preset default
cmake --build --preset default
```

The generated image should be `build/funkin-ps1-probe.bin` with a matching `.cue`. Open the cue sheet in a PS1 emulator such as DuckStation or pcsx-redux. A successful build only proves that the compiler produced an image; emulator and real hardware runs must be recorded separately.

## Current status in this workspace

- CMake configuration succeeded with CMake 4.4.4 and PSn00bSDK 0.24 / GCC 12.3.0 / Ninja 1.11.1.
- `cmake --build --preset default` succeeded and produced `build/funkin-ps1-probe.exe`, `build/funkin-ps1-probe.bin` (381,024 bytes), and its cue sheet.
- The final build completed without compiler warnings.
- The generated cue/bin image booted and ran in DuckStation 0.1-8675. The probe rendered at 320×240 and the emulator reported 60 game/video FPS.
- The probe detected controller port 1 as digital pad type `0x04` and displayed the idle button states. A held-button value was not confirmed during this check.
- The on-screen footer was shortened after the first emulator view showed it clipped; the rebuilt image displayed the full footer.
- No real console run, audio playback, song, or gameplay was tested.

See [the port scope and source analysis](../docs/PS1_PORT.md) for the larger project, engine findings, and next steps.


