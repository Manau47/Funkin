#!/usr/bin/env python3
"""Move only the v76 ISO root record for SYSTEM.CNF to the front.

This preserves every file extent and all bytes outside the two root-directory
sectors. Because inputs are raw Mode 2/2352 sectors, EDC/ECC are recalculated
for the changed sectors. Outputs are created exclusively and never overwrite.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

SECTOR_SIZE = 2352
USER_DATA_OFFSET = 24
USER_DATA_SIZE = 2048
V76_BIN_SHA256 = "828489413342768586115C99AD5C1A6B82FC65F88800A17F16308A3BC9E08402"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def make_tables() -> tuple[list[int], list[int], list[int]]:
    ecc_f = [0] * 256
    ecc_b = [0] * 256
    edc = [0] * 256
    for i in range(256):
        j = (i << 1) ^ (0x11D if i & 0x80 else 0)
        ecc_f[i] = j
        ecc_b[i ^ j] = i
        value = i
        for _ in range(8):
            value = (value >> 1) ^ (0xD8018001 if value & 1 else 0)
        edc[i] = value
    return ecc_f, ecc_b, edc


ECC_F, ECC_B, EDC_TABLE = make_tables()


def calc_edc(data: bytes) -> int:
    value = 0
    for byte in data:
        value = (value >> 8) ^ EDC_TABLE[(value ^ byte) & 0xFF]
    return value


def calc_ecc(data: bytes, major_count: int, minor_count: int,
             major_mult: int, minor_inc: int) -> bytes:
    size = major_count * minor_count
    if len(data) != size:
        raise ValueError(f"ECC input size {len(data)} != {size}")
    result = bytearray(major_count * 2)
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        ecc_a = ecc_b = 0
        for _ in range(minor_count):
            value = data[index]
            index += minor_inc
            if index >= size:
                index -= size
            ecc_a ^= value
            ecc_b ^= value
            ecc_a = ECC_F[ecc_a]
        ecc_a = ECC_B[ECC_F[ecc_a] ^ ecc_b]
        result[major] = ecc_a
        result[major + major_count] = ecc_a ^ ecc_b
    return bytes(result)


def sector_checks(sector: bytes) -> tuple[bytes, bytes, bytes]:
    if len(sector) != SECTOR_SIZE or sector[15] != 2:
        raise ValueError("expected a raw Mode 2/2352 sector")
    # Mode 2 Form 1 has no ECC over the address/mode bytes: use zero address.
    edc = struct.pack("<I", calc_edc(sector[16:2072]))
    address = b"\0\0\0\0"
    ecc_p = calc_ecc(address + sector[16:2076], 86, 24, 2, 86)
    ecc_q = calc_ecc(address + sector[16:2248], 52, 43, 86, 88)
    return edc, ecc_p, ecc_q


def record_name(record: bytes) -> bytes:
    length = record[32]
    return record[33:33 + length]


def parse_records(directory: bytes) -> list[bytes]:
    records: list[bytes] = []
    pos = 0
    while pos < len(directory):
        length = directory[pos]
        if length == 0:
            pos = ((pos // USER_DATA_SIZE) + 1) * USER_DATA_SIZE
            continue
        if length < 34 or pos + length > len(directory):
            raise ValueError(f"invalid directory record at offset {pos}")
        records.append(directory[pos:pos + length])
        pos += length
    return records


def pack_records(records: list[bytes], total_size: int) -> bytes:
    output = bytearray(total_size)
    pos = 0
    for record in records:
        if (pos % USER_DATA_SIZE) + len(record) > USER_DATA_SIZE:
            pos = ((pos // USER_DATA_SIZE) + 1) * USER_DATA_SIZE
        if pos + len(record) > total_size:
            raise ValueError("reordered directory exceeds original extent")
        output[pos:pos + len(record)] = record
        pos += len(record)
    return bytes(output)


def patch_sector(source: bytes, user_data: bytes) -> bytes:
    if len(user_data) != USER_DATA_SIZE:
        raise ValueError("sector user data must be 2048 bytes")
    sector = bytearray(source)
    sector[USER_DATA_OFFSET:USER_DATA_OFFSET + USER_DATA_SIZE] = user_data
    edc, ecc_p, ecc_q = sector_checks(bytes(sector))
    sector[2072:2076] = edc
    # P must be present when Q is computed.
    p_source = b"\0\0\0\0" + bytes(sector[16:2076])
    sector[2076:2248] = calc_ecc(p_source, 86, 24, 2, 86)
    q_source = b"\0\0\0\0" + bytes(sector[16:2248])
    sector[2248:2352] = calc_ecc(q_source, 52, 43, 86, 88)
    return bytes(sector)


def build(source_bin: Path, source_cue: Path, output_bin: Path,
          output_cue: Path) -> None:
    if output_bin.exists() or output_cue.exists():
        raise FileExistsError("refusing to overwrite an existing output")
    raw = source_bin.read_bytes()
    if sha256(raw) != V76_BIN_SHA256:
        raise ValueError("source BIN hash does not match the preserved v76 reference")
    if len(raw) % SECTOR_SIZE:
        raise ValueError("source BIN is not a whole number of raw sectors")

    pvd_pos = 16 * SECTOR_SIZE + USER_DATA_OFFSET
    if raw[pvd_pos:pvd_pos + 7] != b"\x01CD001\x01":
        raise ValueError("ISO9660 primary volume descriptor not found")
    root_record = pvd_pos + 156
    root_lba = struct.unpack_from("<I", raw, root_record + 2)[0]
    root_size = struct.unpack_from("<I", raw, root_record + 10)[0]
    if root_size % USER_DATA_SIZE:
        raise ValueError("root directory extent is not sector aligned")

    start = root_lba * SECTOR_SIZE
    sector_count = root_size // USER_DATA_SIZE
    original_sectors = [raw[start + i * SECTOR_SIZE:start + (i + 1) * SECTOR_SIZE]
                        for i in range(sector_count)]
    for index, sector in enumerate(original_sectors):
        edc, ecc_p, ecc_q = sector_checks(sector)
        if sector[2072:2076] != edc:
            raise ValueError(f"original root sector {root_lba + index} EDC mismatch")
        test = bytearray(sector)
        test[12:16] = b"\0\0\0\0"
        test[2076:2248] = ecc_p
        test[2248:2352] = ecc_q
        if sector[2076:2352] != test[2076:2352]:
            raise ValueError(f"original root sector {root_lba + index} ECC mismatch")

    directory = b"".join(s[USER_DATA_OFFSET:USER_DATA_OFFSET + USER_DATA_SIZE]
                          for s in original_sectors)
    records = parse_records(directory)
    special = [r for r in records if record_name(r) in (b"\0", b"\1")]
    files = [r for r in records if record_name(r) not in (b"\0", b"\1")]
    cnf = [r for r in files if record_name(r).upper() == b"SYSTEM.CNF;1"]
    if len(files) != 48 or len(cnf) != 1:
        raise ValueError(f"expected 48 visible files and one SYSTEM.CNF, got {len(files)}")
    cnf_index = files.index(cnf[0])
    if cnf_index < 30:
        raise ValueError("source SYSTEM.CNF is not late enough to isolate the reported issue")

    exe = [r for r in files if record_name(r).upper() == b"FUNKIN.EXE;1"]
    if len(exe) != 1:
        raise ValueError("expected exactly one FUNKIN.EXE")
    ordered = special + cnf + [r for r in files if r is not cnf[0]]
    patched_directory = pack_records(ordered, root_size)

    result = bytearray(raw)
    for index, sector in enumerate(original_sectors):
        chunk = patched_directory[index * USER_DATA_SIZE:(index + 1) * USER_DATA_SIZE]
        result[start + index * SECTOR_SIZE:start + (index + 1) * SECTOR_SIZE] = patch_sector(sector, chunk)

    # Ensure every byte outside the root-directory sectors is preserved.
    spans = [(start + i * SECTOR_SIZE, start + (i + 1) * SECTOR_SIZE)
             for i in range(sector_count)]
    cursor = 0
    for left, right in spans:
        if raw[cursor:left] != result[cursor:left]:
            raise AssertionError("bytes before root directory changed")
        cursor = right
    if raw[cursor:] != result[cursor:]:
        raise AssertionError("bytes after root directory changed")

    cue_text = source_cue.read_text(encoding="ascii")
    old_name = source_bin.name
    if old_name not in cue_text:
        raise ValueError("source CUE does not name source BIN")
    cue_out = cue_text.replace(old_name, output_bin.name, 1).encode("ascii")
    output_bin.parent.mkdir(parents=True, exist_ok=True)
    with output_bin.open("xb") as stream:
        stream.write(result)
    with output_cue.open("xb") as stream:
        stream.write(cue_out)

    print(f"source_sha256={sha256(raw)}")
    print(f"root_lba={root_lba} root_size={root_size} visible_files={len(files)}")
    print(f"source_system_cnf_file_index={cnf_index + 1}")
    print(f"output_system_cnf_file_index=1")
    print(f"output_bin_bytes={len(result)} output_bin_sha256={sha256(result)}")
    print(f"output_cue_bytes={len(cue_out)} output_cue_sha256={sha256(cue_out)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_bin", type=Path)
    parser.add_argument("source_cue", type=Path)
    parser.add_argument("output_bin", type=Path)
    parser.add_argument("output_cue", type=Path)
    args = parser.parse_args()
    build(args.source_bin, args.source_cue, args.output_bin, args.output_cue)


if __name__ == "__main__":
    main()
