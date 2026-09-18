# Documentation Authority Model

## Purpose

## Mandatory project authority rule

**The Karetao Documentation authority framework is the only project documentation authority framework to use.** Use `Documentation/**` and its normative authority model for Karetao system-level documentation and documentation governance. Do not use `docs/project/**` as a competing or parallel authority framework.

All `docs/project/**` content is **reference/source material only** during the documentation transition. It remains available for reconciliation, provenance, and evidence review, but it is not current authority. After the Karetao documentation is finalized, `docs/project/**` is intended to be removed.


This document defines the normative authority model for Karetao documentation. It establishes which repository, external authority, or verification record owns each class of information and how conflicts are resolved.

The model uses authority domains with an explicit project-level relationship: **Karetao is the higher authority for the integrated Karetao system and for system-level documentation governance.** Component repositories are subordinate to Karetao for system-level matters. External authorities remain authoritative for externally defined equipment and protocol behaviour within their own subject domains, and verification records provide evidence rather than requirements.

```text
Karetao
    higher authority for the integrated system
    owns system requirements and system-level definitions
        │
        ├── Arm_Sensor_Hub
        │     subordinate component authority
        │     owns component implementation documentation
        │
        └── Raspberry_Sensor_Hub
              subordinate component authority
              owns component implementation documentation

Vendor/external documentation
    external authority for externally defined behaviour

Verification records
    evidence; not requirement authority
```

Authority is determined by **subject ownership within this relationship**. A document's physical location does not by itself make it authoritative.

## Authority domains

### Karetao system authority

`LentonNeale/Karetao` is authoritative for:

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

`LentonNeale/Arm_Sensor_Hub` is authoritative for:

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

`LentonNeale/Raspberry_Sensor_Hub` is authoritative for Raspberry Sensor Hub implementation documentation.

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

> Karetao is the higher authority for the integrated Karetao system and for system-level documentation governance.

> A component repository is subordinate to Karetao for system-level requirements, architecture, interfaces, timing, synchronization, safety, configuration, integration, and system verification. It remains authoritative for implementation details within its component scope.

> A lower-level implementation document may explain how a higher-level requirement is implemented, but it must not redefine the higher-level requirement.

> Where two documents conflict, first determine whether the disputed subject is system-level, component-implementation-level, externally defined, or verification evidence. Karetao controls system-level subjects; the responsible component controls implementation subjects within its scope; external authorities control externally defined behaviour; verification records provide evidence and do not redefine requirements.

> Vendor or external specifications remain authoritative for externally defined equipment or protocol behaviour. They do not override Karetao system requirements, and Karetao system requirements do not redefine externally owned equipment/protocol behaviour.

A component document may reference and explain a Karetao requirement. It must not silently replace, weaken, strengthen, or reinterpret that requirement. A component README or other navigation document must not establish a competing project-level documentation authority; references for system-level documentation must defer to Karetao's `Documentation/**` framework.

A vendor document may define external behavior that constrains an implementation. It must not become an accidental source of Karetao requirements.

## Cross-document authority transition

The authority model applies to all repository entry points and navigation documents, including component README files. A README may provide local navigation, but it must not establish a competing project-level authority.

During transition to this framework, existing references that identify `docs/project/` as the canonical project documentation location are legacy authority pointers. In particular, references in:

- `Arm_Sensor_Hub/README.md`;
- `RaspberryPi_Sensor_Hub/README.md`;
- and any equivalent project-level entry-point documentation;

must be treated as subordinate, transitional navigation content rather than as authority declarations. They must ultimately direct users to the Karetao `Documentation/**` framework for system-level documentation.

This is a **cross-document authority transition issue**: correcting the Karetao authority model alone does not make existing README references authoritative. During the later reconciliation/refactoring phase, dependent entry points must be updated so that following documentation links cannot reasonably lead users to conclude that `docs/project/` supersedes or overrides Karetao `Documentation/**`.

## Mixed-authority legacy documents

A legacy document may contain information belonging to multiple authority domains. Authority is assigned to **individual significant statements/content by subject**, not necessarily to the document as a whole.

During reconciliation, each significant normative or factual statement must be:

1. classified by subject authority;
2. assigned to the authority that owns that subject;
3. migrated to the appropriate authoritative location;
4. represented elsewhere by a reference to the authoritative requirement or definition rather than a duplicated requirement, where applicable;
5. retained as historical context in the appropriate archive when necessary.

