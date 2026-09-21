#!/usr/bin/env python3
"""Send repeated TIME_SYNC requests to measure STM32 synchronization.

Records offset candidates, computes statistics, and optionally saves CSV logs.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.data_ready import DataReadyWatcher, DEFAULT_DATA_READY_LINE
from spi.spi_bus import SpiBus, SpiBusConfig
from spi.spi_device import SpiDevice
from spi.spi_protocol import (
    SpiFrame,
    MessageType,
    encode_time_sync_payload,
    decode_command_reply,
    initial_sequence,
)
from spi.time_sync_session import TimeSyncSession
from spi.time_sync_analysis import compute_stats, percentiles


def get_monotonic_time_us() -> int:
    """Get current time in microseconds (monotonic)."""
    return int(time.monotonic() * 1e6)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Send repeated TIME_SYNC requests and measure synchronization offsets'
    )
    parser.add_argument('--device', default='/dev/spidev0.0',
                        help='SPI device path')
    parser.add_argument('--speed-hz', type=int, default=1_000_000,
                        help='SPI clock speed in Hz')
    parser.add_argument('--transactions', type=int, default=100,
                        help='Number of TIME_SYNC requests to send')
    parser.add_argument('--interval-ms', type=float, default=50.0,
                        help='Delay between transactions (ms, used if --data-ready not set)')
    parser.add_argument('--data-ready', action='store_true',
                        help='Wait for DATA_READY GPIO before each transfer')
    parser.add_argument('--data-ready-line', type=int, default=DEFAULT_DATA_READY_LINE,
                        help='GPIO line number for DATA_READY')
    parser.add_argument('--output', metavar='CSV',
                        help='Save CSV log to file')
    parser.add_argument('--verbose', action='store_true',
                        help='Print detailed output for each transaction')
    args = parser.parse_args()

    data_ready = None
    bus = None
    try:
        # Setup GPIO DATA_READY if requested
        if args.data_ready:
            data_ready = DataReadyWatcher(line_offset=args.data_ready_line)

        # Setup SPI bus
        bus = SpiBus(SpiBusConfig(device=args.device, max_speed_hz=args.speed_hz))
        bus.open()

        # Initialize session and device
        session = TimeSyncSession(initial_offset_us=0, drift_limit_us_per_sec=1000.0)
        device = SpiDevice(bus)
        seq_start = initial_sequence()

        print(f'device={args.device} speed={args.speed_hz} Hz')
        print(f'transactions={args.transactions} interval_ms={args.interval_ms}')
        print(f'data_ready={args.data_ready}\n')

        for index in range(args.transactions):
            sync_seq = seq_start + index

            # Record request time (Pi time)
            t_start_us = get_monotonic_time_us()
            session.record_request(seq=sync_seq, pi_time_us=t_start_us)

            # Wait for DATA_READY or fixed interval
            if data_ready is not None:
                if not data_ready.wait_for_ready(timeout_s=0.5):
                    if args.verbose:
                        print(f'tx{index:03d} seq={sync_seq:10d} — DATA_READY timeout, skipping')
                    continue

            # Build and send TIME_SYNC request
            payload = encode_time_sync_payload(pi_time_us=t_start_us, sync_seq=sync_seq)
            request = SpiFrame(
                message_type=MessageType.TIME_SYNC,
                seq=sync_seq,
                payload=payload
            )

            # Transact
            try:
                response = device.transact(request)
            except Exception as exc:
                if args.verbose:
                    print(f'tx{index:03d} seq={sync_seq:10d} — error: {exc}')
                continue

            # Record response time (Pi time)
            t_end_us = get_monotonic_time_us()

            # Decode response
            try:
                req_type, status_code, resp_seq, detail = decode_command_reply(response.payload)
            except ValueError as exc:
                if args.verbose:
                    print(f'tx{index:03d} seq={sync_seq:10d} — decode error: {exc}')
                continue

            # Verify sequence match
            if resp_seq != sync_seq:
                if args.verbose:
                    print(f'tx{index:03d} seq={sync_seq:10d} — response seq mismatch: got {resp_seq}')
                continue

            # Create candidate (stm32_local_us is TBD via SWD)
            candidate = session.record_response(
                seq=sync_seq,
                pi_time_us_stm32=t_start_us,  # Echo of request pi_time (TBD from response)
                stm32_local_us=0,  # TBD from SWD
                status_code=status_code,
                pi_time_us_received=t_end_us
            )

            if args.verbose:
                status_str = 'ACK' if candidate.is_accepted() else f'NACK({status_code})'
                print(f'tx{index:03d} seq={sync_seq:10d} — {status_str} offset={candidate.offset_us:+d} µs')

            # Wait before next transaction
            if data_ready is None:
                time.sleep(args.interval_ms / 1000.0)

        # Compute and display statistics
        print('\n' + '='*70)
        print('STATISTICS')
        print('='*70)
        stats = compute_stats(session)
        print(f'Total attempts:      {stats.total_attempts}')
        print(f'Accepted:            {stats.accepted_count}')
        print(f'Rejected:            {stats.rejected_count}')
        print(f'Acceptance rate:     {stats.acceptance_rate*100:.1f}%')
        if stats.nack_distribution:
            print(f'Rejection reasons:   {", ".join(f"{k}({v})" for k, v in stats.nack_distribution.items())}')
        print()
        print(f'Offset (accepted only):')
        print(f'  Mean:              {stats.offset_mean_us:+.0f} µs')
        print(f'  Std dev:           {stats.offset_std_us:+.0f} µs')
        print(f'  Min:               {stats.offset_min_us:+d} µs')
        print(f'  Max:               {stats.offset_max_us:+d} µs')
        print()
        print(f'Uncertainty bounds (all):')
        print(f'  Mean uncertainty_min: {stats.uncertainty_mean_min_us:.0f} µs')
        print(f'  Mean uncertainty_max: {stats.uncertainty_mean_max_us:.0f} µs')
        if stats.drift_rate_us_per_sec is not None:
            print()
            print(f'Drift rate (accepted): {stats.drift_rate_us_per_sec:+.1f} µs/s')

        print()
        p = percentiles(session, [5, 25, 50, 75, 95])
        print(f'Percentiles (accepted):')
        print(f'  p5:                {p[5]:+d} µs')
        print(f'  p25:               {p[25]:+d} µs')
        print(f'  p50 (median):      {p[50]:+d} µs')
        print(f'  p75:               {p[75]:+d} µs')
        print(f'  p95:               {p[95]:+d} µs')

        # Save CSV log if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(TimeSyncSession.to_csv_header() + '\n')
                for row in session.to_csv_rows():
                    f.write(row + '\n')
            print(f'\nCSV log saved to: {args.output}')

        return 0

    except KeyboardInterrupt:
        print('\n\nInterrupted by user')
        return 130
    except Exception as exc:
        print(f'\nFatal error: {exc}', file=sys.stderr)
        return 1
    finally:
        if bus is not None:
            bus.close()
        if data_ready is not None:
            data_ready.close()


if __name__ == '__main__':
    raise SystemExit(main())
