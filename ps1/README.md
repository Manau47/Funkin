# PS1 technical probe

This directory is a small, native PlayStation 1 program kept separate from the Haxe/Flixel desktop game. It initializes the GPU, draws a low-resolution text screen, polls controller port 1, and displays digital button states. Its `PlayerInput players[2]` storage keeps the two player states independent for a later local multiplayer mode; only player 1 is presented in this first probe.

## Toolchain

The project targets [PSn00bSDK](https://github.com/Lameguy64/PSn00bSDK), an open source C/C++ toolchain with CMake integration. Its official installation guide recommends a prebuilt release and CMake 3.21 or newer. This preset also uses the Ninja generator. PsyQ 4.6 and CodeWarrior are present in the supplied `Psxdev.zip`, but are proprietary legacy tools; CodeWarrior's Windows IDE is a poor fit for a reproducible modern build, and neither package is needed for this probe. The archive was inventoried only; no installer or executable was run and no SDK files were copied here.

Install a PSn00bSDK release and CMake 3.21+ on the host, then set:

```powershell
$env:PSN00BSDK_LIBS = 'C:\PSn00bSDK\lib\libpsn00b'
$env:Path = 'C:\PSn00bSDK\bin;' + $env:Path
```

From this directory, configure and build the executable and CD image:

```powershell
cmake --preset default
cmake --build --preset default
```

The generated image should be `build/funkin-ps1-probe.bin` with a matching `.cue`. Open the cue sheet in a PS1 emulator such as DuckStation or pcsx-redux. A successful build only proves that the compiler produced an image; emulator and real hardware runs must be recorded separately.

## Current status in this workspace

- Source, CMake project, preset, and disc layout are present.
- Build was not run: CMake, Ninja, and the PSn00bSDK toolchain are not installed in the workspace environment.
- Emulator execution was not run: no PS1 emulator is available in `PATH`.

See [the port scope and source analysis](../docs/PS1_PORT.md) for the larger project, engine findings, and next steps.
