from datetime import date
import importlib.util
import io
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from spi.run_record import FirmwareIdentity, PiIdentity, RunMeta, read_run, write_run  # noqa: E402
from spi.spi_bus import SpiBus, SpiBusConfig  # noqa: E402
from spi.spi_device import SpiDevice  # noqa: E402
from spi.spi_protocol import MessageType, SpiFrame  # noqa: E402

_spec = importlib.util.spec_from_file_location('evidence_record', ROOT / 'tools' / 'evidence_record.py')
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

PI_COMMIT = '0123456789abcdef0123456789abcdef01234567'


class VersionBackend:
    """Fake SPI backend that answers every transfer with one VERSION frame."""

    def __init__(self, build_flags: int, response_to_seq: int) -> None:
        payload = struct.pack('<BBBBBBHIII', 1, 1, 0, 1, 0, build_flags, 0,
                              response_to_seq, 0x1A2B3C4D, 1_700_000_000)
        self._response = SpiFrame(message_type=MessageType.VERSION, seq=3, payload=payload).encode()

    def open(self, config: SpiBusConfig) -> None:
        pass

    def transfer(self, tx_data: bytes) -> bytes:
        return self._response

    def close(self) -> None:
        pass


def firmware_from_fake_backend(build_flags: int = 0) -> FirmwareIdentity:
    """The identity a capture tool would record: GET_VERSION through the fake backend."""
    bus = SpiBus(SpiBusConfig(), backend=VersionBackend(build_flags, response_to_seq=100))
    bus.open()
    try:
        info = SpiDevice(bus, start_sequence=100).get_version()
    finally:
        bus.close()
    return FirmwareIdentity.from_version_info(info)


