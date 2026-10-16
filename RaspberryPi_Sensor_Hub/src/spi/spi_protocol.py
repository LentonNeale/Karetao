"""SPI frame helpers for the Raspberry Pi host."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import threading
import time
from typing import Optional
import zlib

# Contract constants (SPI_SYSTEM_INTERFACE.md section 3). Each is defined once here;
# every other module refers to these names. The C side's single home is
# Arm_Sensor_Hub/App/Inc/spi_payload_layout.h, and the shared golden frames in
# shared/test-vectors/spi assert that the two agree byte for byte.
MAGIC = 0xA55A
PROTOCOL_VERSION = 1
CRC_SIZE = 4
MAX_FRAME_BYTES = 512
# magic u16, protocol_version u8, message_type u8, payload_len u16, seq u32, frame_time_us u64
HEADER_STRUCT = struct.Struct('<HBBHIQ')
HEADER_SIZE = HEADER_STRUCT.size
MAX_PAYLOAD_BYTES = MAX_FRAME_BYTES - HEADER_SIZE - CRC_SIZE


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
    if _last_seed and not is_newer_sequence(seed, _last_seed + _SEED_STRIDE):
        seed = (_last_seed + _SEED_STRIDE) & 0xFFFFFFFF
    _last_seed = seed
    return seed or 1


def is_newer_sequence(candidate: int, previous: int) -> bool:
    """Wrap-tolerant ordering matching SpiProtocol_IsNewer in the firmware."""
    return candidate != previous and ((candidate - previous) & 0xFFFFFFFF) < 0x80000000


class Sequencer:
    """Supplier of request `seq` values for one host transmitter.

    The contract makes `seq` monotonic per transmitter (SPI_SYSTEM_INTERFACE.md section 6) and
    ruling R3 makes the Pi one transmitter: every session in a process draws from the one
    `process_sequencer()`, so two sessions never both start from the seed and race the
    firmware's high-water mark. Zero is skipped so an unset correlation field (zero in an
    unsolicited payload) stays distinguishable from a real request. R3's bounded jump after
    BAD_SEQUENCE is added here by #87, with the firmware's first-sequence acceptance.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        start = initial_sequence() if seed is None else seed
        if not 0 <= start <= 0xFFFFFFFF:
            raise ValueError('sequence seed exceeds uint32 range')
        self._next = start or 1
        self._lock = threading.Lock()

    def next(self) -> int:
        with self._lock:
            sequence = self._next
            self._next = (sequence + 1) & 0xFFFFFFFF or 1
            return sequence

    def peek(self) -> int:
        """The sequence the next call to next() returns."""
        with self._lock:
            return self._next


_process_sequencer: Optional[Sequencer] = None
_process_sequencer_lock = threading.Lock()


def process_sequencer() -> Sequencer:
    """The process-wide Sequencer, created on first use and seeded by initial_sequence()."""
    global _process_sequencer
    with _process_sequencer_lock:
        if _process_sequencer is None:
            _process_sequencer = Sequencer()
        return _process_sequencer


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
        header = HEADER_STRUCT.pack(MAGIC, self.protocol_version, int(self.message_type),
                                     len(payload), self.seq, self.frame_time_us)
        crc = crc32_iso_hdlc(header + payload)
        return header + payload + struct.pack('<I', crc)

    @classmethod
    def decode(cls, frame: bytes) -> 'SpiFrame':
        raw = bytes(frame)
        if len(raw) < HEADER_SIZE + CRC_SIZE or len(raw) > MAX_FRAME_BYTES:
            raise ValueError('invalid SPI frame size')

        magic, protocol_version, message_type, payload_len, seq, frame_time_us = HEADER_STRUCT.unpack(raw[:HEADER_SIZE])
        if magic != MAGIC:
            raise ValueError('invalid frame magic')
        if protocol_version != PROTOCOL_VERSION:
            raise ValueError('unsupported protocol version')

        expected_length = HEADER_SIZE + payload_len + CRC_SIZE
        if expected_length > MAX_FRAME_BYTES or len(raw) < expected_length:
            raise ValueError('frame length does not match payload length')

        # SPI transport is fixed at MAX_FRAME_BYTES. The wire frame itself ends at
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


