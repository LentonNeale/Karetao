#!/usr/bin/env python3
"""Send repeated TIME_SYNC requests to measure STM32 synchronization.

Records offset candidates, computes statistics, and optionally saves CSV logs.
Each TIME_SYNC is one exchange through the exchange session (spi/exchange.py):
its ACK or NACK arrives on a later transaction and is matched by request_seq.
Pi times come from the session's raw monotonic clock (ruling R16). TIME_SYNC is
the as-built mechanism that Issue #12 retires (#45).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.data_ready import DataReadyWatcher, DEFAULT_DATA_READY_LINE
from spi.exchange import ExchangeSession, Outcome, Request, now_ns
from spi.fake_backend import FakeFirmware
from spi.spi_bus import SpiBus, SpiBusConfig
from spi.spi_protocol import (
    MessageType,
    encode_time_sync_payload,
    decode_command_reply,
)
from spi.time_sync_session import TimeSyncSession
from spi.time_sync_analysis import compute_stats, percentiles


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description='Send repeated TIME_SYNC requests and measure synchronization offsets'
    )
    parser.add_argument('--device', default='/dev/spidev0.0',
                        help='SPI device path')
    parser.add_argument('--speed-hz', type=int, default=1_000_000,
                        help='SPI clock speed in Hz')
    parser.add_argument('--transactions', type=int, default=100,
                        help='Number of TIME_SYNC requests to send')
    parser.add_argument('--budget', type=int, default=4,
                        help='Most transactions each TIME_SYNC exchange may clock, its own '
                             'included (at least 2: the reply arrives one transaction late)')
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
    parser.add_argument('--fake', action='store_true',
                        help='Run against the firmware-rules fake instead of the bus')
    args = parser.parse_args(argv)
    if args.budget < 2:
        parser.error('--budget must be at least 2: the reply arrives one transaction late')
    if args.data_ready and args.fake:
        parser.error('--data-ready requires real GPIO hardware; incompatible with --fake')

    data_ready = None
    bus = None
    try:
        # Setup GPIO DATA_READY if requested
        if args.data_ready:
            data_ready = DataReadyWatcher(line_offset=args.data_ready_line)

        # Setup SPI bus
        bus = SpiBus(SpiBusConfig(device=args.device, max_speed_hz=args.speed_hz),
                     backend=FakeFirmware() if args.fake else None)
        bus.open()

        # One exchange session owns the link; the TIME_SYNC session tracks offsets
        session = TimeSyncSession(initial_offset_us=0, drift_limit_us_per_sec=1000.0)
        exchanges = ExchangeSession(
            bus=bus, block_id='time_sync', data_ready=data_ready,
            min_interval_s=0.0 if data_ready is not None else args.interval_ms / 1000.0)

        print(f'device={"fake" if args.fake else args.device} speed={args.speed_hz} Hz')
        print(f'transactions={args.transactions} interval_ms={args.interval_ms} budget={args.budget}')
        print(f'data_ready={args.data_ready}\n')

        for index in range(args.transactions):
            # sync_seq is the header seq the session is about to assign: the payload is built
            # before the exchange sends it, and this thread is the session's only caller.
            sync_seq = exchanges.sequencer.peek()

            # Spend the pacing gap before stamping, so the session sends at once and pi_time_us is
            # the send time rather than the time before a pacing sleep. With --data-ready the
            # session's DATA_READY wait still sits between the stamp and the send.
            if data_ready is None and index > 0:
                time.sleep(args.interval_ms / 1000.0)

            # Record request time (Pi time)
            t_start_us = now_ns() // 1000
            session.record_request(seq=sync_seq, pi_time_us=t_start_us)

            payload = encode_time_sync_payload(pi_time_us=t_start_us, sync_seq=sync_seq)
            result = exchanges.exchange(Request(MessageType.TIME_SYNC, payload), budget=args.budget)

            if result.request_seq != sync_seq:
                # Another user of the process sequencer drew a seq between peek() and the send,
                # so the payload names a seq the header does not carry.
                if args.verbose:
                    print(f'tx{index:03d} seq={sync_seq:10d} — sent as seq {result.request_seq}, sample dropped')
                continue

            if result.outcome is Outcome.EXHAUSTED:
                if args.verbose:
                    print(f'tx{index:03d} seq={sync_seq:10d} — no reply within {args.budget} transactions')
                continue

            # Decode the ACK or NACK that named this request
            try:
                _, status_code, _, _ = decode_command_reply(result.reply.payload)
            except ValueError as exc:
                if args.verbose:
                    print(f'tx{index:03d} seq={sync_seq:10d} — decode error: {exc}')
                continue

            # Create candidate (stm32_local_us is TBD via SWD); T4 is the receipt of the reply
            candidate = session.record_response(
                seq=sync_seq,
                pi_time_us_stm32=t_start_us,  # Echo of request pi_time (TBD from response)
                stm32_local_us=0,  # TBD from SWD
                status_code=status_code,
                pi_time_us_received=result.records[-1].t4_response_received_ns // 1000
            )

            if args.verbose:
                status_str = 'ACK' if candidate.is_accepted() else f'NACK({status_code})'
                print(f'tx{index:03d} seq={sync_seq:10d} — {status_str} offset={candidate.offset_us:+d} µs')

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