Where necessary, a mixed-authority legacy document must be split into:

- system requirement;
- system architecture/interface definition;
- component implementation;
- external/vendor reference;
- verification evidence;
- historical context.

Simply moving a legacy document into a new directory does **not** make all of its contents authoritative for that directory.

The Phase 2 authority audit has established the refactor rule: mixed legacy material is separated by subject. System-owned statements are reconciled into Karetao authority documents; component implementation remains component-owned; external behaviour remains externally owned; verification evidence remains evidence.

## Normative and descriptive documentation

The framework distinguishes documents by role:

| Document | Role |
|---|---|
| `SYSTEM_REQUIREMENTS.md` | Normative system requirements |
| `SYSTEM_ARCHITECTURE.md` | Normative system architecture |
| `SYSTEM_TIMING.md` | Normative system timing |
| `SYSTEM_SYNCHRONIZATION.md` | Normative system synchronization |
| `SYSTEM_OVERVIEW.md` | Descriptive system overview |
| `DOCUMENTATION_AUTHORITY_MODEL.md` | Normative documentation authority |
| Component documentation | Implementation authority within component scope |
| Vendor manuals | External authority |
| Verification documents | Evidence |

Normative documents establish requirements, constraints, or authority. Descriptive documents explain or summarize authoritative information for navigation and understanding.

A descriptive document may summarize authoritative information, but it must not introduce a conflicting requirement or create a competing authority.

## System interfaces and component implementations

Karetao defines what the system requires from an interface. The responsible component repository documents how its implementation satisfies that requirement.

The general boundary is:

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

```text
Karetao
    CAN system requirements

Arm_Sensor_Hub
    CAN service implementation

MKS documentation
    MKS CAN protocol/controller behavior
```

A vendor protocol manual must not redefine a Karetao system requirement.

A component implementation document must not redefine the Karetao system interface.

Where a protocol imposes limitations on a system design, the limitation may be documented as an implementation or integration constraint; the Karetao requirement remains owned by Karetao.

## Verification traceability

System verification follows this relationship:

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

Component verification establishes evidence within component scope. It does not by itself establish that the integrated Karetao system satisfies the system requirement.

`Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` is the **authoritative location for Karetao system-level verification status**.

The distinction is explicit:

```text
Component verification evidence
        ≠
Karetao system verification
```

Only the Karetao system verification process and matrix establish system-level verification status.

## Component status semantics

The framework retains the following status vocabulary:

```text
SPECIFIED
IMPLEMENTED
VERIFIED
HARDWARE_VERIFIED
SYSTEM_VERIFIED
RELEASED
SUPERSEDED
DEFERRED
BLOCKED
```

The meanings relevant to authority are:

- `IMPLEMENTED` — the implementation exists.
- `VERIFIED` — the relevant implementation behavior has been verified.
- `HARDWARE_VERIFIED` — the behavior has been verified against actual hardware.
- `SYSTEM_VERIFIED` — the result has been accepted at the Karetao system level.
- `RELEASED` — the item has been formally released according to project process.

A component repository must not claim `SYSTEM_VERIFIED` solely because component-level testing has passed.

## Component integration boundary

Karetao owns the system definition of each component under `Documentation/03_COMPONENTS/`.

Component repositories own the implementation documentation for those components.

The Karetao component document therefore describes:

- the component's role in Karetao;
- system-level responsibilities;
- externally visible interfaces;
- system dependencies;
- system-level assumptions.

It must not become a copy of the component implementation documentation.

The component documentation contract is defined in [`03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md`](../03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md).

## Archive boundary

`Documentation/99_ARCHIVE/` contains historical and non-normative material, including where applicable:

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
5. Classify documents and significant statements.
6. Determine subject authority.
7. Refactor Karetao system documentation.
8. Refactor component documentation.
9. Establish cross-repository references.
10. Archive superseded material.
11. Remove genuinely redundant material.
12. Verify links and authority boundaries.

The audit and classification steps have been completed for this refactor; the active work is the subject-based reconciliation and establishment of the Karetao system documentation authority described above.

## Refactor scope

The Phase 2 authority audit has authorized subject-based reconciliation on this branch. Karetao system documents may be populated from reconciled legacy sources. This does not transfer component implementation authority, copy vendor manuals into system authority, or promote verification evidence into requirements. Legacy source documents are retained unless a later explicit disposition authorizes removal.
