# Karetao Documentation Content Classification

## Purpose

This file records the content-level classification of every documentation-like item in `Documentation/DOCUMENTATION_INDEX.md`. It refines the index's initial/path-oriented classification by examining the statements actually present at the indexed repository baselines.

This is an analysis artifact. It does not migrate, rewrite, relocate, delete, or otherwise alter source documentation.

## Classification Method

Each indexed document was inspected at the repository baseline recorded by the index. Classification was based on substantive statements, their subject, and their role. Filename, directory, repository location, and commit recency were not used as authority by themselves.

Normative statements were separated from implementation descriptions, observed/tested behavior, configuration, decision rationale, historical material, governance/process content, and vendor-defined behavior. Where a document contains materially different domains, it is classified `MIXED` and its significant content groups are listed separately below.

Framework placeholders were treated according to their actual content. For example, a file named `SYSTEM_REQUIREMENTS.md` containing only a placeholder for a future authority location is classified as `GOVERNANCE`, not `SYSTEM_REQUIREMENT`.

## Authority Model

- **Karetao:** system requirements, system architecture, system interfaces, system timing/synchronization, system safety requirements, system configuration requirements, system integration requirements, system-level verification status, and system-level component roles.
- **Arm Sensor Hub:** STM32 firmware implementation, component architecture/interfaces, sensor/CAN/MKS/SPI implementation, component configuration, diagnostics, and component-level verification.
- **Raspberry Sensor Hub:** Raspberry-side implementation, host interfaces, configuration, diagnostics, and component-level verification.
- **Vendor / external:** MKS controller behavior, external protocol definitions, equipment specifications, and other externally owned behavior.
- **Verification Evidence:** tests, measurements, observations, readiness and validation records are evidence; they do not by themselves redefine requirements.
- **Decision:** records a decision and rationale/status; a decision may contain requirement-bearing statements, but its document-level role remains `DECISION`.
- **Historical:** archived/superseded context is preserved as history and is not treated as current normative authority.

## Classification Summary

| Classification | Documents |
|---|---:|
| MIXED | 45 |
| GOVERNANCE | 29 |
| HISTORICAL | 30 |
| DECISION | 27 |
| COMPONENT_IMPLEMENTATION | 16 |
| VERIFICATION_EVIDENCE | 4 |
| VENDOR_EXTERNAL_REFERENCE | 3 |
| SAFETY | 2 |
| SYSTEM_REQUIREMENT | 0 |
| SYSTEM_ARCHITECTURE | 0 |
| SYSTEM_INTERFACE | 0 |
| COMPONENT_INTERFACE | 0 |
| CONFIGURATION | 0 |
| UNKNOWN | 0 |

The document-level result contains **45 MIXED documents**. There are no document-level pure `SYSTEM_REQUIREMENT`, `SYSTEM_ARCHITECTURE`, `SYSTEM_INTERFACE`, `COMPONENT_INTERFACE`, or `CONFIGURATION` documents at this baseline. Those authority domains are nevertheless present as statement groups inside mixed documents and decision records. No document required `UNKNOWN` after content review.

## Document-Level Classification

| Repository | Source path | Document title | Current index classification | Content-level classification | Authority owner | Confidence | Rationale | Potential destination |
|---|---|---|---|---|---|---|---|---|
| LentonNeale/Karetao | `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/README.md` | README | VENDOR_EXTERNAL_REFERENCE | VENDOR_EXTERNAL_REFERENCE | MKS/vendor | HIGH | Describes externally defined MKS protocol/equipment behavior. | External/vendor reference; not Karetao-owned |
| LentonNeale/Karetao | `Arm_Sensor_Hub/README.md` | README | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Karetao | `Documentation/00_INDEX.md` | 00 INDEX | GOVERNANCE | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md` | DOCUMENTATION AUTHORITY MODEL | GOVERNANCE | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md` | SYSTEM ARCHITECTURE | SYSTEM_ARCHITECTURE | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_ARCHITECTURE. The placeholder names the future authoritative destination but contains no substantive SYSTEM_ARCHITECTURE content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/01_SYSTEM/SYSTEM_OVERVIEW.md` | SYSTEM OVERVIEW | SYSTEM_ARCHITECTURE | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_OVERVIEW. The placeholder names the future authoritative destination but contains no substantive SYSTEM_OVERVIEW content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` | SYSTEM REQUIREMENTS | SYSTEM_REQUIREMENT | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_REQUIREMENT. The placeholder names the future authoritative destination but contains no substantive SYSTEM_REQUIREMENT content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/01_SYSTEM/SYSTEM_SYNCHRONIZATION.md` | SYSTEM SYNCHRONIZATION | SYSTEM_ARCHITECTURE | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_SYNCHRONIZATION. The placeholder names the future authoritative destination but contains no substantive SYSTEM_SYNCHRONIZATION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/01_SYSTEM/SYSTEM_TIMING.md` | SYSTEM TIMING | SYSTEM_ARCHITECTURE | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_TIMING. The placeholder names the future authoritative destination but contains no substantive SYSTEM_TIMING content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md` | CAN SYSTEM INTERFACE | MIXED | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_INTERFACE. The placeholder names the future authoritative destination but contains no substantive SYSTEM_INTERFACE content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md` | HOST SYSTEM INTERFACE | MIXED | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_INTERFACE. The placeholder names the future authoritative destination but contains no substantive SYSTEM_INTERFACE content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | SPI SYSTEM INTERFACE | MIXED | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_INTERFACE. The placeholder names the future authoritative destination but contains no substantive SYSTEM_INTERFACE content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` | TIME SYSTEM INTERFACE | MIXED | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_INTERFACE. The placeholder names the future authoritative destination but contains no substantive SYSTEM_INTERFACE content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md` | ARM SENSOR HUB | UNKNOWN | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_COMPONENT_DEFINITION. The placeholder names the future authoritative destination but contains no substantive SYSTEM_COMPONENT_DEFINITION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md` | COMPONENT DOCUMENTATION MODEL | GOVERNANCE | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/03_COMPONENTS/RASPBERRY_SENSOR_HUB.md` | RASPBERRY SENSOR HUB | UNKNOWN | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_COMPONENT_DEFINITION. The placeholder names the future authoritative destination but contains no substantive SYSTEM_COMPONENT_DEFINITION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/04_SAFETY/SAFETY_ARCHITECTURE.md` | SAFETY ARCHITECTURE | SAFETY | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SAFETY. The placeholder names the future authoritative destination but contains no substantive SAFETY content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/04_SAFETY/SAFETY_INTEGRATION.md` | SAFETY INTEGRATION | SAFETY | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SAFETY. The placeholder names the future authoritative destination but contains no substantive SAFETY content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md` | SAFETY REQUIREMENTS | SAFETY | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SAFETY_REQUIREMENT. The placeholder names the future authoritative destination but contains no substantive SAFETY_REQUIREMENT content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/05_REFACTORING_RULES.md` | 05 REFACTORING RULES | UNKNOWN | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/05_VERIFICATION/INTEGRATION_GATES.md` | INTEGRATION GATES | VERIFICATION_EVIDENCE | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_VERIFICATION. The placeholder names the future authoritative destination but contains no substantive SYSTEM_VERIFICATION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` | SYSTEM VERIFICATION MATRIX | VERIFICATION_EVIDENCE | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_VERIFICATION. The placeholder names the future authoritative destination but contains no substantive SYSTEM_VERIFICATION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/05_VERIFICATION/VERIFICATION_STRATEGY.md` | VERIFICATION STRATEGY | VERIFICATION_EVIDENCE | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_VERIFICATION. The placeholder names the future authoritative destination but contains no substantive SYSTEM_VERIFICATION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` | SYSTEM CONFIGURATION | CONFIGURATION | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: SYSTEM_CONFIGURATION. The placeholder names the future authoritative destination but contains no substantive SYSTEM_CONFIGURATION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/06_IMPLEMENTATION_CHECKLIST.md` | 06 IMPLEMENTATION CHECKLIST | GOVERNANCE | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` | ARCHITECTURE DECISIONS | DECISION | GOVERNANCE | Karetao | HIGH | Current content is GOVERNANCE / framework placeholder; intended authority: DECISION. The placeholder names the future authoritative destination but contains no substantive DECISION content at this baseline. | Already in intended destination |
| LentonNeale/Karetao | `Documentation/99_ARCHIVE/CONVERSATIONS/.gitkeep.md` | .Gitkeep | HISTORICAL | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/99_ARCHIVE/DECISIONS/.gitkeep.md` | .Gitkeep | HISTORICAL | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/99_ARCHIVE/SPRINTS/.gitkeep.md` | .Gitkeep | HISTORICAL | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `Documentation/99_ARCHIVE/SUPERSEDED/.gitkeep.md` | .Gitkeep | HISTORICAL | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `README.md` | README | COMPONENT_IMPLEMENTATION | MIXED | Karetao | HIGH | Repository-level overview of the Karetao robotic arm platform, STM32 control/comms firmware, Raspberry Pi host-side integration, ROS 2 components, repository structure, and project documentation organization. It is Karetao-level system/documentation architecture and governance content, not Raspberry Sensor Hub implementation documentation. | Retain as Karetao root README; canonical engineering detail remains under `docs/project/` |
| LentonNeale/Karetao | `RaspberryPi_Sensor_Hub/README.md` | README | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Raspberry Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/RaspberryPi_Sensor_Hub documentation |
| LentonNeale/Karetao | `docs/project/QUESTIONS.md` | QUESTIONS | GOVERNANCE | GOVERNANCE | Karetao documentation governance | HIGH | Content governs documentation/process or defines a framework destination rather than technical behavior. | Documentation/00_INDEX.md or applicable framework governance document |
| LentonNeale/Karetao | `docs/project/README.md` | README | COMPONENT_IMPLEMENTATION | MIXED | Karetao | HIGH | Defines the canonical Karetao project documentation structure and substantive system documentation areas including architecture, decisions, hardware baseline, interfaces, protocols, firmware contracts, safety, operations, and authority. Its governance role is coupled to the organization of the engineering system documentation. | `docs/project/README.md` — already the canonical project-documentation destination |
| LentonNeale/Karetao | `docs/project/SD/SD-01.md` | SD 01 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-02.md` | SD 02 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-03.md` | SD 03 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-04.md` | SD 04 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-05.md` | SD 05 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-06.md` | SD 06 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-07.md` | SD 07 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-08.md` | SD 08 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-09.md` | SD 09 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-10.md` | SD 10 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-11.md` | SD 11 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-12.md` | SD 12 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-13.md` | SD 13 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-14.md` | SD 14 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-15.md` | SD 15 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-16.md` | SD 16 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-17.md` | SD 17 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-18.md` | SD 18 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-19.md` | SD 19 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-20.md` | SD 20 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-21.md` | SD 21 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-22.md` | SD 22 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-23.md` | SD 23 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-24.md` | SD 24 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-25.md` | SD 25 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SD/SD-26.md` | SD 26 | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/SYSTEM_DECISIONS.md` | SYSTEM DECISIONS | DECISION | DECISION | Karetao | HIGH | Records a project decision and rationale/status rather than serving as a pure requirement. | Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md |
| LentonNeale/Karetao | `docs/project/archive/Agent_messages/Agent_message_engr` | Agent Message Engr | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Agent_messages/Agent_message_engr_response` | Agent Message Engr Response | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_BRIEF.md` | CTO DECISION BRIEF | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_FINAL.md` | CTO DECISION FINAL | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/DeepSeek.md` | DeepSeek | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/GPT.md` | GPT | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Conversations/InterAgent_Chat.md` | InterAgent Chat | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Module_TODOs/CAN_Module_TODO.md` | CAN Module TODO | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/Architecture_and_Runtime_Flow.md` | Architecture And Runtime Flow | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/Development_Setup_and_Workflow.md` | Development Setup And Workflow | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/First_Week_Guide.md` | First Week Guide | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/Project_Orientation.md` | Project Orientation | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/OnboardingDocs/README.md` | README | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/PHASE_1_FINAL_CLEARANCE_REPORT.md` | PHASE 1 FINAL CLEARANCE REPORT | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/PROJECT_BASELINE.md` | PROJECT BASELINE | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/README.md` | README | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/SPI_CONTRACT.md` | SPI CONTRACT | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/SPI_PAYLOAD_SCHEMA.md` | SPI PAYLOAD SCHEMA | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/SPI_SERVICE_CONTRACT.md` | SPI SERVICE CONTRACT | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Sprint Info/Sprint_2_Readiness_Report.md` | Sprint 2 Readiness Report | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/Arm_Sensor_Hub/Documentation/Sprint_1_List.md` | Sprint 1 List | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/RaspberryPi_Sensor_Hub/docs/spi.md` | Spi | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/agent_messages/2026-09-08-spi-options-engineering-assessment.md` | 2026 09 08 Spi Options Engineering Assessment | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/docs/RASPBERRY_PI_BRINGUP_V0.md` | RASPBERRY PI BRINGUP V0 | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/archive/docs/proposed_phase2.md` | Proposed Phase2 | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Karetao | `docs/project/firmware/APP_OVERVIEW.md` | APP OVERVIEW | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Karetao | `docs/project/firmware/BUILD_CONTRACT.md` | BUILD CONTRACT | MIXED | MIXED | Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm Sensor Hub documentation; component configuration; component verification |
| LentonNeale/Karetao | `docs/project/firmware/CALIBRATION_CONTRACT.md` | CALIBRATION CONTRACT | MIXED | MIXED | Arm Sensor Hub / Raspberry-side calibration process | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Component interface/configuration and Arm implementation documentation |
| LentonNeale/Karetao | `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md` | CAN BIT TIMING EVIDENCE | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Karetao / Verification Evidence | HIGH | Records calculations, tests, observations, readiness, or validation status. | Documentation/05_VERIFICATION/ or component verification evidence |
| LentonNeale/Karetao | `docs/project/firmware/CAN_SERVICE_CONTRACT.md` | CAN SERVICE CONTRACT | MIXED | MIXED | Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm CAN interface/implementation and safety evidence |
| LentonNeale/Karetao | `docs/project/firmware/CONTRACT_STATUS.md` | CONTRACT STATUS | MIXED | MIXED | Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm contract governance and Verification |
| LentonNeale/Karetao | `docs/project/firmware/CONTRACT_V1_FREEZE.md` | CONTRACT V1 FREEZE | MIXED | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao decisions; Arm component contracts; Verification |
| LentonNeale/Karetao | `docs/project/firmware/ERROR_HANDLING_STRATEGY.md` | ERROR HANDLING STRATEGY | MIXED | MIXED | Karetao / Arm Sensor Hub / Safety authority | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao safety/requirements and Arm error-handling implementation |
| LentonNeale/Karetao | `docs/project/firmware/HEALTH_MONITOR_CONTRACT.md` | HEALTH MONITOR CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao component role and Arm implementation |
| LentonNeale/Karetao | `docs/project/firmware/I2C_MANAGER_CONTRACT.md` | I2C MANAGER CONTRACT | MIXED | MIXED | Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm I2C interface/implementation |
| LentonNeale/Karetao | `docs/project/firmware/JOINT_MAPPING_CONTRACT.md` | JOINT MAPPING CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao component/interface definition and Arm configuration |
| LentonNeale/Karetao | `docs/project/firmware/LIFECYCLE_CONTRACT.md` | LIFECYCLE CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub / Safety authority | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao lifecycle architecture and Arm implementation |
| LentonNeale/Karetao | `docs/project/firmware/MOTOR_SERVICE_CONTRACT.md` | MOTOR SERVICE CONTRACT | MIXED | MIXED | Arm Sensor Hub / Safety authority | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm MotorService documentation and safety evidence |
| LentonNeale/Karetao | `docs/project/firmware/MULTI_SENSOR_CONTRACT.md` | MULTI SENSOR CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao sensor interface; Arm implementation; Verification |
| LentonNeale/Karetao | `docs/project/firmware/SAFETY_RELEASE_CHECKLIST.md` | SAFETY RELEASE CHECKLIST | SAFETY | SAFETY | Karetao safety authority | HIGH | Defines safety release controls or safety evidence gates. | Documentation/04_SAFETY/ or component safety/release evidence |
| LentonNeale/Karetao | `docs/project/firmware/SNAPSHOT_COHERENCY_CONTRACT.md` | SNAPSHOT COHERENCY CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao SPI interface; Arm implementation; Verification |
| LentonNeale/Karetao | `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md` | TIMESTAMP SYNC CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao time interface; Arm time-service documentation/configuration |
| LentonNeale/Karetao | `docs/project/hardware/arm-sensor-hub-baseline.md` | Arm Sensor Hub Baseline | UNKNOWN | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao component definition; Arm baseline; Verification |
| LentonNeale/Karetao | `docs/project/interfaces/raspberry-pi-spi.md` | Raspberry Pi Spi | MIXED | MIXED | Karetao / Raspberry Sensor Hub / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao SPI interface; Raspberry component docs; configuration |
| LentonNeale/Karetao | `docs/project/interfaces/spi-service-contract.md` | Spi Service Contract | MIXED | MIXED | Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm SPI implementation; Verification |
| LentonNeale/Karetao | `docs/project/operations/RASPBERRY_PI_BRINGUP_V0.1.md` | RASPBERRY PI BRINGUP V0.1 | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Karetao | `docs/project/protocols/spi-contract.md` | Spi Contract | MIXED | MIXED | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao SPI interface plus component implementation references |
| LentonNeale/Karetao | `docs/project/protocols/spi-payload-schema.md` | Spi Payload Schema | MIXED | MIXED | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao interface/data model and component serializer/decoder docs |
| LentonNeale/Karetao | `docs/project/system/TODO_List.md` | TODO List | SYSTEM_ARCHITECTURE | MIXED | Karetao / Arm Sensor Hub / Raspberry Sensor Hub / Verification Evidence | HIGH | Contains technical implementation and integration status, hardware-validation gates, protocol/configuration follow-up, and explicit evidence/requirements-boundary notes. The TODO/process role does not make its technical statements governance-only. | Karetao architecture/integration tracking plus component implementation and verification records |
| LentonNeale/Karetao | `docs/project/system/architecture.md` | Architecture | SYSTEM_ARCHITECTURE | MIXED | Karetao / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao architecture and Arm implementation documentation |
| LentonNeale/Karetao | `docs/project/system/development.md` | Development | SYSTEM_ARCHITECTURE | MIXED | Arm Sensor Hub / Raspberry Sensor Hub | HIGH | Contains concrete STM32 and Raspberry Pi tooling, build presets, test commands, implementation-change guidance, and hardware/debug workflow. It is technical component-development material rather than pure documentation governance. | Component development/setup documentation for Arm Sensor Hub and Raspberry Sensor Hub |
| LentonNeale/Arm_Sensor_Hub | `Documentation/APP_OVERVIEW.md` | APP OVERVIEW | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/BUILD_CONTRACT.md` | BUILD CONTRACT | MIXED | MIXED | Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm build/configuration and Verification |
| LentonNeale/Arm_Sensor_Hub | `Documentation/CALIBRATION_CONTRACT.md` | CALIBRATION CONTRACT | MIXED | MIXED | Arm Sensor Hub / Raspberry-side calibration process | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm calibration implementation/configuration |
| LentonNeale/Arm_Sensor_Hub | `Documentation/CAN_BIT_TIMING_EVIDENCE.md` | CAN BIT TIMING EVIDENCE | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | HIGH | Records calculations, tests, observations, readiness, or validation status. | Documentation/05_VERIFICATION/ or component verification evidence |
| LentonNeale/Arm_Sensor_Hub | `Documentation/CAN_Module_Developer_Guide.md` | CAN Module Developer Guide | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/CAN_SERVICE_CONTRACT.md` | CAN SERVICE CONTRACT | MIXED | MIXED | Arm Sensor Hub / Safety authority | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm CAN interface/implementation and safety |
| LentonNeale/Arm_Sensor_Hub | `Documentation/CONTRACT_STATUS.md` | CONTRACT STATUS | MIXED | MIXED | Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm governance and Verification |
| LentonNeale/Arm_Sensor_Hub | `Documentation/CONTRACT_V1_FREEZE.md` | CONTRACT V1 FREEZE | MIXED | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao decisions; Arm contracts; Verification |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Conversations/CTO_DECISION_BRIEF.md` | CTO DECISION BRIEF | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Conversations/CTO_DECISION_FINAL.md` | CTO DECISION FINAL | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Conversations/DeepSeek.md` | DeepSeek | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Conversations/GPT.md` | GPT | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Conversations/InterAgent_Chat.md` | InterAgent Chat | HISTORICAL | HISTORICAL | Historical record | HIGH | Content is explicitly archived, superseded, or retained as historical context. | Documentation/99_ARCHIVE/ or existing historical archive |
| LentonNeale/Arm_Sensor_Hub | `Documentation/ERROR_HANDLING_STRATEGY.md` | ERROR HANDLING STRATEGY | MIXED | MIXED | Karetao / Arm Sensor Hub / Safety authority | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao safety/requirements and Arm implementation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/HEALTH_MONITOR_CONTRACT.md` | HEALTH MONITOR CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao component role and Arm implementation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/I2C_MANAGER_CONTRACT.md` | I2C MANAGER CONTRACT | MIXED | MIXED | Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm I2C documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/JOINT_MAPPING_CONTRACT.md` | JOINT MAPPING CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao component/interface and Arm configuration |
| LentonNeale/Arm_Sensor_Hub | `Documentation/LIFECYCLE_CONTRACT.md` | LIFECYCLE CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub / Safety authority | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao lifecycle architecture and Arm implementation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/MOTOR_SERVICE_CONTRACT.md` | MOTOR SERVICE CONTRACT | MIXED | MIXED | Arm Sensor Hub / Safety authority | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm MotorService documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/MULTI_SENSOR_CONTRACT.md` | MULTI SENSOR CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao sensor definition; Arm implementation; Verification |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Module_TODOs/CAN_Module_TODO.md` | CAN Module TODO | GOVERNANCE | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | HIGH | Contains concrete CAN implementation state, STM32 pin/configuration values, service behavior, hardware bring-up tasks, fault-recovery implementation work, diagnostics, and test procedures. | LentonNeale/Arm_Sensor_Hub CAN implementation documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Module_TODOs/CAN_Service_Copilot_Implementation_Recommendations.md` | CAN Service Copilot Implementation Recommendations | MIXED | MIXED | Arm Sensor Hub / Karetao decisions / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm implementation and Verification; Karetao decision references |
| LentonNeale/Arm_Sensor_Hub | `Documentation/OnboardingDocs/Architecture_and_Runtime_Flow.md` | Architecture And Runtime Flow | SYSTEM_ARCHITECTURE | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/OnboardingDocs/Development_Setup_and_Workflow.md` | Development Setup And Workflow | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | HIGH | Contains concrete STM32 toolchain, CMake presets, build/test commands, debugger configuration, implementation workflow, and code-boundary guidance. | LentonNeale/Arm_Sensor_Hub development documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/OnboardingDocs/First_Week_Guide.md` | First Week Guide | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | HIGH | Onboarding material includes concrete repository modules, build/test commands, runtime-flow inspection, service behavior, and safety-relevant implementation boundaries. | LentonNeale/Arm_Sensor_Hub onboarding/component documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/OnboardingDocs/Project_Orientation.md` | Project Orientation | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/OnboardingDocs/README.md` | README | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | HIGH | Organizes the Arm Sensor Hub onboarding path and directs readers to implementation, contract-status, testing, and architecture material. Its content is component-development onboarding, not Karetao documentation governance. | LentonNeale/Arm_Sensor_Hub onboarding documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/PHASE_1_FINAL_CLEARANCE_REPORT.md` | PHASE 1 FINAL CLEARANCE REPORT | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | HIGH | Records calculations, tests, observations, readiness, or validation status. | Documentation/05_VERIFICATION/ or component verification evidence |
| LentonNeale/Arm_Sensor_Hub | `Documentation/PROJECT_BASELINE.md` | PROJECT BASELINE | GOVERNANCE | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao component definition; Arm baseline; Verification |
| LentonNeale/Arm_Sensor_Hub | `Documentation/RASPBERRY_PI_BRINGUP.md` | RASPBERRY PI BRINGUP | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/README.md` | README | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | HIGH | Indexes concrete Arm Sensor Hub architecture, implementation status, runtime flow, interfaces, contracts, safety gates, verification reports, and onboarding material. The documentation rules describe the component documentation scope rather than serving as Karetao governance. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Arm_Sensor_Hub | `Documentation/ROS2_CALIBRATION_ARCHITECTURE_REPORT.md` | ROS2 CALIBRATION ARCHITECTURE REPORT | MIXED | MIXED | Karetao / Arm Sensor Hub / Raspberry-side application | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao architecture; component/application docs; configuration/safety |
| LentonNeale/Arm_Sensor_Hub | `Documentation/SAFETY_RELEASE_CHECKLIST.md` | SAFETY RELEASE CHECKLIST | SAFETY | SAFETY | Arm Sensor Hub safety/release authority | HIGH | Defines safety release controls or safety evidence gates. | Documentation/04_SAFETY/ or component safety/release evidence |
| LentonNeale/Arm_Sensor_Hub | `Documentation/SNAPSHOT_COHERENCY_CONTRACT.md` | SNAPSHOT COHERENCY CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao SPI interface; Arm implementation; Verification |
| LentonNeale/Arm_Sensor_Hub | `Documentation/SPI_CONTRACT.md` | SPI CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao interface and component implementation docs |
| LentonNeale/Arm_Sensor_Hub | `Documentation/SPI_PAYLOAD_SCHEMA.md` | SPI PAYLOAD SCHEMA | UNKNOWN | MIXED | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao data interface and component docs |
| LentonNeale/Arm_Sensor_Hub | `Documentation/SPI_SERVICE_CONTRACT.md` | SPI SERVICE CONTRACT | MIXED | MIXED | Arm Sensor Hub / Verification Evidence | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Arm SPI implementation; Verification |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Sprint Info/Sprint_2_Readiness_Report.md` | Sprint 2 Readiness Report | VERIFICATION_EVIDENCE | VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | HIGH | Records calculations, tests, observations, readiness, or validation status. | Documentation/05_VERIFICATION/ or component verification evidence |
| LentonNeale/Arm_Sensor_Hub | `Documentation/Sprint_1_List.md` | Sprint 1 List | GOVERNANCE | MIXED | Arm Sensor Hub / Karetao decisions / Verification Evidence | HIGH | Combines task/process rules with concrete STM32 implementation work, protocol and safety constraints, test commands/results, hardware-validation gates, and implementation handoff records. | Arm implementation/task records; Karetao decision references; component/integration verification evidence |
| LentonNeale/Arm_Sensor_Hub | `Documentation/TIMESTAMP_SYNC_CONTRACT.md` | TIMESTAMP SYNC CONTRACT | MIXED | MIXED | Karetao / Arm Sensor Hub | MEDIUM | Contains materially distinct authority domains; see Mixed-Authority Documents. | Karetao time interface; Arm implementation/configuration |
| LentonNeale/Arm_Sensor_Hub | `Middlewares/Third_Party/MksServo/README.md` | README | VENDOR_EXTERNAL_REFERENCE | VENDOR_EXTERNAL_REFERENCE | MKS/vendor | HIGH | Describes externally defined MKS protocol/equipment behavior. | External/vendor reference; not Karetao-owned |
| LentonNeale/Arm_Sensor_Hub | `README.md` | README | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/Arm_Sensor_Hub documentation |
| LentonNeale/Arm_Sensor_Hub | `docs/third party manuals/Mks protocol.md` | Mks Protocol | VENDOR_EXTERNAL_REFERENCE | VENDOR_EXTERNAL_REFERENCE | MKS/vendor | HIGH | Describes externally defined MKS protocol/equipment behavior. | External/vendor reference; not Karetao-owned |
| LentonNeale/RaspberryPi_Sensor_Hub | `README.md` | README | COMPONENT_IMPLEMENTATION | COMPONENT_IMPLEMENTATION | Raspberry Sensor Hub | MEDIUM | Describes how a component is built, configured, operated, or developed. | LentonNeale/RaspberryPi_Sensor_Hub documentation |

## Mixed-Authority Documents

The following 45 documents contain materially different authority domains. The content groups below are analytical groupings, not migration instructions.

| Source | Section/content group | Classification | Authority owner | Rationale | Potential future destination |
|---|---|---|---|---|---|
| `docs/project/firmware/BUILD_CONTRACT.md` | Build policy and reproducibility rules | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | Defines firmware build/toolchain implementation constraints and records CI/test status. | Arm Sensor Hub documentation; component configuration; component verification |
| `docs/project/firmware/CALIBRATION_CONTRACT.md` | Calibration data contract and STM32 validation/selection | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + CONFIGURATION | Arm Sensor Hub / Raspberry-side calibration process | Defines a cross-component calibration record while specifying STM32 validation and activation behavior. | Component interface/configuration and Arm implementation documentation |
| `docs/project/firmware/CAN_SERVICE_CONTRACT.md` | CAN service API, transport behavior, configuration and safety gating | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + SAFETY | Arm Sensor Hub | Separates MKS codec behavior from the Arm service and defines command gating and transport ownership. | Arm CAN interface/implementation and safety evidence |
| `docs/project/firmware/CONTRACT_STATUS.md` | Contract ownership, implementation status and freeze/validation gates | GOVERNANCE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | The matrix mixes process/status assertions with implementation state and test/validation evidence. | Arm contract governance and Verification |
| `docs/project/firmware/CONTRACT_V1_FREEZE.md` | Cross-contract decisions, interface rules, implementation constraints and release gates | DECISION + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | It freezes technical decisions while also defining component contracts and unresolved integration gates. | Karetao decisions; Arm component contracts; Verification |
| `docs/project/firmware/ERROR_HANDLING_STRATEGY.md` | System fault semantics, firmware escalation and safety response | SYSTEM_REQUIREMENT + COMPONENT_IMPLEMENTATION + SAFETY | Karetao / Arm Sensor Hub / Safety authority | Firmware response levels include system-level safety consequences while the document also specifies service-local recovery implementation. | Karetao safety/requirements and Arm error-handling implementation |
| `docs/project/firmware/HEALTH_MONITOR_CONTRACT.md` | Health semantics, service diagnostic interface and runtime implementation | SYSTEM_ARCHITECTURE + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub | Aggregate system health is described alongside the concrete HealthMonitor API and task behavior. | Karetao component role and Arm implementation |
| `docs/project/firmware/I2C_MANAGER_CONTRACT.md` | I2C service API, lifecycle and HAL/RTOS implementation behavior | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Arm Sensor Hub | The public service contract and concrete mutex, callback, timeout and HAL behavior are inseparable in this document. | Arm I2C interface/implementation |
| `docs/project/firmware/JOINT_MAPPING_CONTRACT.md` | System joint identity and Arm configuration/validation implementation | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + CONFIGURATION | Karetao / Arm Sensor Hub | Logical joint identity is system-facing, while record validation and activation are Arm implementation details. | Karetao component/interface definition and Arm configuration |
| `docs/project/firmware/LIFECYCLE_CONTRACT.md` | System lifecycle semantics, STM32 state implementation and safety behavior | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION + SAFETY | Karetao / Arm Sensor Hub / Safety authority | It defines system-facing lifecycle meaning while also specifying STM32 state transitions and safety-relevant recovery behavior. | Karetao lifecycle architecture and Arm implementation |
| `docs/project/firmware/MOTOR_SERVICE_CONTRACT.md` | Future logical motor interface, implementation target and safety constraints | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + SAFETY | Arm Sensor Hub / Safety authority | The proposed API is a component interface, but the same document specifies implementation dependencies and safety limits. | Arm MotorService documentation and safety evidence |
| `docs/project/firmware/MULTI_SENSOR_CONTRACT.md` | Sensor topology contract, acquisition implementation and commissioning evidence | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | Logical sensor identity and snapshot expectations cross the system boundary, while scan behavior and measured timing are component/evidence content. | Karetao sensor interface; Arm implementation; Verification |
| `docs/project/firmware/SNAPSHOT_COHERENCY_CONTRACT.md` | Snapshot interface semantics, buffer ownership implementation and transport evidence | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | The snapshot is a system-visible data contract, but buffer ownership and DMA behavior are implementation details and some sections record observed behavior. | Karetao SPI interface; Arm implementation; Verification |
| `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md` | Time authority/interface, STM32 time-service implementation and configuration limits | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + CONFIGURATION | Karetao / Arm Sensor Hub | The Pi time authority and synchronization semantics are system-facing; timer extension and API behavior are Arm implementation details. | Karetao time interface; Arm time-service documentation/configuration |
| `docs/project/hardware/arm-sensor-hub-baseline.md` | Component architecture, implementation snapshot and verification observations | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | It describes the Arm component's role and concrete architecture while also recording tested and unvalidated behavior. | Karetao component definition; Arm baseline; Verification |
| `docs/project/interfaces/raspberry-pi-spi.md` | Raspberry-side SPI interface, host implementation and deployment configuration | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + CONFIGURATION | Karetao / Raspberry Sensor Hub / Arm Sensor Hub | The document states cross-system SPI roles and pins, then describes Linux spidev implementation and host configuration. | Karetao SPI interface; Raspberry component docs; configuration |
| `docs/project/interfaces/spi-service-contract.md` | SPI service interface, STM32 implementation and target/hardware evidence | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | The service boundary and concrete DMA/buffer behavior coexist with a dated target-hardware observation. | Arm SPI implementation; Verification |
| `docs/project/protocols/spi-contract.md` | Cross-repository SPI wire contract, component transport behavior and protocol rules | SYSTEM_INTERFACE + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | The document defines the system-visible protocol while also tying rules to STM32 and Pi implementations. | Karetao SPI interface plus component implementation references |
| `docs/project/protocols/spi-payload-schema.md` | Cross-system payload schema and serializer/decoder constraints | SYSTEM_INTERFACE + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | Payload meaning is system-visible, while serialization and decoder constraints are component implementation details. | Karetao interface/data model and component serializer/decoder docs |
| `README.md` | Karetao monorepo overview, system/documentation organization, and repository governance | GOVERNANCE + SYSTEM_ARCHITECTURE | Karetao | The root README describes the Karetao platform and the organization/boundaries of its system and component repositories; it is not Raspberry Sensor Hub implementation documentation. | Retain as Karetao root README; canonical engineering detail remains under `docs/project/` |
| `docs/project/README.md` | Canonical project documentation structure plus substantive system-documentation domains | GOVERNANCE + SYSTEM_ARCHITECTURE | Karetao | The project README defines the documentation architecture while enumerating system architecture, decisions, interfaces, protocols, safety, operations, and authority areas. | `docs/project/README.md` as canonical project-documentation index |
| `docs/project/system/TODO_List.md` | Technical implementation/integration backlog, validation gates, and evidence-boundary notes | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Raspberry Sensor Hub / Verification Evidence | The TODO record contains concrete technical status and validation work across system and component boundaries. | Karetao integration tracking; component implementation; Verification Evidence |
| `docs/project/system/development.md` | Arm/Raspberry development tooling, build/test workflow, and implementation guidance | COMPONENT_IMPLEMENTATION | Arm Sensor Hub / Raspberry Sensor Hub | The workflow contains concrete toolchains, presets, commands, module boundaries, and hardware-debug guidance for both component implementations. | Component development/setup documentation |
| `Documentation/Sprint_1_List.md` | STM32 implementation tasks, protocol/safety constraints, test evidence, and task governance | COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE + GOVERNANCE | Arm Sensor Hub / Verification Evidence / Karetao decisions | The sprint record mixes project/task process with concrete implementation work, validation results, and hardware/release gates. | Arm implementation/task records; Verification Evidence; Karetao decision references |
| `docs/project/system/architecture.md` | Monorepo architecture and Arm runtime implementation | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub | The document describes repository-level layers but most concrete runtime flow is STM32/Arm implementation behavior. | Karetao architecture and Arm implementation documentation |
| `Documentation/BUILD_CONTRACT.md` | Arm build policy, configuration and verification status | COMPONENT_IMPLEMENTATION + CONFIGURATION + VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | Build rules are component implementation/configuration policy and the document also records CI results and release validation expectations. | Arm build/configuration and Verification |
| `Documentation/CALIBRATION_CONTRACT.md` | Calibration interface, STM32 validation implementation and configuration | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + CONFIGURATION | Arm Sensor Hub / Raspberry-side calibration process | The record is shared across Pi/workstation and STM32 but validation and activation are component behavior. | Arm calibration implementation/configuration |
| `Documentation/CAN_SERVICE_CONTRACT.md` | CAN service interface, transport implementation and safety gating | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + SAFETY | Arm Sensor Hub / Safety authority | Public service behavior, transport policy and safety gating are all present. | Arm CAN interface/implementation and safety |
| `Documentation/CONTRACT_STATUS.md` | Contract governance, implementation status and verification gates | GOVERNANCE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | It is a status matrix but contains concrete implementation state and evidence requirements. | Arm governance and Verification |
| `Documentation/CONTRACT_V1_FREEZE.md` | Decision freeze, component contracts and integration gates | DECISION + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | The freeze document records decisions and simultaneously defines component contract behavior and remaining evidence gates. | Karetao decisions; Arm contracts; Verification |
| `Documentation/ERROR_HANDLING_STRATEGY.md` | System fault policy, firmware recovery and safety response | SYSTEM_REQUIREMENT + COMPONENT_IMPLEMENTATION + SAFETY | Karetao / Arm Sensor Hub / Safety authority | System-facing fault response is mixed with service-local retry, lifecycle and diagnostic implementation. | Karetao safety/requirements and Arm implementation |
| `Documentation/HEALTH_MONITOR_CONTRACT.md` | Aggregate health interface and concrete HealthMonitor behavior | SYSTEM_ARCHITECTURE + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub | System health semantics are coupled to a specific STM32 task/API design. | Karetao component role and Arm implementation |
| `Documentation/I2C_MANAGER_CONTRACT.md` | Component I2C interface and HAL/RTOS implementation | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Arm Sensor Hub | The public API and implementation concurrency/error rules are both substantive. | Arm I2C documentation |
| `Documentation/JOINT_MAPPING_CONTRACT.md` | System joint identity and Arm mapping/configuration implementation | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + CONFIGURATION | Karetao / Arm Sensor Hub | System-facing identity is defined alongside Arm validation and configuration behavior. | Karetao component/interface and Arm configuration |
| `Documentation/LIFECYCLE_CONTRACT.md` | System lifecycle model, STM32 implementation and safety behavior | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION + SAFETY | Karetao / Arm Sensor Hub / Safety authority | The meaning of lifecycle states is system-facing while transitions and recovery are implemented in firmware. | Karetao lifecycle architecture and Arm implementation |
| `Documentation/MOTOR_SERVICE_CONTRACT.md` | Future motor interface, implementation target and safety constraints | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + SAFETY | Arm Sensor Hub / Safety authority | The proposed service API and its implementation/safety constraints share one document. | Arm MotorService documentation |
| `Documentation/MULTI_SENSOR_CONTRACT.md` | Sensor interface/topology, acquisition implementation and timing evidence | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | Logical sensor topology is system-facing; scan behavior and commissioned observations are component/evidence content. | Karetao sensor definition; Arm implementation; Verification |
| `Documentation/Module_TODOs/CAN_Service_Copilot_Implementation_Recommendations.md` | Implementation recommendations, decision carry-over and test requirements | DECISION + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Arm Sensor Hub / Karetao decisions / Verification Evidence | It contains adopted design decisions as well as concrete code changes and tests. | Arm implementation and Verification; Karetao decision references |
| `Documentation/PROJECT_BASELINE.md` | Component architecture, implementation status and evidence/readiness claims | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | It states the component's role and implementation while recording validation status and open integration work. | Karetao component definition; Arm baseline; Verification |
| `Documentation/ROS2_CALIBRATION_ARCHITECTURE_REPORT.md` | Proposed system/application architecture, component responsibilities, configuration and safety considerations | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION + CONFIGURATION + SAFETY | Karetao / Arm Sensor Hub / Raspberry-side application | The proposal spans ROS2 architecture, hardware-driver implementation boundaries, persistent configuration and safety/commissioning considerations. | Karetao architecture; component/application docs; configuration/safety |
| `Documentation/SNAPSHOT_COHERENCY_CONTRACT.md` | Snapshot system interface, Arm buffer/DMA implementation and evidence | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Karetao / Arm Sensor Hub / Verification Evidence | The snapshot semantics cross the system boundary while ownership and DMA rules are implementation details. | Karetao SPI interface; Arm implementation; Verification |
| `Documentation/SPI_CONTRACT.md` | System SPI interface plus STM32/Pi transport implementation constraints | SYSTEM_INTERFACE + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | The wire contract is system-facing but includes concrete DMA, pin and transport implementation facts. | Karetao interface and component implementation docs |
| `Documentation/SPI_PAYLOAD_SCHEMA.md` | System payload contract plus component serialization/decoder details | SYSTEM_INTERFACE + COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub / Raspberry Sensor Hub | Payload semantics are system-visible while serialization constraints are implementation-facing. | Karetao data interface and component docs |
| `Documentation/SPI_SERVICE_CONTRACT.md` | SPI service interface, STM32 implementation and target evidence | COMPONENT_INTERFACE + COMPONENT_IMPLEMENTATION + VERIFICATION_EVIDENCE | Arm Sensor Hub / Verification Evidence | The document combines service contract semantics with concrete ownership/DMA behavior and target observations. | Arm SPI implementation; Verification |
| `Documentation/TIMESTAMP_SYNC_CONTRACT.md` | System time interface, STM32 time-service implementation and configuration | SYSTEM_INTERFACE + COMPONENT_IMPLEMENTATION + CONFIGURATION | Karetao / Arm Sensor Hub | Time authority and validity are system-facing; timer extension and acceptance bounds are implementation/configuration details. | Karetao time interface; Arm implementation/configuration |

## System Requirements Identified

| Source | Statement group | Classification | Authority | Confidence |
|---|---|---|---|---|
| `docs/project/SD/SD-03.md` | Pi heartbeat timeout and motion-command rejection/stop behavior | SYSTEM_REQUIREMENT | Karetao | HIGH |
| `docs/project/SD/SD-04.md` | Feedback freshness timeout and escalation | SYSTEM_REQUIREMENT | Karetao | HIGH |
| `docs/project/SD/SD-05.md` | v1 CAN bitrate/ID/load targets subject to validation | SYSTEM_REQUIREMENT | Karetao | HIGH |
| `docs/project/SD/SD-15.md` | Fixed SPI frame, mode, endianness and CRC contract | SYSTEM_REQUIREMENT | Karetao | HIGH |
| `docs/project/SD/SD-18.md` | Timestamp accuracy target and synchronization validity | SYSTEM_REQUIREMENT | Karetao | HIGH |
| `docs/project/SD/SD-20.md` | Inhibit time-dependent motion while synchronization is invalid | SYSTEM_REQUIREMENT | Karetao | HIGH |
| `docs/project/SD/SD-24.md` | Recovery returns inactive and does not automatically resume motion | SYSTEM_REQUIREMENT | Karetao | HIGH |
| `docs/project/SD/SD-25.md` | Independent safety mechanisms are release gates | SYSTEM_REQUIREMENT + SAFETY | Karetao / Safety authority | HIGH |
| `docs/project/firmware/*_CONTRACT.md` | Normative contract clauses covering CAN, SPI, lifecycle, sensor, time and error behavior | SYSTEM_REQUIREMENT where system-facing; otherwise component contract | Karetao / Arm Sensor Hub | MEDIUM |
| `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md` | Framework placeholder only; no substantive safety requirement text at this baseline | GOVERNANCE | Karetao | HIGH |

These are statement-level findings. A statement appearing in a component contract or decision record is not automatically a final, uniquely identified Karetao requirement. In particular, implementation behavior and test expectations were not upgraded to requirements merely because they are normative in a component contract.

## System Architecture Identified

| Source | Statement group | Classification | Authority | Confidence |
|---|---|---|---|---|
| `docs/project/system/architecture.md` | Repository layers, startup flow, data flow and concrete service responsibilities | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub | HIGH |
| `Documentation/03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md` | System/component ownership boundary and interface/verification chain | GOVERNANCE + SYSTEM_ARCHITECTURE | Karetao | HIGH |
| `Documentation/01_SYSTEM/*` framework files | Placeholders naming intended architecture/timing/synchronization authorities | GOVERNANCE, not substantive architecture | Karetao | HIGH |
| `Documentation/PROJECT_BASELINE.md` | Arm component role, architecture and current runtime status | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub | MEDIUM |
| `Documentation/OnboardingDocs/Architecture_and_Runtime_Flow.md` | STM32 platform/application/protocol layers and runtime flow | COMPONENT_IMPLEMENTATION | Arm Sensor Hub | HIGH |
| `docs/project/firmware/LIFECYCLE_CONTRACT.md` | Lifecycle states and transitions used across the STM32/system boundary | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION | Karetao / Arm Sensor Hub | HIGH |
| `Documentation/ROS2_CALIBRATION_ARCHITECTURE_REPORT.md` | Proposed calibration package boundary and hardware-driver/application separation | SYSTEM_ARCHITECTURE + COMPONENT_IMPLEMENTATION | Arm Sensor Hub / Karetao integration | MEDIUM |

## System Interfaces Identified

| Source | Interface content | Authority | Classification |
|---|---|---|---|
| `Documentation/02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md` | Framework placeholder for Karetao CAN system interface; no substantive contract text | Karetao | GOVERNANCE at baseline |
| `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | Framework placeholder for Karetao SPI system interface | Karetao | GOVERNANCE at baseline |
| `docs/project/protocols/spi-contract.md` | SPI master/slave roles, framing, CRC, sequence and timing contract | Karetao system + components | MIXED |
| `docs/project/protocols/spi-payload-schema.md` | Cross-system snapshot/event/diagnostic payload semantics | Karetao system + components | MIXED |
| `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md` | Pi time authority, sync validity and STM32 implementation | Karetao + Arm | MIXED |
| `docs/project/interfaces/raspberry-pi-spi.md` | Pi-side pins, spidev behavior and transaction acceptance conditions | Karetao + Raspberry/Arm | MIXED |

## Component Implementation Identified

| Source/family | Component content identified |
|---|---|
| Arm `Documentation/CAN_Module_Developer_Guide.md` | Concrete CanService API, scheduler, queue and state behavior |
| Arm `Documentation/OnboardingDocs/*` | STM32 architecture, runtime flow, development and onboarding material |
| Arm `Documentation/RASPBERRY_PI_BRINGUP.md` | Host provisioning and deployment procedure |
| Karetao `docs/project/firmware/*` | STM32 service, sensor, CAN, SPI, lifecycle and calibration implementation details where present |
| Karetao `docs/project/hardware/arm-sensor-hub-baseline.md` | Arm hardware/firmware architecture and current implementation |
| Raspberry `README.md` | Raspberry-side implementation/integration scaffold description |

## Component Interfaces Identified

| Source | Component interface group | Authority | Future destination |
|---|---|---|---|
| `docs/project/firmware/CAN_SERVICE_CONTRACT.md` | CanService public API and transport boundary | Arm Sensor Hub | Arm Sensor Hub CAN documentation |
| `docs/project/firmware/I2C_MANAGER_CONTRACT.md` | I2C manager API and ownership rules | Arm Sensor Hub | Arm Sensor Hub I2C documentation |
| `docs/project/firmware/MOTOR_SERVICE_CONTRACT.md` | Future logical motor API | Arm Sensor Hub | Arm Sensor Hub MotorService documentation |
| `Documentation/SPI_SERVICE_CONTRACT.md` | SPI service boundary and ownership semantics | Arm Sensor Hub | Arm Sensor Hub SPI documentation |
| `Documentation/SPI_PAYLOAD_SCHEMA.md` | Serializer/decoder-facing schema | Arm + Raspberry Sensor Hub | Component protocol/interface docs |
| `docs/project/firmware/CALIBRATION_CONTRACT.md` | Calibration record passed between Pi/workstation and STM32 | Arm + Raspberry-side calibration process | Component configuration/interface docs |

## Vendor / External References Identified

| Source | External content | Authority |
|---|---|---|
| `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/README.md` | MKS Servo codec protocol encoding/decoding behavior and library constraints | MKS/vendor-derived protocol reference |
| `Arm_Sensor_Hub/docs/third party manuals/Mks protocol.md` | MKS Servo42/57D CAN manual and controller-defined behavior | MKS/vendor |
| `Karetao/docs/third party manuals/Mks protocol.md` | Same MKS manual retained in Karetao | MKS/vendor |

The MKS manual is external authority for MKS controller/protocol behavior. The MksServo README describes a project-integrated codec, so it is classified as vendor/external reference at document level only because its substantive protocol definitions are explicitly tied to the external MKS protocol; its library integration statements are implementation context.

## Verification Evidence Identified

| Source | Evidence content | Authority | Classification |
|---|---|---|---|
| `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md` | CAN timing calculation and explicit statement that hardware validation is not established | Evidence | VERIFICATION_EVIDENCE |
| `Documentation/PHASE_1_FINAL_CLEARANCE_REPORT.md` | Build/test audit and architecture-integrity findings | Evidence | VERIFICATION_EVIDENCE |
| `Documentation/Sprint Info/Sprint_2_Readiness_Report.md` | Readiness and remaining integration gates | Evidence | VERIFICATION_EVIDENCE |
| `docs/project/firmware/*` mixed contracts | Embedded test results, commissioning observations and explicit validation gaps | Evidence | VERIFICATION_EVIDENCE within MIXED documents |
| `Documentation/05_VERIFICATION/*` | Framework placeholders only at this baseline; they define intended verification destinations rather than recording evidence | Karetao | GOVERNANCE |

Component verification evidence is not treated as Karetao system verification. The authoritative Karetao system verification status location remains `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`; at the indexed baseline that file is only a framework placeholder.

## Configuration Identified

| Source | Configuration content | Authority | Classification |
|---|---|---|---|
| `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` | Framework placeholder only | Karetao | GOVERNANCE at baseline |
| `docs/project/firmware/BUILD_CONTRACT.md` | STM32 build/toolchain/preset configuration | Arm Sensor Hub | MIXED |
| `docs/project/firmware/CALIBRATION_CONTRACT.md` | Calibration record schema and activation constraints | Arm Sensor Hub | MIXED |
| `docs/project/interfaces/raspberry-pi-spi.md` | Pi SPI pins, spidev device and 5 MHz configuration ceiling | Raspberry/Arm | MIXED |
| `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md` | Time-sync bounds and state configuration | Arm/Karetao | MIXED |

No pure document-level `CONFIGURATION` authority was identified from actual content at this baseline. Configuration is embedded in mixed implementation/interface documents and must remain distinct from system requirements.

## Safety Content Identified

| Source | Safety content | Authority | Classification |
|---|---|---|---|
| `Documentation/SAFETY_RELEASE_CHECKLIST.md` | Release blockers, independent E-stop, motor disable, stopping time and external safety evidence | Arm Sensor Hub / Safety authority | SAFETY |
| `docs/project/firmware/SAFETY_RELEASE_CHECKLIST.md` | Same release-gate model in Karetao legacy firmware documentation | Karetao / Safety authority | SAFETY |
| `docs/project/SD/SD-25.md` | Independent safety mechanisms as a release gate | Karetao / Safety authority | DECISION with SAFETY statement |
| Mixed lifecycle/error/CAN/motor documents | Fail-closed behavior, motion inhibition, recovery and safety gating | Karetao + Arm + Safety authority | MIXED |

## Decisions Identified

The 27 document-level DECISION entries are `docs/project/SD/SD-01.md` through `SD-26.md` plus `docs/project/SYSTEM_DECISIONS.md`. Their substantive content records system decisions and unresolved issues; decision status does not by itself convert every summary into a requirement or verification result. Additional decision content appears inside `CONTRACT_V1_FREEZE.md`, the CAN implementation recommendations, and historical CTO/conversation records.

Decision records were not reclassified as system requirements merely because their summaries contain normative values. The decision role and the requirement-bearing statements are kept distinct.

## Historical Content Identified

30 documents are classified HISTORICAL at document level: the 25 Karetao archive entries (indices 62-86) and the five Arm conversation records at indices 121-125. Their content can contain technical facts, proposals, decisions or evidence, but the documents are retained as historical/superseded records and are not treated as current normative authority. Archived stubs that merely point to canonical documents were classified HISTORICAL because their substantive role is preservation/compatibility history.

## Governance Content Identified

29 documents are classified GOVERNANCE at document level. This includes the Karetao documentation framework, authority/process rules, project questions, and archive placeholders. The governance recheck moved documents containing substantive implementation, configuration, or verification material out of pure GOVERNANCE classification. Content-level review deliberately prevents a filename such as `SYSTEM_REQUIREMENTS.md` or `SYSTEM_VERIFICATION_MATRIX.md` from being treated as technical authority when the file contains only a framework placeholder.

## Unknown / Unresolved Content

No document-level `UNKNOWN` classification remains after review.

Unresolved analytical questions remain at statement level:
- whether some contract clauses are intended as Karetao system requirements or only Arm implementation constraints;
- which exact system requirement identifiers should eventually be assigned;
- which measured observations constitute integration evidence versus component evidence;
- which vendor claims have been independently verified on the target hardware.

These are unresolved authority/traceability questions, not reasons to classify the source documents as `UNKNOWN`.

## Potential Future Destinations

| Content group | Potential destination |
|---|---|
| Karetao system requirements extracted from decisions/contracts | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` |
| Karetao system architecture and component roles | `Documentation/01_SYSTEM/` and `Documentation/03_COMPONENTS/` |
| Karetao system interfaces | `Documentation/02_INTERFACES/` |
| Karetao safety requirements/architecture | `Documentation/04_SAFETY/` |
| Karetao system verification status/evidence | `Documentation/05_VERIFICATION/` |
| Karetao controlled system configuration | `Documentation/06_CONFIGURATION/` |
| Karetao decisions | `Documentation/07_DECISIONS/` |
| Historical material | `Documentation/99_ARCHIVE/` |
| Arm Sensor Hub implementation/interface/configuration/verification | `LentonNeale/Arm_Sensor_Hub` documentation |
| Raspberry Sensor Hub implementation/interface/configuration/verification | `LentonNeale/RaspberryPi_Sensor_Hub` documentation |
| MKS protocol/equipment behavior | External/vendor reference material |

Potential destinations are recorded only where the authority domain is reasonably identifiable. They do not authorize migration or imply that the source should be moved, split, deleted, or rewritten.

## Classification Limitations

1. The index itself records an indexed-tree baseline rather than a continuously current repository state.
2. The index was created at commit `3fa986e5f0edb98b6be879dafa7bb9777eb516d9`; the branch subsequently received commit `71f851e1db02ae7f73da5102fc034826784b3e30`, which clarified the index's persistent location and embedded baseline metadata. The classification uses the indexed tree commit specified by the index for source-document content.
3. Some documents explicitly describe proposed, target, or future behavior. Such text was classified according to its actual role and confidence, not treated as implemented fact.
4. Archived documents may contain technically correct statements, but their document-level role is historical unless current authority is explicitly re-established elsewhere.
5. Component verification and system verification are intentionally kept separate.
6. Vendor behavior is treated as external authority and not promoted to Karetao requirement authority.
7. The classification does not resolve conflicting technical statements; it identifies the authority domain that owns each statement group.
8. No per-file last-modified history was inferred from the index because the index explicitly left those fields unresolved.

## Baseline

| Item | Baseline |
|---|---|
| Classification file | `Documentation/DOCUMENTATION_CONTENT_CLASSIFICATION.md` |
| Index file | `Documentation/DOCUMENTATION_INDEX.md` |
| Index creation commit | `3fa986e5f0edb98b6be879dafa7bb9777eb516d9` |
| Current branch commit containing the index-location/baseline clarification | `71f851e1db02ae7f73da5102fc034826784b3e30` |
| Indexed Karetao tree commit | `bb473df6cf8df8f997181f3d02beeb143298d17a` |
| Arm Sensor Hub baseline inspected | `a86f83036a3fb97450e661bf5b09557af4064274` |
| RaspberryPi Sensor Hub baseline inspected | `087e6c3e0b102c8e32dbf0dace30376e38b26123` |
| Karetao branch | `doc/reconcile-karetao-mks` |
| Arm branch | `main` |
| Raspberry branch | `main` |

## Validation

- [x] All 156 indexed documentation-like entries have a content-level classification.
- [x] All 45 `MIXED` documents have distinct content groups, authority owners, rationale, and potential destinations.
- [x] Pure framework placeholders were not promoted to technical authority.
- [x] Governance entries were rechecked for substantive system, component, configuration, safety, or verification content; affected documents were reclassified as MIXED or COMPONENT_IMPLEMENTATION.
- [x] System requirement statements were separated from implementation details, design preferences, observations, and historical statements.
- [x] Component verification was not treated as system verification.
- [x] Vendor/MKS behavior was kept separate from Karetao system authority.
- [x] Repository paths and baseline commits were checked against the index and inspected repositories.
- [x] Source documentation, source code, tests, generated files, submodules, and component repositories were not modified during analysis.
- [x] This task writes only the new classification artifact.

## Completion

Classification complete for the indexed baseline. This file is evidence for the documentation reconciliation process and is not permission to begin migration.
