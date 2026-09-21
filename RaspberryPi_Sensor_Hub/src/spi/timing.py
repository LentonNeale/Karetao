"""Per-transaction SPI timing measurement.

The transaction model is pipelined (SPI_SYSTEM_INTERFACE.md section 4): the
response clocked out during transaction N answers a request the host sent
earlier. Wire time for one transfer is therefore *not* request-to-response
latency, and the two must not be conflated. Every response carries a
correlation field identifying the request it answers, so this module records
the transfer duration and the reconstructed round-trip separately and leaves
both in the log.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
import struct
import time
from typing import Optional

from .data_ready import DataReadyLike
from .spi_bus import SpiBus
from .spi_protocol import MessageType, SpiFrame, initial_sequence

try:
    _INTERVAL_CLOCK = time.CLOCK_MONOTONIC_RAW
except AttributeError:  # pragma: no cover - non-Linux fallback
    _INTERVAL_CLOCK = time.CLOCK_MONOTONIC

_U16 = struct.Struct('<H')
_U32 = struct.Struct('<I')

# Payload offset of the field correlating a response to its request. ACK/NACK
# name it request_seq, the others response_to_seq (SPI_PAYLOAD_SCHEMA.md).
_CORRELATION_OFFSETS = {
    MessageType.ACK: 4,
    MessageType.NACK: 4,
    MessageType.SNAPSHOT: 8,
    MessageType.VERSION: 8,
    MessageType.DIAGNOSTIC: 12,
}

# Bound the outstanding-request table so a firmware that never correlates
# cannot grow it without limit during a long soak.
_MAX_PENDING = 4096


def now_ns() -> int:
    return time.clock_gettime_ns(_INTERVAL_CLOCK)


def correlated_request_seq(frame: SpiFrame) -> Optional[int]:
    offset = _CORRELATION_OFFSETS.get(frame.message_type)
    if offset is None or len(frame.payload) < offset + 4:
        return None
    return _U32.unpack_from(frame.payload, offset)[0]


def nack_codes(frame: SpiFrame) -> tuple[Optional[int], Optional[int]]:
    if frame.message_type is not MessageType.NACK or len(frame.payload) < 12:
        return (None, None)
    return (_U16.unpack_from(frame.payload, 2)[0], _U32.unpack_from(frame.payload, 8)[0])


@dataclass(frozen=True)
class TransactionRecord:
    """One clocked 512-byte transaction. Durations are nanoseconds.

    DATA_READY timing fields (microseconds):
    - data_ready_to_nss_low_us: DATA_READY rise to NSS fall (transfer start latency)
    - nss_high_to_data_ready_low_us: NSS rise to DATA_READY fall (pipelined latency)
    - data_ready_interval_us: Time between consecutive DATA_READY rising edges
    """

    index: int
    block_id: str
    request_seq: int
    request_type: str
    t_mono_ns: int
    t_realtime_ns: int
    encode_ns: int
    transfer_ns: int
    decode_ns: int
    total_ns: int
    ok: bool
    error: str = ''
    response_type: str = ''
    response_seq: Optional[int] = None
    response_frame_time_us: Optional[int] = None
    hub_delta_us: Optional[int] = None
    correlated_seq: Optional[int] = None
    round_trip_ns: Optional[int] = None
    nack_status_code: Optional[int] = None
    nack_detail_code: Optional[int] = None
    data_ready_wait_ns: Optional[int] = None
    data_ready_timed_out: bool = False
    time_sync_seq: Optional[int] = None
    time_sync_status: Optional[int] = None
    data_ready_to_nss_low_us: Optional[int] = None
    nss_high_to_data_ready_low_us: Optional[int] = None
    data_ready_interval_us: Optional[int] = None

    def as_row(self) -> dict:
        return asdict(self)

    def data_ready_latency_ms(self) -> Optional[float]:
        """Latency from DATA_READY to transfer start (ms).

        Converts data_ready_to_nss_low_us from microseconds to milliseconds.
        """
        if self.data_ready_to_nss_low_us is None:
            return None
        return self.data_ready_to_nss_low_us / 1000.0


CSV_FIELDS = list(TransactionRecord.__dataclass_fields__)


@dataclass
class SessionCounters:
    transactions: int = 0
    decode_failures: int = 0
    nacks: int = 0
    uncorrelated_responses: int = 0
    correlation_misses: int = 0
    data_ready_timeouts: int = 0


@dataclass
class TimingSession:
    """Clocks measured transactions over an open bus and correlates replies.

    `data_ready` is duck-typed (see data_ready.DataReadyLike) so tests can
    substitute a fake without a real GPIO chip. When set, the session waits
    for DATA_READY before each transfer instead of clocking unconditionally;
    a timeout does not abort the transaction, since the polling model
    (SPI_SYSTEM_INTERFACE.md section 7) is the documented fallback and the
    transaction still needs to be attempted either way. `min_interval_s`
    is a plain fixed-delay fallback for when no DATA_READY watcher is
    configured; it exists because the host has no other pacing mechanism
    and back-to-back transactions can outrun the firmware's bare-metal
    main-loop re-arm (observed on the bench: transactions clocked with no
    gap between them return stale/zeroed frames).
    """

    bus: SpiBus
    block_id: str = ''
    data_ready: Optional[DataReadyLike] = None
    data_ready_timeout_s: float = 0.1
    min_interval_s: float = 0.0
    start_sequence: Optional[int] = None
    counters: SessionCounters = field(default_factory=SessionCounters)

    def __post_init__(self) -> None:
        self._seq = initial_sequence() if self.start_sequence is None else self.start_sequence
        self._index = 0
        self._pending: dict[int, int] = {}
        self._previous_hub_time_us: Optional[int] = None
        self._last_transfer_end_ns: Optional[int] = None

    def reset_counters(self) -> None:
        """Discard counts accumulated during warmup."""
        self.counters = SessionCounters()

    def next_sequence(self) -> int:
        sequence = self._seq
        # Sequence must strictly increase or the firmware rejects it as stale;
        # zero is skipped so an unset correlation field stays distinguishable.
        self._seq = (self._seq + 1) & 0xFFFFFFFF or 1
        return sequence

    def _pace(self) -> tuple[Optional[int], bool]:
        """Wait before clocking the next transfer. Returns (wait_ns, timed_out).

        Neither path aborts the transaction on timeout: DATA_READY not
        asserting yet is expected under the documented polling fallback
        (SPI_SYSTEM_INTERFACE.md section 7), and a fixed delay has no
        failure mode to report.
        """
        if self.data_ready is not None:
            wait_start = now_ns()
            became_ready = self.data_ready.wait_for_ready(self.data_ready_timeout_s)
            return (now_ns() - wait_start, not became_ready)
        if self.min_interval_s > 0 and self._last_transfer_end_ns is not None:
            remaining_s = self.min_interval_s - (now_ns() - self._last_transfer_end_ns) / 1e9
            if remaining_s > 0:
                time.sleep(remaining_s)
        return (None, False)

    def transact(self, message_type: MessageType, payload: bytes = b'') -> TransactionRecord:
        sequence = self.next_sequence()
        request = SpiFrame(message_type=message_type, seq=sequence, payload=payload)

        data_ready_wait_ns, data_ready_timed_out = self._pace()
        if data_ready_timed_out:
            self.counters.data_ready_timeouts += 1

        t_realtime = time.clock_gettime_ns(time.CLOCK_REALTIME)
        t0 = now_ns()
        encoded = request.encode()
        t1 = now_ns()
        raw = self.bus.transfer(encoded)
        t2 = now_ns()
        self._last_transfer_end_ns = t2

        # The request is on the wire across the transfer; its start is the
        # reference point for any response that later correlates back to it.
        self._remember_pending(sequence, t1)
        self.counters.transactions += 1

        try:
            response = SpiFrame.decode(raw)
        except ValueError as exc:
            t3 = now_ns()
            self.counters.decode_failures += 1
            return self._record(sequence, message_type, t_realtime, t0, t1, t2, t3,
                                ok=False, error=str(exc), data_ready_wait_ns=data_ready_wait_ns,
                                data_ready_timed_out=data_ready_timed_out)

        t3 = now_ns()
        correlated = correlated_request_seq(response)
        round_trip = None
        if correlated is None:
            self.counters.uncorrelated_responses += 1
        else:
            sent_ns = self._pending.pop(correlated, None)
            if sent_ns is None:
                self.counters.correlation_misses += 1
            else:
                round_trip = t2 - sent_ns

        hub_delta = None
        if self._previous_hub_time_us is not None:
            hub_delta = response.frame_time_us - self._previous_hub_time_us
        self._previous_hub_time_us = response.frame_time_us

        status_code, detail_code = nack_codes(response)
        if response.message_type is MessageType.NACK:
            self.counters.nacks += 1

        return self._record(sequence, message_type, t_realtime, t0, t1, t2, t3, ok=True,
                            response=response, correlated=correlated, round_trip=round_trip,
                            hub_delta=hub_delta, status_code=status_code, detail_code=detail_code,
                            data_ready_wait_ns=data_ready_wait_ns,
                            data_ready_timed_out=data_ready_timed_out)

    def _remember_pending(self, sequence: int, sent_ns: int) -> None:
        if len(self._pending) >= _MAX_PENDING:
            self._pending.pop(next(iter(self._pending)))
        self._pending[sequence] = sent_ns

    def _record(self, sequence, request_type, t_realtime, t0, t1, t2, t3, *, ok,
                error='', response=None, correlated=None, round_trip=None, hub_delta=None,
                status_code=None, detail_code=None, data_ready_wait_ns=None,
                data_ready_timed_out=False, time_sync_seq=None, time_sync_status=None) -> TransactionRecord:
        self._index += 1
        return TransactionRecord(
            index=self._index,
            block_id=self.block_id,
            request_seq=sequence,
            request_type=request_type.name,
            t_mono_ns=t0,
            t_realtime_ns=t_realtime,
            encode_ns=t1 - t0,
            transfer_ns=t2 - t1,
            decode_ns=t3 - t2,
            total_ns=t3 - t0,
            ok=ok,
            error=error,
            response_type=response.message_type.name if response is not None else '',
            response_seq=response.seq if response is not None else None,
            response_frame_time_us=response.frame_time_us if response is not None else None,
            hub_delta_us=hub_delta,
            correlated_seq=correlated,
            round_trip_ns=round_trip,
            nack_status_code=status_code,
            nack_detail_code=detail_code,
            data_ready_wait_ns=data_ready_wait_ns,
            data_ready_timed_out=data_ready_timed_out,
            time_sync_seq=time_sync_seq,
            time_sync_status=time_sync_status,
        )


def percentiles(values: list[int], points=(50, 90, 99, 99.9)) -> dict[str, float]:
    """Nearest-rank percentiles. Empty input yields an empty mapping."""
    if not values:
        return {}
    ordered = sorted(values)
    result = {}
    for point in points:
        rank = max(1, min(len(ordered), math.ceil(point / 100.0 * len(ordered))))
        result[f'p{point:g}'] = float(ordered[rank - 1])
    return result


def summarise(values: list[int]) -> dict[str, float]:
    if not values:
        return {'count': 0}
    summary = {
        'count': len(values),
        'min': float(min(values)),
        'mean': sum(values) / len(values),
        'max': float(max(values)),
    }
    summary.update(percentiles(values))
    return summary
