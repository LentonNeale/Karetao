"""Unit tests for TIME_SYNC analysis functions."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.time_sync_analysis import compute_stats, percentiles, TimeSyncStats
from spi.time_sync_session import TimeSyncSession


class ComputeStatsTests(unittest.TestCase):
    """Tests for compute_stats() function."""

    def test_compute_stats_empty_session(self) -> None:
        """Empty session should return all zeros."""
        session = TimeSyncSession()
        stats = compute_stats(session)

        self.assertEqual(stats.total_attempts, 0)
        self.assertEqual(stats.accepted_count, 0)
        self.assertEqual(stats.rejected_count, 0)
        self.assertEqual(stats.acceptance_rate, 0.0)
        self.assertEqual(stats.offset_mean_us, 0.0)
        self.assertEqual(stats.offset_std_us, 0.0)
        self.assertEqual(stats.offset_min_us, 0)
        self.assertEqual(stats.offset_max_us, 0)
        self.assertIsNone(stats.drift_rate_us_per_sec)
        self.assertEqual(stats.nack_distribution, {})

    def test_compute_stats_all_accepted(self) -> None:
        """All accepted syncs should compute correct statistics."""
        session = TimeSyncSession(initial_offset_us=0)

        # Simulate 5 accepted syncs with stable offset around 500000
        for i in range(5):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            # offset = pi_time_us_stm32 - stm32_local_us = 1000000 - 500000 = 500000
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - 500000,
                status_code=0,
                pi_time_us_received=pi_time + 100
            )

        stats = compute_stats(session)

        self.assertEqual(stats.total_attempts, 5)
        self.assertEqual(stats.accepted_count, 5)
        self.assertEqual(stats.rejected_count, 0)
        self.assertAlmostEqual(stats.acceptance_rate, 1.0)
        # All offsets should be 500000
        self.assertAlmostEqual(stats.offset_mean_us, 500000.0)
        # Standard deviation should be 0 or very close
        self.assertAlmostEqual(stats.offset_std_us, 0.0, places=1)
        self.assertEqual(stats.offset_min_us, 500000)
        self.assertEqual(stats.offset_max_us, 500000)
        self.assertIsNotNone(stats.drift_rate_us_per_sec)

    def test_compute_stats_mixed_acceptance(self) -> None:
        """Mixed accepted and rejected syncs should compute correctly."""
        session = TimeSyncSession(initial_offset_us=0)

        offsets = [500000, 501000, 499000]
        statuses = [0, 0, 7]  # two ACK, one BAD_TIME_SYNC

        for i, (offset, status) in enumerate(zip(offsets, statuses)):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - offset,
                status_code=status,
                pi_time_us_received=pi_time + 100
            )

        stats = compute_stats(session)

        self.assertEqual(stats.total_attempts, 3)
        self.assertEqual(stats.accepted_count, 2)
        self.assertEqual(stats.rejected_count, 1)
        self.assertAlmostEqual(stats.acceptance_rate, 2 / 3)
        self.assertIn('BAD_TIME_SYNC', stats.nack_distribution)
        self.assertEqual(stats.nack_distribution['BAD_TIME_SYNC'], 1)

    def test_compute_stats_all_rejected(self) -> None:
        """All rejected syncs should show rejection stats."""
        session = TimeSyncSession(initial_offset_us=0)

        for i in range(3):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - 500000,
                status_code=7,  # BAD_TIME_SYNC
                pi_time_us_received=pi_time + 100
            )

        stats = compute_stats(session)

        self.assertEqual(stats.total_attempts, 3)
        self.assertEqual(stats.accepted_count, 0)
        self.assertEqual(stats.rejected_count, 3)
        self.assertEqual(stats.acceptance_rate, 0.0)
        self.assertEqual(stats.offset_mean_us, 0.0)
        self.assertIsNone(stats.drift_rate_us_per_sec)
        self.assertEqual(stats.nack_distribution['BAD_TIME_SYNC'], 3)

    def test_compute_stats_drift_rate_with_stable_offset(self) -> None:
        """Drift rate should be ~0 for stable offsets."""
        session = TimeSyncSession(initial_offset_us=0)

        # Create 3 accepted syncs with stable offset, each 1 second apart
        base_pi_time = 1000000
        for i in range(3):
            pi_time = base_pi_time + i * 1000000  # 1 second apart
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - 500000,  # constant offset
                status_code=0,
                pi_time_us_received=pi_time + 100
            )

        stats = compute_stats(session)

        self.assertIsNotNone(stats.drift_rate_us_per_sec)
        # Drift rate should be very small (0 or close to 0)
        self.assertLess(abs(stats.drift_rate_us_per_sec), 1000)

    def test_compute_stats_uncertainty_statistics(self) -> None:
        """Uncertainty mean values should be computed correctly."""
        session = TimeSyncSession(initial_offset_us=0)

        # Create candidates with known uncertainty_min values
        for i in range(3):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            # uncertainty_min = pi_time_us_received - pi_time_us_stm32
            # Set it to 100, 150, 200 respectively
            pi_time_received = pi_time + (100 + i * 50)
            pi_time_stm32 = pi_time
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time_stm32,
                stm32_local_us=pi_time - 500000,
                status_code=0,
                pi_time_us_received=pi_time_received
            )

        stats = compute_stats(session)

        # Expected uncertainty_min values: 100, 150, 200
        expected_mean = (100 + 150 + 200) / 3
        self.assertAlmostEqual(stats.uncertainty_mean_min_us, expected_mean, places=1)

    def test_compute_stats_multiple_nack_reasons(self) -> None:
        """NACK distribution should account for multiple reasons."""
        session = TimeSyncSession(initial_offset_us=0)

        nack_reasons = [0, 7, 7, 4, 7]  # OK, BAD_TIME_SYNC, BAD_TIME_SYNC, BAD_CRC, BAD_TIME_SYNC

        for i, status in enumerate(nack_reasons):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - 500000,
                status_code=status,
                pi_time_us_received=pi_time + 100
            )

        stats = compute_stats(session)

        self.assertEqual(stats.accepted_count, 1)
        self.assertEqual(stats.rejected_count, 4)
        self.assertEqual(stats.nack_distribution['BAD_TIME_SYNC'], 3)
        self.assertEqual(stats.nack_distribution['BAD_CRC'], 1)


class PercentilesTests(unittest.TestCase):
    """Tests for percentiles() function."""

    def test_percentiles_empty_session(self) -> None:
        """Empty session should return zeros for all percentiles."""
        session = TimeSyncSession()
        p = percentiles(session, [25, 50, 75])

        self.assertEqual(p[25], 0)
        self.assertEqual(p[50], 0)
        self.assertEqual(p[75], 0)

    def test_percentiles_single_value(self) -> None:
        """Single accepted value should return that value for all percentiles."""
        session = TimeSyncSession(initial_offset_us=0)

        session.record_request(seq=1, pi_time_us=1000000)
        session.record_response(
            seq=1,
            pi_time_us_stm32=1000000,
            stm32_local_us=500000,
            status_code=0,
            pi_time_us_received=1000100
        )

        p = percentiles(session, [25, 50, 75])

        # All percentiles should be the single value (500000)
        self.assertEqual(p[25], 500000)
        self.assertEqual(p[50], 500000)
        self.assertEqual(p[75], 500000)

    def test_percentiles_five_values_linear(self) -> None:
        """Linear values should compute correct percentiles."""
        session = TimeSyncSession(initial_offset_us=0)

        offsets = [500000, 510000, 520000, 530000, 540000]

        for i, offset in enumerate(offsets):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - offset,
                status_code=0,
                pi_time_us_received=pi_time + 100
            )

        p = percentiles(session, [0, 25, 50, 75, 100])

        # Percentiles should match or be very close to expected values
        self.assertEqual(p[0], 500000)  # minimum
        self.assertLessEqual(p[25], 510000)  # near first quartile
        self.assertEqual(p[50], 520000)  # median
        self.assertGreaterEqual(p[75], 530000)  # near third quartile
        self.assertEqual(p[100], 540000)  # maximum

    def test_percentiles_ignores_rejected(self) -> None:
        """Rejected candidates should not affect percentiles."""
        session = TimeSyncSession(initial_offset_us=0)

        # Mix of accepted and rejected
        candidates = [
            (500000, 0),   # accepted
            (999999, 7),   # rejected (BAD_TIME_SYNC)
            (510000, 0),   # accepted
            (888888, 4),   # rejected (BAD_CRC)
            (520000, 0),   # accepted
        ]

        for i, (offset, status) in enumerate(candidates):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - offset,
                status_code=status,
                pi_time_us_received=pi_time + 100
            )

        p = percentiles(session, [25, 50, 75])

        # Only accepted values: 500000, 510000, 520000
        # Should not include the rejected values
        self.assertLess(p[25], 515000)
        self.assertEqual(p[50], 510000)  # median
        self.assertGreaterEqual(p[75], 515000)

    def test_percentiles_default_points(self) -> None:
        """Default percentile points should be [5, 25, 50, 75, 95]."""
        session = TimeSyncSession(initial_offset_us=0)

        # Create 20 values from 500000 to 509500 (step of 500)
        for i in range(20):
            offset = 500000 + i * 500
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - offset,
                status_code=0,
                pi_time_us_received=pi_time + 100
            )

        p = percentiles(session)  # Uses default points

        self.assertIn(5, p)
        self.assertIn(25, p)
        self.assertIn(50, p)
        self.assertIn(75, p)
        self.assertIn(95, p)

        # Verify ordering
        self.assertLessEqual(p[5], p[25])
        self.assertLessEqual(p[25], p[50])
        self.assertLessEqual(p[50], p[75])
        self.assertLessEqual(p[75], p[95])


class CsvLoggingTests(unittest.TestCase):
    """Tests for CSV logging methods."""

    def test_csv_header_format(self) -> None:
        """CSV header should have correct pipe-separated format."""
        header = TimeSyncSession.to_csv_header()

        expected_fields = [
            'timestamp_s', 'sync_seq', 'status', 'pi_time_us', 'stm32_local_us',
            'offset_us', 'uncertainty_min_us', 'uncertainty_max_us', 'accepted'
        ]

        # Split by pipe and strip whitespace
        fields = [f.strip() for f in header.split('|')]
        self.assertEqual(fields, expected_fields)

    def test_csv_rows_empty_session(self) -> None:
        """Empty session should produce no CSV rows."""
        session = TimeSyncSession()
        rows = session.to_csv_rows()

        self.assertEqual(rows, [])

    def test_csv_rows_format_accepted(self) -> None:
        """CSV row for accepted candidate should have correct format."""
        session = TimeSyncSession(initial_offset_us=0)

        session.record_request(seq=42, pi_time_us=1234567)
        session.record_response(
            seq=42,
            pi_time_us_stm32=5678900,
            stm32_local_us=3000000,
            status_code=0,
            pi_time_us_received=1234667
        )

        rows = session.to_csv_rows()

        self.assertEqual(len(rows), 1)
        row = rows[0]

        # Check that required fields are present
        self.assertIn('42', row)  # sync_seq
        self.assertIn('OK', row)  # status for ACK
        self.assertIn('5678900', row)  # pi_time_us
        self.assertIn('2678900', row)  # offset_us (5678900 - 3000000)
        self.assertIn('yes', row)  # accepted flag

    def test_csv_rows_format_rejected(self) -> None:
        """CSV row for rejected candidate should have correct NACK reason."""
        session = TimeSyncSession(initial_offset_us=0)

        session.record_request(seq=1, pi_time_us=1000000)
        session.record_response(
            seq=1,
            pi_time_us_stm32=1000000,
            stm32_local_us=500000,
            status_code=7,  # BAD_TIME_SYNC
            pi_time_us_received=1000100
        )

        rows = session.to_csv_rows()

        self.assertEqual(len(rows), 1)
        row = rows[0]

        self.assertIn('BAD_TIME_SYNC', row)  # NACK reason
        self.assertIn('no', row)  # accepted flag is 'no'

    def test_csv_rows_multiple_candidates(self) -> None:
        """Multiple candidates should produce multiple CSV rows."""
        session = TimeSyncSession(initial_offset_us=0)

        for i in range(3):
            pi_time = 1000000 + i * 100000
            session.record_request(seq=i + 1, pi_time_us=pi_time)
            session.record_response(
                seq=i + 1,
                pi_time_us_stm32=pi_time,
                stm32_local_us=pi_time - 500000,
                status_code=0,
                pi_time_us_received=pi_time + 100
            )

        rows = session.to_csv_rows()

        self.assertEqual(len(rows), 3)
        # Each row should contain the corresponding sequence number
        for i, row in enumerate(rows):
            self.assertIn(str(i + 1), row)


if __name__ == '__main__':
    unittest.main()
