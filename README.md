# Arm Sensor Hub

STM32F405RGT6 firmware project generated with STM32CubeMX and built with CMake.

The firmware acts as a sensor hub on STM32F405:
- acquires sensor data from I2C (AS5600 via TCA9548A multiplexer),
- exchanges motor/control telemetry over CAN,
- publishes data to a Raspberry Pi over SPI (slave),
- uses DATA_READY signaling for host-side synchronization.

## Documentation

- **Technical reference:** [Documentation/PROJECT_BASELINE.md](Documentation/PROJECT_BASELINE.md) — architecture, implementation status, runtime flow, MCU/clock, pinout, and API reference.
- **Contracts index:** [Documentation/README.md](Documentation/README.md) — system contracts and current ownership/implementation status ([Documentation/CONTRACT_STATUS.md](Documentation/CONTRACT_STATUS.md)).
- **Onboarding:** [Documentation/OnboardingDocs/README.md](Documentation/OnboardingDocs/README.md) — guided intern onboarding pack.

## Build

Use the existing preset-based build flow:

```bash
cmake --preset Debug
cmake --build --preset Debug
```
