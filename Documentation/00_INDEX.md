# Karetao Documentation

This directory defines the **Karetao system documentation framework**.

The framework establishes Karetao as the authority for system-level documentation while defining the boundary between system documentation, component implementation documentation, external documentation, and verification evidence.

 > **Framework status:** Active reconciliation/refactor. The authoritative Karetao system documentation is being established in `Documentation/**` from the Phase 2 authority audit. Legacy `docs/project/**` remains source material where not yet fully reconciled.

## Mandatory authority notice

**Use the Karetao Documentation authority framework as the only project documentation authority framework.** For Karetao system-level documentation and documentation governance, the authoritative framework is `Documentation/**` as defined by `01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md`. Do not treat `docs/project/**` as an alternative, parallel, or competing authority framework.

All content under `docs/project/**` is **reference/source material only during this transition**. It is being retained solely to support reconciliation, provenance, and evidence review. Once the Karetao documentation is finalized, `docs/project/**` is intended to be removed; it must not be used as the current source of truth in the interim.

## Authority

[`DOCUMENTATION_AUTHORITY_MODEL.md`](01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md) is the normative authority model.

The framework uses separate authority domains. Authority is determined by subject ownership, not by a universal top-down hierarchy:

```text
Karetao
    owns Karetao system requirements and system-level definitions

Arm_Sensor_Hub
    owns Arm Sensor Hub implementation documentation

Raspberry_Sensor_Hub
    owns Raspberry Sensor Hub implementation documentation

Vendor/external documentation
    owns externally defined equipment/protocol behaviour

Verification records
    provide evidence
```

A document's physical location does not by itself make it authoritative. Authority is determined by the subject owned by the relevant repository, external authority, or verification process.

## Framework governance

The following root-level documents govern the documentation framework itself rather than defining Karetao system behaviour:

- `05_REFACTORING_RULES.md` — rules governing the future documentation migration and reconciliation.
- `06_IMPLEMENTATION_CHECKLIST.md` — checklist for implementing and reviewing the documentation framework.

These are governance/process documents. They are not competing system requirements and do not override or replace authoritative system-level documentation.

## Documentation structure

| Section | Purpose |
|---|---|
| [`01_SYSTEM/`](01_SYSTEM/) | System requirements, architecture, timing, synchronization, overview, and documentation authority |
| [`02_INTERFACES/`](02_INTERFACES/) | System-level interface definitions and contracts |
| [`03_COMPONENTS/`](03_COMPONENTS/) | Karetao system-level component definitions and the component documentation contract |
| [`04_SAFETY/`](04_SAFETY/) | System safety requirements and related documentation |
| [`05_VERIFICATION/`](05_VERIFICATION/) | System-level verification requirements, plans, matrices, and evidence references |
| [`06_CONFIGURATION/`](06_CONFIGURATION/) | System-level configuration requirements and controlled configuration information |
| [`07_DECISIONS/`](07_DECISIONS/) | Authoritative system decisions and decision records |
| [`99_ARCHIVE/`](99_ARCHIVE/) | Historical and non-normative Karetao material |

The framework deliberately retains these top-level sections without introducing additional documentation categories.

## System authority

Karetao is authoritative for:

- system requirements;
- system architecture;
- system-level interfaces;
- system timing and synchronization;
- system safety requirements;
- system-level configuration requirements;
- system verification requirements;
- system integration requirements;
- system-level component roles and responsibilities.

The component repositories do not redefine these system requirements.

## Component ownership boundary

[`03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md`](03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md) defines the integration contract.

The Karetao repository owns the system-level definition of components, including:

- [`ARM_SENSOR_HUB.md`](03_COMPONENTS/ARM_SENSOR_HUB.md);
- [`RASPBERRY_SENSOR_HUB.md`](03_COMPONENTS/RASPBERRY_SENSOR_HUB.md).

The component repositories own implementation documentation.

For example:

```text
Karetao
└── 02_INTERFACES/
        └── CAN_SYSTEM_INTERFACE.md
              │
              │ defines system requirement
              ▼
Arm_Sensor_Hub
└── Documentation/
        └── CAN implementation documentation
              │
              │ implements
              ▼
External controller/protocol
```

The same boundary applies conceptually to CAN, SPI, HOST, TIME, and future system interfaces.

## Verification boundary

System verification follows:

```text
Karetao system requirement
        ↓
Responsible component(s)
        ↓
Component implementation
        ↓
Component verification evidence
        ↓
Integration evidence
        ↓
Karetao system verification
```

Component verification does not automatically constitute system verification.

[`05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`](05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md) is the authoritative location for Karetao system-level verification status.

`SYSTEM_VERIFIED` means that the result has been accepted at the Karetao system level. Component repositories may document component-level verification evidence, but component verification alone does not establish `SYSTEM_VERIFIED`.

## Archive boundary

[`99_ARCHIVE/`](99_ARCHIVE/) contains historical/non-normative material such as superseded specifications, historical decisions, sprint reports, conversations, and obsolete planning material.

Archived content must never silently override current authoritative documentation.

## Refactoring sequence

The framework is intentionally established before documentation migration.

The intended sequence is:

1. Establish Karetao authority model.
2. Establish component documentation model.
3. Review and approve the framework.
4. Inventory existing documentation.
5. Classify documents.
6. Determine authority of each document and significant statement.
7. Refactor Karetao system documentation.
8. Refactor component documentation.
9. Establish cross-repository references.
10. Archive superseded material.
11. Remove genuinely redundant material.
12. Verify links and authority boundaries.

**The Phase 2 authority audit has approved the transition into subject-based documentation refactoring.** Existing Karetao system content is being reconciled into the authority domains below. Component implementation authority remains in the component repositories.
