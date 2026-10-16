"""The Pi's one owner of the SPI exchange: send, clock, correlate, pace.

The transaction model is pipelined (SPI_SYSTEM_INTERFACE.md section 4): the response clocked
out during transaction N answers a request the host sent earlier, so an exchange (a request and
its correlated reply, SYSTEM_OVERVIEW.md Vocabulary) spans at least two transactions. Every
solicited response carries a correlation field naming the request it answers; this module keeps
a table of requests still waiting for theirs and stitches each exchange back together from it.

Two calls, one record per transaction:

- `ExchangeSession.transact(request)` paces, clocks one transaction, records its phase timings,
  decodes, correlates and returns one `TransactionRecord`.
- `ExchangeSession.exchange(request, filler, budget=...)` transacts the request, then the filler,
  until the request's reply or NACK correlates or the budget is spent, and returns an
  `ExchangeResult`. Firmware outcomes (a NACK, garbage, a lost reply) are results, never
  exceptions.

A record that correlates holds one clock-sync observation (TIME_SYSTEM_INTERFACE.md section 3):
T1, the send time of the request it answers; `request_received_local_us` (T2), once the wire
placement of that extension is fixed (#42; SPI_PAYLOAD_SCHEMA.md open items); and T4, its own
receive time. The session has no dependency on ClockSync: ClockSync's owner feeds it from the
records.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import struct
import time
from typing import Optional

from .data_ready import DataReadyLike
from .spi_bus import SpiBus
from .spi_protocol import (
    COMMAND_REPLY_OFFSET_REQUEST_SEQ,
    DIAGNOSTIC_OFFSET_RESPONSE_TO_SEQ,
    SNAPSHOT_OFFSET_RESPONSE_TO_SEQ,
    VERSION_OFFSET_RESPONSE_TO_SEQ,
    MessageType,
    Sequencer,
    SpiFrame,
    decode_command_reply,
    process_sequencer,
)

try:
    _INTERVAL_CLOCK = time.CLOCK_MONOTONIC_RAW
except AttributeError:  # pragma: no cover - non-Linux fallback
    _INTERVAL_CLOCK = time.CLOCK_MONOTONIC

_U32 = struct.Struct('<I')

# Payload offset of the field correlating a response to its request. ACK/NACK
# name it request_seq, the others response_to_seq (SPI_PAYLOAD_SCHEMA.md).
_CORRELATION_OFFSETS = {
    MessageType.ACK: COMMAND_REPLY_OFFSET_REQUEST_SEQ,
    MessageType.NACK: COMMAND_REPLY_OFFSET_REQUEST_SEQ,
    MessageType.SNAPSHOT: SNAPSHOT_OFFSET_RESPONSE_TO_SEQ,
    MessageType.VERSION: VERSION_OFFSET_RESPONSE_TO_SEQ,
    MessageType.DIAGNOSTIC: DIAGNOSTIC_OFFSET_RESPONSE_TO_SEQ,
}

# Bound the outstanding-request table so a firmware that never correlates
# cannot grow it without limit during a long soak.
_MAX_PENDING = 4096

# A GET request's payload: schema version 1, then three reserved zero bytes. This is the form
# the shared golden frames use (make_vectors.py GET_REQUEST_PAYLOAD); ruling R1 makes it the
# only accepted form, applied on both sides by #88.
GET_REQUEST_PAYLOAD = bytes([1, 0, 0, 0])


def now_ns() -> int:
    return time.clock_gettime_ns(_INTERVAL_CLOCK)


def correlated_request_seq(frame: SpiFrame) -> Optional[int]:
    offset = _CORRELATION_OFFSETS.get(frame.message_type)
    if offset is None or len(frame.payload) < offset + 4:
        return None
    return _U32.unpack_from(frame.payload, offset)[0]


def nack_codes(frame: SpiFrame) -> tuple[Optional[int], Optional[int]]:
    """Status and detail code of a NACK, or (None, None).

    Decoded by decode_command_reply, the one home of the ACK/NACK layout, so a reply with an
    unsupported schema_version yields (None, None) rather than a schema-1 reading of other
    bytes (SPI_PAYLOAD_SCHEMA.md common rules: unsupported schema versions are rejected).
    """
    if frame.message_type is not MessageType.NACK:
        return (None, None)
    try:
        _, status_code, _, detail_code = decode_command_reply(frame.payload)
    except ValueError:
        return (None, None)
    return (status_code, detail_code)


@dataclass(frozen=True)
class Request:
    """What the Pi asks for; the session assigns the sequence when it sends it."""

    message_type: MessageType
    payload: bytes = b''


GET_STATUS = Request(MessageType.GET_STATUS, GET_REQUEST_PAYLOAD)


@dataclass(frozen=True)
class TransactionRecord:
    """One clocked 512-byte transaction. Durations and Pi times are nanoseconds on the raw
    monotonic clock (ruling R16: the Pi uses one raw monotonic clock).

    The request is the one this transaction sent; the response is whatever the STM32 staged
    before it, which may answer an earlier request (`correlated_seq`). When that request is
    in this session's pending table, the record is a clock-sync observation:
    `t1_request_sent_ns` is that request's send time, `t4_response_received_ns` this
    transaction's receive time, and `round_trip_ns` their difference. All three are set
    together or not at all, so `t1_request_sent_ns is not None` is the test for an
    observation. `raw_response` holds the received bytes only when they did not decode.
    `time_sync_seq` and `time_sync_status` belong to the as-built TIME_SYNC and are never set
    here; they stay so the CSV fields do not change, and go with TIME_SYNC (#45).
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
    t1_request_sent_ns: Optional[int] = None
    t4_response_received_ns: Optional[int] = None
    request_received_local_us: Optional[int] = None
    raw_response: Optional[bytes] = None

    def as_row(self) -> dict:
        row = asdict(self)
        if self.raw_response is not None:
            row['raw_response'] = self.raw_response.hex()
        return row


CSV_FIELDS = list(TransactionRecord.__dataclass_fields__)


@dataclass
class SessionCounters:
    transactions: int = 0
    decode_failures: int = 0
    nacks: int = 0
    uncorrelated_responses: int = 0
    correlation_misses: int = 0
    data_ready_timeouts: int = 0


class Outcome(Enum):
    REPLIED = 'replied'      # the request's reply correlated
    REFUSED = 'refused'      # a NACK naming the request correlated
    EXHAUSTED = 'exhausted'  # the budget was spent before either arrived


@dataclass(frozen=True)
class ExchangeResult:
    outcome: Outcome
    request_seq: int
    reply: Optional[SpiFrame]  # the correlated reply or NACK; None when exhausted
    records: tuple[TransactionRecord, ...]


@dataclass
class ExchangeSession:
    """Clocks transactions over an open bus and correlates replies.

    `data_ready` is duck-typed (see data_ready.DataReadyLike) so tests can substitute a fake
    without a real GPIO chip. When set, the session waits for DATA_READY before each transfer
    instead of clocking unconditionally; a timeout does not abort the transaction, since the
    polling model (SPI_SYSTEM_INTERFACE.md section 7) is the documented fallback and the
    transaction still needs to be attempted either way. The wait defaults to PRM-SPI-04
    (100 ms), which ruling R17 makes the Pi's DATA_READY wait. `min_interval_s` is a plain
    fixed-delay fallback for when no DATA_READY watcher is configured; it exists because the
    host has no other pacing mechanism and back-to-back transactions can outrun the
    firmware's main-loop re-arm (observed on the bench: transactions clocked with no gap
    between them return stale/zeroed frames).

    Sequences come from `sequencer`, by default the process-wide one (ruling R3), so every
    session in a process continues one sequence space. One session owns a link: the pending
    table is the session's, so a second session clocking the same bus would receive replies
    to the first one's requests and count them as correlation misses. Consumers of the link,
    ClockSync among them, read this session's records rather than opening their own.
    """

    bus: SpiBus
    block_id: str = ''
    data_ready: Optional[DataReadyLike] = None
    data_ready_timeout_s: float = 0.1
    min_interval_s: float = 0.0
    sequencer: Optional[Sequencer] = None
    counters: SessionCounters = field(default_factory=SessionCounters)

    def __post_init__(self) -> None:
        if self.sequencer is None:
            self.sequencer = process_sequencer()
        self._index = 0
        self._pending: dict[int, int] = {}
        self._previous_hub_time_us: Optional[int] = None
        self._last_transfer_end_ns: Optional[int] = None

    def reset_counters(self) -> None:
        """Discard counts accumulated during warmup."""
        self.counters = SessionCounters()

    def next_sequence(self) -> int:
        return self.sequencer.next()

    def transact(self, request: Request) -> TransactionRecord:
        return self._transact(request)[0]

    def exchange(self, request: Request, filler: Request = GET_STATUS, *, budget: int) -> ExchangeResult:
        """Transact `request`, then `filler`, until the request's reply or NACK correlates.

        `budget` is the most transactions the exchange may clock, the request's own included.
        It has no default because no register row sets one; it must be at least two, since the
        reply cannot arrive before the transaction after the request.
        """
        if budget < 2:
            raise ValueError('an exchange needs a budget of at least two transactions')
        record, frame = self._transact(request)
        records = [record]
        sequence = record.request_seq
        while True:
            if frame is not None and record.correlated_seq == sequence:
                outcome = Outcome.REFUSED if frame.message_type is MessageType.NACK else Outcome.REPLIED
                return ExchangeResult(outcome, sequence, frame, tuple(records))
            if len(records) >= budget:
                return ExchangeResult(Outcome.EXHAUSTED, sequence, None, tuple(records))
            record, frame = self._transact(filler)
            records.append(record)

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

    def _transact(self, request: Request) -> tuple[TransactionRecord, Optional[SpiFrame]]:
        sequence = self.next_sequence()
        frame = SpiFrame(message_type=request.message_type, seq=sequence, payload=request.payload)

        data_ready_wait_ns, data_ready_timed_out = self._pace()
        if data_ready_timed_out:
            self.counters.data_ready_timeouts += 1

        t_realtime = time.clock_gettime_ns(time.CLOCK_REALTIME)
        t0 = now_ns()
        encoded = frame.encode()
        t1 = now_ns()
        raw = self.bus.transfer(encoded)
        t2 = now_ns()
        self._last_transfer_end_ns = t2

        # The request is on the wire across the transfer; its start is T1 for whichever later
        # response correlates back to it.
        self._remember_pending(sequence, t1)
        self.counters.transactions += 1
        timing = dict(t_realtime=t_realtime, t0=t0, t1=t1, t2=t2,
                      data_ready_wait_ns=data_ready_wait_ns, data_ready_timed_out=data_ready_timed_out)

        try:
            response = SpiFrame.decode(raw)
        except ValueError as exc:
            self.counters.decode_failures += 1
            record = self._record(sequence, request.message_type, t3=now_ns(), ok=False, error=str(exc),
                                  raw_response=bytes(raw), **timing)
            return (record, None)

        t3 = now_ns()
        correlated = correlated_request_seq(response)
        sent_ns = None
        if correlated is None:
            self.counters.uncorrelated_responses += 1
        else:
            sent_ns = self._pending.pop(correlated, None)
            if sent_ns is None:
                self.counters.correlation_misses += 1

        hub_delta = None
        if self._previous_hub_time_us is not None:
            hub_delta = response.frame_time_us - self._previous_hub_time_us
        self._previous_hub_time_us = response.frame_time_us

        status_code, detail_code = nack_codes(response)
        if response.message_type is MessageType.NACK:
            self.counters.nacks += 1

        record = self._record(sequence, request.message_type, t3=t3, ok=True, response=response,
                              correlated=correlated, sent_ns=sent_ns, hub_delta=hub_delta,
                              status_code=status_code, detail_code=detail_code, **timing)
        return (record, response)

    def _remember_pending(self, sequence: int, sent_ns: int) -> None:
        if len(self._pending) >= _MAX_PENDING:
            self._pending.pop(next(iter(self._pending)))
        self._pending[sequence] = sent_ns

    def _record(self, sequence, request_type, *, t_realtime, t0, t1, t2, t3, ok, error='',
                response=None, correlated=None, sent_ns=None, hub_delta=None, status_code=None,
                detail_code=None, data_ready_wait_ns=None, data_ready_timed_out=False,
                raw_response=None) -> TransactionRecord:
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
            round_trip_ns=t2 - sent_ns if sent_ns is not None else None,
            nack_status_code=status_code,
            nack_detail_code=detail_code,
            data_ready_wait_ns=data_ready_wait_ns,
            data_ready_timed_out=data_ready_timed_out,
            t1_request_sent_ns=sent_ns,
            t4_response_received_ns=t2 if sent_ns is not None else None,
            raw_response=raw_response,
        )
