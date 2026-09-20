# System Configuration

## Authority

This document is the authoritative Karetao destination for system-level controlled configuration. Component-specific build/toolchain, driver and implementation configuration remains component authority.

## Current system configuration constraints

- CAN nominal rate: **1 Mbps** for v1, standard 11-bit IDs (SD-05).
- SPI initial maximum: **5 MHz**, pending target-system validation (SD-01, SD-15).
- SPI framing: 512-byte frame, maximum 490-byte payload, Mode 0, little-endian, CRC-32/ISO-HDLC (SD-15).
- TIME_SYNC: 1 Hz nominal, configurable to 10 Hz; invalid after 5 s without accepted update (SD-19).
- Host/API authoritative joint representation: calibrated radians (SD-12).
- Calibration data is versioned and integrity-protected, with redundant STM32 storage and a host-side source copy (SD-11).

## Configuration authority boundary

Concrete STM32 build/toolchain settings, driver settings, Raspberry provisioning and component-specific configuration are not system configuration authority and remain in the component repositories.

Values marked provisional or validation-dependent must not be represented as final release configuration until the corresponding evidence is accepted.
