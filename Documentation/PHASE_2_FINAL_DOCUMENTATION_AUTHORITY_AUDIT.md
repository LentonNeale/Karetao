# Phase 2 — Final Documentation Authority Audit

## Status

Human-reviewed authority dispositions recorded from the Phase 2 reconciliation decisions.

**Audit branch:** `doc/reconcile-karetao-mks`  
**Mode for this update:** repository audit amendment explicitly authorized by the latest task instruction.  
**Refactor branch:** `doc/documentation-framework` (not used for this audit update).

## Authority model

Karetao `Documentation/**` is the current authority for system requirements, system architecture, system-level interfaces, timing/synchronization, safety, controlled system configuration, system integration requirements, system verification status, and system-level component roles.

Component repositories retain authority for implementation details, component interfaces/configuration, and component-level verification within their scope. Vendor material remains external authority for externally defined equipment/protocol behaviour. Decisions preserve decision status and rationale even where selected statements are promoted into system requirements.

`docs/project/archive/**` is historical/archived material and is excluded from current authority determination and normal migration.

## Source authority table

| Source family | Ownership/provenance | Subject/purpose | Status | Authority | Refactor disposition |
|---|---|---|---|---|---|
| `Documentation/00_INDEX.md` and framework governance | Karetao | Documentation framework and authority domains | Current | Karetao governance | Retain as framework entry point |
| `Documentation/01_SYSTEM/**` | Karetao | System authority destinations | Current framework; substantive content incomplete in several placeholders | Karetao | Populate from reconciled sources |
| `Documentation/02_INTERFACES/**` | Karetao | System-level interfaces | Current framework; substantive content incomplete in placeholders | Karetao | Populate from system-facing contracts/decisions |
| `Documentation/03_COMPONENTS/**` | Karetao | System-level component roles | Current framework; substantive content incomplete in placeholders | Karetao | Populate system role/contract boundaries |
| `Documentation/04_SAFETY/**` | Karetao / safety authority | System safety requirements and architecture | Current framework | Karetao for system scope | Populate from safety decisions and evidence |
| `Documentation/05_VERIFICATION/**` | Karetao | System verification status | Current framework | Karetao | Populate; retain component evidence as evidence |
| `Documentation/06_CONFIGURATION/**` | Karetao | Controlled system configuration | Current framework | Karetao | Populate only system-owned configuration |
| `Documentation/07_DECISIONS/**` | Karetao | Decision records and rationale | Current framework | Karetao decision record | Preserve decision provenance |
| `docs/project/**` non-archive | Karetao legacy project documentation | Mixed system/component/decision/interface content | Legacy/transitional | Subject-dependent; not canonical by location | Reconcile by subject; retain source provenance during transition |
| `README.md` | Karetao | Repository overview and legacy documentation pointer | Legacy/transitional | Not documentation authority | Rebuild after refactor |
| `Arm_Sensor_Hub/**` documentation | Arm Sensor Hub | Component implementation | Current component authority | Arm Sensor Hub | Preserve implementation authority; update stale Karetao pointers |
| `RaspberryPi_Sensor_Hub/**` documentation | Raspberry Sensor Hub | Component implementation | Current component authority | Raspberry Sensor Hub | Preserve implementation authority; update stale Karetao pointers |
| MKS manuals / integrated codec references | Vendor / external | MKS equipment/protocol behaviour | External | Vendor | Retain as external reference |

## Conflict register — resolved dispositions

### C-01 — Root README authority

**Source A:** `README.md`, which describes `docs/project/` as canonical project documentation.  
**Source B:** Karetao `Documentation/**` framework and authority model.  
**Subject:** Current Karetao documentation hierarchy.  
**Nature:** Legacy README canonicality statement conflicts with the established framework.  
**Evidence:** `Documentation/00_INDEX.md` and `Documentation/01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md` establish Karetao `Documentation/**` as the system documentation framework; the README retains the older `docs/project/` statement.  
**Resolution:** **Source B.** `Documentation/**` is the current Karetao documentation authority. Root README is non-authoritative for hierarchy and is to be rebuilt after refactor.

