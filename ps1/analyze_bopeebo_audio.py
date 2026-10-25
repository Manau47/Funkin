#!/usr/bin/env python3
"""Compare decoded Bopeebo stems, sample-rate conversion, and VAGi ADPCM."""

from __future__ import annotations

import argparse
import math
import struct
import wave
from array import array
from pathlib import Path

FILTERS = ((0, 0), (60, 0), (115, -52), (98, -55), (122, -60))
STEMS = ("instrumental", "BF", "Dad")


def wav_read(path: Path) -> tuple[array, int]:
    with wave.open(str(path), "rb") as source:
        if source.getnchannels() != 2 or source.getsampwidth() != 2:
            raise ValueError(f"expected 16-bit stereo PCM: {path}")
        rate = source.getframerate()
        pcm = array("h")
        pcm.frombytes(source.readframes(source.getnframes()))
        if struct.pack("=H", 1) != struct.pack("<H", 1):
            pcm.byteswap()
        return pcm, rate


def decode_vagi(path: Path) -> tuple[list[array], int, int]:
    data = path.read_bytes()
    if data[:4] != b"VAGi":
        raise ValueError(f"not VAGi: {path}")
    interleave = struct.unpack_from("<I", data, 8)[0]
    channel_bytes, rate = struct.unpack_from(">II", data, 12)
    channels = struct.unpack_from("<H", data, 30)[0]
    if channels != 6 or interleave % 16 or len(data) != 2048 + channels * channel_bytes:
        raise ValueError("unexpected VAGi channel count, alignment, or length")

    decoded = [array("h") for _ in range(channels)]
    chunks = channel_bytes // interleave
    for channel in range(channels):
        previous = older = 0
        for chunk in range(chunks):
            start = 2048 + (chunk * channels + channel) * interleave
            end = start + interleave
            for offset in range(start, end, 16):
                header = data[offset]
                predictor, shift = header >> 4, header & 0x0F
                if predictor >= len(FILTERS) or shift > 12:
                    raise ValueError("invalid PSX ADPCM block header")
                coef1, coef2 = FILTERS[predictor]
                for packed in data[offset + 2:offset + 16]:
                    for nibble in (packed & 0x0F, packed >> 4):
                        signed = nibble - 16 if nibble & 8 else nibble
                        prediction = (previous * coef1 + older * coef2 + 32) >> 6
                        sample = max(-32768, min(32767,
                            prediction + signed * (4096 >> shift)))
                        decoded[channel].append(sample)
                        older, previous = previous, sample
    return decoded, rate, chunks


def add_stereo(stems: list[array], frame_count: int) -> array:
    mixed = array("i")
    for frame in range(frame_count):
        base = frame * 2
        mixed.extend((sum(stem[base] for stem in stems),
                      sum(stem[base + 1] for stem in stems)))
    return mixed


def stats(samples: array) -> tuple[float, int, int, float]:
    total = 0
    peak = clips = 0
    for value in samples:
        total += value * value
        peak = max(peak, abs(value))
        clips += value < -32768 or value > 32767
    return math.sqrt(total / len(samples)), peak, clips, 20 * math.log10(32768 / max(peak, 1))


def comparison(reference: array, candidate: array) -> tuple[float, float, float]:
    if len(reference) != len(candidate):
        raise ValueError(f"comparison lengths differ: {len(reference)} vs {len(candidate)}")
    n = len(reference)
    sum_ref = sum_candidate = sum_ref2 = sum_candidate2 = cross = error = 0
    for ref, got in zip(reference, candidate):
        sum_ref += ref
        sum_candidate += got
        sum_ref2 += ref * ref
        sum_candidate2 += got * got
        cross += ref * got
        delta = ref - got
        error += delta * delta
    ref_var = sum_ref2 - sum_ref * sum_ref / n
    got_var = sum_candidate2 - sum_candidate * sum_candidate / n
    covariance = cross - sum_ref * sum_candidate / n
    corr = covariance / math.sqrt(ref_var * got_var) if ref_var and got_var else 0.0
    snr = 10 * math.log10(sum_ref2 / error) if error else float("inf")
    rmse = math.sqrt(error / n)
    return snr, rmse, corr


def report(label: str, samples: array) -> None:
    rms, peak, clips, headroom = stats(samples)
    print(f"{label}: RMS={rms:.1f} peak={peak} over-16bit={clips} headroom={headroom:.2f} dB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", nargs=3, type=Path, required=True,
        metavar=("INST_44100", "BF_44100", "DAD_44100"))
    parser.add_argument("--roundtrip", nargs=3, type=Path, required=True,
        metavar=("INST_UP", "BF_UP", "DAD_UP"))
    parser.add_argument("--pcm", nargs=3, type=Path, required=True,
        metavar=("INST_PCM", "BF_PCM", "DAD_PCM"))
    parser.add_argument("--vagi", type=Path, required=True)
    args = parser.parse_args()

    source = [wav_read(path) for path in args.source]
    roundtrip = [wav_read(path) for path in args.roundtrip]
    pcm = [wav_read(path) for path in args.pcm]
    decoded, rate, chunks = decode_vagi(args.vagi)
    group_counts = [
        {len(samples) // 2 for samples, _ in group}
        for group in (source, roundtrip, pcm)
    ]
    rates = {sample_rate for group in (source, roundtrip, pcm)
        for _, sample_rate in group}
    if any(len(counts) != 1 for counts in group_counts) or len(rates) != 2 or rate not in rates:
        raise ValueError("stems within a group are not aligned or VAGi rate does not match PCM")
    source_frames, roundtrip_frames, pcm_frames = [next(iter(counts)) for counts in group_counts]
    source_compare_frames = min(source_frames, roundtrip_frames)
    if any(sample_rate != 44100 for _, sample_rate in source + roundtrip):
        raise ValueError("source and roundtrip stems must be 44100 Hz")
    pcm_rate = pcm[0][1]
    if any(sample_rate != pcm_rate for _, sample_rate in pcm) or rate != pcm_rate:
        raise ValueError("PCM and VAGi sample rates differ")
    if any(len(channel) < pcm_frames for channel in decoded):
        raise ValueError("VAGi decode is shorter than PCM source")

    source_mix = add_stereo([samples for samples, _ in source], source_compare_frames)
    roundtrip_mix = add_stereo([samples for samples, _ in roundtrip], source_compare_frames)
    pcm_stems = [samples for samples, _ in pcm]
    pcm_mix = add_stereo(pcm_stems, pcm_frames)
    adpcm_stems = [array("h") for _ in range(3)]
    for stem in range(3):
        left, right = decoded[stem * 2:stem * 2 + 2]
        for frame in range(pcm_frames):
            adpcm_stems[stem].extend((left[frame], right[frame]))
    adpcm_mix = add_stereo(adpcm_stems, pcm_frames)
    gain = 0x2800 / 0x3FFF
    scaled_adpcm = array("i", (round(value * gain) for value in adpcm_mix))

    print(f"rate={rate} PCM frames={pcm_frames} duration={pcm_frames / rate:.6f}s chunks={chunks}")
    report("original 44.1kHz mix", source_mix)
    report("PCM target-rate mix", pcm_mix)
    report("decoded ADPCM mix", adpcm_mix)
    report("decoded ADPCM after common 0x2800 gain", scaled_adpcm)
    resample = comparison(source_mix, roundtrip_mix)
    adpcm = comparison(pcm_mix, adpcm_mix)
    print(f"44.1k -> {rate}k -> 44.1k resample: SNR={resample[0]:.2f} dB RMSE={resample[1]:.1f} corr={resample[2]:.7f}")
    print(f"target-rate PCM -> ADPCM decode: SNR={adpcm[0]:.2f} dB RMSE={adpcm[1]:.1f} corr={adpcm[2]:.7f}")
    for index, label in enumerate(STEMS):
        stem = add_stereo([pcm_stems[index]], pcm_frames)
        got = add_stereo([adpcm_stems[index]], pcm_frames)
        result = comparison(stem, got)
        print(f"{label} ADPCM: SNR={result[0]:.2f} dB RMSE={result[1]:.1f} corr={result[2]:.7f}")


if __name__ == "__main__":
    main()
