#!/usr/bin/env python3
"""SPI transport timing harness for the Raspberry Pi to STM32 bench link.

Sweeps clock rate x CPU load x message type, writing one row per transaction so
the run can be analysed offline rather than only as pre-reduced statistics.

Records are buffered in memory and flushed between blocks: writing to disk
inside a measurement loop would put filesystem jitter into the numbers.

Outputs per run:
  <run_id>_transactions.csv  one row per clocked transaction
  <run_id>_blocks.csv        environment sampled around each block
  <run_id>_metadata.json     firmware identity, host state, configuration

This measures the polled request/response path only. DATA_READY is not wired
into the host yet (SD-17), so assert-to-service latency is out of scope here.
"""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_device import SpiDevice  # noqa: E402
from spi.spi_protocol import MessageType, SpiFrame  # noqa: E402
from spi.timing import CSV_FIELDS, TimingSession, summarise  # noqa: E402

DEFAULT_CLOCKS = '1000000,2000000,5000000'
DEFAULT_LOADS = '0,2,4'
DEFAULT_MESSAGES = 'GET_STATUS,GET_VERSION'
REQUEST_PAYLOADS = {
    # Contract: GET requests carry a one-byte schema_version.
    MessageType.GET_STATUS: b'\x01',
    MessageType.GET_VERSION: b'\x01',
    MessageType.GET_SNAPSHOT: b'\x01',
}


# --------------------------------------------------------------------------
# Environment capture
# --------------------------------------------------------------------------

def _read_text(path: str) -> str:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return ''


def read_cpu_temp_c() -> float | None:
    raw = _read_text('/sys/class/thermal/thermal_zone0/temp')
    return int(raw) / 1000.0 if raw.isdigit() else None


def read_cpu_freqs_khz() -> list[int]:
    freqs = []
    for path in sorted(Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_cur_freq')):
        raw = _read_text(str(path))
        if raw.isdigit():
            freqs.append(int(raw))
    return freqs


def read_throttled() -> str:
    """Raspberry Pi throttle/undervoltage bitmask; empty when unavailable."""
    try:
        result = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True,
                                text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else ''
    except (OSError, subprocess.SubprocessError):
        return ''


def read_loadavg() -> tuple[float, float, float] | None:
    raw = _read_text('/proc/loadavg').split()
    if len(raw) < 3:
        return None
    try:
        return (float(raw[0]), float(raw[1]), float(raw[2]))
    except ValueError:
        return None


def read_ctxt_switches() -> tuple[int, int]:
    voluntary = nonvoluntary = 0
    for line in _read_text('/proc/self/status').splitlines():
        if line.startswith('voluntary_ctxt_switches:'):
            voluntary = int(line.split()[-1])
        elif line.startswith('nonvoluntary_ctxt_switches:'):
            nonvoluntary = int(line.split()[-1])
    return (voluntary, nonvoluntary)


def sample_environment() -> dict:
    loadavg = read_loadavg()
    freqs = read_cpu_freqs_khz()
    return {
        'cpu_temp_c': read_cpu_temp_c(),
        'cpu_freq_khz_min': min(freqs) if freqs else None,
        'cpu_freq_khz_max': max(freqs) if freqs else None,
        'loadavg_1m': loadavg[0] if loadavg else None,
        'throttled': read_throttled(),
    }


# --------------------------------------------------------------------------
# Synthetic CPU load
# --------------------------------------------------------------------------

def _burn(stop_event, cpus) -> None:
    if cpus:
        try:
            os.sched_setaffinity(0, cpus)
        except OSError:
            pass
    value = 0
    while not stop_event.is_set():
        value = (value * 1103515245 + 12345) & 0xFFFFFFFF


class LoadGenerator:
    """Runs N busy-loop processes for the duration of a block."""

    def __init__(self, workers: int, cpus: set[int] | None = None) -> None:
        self.workers = workers
        self.cpus = cpus
        self._stop = None
        self._procs: list[mp.Process] = []

    def __enter__(self) -> 'LoadGenerator':
        if self.workers > 0:
            self._stop = mp.Event()
            for _ in range(self.workers):
                proc = mp.Process(target=_burn, args=(self._stop, self.cpus), daemon=True)
                proc.start()
                self._procs.append(proc)
        return self

    def __exit__(self, *exc_info) -> None:
        if self._stop is not None:
            self._stop.set()
        for proc in self._procs:
            proc.join(timeout=5)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=5)
        self._procs.clear()


