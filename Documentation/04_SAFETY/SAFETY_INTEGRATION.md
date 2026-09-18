# Safety Integration

## Authority

This document defines system-level integration obligations for safety-related behaviour. It does not define the detailed implementation of firmware, hardware safety circuits, or external safety equipment.

## Integration requirements

- Application controls shall fail toward a defined non-motion state when applicable gating conditions are not satisfied.
- Loss of required heartbeat/freshness, invalid synchronization where motion depends on time, CAN failure, lifecycle failure, and persistent service faults shall not silently preserve an active motor command.
- System restart and recovery shall require explicit dependency-ordered reactivation and shall not automatically resume motor motion.
- Independent E-stop and motor-disable/power-removal paths shall remain distinct from application controlled-stop behaviour.
- Safety evidence shall identify the hardware, operating conditions, test method, acceptance authority, and resulting status.
- Component verification does not establish system safety acceptance.

## Evidence boundary

Firmware tests and builds are implementation evidence. Hardware stopping-time, E-stop, motor-disable, watchdog, brake, and signal-integrity results require the relevant hardware evidence and review. External safety assessment remains an independent authority where applicable.

## Current status

The audited safety release checklist records the required safety evidence as blocked because artifacts had not been recorded at the specified evidence locations.

## Provenance

Reconciled from docs/project/firmware/SAFETY_RELEASE_CHECKLIST.md, with system recovery and gating semantics cross-referenced to SD-03, SD-06, SD-20, SD-23, SD-24, and SD-25.
