"""The firmware-rules fake (src/spi/fake_backend.py) against the shared golden frames.

Each vector puts the STM32 in a state, feeds it a request and names the response it stages.
The C host test spi_golden_vector_tests asserts the same file against spi_protocol.c, so a fake
that reproduces every vector byte for byte answers the way the firmware's protocol module does.
"""

import importlib.util
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))


def _load_module(name: str, path: Path):
    # Loaded by path, as test_golden_vectors.py does, so neither helper shadows another module.
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


golden_vectors = _load_module('karetao_golden_vectors', Path(__file__).resolve().parent / 'golden_vectors.py')
make_vectors = _load_module('karetao_make_vectors', golden_vectors.DEFAULT_PATH.parent / 'make_vectors.py')

from spi.fake_backend import IDLE_MISO, FakeFirmware, FirmwareIdentity  # noqa: E402
from spi.spi_protocol import HEADER_SIZE, MAX_FRAME_BYTES, MessageType, NackReason, SpiFrame, decode_command_reply  # noqa: E402
from spi.exchange import GET_REQUEST_PAYLOAD  # noqa: E402


def _padded(frame: bytes) -> bytes:
    return frame.ljust(MAX_FRAME_BYTES, b'\x00')


def _request(message_type: MessageType, seq: int, payload: bytes = GET_REQUEST_PAYLOAD) -> bytes:
    return _padded(SpiFrame(message_type=message_type, seq=seq, payload=payload).encode())


class GoldenVectorTests(unittest.TestCase):
    def test_identity_default_is_the_vectors_host_test_identity(self) -> None:
        identity = FirmwareIdentity()
        self.assertEqual(dict(major=identity.major, minor=identity.minor, patch=identity.patch,
                              build_flags=identity.build_flags, git_hash_abbrev=identity.git_hash_abbrev,
                              commit_epoch_secs=identity.commit_epoch_secs),
                         make_vectors.HOST_TEST_IDENTITY)

    def test_get_payload_is_the_vectors_form(self) -> None:
        self.assertEqual(GET_REQUEST_PAYLOAD, make_vectors.GET_REQUEST_PAYLOAD)

    def test_every_vector_reproduced_byte_for_byte(self) -> None:
        for vector in golden_vectors.load():
            with self.subTest(vector=vector.name):
                if vector.request is None:
                    # The boot frame: what a fresh slave stages before any request.
                    fake = FakeFirmware(next_tx_seq=vector.next_tx_seq, clock_us=lambda: vector.now_us)
                    self.assertEqual(fake.staged_frame, _padded(vector.response))
                    self.assertEqual(fake.next_tx_seq, vector.next_tx_seq + 1)
                    continue

                fake = FakeFirmware(next_tx_seq=vector.next_tx_seq, last_request_seq=vector.last_request_seq,
                                    clock_us=lambda: vector.now_us, boot=False)
                if vector.staged_snapshot is not None:
                    fake.publish_snapshot(vector.staged_snapshot)

                fake.transfer(_padded(vector.request))

                self.assertEqual(fake.results, [NackReason[vector.expect]])
                self.assertEqual(fake.staged_frame, _padded(vector.response))
                self.assertEqual(fake.next_tx_seq, vector.next_tx_seq + 1)  # one transmit seq used
                if vector.expect == 'OK':
                    self.assertEqual(fake.last_request_seq, vector.request_fields.seq)
                else:
                    self.assertEqual(fake.last_request_seq, vector.last_request_seq)  # nothing changed