VERSION_SCHEMA_VERSION = 1
BUILD_FLAG_DIRTY = 0x01
# schema u8, protocol_version u8, major u8, minor u8, patch u8, build_flags u8, reserved u16,
# response_to_seq u32, git_hash_abbrev u32, commit_epoch_secs u32
_VERSION_STRUCT = struct.Struct('<BBBBBBHIII')
VERSION_PAYLOAD_BYTES = _VERSION_STRUCT.size
VERSION_OFFSET_RESPONSE_TO_SEQ = struct.calcsize('<BBBBBBH')


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

    def encode(self) -> bytes:
        """The VERSION payload bytes; the fake firmware builds its reply with this."""
        try:
            return _VERSION_STRUCT.pack(self.schema_version, self.protocol_version, self.firmware_major,
                                        self.firmware_minor, self.firmware_patch, self.build_flags, 0,
                                        self.response_to_seq, self.git_hash_abbrev, self.commit_epoch_secs)
        except struct.error as exc:
            raise ValueError(f'VERSION field out of range: {exc}') from exc

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


SENSOR_VALIDITY_SAMPLE_VALID = 0x0001
SENSOR_VALIDITY_COMMUNICATION_ERROR = 0x0002
SENSOR_VALIDITY_MAGNET_NOT_DETECTED = 0x0004
SENSOR_VALIDITY_MAGNET_TOO_WEAK = 0x0008
SENSOR_VALIDITY_MAGNET_TOO_STRONG = 0x0010
# Bit 5 (timestamp synchronized) is retired by ruling R16: the firmware writes it zero and it is
# reserved, like bits 7-15. A stale sample arrives with SAMPLE_VALID clear and its last values
# and acquisition timestamp kept (SPI_PAYLOAD_SCHEMA.md, SNAPSHOT).
SENSOR_VALIDITY_NOT_FITTED = 0x0040
# sensor_id u8, status u8, validity_flags u16, measurement_timestamp_us u64, raw_angle u16,
# processed_angle_mdeg i32, magnitude u16, agc u8, reserved u8, reserved_2 u16
_SENSOR_RECORD_STRUCT = struct.Struct('<BBHQHiHBBH')
SENSOR_RECORD_BYTES = _SENSOR_RECORD_STRUCT.size
# Snapshot prefix: schema u8, sensor_count u8, motor_count u8, reserved u8, flags u16,
# dropped_snapshot_count_low u16, response_to_seq u32 (spi_payload_layout.h SPI_SNAPSHOT_*)
_SNAPSHOT_PREFIX_STRUCT = struct.Struct('<BBBBHHI')
SNAPSHOT_PREFIX_BYTES = _SNAPSHOT_PREFIX_STRUCT.size
SNAPSHOT_SCHEMA_VERSION = 1
SNAPSHOT_OFFSET_SCHEMA_VERSION = 0
SNAPSHOT_OFFSET_SENSOR_COUNT = 1
SNAPSHOT_OFFSET_RESPONSE_TO_SEQ = struct.calcsize('<BBBBHH')


