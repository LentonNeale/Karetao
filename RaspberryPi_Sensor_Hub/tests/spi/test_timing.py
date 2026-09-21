import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.spi_bus import SpiBus, SpiBusConfig
from spi.spi_protocol import MessageType, SpiFrame
from spi.timing import (
    TimingSession,
    correlated_request_seq,
    nack_codes,
    percentiles,
    summarise,
)


def ack_payload(request_seq: int, status: int = 0, detail: int = 0) -> bytes:
    return struct.pack('<BBHII', 1, 0x11, status, request_seq, detail)


def version_payload(response_to_seq: int) -> bytes:
    return struct.pack('<BBBBBBHIII', 1, 1, 0, 1, 0, 0, 0, response_to_seq, 0, 0)


class CorrelationTests(unittest.TestCase):
    def test_ack_correlation_read_from_request_seq(self) -> None:
        frame = SpiFrame(message_type=MessageType.ACK, seq=2, payload=ack_payload(41))
        self.assertEqual(correlated_request_seq(frame), 41)

    def test_version_correlation_read_from_response_to_seq(self) -> None:
        frame = SpiFrame(message_type=MessageType.VERSION, seq=2, payload=version_payload(77))
        self.assertEqual(correlated_request_seq(frame), 77)

    def test_diagnostic_correlation_offset(self) -> None:
        payload = struct.pack('<BBHQI', 1, 0, 0, 1234, 55).ljust(20, b'\x00')
        frame = SpiFrame(message_type=MessageType.DIAGNOSTIC, seq=2, payload=payload)
        self.assertEqual(correlated_request_seq(frame), 55)

    def test_short_payload_has_no_correlation(self) -> None:
        frame = SpiFrame(message_type=MessageType.DIAGNOSTIC, seq=2, payload=b'')
        self.assertIsNone(correlated_request_seq(frame))

    def test_nack_codes_extracted(self) -> None:
        frame = SpiFrame(message_type=MessageType.NACK, seq=2, payload=ack_payload(9, status=4, detail=7))
        self.assertEqual(nack_codes(frame), (4, 7))

    def test_nack_codes_absent_for_ack(self) -> None:
        frame = SpiFrame(message_type=MessageType.ACK, seq=2, payload=ack_payload(9))
        self.assertEqual(nack_codes(frame), (None, None))


class PipelinedBackend:
    """Returns the reply staged by the previous transaction."""

    def __init__(self) -> None:
        self._staged = SpiFrame(message_type=MessageType.ACK, seq=0, payload=ack_payload(0)).encode()
        self._tx = 0

    def open(self, config: SpiBusConfig) -> None:
        return None

    def transfer(self, tx_data: bytes) -> bytes:
        previous = self._staged
        self._tx += 1
        request = SpiFrame.decode(tx_data)
        self._staged = SpiFrame(message_type=MessageType.ACK, seq=self._tx,
                                frame_time_us=self._tx * 1000,
                                payload=ack_payload(request.seq)).encode()
        return previous

    def close(self) -> None:
        return None


class GarbageBackend:
    def open(self, config: SpiBusConfig) -> None:
        return None

    def transfer(self, tx_data: bytes) -> bytes:
        return b'\xff' * 512

    def close(self) -> None:
        return None


class TimingSessionTests(unittest.TestCase):
    def _session(self, backend) -> TimingSession:
        bus = SpiBus(SpiBusConfig(), backend=backend)
        bus.open()
        return TimingSession(bus=bus, block_id='test')

    def test_round_trip_spans_the_pipeline_delay(self) -> None:
        session = self._session(PipelinedBackend())

        first = session.transact(MessageType.GET_STATUS, b'\x01')
        second = session.transact(MessageType.GET_STATUS, b'\x01')

        # The first reply answers a request from before the run, so it cannot
        # correlate; the second answers the first request.
        self.assertIsNone(first.round_trip_ns)
        self.assertEqual(second.correlated_seq, first.request_seq)
        self.assertIsNotNone(second.round_trip_ns)
        # Round trip spans two transfers, so it must exceed either one alone.
        self.assertGreaterEqual(second.round_trip_ns, second.transfer_ns)

    def test_phases_are_recorded_separately(self) -> None:
        session = self._session(PipelinedBackend())
        record = session.transact(MessageType.GET_STATUS, b'\x01')

        self.assertTrue(record.ok)
        self.assertGreater(record.transfer_ns, 0)
        self.assertGreaterEqual(record.total_ns, record.transfer_ns)
        self.assertEqual(record.request_type, 'GET_STATUS')
        self.assertEqual(record.block_id, 'test')

    def test_hub_time_delta_tracked_between_responses(self) -> None:
        session = self._session(PipelinedBackend())
        session.transact(MessageType.GET_STATUS, b'\x01')
        second = session.transact(MessageType.GET_STATUS, b'\x01')
        self.assertEqual(second.hub_delta_us, 1000)

    def test_decode_failure_is_recorded_not_raised(self) -> None:
        session = self._session(GarbageBackend())
        record = session.transact(MessageType.GET_STATUS, b'\x01')

        self.assertFalse(record.ok)
        self.assertNotEqual(record.error, '')
        self.assertEqual(session.counters.decode_failures, 1)
        self.assertEqual(record.response_type, '')

    def test_sequence_never_reuses_zero(self) -> None:
        session = self._session(PipelinedBackend())
        session._seq = 0xFFFFFFFF
        self.assertEqual(session.next_sequence(), 0xFFFFFFFF)
        self.assertEqual(session.next_sequence(), 1)


class StatisticsTests(unittest.TestCase):
    def test_percentiles_nearest_rank(self) -> None:
        values = list(range(1, 101))
        result = percentiles(values, points=(50, 99))
        self.assertEqual(result['p50'], 50.0)
        self.assertEqual(result['p99'], 99.0)

    def test_percentiles_of_empty_input(self) -> None:
        self.assertEqual(percentiles([]), {})

    def test_summarise_reports_count_for_empty(self) -> None:
        self.assertEqual(summarise([]), {'count': 0})

    def test_summarise_basic_statistics(self) -> None:
        summary = summarise([10, 20, 30])
        self.assertEqual(summary['count'], 3)
        self.assertEqual(summary['min'], 10.0)
        self.assertEqual(summary['max'], 30.0)
        self.assertAlmostEqual(summary['mean'], 20.0)


if __name__ == '__main__':
    unittest.main()
