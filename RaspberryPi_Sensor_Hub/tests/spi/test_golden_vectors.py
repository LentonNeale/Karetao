"""The Pi side of the shared SPI golden frames (shared/test-vectors/spi/frames.txt).

The C host test spi_golden_vector_tests asserts the same file against spi_protocol.c, so a
vector that passes both suites is a frame the two implementations agree on byte for byte
(SYS-SPI-001 acceptance). What this side asserts is in the README next to the file.
"""

import importlib.util
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))


def _load_module(name: str, path: Path):
    # Loaded by path rather than by sys.path so neither helper shadows, or is shadowed by,
    # a same-named module elsewhere in the test process.
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolve annotations through sys.modules[__module__]
    spec.loader.exec_module(module)
    return module


golden_vectors = _load_module('karetao_golden_vectors', Path(__file__).resolve().parent / 'golden_vectors.py')
DEFAULT_PATH = golden_vectors.DEFAULT_PATH
load = golden_vectors.load
make_vectors = _load_module('karetao_make_vectors', DEFAULT_PATH.parent / 'make_vectors.py')
from spi.spi_protocol import (  # noqa: E402
    HEADER_STRUCT,
    MAX_FRAME_BYTES,
    SNAPSHOT_OFFSET_RESPONSE_TO_SEQ,
    SNAPSHOT_OFFSET_SCHEMA_VERSION,
    SNAPSHOT_SCHEMA_VERSION,
    PROTOCOL_VERSION,
    MessageType,
    NackReason,
    SpiFrame,
    VersionInfo,
    decode_command_reply,
    decode_snapshot_sensor_records,
)


def _transaction(frame: bytes) -> bytes:
    """The 512-byte transaction that carries a frame: zero bytes follow it."""
    return frame.ljust(MAX_FRAME_BYTES, b'\x00')


class GoldenVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vectors = load()

    def test_frames_file_matches_its_generator(self) -> None:
        # frames.txt is the authority and make_vectors.py the tool that writes it; this is the
        # `--check` the README promises, run on every test run so neither can drift from the other.
        self.assertEqual(DEFAULT_PATH.read_text(), make_vectors.render_all())

    def test_generator_type_set_is_the_message_type_enum(self) -> None:
        # The generator decides from this set whether a request is transport-valid for the Pi,
        # so it must be exactly the types the Pi decoder accepts.
        self.assertEqual(make_vectors.PI_KNOWN_TYPES, {int(member) for member in MessageType})

    def test_every_expected_result_is_a_known_reason(self) -> None:
        for vector in self.vectors:
            with self.subTest(vector=vector.name):
                self.assertIn(vector.expect, NackReason.__members__)

    def test_requests_encode_to_the_vector_bytes(self) -> None:
        # The Pi is the producer of requests, so this is its production encode path.
        checked = 0
        for vector in self.vectors:
            if vector.request_fields is None:
                continue
            with self.subTest(vector=vector.name):
                fields = vector.request_fields
                frame = SpiFrame(message_type=MessageType(fields.type), seq=fields.seq,
                                 frame_time_us=fields.frame_time_us, payload=fields.payload)
                self.assertEqual(frame.encode(), vector.request)
                checked += 1
        self.assertGreater(checked, 0)

    def test_requests_decode_to_the_vector_fields(self) -> None:
        for vector in self.vectors:
            if vector.request_fields is None:
                continue
            with self.subTest(vector=vector.name):
                decoded = SpiFrame.decode(_transaction(vector.request))
                self._assert_fields(decoded, vector.request_fields)

    def test_malformed_requests_are_rejected(self) -> None:
        # A request without decoded fields is not a valid transport frame for the Pi either,
        # whatever reason code the firmware NACKs it with.
        checked = 0
        for vector in self.vectors:
            if vector.request is None or vector.request_fields is not None:
                continue
            with self.subTest(vector=vector.name):
                with self.assertRaises(ValueError):
                    SpiFrame.decode(_transaction(vector.request))
                checked += 1
        self.assertGreater(checked, 0)

    def test_responses_decode_to_the_vector_fields(self) -> None:
        checked = 0
        for vector in self.vectors:
            if vector.response is None:
                continue
            with self.subTest(vector=vector.name):
                self.assertIsNotNone(vector.response_fields)
                decoded = SpiFrame.decode(_transaction(vector.response))
                self._assert_fields(decoded, vector.response_fields)
                checked += 1
        self.assertGreater(checked, 0)

    def test_command_replies_carry_the_expected_status_and_echo_the_request(self) -> None:
        checked = 0
        for vector in self.vectors:
            if vector.response is None or vector.response_fields.type not in (MessageType.ACK, MessageType.NACK):
                continue
            with self.subTest(vector=vector.name):
                self.assertIsNotNone(vector.request, 'an ACK or NACK answers a request')
                request_type, status, request_seq, detail = decode_command_reply(vector.response_fields.payload)
                self.assertEqual(NackReason.describe(status), vector.expect)
                self.assertEqual(vector.response_fields.type,
                                 MessageType.ACK if status == NackReason.OK else MessageType.NACK)
                # The firmware echoes the request's type and seq straight from the header, even
                # for a malformed request, so read them from the raw header rather than decode.
                _, _, raw_type, _, raw_seq, _ = HEADER_STRUCT.unpack_from(vector.request)
                self.assertEqual(request_type, raw_type)
                self.assertEqual(request_seq, raw_seq)
                self.assertEqual(detail, 0)
                checked += 1
        self.assertGreater(checked, 0)

    def test_snapshot_responses_correlate_and_decode(self) -> None:
        checked = 0
        for vector in self.vectors:
            if vector.response is None or vector.response_fields.type != MessageType.SNAPSHOT:
                continue
            with self.subTest(vector=vector.name):
                payload = vector.response_fields.payload
                self.assertEqual(payload[SNAPSHOT_OFFSET_SCHEMA_VERSION], SNAPSHOT_SCHEMA_VERSION)
                response_to_seq = struct.unpack_from('<I', payload, SNAPSHOT_OFFSET_RESPONSE_TO_SEQ)[0]
                self.assertEqual(response_to_seq, vector.request_fields.seq)
                records = decode_snapshot_sensor_records(payload)
                self.assertEqual([record.sensor_id for record in records], list(range(len(records))))
                self.assertTrue(any(record.is_valid for record in records))
                self.assertTrue(any(record.is_not_fitted for record in records))
                checked += 1
        self.assertGreater(checked, 0)

    def test_version_responses_decode_and_correlate(self) -> None:
        checked = 0
        for vector in self.vectors:
            if vector.response is None or vector.response_fields.type != MessageType.VERSION:
                continue
            with self.subTest(vector=vector.name):
                info = VersionInfo.decode(vector.response_fields.payload)
                self.assertEqual(info.response_to_seq, vector.request_fields.seq)
                self.assertEqual(info.protocol_version, PROTOCOL_VERSION)
                identity = make_vectors.HOST_TEST_IDENTITY
                self.assertEqual(info.firmware_version,
                                 f"{identity['major']}.{identity['minor']}.{identity['patch']}")
                self.assertEqual(info.build_flags, identity['build_flags'])
                checked += 1
        self.assertGreater(checked, 0)

    def _assert_fields(self, decoded: SpiFrame, fields) -> None:
        self.assertEqual(int(decoded.message_type), fields.type)
        self.assertEqual(decoded.seq, fields.seq)
        self.assertEqual(decoded.frame_time_us, fields.frame_time_us)
        self.assertEqual(decoded.payload, fields.payload)


if __name__ == '__main__':
    unittest.main()
