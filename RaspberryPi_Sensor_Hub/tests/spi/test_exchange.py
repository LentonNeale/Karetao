"""ExchangeSession (src/spi/exchange.py) against the firmware-rules fake."""

import struct
import sys
import time
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.exchange import (  # noqa: E402
    GET_STATUS,
    CSV_FIELDS,
    ExchangeSession,
    Outcome,
    Request,
    correlated_request_seq,
    nack_codes,
)
from spi.fake_backend import IDLE_MISO, FakeDataReady, FakeFirmware  # noqa: E402
from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_protocol import MessageType, NackReason, Sequencer, SpiFrame, process_sequencer  # noqa: E402

GET_VERSION = Request(MessageType.GET_VERSION, GET_STATUS.payload)


def session_over(fake: FakeFirmware, seed: int = 100, **kwargs) -> ExchangeSession:
    bus = SpiBus(SpiBusConfig(), backend=fake)
    bus.open()
    return ExchangeSession(bus=bus, block_id='test', sequencer=Sequencer(seed), **kwargs)


def ack_payload(request_seq: int, status: int = 0, detail: int = 0) -> bytes:
    return struct.pack('<BBHII', 1, 0x11, status, request_seq, detail)


def version_payload(response_to_seq: int) -> bytes:
    return struct.pack('<BBBBBBHIII', 1, 1, 0, 1, 0, 0, 0, response_to_seq, 0, 0)


class GarbleTransaction:
    """A DataReadyLike that puts the fake into garbage mode for the listed transactions only.

    The session waits on DATA_READY just before each transfer, so this is the hook between two
    transactions of one exchange. In garbage mode the fake returns idle MISO and does not
    receive the request, but keeps what it had staged for the next transaction.
    """

    def __init__(self, fake: FakeFirmware, garbled: set[int]) -> None:
        self._fake = fake
        self._garbled = garbled
        self._transaction = 0

    def is_ready(self) -> bool:
        return True

    def wait_for_ready(self, timeout_s: float) -> bool:
        self._transaction += 1
        self._fake.garbage = self._transaction in self._garbled
        return True


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


class TransactTests(unittest.TestCase):
    def test_transfer_requires_an_open_bus(self) -> None:
        # A caller error, so it raises, unlike every firmware outcome.
        session = ExchangeSession(bus=SpiBus(SpiBusConfig(), backend=FakeFirmware()), sequencer=Sequencer(1))
        with self.assertRaises(RuntimeError):
            session.transact(GET_STATUS)

    def test_phases_are_recorded_separately(self) -> None:
        record = session_over(FakeFirmware()).transact(GET_STATUS)

        self.assertTrue(record.ok)
        self.assertGreater(record.transfer_ns, 0)
        self.assertEqual(record.total_ns, record.encode_ns + record.transfer_ns + record.decode_ns)
        self.assertEqual(record.request_type, 'GET_STATUS')
        self.assertEqual(record.block_id, 'test')

    def test_hub_time_delta_tracked_between_responses(self) -> None:
        ticks = iter(range(1000, 10_000, 1000))  # one tick per frame the fake builds
        session = session_over(FakeFirmware(clock_us=lambda: next(ticks)))
        first = session.transact(GET_STATUS)
        second = session.transact(GET_STATUS)

        self.assertIsNone(first.hub_delta_us)  # nothing earlier to compare with
        self.assertEqual(second.hub_delta_us, 1000)

    def test_reply_correlates_one_transaction_later(self) -> None:
        session = session_over(FakeFirmware())
        first = session.transact(GET_STATUS)
        second = session.transact(GET_STATUS)

        self.assertEqual(first.response_type, 'DIAGNOSTIC')  # the boot frame answers nothing
        self.assertIsNone(first.correlated_seq)
        self.assertEqual(second.correlated_seq, first.request_seq)
        self.assertEqual(session.counters.uncorrelated_responses, 1)
        self.assertEqual(session.counters.correlation_misses, 0)

    def test_t1_and_t4_bracket_the_exchange(self) -> None:
        session = session_over(FakeFirmware())
        first = session.transact(GET_STATUS)
        second = session.transact(GET_STATUS)

        # T1 is the start of the transfer that carried the request; T4 the end of the one that
        # carried its reply.
        self.assertEqual(second.t1_request_sent_ns, first.t_mono_ns + first.encode_ns)
        self.assertEqual(second.t4_response_received_ns,
                         second.t_mono_ns + second.encode_ns + second.transfer_ns)
        self.assertEqual(second.round_trip_ns, second.t4_response_received_ns - second.t1_request_sent_ns)
        self.assertIsNone(first.t1_request_sent_ns)  # nothing to correlate, so no observation
        self.assertIsNone(first.t4_response_received_ns)
        self.assertIsNone(second.request_received_local_us)  # no wire placement yet (#42)

    def test_garbage_is_recorded_with_its_raw_bytes(self) -> None:
        fake = FakeFirmware()
        fake.garbage = True
        record = session_over(fake).transact(GET_STATUS)

        self.assertFalse(record.ok)
        self.assertNotEqual(record.error, '')
        self.assertEqual(record.raw_response, IDLE_MISO)
        self.assertEqual(record.as_row()['raw_response'], IDLE_MISO.hex())

    def test_a_reply_to_an_unknown_request_is_no_observation(self) -> None:
        # The reply correlates (another process's or session's request), but not to this
        # session's pending table, so it carries neither T1 nor T4.
        fake = FakeFirmware()
        other = session_over(fake, seed=500)
        mine = session_over(fake, seed=900)
        other.transact(GET_STATUS)
        record = mine.transact(GET_STATUS)

        self.assertEqual(record.correlated_seq, 500)
        self.assertIsNone(record.t1_request_sent_ns)
        self.assertIsNone(record.t4_response_received_ns)
        self.assertIsNone(record.round_trip_ns)
        self.assertEqual(mine.counters.correlation_misses, 1)

    def test_garbage_is_no_observation(self) -> None:
        fake = FakeFirmware()
        fake.garbage = True
        record = session_over(fake).transact(GET_STATUS)
        self.assertIsNone(record.t4_response_received_ns)

    def test_decoded_response_keeps_no_raw_bytes(self) -> None:
        record = session_over(FakeFirmware()).transact(GET_STATUS)
        self.assertIsNone(record.raw_response)

    def test_csv_fields_keep_their_order_and_gain_four(self) -> None:
        self.assertEqual(CSV_FIELDS[:3], ['index', 'block_id', 'request_seq'])
        self.assertEqual(CSV_FIELDS[-4:], ['t1_request_sent_ns', 't4_response_received_ns',
                                           'request_received_local_us', 'raw_response'])


