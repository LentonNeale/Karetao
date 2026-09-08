import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.spi_protocol import MessageType, SpiFrame, crc32_iso_hdlc


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

    def test_oversized_payload_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SpiFrame(message_type=MessageType.DIAGNOSTIC, seq=1, payload=b'x' * 491).encode()


if __name__ == '__main__':
    unittest.main()
