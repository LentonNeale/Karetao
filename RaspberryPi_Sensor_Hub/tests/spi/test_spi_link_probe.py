import contextlib
import importlib.util
import io
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from spi.exchange import ExchangeResult, ExchangeSession, Outcome  # noqa: E402
from spi.fake_backend import IDLE_MISO, FakeFirmware  # noqa: E402
from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_protocol import MessageType, Sequencer, SpiFrame  # noqa: E402

_spec = importlib.util.spec_from_file_location('spi_link_probe', ROOT / 'tools' / 'spi_link_probe.py')
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


def version_frame(flags: int, payload: bytes | None = None) -> SpiFrame:
    if payload is None:
        payload = struct.pack('<BBBBBBHIII', 1, 1, 2, 3, 4, flags, 0, 7, 0x00ABCDEF, 1_700_000_000)
    return SpiFrame(message_type=MessageType.VERSION, seq=7, payload=payload)


def session_over(fake: FakeFirmware, seed: int = 100) -> ExchangeSession:
    bus = SpiBus(SpiBusConfig(), backend=fake)
    bus.open()
    return ExchangeSession(bus=bus, sequencer=Sequencer(seed))


class VersionLinesTests(unittest.TestCase):
    def test_clean_build(self):
        lines = probe.version_lines(version_frame(0x00))
        self.assertEqual(len(lines), 1)
        self.assertIn('firmware_version=2.3.4', lines[0])
        self.assertIn('git_hash_abbrev=00abcdef', lines[0])
        self.assertIn('build_flags=0x00', lines[0])
        self.assertIn('dirty=no', lines[0])
        self.assertIn('protocol_version=1', lines[0])
        self.assertIn('commit_epoch_secs=1700000000', lines[0])

    def test_dirty_build(self):
        lines = probe.version_lines(version_frame(0x01))
        self.assertEqual(len(lines), 1)
        self.assertIn('build_flags=0x01', lines[0])
        self.assertIn('dirty=yes', lines[0])

    def test_non_version_frame_gives_no_lines(self):
        frame = SpiFrame(message_type=MessageType.DIAGNOSTIC, seq=1)
        self.assertEqual(probe.version_lines(frame), [])

    def test_wrong_size_payload_is_undecodable(self):
        lines = probe.version_lines(version_frame(0, payload=b'\x01' * 5))
        self.assertEqual(len(lines), 1)
        self.assertIn('undecodable', lines[0])



class RecordLinesTests(unittest.TestCase):
    def test_undecodable_response_is_classified_from_its_raw_bytes(self):
        fake = FakeFirmware()
        fake.garbage = True
        lines = probe.record_lines(session_over(fake).transact(probe.GET_VERSION))
        self.assertIn('undecodable', lines[0])
        self.assertIn('all 0xFF', lines[1])
        self.assertIn('first 24 bytes: ff ff', lines[2])

    def test_nack_names_its_reason_and_the_request_it_answers(self):
        session = session_over(FakeFirmware(last_request_seq=1000), seed=10)
        session.transact(probe.GET_VERSION)
        lines = probe.record_lines(session.transact(probe.GET_VERSION))
        self.assertIn('NACK', lines[0])
        self.assertIn('answers=10', lines[0])
        self.assertIn('reason=BAD_SEQUENCE', lines[0])


class VerdictTests(unittest.TestCase):
    def test_version_reply_means_the_link_works(self):
        result = session_over(FakeFirmware()).exchange(probe.GET_VERSION, budget=4)
        self.assertIn('The link works', probe.verdict(result))

    def test_garbage_means_wiring_or_power(self):
        fake = FakeFirmware()
        fake.garbage = True
        result = session_over(fake).exchange(probe.GET_VERSION, budget=3)
        self.assertIn('no well-framed response', probe.verdict(result))

    def test_refusal_names_its_reason(self):
        result = session_over(FakeFirmware(last_request_seq=1000), seed=10).exchange(probe.GET_VERSION, budget=4)
        text = probe.verdict(result)
        self.assertIn('refused GET_VERSION with BAD_SEQUENCE', text)
        self.assertIn('power-cycle', text)

    def test_a_nack_for_another_sequence_points_at_transit_corruption(self):
        # Every request NACKed but none under this run's sequence: what a corrupted request
        # looks like, since the firmware reads the seq from the damaged header.
        session = session_over(FakeFirmware(last_request_seq=1000), seed=10)
        session.transact(probe.GET_VERSION)
        nack = session.transact(probe.GET_VERSION)  # the NACK naming seq 10
        result = ExchangeResult(Outcome.EXHAUSTED, request_seq=99, reply=None, records=(nack,))
        self.assertIn('corrupted in transit', probe.verdict(result))


class FakeRunTests(unittest.TestCase):
    def test_runs_end_to_end_against_the_fake(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(probe.main(['--fake', '--snapshot', '--interval-ms', '0']), 0)
        text = out.getvalue()
        self.assertIn('device=fake', text)
        self.assertIn('firmware_version=0.1.0', text)
        self.assertIn('GET_SNAPSHOT answered with ACK', text)
        self.assertIn('The link works', text)


if __name__ == '__main__':
    unittest.main()
