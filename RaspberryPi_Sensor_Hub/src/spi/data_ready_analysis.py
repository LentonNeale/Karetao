"""Analysis of DATA_READY GPIO timing characteristics.

Computes statistics for the three key DATA_READY measurements:

1. DATA_READY to NSS fall (transfer start latency): time from DATA_READY
   rising edge to NSS falling edge. Target: within cable propagation delay
   (~5 µs per 30cm; SYS-SPI-004 conservative bound is 5 ms).

2. NSS rise to DATA_READY fall (pipelined latency): time from NSS rising
   edge (end of transfer) to DATA_READY falling edge (response no longer
   valid). Characterizes the firmware's pipeline delay.

3. DATA_READY interval (time between consecutive rising edges): cycle time
   for the pipelined transaction loop. Dominated by firmware processing
   delay and sensor polling interval.

Reference: SPI_SYSTEM_INTERFACE.md sections 4, 7, 16.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import statistics


@dataclass
class DataReadyStats:
    """Summary statistics for DATA_READY timing measurements.

    All optional fields will be None if there are no measurements of that type.
    """
    total_measurements: int

    # DATA_READY to NSS fall latency (DATA_READY rise to transfer start)
    dr_to_nss_mean_us: Optional[float] = None
    dr_to_nss_std_us: Optional[float] = None
    dr_to_nss_min_us: Optional[int] = None
    dr_to_nss_max_us: Optional[int] = None

    # NSS rise to DATA_READY fall interval (pipelined latency)
    nss_to_dr_mean_us: Optional[float] = None
    nss_to_dr_std_us: Optional[float] = None
    nss_to_dr_min_us: Optional[int] = None
    nss_to_dr_max_us: Optional[int] = None

    # DATA_READY interval (consecutive rising edges)
    dr_interval_mean_us: Optional[float] = None
    dr_interval_std_us: Optional[float] = None
    dr_interval_min_us: Optional[int] = None
    dr_interval_max_us: Optional[int] = None

    # Conformance checks
    dr_to_nss_within_cable_delay: bool = False
    firmware_loop_delay_plausible: bool = False


def compute_data_ready_stats(records: List) -> DataReadyStats:
    """Compute DATA_READY timing statistics from transaction records.

    Args:
        records: List of TransactionRecord objects with DATA_READY measurements.

    Returns:
        DataReadyStats with mean/std/min/max for each measurement type.
    """
    # Filter for records with each type of DATA_READY measurement
    dr_to_nss = [r.data_ready_to_nss_low_us for r in records
                 if r.data_ready_to_nss_low_us is not None]
    nss_to_dr = [r.nss_high_to_data_ready_low_us for r in records
                 if r.nss_high_to_data_ready_low_us is not None]
    dr_interval = [r.data_ready_interval_us for r in records
                   if r.data_ready_interval_us is not None]

    def stats_for_list(values):
        """Extract mean, std, min, max from a list of values."""
        if not values:
            return None, None, None, None
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0.0
        return (mean_val, std_val, min(values), max(values))

    dr_to_nss_mean, dr_to_nss_std, dr_to_nss_min, dr_to_nss_max = stats_for_list(dr_to_nss)
    nss_to_dr_mean, nss_to_dr_std, nss_to_dr_min, nss_to_dr_max = stats_for_list(nss_to_dr)
    dr_interval_mean, dr_interval_std, dr_interval_min, dr_interval_max = stats_for_list(dr_interval)

    # Conformance checks
    # DATA_READY to NSS fall must be within cable propagation delay
    # Conservative bound: 5 ms for 30cm cable at ~170 ns/meter
    dr_to_nss_compliant = (dr_to_nss_max is None) or (dr_to_nss_max < 5000)

    # Firmware loop delay plausibility check:
    # NSS to DATA_READY fall + sensor polling should be <= known firmware max
    # From timing.py: TX_RX_CMPLT_CALLBACK_LATENCY_US = 40 µs
    # Conservative: check that nss_to_dr is plausible (not > 1s)
    firmware_plausible = (nss_to_dr_max is None) or (nss_to_dr_max < 1_000_000)

    return DataReadyStats(
        total_measurements=len(records),
        dr_to_nss_mean_us=dr_to_nss_mean,
        dr_to_nss_std_us=dr_to_nss_std,
        dr_to_nss_min_us=dr_to_nss_min,
        dr_to_nss_max_us=dr_to_nss_max,
        nss_to_dr_mean_us=nss_to_dr_mean,
        nss_to_dr_std_us=nss_to_dr_std,
        nss_to_dr_min_us=nss_to_dr_min,
        nss_to_dr_max_us=nss_to_dr_max,
        dr_interval_mean_us=dr_interval_mean,
        dr_interval_std_us=dr_interval_std,
        dr_interval_min_us=dr_interval_min,
        dr_interval_max_us=dr_interval_max,
        dr_to_nss_within_cable_delay=dr_to_nss_compliant,
        firmware_loop_delay_plausible=firmware_plausible,
    )


def percentile_data_ready_latency(records: List, percentiles: List[int] = None) -> dict:
    """Compute percentile DATA_READY to NSS fall latencies.

    Args:
        records: List of TransactionRecord objects.
        percentiles: List of percentile points (5, 50, 95, etc.).
                    Defaults to [5, 50, 95].

    Returns:
        Dictionary mapping percentile point to latency in microseconds.
        Returns None for percentiles where no data is available.
    """
    if percentiles is None:
        percentiles = [5, 50, 95]

    latencies = [r.data_ready_to_nss_low_us for r in records
                 if r.data_ready_to_nss_low_us is not None]

    if not latencies:
        return {p: None for p in percentiles}

    latencies.sort()
    result = {}

    for p in percentiles:
        # Nearest-rank percentile (same as timing.percentiles())
        rank = max(1, min(len(latencies), round(p / 100.0 * len(latencies))))
        result[p] = latencies[rank - 1]

    return result
