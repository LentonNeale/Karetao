# Arm Sensor Hub Documentation

This folder contains the project-level engineering documentation for onboarding, architecture, and interface contracts.

## Documents

| Document | Purpose |
| --- | --- |
| [Project Baseline](PROJECT_BASELINE.md) | Current architecture, implementation status, runtime flow, and API reference. |
| [Lifecycle Contract](LIFECYCLE_CONTRACT.md) | System-wide lifecycle states, transitions, dependencies, safety rules, and reusable contract template. |
| [SPI Host Contract](SPI_CONTRACT.md) | Raspberry Pi to STM32 SPI framing, DATA_READY, coherency, timestamps, and time synchronization. |
| [Contract Status](CONTRACT_STATUS.md) | Ownership, implementation status, dependencies, and next action for every project contract. |
| [Contract v1.0 Freeze](CONTRACT_V1_FREEZE.md) | Cross-contract decisions and implementation gates before SPI/snapshot code. |
| [CAN Service Contract](CAN_SERVICE_CONTRACT.md) | CAN/MKS transport ownership, lifecycle gating, polling, diagnostics, and open transport policy. |
| [SPI Payload Schema](SPI_PAYLOAD_SCHEMA.md) | Draft serialized payload layouts for snapshots, events, diagnostics, and synchronization. |
| [Snapshot Coherency Contract](SNAPSHOT_COHERENCY_CONTRACT.md) | Sensor/CAN snapshot assembly, buffer ownership, DMA safety, and overwrite policy. |
| [SPI Service Contract](SPI_SERVICE_CONTRACT.md) | SPI3 service lifecycle, DMA ownership, DATA_READY implementation, and transport recovery. |
| [Safety Release Checklist](SAFETY_RELEASE_CHECKLIST.md) | Energized-motion release blockers, evidence classes, owners, and required artifacts. |
| [Application Overview](APP_OVERVIEW.md) | Original application-level project objectives and scope. |

## Documentation Rules

- `README.md` at the repository root remains the repository entry point and contains the current project snapshot.
- Documents in this folder are authoritative for project architecture and system contracts.
- Protocol-specific documentation remains beside its implementation when it describes a reusable third-party module, such as `Middlewares/Third_Party/MksServo/README.md`.
- Generated files, build output, editor configuration, and temporary planning artifacts are not project documentation.

## Related Module Documentation

- [MksServo protocol library](../Middlewares/Third_Party/MksServo/README.md)
- [MksServo source attachment](../TEMP/MksServo/README.md)

## Recommended Reading Order

1. [Project Baseline](PROJECT_BASELINE.md)
2. [Lifecycle Contract](LIFECYCLE_CONTRACT.md)
3. [SPI Host Contract](SPI_CONTRACT.md)
4. [Contract Status](CONTRACT_STATUS.md)
5. [Contract v1.0 Freeze](CONTRACT_V1_FREEZE.md)
6. [CAN Service Contract](CAN_SERVICE_CONTRACT.md)
7. [SPI Payload Schema](SPI_PAYLOAD_SCHEMA.md)
8. [Snapshot Coherency Contract](SNAPSHOT_COHERENCY_CONTRACT.md)
9. [SPI Service Contract](SPI_SERVICE_CONTRACT.md)
10. [Safety Release Checklist](SAFETY_RELEASE_CHECKLIST.md)
11. [Application Overview](APP_OVERVIEW.md)
