# System Architecture

## Authority

This document is the Karetao system-level architecture authority. It describes the integrated system structure and responsibilities, not component implementation details.

## System structure

Karetao integrates:

1. **Arm Sensor Hub** — STM32-based hardware-facing control and sensor component.
2. **Raspberry Sensor Hub** — Raspberry Pi host-side integration component.
3. **ROS 2 / estimation / control / planning** — host-side system functions.
4. **External motor/controller equipment** — externally defined equipment and protocol behaviour.
5. **Independent safety functions** — safety mechanisms whose independence and boundary are determined by the machine risk assessment and safety architecture.

The architectural boundary is:

```
Karetao system
├── Raspberry Sensor Hub / host integration
│   ├── measurement history / estimator integration
│   ├── system command and state interfaces
│   └── ROS 2 integration
├── Arm Sensor Hub
│   ├── sensor acquisition
│   ├── actuator-facing services
│   └── system interface implementation
├── External MKS/controller equipment
└── Independent safety path
```

## Responsibility model

Karetao owns the system requirements, system interfaces, timing/synchronization rules, integration constraints, safety requirements and component roles.

Arm Sensor Hub owns implementation of its assigned STM32 services and hardware-facing behaviour.

Raspberry Sensor Hub owns implementation of its host-side integration.

External vendors define the behaviour of their equipment and protocols.

## Data and control flow

At system level:

1. Sensors are acquired by the Arm Sensor Hub.
2. Timestamped/coherent state is exposed through the system interfaces.
3. Raspberry-side integration owns estimator history and system-level host processing.
4. Commands flow from host/system control toward the Arm Sensor Hub and external actuator interface.
5. Fault, freshness, lifecycle, synchronization and safety gates constrain motion permission.
6. Recovery returns the system to an explicitly reactivated state and must not silently resume motion.

The exact service APIs, DMA ownership, scheduler details and codec implementation remain component documentation.

## Startup Flow

The system startup sequence ensures dependency ordering and safe initialization:

1. **HAL and peripheral initialization** in `main`: clock, GPIO, DMA, I2C, SPI, CAN, timer.
2. **RTOS kernel initialization** (`osKernelInitialize`).
3. **Application configuration** (`App_Init`): static RTOS resource creation, services configured to `INACTIVE`.
4. **Task creation**: execution context established (not itself activation).
5. **RTOS kernel start** (`osKernelStart`): scheduler begins.
6. **System/application task activation**: dependency-ordered (I2C → CAN → SPI → Sensor Task → System Manager).
7. **Periodic processing loop**: services process their tasks in sequence.

---

## Data Flow

**Sensor path:**
1. `SensorTask` uses `I2CManager` to read AS5600 encoders through the TCA9548A multiplexer.
2. Each encoder reading captures its acquisition timestamp immediately after receiving measurement bytes.
3. Normalized and timestamped values store in the sensor latest-value cache with validity and synchronization flags.

**Motor/CAN path:**
1. `CanService` registers configured motors and processes CAN RX/TX.
2. Polling sends periodic encoder-value and realtime-speed requests to each motor.
3. MKS codec decodes responses into generic feedback fields.
4. Decoded motor information stores in the motor latest-value cache with timestamp, quality, and diagnostic counters.

**Host/SPI path:**
1. `SnapshotBuilder` reads sensor and motor latest-value caches.
2. Serializes a coherent snapshot: six sensor records (always serialized, even if unavailable), motor records (up to eight).
3. `SpiSlaveService` stages the snapshot, arms DMA transfer, asserts `DATA_READY`.
4. Pi clocks the transaction; STM32 returns the staged frame while accepting the next request.

**Time synchronization path:**
1. Pi sends `TIME_SYNC` via SPI with its current time.
2. STM32 receives the update, captures local monotonic time, calculates offset.
3. Offset is atomically committed in `TimeService` state.
4. All exported timestamps use `local_time_us + time_offset_us` (hub-time domain).

---

## Architectural Decisions and Constraints

- **100 Hz baseline:** Baseline sensor/state publication and initial control-loop rate; current EKF is 500 Hz subject to integration constraints (SD-01).
- **Six-axis sampling:** Approximately 46 ms physical sweep is not a 500 Hz full-sweep rate; estimator behavior depends on timestamped/latest-value handling (SD-01, SD-08).
- **Differential end effector:** Requires explicit motor-to-DOF transformation; v1 schema cannot represent it (SD-26, SYS-MECH-001).
- **Motion authority:** System-level motion permission must be a defined authority rather than emergent property of individual state machines (SD-02, SD-23).
- **Independent safety:** Safety functions remain distinct from application controlled-stop behavior (SD-25).
- **Synchronization requirement:** Time-dependent motion requires valid time synchronization; expiry inhibits motion without stopping acquisition (SD-20).

---

## Provenance

Reconciled from `docs/project/system/architecture.md`. System-level architecture structure, data and control flow, startup sequence, and architectural decisions are Karetao-owned. Component implementation details (STM32 service/API, codec architecture, task scheduling, HAL integration), test procedures, and intern learning paths remain component-owned documentation.
