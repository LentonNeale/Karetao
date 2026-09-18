# Documentation Authority Model

## Purpose

This document defines the normative authority model for Karetao documentation. It establishes which repository or record owns each class of information and how conflicts are resolved.

The model is:

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

## Authority hierarchy

### Karetao system authority

\`LentonNeale/Karetao\` is authoritative for:

- system requirements;
- system architecture;
- system-level interfaces;
- system timing;
- system synchronization;
- system safety requirements;
- system-level configuration requirements;
- system verification requirements;
- system integration requirements;
- system-level component roles and responsibilities.

### Arm Sensor Hub component authority

\`LentonNeale/Arm_Sensor_Hub\` is authoritative for:

- Arm Sensor Hub implementation;
- STM32 firmware architecture;
- implementation-specific interfaces;
- sensor acquisition implementation;
- CAN implementation;
- MKS integration implementation;
- implementation-specific configuration;
- implementation diagnostics;
- component-level verification evidence.

It is **not** authoritative for Karetao system requirements.

### Raspberry Sensor Hub component authority

\`LentonNeale/Raspberry_Sensor_Hub\` is authoritative for Raspberry Sensor Hub implementation documentation.

It is **not** authoritative for Karetao system requirements.

### External authority

Vendor manuals, datasheets, standards, and other external specifications are authoritative for the external equipment or protocol they define.

They do **not** define Karetao system requirements.

For example, an MKS manual defines MKS equipment/controller behavior and any external protocol it specifies. Karetao documentation defines the system requirements imposed on that equipment or protocol.

### Verification authority

Verification records provide evidence that requirements or implementation behavior have been tested or otherwise verified.

Verification evidence does **not** redefine requirements.

The distinction is:

| Role | Meaning |
|---|---|
| **Requirement** | What the system or component is required to do |
| **Implementation** | How a component implements its assigned responsibilities |
| **Verification evidence** | Evidence that a requirement or implementation behavior has been satisfied or verified |

Successful component verification does not automatically constitute system verification.

## Critical authority rules

> A document's physical location does not by itself make it authoritative. Authority is determined by the subject ownership defined by this model.

> A lower-level document may explain how a higher-level requirement is implemented, but it must not redefine the higher-level requirement.

> Where two documents conflict, determine which authority owns the subject before resolving the conflict.

A component document may reference and explain a Karetao requirement. It must not silently replace, weaken, strengthen, or reinterpret that requirement.

A vendor document may define external behavior that constrains an implementation. It must not become an accidental source of Karetao requirements.

## Normative and descriptive documentation

The framework distinguishes documents by role:

| Document | Role |
|---|---|
| \`SYSTEM_REQUIREMENTS.md\` | Normative system requirements |
| \`SYSTEM_ARCHITECTURE.md\` | Normative system architecture |
| \`SYSTEM_TIMING.md\` | Normative system timing |
| \`SYSTEM_SYNCHRONIZATION.md\` | Normative system synchronization |
| \`SYSTEM_OVERVIEW.md\` | Descriptive system overview |
| \`DOCUMENTATION_AUTHORITY_MODEL.md\` | Normative documentation authority |
| Component documentation | Implementation authority within component scope |
| Vendor manuals | External authority |
| Verification documents | Evidence |

Normative documents establish requirements, constraints, or authority. Descriptive documents explain or summarize authoritative information for navigation and understanding.

A descriptive document may summarize authoritative information, but it must not introduce a conflicting requirement or create a competing authority.

## System interfaces and component implementations

Karetao defines what the system requires from an interface. The responsible component repository documents how its implementation satisfies that requirement.

The general boundary is:

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

The same conceptual boundary applies to:

- CAN;
- SPI;
- HOST;
- TIME;
- other future system interfaces.

A system-interface document owns the system contract. A component implementation document owns implementation details. An external protocol specification owns externally defined protocol behavior.

## Protocol authority

System interface, component implementation, and external protocol are separate authority domains.

For example:

\`\`\`text
Karetao
    CAN system requirements

Arm_Sensor_Hub
    CAN service implementation

MKS documentation
    MKS CAN protocol/controller behavior
\`\`\`

A vendor protocol manual must not redefine a Karetao system requirement.

A component implementation document must not redefine the Karetao system interface.

Where a protocol imposes limitations on a system design, the limitation may be documented as an implementation or integration constraint; the Karetao requirement remains owned by Karetao.

## Verification traceability

System verification follows this relationship:

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

Component verification establishes evidence within component scope. It does not by itself establish that the integrated Karetao system satisfies the system requirement.

The Karetao system verification matrix should eventually be the authoritative location for system-level verification status.

## Component status semantics

The framework retains the following status vocabulary:

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

The meanings relevant to authority are:

- \`IMPLEMENTED\` — the implementation exists.
- \`VERIFIED\` — the relevant implementation behavior has been verified.
- \`HARDWARE_VERIFIED\` — the behavior has been verified against actual hardware.
- \`SYSTEM_VERIFIED\` — the result has been accepted at the Karetao system level.
- \`RELEASED\` — the item has been formally released according to project process.

A component repository must not claim \`SYSTEM_VERIFIED\` solely because component-level testing has passed.

## Component integration boundary

Karetao owns the system definition of each component under \`Documentation/03_COMPONENTS/\`.

Component repositories own the implementation documentation for those components.

The Karetao component document therefore describes:

- the component's role in Karetao;
- system-level responsibilities;
- externally visible interfaces;
- system dependencies;
- system-level assumptions.

It must not become a copy of the component implementation documentation.

The component documentation contract is defined in [\`03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md\`](../03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md).

## Archive boundary

\`Documentation/99_ARCHIVE/\` contains historical and non-normative material, including where applicable:

- superseded specifications;
- historical decisions;
- sprint reports;
- conversations;
- obsolete planning material.

Archive content must never silently override current authoritative documentation. If archived material is retained for traceability, its historical status must remain clear.

## Refactoring sequence

This framework is preparatory. The intended documentation refactoring sequence is:

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

Steps 4 onward are outside the scope of this framework-correction task.

## Framework scope

This branch establishes the governance framework only. It does not migrate existing Karetao documentation, import component-repository documentation, copy vendor manuals, or modify component repositories.

No existing system requirements are being rewritten by this framework document.
