> **Transitional status:** This legacy project documentation index is retained as source material and migration provenance. It is **not** the current Karetao documentation authority. Current Karetao system documentation is authoritative under [Documentation/](../../Documentation/), beginning with [Documentation/00_INDEX.md](../../Documentation/00_INDEX.md). Directory location does not establish authority.

# Karetao Project Documentation

This directory contains the legacy project-documentation organization retained during the Karetao documentation refactor.

It remains useful as source material and provenance while system-level content is reconciled into the current `Documentation/**` framework. It must not be treated as a competing source of truth.

## Document table

| Area | Document | Status | Refactor disposition |
|---|---|---|---|
| System | [architecture.md](system/architecture.md) | Legacy source | System-level architecture reconciled into `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md`; component implementation details remain component-owned. |
| System | [development.md](system/development.md) | Legacy source | Retain for reconciliation; do not promote automatically to system authority. |
| System | [TODO_List.md](system/TODO_List.md) | Legacy source | Retain as project/process source material; unresolved work is not a system requirement by itself. |
| System | [Open_Items_List.md](Open_Items_List.md) | Legacy source | Retain as source for unresolved questions; unresolved questions are not silently converted into requirements. |
| System | [SYSTEM_DECISIONS.md](SYSTEM_DECISIONS.md) | Transitional decision provenance | SD-01 through SD-26 are reconciled into `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` and `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`; this register remains for provenance during transition. |
| Hardware | [arm-sensor-hub-baseline.md](hardware/arm-sensor-hub-baseline.md) | Legacy mixed source | Karetao system/component-role content is reconciled into `Documentation/03_COMPONENTS/`; implementation content remains Arm Sensor Hub-owned. |
| Interfaces | [raspberry-pi-spi.md](interfaces/raspberry-pi-spi.md) | Legacy mixed source | System SPI requirements are reconciled into `Documentation/02_INTERFACES/`; Raspberry/STM32 implementation details remain component-owned. |
| Interfaces | [spi-service-contract.md](interfaces/spi-service-contract.md) | Legacy mixed source | Separate system interface from component implementation content according to the Phase 2 authority audit. |
| Protocols | [spi-contract.md](protocols/spi-contract.md) | Legacy mixed source | System-visible SPI contract content is reconciled into `Documentation/02_INTERFACES/`; implementation details remain component-owned. |
| Protocols | [spi-payload-schema.md](protocols/spi-payload-schema.md) | Legacy mixed source | System payload semantics are reconciled as system interface content; serializer/decoder implementation remains component-owned. |
| Firmware | `firmware/*` | Legacy mixed source | System-facing clauses are reconciled into Karetao authority documents; STM32 implementation, configuration and component evidence remain Arm-owned. |
| Operations | [RASPBERRY_PI_BRINGUP_V0.1.md](operations/RASPBERRY_PI_BRINGUP_V0.1.md) | Legacy component/integration source | Retain as source material; do not treat component procedure as Karetao system authority. |

## Archive

`archive/` contains superseded, deprecated, historical, or planning-only material retained for traceability. It is excluded from current authority determination and ordinary migration.

## Authority

The current Karetao system documentation authority is `Documentation/**`.

Karetao owns system requirements, architecture, system interfaces, timing and synchronization, safety requirements, system configuration requirements, system integration requirements, system-level verification status, and system-level component roles.

Component repositories remain authoritative for their own implementation documentation. External/vendor sources remain authoritative for externally defined equipment and protocol behaviour. Verification records provide evidence and do not redefine requirements.

## Refactor status

The Phase 2 authority audit is the governing source for disposition of the legacy content. Mixed documents are not moved mechanically: significant statements are separated by subject authority, supported information and provenance are retained, duplication is removed only where justified, and unresolved conflicts remain explicit.

This legacy directory is therefore a **source/provenance area during transition**, not the current Karetao source of truth.