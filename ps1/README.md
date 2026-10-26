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

Build v25c : cibles jouable et audio secondaire compilées avec PSn00bSDK 0.24/GCC 12.3. BIN/CUE sous `outputs/FNF-PS1-v25c-judgement-visibility/`. DuckStation a affiché Freeplay normal à 320×240; l’injection clavier n’a pas permis de lancer le morceau de façon reproductible. Les popups, fautes rapprochées, sons officiels, unders/underruns et transitions du jeu restent à essayer; aucune exécution complète ni console réelle n’est revendiquée. Voir [PS1_PORT.md](../docs/PS1_PORT.md#v25--jugements-fautes-rapprochées-et-sfx-officiels).

## v26 — validation déterministe des jugements

La cible QA `FUNKIN_PS1_JUDGEMENT_VISUAL_TEST_DEFAULT=ON` simule quatre appuis chart (0/60/110/150 ms) via `game_update()` puis le vrai renderer. Elle affiche les assets officiels Sick/Good/Bad/Shit sans entrée manette ni audio; l’horloge synthétique avance à ¼ vitesse pour exposer la fenêtre réelle de 650 ms musicaux. Ne pas activer ce flag dans l’image jouable. Le build normal v26 garde diagnostics, planche et modes QA masqués. BIN/CUE et capture QA sont livrés dans `outputs/FNF-PS1-v26g-judgement-hitpath-qa/`; le BIN/CUE normal et sa capture de gameplay dans `outputs/FNF-PS1-v26-normal-judgements/`. La QA a été observée dans DuckStation; une capture de jugement par hit manette pendant le flux normal reste à vérifier. Voir [PS1_PORT.md](../docs/PS1_PORT.md#v26--chaîne-de-rendu-des-jugements-et-cible-qa-déterministe).

