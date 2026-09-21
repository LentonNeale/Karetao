"""Unit tests for measurement report generation and analysis."""

import sys
import unittest
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.measurement_report import (
    SessionReport, RepeatabilityMetrics, compute_repeatability_metrics,
    load_session_csv, write_report_files, generate_text_report
)


class SessionReportTests(unittest.TestCase):
    """Tests for SessionReport dataclass."""

    def test_session_report_creation(self) -> None:
        """SessionReport should be constructible with all fields."""
        report = SessionReport(
            session_num=1,
            total_attempts=100,
            accepted_count=95,
            acceptance_rate=0.95,
            offset_mean_us=500000.0,
            offset_std_us=1000.0,
            offset_min_us=498000,
            offset_max_us=502000,
            percentile_50_us=500000,
            percentile_95_us=501500,
            drift_rate_us_per_s=10.5,
        )

        self.assertEqual(report.session_num, 1)
        self.assertEqual(report.total_attempts, 100)
        self.assertEqual(report.accepted_count, 95)
        self.assertAlmostEqual(report.acceptance_rate, 0.95)
        self.assertAlmostEqual(report.offset_mean_us, 500000.0)


class LoadSessionCsvTests(unittest.TestCase):
    """Tests for CSV parsing."""

    def test_load_session_csv_nonexistent(self) -> None:
        """load_session_csv should return None for non-existent file."""
        result = load_session_csv(Path('/nonexistent/file.csv'))
        self.assertIsNone(result)

    def test_load_session_csv_empty_file(self) -> None:
        """load_session_csv should return None for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            result = load_session_csv(csv_path)
            self.assertIsNone(result)
        finally:
            csv_path.unlink()

    def test_load_session_csv_header_only(self) -> None:
        """load_session_csv should return None for header-only file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('timestamp_s | sync_seq | status | pi_time_us | stm32_local_us | offset_us | uncertainty_min_us | uncertainty_max_us | accepted\n')
            csv_path = Path(f.name)

        try:
            result = load_session_csv(csv_path)
            self.assertIsNone(result)
        finally:
            csv_path.unlink()

    def test_load_session_csv_single_accepted(self) -> None:
        """load_session_csv should parse a single accepted candidate."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('timestamp_s | sync_seq | status | pi_time_us | stm32_local_us | offset_us | uncertainty_min_us | uncertainty_max_us | accepted\n')
            f.write('2024-01-01T00:00:00.000000 | 1 | OK | 1000000 | 500000 | 500000 | 100 | 200 | yes\n')
            csv_path = Path(f.name)

        try:
            report = load_session_csv(csv_path)
            self.assertIsNotNone(report)
            self.assertEqual(report.total_attempts, 1)
            self.assertEqual(report.accepted_count, 1)
            self.assertAlmostEqual(report.acceptance_rate, 1.0)
            self.assertAlmostEqual(report.offset_mean_us, 500000.0)
        finally:
            csv_path.unlink()

    def test_load_session_csv_multiple_rows(self) -> None:
        """load_session_csv should parse multiple candidates."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('timestamp_s | sync_seq | status | pi_time_us | stm32_local_us | offset_us | uncertainty_min_us | uncertainty_max_us | accepted\n')
            f.write('2024-01-01T00:00:00.000000 | 1 | OK | 1000000 | 500000 | 500000 | 100 | 200 | yes\n')
            f.write('2024-01-01T00:00:00.050000 | 2 | OK | 1050000 | 550000 | 500000 | 100 | 200 | yes\n')
            f.write('2024-01-01T00:00:00.100000 | 3 | OK | 1100000 | 600000 | 500000 | 100 | 200 | yes\n')
            csv_path = Path(f.name)

        try:
            report = load_session_csv(csv_path)
            self.assertIsNotNone(report)
            self.assertEqual(report.total_attempts, 3)
            self.assertEqual(report.accepted_count, 3)
            self.assertAlmostEqual(report.acceptance_rate, 1.0)
            self.assertAlmostEqual(report.offset_mean_us, 500000.0)
        finally:
            csv_path.unlink()

    def test_load_session_csv_mixed_accept_reject(self) -> None:
        """load_session_csv should handle both ACK and NACK responses."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('timestamp_s | sync_seq | status | pi_time_us | stm32_local_us | offset_us | uncertainty_min_us | uncertainty_max_us | accepted\n')
            f.write('2024-01-01T00:00:00.000000 | 1 | OK | 1000000 | 500000 | 500000 | 100 | 200 | yes\n')
            f.write('2024-01-01T00:00:00.050000 | 2 | DRIFT_TOO_FAST | 1050000 | 550000 | 505000 | 100 | 200 | no\n')
            f.write('2024-01-01T00:00:00.100000 | 3 | OK | 1100000 | 600000 | 500000 | 100 | 200 | yes\n')
            csv_path = Path(f.name)

        try:
            report = load_session_csv(csv_path)
            self.assertIsNotNone(report)
            self.assertEqual(report.total_attempts, 3)
            self.assertEqual(report.accepted_count, 2)
            self.assertAlmostEqual(report.acceptance_rate, 2/3)
            self.assertAlmostEqual(report.offset_mean_us, 500000.0)  # Only accepted
        finally:
            csv_path.unlink()


class RepeatabilityMetricsTests(unittest.TestCase):
    """Tests for repeatability metrics computation."""

    def test_compute_repeatability_empty_list(self) -> None:
        """compute_repeatability_metrics should handle empty list."""
        metrics = compute_repeatability_metrics([])
        self.assertEqual(metrics.num_sessions, 0)
        self.assertEqual(metrics.offset_mean_of_means_us, 0.0)
        self.assertFalse(metrics.means_within_target)
        self.assertFalse(metrics.acceptance_rate_high)

    def test_compute_repeatability_single_session(self) -> None:
        """compute_repeatability_metrics with one session."""
        report = SessionReport(
            session_num=1,
            total_attempts=100,
            accepted_count=100,
            acceptance_rate=1.0,
            offset_mean_us=500000.0,
            offset_std_us=1000.0,
            offset_min_us=498000,
            offset_max_us=502000,
            percentile_50_us=500000,
            percentile_95_us=501500,
            drift_rate_us_per_s=10.0,
        )

        metrics = compute_repeatability_metrics([report])
        self.assertEqual(metrics.num_sessions, 1)
        self.assertAlmostEqual(metrics.offset_mean_of_means_us, 500000.0)
        self.assertEqual(metrics.offset_std_of_means_us, 0.0)
        self.assertTrue(metrics.means_within_target)  # Only one session
        self.assertTrue(metrics.acceptance_rate_high)  # 100%
        self.assertTrue(metrics.variance_consistent)

    def test_compute_repeatability_multiple_sessions_stable(self) -> None:
        """Repeatability with stable offset across sessions."""
        reports = [
            SessionReport(1, 100, 100, 1.0, 500000.0, 1000.0, 498000, 502000, 500000, 501500, 10.0),
            SessionReport(2, 100, 100, 1.0, 500500.0, 1100.0, 498500, 502500, 500500, 501500, 11.0),
            SessionReport(3, 100, 100, 1.0, 499500.0, 900.0, 497500, 501500, 499500, 500500, 9.0),
        ]

        metrics = compute_repeatability_metrics(reports)
        self.assertEqual(metrics.num_sessions, 3)
        self.assertTrue(metrics.means_within_target)  # Range = 1000 µs
        self.assertTrue(metrics.acceptance_rate_high)  # All 100%
        self.assertTrue(metrics.variance_consistent)

    def test_compute_repeatability_means_exceed_target(self) -> None:
        """Repeatability fails when means exceed ±1ms spread."""
        reports = [
            SessionReport(1, 100, 100, 1.0, 500000.0, 1000.0, 498000, 502000, 500000, 501500, 10.0),
            SessionReport(2, 100, 100, 1.0, 502000.0, 1100.0, 500000, 504000, 502000, 503000, 11.0),
            SessionReport(3, 100, 100, 1.0, 500000.0, 900.0, 498000, 502000, 500000, 501000, 9.0),
        ]

        metrics = compute_repeatability_metrics(reports)
        self.assertFalse(metrics.means_within_target)  # Range = 2000 µs > 1000

    def test_compute_repeatability_low_acceptance_rate(self) -> None:
        """Repeatability fails when acceptance rate < 90%."""
        reports = [
            SessionReport(1, 100, 85, 0.85, 500000.0, 1000.0, 498000, 502000, 500000, 501500, 10.0),
            SessionReport(2, 100, 100, 1.0, 500500.0, 1100.0, 498500, 502500, 500500, 501500, 11.0),
        ]

        metrics = compute_repeatability_metrics(reports)
        self.assertFalse(metrics.acceptance_rate_high)  # First session < 90%

    def test_compute_repeatability_inconsistent_variance(self) -> None:
        """Repeatability fails when variance is inconsistent across sessions."""
        reports = [
            SessionReport(1, 100, 100, 1.0, 500000.0, 5000.0, 495000, 505000, 500000, 502500, 10.0),
            SessionReport(2, 100, 100, 1.0, 500500.0, 150000.0, 350500, 650500, 500500, 501500, 11.0),
        ]

        metrics = compute_repeatability_metrics(reports)
        # High variance in stds: 5000 and 150000
        # Mean offset: 500250, stdev of stds ≈ 102325
        # rel_std ≈ 102325 / 500250 ≈ 20.4% > 20%
        self.assertFalse(metrics.variance_consistent)  # > 20% relative variance

    def test_conformance_pass(self) -> None:
        """All conformance checks pass together."""
        reports = [
            SessionReport(1, 100, 95, 0.95, 500000.0, 1000.0, 498000, 502000, 500000, 501500, 10.0),
            SessionReport(2, 100, 92, 0.92, 500300.0, 1100.0, 498300, 502300, 500300, 501500, 11.0),
            SessionReport(3, 100, 97, 0.97, 499700.0, 900.0, 497700, 501700, 499700, 500700, 9.0),
        ]

        metrics = compute_repeatability_metrics(reports)
        self.assertTrue(metrics.means_within_target)
        self.assertTrue(metrics.acceptance_rate_high)
        self.assertTrue(metrics.variance_consistent)


class GenerateTextReportTests(unittest.TestCase):
    """Tests for text report generation."""

    def test_generate_text_report_pass(self) -> None:
        """Text report should indicate PASS when all checks pass."""
        metrics = RepeatabilityMetrics(
            num_sessions=3,
            offset_mean_of_means_us=500000.0,
            offset_std_of_means_us=300.0,
            offset_min_mean_us=499700,
            offset_max_mean_us=500300,
            std_dev_of_stds_us=100.0,
            acceptance_rate_mean=0.95,
            acceptance_rate_std=0.02,
            acceptance_rate_min=0.92,
            acceptance_rate_max=0.97,
            means_within_target=True,
            acceptance_rate_high=True,
            variance_consistent=True,
        )

        report = generate_text_report(metrics)
        self.assertIn('Overall Result: PASS', report)
        self.assertIn('Sessions: 3', report)
        self.assertIn('+500000', report)

    def test_generate_text_report_fail(self) -> None:
        """Text report should indicate FAIL when checks fail."""
        metrics = RepeatabilityMetrics(
            num_sessions=3,
            offset_mean_of_means_us=500000.0,
            offset_std_of_means_us=1000.0,
            offset_min_mean_us=498000,
            offset_max_mean_us=502500,
            std_dev_of_stds_us=5000.0,
            acceptance_rate_mean=0.85,
            acceptance_rate_std=0.05,
            acceptance_rate_min=0.80,
            acceptance_rate_max=0.90,
            means_within_target=False,
            acceptance_rate_high=False,
            variance_consistent=False,
        )

        report = generate_text_report(metrics)
        self.assertIn('Overall Result: FAIL', report)


class WriteReportFilesTests(unittest.TestCase):
    """Tests for report file writing."""

    def test_write_report_files_creates_output(self) -> None:
        """write_report_files should create text and JSON reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            metrics = RepeatabilityMetrics(
                num_sessions=2,
                offset_mean_of_means_us=500000.0,
                offset_std_of_means_us=300.0,
                offset_min_mean_us=499700,
                offset_max_mean_us=500300,
                std_dev_of_stds_us=100.0,
                acceptance_rate_mean=0.95,
                acceptance_rate_std=0.02,
                acceptance_rate_min=0.92,
                acceptance_rate_max=0.97,
                means_within_target=True,
                acceptance_rate_high=True,
                variance_consistent=True,
            )

            reports = [
                SessionReport(1, 100, 95, 0.95, 500000.0, 1000.0, 498000, 502000, 500000, 501500, 10.0),
                SessionReport(2, 100, 97, 0.97, 500300.0, 1000.0, 498300, 502300, 500300, 501500, 10.0),
            ]

            write_report_files(output_dir, metrics, reports)

            # Check files were created
            self.assertTrue((output_dir / 'report.txt').exists())
            self.assertTrue((output_dir / 'repeatability_metrics.json').exists())

            # Check text report content
            with open(output_dir / 'report.txt', 'r') as f:
                text = f.read()
                self.assertIn('PASS', text)
                self.assertIn('Sessions: 2', text)

            # Check JSON content
            with open(output_dir / 'repeatability_metrics.json', 'r') as f:
                data = json.load(f)
                self.assertEqual(data['num_sessions'], 2)
                self.assertAlmostEqual(data['offset_mean_of_means_us'], 500000.0)
                self.assertTrue(data['conformance']['overall_pass'])


if __name__ == '__main__':
    unittest.main()
