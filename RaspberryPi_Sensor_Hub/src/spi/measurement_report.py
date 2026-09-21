"""Post-analysis and reporting for TIME_SYNC measurement sessions.

Provides SessionReport (summary of a single session) and RepeatabilityMetrics
(cross-session consistency analysis) along with report generation functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import csv
import statistics
import json
from pathlib import Path


@dataclass
class SessionReport:
    """Summary of one TIME_SYNC measurement session.

    Attributes:
        session_num: Session index (1-based)
        total_attempts: Total TIME_SYNC requests sent
        accepted_count: Number of accepted (ACK) responses
        acceptance_rate: Fraction of attempts that were accepted
        offset_mean_us: Mean offset of accepted candidates (microseconds)
        offset_std_us: Standard deviation of accepted offsets
        offset_min_us: Minimum offset of accepted candidates
        offset_max_us: Maximum offset of accepted candidates
        percentile_50_us: Median (p50) offset
        percentile_95_us: 95th percentile offset
        drift_rate_us_per_s: Estimated offset drift rate, None if < 2 samples
    """

    session_num: int
    total_attempts: int
    accepted_count: int
    acceptance_rate: float

    offset_mean_us: float
    offset_std_us: float
    offset_min_us: int
    offset_max_us: int

    percentile_50_us: int
    percentile_95_us: int

    drift_rate_us_per_s: Optional[float]


@dataclass
class RepeatabilityMetrics:
    """Cross-session repeatability and consistency statistics.

    Analyzes how stable the offset measurements are across multiple sessions,
    whether acceptance rates are consistently high, and whether measurement
    noise is consistent.

    Attributes:
        num_sessions: Number of completed sessions
        offset_mean_of_means_us: Mean of session offset means
        offset_std_of_means_us: Std dev of session offset means
        offset_min_mean_us: Smallest session offset mean
        offset_max_mean_us: Largest session offset mean
        std_dev_of_stds_us: Std dev of session std devs (measurement consistency)
        acceptance_rate_mean: Mean acceptance rate across sessions
        acceptance_rate_std: Std dev of acceptance rates
        acceptance_rate_min: Lowest acceptance rate
        acceptance_rate_max: Highest acceptance rate
        means_within_target: All session means within ±1ms of first
        acceptance_rate_high: All sessions > 90%
        variance_consistent: Std dev < 20% relative variance
    """

    num_sessions: int

    # Offset mean across sessions
    offset_mean_of_means_us: float
    offset_std_of_means_us: float
    offset_min_mean_us: int
    offset_max_mean_us: int

    # Consistency of variance
    std_dev_of_stds_us: float

    # Acceptance rate stats
    acceptance_rate_mean: float
    acceptance_rate_std: float
    acceptance_rate_min: float
    acceptance_rate_max: float

    # Overall conformance
    means_within_target: bool
    acceptance_rate_high: bool
    variance_consistent: bool


def load_session_csv(csv_path: Path) -> SessionReport | None:
    """Parse a TIME_SYNC session CSV file and compute session statistics.

    Expected CSV format (pipe-separated):
        timestamp_s | sync_seq | status | pi_time_us | stm32_local_us | offset_us | uncertainty_min_us | uncertainty_max_us | accepted

    Args:
        csv_path: Path to session CSV file

    Returns:
        SessionReport with computed statistics, or None if parse fails

    Raises:
        FileNotFoundError: If CSV file doesn't exist
    """
    if not csv_path.exists():
        return None

    try:
        offsets_accepted = []
        total_count = 0
        accepted_count = 0

        with open(csv_path, 'r') as f:
            # Skip header (first line contains column names)
            lines = f.readlines()
            if not lines:
                return None

            # Parse data rows (skip header)
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue

                # Parse pipe-separated values
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 9:
                    continue

                try:
                    sync_seq = int(parts[1])
                    status = parts[2].strip()
                    offset_us = int(parts[5])
                    accepted_str = parts[8].strip().lower()
                    is_accepted = accepted_str == 'yes'

                    total_count += 1
                    if is_accepted:
                        offsets_accepted.append(offset_us)
                        accepted_count += 1
                except (ValueError, IndexError):
                    continue

        if total_count == 0:
            return None

        # Compute statistics from accepted candidates
        acceptance_rate = accepted_count / total_count if total_count > 0 else 0.0

        if offsets_accepted:
            offset_mean = statistics.mean(offsets_accepted)
            offset_std = statistics.stdev(offsets_accepted) if len(offsets_accepted) > 1 else 0.0
            offset_min = min(offsets_accepted)
            offset_max = max(offsets_accepted)

            # Percentiles
            sorted_offsets = sorted(offsets_accepted)
            p50_idx = int(len(sorted_offsets) * 0.50)
            p95_idx = int(len(sorted_offsets) * 0.95)
            percentile_50 = sorted_offsets[p50_idx] if sorted_offsets else 0
            percentile_95 = sorted_offsets[p95_idx] if sorted_offsets else 0
        else:
            offset_mean = 0.0
            offset_std = 0.0
            offset_min = 0
            offset_max = 0
            percentile_50 = 0
            percentile_95 = 0

        return SessionReport(
            session_num=0,  # Will be set by caller
            total_attempts=total_count,
            accepted_count=accepted_count,
            acceptance_rate=acceptance_rate,
            offset_mean_us=offset_mean,
            offset_std_us=offset_std,
            offset_min_us=offset_min,
            offset_max_us=offset_max,
            percentile_50_us=percentile_50,
            percentile_95_us=percentile_95,
            drift_rate_us_per_s=None,  # Not computed from CSV
        )

    except Exception:
        return None


def compute_repeatability_metrics(reports: List[SessionReport]) -> RepeatabilityMetrics:
    """Compute cross-session repeatability and consistency metrics.

    Analyzes how the offset means vary across sessions, whether acceptance
    rates are consistently high, and whether measurement variance is stable.

    Conformance checks:
        - means_within_target: All session means within ±1ms of first session
        - acceptance_rate_high: All sessions >= 90%
        - variance_consistent: Relative std dev of stds < 20%

    Args:
        reports: List of SessionReport objects to analyze

    Returns:
        RepeatabilityMetrics object

    Example:
        >>> reports = [load_session_csv(f) for f in csv_files]
        >>> metrics = compute_repeatability_metrics(reports)
        >>> print(f"Offset: {metrics.offset_mean_of_means_us:.0f} µs")
        >>> print(f"All conformant: {all([metrics.means_within_target, ...])}")
    """

    if not reports:
        return RepeatabilityMetrics(
            num_sessions=0,
            offset_mean_of_means_us=0.0,
            offset_std_of_means_us=0.0,
            offset_min_mean_us=0,
            offset_max_mean_us=0,
            std_dev_of_stds_us=0.0,
            acceptance_rate_mean=0.0,
            acceptance_rate_std=0.0,
            acceptance_rate_min=0.0,
            acceptance_rate_max=0.0,
            means_within_target=False,
            acceptance_rate_high=False,
            variance_consistent=False,
        )

    means = [r.offset_mean_us for r in reports]
    stds = [r.offset_std_us for r in reports]
    acceptance_rates = [r.acceptance_rate for r in reports]

    offset_mean_of_means = statistics.mean(means)
    offset_std_of_means = statistics.stdev(means) if len(means) > 1 else 0.0
    offset_min_mean = int(min(means))
    offset_max_mean = int(max(means))

    std_dev_of_stds = statistics.stdev(stds) if len(stds) > 1 else 0.0

    acceptance_rate_mean = statistics.mean(acceptance_rates)
    acceptance_rate_std = statistics.stdev(acceptance_rates) if len(acceptance_rates) > 1 else 0.0
    acceptance_rate_min = min(acceptance_rates)
    acceptance_rate_max = max(acceptance_rates)

    # Conformance: all means within ±1ms (±1000µs) of each other
    means_within_target = (offset_max_mean - offset_min_mean) <= 1000

    # All acceptance rates >= 90%
    acceptance_rate_high = all(r >= 0.90 for r in acceptance_rates)

    # Std dev consistency: relative std dev < 20%
    if offset_mean_of_means != 0:
        rel_std = abs(std_dev_of_stds) / abs(offset_mean_of_means)
        variance_consistent = rel_std < 0.20
    else:
        variance_consistent = True

    return RepeatabilityMetrics(
        num_sessions=len(reports),
        offset_mean_of_means_us=offset_mean_of_means,
        offset_std_of_means_us=offset_std_of_means,
        offset_min_mean_us=offset_min_mean,
        offset_max_mean_us=offset_max_mean,
        std_dev_of_stds_us=std_dev_of_stds,
        acceptance_rate_mean=acceptance_rate_mean,
        acceptance_rate_std=acceptance_rate_std,
        acceptance_rate_min=acceptance_rate_min,
        acceptance_rate_max=acceptance_rate_max,
        means_within_target=means_within_target,
        acceptance_rate_high=acceptance_rate_high,
        variance_consistent=variance_consistent,
    )


def generate_text_report(metrics: RepeatabilityMetrics) -> str:
    """Generate a human-readable text report of repeatability metrics.

    Args:
        metrics: RepeatabilityMetrics object to format

    Returns:
        Multi-line formatted report string
    """

    overall_pass = all([
        metrics.means_within_target,
        metrics.acceptance_rate_high,
        metrics.variance_consistent,
    ])

    report = f"""
