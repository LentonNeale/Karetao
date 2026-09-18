# Karetao Documentation

This directory defines the **Karetao system documentation framework**.

The framework establishes Karetao as the authority for system-level documentation while defining the boundary between system documentation, component implementation documentation, external documentation, and verification evidence.

> **Framework status:** Preparatory. Existing documentation has not yet been migrated or refactored under this framework.

## Authority

[\`DOCUMENTATION_AUTHORITY_MODEL.md\`](01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md) is the normative authority model.

In summary:

\`\`\`text
Karetao
    ↓
System authority

Component repositories
    ↓
Component implementation authority

Vendor/external documentation
    ↓
External equipment/protocol authority

Verification records
    ↓
Evidence
\`\`\`

A document's physical location does not by itself make it authoritative. Authority is determined by subject ownership.

## Documentation structure

| Section | Purpose |
|---|---|
| [\`01_SYSTEM/\`](01_SYSTEM/) | System requirements, architecture, timing, synchronization, overview, and documentation authority |
| [\`02_INTERFACES/\`](02_INTERFACES/) | System-level interface definitions and contracts |
| [\`03_COMPONENTS/\`](03_COMPONENTS/) | Karetao system-level component definitions and the component documentation contract |
| [\`04_SAFETY/\`](04_SAFETY/) | System safety requirements and related documentation |
| [\`05_VERIFICATION/\`](05_VERIFICATION/) | System-level verification requirements, plans, matrices, and evidence references |
| [\`06_CONFIGURATION/\`](06_CONFIGURATION/) | System-level configuration requirements and controlled configuration information |
| [\`07_DECISIONS/\`](07_DECISIONS/) | Authoritative system decisions and decision records |
| [\`99_ARCHIVE/\`](99_ARCHIVE/) | Historical and non-normative Karetao material |

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

[\`03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md\`](03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md) defines the integration contract.

The Karetao repository owns the system-level definition of components, including:

- [\`ARM_SENSOR_HUB.md\`](03_COMPONENTS/ARM_SENSOR_HUB.md);
- [\`RASPBERRY_SENSOR_HUB.md\`](03_COMPONENTS/RASPBERRY_SENSOR_HUB.md).

The component repositories own implementation documentation.

For example:

\`\`\`text
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
\`\`\`

The same boundary applies conceptually to CAN, SPI, HOST, TIME, and future system interfaces.

## Verification boundary

System verification follows:

\`\`\`text
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
\`\`\`

Component verification does not automatically constitute system verification.

The eventual Karetao system verification matrix is intended to be the authoritative location for system-level verification status.

## Archive boundary

[\`99_ARCHIVE/\`](99_ARCHIVE/) contains historical/non-normative material such as superseded specifications, historical decisions, sprint reports, conversations, and obsolete planning material.

Archived content must never silently override current authoritative documentation.

## Refactoring sequence

The framework is intentionally established before documentation migration.

The intended sequence is:

1. Establish Karetao authority model.
2. Establish component documentation model.
3. Review and approve the framework.
4. Inventory existing documentation.
5. Classify documents.
6. Determine authority of each document.
7. Refactor Karetao system documentation.
8. Refactor component documentation.
9. Establish cross-repository references.
10. Archive superseded material.
11. Remove genuinely redundant material.
12. Verify links and authority boundaries.

**Steps 4 onward are not part of this branch's framework-correction task.**

No existing Karetao requirements or component documentation are being migrated by this framework stage.
