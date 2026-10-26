#!/usr/bin/env python3
"""Convert pinned official menu music and navigation cues for the PS1 probe."""

from __future__ import annotations

import argparse
import math
import struct
import subprocess
import wave
from array import array
from pathlib import Path

from convert_bopeebo_to_vagi import (
    INTERLEAVE,
    SAMPLES_PER_BLOCK,
    SAMPLES_PER_CHUNK,
    encode_block,
    encode_channel,
    write_vagi,
)

MENU_RATE = 43008
SFX_RATE = 22050
BLOCK_BYTES = 16
MENU_SOUNDS = ("scrollMenu", "confirmMenu", "cancelMenu")
MISS_SOUNDS = ("missnote1", "missnote2", "missnote3")


def decode_pcm(ffmpeg: Path, source: Path, rate: int, channels: int) -> array:
    command = [str(ffmpeg), "-v", "error", "-i", str(source), "-f", "s16le",
               "-acodec", "pcm_s16le", "-ar", str(rate), "-ac", str(channels),
               "pipe:1"]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    pcm = array("h")
    pcm.frombytes(result.stdout)
    if struct.pack("=H", 1) != struct.pack("<H", 1):
        pcm.byteswap()
    if len(pcm) % channels:
        raise ValueError(f"{source} decoded to a partial PCM frame")
    return pcm


def make_menu_vagi(ffmpeg: Path, source: Path, output: Path) -> int:
    pcm = decode_pcm(ffmpeg, source, MENU_RATE, 2)
    frame_count = len(pcm) // 2
    chunk_count = math.ceil(frame_count / SAMPLES_PER_CHUNK)
    padded_samples = chunk_count * SAMPLES_PER_CHUNK
    left = [0] * padded_samples
    right = [0] * padded_samples
    for frame in range(frame_count):
        left[frame] = pcm[frame * 2]
        right[frame] = pcm[frame * 2 + 1]
    # Use the same 4-voice interleave as the already exercised gameplay path.
    # The menu source is stereo; channels 2 and 3 are silent ADPCM padding.
    silence = [0] * padded_samples
    encoded = [encode_channel(channel, chunk_count)
               for channel in (left, right, silence, silence)]
    write_vagi(output, encoded, MENU_RATE, frame_count, b"FNF FREAKY MENU")
    return frame_count


def make_sfx(ffmpeg: Path, assets: Path, header_path: Path) -> tuple[int, int]:
    samples: list[bytes] = []
    sample_counts: list[int] = []
    names = [(name, assets / "preload" / "sounds" / f"{name}.ogg")
             for name in MENU_SOUNDS]
    names.extend((name, assets / "shared" / "sounds" / f"{name}.ogg")
                 for name in MISS_SOUNDS)
    for name, source in names:
        pcm = decode_pcm(ffmpeg, source, SFX_RATE, 1)
        sample_count = len(pcm)
        blocks = math.ceil(sample_count / SAMPLES_PER_BLOCK)
        blocks = (blocks + 3) & ~3  # 64-byte SPU/DMA alignment.
        padded = list(pcm) + [0] * (blocks * SAMPLES_PER_BLOCK - sample_count)
        encoded = bytearray()
        history = (0, 0)
        for block_index in range(blocks):
            start = block_index * SAMPLES_PER_BLOCK
            block, history = encode_block(
                padded[start:start + SAMPLES_PER_BLOCK], history, False)
            encoded.extend(block)
        if len(encoded) % 64:
            raise AssertionError("menu SFX sample is not DMA aligned")
        encoded[-15] = 0x01  # End block; do not loop.
        samples.append(bytes(encoded))
        sample_counts.append(sample_count)

    bank = bytearray()
    offsets: list[int] = []
    for payload in samples:
        bank.extend(bytes((-len(bank)) % 64))
        offsets.append(len(bank))
        bank.extend(payload)
    if len(bank) > 0x5E000:  # Available from SPU address 0x22000 through 0x7FFFF.
        raise ValueError(f"menu and miss SFX bank exceeds reserved SPU region: {len(bank)} bytes")

    lines = ["#ifndef FUNKIN_PS1_MENU_AUDIO_DATA_H",
             "#define FUNKIN_PS1_MENU_AUDIO_DATA_H", "#include <stdint.h>",
             f"#define MENU_SFX_BANK_SIZE {len(bank)}u",
             f"#define MENU_SFX_RATE {SFX_RATE}u"]
    for index, (name, _source) in enumerate(names):
        macro = name.upper()
        prefix = "MISS_SFX" if name.startswith("missnote") else "MENU_SFX"
        lines.extend((f"#define {prefix}_{macro}_OFFSET {offsets[index]}u",
                      f"#define {prefix}_{macro}_SIZE {len(samples[index])}u",
                      f"#define {prefix}_{macro}_FRAMES {math.ceil(sample_counts[index] * 60 / SFX_RATE)}u"))
    values = ",\n\t".join(", ".join(f"0x{byte:02x}" for byte in bank[i:i + 16])
                                 for i in range(0, len(bank), 16))
    lines.extend((f"static const uint8_t menu_sfx_bank[MENU_SFX_BANK_SIZE] __attribute__((aligned(64))) = {{\n\t{values}\n}};",
                  "#endif"))
    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return len(bank), max(math.ceil(count * 60 / SFX_RATE) for count in sample_counts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--header", type=Path, required=True)
    args = parser.parse_args()

    music_source = args.assets / "preload" / "music" / "freakyMenu" / "freakyMenu.ogg"
    frames = make_menu_vagi(args.ffmpeg, music_source, args.music)
    bank_size, max_sfx_frames = make_sfx(args.ffmpeg, args.assets, args.header)
    print(f"Menu music: pinned FreakyMenu, stereo decoded at {MENU_RATE} Hz, "
          f"two interleaved VAGi channels, "
          f"{frames / MENU_RATE:.3f} s, looping")
    print(f"Official navigation and miss SFX: VAGp ADPCM, {bank_size} SPU bytes, "
          f"max {max_sfx_frames} frames, one-shot; missnote1..3 share the playable SFX pool")


if __name__ == "__main__":
    main()

