#!/usr/bin/env python3
"""Dump what the STM32 actually returns, to classify a non-responsive link.

An exchange that ends without a reply collapses every persistent fault into one
outcome. This probe prints every transaction of the exchange, keeping the raw
bytes of any that did not decode, so the fault can be named: a silent MISO, a
byte-shifted frame, a firmware that rejects the request, and a firmware that
never answers.

Read-only: it runs one GET_VERSION exchange through the exchange session
(spi/exchange.py) and reports. It changes no device state beyond the sequence
numbers it consumes. The VERSION reply is printed decoded (firmware version,
git hash, build flags with the dirty bit, protocol version, commit epoch).

With --snapshot it then runs one GET_SNAPSHOT exchange and prints the decoded
sensor records (id, validity flag names, angles, timestamp), still read-only.
With --fake it runs against the firmware-rules fake (spi/fake_backend.py)
instead of the bus, which exercises the probe itself, not the link.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.data_ready import DataReadyWatcher, DEFAULT_DATA_READY_LINE  # noqa: E402
from spi.exchange import (  # noqa: E402
    GET_REQUEST_PAYLOAD,
    ExchangeResult,
    ExchangeSession,
    Outcome,
    Request,
    TransactionRecord,
)
from spi.fake_backend import FakeFirmware  # noqa: E402
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
    SpiFrame,
    VersionInfo,
    decode_snapshot_sensor_records,
)

MAGIC_LE = struct.pack('<H', MAGIC)
GET_VERSION = Request(MessageType.GET_VERSION, GET_REQUEST_PAYLOAD)
GET_SNAPSHOT = Request(MessageType.GET_SNAPSHOT, GET_REQUEST_PAYLOAD)

VALIDITY_FLAG_NAMES = (
    (SENSOR_VALIDITY_SAMPLE_VALID, 'SAMPLE_VALID'),
    (SENSOR_VALIDITY_COMMUNICATION_ERROR, 'COMMUNICATION_ERROR'),
    (SENSOR_VALIDITY_MAGNET_NOT_DETECTED, 'MAGNET_NOT_DETECTED'),
    (SENSOR_VALIDITY_MAGNET_TOO_WEAK, 'MAGNET_TOO_WEAK'),
    (SENSOR_VALIDITY_MAGNET_TOO_STRONG, 'MAGNET_TOO_STRONG'),
    (SENSOR_VALIDITY_NOT_FITTED, 'NOT_FITTED'),
)


def snapshot_lines(frame: SpiFrame) -> list[str]:
    """One line per sensor record when frame is a SNAPSHOT, otherwise no lines."""
    if frame.message_type is not MessageType.SNAPSHOT:
        return []
    try:
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


def version_lines(frame: SpiFrame) -> list[str]:
    """One decoded line when frame is a VERSION, otherwise no lines.

    ENCODER_BENCH_PROCEDURE.md reads git_hash_abbrev and dirty from this line.
    """
    if frame.message_type is not MessageType.VERSION:
        return []
    try:
        v = VersionInfo.decode(frame.payload)
    except ValueError as exc:
        return [f'     VERSION payload undecodable ({exc})']
    return [f'     firmware_version={v.firmware_version} git_hash_abbrev={v.git_hash} '
            f'build_flags=0x{v.build_flags:02x} dirty={"yes" if v.is_dirty_build else "no"} '
            f'protocol_version={v.protocol_version} commit_epoch_secs={v.commit_epoch_secs}']


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


def record_lines(record: TransactionRecord) -> list[str]:
    """What one transaction sent and received; an undecodable response is classified."""
    sent = f'tx{record.index:02d} sent {record.request_type:12s} seq={record.request_seq} -> '
    lines = []
    if record.data_ready_timed_out:
        lines.append(f'     (DATA_READY not asserted within the session wait, PRM-SPI-04; clocked anyway)')
    if not record.ok:
        raw = record.raw_response or b''
        lines.append(sent + f'undecodable ({record.error})')
        lines.append(f'     {classify(raw)}')
        lines.append(f'     first 24 bytes: {raw[:24].hex(" ")}')
        return lines
    detail = f'{record.response_type} seq={record.response_seq}'
    if record.correlated_seq is not None:
        detail += f' answers={record.correlated_seq}'
    if record.nack_status_code is not None:
        detail += f' reason={NackReason.describe(record.nack_status_code)}'
    lines.append(sent + detail)
    return lines


def verdict(version: ExchangeResult) -> str:
    """Name the link's state from the GET_VERSION exchange.

    A NACK counts as a refusal only when it names this run's request: a request
    corrupted in transit is NACKed under a sequence the probe never sent, so it
    shows as an uncorrelated NACK instead.
    """
    if version.outcome is Outcome.REPLIED and version.reply.message_type is MessageType.VERSION:
        return 'VERDICT: firmware answered GET_VERSION. The link works.'
    if version.outcome is Outcome.REFUSED:
        status = version.records[-1].nack_status_code
        reason = NackReason.describe(status) if status is not None else 'an undecodable NACK'
        text = f'VERDICT: firmware is alive and framing correctly but refused GET_VERSION with {reason}.'
        remedy = NackReason.remedy(status) if status is not None else ''
        return f'{text} {remedy}' if remedy else text
    if version.outcome is Outcome.REPLIED:
        return (f'VERDICT: firmware answered GET_VERSION with {version.reply.message_type.name}, '
                f'not VERSION.')
    if not any(record.ok for record in version.records):
        return ('VERDICT: no well-framed response at all -- treat this as a wiring, power, '
                'or firmware-not-running fault before looking at the protocol.')
    if any(record.response_type == 'NACK' for record in version.records):
        return ('VERDICT: firmware is alive and framing correctly but NACKed requests under '
                'sequences this run did not send (see answers= above): requests are being '
                'corrupted in transit. Rerun with --data-ready before concluding anything about '
                'wiring or firmware logic.')
    return ('VERDICT: firmware is alive and framing correctly but never sent VERSION. '
            'The running build most likely predates GET_VERSION (0x14) support -- '
            'rebuild and reflash, then power-cycle the STM32.')


def print_exchange(result: ExchangeResult, show_snapshot: bool = False) -> None:
    for record in result.records:
        for line in record_lines(record):
            print(line)
    if result.reply is not None:
        for line in version_lines(result.reply):
            print(line)
        if show_snapshot:
            for line in snapshot_lines(result.reply):
                print(line)
            if result.reply.message_type is not MessageType.SNAPSHOT:
                print(f'     GET_SNAPSHOT answered with {result.reply.message_type.name}, no sensor records')
    print(f'     outcome: {result.outcome.value} after {len(result.records)} transaction(s)')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--speed-hz', type=int, default=1_000_000)
    parser.add_argument('--transactions', type=int, default=10,
                        help='Most transactions each exchange may clock, its own request '
                             'included (at least 2: the reply arrives one transaction late).')
    parser.add_argument('--interval-ms', type=float, default=20.0,
                        help='Fixed delay between transfers when --data-ready is not given. '
                             'This is a fallback, not a fix: the firmware only rearms DMA for '
                             'the next transfer when its bare-metal main loop next runs '
                             '(spi_slave_service.c SpiSlaveService_Process), so any fixed delay '
                             'is an estimate of that timing rather than a guarantee of it.')
    parser.add_argument('--data-ready', action='store_true',
                        help='Wait for DATA_READY (SD-17) before each transfer instead of a '
                             'fixed delay. This is what the transaction is actually gated on, '
                             'so prefer it over --interval-ms when diagnosing corruption.')
    parser.add_argument('--data-ready-line', type=int, default=DEFAULT_DATA_READY_LINE)
    parser.add_argument('--snapshot', action='store_true',
                        help='Also run a GET_SNAPSHOT exchange and print each sensor record '
                             'from its reply.')
    parser.add_argument('--fake', action='store_true',
                        help='Run against the firmware-rules fake instead of the bus.')
    args = parser.parse_args(argv)
    if args.transactions < 2:
        parser.error('--transactions must be at least 2: the reply arrives one transaction late')
    if args.data_ready and args.fake:
        parser.error('--data-ready requires real GPIO hardware; incompatible with --fake')

    data_ready = DataReadyWatcher(line_offset=args.data_ready_line) if args.data_ready else None
    bus = SpiBus(SpiBusConfig(max_speed_hz=args.speed_hz), backend=FakeFirmware() if args.fake else None)
    bus.open()
    session = ExchangeSession(bus=bus, block_id='probe', data_ready=data_ready,
                              min_interval_s=0.0 if data_ready is not None else args.interval_ms / 1000.0)

    print(f'device={"fake" if args.fake else bus.config.device} speed={args.speed_hz} Hz '
          f'start_seq={session.sequencer.peek()} budget={args.transactions}\n')
    try:
        version = session.exchange(GET_VERSION, budget=args.transactions)
        print_exchange(version)
        if args.snapshot:
            print()
            print_exchange(session.exchange(GET_SNAPSHOT, budget=args.transactions), show_snapshot=True)
    finally:
        bus.close()
        if data_ready is not None:
            data_ready.close()

    print()
    print(verdict(version))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
