import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

import struct

from spi.spi_bus import SpiBus, SpiBusConfig
from spi.spi_device import SpiDevice
from spi.spi_protocol import MessageType, SpiFrame, initial_sequence


def build_version_payload(response_to_seq: int = 7, build_flags: int = 0) -> bytes:
    return struct.pack('<BBBBBBHIII', 1, 1, 0, 1, 0, build_flags, 0,
                       response_to_seq, 0x1A2B3C4D, 1_700_000_000)


class FakeBackend:
    def __init__(self, response: bytes | None = None) -> None:
        self.last_request = b''
        self.requests: list[bytes] = []
        self._response = response or SpiFrame(message_type=MessageType.ACK, seq=99, payload=b'\x01\x11\x00\x00\x2A\x00\x00\x00\x00\x00\x00\x00').encode()

    def open(self, config: SpiBusConfig) -> None:
        self.config = config

    def transfer(self, tx_data: bytes) -> bytes:
        self.last_request = tx_data
        self.requests.append(tx_data)
        return self._response

    def close(self) -> None:
        return None


class PipelinedFakeBackend:
    """Stages a reply only after the request is clocked in, like the firmware."""

    def __init__(self, delay_transactions: int = 1) -> None:
        self.transfers = 0
        self._delay = delay_transactions
        self._queue: list[bytes] = []
        self._idle = SpiFrame(message_type=MessageType.ACK, seq=0,
                              payload=b'\x01\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00').encode()

    def open(self, config: SpiBusConfig) -> None:
        self.config = config

    def transfer(self, tx_data: bytes) -> bytes:
        self.transfers += 1
        request = SpiFrame.decode(tx_data)
        if request.message_type is MessageType.GET_VERSION:
            staged = SpiFrame(message_type=MessageType.VERSION, seq=self.transfers,
                              payload=build_version_payload(response_to_seq=request.seq)).encode()
            self._queue.extend([self._idle] * (self._delay - 1) + [staged])
        return self._queue.pop(0) if self._queue else self._idle

    def close(self) -> None:
        return None


