# Karetao Documentation

## Start here

1. [`01_SYSTEM/PROJECT_CHARTER.md`](01_SYSTEM/PROJECT_CHARTER.md): scope, goals, non-goals and who decides.
2. This map.

Rules for keeping these documents consistent: [`DOCUMENTATION_RULES.md`](DOCUMENTATION_RULES.md).

## Map

| Section | What it holds | Key files |
|---|---|---|
| `01_SYSTEM/` | Scope, requirements, architecture, lifecycle, synchronization | [`PROJECT_CHARTER`](01_SYSTEM/PROJECT_CHARTER.md), [`SYSTEM_OVERVIEW`](01_SYSTEM/SYSTEM_OVERVIEW.md), [`SYSTEM_REQUIREMENTS`](01_SYSTEM/SYSTEM_REQUIREMENTS.md), [`SYSTEM_ARCHITECTURE`](01_SYSTEM/SYSTEM_ARCHITECTURE.md), [`SYSTEM_LIFECYCLE`](01_SYSTEM/SYSTEM_LIFECYCLE.md), [`SYSTEM_SYNCHRONIZATION`](01_SYSTEM/SYSTEM_SYNCHRONIZATION.md) |
| `02_INTERFACES/` | System-level interface contracts | [`SPI_SYSTEM_INTERFACE`](02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md), [`SPI_PAYLOAD_SCHEMA`](02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md), [`CAN_SYSTEM_INTERFACE`](02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md), [`TIME_SYSTEM_INTERFACE`](02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md), [`HOST_SYSTEM_INTERFACE`](02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md) |
| `03_COMPONENTS/` | System-level definition of each component | [`ARM_SENSOR_HUB`](03_COMPONENTS/ARM_SENSOR_HUB.md), [`RASPBERRY_SENSOR_HUB`](03_COMPONENTS/RASPBERRY_SENSOR_HUB.md) |
| `04_SAFETY/` | System safety behaviours | [`SAFETY_REQUIREMENTS`](04_SAFETY/SAFETY_REQUIREMENTS.md) |
| `05_VERIFICATION/` | Verification status, strategy, evidence | [`SYSTEM_VERIFICATION_MATRIX`](05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md), [`VERIFICATION_STRATEGY`](05_VERIFICATION/VERIFICATION_STRATEGY.md), [`EVIDENCE_RECORD_FORMAT`](05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md), [`CAN_INTEGRATION_EVIDENCE`](05_VERIFICATION/CAN_INTEGRATION_EVIDENCE.md), [`TIME_SYNC_VALIDATION`](05_VERIFICATION/TIME_SYNC_VALIDATION.md), [`TIME_SYNC_CHARACTERISATION_EVIDENCE`](05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md) |
| `06_CONFIGURATION/` | Every numeric value with its basis; configuration | [`PARAMETER_REGISTER`](06_CONFIGURATION/PARAMETER_REGISTER.md), [`SYSTEM_CONFIGURATION`](06_CONFIGURATION/SYSTEM_CONFIGURATION.md) |
| `07_DECISIONS/` | Decision records | [`ARCHITECTURE_DECISIONS`](07_DECISIONS/ARCHITECTURE_DECISIONS.md), [`ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS`](07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md), [`KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER`](07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md) |

Component implementation documents are in `Arm_Sensor_Hub/Documentation/` and `RaspberryPi_Sensor_Hub/Documentation/`. Vendor references are in `icm-project/references/`.

## Authority in one paragraph per domain

**Karetao system documents** (`Documentation/**`) own system requirements, interfaces, safety behaviours, configuration and parameters, and verification status. Authority follows the subject, not the folder.

**Component documents** (`Arm_Sensor_Hub/Documentation/`, `RaspberryPi_Sensor_Hub/Documentation/`) own implementation. They may explain how a system requirement is met, and they never redefine it or keep a competing copy.

**Vendor documents** are external authority for the equipment and protocols they define. They are kept as reference folders in `icm-project/references/` and are not rewritten as project specifications.

**Verification evidence** records what was run and observed. It never becomes a requirement. `SYSTEM_VERIFIED` is set only in `SYSTEM_VERIFICATION_MATRIX.md`, by Lenton Neale. Component test results do not establish it.

## Status vocabulary

| Applies to | Values |
|---|---|
| Requirements | Approved, Retired, Deferred, Withdrawn |
| Parameters | Measured, Datasheet, Derived, Provisional |
| Verification | OPEN, COMPONENT_EVIDENCE, SYSTEM_VERIFIED |
| Design descriptions | As-built (describes the code as it is now), Target (decided, not yet implemented) |

Items still marked proposed or open are not normative.

Terms for the arm's parts (joint, axis, motor, drive, joint encoder) for the data path (sample, feedback, latest value, record, snapshot, message, frame, transaction, exchange, publish) for time (TIME_SYNC, clock sync, ClockSync, observation, offset, acquisition and synchronized timestamps, spread) and for gating (motion gate, fault, error, retry, recovery, reactivation, stale, E-stop, controlled stop): [`SYSTEM_OVERVIEW.md`](01_SYSTEM/SYSTEM_OVERVIEW.md) § Vocabulary.

## Who decides

Lenton Neale decides scope, priorities, requirement approval and verification acceptance (see the charter).

## Changing or removing a document

Follow [`DOCUMENTATION_RULES.md`](DOCUMENTATION_RULES.md): check git history, unique content and inbound links first, and record the removal in the provenance line below.

## Governance

- [`DOCUMENTATION_RULES.md`](DOCUMENTATION_RULES.md): the rules for these documents.
- [`CHARTER_ALIGNMENT_PLAN.md`](CHARTER_ALIGNMENT_PLAN.md): status of the alignment of these documents with the charter.

## Provenance

The former `docs/project` tree, `99_ARCHIVE/` (last at commit `9c637ba`), the documentation authority model, component documentation model, refactoring rules, plan and ledger, and the implementation checklist were removed from the working tree (2026-09-25 and 2026-10-03) and live in git history; the research notes moved to `icm-project/`.
