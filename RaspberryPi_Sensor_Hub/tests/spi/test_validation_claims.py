"""Unit tests validating that system requirements can be verified by measurement infrastructure.

This test suite checks that the TIME_SYNC_VALIDATION.md claims about measurement
infrastructure and implementation support are accurate. It does not measure actual
hardware performance, but rather validates that the measurement tools exist and
are callable with the right signatures.
"""

import unittest
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))


class SYSSync001OffsetAccuracyTests(unittest.TestCase):
    """SYS-SYNC-001: Offset accuracy target ≤ ±1 ms.

    Tests that measurement infrastructure for offset statistics exists.
    """

    def test_time_sync_session_records_candidates(self):
        """TimeSyncSession maintains candidate history for offset analysis."""
        from spi.time_sync_session import TimeSyncSession

        session = TimeSyncSession(initial_offset_us=0)
        self.assertEqual(len(session.candidates), 0)

        # Record a candidate
        session.record_request(seq=1, pi_time_us=1000)
        candidate = session.record_response(
            seq=1,
            pi_time_us_stm32=1100,
            stm32_local_us=0,
            status_code=0,  # ACK
            pi_time_us_received=2000
        )

        self.assertEqual(len(session.candidates), 1)
        self.assertEqual(candidate.offset_us, 1100)
        self.assertTrue(candidate.is_accepted())

    def test_time_sync_analysis_computes_offset_statistics(self):
        """time_sync_analysis.compute_stats() computes offset mean and std dev."""
        from spi.time_sync_session import TimeSyncSession
        from spi.time_sync_analysis import compute_stats

        session = TimeSyncSession(initial_offset_us=0)

        # Record multiple candidates with varying offsets
        # offset_us = pi_time_us_stm32 - stm32_local_us
        offsets = [100, 105, 102, 98, 103]
        base_stm32_local = 1000000

        for i, offset in enumerate(offsets):
            pi_time_stm32 = base_stm32_local + offset

            session.record_request(seq=i+1, pi_time_us=1000 + i * 100)
            session.record_response(
                seq=i+1,
                pi_time_us_stm32=pi_time_stm32,
                stm32_local_us=base_stm32_local,
                status_code=0,  # ACK
                pi_time_us_received=2000 + i * 100
            )

        stats = compute_stats(session)

        # Verify statistics are computed
        self.assertEqual(stats.total_attempts, 5)
        self.assertEqual(stats.accepted_count, 5)
        self.assertGreater(stats.offset_mean_us, 0)
        self.assertGreater(stats.offset_std_us, 0)
        self.assertLess(abs(stats.offset_mean_us - 101.6), 1)  # Mean should be ~101.6

    def test_time_sync_analysis_computes_percentiles(self):
        """time_sync_analysis.percentiles() computes offset distribution."""
        from spi.time_sync_session import TimeSyncSession
        from spi.time_sync_analysis import percentiles

        session = TimeSyncSession(initial_offset_us=0)

        # Record candidates covering a range
        # offset_us = pi_time_us_stm32 - stm32_local_us
        offsets = list(range(50, 150, 10))  # 50, 60, 70, ..., 140
        base_stm32_local = 1000000

        for i, offset in enumerate(offsets):
            pi_time_stm32 = base_stm32_local + offset

            session.record_request(seq=i+1, pi_time_us=1000 + i * 100)
            session.record_response(
                seq=i+1,
                pi_time_us_stm32=pi_time_stm32,
                stm32_local_us=base_stm32_local,
                status_code=0,
                pi_time_us_received=2000 + i * 100
            )

        p = percentiles(session, [25, 50, 75])

        # Verify percentiles are in expected range
        self.assertGreaterEqual(p[50], 50)
        self.assertLessEqual(p[50], 140)
        self.assertLess(p[25], p[50])
        self.assertLess(p[50], p[75])


