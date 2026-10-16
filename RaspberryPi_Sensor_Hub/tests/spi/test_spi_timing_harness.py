"""The timing harness (tools/spi_timing_harness.py): its statistics, its identity read, and a
--fake run end to end."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from spi.exchange import ExchangeSession, GET_REQUEST_PAYLOAD  # noqa: E402
from spi.fake_backend import FakeFirmware, FirmwareIdentity  # noqa: E402
from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_protocol import MessageType, Sequencer  # noqa: E402

_spec = importlib.util.spec_from_file_location('spi_timing_harness', ROOT / 'tools' / 'spi_timing_harness.py')
harness = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = harness  # @dataclass resolves the module through sys.modules
_spec.loader.exec_module(harness)


def session_over(fake: FakeFirmware, seed: int = 100) -> ExchangeSession:
    bus = SpiBus(SpiBusConfig(), backend=fake)
    bus.open()
    return ExchangeSession(bus=bus, sequencer=Sequencer(seed))


class StatisticsTests(unittest.TestCase):
    def test_percentiles_nearest_rank(self) -> None:
        result = harness.percentiles(list(range(1, 101)), points=(50, 99))
        self.assertEqual(result['p50'], 50.0)
        self.assertEqual(result['p99'], 99.0)

    def test_percentiles_of_empty_input(self) -> None:
        self.assertEqual(harness.percentiles([]), {})

    def test_summarise_reports_count_for_empty(self) -> None:
        self.assertEqual(harness.summarise([]), {'count': 0})

    def test_summarise_basic_statistics(self) -> None:
        summary = harness.summarise([10, 20, 30])
        self.assertEqual(summary['count'], 3)
        self.assertEqual(summary['min'], 10.0)
        self.assertEqual(summary['max'], 30.0)
        self.assertAlmostEqual(summary['mean'], 20.0)


class RequestTests(unittest.TestCase):
    def test_get_requests_carry_the_session_get_payload(self) -> None:
        self.assertEqual(harness.request_for(MessageType.GET_VERSION).payload, GET_REQUEST_PAYLOAD)

    def test_other_requests_carry_no_payload(self) -> None:
        self.assertEqual(harness.request_for(MessageType.TIME_SYNC).payload, b'')


class ReadVersionTests(unittest.TestCase):
    def test_reads_the_firmware_identity(self) -> None:
        fake = FakeFirmware(identity=FirmwareIdentity(major=2, minor=3, patch=4, build_flags=1,
                                                      git_hash_abbrev=0x1A2B3C4D))
        version = harness.read_version(session_over(fake), budget=2)
        self.assertEqual(version.firmware_version, '2.3.4')
        self.assertEqual(version.git_hash, '1a2b3c4d')
        self.assertTrue(version.is_dirty_build)

    def test_refusal_names_the_nack_reason(self) -> None:
        with self.assertRaises(RuntimeError) as caught:
            harness.read_version(session_over(FakeFirmware(last_request_seq=1000), seed=10), budget=4)
        self.assertIn('BAD_SEQUENCE', str(caught.exception))
        self.assertIn('power-cycle', str(caught.exception))

    def test_no_reply_within_the_budget_times_out(self) -> None:
        fake = FakeFirmware()
        fake.garbage = True
        with self.assertRaises(TimeoutError):
            harness.read_version(session_over(fake), budget=3)


class FakeRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.outdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.outdir)

    def test_runs_end_to_end_against_the_fake(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            code = harness.main(['--fake', '--clocks', '1000000', '--loads', '0', '--iterations', '5',
                                 '--warmup', '2', '--settle', '0', '--min-interval-ms', '0',
                                 '--outdir', str(self.outdir)])
        self.assertEqual(code, 0)
        metadata = json.loads(next(self.outdir.glob('*_metadata.json')).read_text())
        self.assertIsNone(metadata['firmware_warning'])
        self.assertEqual(metadata['firmware']['version'], '0.1.0')
        for block in metadata['blocks']:
            self.assertEqual(block['errors'], 0)
            self.assertEqual(block['nacks'], 0)
            self.assertEqual(block['round_trip_ns']['count'], 5)  # every reply correlated
        rows = next(self.outdir.glob('*_transactions.csv')).read_text().splitlines()
        self.assertEqual(len(rows), 1 + 2 * 5)  # header, two blocks of five


if __name__ == '__main__':
    unittest.main()
