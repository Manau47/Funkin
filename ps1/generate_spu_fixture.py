#!/usr/bin/env python3
"""Generate a small loop-aligned VAGi SPU stream fixture with exact BPM clicks."""

from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

RATE = 43_008
BPM = 120
BEAT_SAMPLES = RATE * 60 // BPM
INTERLEAVE = 4096
FILTERS = ((0, 0), (60, 0), (115, -52), (98, -55), (122, -60))
SAMPLES_PER_BLOCK = 28
BYTES_PER_BLOCK = 16


def round_signed(value: float) -> int:
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def encode_block(samples: list[int], history: tuple[int, int], loop_end: bool) -> tuple[bytes, tuple[int, int]]:
    """Encode 28 PCM samples, choosing the lowest-error PSX SPU ADPCM filter/shift."""
    if len(samples) != SAMPLES_PER_BLOCK:
        raise ValueError("SPU ADPCM blocks must contain exactly 28 samples")

    best_error = None
    best_encoded = None
    best_history = history

    for predictor, (coef1, coef2) in enumerate(FILTERS):
        for shift in range(13):
            previous, older = history
            nibbles: list[int] = []
            decoded: list[int] = []
            error = 0
            scale = 4096 >> shift
            for source in samples:
                prediction = (previous * coef1 + older * coef2 + 32) >> 6
                nibble = round_signed((source - prediction) / scale)
                nibble = min(7, max(-8, nibble))
                reconstructed = prediction + (nibble * scale)
                reconstructed = min(32767, max(-32768, reconstructed))
                delta = source - reconstructed
                error += delta * delta
                nibbles.append(nibble & 0x0F)
                decoded.append(reconstructed)
                older, previous = previous, reconstructed

            if best_error is None or error < best_error:
                flags = 0x03 if loop_end else 0x00
                body = bytearray((predictor << 4 | shift, flags))
                for i in range(0, SAMPLES_PER_BLOCK, 2):
                    body.append(nibbles[i] | (nibbles[i + 1] << 4))
                best_error = error
                best_encoded = bytes(body)
                best_history = (previous, older)

    assert best_encoded is not None
    assert len(best_encoded) == BYTES_PER_BLOCK
    return best_encoded, best_history


def make_pcm(channel_count: int, sample_count: int) -> list[list[int]]:
    channels = [[] for _ in range(channel_count)]
    for sample in range(sample_count):
        phase = sample % BEAT_SAMPLES
        time = sample / RATE

        # Each beat has a short 1.2 kHz transient at its exact sample boundary.
        click = 0.0
        if phase < RATE // 20:
            click = math.sin(2 * math.pi * 1200 * time) * math.exp(-phase / (RATE * 0.018)) * 0.78
        bass = math.sin(2 * math.pi * 110 * time) * 0.16
        left = max(-1.0, min(1.0, click + bass))
        right = max(-1.0, min(1.0, click * 0.88 + math.sin(2 * math.pi * 110 * time + 0.2) * 0.16))
        channels[0].append(round(left * 32767))
        channels[1].append(round(right * 32767))

        if channel_count == 4:
            # A distinct two-note voice motif, half a beat after each beat.
            voice_phase = (phase - BEAT_SAMPLES // 2) % BEAT_SAMPLES
            voice_env = math.exp(-voice_phase / (RATE * 0.12)) if voice_phase < RATE // 4 else 0.0
            voice_left = math.sin(2 * math.pi * 660 * time) * voice_env * 0.36
            voice_right = math.sin(2 * math.pi * 880 * time) * voice_env * 0.30
            channels[2].append(round(voice_left * 32767))
            channels[3].append(round(voice_right * 32767))

    return channels


def encode_channel(samples: list[int], chunk_samples: int) -> bytes:
    if len(samples) % SAMPLES_PER_BLOCK:
        raise ValueError("sample count must be divisible by 28")
    block_count = len(samples) // SAMPLES_PER_BLOCK
    blocks_per_chunk = chunk_samples // SAMPLES_PER_BLOCK
    if chunk_samples % SAMPLES_PER_BLOCK or block_count % blocks_per_chunk:
        raise ValueError("duration must align to the VAGi interleave")

    encoded = bytearray()
    history = (0, 0)
    for block_index in range(block_count):
        start = block_index * SAMPLES_PER_BLOCK
        ends_chunk = (block_index + 1) % blocks_per_chunk == 0
        block, history = encode_block(samples[start : start + SAMPLES_PER_BLOCK], history, ends_chunk)
        encoded.extend(block)
    return bytes(encoded)


def write_vagi(path: Path, channel_data: list[bytes], sample_count: int) -> None:
    channel_count = len(channel_data)
    if channel_count not in (2, 4):
        raise ValueError("fixture supports exactly 2 or 4 channels")
    channel_bytes = len(channel_data[0])
    if any(len(channel) != channel_bytes for channel in channel_data):
        raise ValueError("all channels must have the same encoded length")
    if channel_bytes % INTERLEAVE:
        raise ValueError("encoded duration must be a whole number of interleave chunks")

    header = bytearray()
    header.extend(b"VAGi")
    header.extend(struct.pack(">I", 0x20))
    header.extend(struct.pack("<I", INTERLEAVE))
    header.extend(struct.pack(">II", channel_bytes, RATE))
    header.extend(bytes(10))
    header.extend(struct.pack("<H", channel_count))
    header.extend(b"FNF SPU TEST\0\0\0\0")
    if len(header) != 48:
        raise AssertionError(f"unexpected VAGi header size: {len(header)}")
    header.extend(bytes(2048 - len(header)))

    interleaved = bytearray(header)
    chunk_count = channel_bytes // INTERLEAVE
    for chunk in range(chunk_count):
        start = chunk * INTERLEAVE
        end = start + INTERLEAVE
        for channel in channel_data:
            interleaved.extend(channel[start:end])

    expected_size = 2048 + chunk_count * channel_count * INTERLEAVE
    if len(interleaved) != expected_size:
        raise AssertionError("unexpected VAGi data length")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(interleaved)
    print(
        f"Wrote {path}: {channel_count} channels, {RATE} Hz, {BPM} BPM, "
        f"{sample_count / RATE:.0f} s loop, {chunk_count} chunks, {len(interleaved)} bytes"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="output VAGi path")
    parser.add_argument("--channels", type=int, choices=(2, 4), default=2)
    parser.add_argument("--loop-beats", type=int, default=16)
    args = parser.parse_args()
    if args.loop_beats <= 0 or args.loop_beats % 16:
        parser.error("--loop-beats must be a positive multiple of 16")

    sample_count = BEAT_SAMPLES * args.loop_beats
    blocks_per_chunk = INTERLEAVE // BYTES_PER_BLOCK
    samples_per_chunk = blocks_per_chunk * SAMPLES_PER_BLOCK
    if sample_count % samples_per_chunk:
        parser.error("loop length does not end on a stream chunk boundary")

    pcm = make_pcm(args.channels, sample_count)
    encoded = [encode_channel(channel, samples_per_chunk) for channel in pcm]
    write_vagi(args.output, encoded, sample_count)


if __name__ == "__main__":
    main()
