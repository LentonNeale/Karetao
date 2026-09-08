# Arm Sensor Hub Documentation

This folder contains ARM-specific engineering documentation and compatibility pointers for topics that are now canonicalized at the monorepo root.

## Canonical root docs

| Document | Purpose |
| --- | --- |
| [../../docs/architecture.md](../../docs/architecture.md) | Monorepo architecture and runtime flow. |
| [../../docs/development.md](../../docs/development.md) | Monorepo development workflow and validation paths. |
| [../../docs/hardware/arm-sensor-hub-baseline.md](../../docs/hardware/arm-sensor-hub-baseline.md) | ARM hardware/firmware baseline, pinout, and implementation snapshot. |
| [../../docs/protocols/spi-contract.md](../../docs/protocols/spi-contract.md) | Raspberry Pi to STM32 SPI framing, DATA_READY, coherency, timestamps, and time synchronization. |
| [../../docs/protocols/spi-payload-schema.md](../../docs/protocols/spi-payload-schema.md) | Serialized payload layouts for snapshots, events, diagnostics, and synchronization. |
| [../../docs/interfaces/spi-service-contract.md](../../docs/interfaces/spi-service-contract.md) | SPI3 service lifecycle, DMA ownership, DATA_READY implementation, and transport recovery. |

## ARM-specific local docs

| Document | Purpose |
| --- | --- |
| [CONTRACT_STATUS.md](CONTRACT_STATUS.md) | Ownership, implementation status, dependencies, and next action for every project contract. |
| [LIFECYCLE_CONTRACT.md](LIFECYCLE_CONTRACT.md) | System-wide lifecycle states, transitions, dependencies, safety rules, and reusable contract template. |
| [CONTRACT_V1_FREEZE.md](CONTRACT_V1_FREEZE.md) | Cross-contract decisions and implementation gates before SPI/snapshot code. |
| [CAN_SERVICE_CONTRACT.md](CAN_SERVICE_CONTRACT.md) | CAN/MKS transport ownership, lifecycle gating, polling, diagnostics, and open transport policy. |
| [SNAPSHOT_COHERENCY_CONTRACT.md](SNAPSHOT_COHERENCY_CONTRACT.md) | Sensor/CAN snapshot assembly, buffer ownership, DMA safety, and overwrite policy. |
| [I2C_MANAGER_CONTRACT.md](I2C_MANAGER_CONTRACT.md) | I2C manager responsibilities and HAL boundary. |
| [MULTI_SENSOR_CONTRACT.md](MULTI_SENSOR_CONTRACT.md) | Six-channel AS5600 topology and sensor model assumptions. |
| [TIMESTAMP_SYNC_CONTRACT.md](TIMESTAMP_SYNC_CONTRACT.md) | Time-domain and synchronization rules beyond the shared SPI contract. |
| [CALIBRATION_CONTRACT.md](CALIBRATION_CONTRACT.md) | Calibration record design and validation. |
| [JOINT_MAPPING_CONTRACT.md](JOINT_MAPPING_CONTRACT.md) | Joint-to-sensor and joint-to-motor identity mapping. |
| [ERROR_HANDLING_STRATEGY.md](ERROR_HANDLING_STRATEGY.md) | Service-fault handling and lifecycle escalation strategy. |
| [HEALTH_MONITOR_CONTRACT.md](HEALTH_MONITOR_CONTRACT.md) | Health aggregation and reporting. |
| [BUILD_CONTRACT.md](BUILD_CONTRACT.md) | Developer environment and reproducible ARM build expectations. |
| [MOTOR_SERVICE_CONTRACT.md](MOTOR_SERVICE_CONTRACT.md) | Future joint/motor abstraction contract. |
| [APP_OVERVIEW.md](APP_OVERVIEW.md) | Original application-level project objectives and scope. |
| [OnboardingDocs/README.md](OnboardingDocs/README.md) | Guided onboarding pack with root-doc links. |

## Related Module Documentation

- [MksServo protocol library](../Middlewares/Third_Party/MksServo/README.md)
