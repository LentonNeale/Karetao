import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.spi_protocol import (
    COMMAND_REPLY_PAYLOAD_BYTES,
    TIME_SYNC_PAYLOAD_BYTES,
    VERSION_PAYLOAD_BYTES,
    MessageType,
    SpiFrame,
    VersionInfo,
    crc32_iso_hdlc,
    decode_command_reply,
    encode_time_sync_payload,
    extract_time_sync_from_ack_nack,
    SENSOR_RECORD_BYTES,
    SENSOR_VALIDITY_COMMUNICATION_ERROR,
    SENSOR_VALIDITY_MAGNET_NOT_DETECTED,
    SENSOR_VALIDITY_MAGNET_TOO_STRONG,
    SENSOR_VALIDITY_MAGNET_TOO_WEAK,
    SENSOR_VALIDITY_NOT_FITTED,
    SENSOR_VALIDITY_SAMPLE_VALID,
    SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED,
    SNAPSHOT_PREFIX_BYTES,
    SensorRecord,
    decode_snapshot_sensor_records,
)


def _sensor_record(sensor_id: int, flags: int, timestamp_us: int = 0, raw_angle: int = 0,
                   processed_mdeg: int = 0, magnitude: int = 0, agc: int = 0) -> bytes:
    return struct.pack('<BBHQHiHBBH', sensor_id, 0, flags, timestamp_us, raw_angle,
                       processed_mdeg, magnitude, agc, 0, 0)


class SpiProtocolTests(unittest.TestCase):
    def test_crc32_reference_vectors_match_contract(self) -> None:
        self.assertEqual(crc32_iso_hdlc(b''), 0x00000000)
        self.assertEqual(crc32_iso_hdlc(b'123456789'), 0xCBF43926)
        self.assertEqual(
            crc32_iso_hdlc(bytes.fromhex('5A A5 01 01 03 00 34 12 00 00 88 77 66 55 44 33 22 11 AA BB CC')),
            0x049705F5,
        )

    def test_frame_round_trip(self) -> None:
        frame = SpiFrame(
            message_type=MessageType.TIME_SYNC,
            seq=7,
            frame_time_us=123456,
            payload=b'\x01\x00\x02\x00abcdefgh\x03\x00\x00\x00',
        )
        encoded = frame.encode()
        decoded = SpiFrame.decode(encoded)
        self.assertEqual(decoded, frame)

    def test_fixed_512_byte_transport_padding_is_accepted(self) -> None:
        frame = SpiFrame(message_type=MessageType.GET_STATUS, seq=1)
        encoded = frame.encode()
        decoded = SpiFrame.decode(encoded.ljust(512, b'\x00'))
        self.assertEqual(decoded, frame)

    def test_nonzero_transport_padding_is_rejected(self) -> None:
        frame = SpiFrame(message_type=MessageType.GET_STATUS, seq=1)
        encoded = frame.encode()
        padded = bytearray(encoded.ljust(512, b'\x00'))
        padded[-1] = 0x01
        with self.assertRaises(ValueError):
            SpiFrame.decode(padded)

    def test_unsupported_protocol_version_is_rejected(self) -> None:
        frame = SpiFrame(message_type=MessageType.GET_STATUS, seq=1, protocol_version=2).encode()
        with self.assertRaises(ValueError):
            SpiFrame.decode(frame)

    def test_oversized_payload_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SpiFrame(message_type=MessageType.DIAGNOSTIC, seq=1, payload=b'x' * 491).encode()


class VersionPayloadTests(unittest.TestCase):
    @staticmethod
    def payload(schema_version: int = 1, reserved: int = 0) -> bytes:
        return struct.pack('<BBBBBBHIII', schema_version, 1, 0, 1, 0, 0, reserved,
                           7, 0x1A2B3C4D, 1_700_000_000)

    def test_version_payload_matches_contract_size(self) -> None:
        self.assertEqual(len(self.payload()), VERSION_PAYLOAD_BYTES)

    def test_version_payload_decodes(self) -> None:
        info = VersionInfo.decode(self.payload())
        self.assertEqual(info.protocol_version, 1)
        self.assertEqual(info.firmware_version, '0.1.0')
        self.assertEqual(info.git_hash, '1a2b3c4d')
        self.assertEqual(info.commit_epoch_secs, 1_700_000_000)
        self.assertFalse(info.is_dirty_build)

    def test_unsupported_schema_version_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            VersionInfo.decode(self.payload(schema_version=2))

    def test_nonzero_reserved_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            VersionInfo.decode(self.payload(reserved=1))

    def test_wrong_payload_size_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            VersionInfo.decode(self.payload()[:-1])


