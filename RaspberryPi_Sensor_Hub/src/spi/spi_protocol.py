"""SPI frame helpers for the Raspberry Pi host."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import zlib

MAGIC = 0xA55A
PROTOCOL_VERSION = 1
HEADER_SIZE = 18
CRC_SIZE = 4
MAX_FRAME_BYTES = 512
MAX_PAYLOAD_BYTES = 490
_HEADER_STRUCT = struct.Struct('<HBBHIQ')


class MessageType(IntEnum):
    SNAPSHOT = 0x01
    EVENT = 0x02
    DIAGNOSTIC = 0x03
    VERSION = 0x04
    GET_SNAPSHOT = 0x10
    GET_STATUS = 0x11
    TIME_SYNC = 0x12
    SET_MOTOR_COMMAND = 0x13
    GET_VERSION = 0x14
    ACK = 0x80
    NACK = 0x81


@dataclass(frozen=True)
class SpiFrame:
    message_type: MessageType
    seq: int
    frame_time_us: int = 0
    payload: bytes = b''
    protocol_version: int = PROTOCOL_VERSION

    def encode(self) -> bytes:
        payload = bytes(self.payload)
        if len(payload) > MAX_PAYLOAD_BYTES:
            raise ValueError('payload exceeds SPI contract limit')
        if not 0 <= self.seq <= 0xFFFFFFFF:
            raise ValueError('sequence exceeds uint32 range')
        if not 0 <= self.frame_time_us <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError('frame time exceeds uint64 range')
        header = _HEADER_STRUCT.pack(MAGIC, self.protocol_version, int(self.message_type),
                                     len(payload), self.seq, self.frame_time_us)
        crc = crc32_iso_hdlc(header + payload)
        return header + payload + struct.pack('<I', crc)

    @classmethod
    def decode(cls, frame: bytes) -> 'SpiFrame':
        raw = bytes(frame)
        if len(raw) < HEADER_SIZE + CRC_SIZE or len(raw) > MAX_FRAME_BYTES:
            raise ValueError('invalid SPI frame size')

        magic, protocol_version, message_type, payload_len, seq, frame_time_us = _HEADER_STRUCT.unpack(raw[:HEADER_SIZE])
        if magic != MAGIC:
            raise ValueError('invalid frame magic')
        if protocol_version != PROTOCOL_VERSION:
            raise ValueError('unsupported protocol version')

        expected_length = HEADER_SIZE + payload_len + CRC_SIZE
        if expected_length > MAX_FRAME_BYTES or len(raw) < expected_length:
            raise ValueError('frame length does not match payload length')

        # SPI transport is fixed at 512 bytes. The wire frame itself ends at
        # expected_length; the remainder must be zero padding.
        if len(raw) > expected_length and any(raw[expected_length:]):
            raise ValueError('non-zero bytes after SPI frame')

        try:
            decoded_type = MessageType(message_type)
        except ValueError as exc:
            raise ValueError('unsupported message type') from exc

        expected_crc = struct.unpack('<I', raw[expected_length - CRC_SIZE:expected_length])[0]
        actual_crc = crc32_iso_hdlc(raw[:expected_length - CRC_SIZE])
        if actual_crc != expected_crc:
            raise ValueError('invalid frame crc')

        return cls(message_type=decoded_type, seq=seq, frame_time_us=frame_time_us,
                   payload=raw[HEADER_SIZE:expected_length - CRC_SIZE], protocol_version=protocol_version)


VERSION_PAYLOAD_BYTES = 20
VERSION_SCHEMA_VERSION = 1
BUILD_FLAG_DIRTY = 0x01
_VERSION_STRUCT = struct.Struct('<BBBBBBHIII')


@dataclass(frozen=True)
class VersionInfo:
    """Decoded VERSION (0x04) payload identifying the firmware build."""

    schema_version: int
    protocol_version: int
    firmware_major: int
    firmware_minor: int
    firmware_patch: int
    build_flags: int
    response_to_seq: int
    git_hash_abbrev: int
    commit_epoch_secs: int

    @classmethod
    def decode(cls, payload: bytes) -> 'VersionInfo':
        if len(payload) != VERSION_PAYLOAD_BYTES:
            raise ValueError('unexpected VERSION payload size')
        (schema_version, protocol_version, major, minor, patch, build_flags,
         reserved, response_to_seq, git_hash, commit_epoch) = _VERSION_STRUCT.unpack(payload)
        if schema_version != VERSION_SCHEMA_VERSION:
            raise ValueError('unsupported VERSION schema version')
        if reserved:
            raise ValueError('non-zero reserved bytes in VERSION payload')
        return cls(schema_version=schema_version, protocol_version=protocol_version,
                   firmware_major=major, firmware_minor=minor, firmware_patch=patch,
                   build_flags=build_flags, response_to_seq=response_to_seq,
                   git_hash_abbrev=git_hash, commit_epoch_secs=commit_epoch)

    @property
    def firmware_version(self) -> str:
        return f'{self.firmware_major}.{self.firmware_minor}.{self.firmware_patch}'

    @property
    def git_hash(self) -> str:
        return f'{self.git_hash_abbrev:08x}'

    @property
    def is_dirty_build(self) -> bool:
        """True when the firmware was built from uncommitted changes.

        Evidence recorded against a dirty build cannot close an integration
        gate (SPI_PAYLOAD_SCHEMA.md, VERSION payload).
        """
        return bool(self.build_flags & BUILD_FLAG_DIRTY)

    def summary(self) -> str:
        suffix = '-dirty' if self.is_dirty_build else ''
        return (f'fw {self.firmware_version} ({self.git_hash}{suffix}) '
                f'protocol {self.protocol_version} commit_epoch {self.commit_epoch_secs}')


def crc32_iso_hdlc(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF
