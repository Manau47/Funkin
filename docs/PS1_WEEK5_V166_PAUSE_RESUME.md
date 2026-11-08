# Week 5 v166 — pause/resume stream fix

## Scope

This is a narrow runtime fix on top of the v165 Week 5 build. It does not
change charts, audio files, scene art, character extraction, composition, or
gameplay rules. The v165 scene remains unchanged for this test.

## Diagnosis from the supplied error screen

The reported screen shows `FUNKIN PS1 ERROR / CODE 8`, zero CD errors, and 78
SPU underruns with an empty RAM buffer. That identifies an SPU starvation
condition, not a failed CD command. In the old pause path, `abort_cd_read()`
cancelled the active asynchronous sector read after `feed_stream()` had already
advanced `next_sector` and reserved those sectors. The pause screen also did
not pump the audio ring. Resume therefore restarted SPU playback with a
partially drained buffer and could skip the cancelled sector range.

## Change

- Pause now stops SPU playback but lets an in-flight CD read complete.
- The pause loop continues feeding the ring from CD while audio is stopped.
- Resume waits, with the existing bounded wait, until the ring has the
  refill-threshold plus one interleave chunk (clamped to the configured ring
  capacity), then calls `Stream_Start(..., true)`.
- CD errors and prebuffer timeout still produce explicit errors; no failure is
  hidden by clearing counters.

## Build and validation

- The pre-build Ninja dry-run contained only `spu_probe.c` compile, ELF link,
  and ISO creation. No resource conversion was scheduled.
- Compile/ISO status and artifact hashes are recorded in the external v166
  delivery folder.
- Static code/build verification only. DuckStation retest is pending the user;
  the error screenshot establishes the previous failure, not the fix.
- Scene composition and sprite resolution are not corrected by this build.
  The supplied Drive item was accessible as metadata, but the video bytes could
  not be opened by the available file preview/download path in this session.
  Do not infer visual validation from v165's static extraction preview.
