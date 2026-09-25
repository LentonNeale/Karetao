# System Verification Matrix

## Authority

This document is the authoritative Karetao system-level verification status record. Component verification remains component evidence and is not, by itself, system verification.

## Verification status

| Requirement group | System status | Required evidence |
|---|---|---|
| Timing / synchronization | OPEN | Target hardware timing, timestamp error, sync drift and EKF adequacy |
| Pi link liveness (`link_stale`) / loss response | OPEN | Count-based detection within interim 500 ms (SYS-FAIL-001), end-to-end timeout, controlled-stop/motor-disable timing, no last-command hold |
| Motor feedback timeout | OPEN | Integrated freshness and escalation behaviour |
| CAN interface | OPEN | Live CAN configuration, load, bus-off recovery and motion-inhibit evidence |
| Joint/state mapping | OPEN | Versioned mapping and differential end-effector verification |
| SPI interface | OPEN | Pi/STM32 live framing, CRC, ownership, timing and physical-layer evidence |
| Host command/state interface | OPEN | End-to-end acknowledgement, freshness, lifecycle and gating evidence |
| Calibration/configuration | OPEN | Versioning, integrity, controlled transfer and recovery evidence |
| System motion permission | OPEN / PROPOSED | Verify aggregate prerequisite logic, fail-closed behaviour, freshness/synchronization inputs, global inhibit handling, recovery, and explicit reactivation; normative verification awaits decision approval |
| Fault/recovery | OPEN | System-level motion gating and dependency-ordered reactivation tests |
| Independent safety mechanisms | OPEN | Risk assessment, safety architecture and independent-path fault evidence |

## Status rule

`SYSTEM_VERIFIED` may be assigned only by Karetao system verification after integrated evidence is accepted. Component `VERIFIED` or `HARDWARE_VERIFIED` status does not automatically establish `SYSTEM_VERIFIED`.

## Traceability

Primary requirement source is `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`; source decision IDs are retained there. Component test results are evidence inputs and must be linked when accepted.
