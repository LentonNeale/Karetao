"""High-level Raspberry Pi SPI device access."""

from __future__ import annotations

from .spi_bus import SpiBus
from .spi_protocol import MessageType, SpiFrame


class SpiDevice:
    def __init__(self, bus: SpiBus) -> None:
        self.bus = bus
        self._next_sequence = 1

    def transact(self, request: SpiFrame) -> SpiFrame:
        """Clock one fixed-size transaction and decode the staged response."""
        response = self.bus.transfer(request.encode())
        return SpiFrame.decode(response)

    def next_sequence(self) -> int:
        sequence = self._next_sequence
        self._next_sequence = (self._next_sequence + 1) & 0xFFFFFFFF
        return sequence

    def get_status(self, seq: int | None = None) -> SpiFrame:
        request = SpiFrame(
            message_type=MessageType.GET_STATUS,
            seq=self.next_sequence() if seq is None else seq,
        )
        return self.transact(request)
