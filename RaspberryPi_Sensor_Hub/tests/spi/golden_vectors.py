"""Loader for the shared SPI golden frames (shared/test-vectors/spi/frames.txt).

The file format is described in the README next to the file. This module only parses it;
the assertions live in test_golden_vectors.py (and later in the firmware-rules fake of the
exchange session, which replays the same vectors).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = REPO_ROOT / 'shared' / 'test-vectors' / 'spi' / 'frames.txt'


@dataclass(frozen=True)
class FrameFields:
    """The decoded view of a frame, as the vector states it."""

    type: int
    seq: int
    frame_time_us: int
    payload: bytes


@dataclass
class Vector:
    name: str
    description: str = ''
    next_tx_seq: Optional[int] = None
    last_request_seq: Optional[int] = None
    last_request_seq_given: bool = False
    now_us: Optional[int] = None
    staged_snapshot: Optional[bytes] = None
    request: Optional[bytes] = None
    request_fields: Optional[FrameFields] = None
    expect: str = ''
    response: Optional[bytes] = None
    response_fields: Optional[FrameFields] = None
    _pending: dict = field(default_factory=dict, repr=False)


def _parse_int(value: str) -> int:
    return int(value, 0)


def _finish(vector: Vector) -> Vector:
    for prefix in ('request', 'response'):
        parts = vector._pending.pop(prefix, None)
        if parts is None:
            continue
        missing = {'type', 'seq', 'frame_time_us', 'payload'} - set(parts)
        if missing:
            raise ValueError(f'[{vector.name}] {prefix} fields incomplete: {sorted(missing)}')
        setattr(vector, f'{prefix}_fields', FrameFields(**parts))
    if vector.next_tx_seq is None or vector.now_us is None or not vector.last_request_seq_given or not vector.expect:
        raise ValueError(f'[{vector.name}] stm32.next_tx_seq, stm32.last_request_seq, stm32.now_us '
                         'and expect are required')
    if vector.response is not None and vector.response_fields is None:
        raise ValueError(f'[{vector.name}] a response needs its response.* fields')
    if vector.request is None and vector.request_fields is not None:
        raise ValueError(f'[{vector.name}] request.* fields without a request')
    if vector.request is None and vector.expect != 'OK':
        raise ValueError(f'[{vector.name}] a vector without a request can only expect OK')
    return vector


def _set(vector: Vector, key: str, value: str) -> None:
    if key == 'description':
        vector.description = value
    elif key == 'stm32.next_tx_seq':
        vector.next_tx_seq = _parse_int(value)
    elif key == 'stm32.last_request_seq':
        vector.last_request_seq = None if value == 'none' else _parse_int(value)
        vector.last_request_seq_given = True
    elif key == 'stm32.now_us':
        vector.now_us = _parse_int(value)
    elif key == 'stm32.staged_snapshot':
        vector.staged_snapshot = bytes.fromhex(value)
    elif key in ('request', 'response'):
        setattr(vector, key, bytes.fromhex(value))
    elif key == 'expect':
        vector.expect = value
    elif key.startswith(('request.', 'response.')):
        prefix, name = key.split('.', 1)
        parts = vector._pending.setdefault(prefix, {})
        if name == 'payload':
            parts[name] = bytes.fromhex(value)
        elif name in ('type', 'seq', 'frame_time_us'):
            parts[name] = _parse_int(value)
        else:
            raise ValueError(f'[{vector.name}] unknown frame field {key}')
    else:
        raise ValueError(f'[{vector.name}] unknown key {key}')


def load(path: Path = DEFAULT_PATH) -> list[Vector]:
    vectors: list[Vector] = []
    current: Optional[Vector] = None
    for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
        text = raw.strip()
        if not text or text.startswith('#'):
            continue
        if text.startswith('['):
            if not text.endswith(']'):
                raise ValueError(f'{path}:{line_number}: bad vector header')
            if current is not None:
                vectors.append(_finish(current))
            current = Vector(name=text[1:-1])
            continue
        if current is None or '=' not in text:
            raise ValueError(f'{path}:{line_number}: expected "key = value" inside a vector')
        key, value = (part.strip() for part in text.split('=', 1))
        _set(current, key, value)
    if current is not None:
        vectors.append(_finish(current))
    if not vectors:
        raise ValueError(f'{path}: no vectors')
    names = [v.name for v in vectors]
    if len(set(names)) != len(names):
        raise ValueError(f'{path}: duplicate vector names')
    return vectors
