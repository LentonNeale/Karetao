"""High-level Raspberry Pi SPI device access."""

from __future__ import annotations

from .spi_bus import SpiBus
from .spi_protocol import MessageType, SpiFrame, VersionInfo


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

    def get_version(self, seq: int | None = None, max_transactions: int = 8) -> VersionInfo:
        """Request the firmware build identity for evidence records.

        Transactions are pipelined (SPI_SYSTEM_INTERFACE.md section 4): the
        device stages a reply only after the request has been clocked in, so
        the VERSION frame arrives on a later transfer. Further transactions
        clock it out, and the correlation field confirms which request it
        answers rather than trusting arrival order.
        """
        request_seq = self.next_sequence() if seq is None else seq
        response = self.transact(SpiFrame(
            message_type=MessageType.GET_VERSION, seq=request_seq, payload=bytes([1])))

        for _ in range(max_transactions):
            if response.message_type is MessageType.VERSION:
                info = VersionInfo.decode(response.payload)
                if info.response_to_seq == request_seq:
                    return info
            response = self.transact(SpiFrame(
                message_type=MessageType.GET_STATUS, seq=self.next_sequence(), payload=bytes([1])))

        raise TimeoutError(
            f'no VERSION response correlated to seq {request_seq} within {max_transactions} transactions')
