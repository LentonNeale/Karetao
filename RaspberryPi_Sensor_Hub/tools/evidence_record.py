#!/usr/bin/env python3
"""Draft an evidence record from a run directory.

Reads a run directory written in the run-record format (``spi.run_record``,
``meta.json`` plus one CSV per series) and drafts the record described by
``Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md``.

The record is tool-drafted and human-completed (GitHub #70, decided in #109):
the tool fills Date, Requirement IDs, Firmware identity (with the Pi commit and
both dirty flags), Hardware or rig, Procedure and Attachments from ``meta.json``,
and states whether the run may satisfy a matrix row. Result and "Accepted by
and date" are left for Lenton Neale. The tool never marks a run from a dirty
firmware build or a dirty Pi tree as eligible (format "Rules"; ruling R28(b)).

Examples::

    # Print the draft
    python3 tools/evidence_record.py BenchWork/runs/2026-10-20-spi-link-phase5

    # File it as Documentation/05_VERIFICATION/evidence/<date>-<kind>-<name>.md
    python3 tools/evidence_record.py BenchWork/runs/2026-10-20-spi-link-phase5 --file

    # Fail (exit 2) unless the run is reproducible, for scripts
    python3 tools/evidence_record.py <run dir> --file --require-clean

An existing record is never overwritten: records are not edited after
acceptance, and a new run is a new record.
"""

from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import shlex
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from spi.run_record import Run, RunRecordError, read_run  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE_DIR = REPO_ROOT / 'Documentation' / '05_VERIFICATION' / 'evidence'
TOOL_PATH = 'RaspberryPi_Sensor_Hub/tools/evidence_record.py'
FORMAT_PATH = 'Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md'
HUMAN = '**(human)**'

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_CLEAN = 2


def _is_requirement(identifier: str) -> bool:
    """Only SYS-* rows are matrix rows (EVIDENCE_RECORD_FORMAT.md "Requirement IDs")."""
    return identifier.upper().startswith('SYS-')


def _is_register(identifier: str) -> bool:
    return identifier.upper().startswith('PRM-')


def _cell(text: str) -> str:
    """Make free text safe inside a Markdown table cell."""
    return ' '.join(text.replace('|', '\\|').split())


def _codes(identifiers: list[str]) -> str:
    return ', '.join(f'`{_cell(i)}`' for i in identifiers)


def _relative(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path.resolve(), start.resolve())).as_posix()


def record_path(run: Run, evidence_dir: Path) -> Path:
    """``<evidence dir>/<date>-<kind>[-<name>].md``, from ``meta.json`` alone."""
    return evidence_dir / f'{run.meta.date}-{run.meta.short_name}.md'


def eligibility(run: Run) -> tuple[bool, list[str]]:
    """Whether the run may satisfy a matrix row, and the reasons when it may not.

    The verdict is ``RunMeta.reproducible``, the module's single definition;
    this function only puts words to it.
    """
    meta = run.meta
    reasons: list[str] = []
    if meta.firmware.dirty:
        if meta.firmware.warning:
            reasons.append(f'the firmware identity is unknown ({_cell(meta.firmware.warning)}), '
                           f'recorded as dirty')
        else:
            reasons.append('the firmware VERSION reports `build_flags` bit 0 set: built from '
                           'uncommitted changes (EVIDENCE_RECORD_FORMAT.md "Rules")')
    if not meta.pi.is_known:
        reasons.append(f'the Pi code identity is unknown ({_cell(meta.pi.error or "no commit")}), '
                       f'recorded as dirty (ruling R28(b))')
    elif meta.pi.dirty:
        reasons.append('the Pi working tree had uncommitted changes under '
                       + ', '.join(f'`{_cell(p)}/`' for p in meta.pi.scope)
                       + ' (ruling R28(b))')
    eligible = meta.reproducible
    if not eligible and not reasons:
        reasons.append('the run is not reproducible (RunMeta.reproducible)')
    return eligible, reasons


