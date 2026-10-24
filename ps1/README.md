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

## Optional CD audio clock probe

The CD audio probe builds a separate disc image with a 12-second synthetic click track. It displays CD-DA track position read from the drive's Subchannel Q data and derives a 120 BPM visual pulse from that position. It does not use a video-frame counter as its music clock. The generated audio is only a timing fixture; it contains no FNF music.

Generate the WAV outside the repository, then configure and build the audio image:

```powershell
$testDir = Join-Path $env:TEMP 'fnf-ps1-audio-probe'
python .\generate_click_track.py (Join-Path $testDir 'audio-probe.wav')
cmake --preset default "-DFUNKIN_PS1_AUDIO_WAV=$(Join-Path $testDir 'audio-probe.wav')"
cmake --build --preset default --target ps1-audio-disc
```

Open `build/funkin-ps1-audio-probe.cue` in DuckStation. The source WAV and generated disc image stay outside Git; `/ps1/build/` is ignored.

## Optional CD-to-SPU stream probe

The selected audio direction is PSn00bSDK's CD-to-SPU ADPCM streaming driver. The probe uses its `Stream_GetSamplesPlayed()` sample clock, anchored by SPU block interrupts and interpolated between interrupts, then derives elapsed time and the 120 BPM visual pulse from that clock. The driver defaults to VSync for interpolation; the displayed position is audio-clock based rather than a frame count accumulated as music time.

Build against the SDK's own VAGi fixture, which stays outside the repository:

```powershell
$sdk = 'C:\Users\Manau47\Documents\Codex\toolchains\PSn00bSDK-0.24-win32'
cmake --preset default "-DFUNKIN_PS1_AUDIO_VAGI=$sdk\share\psn00bsdk\examples\sound\cdstream\stream.vag"
cmake --build --preset default --target ps1-spu-disc
```

Open `build/funkin-ps1-spu-probe.cue` in DuckStation. The CMake build uses `stream.c` and `stream.h` from that SDK installation directly; it does not vendor SDK files into Git. The probe requires PSn00bSDK 0.24's example sources to be installed alongside the library. Supply a local stereo VAGi file with `FUNKIN_PS1_AUDIO_VAGI` to test other material. The `FUNKIN_PS1_AUDIO_WAV` CD-DA probe remains a separate comparison target (`ps1-audio-disc`), not the selected game-audio path.

Generate the rights-safe 8-second stereo fixture outside Git. Its 16 beats are exactly aligned to 43,008 Hz, 120 BPM, and the 4,096-byte VAGi interleave; a beat spans three stream chunks and the loop spans 48 chunks:

```powershell
$fixture = Join-Path $env:TEMP 'fnf-spu-stereo.vag'
python .\generate_spu_fixture.py $fixture --channels 2 --loop-beats 16
$sdk = 'C:\Users\Manau47\Documents\Codex\toolchains\PSn00bSDK-0.24-win32'
cmake --preset default "-DFUNKIN_PS1_AUDIO_VAGI=$fixture"
cmake --build --preset default --target ps1-spu-disc
```

`spu_probe.c` checks the VAGi signature/version, stereo channel count, sample rate, sector/block alignment, SPU double-buffer range, expected payload length against the ISO file size, command returns, read completion, and a bounded initial-buffer wait. Error codes 1–8 identify missing file, header read, header format, CD command, CD read, initial-buffer timeout, stream start, or underrun. Any runtime CD error or underrun stops the clocked test instead of displaying a misleading position.

`Stream_GetSamplesPlayed()` is not a sample-accurate hardware read head. `stream.c` increments its base counter by `interleave / 16 * 28` decoded samples on each SPU block IRQ, then interpolates elapsed samples from its configured timer. The default timer is VSync at 60 Hz NTSC or 50 Hz PAL (one-frame interpolation resolution); the block IRQ anchors the estimate. The counter is monotonic across the feeder's file loop and does not wrap when sectors restart at the beginning. The SDK underrun branch invokes a callback but does not advance/re-anchor `play_time` or `last_updated`; therefore the displayed clock would no longer track playback, and this probe treats an underrun as failure.

