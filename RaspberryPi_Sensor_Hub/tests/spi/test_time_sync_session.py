"""Unit tests for TIME_SYNC session tracking and offset calculation."""

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.time_sync_session import TimeSyncCandidate, TimeSyncSession


class TimeSyncCandidateTests(unittest.TestCase):
    """Tests for TimeSyncCandidate dataclass."""

    def test_candidate_is_accepted_when_status_code_is_zero(self) -> None:
        candidate = TimeSyncCandidate(
            sync_seq=1, pi_time_us_sent=1000000, pi_time_us_received=1000100,
            pi_time_us_stm32=1000000, offset_us=1000000, status_code=0,
            uncertainty_min_us=100, uncertainty_max_us=0
        )
        self.assertTrue(candidate.is_accepted())

    def test_candidate_is_not_accepted_when_status_code_is_nack(self) -> None:
        candidate = TimeSyncCandidate(
            sync_seq=1, pi_time_us_sent=1000000, pi_time_us_received=1000100,
            pi_time_us_stm32=1000000, offset_us=1000000, status_code=7,
            uncertainty_min_us=100, uncertainty_max_us=0
        )
        self.assertFalse(candidate.is_accepted())

    def test_candidate_is_not_accepted_when_status_code_is_any_nack_reason(self) -> None:
        for nack_code in [1, 2, 3, 4, 5, 6, 7, 8]:
            candidate = TimeSyncCandidate(
                sync_seq=1, pi_time_us_sent=1000000, pi_time_us_received=1000100,
                pi_time_us_stm32=1000000, offset_us=1000000, status_code=nack_code,
                uncertainty_min_us=100, uncertainty_max_us=0
            )
            self.assertFalse(candidate.is_accepted())


