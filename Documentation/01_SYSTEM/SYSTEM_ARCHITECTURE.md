# System Architecture

This document is the Karetao system-level architecture authority. It covers system structure and responsibilities, not component implementation.

## System structure

Karetao integrates:
1. **Arm Sensor Hub**: STM32-based hardware-facing control and sensor component.
2. **Raspberry Sensor Hub**: Raspberry Pi host-side component.
3. **External MKS controller equipment**: externally defined equipment and protocol behaviour.
4. **Safety behaviours for attended operation**: a hardware power cut or E-stop reachable by the operator, plus the application controls. No rating claimed ([PROJECT_CHARTER.md](PROJECT_CHARTER.md)).

The architectural boundary is:
```
Karetao system
├── Raspberry Sensor Hub (Pi)
│   ├── SPI master and time authority
│   ├── ClockSync model and snapshot decoding
│   ├── single gated commands
│   └── evidence tools
├── Arm Sensor Hub
│   ├── sensor acquisition
│   ├── actuator-facing services
│   └── system interface implementation
├── External MKS controller equipment
└── Safety behaviours (hardware power cut or E-stop, application controls)
```

## Responsibility model

Karetao owns the system requirements, system interfaces, timing/synchronization rules, integration constraints, safety requirements and component roles.

Arm Sensor Hub owns implementation of its assigned STM32 services and hardware-facing behaviour.
Raspberry Sensor Hub owns implementation of its host-side integration.
External vendors define the behaviour of their equipment and protocols.

## Motion gate

One system-level gate sits above service readiness, implemented in `motion_permission.c`. Its inputs per SYS-GATE-001 (lifecycle ACTIVE, CAN ACTIVE, link not stale, no global inhibit, motor ready) are decided in the Sprint 4 run ([ARCHITECTURE_DECISIONS.md](../07_DECISIONS/ARCHITECTURE_DECISIONS.md)). CAN ACTIVE is necessary but not sufficient.

## Data and control flow

1. Sensors are acquired by the Arm Sensor Hub.
2. Timestamped/coherent state is exposed through the system interfaces.
3. The Pi decodes snapshots, converts timestamps through ClockSync and files evidence.
4. Single gated commands flow from the Pi through the gate to the CAN motors.
5. Fault, lifecycle and link state feed the motion gate.
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
1. Pi records T1 and sends any request. The STM32 SPI DMA-complete ISR captures the raw TIM2 counter (T2).
2. The STM32 extends T2 to 64 bits in task context and returns it as `request_received_local_us` in the response. The Pi records T4.
3. `TimingSession.transact()` passes the correlated exchange to `ClockSync.record_exchange()`, which estimates offset and frequency.
4. Target (Issue #12): the STM32 exports raw local acquisition timestamps, ClockSync converts them to synchronized `measurement_timestamp_us`, and the STM32 performs no clock math. The Pi-side ClockSync conversion is not yet implemented.

## Architectural Decisions and Constraints

- **Rates and link parameters:** [PARAMETER_REGISTER.md](../06_CONFIGURATION/PARAMETER_REGISTER.md).
- **Six-axis sampling:** the sweep time and the I2C protocol floor are PRM-ACQ-02 and PRM-ACQ-03; the floor is a theoretical floor, not a measurement.
- **Differential end effector:** deferred until the hardware exists (charter non-goal); SD-26 stays proposed.
- **Motion authority:** the motion gate SYS-GATE-001 (Sprint 4).
- **Safety:** safety behaviours for attended operation ([SAFETY_REQUIREMENTS.md](../04_SAFETY/SAFETY_REQUIREMENTS.md)); no rating claimed.
- **Synchronization requirement:** single gated commands are not time-dependent motion; ClockSync validity governs timestamp usability, not the gate.

## Provenance

Reconciled from `docs/project/system/architecture.md`; realigned to the project charter on 2026-10-03.
