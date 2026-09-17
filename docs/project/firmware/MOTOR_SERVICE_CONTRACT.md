# Motor Service Contract

**Status:** Future design contract  
**Owner:** Future `MotorService`  
**Boundary:** Logical joint commands/feedback -> `CanService`

## Scope

MotorService will provide a logical joint/axis API above physical MKS CAN devices. It is not currently implemented; current application code registers motors and calls `CanService` directly.

## Target Model

- Six logical axes, provisionally indexed 0-5.
- Each axis maps to one commissioned CAN ID and MKS model.
- Mapping is configuration, not hard-coded protocol behavior.
- CAN transport and MKS command encoding remain owned by existing modules.

## Target States

Motor-specific operational states may include `DISABLED`, `READY`, `HOMING`, `MOVING`, `HOLDING`, and `ERROR`, but these are subordinate to the system lifecycle. A motor cannot be operational unless MotorService and CAN are `ACTIVE`.

## Command Contract

Define validation and allowed states for enable, disable, emergency stop, absolute move, relative move, speed, zeroing, and configuration commands. Commands must have explicit timeout, completion, cancellation, and failure results.

Emergency stop must be safety-reviewed separately. It may be permitted as a transport-level action during selected failure states only if the CAN hardware path is verified operational.

## Feedback and Faults

CanService owns the bounded generic decoded-feedback cache used for snapshot publication. Future MotorService consumes that cache and may derive commissioned encoder, speed, current, and logical state fields without taking ownership of CAN records. Exact decoded field semantics remain unavailable until controller commissioning.

Define stale-data limits, stall detection, current limits, homing timeout, communication timeout, and escalation to HealthMonitor before implementation.

## Dependencies

- CAN Service `ACTIVE` for normal commands;
- MKS codec for frame semantics;
- lifecycle core for service state;
- HealthMonitor for aggregate reporting;
- SPI payload schema for host publication.

## Open Decisions

- exact axis/CAN-ID mapping;
- homing sequence;
- state machine and command arbitration;
- feedback filtering;
- safety authority and emergency-stop path;
- persistence of calibration/zero points.