REPEATABILITY ANALYSIS REPORT
{'='*70}

Measurement Summary:
  Sessions: {metrics.num_sessions}

Offset Statistics (across sessions):
  Mean of means:      {metrics.offset_mean_of_means_us:+.0f} µs
  Std dev of means:   {metrics.offset_std_of_means_us:+.0f} µs
  Range:              {metrics.offset_min_mean_us:+d} to {metrics.offset_max_mean_us:+d} µs
  Spread:             {metrics.offset_max_mean_us - metrics.offset_min_mean_us:d} µs

Variance Consistency:
  Std dev of std devs: {metrics.std_dev_of_stds_us:+.0f} µs
  (Measures consistency of measurement noise across sessions)

Acceptance Rate (all sessions):
  Mean:               {metrics.acceptance_rate_mean*100:.1f}%
  Std dev:            {metrics.acceptance_rate_std*100:.1f}%
  Range:              {metrics.acceptance_rate_min*100:.1f}% to {metrics.acceptance_rate_max*100:.1f}%

Conformance Checks (per SYS-SYNC-001):
  ✓ Offset means within ±1ms:  {metrics.means_within_target}
  ✓ Acceptance rate >= 90%:    {metrics.acceptance_rate_high}
  ✓ Variance consistent (<20%): {metrics.variance_consistent}

