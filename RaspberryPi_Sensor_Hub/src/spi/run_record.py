"""Run-record format: one directory per bench run, shared by writer and reader.

A run directory holds ``meta.json`` and one CSV per series::

    <run directory>/          (by convention named <date>-<kind>-<name>)
        meta.json
        <series>.csv ...

This module implements the run-directory contract stated in
``Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md`` ("Run directories"),
in the same lockstep pattern as the SPI frame codec implements the SPI
contract: the Pi capture tools write it through ``write_run`` and the PC-side
analysis and the evidence-record tool read it through ``read_run``. The
mandatory fields and the Pi dirty scope below repeat that section and change
only with it. Decided in GitHub #109 and carried by #70.

``meta.json`` captures at run time everything an evidence record needs so
nothing is reconstructed afterwards: what kind of run it was, on which rig,
which register or verification IDs it informs, the firmware identity from the
VERSION frame, and the Pi code identity. The record's name and date come from
``meta.json`` (``kind``, ``name``, ``started``), never from the directory name.

Identity rules mirror the firmware build (``Arm_Sensor_Hub/cmake/firmware_identity.cmake``):

- the Pi dirty check is scoped to the paths that affect the Pi side,
  ``RaspberryPi_Sensor_Hub/`` and ``shared/`` (ruling R28(b)); untracked files
  count, ignored files do not, exactly as ``git status --porcelain`` reports;
- when git cannot read the tree the identity is unknown and conservative:
  empty commit, dirty set, and the reason recorded.

Standard library only (the Pi component rule).
"""

from __future__ import annotations

import csv
from datetime import datetime
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .spi_protocol import VersionInfo

RUN_RECORD_SCHEMA_VERSION = 1
META_FILENAME = 'meta.json'

# Paths, relative to the repository root, whose uncommitted changes make a Pi
# run unreproducible (EVIDENCE_RECORD_FORMAT.md "Rules"). The firmware's
# counterpart is Arm_Sensor_Hub/ and shared/.
PI_DIRTY_SCOPE: tuple[str, ...] = ('RaspberryPi_Sensor_Hub', 'shared')

# The run_record module lives at <repo>/RaspberryPi_Sensor_Hub/src/spi/run_record.py.
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]

# Top-level keys every meta.json must carry (EVIDENCE_RECORD_FORMAT.md "Run directories").
REQUIRED_META_FIELDS: tuple[str, ...] = (
    'schema_version', 'kind', 'rig', 'informs', 'started', 'tool_command',
    'firmware', 'pi', 'series',
)
REQUIRED_FIRMWARE_FIELDS: tuple[str, ...] = (
    'version', 'git_hash', 'commit_epoch_secs', 'protocol_version', 'dirty',
)
REQUIRED_PI_FIELDS: tuple[str, ...] = ('commit', 'dirty', 'scope')
REQUIRED_SERIES_FIELDS: tuple[str, ...] = ('name', 'file', 'columns', 'rows')

GitRunner = Callable[[Sequence[str], Path], tuple[int, str, str]]


class RunRecordError(ValueError):
    """A run directory or its meta.json does not follow the run-record format."""


# --- field readers: every malformed value becomes a RunRecordError naming the field ---

def _require(data: Mapping[str, Any], fields: Sequence[str], where: str) -> None:
    if not isinstance(data, Mapping):
        raise RunRecordError(f'{where} must be a JSON object')
    for name in fields:
        if name not in data:
            raise RunRecordError(f'{where} is missing the mandatory field {name!r}')


def _str(data: Mapping[str, Any], name: str, where: str, non_empty: bool = False) -> str:
    value = data[name]
    if not isinstance(value, str) or (non_empty and not value.strip()):
        kind = 'a non-empty string' if non_empty else 'a string'
        raise RunRecordError(f'{where} field {name!r} must be {kind}')
    return value


