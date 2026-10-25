#!/usr/bin/env python3
"""Measure voice mono downmix and decoded four-channel Bopeebo mix headroom."""

from __future__ import annotations

import argparse
import math
import struct
import sys
from array import array
from pathlib import Path

from analyze_bopeebo_audio import FILTERS, decode_vagi, wav_read

PAN = (
    (11585, 11585), (12809, 10215), (13872, 8716), (14761, 7108),
    (15464, 5411), (15972, 3646), (16280, 1834), (16383, 0),
)
MUSIC_GAIN = 0x2800
SFX_POOL_VOLUME_BUDGET = 0x1800


def mono_stats(stereo: array) -> tuple[float, float, int]:
    left = stereo[0::2]
    right = stereo[1::2]
    dot = sum(a * b for a, b in zip(left, right))
    rho = dot / math.sqrt(sum(x*x for x in left) * sum(x*x for x in right))
    mono = [((a + b + 1) // 2 if a + b >= 0 else -((-a - b + 1) // 2))
        for a, b in zip(left, right)]
    source_rms = math.sqrt((sum(x*x for x in left) + sum(x*x for x in right)) / (2 * len(left)))
    mono_rms = math.sqrt(sum(x*x for x in mono) / len(mono))
    delta_db = 20 * math.log10(mono_rms / source_rms)
    return rho, delta_db, max(map(abs, mono))


def decode_vag_payload(path: Path) -> array:
    data = path.read_bytes()
    if data[:4] != b"VAGp":
        raise ValueError("SFX file must be a VAGp file")
    size = struct.unpack_from(">I", data, 12)[0]
    rate = struct.unpack_from(">I", data, 16)[0]
    if size != len(data) - 48 or size % 64 or rate != 22050:
        raise ValueError("invalid VAGp payload size")
    flags = [data[offset + 1] for offset in range(48, len(data), 16)]
    if flags[-1] != 0x01 or any(flag != 0 for flag in flags[:-1]):
        raise ValueError("expected non-looping VAGp blocks and one final end flag")
    result = array("h")
    previous = older = 0
    for offset in range(48, len(data), 16):
        predictor, shift = data[offset] >> 4, data[offset] & 15
        if predictor >= len(FILTERS) or shift > 12:
            raise ValueError("invalid ADPCM block")
        c1, c2 = FILTERS[predictor]
        for byte in data[offset + 2:offset + 16]:
            for nibble in (byte & 15, byte >> 4):
                signed = nibble - 16 if nibble & 8 else nibble
                sample = max(-32768, min(32767,
                    ((previous * c1 + older * c2 + 32) >> 6) + signed * (4096 >> shift)))
                result.append(sample)
                older, previous = previous, sample
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instrumental", type=Path, required=True, help="43,008 Hz stereo PCM WAV")
    parser.add_argument("--bf", type=Path, required=True, help="43,008 Hz stereo PCM WAV")
    parser.add_argument("--dad", type=Path, required=True, help="43,008 Hz stereo PCM WAV")
    parser.add_argument("--vagi", type=Path, required=True)
    parser.add_argument("--sfx", type=Path, required=True, help="generated VAGp test effect")
    args = parser.parse_args()

    sources = [wav_read(path) for path in (args.instrumental, args.dad, args.bf)]
    if len({rate for _, rate in sources}) != 1 or sources[0][1] != 43008:
        raise ValueError("all PCM sources must be 43,008 Hz")
    if len({len(pcm) for pcm, _ in sources}) != 1:
        raise ValueError("PCM stems must have a common origin and duration")
    decoded, rate, chunks = decode_vagi(args.vagi)
    frames = len(sources[0][0]) // 2
    if rate != 43008 or len(decoded) != 4 or any(len(channel) < frames for channel in decoded):
        raise ValueError("expected a four-channel 43,008 Hz VAGi covering all PCM frames")

    print(f"VAGi {rate} Hz, {frames} source frames, {frames/rate:.6f} s, {chunks} chunks")
    for label, (pcm, _) in zip(("Dad", "BF"), sources[1:]):
        rho, delta, peak = mono_stats(pcm)
        print(f"{label} mono average(L,R): correlation={rho:.6f}, RMS delta={delta:+.3f} dB, peak={peak}")

    effect = decode_vag_payload(args.sfx)
    effect_peak = max(map(abs, effect))
    effect_rms = math.sqrt(sum(sample * sample for sample in effect) / len(effect))
    sfx_bound = math.ceil(effect_peak * SFX_POOL_VOLUME_BUDGET / 0x3FFF)
    print(f"SFX 22050 Hz, {len(effect)} decoded samples ({len(effect)/22050:.3f} s), "
          f"RMS={effect_rms:.1f}, peak={effect_peak}; up to 4 simultaneous voices with "
          f"aggregate volume budget 0x{SFX_POOL_VOLUME_BUDGET:04x}: <= {sfx_bound} LSB/channel")

    music_gain = MUSIC_GAIN / 0x3FFF
    for width in (0, 4, 7):
        pl, pr = PAN[width]
        left_peak = right_peak = 0
        left_sq = right_sq = 0
        for i in range(frames):
            # Fixed order: instrumental L/R, Dad mono, BF mono. Voices are panned
            # symmetrically around center, preserving equal-power pan law.
            left = (decoded[0][i] * 0x3FFF + decoded[2][i] * pl + decoded[3][i] * pr) / 0x3FFF * music_gain
            right = (decoded[1][i] * 0x3FFF + decoded[2][i] * pr + decoded[3][i] * pl) / 0x3FFF * music_gain
            left_i, right_i = round(left), round(right)
            left_peak, right_peak = max(left_peak, abs(left_i)), max(right_peak, abs(right_i))
            left_sq += left_i * left_i
            right_sq += right_i * right_i
        combined_l, combined_r = left_peak + sfx_bound, right_peak + sfx_bound
        headroom_l = 20 * math.log10(32767 / max(combined_l, 1))
        headroom_r = 20 * math.log10(32767 / max(combined_r, 1))
        print(f"pan width {width}/7: music peak L/R={left_peak}/{right_peak}, "
              f"RMS L/R={math.sqrt(left_sq/frames):.1f}/{math.sqrt(right_sq/frames):.1f}, "
              f"music+4xSFX worst-case bound={combined_l}/{combined_r}, "
              f"remaining headroom={headroom_l:.2f}/{headroom_r:.2f} dB")


if __name__ == "__main__":
    main()