Overall Result: {'PASS' if overall_pass else 'FAIL'}
"""

    return report


def write_report_files(output_dir: Path, metrics: RepeatabilityMetrics,
                       reports: List[SessionReport]) -> None:
    """Write repeatability analysis reports to files.

    Writes two files to output_dir:
        - report.txt: Human-readable text summary
        - repeatability_metrics.json: Machine-readable metrics

    Args:
        output_dir: Directory to write reports
        metrics: RepeatabilityMetrics to analyze
        reports: List of SessionReport objects for per-session info
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Text report
    text_report = generate_text_report(metrics)
    with open(output_dir / 'report.txt', 'w') as f:
        f.write(text_report)

    # JSON metrics
    metrics_dict = {
        'num_sessions': metrics.num_sessions,
        'offset_mean_of_means_us': metrics.offset_mean_of_means_us,
        'offset_std_of_means_us': metrics.offset_std_of_means_us,
        'offset_min_mean_us': metrics.offset_min_mean_us,
        'offset_max_mean_us': metrics.offset_max_mean_us,
        'std_dev_of_stds_us': metrics.std_dev_of_stds_us,
        'acceptance_rate_mean': metrics.acceptance_rate_mean,
        'acceptance_rate_std': metrics.acceptance_rate_std,
        'acceptance_rate_min': metrics.acceptance_rate_min,
        'acceptance_rate_max': metrics.acceptance_rate_max,
        'conformance': {
            'means_within_target': metrics.means_within_target,
            'acceptance_rate_high': metrics.acceptance_rate_high,
            'variance_consistent': metrics.variance_consistent,
            'overall_pass': all([
                metrics.means_within_target,
                metrics.acceptance_rate_high,
                metrics.variance_consistent,
            ]),
        },
        'per_session': [
            {
                'session_num': r.session_num,
                'total_attempts': r.total_attempts,
                'accepted_count': r.accepted_count,
                'acceptance_rate': r.acceptance_rate,
                'offset_mean_us': r.offset_mean_us,
                'offset_std_us': r.offset_std_us,
                'offset_min_us': r.offset_min_us,
                'offset_max_us': r.offset_max_us,
                'percentile_50_us': r.percentile_50_us,
                'percentile_95_us': r.percentile_95_us,
            }
            for r in reports
        ]
    }

    with open(output_dir / 'repeatability_metrics.json', 'w') as f:
        json.dump(metrics_dict, f, indent=2)
