# Arm Sensor Hub

**Status:** STM32F405RGT6 firmware project, generated with STM32CubeMX, built with CMake.

## System Role

The Arm Sensor Hub is the STM32-based hardware-facing Karetao component. Karetao defines its system role, requirements, external interfaces, and integration obligations; the Arm Sensor Hub repository remains authoritative for implementation details.

## System Responsibilities

- Acquire six-axis encoder measurements via I2C (AS5600 through TCA9548A multiplexer).
- Exchange motor command and feedback over CAN to external MKS controller.
- Maintain a monotonic local clock and report request-receipt times (`request_received_local_us`) as clock-sync observations; perform no clock math (Issue #12).
- Run the count-based Pi link-liveness check (`link_stale`) that gates motion permission (SYS-FAIL-001).
- Serialize coherent sensor/motor snapshots and publish over SPI with `DATA_READY` signaling.
- Apply lifecycle state gating (UNCONFIGURED / INACTIVE / ACTIVE / ERROR) to motion commands and publication.
- Apply system-defined freshness, synchronization validity, and motion safety requirements.
- Participate in fault detection, bounded recovery, and explicit reactivation.
- Provide implementation evidence required for Karetao integration verification.

---

## Hardware Baseline (System-Visible)

**MCU:** STM32F405RGT6 (LQFP64 package)

**Clock tree:**
- HSE: 8 MHz external oscillator
- SYSCLK: 168 MHz
- APB1: 42 MHz (constrains CAN and SPI timing)
- APB2: 84 MHz

**Timing constraints:**
- CAN bitrate nominally 1 Mbps derived from APB1 42 MHz clock (see CAN_INTEGRATION_EVIDENCE.md for candidate configuration).
- SPI3 clock nominally 5 MHz maximum (integration ceiling pending target-system validation).
- Sensor acquisition sweep (six AS5600 encoders): approximately 46 ms full-axis scan time, measured on target hardware 2026-09-17. **Improvement target:** a theoretical protocol floor of ~690 µs has been established (see provenance note below); reducing measured sweep time toward that floor is desired but not yet scheduled or achieved.

---

## System Interface Implementation

### I2C1 (Sensor Acquisition)

| Signal | Pin | Direction | Standard |
|---|---|---|---|
| SCL | PB6 | bidirectional | Fast mode (400 kHz) |
| SDA | PB7 | bidirectional | Fast mode (400 kHz) |

The I2C1 interface connects to a TCA9548A I2C multiplexer for routing to six AS5600 encoders. Mux channel selection and AS5600 transaction form one atomic I2C operation.

### CAN1 (Motor Control)

| Signal | Pin | Direction | Standard |
|---|---|---|---|
| RX | PB8 | input | ISO 11898-1 (500 kHz–1 Mbps) |
| TX | PB9 | output | ISO 11898-1 (500 kHz–1 Mbps) |

CAN1 implements the MKS motor controller protocol. The nominal bitrate target is 1 Mbps; current generated configuration produces 875 kbps (implementation gap, see CAN_INTEGRATION_EVIDENCE.md).

### SPI3 (Host Publication)

| Signal | Pin | Direction | Standard |
|---|---|---|---|
| NSS | PA15 | input | Hardware NSS (SPI master controlled) |
| SCK | PC10 | input | SPI clock (SPI master controlled) |
| MISO | PC11 | output | SPI data to master (serialized frames) |
| MOSI | PC12 | input | SPI data from master (requests) |

SPI3 operates as a slave in mode 0 (CPOL=0, CPHA=0) with hardware NSS. The fixed transaction size is 512 bytes. The interface uses full-duplex DMA with pipelined request/response semantics.

### DATA_READY GPIO

| Signal | Pin | Direction | Behavior |
|---|---|---|---|
| DATA_READY | PA8 | output | Push-pull, active high |

Asserted HIGH only when a complete frame is staged and DMA transfer is armed (armed-then-assert model). Used as optional interrupt signal on the Raspberry Pi; polling fallback (1 ms default) is retained.

---

## Authority Boundary

**Karetao-owned (system-level):**
- System role, responsibilities, and interface contracts
- CAN, SPI, TIME, and lifecycle integration requirements
- Timing constraints (5 MHz SPI, 1 Mbps CAN, 46 ms sensor sweep — measured; see improvement note below for the theoretical floor)

**Arm Sensor Hub-owned (implementation):**
- Service architecture (I2CManager, CAN Service, SPI Slave Service, Sensor Task, Health Monitor)
- STM32 firmware APIs and internal state machines
- DMA configuration and ISR handling
- FreeRTOS task structure and scheduling
- Build configuration and toolchain settings
- Full peripheral pinout and register configuration
- Component-only diagnostics and testing

**External authority:**
- MKS motor controller protocol and firmware behavior
- AS5600 sensor register map and operation
- TCA9548A I2C multiplexer behavior
- STM32F405 HAL and peripherals

---

## AS5600 Precision and Accuracy

AS5600-specific resolution, physical accuracy considerations, magnetic/mechanical installation constraints, and the rationale for the system's four-decimal-radian representation are documented in:

`Arm_Sensor_Hub/Documentation/AS5600_PRECISION_AND_ACCURACY.md`

This component note is supporting engineering documentation. The AS5600 datasheet remains the authority for device specifications, while `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` remains authoritative for the Karetao-level angle representation.

## Provenance

Reconciled from `docs/project/hardware/arm-sensor-hub-baseline.md`. System-visible hardware baseline (MCU family, clock tree constraints, interface pin assignments that other components depend on) is included. Component-internal details (full pinout, peripheral configuration, DMA specifics, build system, service APIs) remain Arm Sensor Hub implementation authority.

## Timing improvement note (2026-09-20)

The ~46 ms full six-axis sweep figure was measured on target hardware on 2026-09-17 (`tools/check-sensors.sh`, recorded in the archived `CONTRACT_STATUS.md`) and remains the current verification evidence feeding SD-01's EKF-timing discussion and `SYSTEM_ARCHITECTURE.md`. A datasheet-derived I2C protocol-timing analysis (`Arm_Sensor_Hub/Documentation/I2C_SCAN_TIMING_ANALYSIS.md`) separately establishes that the I2C bus itself requires only ~690 µs for a six-sensor scan under theoretical, zero-overhead conditions. That figure is a **theoretical floor, not a measurement**, and does not replace or discredit the 46 ms measured value.

The gap between the two (roughly 45.3 ms) indicates firmware and scheduling overhead, not I2C protocol timing, dominates the measured sweep. This is recorded as an improvement target: reducing the measured sweep time toward the theoretical floor is desirable where practical, but requires instrumenting real per-axis latency on target hardware to identify the actual overhead sources (candidate causes include RTOS tick granularity, mux settle time, HAL polling timeouts, per-channel timeout budget, and task/mutex serialization — see the analysis document). No such instrumentation has been performed yet; this remains open (decisions register, SD-01, "instrument real per-axis update latency on target hardware").
