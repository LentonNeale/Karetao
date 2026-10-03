# Safety requirements (attended operation)

Status: Rewritten 2026-10-03 to the charter scope. Owner: Lenton Neale.

## Scope

No PL or SIL rating is claimed. Operation is attended, by the maintainer only. Safety behaviours are designed and tested; they are not an independent safety function and are not represented as one. (Source: `01_SYSTEM/PROJECT_CHARTER.md`.)

## Behaviours

| ID | Behaviour | Relies on | Evidence required | Matrix row |
|---|---|---|---|---|
| SAFE-01 | An operator-reachable hardware power cut or E-stop removes motor power without software. It is hardware, and is tested by hand before each session with motion. | — | Evidence record: power cut stops and de-energises every motor. | SAFE-01 |
| SAFE-02 | On Pi link loss, new commands are rejected, a controlled stop follows, then motors are disabled. The last command is never held. | SYS-FAIL-001, SYS-FAIL-002, SYS-GATE-001 | Evidence record: link removed during motion, stop and disable observed, timing noted against PRM-LINK-01. | SAFE-02 |
| SAFE-03 | On CAN bus-off, transmission is inhibited, recovery is bounded, and reactivation is explicit. | SYS-CAN-003 | Evidence record per `05_VERIFICATION/CAN_INTEGRATION_EVIDENCE.md`. | SAFE-03 |
| SAFE-04 | Reset or recovery never resumes motion by itself. Explicit reactivation is required. | SYS-REC-001, SYS-REC-002 | Evidence record: reset during motion, no motion after reset until reactivated. | SAFE-04 |
| SAFE-05 | Faults are visible to the operator: the DIAGNOSTIC message once implemented; until then the health monitor state read over SWD or the bench tool. | health_monitor.c, DIAGNOSTIC (not implemented) | Evidence record: an injected fault is visible. | SAFE-05 |

## Application controls

The application controls are lifecycle state, link liveness monitoring, CAN command gating, bounded recovery and controlled-stop behaviour. They contribute to safe behaviour but establish no rating.

## Withdrawn by the charter (2026-10-03)

- SAFE-001: machine risk assessment and PL/SIL target.
- SAFE-008: stopping time under hazardous conditions.
- SAFE-009: safety-rated relay/controller architecture.
- The former "release gate" framing.

Mapping of the other former IDs: SAFE-002 -> SAFE-01; SAFE-003 -> SAFE-01; SAFE-004 (watchdog) -> open item below; SAFE-005 -> SAFE-02 and SAFE-04; SAFE-006 -> SAFE-05; SAFE-007 -> SAFE-04; SAFE-010 -> SYS-GATE-001.

## Open items

- Watchdog behaviour: whether a hardware watchdog is enabled and what it does on expiry is unknown. Lenton to confirm.
- Whether a CAN failure inhibits one joint or the whole arm (SD-06 scope). Lenton decides.
- The actual E-stop hardware fitted is unknown.

## Provenance

Former SAFETY_REQUIREMENTS, SAFETY_ARCHITECTURE and SAFETY_INTEGRATION (see git history); SD-25 kept with no rating claimed.