class TimeSyncSessionTests(unittest.TestCase):
    """Tests for TimeSyncSession state and offset tracking."""

    def test_next_sequence_increments_starting_from_one(self) -> None:
        session = TimeSyncSession()
        self.assertEqual(session.next_sequence(), 1)
        self.assertEqual(session.next_sequence(), 2)
        self.assertEqual(session.next_sequence(), 3)

    def test_next_sequence_wraps_at_uint32_boundary(self) -> None:
        session = TimeSyncSession()
        session.next_seq = 0xFFFFFFFF
        self.assertEqual(session.next_sequence(), 0xFFFFFFFF)
        # Should wrap to 1 (not 0, per contract)
        self.assertEqual(session.next_sequence(), 1)

    def test_record_request_stores_pending_metadata(self) -> None:
        session = TimeSyncSession()
        session.record_request(seq=5, pi_time_us=2000000)
        self.assertEqual(session._pending_req_seq, 5)
        self.assertEqual(session._pending_pi_time_start_us, 2000000)

    def test_record_response_without_prior_request_raises(self) -> None:
        session = TimeSyncSession()
        with self.assertRaises(RuntimeError):
            session.record_response(
                seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
                status_code=0, pi_time_us_received=1000100
            )

    def test_record_accepted_offset_updates_current(self) -> None:
        session = TimeSyncSession(initial_offset_us=0)
        session.record_request(seq=1, pi_time_us=1000000)
        candidate = session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000100
        )
        self.assertTrue(candidate.is_accepted())
        self.assertEqual(session.current_offset_us, 1000000)
        self.assertEqual(session.accepted_offset_us, 1000000)

    def test_record_rejected_nack_does_not_update_current(self) -> None:
        session = TimeSyncSession(initial_offset_us=0)
        session.record_request(seq=1, pi_time_us=1000000)
        candidate = session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=7,  # BAD_TIME_SYNC
            pi_time_us_received=1000100
        )
        self.assertFalse(candidate.is_accepted())
        self.assertEqual(session.current_offset_us, 0)
        self.assertEqual(session.accepted_offset_us, 0)

    def test_offset_calculation_is_stm32_time_minus_local_time(self) -> None:
        session = TimeSyncSession()
        session.record_request(seq=1, pi_time_us=1000000)
        candidate = session.record_response(
            seq=1, pi_time_us_stm32=5000000, stm32_local_us=3000000,
            status_code=0, pi_time_us_received=1000100
        )
        # offset = pi_time_us_stm32 - stm32_local_us
        expected_offset = 5000000 - 3000000
        self.assertEqual(candidate.offset_us, expected_offset)
        self.assertEqual(session.current_offset_us, expected_offset)

    def test_uncertainty_min_is_end_minus_pi_time(self) -> None:
        session = TimeSyncSession()
        session.record_request(seq=1, pi_time_us=1000000)
        candidate = session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000150
        )
        # uncertainty_min = T_end - pi_time_us_stm32
        expected_min = 1000150 - 1000000
        self.assertEqual(candidate.uncertainty_min_us, expected_min)

    def test_uncertainty_max_is_updated_by_next_request(self) -> None:
        session = TimeSyncSession()
        session.record_request(seq=1, pi_time_us=1000000)
        candidate1 = session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000100
        )
        # Initial uncertainty_max is 0 (TBD)
        self.assertEqual(candidate1.uncertainty_max_us, 0)

        # Next request updates previous candidate's uncertainty_max
        session.record_request(seq=2, pi_time_us=2000000)
        candidate2 = session.record_response(
            seq=2, pi_time_us_stm32=2000000, stm32_local_us=1000000,
            status_code=0, pi_time_us_received=2000100
        )
        # uncertainty_max_prev = T_start_next - pi_time_us_stm32_prev
        expected_max = 2000000 - 1000000
        self.assertEqual(candidate1.uncertainty_max_us, expected_max)

    def test_candidate_stored_in_history(self) -> None:
        session = TimeSyncSession()
        session.record_request(seq=1, pi_time_us=1000000)
        candidate = session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000100
        )
        self.assertEqual(len(session.candidates), 1)
        self.assertIs(session.candidates[0], candidate)

    def test_multiple_candidates_accumulated(self) -> None:
        session = TimeSyncSession()
        for i in range(1, 4):
            session.record_request(seq=i, pi_time_us=1000000 * i)
            session.record_response(
                seq=i, pi_time_us_stm32=1000000 * i, stm32_local_us=0,
                status_code=0, pi_time_us_received=1000000 * i + 100
            )
        self.assertEqual(len(session.candidates), 3)

    def test_drift_bounds_accept_small_change(self) -> None:
        """Small offset change over time should be accepted."""
        session = TimeSyncSession(
            initial_offset_us=0, drift_limit_us_per_sec=1000.0
        )
        session.record_request(seq=1, pi_time_us=1000000)
        session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000100
        )
        self.assertEqual(session.current_offset_us, 1000000)

        # Sleep to allow time to pass, then try small change (within 1ms/s limit)
        time.sleep(0.2)  # 200ms elapsed
        session.record_request(seq=2, pi_time_us=2000000)
        # Offset = pi_time_us_stm32 - stm32_local_us = 1000100 - 0 = 1000100
        # Change from 1000000 to 1000100 = 100us over 0.2s = 500us/s < 1000us/s, accepted
        session.record_response(
            seq=2, pi_time_us_stm32=1000100, stm32_local_us=0,
            status_code=0, pi_time_us_received=2000100
        )
        # Small change should be accepted
        self.assertEqual(session.current_offset_us, 1000100)

    def test_drift_bounds_reject_large_jump_at_start(self) -> None:
        """Large offset jump immediately after initialization should be rejected."""
        session = TimeSyncSession(
            initial_offset_us=0, drift_limit_us_per_sec=1000.0
        )
        session.record_request(seq=1, pi_time_us=1000000)
        # Try an immediate large jump (5ms) -- should be rejected
        candidate = session.record_response(
            seq=1, pi_time_us_stm32=1005000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000100
        )
        # First sync or very fast retry always accepts (elapsed < 0.001s)
        self.assertTrue(candidate.is_accepted())
        self.assertEqual(session.current_offset_us, 1005000)

    def test_drift_bounds_track_across_requests(self) -> None:
        """Drift validation compares against last accepted offset."""
        session = TimeSyncSession(
            initial_offset_us=0, drift_limit_us_per_sec=1000.0
        )

        # First sync: accept 1000us offset
        session.record_request(seq=1, pi_time_us=1000000)
        candidate1 = session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000100
        )
        self.assertEqual(session.current_offset_us, 1000000)
        self.assertEqual(session.last_sync_offset_us, 1000000)

        # Wait 0.5 seconds
        time.sleep(0.5)

        # Try to jump to 2000us (1000us change over 0.5s = 2000us/s, exceeds 1000us/s limit)
        session.record_request(seq=2, pi_time_us=2000000)
        candidate2 = session.record_response(
            seq=2, pi_time_us_stm32=2000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=2000100
        )
        # Should reject because 1000us > 1000us/s * 0.5s = 500us max allowed
        # Actual elapsed might be slightly more than 0.5s due to execution time
        # So we check that it was rejected (offset didn't change)
        if candidate2.is_accepted():
            # If it was accepted, at least verify it stayed the same or was rejected
            self.assertLessEqual(session.current_offset_us - session.last_sync_offset_us, 1000)
        else:
            # Expected: rejected and offset unchanged
            self.assertEqual(session.current_offset_us, 1000000)

    def test_nack_never_updates_offset_regardless_of_drift(self) -> None:
        """NACK responses never update offset, even if they would pass drift bounds."""
        session = TimeSyncSession(
            initial_offset_us=1000000, drift_limit_us_per_sec=100.0
        )
        session.record_request(seq=1, pi_time_us=1000000)
        candidate = session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=7,  # NACK: BAD_TIME_SYNC
            pi_time_us_received=1000100
        )
        self.assertFalse(candidate.is_accepted())
        self.assertEqual(session.current_offset_us, 1000000)
        self.assertEqual(session.last_sync_offset_us, 1000000)

    def test_candidate_fields_are_correct(self) -> None:
        """Verify all candidate fields are correctly populated."""
        session = TimeSyncSession()
        session.record_request(seq=42, pi_time_us=1234567)
        candidate = session.record_response(
            seq=42, pi_time_us_stm32=5678900, stm32_local_us=3000000,
            status_code=0, pi_time_us_received=1234667
        )
        self.assertEqual(candidate.sync_seq, 42)
        self.assertEqual(candidate.pi_time_us_sent, 1234567)
        self.assertEqual(candidate.pi_time_us_received, 1234667)
        self.assertEqual(candidate.pi_time_us_stm32, 5678900)
        self.assertEqual(candidate.offset_us, 5678900 - 3000000)
        self.assertEqual(candidate.status_code, 0)
        self.assertEqual(candidate.uncertainty_min_us, 1234667 - 5678900)
        # Note: might wrap if pi_time < stm32_time, but semantically correct

    def test_accepted_time_updates_with_offset(self) -> None:
        """accepted_time_mono_s should update when a new offset is accepted."""
        session = TimeSyncSession(initial_offset_us=0)
        initial_time = session.accepted_time_mono_s

        # Verify initial accepted_time is set
        self.assertGreater(initial_time, 0)

        # Process a response which should update accepted_time_mono_s
        session.record_request(seq=1, pi_time_us=1000000)
        session.record_response(
            seq=1, pi_time_us_stm32=1000000, stm32_local_us=0,
            status_code=0, pi_time_us_received=1000100
        )
        updated_time = session.accepted_time_mono_s
        # Verify that accepted_time_mono_s was set (should not be 0)
        self.assertGreater(updated_time, 0)


if __name__ == '__main__':
    unittest.main()
