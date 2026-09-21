"""Raspberry Pi SPI scaffold aligned to the Arm Sensor Hub SPI contract."""

from .spi_bus import SpiBackend, SpiBus, SpiBusConfig
from .spi_device import SpiDevice
from .spi_protocol import (
    BUILD_FLAG_DIRTY,
    CRC_SIZE,
    HEADER_SIZE,
    MAGIC,
    MAX_FRAME_BYTES,
    MAX_PAYLOAD_BYTES,
    PROTOCOL_VERSION,
    VERSION_PAYLOAD_BYTES,
    MessageType,
    SpiFrame,
    VersionInfo,
    crc32_iso_hdlc,
)

__all__ = [
    'BUILD_FLAG_DIRTY',
    'CRC_SIZE',
    'HEADER_SIZE',
    'MAGIC',
    'MAX_FRAME_BYTES',
    'MAX_PAYLOAD_BYTES',
    'PROTOCOL_VERSION',
    'VERSION_PAYLOAD_BYTES',
    'MessageType',
    'SpiBackend',
    'SpiBus',
    'SpiBusConfig',
    'SpiDevice',
    'SpiFrame',
    'VersionInfo',
    'crc32_iso_hdlc',
]
