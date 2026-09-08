# RaspberryPi_Sensor_Hub

Raspberry Pi implementation and documentation for sensor hub applications. Works alongside `Arm_Sensor_Hub`.

## Canonical Documentation

Shared monorepo documentation now lives under the root `docs/` tree:

- [Architecture](../docs/architecture.md)
- [Development workflow](../docs/development.md)
- [SPI transport contract](../docs/protocols/spi-contract.md)
- [SPI payload schema](../docs/protocols/spi-payload-schema.md)
- [SPI service contract](../docs/interfaces/spi-service-contract.md)
- [Raspberry Pi SPI scaffold](../docs/interfaces/raspberry-pi-spi.md)

A local compatibility pointer is kept at [docs/spi.md](docs/spi.md).

## Current Scaffold

The subtree now includes a minimal Python SPI scaffold under `src/spi/` and placeholder contract tests under `tests/spi/`.
The implementation intentionally leaves hardware-specific Linux SPI and GPIO choices as TODO items until the ARM contract gates are finalized.
