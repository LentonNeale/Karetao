import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.spi_protocol import (
    VERSION_PAYLOAD_BYTES,
    MessageType,
    SpiFrame,
    VersionInfo,
    crc32_iso_hdlc,
)


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


if __name__ == '__main__':
    unittest.main()