class TimeSyncPayloadEncoderTests(unittest.TestCase):
    def test_encode_time_sync_payload_valid_inputs(self) -> None:
        payload = encode_time_sync_payload(pi_time_us=1000, sync_seq=1, flags=0)
        self.assertEqual(len(payload), TIME_SYNC_PAYLOAD_BYTES)
        # Verify bytes at key offsets per SPI_PAYLOAD_SCHEMA.md
        self.assertEqual(payload[0], 1)  # schema_version
        self.assertEqual(payload[1], 0)  # reserved
        # flags at offset 2-3 (little-endian uint16)
        flags_value = struct.unpack('<H', payload[2:4])[0]
        self.assertEqual(flags_value, 0)
        # pi_time_us at offset 4-11 (little-endian uint64)
        pi_time_value = struct.unpack('<Q', payload[4:12])[0]
        self.assertEqual(pi_time_value, 1000)
        # sync_seq at offset 12-15 (little-endian uint32)
        sync_seq_value = struct.unpack('<I', payload[12:16])[0]
        self.assertEqual(sync_seq_value, 1)

    def test_encode_time_sync_payload_max_values(self) -> None:
        payload = encode_time_sync_payload(
            pi_time_us=0xFFFFFFFFFFFFFFFF,
            sync_seq=0xFFFFFFFF,
            flags=0xFFFF
        )
        self.assertEqual(len(payload), TIME_SYNC_PAYLOAD_BYTES)
        pi_time_value = struct.unpack('<Q', payload[4:12])[0]
        self.assertEqual(pi_time_value, 0xFFFFFFFFFFFFFFFF)
        sync_seq_value = struct.unpack('<I', payload[12:16])[0]
        self.assertEqual(sync_seq_value, 0xFFFFFFFF)
        flags_value = struct.unpack('<H', payload[2:4])[0]
        self.assertEqual(flags_value, 0xFFFF)

    def test_encode_time_sync_payload_rejects_pi_time_us_overflow(self) -> None:
        with self.assertRaises(ValueError):
            encode_time_sync_payload(pi_time_us=0x10000000000000000, sync_seq=1)

    def test_encode_time_sync_payload_rejects_sync_seq_overflow(self) -> None:
        with self.assertRaises(ValueError):
            encode_time_sync_payload(pi_time_us=1000, sync_seq=0x100000000)

    def test_encode_time_sync_payload_rejects_flags_overflow(self) -> None:
        with self.assertRaises(ValueError):
            encode_time_sync_payload(pi_time_us=1000, sync_seq=1, flags=0x10000)

    def test_encode_time_sync_payload_with_nonzero_flags(self) -> None:
        payload = encode_time_sync_payload(pi_time_us=500, sync_seq=42, flags=0x1234)
        flags_value = struct.unpack('<H', payload[2:4])[0]
        self.assertEqual(flags_value, 0x1234)


