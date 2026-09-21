"""Analysis functions for TIME_SYNC measurements and offset characterization.

Provides summary statistics, percentile analysis, and drift rate computation
for TIME_SYNC synchronization sessions.
"""

from __future__ import annotations

from dataclasses import dataclass
import statistics
from typing import List, Optional

from .spi_protocol import NackReason
from .time_sync_session import TimeSyncSession


@dataclass
class TimeSyncStats:
    """Summary statistics for TIME_SYNC measurements.

    Attributes:
        total_attempts: Total number of synchronization attempts
        accepted_count: Number of accepted (ACK) candidates
        rejected_count: Number of rejected (NACK) candidates
        acceptance_rate: Fraction of attempts that were accepted
        offset_mean_us: Mean offset of accepted candidates
        offset_std_us: Standard deviation of offset (0 if < 2 accepted samples)
        offset_min_us: Minimum offset of accepted candidates
        offset_max_us: Maximum offset of accepted candidates
        uncertainty_mean_min_us: Mean of uncertainty_min_us across all candidates
        uncertainty_mean_max_us: Mean of uncertainty_max_us (excluding zeros)
        drift_rate_us_per_sec: Estimated offset drift rate, None if < 2 accepted samples
        nack_distribution: Dict mapping NACK reason name to count
    """

    total_attempts: int
    accepted_count: int
    rejected_count: int
    acceptance_rate: float
    offset_mean_us: float
    offset_std_us: float
    offset_min_us: int
    offset_max_us: int
    uncertainty_mean_min_us: float
    uncertainty_mean_max_us: float
    drift_rate_us_per_sec: Optional[float]
    nack_distribution: dict[str, int]


def compute_stats(session: TimeSyncSession) -> TimeSyncStats:
    """Compute summary statistics from TIME_SYNC candidates.

    Analyzes accepted candidates to compute offset statistics, acceptance rate,
    and drift rate. For rejected candidates, computes the distribution of
    NACK reasons.

    Args:
        session: TimeSyncSession to analyze

    Returns:
        TimeSyncStats object with computed summary

    Example:
        >>> session = TimeSyncSession()
        >>> # ... record candidates ...
        >>> stats = compute_stats(session)
        >>> print(f"Acceptance rate: {stats.acceptance_rate:.1%}")
        >>> print(f"Offset: {stats.offset_mean_us:.0f} ± {stats.offset_std_us:.0f} µs")
    """
    candidates = session.candidates
    if not candidates:
        return TimeSyncStats(
            total_attempts=0,
            accepted_count=0,
            rejected_count=0,
            acceptance_rate=0.0,
            offset_mean_us=0.0,
            offset_std_us=0.0,
            offset_min_us=0,
            offset_max_us=0,
            uncertainty_mean_min_us=0.0,
            uncertainty_mean_max_us=0.0,
            drift_rate_us_per_sec=None,
            nack_distribution={}
        )

    accepted = [c for c in candidates if c.is_accepted()]
    rejected = [c for c in candidates if not c.is_accepted()]

    total = len(candidates)
    accepted_count = len(accepted)
    rejected_count = len(rejected)
    acceptance_rate = accepted_count / total if total > 0 else 0

    # Offset statistics (from accepted only)
    if accepted:
        offsets = [c.offset_us for c in accepted]
        offset_mean = statistics.mean(offsets)
        offset_std = statistics.stdev(offsets) if len(offsets) > 1 else 0.0
        offset_min = min(offsets)
        offset_max = max(offsets)
    else:
        offset_mean = 0.0
        offset_std = 0.0
        offset_min = 0
        offset_max = 0

    # Uncertainty statistics
    uncertainty_mins = [c.uncertainty_min_us for c in candidates]
    uncertainty_maxs = [c.uncertainty_max_us for c in candidates if c.uncertainty_max_us > 0]

    uncertainty_mean_min = statistics.mean(uncertainty_mins) if uncertainty_mins else 0.0
    uncertainty_mean_max = statistics.mean(uncertainty_maxs) if uncertainty_maxs else 0.0

    # Drift rate (accepted offsets only)
    drift_rate = None
    if len(accepted) >= 2:
        time_deltas = []
        offset_deltas = []
        for i in range(1, len(accepted)):
            # Use pi_time_us_received as a proxy for elapsed time (in microseconds on Pi clock)
            dt_us = accepted[i].pi_time_us_received - accepted[i - 1].pi_time_us_received
            if dt_us > 0:
                do_us = abs(accepted[i].offset_us - accepted[i - 1].offset_us)
                # Convert microseconds to seconds
                rate = do_us / (dt_us / 1e6)
                time_deltas.append(dt_us)
                offset_deltas.append(rate)

        if offset_deltas:
            drift_rate = statistics.mean(offset_deltas)

    # NACK distribution
    nack_dist = {}
    for c in rejected:
        reason = NackReason.describe(c.status_code)
        nack_dist[reason] = nack_dist.get(reason, 0) + 1

    return TimeSyncStats(
        total_attempts=total,
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        acceptance_rate=acceptance_rate,
        offset_mean_us=offset_mean,
        offset_std_us=offset_std,
        offset_min_us=offset_min,
        offset_max_us=offset_max,
        uncertainty_mean_min_us=uncertainty_mean_min,
        uncertainty_mean_max_us=uncertainty_mean_max,
        drift_rate_us_per_sec=drift_rate,
        nack_distribution=nack_dist
    )


def percentiles(session: TimeSyncSession, percentile_points: List[int] = None) -> dict[int, int]:
    """Compute percentile offsets from accepted candidates.

    Uses linear interpolation for sub-integer percentiles.

    Args:
        session: TimeSyncSession to analyze
        percentile_points: List of percentile values to compute (e.g., [5, 25, 50, 75, 95])
                          Defaults to [5, 25, 50, 75, 95]

    Returns:
        Dict mapping percentile point to offset value (integer microseconds)
        Returns empty dict if no accepted candidates

    Example:
        >>> session = TimeSyncSession()
        >>> # ... record candidates ...
        >>> p = percentiles(session, [25, 50, 75])
        >>> print(f"Median offset: {p[50]} µs")
    """
    if percentile_points is None:
        percentile_points = [5, 25, 50, 75, 95]

    accepted = [c.offset_us for c in session.candidates if c.is_accepted()]
    if not accepted:
        return {p: 0 for p in percentile_points}

    result = {}
    sorted_offsets = sorted(accepted)

    for p in percentile_points:
        # Linear interpolation: index = (p / 100) * (n - 1)
        # This puts the 0th percentile at the minimum and 100th at the maximum
        index = (p / 100) * (len(sorted_offsets) - 1)
        lower_idx = int(index)
        upper_idx = min(lower_idx + 1, len(sorted_offsets) - 1)
        frac = index - lower_idx

        # Linear interpolation
        value = int(
            sorted_offsets[lower_idx] * (1 - frac) + sorted_offsets[upper_idx] * frac
        )
        result[p] = value

    return result
