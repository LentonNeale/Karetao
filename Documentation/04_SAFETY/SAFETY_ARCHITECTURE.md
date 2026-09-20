# Safety Architecture

## Authority

This document defines the Karetao system-level safety architecture boundary. It does not replace the machine risk assessment or external safety assessment.

## Architectural boundary

The system safety boundary is divided between Karetao application controls and independent safety functions.

Application controls include lifecycle/readiness gating, heartbeat/freshness monitoring, CAN command gating, synchronization gating, bounded recovery, and controlled-stop behaviour.

Independent safety functions include the E-stop path, motor-disable or power-removal path, applicable safety-rated controller/relay, and other functions established by the machine risk assessment.

The independent safety path is authoritative for the safety function it implements. Karetao application behaviour must not be documented as a substitute for that independent function.
\n## Motion-permission boundary (proposed)\n\nThe proposed system-level normal-motion permission gate is an application control above individual service readiness. It is supplementary to the independent E-stop, motor-disable/power-removal, watchdog, and other safety-rated functions established by the machine risk assessment. The proposal must not be represented as the independent safety function or as a PL/SIL claim.\n
## Required architecture evidence

The safety architecture must establish hazards and risk-reduction measures from the machine risk assessment, applicable safety targets, independence and interfaces of the E-stop path, motor-disable/power-removal behaviour, actuator stop/brake behaviour, watchdog and reset interactions, fault indication, and boundaries between application and independent safety controls.

The audited baseline does not contain sufficient evidence to declare this architecture complete.

## Release status

Safety architecture remains OPEN / BLOCKED pending the required risk assessment and hardware/external safety evidence.

## Provenance

Reconciled from the audited docs/project/firmware/SAFETY_RELEASE_CHECKLIST.md and docs/project/SD/SD-25.md.