class CommandReplyDecoderTests(unittest.TestCase):
    def test_decode_command_reply_valid_ack(self) -> None:
        # Build 12-byte payload: schema=1, type=0x80, status=0, seq=42, detail=0
        payload = struct.pack('<BBHII', 1, 0x80, 0, 42, 0)
        req_type, status, req_seq, detail = decode_command_reply(payload)
        self.assertEqual(req_type, 0x80)
        self.assertEqual(status, 0)
        self.assertEqual(req_seq, 42)
        self.assertEqual(detail, 0)

    def test_decode_command_reply_valid_nack(self) -> None:
        # Build NACK with type=0x81, status=7, seq=100, detail=0x12345678
        payload = struct.pack('<BBHII', 1, 0x81, 7, 100, 0x12345678)
        req_type, status, req_seq, detail = decode_command_reply(payload)
        self.assertEqual(req_type, 0x81)
        self.assertEqual(status, 7)
        self.assertEqual(req_seq, 100)
        self.assertEqual(detail, 0x12345678)

    def test_decode_command_reply_rejects_short_payload(self) -> None:
        payload = b'\x01\x80\x00\x00\x2a\x00\x00\x00\x00\x00'  # 10 bytes
        with self.assertRaises(ValueError):
            decode_command_reply(payload)

    def test_decode_command_reply_rejects_wrong_schema(self) -> None:
        payload = struct.pack('<BBHII', 2, 0x80, 0, 42, 0)  # schema=2
        with self.assertRaises(ValueError):
            decode_command_reply(payload)

    def test_decode_command_reply_accepts_extra_bytes(self) -> None:
        # 12-byte payload plus extra bytes (should be accepted)
        payload = struct.pack('<BBHII', 1, 0x80, 0, 42, 0) + b'\x00\x00\x00\x00'
        req_type, status, req_seq, detail = decode_command_reply(payload)
        self.assertEqual(req_type, 0x80)
        self.assertEqual(status, 0)
        self.assertEqual(req_seq, 42)
        self.assertEqual(detail, 0)


