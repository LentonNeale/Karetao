"""Per-transaction SPI timing statistics, and the legacy TimingSession entry point.

The send, clock, correlate and pace loop lives in exchange.ExchangeSession, grown from the
TimingSession that was here (issue #78); see that module for the pipelined transaction model.
TimingSession stays as a thin wrapper with its original constructor, transact(message_type,
payload) signature and start_sequence seed, so the timing harness keeps working until #102 moves its
callers to ExchangeSession and deletes this adapter. The moved names are re-exported for the
same callers.
"""

from __future__ import annotations

import math
from typing import Optional

from .data_ready import DataReadyLike
from .exchange import (  # noqa: F401  (re-exported for existing callers)
    CSV_FIELDS,
    ExchangeSession,
    Request,
    SessionCounters,
    TransactionRecord,
    correlated_request_seq,
    nack_codes,
    now_ns,
)
from .spi_bus import SpiBus
from .spi_protocol import MessageType, Sequencer


class TimingSession:
    """An ExchangeSession behind the former TimingSession constructor and call signature.

    A wrapper rather than a subclass, so an ExchangeSession is never handed out with a
    different transact() signature. Removed by #102.
    """

    def __init__(self, bus: SpiBus, block_id: str = '', data_ready: Optional[DataReadyLike] = None,
                 data_ready_timeout_s: float = 0.1, min_interval_s: float = 0.0,
                 start_sequence: Optional[int] = None, counters: Optional[SessionCounters] = None) -> None:
        self.session = ExchangeSession(
            bus=bus, block_id=block_id, data_ready=data_ready, data_ready_timeout_s=data_ready_timeout_s,
            min_interval_s=min_interval_s,
            sequencer=Sequencer(start_sequence) if start_sequence is not None else None,
            counters=counters if counters is not None else SessionCounters())

    @property
    def counters(self) -> SessionCounters:
        return self.session.counters

    def reset_counters(self) -> None:
        self.session.reset_counters()

    def next_sequence(self) -> int:
        return self.session.next_sequence()

    def transact(self, message_type: MessageType, payload: bytes = b'') -> TransactionRecord:
        return self.session.transact(Request(message_type, payload))


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
