"""Raspberry Pi SPI scaffold aligned to the Arm Sensor Hub SPI contract."""

from .spi_bus import SpiBackend, SpiBus, SpiBusConfig
from .spi_device import SpiDevice
from .spi_protocol import (
    CRC_SIZE,
    HEADER_SIZE,
    MAGIC,
    MAX_FRAME_BYTES,
    MAX_PAYLOAD_BYTES,
    PROTOCOL_VERSION,
    MessageType,
    SpiFrame,
    crc32_iso_hdlc,
)

__all__ = [
    'CRC_SIZE',
    'HEADER_SIZE',
    'MAGIC',
    'MAX_FRAME_BYTES',
    'MAX_PAYLOAD_BYTES',
    'PROTOCOL_VERSION',
    'MessageType',
    'SpiBackend',
    'SpiBus',
    'SpiBusConfig',
    'SpiDevice',
    'SpiFrame',
    'crc32_iso_hdlc',
]