@dataclass(frozen=True)
class SensorRecord:
    """Decoded 24-byte sensor record of a SNAPSHOT (0x01) payload.

    Layout: spi_payload_layout.h (SPI_SENSOR_RECORD_*) and SPI_PAYLOAD_SCHEMA.md.
    """

    sensor_id: int
    status: int
    validity_flags: int
    measurement_timestamp_us: int
    raw_angle: int
    processed_angle_mdeg: int
    magnitude: int
    agc: int

    @classmethod
    def decode(cls, record: bytes) -> 'SensorRecord':
        if len(record) != SENSOR_RECORD_BYTES:
            raise ValueError('unexpected sensor record size')
        (sensor_id, status, validity_flags, timestamp_us, raw_angle, processed_angle_mdeg,
         magnitude, agc, reserved, reserved_2) = _SENSOR_RECORD_STRUCT.unpack(record)
        if reserved or reserved_2:
            raise ValueError('non-zero reserved bytes in sensor record')
        return cls(sensor_id=sensor_id, status=status, validity_flags=validity_flags,
                   measurement_timestamp_us=timestamp_us, raw_angle=raw_angle,
                   processed_angle_mdeg=processed_angle_mdeg, magnitude=magnitude, agc=agc)

    @property
    def is_valid(self) -> bool:
        return bool(self.validity_flags & SENSOR_VALIDITY_SAMPLE_VALID)

    @property
    def is_not_fitted(self) -> bool:
        """True when the axis has no encoder in the commissioning table."""
        return bool(self.validity_flags & SENSOR_VALIDITY_NOT_FITTED)


def decode_snapshot_sensor_records(payload: bytes) -> list[SensorRecord]:
    """Decode the sensor records of a SNAPSHOT payload (sensor_count at offset 1)."""
    if len(payload) < SNAPSHOT_PREFIX_BYTES:
        raise ValueError('SNAPSHOT payload shorter than its prefix')
    sensor_count = payload[SNAPSHOT_OFFSET_SENSOR_COUNT]
    end = SNAPSHOT_PREFIX_BYTES + sensor_count * SENSOR_RECORD_BYTES
    if len(payload) < end:
        raise ValueError('SNAPSHOT payload shorter than its sensor records')
    return [SensorRecord.decode(payload[offset:offset + SENSOR_RECORD_BYTES])
            for offset in range(SNAPSHOT_PREFIX_BYTES, end, SENSOR_RECORD_BYTES)]


TIME_SYNC_PAYLOAD_BYTES = 16
TIME_SYNC_SCHEMA_VERSION = 1
# ACK/NACK: schema u8, request_type u8, status_code u16, request_seq u32, detail_code u32
_COMMAND_REPLY_STRUCT = struct.Struct('<BBHII')
COMMAND_REPLY_PAYLOAD_BYTES = _COMMAND_REPLY_STRUCT.size
COMMAND_REPLY_SCHEMA_VERSION = 1
COMMAND_REPLY_OFFSET_REQUEST_SEQ = struct.calcsize('<BBH')
# DIAGNOSTIC (0x03): schema u8, health_level u8, reserved u16, diagnostic_timestamp_us u64,
# then response_to_seq u32 (SPI_PAYLOAD_SCHEMA.md); no decoder exists on this side yet.
DIAGNOSTIC_OFFSET_RESPONSE_TO_SEQ = struct.calcsize('<BBHQ')


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


def encode_command_reply(request_type: int, status_code: int, request_seq: int, detail_code: int = 0) -> bytes:
    """ACK/NACK payload as SpiProtocol_BuildCommandReply writes it (SPI_PAYLOAD_SCHEMA.md)."""
    try:
        return _COMMAND_REPLY_STRUCT.pack(COMMAND_REPLY_SCHEMA_VERSION, request_type, status_code,
                                          request_seq, detail_code)
    except struct.error as exc:
        raise ValueError(f'ACK/NACK field out of range: {exc}') from exc


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

    schema, req_type, status, req_seq, detail = _COMMAND_REPLY_STRUCT.unpack_from(payload, 0)
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
    if len(payload) < COMMAND_REPLY_PAYLOAD_BYTES + TIME_SYNC_PAYLOAD_BYTES:
        return None

    try:
        # The TIME_SYNC echo follows the command reply; pi_time_us sits after
        # schema_version, reserved and flags (4 bytes), sync_seq after pi_time_us.
        echo = COMMAND_REPLY_PAYLOAD_BYTES
        pi_time_us = struct.unpack_from('<Q', payload, echo + 4)[0]
        sync_seq = struct.unpack_from('<I', payload, echo + 12)[0]
        return (pi_time_us, sync_seq)
    except struct.error:
        return None


def crc32_iso_hdlc(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF
