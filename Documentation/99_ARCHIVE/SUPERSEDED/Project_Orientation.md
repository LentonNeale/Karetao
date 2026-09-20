⚠ **ARCHIVED — Non-normative historical document**

- **Archived:** 2026-09-20
- **Historical status:** Superseded proposal or earlier version
- **Superseded by:** Current system documentation in `Documentation/` framework

---

# Project Orientation

## What This Project Is

Arm Sensor Hub is STM32F405 firmware that gathers sensor data, exchanges motor telemetry over CAN, and sends structured data to a Raspberry Pi over SPI. The current repository baseline describes the hub as:

- collecting encoder values from AS5600 sensors over I2C through a TCA9548A multiplexer,
- exchanging motor/control telemetry over CAN, and
- publishing data to the Raspberry Pi over SPI using a `DATA_READY` signal.

See [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/README.md`](../../README.md) and [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/PROJECT_BASELINE.md`](../PROJECT_BASELINE.md).

## Why The Repository Looks Document-Heavy

This project is being built contract-first. That means many interface and behavior decisions are written down before the full runtime integration is finished. Interns should expect to see:

- implementation code in `App/`, `Core/`, `Drivers/`, and `Middlewares/`,
- technical contracts in `Documentation/`, and
- tests that validate pieces of the design before full hardware integration.

Do not assume every documented behavior is already fully wired into the STM32 runtime. Check [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md`](../CONTRACT_STATUS.md) for the current implementation state.

## Repository Map

### `App/`

Application-owned firmware logic.

- `App/Src/app_init.c`: startup orchestration and service registration
- `App/Src/sensor_task.c`: sensor bring-up and periodic sampling
- `App/Src/can_service.c`: CAN/MKS message transport logic
- `App/Src/spi_slave_service.c`: SPI-side snapshot staging and `DATA_READY`
- `App/Src/time_service.c`: monotonic time and host-sync support

### `Core/`

STM32CubeMX-generated platform entry points, especially `Core/Src/main.c`, where hardware init, RTOS startup, and the default task loop live.

### `Drivers/`

STM32 HAL and CMSIS support code. Interns usually read this less often, but it matters when debugging hardware-facing behavior.

### `Middlewares/Third_Party/MksServo/`

Third-party C++17 protocol library for MKS servo CAN frames. Application C code talks to it through `mks_api.h`.

### `tests/host/`

Native host tests for protocol and data-plane logic. This is the fastest feedback loop for many safe changes.

### `Documentation/`

Architecture, contract, safety, and planning references. Treat this as part of the product, not side notes.

## Current State In Plain Language

The project has a solid architectural baseline, but it is not yet a fully hardware-validated end-to-end system.

What is already strong:

- service boundaries are defined,
- host-side protocol tests exist,
- lifecycle, snapshot, timestamp, and payload contracts are documented,
- single-channel sensor bring-up and core CAN/SPI scaffolding exist.

What is still incomplete or gated:

- full six-sensor scheduling,
- complete SPI runtime integration on hardware,
- complete CAN hardware validation and recovery evidence,
- fuller health-monitor aggregation,
- some persistence and startup robustness work.

This matters because interns should make changes with current limits in mind instead of assuming the system is already feature-complete.

## Vocabulary You Will See Often

- **Lifecycle**: shared service state model for configure, activate, fault, and recovery behavior.
- **Snapshot**: a coherent package of sensor and motor data prepared for SPI transfer.
- **TIME_SYNC**: mechanism for aligning STM32 time with Raspberry Pi time.
- **Host tests**: native tests built on the development machine instead of on STM32 hardware.
- **Contract**: authoritative definition of interface behavior, constraints, and invariants.

## Best First Mental Model

Think of the firmware as a pipeline:

1. initialize services,
2. acquire sensor and motor data,
3. attach timing and validity metadata,
4. build a coherent snapshot,
5. expose that snapshot to the Raspberry Pi over SPI.

If you keep that model in mind, the file structure becomes much easier to follow.
