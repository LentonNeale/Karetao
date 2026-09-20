# Integration Gates

## Authority

These gates define the evidence expected before Karetao system verification can be accepted. They are not a substitute for detailed verification records.

| Gate | Required evidence | Current status |
|---|---|---|
| Timing / synchronization | Target-hardware timing, timestamp error, sync drift, EKF adequacy | OPEN |
| Host communication loss | End-to-end timeout, controlled stop/motor disable timing, no last-command hold | OPEN |
| Motor feedback | Integrated freshness and escalation behaviour | OPEN |
| CAN | Live configuration, load, bus-off recovery and motion inhibit | OPEN |
| State/mapping | Versioned mapping and differential end-effector verification | OPEN |
| SPI | Live Pi/STM32 framing, CRC, ownership, timing and physical-layer evidence | OPEN |
| Host command/state | End-to-end acknowledgement, freshness, lifecycle and gating | OPEN |
| Calibration/configuration | Versioning, integrity, controlled transfer and recovery | OPEN |
| Fault/recovery | System-level motion gating and dependency-ordered reactivation | OPEN |
| Independent safety | Risk assessment, safety architecture and independent-path evidence | OPEN |

A gate remains open when evidence is absent, incomplete, not accepted, or outside the stated scope.

## Relationship to system verification

Passing a component test does not close an integration gate. A gate can only support SYSTEM_VERIFIED when evidence demonstrates the applicable system requirement at the required integration scope and has been accepted by the Karetao verification process.

## Provenance

Reconciled from the existing SYSTEM_VERIFICATION_MATRIX.md, the audited safety release checklist, and the Phase 2 content classification.
