"""A firmware-rules fake of the STM32 SPI slave, as one SpiBackend adapter.

It enforces the rules the Pi depends on, copied from the as-built firmware, and reproduces the
shared golden frames byte for byte (tests/spi/test_fake_backend.py):

- one-transaction reply delay: transaction N returns the frame staged before it, and request
  N's reply is staged for transaction N+1 (SPI_SYSTEM_INTERFACE.md section 4;
  `SpiSlaveService_ProcessRequestFrame` stages exactly one response per request);
- the boot DIAGNOSTIC as the first staged frame (`SpiProtocol_BuildBootStatus`);
- request checks in `SpiProtocol_ValidateRequest`'s order: magic, version, length, CRC, sequence
  against the high-water mark, message type, TIME_SYNC payload. The NACK names the request type
  and seq read from their header offsets, whatever else is wrong with the frame;
- BAD_STATE while the service is not active (`SpiSlaveService_RequestAllowed`; TIME_SYNC is still
  allowed), checked after those and without moving the high-water mark;
- SNAPSHOT for GET_SNAPSHOT while a snapshot is staged (its `response_to_seq` set to the request
  seq), VERSION for GET_VERSION, ACK for every other accepted request;
- garbage mode: nothing is armed, so the Pi clocks idle MISO and the request is never received.

It lives in `src/spi`, not in the tests, so the tools can run against it too (the `--fake` mode
of the timing harness and the two probes). Two simplifications. The as-built service also stops
arming DMA while it is not active, so on today's hardware a not-active slave looks like garbage mode; the fake answers BAD_STATE so the
Pi's handling of that NACK can be tested. And the fake does not judge a TIME_SYNC sample, which
the firmware's time service may still NACK (deprecated by Issue #12).
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
import time
from typing import Callable, Optional

from .spi_protocol import (
    CRC_SIZE,
    HEADER_SIZE,
    HEADER_STRUCT,
    MAGIC,
    MAX_FRAME_BYTES,
    MAX_PAYLOAD_BYTES,
    PROTOCOL_VERSION,
    SNAPSHOT_OFFSET_RESPONSE_TO_SEQ,
    SNAPSHOT_PREFIX_BYTES,
    TIME_SYNC_PAYLOAD_BYTES,
    TIME_SYNC_SCHEMA_VERSION,
    VERSION_SCHEMA_VERSION,
    MessageType,
    NackReason,
    SpiFrame,
    VersionInfo,
    crc32_iso_hdlc,
    encode_command_reply,
    is_newer_sequence,
)

# Stand-in for what the Pi reads from a slave with nothing armed. The real idle level of MISO
# is not characterised; any bytes that fail to decode serve the tests.
IDLE_MISO = b'\xff' * MAX_FRAME_BYTES

_ACCEPTED_REQUESTS = frozenset({MessageType.GET_SNAPSHOT, MessageType.GET_STATUS,
                                MessageType.TIME_SYNC, MessageType.GET_VERSION})
_U32 = struct.Struct('<I')


@dataclass(frozen=True)
class FirmwareIdentity:
    """The VERSION reply's build facts. The default is the host-test fallback identity of
    firmware_version.h, which the shared golden frames carry (their README)."""

    major: int = 0
    minor: int = 1
    patch: int = 0
    build_flags: int = 0
    git_hash_abbrev: int = 0
    commit_epoch_secs: int = 0


class FakeFirmware:
    """The STM32 side of the link, behind the SpiBackend interface (spi_bus.SpiBackend).

    State is public so tests can set it up and check it: `next_tx_seq` (the seq the next
    response frame takes), `last_request_seq` (the high-water mark, None since boot), `active`
    and `garbage`. `results` lists the reason each received request was accepted (OK) or
    NACKed. `boot=False` starts with nothing staged, as if the boot frame had been consumed.
    """

    def __init__(self, *, next_tx_seq: int = 1, last_request_seq: Optional[int] = None,
                 clock_us: Optional[Callable[[], int]] = None, identity: FirmwareIdentity = FirmwareIdentity(),
                 active: bool = True, boot: bool = True) -> None:
        self.next_tx_seq = next_tx_seq
        self.last_request_seq = last_request_seq
        self.active = active
        self.garbage = False
        self.identity = identity
        self.results: list[NackReason] = []
        self._clock_us = clock_us if clock_us is not None else (lambda: time.monotonic_ns() // 1000)
        self._staged: Optional[bytes] = None
        self._snapshot: Optional[bytearray] = None
        if boot:
            self._staged = self._build_frame(MessageType.DIAGNOSTIC, b'')

    def open(self, config) -> None:
        return None

    def close(self) -> None:
        return None

    def transfer(self, tx_data: bytes) -> bytes:
        if len(tx_data) != MAX_FRAME_BYTES:
            raise ValueError(f'SPI transactions must be exactly {MAX_FRAME_BYTES} bytes')
        if self.garbage:
            return IDLE_MISO
        response = self._staged if self._staged is not None else IDLE_MISO
        self._staged = None
        self._receive(bytes(tx_data))
        return response

    @property
    def staged_frame(self) -> Optional[bytes]:
        """The 512 bytes the next transaction will clock out, or None when nothing is staged."""
        return self._staged

    def activate(self) -> None:
        self.active = True

    def publish_snapshot(self, payload: bytes) -> None:
        """Stage a snapshot for the next GET_SNAPSHOT (`SpiProtocol_SetUnsolicitedSnapshot`)."""
        if not SNAPSHOT_PREFIX_BYTES <= len(payload) <= MAX_PAYLOAD_BYTES:
            raise ValueError('snapshot payload length outside the SNAPSHOT limits')
        self._snapshot = bytearray(payload)

    def _receive(self, request: bytes) -> None:
        _, _, request_type, _, sequence, _ = HEADER_STRUCT.unpack_from(request)
        result = self._validate(request)
        if result is NackReason.OK and not self._allowed(request_type):
            result = NackReason.BAD_STATE
        self.results.append(result)
        if result is not NackReason.OK:
            payload = encode_command_reply(request_type, int(result), sequence)
            self._staged = self._build_frame(MessageType.NACK, payload)
            return

        self.last_request_seq = sequence
        if request_type == MessageType.GET_SNAPSHOT and self._snapshot is not None:
            _U32.pack_into(self._snapshot, SNAPSHOT_OFFSET_RESPONSE_TO_SEQ, sequence)
            self._staged = self._build_frame(MessageType.SNAPSHOT, bytes(self._snapshot))
            self._snapshot = None
        elif request_type == MessageType.GET_VERSION:
            identity = self.identity
            version = VersionInfo(schema_version=VERSION_SCHEMA_VERSION, protocol_version=PROTOCOL_VERSION,
                                  firmware_major=identity.major, firmware_minor=identity.minor,
                                  firmware_patch=identity.patch, build_flags=identity.build_flags,
                                  response_to_seq=sequence, git_hash_abbrev=identity.git_hash_abbrev,
                                  commit_epoch_secs=identity.commit_epoch_secs)
            self._staged = self._build_frame(MessageType.VERSION, version.encode())
        else:
            self._staged = self._build_frame(MessageType.ACK, encode_command_reply(request_type, 0, sequence))

    def _validate(self, request: bytes) -> NackReason:
        magic, version, request_type, length, sequence, _ = HEADER_STRUCT.unpack_from(request)
        if magic != MAGIC:
            return NackReason.BAD_MAGIC
        if version != PROTOCOL_VERSION:
            return NackReason.BAD_VERSION
        crc_offset = HEADER_SIZE + length
        if length > MAX_PAYLOAD_BYTES or crc_offset + CRC_SIZE > MAX_FRAME_BYTES:
            return NackReason.BAD_LENGTH
        if crc32_iso_hdlc(request[:crc_offset]) != _U32.unpack_from(request, crc_offset)[0]:
            return NackReason.BAD_CRC
        if self.last_request_seq is not None and not is_newer_sequence(sequence, self.last_request_seq):
            return NackReason.BAD_SEQUENCE
        if request_type not in _ACCEPTED_REQUESTS:
            return NackReason.BAD_MESSAGE
        if request_type == MessageType.TIME_SYNC and not (
                length == TIME_SYNC_PAYLOAD_BYTES and request[HEADER_SIZE] == TIME_SYNC_SCHEMA_VERSION):
            return NackReason.BAD_TIME_SYNC
        return NackReason.OK

    def _allowed(self, request_type: int) -> bool:
        return self.active or request_type == MessageType.TIME_SYNC

    def _build_frame(self, message_type: MessageType, payload: bytes) -> bytes:
        sequence = self.next_tx_seq
        self.next_tx_seq = (sequence + 1) & 0xFFFFFFFF
        frame = SpiFrame(message_type=message_type, seq=sequence, frame_time_us=self._clock_us(), payload=payload)
        return frame.encode().ljust(MAX_FRAME_BYTES, b'\x00')


class FakeDataReady:
    """Fake satisfying data_ready.DataReadyLike, so pacing is testable without a GPIO chip.

    With `ready_sequence`, each wait returns the next value (False once it runs out);
    otherwise every wait returns `always_ready`.
    """

    def __init__(self, ready_sequence=None, always_ready=True) -> None:
        self._ready_sequence = list(ready_sequence) if ready_sequence is not None else None
        self._always_ready = always_ready
        self.wait_calls = 0

    def is_ready(self) -> bool:
        return self._always_ready

    def wait_for_ready(self, timeout_s: float) -> bool:
        self.wait_calls += 1
        if self._ready_sequence is not None:
            return self._ready_sequence.pop(0) if self._ready_sequence else False
        return self._always_ready
