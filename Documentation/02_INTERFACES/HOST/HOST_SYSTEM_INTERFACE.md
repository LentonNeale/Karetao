# Host System Interface

## Authority

This document defines the Karetao system-level host interface between the Raspberry-side integration and the rest of the system. Host implementation details remain Raspberry Sensor Hub authority.

Tunable and physical values are referenced by PRM ID; their working values and bases are in [`PARAMETER_REGISTER.md`](../../06_CONFIGURATION/PARAMETER_REGISTER.md).

## Contract

- Healthy Pi communication is required for motion permission. Any accepted, valid SPI message counts as liveness, so there is no separate heartbeat message. The STM32 count-based liveness check sets `link_stale`, which rejects motion. The trip thresholds `N_moving`/`N_idle` (PRM-LINK-02) are open, and until they are set detection shall occur within **PRM-LINK-01** (SD-03, Issue #12 item 11).
- The host/API authoritative joint representation is calibrated **radians**; changes to wire representation require explicit schema versioning (SD-12).
- Joint state exposes stable identity, position, available velocity, validity/status, acquisition timestamp, synchronization quality and calibration version (SD-13, SYS-ENC-001, SYS-MOT-001).
- Single gated commands (SD-14): ENABLE, DISABLE, STOP (controlled stop), MOVE_TO_POSITION and MOVE_AT_VELOCITY, all sent as `SET_MOTOR_COMMAND` (wire layout in [`SPI_PAYLOAD_SCHEMA.md`](../SPI/SPI_PAYLOAD_SCHEMA.md)).
  - The reply is ACK (the motion gate, SYS-GATE-001, accepted the command and it is queued to CAN) or NACK with the gate reason. ACK means accepted, not executed; completion is observed in the snapshot motor record.
  - There is at most one outstanding command per motor. A new command supersedes an unexecuted one.
  - Trajectories are not queued (charter non-goal).
- Calibration is computed on the Pi and transferred through a controlled validated configuration path (SD-10).
- Measurement history is owned on the Pi (SD-09); the STM32 provides bounded latest-value/coherent records.

## Motion gate

Pi link liveness is one prerequisite of the normal-motion gate (SYS-GATE-001), and a live link does not by itself grant motion permission. When `link_stale` trips, the STM32 motion gate fails closed. New motion commands are rejected, and the approved SD-03 controlled stop, then motor disable, starts where the transport remains usable. The last motion command is never held.

## Acknowledgement and freshness (resolved 2026-10-03)

- ACK/NACK are the acknowledgement. There is no separate command-freshness window, because a command is either accepted at the gate or not.
- The host must not retry a NACKed command until the NACK reason clears.
- The host's wait for an ACK times out per PRM-LINK-01.
