# Safety Requirements

## Authority

This document defines Karetao system-level safety requirements and release-gate expectations. It does not establish a safety certification, PL/SIL rating, or independent safety function.

The boundary between application controls and independent safety functions shall be determined by the machine risk assessment and safety architecture.

## Release-gate requirements

| ID | Requirement / gate | Status |
|---|---|---|
| SAFE-001 | An applicable machine risk assessment and required PL/SIL target shall be established by the responsible safety process. | OPEN / BLOCKED pending evidence |
| SAFE-002 | An independent E-stop path shall be provided and independently evidenced. | OPEN / BLOCKED |
| SAFE-003 | A motor-disable or power-removal path shall be provided and evidenced. | OPEN / BLOCKED |
| SAFE-004 | Watchdog behaviour and fault recovery shall be evidenced on relevant hardware. | OPEN / BLOCKED |
| SAFE-005 | Actuator stop, brake, and power behaviour shall be evidenced under relevant conditions. | OPEN / BLOCKED |
| SAFE-006 | Fault indication and operator-visible reporting shall be evidenced. | OPEN / BLOCKED |
| SAFE-007 | Reset shall not automatically reactivate energized motion; reset/recovery behaviour shall be evidenced. | OPEN / BLOCKED |
| SAFE-008 | Stopping time shall be measured under hazardous operating conditions where required by the safety assessment. | OPEN / BLOCKED |
| SAFE-009 | Applicable safety-rated relay/controller and safety architecture shall be established and assessed. | OPEN / BLOCKED |
| SAFE-010 | The proposed normal-motion permission policy shall fail closed when any required system prerequisite is invalid, unavailable, stale, unsynchronized, or explicitly inhibited, once the proposed motion-permission decision is approved. | PROPOSED / NOT YET NORMATIVE |

These statuses preserve the audited release checklist state: no supporting artifact had been recorded at the stated evidence locations.

## Application-control boundary

Karetao application controls include lifecycle state, heartbeat/freshness monitoring, CAN command gating, synchronization gating, bounded recovery, and controlled-stop behaviour.

These controls may contribute to system behaviour and risk reduction, but they do not by themselves establish an independent safety function or a PL/SIL rating.

## Provenance

Reconciled from the audited docs/project/firmware/SAFETY_RELEASE_CHECKLIST.md and SD-25.

SD-25 states that independent E-stop, motor-disable/power-removal, watchdog, stop/brake behaviour, fault indication, reset behaviour, and applicable safety-rated architecture are release gates. It leaves the application-control/independent-safety boundary to the machine risk assessment and safety architecture.

## Open safety decisions

- Complete the machine risk assessment and establish applicable safety targets.
- Define the interface between application controlled-stop and independent safety functions.
- Identify the responsible evidence artifacts and acceptance authority for each release gate.
- Do not mark a gate complete until the corresponding evidence is independently reviewed and accepted.
