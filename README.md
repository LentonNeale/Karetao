# Karetao

Monorepo for the Karetao robotic arm platform: STM32 control/comms firmware, Raspberry Pi host-side integration, and shared monorepo scaffolding.

## Repository Layout

- `Arm_Sensor_Hub/` — STM32 firmware, host tests, and ARM-specific engineering contracts.
- `RaspberryPi_Sensor_Hub/` — Raspberry Pi host-side code and SPI integration scaffold.
- `docs/` — canonical documentation source of truth for monorepo architecture, development workflow, interfaces, and protocols.
- `shared/` — placeholder location for shared protocols, libraries, and test vectors.

## Documentation Source of Truth

The root `docs/` tree is the canonical documentation location for content shared across subtrees.
Use these entry points first:

- [Architecture](docs/architecture.md)
- [Development workflow](docs/development.md)
- [ARM hardware baseline](docs/hardware/arm-sensor-hub-baseline.md)
- [SPI transport contract](docs/protocols/spi-contract.md)
- [SPI payload schema](docs/protocols/spi-payload-schema.md)
- [SPI service contract](docs/interfaces/spi-service-contract.md)
- [Raspberry Pi SPI scaffold](docs/interfaces/raspberry-pi-spi.md)

Subtree-local copies that used to hold these topics now contain short compatibility stubs that point back to `docs/`.
