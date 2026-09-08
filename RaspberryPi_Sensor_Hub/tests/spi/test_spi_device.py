import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from spi.spi_bus import SpiBus, SpiBusConfig
from spi.spi_device import SpiDevice
from spi.spi_protocol import MessageType, SpiFrame


class FakeBackend:
    def __init__(self) -> None:
        self.last_request = b''
        self._response = SpiFrame(message_type=MessageType.ACK, seq=99, payload=b'\x01\x11\x00\x00\x2A\x00\x00\x00\x00\x00\x00\x00').encode()

    def open(self, config: SpiBusConfig) -> None:
        self.config = config

    def transfer(self, tx_data: bytes) -> bytes:
        self.last_request = tx_data
        return self._response

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


if __name__ == '__main__':
    unittest.main()