def make_run(root: Path, directory: str = '2026-10-20-spi-link-phase5', build_flags: int = 0,
             pi: PiIdentity | None = None, informs=None, rows=2, **overrides) -> Path:
    fields = dict(
        kind='spi-link', rig='bench A, STM32F405 board 1, axes 0-2, 300 mm cable',
        informs=['SYS-SPI-001', 'LIVE-17', 'PRM-SPI-01'] if informs is None else informs,
        started='2026-10-20T10:15:00+13:00',
        tool_command=['python3', 'tools/spi_link_probe.py', '--data-ready', '--output', 'runs/x y'],
        firmware=firmware_from_fake_backend(build_flags),
        pi=PiIdentity(commit=PI_COMMIT, dirty=False) if pi is None else pi,
        name='phase5',
    )
    fields.update(overrides)
    run_dir = root / 'BenchWork' / 'runs' / directory
    write_run(run_dir, RunMeta(**fields), {
        'transactions': (['index', 'kind', 'ok'], [[i, 'GET_STATUS', 1] for i in range(rows)]),
    })
    return run_dir


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.evidence_dir = self.tmp / 'Documentation' / '05_VERIFICATION' / 'evidence'

    def draft(self, run_dir: Path) -> str:
        return tool.draft_record(read_run(run_dir), self.evidence_dir, today=date(2026, 10, 21))

    def test_clean_run_fills_every_required_field(self):
        text = self.draft(make_run(self.tmp))
        for label in ('| Date |', '| Requirement IDs |', '| Firmware identity |', '| Hardware or rig |',
                      '| Procedure |', '| Result |', '| Attachments |', '| Accepted by and date |'):
            self.assertIn(label, text)
        self.assertIn('| Date | 2026-10-20 |', text)
        self.assertIn('| Requirement IDs | `SYS-SPI-001` |', text)
        self.assertIn('`git_hash_abbrev` `1a2b3c4d`', text)
        self.assertIn('`build_flags` bit 0 clear (clean build)', text)
        self.assertIn(f'Pi commit `{PI_COMMIT}`, working tree clean under `RaspberryPi_Sensor_Hub/`, `shared/`', text)
        self.assertIn('| Hardware or rig | bench A, STM32F405 board 1, axes 0-2, 300 mm cable |', text)
        self.assertIn("`python3 tools/spi_link_probe.py --data-ready --output 'runs/x y'`", text)
        self.assertIn('Eligible:', text)
        self.assertIn('matrix rows named under Requirement IDs', text)
        self.assertNotIn('Not eligible', text)

    def test_human_fields_are_left_open(self):
        text = self.draft(make_run(self.tmp))
        self.assertIn('| Result | **(human)** Pass or fail with the numbers observed, and the `PRM-*` IDs '
                      'they inform: `PRM-SPI-01`; the run also informs `LIVE-17` |', text)
        self.assertIn('| Accepted by and date | **(human)** Lenton Neale, YYYY-MM-DD |', text)

    def test_live_ids_are_not_requirement_ids(self):
        text = self.draft(make_run(self.tmp, informs=['LIVE-17']))
        self.assertIn('| Requirement IDs | none: not offered against a matrix row |', text)
        self.assertIn('the run also informs `LIVE-17`', text)
        self.assertIn('Eligible:', text)
        self.assertIn('is not offered against a matrix row', text)
        self.assertNotIn('matrix rows named under Requirement IDs', text)

    def test_attachments_are_relative_to_the_evidence_dir(self):
        text = self.draft(make_run(self.tmp, rows=3))
        self.assertIn('`../../../BenchWork/runs/2026-10-20-spi-link-phase5/transactions.csv` (series `transactions`, 3 rows)', text)
        self.assertIn('`../../../BenchWork/runs/2026-10-20-spi-link-phase5/meta.json` (run metadata)', text)

    def test_shell_metacharacters_are_quoted_in_procedure(self):
        text = self.draft(make_run(self.tmp, tool_command=['probe', '--output', 'runs/*', '--note', 'a;b']))
        self.assertIn("`probe --output 'runs/*' --note 'a;b'`", text)

    def test_table_cells_are_escaped(self):
        text = self.draft(make_run(self.tmp, rig='bench A | board 1', notes='line one\nline two'))
        self.assertIn('| Hardware or rig | bench A \\| board 1 |', text)
        self.assertIn('notes: line one line two', text)
        table = [line for line in text.splitlines() if line.startswith('| ')]
        self.assertEqual(len(table), 9)  # header + eight required fields
        for line in table:
            self.assertEqual(line.count('|') - line.count('\\|'), 3, line)

    def test_dirty_firmware_is_not_eligible(self):
        text = self.draft(make_run(self.tmp, build_flags=0x01))
        self.assertIn('`build_flags` bit 0 set (dirty build)', text)
        self.assertIn('**Not eligible: this record cannot satisfy a matrix row**', text)
        self.assertIn('EVIDENCE_RECORD_FORMAT.md "Rules"', text)
        self.assertNotIn('Eligible:', text)

    def test_dirty_pi_tree_is_not_eligible(self):
        text = self.draft(make_run(self.tmp, pi=PiIdentity(commit=PI_COMMIT, dirty=True)))
        self.assertIn('working tree dirty under', text)
        self.assertIn('**Not eligible: this record cannot satisfy a matrix row**', text)
        self.assertIn('ruling R28(b)', text)

    def test_unknown_pi_identity_is_not_eligible(self):
        text = self.draft(make_run(self.tmp, pi=PiIdentity(commit='', dirty=True, error='git unavailable')))
        self.assertIn('Pi commit unknown (git unavailable)', text)
        self.assertIn('Not eligible', text)

    def test_eligibility_follows_the_module_predicate(self):
        for run_dir in (make_run(self.tmp, 'a'), make_run(self.tmp, 'b', build_flags=0x01),
                        make_run(self.tmp, 'c', pi=PiIdentity(commit=PI_COMMIT, dirty=True))):
            run = read_run(run_dir)
            eligible, reasons = tool.eligibility(run)
            self.assertEqual(eligible, run.meta.reproducible)
            self.assertEqual(bool(reasons), not eligible)

    def test_both_dirty_lists_both_reasons(self):
        run = read_run(make_run(self.tmp, build_flags=0x01, pi=PiIdentity(commit=PI_COMMIT, dirty=True)))
        eligible, reasons = tool.eligibility(run)
        self.assertFalse(eligible)
        self.assertEqual(len(reasons), 2)

    def test_record_name_comes_from_meta_not_the_directory(self):
        run = read_run(make_run(self.tmp, directory='2026-10-21-probe'))
        self.assertEqual(tool.record_path(run, self.evidence_dir),
                         self.evidence_dir / '2026-10-20-spi-link-phase5.md')
        text = self.draft(run.directory)
        self.assertIn('# Evidence record: 2026-10-20 spi-link-phase5', text)

    def test_date_is_the_local_run_day(self):
        run = read_run(make_run(self.tmp, started='2026-10-21T10:30:00+13:00'))
        self.assertEqual(tool.record_path(run, self.evidence_dir),
                         self.evidence_dir / '2026-10-21-spi-link-phase5.md')


class MainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.evidence_dir = self.tmp / 'evidence'

    def run_main(self, *argv) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch('sys.stdout', out), mock.patch('sys.stderr', err):
            code = tool.main([str(a) for a in argv])
        return code, out.getvalue(), err.getvalue()

    def test_prints_draft_by_default(self):
        run_dir = make_run(self.tmp)
        code, out, err = self.run_main(run_dir, '--evidence-dir', self.evidence_dir)
        self.assertEqual(code, tool.EXIT_OK)
        self.assertIn('# Evidence record: 2026-10-20 spi-link-phase5', out)
        self.assertEqual(err, '')
        self.assertFalse(self.evidence_dir.exists())

    def test_file_writes_the_record_once(self):
        run_dir = make_run(self.tmp)
        code, out, _ = self.run_main(run_dir, '--evidence-dir', self.evidence_dir, '--file')
        self.assertEqual(code, tool.EXIT_OK)
        record = self.evidence_dir / '2026-10-20-spi-link-phase5.md'
        self.assertTrue(record.is_file())
        self.assertIn('drafted', out)
        first = record.read_text()
        self.assertIn('../BenchWork/runs/2026-10-20-spi-link-phase5/transactions.csv', first)

        code, _, err = self.run_main(run_dir, '--evidence-dir', self.evidence_dir, '--file')
        self.assertEqual(code, tool.EXIT_ERROR)
        self.assertIn('never edited after acceptance', err)
        self.assertEqual(record.read_text(), first)

    def test_output_path(self):
        run_dir = make_run(self.tmp)
        target = self.tmp / 'elsewhere' / 'rec.md'
        code, _, _ = self.run_main(run_dir, '--output', target)
        self.assertEqual(code, tool.EXIT_OK)
        self.assertIn('`../BenchWork/runs/2026-10-20-spi-link-phase5/meta.json`', target.read_text())

    def test_require_clean_refuses_a_dirty_run(self):
        run_dir = make_run(self.tmp, build_flags=0x01)
        code, _, err = self.run_main(run_dir, '--evidence-dir', self.evidence_dir, '--file', '--require-clean')
        self.assertEqual(code, tool.EXIT_NOT_CLEAN)
        self.assertIn('cannot satisfy a matrix row', err)
        self.assertFalse(self.evidence_dir.exists())

    def test_dirty_run_is_still_drafted_without_require_clean(self):
        run_dir = make_run(self.tmp, pi=PiIdentity(commit=PI_COMMIT, dirty=True))
        code, out, _ = self.run_main(run_dir, '--evidence-dir', self.evidence_dir, '--file')
        self.assertEqual(code, tool.EXIT_OK)
        self.assertIn('cannot satisfy a matrix row', out)
        self.assertIn('Not eligible', (self.evidence_dir / '2026-10-20-spi-link-phase5.md').read_text())

    def test_missing_field_is_reported(self):
        run_dir = make_run(self.tmp)
        meta = run_dir / 'meta.json'
        meta.write_text(meta.read_text().replace('"rig"', '"rigg"'))
        code, _, err = self.run_main(run_dir)
        self.assertEqual(code, tool.EXIT_ERROR)
        self.assertIn("'rig'", err)

    def test_malformed_value_is_reported_not_raised(self):
        run_dir = make_run(self.tmp)
        meta = run_dir / 'meta.json'
        meta.write_text(meta.read_text().replace('"commit_epoch_secs": 1700000000', '"commit_epoch_secs": "soon"'))
        code, _, err = self.run_main(run_dir)
        self.assertEqual(code, tool.EXIT_ERROR)
        self.assertIn("'commit_epoch_secs'", err)


if __name__ == '__main__':
    unittest.main()
