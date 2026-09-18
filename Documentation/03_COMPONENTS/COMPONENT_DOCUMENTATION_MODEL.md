# Component Documentation Model

## Purpose

This document defines the documentation contract between Karetao and component repositories.

The central boundary is:

> Karetao defines **what the system requires from a component and its interfaces**. The component repository documents **how the component implements those responsibilities**.

This document is normative for the integration model. It does not modify component repositories.

## Ownership boundary

### System-level component definition — Karetao

The Karetao repository owns the system-level definition of each component:

- [\`ARM_SENSOR_HUB.md\`](ARM_SENSOR_HUB.md)
- [\`RASPBERRY_SENSOR_HUB.md\`](RASPBERRY_SENSOR_HUB.md)

These documents describe:

- the component's role in Karetao;
- system-level responsibilities;
- externally visible interfaces;
- system dependencies;
- system-level assumptions.

They are system documentation, not component implementation manuals.

They must not become copies of the component implementation documentation.

### Component implementation — component repository

The component repository owns implementation documentation within its component scope.

For example:

\`\`\`text
Arm_Sensor_Hub
└── Documentation/
    ├── architecture
    ├── interfaces
    ├── sensors
    ├── CAN
    ├── MKS
    └── verification
\`\`\`

The component repository describes how the component implements its responsibilities, including implementation architecture, internal interfaces, hardware/software details, diagnostics, configuration, and component-level verification evidence.

The same model applies to Raspberry Sensor Hub and future components.

## System interface versus implementation

The interface boundary follows this pattern:

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

The same conceptual model applies to:

- CAN;
- SPI;
- HOST;
- TIME;
- other future system interfaces.

Karetao defines the system contract: required behavior, externally visible semantics, timing constraints, synchronization expectations, safety constraints, and integration requirements.

The component repository defines the implementation: firmware/software architecture, drivers, internal services, message handling, configuration mechanisms, diagnostics, and implementation-specific constraints.

A component implementation document may explain how a system requirement is met, but it must not redefine the system requirement.

## Protocol authority

Three authority domains must remain distinct:

\`\`\`text
System interface
        ↓
Component implementation
        ↓
External protocol/equipment
\`\`\`

For example:

\`\`\`text
Karetao
    CAN system requirements

Arm_Sensor_Hub
    CAN service implementation

MKS documentation
    MKS CAN protocol/controller behavior
\`\`\`

Karetao remains authoritative for the system requirements placed on CAN.

The component repository remains authoritative for its CAN implementation.

Vendor or external protocol documentation remains authoritative for the external protocol or equipment behavior it defines.

A vendor protocol manual must not become an accidental source of Karetao requirements. A component implementation document must not redefine the Karetao system interface.

## Component authority declaration

Each component repository should eventually contain a documentation authority declaration identifying:

- the repository and component;
- the component implementation documentation authority;
- the Karetao system authority;
- relevant external authorities;
- the relationship between requirements, implementation, and evidence.

A component repository should reference Karetao system requirements by stable identifiers rather than copying complete system requirements into component documentation.

## Verification traceability

Component documentation should support the following traceability chain:

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

Component verification evidence demonstrates behavior within component scope.

> Successful component verification does not automatically constitute system verification.

System-level acceptance is owned by Karetao. The eventual Karetao system verification matrix should be the authoritative location for system-level verification status.

## Status semantics

Component documentation may use the following status vocabulary:

\`\`\`text
SPECIFIED
IMPLEMENTED
VERIFIED
HARDWARE_VERIFIED
SYSTEM_VERIFIED
RELEASED
SUPERSEDED
DEFERRED
BLOCKED
\`\`\`

The meanings are:

- **SPECIFIED** — the relevant requirement or intended behavior has been defined.
- **IMPLEMENTED** — the implementation exists.
- **VERIFIED** — the relevant implementation behavior has been verified.
- **HARDWARE_VERIFIED** — the behavior has been verified against actual hardware.
- **SYSTEM_VERIFIED** — the result has been accepted at Karetao system level.
- **RELEASED** — the item has been formally released according to project process.
- **SUPERSEDED** — replaced by a newer authoritative item.
- **DEFERRED** — intentionally postponed.
- **BLOCKED** — progress or verification is prevented by an identified blocker.

A component repository must not claim \`SYSTEM_VERIFIED\` solely because component-level testing has passed.

## External documentation

Vendor manuals, datasheets, standards, and other external specifications remain external authority for the equipment or protocol they define.

Component documentation may reference those sources and explain how the implementation uses them. Such references must distinguish:

1. Karetao system requirements;
2. component implementation behavior;
3. external equipment or protocol behavior.

The physical location of a document does not determine its authority.

## Conflict resolution

When documentation conflicts:

1. Identify the subject of the disputed statement.
2. Identify the authority that owns that subject.
3. Treat that authority as controlling for the subject.
4. Update dependent documentation only as part of the appropriate review/refactoring process.

A lower-level document may explain how a higher-level requirement is implemented, but it must not redefine the higher-level requirement.

## Archive boundary

Historical component documentation belongs in the appropriate repository's archive according to that repository's process. Karetao's [\`99_ARCHIVE/\`](../99_ARCHIVE/) is for historical/non-normative Karetao material.

Archived material may be retained for traceability but must never silently override current authoritative documentation.

## Future component adoption

A future component can adopt this model by establishing:

1. a Karetao component definition under \`Documentation/03_COMPONENTS/\`;
2. an implementation documentation structure in the component repository;
3. an explicit authority declaration;
4. references from implementation documentation to Karetao system requirement identifiers;
5. component-level verification evidence;
6. integration evidence;
7. a clear distinction between component verification and Karetao system verification.

The model is intended to be reusable without creating a new authority scheme for each component.

## Scope of this framework branch

This document defines the integration standard only.

It does not:

- migrate existing component documentation;
- import Arm Sensor Hub documentation;
- import Raspberry Sensor Hub documentation;
- rewrite existing Karetao requirements;
- copy vendor manuals;
- modify component repositories;
- modify submodules.

Documentation inventory, classification, authority determination, migration, archival cleanup, and cross-repository reference establishment occur only after this framework has been reviewed and approved.
