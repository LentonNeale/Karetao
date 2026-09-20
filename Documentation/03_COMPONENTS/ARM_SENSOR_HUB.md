# Arm Sensor Hub

## System role

The Arm Sensor Hub is the STM32-based hardware-facing Karetao component. Karetao defines its system role, requirements, external interfaces and integration obligations; the Arm Sensor Hub repository remains authoritative for implementation details.

## System responsibilities

- Acquire and expose sensor/state information through the Karetao system interfaces.
- Implement the assigned CAN, SPI, time, lifecycle and actuator-facing interfaces.
- Apply system-defined freshness, lifecycle, calibration and motion-gating requirements.
- Participate in fault detection, bounded recovery and explicit reactivation.
- Provide the implementation evidence required for Karetao integration verification.

## Authority boundary

This document does not define STM32 service APIs, scheduler/DMA design, concrete driver architecture, codec implementation or component-only configuration. Those remain Arm Sensor Hub implementation authority.

System requirements are owned by Karetao and are defined in `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`.
