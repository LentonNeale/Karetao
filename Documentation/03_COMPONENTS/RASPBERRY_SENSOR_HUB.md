# Raspberry Sensor Hub

## System role

The Raspberry Sensor Hub is the host-side Karetao integration component. Karetao defines its system role, requirements, external interfaces and integration obligations; the Raspberry Sensor Hub repository remains authoritative for implementation details.

## System responsibilities

- Maintain the host-side integration boundary to the Arm Sensor Hub.
- Own measurement/estimator history as specified by the system model.
- Provide heartbeat and command/state integration.
- Manage the controlled calibration/configuration path.
- Participate in lifecycle, synchronization, fault and recovery handling.
- Provide component evidence required for Karetao system integration verification.

## Authority boundary

This document does not define Raspberry provisioning, host software internals, driver implementation or component-only configuration. Those remain Raspberry Sensor Hub implementation authority.

System requirements are owned by Karetao and are defined in `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`.
