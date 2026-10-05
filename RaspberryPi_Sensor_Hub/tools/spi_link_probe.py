#!/usr/bin/env python3
"""Dump what the STM32 actually returns, to classify a non-responsive link.

`get_version()` treats an undecodable transfer as "not yet" and retries, which
is right for an occasional glitch but collapses every persistent fault into the
same timeout. This probe keeps the raw bytes so the fault can be named: a
silent MISO, a byte-shifted frame, a firmware that rejects the request, and a
firmware that never answers all look identical through the normal client.

Read-only: it clocks GET_VERSION once, then GET_STATUS, and reports. It changes
no device state beyond the sequence numbers it consumes.

With --snapshot it also clocks GET_SNAPSHOT once and prints the decoded sensor
records (id, validity flag names, angles, timestamp), still read-only.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.data_ready import DataReadyWatcher, DEFAULT_DATA_READY_LINE  # noqa: E402
from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_protocol import (  # noqa: E402
    MAGIC,
    MessageType,
    NackReason,
    SENSOR_VALIDITY_COMMUNICATION_ERROR,
    SENSOR_VALIDITY_MAGNET_NOT_DETECTED,
    SENSOR_VALIDITY_MAGNET_TOO_STRONG,
    SENSOR_VALIDITY_MAGNET_TOO_WEAK,
    SENSOR_VALIDITY_NOT_FITTED,
    SENSOR_VALIDITY_SAMPLE_VALID,
    SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED,
    SpiFrame,
    decode_snapshot_sensor_records,
    initial_sequence,
)

MAGIC_LE = struct.pack('<H', MAGIC)

VALIDITY_FLAG_NAMES = (
    (SENSOR_VALIDITY_SAMPLE_VALID, 'SAMPLE_VALID'),
    (SENSOR_VALIDITY_COMMUNICATION_ERROR, 'COMMUNICATION_ERROR'),
    (SENSOR_VALIDITY_MAGNET_NOT_DETECTED, 'MAGNET_NOT_DETECTED'),
    (SENSOR_VALIDITY_MAGNET_TOO_WEAK, 'MAGNET_TOO_WEAK'),
    (SENSOR_VALIDITY_MAGNET_TOO_STRONG, 'MAGNET_TOO_STRONG'),
    (SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED, 'TIMESTAMP_SYNCHRONIZED'),
    (SENSOR_VALIDITY_NOT_FITTED, 'NOT_FITTED'),
)


def snapshot_lines(raw: bytes) -> list[str]:
    """One line per sensor record when raw is a SNAPSHOT frame, otherwise no lines."""
    try:
        frame = SpiFrame.decode(raw)
        if frame.message_type is not MessageType.SNAPSHOT:
            return []
        records = decode_snapshot_sensor_records(frame.payload)
    except ValueError as exc:
        return [f'     snapshot sensor records undecodable ({exc})']
    lines = []
    for record in records:
        names = [name for bit, name in VALIDITY_FLAG_NAMES if record.validity_flags & bit]
        lines.append(f'     sensor {record.sensor_id}: flags={"|".join(names) or "none"} '
                     f'raw_angle={record.raw_angle} processed_mdeg={record.processed_angle_mdeg} '
                     f'timestamp_us={record.measurement_timestamp_us}')
    return lines


def classify(raw: bytes) -> str:
    """Name the failure mode a raw response shows, before any frame decoding."""
    if not raw:
        return 'empty transfer'
    if all(byte == 0x00 for byte in raw):
        return ('all zero bytes -- MISO is never driven high. The STM32 is not '
                'transmitting: check power, that the firmware is running, and MISO wiring')
    if all(byte == 0xFF for byte in raw):
        return ('all 0xFF -- MISO idles high with nothing driving it. Check MISO wiring '
                'and that the STM32 SPI peripheral is enabled')
    offset = raw.find(MAGIC_LE)
    if offset < 0:
        return 'no frame magic anywhere in the transfer -- data is present but unframed'
    if offset > 0:
        return (f'frame magic found at byte offset {offset}, not 0 -- the response is '
                f'shifted by {offset} byte(s), so DMA was armed late relative to NSS')
    return 'magic at offset 0'


def describe(raw: bytes) -> str:
    try:
        frame = SpiFrame.decode(raw)
    except ValueError as exc:
        return f'undecodable ({exc})'

    detail = f'{frame.message_type.name} seq={frame.seq} payload={len(frame.payload)}B'
    if frame.message_type is MessageType.NACK and len(frame.payload) >= 8:
        status, nacked = struct.unpack_from('<HI', frame.payload, 2)
        detail += f' rejected_seq={nacked} reason={NackReason.describe(status)}'
    elif frame.payload:
        detail += f' head={frame.payload[:12].hex(" ")}'
    return detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--speed-hz', type=int, default=1_000_000)
    parser.add_argument('--transactions', type=int, default=10)
    parser.add_argument('--interval-ms', type=float, default=20.0,
                        help='Fixed delay between transfers when --data-ready is not given. '
                             'This is a fallback, not a fix: the firmware only rearms DMA for '
                             'the next transfer when its bare-metal main loop next runs '
                             '(spi_slave_service.c SpiSlaveService_Process), so any fixed delay '
                             'is a guess at that timing rather than a guarantee of it.')
    parser.add_argument('--data-ready', action='store_true',
                        help='Wait for DATA_READY (SD-17) before each transfer instead of a '
                             'fixed delay. This is what the transaction is actually gated on, '
                             'so prefer it over --interval-ms when diagnosing corruption.')
    parser.add_argument('--data-ready-line', type=int, default=DEFAULT_DATA_READY_LINE)
    parser.add_argument('--snapshot', action='store_true',
                        help='Also send GET_SNAPSHOT (as the second request) and print each '
                             'sensor record from its reply, which arrives on the next transfer. '
                             'Needs at least 3 transactions.')
    args = parser.parse_args()

    data_ready = DataReadyWatcher(line_offset=args.data_ready_line) if args.data_ready else None
    bus = SpiBus(SpiBusConfig(max_speed_hz=args.speed_hz))
    bus.open()
    sequence = initial_sequence()
    seen_magic = False
    seen_version = False
    replies: dict[str, int] = {}

    print(f'device={bus.config.device} speed={args.speed_hz} Hz '
          f'start_seq={sequence} transactions={args.transactions}\n')
    try:
        for index in range(args.transactions):
            # Ask for the version first; later transfers clock out its reply,
            # since the device stages a response only after reading the request.
            kind = MessageType.GET_VERSION if index == 0 else MessageType.GET_STATUS
            if args.snapshot and index == 1:
                kind = MessageType.GET_SNAPSHOT
            request = SpiFrame(message_type=kind, seq=sequence + index, payload=b'\x01')
            if data_ready is not None:
                t0 = time.monotonic()
                ready = data_ready.wait_for_ready(0.2)
                elapsed_ms = (time.monotonic() - t0) * 1000
                if not ready:
                    print(f'tx{index:02d} sent {kind.name:12s} -> [skipped: DATA_READY not asserted within 200ms]')
                    continue
                print(f'     (DATA_READY was already/became asserted after {elapsed_ms:.1f} ms)')
            raw = bus.transfer(request.encode())

            shape = classify(raw)
            decoded = describe(raw)
            if 'magic at offset 0' in shape:
                seen_magic = True
            if decoded.startswith('VERSION'):
                seen_version = True
            replies[decoded.split(' ')[0]] = replies.get(decoded.split(' ')[0], 0) + 1

            print(f'tx{index:02d} sent {kind.name:12s} -> {decoded}')
            if args.snapshot:
                for line in snapshot_lines(raw):
                    print(line)
            if 'magic at offset 0' not in shape:
                print(f'     {shape}')
                print(f'     first 24 bytes: {raw[:24].hex(" ")}')
            if data_ready is None:
                time.sleep(args.interval_ms / 1000.0)
    finally:
        bus.close()
        if data_ready is not None:
            data_ready.close()

    print('\nreply frames seen:', ', '.join(f'{k}x{v}' for k, v in replies.items()) or 'none')
    if seen_version:
        print('VERDICT: firmware answered GET_VERSION. The link works.')
    elif not seen_magic:
        print('VERDICT: no well-framed response at all -- treat this as a wiring, power, '
              'or firmware-not-running fault before looking at the protocol.')
    elif 'NACK' in replies:
        if not args.data_ready:
            print('VERDICT: firmware is alive and framing correctly but refused the request. '
                  'This run used a fixed --interval-ms delay, not DATA_READY: if the rejected '
                  'sequence numbers printed above climb by a fixed power-of-256 step instead of '
                  'matching real host sequence numbers, that is a request corrupted in transit, '
                  'not a real protocol rejection -- rerun with --data-ready before concluding '
                  'anything about wiring or firmware logic.')
        else:
            print('VERDICT: firmware is alive and framing correctly but refused the request, '
                  'even with DATA_READY pacing; the reason printed above is authoritative.')
    else:
        print('VERDICT: firmware is alive and framing correctly but never sent VERSION. '
              'The running build most likely predates GET_VERSION (0x14) support -- '
              'rebuild and reflash, then power-cycle the STM32.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