class ExchangeTests(unittest.TestCase):
    def test_replied_after_one_filler(self) -> None:
        session = session_over(FakeFirmware())
        result = session.exchange(GET_VERSION, budget=4)

        self.assertIs(result.outcome, Outcome.REPLIED)
        self.assertIs(result.reply.message_type, MessageType.VERSION)
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.records[0].request_type, 'GET_VERSION')
        self.assertEqual(result.records[1].request_type, 'GET_STATUS')  # the filler
        self.assertEqual(result.records[1].correlated_seq, result.request_seq)

    def test_next_exchange_absorbs_the_previous_fillers_reply(self) -> None:
        session = session_over(FakeFirmware())
        session.exchange(GET_VERSION, budget=4)
        second = session.exchange(GET_VERSION, budget=4)

        # The first transaction of the second exchange carries the reply to the first exchange's
        # filler: it correlates through the pending table, not as this exchange's reply.
        self.assertIs(second.outcome, Outcome.REPLIED)
        self.assertEqual(second.records[0].response_type, 'ACK')
        self.assertEqual(session.counters.correlation_misses, 0)

    def test_refused_by_bad_sequence(self) -> None:
        # A Pi seed below the STM32's high-water mark: what R3 addresses (the jump is #87's).
        session = session_over(FakeFirmware(last_request_seq=1000), seed=10)
        result = session.exchange(GET_STATUS, budget=4)

        self.assertIs(result.outcome, Outcome.REFUSED)
        self.assertIs(result.reply.message_type, MessageType.NACK)
        self.assertEqual(result.records[-1].nack_status_code, NackReason.BAD_SEQUENCE)

    def test_refused_by_bad_state_then_replied_after_activation(self) -> None:
        fake = FakeFirmware(active=False)
        session = session_over(fake)

        refused = session.exchange(GET_STATUS, budget=4)
        fake.activate()
        replied = session.exchange(GET_STATUS, budget=4)

        self.assertIs(refused.outcome, Outcome.REFUSED)
        self.assertEqual(refused.records[-1].nack_status_code, NackReason.BAD_STATE)
        self.assertIs(replied.outcome, Outcome.REPLIED)

    def test_a_garbled_transaction_is_not_yet_rather_than_fatal(self) -> None:
        # The filler's transaction comes back as idle MISO; the VERSION stays staged and the
        # next filler clocks it out.
        fake = FakeFirmware()
        session = session_over(fake, data_ready=GarbleTransaction(fake, garbled={2}))
        result = session.exchange(GET_VERSION, budget=4)

        self.assertIs(result.outcome, Outcome.REPLIED)
        self.assertEqual([r.ok for r in result.records], [True, False, True])
        self.assertIs(result.reply.message_type, MessageType.VERSION)

    def test_a_nack_naming_another_request_is_not_a_refusal(self) -> None:
        # Another transmitter's request below the high-water mark is NACKed; that NACK reaches
        # this session first, and must not end its exchange.
        fake = FakeFirmware(last_request_seq=1000)
        session_over(fake, seed=500).transact(GET_STATUS)
        result = session_over(fake, seed=2000).exchange(GET_VERSION, budget=4)

        self.assertEqual(result.records[0].response_type, 'NACK')
        self.assertEqual(result.records[0].correlated_seq, 500)
        self.assertIs(result.outcome, Outcome.REPLIED)
        self.assertIs(result.reply.message_type, MessageType.VERSION)

    def test_a_version_for_another_request_does_not_end_the_exchange(self) -> None:
        # A stale VERSION (another transmitter's) must not be read as this request's identity.
        fake = FakeFirmware()
        session_over(fake, seed=500).transact(GET_VERSION)
        result = session_over(fake, seed=900).exchange(GET_VERSION, budget=4)

        self.assertEqual(result.records[0].response_type, 'VERSION')
        self.assertEqual(result.records[0].correlated_seq, 500)
        self.assertIs(result.outcome, Outcome.REPLIED)
        self.assertEqual(result.records[-1].correlated_seq, result.request_seq)

    def test_a_request_lost_in_its_own_transaction_exhausts(self) -> None:
        # Garbage on the request's own transaction means the STM32 never received it, so no
        # reply can come; the exchange ends exhausted, not with a later request's reply.
        fake = FakeFirmware()
        session = session_over(fake, data_ready=GarbleTransaction(fake, garbled={1}))
        result = session.exchange(GET_VERSION, budget=4)

        self.assertIs(result.outcome, Outcome.EXHAUSTED)
        self.assertFalse(result.records[0].ok)
        self.assertTrue(all(r.correlated_seq != result.request_seq for r in result.records))

    def test_exhausted_without_raising(self) -> None:
        fake = FakeFirmware()
        fake.garbage = True
        session = session_over(fake)
        result = session.exchange(GET_STATUS, budget=3)

        self.assertIs(result.outcome, Outcome.EXHAUSTED)
        self.assertIsNone(result.reply)
        self.assertEqual(len(result.records), 3)
        self.assertEqual(session.counters.decode_failures, 3)

    def test_budget_must_allow_the_pipeline_delay(self) -> None:
        session = session_over(FakeFirmware())
        with self.assertRaises(ValueError):
            session.exchange(GET_STATUS, budget=1)
        self.assertEqual(session.counters.transactions, 0)