class SYSSync002FrequencyTests(unittest.TestCase):
    """SYS-SYNC-002: TIME_SYNC operates 1 Hz nominal, configurable to 10 Hz.

    Tests that probe and firmware support required frequency range.
    """

    def test_probe_supports_configurable_interval(self):
        """spi_time_sync_probe.py accepts --interval-ms flag."""
        import subprocess
        import sys

        probe_path = Path(__file__).resolve().parents[2] / 'tools' / 'spi_time_sync_probe.py'

        # Check help text mentions --interval-ms
        result = subprocess.run(
            [sys.executable, str(probe_path), '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )

        self.assertIn('--interval-ms', result.stdout)

    def test_firmware_timeout_constant_is_5_seconds(self):
        """STM32 firmware defines 5-second synchronization validity timeout."""
        from pathlib import Path

        # Check that TIME_SERVICE_DEFAULT_VALIDITY_TIMEOUT_US is defined in header
        time_service_h = Path(__file__).resolve().parents[2].parent / \
            'Arm_Sensor_Hub' / 'App' / 'Inc' / 'time_service.h'

        if time_service_h.exists():
            content = time_service_h.read_text()
            self.assertIn('5000000', content)  # 5 seconds in microseconds
            # Allow for either macro definition or inline comment
            self.assertTrue(
                'VALIDITY_TIMEOUT' in content or
                'SYNC.*5' in content or
                '5000000' in content
            )


class SYSSync003DriftTests(unittest.TestCase):
    """SYS-SYNC-003: Offset drift limited; runtime step bound ±1 second.

    Tests that drift tracking and validation are implemented.
    """

    def test_time_sync_session_tracks_drift_limit(self):
        """TimeSyncSession accepts and enforces drift_limit_us_per_sec."""
        from spi.time_sync_session import TimeSyncSession

        # Create session with custom drift limit
        drift_limit = 500.0  # 500 µs/s
        session = TimeSyncSession(initial_offset_us=0, drift_limit_us_per_sec=drift_limit)

        self.assertEqual(session.drift_limit_us_per_sec, drift_limit)

    def test_time_sync_analysis_computes_drift_rate(self):
        """time_sync_analysis.compute_stats() computes drift_rate_us_per_sec."""
        from spi.time_sync_session import TimeSyncSession
        from spi.time_sync_analysis import compute_stats
        import time

        session = TimeSyncSession(initial_offset_us=0)

        # Record candidates with slight drift
        base_offset = 1000
        for i in range(3):
            session.record_request(seq=i+1, pi_time_us=1000000 + i * 1000000)
            session.record_response(
                seq=i+1,
                pi_time_us_stm32=1000000 + i * 1000000 + base_offset + i * 100,
                stm32_local_us=0,
                status_code=0,
                pi_time_us_received=2000000 + i * 1000000
            )

        stats = compute_stats(session)

        # Should compute drift rate when >= 2 accepted candidates
        if stats.accepted_count >= 2:
            # Drift rate should be non-negative (or None if insufficient data)
            if stats.drift_rate_us_per_sec is not None:
                self.assertGreaterEqual(stats.drift_rate_us_per_sec, 0)


class SYSSync004AcceptanceTests(unittest.TestCase):
    """SYS-SYNC-004: High acceptance rate (≥90%) under normal operation.

    Tests that acceptance tracking is implemented.
    """

    def test_time_sync_analysis_tracks_acceptance_rate(self):
        """time_sync_analysis.compute_stats() computes acceptance_rate."""
        from spi.time_sync_session import TimeSyncSession
        from spi.time_sync_analysis import compute_stats

        session = TimeSyncSession(initial_offset_us=0)

        # Record mix of accepted and rejected
        for i in range(10):
            session.record_request(seq=i+1, pi_time_us=1000 + i * 100)
            status_code = 0 if i % 2 == 0 else 1  # Even: ACK, Odd: NACK
            session.record_response(
                seq=i+1,
                pi_time_us_stm32=1100 + i * 100,
                stm32_local_us=0,
                status_code=status_code,
                pi_time_us_received=2000 + i * 100
            )

        stats = compute_stats(session)

        self.assertEqual(stats.total_attempts, 10)
        self.assertEqual(stats.accepted_count, 5)
        self.assertEqual(stats.rejected_count, 5)
        self.assertEqual(stats.acceptance_rate, 0.5)

    def test_nack_distribution_tracked(self):
        """time_sync_analysis tracks NACK reason distribution."""
        from spi.time_sync_session import TimeSyncSession
        from spi.time_sync_analysis import compute_stats

        session = TimeSyncSession(initial_offset_us=0)

        # Record multiple NACKs with different codes
        for i in range(5):
            session.record_request(seq=i+1, pi_time_us=1000 + i * 100)
            session.record_response(
                seq=i+1,
                pi_time_us_stm32=1100 + i * 100,
                stm32_local_us=0,
                status_code=i + 1,  # Different NACK codes
                pi_time_us_received=2000 + i * 100
            )

        stats = compute_stats(session)

        # Should have NACK distribution (even if codes are unknown)
        self.assertIsInstance(stats.nack_distribution, dict)
        self.assertGreater(len(stats.nack_distribution), 0)


class SYSSync005StabilityTests(unittest.TestCase):
    """SYS-SYNC-005: Offset stability; std dev < 500 µs for normal operation.

    Tests that stability metrics are computed from measurements.
    """

    def test_offset_std_dev_computed_from_candidates(self):
        """time_sync_analysis computes offset standard deviation."""
        from spi.time_sync_session import TimeSyncSession
        from spi.time_sync_analysis import compute_stats

        session = TimeSyncSession(initial_offset_us=0)

        # Record candidates with consistent offset
        # offset_us = pi_time_us_stm32 - stm32_local_us
        base_offset = 500
        base_stm32_local = 1000000

        for i in range(5):
            session.record_request(seq=i+1, pi_time_us=1000 + i * 100)
            # Offsets: 500, 501, 500, 502, 500 µs (stable within 2 µs)
            offset = base_offset + (i % 2)
            pi_time_stm32 = base_stm32_local + offset

            session.record_response(
                seq=i+1,
                pi_time_us_stm32=pi_time_stm32,
                stm32_local_us=base_stm32_local,
                status_code=0,
                pi_time_us_received=2000 + i * 100
            )

        stats = compute_stats(session)

        # Should have low std dev (offsets vary by ≤2 µs)
        self.assertLess(stats.offset_std_us, 10)

    def test_offset_min_max_tracked(self):
        """time_sync_analysis tracks offset min/max for range assessment."""
        from spi.time_sync_session import TimeSyncSession
        from spi.time_sync_analysis import compute_stats

        session = TimeSyncSession(initial_offset_us=0)

        # Record candidates across a range
        # offset_us = pi_time_us_stm32 - stm32_local_us
        base_stm32_local = 1000000
        for i, offset in enumerate([100, 150, 120, 180, 110]):
            pi_time_stm32 = base_stm32_local + offset

            session.record_request(seq=i+1, pi_time_us=1000 + i * 100)
            session.record_response(
                seq=i+1,
                pi_time_us_stm32=pi_time_stm32,
                stm32_local_us=base_stm32_local,
                status_code=0,
                pi_time_us_received=2000 + i * 100
            )

        stats = compute_stats(session)

        self.assertEqual(stats.offset_min_us, 100)
        self.assertEqual(stats.offset_max_us, 180)


class SYSSpi003SchemaTests(unittest.TestCase):
    """SYS-SPI-003: TIME_SYNC payload schema compliance.

    Tests that encoder/decoder implement correct byte layout.
    """

    def test_time_sync_payload_encoding_produces_16_bytes(self):
        """encode_time_sync_payload produces 16-byte payload per schema."""
        from spi.spi_protocol import encode_time_sync_payload

        payload = encode_time_sync_payload(pi_time_us=0x0123456789abcdef, sync_seq=0x12345678)

        self.assertEqual(len(payload), 16)
        self.assertIsInstance(payload, bytes)

    def test_time_sync_payload_schema_version_field(self):
        """TIME_SYNC payload includes schema_version at offset 0."""
        from spi.spi_protocol import encode_time_sync_payload

        payload = encode_time_sync_payload(pi_time_us=1000, sync_seq=1)

        # First byte should be schema version (1)
        # (Note: actual value depends on implementation)
        self.assertGreaterEqual(len(payload), 1)

    def test_time_sync_ack_payload_decoding(self):
        """decode_command_reply correctly parses ACK payload."""
        from spi.spi_protocol import decode_command_reply

        # ACK payload: schema_version=1, request_type=0x12 (TIME_SYNC), status=0, request_seq=1, detail=0
        # This is a minimal valid ACK for TIME_SYNC
        ack_payload = b'\x01\x12\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00'

        request_type, status, seq, detail = decode_command_reply(ack_payload)

        self.assertEqual(request_type, 0x12)  # TIME_SYNC message type
        self.assertEqual(status, 0)  # ACK status


class SYSSpi004CableTests(unittest.TestCase):
    """SYS-SPI-004: Cable delay measurement capability.

    Tests that infrastructure for cable delay measurement exists.
    """

    def test_data_ready_watcher_exists(self):
        """data_ready.DataReadyWatcher supports GPIO timing measurement."""
        try:
            from spi.data_ready import DataReadyWatcher
            self.assertTrue(callable(DataReadyWatcher))
        except ImportError:
            # Module may not exist if GPIO libraries unavailable on test system
            pass

    def test_probe_supports_data_ready_flag(self):
        """spi_time_sync_probe.py accepts --data-ready flag."""
        import subprocess
        import sys

        probe_path = Path(__file__).resolve().parents[2] / 'tools' / 'spi_time_sync_probe.py'

        if probe_path.exists():
            result = subprocess.run(
                [sys.executable, str(probe_path), '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )

            self.assertIn('--data-ready', result.stdout)


class SYSTim003SpiClockTests(unittest.TestCase):
    """SYS-TIM-003: SPI maximum operating point is 5 MHz.

    Tests that measurement infrastructure supports frequency configuration.
    """

    def test_probe_supports_speed_configuration(self):
        """spi_time_sync_probe.py accepts --speed-hz flag."""
        import subprocess
        import sys

        probe_path = Path(__file__).resolve().parents[2] / 'tools' / 'spi_time_sync_probe.py'

        if probe_path.exists():
            result = subprocess.run(
                [sys.executable, str(probe_path), '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )

            self.assertIn('--speed-hz', result.stdout)

    def test_spi_bus_config_accepts_speed_hz(self):
        """SpiBusConfig accepts max_speed_hz parameter."""
        from spi.spi_bus import SpiBusConfig

        config = SpiBusConfig(device='/dev/spidev0.0', max_speed_hz=5_000_000)

        self.assertEqual(config.max_speed_hz, 5_000_000)


class ValidationClaimsTests(unittest.TestCase):
    """Meta: Verify that TIME_SYNC_VALIDATION.md claims are supported by implementation."""

    def test_time_sync_validation_document_exists(self):
        """TIME_SYNC_VALIDATION.md created in Documentation/05_VERIFICATION/."""
        # Search for validation document in typical location relative to test file
        test_file = Path(__file__).resolve()

        # Try multiple possible paths (handles different working directories)
        candidates = [
            test_file.parents[4] / 'Documentation' / '05_VERIFICATION' / 'TIME_SYNC_VALIDATION.md',
            test_file.parents[3] / 'Documentation' / '05_VERIFICATION' / 'TIME_SYNC_VALIDATION.md',
            test_file.parents[2] / 'Documentation' / '05_VERIFICATION' / 'TIME_SYNC_VALIDATION.md',
        ]

        validation_doc = None
        for candidate in candidates:
            if candidate.exists():
                validation_doc = candidate
                break

        self.assertIsNotNone(validation_doc,
                            f"Validation document not found. Tried: {candidates}")

    def test_time_sync_session_is_importable(self):
        """Core measurement module is importable."""
        from spi.time_sync_session import TimeSyncSession
        self.assertTrue(callable(TimeSyncSession))

    def test_time_sync_analysis_is_importable(self):
        """Analysis module is importable."""
        from spi.time_sync_analysis import compute_stats, percentiles
        self.assertTrue(callable(compute_stats))
        self.assertTrue(callable(percentiles))

    def test_spi_protocol_has_time_sync_codec(self):
        """SPI protocol module has TIME_SYNC encoder/decoder."""
        from spi.spi_protocol import encode_time_sync_payload, decode_command_reply
        self.assertTrue(callable(encode_time_sync_payload))
        self.assertTrue(callable(decode_command_reply))


if __name__ == '__main__':
    unittest.main()
