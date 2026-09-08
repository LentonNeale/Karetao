"""High-level Raspberry Pi SPI device access scaffold."""

from __future__ import annotations

from .spi_bus import SpiBus
from .spi_protocol import MessageType, SpiFrame


class SpiDevice:
    def __init__(self, bus: SpiBus) -> None:
        self.bus = bus

    def transact(self, request: SpiFrame) -> SpiFrame:
        response = self.bus.transfer(request.encode())
        return SpiFrame.decode(response)

    def get_status(self, seq: int) -> SpiFrame:
        return self.transact(SpiFrame(message_type=MessageType.GET_STATUS, seq=seq))
