"""SPI bus lifecycle scaffold.

TODO: confirm the production Linux SPI backend (`spidev`, `python-periphery`, or a custom bridge)
and final DATA_READY integration strategy from docs/interfaces/raspberry-pi-spi.md.
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
    device: str = '/dev/spidevTODO'
    mode: int = 0
    bits_per_word: int = 8
    max_speed_hz: Optional[int] = None
    data_ready_gpio: Optional[int] = None


class SpiBus:
    def __init__(self, config: SpiBusConfig, backend: Optional[SpiBackend] = None) -> None:
        self.config = config
        self.backend = backend
        self._is_open = False

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        if self._is_open:
            return
        if self.backend is not None:
            self.backend.open(self.config)
        self._is_open = True

    def transfer(self, tx_data: bytes) -> bytes:
        if not self._is_open:
            raise RuntimeError('SPI bus must be opened before transfer')
        if self.backend is None:
            raise NotImplementedError('TODO: inject a concrete Raspberry Pi SPI backend')
        return self.backend.transfer(bytes(tx_data))

    def close(self) -> None:
        if not self._is_open:
            return
        try:
            if self.backend is not None:
                self.backend.close()
        finally:
            self._is_open = False
