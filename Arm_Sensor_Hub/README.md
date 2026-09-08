# Arm Sensor Hub

STM32F405RGT6 firmware project generated with STM32CubeMX and built with CMake.

The firmware acts as a sensor hub on STM32F405:
- acquires sensor data from I2C (AS5600 via TCA9548A multiplexer),
- exchanges motor/control telemetry over CAN,
- publishes data to a Raspberry Pi over SPI (slave),
- uses DATA_READY signaling for host-side synchronization.

## Canonical Documentation

Shared architecture, development workflow, and SPI interface/protocol guidance now live in the monorepo root `docs/` tree:

- [Architecture](../docs/architecture.md)
- [Development workflow](../docs/development.md)
- [ARM hardware baseline](../docs/hardware/arm-sensor-hub-baseline.md)
- [SPI transport contract](../docs/protocols/spi-contract.md)
- [SPI payload schema](../docs/protocols/spi-payload-schema.md)
- [SPI service contract](../docs/interfaces/spi-service-contract.md)

ARM-specific contract inventory that remains local to this subtree:

- [Documentation/README.md](Documentation/README.md)
- [Documentation/CONTRACT_STATUS.md](Documentation/CONTRACT_STATUS.md)
- [Documentation/LIFECYCLE_CONTRACT.md](Documentation/LIFECYCLE_CONTRACT.md)

## Build

Use the existing preset-based build flow:

```bash
cd Arm_Sensor_Hub
cmake --preset Debug
cmake --build --preset Debug
```
