"""DATA_READY GPIO watcher for the Raspberry Pi host (SD-17).

DATA_READY is a level signal, not a pulse (SPI_SYSTEM_INTERFACE.md section
7): the STM32 holds it high from the moment a frame is armed until the host
consumes it, so waiting for it means checking the current level before
waiting for a fresh edge, not only watching for edges.

The physical pin is GPIO25 (BCM numbering), header pin 22, wired to the
STM32's PA8 (README.md, RASPBERRY_PI_BRINGUP_V1.md E1). This is a harness
assignment picked and wired for SD-17, not yet an electrically validated one
(SPI_SYSTEM_INTERFACE.md section 16 acceptance is outstanding). Using it to
pace the host is a bench aid, not a claim that the interrupt path itself has
been accepted.

Uses libgpiod v1 (the `python3-libgpiod` package on Ubuntu 24.04 / this
kernel; confirmed against gpiod 1.6.3, which exposes `gpiod.Chip` and
`Line.event_wait`, not the v2 `gpiod.request_lines` API). Import is lazy so
unit tests and non-Pi development do not require the package to be
installed, following the same pattern as `SpidevBackend` in `spi_bus.py`.

The Pi 5's 40-pin header GPIO controller is exposed as a different
`/dev/gpiochipN` depending on kernel: `gpiochip4` on the 6.8 raspi kernel
used here, `gpiochip0` on newer kernels (RASPBERRY_PI_BRINGUP_V1.md E2:
"GPIO chip numbering on the Pi 5 depends on the kernel"). This module
selects the chip by its `pinctrl-rp1` driver label instead of a hard-coded
chip number, per that document's instruction not to hard-code the chip.
"""

from __future__ import annotations

from typing import Optional, Protocol

RP1_CHIP_LABEL = 'pinctrl-rp1'
DEFAULT_DATA_READY_LINE = 25  # BCM/GPIO25, header pin 22 (SPI_SYSTEM_INTERFACE.md, README.md)
DEFAULT_CONSUMER = 'karetao-data-ready'


class DataReadyLike(Protocol):
    """Duck-typed interface the exchange session depends on, so tests can
    substitute a fake without a real GPIO chip."""

    def is_ready(self) -> bool:
        ...

    def wait_for_ready(self, timeout_s: float) -> bool:
        ...


def find_rp1_chip():
    """Locate the RP1 GPIO chip by driver label, not by chip number.

    Raises RuntimeError if no matching chip is found, since a caller asking
    for DATA_READY pacing has no useful fallback if the chip cannot be
    located; `gpiodetect` is the documented way to inspect what's present.
    """
    import gpiod

    for chip in gpiod.ChipIter():
        if chip.label == RP1_CHIP_LABEL:
            return chip
        chip.close()
    raise RuntimeError(
        f'no GPIO chip with label {RP1_CHIP_LABEL!r} found; '
        f'run `gpiodetect` on the Pi to inspect available chips')


class DataReadyWatcher:
    """Blocks until the STM32 asserts DATA_READY (armed-then-assert model).

    Requests the line with rising-edge detection and bias disabled (no
    internal pull; the STM32 drives the line push-pull per
    RASPBERRY_PI_BRINGUP_V1.md E1). `wait_for_ready` checks the current
    level first: if the signal is already asserted (staged before this call
    started waiting), it returns immediately rather than blocking for a new
    edge that already happened and will not repeat.
    """

    def __init__(self, line_offset: int = DEFAULT_DATA_READY_LINE,
                 consumer: str = DEFAULT_CONSUMER, chip=None) -> None:
        import gpiod

        self._gpiod = gpiod
        self._chip = chip if chip is not None else find_rp1_chip()
        self._owns_chip = chip is None
        self._line = self._chip.get_line(line_offset)
        self._line.request(
            consumer=consumer,
            type=gpiod.LINE_REQ_EV_RISING_EDGE,
            flags=gpiod.LINE_REQ_FLAG_BIAS_DISABLE,
        )

    def is_ready(self) -> bool:
        return bool(self._line.get_value())

    def wait_for_ready(self, timeout_s: float) -> bool:
        """Returns True once DATA_READY is (or becomes) asserted.

        False means the timeout elapsed with no assertion observed — the
        caller decides whether to clock anyway (falling back to the
        polling model) or treat it as a stall.
        """
        if self.is_ready():
            return True
        whole_seconds = int(timeout_s)
        nanoseconds = int((timeout_s - whole_seconds) * 1e9)
        if not self._line.event_wait(sec=whole_seconds, nsec=nanoseconds):
            return False
        self._line.event_read()  # drain the event so it is not seen again
        return self.is_ready()

    def close(self) -> None:
        self._line.release()
        if self._owns_chip:
            self._chip.close()

    def __enter__(self) -> 'DataReadyWatcher':
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
