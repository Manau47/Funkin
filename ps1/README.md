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
- The user reports a manual DuckStation pass of the four-channel synthetic stream: 3 min 08 s, 0 CD errors, 0 underruns, and Circle voice mute/restore worked. Precise drift and real-console behavior remain unmeasured.
- The user confirmed the full-length classic Bopeebo audio test and BF mute/restore with Circle (DuckStation keyboard mapping `L`). Their listening report noted degraded sound. Investigation found both low-rate resampling loss and an ADPCM shift-selection bug; the encoder fix and 43,008 Hz variant are documented in [PS1_PORT.md](../docs/PS1_PORT.md). The 43,008 Hz image ran through `FINISHED (NO LOOP)` in DuckStation with 0 underruns and 0 CD errors. A/B listening of the corrected variants and real-console behavior remain unverified.
- The user subsequently confirmed the corrected six-channel 43,008 Hz version sounds good and that Circle/`L` mutes BF. Its reproducible reference image remains in ignored `build/bopeebo-audio-43008-final/`.
- The user confirmed the SFX diagnostic from commit `7a6250c`: automatic pre-music/in-music playback and manual Square/`J` playback work. They report that the temporary effect is somewhat quiet; defer adjustment to final mix work. Keep the four-channel configuration, pan default `5/7`, and Circle/`L` BF mute. Pan adjustment is retained at runtime; saving it belongs with the future options menu. The first Bopeebo Normal prototype now adds chart rendering, input, scoring, hold notes, health and a restart path while keeping all source chart/audio assets outside Git.
- The user confirmed the hold-release fix at commit `01e84a0`: early release muted BF, a later BF success restored its voice, and Dad/BF placement was correct. This validation is specific to that earlier build.
- The latest graphics-audit build is generated in `build/bopeebo-visual-audit-v5/`. It reconstructs actual Dad and GF poses from the pinned Animate rigs, keeps BF's official Sparrow poses, composites the week 1 stage, and preloads all textures before starting CD streaming. See [PS1_PORT.md](../docs/PS1_PORT.md) for conversion details, VRAM/RAM estimates, build inputs and validation limits.
- That build compiled with PSn00bSDK 0.24 / GCC 12.3.0 and was observed briefly in DuckStation at 320×240 and about 60 IPS. The GPU pages, character art and corrected framebuffer-safe CLUT placement displayed correctly. CD/underrun diagnostics, full-song gameplay, input/mute/holds/SFX/restart, user acceptance and real console behavior remain unverified for this build.

See [the port scope and source analysis](../docs/PS1_PORT.md) for the larger project, engine findings, and next steps.

### Menus and next presentation steps

The user has validated v52's animated judgment/combo popups in DuckStation. Palette-transfer synchronization in the visual loader is retained. The current menu prototype has official title/freeplay backgrounds, logo, GF dance, FreakyMenu music, and official navigation sounds. v54 adds the three-frame selected Freeplay graphic and labels the sole playable entry `BOPEEBO / NORMAL`. Build it with the configured `bopeebo-playable-normal-4ch` CMake directory; the user-facing BIN/CUE is in `outputs/FNF-PS1-v54-menu-freeplay/`.

v53's title was observed in DuckStation; its Freeplay screen was also seen. v54 compiles but has not yet been observed in the emulator. The complete controller path, menu audio during transitions, song launch/return, Game Over/retry, results, and real-console behavior remain to be verified. The current C code still returns to Freeplay on both health depletion and song completion; it has no Game Over or results state. See the latest v52-v54 entries and source audit in [PS1_PORT.md](../docs/PS1_PORT.md).

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

## Current playable milestone: Bopeebo UI

The current branch adds isolated Dad/BF note groups, colored outlined arrows and hold shapes, a compact HUD, and audio-clocked camera movement. Triangle toggles Dad's autoplay display; the underlying lanes, chart and animation remain active. The current compact-HUD disc is `build/bopeebo-fnf-ui-v9/funkin-ps1-bopeebo-playable.cue`; configure `FUNKIN_PS1_DIAGNOSTICS_DEFAULT=ON` for a diagnostics-on QA build. Conversion and live DuckStation findings, including the pending verification of the 4bpp miss-page fix, are documented in [the PS1 port notes](../docs/PS1_PORT.md#interface-de-notes-et-composition-v6). Build inputs (PSn00bSDK, chart, VAGi, art assets and FFmpeg) remain local/outside Git. The final disc, comparison disc and captured screenshots are in ignored `ps1/build/bopeebo-fnf-ui-v9/`, `ps1/build/bopeebo-fnf-ui-off-v9/` and `ps1/build/bopeebo-fnf-ui-v7/` folders.

