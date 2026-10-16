"""ExchangeSession (src/spi/exchange.py) against the firmware-rules fake."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.exchange import (  # noqa: E402
    GET_STATUS,
    CSV_FIELDS,
    ExchangeSession,
    Outcome,
    Request,
)
from spi.fake_backend import IDLE_MISO, FakeDataReady, FakeFirmware  # noqa: E402
from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_protocol import MessageType, NackReason, Sequencer, process_sequencer  # noqa: E402

GET_VERSION = Request(MessageType.GET_VERSION, GET_STATUS.payload)


def session_over(fake: FakeFirmware, seed: int = 100, **kwargs) -> ExchangeSession:
    bus = SpiBus(SpiBusConfig(), backend=fake)
    bus.open()
    return ExchangeSession(bus=bus, block_id='test', sequencer=Sequencer(seed), **kwargs)


class TransactTests(unittest.TestCase):
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
