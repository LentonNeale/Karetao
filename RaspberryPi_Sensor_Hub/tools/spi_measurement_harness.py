#!/usr/bin/env python3
"""Run multiple TIME_SYNC measurement sessions and generate repeatability report.

This harness orchestrates running the spi_time_sync_probe multiple times,
collecting statistics from each session, and generating a cross-session
repeatability analysis report.

Example:
    python tools/spi_measurement_harness.py --sessions 5 --transactions-per-session 100
    # Runs 5 measurement sessions with 100 transactions each
    # Creates output_directory/session_NNN.csv for each session
    # Generates repeatability_metrics.json and report.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.measurement_report import (
    load_session_csv, compute_repeatability_metrics, write_report_files, SessionReport
)


def run_probe_session(session_num: int, csv_file: Path, args: argparse.Namespace) -> dict | None:
    """Execute one spi_time_sync_probe session and return result metadata.

    Args:
        session_num: Session index (1-based)
        csv_file: Path where probe should write CSV output
        args: Parsed command-line arguments

    Returns:
        Dict with session metadata if successful, None if probe failed
    """

    # Construct probe command
    probe_script = Path(__file__).parent / 'spi_time_sync_probe.py'
    cmd = [
        sys.executable, str(probe_script),
        '--device', args.device,
        '--speed-hz', str(args.speed_hz),
        '--transactions', str(args.transactions_per_session),
        '--interval-ms', str(args.interval_ms),
        '--output', str(csv_file),
    ]

    if args.data_ready:
        cmd.append('--data-ready')
        if args.data_ready_line is not None:
            cmd.extend(['--data-ready-line', str(args.data_ready_line)])

    if args.verbose:
        cmd.append('--verbose')

    # Run probe
    print(f'[Session {session_num:2d}] Starting ({args.transactions_per_session} transactions)...', end=' ', flush=True)
    start_time = time.monotonic()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                               cwd=Path(__file__).parent.parent)
        elapsed = time.monotonic() - start_time

        if result.returncode != 0:
            print(f'FAILED (exit {result.returncode})')
            if args.verbose:
                print(f'  stderr: {result.stderr}')
            return None

        print(f'OK ({elapsed:.1f}s)')

        return {
            'session': session_num,
            'csv_file': str(csv_file),
            'elapsed_s': elapsed,
            'returncode': result.returncode,
        }

    except subprocess.TimeoutExpired:
        print(f'TIMEOUT (>300s)')
        return None
    except Exception as exc:
        print(f'ERROR: {exc}')
        return None


def main() -> int:
    """Run multiple measurement sessions and generate repeatability report."""

    parser = argparse.ArgumentParser(
        description='Run multiple TIME_SYNC measurement sessions and analyze repeatability'
    )
    parser.add_argument('--device', default='/dev/spidev0.0',
                        help='SPI device path (default: /dev/spidev0.0)')
    parser.add_argument('--speed-hz', type=int, default=1_000_000,
                        help='SPI clock speed in Hz (default: 1 MHz)')
    parser.add_argument('--sessions', type=int, default=5,
                        help='Number of measurement sessions to run (default: 5)')
    parser.add_argument('--transactions-per-session', type=int, default=100,
                        help='TIME_SYNC transactions per session (default: 100)')
    parser.add_argument('--interval-ms', type=float, default=50.0,
                        help='Delay between transactions in ms (default: 50 ms, used if --data-ready not set)')
    parser.add_argument('--data-ready', action='store_true',
                        help='Use DATA_READY GPIO instead of fixed interval')
    parser.add_argument('--data-ready-line', type=int, default=None,
                        help='GPIO line number for DATA_READY')
    parser.add_argument('--output-dir', type=Path, default=Path('measurement_results'),
                        help='Directory to save results (default: measurement_results)')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose output from probe')
    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run sessions
    print(f'Running {args.sessions} TIME_SYNC measurement sessions...\n')
    session_metadata = []
    csv_files = []

    for i in range(1, args.sessions + 1):
        csv_file = args.output_dir / f'session_{i:03d}.csv'
        result = run_probe_session(i, csv_file, args)

        if result:
            session_metadata.append(result)
            csv_files.append(csv_file)

        # Brief pause between sessions
        if i < args.sessions:
            time.sleep(1)

    if not session_metadata:
        print('\nNo successful sessions completed', file=sys.stderr)
        return 1

    print(f'\nSuccessfully completed {len(session_metadata)}/{args.sessions} sessions')

    # Load and analyze session statistics
    print('Loading and analyzing session data...')
    reports: list[SessionReport] = []

    for i, csv_file in enumerate(csv_files, 1):
        report = load_session_csv(csv_file)
        if report:
            # Set session number
            object.__setattr__(report, 'session_num', i)
            reports.append(report)
            print(f'  Session {i}: {report.total_attempts} attempts, '
                  f'{report.accepted_count} accepted ({report.acceptance_rate*100:.1f}%), '
                  f'offset {report.offset_mean_us:+.0f}±{report.offset_std_us:.0f} µs')

    if not reports:
        print('Failed to load any session data', file=sys.stderr)
        return 1

    # Compute repeatability metrics
    print('\nComputing repeatability metrics...')
    metrics = compute_repeatability_metrics(reports)

    # Write reports
    write_report_files(args.output_dir, metrics, reports)

    # Display summary
    print(f'\n' + '='*70)
    print('REPEATABILITY ANALYSIS SUMMARY')
    print('='*70)
    print(f'Sessions: {metrics.num_sessions}')
    print(f'Offset (mean of means): {metrics.offset_mean_of_means_us:+.0f} µs')
    print(f'Offset (std of means): {metrics.offset_std_of_means_us:+.0f} µs')
    print(f'Range: {metrics.offset_min_mean_us:+d} to {metrics.offset_max_mean_us:+d} µs')
    print(f'Acceptance rate: {metrics.acceptance_rate_mean*100:.1f}% '
          f'(range {metrics.acceptance_rate_min*100:.1f}%-{metrics.acceptance_rate_max*100:.1f}%)')
    print()
    print('Conformance checks:')
    print(f'  ✓ Means within ±1ms: {metrics.means_within_target}')
    print(f'  ✓ Acceptance >= 90%:  {metrics.acceptance_rate_high}')
    print(f'  ✓ Variance consistent: {metrics.variance_consistent}')
    print()
    overall_pass = all([
        metrics.means_within_target,
        metrics.acceptance_rate_high,
        metrics.variance_consistent,
    ])
    print(f'Overall: {"PASS" if overall_pass else "FAIL"}')

    # Save metadata
    metadata = {
        'timestamp': datetime.utcnow().isoformat(),
        'device': args.device,
        'speed_hz': args.speed_hz,
        'sessions': len(session_metadata),
        'transactions_per_session': args.transactions_per_session,
        'interval_ms': args.interval_ms,
        'data_ready': args.data_ready,
        'data_ready_line': args.data_ready_line,
    }
    with open(args.output_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f'\nResults saved to: {args.output_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
