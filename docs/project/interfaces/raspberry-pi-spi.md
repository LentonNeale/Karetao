# Raspberry Pi SPI Interface

This document is the Raspberry Pi-side companion to the ARM-owned SPI contracts.

## Hardware baseline

The Raspberry Pi is the SPI master and the STM32F405 SPI3 peripheral is the slave.
The selected Raspberry Pi SPI0 wiring is:

| Raspberry Pi physical pin | Signal | STM32 SPI3 |
| ---: | --- | --- |
| 19 | MOSI | PC12 MOSI |
| 21 | MISO | PC11 MISO |
| 23 | SCLK | PC10 SCK |
| 24 | CE0 / NSS | PA15 NSS |

Pins 19, 21 and 23 are the user-specified SPI data/clock pins. CE0 on physical pin 24 is used as the SPI chip-select because the STM32 SPI3 interface uses hardware NSS.

`DATA_READY` is intentionally not assigned a Raspberry Pi GPIO in this baseline because no Raspberry Pi GPIO number was supplied. The Pi transport therefore performs explicit SPI transfers when the application requests them; assigning a DATA_READY GPIO can be added later without changing the SPI wire format.

## Transport

The implementation uses Linux `spidev` with:

- `/dev/spidev0.0`;
- SPI mode 0;
- 8 bits per word;
- maximum configured clock 5 MHz;
- fixed 512-byte full-duplex transfers.

A logical frame may be shorter than 512 bytes. The remaining bytes in the transport transaction are zero padding. The CRC covers only the logical frame header and payload, exactly as defined by `docs/protocols/spi-contract.md`.

The STM32 stages the response before the Pi clocks the transaction. A transaction carries a request from the Pi and the response staged before that request; the request is validated after DMA completion and the next response is then staged. This is the canonical pipelined request/response model.

## Software

The Pi implementation is split into:

- `src/spi/spi_bus.py` — Linux `spidev` backend and fixed-size transfer wrapper;
- `src/spi/spi_protocol.py` — explicit frame serialization, deserialization and CRC;
- `src/spi/spi_device.py` — high-level device access.

The `SpiBus` backend remains injectable, so protocol and device tests do not require Raspberry Pi hardware or the `spidev` package.

## Bring-up

Install the target image's `spidev` Python package and enable SPI0. Confirm `/dev/spidev0.0` exists before running the device interface.

Start at 5 MHz or below. The 5 MHz value is the current integration ceiling in the STM32 contract; final acceptance still requires target hardware evidence for signal integrity, DMA timing, NSS behaviour and complete 512-byte transactions.

## Validation requirements

Before treating SPI as closed, verify on target hardware:

1. MOSI/MISO/SCLK/NSS connectivity using the physical mapping above.
2. Mode 0 timing at the selected clock.
3. Complete 512-byte DMA transactions without overrun/underrun.
4. Correct CRC and sequence/correlation behaviour.
5. NSS abort/error recovery.
6. DATA_READY behaviour if a Raspberry Pi GPIO is subsequently assigned.
7. Repeated transactions under sustained load.
