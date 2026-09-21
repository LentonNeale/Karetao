#!/usr/bin/env python3
"""Dump what the STM32 actually returns, to classify a non-responsive link.

`get_version()` treats an undecodable transfer as "not yet" and retries, which
is right for an occasional glitch but collapses every persistent fault into the
same timeout. This probe keeps the raw bytes so the fault can be named: a
silent MISO, a byte-shifted frame, a firmware that rejects the request, and a
firmware that never answers all look identical through the normal client.

Read-only: it clocks GET_VERSION once, then GET_STATUS, and reports. It changes
no device state beyond the sequence numbers it consumes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_protocol import (  # noqa: E402
    MAGIC,
    MessageType,
    NackReason,
    SpiFrame,
    initial_sequence,
)

MAGIC_LE = struct.pack('<H', MAGIC)


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
    parser.add_argument('--interval-ms', type=float, default=20.0)
    args = parser.parse_args()

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
            request = SpiFrame(message_type=kind, seq=sequence + index, payload=b'\x01')
            raw = bus.transfer(request.encode())

            shape = classify(raw)
            decoded = describe(raw)
            if 'magic at offset 0' in shape:
                seen_magic = True
            if decoded.startswith('VERSION'):
                seen_version = True
            replies[decoded.split(' ')[0]] = replies.get(decoded.split(' ')[0], 0) + 1

            print(f'tx{index:02d} sent {kind.name:12s} -> {decoded}')
            if 'magic at offset 0' not in shape:
                print(f'     {shape}')
                print(f'     first 24 bytes: {raw[:24].hex(" ")}')
            time.sleep(args.interval_ms / 1000.0)
    finally:
        bus.close()

    print('\nreply frames seen:', ', '.join(f'{k}x{v}' for k, v in replies.items()) or 'none')
    if seen_version:
        print('VERDICT: firmware answered GET_VERSION. The link works.')
    elif not seen_magic:
        print('VERDICT: no well-framed response at all -- treat this as a wiring, power, '
              'or firmware-not-running fault before looking at the protocol.')
    elif 'NACK' in replies:
        print('VERDICT: firmware is alive and framing correctly but refused the request; '
              'the reason printed above is authoritative.')
    else:
        print('VERDICT: firmware is alive and framing correctly but never sent VERSION. '
              'The running build most likely predates GET_VERSION (0x14) support -- '
              'rebuild and reflash, then power-cycle the STM32.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
