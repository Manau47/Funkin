#!/usr/bin/env python3
"""Generate a short stereo click/bass WAV to verify CD-DA clocking."""

import argparse
import math
import struct
import wave
from pathlib import Path

RATE = 44_100
DURATION_SECONDS = 12
BPM = 120


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="output PCM WAV path")
    args = parser.parse_args()

    sample_count = RATE * DURATION_SECONDS
    beat_samples = RATE * 60 // BPM
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(args.output), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)

        pcm = bytearray()
        for sample in range(sample_count):
            t = sample / RATE
            phase = sample % beat_samples
            click = 0.0
            if phase < RATE * 0.08:
                click = math.sin(2 * math.pi * 1200 * t) * math.exp(-phase / (RATE * 0.018)) * 0.8
            bass = math.sin(2 * math.pi * 110 * t) * 0.12
            value = max(-1.0, min(1.0, click + bass))
            pcm.extend(struct.pack("<hh", round(value * 32767), round(value * 32767)))

        output.writeframes(pcm)


if __name__ == "__main__":
    main()
