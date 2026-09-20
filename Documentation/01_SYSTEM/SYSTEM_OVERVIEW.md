# System Overview

Karetao is a six-axis robotic arm control system integrating hardware-facing sensor acquisition (STM32 Arm Sensor Hub) with host-side estimation, control, and planning (Raspberry Pi Sensor Hub) via deterministic synchronization and bounded real-time interfaces.

## Purpose

The system collects synchronized sensor measurements from six joint encoders and motor feedback through a CAN interface, timestamps them in a shared time domain with the host, and exposes coherent snapshots over an SPI interface to support real-time estimation and control loops on a Raspberry Pi host.

## Core Responsibilities

- **Arm Sensor Hub (STM32):**
  - Collect encoder values from six AS5600 encoders (I2C via TCA9548A multiplexer).
  - Integrate motor feedback from MKS CAN controller.
  - Timestamp measurements in a monotonic local time domain and synchronize to Pi time authority.
  - Serialize coherent snapshots and send over SPI with integrity protection.
  - Gate motion commands based on lifecycle state, synchronization validity, and CAN health.

- **Raspberry Sensor Hub (Pi):**
  - Serve as system time authority.
  - Manage system startup, lifecycle, and recovery.
  - Maintain host estimation, EKF loop, and control algorithms.
  - Command motors through the STM32/CAN interface.
  - Collect and process sensor history.

- **ROS 2 / Control Layer:**
  - Motion planning, trajectory execution, and higher-level control.
  - Integration with host operating system.

## Key Interfaces

- **SPI:** 512-byte fixed frames at 5 MHz max (integration ceiling, pending validation), carrying snapshots, diagnostics, and responses.
- **CAN:** 1 Mbps nominal (integration ceiling pending physical validation), MKS motor controller protocol, polling and commanded feedback.
- **TIME_SYNC:** 1 Hz nominal (configurable to 10 Hz) synchronization of STM32 local time to Pi authority.
- **Lifecycle:** Four-state machine (UNCONFIGURED, INACTIVE, ACTIVE, ERROR) controlling readiness and motion safety.

## Current Status

**What is established and working:**
- Contract structure and authority model.
- Snapshot payload constants and field definitions.
- Host-side SPI protocol validation and decoding.
- Lifecycle vocabulary and state machine.
- Time synchronization model (one-way transaction-point estimate).
- STM32 SPI3 DMA arm/complete/error/stall/re-arm software path.
- Raspberry Pi Linux `spidev` backend and fixed-frame decoder.
- Build and CI coverage (Debug/Release).

**What remains under integration and validation:**
- Live Raspberry Pi ↔ STM32 SPI transaction acceptance.
- Physical SPI acceptance: 5 MHz clock, DMA timing, NSS, DATA_READY electrical, signal integrity.
- Sustained SPI transaction validation and error recovery.
- CAN physical layer validation: bitrate acceptance, bus-off recovery, error handling under load.
- Complete TIME_SYNC end-to-end validation.
- Calibration persistence and integrity validation.
- Motor controller model/firmware and command semantics.
- Independent safety validation and machine risk assessment for energized-motion release.
