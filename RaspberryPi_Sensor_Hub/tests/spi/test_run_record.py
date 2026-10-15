from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi import run_record  # noqa: E402
from spi.run_record import (  # noqa: E402
    PI_DIRTY_SCOPE, FirmwareIdentity, PiIdentity, RunMeta, RunRecordError,
    pi_identity, read_run, started_now, write_run,
)
from spi.spi_protocol import VersionInfo  # noqa: E402


def version_info(build_flags: int = 0) -> VersionInfo:
    payload = struct.pack('<BBBBBBHIII', 1, 1, 0, 1, 0, build_flags, 0, 7, 0x1A2B3C4D, 1_700_000_000)
    return VersionInfo.decode(payload)


def clean_meta(**overrides) -> RunMeta:
    fields = dict(
        kind='spi-link', rig='bench A, STM32F405 board 1, axes 0-2, cable 300 mm',
        informs=['SYS-SPI-001', 'PRM-SPI-01'],
        started='2026-10-20T10:15:00+13:00',
        tool_command=['python3', 'tools/spi_link_probe.py', '--data-ready', '--output', 'run'],
        firmware=FirmwareIdentity.from_version_info(version_info()),
        pi=PiIdentity(commit='0123456789abcdef0123456789abcdef01234567', dirty=False),
        name='phase5',
    )
    fields.update(overrides)
    return RunMeta(**fields)


SERIES = {'transactions': (['index', 'kind', 'ok'], [[0, 'GET_VERSION', 1], [1, 'GET_STATUS', 1]])}


class FakeGit:
    """Scripted git results: (returncode, stdout, stderr) per subcommand."""

    def __init__(self, rev_parse=(0, 'abc123\n', ''), status=(0, '', '')) -> None:
        self.rev_parse = rev_parse
        self.status = status
        self.calls: list[list[str]] = []

    def __call__(self, args, cwd):
        self.calls.append(list(args))
        return self.rev_parse if args[1] == 'rev-parse' else self.status


class RunRoundTripTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_valid_run_round_trips(self):
        run_dir = self.tmp / '2026-10-20-spi-link-phase5'
        meta_path = write_run(run_dir, clean_meta(), SERIES)
        self.assertEqual(meta_path, run_dir / 'meta.json')

        run = read_run(run_dir)
        self.assertEqual(run.meta.kind, 'spi-link')
        self.assertEqual(run.meta.name, 'phase5')
        self.assertEqual(run.meta.short_name, 'spi-link-phase5')
        self.assertEqual(run.meta.date, '2026-10-20')
        self.assertEqual(run.meta.informs, ['SYS-SPI-001', 'PRM-SPI-01'])
        self.assertEqual(run.meta.firmware.git_hash, '1a2b3c4d')
        self.assertFalse(run.meta.firmware.dirty)
        self.assertEqual(run.meta.pi.commit, '0123456789abcdef0123456789abcdef01234567')
        self.assertEqual(run.meta.pi.scope, PI_DIRTY_SCOPE)
        self.assertTrue(run.meta.reproducible)

        self.assertEqual([s.name for s in run.meta.series], ['transactions'])
        self.assertEqual(run.meta.series[0].rows, 2)
        columns, rows = run.read_series('transactions')
        self.assertEqual(columns, ['index', 'kind', 'ok'])
        self.assertEqual(rows, [['0', 'GET_VERSION', '1'], ['1', 'GET_STATUS', '1']])
        self.assertEqual(run.attachments(), [run_dir / 'meta.json', run_dir / 'transactions.csv'])

    def test_meta_json_is_plain_and_versioned(self):
        run_dir = self.tmp / 'run'
        write_run(run_dir, clean_meta(), SERIES)
        data = json.loads((run_dir / 'meta.json').read_text())
        self.assertEqual(data['schema_version'], run_record.RUN_RECORD_SCHEMA_VERSION)
        for name in run_record.REQUIRED_META_FIELDS:
            self.assertIn(name, data)
        self.assertEqual(data['series'][0]['file'], 'transactions.csv')

    def test_short_name_without_name(self):
        self.assertEqual(clean_meta(name='').short_name, 'spi-link')

    def test_date_is_the_local_day_of_the_offset_carried(self):
        # 21:30 UTC on the 20th is 10:30 on the 21st in New Zealand daylight time.
        self.assertEqual(clean_meta(started='2026-10-21T10:30:00+13:00').date, '2026-10-21')
        self.assertEqual(clean_meta(started='2026-10-20T21:30:00+00:00').date, '2026-10-20')

    def test_started_now_carries_an_offset(self):
        parsed = datetime.fromisoformat(started_now())
        self.assertIsNotNone(parsed.tzinfo)

    def test_run_is_written_once(self):
        run_dir = self.tmp / 'run'
        write_run(run_dir, clean_meta(), SERIES)
        with self.assertRaises(RunRecordError):
            write_run(run_dir, clean_meta(), SERIES)

    def test_invalid_meta_writes_nothing(self):
        run_dir = self.tmp / 'run'
        with self.assertRaises(RunRecordError):
            write_run(run_dir, clean_meta(tool_command=[]), SERIES)
        self.assertFalse(run_dir.exists())

    def test_failed_series_write_removes_the_files(self):
        run_dir = self.tmp / 'run'
        with self.assertRaises(RunRecordError):
            write_run(run_dir, clean_meta(), {'good': (['a'], [[1]]), 'bad': (['a', 'b'], [[1]])})
        self.assertEqual(sorted(p.name for p in run_dir.iterdir()), [])

    def test_series_name_must_be_a_file_stem(self):
        with self.assertRaises(RunRecordError):
            write_run(self.tmp / 'run', clean_meta(), {'../x': (['a'], [[1]])})

    def test_unknown_series_is_an_error(self):
        write_run(self.tmp / 'run', clean_meta(), SERIES)
        with self.assertRaises(RunRecordError):
            read_run(self.tmp / 'run').series_path('nope')


class MetaValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.run_dir = self.tmp / 'run'
        write_run(self.run_dir, clean_meta(), SERIES)
        self.meta_path = self.run_dir / 'meta.json'

    def _rewrite(self, mutate):
        data = json.loads(self.meta_path.read_text())
        mutate(data)
        self.meta_path.write_text(json.dumps(data))

    def _assert_rejected(self, fragment: str):
        with self.assertRaises(RunRecordError) as ctx:
            read_run(self.run_dir)
        self.assertIn(fragment, str(ctx.exception))

    def test_missing_mandatory_field_is_named(self):
        for name in run_record.REQUIRED_META_FIELDS:
            with self.subTest(field=name):
                write_run(self.tmp / name, clean_meta(), SERIES)
                path = self.tmp / name / 'meta.json'
                data = json.loads(path.read_text())
                del data[name]
                path.write_text(json.dumps(data))
                with self.assertRaises(RunRecordError) as ctx:
                    read_run(self.tmp / name)
                self.assertIn(repr(name), str(ctx.exception))

    def test_missing_identity_subfield_is_named(self):
        self._rewrite(lambda d: d['pi'].pop('dirty'))
        self._assert_rejected("'dirty'")

    def test_malformed_values_are_named_not_raised_raw(self):
        cases = [
            ('commit_epoch_secs', lambda d: d['firmware'].__setitem__('commit_epoch_secs', 'soon')),
            ('dirty', lambda d: d['firmware'].__setitem__('dirty', 'no')),
            ('rows', lambda d: d['series'][0].__setitem__('rows', 'n/a')),
            ('scope', lambda d: d['pi'].__setitem__('scope', 5)),
            ('tool_metadata', lambda d: d.__setitem__('tool_metadata', [])),
            ('informs', lambda d: d.__setitem__('informs', 'SYS-SPI-001')),
            ('started', lambda d: d.__setitem__('started', '1760000000')),
            ('started', lambda d: d.__setitem__('started', '2026-10-20T10:15:00')),
            ('firmware', lambda d: d.__setitem__('firmware', 'none')),
            ('rig', lambda d: d.__setitem__('rig', '   ')),
        ]
        for index, (name, mutate) in enumerate(cases):
            with self.subTest(field=name, case=index):
                run_dir = self.tmp / f'case-{index}'
                write_run(run_dir, clean_meta(), SERIES)
                path = run_dir / 'meta.json'
                data = json.loads(path.read_text())
                mutate(data)
                path.write_text(json.dumps(data))
                with self.assertRaises(RunRecordError) as ctx:
                    read_run(run_dir)
                self.assertIn(name, str(ctx.exception))

    def test_unsupported_schema_version(self):
        self._rewrite(lambda d: d.__setitem__('schema_version', 99))
        self._assert_rejected('schema_version')

    def test_empty_tool_command_is_rejected(self):
        self._rewrite(lambda d: d.__setitem__('tool_command', []))
        self._assert_rejected("'tool_command'")

    def test_missing_series_file(self):
        (self.run_dir / 'transactions.csv').unlink()
        self._assert_rejected('transactions.csv')

    def test_missing_meta(self):
        with self.assertRaises(RunRecordError):
            read_run(self.tmp / 'absent')

    def test_invalid_json(self):
        self.meta_path.write_text('{not json')
        self._assert_rejected('not valid JSON')


