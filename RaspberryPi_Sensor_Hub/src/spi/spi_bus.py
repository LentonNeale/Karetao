"""Raspberry Pi SPI bus implementation.

The production path uses Linux spidev on SPI0 CE0. DATA_READY remains an
optional GPIO input. The harness candidate is GPIO25 (BCM numbering,
`gpiochip4` line 25 on the Ubuntu 24.04 kernel, header pin 22; see
RaspberryPi_Sensor_Hub/Documentation/README.md and RASPBERRY_PI_BRINGUP_V1.md
E1). This is a Raspberry Sensor Hub harness assignment, not a validated one:
SD-17's electrical and timing acceptance (SPI_SYSTEM_INTERFACE.md §16) has
not been performed. `data_ready_gpio` therefore still defaults to None below;
callers should not pass 25 as a production default until that acceptance is
recorded, since doing so would make interrupt-driven behaviour depend on an
unvalidated electrical path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


class SpiBackend(Protocol):
    def open(self, config: 'SpiBusConfig') -> None:
        ...

    def transfer(self, tx_data: bytes) -> bytes:
        ...

    def close(self) -> None:
        ...


@dataclass(frozen=True)
class SpiBusConfig:
    # Raspberry Pi physical pins: 19=MOSI, 21=MISO, 23=SCLK; CE0 is pin 24.
    device: str = '/dev/spidev0.0'
    mode: int = 0
    bits_per_word: int = 8
    max_speed_hz: int = 5_000_000
    data_ready_gpio: Optional[int] = None
    transfer_size: int = 512


class SpidevBackend:
    """Small production backend around Linux ``spidev``.

    Import is lazy so protocol/unit tests do not require the Raspberry Pi
    ``spidev`` package to be installed.
    """

    def __init__(self) -> None:
        self._spi = None

    def open(self, config: SpiBusConfig) -> None:
        if config.mode != 0:
            raise ValueError('SPI contract requires mode 0')
        if config.bits_per_word != 8:
            raise ValueError('SPI contract requires 8 bits per word')
        if config.transfer_size != 512:
            raise ValueError('SPI contract requires 512-byte transactions')

        try:
            import spidev
        except ImportError as exc:
            raise RuntimeError('spidev is required on the Raspberry Pi target') from exc

        bus, chip_select = _parse_spidev_device(config.device)
        spi = spidev.SpiDev()
        spi.open(bus, chip_select)
        spi.mode = config.mode
        spi.bits_per_word = config.bits_per_word
        spi.max_speed_hz = config.max_speed_hz
        self._spi = spi

    def transfer(self, tx_data: bytes) -> bytes:
        if self._spi is None:
            raise RuntimeError('SPI backend must be opened before transfer')
        if len(tx_data) != 512:
            raise ValueError('SPI transactions must be exactly 512 bytes')
        return bytes(self._spi.xfer2(list(tx_data)))

    def close(self) -> None:
        if self._spi is not None:
            self._spi.close()
            self._spi = None


def _parse_spidev_device(device: str) -> tuple[int, int]:
    prefix = '/dev/spidev'
    if not device.startswith(prefix):
        raise ValueError('SPI device must be /dev/spidev<bus>.<chip-select>')
    try:
        bus_text, cs_text = device[len(prefix):].split('.', 1)
        return int(bus_text), int(cs_text)
    except ValueError as exc:
        raise ValueError('invalid spidev device path') from exc


class SpiBus:
    def __init__(self, config: SpiBusConfig, backend: Optional[SpiBackend] = None) -> None:
        self.config = config
        self.backend = backend if backend is not None else SpidevBackend()
        self._is_open = False

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        if self._is_open:
            return
        self.backend.open(self.config)
        self._is_open = True

    def transfer(self, tx_data: bytes) -> bytes:
        if not self._is_open:
            raise RuntimeError('SPI bus must be opened before transfer')
        if len(tx_data) > self.config.transfer_size:
            raise ValueError('SPI request exceeds transfer size')
        padded = bytes(tx_data).ljust(self.config.transfer_size, b'\x00')
        return self.backend.transfer(padded)

    def close(self) -> None:
        if not self._is_open:
            return
        try:
            self.backend.close()
        finally:
            self._is_open = False