def _int(data: Mapping[str, Any], name: str, where: str) -> int:
    value = data[name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise RunRecordError(f'{where} field {name!r} must be an integer')
    return value


def _bool(data: Mapping[str, Any], name: str, where: str) -> bool:
    value = data[name]
    if not isinstance(value, bool):
        raise RunRecordError(f'{where} field {name!r} must be true or false')
    return value


def _str_list(data: Mapping[str, Any], name: str, where: str) -> list[str]:
    value = data[name]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise RunRecordError(f'{where} field {name!r} must be a list of strings')
    return list(value)


def _optional_str(data: Mapping[str, Any], name: str, where: str, default: str = '') -> str:
    if name not in data or data[name] is None:
        return default
    return _str(data, name, where)


def started_now() -> str:
    """The ``started`` value for a run beginning now: local time with its UTC offset."""
    return datetime.now().astimezone().isoformat(timespec='seconds')


def parse_started(value: str) -> datetime:
    """Parse ``started``: ISO 8601 with a UTC offset, so the local run date is unambiguous."""
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise RunRecordError(
            f'meta.json field \'started\' must be an ISO 8601 time with a UTC offset, '
            f'such as 2026-10-20T10:15:00+13:00, not {value!r}') from None
    if parsed.tzinfo is None:
        raise RunRecordError('meta.json field \'started\' must carry a UTC offset')
    return parsed


@dataclass(frozen=True)
class FirmwareIdentity:
    """The firmware build that produced the run, as decoded from a VERSION frame."""

    version: str
    git_hash: str
    commit_epoch_secs: int
    protocol_version: int
    dirty: bool
    warning: str | None = None

    @classmethod
    def from_version_info(cls, info: VersionInfo) -> 'FirmwareIdentity':
        return cls(version=info.firmware_version, git_hash=info.git_hash,
                   commit_epoch_secs=info.commit_epoch_secs,
                   protocol_version=info.protocol_version, dirty=info.is_dirty_build)

    @classmethod
    def unknown(cls, reason: str) -> 'FirmwareIdentity':
        """The identity when GET_VERSION could not be answered.

        Conservative, like the firmware build when git fails: hash zero and
        dirty set, so the run is kept but can never satisfy a matrix row.
        """
        return cls(version='unknown', git_hash='00000000', commit_epoch_secs=0,
                   protocol_version=0, dirty=True, warning=reason)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            'version': self.version, 'git_hash': self.git_hash,
            'commit_epoch_secs': self.commit_epoch_secs,
            'protocol_version': self.protocol_version, 'dirty': self.dirty,
        }
        if self.warning is not None:
            data['warning'] = self.warning
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> 'FirmwareIdentity':
        where = 'meta.json "firmware"'
        _require(data, REQUIRED_FIRMWARE_FIELDS, where)
        warning = _optional_str(data, 'warning', where, default='')
        return cls(version=_str(data, 'version', where), git_hash=_str(data, 'git_hash', where),
                   commit_epoch_secs=_int(data, 'commit_epoch_secs', where),
                   protocol_version=_int(data, 'protocol_version', where),
                   dirty=_bool(data, 'dirty', where), warning=warning or None)


@dataclass(frozen=True)
class PiIdentity:
    """The Pi checkout that produced the run."""

    commit: str
    dirty: bool
    scope: tuple[str, ...] = PI_DIRTY_SCOPE
    error: str | None = None

    @property
    def is_known(self) -> bool:
        return self.commit != '' and self.error is None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {'commit': self.commit, 'dirty': self.dirty,
                                'scope': list(self.scope)}
        if self.error is not None:
            data['error'] = self.error
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> 'PiIdentity':
        where = 'meta.json "pi"'
        _require(data, REQUIRED_PI_FIELDS, where)
        error = _optional_str(data, 'error', where, default='')
        return cls(commit=_str(data, 'commit', where), dirty=_bool(data, 'dirty', where),
                   scope=tuple(_str_list(data, 'scope', where)), error=error or None)


def _subprocess_runner(args: Sequence[str], cwd: Path) -> tuple[int, str, str]:
    completed = subprocess.run(list(args), capture_output=True, text=True, timeout=10,
                               cwd=str(cwd))
    return completed.returncode, completed.stdout, completed.stderr


def pi_identity(repo_root: Path | None = None, scope: Sequence[str] = PI_DIRTY_SCOPE,
                runner: GitRunner | None = None) -> PiIdentity:
    """Read the Pi code identity the way the firmware build reads its own.

    ``git rev-parse HEAD`` gives the commit; ``git status --porcelain -- <scope>``
    gives the dirty flag, limited to the paths that affect this component so an
    unrelated edit elsewhere in the repository does not disqualify a run. Any
    git failure (no git, not a checkout, unreadable tree) yields an unknown and
    dirty identity with the reason, never a silent "clean".
    """
    root = DEFAULT_REPO_ROOT if repo_root is None else Path(repo_root)
    run = _subprocess_runner if runner is None else runner
    scope = tuple(scope)
    try:
        code, out, err = run(['git', 'rev-parse', 'HEAD'], root)
        if code != 0:
            return PiIdentity(commit='', dirty=True, scope=scope,
                              error=f'git rev-parse failed: {err.strip() or code}')
        commit = out.strip()
        code, out, err = run(['git', 'status', '--porcelain', '--', *scope], root)
        if code != 0:
            return PiIdentity(commit='', dirty=True, scope=scope,
                              error=f'git status failed: {err.strip() or code}')
    except (OSError, subprocess.SubprocessError) as exc:
        return PiIdentity(commit='', dirty=True, scope=scope, error=f'git unavailable: {exc}')
    return PiIdentity(commit=commit, dirty=bool(out.strip()), scope=scope)