The generated stereo image builds successfully. DuckStation 0.1-8675 is available, but this session could not select the image in its native file dialog: the automation can observe the dialog but cannot target its separate window. CLI attempts while the dialog was open did not load the image. No sound, pulse, position advance, loop, error counter, or multi-minute drift was observed. **The stereo stream is not validated in an emulator.**

For the requested validation, open `build/funkin-ps1-spu-probe.cue` via DuckStation **Système → Démarrer le fichier…**. Confirm audible left/right clicks, the `AUDIO` and `SAMPLES` values advancing, the visual `BEAT` marker at 120 BPM, and the sound looping at 8 seconds while the counter continues. Leave it running for at least three minutes; record the counter at start and end, count beat markers over a timed interval, and compare audio clicks to markers at the beginning and end. Report visual alignment separately from a measured drift. Any nonzero CD error or underrun fails the run. The currently built files are `build/funkin-ps1-spu-probe.bin` (858,480 bytes) and its 86-byte `.cue`; both are ignored build artifacts and are not committed.

Input buttons also remain unvalidated under active play. Boot `build/funkin-ps1-probe.cue`, then test each direction, triangle/circle/cross/square, Start, press/hold/release, multiple buttons at once, and controller unplug/replug. The probe displays active button count, held frames, and pressed/released masks. A detected pad alone is not evidence that these transitions passed.

The four-channel attenuation test is intentionally deferred until stereo playback passes. The planned shared interleaved stream puts instrumental L/R and voice L/R in one file, and mutes voices by setting only those SPU channel volumes to zero while the stream continues. For 4,096-byte interleave at 43,008 Hz, the SDK formulas imply 7,168 samples per channel per chunk; a four-channel chunk is 16 KiB and its SPU double buffer is 32 KiB, occupying `0x1010–0x9010` (4 of 24 SPU voices). The 96 KiB main-RAM ring buffer holds about 1.0 second of four-channel ADPCM at this rate; the 24-sector refill threshold is 48 KiB. Encoded payload throughput is about 98.3 kB/s (48 CD sectors/s), leaving 20 SPU voices for effects. These are formula-based estimates, not console measurements; CD seek/read jitter, CPU/GPU/RAM headroom, channel volumes and voice-only mute behavior still need emulator and hardware testing. No four-channel fixture has been built or tested in this milestone.

### Retry after preload timeout

The first manual DuckStation run displayed error code 6 with zero CD errors and zero underruns. The cause was that `CdReadCallback(0)` used for the header read was never followed by reinstalling the streaming completion callback. The stream read now registers its callback before `CdRead`; only `CdlComplete` credits received sectors and feeds the ring buffer. CD errors, immediate read-start failures, and `CdReadSync` failures release `read_pending`; timeout cancellation is bounded. The error screen now shows buffer fill, pending state, requested/received sectors, and callback totals.

The 57,344-byte preload requirement (24 sectors plus one 8,192-byte stereo chunk) fits in the 98,304-byte ring buffer. Its initial read can request 48 sectors, which supplies 98,304 bytes on successful completion. This proves the prefill condition is reachable by calculation; the corrected image still needs a manual run to verify the actual callback and CD path. It has not yet been executed, and the stereo test is still unvalidated.

The rebuilt image is in `build/spu-retry/funkin-ps1-spu-probe.cue` and `.bin` (860,832 bytes). It was built in a separate ignored folder because the prior image was locked by the active DuckStation session. No four-channel test should begin until this stereo retry passes.

### Callback contract retry

PSn00bSDK 0.24's `CdRead()` completion callback receives `CdlDataReady` (1) after the final requested sector has been copied, not `CdlComplete`. The previous probe expected `CdlComplete`, matching the reported one callback, zero received sectors and an empty buffer. The probe now accepts only `CdlDataReady` to feed the received buffer; it records the callback event/payload, `CdRead`/`CdReadSync` returns, response bytes, and the specific read-error cause. See [the port notes](../docs/PS1_PORT.md) for the API contract, sector range, and test status.

The refreshed image is in `build/spu-contract-fix/funkin-ps1-spu-probe.cue` and `.bin`. It is compiled but not yet run in DuckStation; the stereo stream is not validated.