class SpiDeviceTests(unittest.TestCase):
    def test_device_transact_uses_bus_backend(self) -> None:
        backend = FakeBackend()
        bus = SpiBus(SpiBusConfig(), backend=backend)
        bus.open()

        device = SpiDevice(bus)
        request = SpiFrame(message_type=MessageType.GET_STATUS, seq=5)
        response = device.transact(request)

        self.assertEqual(SpiFrame.decode(backend.last_request), request)
        self.assertEqual(response.message_type, MessageType.ACK)
        self.assertEqual(response.seq, 99)

    def test_transfer_requires_open_bus(self) -> None:
        device = SpiDevice(SpiBus(SpiBusConfig(), backend=FakeBackend()))
        with self.assertRaises(RuntimeError):
            device.get_status(seq=1)

    def test_get_version_decodes_firmware_identity(self) -> None:
        response = SpiFrame(message_type=MessageType.VERSION, seq=42,
                            payload=build_version_payload(response_to_seq=7)).encode()
        backend = FakeBackend(response)
        bus = SpiBus(SpiBusConfig(), backend=backend)
        bus.open()

        version = SpiDevice(bus).get_version(seq=7, retry_delay_s=0)

        # Pipelining means the request's own transfer can never carry its
        # answer; the GET_VERSION request must be on the wire, but the
        # decoded VERSION always arrives on a later transaction.
        sent_types = [SpiFrame.decode(raw).message_type for raw in backend.requests]
        self.assertIn(MessageType.GET_VERSION, sent_types)
        version_request = next(SpiFrame.decode(raw) for raw in backend.requests
                               if SpiFrame.decode(raw).message_type is MessageType.GET_VERSION)
        self.assertEqual(version_request.payload, b'\x01')
        self.assertEqual(version.firmware_version, '0.1.0')
        self.assertEqual(version.git_hash, '1a2b3c4d')
        self.assertEqual(version.response_to_seq, 7)
        self.assertFalse(version.is_dirty_build)

    def test_get_version_flags_dirty_build(self) -> None:
        response = SpiFrame(message_type=MessageType.VERSION, seq=42,
                            payload=build_version_payload(build_flags=0x01)).encode()
        bus = SpiBus(SpiBusConfig(), backend=FakeBackend(response))
        bus.open()

        version = SpiDevice(bus).get_version(seq=7)

        self.assertTrue(version.is_dirty_build)
        self.assertIn('-dirty', version.summary())

    def test_get_version_gives_up_when_no_version_frame_arrives(self) -> None:
        bus = SpiBus(SpiBusConfig(), backend=FakeBackend())
        bus.open()

        with self.assertRaises(TimeoutError):
            SpiDevice(bus).get_version(seq=7, max_transactions=3)

    def test_get_version_tolerates_pipelined_response_delay(self) -> None:
        """The reply is staged after the request is clocked in, so it lands later."""
        backend = PipelinedFakeBackend(delay_transactions=2)
        bus = SpiBus(SpiBusConfig(), backend=backend)
        bus.open()

        version = SpiDevice(bus).get_version(seq=7)

        self.assertEqual(version.response_to_seq, 7)
        self.assertEqual(version.firmware_version, '0.1.0')
        self.assertGreater(backend.transfers, 1)

    def test_get_version_tolerates_a_corrupted_transfer(self) -> None:
        """A single garbled response mid-retry must not abort get_version.

        On the bench, an unpaced transfer can come back with a shifted or
        zeroed frame (invalid magic/CRC); the firmware still answers a
        retried request, so this should be treated as "not yet", not fatal.
        """
        class FlakyBackend:
            def __init__(self) -> None:
                self.calls = 0

            def open(self, config: SpiBusConfig) -> None:
                return None

            def transfer(self, tx_data: bytes) -> bytes:
                self.calls += 1
                if self.calls == 2:
                    return b'\xff' * 512  # garbage: bad magic
                return SpiFrame(message_type=MessageType.VERSION, seq=self.calls,
                                payload=build_version_payload(response_to_seq=7)).encode()

        bus = SpiBus(SpiBusConfig(), backend=FlakyBackend())
        bus.open()

        version = SpiDevice(bus).get_version(seq=7, retry_delay_s=0)

        self.assertEqual(version.response_to_seq, 7)

    def test_get_version_tolerates_corruption_on_the_initial_send(self) -> None:
        """The very first transfer (sending the GET_VERSION request itself)
        can also come back corrupted; that call's result is discarded
        either way, so a decode failure there must not propagate either."""
        class FlakyFirstCallBackend:
            def __init__(self) -> None:
                self.calls = 0

            def open(self, config: SpiBusConfig) -> None:
                return None

            def transfer(self, tx_data: bytes) -> bytes:
                self.calls += 1
                if self.calls == 1:
                    return b'\xff' * 512  # garbage: bad magic, on the request-sending transfer itself
                return SpiFrame(message_type=MessageType.VERSION, seq=self.calls,
                                payload=build_version_payload(response_to_seq=7)).encode()

        bus = SpiBus(SpiBusConfig(), backend=FlakyFirstCallBackend())
        bus.open()

        version = SpiDevice(bus).get_version(seq=7, retry_delay_s=0)

        self.assertEqual(version.response_to_seq, 7)

    def test_restarted_host_does_not_reuse_earlier_sequences(self) -> None:
        """The firmware keeps its accepted-sequence high-water mark until it is
        power-cycled and refuses anything not strictly newer, so a fresh host
        process must not restart its counter where an earlier one began."""
        bus = SpiBus(SpiBusConfig(), backend=FakeBackend())
        bus.open()

        first_run = [SpiDevice(bus).next_sequence() for _ in range(5)]
        second_run_start = SpiDevice(bus).next_sequence()

        self.assertGreater(second_run_start, max(first_run))

    def test_sequence_seed_fits_the_wire_field(self) -> None:
        seed = initial_sequence()
        self.assertGreater(seed, 0)  # zero means "no correlation", so it is skipped
        self.assertLess(seed, 1 << 32)

    def test_get_version_reports_bad_sequence_rejection(self) -> None:
        """A NACK naming our own request must surface its cause; returning a
        bare timeout hides the one fact that explains the failure."""
        nack = SpiFrame(message_type=MessageType.NACK, seq=3,
                        payload=struct.pack('<BBHII', 1, 0x14, 5, 7, 0)).encode()
        bus = SpiBus(SpiBusConfig(), backend=FakeBackend(nack))
        bus.open()

        with self.assertRaises(RuntimeError) as caught:
            SpiDevice(bus).get_version(seq=7, max_transactions=3, retry_delay_s=0)

        self.assertIn('BAD_SEQUENCE', str(caught.exception))

    def test_get_version_ignores_nack_for_a_different_request(self) -> None:
        nack = SpiFrame(message_type=MessageType.NACK, seq=3,
                        payload=struct.pack('<BBHII', 1, 0x14, 5, 999, 0)).encode()
        bus = SpiBus(SpiBusConfig(), backend=FakeBackend(nack))
        bus.open()

        with self.assertRaises(TimeoutError):
            SpiDevice(bus).get_version(seq=7, max_transactions=3, retry_delay_s=0)

    def test_get_version_ignores_version_frame_for_another_request(self) -> None:
        stale = SpiFrame(message_type=MessageType.VERSION, seq=1,
                         payload=build_version_payload(response_to_seq=999)).encode()
        bus = SpiBus(SpiBusConfig(), backend=FakeBackend(stale))
        bus.open()

        with self.assertRaises(TimeoutError):
            SpiDevice(bus).get_version(seq=7, max_transactions=3)


if __name__ == '__main__':
    unittest.main()
