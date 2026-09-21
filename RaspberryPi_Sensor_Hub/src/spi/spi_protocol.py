"""SPI frame helpers for the Raspberry Pi host."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import time
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


class NackReason(IntEnum):
    """Mirrors SpiProtocol_Result in Arm_Sensor_Hub/App/Inc/spi_protocol.h.

    The NACK status field carries this code, so decoding it turns an opaque
    rejection into a named cause.
    """

    OK = 0
    BAD_MAGIC = 1
    BAD_VERSION = 2
    BAD_LENGTH = 3
    BAD_CRC = 4
    BAD_SEQUENCE = 5
    BAD_MESSAGE = 6
    BAD_TIME_SYNC = 7
    BAD_STATE = 8

    @classmethod
    def describe(cls, code: int) -> str:
        try:
            return cls(code).name
        except ValueError:
            return f'UNKNOWN({code})'


_last_seed = 0

# Separation forced between two seeds issued by one process when the clock has
# not advanced enough on its own. Chosen far above the transaction count any
# single session consumes, so a later transmitter cannot land inside the span
# an earlier one already used.
_SEED_STRIDE = 1_000_000


def initial_sequence() -> int:
    """Seed for a host transmitter's sequence counter.

    The interface contract (SPI_SYSTEM_INTERFACE.md section 6) requires `seq`
    to increment monotonically *per transmitter*, and the firmware enforces
    this by rejecting any request that is not strictly newer than the last it
    accepted (SPI_PROTOCOL_BAD_SEQUENCE). The firmware's high-water mark lives
    in RAM and survives until the STM32 is power-cycled, but a host process
    starting from a fixed value resets on every run -- so the second and all
    later runs against a still-powered STM32 would be NACKed for the whole
    span the previous run already consumed.

    Wall-clock milliseconds keep the seed ahead of that high-water mark across
    restarts without persisting any state: each new process starts roughly
    `elapsed_ms` beyond the last one, which outpaces the transaction rate the
    bench sustains (pacing holds it near 100/s; see DEFAULT_RETRY_DELAY_S).
    Truncation to 32 bits wraps about every 50 days, which the firmware's
    wrap-tolerant half-space comparison handles.

    Within a single process the clock alone is not enough -- two transmitters
    built moments apart can be separated by fewer milliseconds than the first
    consumed sequences -- so seeds are additionally forced apart by
    `_SEED_STRIDE`.
    """
    global _last_seed
    seed = (time.time_ns() // 1_000_000) & 0xFFFFFFFF
    if _last_seed and not _is_newer(seed, _last_seed + _SEED_STRIDE):
        seed = (_last_seed + _SEED_STRIDE) & 0xFFFFFFFF
    _last_seed = seed
    return seed or 1


def _is_newer(candidate: int, previous: int) -> bool:
    """Wrap-tolerant ordering matching SpiProtocol_IsNewer in the firmware."""
    return candidate != previous and ((candidate - previous) & 0xFFFFFFFF) < 0x80000000


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


TIME_SYNC_PAYLOAD_BYTES = 16
TIME_SYNC_SCHEMA_VERSION = 1
COMMAND_REPLY_PAYLOAD_BYTES = 12
COMMAND_REPLY_SCHEMA_VERSION = 1


def encode_time_sync_payload(pi_time_us: int, sync_seq: int, flags: int = 0) -> bytes:
    """Encode TIME_SYNC payload per SPI_PAYLOAD_SCHEMA.md.

    Args:
        pi_time_us: Pi time in microseconds (uint64)
        sync_seq: Monotonic synchronization sequence (uint32)
        flags: Control flags (uint16, default 0)

    Returns:
        16-byte little-endian payload

    Raises:
        ValueError: if values exceed type limits
    """
    if not 0 <= pi_time_us <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError(f'pi_time_us must be uint64, got {pi_time_us}')
    if not 0 <= sync_seq <= 0xFFFFFFFF:
        raise ValueError(f'sync_seq must be uint32, got {sync_seq}')
    if not 0 <= flags <= 0xFFFF:
        raise ValueError(f'flags must be uint16, got {flags}')

    return struct.pack('<BBHQI',
                       TIME_SYNC_SCHEMA_VERSION,  # schema_ver
                       0,                          # reserved
                       flags,                      # flags
                       pi_time_us,                 # pi_time_us
                       sync_seq)                   # sync_seq


def decode_command_reply(payload: bytes) -> tuple:
    """Decode ACK/NACK response payload.

    Args:
        payload: ACK/NACK payload (at least 12 bytes)

    Returns:
        (request_type, status_code, request_seq, detail_code)

    Raises:
        ValueError: if payload size < 12 or schema != 1
    """
    if len(payload) < COMMAND_REPLY_PAYLOAD_BYTES:
        raise ValueError(f'ACK/NACK payload must be >={COMMAND_REPLY_PAYLOAD_BYTES} bytes, got {len(payload)}')

    schema, req_type, status, req_seq, detail = struct.unpack_from('<BBHII', payload, 0)
    if schema != COMMAND_REPLY_SCHEMA_VERSION:
        raise ValueError(f'Expected schema {COMMAND_REPLY_SCHEMA_VERSION}, got {schema}')

    return (req_type, status, req_seq, detail)


def extract_time_sync_from_ack_nack(payload: bytes) -> tuple[int, int] | None:
    """Extract TIME_SYNC pi_time_us and sync_seq from an ACK/NACK response.

    When a TIME_SYNC request is acknowledged, the response echoes the
    pi_time_us and sync_seq from the request payload for correlation.
    This is used to compute the TIME_SYNC offset and track uncertainty bounds.

    Args:
        payload: ACK/NACK payload (minimum 12 bytes, typically 28+ for TIME_SYNC)

    Returns:
        (pi_time_us, sync_seq) if TIME_SYNC echo is present, else None
        where pi_time_us is uint64 and sync_seq is uint32

    Raises:
        ValueError: if payload < 12 bytes
    """
    if len(payload) < 12 + TIME_SYNC_PAYLOAD_BYTES:
        return None

    try:
        # TIME_SYNC echo starts at offset 12 (after command_reply header)
        # pi_time_us is at offset 12+4=16 (after schema_version, reserved, flags)
        pi_time_us = struct.unpack_from('<Q', payload, 12 + 4)[0]
        # sync_seq is at offset 12+12=24
        sync_seq = struct.unpack_from('<I', payload, 12 + 12)[0]
        return (pi_time_us, sync_seq)
    except struct.error:
        return None


def crc32_iso_hdlc(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF
