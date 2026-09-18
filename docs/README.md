# Karetao Documentation Framework

## Purpose

This directory is the system-level documentation entry point for Karetao.

Karetao documentation defines the complete system. Component repositories define their own implementations. External specifications define external equipment and dependencies. Verification records provide evidence.

This framework establishes the documentation hierarchy, authority boundaries, integration model, and rules for the later documentation refactor.

## Authority model

See [AUTHORITY.md](AUTHORITY.md) for the normative authority hierarchy, ownership boundaries, and conflict-resolution rules.



| Documentation domain | Authority | Role |
| --- | --- | --- |
| Karetao system requirements | `LentonNeale/Karetao` | Defines what the complete system shall do. |
| Karetao system architecture | `LentonNeale/Karetao` | Defines system decomposition, relationships, and integration boundaries. |
| System-level interfaces, timing, synchronization, safety, configuration, integration and verification requirements | `LentonNeale/Karetao` | Defines cross-component obligations and acceptance conditions. |
| Arm Sensor Hub implementation | `LentonNeale/Arm_Sensor_Hub` | Defines how the Arm Sensor Hub implementation satisfies applicable system requirements. |
| Raspberry Sensor Hub implementation | `LentonNeale/Raspberry_Sensor_Hub` | Defines how the Raspberry Sensor Hub implementation satisfies applicable system requirements. |
| External equipment specifications | Equipment/manufacturer specification | Defines externally controlled characteristics and constraints. |
| Verification evidence | Verification record / evidence owner | Demonstrates whether a requirement or implementation claim has been verified. |

Authority is determined by ownership, not by document location, link direction, or implementation convenience.

## Documentation hierarchy

The target Karetao hierarchy is:

```text
docs/
├── README.md                 # framework and navigation
├── requirements/             # system requirements
├── architecture/             # system architecture
├── interfaces/               # system-level interfaces
├── timing/                   # system timing and latency
├── synchronization/          # system synchronization and data coherency
├── safety/                   # system safety requirements and boundaries
├── configuration/            # system configuration requirements
├── integration/              # integration contracts and procedures
├── verification/             # verification requirements, plans and evidence indexes
├── decisions/                # system decisions / ADRs
├── external/                 # references to externally owned specifications
├── component-integration/    # component-to-system integration views
└── archive/                  # explicitly superseded historical material
```

This is the framework target. Existing documents are not moved, renamed, rewritten, or deleted by this stage.

## Component integration model

Component repositories remain independently authoritative for implementation detail.

A component implementation document should:

1. identify the applicable Karetao system requirement(s);
2. state the implementation responsibility of the component;
3. describe implementation-specific behaviour, constraints, APIs, configuration, and test strategy;
4. link to the system-level contract rather than copy or redefine it;
5. record implementation evidence and verification status where appropriate.

Karetao system documentation should:

1. define the system obligation;
2. define the cross-component contract;
3. identify the responsible component;
4. reference the component implementation documentation;
5. consume verification evidence without becoming a duplicate implementation manual.

A component may add implementation detail, but it must not silently alter a system requirement.

## Requirement-to-implementation relationship

The intended traceability chain is:

```text
System requirement
      │
      ├── system architecture / interface / constraint
      │
      ├── component responsibility
      │       └── component implementation documentation
      │
      └── verification requirement
              └── verification evidence
```

System requirements are normative at the Karetao level. Component documentation is explanatory and implementation-specific unless it explicitly cites an applicable requirement.

When an implementation appears to conflict with a system requirement, the conflict is resolved by reviewing the authoritative system requirement and the component implementation together; the component document is not treated as an implicit change to the system.

## Documentation classes

Documents should be classified before the later refactor:

- **Normative** — defines a requirement, contract, constraint, or approved system decision.
- **Descriptive** — explains architecture or implementation without creating a new requirement.
- **Procedural** — defines an operational, development, integration, or verification procedure.
- **Evidence** — records test, inspection, analysis, measurement, review, or other verification results.
- **Historical** — retained for traceability but no longer authoritative.
- **External reference** — points to a specification owned outside Karetao.

Every normative document must have a clear owner and authority boundary.

## Duplication and precedence

Do not maintain two competing definitions of the same system requirement.

Where content is duplicated during transition:

1. the explicitly designated authoritative source takes precedence;
2. the duplicate must be treated as a compatibility or historical copy;
3. later refactor work should replace duplication with a reference;
4. conflicting statements must be surfaced rather than silently reconciled.

Archive status does not make a document current. A compatibility pointer does not become authoritative merely because it is convenient to follow.

## Change control

Changes to system-level requirements, architecture, interfaces, timing, synchronization, safety, configuration, integration, or verification requirements belong in Karetao.

Changes to component implementation documentation belong in the owning component repository.

A component change that affects a system contract requires corresponding review of the Karetao documentation and traceability. A system-contract change may require coordinated changes in affected component repositories, but does not transfer system authority to those repositories.

Approved system decisions and ADRs are part of the system documentation authority chain.

## Verification and evidence

A verification record is evidence, not the requirement itself.

Verification documentation shall identify, where applicable:

- the requirement or contract being verified;
- the verification method;
- configuration/version under test;
- environment and equipment;
- result and acceptance criterion;
- date and responsible owner;
- linked artifacts or raw evidence.

Passing implementation tests do not by themselves redefine system release or safety requirements.

## External specifications

External equipment and standards remain authoritative within their own scope.

Karetao documentation should record the externally imposed interface or constraint needed by the system and reference the external source. It must not reproduce an external specification wholesale or imply ownership of it.

## Later refactor rules

The subsequent documentation refactor shall:

- preserve information and traceability before changing structure;
- classify documents before deciding their destination;
- establish one authoritative home for each system-level claim;
- replace duplicated normative content with references;
- keep component implementation detail in its owning repository;
- preserve historical records as historical where traceability requires them;
- avoid changing source code, tests, generated files, or submodules as part of documentation-only moves;
- record unresolved authority or requirement conflicts explicitly;
- validate links and requirement traceability after migration;
- require review and approval of the framework before migration begins.

## Non-goals of this stage

This framework does not:

- migrate existing documentation;
- rewrite existing documentation;
- delete existing documentation;
- modify component repositories;
- modify source code, tests, generated files, or submodules.

Those activities belong to later, separately reviewed work.
