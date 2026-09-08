"""SPI frame helpers for the Raspberry Pi host.

TODO: confirm whether the production host always transfers fixed 512-byte buffers or
uses a transport wrapper around the canonical frame sizes from docs/protocols/spi-contract.md.
TODO: confirm final supported message coverage before adding SET_MOTOR_COMMAND payload helpers.
"""

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

        header = _HEADER_STRUCT.pack(
            MAGIC,
            self.protocol_version,
            int(self.message_type),
            len(payload),
            self.seq,
            self.frame_time_us,
        )
        crc = crc32_iso_hdlc(header + payload)
        frame = header + payload + struct.pack('<I', crc)
        if len(frame) > MAX_FRAME_BYTES:
            raise ValueError('frame exceeds SPI contract limit')
        return frame

    @classmethod
    def decode(cls, frame: bytes) -> 'SpiFrame':
        raw = bytes(frame)
        if len(raw) < HEADER_SIZE + CRC_SIZE:
            raise ValueError('frame too short')
        if len(raw) > MAX_FRAME_BYTES:
            raise ValueError('frame exceeds SPI contract limit')

        magic, protocol_version, message_type, payload_len, seq, frame_time_us = _HEADER_STRUCT.unpack(
            raw[:HEADER_SIZE]
        )
        if magic != MAGIC:
            raise ValueError('invalid frame magic')

        expected_length = HEADER_SIZE + payload_len + CRC_SIZE
        if len(raw) != expected_length:
            raise ValueError('frame length does not match payload length')

        expected_crc = struct.unpack('<I', raw[-CRC_SIZE:])[0]
        actual_crc = crc32_iso_hdlc(raw[:-CRC_SIZE])
        if actual_crc != expected_crc:
            raise ValueError('invalid frame crc')

        return cls(
            message_type=MessageType(message_type),
            seq=seq,
            frame_time_us=frame_time_us,
            payload=raw[HEADER_SIZE:-CRC_SIZE],
            protocol_version=protocol_version,
        )


def crc32_iso_hdlc(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF
