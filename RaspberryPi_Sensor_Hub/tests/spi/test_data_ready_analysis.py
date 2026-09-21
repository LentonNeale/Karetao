import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.data_ready_analysis import (
    DataReadyStats,
    compute_data_ready_stats,
    percentile_data_ready_latency,
)
from spi.timing import TransactionRecord


class DataReadyStatsTests(unittest.TestCase):
    """Tests for the DataReadyStats dataclass."""

    def test_dataclass_construction(self):
        """Verify DataReadyStats can be constructed with all fields."""
        stats = DataReadyStats(
            total_measurements=10,
            dr_to_nss_mean_us=100.5,
            dr_to_nss_std_us=20.0,
            dr_to_nss_min_us=50,
            dr_to_nss_max_us=200,
            nss_to_dr_mean_us=150.5,
            nss_to_dr_std_us=30.0,
            nss_to_dr_min_us=100,
            nss_to_dr_max_us=250,
            dr_interval_mean_us=500.0,
            dr_interval_std_us=50.0,
            dr_interval_min_us=400,
            dr_interval_max_us=600,
            dr_to_nss_within_cable_delay=True,
            firmware_loop_delay_plausible=True,
        )
        self.assertEqual(stats.total_measurements, 10)
        self.assertEqual(stats.dr_to_nss_mean_us, 100.5)
        self.assertTrue(stats.dr_to_nss_within_cable_delay)


class ComputeDataReadyStatsTests(unittest.TestCase):
    """Tests for compute_data_ready_stats() function."""

    def test_empty_records_list(self):
        """Empty records list yields zero measurements, all stats None."""
        stats = compute_data_ready_stats([])
        self.assertEqual(stats.total_measurements, 0)
        self.assertIsNone(stats.dr_to_nss_mean_us)
        self.assertIsNone(stats.nss_to_dr_mean_us)
        self.assertIsNone(stats.dr_interval_mean_us)
        self.assertTrue(stats.dr_to_nss_within_cable_delay)
        self.assertTrue(stats.firmware_loop_delay_plausible)

    def test_single_measurement_all_fields(self):
        """Single record with all three DATA_READY fields."""
        records = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100,
                nss_high_to_data_ready_low_us=50,
                data_ready_interval_us=1000,
            )
        ]
        stats = compute_data_ready_stats(records)

        self.assertEqual(stats.total_measurements, 1)
        self.assertEqual(stats.dr_to_nss_min_us, 100)
        self.assertEqual(stats.dr_to_nss_max_us, 100)
        self.assertEqual(stats.dr_to_nss_mean_us, 100.0)
        self.assertEqual(stats.dr_to_nss_std_us, 0.0)
        self.assertEqual(stats.nss_to_dr_min_us, 50)
        self.assertEqual(stats.nss_to_dr_max_us, 50)
        self.assertEqual(stats.dr_interval_min_us, 1000)
        self.assertEqual(stats.dr_interval_max_us, 1000)

    def test_multiple_measurements(self):
        """Multiple records compute correct statistics."""
        records = [
            TransactionRecord(
                index=i,
                block_id='test',
                request_seq=i,
                request_type='GET_STATUS',
                t_mono_ns=1000 * i,
                t_realtime_ns=2000 * i,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100 + i * 10,
                nss_high_to_data_ready_low_us=50 + i * 5,
                data_ready_interval_us=1000 + i * 100,
            )
            for i in range(5)
        ]
        stats = compute_data_ready_stats(records)

        self.assertEqual(stats.total_measurements, 5)
        # dr_to_nss: [100, 110, 120, 130, 140]
        self.assertEqual(stats.dr_to_nss_min_us, 100)
        self.assertEqual(stats.dr_to_nss_max_us, 140)
        self.assertEqual(stats.dr_to_nss_mean_us, 120.0)
        self.assertGreater(stats.dr_to_nss_std_us, 0)

        # nss_to_dr: [50, 55, 60, 65, 70]
        self.assertEqual(stats.nss_to_dr_min_us, 50)
        self.assertEqual(stats.nss_to_dr_max_us, 70)
        self.assertEqual(stats.nss_to_dr_mean_us, 60.0)

        # dr_interval: [1000, 1100, 1200, 1300, 1400]
        self.assertEqual(stats.dr_interval_min_us, 1000)
        self.assertEqual(stats.dr_interval_max_us, 1400)
        self.assertEqual(stats.dr_interval_mean_us, 1200.0)

    def test_partial_measurements_ignored(self):
        """Records without DATA_READY fields are skipped, not errored."""
        records = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100,
                # nss_high_to_data_ready_low_us and data_ready_interval_us are None
            ),
            TransactionRecord(
                index=1,
                block_id='test',
                request_seq=2,
                request_type='GET_STATUS',
                t_mono_ns=2000,
                t_realtime_ns=3000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                # All DATA_READY fields are None
            ),
        ]
        stats = compute_data_ready_stats(records)

        self.assertEqual(stats.total_measurements, 2)
        # Only 1 record has dr_to_nss
        self.assertEqual(stats.dr_to_nss_min_us, 100)
        self.assertEqual(stats.dr_to_nss_max_us, 100)
        # No records have nss_to_dr
        self.assertIsNone(stats.nss_to_dr_mean_us)
        # No records have dr_interval
        self.assertIsNone(stats.dr_interval_mean_us)

    def test_cable_delay_conformance_check(self):
        """DATA_READY to NSS latency < 5000 µs passes conformance."""
        # All within cable delay bound
        records = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=1000,
            )
        ]
        stats = compute_data_ready_stats(records)
        self.assertTrue(stats.dr_to_nss_within_cable_delay)

        # Exceeds cable delay bound
        records_over = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=6000,
            )
        ]
        stats_over = compute_data_ready_stats(records_over)
        self.assertFalse(stats_over.dr_to_nss_within_cable_delay)

    def test_firmware_loop_delay_plausibility_check(self):
        """NSS to DATA_READY fall is plausible if < 1 second."""
        # Plausible value
        records = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                nss_high_to_data_ready_low_us=1000,  # 1 ms
            )
        ]
        stats = compute_data_ready_stats(records)
        self.assertTrue(stats.firmware_loop_delay_plausible)

        # Implausible value (> 1s)
        records_implausible = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                nss_high_to_data_ready_low_us=2_000_000,  # 2 seconds
            )
        ]
        stats_implausible = compute_data_ready_stats(records_implausible)
        self.assertFalse(stats_implausible.firmware_loop_delay_plausible)

    def test_standard_deviation_single_vs_multiple(self):
        """Standard deviation is 0 for single value, > 0 for multiple."""
        single = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100,
            )
        ]
        stats_single = compute_data_ready_stats(single)
        self.assertEqual(stats_single.dr_to_nss_std_us, 0.0)

        # Multiple values with variance
        multiple = [
            TransactionRecord(
                index=i,
                block_id='test',
                request_seq=i,
                request_type='GET_STATUS',
                t_mono_ns=1000 * i,
                t_realtime_ns=2000 * i,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100 + i * 20,
            )
            for i in range(5)
        ]
        stats_multiple = compute_data_ready_stats(multiple)
        self.assertGreater(stats_multiple.dr_to_nss_std_us, 0)


class PercentileDataReadyLatencyTests(unittest.TestCase):
    """Tests for percentile_data_ready_latency() function."""

    def test_empty_records_returns_none(self):
        """No records yields None for all percentiles."""
        result = percentile_data_ready_latency([])
        self.assertEqual(result[5], None)
        self.assertEqual(result[50], None)
        self.assertEqual(result[95], None)

    def test_default_percentiles(self):
        """Default percentiles are [5, 50, 95]."""
        records = [
            TransactionRecord(
                index=i,
                block_id='test',
                request_seq=i,
                request_type='GET_STATUS',
                t_mono_ns=1000 * i,
                t_realtime_ns=2000 * i,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100 + i * 10,
            )
            for i in range(20)
        ]
        result = percentile_data_ready_latency(records)
        self.assertIn(5, result)
        self.assertIn(50, result)
        self.assertIn(95, result)
        self.assertIsNotNone(result[5])
        self.assertIsNotNone(result[50])
        self.assertIsNotNone(result[95])

    def test_single_record(self):
        """Single record: all percentiles return that value."""
        records = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100,
            )
        ]
        result = percentile_data_ready_latency(records, [0, 50, 100])
        self.assertEqual(result[0], 100)
        self.assertEqual(result[50], 100)
        self.assertEqual(result[100], 100)

    def test_ordered_percentiles_on_sorted_list(self):
        """Percentiles return values in the correct order."""
        # Create 100 records with latencies 1 to 100
        records = [
            TransactionRecord(
                index=i,
                block_id='test',
                request_seq=i,
                request_type='GET_STATUS',
                t_mono_ns=1000 * i,
                t_realtime_ns=2000 * i,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=i + 1,
            )
            for i in range(100)
        ]
        result = percentile_data_ready_latency(records, [0, 25, 50, 75, 100])

        # Percentiles should be ordered (not necessarily exactly at percentile points,
        # but in increasing order)
        self.assertLessEqual(result[0], result[25])
        self.assertLessEqual(result[25], result[50])
        self.assertLessEqual(result[50], result[75])
        self.assertLessEqual(result[75], result[100])

    def test_custom_percentiles(self):
        """Custom percentile list is respected."""
        records = [
            TransactionRecord(
                index=i,
                block_id='test',
                request_seq=i,
                request_type='GET_STATUS',
                t_mono_ns=1000 * i,
                t_realtime_ns=2000 * i,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=i + 1,
            )
            for i in range(20)
        ]
        custom_percentiles = [10, 25, 75, 99]
        result = percentile_data_ready_latency(records, custom_percentiles)

        for p in custom_percentiles:
            self.assertIn(p, result)
            self.assertIsNotNone(result[p])

    def test_records_without_data_ready_field_ignored(self):
        """Records without data_ready_to_nss_low_us are skipped."""
        records = [
            TransactionRecord(
                index=0,
                block_id='test',
                request_seq=1,
                request_type='GET_STATUS',
                t_mono_ns=1000,
                t_realtime_ns=2000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100,
            ),
            TransactionRecord(
                index=1,
                block_id='test',
                request_seq=2,
                request_type='GET_STATUS',
                t_mono_ns=2000,
                t_realtime_ns=3000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                # data_ready_to_nss_low_us is None
            ),
            TransactionRecord(
                index=2,
                block_id='test',
                request_seq=3,
                request_type='GET_STATUS',
                t_mono_ns=3000,
                t_realtime_ns=4000,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=200,
            ),
        ]
        result = percentile_data_ready_latency(records, [50])
        # Only 2 records have data_ready_to_nss_low_us (100, 200)
        self.assertIn(result[50], [100, 200])

    def test_percentile_with_tight_range(self):
        """When all values are the same, percentiles return that value."""
        records = [
            TransactionRecord(
                index=i,
                block_id='test',
                request_seq=i,
                request_type='GET_STATUS',
                t_mono_ns=1000 * i,
                t_realtime_ns=2000 * i,
                encode_ns=100,
                transfer_ns=200,
                decode_ns=50,
                total_ns=350,
                ok=True,
                data_ready_to_nss_low_us=100,  # Same value for all
            )
            for i in range(10)
        ]
        result = percentile_data_ready_latency(records, [5, 50, 95])
        self.assertEqual(result[5], 100)
        self.assertEqual(result[50], 100)
        self.assertEqual(result[95], 100)


