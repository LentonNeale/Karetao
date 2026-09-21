"""High-level Raspberry Pi SPI device access."""

from __future__ import annotations

import struct
import time

from .spi_bus import SpiBus
from .spi_protocol import MessageType, NackReason, SpiFrame, VersionInfo, initial_sequence

# Without DATA_READY wired into the caller, transactions clocked back-to-back
# can outrun the firmware's bare-metal main-loop re-arm and come back
# stale/corrupted (observed on the bench: first transaction after bus.open()
# is often shifted by one byte, and unpaced follow-ups return zeroed frames).
# This default gives the main-loop time to service each request.
DEFAULT_RETRY_DELAY_S = 0.01

_NACK_HINTS = {
    'BAD_SEQUENCE': 'The firmware only accepts strictly increasing sequence numbers and keeps '
                    'its high-water mark until power-cycled, so a host that restarts its '
                    'counter below that mark is refused; see initial_sequence().',
}


class SpiDevice:
    def __init__(self, bus: SpiBus, start_sequence: int | None = None) -> None:
        self.bus = bus
        self._next_sequence = initial_sequence() if start_sequence is None else start_sequence

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

    def get_version(self, seq: int | None = None, max_transactions: int = 8,
                    retry_delay_s: float = DEFAULT_RETRY_DELAY_S) -> VersionInfo:
        """Request the firmware build identity for evidence records.

        Transactions are pipelined (SPI_SYSTEM_INTERFACE.md section 4): the
        device stages a reply only after the request has been clocked in, so
        the VERSION frame arrives on a later transfer. Further transactions
        clock it out, and the correlation field confirms which request it
        answers rather than trusting arrival order.

        A decode failure on any single transfer is treated as "not yet"
        rather than a fatal error: without DATA_READY pacing, an individual
        transfer can come back corrupted (see module docstring), and the
        firmware will still answer a retried request.
        """
        request_seq = self.next_sequence() if seq is None else seq
        rejection: str | None = None
        try:
            self.transact(SpiFrame(
                message_type=MessageType.GET_VERSION, seq=request_seq, payload=bytes([1])))
        except ValueError:
            pass  # result is unused either way; this call only needs to get the request onto the wire

        for attempt in range(max_transactions):
            if attempt > 0:
                time.sleep(retry_delay_s)
            try:
                response = self.transact(SpiFrame(
                    message_type=MessageType.GET_STATUS, seq=self.next_sequence(), payload=bytes([1])))
            except ValueError:
                continue
            if response.message_type is MessageType.VERSION:
                try:
                    info = VersionInfo.decode(response.payload)
                except ValueError:
                    continue
                if info.response_to_seq == request_seq:
                    return info
            elif response.message_type is MessageType.NACK and len(response.payload) >= 8:
                # ACK/NACK payload: schema, echoed type, status u16 @2, request_seq u32 @4
                # (SPI_PAYLOAD_SCHEMA.md). Remember why our own request was refused.
                status, nacked_seq = struct.unpack_from('<HI', response.payload, 2)
                if nacked_seq == request_seq:
                    rejection = NackReason.describe(status)

        if rejection is not None:
            raise RuntimeError(
                f'firmware rejected GET_VERSION seq {request_seq} with {rejection}. '
                f'{_NACK_HINTS.get(rejection, "")}'.strip())
        raise TimeoutError(
            f'no VERSION response correlated to seq {request_seq} within {max_transactions} transactions')