class FirmwareRuleTests(unittest.TestCase):
    def test_reply_arrives_one_transaction_late(self) -> None:
        fake = FakeFirmware()
        first = SpiFrame.decode(fake.transfer(_request(MessageType.GET_STATUS, 10)))
        second = SpiFrame.decode(fake.transfer(_request(MessageType.GET_STATUS, 11)))

        self.assertIs(first.message_type, MessageType.DIAGNOSTIC)  # the boot frame
        self.assertIs(second.message_type, MessageType.ACK)
        self.assertEqual(decode_command_reply(second.payload)[2], 10)  # answers the first request

    def test_high_water_mark_refuses_a_repeated_sequence(self) -> None:
        fake = FakeFirmware()
        fake.transfer(_request(MessageType.GET_STATUS, 10))
        fake.transfer(_request(MessageType.GET_STATUS, 10))
        self.assertEqual(fake.results, [NackReason.OK, NackReason.BAD_SEQUENCE])
        self.assertEqual(fake.last_request_seq, 10)

    def test_sequence_checked_before_message_type(self) -> None:
        # SpiProtocol_ValidateRequest checks the sequence before the type (spi_protocol.c), and no
        # golden vector has both faults, so this pins the order the vectors leave open.
        fake = FakeFirmware(last_request_seq=10)
        fake.transfer(_request(MessageType.ACK, 10, b''))
        self.assertEqual(fake.results, [NackReason.BAD_SEQUENCE])

    def test_high_water_mark_is_wrap_tolerant(self) -> None:
        fake = FakeFirmware(last_request_seq=0xFFFFFFFF)
        fake.transfer(_request(MessageType.GET_STATUS, 1))
        self.assertEqual(fake.results, [NackReason.OK])

    def test_not_active_refuses_with_bad_state_and_keeps_the_mark(self) -> None:
        fake = FakeFirmware(active=False)
        fake.transfer(_request(MessageType.GET_STATUS, 10))
        self.assertEqual(fake.results, [NackReason.BAD_STATE])
        self.assertIsNone(fake.last_request_seq)

        fake.activate()
        fake.transfer(_request(MessageType.GET_STATUS, 10))  # the same seq is still newer
        self.assertEqual(fake.results[-1], NackReason.OK)

    def test_time_sync_allowed_while_not_active(self) -> None:
        fake = FakeFirmware(active=False)
        payload = bytes([1, 0, 0, 0]) + bytes(12)
        fake.transfer(_request(MessageType.TIME_SYNC, 10, payload))
        self.assertEqual(fake.results, [NackReason.OK])

    def test_request_crc_checked(self) -> None:
        fake = FakeFirmware()
        request = bytearray(_request(MessageType.GET_STATUS, 10))
        request[HEADER_SIZE + len(GET_REQUEST_PAYLOAD)] ^= 0x01  # first CRC byte
        fake.transfer(bytes(request))
        self.assertEqual(fake.results, [NackReason.BAD_CRC])

    def test_snapshot_answers_get_snapshot_once(self) -> None:
        fake = FakeFirmware()
        fake.publish_snapshot(bytes([1, 0, 0, 0, 0, 0, 0, 0]) + bytes(4))
        fake.transfer(_request(MessageType.GET_SNAPSHOT, 10))
        reply = SpiFrame.decode(fake.transfer(_request(MessageType.GET_SNAPSHOT, 11)))
        after = SpiFrame.decode(fake.transfer(_request(MessageType.GET_STATUS, 12)))

        self.assertIs(reply.message_type, MessageType.SNAPSHOT)
        self.assertIs(after.message_type, MessageType.ACK)  # GET_SNAPSHOT 11 found nothing staged

    def test_garbage_mode_never_receives_the_request(self) -> None:
        fake = FakeFirmware()
        fake.garbage = True
        self.assertEqual(fake.transfer(_request(MessageType.GET_STATUS, 10)), IDLE_MISO)
        self.assertEqual(fake.results, [])
        self.assertIsNone(fake.last_request_seq)

    def test_snapshot_length_limits(self) -> None:
        with self.assertRaises(ValueError):
            FakeFirmware().publish_snapshot(b'\x01')

    def test_transfer_must_be_a_full_transaction(self) -> None:
        with self.assertRaises(ValueError):
            FakeFirmware().transfer(b'\x00' * 10)



if __name__ == '__main__':
    unittest.main()