### C-02 — Legacy project README canonicality

**Source A:** `docs/project/README.md`, which declares `docs/project/` canonical.  
**Source B:** Karetao `Documentation/**` framework.  
**Subject:** Project documentation authority.  
**Nature:** Legacy organization claim conflicts with the current framework.  
**Evidence:** Current framework authority model assigns system subjects to Karetao `Documentation/**`.  
**Resolution:** **Source B.** `docs/project/**` is source material during reconciliation, not current authority merely by directory location.

### C-03 — Component README authority pointer

**Source A:** `Arm_Sensor_Hub/README.md` and `RaspberryPi_Sensor_Hub/README.md`, which direct users to `docs/project/` for project documentation.  
**Source B:** Karetao authority model plus component documentation model.  
**Subject:** System-vs-component documentation authority.  
**Nature:** Stale Karetao documentation pointer conflicts with the current system framework.  
**Evidence:** Karetao owns system-level requirements/interfaces/architecture/integration; component repositories own implementation details.  
**Resolution:** **Source B, while preserving component implementation authority.** Component implementation remains authoritative in the respective component repositories. Karetao owns only the system-level definition and integration boundary. The stale Karetao pointer is updated during refactor.

### C-04 — Mixed legacy architecture

**Source A:** `docs/project/system/architecture.md` and related mixed legacy documents.  
**Source B:** Karetao authority domains plus component ownership model.  
**Subject:** Architecture, component roles, implementation, interfaces and external behaviour.  
**Nature:** A single legacy document combines multiple authority subjects.  
**Evidence:** The legacy architecture contains system structure/data flow as well as concrete STM32 implementation details and external protocol context.  
**Resolution:** **Separate by subject.** System architecture and system component roles move into Karetao `Documentation/01_SYSTEM/**` and `Documentation/03_COMPONENTS/**`; system interfaces into `Documentation/02_INTERFACES/**`; Arm/Raspberry implementation remains component-owned; vendor-defined behaviour remains external reference. Do not promote the mixed source wholesale.

### C-05 — Decision records versus system requirements

**Source A:** `docs/project/SD/SD-01.md` through `SD-26.md` and `docs/project/SYSTEM_DECISIONS.md`.  
**Source B:** Karetao `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` authority destination.  
**Subject:** System-level normative requirements embedded in decisions.  
**Nature:** Decision records contain requirement-bearing statements but remain decision records; the prior framework placeholder contains no substantive requirements.  
**Evidence:** Content review identifies system-requirement-bearing statements across the SD set, including timing, failure response, CAN, SPI, time synchronization, recovery and safety.  
**Resolution:** **Source B + systematic SD-derived requirement coverage.** System-owned normative statements are to be reconciled into `SYSTEM_REQUIREMENTS.md`, with traceability back to their SD identifiers. Decision status/rationale remains in the decision record. Not every decision statement is automatically a requirement; proposed/open items and implementation-only constraints remain appropriately classified.

#### Systematic SD-derived requirement coverage

All SD-01 through SD-26 were reviewed for requirement-bearing system content:

