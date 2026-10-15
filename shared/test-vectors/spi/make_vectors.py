#!/usr/bin/env python3
"""Generate or check the shared SPI golden frames (frames.txt, format in README.md).

`frames.txt` is the authority: it is what both test suites read. This script is the tool
that produces a candidate for it and checks that the committed file still equals that
candidate (`--check`). It encodes with plain `struct` and `zlib` on purpose and imports
neither production implementation, so a vector it writes is a third, independent
rendering of the contract rather than a copy of either side's output.

The vectors describe the as-built protocol module (`Arm_Sensor_Hub/App/Src/spi_protocol.c`):
the STM32 state before a transaction, the request the Pi sends, the result the firmware
reports, and the exact response it stages. Rulings that change the wire (R1 rejection
rules, R4 padding, R18 reason codes, R19 system-activate) add their vectors in the same
commit that changes the code (ARCHITECTURE_DECISIONS.md, code-review rulings preamble).

Usage, from the repository root:
    python3 shared/test-vectors/spi/make_vectors.py            # rewrite frames.txt
    python3 shared/test-vectors/spi/make_vectors.py --check    # exit 1 if frames.txt differs
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

# SPI_SYSTEM_INTERFACE.md section 3.
MAGIC = 0xA55A
PROTOCOL_VERSION = 1
FRAME_BYTES = 512
HEADER = struct.Struct('<HBBHIQ')   # magic, version, type, payload_len, seq, frame_time_us
CRC = struct.Struct('<I')

# SPI_SYSTEM_INTERFACE.md section 5 (the as-built subset the firmware implements).
SNAPSHOT, DIAGNOSTIC, VERSION, GET_SNAPSHOT, GET_STATUS, TIME_SYNC, GET_VERSION, ACK, NACK = (
    0x01, 0x03, 0x04, 0x10, 0x11, 0x12, 0x14, 0x80, 0x81)
UNASSIGNED_TYPE = 0x15
# Every assigned value in section 5: the types the Pi decoder (MessageType) accepts. A request
# of any other type is not a transport-valid frame for the Pi, so it carries no request fields.
PI_KNOWN_TYPES = {0x01, 0x02, 0x03, 0x04, 0x10, 0x11, 0x12, 0x13, 0x14, 0x80, 0x81}

# NACK status codes, SPI_SYSTEM_INTERFACE.md section 14 (SpiProtocol_Result / NackReason).
RESULT = {
    'OK': 0, 'BAD_MAGIC': 1, 'BAD_VERSION': 2, 'BAD_LENGTH': 3, 'BAD_CRC': 4,
    'BAD_SEQUENCE': 5, 'BAD_MESSAGE': 6, 'BAD_TIME_SYNC': 7, 'BAD_STATE': 8,
}

# The VERSION reply carries the firmware identity (firmware_version.h). The host tests build
# without the generated identity header, so they report these fallback values; a change to
# FIRMWARE_VERSION_MAJOR/MINOR/PATCH regenerates the get_version vector (README.md).
HOST_TEST_IDENTITY = dict(major=0, minor=1, patch=0, build_flags=0, git_hash_abbrev=0, commit_epoch_secs=0)

# SPI_PAYLOAD_SCHEMA.md, "GET and Command Requests": schema_version then reserved zero bytes.
# Four bytes is the shape ruling R1 fixes; the as-built firmware accepts it already.
GET_REQUEST_PAYLOAD = bytes([1, 0, 0, 0])


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def frame(msg_type: int, seq: int, payload: bytes = b'', frame_time_us: int = 0, *,
          version: int = PROTOCOL_VERSION, magic: int = MAGIC,
          payload_len: int | None = None, crc: int | None = None) -> bytes:
    header = HEADER.pack(magic, version, msg_type,
                         len(payload) if payload_len is None else payload_len, seq, frame_time_us)
    body = header + payload
    return body + CRC.pack(crc32(body) if crc is None else crc)


def command_reply(request_type: int, status: int, request_seq: int, detail: int = 0) -> bytes:
    # SPI_PAYLOAD_SCHEMA.md ACK/NACK: schema, request_type, status_code, request_seq, detail_code.
    return struct.pack('<BBHII', 1, request_type, status, request_seq, detail)


def version_payload(response_to_seq: int) -> bytes:
    # SPI_PAYLOAD_SCHEMA.md VERSION: schema, protocol_version, major, minor, patch, build_flags,
    # reserved, response_to_seq, git_hash_abbrev, commit_epoch_secs.
    identity = HOST_TEST_IDENTITY
    return struct.pack('<BBBBBBHIII', 1, PROTOCOL_VERSION, identity['major'], identity['minor'],
                       identity['patch'], identity['build_flags'], 0, response_to_seq,
                       identity['git_hash_abbrev'], identity['commit_epoch_secs'])


def sensor_record(sensor_id: int, flags: int, ts: int, raw: int, mdeg: int, mag: int, agc: int) -> bytes:
    return struct.pack('<BBHQHiHBBH', sensor_id, 0, flags, ts, raw, mdeg, mag, agc, 0, 0)


def motor_record(index: int, flags: int, can_id: int, cmd: int, ts: int, payload: bytes) -> bytes:
    return struct.pack('<BBHHBBQ8s', index, 0, flags, can_id, cmd, len(payload), ts, payload.ljust(8, b'\0'))


def snapshot_payload(response_to_seq: int) -> bytes:
    # Prefix (spi_payload_layout.h SPI_SNAPSHOT_*): schema 1, six sensor records, one motor record.
    prefix = struct.pack('<BBBBHHI', 1, 6, 1, 0, 0, 0, response_to_seq)
    valid = 0x0001 | 0x0020          # SAMPLE_VALID | TIMESTAMP_SYNCHRONIZED
    not_fitted = 0x0040
    sensors = b''.join([
        sensor_record(0, valid, 1_000_100, 0x0123, 25_620, 1_480, 96),
        sensor_record(1, valid, 1_000_250, 0x0800, 180_000, 1_502, 93),
        sensor_record(2, valid, 1_000_400, 0x0FFF, 359_912, 1_431, 101),
        sensor_record(3, not_fitted, 0, 0, 0, 0, 0),
        sensor_record(4, not_fitted, 0, 0, 0, 0, 0),
        sensor_record(5, not_fitted, 0, 0, 0, 0, 0),
    ])
    motor = motor_record(0, 0x0001, 0x0001, 0x31, 1_000_600, bytes.fromhex('31 00 00 12 34 56 00 00'))
    return prefix + sensors + motor


class Vector:
    def __init__(self, name: str, description: str, *, next_tx_seq: int, now_us: int,
                 last_request_seq: int | None = None, staged_snapshot: bytes | None = None,
                 request: bytes | None = None, request_fields: tuple | None = None,
                 expect: str = 'OK', response: bytes | None = None, response_fields: tuple | None = None):
        if expect not in RESULT:
            raise ValueError(expect)
        self.name, self.description = name, description
        self.next_tx_seq, self.now_us, self.last_request_seq = next_tx_seq, now_us, last_request_seq
        self.staged_snapshot = staged_snapshot
        self.request, self.request_fields = request, request_fields
        self.expect = expect
        self.response, self.response_fields = response, response_fields

    def render(self) -> str:
        lines = [f'[{self.name}]', f'description = {self.description}',
                 f'stm32.next_tx_seq = {self.next_tx_seq}',
                 'stm32.last_request_seq = ' + ('none' if self.last_request_seq is None else str(self.last_request_seq)),
                 f'stm32.now_us = {self.now_us}']
        if self.staged_snapshot is not None:
            lines.append(f'stm32.staged_snapshot = {self.staged_snapshot.hex().upper()}')
        if self.request is not None:
            lines.append(f'request = {self.request.hex().upper()}')
            lines += _fields('request', self.request_fields)
        lines.append(f'expect = {self.expect}')
        if self.response is not None:
            lines.append(f'response = {self.response.hex().upper()}')
            lines += _fields('response', self.response_fields)
        return '\n'.join(lines) + '\n'


def _fields(prefix: str, fields: tuple | None) -> list[str]:
    if fields is None:
        return []
    msg_type, seq, frame_time_us, payload = fields
    return [f'{prefix}.type = 0x{msg_type:02X}', f'{prefix}.seq = {seq}',
            f'{prefix}.frame_time_us = {frame_time_us}', f'{prefix}.payload = {payload.hex().upper()}']


def request_vector(name, description, *, msg_type, seq, payload=b'', next_tx_seq, now_us,
                   last_request_seq=None, staged_snapshot=None, expect='OK',
                   reply_type=None, reply_payload=None, **frame_overrides) -> Vector:
    """A request the Pi encodes, and the reply the protocol module stages for it."""
    req = frame(msg_type, seq, payload, 0, **frame_overrides)
    malformed = bool(frame_overrides) or (msg_type not in PI_KNOWN_TYPES)
    reply = None if reply_type is None else frame(reply_type, next_tx_seq, reply_payload, now_us)
    return Vector(name, description, next_tx_seq=next_tx_seq, now_us=now_us,
                  last_request_seq=last_request_seq, staged_snapshot=staged_snapshot,
                  request=req, request_fields=None if malformed else (msg_type, seq, 0, payload),
                  expect=expect, response=reply,
                  response_fields=None if reply is None else (reply_type, next_tx_seq, now_us, reply_payload))


def nack_vector(name, description, *, request_type, seq, expect, **kw) -> Vector:
    kw.setdefault('msg_type', request_type)
    return request_vector(name, description, seq=seq, expect=expect, reply_type=NACK,
                          reply_payload=command_reply(request_type, RESULT[expect], seq), **kw)


def vectors() -> list[Vector]:
    staged = snapshot_payload(0)
    v = []
    v.append(Vector(
        'boot_status',
        'First frame after boot (SPI_SYSTEM_INTERFACE.md section 4): DIAGNOSTIC (0x03) with an empty '
        'payload as built; ruling R14 adds the DIAGNOSTIC v1 content.',
        next_tx_seq=1, now_us=1_000,
        response=frame(DIAGNOSTIC, 1, b'', 1_000), response_fields=(DIAGNOSTIC, 1, 1_000, b'')))
    v.append(request_vector(
        'get_status_ack',
        'GET_STATUS with the four-byte request payload (schema 1, three reserved zero bytes); '
        'answered by ACK with status 0 and the request seq echoed.',
        msg_type=GET_STATUS, seq=10, payload=GET_REQUEST_PAYLOAD, next_tx_seq=2, now_us=2_000,
        reply_type=ACK, reply_payload=command_reply(GET_STATUS, 0, 10)))
    v.append(request_vector(
        'get_snapshot_staged',
        'GET_SNAPSHOT while a snapshot is staged: the staged payload is sent as SNAPSHOT with '
        'response_to_seq patched to the request seq (six sensor records, one motor record).',
        msg_type=GET_SNAPSHOT, seq=11, payload=GET_REQUEST_PAYLOAD, next_tx_seq=3, now_us=3_000,
        last_request_seq=10, staged_snapshot=staged,
        reply_type=SNAPSHOT, reply_payload=snapshot_payload(11)))
    v.append(request_vector(
        'get_snapshot_none_staged',
        'GET_SNAPSHOT with nothing staged is acknowledged, not answered with a SNAPSHOT.',
        msg_type=GET_SNAPSHOT, seq=12, payload=GET_REQUEST_PAYLOAD, next_tx_seq=4, now_us=4_000,
        last_request_seq=11, reply_type=ACK, reply_payload=command_reply(GET_SNAPSHOT, 0, 12)))
    v.append(request_vector(
        'get_version',
        'GET_VERSION answered by VERSION (0x04). The identity fields (version, build flags, git '
        'hash, commit epoch) are the host-test fallback identity of firmware_version.h, not contract; '
        'the layout, type and response_to_seq are.',
        msg_type=GET_VERSION, seq=13, payload=GET_REQUEST_PAYLOAD, next_tx_seq=5, now_us=5_000,
        last_request_seq=12, reply_type=VERSION, reply_payload=version_payload(13)))
    v.append(request_vector(
        'time_sync_ack',
        'TIME_SYNC (deprecated by Issue #12, still implemented) with its 16-byte payload: the '
        'protocol module ACKs a well-formed request. The service may still NACK BAD_TIME_SYNC after '
        'time_service judges the sample; that path is not a frame-format fact.',
        msg_type=TIME_SYNC, seq=14, payload=struct.pack('<BBHQI', 1, 0, 0, 1_700_000_000_000_000, 7),
        next_tx_seq=6, now_us=6_000, last_request_seq=13,
        reply_type=ACK, reply_payload=command_reply(TIME_SYNC, 0, 14)))
    v.append(nack_vector(
        'nack_bad_magic',
        'Magic 0xA55B instead of 0xA55A (CRC valid over the bytes as sent): NACK BAD_MAGIC.',
        request_type=GET_STATUS, seq=15, payload=GET_REQUEST_PAYLOAD, next_tx_seq=7, now_us=7_000,
        last_request_seq=14, expect='BAD_MAGIC', magic=0xA55B))
    v.append(nack_vector(
        'nack_bad_version',
        'protocol_version 2 (CRC valid): NACK BAD_VERSION.',
        request_type=GET_STATUS, seq=16, payload=GET_REQUEST_PAYLOAD, next_tx_seq=8, now_us=8_000,
        last_request_seq=15, expect='BAD_VERSION', version=2))
    v.append(nack_vector(
        'nack_bad_length',
        'payload_len 491, one above the 490-byte maximum; the frame has no CRC position inside '
        '512 bytes, so the request is the full 512-byte transaction: NACK BAD_LENGTH.',
        request_type=GET_STATUS, seq=17, payload=bytes(FRAME_BYTES - HEADER.size - CRC.size),
        next_tx_seq=9, now_us=9_000, last_request_seq=16, expect='BAD_LENGTH',
        payload_len=491, crc=0))
    v.append(nack_vector(
        'nack_bad_crc',
        'GET_STATUS with every CRC bit inverted: NACK BAD_CRC.',
        request_type=GET_STATUS, seq=18, payload=GET_REQUEST_PAYLOAD, next_tx_seq=10, now_us=10_000,
        last_request_seq=17, expect='BAD_CRC',
        crc=crc32(HEADER.pack(MAGIC, PROTOCOL_VERSION, GET_STATUS, 4, 18, 0) + GET_REQUEST_PAYLOAD) ^ 0xFFFFFFFF))
    v.append(nack_vector(
        'nack_bad_sequence',
        'A well-formed GET_STATUS whose seq equals the last accepted request seq is not newer '
        '(SPI_SYSTEM_INTERFACE.md section 6): NACK BAD_SEQUENCE.',
        request_type=GET_STATUS, seq=18, payload=GET_REQUEST_PAYLOAD, next_tx_seq=11, now_us=11_000,
        last_request_seq=18, expect='BAD_SEQUENCE'))
    v.append(nack_vector(
        'nack_bad_message',
        'Unassigned message type 0x15 (CRC valid): NACK BAD_MESSAGE. Not a transport-valid frame '
        'for the Pi decoder either, so no request fields.',
        request_type=UNASSIGNED_TYPE, seq=19, payload=GET_REQUEST_PAYLOAD, next_tx_seq=12, now_us=12_000,
        last_request_seq=18, expect='BAD_MESSAGE'))
    v.append(nack_vector(
        'nack_bad_time_sync',
        'TIME_SYNC with a 15-byte payload instead of 16 (transport-valid frame): NACK BAD_TIME_SYNC.',
        request_type=TIME_SYNC, seq=20, payload=bytes([1]) + bytes(14), next_tx_seq=13, now_us=13_000,
        last_request_seq=19, expect='BAD_TIME_SYNC'))
    return v


HEADER_TEXT = """\
# Karetao shared SPI golden frames. Format and rules: README.md in this directory.
# This file is the authority; make_vectors.py regenerates it and `--check` compares.
# Hex values are byte sequences in wire order: the first two characters are byte 0.
# Bytes beyond a request or response up to the 512-byte transaction are zero.
"""


def render_all() -> str:
    return HEADER_TEXT + '\n' + '\n'.join(v.render() for v in vectors())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='compare frames.txt with the generated text')
    args = parser.parse_args(argv)
    target = Path(__file__).resolve().parent / 'frames.txt'
    text = render_all()
    if args.check:
        current = target.read_text() if target.exists() else ''
        if current != text:
            print(f'{target} differs from the generated vectors; rerun without --check', file=sys.stderr)
            return 1
        print(f'{target}: matches ({len(vectors())} vectors)')
        return 0
    target.write_text(text)
    print(f'wrote {target} ({len(vectors())} vectors)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
