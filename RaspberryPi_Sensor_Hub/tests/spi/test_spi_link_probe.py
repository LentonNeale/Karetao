import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from spi.spi_protocol import MessageType, SpiFrame  # noqa: E402

_spec = importlib.util.spec_from_file_location('spi_link_probe', ROOT / 'tools' / 'spi_link_probe.py')
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


def version_frame(flags: int, payload: bytes | None = None) -> bytes:
    if payload is None:
        payload = struct.pack('<BBBBBBHIII', 1, 1, 2, 3, 4, flags, 0, 7, 0x00ABCDEF, 1_700_000_000)
    return SpiFrame(message_type=MessageType.VERSION, seq=7, payload=payload).encode()


class VersionLinesTests(unittest.TestCase):
    def test_clean_build(self):
        lines = probe.version_lines(version_frame(0x00))
        self.assertEqual(len(lines), 1)
        self.assertIn('firmware_version=2.3.4', lines[0])
        self.assertIn('git_hash_abbrev=00abcdef', lines[0])
        self.assertIn('build_flags=0x00', lines[0])
        self.assertIn('dirty=no', lines[0])
        self.assertIn('protocol_version=1', lines[0])
        self.assertIn('commit_epoch_secs=1700000000', lines[0])

    def test_dirty_build(self):
        lines = probe.version_lines(version_frame(0x01))
        self.assertEqual(len(lines), 1)
        self.assertIn('build_flags=0x01', lines[0])
        self.assertIn('dirty=yes', lines[0])

    def test_non_version_frame_gives_no_lines(self):
        raw = SpiFrame(message_type=MessageType.DIAGNOSTIC, seq=1).encode()
        self.assertEqual(probe.version_lines(raw), [])

    def test_wrong_size_payload_is_undecodable(self):
        lines = probe.version_lines(version_frame(0, payload=b'\x01' * 5))
        self.assertEqual(len(lines), 1)
        self.assertIn('undecodable', lines[0])


if __name__ == '__main__':
    unittest.main()
