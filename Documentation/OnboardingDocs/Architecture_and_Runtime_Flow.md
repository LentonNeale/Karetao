# Architecture and Runtime Flow

## High-Level Layers

The codebase is easiest to understand as three layers.

## 1. Platform Layer

Owned mostly by STM32CubeMX-generated code:

- MCU startup
- HAL peripheral initialization
- DMA, interrupts, and linker/startup support
- FreeRTOS kernel startup

Key file: [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Core/Src/main.c`](../../Core/Src/main.c)

## 2. Application Layer

Owned by the project in `App/`.

Important modules:

- `app_init`: initializes services and registers known configuration
- `sensor_task`: sensor bring-up and sampling state machine
- `i2c_manager` and `tca9548a_mux`: shared I2C access and channel selection
- `can_service`: CAN transport-facing service and MKS message handling
- `spi_slave_service`: SPI request/response path and staged snapshot ownership
- `time_service`: monotonic time and synchronization state
- `snapshot_builder`: coherent frame assembly
- `health_monitor`: health scaffold for broader diagnostics

## 3. Protocol Library Layer

`Middlewares/Third_Party/MksServo` is a transport-agnostic C++17 codec library. It handles frame encoding/decoding, while the application layer owns scheduling, retries, lifecycle gating, and HAL-facing transport behavior.

## Startup Flow

The main runtime flow is:

1. HAL and peripheral initialization in `main`
2. RTOS kernel initialization
3. `App_Init()` during scheduler setup
4. default task starts and calls `App_Start()`
5. default task loops over the main services:
   - `I2CManager_Process()`
   - `SensorTask_Process()`
   - `CanService_Process()`
   - `SpiSlaveService_Process()`
   - `HealthMonitor_Process()`

This loop is visible in [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Core/Src/main.c`](../../Core/Src/main.c).

## Data Flow

### Sensor path

1. `sensor_task` uses `i2c_manager` and `tca9548a_mux`.
2. `as5600` reads status and angle data.
3. `sensor_latest_value` stores normalized latest values with validity and timing metadata.

### Motor/CAN path

1. `can_service` registers configured motors.
2. the MKS codec builds or decodes CAN payloads,
3. latest decoded motor information is stored in `motor_latest_value`.

### Host/SPI path

1. `snapshot_builder` prepares frame data,
2. `spi_protocol` applies framing rules,
3. `spi_slave_service` stages responses/snapshots and manages `DATA_READY`.

## What Is Mature Vs What Is Emerging

More mature:

- contract structure,
- snapshot/payload constants,
- host-side validation path,
- lifecycle vocabulary,
- time sync model,
- single-channel sensor path.

Less mature or still being integrated:

- six-channel sensor scheduling,
- final SPI DMA/NSS hardware integration,
- complete TIME_SYNC dispatch through live SPI command handling,
- expanded health aggregation,
- end-to-end target-hardware evidence.

## Files Interns Should Learn Early

- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/README.md`](../../README.md)
- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md`](../CONTRACT_STATUS.md)
- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md`](../LIFECYCLE_CONTRACT.md)
- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/App/Src/app_init.c`](../../App/Src/app_init.c)
- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Core/Src/main.c`](../../Core/Src/main.c)
- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/tests/host/protocol_test_main.c`](../../tests/host/protocol_test_main.c)

