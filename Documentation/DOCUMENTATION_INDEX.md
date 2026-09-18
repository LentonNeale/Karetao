# Karetao Documentation Index

## Purpose

This document is the persistent cross-repository documentation inventory for the Karetao reconciliation project. It records the documentation landscape observed at a defined Git baseline before reconciliation or migration.

This is an inventory and traceability aid. It does **not** establish final authority, resolve technical conflicts, verify requirements, or decide what should be migrated.

### Interpretation rules

- **Observed location** is the repository and path where a document was found.
- **Likely authority** is an initial classification only.
- **Confidence** describes confidence in that classification, not confidence that the document is technically correct.
- **Confirmed authority** is not asserted unless repository evidence explicitly establishes it.
- `Unknown` or `Unclear` is used where evidence is insufficient.
- Relationships inferred from subject/path are marked as such; no undocumented traceability is asserted.
- **Potential duplicate / overlap** does not decide which document is authoritative.

## Indexing Baseline

| Repository | Branch inspected | Commit SHA |
|---|---|---|
| `LentonNeale/Karetao` | `doc/reconcile-karetao-mks` (created from `doc/documentation-framework`) | `bb473df6cf8df8f997181f3d02beeb143298d17a` |
| `LentonNeale/Arm_Sensor_Hub` | `main` | `a86f83036a3fb97450e661bf5b09557af4064274` |
| `LentonNeale/RaspberryPi_Sensor_Hub` | `main` | `087e6c3e0b102c8e32dbf0dace30376e38b26123` |

- **Index generated:** 2026-09-18
- **Indexing date:** 2026-09-18
- **Repositories:** 3
- **Karetao source baseline:** `doc/documentation-framework`
- **Karetao reconciliation branch:** `doc/reconcile-karetao-mks`
- **Requested Raspberry repository name:** `Raspberry_Sensor_Hub` was not found; the matching repository available is `LentonNeale/RaspberryPi_Sensor_Hub`.
- **Last modified commit/date:** not individually resolved for every file in this baseline pass. The repository commit above is the last-indexed baseline; future maintenance should resolve Git path history for changed entries.

## Repositories Indexed

### Karetao

Current `Documentation/**`, legacy `docs/project/**`, archived material, root documentation, and documentation-like files embedded in the repository tree were inspected.

### Arm Sensor Hub

`LentonNeale/Arm_Sensor_Hub`, branch `main`, commit `a86f83036a3fb97450e661bf5b09557af4064274`.

### Raspberry Sensor Hub

`LentonNeale/RaspberryPi_Sensor_Hub`, branch `main`, commit `087e6c3e0b102c8e32dbf0dace30376e38b26123`.

## Authority Classification

Allowed initial classifications:

`SYSTEM_REQUIREMENT`, `SYSTEM_ARCHITECTURE`, `SYSTEM_INTERFACE`, `COMPONENT_IMPLEMENTATION`, `COMPONENT_INTERFACE`, `VENDOR_EXTERNAL_REFERENCE`, `VERIFICATION_EVIDENCE`, `CONFIGURATION`, `SAFETY`, `DECISION`, `HISTORICAL`, `GOVERNANCE`, `UNKNOWN`, `MIXED`.

Physical repository location, filename, and commit recency are not treated as proof of authority.

## Karetao Documentation

**Repository:** `LentonNeale/Karetao`  
**Branch:** `doc/reconcile-karetao-mks`  
**Baseline commit:** `bb473df6cf8df8f997181f3d02beeb143298d17a`  
**Tree enumeration:** complete for this Git tree response  
**Indexed documentation-like files:** 112

| Path | Filename / title | Format | Category | Likely authority | Confidence | Status | Last indexed commit | Last modified commit/date | Document relationship | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/README.md` | README | MD | VENDOR_EXTERNAL_REFERENCE | VENDOR_EXTERNAL_REFERENCE | High | CURRENT / LEGACY | `bb473df6` | Unknown | motor/MKS family; sensor family | External/vendor reference; distinguish from project-owned protocol claims. |
| `Arm_Sensor_Hub/README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | sensor family | Implementation/developer reference |
| `Documentation/00_INDEX.md` | 00 INDEX | MD | GOVERNANCE | GOVERNANCE | High | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Framework governance; not technical authority. |
| `Documentation/01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md` | DOCUMENTATION AUTHORITY MODEL | MD | GOVERNANCE | GOVERNANCE | High | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Framework governance; not technical authority. |
| `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md` | SYSTEM ARCHITECTURE | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Architecture/system description |
| `Documentation/01_SYSTEM/SYSTEM_OVERVIEW.md` | SYSTEM OVERVIEW | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Architecture/system description |
| `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` | SYSTEM REQUIREMENTS | MD | SYSTEM_REQUIREMENT | SYSTEM_REQUIREMENT | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Intended requirement location; not evidence that requirements are complete. |
| `Documentation/01_SYSTEM/SYSTEM_SYNCHRONIZATION.md` | SYSTEM SYNCHRONIZATION | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Architecture/system description |
| `Documentation/01_SYSTEM/SYSTEM_TIMING.md` | SYSTEM TIMING | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Architecture/system description |
| `Documentation/02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md` | CAN SYSTEM INTERFACE | MD | MIXED | MIXED | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | CAN family | Interface material may combine system contract and component implementation |
| `Documentation/02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md` | HOST SYSTEM INTERFACE | MD | MIXED | MIXED | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Interface material may combine system contract and component implementation |
| `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | SPI SYSTEM INTERFACE | MD | MIXED | MIXED | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | SPI family | Interface material may combine system contract and component implementation |
| `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` | TIME SYSTEM INTERFACE | MD | MIXED | MIXED | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | timing/synchronization family | Interface material may combine system contract and component implementation |
| `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md` | ARM SENSOR HUB | MD | UNKNOWN | UNKNOWN | Low | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | sensor family | Requires content review |
| `Documentation/03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md` | COMPONENT DOCUMENTATION MODEL | MD | GOVERNANCE | GOVERNANCE | High | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Framework governance; not technical authority. |
| `Documentation/03_COMPONENTS/RASPBERRY_SENSOR_HUB.md` | RASPBERRY SENSOR HUB | MD | UNKNOWN | UNKNOWN | Low | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | sensor family; host/Raspberry Pi family | Requires content review |
| `Documentation/04_SAFETY/SAFETY_ARCHITECTURE.md` | SAFETY ARCHITECTURE | MD | SAFETY | SAFETY | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | safety family | Safety-related material |
| `Documentation/04_SAFETY/SAFETY_INTEGRATION.md` | SAFETY INTEGRATION | MD | SAFETY | SAFETY | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | safety family | Safety-related material |
| `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md` | SAFETY REQUIREMENTS | MD | SAFETY | SAFETY | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | safety family | Safety requirements/checklist |
| `Documentation/05_REFACTORING_RULES.md` | 05 REFACTORING RULES | MD | UNKNOWN | UNKNOWN | Low | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Requires content review |
| `Documentation/05_VERIFICATION/INTEGRATION_GATES.md` | INTEGRATION GATES | MD | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | verification family | Evidence classification requires later review. |
| `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` | SYSTEM VERIFICATION MATRIX | MD | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | verification family | Evidence classification requires later review. |
| `Documentation/05_VERIFICATION/VERIFICATION_STRATEGY.md` | VERIFICATION STRATEGY | MD | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | verification family | Evidence classification requires later review. |
| `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` | SYSTEM CONFIGURATION | MD | CONFIGURATION | CONFIGURATION | Medium | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Configuration reference |
| `Documentation/06_IMPLEMENTATION_CHECKLIST.md` | 06 IMPLEMENTATION CHECKLIST | MD | GOVERNANCE | GOVERNANCE | High | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Framework governance; not technical authority. |
| `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` | ARCHITECTURE DECISIONS | MD | DECISION | DECISION | High | CURRENT / FRAMEWORK OR LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `Documentation/99_ARCHIVE/CONVERSATIONS/.gitkeep.md` | .Gitkeep | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | No cross-document relationship established from path alone | Historical |
| `Documentation/99_ARCHIVE/DECISIONS/.gitkeep.md` | .Gitkeep | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | decision family | Historical |
| `Documentation/99_ARCHIVE/SPRINTS/.gitkeep.md` | .Gitkeep | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | No cross-document relationship established from path alone | Historical |
| `Documentation/99_ARCHIVE/SUPERSEDED/.gitkeep.md` | .Gitkeep | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | No cross-document relationship established from path alone | Historical |
| `README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `RaspberryPi_Sensor_Hub/README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | sensor family; host/Raspberry Pi family | Implementation/developer reference |
| `docs/project/QUESTIONS.md` | QUESTIONS | MD | GOVERNANCE | GOVERNANCE | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Project/process/history material; may contain technical claims |
| `docs/project/README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `docs/project/SD/SD-01.md` | SD 01 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-02.md` | SD 02 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-03.md` | SD 03 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-04.md` | SD 04 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-05.md` | SD 05 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-06.md` | SD 06 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-07.md` | SD 07 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-08.md` | SD 08 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-09.md` | SD 09 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-10.md` | SD 10 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-11.md` | SD 11 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-12.md` | SD 12 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-13.md` | SD 13 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-14.md` | SD 14 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-15.md` | SD 15 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-16.md` | SD 16 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-17.md` | SD 17 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-18.md` | SD 18 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-19.md` | SD 19 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-20.md` | SD 20 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-21.md` | SD 21 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-22.md` | SD 22 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-23.md` | SD 23 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-24.md` | SD 24 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-25.md` | SD 25 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SD/SD-26.md` | SD 26 | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/SYSTEM_DECISIONS.md` | SYSTEM DECISIONS | MD | DECISION | DECISION | High | CURRENT / LEGACY | `bb473df6` | Unknown | decision family | Decision record; not a requirement |
| `docs/project/archive/Agent_messages/Agent_message_engr` | Agent Message Engr | TEXT | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | No cross-document relationship established from path alone | Historical |
| `docs/project/archive/Agent_messages/Agent_message_engr_response` | Agent Message Engr Response | TEXT | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | No cross-document relationship established from path alone | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_BRIEF.md` | CTO DECISION BRIEF | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family; decision family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_FINAL.md` | CTO DECISION FINAL | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family; decision family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/DeepSeek.md` | DeepSeek | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/GPT.md` | GPT | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/InterAgent_Chat.md` | InterAgent Chat | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Module_TODOs/CAN_Module_TODO.md` | CAN Module TODO | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | CAN family; sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/Architecture_and_Runtime_Flow.md` | Architecture And Runtime Flow | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | timing/synchronization family; sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/Development_Setup_and_Workflow.md` | Development Setup And Workflow | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/First_Week_Guide.md` | First Week Guide | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/Project_Orientation.md` | Project Orientation | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/README.md` | README | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/PHASE_1_FINAL_CLEARANCE_REPORT.md` | PHASE 1 FINAL CLEARANCE REPORT | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/PROJECT_BASELINE.md` | PROJECT BASELINE | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/README.md` | README | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/SPI_CONTRACT.md` | SPI CONTRACT | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | SPI family; sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/SPI_PAYLOAD_SCHEMA.md` | SPI PAYLOAD SCHEMA | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | SPI family; sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/SPI_SERVICE_CONTRACT.md` | SPI SERVICE CONTRACT | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | SPI family; sensor family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Sprint Info/Sprint_2_Readiness_Report.md` | Sprint 2 Readiness Report | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family; verification family | Historical |
| `docs/project/archive/Arm_Sensor_Hub/Documentation/Sprint_1_List.md` | Sprint 1 List | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | sensor family | Historical |
| `docs/project/archive/RaspberryPi_Sensor_Hub/docs/spi.md` | Spi | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | SPI family; sensor family; host/Raspberry Pi family | Historical |
| `docs/project/archive/agent_messages/2026-09-08-spi-options-engineering-assessment.md` | 2026 09 08 Spi Options Engineering Assessment | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | SPI family | Historical |
| `docs/project/archive/docs/RASPBERRY_PI_BRINGUP_V0.md` | RASPBERRY PI BRINGUP V0 | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | host/Raspberry Pi family | Historical |
| `docs/project/archive/docs/proposed_phase2.md` | Proposed Phase2 | MD | HISTORICAL | HISTORICAL | High | ARCHIVED | `bb473df6` | Unknown | No cross-document relationship established from path alone | Historical |
| `docs/project/firmware/APP_OVERVIEW.md` | APP OVERVIEW | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `docs/project/firmware/BUILD_CONTRACT.md` | BUILD CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/CALIBRATION_CONTRACT.md` | CALIBRATION CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md` | CAN BIT TIMING EVIDENCE | MD | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | CAN family; verification family | Evidence classification requires later review. |
| `docs/project/firmware/CAN_SERVICE_CONTRACT.md` | CAN SERVICE CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | CAN family | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/CONTRACT_STATUS.md` | CONTRACT STATUS | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/CONTRACT_V1_FREEZE.md` | CONTRACT V1 FREEZE | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/ERROR_HANDLING_STRATEGY.md` | ERROR HANDLING STRATEGY | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/HEALTH_MONITOR_CONTRACT.md` | HEALTH MONITOR CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/I2C_MANAGER_CONTRACT.md` | I2C MANAGER CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/JOINT_MAPPING_CONTRACT.md` | JOINT MAPPING CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/LIFECYCLE_CONTRACT.md` | LIFECYCLE CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/MOTOR_SERVICE_CONTRACT.md` | MOTOR SERVICE CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | motor/MKS family | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/MULTI_SENSOR_CONTRACT.md` | MULTI SENSOR CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | sensor family | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/SAFETY_RELEASE_CHECKLIST.md` | SAFETY RELEASE CHECKLIST | MD | SAFETY | SAFETY | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | safety family | Safety requirements/checklist |
| `docs/project/firmware/SNAPSHOT_COHERENCY_CONTRACT.md` | SNAPSHOT COHERENCY CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md` | TIMESTAMP SYNC CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | timing/synchronization family | Contract/behavior material spanning system and component domains |
| `docs/project/hardware/arm-sensor-hub-baseline.md` | Arm Sensor Hub Baseline | MD | UNKNOWN | UNKNOWN | Low | CURRENT / LEGACY | `bb473df6` | Unknown | sensor family | Requires content review |
| `docs/project/interfaces/raspberry-pi-spi.md` | Raspberry Pi Spi | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | SPI family; host/Raspberry Pi family | Interface material may combine system contract and component implementation |
| `docs/project/interfaces/spi-service-contract.md` | Spi Service Contract | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | SPI family | Interface material may combine system contract and component implementation |
| `docs/project/operations/RASPBERRY_PI_BRINGUP_V0.1.md` | RASPBERRY PI BRINGUP V0.1 | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | host/Raspberry Pi family | Implementation/developer reference |
| `docs/project/protocols/spi-contract.md` | Spi Contract | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | SPI family | Interface material may combine system contract and component implementation |
| `docs/project/protocols/spi-payload-schema.md` | Spi Payload Schema | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | SPI family | Interface material may combine system contract and component implementation |
| `docs/project/system/TODO_List.md` | TODO List | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Architecture/system description |
| `docs/project/system/architecture.md` | Architecture | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Architecture/system description |
| `docs/project/system/development.md` | Development | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / LEGACY | `bb473df6` | Unknown | No cross-document relationship established from path alone | Architecture/system description |

## Arm Sensor Hub Documentation

**Repository:** `LentonNeale/Arm_Sensor_Hub`  
**Branch:** `main`  
**Baseline commit:** `a86f83036a3fb97450e661bf5b09557af4064274`  
**Tree enumeration:** complete for this Git tree response  
**Indexed documentation-like files:** 43

| Path | Filename / title | Format | Category | Likely authority | Confidence | Status | Last indexed commit | Last modified commit/date | Document relationship | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `Documentation/APP_OVERVIEW.md` | APP OVERVIEW | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `Documentation/BUILD_CONTRACT.md` | BUILD CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/CALIBRATION_CONTRACT.md` | CALIBRATION CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/CAN_BIT_TIMING_EVIDENCE.md` | CAN BIT TIMING EVIDENCE | MD | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | CAN family; verification family | Evidence classification requires later review. |
| `Documentation/CAN_Module_Developer_Guide.md` | CAN Module Developer Guide | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | CAN family | Implementation/developer reference |
| `Documentation/CAN_SERVICE_CONTRACT.md` | CAN SERVICE CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | CAN family | Contract/behavior material spanning system and component domains |
| `Documentation/CONTRACT_STATUS.md` | CONTRACT STATUS | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/CONTRACT_V1_FREEZE.md` | CONTRACT V1 FREEZE | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/Conversations/CTO_DECISION_BRIEF.md` | CTO DECISION BRIEF | MD | HISTORICAL | HISTORICAL | High | HISTORICAL | `a86f8303` | Unknown | decision family | Historical |
| `Documentation/Conversations/CTO_DECISION_FINAL.md` | CTO DECISION FINAL | MD | HISTORICAL | HISTORICAL | High | HISTORICAL | `a86f8303` | Unknown | decision family | Historical |
| `Documentation/Conversations/DeepSeek.md` | DeepSeek | MD | HISTORICAL | HISTORICAL | High | HISTORICAL | `a86f8303` | Unknown | No cross-document relationship established from path alone | Historical |
| `Documentation/Conversations/GPT.md` | GPT | MD | HISTORICAL | HISTORICAL | High | HISTORICAL | `a86f8303` | Unknown | No cross-document relationship established from path alone | Historical |
| `Documentation/Conversations/InterAgent_Chat.md` | InterAgent Chat | MD | HISTORICAL | HISTORICAL | High | HISTORICAL | `a86f8303` | Unknown | No cross-document relationship established from path alone | Historical |
| `Documentation/ERROR_HANDLING_STRATEGY.md` | ERROR HANDLING STRATEGY | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/HEALTH_MONITOR_CONTRACT.md` | HEALTH MONITOR CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/I2C_MANAGER_CONTRACT.md` | I2C MANAGER CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/JOINT_MAPPING_CONTRACT.md` | JOINT MAPPING CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/LIFECYCLE_CONTRACT.md` | LIFECYCLE CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/MOTOR_SERVICE_CONTRACT.md` | MOTOR SERVICE CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | motor/MKS family | Contract/behavior material spanning system and component domains |
| `Documentation/MULTI_SENSOR_CONTRACT.md` | MULTI SENSOR CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | sensor family | Contract/behavior material spanning system and component domains |
| `Documentation/Module_TODOs/CAN_Module_TODO.md` | CAN Module TODO | MD | GOVERNANCE | GOVERNANCE | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | CAN family | Project/process/history material; may contain technical claims |
| `Documentation/Module_TODOs/CAN_Service_Copilot_Implementation_Recommendations.md` | CAN Service Copilot Implementation Recommendations | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | CAN family | Contract/behavior material spanning system and component domains |
| `Documentation/OnboardingDocs/Architecture_and_Runtime_Flow.md` | Architecture And Runtime Flow | MD | SYSTEM_ARCHITECTURE | SYSTEM_ARCHITECTURE | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | timing/synchronization family | Architecture/system description |
| `Documentation/OnboardingDocs/Development_Setup_and_Workflow.md` | Development Setup And Workflow | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `Documentation/OnboardingDocs/First_Week_Guide.md` | First Week Guide | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `Documentation/OnboardingDocs/Project_Orientation.md` | Project Orientation | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `Documentation/OnboardingDocs/README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `Documentation/PHASE_1_FINAL_CLEARANCE_REPORT.md` | PHASE 1 FINAL CLEARANCE REPORT | MD | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Evidence classification requires later review. |
| `Documentation/PROJECT_BASELINE.md` | PROJECT BASELINE | MD | GOVERNANCE | GOVERNANCE | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Project/process/history material; may contain technical claims |
| `Documentation/RASPBERRY_PI_BRINGUP.md` | RASPBERRY PI BRINGUP | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | host/Raspberry Pi family | Implementation/developer reference |
| `Documentation/README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `Documentation/ROS2_CALIBRATION_ARCHITECTURE_REPORT.md` | ROS2 CALIBRATION ARCHITECTURE REPORT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/SAFETY_RELEASE_CHECKLIST.md` | SAFETY RELEASE CHECKLIST | MD | SAFETY | SAFETY | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | safety family | Safety requirements/checklist |
| `Documentation/SNAPSHOT_COHERENCY_CONTRACT.md` | SNAPSHOT COHERENCY CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Contract/behavior material spanning system and component domains |
| `Documentation/SPI_CONTRACT.md` | SPI CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | SPI family | Contract/behavior material spanning system and component domains |
| `Documentation/SPI_PAYLOAD_SCHEMA.md` | SPI PAYLOAD SCHEMA | MD | UNKNOWN | UNKNOWN | Low | CURRENT / LEGACY | `a86f8303` | Unknown | SPI family | Requires content review |
| `Documentation/SPI_SERVICE_CONTRACT.md` | SPI SERVICE CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | SPI family | Contract/behavior material spanning system and component domains |
| `Documentation/Sprint Info/Sprint_2_Readiness_Report.md` | Sprint 2 Readiness Report | MD | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | verification family | Evidence classification requires later review. |
| `Documentation/Sprint_1_List.md` | Sprint 1 List | MD | GOVERNANCE | GOVERNANCE | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Project/process/history material; may contain technical claims |
| `Documentation/TIMESTAMP_SYNC_CONTRACT.md` | TIMESTAMP SYNC CONTRACT | MD | MIXED | MIXED | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | timing/synchronization family | Contract/behavior material spanning system and component domains |
| `Middlewares/Third_Party/MksServo/README.md` | README | MD | VENDOR_EXTERNAL_REFERENCE | VENDOR_EXTERNAL_REFERENCE | High | CURRENT / LEGACY | `a86f8303` | Unknown | motor/MKS family | External/vendor reference; distinguish from project-owned protocol claims. |
| `README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `a86f8303` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |
| `docs/third party manuals/Mks protocol.md` | Mks Protocol | MD | VENDOR_EXTERNAL_REFERENCE | VENDOR_EXTERNAL_REFERENCE | High | CURRENT / LEGACY | `a86f8303` | Unknown | motor/MKS family | External/vendor reference; distinguish from project-owned protocol claims. |

## Raspberry Sensor Hub Documentation

**Repository:** `LentonNeale/RaspberryPi_Sensor_Hub`  
**Branch:** `main`  
**Baseline commit:** `087e6c3e0b102c8e32dbf0dace30376e38b26123`  
**Tree enumeration:** complete for this Git tree response  
**Indexed documentation-like files:** 1

| Path | Filename / title | Format | Category | Likely authority | Confidence | Status | Last indexed commit | Last modified commit/date | Document relationship | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `README.md` | README | MD | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Medium | CURRENT / LEGACY | `087e6c3e` | Unknown | No cross-document relationship established from path alone | Implementation/developer reference |

## Current Documentation Framework

The following framework destinations are present in the Karetao baseline:

- `Documentation/00_INDEX.md`
- `Documentation/01_SYSTEM/**`
- `Documentation/02_INTERFACES/**`
- `Documentation/03_COMPONENTS/**`
- `Documentation/04_SAFETY/**`
- `Documentation/05_VERIFICATION/**`
- `Documentation/06_CONFIGURATION/**`
- `Documentation/07_DECISIONS/**`
- `Documentation/99_ARCHIVE/**`
- `Documentation/05_REFACTORING_RULES.md`
- `Documentation/06_IMPLEMENTATION_CHECKLIST.md`

Framework files are indexed as current/template/governance material and are not treated as proof that corresponding legacy content has been migrated.

## Legacy Documentation

Karetao legacy material is concentrated under `docs/project/**`, including questions, system decisions, firmware contracts, hardware baselines, interface/protocol descriptions, bring-up material, and historical archives.

## Archived Documentation

Karetao archive material exists under both `Documentation/99_ARCHIVE/**` and `docs/project/archive/**`. Arm and Raspberry historical copies, conversation records, engineering assessments, and earlier bring-up material remain indexed because they may contain useful historical technical information.

## Cross-Repository Interfaces

### SPI

Observed family:

- Karetao system: `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`.
- Karetao legacy: `docs/project/interfaces/spi-service-contract.md`, `docs/project/protocols/spi-contract.md`, `docs/project/protocols/spi-payload-schema.md`, `docs/project/interfaces/raspberry-pi-spi.md`.
- Arm: `Documentation/SPI_CONTRACT.md`, `Documentation/SPI_SERVICE_CONTRACT.md`, `Documentation/SPI_PAYLOAD_SCHEMA.md`.
- Historical archived SPI copies also exist.

Potential relationship: Karetao system interface → Arm SPI implementation/contract → Raspberry Pi host implementation. This is a subject-level relationship, not confirmed traceability.

### CAN

Observed family:

- Karetao system: `Documentation/02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md`.
- Karetao legacy: CAN service contract and CAN bit-timing evidence.
- Arm: `Documentation/CAN_SERVICE_CONTRACT.md`, `Documentation/CAN_Module_Developer_Guide.md`, `Documentation/CAN_BIT_TIMING_EVIDENCE.md`.
- Arm external reference: `docs/third party manuals/Mks protocol.md`.

Potential relationship: Karetao system CAN interface → Arm CAN implementation/contract → MKS controller protocol reference.

### Host / Raspberry Pi

Observed family:

- Karetao: host interface, Raspberry component, and `docs/project/operations/RASPBERRY_PI_BRINGUP_V0.1.md`.
- Arm: `Documentation/RASPBERRY_PI_BRINGUP.md` and SPI contracts.
- Raspberry repository: `README.md` only at the indexed baseline.

The sparse Raspberry repository documentation is an inventory observation, not a conclusion about implementation completeness.

### Time synchronization

Observed family:

- Karetao framework: `SYSTEM_TIMING.md`, `SYSTEM_SYNCHRONIZATION.md`, and TIME interface.
- Karetao legacy: `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md`.
- Arm: `Documentation/TIMESTAMP_SYNC_CONTRACT.md`.

The Arm timestamp contract states that Raspberry Pi time is authoritative; this is recorded as a documented claim and is not independently verified by this index.

## Potentially Mixed-Authority Documents

Initial mixed-authority candidates include system/component contracts, interface/protocol documents, project baselines, and analysis records whose content can span more than one authority domain.

Notable families:

- `docs/project/firmware/*_CONTRACT.md`
- `docs/project/interfaces/*`
- `docs/project/protocols/*`
- Arm `Documentation/*_CONTRACT.md`
- `Documentation/PROJECT_BASELINE.md`
- `Documentation/ROS2_CALIBRATION_ARCHITECTURE_REPORT.md`
- selected conversation/agent material containing design recommendations alongside recorded facts.

These documents are not split, rewritten, moved, or declared authoritative during indexing.

## Potential Duplicates / Overlaps

| Subject | Observed overlap |
|---|---|
| SPI | Karetao system/legacy SPI documents + Arm SPI contract/service/payload documents + archived copies |
| CAN | Karetao system/legacy CAN documents + Arm CAN service/developer documents |
| CAN timing | Karetao and Arm CAN timing evidence |
| Time synchronization | Karetao framework + legacy timestamp contract + Arm timestamp contract |
| Raspberry bring-up | Karetao V0.1 + archived V0 + Arm bring-up document |
| Sensor contracts | Karetao legacy multi-sensor contract + Arm multi-sensor contract |
| Motor semantics | Karetao/Arm motor service material + MKS protocol reference |
| Safety/release | Karetao safety framework + Arm safety/release material |
| Decisions | SD-01..SD-26 + aggregated system decisions + Arm decision/conversation material |
| Onboarding | Current Arm onboarding + archived onboarding copies |

These are **Potential duplicate / overlap** cases only.

## Verification Documentation

The intended Karetao system-level verification location is:

`Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`

Other evidence includes integration gates, verification strategy, CAN timing evidence, Arm phase-clearance reporting, sprint readiness reporting, commissioning/bring-up results, and historical validation records.

Evidence class remains provisional. Component verification is not automatically system verification.

## Requirements Documentation

### Explicit requirement destinations

- `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`
- `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md`

### Requirement-bearing documents

Many contracts contain normative requirement statements without a stable `REQ-*` identifier scheme. These include SPI, CAN, lifecycle, sensor, motor, time, health, error-handling, calibration, and safety contracts.

No stable `REQ-*` identifier scheme was established by this indexing pass. `SD-01` through `SD-26` are decision identifiers, not requirement identifiers. Requirement extraction and reconciliation are deferred to the next phase.

## Timing and Synchronization Documentation

Primary sources are Karetao system timing/synchronization documents, Karetao legacy timestamp and SPI timing material, Arm timestamp synchronization and CAN timing evidence, and historical engineering assessments.

## Safety Documentation

Primary sources are Karetao `Documentation/04_SAFETY/**`, Arm `SAFETY_RELEASE_CHECKLIST.md`, and safety clauses embedded in CAN, motor, lifecycle, health, and error-handling contracts.

The index does not determine the applicable safety standard, required performance level, or whether stated safety behavior is independently verified.

## Open Classification Questions

1. Which document is confirmed owner of each system-level interface: SPI, CAN, host, and time synchronization?
2. Which contract statements are system requirements versus component implementation constraints?
3. Which Arm documents contain component authority versus system-level claims?
4. Which MKS material is vendor reference versus project-derived protocol interpretation?
5. Which readiness/clearance/test records provide component, integration, or system verification evidence?
6. Which decision records explicitly supersede earlier decisions?
7. Is the sparse `RaspberryPi_Sensor_Hub` documentation intentional or incomplete?
8. Are archived copies exact historical snapshots or edited extracts?

## Initial Counts

Counts are based on the indexed Git tree and provisional path-based classification.

- Karetao documents indexed: 112
- Arm Sensor Hub documents indexed: 43
- Raspberry Sensor Hub documents indexed: 1
- Total documents indexed: 156
- Likely mixed-authority documents: 40
- Explicit requirement-category documents: 1
- Explicit safety-requirement/checklist documents: 3
- Interface-related documents: 24
- Verification/evidence/readiness documents: 7
- Potential overlap families: 10
- Unresolved classification/authority questions: 8

## Validation

### Repository coverage

- [x] Karetao indexed.
- [x] Arm Sensor Hub indexed.
- [x] Raspberry Sensor Hub indexed.
- [x] Karetao target branch `doc/reconcile-karetao-mks` created from `doc/documentation-framework`.

### Documentation coverage

- [x] Current Karetao framework indexed.
- [x] Karetao legacy documentation indexed.
- [x] Relevant archived documentation indexed.
- [x] Arm documentation indexed.
- [x] Raspberry documentation indexed.
- [x] Documentation-like conversation/agent files discovered in the Karetao archive were included.
- [x] Vendor/external MKS reference identified separately.

### Classification

- [x] Authority classifications are explicit.
- [x] Mixed-authority candidates are identified.
- [x] Uncertain classifications are marked.
- [x] Verification evidence is distinguished from requirement-category documents.
- [x] Vendor references are distinguished from project authority.

### Traceability

- [x] Repository branches recorded.
- [x] Repository commit SHAs recorded.
- [x] Repository-relative paths are exact for the indexed Git tree baseline.
- [x] No fabricated files or relationships were added.
- [x] Potential overlaps are identified.
- [ ] Per-file last-modified commit/date was not individually resolved; future maintenance should resolve it for changed entries.

### Scope

- [x] No documentation was moved.
- [x] No documentation was deleted.
- [x] No requirements were rewritten.
- [x] No source code was changed.
- [x] No tests were changed.
- [x] No submodules were changed.
- [x] No vendor files were added.
- [x] Only the documentation index is intended to be committed.

## Index Maintenance

`Documentation/DOCUMENTATION_INDEX.md` is the persistent documentation inventory for the reconciliation project. It must be updated when relevant documentation files are added, removed, renamed, or materially changed.

Future workflow:

```text
Repository change
        ↓
Detect changed documentation
        ↓
Review affected index entries
        ↓
Update DOCUMENTATION_INDEX.md
        ↓
Continue reconciliation
```

When updating:

1. Inspect the previous index.
2. Identify the previous repository commit baseline.
3. Compare the current repository state.
4. Identify added files.
5. Identify removed files.
6. Identify renamed files.
7. Identify materially changed documentation.
8. Update affected entries.
9. Preserve classifications that remain valid.
10. Flag classifications that may require re-evaluation after substantive changes.

Git history is supporting evidence only. Do not infer authority from commit recency.

## Change Detection Fields

Each entry records the repository baseline as **Last indexed commit**. **Last modified commit/date** is `Unknown` where it was not resolved during this baseline generation. Future updates should populate it for changed files using path-specific Git history where practical.

A content hash may be added later if Git commit/path history proves insufficient; it is not required for this baseline.

## Scope Boundary

This phase performed indexing only. It did not:

- migrate documentation;
- rewrite legacy documents;
- move files;
- delete files;
- change requirements;
- change firmware or source code;
- change tests;
- change generated files;
- modify submodules;
- modify vendor documentation;
- resolve technical conflicts;
- declare requirements verified;
- declare implementation compliant.

