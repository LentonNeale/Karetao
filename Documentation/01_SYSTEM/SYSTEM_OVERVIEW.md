# System Overview

Scope authority is the [project charter](PROJECT_CHARTER.md).

## Purpose

Karetao is a hobby-level robotic arm platform, built and maintained by one person. It aims for good engineering practice (traceability, recorded decisions, evidence before done) at a size one person can keep up.

## The three parts

- **STM32F405 Arm Sensor Hub:** reads AS5600 encoders through a TCA9548A I2C mux, polls the MKS servos over CAN, and serves snapshots to the Pi over SPI as slave.
- **MKS SERVO42D/57D motors:** closed-loop steppers on the CAN bus.
- **Raspberry Pi host:** SPI master and system time authority. It owns the Pi-side ClockSync model, sends single gated commands, and runs the evidence tools.

## Interfaces

- **SPI:** fixed frames, CRC-32, and a DATA_READY line. See [SPI](../02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md) and [payload schema](../02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md).
- **CAN:** the MKS protocol. See [CAN](../02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md).
- **Clock sync:** every SPI exchange is an observation, and the Pi does the conversion. The target design is Issue #12. See [TIME](../02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md).
- **Lifecycle:** UNCONFIGURED, INACTIVE, ACTIVE, ERROR.
- **Host:** see [HOST](../02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md). All interface documents are listed in [00_INDEX.md](../00_INDEX.md).

## Current status (as built, 2026-10-03)

Exists in code:
- SPI framing on both sides, with tests.
- STM32 SPI3 DMA path with DATA_READY.
- Six-axis encoder sweep (measured about 46 ms on 2026-09-17).
- CAN service polling scaffold, with one motor registered.
- Calibration record and joint-mapping models.
- Lifecycle and health monitor.
- A motion-permission module.

Not yet:
- The Issue #12 clock-sync redesign (the code still runs the older one-way TIME_SYNC).
- The DIAGNOSTIC message.
- The SET_MOTOR_COMMAND path.
- Six motors registered.
- A "not fitted" sensor state.

## Future, not now

These are charter non-goals for now and are named only here: ROS 2 integration, a state estimator, the differential end effector, trajectory or motion planning, and the gripper (jaw servo, and an Arduino Nano with an MCP2515 that turns CAN commands into jaw movements, likely on a separate CAN bus from the STM32), and a custom carrier PCB for the STM32F405 and a Raspberry Pi Compute Module 5, developed after the prototype hardware is signed off.