# --------------------------------------------------------------------------
# Off-hardware simulation
# --------------------------------------------------------------------------

class PipelinedFakeBackend:
    """Mimics the firmware's one-behind response staging, for dry runs.

    Exists so the harness itself can be exercised without the STM32 attached.
    Timing produced this way is meaningless; only the plumbing is real.
    """

    def __init__(self) -> None:
        # Stands in for the firmware's boot status frame, which is what a real
        # device returns on the first transaction before anything is staged.
        self._staged = SpiFrame(message_type=MessageType.DIAGNOSTIC, seq=0).encode()
        self._tx_seq = 1

    def open(self, config: SpiBusConfig) -> None:
        self._config = config

    def transfer(self, tx_data: bytes) -> bytes:
        previous = self._staged
        try:
            request = SpiFrame.decode(tx_data)
            self._staged = self._build_response(request)
        except ValueError:
            pass
        time.sleep(0.0002)
        return previous.ljust(512, b'\x00')

    def _build_response(self, request: SpiFrame) -> bytes:
        self._tx_seq += 1
        if request.message_type is MessageType.GET_VERSION:
            payload = bytes([1, 1, 0, 1, 0, 0]) + b'\x00\x00' + \
                request.seq.to_bytes(4, 'little') + (0x1A2B3C4D).to_bytes(4, 'little') + \
                (1700000000).to_bytes(4, 'little')
            return SpiFrame(message_type=MessageType.VERSION, seq=self._tx_seq,
                            frame_time_us=int(time.monotonic() * 1e6), payload=payload).encode()
        payload = bytes([1, int(request.message_type), 0, 0]) + \
            request.seq.to_bytes(4, 'little') + (0).to_bytes(4, 'little')
        return SpiFrame(message_type=MessageType.ACK, seq=self._tx_seq,
                        frame_time_us=int(time.monotonic() * 1e6), payload=payload).encode()

    def close(self) -> None:
        return None


# --------------------------------------------------------------------------
# Run orchestration
# --------------------------------------------------------------------------

@dataclass
class BlockResult:
    block_id: str
    clock_hz: int
    load_workers: int
    message_type: str
    iterations: int
    records: list = field(default_factory=list)
    environment_before: dict = field(default_factory=dict)
    environment_after: dict = field(default_factory=dict)
    ctxt_voluntary_delta: int = 0
    ctxt_nonvoluntary_delta: int = 0


def run_block(args, clock_hz: int, workers: int, message_type: MessageType,
              backend) -> BlockResult:
    block_id = f'{clock_hz}hz_load{workers}_{message_type.name}'
    config = SpiBusConfig(device=args.device, max_speed_hz=clock_hz)
    bus = SpiBus(config, backend=backend) if backend is not None else SpiBus(config)
    payload = REQUEST_PAYLOADS.get(message_type, b'\x01')

    load_cpus = None
    if args.load_avoids_harness_cpu and args.affinity is not None:
        available = set(range(os.cpu_count() or 1)) - {args.affinity}
        load_cpus = available or None

    result = BlockResult(block_id=block_id, clock_hz=clock_hz, load_workers=workers,
                         message_type=message_type.name, iterations=args.iterations)

    with LoadGenerator(workers, load_cpus):
        time.sleep(args.settle)
        result.environment_before = sample_environment()
        voluntary_before, nonvoluntary_before = read_ctxt_switches()

        bus.open()
        try:
            session = TimingSession(bus=bus, block_id=block_id)
            for _ in range(args.warmup):
                session.transact(message_type, payload)
            session.reset_counters()
            records = [session.transact(message_type, payload) for _ in range(args.iterations)]
        finally:
            bus.close()

        voluntary_after, nonvoluntary_after = read_ctxt_switches()
        result.environment_after = sample_environment()

    result.records = records
    result.ctxt_voluntary_delta = voluntary_after - voluntary_before
    result.ctxt_nonvoluntary_delta = nonvoluntary_after - nonvoluntary_before
    return result


