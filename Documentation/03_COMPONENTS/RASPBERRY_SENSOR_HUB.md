# Raspberry Sensor Hub

## System role

The Raspberry Sensor Hub is the host-side Karetao component. Karetao defines its system role, requirements, external interfaces and integration obligations; the Raspberry Sensor Hub repository remains authoritative for implementation details.

## System responsibilities

- SPI master and system time authority.
- Owner of the ClockSync model and timestamp conversion (Issue #12 target; not yet implemented).
- Snapshot decoding and validation (`spi_protocol.py`).
- Sender of single gated commands (SET_MOTOR_COMMAND, frozen in Sprint 4).
- Host-side source copy of calibration records (SYS-CAL).
- Evidence tools (`spi_timing_harness.py`, `spi_link_probe.py`, `measurement_report.py`) producing records per [EVIDENCE_RECORD_FORMAT.md](../05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md).

Future, not now: ROS 2 integration and any estimator ([PROJECT_CHARTER.md](../01_SYSTEM/PROJECT_CHARTER.md) non-goals).

## Authority boundary

This document does not define Raspberry provisioning, host software internals, driver implementation or component-only configuration. Those remain Raspberry Sensor Hub implementation authority.

System requirements are owned by Karetao and are defined in `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`.
