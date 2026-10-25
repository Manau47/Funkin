#!/usr/bin/env python3
"""Encode Bopeebo as instrumental L/R, Dad mono, and BF mono VAGi channels."""

from __future__ import annotations

import argparse
import math
import struct
import wave
from array import array
from pathlib import Path

from convert_bopeebo_to_vagi import (
    DEFAULT_RATE,
    INTERLEAVE,
    SAMPLES_PER_BLOCK,
    SAMPLES_PER_CHUNK,
    TAIL_CHUNKS,
    encode_channel,
    read_wav,
    round_signed,
)


def rms(values: list[int]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def encode_mono_voice(pcm: array, frame_count: int) -> tuple[list[int], float, int, float]:
    left = [pcm[frame * 2] for frame in range(frame_count)]
    right = [pcm[frame * 2 + 1] for frame in range(frame_count)]
    mono = [round_signed((l + r) * 0.5) for l, r in zip(left, right)]
    rho = sum(l * r for l, r in zip(left, right)) / math.sqrt(
        sum(v * v for v in left) * sum(v * v for v in right)
    )
    stereo_rms = math.sqrt((sum(v * v for v in left) + sum(v * v for v in right)) /
        (2 * frame_count))
    mono_rms = rms(mono)
    return mono, max(map(abs, mono)), max(-120.0, 20.0 * math.log10(mono_rms / stereo_rms)), rho


def write_vagi(path: Path, channels: list[bytes], rate: int, source_samples: int) -> None:
    channel_bytes = len(channels[0])
    channel_count = len(channels)
    if channel_count != 4 or channel_bytes % INTERLEAVE or any(len(ch) != channel_bytes for ch in channels):
        raise ValueError("expected four equal-length, interleave-aligned channels")
    header = bytearray(b"VAGi")
    header.extend(struct.pack(">I", 0x20))
    header.extend(struct.pack("<I", INTERLEAVE))
    header.extend(struct.pack(">II", channel_bytes, rate))
    header.extend(bytes(10))
    header.extend(struct.pack("<H", channel_count))
    header.extend(b"FNF BOPEEBO 4CH\0")
    if len(header) != 48:
        raise AssertionError(f"unexpected VAGi header size: {len(header)}")
    output = bytearray(header)
    output.extend(bytes(2048 - len(header)))
    for chunk in range(channel_bytes // INTERLEAVE):
        start = chunk * INTERLEAVE
        end = start + INTERLEAVE
        for channel in channels:
            output.extend(channel[start:end])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)
    print(f"Wrote {path}: 4 channels, {rate} Hz, {source_samples / rate:.6f} s, "
        f"{channel_bytes // INTERLEAVE} chunks, {len(output)} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--instrumental", type=Path, required=True)
    parser.add_argument("--player-voice", type=Path, required=True)
    parser.add_argument("--opponent-voice", type=Path, required=True)
    parser.add_argument("--rate", type=int, default=DEFAULT_RATE)
    args = parser.parse_args()
    if args.rate <= 0 or args.rate > 44100:
        parser.error("--rate must be between 1 and 44100 Hz")

    inst, inst_frames = read_wav(args.instrumental, args.rate)
    bf, bf_frames = read_wav(args.player_voice, args.rate)
    dad, dad_frames = read_wav(args.opponent_voice, args.rate)
    if len({inst_frames, bf_frames, dad_frames}) != 1:
        parser.error("all stems must have the same sample origin and frame count")

    dad_mono, dad_peak, dad_gain_db, dad_rho = encode_mono_voice(dad, dad_frames)
    bf_mono, bf_peak, bf_gain_db, bf_rho = encode_mono_voice(bf, bf_frames)
    print(f"Dad downmix: rho={dad_rho:.6f}, RMS delta={dad_gain_db:+.3f} dB, peak={dad_peak}")
    print(f"BF downmix:  rho={bf_rho:.6f}, RMS delta={bf_gain_db:+.3f} dB, peak={bf_peak}")

    chunk_count = (inst_frames + SAMPLES_PER_CHUNK - 1) // SAMPLES_PER_CHUNK + TAIL_CHUNKS
    padded_samples = chunk_count * SAMPLES_PER_CHUNK
    stream_channels: list[list[int]] = [
        [inst[i * 2] for i in range(inst_frames)],
        [inst[i * 2 + 1] for i in range(inst_frames)],
        dad_mono,
        bf_mono,
    ]
    encoded: list[bytes] = []
    names = ("INST L", "INST R", "DAD mono L", "BF mono R")
    for name, samples in zip(names, stream_channels):
        samples.extend([0] * (padded_samples - inst_frames))
        print(f"Encoding {name}: {len(samples)} samples")
        encoded.append(encode_channel(samples, chunk_count))
    write_vagi(args.output, encoded, args.rate, inst_frames)


if __name__ == "__main__":
    main()
