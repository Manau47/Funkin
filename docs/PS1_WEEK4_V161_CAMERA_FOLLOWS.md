# Week 4 v161 — camera follows adjusted character anchors

v160 had the requested visible placement offsets, but the Week 4 camera focus
targets still used the old X anchors. This pass makes the Mom, GF, and BF
focus targets follow their current transformed anchors. It preserves the v160
layer positions (dancers 40 screen pixels higher than v159; Mom/GF/BF about 30
pixels left), the saved camera transform and zoom, and the prior v159 scene
composition. It changes camera targeting only; no assets, scale, animation,
chart, gameplay, or audio changes.

The scene editor, scene demo, and startup diagnostics remain disabled. The
incremental dry-run should include only C compilation, linking, and ISO
creation; converted resources are reused. The ISO root is reordered and
verified with the existing tool. The user still needs to test the result in
DuckStation; no runtime or console validation is claimed.

Exact source, build configuration, executable, ISO, and hashes are archived in
`source-v161/manifest-v161.json` and `delivery-v161-ordered/` outside the repo.

- BIN SHA-256: `9142efece98b3ebd4ab82b1720f2a5e28278ba15af0702dbbfe91b822e06df0f`
- CUE SHA-256: `ba4aea8b20a63bb306b5104e06293415ab72d33c39db013e7f199a4b40fa571c`
