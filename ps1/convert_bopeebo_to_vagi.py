#!/usr/bin/env python3
"""Convert aligned stereo Bopeebo WAV stems into a six-channel VAGi."""

from __future__ import annotations

import argparse
import math
import struct
import wave
from array import array
from pathlib import Path

DEFAULT_RATE = 22050
INTERLEAVE = 4096
SAMPLES_PER_BLOCK = 28
BYTES_PER_BLOCK = 16
BLOCKS_PER_CHUNK = INTERLEAVE // BYTES_PER_BLOCK
SAMPLES_PER_CHUNK = BLOCKS_PER_CHUNK * SAMPLES_PER_BLOCK
TAIL_CHUNKS = 3
FILTERS = ((0, 0), (60, 0), (115, -52), (98, -55), (122, -60))


def round_signed(value: float) -> int:
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def encode_block(samples: list[int], history: tuple[int, int], loop_end: bool) -> tuple[bytes, tuple[int, int]]:
    """Encode one PSX ADPCM block, testing one data-derived shift per predictor."""
    best_error: int | None = None
    best_body: bytes | None = None
    best_history = history

    for predictor, (coef1, coef2) in enumerate(FILTERS):
        # Estimate the residual with unquantized history to choose a shift,
        # then measure the actual quantized reconstruction for that candidate.
        previous, older = history
        max_residual = 0
        for source in samples:
            prediction = (previous * coef1 + older * coef2 + 32) >> 6
            max_residual = max(max_residual, abs(source - prediction))
            older, previous = previous, source
        # PSX ADPCM's shift is inverse: larger values mean a finer step.
        # Select the finest step that still contains the whole residual range.
        shift = 0
        while shift < 12 and max_residual <= 7 * (4096 >> (shift + 1)):
            shift += 1

        previous, older = history
        nibbles: list[int] = []
        decoded: list[int] = []
        error = 0
        scale = 4096 >> shift
        for source in samples:
            prediction = (previous * coef1 + older * coef2 + 32) >> 6
            nibble = round_signed((source - prediction) / scale)
            nibble = min(7, max(-8, nibble))
            reconstructed = max(-32768, min(32767, prediction + nibble * scale))
            delta = source - reconstructed
            error += delta * delta
            nibbles.append(nibble & 0x0f)
            decoded.append(reconstructed)
            older, previous = previous, reconstructed

        if best_error is None or error < best_error:
            flags = 0x03 if loop_end else 0x00
            body = bytearray((predictor << 4 | shift, flags))
            for index in range(0, 28, 2):
                body.append(nibbles[index] | (nibbles[index + 1] << 4))
            best_error = error
            best_body = bytes(body)
            best_history = (previous, older)

    assert best_body is not None
    return best_body, best_history


def read_wav(path: Path, rate: int) -> tuple[array, int]:
    with wave.open(str(path), "rb") as source:
        if source.getnchannels() != 2 or source.getsampwidth() != 2 or source.getframerate() != rate:
            raise ValueError(f"{path} must be 16-bit stereo PCM at {rate} Hz")
        frame_count = source.getnframes()
        pcm = array("h")
        pcm.frombytes(source.readframes(frame_count))
        if struct.pack("=H", 1) != struct.pack("<H", 1):
            pcm.byteswap()
        if len(pcm) != frame_count * 2:
            raise ValueError(f"truncated WAV: {path}")
        return pcm, frame_count


def encode_channel(samples: list[int], chunk_count: int) -> bytes:
    if len(samples) != chunk_count * SAMPLES_PER_CHUNK:
        raise ValueError("all channels must share the VAGi-aligned duration")
    encoded = bytearray()
    history = (0, 0)
    for block_index in range(len(samples) // SAMPLES_PER_BLOCK):
        start = block_index * SAMPLES_PER_BLOCK
        ends_chunk = (block_index + 1) % BLOCKS_PER_CHUNK == 0
        block, history = encode_block(samples[start:start + 28], history, ends_chunk)
        encoded.extend(block)
    return bytes(encoded)


def write_vagi(path: Path, channels: list[bytes], rate: int, sample_count: int) -> None:
    channel_count = len(channels)
    channel_bytes = len(channels[0])
    if channel_count != 6 or channel_bytes % INTERLEAVE or any(len(c) != channel_bytes for c in channels):
        raise ValueError("expected six equally sized, interleave-aligned channels")
    header = bytearray(b"VAGi")
    header.extend(struct.pack(">I", 0x20))
    header.extend(struct.pack("<I", INTERLEAVE))
    header.extend(struct.pack(">II", channel_bytes, rate))
    header.extend(bytes(10))
    header.extend(struct.pack("<H", channel_count))
    header.extend(b"FNF BOPEEBO\0\0\0\0\0")
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
    print(
        f"Wrote {path}: six channels, {rate} Hz, {sample_count / rate:.3f} s source, "
        f"{channel_bytes // INTERLEAVE} chunks, {len(output)} bytes"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--instrumental", type=Path, required=True)
    parser.add_argument("--player-voice", type=Path, required=True)
    parser.add_argument("--opponent-voice", type=Path, required=True)
    parser.add_argument("--rate", type=int, default=DEFAULT_RATE,
        help=f"PCM/VAGi sample rate (default: {DEFAULT_RATE})")
    args = parser.parse_args()

    if args.rate <= 0 or args.rate > 44100:
        parser.error("--rate must be between 1 and 44100 Hz (PS1 SPU output limit)")
    sources = [read_wav(path, args.rate) for path in (args.instrumental, args.player_voice, args.opponent_voice)]
    lengths = {length for _, length in sources}
    if len(lengths) != 1:
        parser.error("all three WAV stems must have the same decoded frame count and origin")
    source_samples = lengths.pop()
    chunk_count = (source_samples + SAMPLES_PER_CHUNK - 1) // SAMPLES_PER_CHUNK + TAIL_CHUNKS
    padded_samples = chunk_count * SAMPLES_PER_CHUNK

    encoded_channels = []
    labels = ("INST L", "INST R", "BF L", "BF R", "DAD L", "DAD R")
    for stem_index, (pcm, _) in enumerate(sources):
        for channel_index in range(2):
            channel = [pcm[frame * 2 + channel_index] for frame in range(source_samples)]
            channel.extend([0] * (padded_samples - source_samples))
            print(f"Encoding {labels[stem_index * 2 + channel_index]}: {len(channel)} samples")
            encoded_channels.append(encode_channel(channel, chunk_count))

    write_vagi(args.output, encoded_channels, args.rate, source_samples)


if __name__ == "__main__":
    main()
