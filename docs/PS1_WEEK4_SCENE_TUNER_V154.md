# Week 4 scene tuner v154

This is a temporary inspection build for adjusting the existing Week 4 layers
in memory. It is not the normal play build and it does not save changes into
the game.

## Controls

Open or close the compact panel with **Select**. While it is open:

- Up/down selects Stage, Camera, Far Limo, GF, Front Limo, Mom, or BF.
- Left/right moves the selected item on X; L1/R1 moves it on Y.
- Cross/Circle changes its scale, bounded from 50% to 200%.
- Hold R2 for faster 10-unit movement / 12.5% scale steps; holding a control
  repeats adjustments every five game frames after the first press.
- Square resets the selected layer's temporary transform.
- Start pauses/resumes the music stream and sample-driven scene while the
  tuner is open, so framing can be adjusted without the song advancing.
- Triangle switches between the editor controls and a full transform summary.
  Capture that summary to preserve the values from the emulator session.

Camera X/Y and zoom are applied after the chart-driven smooth focus transition,
so all scene layers and parallax use the changed projection. The Mom and BF
focus targets also follow their edited world anchors. This prevents character
placement tweaks from leaving the camera aimed at the old coordinates.

The scene demo follows the song timeline and animates the scene, but skips
judgments, score, health changes, misses, and game-over logic so the D-pad can
be used for composition work. The audio/chart data and scene assets are reused.
The panel is hidden at startup; Select is its only toggle. No arrow sheet or
general diagnostics overlay is enabled.

The initial anchors, camera focus data, and parallax factors come from the
pinned Week 4 scene data and the current renderer. The tuner does not read
DuckStation memory remotely: its summary page reports the live offsets and
scales on screen. A screenshot of that page is the handoff for copying selected
values back into the scene constants after review.

The exposed layers are those rendered by the current v153 Week 4 code. The
standalone speaker artwork requested in the original scene composition is not
yet drawn as its own layer; this tuner cannot place an asset that is absent
from the renderer.

## Build and evidence

- Source base: local `ps1-port` snapshot at commit
  `7057882fa4c481fb878de4cc27d3a827179f7ddd`, plus the pre-existing local
  modifications present in that checkout and the v154 tuner changes.
- Build type: Debug, PSn00bSDK 0.24, GCC MIPS 12.3.0.
- Scene-demo and Week 4 tuner are enabled only in this dedicated build.
- The v153 BF pose header and Week 1 pose sidecar are reused byte-for-byte;
  no audio, chart, or general graphics conversion is part of the final dry-run.
- ISO boot directory was statically reordered so `SYSTEM.CNF;1` is entry 1 and
  `FUNKIN.EXE;1` is entry 2. This confirms structure, not a DuckStation run.
- BIN SHA-256:
  `F9415CD2688B5A6264D2FC28FCB26C966BC3A64BBF2C5F0D15BFAF7A9F638BCE`
- CUE SHA-256:
  `205213DDA1B5432DC6C9F6C250B2F47BBAF676BCA81828A5673D0641BD8D7260`

Compilation and static ISO checks passed. Runtime behavior, input mapping,
layer transformations, and visual usefulness remain unobserved until the user
loads the CUE in DuckStation.

## v154b delivery

The first v154 delivery remains preserved. A second, separately named image
was rebuilt from the same converted resources after confirming the tuner also
applies to BF's additional singing-frame path. The target-specific dry-run
contained only the gameplay source compile, executable link, and CD-image
generation; it did not schedule asset conversion. The root directory was
checked again after the ISO boot-record ordering step: `SYSTEM.CNF;1` is entry
1 and `FUNKIN.EXE;1` is entry 2.

- BIN SHA-256: `3FE2CFF4470E7CBE81002E83CE8FABE6BEA66CE65CC3792F99FE54931725A46C`
- CUE SHA-256: `27DE99DC119591D7B661CAA7B8BF9940CBCCDC1950DE87C72955EA07D9E7FB0A`
- Source/configuration archive: `C:/Users/Manau47/Documents/Codex/week4-composition-tuner-v154/source-v154b/`

This is still an unobserved DuckStation test build. No claim is made that the
controls or transforms have been verified at runtime.

## v154c: menu-freeze fix

The user reported that v154b froze on arrival at the main menu. Static review
found the tuner added a ninth `FntOpen` stream. In the linked PSn00bSDK 0.24
`libpsxgpu` object, `_stream` is `0xe0` bytes and `FntOpen` advances by 28-byte
entries without a capacity check: eight streams fit, but the ninth writes past
the table. This is a concrete memory-corruption defect consistent with the
reported freeze. The tuner now reuses the already-open error font for its
temporary panel, keeping the build at eight `FntOpen` calls. This diagnosis is
static; the fix still needs the user's DuckStation run.

The target-only dry-run scheduled three operations: compile `spu_probe.c`,
link the executable, and generate the CD image. No resource conversion was
scheduled. The separate v154b BIN/CUE was retained.

- BIN SHA-256: `D645900B77CC5C2BB9BA29AD8F773B22598F7A0A57E5909A1590DEED495887F3`
- CUE SHA-256: `4A858CE18E6A082A1C1D87979E5EEDF0C00C540D1F28805F611997C780088959`
- Source/configuration archive: `C:/Users/Manau47/Documents/Codex/week4-composition-tuner-v154/source-v154c/`

## v154d: camera-aware faster tuning

After the first successful user run, feedback was that seven separate scene
elements could not be adjusted quickly enough during a song, and character
edits did not move their camera focus targets. v154d adds a Camera layer whose
offset and zoom are applied to the projected scene after chart focus easing;
Mom/BF focus targets now include their edited world offsets. Holding a D-pad,
shoulder, Cross, or Circle control repeats adjustments every five game frames.
Holding R2 selects larger 10-unit position and 12.5% scale steps. These edits
remain temporary and no gameplay/audio rules were changed.

The target-only dry-run and build contained only source compile, link, and ISO
generation; the existing scene, audio, and chart resources were reused. The
ISO root order check passed. Runtime camera response and editing speed remain
for the user's next DuckStation run.

- BIN SHA-256: `F966B240FEC5F2E5A88C93D84CB41D262403A8255F2661D3A87ECF8038D659B8`
- CUE SHA-256: `EAC4405221D6E031BBC75F7FDAD9F8755E89A7CD2247A8419241CDC164F750D4`
- Source/configuration archive: `C:/Users/Manau47/Documents/Codex/week4-composition-tuner-v154/source-v154d/`

## v154e: editor pause and value handoff

The user requested that the song stop progressing during composition work and
asked how edited scene values would be recovered. In editor mode, Start now
uses the SDK cdstream's documented/example `Stream_Stop()` and
`Stream_Start(ctx, true)` pause/resume path without leaving gameplay. The sample
clock, scene animation, and camera therefore hold at the current position
while editing. Triangle opens a summary page showing all seven transforms;
the user can send a screenshot, from which those values can be transferred to
the scene constants. No remote DuckStation memory read is assumed.

The target-only dry-run and build scheduled source compile, link, and ISO
generation only. The root directory check passed. Pause/resume and summary
capture are newly compiled and still need the user's runtime check.

- BIN SHA-256: `C15BCDE5FCC0DEA8F629F8FB0FA484937191D7055E3933211774C58F857363C3`
- CUE SHA-256: `EA93F6301127408AAE0DFF66243A0CDC6B2EC9B78800CD376B21F53F26C2D8E7`
- Source/configuration archive: `C:/Users/Manau47/Documents/Codex/week4-composition-tuner-v154/source-v154e/`