class ReproducibilityTests(unittest.TestCase):
    def test_dirty_firmware_is_not_reproducible(self):
        meta = clean_meta(firmware=FirmwareIdentity.from_version_info(version_info(0x01)))
        self.assertTrue(meta.firmware.dirty)
        self.assertFalse(meta.reproducible)

    def test_dirty_pi_tree_is_not_reproducible(self):
        meta = clean_meta(pi=PiIdentity(commit='abc', dirty=True))
        self.assertFalse(meta.reproducible)

    def test_unknown_identities_are_dirty(self):
        unknown_fw = FirmwareIdentity.unknown('no VERSION reply')
        self.assertTrue(unknown_fw.dirty)
        self.assertEqual(unknown_fw.git_hash, '00000000')
        meta = clean_meta(firmware=unknown_fw)
        self.assertFalse(meta.reproducible)
        self.assertEqual(FirmwareIdentity.from_dict(unknown_fw.to_dict()), unknown_fw)

        unknown_pi = PiIdentity(commit='', dirty=True, error='git unavailable')
        self.assertFalse(unknown_pi.is_known)
        self.assertFalse(clean_meta(pi=unknown_pi).reproducible)
        self.assertEqual(PiIdentity.from_dict(unknown_pi.to_dict()), unknown_pi)


class PiIdentityScriptedTests(unittest.TestCase):
    def test_clean_tree(self):
        git = FakeGit()
        identity = pi_identity(Path('/repo'), runner=git)
        self.assertEqual(identity, PiIdentity(commit='abc123', dirty=False))
        self.assertEqual(git.calls[0], ['git', 'rev-parse', 'HEAD'])
        self.assertEqual(git.calls[1], ['git', 'status', '--porcelain', '--', *PI_DIRTY_SCOPE])

    def test_dirty_tree(self):
        identity = pi_identity(Path('/repo'), runner=FakeGit(status=(0, ' M RaspberryPi_Sensor_Hub/x.py\n', '')))
        self.assertTrue(identity.dirty)
        self.assertEqual(identity.commit, 'abc123')

    def test_git_failure_is_unknown_and_dirty(self):
        identity = pi_identity(Path('/repo'), runner=FakeGit(rev_parse=(128, '', 'fatal: not a git repository')))
        self.assertFalse(identity.is_known)
        self.assertTrue(identity.dirty)
        self.assertIn('not a git repository', identity.error)

    def test_missing_git_is_unknown_and_dirty(self):
        def no_git(args, cwd):
            raise FileNotFoundError('git')
        identity = pi_identity(Path('/repo'), runner=no_git)
        self.assertFalse(identity.is_known)
        self.assertTrue(identity.dirty)


@unittest.skipIf(shutil.which('git') is None, 'git is not installed')
class PiIdentityRealGitTests(unittest.TestCase):
    """The scope rule against a real repository: untracked counts, out-of-scope does not."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', '-c', 'commit.gpgsign=false']
        subprocess.run([*git, 'init', '-q'], cwd=self.repo, check=True, env=env)
        (self.repo / 'RaspberryPi_Sensor_Hub').mkdir()
        (self.repo / 'RaspberryPi_Sensor_Hub' / 'a.py').write_text('x = 1\n')
        (self.repo / 'Documentation').mkdir()
        (self.repo / 'Documentation' / 'd.md').write_text('# d\n')
        (self.repo / '.gitignore').write_text('*.pyc\n')
        subprocess.run([*git, 'add', '-A'], cwd=self.repo, check=True, env=env)
        subprocess.run([*git, 'commit', '-q', '-m', 'init'], cwd=self.repo, check=True, env=env)
        self.head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.repo, check=True,
                                   capture_output=True, text=True, env=env).stdout.strip()

    def test_clean_checkout(self):
        identity = pi_identity(self.repo)
        self.assertEqual(identity.commit, self.head)
        self.assertFalse(identity.dirty)
        self.assertTrue(identity.is_known)

    def test_untracked_file_in_scope_is_dirty(self):
        (self.repo / 'RaspberryPi_Sensor_Hub' / 'run.csv').write_text('a\n')
        self.assertTrue(pi_identity(self.repo).dirty)

    def test_modified_file_in_scope_is_dirty(self):
        (self.repo / 'RaspberryPi_Sensor_Hub' / 'a.py').write_text('x = 2\n')
        self.assertTrue(pi_identity(self.repo).dirty)

    def test_change_outside_scope_is_clean(self):
        (self.repo / 'Documentation' / 'd.md').write_text('# changed\n')
        (self.repo / 'BenchWork').mkdir()
        (self.repo / 'BenchWork' / 'run.csv').write_text('a\n')
        self.assertFalse(pi_identity(self.repo).dirty)

    def test_ignored_file_in_scope_is_clean(self):
        (self.repo / 'RaspberryPi_Sensor_Hub' / 'a.pyc').write_bytes(b'\x00')
        self.assertFalse(pi_identity(self.repo).dirty)

    def test_not_a_repository_is_unknown(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        identity = pi_identity(outside)
        self.assertFalse(identity.is_known)
        self.assertTrue(identity.dirty)


if __name__ == '__main__':
    unittest.main()