class PacingTests(unittest.TestCase):
    def test_every_transaction_waits_for_data_ready(self) -> None:
        watcher = FakeDataReady(always_ready=True)
        session = session_over(FakeFirmware(), data_ready=watcher)
        result = session.exchange(GET_STATUS, budget=4)

        self.assertEqual(watcher.wait_calls, len(result.records))
        self.assertTrue(all(r.data_ready_wait_ns is not None for r in result.records))
        self.assertFalse(any(r.data_ready_timed_out for r in result.records))
        self.assertEqual(session.counters.data_ready_timeouts, 0)

    def test_no_pacing_by_default(self) -> None:
        record = session_over(FakeFirmware()).transact(GET_STATUS)
        self.assertIsNone(record.data_ready_wait_ns)
        self.assertFalse(record.data_ready_timed_out)

    def test_min_interval_enforces_spacing_between_transfers(self) -> None:
        session = session_over(FakeFirmware(), min_interval_s=0.02)
        session.transact(GET_STATUS)
        start = time.monotonic()
        session.transact(GET_STATUS)
        self.assertGreaterEqual(time.monotonic() - start, 0.015)  # scheduler slack below 20 ms

    def test_min_interval_does_not_delay_the_first_transaction(self) -> None:
        session = session_over(FakeFirmware(), min_interval_s=1.0)
        start = time.monotonic()
        session.transact(GET_STATUS)
        self.assertLess(time.monotonic() - start, 0.5)

    def test_data_ready_takes_precedence_over_min_interval(self) -> None:
        session = session_over(FakeFirmware(), data_ready=FakeDataReady(always_ready=True), min_interval_s=1.0)
        start = time.monotonic()
        session.transact(GET_STATUS)
        session.transact(GET_STATUS)
        self.assertLess(time.monotonic() - start, 0.5)  # >= 1 s if min_interval_s also applied

    def test_data_ready_timeout_still_clocks(self) -> None:
        watcher = FakeDataReady(ready_sequence=[False, True])
        session = session_over(FakeFirmware(), data_ready=watcher, data_ready_timeout_s=0.001)
        result = session.exchange(GET_STATUS, budget=4)

        self.assertIs(result.outcome, Outcome.REPLIED)
        self.assertTrue(result.records[0].data_ready_timed_out)
        self.assertEqual(session.counters.data_ready_timeouts, 1)


class ProcessSequencerTests(unittest.TestCase):
    def test_sessions_share_the_process_sequencer_by_default(self) -> None:
        bus = SpiBus(SpiBusConfig(), backend=FakeFirmware())
        bus.open()
        first = ExchangeSession(bus=bus)
        second = ExchangeSession(bus=bus)

        self.assertIs(first.sequencer, process_sequencer())
        self.assertIs(second.sequencer, first.sequencer)
        sequence = first.next_sequence()
        self.assertEqual(second.next_sequence(), (sequence + 1) & 0xFFFFFFFF or 1)  # one sequence space


if __name__ == '__main__':
    unittest.main()
