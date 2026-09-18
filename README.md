# Karetao

Monorepo for the Karetao robotic arm platform: STM32 control/comms firmware, Raspberry Pi host-side integration, ROS 2 components, and shared project scaffolding.

## Repository Layout

- `Arm_Sensor_Hub/` — STM32 firmware and hardware-facing implementation.
- `RaspberryPi_Sensor_Hub/` — Raspberry Pi host-side implementation and integration scaffold.
- `Documentation/` — current Karetao system documentation authority.
- `docs/project/` — legacy/transitional project documentation retained as reconciliation source material where applicable.
- `shared/` — shared protocols, libraries, and test vectors.

## Documentation Source of Truth

Karetao system-level documentation is authoritative under [`Documentation/`](Documentation/).

Use [`Documentation/00_INDEX.md`](Documentation/00_INDEX.md) as the entry point for the current documentation framework.

The `docs/project/` tree is legacy/transitional source material during reconciliation. Its directory location does not make it authoritative. Archived material under `docs/project/archive/**` is historical and excluded from current authority determination.

## Component authority

Karetao defines the integrated system requirements, architecture, interfaces, safety, configuration, verification status and system-level component roles.

The component repositories remain authoritative for implementation details and component-level verification:

- Arm Sensor Hub implementation: `Arm_Sensor_Hub/`
- Raspberry Sensor Hub implementation: `RaspberryPi_Sensor_Hub/`

A component implementation document may explain how a Karetao requirement is implemented, but does not redefine the system requirement.
## Mandatory documentation authority rule

**The Karetao Documentation authority framework is the only project documentation authority framework to use.** Use `Documentation/**` and its authority model for Karetao system-level documentation and documentation governance. Do not use `docs/project/**` as a competing or parallel authority framework.

All files in `docs/project/**` are **reference/source material only** during this transition. They are retained for reconciliation, provenance, and evidence review, but are not current authority. Once the Karetao documentation is finalized, the `docs/project/**` tree is intended to be removed.