| SD | Requirement-bearing subject identified | Treatment |
|---|---|---|
| SD-01 | 100 Hz publication/control baseline; 500 Hz EKF setting; SPI 5 MHz initial maximum | Reconcile system timing requirements; preserve validation caveats |
| SD-02 | Failure classes and motion-inhibit ownership | Reconcile system fault/motion-permission requirements; risk-assessment dependency retained |
| SD-03 | 500 ms heartbeat; reject motion; controlled stop/motor disable; no last-command hold | Reconcile as system safety/fault-response requirements |
| SD-04 | Feedback timeout thresholds and motor inhibit/escalation | Reconcile as system fault-response requirements |
| SD-05 | 1 Mbps CAN; standard IDs; measured load target; validation dependencies | Reconcile system CAN requirements with provisional/validation status explicit |
| SD-06 | Bus-off detection, command inhibit, bounded recovery, explicit reactivation | Reconcile system CAN fault/recovery requirements |
| SD-07 | Versioned deterministic joint/motor mapping | Reconcile system interface/component-role requirement; differential exception remains |
| SD-08 | Observation skew targets and acquisition timestamps | Reconcile timing/data-quality requirement; integration implications retained |
| SD-09 | Measurement history ownership and latest-value/timestamp semantics | Reconcile system data-flow/interface requirement; implementation ownership remains component-specific |
| SD-10 | Calibration ownership and controlled parameter path | Reconcile system calibration/configuration requirement |
| SD-11 | Versioned, CRC-protected redundant calibration storage | Reconcile system configuration/integrity requirement where system-owned |
| SD-12 | Host/API radians authority and versioned wire-schema changes | Reconcile system interface/schema requirement |
| SD-13 | Required joint state fields, validity/status/timestamp/sync/calibration metadata | Reconcile system state interface requirement |
| SD-14 | Position/velocity command plus enable/disable/controlled-stop and gating | Reconcile system command-interface requirements; acknowledgement/freshness remain explicit open items |
| SD-15 | 512-byte frame, payload limit, Mode 0, little-endian, CRC-32, ownership | Reconcile system SPI interface requirements |
| SD-16 | Snapshot priority, immutable DMA buffers, replace-if-new semantics | Reconcile system SPI/data-consistency requirements; performance validation retained |
| SD-17 | DATA_READY/polling strategy and 1 ms initial polling | Reconcile interface/timing requirements with current hardware limitation explicit |
| SD-18 | Timestamp error target <= +/-1 ms; sync validity/age | Reconcile system timing/synchronization requirement |
| SD-19 | 1 Hz nominal sync, configurable to 10 Hz, five-second invalidation | Reconcile synchronization requirements with validation status |
| SD-20 | Continue acquisition/diagnostics; inhibit time-dependent motion during invalid sync | Reconcile system safety/motion-permission requirement; define exact scope during refactor |
| SD-21 | Initial/runtime time-offset validation and rejection without silent slew | Reconcile synchronization/interface requirement; provisional bounds remain marked |
| SD-22 | Reset clears sync validity/offset; unsynchronized until accepted update | Reconcile reset/synchronization requirement |
| SD-23 | Bounded retries; persistent failures enter ERROR; recovery to INACTIVE | Reconcile system recovery/fault-state requirements; motion race remains to be explicitly resolved |
| SD-24 | INACTIVE recovery; dependency-ordered reactivation; no automatic motion resume | Reconcile system recovery/motion-release requirement |
| SD-25 | Independent E-stop, motor disable/power removal, watchdog, stop/brake, fault indication, reset, safety-rated architecture as release gates | Reconcile into safety requirements with risk-assessment boundary preserved |
| SD-26 | Differential motor-to-DOF mapping | PROPOSED: retain as decision/design requirement candidate; do not promote as implemented fact until mechanical mapping is verified |

This coverage table is a traceability inventory, not a claim that every listed statement is already a uniquely numbered final requirement. Requirement identifiers, wording and acceptance criteria must be established in the refactor.

### C-06 — System verification versus component evidence

**Source A:** component-level verification records and implementation tests.  
**Source B:** Karetao `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`.  
**Subject:** Authority for system-level verification status.  
**Nature:** Component evidence can demonstrate component behaviour but does not by itself establish system-level acceptance.  
**Evidence:** The authority model explicitly separates component verification from Karetao system verification.  
**Resolution:** **Source B.** The Karetao system verification matrix is authoritative for system-level verification status. Component verification remains evidence within component scope and is traced into system verification where applicable.

## README classification

`README.md` is **MIXED / Karetao-owned**, but its documentation-hierarchy statement is legacy/non-authoritative. Its `docs/project/` canonicality claim must not be used as current authority. Disposition: **rebuild after refactor**.

Component README pointers to `docs/project/` are likewise transitional/stale and should be updated to point to the current Karetao system documentation while preserving the component repositories as implementation authorities.

## Archive exclusion confirmation

`docs/project/archive/**` is explicitly excluded from current authority determination and normal migration. It remains historical/archived material and must not be promoted to current authority solely because it contains technically useful statements.

## Proposed target structure

