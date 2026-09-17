# RaspberryPi_Sensor_Hub

Raspberry Pi implementation and documentation for sensor hub applications. Works alongside `Arm_Sensor_Hub`.

## Canonical Documentation

Shared monorepo documentation now lives under the root `docs/` tree:

- [Architecture](../docs/architecture.md)
- [Development workflow](../docs/development.md)
- [SPI transport contract](../docs/protocols/spi-contract.md)
- [SPI payload schema](../docs/protocols/spi-payload-schema.md)
- [SPI service contract](../docs/interfaces/spi-service-contract.md)
- [Raspberry Pi SPI interface](../docs/interfaces/raspberry-pi-spi.md)

A local compatibility pointer is kept at [docs/spi.md](docs/spi.md).

## Current SPI Implementation

The subtree includes the production Linux `spidev` backend under `src/spi/` and host-test coverage under `tests/spi/`.

The current backend configuration is `/dev/spidev0.0`, SPI mode 0, 8 bits per word, a configured maximum of 5 MHz, and fixed 512-byte full-duplex transfers. `SpiBus` keeps the backend injectable so protocol/device tests do not require Raspberry Pi hardware or the `spidev` package.

The 5 MHz value is the current integration ceiling, not hardware approval. Live Raspberry Pi <-> STM32 transactions, DATA_READY GPIO integration, NSS behavior, DMA timing, signal integrity, and sustained repeated-transfer acceptance remain open hardware gates.
