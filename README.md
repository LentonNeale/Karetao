# Karetao

Monorepo for the Karetao robotic arm platform: STM32 control/comms firmware, Raspberry Pi host-side integration, ROS 2 components, and shared project scaffolding.

## Repository Layout

- `Arm_Sensor_Hub/` — STM32 firmware and hardware-facing implementation.
- `RaspberryPi_Sensor_Hub/` — Raspberry Pi host-side implementation and integration scaffold.
- `Documentation/` — Karetao system documentation authority.
- `shared/` — shared protocols, libraries, and test vectors.

## Documentation Source of Truth

Karetao system-level documentation is authoritative under [`Documentation/`](Documentation/).

Use [`Documentation/00_INDEX.md`](Documentation/00_INDEX.md) as the entry point for the documentation framework.

## Component authority

Karetao defines the integrated system requirements, architecture, interfaces, safety, configuration, verification status and system-level component roles.

The component repositories remain authoritative for implementation details and component-level verification:

- Arm Sensor Hub implementation: `Arm_Sensor_Hub/`
- Raspberry Sensor Hub implementation: `RaspberryPi_Sensor_Hub/`

A component implementation document may explain how a Karetao requirement is implemented, but does not redefine the system requirement.
## Mandatory documentation authority rule

**The Karetao Documentation authority framework is the only project documentation authority framework.** Use `Documentation/**` and its authority model for Karetao system-level documentation and documentation governance.
