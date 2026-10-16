"""The time-sync probe (tools/spi_time_sync_probe.py) run end to end against the fake."""

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

_spec = importlib.util.spec_from_file_location('spi_time_sync_probe', ROOT / 'tools' / 'spi_time_sync_probe.py')
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


class FakeRunTests(unittest.TestCase):
    def test_every_time_sync_is_correlated_and_accepted(self) -> None:
        # The reply to a TIME_SYNC arrives on a later transaction; matched by request_seq, every
        # request's ACK is counted rather than dropped as a sequence mismatch.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = probe.main(['--fake', '--transactions', '4', '--interval-ms', '0'])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn('Total attempts:      4', text)
        self.assertIn('Accepted:            4', text)


if __name__ == '__main__':
    unittest.main()