The current menu-layout test is `outputs/FNF-PS1-v57-options-menu-test/FNF-PS1-v57-options-menu-test.cue`. It replaces Merch with the user-approved Options lettering. Square (`J`) previews its selected animation; Cross (`K`) continues to Freeplay as before. Load the CUE in DuckStation manually; v57 compiled but has not yet been observed running. The previous v56 image remains in `outputs/FNF-PS1-v56-menu-layout/`. Details and the backup of pre-integration sources are in [the v57 port notes](../docs/PS1_PORT.md#v57-essai-intégré-du-libellé-options).

### Retry after preload timeout

The first manual DuckStation run displayed error code 6 with zero CD errors and zero underruns. The cause was that `CdReadCallback(0)` used for the header read was never followed by reinstalling the streaming completion callback. The stream read now registers its callback before `CdRead`; only `CdlComplete` credits received sectors and feeds the ring buffer. CD errors, immediate read-start failures, and `CdReadSync` failures release `read_pending`; timeout cancellation is bounded. The error screen now shows buffer fill, pending state, requested/received sectors, and callback totals.

The 57,344-byte preload requirement (24 sectors plus one 8,192-byte stereo chunk) fits in the 98,304-byte ring buffer. Its initial read can request 48 sectors, which supplies 98,304 bytes on successful completion. This proves the prefill condition is reachable by calculation; the corrected image still needs a manual run to verify the actual callback and CD path. It has not yet been executed, and the stereo test is still unvalidated.

The rebuilt image is in `build/spu-retry/funkin-ps1-spu-probe.cue` and `.bin` (860,832 bytes). It was built in a separate ignored folder because the prior image was locked by the active DuckStation session. No four-channel test should begin until this stereo retry passes.

### Callback contract retry

PSn00bSDK 0.24's `CdRead()` completion callback receives `CdlDataReady` (1) after the final requested sector has been copied, not `CdlComplete`. The previous probe expected `CdlComplete`, matching the reported one callback, zero received sectors and an empty buffer. The probe now accepts only `CdlDataReady` to feed the received buffer; it records the callback event/payload, `CdRead`/`CdReadSync` returns, response bytes, and the specific read-error cause. See [the port notes](../docs/PS1_PORT.md) for the API contract, sector range, and test status.

The refreshed image is in `build/spu-contract-fix/funkin-ps1-spu-probe.cue` and `.bin`. It is compiled but not yet run in DuckStation; the stereo stream is not validated.

### Stereo result and four-channel prototype

The user manually validated the stereo image in DuckStation for 4 min 02 s: zero underruns, zero CD errors, and no listening problems reported. Precise drift was not measured, and no real-console test was done.

The independent four-channel target uses one interleaved VAGi stream for instrumental L/R then voice L/R. PSn00bSDK 0.24's `cdstream` counts enabled `channel_mask` bits, sizes each chunk as `interleave × channel_count`, and transfers each channel's interleaved data to its own SPU voice. The four-channel probe pans channels 0/1 left/right and 2/3 left/right. Circle toggles only voice-channel volume between zero and `0x2fff`; playback keys and stream position continue. On-screen text shows pad connection, Circle state, voice mute state, audio position, buffer, CD errors, and underruns.

Generate and build in a separate folder (fixture remains in `%TEMP%`):

```powershell
$fixture4 = Join-Path $env:TEMP 'fnf-spu-4ch.vag'
python .\generate_spu_fixture.py $fixture4 --channels 4 --loop-beats 16
cmake --preset default -B .\build\spu-four-channel "-DFUNKIN_PS1_AUDIO_VAGI_4CH=$fixture4"
cmake --build .\build\spu-four-channel --target ps1-spu-4ch-disc
```

Open `build/spu-four-channel/funkin-ps1-spu-4ch-probe.cue` in DuckStation. Confirm both signal groups are distinct, toggle Circle and check that only voice audio mutes while `SAMPLES` continues, then watch CD errors and underruns over several minutes. The four-channel image is not validated until this run is observed. See [PS1_PORT.md](../docs/PS1_PORT.md) for the format checks, mix headroom, and RAM/SPU/CD calculations.



## Official note art candidate (v10)

The playable Bopeebo candidate now converts note arrows, strumline idle/press/confirm frames, and sustain bodies/caps from the pinned official Funkin note style. The conversion runs from CMake with `FUNKIN_PS1_ASSETS_DIR` and FFmpeg; source XML/PNG assets remain in the asset submodule and generated art tables remain under the ignored build directory. The final candidate image and DuckStation captures are in `build/bopeebo-official-assets-v10/` (ignored). Its user-visible state remains an unvalidated visual prototype pending idle/sing/miss review and full-song checks.

## v13: scene composition, camera, and note transparency

The latest candidate improves the 4:3 stage composition, draws GF behind Dad and BF, uses chart `FocusCamera` sections for a smooth audio-clocked scene follow, enlarges official note receptors, and preserves alpha during atlas conversion. Health balance and transient judgment labels are display-only; the scoring/gameplay rules are unchanged. Explicit art gaps remain: judgment labels use the SDK font, and the health markers use tiny character frames instead of official HUD icons.

Build outputs (kept out of Git): `build/bopeebo-scene-camera-ui-v13/funkin-ps1-bopeebo-playable.cue` and `.bin`. The BIN is 10,466,400 bytes, SHA-256 `11C9BB94C8A5B1ABD9C97ABFC51BD517CB7B99FDFFBA7BD0092666A700AD4119`. A 9.97-second, 30 fps DuckStation capture is `build/bopeebo-scene-camera-ui-v13/captures/camera-follow-v13.mp4` (video only). v13 compiled and was briefly observed in DuckStation at 320×240 and about 59–60 IPS. The five existing hold-drop regression tests and Python syntax compilation pass. This is not full-song, controller/audio regression, user-accepted, or real-console validation. RAM/VRAM calculations and exact known limitations are in [PS1_PORT.md](../docs/PS1_PORT.md#révision-v13--composition-caméra-et-transparence-des-notes).

## v15: official stage camera prototype

The latest candidate derives actor anchors, camera offsets, stage z-order, note receptors, health icons, and judgment art from the pinned assets/chart. It uses the official focus events with 600 ms easing, a tighter 4:3 crop, and fixed screen-space notes/HUD. `FUNKIN_PS1_SCENE_DEMO_DEFAULT=ON` creates a labeled camera demo with gameplay penalties disabled; `Select` is intended to toggle diagnostics. The image was booted and recorded in DuckStation, including Dad→BF and BF→Dad transitions. This is not user-accepted visual validation or a full-song audio test. The playable and camera-demo BIN/CUE, captures, and reproducible run notes are under ignored `build/bopeebo-playable-v15/`, `build/bopeebo-camera-demo-v15/`, and [PS1_PORT.md](../docs/PS1_PORT.md#révision-v15--composition-officielle-et-caméra-de-scène).

## v18 — portraits au premier plan et vérification de zone sûre

La scène v15 est conservée. Le HUD soumet maintenant les portraits officiels 24×24 après le fond, le remplissage et le cadre de la barre. Leur défaut ne venait pas de l'ordre des commandes GPU : le rendu DuckStation ne montrait pas les icônes du chemin 4bpp. La variante v18 les place en 8bpp et réutilise les palettes de personnage déjà chargées. La santé et le gameplay ne changent pas. Le score/combo est descendu sous les portraits; aucune interpolation floue n'a été ajoutée.

Avec `FUNKIN_PS1_DIAGNOSTICS_DEFAULT=ON`, les repères estimatifs titre 95 % et action 90 % sont visibles dès le démarrage. En mode jouable normal, ils sont masqués; `Select` les affiche avec les compteurs. L'image normale et l'image diagnostic sont dans `build/bopeebo-crt-v18/` et `build/bopeebo-crt-v18-diagnostics/` (ignorés par Git). Deux PNG de capture 320×240 sont dans `build/bopeebo-crt-v18/captures/`. DuckStation exporte ici une image 800×610; les PNG 320×240 sont des réductions nearest-neighbor sans interpolation d'une zone de jeu recadrée à 800×600. DuckStation affichait le mode 320×240 à environ 59–60 IPS. Cela ne valide ni un signal PAL/NTSC matériel, ni un CRT ou une console réelle.

Mesures mises à jour dans [PS1_PORT.md](../docs/PS1_PORT.md#révision-v18--portraits-de-vie-et-lisibilité-crt): ELF 668 650 octets, ring RAM 98 304 octets, VRAM suivie 930 976 octets sur 1 Mio (dont 589 824 octets de textures), 34 304 octets SPU et 8/24 voix. Ce budget est celui du prototype Bopeebo uniquement; piles, heap et allocations SDK ne sont pas toutes instrumentées.

## v20 — cycles d’animation et zone sûre Dad

Le groupe Dad/autoplay est rentré de 6 px : les notes/récepteurs de 16 px commencent à x=16, alignées sur la zone action 90 % (verte). Le guide bleu/gris reste la zone titre 95 % (x=8..311, y=6..233). Timing, lanes, ownership, caméra, audio quatre canaux, tenues, mute et SFX ne changent pas.

BF rejoue son timeline idle officiel de 14 entrées en dédupliquant les images identiques; Dad parcourt six poses du rig idle couvrant son cycle source, chante dans ses quatre directions; GF alterne ses poses de danse gauche/droite avec les enceintes intégrées. Phases, pulsations et changements caméra suivent la position audio et la table tempo. Le chart Bopeebo épinglé n’a pas de changement BPM effectif, donc ce cas n’a pas été observé dans DuckStation. Ces images extraites restent un échantillonnage de rigs, pas tous les intermédiaires du rendu PC.

Deux configurations PSn00bSDK 0.24/GCC MIPS 12.3 ont compilé : normal `FUNKIN_PS1_SCENE_DEMO_DEFAULT=OFF`, et démo caméra ON. BIN jouable 10 459 344 octets. La démo a été capturée dans DuckStation à 320×240 logique/~60 IPS; la vidéo MP4 640×480, 59,82 fps, inclut le son émulateur. Compilation et observation de courte durée ne valent pas validation utilisateur, morceau complet, audio prolongé, CRT/PAL ou console réelle. Budgets v20 et reste des vérifications figurent dans [PS1_PORT.md](../docs/PS1_PORT.md#révision-v20--zone-sûre-dad-et-cycles-danimation-audio-clockés). BIN/CUE et capture finale sont fournis hors Git sous `outputs/FNF-PS1-v20-final/`.

## v21 — première navigation de menu

Le convertisseur préserve et vérifie le rouge des notes droite (360 pixels source rouges opaques, CLUT distincte); les états récepteurs idle restent issus des assets officiels sans recoloration forcée. Le build ajoute le titre officiel logo/GF, le menu principal avec Freeplay comme seule entrée active, `Bopeebo — Normal`, une pause simple et le retour au Freeplay à la fin du morceau. Les assets viennent toujours de la révision épinglée.

Build PSn00bSDK 0.24 / GCC MIPS 12.3 / Ninja réussi; BIN 10 461 696 o, CUE 93 o, sous `outputs/FNF-PS1-v21-menu-preview/`. Le convertisseur confirme 9 pages 8bpp + 2 pages 4bpp et un VRAM suivi de 996 544 o, mais les textures de menu et de gameplay restent chargées ensemble et le ring RAM reste alloué dans les menus. Musique et sons de navigation officiels du menu ne sont pas encore raccordés. DuckStation n’a pas pu être amené à afficher ce binaire après son redémarrage; aucune capture/vidéo v21 ni parcours manette n’est donc affirmé. Voir [PS1_PORT.md](../docs/PS1_PORT.md#révision-v21--correction-rouge-et-première-navigation-menu) pour les budgets par écran, limites et vérifications requises.

## v22 — menu audio et correctif de palette droite

Build séparé sous `outputs/FNF-PS1-v22-menu-audio-arrowfix/` : BIN 23 268 336 octets et CUE 93 octets. Ajoute `FreakyMenu` en VAGi 4 canaux bouclé (stéréo sur 0/1, silences sur 2/3), les sons officiels de navigation et une page VRAM menu relâchée/rechargée entre menus et gameplay. v22 tentait une CLUT indépendante pour la note droite, mais l’utilisateur a confirmé que la note avait disparu; ce correctif ne fonctionnait donc pas.

Le BIN a démarré dans DuckStation 0.1-8675 et l’écran titre est resté affiché plus de 140 s à 320×240 (~59–61 IPS), sans erreur affichée, à travers une boucle. Cela ne valide pas le son à l’écoute ni le menu.

## v23 — diagnostic et correction runtime de la note droite

La note droite utilise maintenant la CLUT partagée avec ses récepteurs gris, avec le rouge officiel réservé dans la palette; l’erreur de quantification du groupe droit est RMSE 11,11 (v22 : 10,79). Le mode QA `FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT=ON` autolance Bopeebo et affiche les quatre directions en note, repos, appui, confirmation et tenue. Le build normal garde ce mode désactivé; Select ouvre la planche diagnostic en jeu.

BIN/CUE et capture DuckStation dans `outputs/FNF-PS1-v23-right-note-fix/`. Compilation réussie; le build a été exécuté dans DuckStation 0.1-8675 x64 / D3D11, 320×240 logique et 60 IPS affichés. La capture réelle montre la note droite rouge, le récepteur droit gris, les états de quatre directions et les tenues; au moment de la capture `CD 0`, `underruns 0`, `PAD ON`. Observation d’environ 14 s d’horloge audio uniquement; boutons, morceau complet, écoute, menus fidèles, game over, résultats, CRT/PAL et console restent à vérifier. Voir [les notes v23](../docs/PS1_PORT.md#révision-v23--correctif-runtime-de-la-flèche-droite).

## v25 — jugements et missnotes

Le build normal garde Select/diagnostics masqués au démarrage. Select les affiche en jeu; l’option QA `FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT=ON` autolance la planche et n’est pas activée dans l’image jouable. Les assets de jugement officiels sont maintenant dessinés après la scène/notes, avec durée liée à l’horloge audio; la réserve passe à 384 primitives. L’apparition des jugements doit encore être confirmée à l’écran sur un run avec commandes reçues.

Une faute BF existante redémarre immédiatement sa timeline visuelle même pendant une réaction précédente. Pour fautes simultanées, l’ordre du chart détermine la dernière lane/pose affichée; chaque miss/drop/ghost miss garde exactement un traitement et son événement SFX existant. Les missnotes utilisent les trois sons officiels aléatoires et les gains du moteur; le bip synthétique reste réservé aux probes. Le pool de quatre voix répartit un budget de volume borné et accepte les occurrences rapprochées.

## v27 — dernière passe de jugement et tenues

La primitive Sick/Good/Bad/Shit est maintenant soumise après le HUD principal dans une passe indépendante. `Select` active les diagnostics en jeu : ils indiquent hits, dernier front de direction, jugement, delta, temps restant et soumission GPU. Tous les diagnostics restent masqués au démarrage. Les corps et capuchons de notes tenues utilisent un flip UV 180°; les flèches/récepteurs ne tournent pas et les règles des tenues sont inchangées.

Build normal : [BIN](../outputs/FNF-PS1-v27-judgement-final-layer/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v27-judgement-final-layer/funkin-ps1-bopeebo-playable.cue). Compilé avec diagnostics, tests QA et planche masqués. Le jeu normal n’a pas encore été observé dans DuckStation après ces corrections; valider les jugements sur hits manette et l’orientation des tenues avant de considérer ce correctif visuel accepté.

Build v25c : cibles jouable et audio secondaire compilées avec PSn00bSDK 0.24/GCC 12.3. BIN/CUE sous `outputs/FNF-PS1-v25c-judgement-visibility/`. DuckStation a affiché Freeplay normal à 320×240; l’injection clavier n’a pas permis de lancer le morceau de façon reproductible. Les popups, fautes rapprochées, sons officiels, unders/underruns et transitions du jeu restent à essayer; aucune exécution complète ni console réelle n’est revendiquée. Voir [PS1_PORT.md](../docs/PS1_PORT.md#v25--jugements-fautes-rapprochées-et-sfx-officiels).

## v26 — validation déterministe des jugements

La cible QA `FUNKIN_PS1_JUDGEMENT_VISUAL_TEST_DEFAULT=ON` simule quatre appuis chart (0/60/110/150 ms) via `game_update()` puis le vrai renderer. Elle affiche les assets officiels Sick/Good/Bad/Shit sans entrée manette ni audio; l’horloge synthétique avance à ¼ vitesse pour exposer la fenêtre réelle de 650 ms musicaux. Ne pas activer ce flag dans l’image jouable. Le build normal v26 garde diagnostics, planche et modes QA masqués. BIN/CUE et capture QA sont livrés dans `outputs/FNF-PS1-v26g-judgement-hitpath-qa/`; le BIN/CUE normal et sa capture de gameplay dans `outputs/FNF-PS1-v26-normal-judgements/`. La QA a été observée dans DuckStation; une capture de jugement par hit manette pendant le flux normal reste à vérifier. Voir [PS1_PORT.md](../docs/PS1_PORT.md#v26--chaîne-de-rendu-des-jugements-et-cible-qa-déterministe).

## v28 — jugement plus compact et tenue orientée

L’utilisateur valide le rendu v27 et confirme les jugements visibles. v28 réduit les popups de 18 % sans changer leur durée ou leur logique, et dessine les terminaisons des tenues en haut, derrière les corps qui les recouvrent légèrement. Le build normal garde diagnostics et QA désactivés. [BIN](../outputs/FNF-PS1-v28-judgement-hold-cap/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v28-judgement-hold-cap/funkin-ps1-bopeebo-playable.cue). Compilation vérifiée; cette nouvelle image n’a pas encore été observée dans DuckStation ou sur console.

## v29 — points affichés près du jugement

Le jeu affiche désormais près du popup le delta de score de l’événement lui-même, avec son signe : points gagnés au hit ou pénalité existante en cas de miss/drop. Le total et les règles de score restent inchangés. Pour une tenue, l’étiquette indique les points attribués à sa tête; l’accumulation durant le maintien continue séparément.

Build normal compilé, diagnostics masqués : [BIN](../outputs/FNF-PS1-v29-judgement-points/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v29-judgement-points/funkin-ps1-bopeebo-playable.cue). Pas encore observé dans DuckStation ou sur console; visibilité et placement du nombre doivent être vérifiés dans le jeu.

## v30 — compteur de combo et score

Clarification : l’affichage demandé près du jugement est le compteur de combo à partir de 10 réussites, pas les points gagnés par note. v30 retire le delta de score de v29, affiche les chiffres combo officiels (trois chiffres minimum) avec la fenêtre musicale d’origine, et montre brièvement `000` en cas de rupture d’un combo affiché. Le gameplay et ses règles restent inchangés.

Le libellé `COMBO` disparaît de la barre de score. Le score total utilise les glyphes VCR bitmap officiels et se place à droite, à hauteur de la barre de vie. Les glyphes extraits et chiffres combo partagent les pages/CLUT popup déjà existantes; le convertisseur confirme une carte texturée de 9 pages 8bpp et 2 pages 4bpp.

Build normal diagnostics masqués : [BIN](../outputs/FNF-PS1-v30-combo-score/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v30-combo-score/funkin-ps1-bopeebo-playable.cue). BIN 23 324 784 octets; SHA-256 `552F20EC65D5D896CA785902D384FDAAB87B498655CEC6272C3B2B5D4C1AD921`; CUE 93 octets. Compilation réussie; l’image v30 reste à observer dans DuckStation et sur console.

## v31 — réserve HUD

v30 soumettait deux primitives par glyphe du score puis les jugements dans le même tableau fixe de 512 primitives. L’interface finale pouvait donc être rejetée si la scène et les notes consommaient le budget; cette saturation est une explication au niveau du code, sans mesure runtime v30 confirmant le compteur atteint pendant l’essai utilisateur.

v31 porte le tableau à 640, plafonne la scène/les notes à 608 et réserve 32 primitives aux couches finales. Le score VCR utilise une primitive par caractère. Select affiche les compteurs de charge/rejet HUD en diagnostic; tout reste masqué par défaut. RAM statique estimée en hausse de 5 120 octets; VRAM et gameplay inchangés.

[BIN v31](../outputs/FNF-PS1-v31-hud-primitive-reserve/funkin-ps1-bopeebo-playable.bin) · [CUE v31](../outputs/FNF-PS1-v31-hud-primitive-reserve/funkin-ps1-bopeebo-playable.cue). BIN 23 324 784 octets; SHA-256 `D0EA4FF0F23041FC7CBAC5D31269D42913A6EC2D41433CF1D9477DD66E42426B`; CUE 93 octets. Build compilé, affichage encore à observer dans DuckStation.

## v32 — score via le bitmap SDK

Les captures v31 montrent toujours le score absent malgré 14 glyphes VCR soumis. v32 remplace le score texturé par `FntPrint/FntFlush` à droite de la barre de vie, en s’appuyant sur le chemin font SDK visible dans les diagnostics. La police est la bitmap PSn00bSDK, car les glyphes VCR du jeu ne se sont pas affichés dans l’essai utilisateur; leur extraction reste dans les ressources converties mais le score normal ne les emploie plus.

La capture diagnostic indique aussi `J 4 LEFT 0` et `DMS 1010`. Le jugement dure 650 ms audio et avait déjà expiré au moment de la capture. Le code garde cette durée; il faut observer un hit dans la fenêtre active pour confirmer le popup sur v32.

[BIN v32](../outputs/FNF-PS1-v32-score-font-fallback/funkin-ps1-bopeebo-playable.bin) · [CUE v32](../outputs/FNF-PS1-v32-score-font-fallback/funkin-ps1-bopeebo-playable.cue). BIN 23 322 432 octets; SHA-256 `6C421D812E3AAF99E3535B7939B88C31A493F6E4D6D00E90ABC55B63457F4C0B`; CUE 93 octets. Compilé, pas encore observé dans DuckStation.

## v33 — placement score et animation des popups

L’utilisateur confirme ensuite par capture que score et jugement v32 apparaissent, mais que le score touche la barre de vie. v33 le place sous celle-ci, en `(208,37)`, avec 96 px de largeur, sans changer les valeurs ni le gameplay.

Les assets officiels des jugements et chiffres combo sont des images fixes; `PopUpStuff.hx` leur applique des tweens. v33 reprend le flottement vertical, la petite entrée en taille et le fondu, pilotés par l’horloge en échantillons audio. Le mouvement est déterministe sur PS1. Le fondu assombrit les pixels jusqu’au noir plutôt qu’utiliser un alpha continu; la popup de jugement conserve sa durée existante de 650 ms.

[BIN v33](../outputs/FNF-PS1-v33-popup-motion-score-layout/funkin-ps1-bopeebo-playable.bin) · [CUE v33](../outputs/FNF-PS1-v33-popup-motion-score-layout/funkin-ps1-bopeebo-playable.cue). BIN 23 324 784 octets; SHA-256 `97A8C06BF8D6DDBC1E46BDB62D55446B819A5103082BFE1A92CE3E993346910E`; CUE 93 octets. Compilation réussie; v33 reste à lancer dans DuckStation.

## v34 — jugement à pleine intensité

Retour utilisateur : score v33 bien placé, popup de jugement invisible. v34 retire son fondu RGB jusqu’au noir et conserve mouvement, entrée en taille et fenêtre 650 ms, afin que l’illustration officielle reste à modulation normale pendant toute son apparition. Les règles ne changent pas. Le combo conserve son animation séparée.

[BIN v34](../outputs/FNF-PS1-v34-judgement-visible/funkin-ps1-bopeebo-playable.bin) · [CUE v34](../outputs/FNF-PS1-v34-judgement-visible/funkin-ps1-bopeebo-playable.cue). BIN 23 324 784 octets; SHA-256 `0628E2D4445D262FDB4FEA146FE51EDFFCE0F3A85C68009128E13CC3FBA5864A`; CUE 93 octets. Compilation réussie; la visibilité du popup après un hit réel reste à vérifier dans DuckStation.

## v35 — durée originale du popup

Correction du diagnostic : `DMS` indique l’écart de timing du hit, tandis que `LEFT 0` signifie que le popup avait expiré à l’image capturée. Le jugement suit maintenant la durée du moteur original (un beat + 200 ms), soit 800 ms à 100 BPM pour Bopeebo. L’image garde sa modulation entière et son mouvement; seule sa fenêtre d’affichage change.

[BIN v35](../outputs/FNF-PS1-v35-original-popup-window/funkin-ps1-bopeebo-playable.bin) · [CUE v35](../outputs/FNF-PS1-v35-original-popup-window/funkin-ps1-bopeebo-playable.cue). BIN 23 324 784 octets; SHA-256 `CDE7F9412F5A5DD4895FA6C293A165B21227FB094D8AF71ACDDA5E67DB988E2E`; CUE 93 octets. Compilation réussie; test DuckStation du popup normal reste à faire.

## v36 — couche popup au-dessus des diagnostics

La capture v35 montre le panneau de diagnostic opaque au-dessus du centre du gameplay. Le flush de sa police intervenait après le dessin des jugements, les recouvrant quand Select était actif. v36 dessine Sick/Good/Bad/Shit et le combo après ce flush. Aucune règle de jugement ni donnée de gameplay ne change; la fenêtre reste celle du v35.

Compilation PSn00bSDK 0.24 / GCC MIPS 12.3 réussie : BIN 23 324 784 octets, CUE 93 octets, SHA-256 BIN `DA81B623983AFDC279DD31B0685DBCD4F18B9A6CB761C899BAD0FD2D64AD6B96` dans `outputs/FNF-PS1-v36-popup-over-diagnostics/`. Lancer un hit avec Select activé puis masqué dans DuckStation; l’ancienne capture identifie le recouvrement mais ne valide pas le nouveau rendu. Pas de test console réelle.

## v37 — jugement stable

Les captures utilisateur v36 ne montrent toujours pas le popup; déplacer le calque seul n’a pas suffi. v37 restaure le rendu fixe v32, observé auparavant à l’écran, en supprimant le mouvement et le zoom du jugement. La fenêtre d’affichage audio reste à un beat + 200 ms; le combo conserve son animation.

[BIN v37](../outputs/FNF-PS1-v37-stable-judgement-display/funkin-ps1-bopeebo-playable.bin) · [CUE v37](../outputs/FNF-PS1-v37-stable-judgement-display/funkin-ps1-bopeebo-playable.cue). BIN 23 324 784 octets; SHA-256 `788F1E29875B762F38F76ADF705627E5FD7920FBFF72E0A802BB78798D45D313`; CUE 93 octets. Démarré dans DuckStation jusqu’à l’écran titre (60 IPS affichés); essai du popup en gameplay impossible faute d’entrée Start disponible dans cette session. Pas de test console réelle.

## v38 — fenêtre de jugement plus facile à observer

La capture v37 ne montre pas de popup et affiche `J DRAW 0` à l’image capturée. v38 garde l’asset et le placement fixes v32, avec une fenêtre d’affichage de deux beats + 200 ms (1,4 s à 100 BPM). `LEFT` diagnostique maintenant des millisecondes. C’est une durée d’affichage uniquement; les règles du jeu restent inchangées.

[BIN v38](../outputs/FNF-PS1-v38-longer-judgement-window/funkin-ps1-bopeebo-playable.bin) · [CUE v38](../outputs/FNF-PS1-v38-longer-judgement-window/funkin-ps1-bopeebo-playable.cue). BIN 23 324 784 octets; SHA-256 `1515C1287F52FC0A36A06750745BF27261FC122445265316DFBB2BAB60A1030F`; compilation réussie, exécution gameplay à confirmer.

## v39 — trace du rendu de jugement

Le diagnostic `J DRAW` de v38 était affiché avant le rendu de la frame courante. v39 le remplace par `J LAST tentative/soumise frame`, mémorisé après l’appel GPU; Select affiche les diagnostics, masqués au démarrage. QA et jeu utilisent les mêmes textures/CLUT et le popup est chargé avant le morceau. Cette trace indique une soumission de primitive, pas sa visibilité à l’écran. La fenêtre v38 est conservée; aucun correctif ni validation visuelle n’est revendiqué avant un hit manuel observé dans le jeu normal.

Build v39 : [BIN](../outputs/FNF-PS1-v39-judgement-render-trace/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v39-judgement-render-trace/funkin-ps1-bopeebo-playable.cue). PSn00bSDK 0.24 / GCC MIPS 12.3 a compilé l’image : BIN 23 324 784 octets, CUE 93 octets, SHA-256 `F4F97A9301F656E7DD1C44EE0C98348B16DF22C932FD965A3DA2CB3A3B388CB6`. Le disque n’a pas été exécuté en gameplay dans DuckStation; la fenêtre active et la soumission réelle au hit manuel restent à relever. Aucun test console.

Select affiche les diagnostics. Pendant un hit, `LEFT` doit être positif si l’état de popup est encore actif; `J LAST a/s Fnn` donne la tentative/soumission mémorisée après le rendu précédent (1/1 signifie primitive remise au GPU, pas pixels confirmés). Capturer ensuite le même hit diagnostics masqués. La durée v38 (1,4 s à 100 BPM) et les règles de jeu sont conservées.
# Menus et Game Over — build v55

`FNF-PS1-v55-menu-gameover` fournit un parcours titre → menu principal → Freeplay → Bopeebo Normal et un écran Game Over avec BF Death officiel, sons de perte, boucle Game Over, Croix pour réessayer et Rond pour revenir. Les diagnostics sont masqués au démarrage. Le parcours n’a pas été exécuté dans DuckStation pour cette version : charge le CUE manuellement, puis confirme ici que l’émulateur l’a ouvert. On fera ensuite l’essai ensemble avec le clavier visuel. Résultats après réussite non inclus.

Assets et dépendances restent sous le checkout local `assets/`; les conversions générées sont dans le répertoire build ignoré. `generate_ps1_menu_audio.py` convertit FreakyMenu, gameOver/gameOverEnd et les sons officiels navigation/faute/perte. Build local : cible CMake `ps1-bopeebo-playable-disc`, avec les variables PSn00bSDK, chart, VAGi Bopeebo et ffmpeg définies comme dans `docs/PS1_PORT.md`.

## Essai menu v62

`outputs/FNF-PS1-v62-options-contour-noise/funkin-ps1-bopeebo-playable.cue` est le nouveau build à essayer. Il conserve la taille et la disposition validées en v60/v61, élargit légèrement le contour noir de sélection et lui donne une variation déterministe plus irrégulière. BIN/CUE compilés; v62 attend l’essai utilisateur dans DuckStation. Diagnostics masqués au démarrage. Détails : `docs/PS1_PORT.md`, section v62.
## Build v63 — Week 1 et Tutorial

Le Freeplay propose Tutorial, Bopeebo, Fresh et Dadbattle. Haut/Bas sélectionne le morceau; Gauche/Droite choisit Easy, Normal ou Hard; Croix joue et Rond revient. Bopeebo Normal reste le défaut. Erect/Nightmare sont des placeholders sans entrée jouable.

Les charts officiels sont convertis à 43 008 Hz; Tutorial utilise GF comme adversaire, les morceaux Week 1 Dad. Audio quatre canaux : instrumental stéréo, adversaire mono, BF mono, tous alignés à la même origine. Les ressources officielles et fichiers convertis restent hors Git.

Le BIN/CUE v63 est compilé mais attend l’essai DuckStation de l’utilisateur : [BIN](../outputs/FNF-PS1-v63-week1-songs/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v63-week1-songs/funkin-ps1-bopeebo-playable.cue). Diagnostics masqués au démarrage; vérifier navigation Freeplay, quatre morceaux, trois difficultés, transitions audio et retour menu. Pas de validation console réelle.

Assets utilisés : sous-module épinglé `assets` à `724eba9de9e76761d9cefd52169926bc51c760a5`.

## v64 — Tutorial en tête et Freeplay 4:3

L’utilisateur estime les quatre morceaux corrects et demande Tutorial en premier. Le catalogue est maintenant ordonné Tutorial, Bopeebo, Fresh, Dadbattle; Normal reste la difficulté par défaut. Le Freeplay utilise le rig officiel animé BF DJ à gauche, le fond Week 1 à droite, la liste de quatre titres, la capsule de sélection et la pochette Volume 1, adaptés en 4:3. Erect/Nightmare restent indisponibles. Contrôles : Haut/Bas chanson, Gauche/Droite difficulté, Croix lancer, Rond retour.

Le nouveau Freeplay est compilé mais doit encore être essayé dans DuckStation; vérifier l’ordre, les quatre lignes sélectionnables, les trois difficultés et les transitions avant de le déclarer validé. La compilation mesure 1 496 762 octets de sections résidentes; le FIFO audio reste à 96 Kio, environ 362 Kio restent avant stack/allocations ponctuelles dans l’estimation de RAM disponible. VRAM inchangée : 9 pages 8bpp et 2 pages 4bpp (655 360 octets). [BIN v64](../outputs/FNF-PS1-v64-tutorial-first-freeplay/funkin-ps1-bopeebo-playable.bin) · [CUE v64](../outputs/FNF-PS1-v64-tutorial-first-freeplay/funkin-ps1-bopeebo-playable.cue). Les détails et limites sont dans `docs/PS1_PORT.md`, section v64.

## v65 — crash Freeplay

Après le crash de v64 à l’ouverture de Freeplay, les quatre régions texte par chanson ont été regroupées dans une seule région, ramenant le nombre total de `FntOpen` au niveau précédent. La cause exacte reste à confirmer dans DuckStation. Essai attendu : ouvrir Freeplay, déplacer la sélection et confirmer que le jeu reste actif. Voir `docs/PS1_PORT.md`, section v65.

## v66 — Freeplay jouable, catalogue étendu

Le Freeplay utilise la composition 4:3 corrigée : inscriptions officielles en nuances distinctes, fond officiel recadré sur Dad, capsules et portraits pixel officiels agrandis et alignés. Tutorial, Bopeebo, Fresh et Dadbattle restent lançables; le reste du catalogue se parcourt avec l’état `LOCKED` et ne démarre rien. Flèches haut/bas pour parcourir, gauche/droite pour changer Easy/Normal/Hard, Croix pour lancer les quatre morceaux disponibles, Rond pour revenir. Les diagnostics restent masqués par défaut.

Le BIN/CUE v66 est compilé et prêt à charger dans DuckStation : [BIN](../outputs/FNF-PS1-freeplay-v66/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-freeplay-v66/funkin-ps1-bopeebo-playable.cue). L’essai manuel est en attente; le parcours menu/Freeplay et les transitions audio ne sont pas déclarés validés. BF DJ est affiché dans une pose officielle fixe; son animation reste différée. Budgets, hash et résultats de compilation sont consignés dans `docs/PS1_PORT.md`, section v66.

## v67 — intégration Freeplay alignée sur la maquette

v67 remplace les titres trop réduits par des glyphes dérivés de la police VCR du mockup, utilise les images officielles Easy/Normal/Hard et leurs flèches, et corrige le panoramique de l’illustration afin de garder Dad visible sans GF ni agrandissement par crop. Les titres lançables ont leur largeur de cavité complète; les entrées verrouillées conservent un compartiment séparé. Une petite bande de difficulté est mise à jour dans la page menu existante; VRAM et navigation restent inchangées.

[BIN v67](../outputs/FNF-PS1-v67-freeplay-reference-match/funkin-ps1-bopeebo-playable.bin) · [CUE v67](../outputs/FNF-PS1-v67-freeplay-reference-match/funkin-ps1-bopeebo-playable.cue). Build PSn00bSDK réussi, diagnostics masqués au démarrage. v67 n’a pas été exécuté dans DuckStation : charge le CUE et confirme ici. La capture framebuffer native 320×240 et la comparaison visuelle restent à faire après ton chargement; voir `docs/PS1_PORT.md`, section v67 pour les coordonnées, les budgets et les résultats détaillés.

## v68 — test sans transfert VRAM partiel à l’ouverture

Pour isoler le gel signalé en entrant dans Freeplay sous v67, v68 remplace le chargement partiel du sélecteur de difficulté par Easy/Normal/Hard composés dans des pages complètes, chargées par le chemin déjà utilisé pour les autres écrans menu. Compilation réussie; le gel reste à retester par l’utilisateur.

[BIN v68](../outputs/FNF-PS1-v68-freeplay-no-partial-vram-load/funkin-ps1-bopeebo-playable.bin) · [CUE v68](../outputs/FNF-PS1-v68-freeplay-no-partial-vram-load/funkin-ps1-bopeebo-playable.cue). L’utilisateur confirme ensuite que Freeplay s’ouvre et fonctionne dans DuckStation. Les deux pages complètes supplémentaires coûtent environ 128 Kio de mémoire statique; la carte VRAM ne change pas. Les diagnostics sont masqués au démarrage. Résultats et budget complet dans `docs/PS1_PORT.md`, section v68.

## v69 — titres Freeplay plus lisibles

L’utilisateur confirme que v68 ouvre Freeplay, puis valide la lisibilité des titres et la marge haute en v69. v69 agrandit et éclaircit les titres des chansons, et descend le bandeau supérieur pour préserver une marge au bord de l’écran. La disposition générale, les capsules et la navigation restent identiques. Build v69 : [BIN](../outputs/FNF-PS1-v69-freeplay-title-legibility/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v69-freeplay-title-legibility/funkin-ps1-bopeebo-playable.cue).

## v70 — animation officielle BF DJ dans Freeplay

Le rig Animate officiel joue son intro à l’entrée de Freeplay, puis boucle son idle à 12 images/s. L’utilisateur a rapporté un gel immédiat à l’ouverture de Freeplay; la cause n’est pas confirmée. Le chemin de mise à jour partielle VRAM à chaque pose est retiré en v71. Détails : `docs/PS1_PORT.md`, sections v70/v71.

## v71 — correctif candidat du gel Freeplay

Les poses BF sont packées dans trois pages 8bpp temporaires chargées par transferts complets synchronisés à l’entrée de Freeplay. Le jeu restaure les pages du gameplay avant de lancer un morceau; les changements de pose n’envoient plus d’écritures VRAM. Carte VRAM toujours 655 360 octets de textures; atlas résident 196 608 octets; ELF `size` total 1 710 878 octets. L’utilisateur confirme que v71 s’ouvre et fonctionne, mais signale que le DJ est trop petit. Build : [BIN](../outputs/FNF-PS1-v71-freeplay-dj-atlas/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v71-freeplay-dj-atlas/funkin-ps1-bopeebo-playable.cue). Les animations confirm/fist-pump restent différées.

## v72 — BF DJ agrandi

Le rig officiel conserve ses pixels transparents et son ancrage; les poses sont recadrées à leur emprise commune 31×90 puis rendues à 1,75× (environ 54×157) dans la zone basse gauche. Le fond et les capsules restent en couches distinctes. Un seul atlas temporaire 8bpp (65 536 octets) est chargé en Freeplay et restauré avant le jeu. La VRAM reste à 655 360 octets de textures; ELF `size` total 1 579 802 octets. Build compilé, exécution DuckStation à confirmer : [BIN](../outputs/FNF-PS1-v72-freeplay-dj-size/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v72-freeplay-dj-size/funkin-ps1-bopeebo-playable.cue). Détails et budget dans `docs/PS1_PORT.md`, section v72.

## Build v73 — première adaptation Week 2

Freeplay ajoute Spookeez, South et Monster après les quatre entrées déjà jouables. Easy, Normal et Hard sont disponibles pour ces sept chansons; les autres titres restent verrouillés. Les trois charts, stems et le décor/habillage Week 2 viennent des assets épinglés. Les voix courtes sont complétées de silence en fin de flux pour partager la même origine et la même durée de lecture.

Le jeu reprend l’arrière-plan Spooky Mansion, les poses de chant de Spooky Kids/Monster, leurs icônes et le cadrage de scène. Le fond reste statique et seules des poses échantillonnées des rigs sont présentes; éclair, secousse et séquences d’animation complètes restent différés. Le DJ Freeplay reste inchangé, conformément au retour utilisateur.

Compilation PSn00bSDK 0.24 réussie. BIN/CUE à charger manuellement dans DuckStation : [BIN v73](../outputs/FNF-PS1-v73-week2-adaptation/funkin-ps1-week2-playable.bin) · [CUE v73](../outputs/FNF-PS1-v73-week2-adaptation/funkin-ps1-week2-playable.cue). Le build n’a pas encore été observé en émulateur; demander confirmation avant de poursuivre les essais interactifs. Budget relevé : 1 817 142 octets de sections résidentes, 3 pages temporaires Week 2 (196 608 octets), VRAM inchangée à 655 360 octets de textures. Voir [PS1_PORT.md](../docs/PS1_PORT.md#v73--première-adaptation-jouable-de-la-week-2).

## v74 — charts et scène Week 2 chargés depuis le CD

Les 21 combinaisons chanson/difficulté sont des fichiers chart autonomes sur le disque. Le programme ne conserve en RAM que le chart choisi : il le lit au lancement après l’arrêt de la musique de menu, le garde pendant gameplay/retry, puis le libère au retour au Freeplay. La scène Week 2 (`W2SCENE.BIN`, 197 120 octets) est aussi séparée de l’exécutable; ses trois pages VRAM sont lues une par une avec un tampon temporaire de 64 Kio. La musique du morceau ne démarre qu’après le chargement du chart et de la scène.

Les sections résidentes ELF passent de 1 817 142 octets en v73 à 1 559 922 en v74 (257 220 octets économisés). Le plafond de calcul projet est 1 966 080 octets; après les sections résidentes et le FIFO audio de 96 Kio, il reste 307 854 octets avant staging, chart, pile et autres allocations. Le pic RAM n’a pas été mesuré. Les pages Week 1 et données des menus restent intégrées à l’exécutable.

Build compilé, essai DuckStation attendu : [BIN v74](../outputs/FNF-PS1-v74-independent-song-loading/funkin-ps1-bopeebo-playable.bin) · [CUE v74](../outputs/FNF-PS1-v74-independent-song-loading/funkin-ps1-bopeebo-playable.cue). Vérifier les transitions Week 1/Week 2, audio, retry et retour au Freeplay.

## v75 — pages Week 1 à la demande, Week 2 enrichie

Les pages de texture du gameplay Week 1 sont maintenant dans `W1SCENE.BIN` (640 Kio), lues depuis le CD par pages de 64 Kio et restaurées quand les pages VRAM sont réutilisées. Les ressources d’interface et BF DJ restent séparées. Week 2 a été régénérée avec un décor de 362×256, Spooky Kids à 72×84 avec plusieurs poses d’idle/chant et deux poses officielles de danse GF. Son paquet fait 328 192 octets : cinq pages 8bpp et une CLUT. Les pages Week 2 remplacent temporairement 0, 1, 2, 3 et 8; le retour restaure la scène Week 1. VRAM totale inchangée à 655 360 octets de textures.

ELF : 905 398 octets de sections résidentes; après le FIFO audio de 96 Kio, la marge arithmétique est 962 378 octets sous l’enveloppe de calcul projet, avant staging/runtime. Le staging de scène est 64 Kio. Ces valeurs sont des budgets calculés, pas des pics mesurés. BIN/CUE compilés : [BIN v75](../outputs/FNF-PS1-v75-week1-on-demand-week2-enhanced/funkin-ps1-bopeebo-playable.bin) · [CUE v75](../outputs/FNF-PS1-v75-week1-on-demand-week2-enhanced/funkin-ps1-bopeebo-playable.cue). L’utilisateur confirme v75 validée dans DuckStation. Aucun test console réelle.

## v76 — Week 2, première Week 3 et écran de chargement

L’utilisateur a validé v75 dans DuckStation. v76 reprend le zoom officiel propre à chaque stage pour corriger le cadrage Week 2 et commence la Week 3 (Pico, Philly Nice, Blammed; Easy/Normal/Hard). Philly utilise ses couches de scène officielles fixes; le train mobile est différé. Les scènes de semaine sont chargées depuis le CD avec écran de transition; chaque morceau conserve ses ressources isolées. BIN/CUE compilés, essai utilisateur en attente : [BIN](../outputs/FNF-PS1-v76-week2-week3-loading/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v76-week2-week3-loading/funkin-ps1-bopeebo-playable.cue).

## v77 — correction du démarrage v76

L’utilisateur a signalé que v76 restait sur l’écran Sony PlayStation. L’audit ISO a trouvé `W1SCENE.BIN` au LBA 53 257, après les gros fichiers audio, alors que le programme la lit avant son premier écran. v77 place les trois scènes au début du disque, avec W1 au LBA 446, et affiche « LOADING GAME » avant les lectures. BIN/CUE compilés, à essayer dans DuckStation : [BIN](../outputs/FNF-PS1-v77-startup-loading-fix/funkin-ps1-bopeebo-playable.bin) · [CUE](../outputs/FNF-PS1-v77-startup-loading-fix/funkin-ps1-bopeebo-playable.cue). La cause et la correction restent à confirmer par l’essai utilisateur.

### v78 — repère de démarrage précoce

v77 reste bloquée sur le logo Sony selon le dernier essai utilisateur. v78 dessine un aplat GPU après ResetGraph, avant les polices et les initialisations CD/SPU, sans capture VRAM. BIN/CUE compilés : outputs/FNF-PS1-v78-early-boot-marker/. Résultat DuckStation en attente; repère bleu-noir = entrée dans l'initialisation vidéo, écran LOADING GAME = démarrage franchi. Aucun essai console réelle.

### v79 — sonde minimale PS-X

Image séparée avec `SYSTEM.CNF` + `FUNKIN.EXE` seulement. La sonde affiche un aplat bleu par une primitive GPU et reste dessus, sans polices, CD/SPU, manette, assets ou gameplay. Elle utilise le même PSn00bSDK et la même cible CMake de disque que le jeu. [BIN](../outputs/FNF-PS1-v79-minimal-boot-probe/funkin-ps1-boot-probe.bin) · [CUE](../outputs/FNF-PS1-v79-minimal-boot-probe/funkin-ps1-boot-probe.cue). Essai utilisateur requis avant toute réintroduction d’initialisations.

### v80 — repères persistants de démarrage

À partir de la sonde v79, cette image ajoute des aplats de couleur avant/après l’initialisation vidéo, polices, SPU, CD (CdInit uniquement) et manette. Elle utilise une BSS de 39 640 octets, proche des 39 152 octets de l’exécutable v78, pour comparer l’initialisation CRT. La couleur atteinte reste à l’écran si une routine suivante se bloque. Aucun asset ni lecture CD/scène. [BIN](../outputs/FNF-PS1-v80-startup-stage-checkpoints/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v80-startup-stage-checkpoints/funkin-ps1-startup-stage-probe.cue). Tableau des couleurs et détails dans `docs/PS1_PORT.md`, section v80.

### v81 — checkpoint CdlPause

Suite à la capture v80 (repère vert final), v81 ajoute uniquement `CdControlB(CdlPause)`. Écran bleu marine = avant la commande, jaune-orangé = succès, rose-rouge = retour d’erreur. Aucun fichier n’est lu. [BIN](../outputs/FNF-PS1-v81-cd-pause-checkpoint/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v81-cd-pause-checkpoint/funkin-ps1-startup-stage-probe.cue). Essai utilisateur requis avant d’ajouter une lecture CD.

### v82 — recherche du package Week 1

Suite au succès de `CdlPause` en v81, v82 teste une allocation de 64 Kio puis `CdSearchFile("\\W1SCENE.BIN")` et sa taille. Le disque inclut W1SCENE pour la recherche; aucun secteur n’est lu ou chargé en VRAM. Orange = avant malloc, cyan = allocation réussie, bleu marine = avant recherche, rose = introuvable, jaune = taille inattendue, vert = recherche valide, blanc = tampon libéré. [BIN](../outputs/FNF-PS1-v82-allocation-file-search/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v82-allocation-file-search/funkin-ps1-startup-stage-probe.cue).

### v83 — `CdSetloc`

L’utilisateur confirme le blanc v82 : allocation, recherche du fichier et validation de taille passent. v83 ajoute la conversion de position et `CdControl(CdlSetloc)` avec repères persistants, sans `CdRead` ni transfert de secteur. L’utilisateur confirme ensuite le blanc v83, donc la commande a réussi. [BIN](../outputs/FNF-PS1-v83-cd-setloc-checkpoint/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v83-cd-setloc-checkpoint/funkin-ps1-startup-stage-probe.cue).

### v84 — lecture d’un secteur, sans chargement VRAM

La sonde tente un seul secteur de 2048 octets dans le tampon RAM, appelle `CdRead` puis interroge `CdReadSync(1)` avec un délai de 300 images. Elle vérifie le CRC-32 du contenu (attendu `0x569EEEF7`), n’installe aucun callback et n’envoie rien à la VRAM. L’utilisateur confirme le blanc : le secteur est lu et le CRC correspond. [BIN](../outputs/FNF-PS1-v84-cd-read-first-sector/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v84-cd-read-first-sector/funkin-ps1-startup-stage-probe.cue).

### v85 — callback de lecture

Cette sonde ajoute un callback au même test d’un secteur et attend un événement unique `CdlDataReady` (valeur enum 1), un payload présent et le CRC attendu, avec polling `CdReadSync(1)` borné à 300 images. Le commentaire de l’en-tête `CdReadCallback` parle de `CdlComplete`/`CdlDiskError`; cette sonde isole l’événement runtime. Aucun transfert VRAM. L’utilisateur a observé le bleu : événement reçu, payload nul; le CRC n’a donc pas été contrôlé par v85. [BIN](../outputs/FNF-PS1-v85-cd-read-callback/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v85-cd-read-callback/funkin-ps1-startup-stage-probe.cue).

### v86 — validation du secteur malgré un payload callback nul

v86 garde le callback `CdlDataReady` et vérifie le CRC après la fin de lecture même si le pointeur payload du callback est nul. L’utilisateur confirme le vert : callback/CRC valides avec payload nul. [BIN](../outputs/FNF-PS1-v86-cd-read-null-payload-check/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v86-cd-read-null-payload-check/funkin-ps1-startup-stage-probe.cue).

### v87 — lecture d’une page de scène complète

La lecture passe à 32 secteurs (65 536 octets), taille d’une page du chargeur. Callback `CdlDataReady` unique, polling `CdReadSync(1)` borné et CRC-32 `0xA3BEABD8` vérifiés; aucune écriture VRAM. L’utilisateur confirme le vert : la page et son CRC sont valides malgré le payload callback nul. [BIN](../outputs/FNF-PS1-v87-cd-read-one-scene-page/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v87-cd-read-one-scene-page/funkin-ps1-startup-stage-probe.cue).

### v88 — lecture de la scène complète

Cette sonde lit les 320 secteurs `W1SCENE.BIN` en 11 blocs (9×32 secteurs 8bpp, 2×16 secteurs 4bpp), avec le même tampon réutilisé de 64 Kio. Elle vérifie callbacks et CRC-32 global `0xF32FB433`, sans `LoadImage`. L’utilisateur confirme le vert : lecture et CRC complets valides avec payloads callback nuls. [BIN](../outputs/FNF-PS1-v88-read-full-week1-scene/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v88-read-full-week1-scene/funkin-ps1-startup-stage-probe.cue).

### v89 — première page de scène vers VRAM

Après lecture de 32 secteurs et vérification du CRC de la première page, la sonde transfère cette page 8bpp et sa palette officielle en VRAM, puis dessine un quad texturé couvrant l’écran avec synchronisations GPU autour des transferts. Un carré vert en haut à gauche suit le quad. Les écrans de couleur persistants marquent les étapes. Cette version ne démarre pas le jeu et ne charge pas les autres pages. Build réussi; essai DuckStation requis. [BIN](../outputs/FNF-PS1-v89-first-scene-vram-upload/funkin-ps1-startup-stage-probe.bin) · [CUE](../outputs/FNF-PS1-v89-first-scene-vram-upload/funkin-ps1-startup-stage-probe.cue).

## Journal de développement

La chronologie des jalons, diagnostics et validations utilisateur est tenue dans [docs/PS1_DEVLOG.md](../docs/PS1_DEVLOG.md). Les mesures et détails techniques des images restent dans [docs/PS1_PORT.md](../docs/PS1_PORT.md).