@dataclass(frozen=True)
class SeriesInfo:
    """One CSV in the run directory."""

    name: str
    file: str
    columns: tuple[str, ...]
    rows: int

    def to_dict(self) -> dict[str, Any]:
        return {'name': self.name, 'file': self.file, 'columns': list(self.columns),
                'rows': self.rows}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> 'SeriesInfo':
        where = 'meta.json "series" entry'
        _require(data, REQUIRED_SERIES_FIELDS, where)
        return cls(name=_str(data, 'name', where, non_empty=True),
                   file=_str(data, 'file', where, non_empty=True),
                   columns=tuple(_str_list(data, 'columns', where)),
                   rows=_int(data, 'rows', where))


@dataclass
class RunMeta:
    """The content of ``meta.json``.

    ``informs`` lists the identifiers the run is meant to inform: ``PRM-*``
    register rows (Provisional to Measured), ``LIVE-*`` items, or ``SYS-*``
    requirements it is offered against. ``started`` is the local start time
    with its UTC offset (``started_now()``), so the record's date is the day
    the run was made. ``tool_command`` is the capture command, argument by
    argument, so the Procedure field of the record is the command actually
    run. ``name`` distinguishes runs of one kind and, with ``kind`` and the
    date, names the record. ``tool_metadata`` is free-form for the capturing
    tool (host state, configuration) and is not interpreted here.
    """

    kind: str
    rig: str
    informs: list[str]
    started: str
    tool_command: list[str]
    firmware: FirmwareIdentity
    pi: PiIdentity
    series: list[SeriesInfo] = field(default_factory=list)
    name: str = ''
    notes: str = ''
    tool_metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = RUN_RECORD_SCHEMA_VERSION

    @property
    def date(self) -> str:
        """The run date, YYYY-MM-DD, in the offset ``started`` carries."""
        return parse_started(self.started).date().isoformat()

    @property
    def short_name(self) -> str:
        """``<kind>`` or ``<kind>-<name>``: the record is ``<date>-<short_name>.md``."""
        return f'{self.kind}-{self.name}' if self.name else self.kind

    @property
    def reproducible(self) -> bool:
        """True when both identities are known and clean.

        This is the admissibility test of EVIDENCE_RECORD_FORMAT.md "Rules" and
        ruling R28(b): only such a run may satisfy a matrix row.
        """
        return (not self.firmware.dirty) and self.pi.is_known and (not self.pi.dirty)

    def to_dict(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'kind': self.kind,
            'name': self.name,
            'rig': self.rig,
            'informs': list(self.informs),
            'started': self.started,
            'tool_command': list(self.tool_command),
            'firmware': self.firmware.to_dict(),
            'pi': self.pi.to_dict(),
            'series': [s.to_dict() for s in self.series],
            'notes': self.notes,
            'tool_metadata': dict(self.tool_metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> 'RunMeta':
        where = 'meta.json'
        _require(data, REQUIRED_META_FIELDS, where)
        schema_version = _int(data, 'schema_version', where)
        if schema_version != RUN_RECORD_SCHEMA_VERSION:
            raise RunRecordError(
                f'meta.json schema_version {schema_version!r} is not supported '
                f'(this reader understands {RUN_RECORD_SCHEMA_VERSION})')
        started = _str(data, 'started', where, non_empty=True)
        parse_started(started)
        tool_command = _str_list(data, 'tool_command', where)
        if not tool_command:
            raise RunRecordError('meta.json field \'tool_command\' must name the capture command')
        series = data['series']
        if not isinstance(series, list):
            raise RunRecordError('meta.json field \'series\' must be a list')
        tool_metadata = data.get('tool_metadata', {})
        if not isinstance(tool_metadata, Mapping):
            raise RunRecordError('meta.json field \'tool_metadata\' must be a JSON object')
        return cls(
            kind=_str(data, 'kind', where, non_empty=True),
            rig=_str(data, 'rig', where, non_empty=True),
            informs=_str_list(data, 'informs', where),
            started=started,
            tool_command=tool_command,
            firmware=FirmwareIdentity.from_dict(data['firmware']),
            pi=PiIdentity.from_dict(data['pi']),
            series=[SeriesInfo.from_dict(s) for s in series],
            name=_optional_str(data, 'name', where),
            notes=_optional_str(data, 'notes', where),
            tool_metadata=dict(tool_metadata),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class Run:
    """A run directory opened for reading."""

    directory: Path
    meta: RunMeta

    @property
    def meta_path(self) -> Path:
        return self.directory / META_FILENAME

    def series_path(self, name: str) -> Path:
        for info in self.meta.series:
            if info.name == name:
                return self.directory / info.file
        raise RunRecordError(f'run has no series named {name!r}')

    def read_series(self, name: str) -> tuple[list[str], list[list[str]]]:
        """Return a series as (columns, rows of strings); callers convert types."""
        return read_series(self.series_path(name))

    def attachments(self) -> list[Path]:
        """Every file the record should attach: meta.json then each series."""
        return [self.meta_path] + [self.directory / s.file for s in self.meta.series]


def write_series(path: Path, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
    """Write one CSV with a header row; returns the number of data rows."""
    count = 0
    with open(path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(list(columns))
        for row in rows:
            if len(row) != len(columns):
                raise RunRecordError(
                    f'{path.name}: row {count} has {len(row)} values for {len(columns)} columns')
            writer.writerow(list(row))
            count += 1
    return count


def read_series(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, 'r', newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        try:
            columns = next(reader)
        except StopIteration:
            raise RunRecordError(f'{path.name}: empty series file') from None
        rows = [row for row in reader]
    return columns, rows


def write_run(run_dir: Path, meta: RunMeta,
              series: Mapping[str, tuple[Sequence[str], Iterable[Sequence[Any]]]] | None = None,
              ) -> Path:
    """Create a run directory from ``meta`` and the given series.

    ``series`` maps a series name to ``(columns, rows)``; each becomes
    ``<name>.csv`` and is listed in ``meta.series``. The metadata is validated
    before anything is written, and a failed series write removes the files
    written so far, so the directory either holds a complete run or nothing
    of this one. An existing ``meta.json`` is never overwritten: a run is
    written once (a new run is a new directory). Returns the path of
    ``meta.json``.
    """
    run_dir = Path(run_dir)
    meta_path = run_dir / META_FILENAME
    if meta_path.exists():
        raise RunRecordError(f'{run_dir} already holds a run; a new run is a new directory')
    series = dict(series or {})
    for name in series:
        if not name or '/' in name or '\\' in name or name.startswith('.'):
            raise RunRecordError(f'series name {name!r} is not a plain file stem')
    # Validate before touching the filesystem, so a writer cannot leave a
    # half-written run or produce what the reader rejects.
    meta.series = []
    RunMeta.from_dict(meta.to_dict())

    run_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    infos: list[SeriesInfo] = []
    try:
        for name, (columns, rows) in series.items():
            file_name = f'{name}.csv'
            path = run_dir / file_name
            written.append(path)
            count = write_series(path, columns, rows)
            infos.append(SeriesInfo(name=name, file=file_name, columns=tuple(columns), rows=count))
        meta.series = infos
        content = RunMeta.from_dict(meta.to_dict()).to_dict()
        with open(meta_path, 'x', encoding='utf-8') as handle:
            json.dump(content, handle, indent=2, sort_keys=False)
            handle.write('\n')
    except Exception:
        for path in written:
            path.unlink(missing_ok=True)
        raise
    return meta_path


def read_run(run_dir: Path) -> Run:
    """Open a run directory, validating ``meta.json`` and that each series file exists."""
    run_dir = Path(run_dir)
    meta_path = run_dir / META_FILENAME
    if not meta_path.is_file():
        raise RunRecordError(f'{run_dir} has no {META_FILENAME}')
    try:
        with open(meta_path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RunRecordError(f'{meta_path} is not valid JSON: {exc}') from exc
    meta = RunMeta.from_dict(data)
    for info in meta.series:
        if not (run_dir / info.file).is_file():
            raise RunRecordError(f'series {info.name!r} names a missing file {info.file!r}')
    return Run(directory=run_dir, meta=meta)
