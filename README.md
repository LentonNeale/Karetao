# Karetao

Monorepo for the Karetao robotic arm platform: STM32 control/comms firmware, Raspberry Pi host-side integration, ROS 2 components, and shared project scaffolding.

## Repository Layout

- `Arm_Sensor_Hub/` — STM32 firmware and hardware-facing implementation.
- `RaspberryPi_Sensor_Hub/` — Raspberry Pi host-side implementation and integration scaffold.
- `docs/project/` — canonical project documentation for system architecture, interfaces, protocols, firmware contracts, hardware, operations, and requirements.
- `shared/` — shared protocols, libraries, and test vectors.

## Documentation Source of Truth

All project-level engineering documentation is consolidated under `docs/project/`.

Start with [docs/project/README.md](docs/project/README.md). Superseded and historical material is retained under `docs/project/archive/`.

Former documentation paths may be retained as compatibility pointers; they are not authoritative.
