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
- Participate in fault detection, bounded recovery, and explicit reactivation; provide implementation evidence required for Karetao integration verification.

## Hardware Baseline (System-Visible)

**MCU:** STM32F405RGT6 (LQFP64 package). **Clock tree** (PRM-MCU-01): HSE 8 MHz external oscillator; SYSCLK 168 MHz; APB1 42 MHz (constrains CAN and SPI timing); APB2 84 MHz. **Timing and link parameters:** see [`PARAMETER_REGISTER.md`](../06_CONFIGURATION/PARAMETER_REGISTER.md) (PRM-CAN-01/02, PRM-SPI-01, PRM-ACQ-02/03).

## System Interface Implementation

### I2C1 (Sensor Acquisition)

| Signal | Pin | Direction | Standard |
|---|---|---|---|
| SCL | PB6 | bidirectional | Fast mode (400 kHz) |
| SDA | PB7 | bidirectional | Fast mode (400 kHz) |

The I2C1 interface connects to a TCA9548A I2C multiplexer for routing to six AS5600 encoders. The channel map is in [`SYSTEM_CONFIGURATION.md`](../06_CONFIGURATION/SYSTEM_CONFIGURATION.md) §2.1. Mux channel selection and AS5600 transaction form one atomic I2C operation.

### CAN1 (Motor Control)

| Signal | Pin | Direction | Standard |
|---|---|---|---|
| RX | PB8 | input | ISO 11898-1 (500 kHz–1 Mbps) |
| TX | PB9 | output | ISO 11898-1 (500 kHz–1 Mbps) |

CAN1 implements the MKS motor controller protocol. For the bitrate target and the generated value, see PRM-CAN-02.

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

## Authority Boundary

**Karetao-owned (system-level):** system role, responsibilities, and interface contracts; CAN, SPI, TIME, and lifecycle integration requirements; timing and link parameters (PARAMETER_REGISTER.md).

**Arm Sensor Hub-owned (implementation):** service architecture (I2CManager, CAN Service, SPI Slave Service, Sensor Task, Health Monitor); STM32 firmware APIs and internal state machines; DMA configuration and ISR handling; FreeRTOS task structure and scheduling; build configuration and toolchain settings; full peripheral pinout and register configuration; component-only diagnostics and testing.

**External authority:** MKS motor controller protocol and firmware behavior; AS5600 sensor register map and operation; TCA9548A I2C multiplexer behavior; STM32F405 HAL and peripherals.

## AS5600 Precision and Accuracy

Resolution, accuracy, installation constraints, and the rationale for the four-decimal-radian representation are in `Arm_Sensor_Hub/Documentation/AS5600_PRECISION_AND_ACCURACY.md` (supporting note). The AS5600 datasheet is the device authority; [`SYSTEM_CONFIGURATION.md`](../06_CONFIGURATION/SYSTEM_CONFIGURATION.md) is authoritative for the Karetao-level angle representation.

## Timing improvement note (2026-09-20)

The full six-axis sweep measured about 46 ms on target hardware (PRM-ACQ-02). The theoretical I2C protocol floor (PRM-ACQ-03, `Arm_Sensor_Hub/Documentation/I2C_SCAN_TIMING_ANALYSIS.md`) is a floor, not a measurement. The gap is firmware overhead, and reducing it is an open improvement, not scheduled.

*Provenance:* reconciled from `docs/project/hardware/arm-sensor-hub-baseline.md`. Component-internal details (full pinout, peripheral configuration, DMA specifics, build system, service APIs) remain Arm Sensor Hub implementation authority.
