# Contract v1.0 Freeze Specification

**⚠ ARCHIVED — Non-normative historical document**

- **Archived:** 2026-09-20
- **Status:** Superseded by Karetao Documentation framework
- **Superseding documents:** 
  - Lifecycle: `01_SYSTEM/SYSTEM_LIFECYCLE.md`
  - SPI contract: `02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`, `02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md`
  - Time contract: `02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`
  - CAN contract: `02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md`
  - Configuration: `06_CONFIGURATION/SYSTEM_CONFIGURATION.md`
  - Architecture: `01_SYSTEM/SYSTEM_ARCHITECTURE.md`

This document's v1.0 decisions have been reconciled and distributed into Karetao's normative framework. The contract hierarchy diagram is superseded by the authority model. The DATA_READY semantics (conflict C-1) are resolved in favor of the armed-then-assert model (SPI_SYSTEM_INTERFACE.md §7).

---

# Contract v1.0 Freeze Specification [ARCHIVED]

**Status:** Pre-freeze/approval baseline; approved v1.0 decisions are propagated, with only explicit integration gates remaining
**Scope:** STM32F405 sensor hub and Raspberry Pi SPI integration  
**Exclusions:** ROS runtime integration, MotorService implementation, and generated-code restructuring

## Purpose and Authority

This document reconciles the project contracts before SPI DMA, snapshot publication, and time synchronization runtime code are implemented. A lower-level contract must not redefine a rule owned here.

The STM32 remains an independent embedded system using a C11 application layer. The MKS Servo codec remains a separate C++17 library behind `mks_api.h`.

## Contract Hierarchy

```text
LIFECYCLE_CONTRACT
├── ERROR_HANDLING_STRATEGY
├── I2C_MANAGER_CONTRACT
├── CAN_SERVICE_CONTRACT
└── SPI_SERVICE_CONTRACT
    ├── SPI_CONTRACT
    ├── SPI_PAYLOAD_SCHEMA
    ├── SNAPSHOT_COHERENCY_CONTRACT
    └── TIMESTAMP_SYNC_CONTRACT
```

- `LIFECYCLE_CONTRACT.md`: canonical states, transitions, dependencies, and safety gating.
- `ERROR_HANDLING_STRATEGY.md`: fault classes, escalation, and recovery authority.
- `SPI_CONTRACT.md`: SPI framing, transaction model, CRC, sequence, DATA_READY, and transport errors.
- `SPI_PAYLOAD_SCHEMA.md`: serialized payload layouts and payload schema versions.
- `SNAPSHOT_COHERENCY_CONTRACT.md`: producer caches, snapshot assembly, and frame-buffer ownership.
- `TIMESTAMP_SYNC_CONTRACT.md`: monotonic time, Pi offset, validity, and measurement timestamp quality.
- Service contracts: interface-specific timing, ownership, and recovery rules.

## Decisions to Freeze

### SPI Transaction Model

Use a pipelined request/response model:

```text
Transaction N:
    Pi clocks request N
    STM32 clocks response staged before transaction N

Between transactions:
    STM32 processes request N and stages response N+1

Transaction N+1:
    Pi clocks response N+1 while sending request N+1
```

The first response after boot is a defined `ACK`, `NACK`, or status frame. The response sequence identifies the request it answers. The STM32 never initiates clocking.

### DATA_READY

`DATA_READY = HIGH` means a complete response frame is staged and ready for the Raspberry Pi to clock. It does not merely mean that new sensor data exists.

The SPI service owns DATA_READY in production. SensorTask bring-up GPIO toggling is temporary and must be removed when SPI publication is implemented.

### SPI Physical Baseline

- SPI mode: mode 0, CPOL=0 and CPHA=0, matching current CubeMX configuration.
- Byte order: little-endian for multi-byte protocol fields.
- Maximum SPI clock: unresolved integration gate; it must be approved with the Raspberry Pi driver before DMA implementation.

### CRC

Approved v1.0 definition: CRC-32/ISO-HDLC.

| Parameter | Value |
| --- | --- |
| Width | 32 |
| Polynomial | `0x04C11DB7` |
| Initial value | `0xFFFFFFFF` |
| Input reflection | true |
| Output reflection | true |
| Final XOR | `0xFFFFFFFF` |
| Wire byte order | little-endian |
| Coverage | Fixed frame header plus payload, excluding CRC field |

Both STM32 and Raspberry Pi implementations must use this definition.

### Frame Size

Approved v1.0 target:

```text
MAX_FRAME_BYTES = 512
MAX_PAYLOAD_BYTES = 512 - 18-byte header - 4-byte CRC = 490
```

The current proposed six-sensor/eight-motor snapshot is approximately 370 bytes including header and CRC, so a 256-byte limit is insufficient without reducing the schema.

### Snapshot Ownership

Do not allow SensorTask and CAN service to write one shared snapshot build buffer.

```text
SensorTask -> sensor latest-value cache ----┐
                                            ├-> Snapshot Builder -> free SPI frame buffer -> DMA
CAN service -> motor latest-value cache ----┘
```