class TimeSyncFrameExtensionTests(unittest.TestCase):
    """Tests for TIME_SYNC field extraction from ACK/NACK frames."""

    def test_extract_time_sync_from_valid_ack_response(self) -> None:
        # Build ACK response with TIME_SYNC payload echo
        # Command reply header (12 bytes) + TIME_SYNC payload echo (16 bytes)
        cmd_reply = struct.pack('<BBHII', 1, 0x80, 0, 42, 0)
        time_sync_echo = encode_time_sync_payload(pi_time_us=5000000, sync_seq=7, flags=0)
        payload = cmd_reply + time_sync_echo

        result = extract_time_sync_from_ack_nack(payload)
        self.assertIsNotNone(result)
        pi_time_us, sync_seq = result
        self.assertEqual(pi_time_us, 5000000)
        self.assertEqual(sync_seq, 7)

    def test_extract_time_sync_from_nack_response(self) -> None:
        # Build NACK response with TIME_SYNC payload echo
        cmd_reply = struct.pack('<BBHII', 1, 0x81, 7, 42, 0)
        time_sync_echo = encode_time_sync_payload(pi_time_us=3000000, sync_seq=99, flags=0)
        payload = cmd_reply + time_sync_echo

        result = extract_time_sync_from_ack_nack(payload)
        self.assertIsNotNone(result)
        pi_time_us, sync_seq = result
        self.assertEqual(pi_time_us, 3000000)
        self.assertEqual(sync_seq, 99)

    def test_extract_time_sync_returns_none_for_short_payload(self) -> None:
        # Command reply without full TIME_SYNC echo
        payload = struct.pack('<BBHII', 1, 0x80, 0, 42, 0)
        result = extract_time_sync_from_ack_nack(payload)
        self.assertIsNone(result)

    def test_extract_time_sync_returns_none_for_min_length_payload(self) -> None:
        # Exactly at COMMAND_REPLY_PAYLOAD_BYTES (12 bytes)
        payload = struct.pack('<BBHII', 1, 0x80, 0, 42, 0)
        self.assertEqual(len(payload), COMMAND_REPLY_PAYLOAD_BYTES)
        result = extract_time_sync_from_ack_nack(payload)
        self.assertIsNone(result)

    def test_extract_time_sync_max_values(self) -> None:
        # Test with maximum uint64 and uint32 values
        cmd_reply = struct.pack('<BBHII', 1, 0x80, 0, 42, 0)
        time_sync_echo = encode_time_sync_payload(
            pi_time_us=0xFFFFFFFFFFFFFFFF, sync_seq=0xFFFFFFFF, flags=0
        )
        payload = cmd_reply + time_sync_echo

        result = extract_time_sync_from_ack_nack(payload)
        self.assertIsNotNone(result)
        pi_time_us, sync_seq = result
        self.assertEqual(pi_time_us, 0xFFFFFFFFFFFFFFFF)
        self.assertEqual(sync_seq, 0xFFFFFFFF)

    def test_extract_time_sync_with_extra_trailing_bytes(self) -> None:
        # Response with extra bytes after TIME_SYNC echo
        cmd_reply = struct.pack('<BBHII', 1, 0x80, 0, 42, 0)
        time_sync_echo = encode_time_sync_payload(pi_time_us=1234567, sync_seq=50, flags=0)
        payload = cmd_reply + time_sync_echo + b'\x00\x00\x00\x00'

        result = extract_time_sync_from_ack_nack(payload)
        self.assertIsNotNone(result)
        pi_time_us, sync_seq = result
        self.assertEqual(pi_time_us, 1234567)
        self.assertEqual(sync_seq, 50)

    def test_sensor_validity_constants(self) -> None:
        self.assertEqual(SENSOR_VALIDITY_SAMPLE_VALID, 0x0001)
        self.assertEqual(SENSOR_VALIDITY_COMMUNICATION_ERROR, 0x0002)
        self.assertEqual(SENSOR_VALIDITY_MAGNET_NOT_DETECTED, 0x0004)
        self.assertEqual(SENSOR_VALIDITY_MAGNET_TOO_WEAK, 0x0008)
        self.assertEqual(SENSOR_VALIDITY_MAGNET_TOO_STRONG, 0x0010)
        self.assertEqual(SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED, 0x0020)
        self.assertEqual(SENSOR_VALIDITY_NOT_FITTED, 0x0040)
        self.assertEqual(struct.calcsize('<BBHQHiHBBH'), SENSOR_RECORD_BYTES)

    def test_sensor_record_not_fitted_decode(self) -> None:
        record = SensorRecord.decode(_sensor_record(3, SENSOR_VALIDITY_NOT_FITTED))
        self.assertTrue(record.is_not_fitted)
        self.assertFalse(record.is_valid)
        self.assertEqual(record.sensor_id, 3)
        self.assertEqual(record.raw_angle, 0)
        self.assertEqual(record.processed_angle_mdeg, 0)

    def test_sensor_record_valid_round_trip(self) -> None:
        flags = SENSOR_VALIDITY_SAMPLE_VALID | SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED
        record = SensorRecord.decode(_sensor_record(1, flags, 123456789, 2048, -45000, 1500, 90))
        self.assertTrue(record.is_valid)
        self.assertFalse(record.is_not_fitted)
        self.assertEqual(record.validity_flags, flags)
        self.assertEqual(record.measurement_timestamp_us, 123456789)
        self.assertEqual(record.raw_angle, 2048)
        self.assertEqual(record.processed_angle_mdeg, -45000)
        self.assertEqual(record.magnitude, 1500)
        self.assertEqual(record.agc, 90)

    def test_sensor_record_reject_short_payload(self) -> None:
        with self.assertRaises(ValueError):
            SensorRecord.decode(b'\x00' * (SENSOR_RECORD_BYTES - 1))

    def test_sensor_record_reject_nonzero_reserved(self) -> None:
        raw = bytearray(_sensor_record(0, 0))
        raw[21] = 1
        with self.assertRaises(ValueError):
            SensorRecord.decode(bytes(raw))

    def test_decode_snapshot_sensor_records(self) -> None:
        prefix = struct.pack('<BBB', 1, 2, 0) + b'\x00' * (SNAPSHOT_PREFIX_BYTES - 3)
        payload = (prefix + _sensor_record(0, SENSOR_VALIDITY_SAMPLE_VALID)
                   + _sensor_record(1, SENSOR_VALIDITY_NOT_FITTED))
        records = decode_snapshot_sensor_records(payload)
        self.assertEqual([r.sensor_id for r in records], [0, 1])
        self.assertTrue(records[0].is_valid)
        self.assertTrue(records[1].is_not_fitted)
        with self.assertRaises(ValueError):
            decode_snapshot_sensor_records(payload[:-1])


if __name__ == '__main__':
    unittest.main()