def draft_record(run: Run, evidence_dir: Path, today: date | None = None) -> str:
    """Render the Markdown draft; ``evidence_dir`` fixes the attachment paths."""
    meta = run.meta
    today = date.today() if today is None else today
    eligible, reasons = eligibility(run)

    requirement_ids = [i for i in meta.informs if _is_requirement(i)]
    register_ids = [i for i in meta.informs if _is_register(i)]
    other_ids = [i for i in meta.informs if not _is_requirement(i) and not _is_register(i)]

    fw = meta.firmware
    fw_bit = 'set (dirty build)' if fw.dirty else 'clear (clean build)'
    pi = meta.pi
    if pi.is_known:
        pi_state = 'dirty' if pi.dirty else 'clean'
        pi_text = (f'Pi commit `{_cell(pi.commit)}`, working tree {pi_state} under '
                   + ', '.join(f'`{_cell(p)}/`' for p in pi.scope))
    else:
        pi_text = f'Pi commit unknown ({_cell(pi.error or "no commit")}), recorded as dirty'
    firmware_text = (f'`git_hash_abbrev` `{_cell(fw.git_hash)}`, `build_flags` bit 0 {fw_bit}, '
                     f'firmware {_cell(fw.version)}, protocol {fw.protocol_version}, '
                     f'commit epoch {fw.commit_epoch_secs}; {pi_text}')
    if fw.warning:
        firmware_text += f'; firmware warning: {_cell(fw.warning)}'

    procedure = f'`{_cell(shlex.join(meta.tool_command))}` (run kind `{_cell(meta.kind)}`)'
    if meta.notes:
        procedure += f'; notes: {_cell(meta.notes)}'

    attachments = []
    for info in meta.series:
        attachments.append(f'`{_cell(_relative(run.directory / info.file, evidence_dir))}` '
                           f'(series `{_cell(info.name)}`, {info.rows} rows)')
    attachments.append(f'`{_cell(_relative(run.meta_path, evidence_dir))}` (run metadata)')

    result_hint = 'Pass or fail with the numbers observed'
    if register_ids:
        result_hint += ', and the `PRM-*` IDs they inform: ' + _codes(register_ids)
    else:
        result_hint += ', and the `PRM-*` IDs they inform, if any'
    if other_ids:
        result_hint += '; the run also informs ' + _codes(other_ids)

    requirement_text = _codes(requirement_ids) or 'none: not offered against a matrix row'

    lines = [
        f'# Evidence record: {meta.date} {meta.short_name}',
        '',
        f'Drafted by `{TOOL_PATH}` on {today.isoformat()} from the run directory '
        f'`{_relative(run.directory, evidence_dir)}`, following `{FORMAT_PATH}`. '
        f'Fields marked {HUMAN} are completed by Lenton Neale; the other fields were '
        f'read from `meta.json` and are not edited by hand.',
        '',
        '| Field | Content |',
        '|---|---|',
        f'| Date | {meta.date} |',
        f'| Requirement IDs | {requirement_text} |',
        f'| Firmware identity | {firmware_text} |',
        f'| Hardware or rig | {_cell(meta.rig)} |',
        f'| Procedure | {procedure} |',
        f'| Result | {HUMAN} {result_hint} |',
        f'| Attachments | {"; ".join(attachments)} |',
        f'| Accepted by and date | {HUMAN} Lenton Neale, YYYY-MM-DD |',
        '',
        '## Matrix eligibility',
        '',
    ]
    if eligible and requirement_ids:
        lines.append('Eligible: the firmware build and the Pi working tree were both clean, so '
                     'once accepted this record may be offered against the matrix rows named '
                     'under Requirement IDs. Only `SYSTEM_VERIFICATION_MATRIX.md` assigns a '
                     'row\'s status.')
    elif eligible:
        lines.append('Eligible: the firmware build and the Pi working tree were both clean. '
                     'No `SYS-*` row is named under Requirement IDs, so this record informs '
                     'the identifiers listed in Result and is not offered against a matrix row.')
    else:
        lines.append('**Not eligible: this record cannot satisfy a matrix row**, because')
        lines.append('')
        for reason in reasons:
            lines.append(f'- {reason}')
        lines.append('')
        lines.append('It is kept as the record of what was run. Rerun from committed code to '
                     'produce evidence.')
    lines.append('')
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('run_dir', type=Path, help='run directory holding meta.json')
    parser.add_argument('--evidence-dir', type=Path, default=DEFAULT_EVIDENCE_DIR,
                        help='where records are filed; attachment paths are relative to it '
                             '(default: Documentation/05_VERIFICATION/evidence)')
    parser.add_argument('--file', action='store_true',
                        help='write <evidence-dir>/<date>-<kind>-<name>.md instead of printing')
    parser.add_argument('--output', type=Path,
                        help='write the draft to this path instead (implies a file)')
    parser.add_argument('--require-clean', action='store_true',
                        help=f'exit {EXIT_NOT_CLEAN} without writing when the run cannot '
                             f'satisfy a matrix row')
    args = parser.parse_args(argv)

    try:
        run = read_run(args.run_dir)
    except RunRecordError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return EXIT_ERROR

    eligible, reasons = eligibility(run)
    if args.require_clean and not eligible:
        print('error: this run cannot satisfy a matrix row:', file=sys.stderr)
        for reason in reasons:
            print(f'  - {reason}', file=sys.stderr)
        return EXIT_NOT_CLEAN

    target = args.output if args.output is not None else (
        record_path(run, args.evidence_dir) if args.file else None)
    evidence_dir = target.parent if target is not None else args.evidence_dir
    draft = draft_record(run, evidence_dir)

    if target is None:
        sys.stdout.write(draft)
        return EXIT_OK
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Exclusive create: the never-overwrite rule holds even when two drafts race.
        with open(target, 'x', encoding='utf-8') as handle:
            handle.write(draft)
    except FileExistsError:
        print(f'error: {target} exists; records are never edited after acceptance, '
              f'and a new run is a new record', file=sys.stderr)
        return EXIT_ERROR
    print(f'drafted {target}')
    if not eligible:
        print('note: this run cannot satisfy a matrix row (see the record\'s eligibility section)')
    return EXIT_OK


if __name__ == '__main__':
    sys.exit(main())