def collect_metadata(args, backend) -> dict:
    metadata = {
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'host': {
            'hostname': platform.node(),
            'kernel': platform.release(),
            'machine': platform.machine(),
            'python': platform.python_version(),
            'cpu_count': os.cpu_count(),
        },
        'configuration': vars(args).copy(),
        'host_code_revision': _git_describe(),
        'firmware': None,
        'firmware_warning': None,
    }
    metadata['configuration']['outdir'] = str(args.outdir)

    try:
        config = SpiBusConfig(device=args.device, max_speed_hz=min(_parse_ints(args.clocks)))
        bus = SpiBus(config, backend=backend) if backend is not None else SpiBus(config)
        bus.open()
        try:
            version = SpiDevice(bus).get_version()
        finally:
            bus.close()
        metadata['firmware'] = {
            'version': version.firmware_version,
            'git_hash': version.git_hash,
            'commit_epoch_secs': version.commit_epoch_secs,
            'protocol_version': version.protocol_version,
            'dirty_build': version.is_dirty_build,
            'summary': version.summary(),
        }
        if version.is_dirty_build:
            metadata['firmware_warning'] = (
                'Firmware reports a dirty build; this run cannot serve as '
                'integration-gate evidence (SPI_PAYLOAD_SCHEMA.md, VERSION payload).')
    except Exception as exc:  # noqa: BLE001 - identity is best-effort, the run still proceeds
        metadata['firmware_warning'] = f'could not read firmware identity: {exc}'
    return metadata


def _git_describe() -> dict:
    def _run(cmd):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=5,
                                 cwd=str(Path(__file__).resolve().parent))
            return out.stdout.strip() if out.returncode == 0 else ''
        except (OSError, subprocess.SubprocessError):
            return ''
    return {
        'commit': _run(['git', 'rev-parse', '--short=8', 'HEAD']),
        'dirty': bool(_run(['git', 'status', '--porcelain'])),
    }


def _parse_ints(raw: str) -> list[int]:
    return [int(value) for value in raw.split(',') if value.strip()]


def write_outputs(outdir: Path, run_id: str, blocks: list[BlockResult], metadata: dict) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    transactions_path = outdir / f'{run_id}_transactions.csv'
    with transactions_path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for block in blocks:
            for record in block.records:
                writer.writerow(record.as_row())

    blocks_path = outdir / f'{run_id}_blocks.csv'
    with blocks_path.open('w', newline='') as handle:
        fields = ['block_id', 'clock_hz', 'load_workers', 'message_type', 'iterations',
                  'ctxt_voluntary_delta', 'ctxt_nonvoluntary_delta',
                  'cpu_temp_c_before', 'cpu_temp_c_after', 'cpu_freq_khz_max_before',
                  'cpu_freq_khz_max_after', 'loadavg_1m_before', 'loadavg_1m_after',
                  'throttled_before', 'throttled_after']
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for block in blocks:
            before, after = block.environment_before, block.environment_after
            writer.writerow({
                'block_id': block.block_id,
                'clock_hz': block.clock_hz,
                'load_workers': block.load_workers,
                'message_type': block.message_type,
                'iterations': block.iterations,
                'ctxt_voluntary_delta': block.ctxt_voluntary_delta,
                'ctxt_nonvoluntary_delta': block.ctxt_nonvoluntary_delta,
                'cpu_temp_c_before': before.get('cpu_temp_c'),
                'cpu_temp_c_after': after.get('cpu_temp_c'),
                'cpu_freq_khz_max_before': before.get('cpu_freq_khz_max'),
                'cpu_freq_khz_max_after': after.get('cpu_freq_khz_max'),
                'loadavg_1m_before': before.get('loadavg_1m'),
                'loadavg_1m_after': after.get('loadavg_1m'),
                'throttled_before': before.get('throttled'),
                'throttled_after': after.get('throttled'),
            })

    metadata['blocks'] = [
        {
            'block_id': block.block_id,
            'transfer_ns': summarise([r.transfer_ns for r in block.records]),
            'round_trip_ns': summarise([r.round_trip_ns for r in block.records
                                        if r.round_trip_ns is not None]),
            'errors': sum(1 for r in block.records if not r.ok),
            'nacks': sum(1 for r in block.records if r.response_type == 'NACK'),
        }
        for block in blocks
    ]
    (outdir / f'{run_id}_metadata.json').write_text(json.dumps(metadata, indent=2, default=str))