```
Documentation/
├── 00_INDEX.md
├── 01_SYSTEM/
│   ├── SYSTEM_OVERVIEW.md
│   ├── SYSTEM_REQUIREMENTS.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── SYSTEM_TIMING.md
│   ├── SYSTEM_SYNCHRONIZATION.md
│   └── DOCUMENTATION_AUTHORITY_MODEL.md
├── 02_INTERFACES/
│   ├── CAN/CAN_SYSTEM_INTERFACE.md
│   ├── HOST/HOST_SYSTEM_INTERFACE.md
│   ├── SPI/SPI_SYSTEM_INTERFACE.md
│   └── TIME/TIME_SYSTEM_INTERFACE.md
├── 03_COMPONENTS/
│   ├── ARM_SENSOR_HUB.md
│   ├── RASPBERRY_SENSOR_HUB.md
│   └── COMPONENT_DOCUMENTATION_MODEL.md
├── 04_SAFETY/
├── 05_VERIFICATION/
├── 06_CONFIGURATION/
├── 07_DECISIONS/
└── 99_ARCHIVE/
```

Migration is subject-based. Mixed legacy documents are used as evidence/source material and decomposed without losing provenance. Legacy source documents are not silently deleted. Where retained temporarily, they are marked transitional and point to the new authoritative destinations.

## Migration/disposition matrix

| Content | Disposition |
|---|---|
| System requirements from SDs/contracts | Reconcile into `01_SYSTEM/SYSTEM_REQUIREMENTS.md` with source traceability |
| System architecture from mixed legacy docs | Extract into `01_SYSTEM/**`; separate implementation content |
| System interfaces | Extract into `02_INTERFACES/**` |
| System component roles | Extract into `03_COMPONENTS/**` |
| Arm implementation | Preserve in Arm Sensor Hub documentation |
| Raspberry implementation | Preserve in Raspberry Sensor Hub documentation |
| Safety requirements/architecture | Reconcile into `04_SAFETY/**` |
| System verification status | Reconcile into `05_VERIFICATION/**`; trace component evidence |
| System configuration | Reconcile into `06_CONFIGURATION/**` |
| Decisions/rationale | Preserve in `07_DECISIONS/**` |
| Legacy non-archive source docs | Retain or transition with explicit provenance; do not silently delete |
| `docs/project/archive/**` | Exclude; historical only |
| Root README | Rebuild after refactor |
| Component README stale pointers | Update to current Karetao documentation; preserve component implementation authority |

## Unresolved decisions requiring human review

1. Exact unique system requirement identifiers and final wording/acceptance criteria.
2. Exact boundary between system requirements and Arm-only implementation constraints in mixed firmware contracts.
3. Exact definition of “time-dependent motion” under SD-20.
4. System-level motion-permission authority and recovery-in-progress behaviour under SD-02/SD-23.
5. Exact dependency-ordered recovery sequence under SD-24.
6. Safety boundary between application controlled-stop and independent safety system under SD-25.
7. Validation of provisional timing/CAN/SPI/time-sync values against target hardware.
8. SD-26 differential end-effector transformation and its verified mechanical model.
9. Which existing observations qualify as system integration evidence versus component evidence.

## Refactor gate

**The refactor may proceed on `doc/documentation-framework`, subject to preserving the above resolutions and unresolved items.**

No authority is inferred solely from directory location. No archived material is promoted. No component implementation authority is transferred to Karetao.

## Audit provenance

The audit is based on the Phase 2 indexed/reconciled Karetao documentation baseline and the content-level classification. The six conflict dispositions above are the human decisions supplied for this reconciliation pass.

## Validation

- [x] C-01 resolved to Source B.
- [x] C-02 resolved to Source B.
- [x] C-03 resolved to Source B while preserving component implementation authority.
- [x] C-04 resolved by subject separation.
- [x] C-05 resolved to Source B with systematic SD-01..SD-26 coverage.
- [x] C-06 resolved to Source B.
- [x] README legacy/non-authoritative classification retained.
- [x] Archive exclusion retained.
- [x] Refactor boundary and unresolved issues recorded.
