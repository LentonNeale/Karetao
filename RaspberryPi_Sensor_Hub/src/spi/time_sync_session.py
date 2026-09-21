"""TIME_SYNC session state and offset calculation tracking.

Maintains TIME_SYNC request/response state, computes candidate offsets,
tracks uncertainty bounds, and validates drift across synchronization attempts.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import time
from typing import Optional


@dataclass
class TimeSyncCandidate:
    """Single TIME_SYNC synchronization attempt.

    Records a complete request/response cycle with computed offset and
    uncertainty bounds. The offset represents the difference between Pi's
    clock and STM32's local clock at the moment of ACK/NACK.

    Attributes:
        sync_seq: Sequence number from TIME_SYNC request
        pi_time_us_sent: Pi time when request was sent (T_start)
        pi_time_us_received: Pi time when response was received (T_end)
        pi_time_us_stm32: STM32's pi_time_us captured in ACK/NACK payload
        offset_us: candidate_offset_us = pi_time_us_stm32 - stm32_local_us
        status_code: ACK (0) or NACK reason code
        uncertainty_min_us: T_end - pi_time_us_stm32
        uncertainty_max_us: T_start_next - pi_time_us_stm32 (updated by next request)
    """

    sync_seq: int
    pi_time_us_sent: int
    pi_time_us_received: int
    pi_time_us_stm32: int
    offset_us: int
    status_code: int
    uncertainty_min_us: int
    uncertainty_max_us: int

    def is_accepted(self) -> bool:
        """True if this candidate was an ACK (status_code == 0)."""
        return self.status_code == 0


class TimeSyncSession:
    """Maintains TIME_SYNC request/response state and offset tracking.

    Coordinates request/response pairs, computes candidate offsets with
    uncertainty bounds, and validates that accepted offsets stay within
    drift limits. The session maintains the current best-estimate offset
    and tracks the history of all candidates for analysis.

    Attributes:
        current_offset_us: Best-estimate offset currently in use
        accepted_offset_us: Most recently accepted offset
        accepted_time_mono_s: Monotonic time when last offset was accepted
        drift_limit_us_per_sec: Maximum allowed offset change per second
        candidates: History of all synchronization attempts
    """

    def __init__(self, initial_offset_us: int = 0,
                 drift_limit_us_per_sec: float = 1000.0) -> None:
        """Initialize TIME_SYNC session.

        Args:
            initial_offset_us: Starting offset estimate (default 0)
            drift_limit_us_per_sec: Max offset change rate in us/s
                (default 1000.0, matching ±1ms per sync per SYS-SYNC-001)
        """
        self.current_offset_us = initial_offset_us
        self.accepted_offset_us = initial_offset_us
        self.accepted_time_mono_s = time.monotonic()
        self.drift_limit_us_per_sec = drift_limit_us_per_sec
        self.last_sync_offset_us = initial_offset_us
        self.last_sync_time_mono_s = time.monotonic()
        self.candidates: list[TimeSyncCandidate] = []
        self.next_seq = 1
        self._pending_req_seq: Optional[int] = None
        self._pending_pi_time_start_us: Optional[int] = None

    def next_sequence(self) -> int:
        """Return next sequence number for TIME_SYNC request.

        Increments internal counter and returns the current value.
        Returns a uint32 that fits in the TIME_SYNC payload.

        Returns:
            Next sequence number (starting from 1)
        """
        seq = self.next_seq
        self.next_seq = (self.next_seq + 1) & 0xFFFFFFFF or 1
        return seq

    def record_request(self, seq: int, pi_time_us: int) -> None:
        """Called when TIME_SYNC request is sent (at T_start).

        Stores the request metadata for later use when the response arrives.

        Args:
            seq: Sequence number from request
            pi_time_us: Pi clock time at moment request is sent
        """
        self._pending_req_seq = seq
        self._pending_pi_time_start_us = pi_time_us

    def record_response(self, seq: int, pi_time_us_stm32: int,
                        stm32_local_us: int, status_code: int,
                        pi_time_us_received: int) -> TimeSyncCandidate:
        """Called when ACK/NACK is decoded (at T_end).

        Constructs a TimeSyncCandidate with computed offset and uncertainty.
        Updates the uncertainty_max_us of the previous candidate if present.
        If the candidate is accepted (status_code==0) and passes drift
        validation, updates current_offset_us.

        Args:
            seq: Echoed sequence from ACK/NACK response
            pi_time_us_stm32: Pi time captured by STM32 during request
            stm32_local_us: STM32 local clock value (TIM2) at ACK/NACK moment
            status_code: ACK=0, otherwise NACK reason code
            pi_time_us_received: Pi clock at ACK/NACK decode time (T_end)

        Returns:
            TimeSyncCandidate with offset and uncertainty bounds

        Raises:
            RuntimeError: if no pending request was recorded
        """
        if self._pending_pi_time_start_us is None:
            raise RuntimeError('record_response called without prior record_request')

        # Offset: difference between Pi's time and STM32's local time
        # as captured by the STM32 at the moment of processing the request
        offset_us = pi_time_us_stm32 - stm32_local_us

        # Uncertainty bounds per SPI_SYSTEM_INTERFACE.md section 11:
        # - Min: T_end (when response was received) - pi_time_us_stm32
        #   (STM32 processed request at least this long before we got response)
        # - Max: updated when next request is sent
        uncertainty_min_us = pi_time_us_received - pi_time_us_stm32

        candidate = TimeSyncCandidate(
            sync_seq=seq,
            pi_time_us_sent=self._pending_pi_time_start_us,
            pi_time_us_received=pi_time_us_received,
            pi_time_us_stm32=pi_time_us_stm32,
            offset_us=offset_us,
            status_code=status_code,
            uncertainty_min_us=uncertainty_min_us,
            uncertainty_max_us=0  # Will be updated by next request
        )

        # Update previous candidate's uncertainty_max_us now that we know
        # when the next request started (T_start_next)
        if self.candidates:
            # uncertainty_max_us = T_start_next - pi_time_us_stm32_of_prev
            # But we use the pi_time_us_stm32 from THIS candidate's request moment
            prev_candidate = self.candidates[-1]
            # The previous uncertainty_max is when the next request was sent
            # relative to when the STM32 captured the pi_time for that prev request
            # This is tricky: we need T_start_next - pi_time_us_stm32_prev
            # T_start_next is self._pending_pi_time_start_us (just sent)
            # pi_time_us_stm32_prev is from the previous candidate
            # Actually, looking at the spec more carefully:
            # uncertainty_max_us = T_start_next - pi_time_us_stm32
            # where pi_time_us_stm32 is from the PREVIOUS response
            object.__setattr__(prev_candidate, 'uncertainty_max_us',
                             self._pending_pi_time_start_us - prev_candidate.pi_time_us_stm32)

        self.candidates.append(candidate)

        # Accept offset if it's an ACK and passes drift validation
        if candidate.is_accepted() and self._is_within_drift_bounds(offset_us):
            self.current_offset_us = offset_us
            self.accepted_offset_us = offset_us
            self.accepted_time_mono_s = time.monotonic()
            # Update drift tracking for next comparison
            self.last_sync_offset_us = offset_us
            self.last_sync_time_mono_s = time.monotonic()

        return candidate

    def _is_within_drift_bounds(self, candidate_offset_us: int) -> bool:
        """Check if offset change is within allowed drift rate.

        Compares the candidate offset against the last accepted offset,
        accounting for elapsed time since that acceptance. A jump larger
        than drift_limit_us_per_sec * elapsed_s is rejected.

        Args:
            candidate_offset_us: Proposed new offset in microseconds

        Returns:
            True if change is acceptable, False otherwise
        """
        elapsed_s = time.monotonic() - self.last_sync_time_mono_s

        # First sync or immediate retry: always accept
        if elapsed_s < 0.001:
            return True

        # Check if jump exceeds drift rate
        delta_us = abs(candidate_offset_us - self.last_sync_offset_us)
        max_drift_us = self.drift_limit_us_per_sec * elapsed_s

        if delta_us > max_drift_us:
            return False

        # Update drift tracking state for next comparison
        self.last_sync_offset_us = candidate_offset_us
        self.last_sync_time_mono_s = time.monotonic()
        return True

    @staticmethod
    def to_csv_header() -> str:
        """CSV header line for TIME_SYNC measurements.

        Returns:
            Pipe-separated header string
        """
        return 'timestamp_s | sync_seq | status | pi_time_us | stm32_local_us | offset_us | uncertainty_min_us | uncertainty_max_us | accepted'

    def to_csv_rows(self) -> list[str]:
        """Convert TIME_SYNC candidates to CSV rows.

        Returns:
            List of pipe-separated CSV rows, one per candidate
        """
        from .spi_protocol import NackReason

        rows = []
        for candidate in self.candidates:
            status = 'OK' if candidate.is_accepted() else NackReason.describe(candidate.status_code)
            accepted_str = 'yes' if candidate.is_accepted() else 'no'

            # Timestamp: use current UTC time as placeholder
            # (in production, would convert pi_time_us_received to wall-clock using monotonic offset)
            timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            row = (f'{timestamp_iso} | {candidate.sync_seq} | {status} | '
                   f'{candidate.pi_time_us_stm32} | 0 | {candidate.offset_us} | '
                   f'{candidate.uncertainty_min_us} | {candidate.uncertainty_max_us} | {accepted_str}')
            rows.append(row)

        return rows