def print_summary(blocks: list[BlockResult]) -> None:
    header = f'{"block":<34}{"n":>7}{"xfer p50":>11}{"xfer p99":>11}{"rtt p50":>11}{"err":>6}'
    print('\n' + header)
    print('-' * len(header))
    for block in blocks:
        transfer = summarise([r.transfer_ns for r in block.records])
        rtt = summarise([r.round_trip_ns for r in block.records if r.round_trip_ns is not None])
        errors = sum(1 for r in block.records if not r.ok)
        print(f'{block.block_id:<34}{len(block.records):>7}'
              f'{transfer.get("p50", 0) / 1000:>10.1f}u'
              f'{transfer.get("p99", 0) / 1000:>10.1f}u'
              f'{rtt.get("p50", 0) / 1000:>10.1f}u'
              f'{errors:>6}')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--device', default='/dev/spidev0.0')
    parser.add_argument('--clocks', default=DEFAULT_CLOCKS, help='comma-separated Hz')
    parser.add_argument('--loads', default=DEFAULT_LOADS, help='comma-separated busy-worker counts')
    parser.add_argument('--messages', default=DEFAULT_MESSAGES, help='comma-separated message types')
    parser.add_argument('--iterations', type=int, default=2000)
    parser.add_argument('--warmup', type=int, default=200)
    parser.add_argument('--settle', type=float, default=2.0, help='seconds between load start and measurement')
    parser.add_argument('--outdir', type=Path, default=Path('spi_timing_runs'))
    parser.add_argument('--affinity', type=int, default=None, help='pin the harness to this CPU')
    parser.add_argument('--rt-priority', type=int, default=None, help='SCHED_FIFO priority (needs root)')
    parser.add_argument('--load-avoids-harness-cpu', action='store_true',
                        help='keep synthetic load off the pinned harness CPU')
    parser.add_argument('--fake', action='store_true',
                        help='run against a simulated device; validates plumbing, not timing')
    args = parser.parse_args(argv)

    if args.affinity is not None:
        os.sched_setaffinity(0, {args.affinity})
    if args.rt_priority is not None:
        try:
            os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(args.rt_priority))
        except (OSError, PermissionError) as exc:
            print(f'warning: could not set SCHED_FIFO priority ({exc}); '
                  f'scheduling jitter will be in the results', file=sys.stderr)

    clocks = _parse_ints(args.clocks)
    loads = _parse_ints(args.loads)
    try:
        messages = [MessageType[name.strip()] for name in args.messages.split(',') if name.strip()]
    except KeyError as exc:
        parser.error(f'unknown message type {exc}')

    backend = PipelinedFakeBackend() if args.fake else None
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    metadata = collect_metadata(args, backend)
    if metadata.get('firmware_warning'):
        print(f'warning: {metadata["firmware_warning"]}', file=sys.stderr)

    blocks: list[BlockResult] = []
    try:
        for clock_hz in clocks:
            for workers in loads:
                for message_type in messages:
                    print(f'running {clock_hz} Hz, load {workers}, {message_type.name} ...',
                          flush=True)
                    blocks.append(run_block(args, clock_hz, workers, message_type,
                                            PipelinedFakeBackend() if args.fake else None))
    except KeyboardInterrupt:
        print('\ninterrupted; writing partial results', file=sys.stderr)
    finally:
        metadata['finished_utc'] = datetime.now(timezone.utc).isoformat()
        if blocks:
            write_outputs(args.outdir, run_id, blocks, metadata)
            print_summary(blocks)
            print(f'\nwrote {args.outdir}/{run_id}_*.csv|json')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