class TransactionRecordDataReadyMethodTests(unittest.TestCase):
    """Tests for TransactionRecord.data_ready_latency_ms() method."""

    def test_converts_microseconds_to_milliseconds(self):
        """Conversion from microseconds to milliseconds is correct."""
        record = TransactionRecord(
            index=0,
            block_id='test',
            request_seq=1,
            request_type='GET_STATUS',
            t_mono_ns=1000,
            t_realtime_ns=2000,
            encode_ns=100,
            transfer_ns=200,
            decode_ns=50,
            total_ns=350,
            ok=True,
            data_ready_to_nss_low_us=1000,
        )
        self.assertEqual(record.data_ready_latency_ms(), 1.0)

        record2 = TransactionRecord(
            index=0,
            block_id='test',
            request_seq=1,
            request_type='GET_STATUS',
            t_mono_ns=1000,
            t_realtime_ns=2000,
            encode_ns=100,
            transfer_ns=200,
            decode_ns=50,
            total_ns=350,
            ok=True,
            data_ready_to_nss_low_us=500,
        )
        self.assertEqual(record2.data_ready_latency_ms(), 0.5)

    def test_returns_none_when_field_is_none(self):
        """Returns None when data_ready_to_nss_low_us is not set."""
        record = TransactionRecord(
            index=0,
            block_id='test',
            request_seq=1,
            request_type='GET_STATUS',
            t_mono_ns=1000,
            t_realtime_ns=2000,
            encode_ns=100,
            transfer_ns=200,
            decode_ns=50,
            total_ns=350,
            ok=True,
            # data_ready_to_nss_low_us is None by default
        )
        self.assertIsNone(record.data_ready_latency_ms())


if __name__ == '__main__':
    unittest.main()