- SensorTask owns sensor records.
- CAN service owns motor records.
- Snapshot Builder owns serialization.
- SPI service owns the two serialized frame buffers and DMA transfer.
- DMA owns the active buffer until transaction completion.
- Use replace-if-new for an unread staged response and count replacements/dropped snapshots.
- Never block sensor acquisition waiting for Raspberry Pi consumption.

### Fixed Snapshot Records

The target six-axis topology always serializes six sensor records. `sensor_count` means serialized record count, not valid-record count. A normal six-axis snapshot therefore has `sensor_count = 6`; invalid channels remain present with validity flags.

Sensor IDs `0..5` identify logical axes. Physical TCA9548A channel mapping remains an internal/configuration concern.

Motor record count remains topology-dependent until motor commissioning is finalized.

### Time Model

- Raspberry Pi is the system time authority.
- STM32 local time is monotonic and is never reset.
- `hub_time_us = local_time_us + signed_offset_us`.
- `frame_time_us` identifies frame assembly time.
- `measurement_timestamp_us` identifies measurement acquisition time.
- Version 1 permits direct offset steps and therefore permits synchronized system-time discontinuities.
- Two-way RTT estimation and slew correction are future versioned enhancements.

AS5600 measurement timestamps are captured immediately after successful measurement bytes are received and decoded.

### Extended Time

TIM2 is a 32-bit, 1 MHz counter and wraps after approximately 4,295 seconds. A shared time service must extend it to a 64-bit monotonic timestamp before long-lived synchronization and freshness logic are implemented.

All I2C/AS5600, CAN, SPI, and diagnostic timestamps must use the shared time service rather than independently selecting HAL tick or raw TIM2 values.

### TIME_SYNC Validity

Approved v1.0 synchronization validity timeout: 5 seconds. The STM32 exposes:

- `time_sync_valid`;
- signed `time_offset_us`;
- last synchronization sequence;
- last synchronization local timestamp;
- synchronization age/quality.

After expiry, the STM32 continues local acquisition and diagnostics, marks new records unsynchronized, and rejects or inhibits time-dependent motion commands until a new accepted update restores validity. Explicitly defined non-motion service operations may continue.

Version 1 uses a one-way transaction-point estimate. Two-way synchronization is a later protocol version.

### CAN Ownership and Timing

Before production CAN implementation:

- derive and approve bitrate/sample point/SJW from the actual APB1 CAN clock;
- define one logical TX owner/queue for polling, motion, and safety commands;
- choose hardware retransmission or bounded software retry;
- define command priority and ordering;
- define bus-off detection and recovery.

Current normal TX lifecycle gating is already centralized in `CanService_TransmitFrame()`.

### I2C Ownership

Mux channel selection plus the AS5600 transaction is one atomic logical operation. Application code must not independently schedule a mux selection and sensor read under separate ownership windows.

### Lifecycle and RTOS Startup

The system must distinguish:

1. CubeMX/HAL hardware initialization.
2. RTOS static-object creation.
3. Service lifecycle configuration to `INACTIVE`.
4. Task creation.
5. Service activation from system/task context.

The lifecycle startup order is fixed: CubeMX hardware initialization, `osKernelInitialize`, static RTOS object creation and service configuration to `INACTIVE`, task creation, then dependency-ordered activation from system/task context before normal processing. Lifecycle recovery is owned by the System Manager; services own local recovery; HealthMonitor observes and recommends only. Current source ordering must be aligned with this fixed contract.

After reset, configuration, or recovery, services return to `INACTIVE`. Motion remains inhibited until an explicit, dependency-ordered activation confirms configuration, calibration, time, and safety prerequisites. Firmware response levels (`INFORMATIONAL`, `DEGRADED`, `FAULT`, and `SAFETY_CRITICAL`) define application behavior only and do not imply a formal PL or SIL rating.

## Remaining Integration Gates

The following decisions remain intentionally unresolved and must be approved before the affected implementation is frozen:

- CAN bitrate/retry/TX ownership;
- MotorService-specific command/state decisions;
- maximum SPI clock and associated DMA timing;
- independent safety validation and machine risk assessment, including the required PL/SIL target.

All other v1.0 decisions in this document are approved architectural baselines for implementation. CRC reference vectors remain a validation task, not an open architectural decision.

## Required Validation Before Code

- Cross-language/document link audit.
- CRC reference vectors and little-endian field offsets.
- Snapshot serialized-size calculation.
- TIM2 wrap-extension and offset-step tests.
- Raspberry Pi transaction timing review.
- CAN bitrate calculation against hardware clock and bus requirements.
- Raspberry Pi approval of the maximum SPI clock.

## Status Vocabulary

- **Document exists:** the contract file is present.
- **Implementation target:** intended behavior is documented but not fully implemented.
- **Pre-freeze/approval baseline:** approved v1.0 decisions are propagated, but remaining integration gates must be approved before implementation freeze.
- **Implemented:** code and contract exist; production verification may still be pending.
