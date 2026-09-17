# Arm Sensor Hub

STM32F405RGT6 firmware project generated with STM32CubeMX and built with CMake.

## Technical Baseline (Project Snapshot)

This section is the current engineering baseline for onboarding. It summarizes the implemented architecture, active modules, and open integration work.

### System Objective

The firmware acts as a sensor hub on STM32F405:
- acquires sensor data from I2C (AS5600 via TCA9548A multiplexer),
- exchanges motor/control telemetry over CAN,
- publishes data to a Raspberry Pi over SPI (slave),
- uses DATA_READY signaling for host-side synchronization.

### Architecture Overview

- Platform layer:
  - STM32CubeMX generated startup, HAL drivers, linker/startup files.
  - FreeRTOS (CMSIS-RTOS v2) with a default task loop.
- Application layer (`App/`):
  - `sensor_task`: AS5600 bring-up and periodic six-axis sampling state machine.
  - `i2c_manager` + `tca9548a_mux`: I2C access and channel routing.
  - `can_service`: CAN transport-facing service and MKS protocol bridge.
  - `spi_slave_service`: SPI slave service, fixed-frame protocol path, DMA transfer ownership, and DATA_READY owner.
  - `health_monitor`: task-context aggregate health snapshot baseline.
- Protocol library layer:
  - `Middlewares/Third_Party/MksServo`: C++17 protocol codec library.
  - `mks_api.h`: C11-compatible boundary used by application C code.

### Current Implementation Status

- Build system:
  - Root firmware project builds with C11 + C++17 support.
  - MksServo library is linked as a third-party module.
  - HostTests cover both protocol/data-plane primitives and minimal service smoke paths.
  - CI builds HostTests, Debug firmware, and Release firmware; the current baseline run also records firmware size/checksum information and uploads the firmware artifacts.
- I2C sensor path:
  - Six stable logical sensor records are processed per scheduler pass.
  - The commissioned logical mapping is axis 0-5 -> TCA9548A channels 2-7 (SD2-SD7), with configurable binding and activation gating for invalid maps.
  - Physical commissioning evidence exists for all six mapped axes under the recorded bench conditions.
  - The measured full six-axis sweep is approximately 46 ms; the 20 ms value is a scheduler period, not an accepted 20 ms full-scan completion time. Scan timing parameters remain unfrozen.
- CAN path:
  - Thin C11 wrappers implemented for key MKS commands:
    - motor enable/disable,
    - emergency stop,
    - absolute/relative pulse move,
    - encoder value request,
    - realtime speed request.
  - Per-motor registration supports model-specific config (Servo42/Servo57) and CAN ID validation.
  - RX FIFO processing includes MKS frame decode and per-motor response/error counters.
  - Lightweight periodic polling scheduler alternates encoder and speed requests.
  - Physical CAN behavior remains unvalidated.
- SPI path:
  - Raspberry Pi SPI0 CE0 backend uses Linux `spidev` with `/dev/spidev0.0`, mode 0, 8 bits per word, configured maximum 5 MHz, and fixed 512-byte transfers.
  - Raspberry Pi protocol decoding enforces protocol version, frame size/payload limits, CRC, and zero-padding rules.
  - STM32 SPI3 uses RX/TX DMA with task-context error/host-stall recovery and the approved armed-then-assert DATA_READY model.
  - The STM32 DMA software path has target evidence from a physical run, but no live Raspberry Pi transaction was clocked; 5 MHz, NSS, DATA_READY electrical timing, GPIO behavior, signal integrity, and sustained real transactions remain acceptance gates.
- Health path:
  - Read-only aggregate snapshot baseline implemented for lifecycle states, sync validity, and core service counters.

### Runtime Flow (Current)

1. `App_Init()` initializes managers/services and registers configured MKS motors and commissioned sensor mux mapping.
2. FreeRTOS default task repeatedly runs sensor processing and CAN service processing.
3. CAN service transmits encoded MKS frames and decodes inbound responses.
4. Sensor diagnostics and CAN response snapshots are retained in memory for integration/debug.
5. `SpiSlaveService_Process()` manages staged frames, DMA recovery, request processing, and DATA_READY ownership.

### Open Work / Next Milestones

- See [Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md](../../Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md) for the system-wide lifecycle vocabulary, transition rules, dependency model, and service contract template.

- Freeze the six-axis scan period, mux settle delay, per-channel timeout, and healthy-channel threshold against the measured approximately 46 ms full-axis sweep.
- Validate the implemented SPI path with a live Raspberry Pi host and accept the 5 MHz maximum only after DMA timing, NSS, DATA_READY/GPIO timing, signal integrity, sustained transactions, and real request/response evidence are recorded.
- Add CAN TX queueing policy, retry/timeout strategy, and bus-off recovery policy.
- Add integration tests for end-to-end sensor-to-host data path.
- Validate TIME_SYNC end-to-end on target hardware.
- Complete calibration persistence, motor-controller semantics, and independent safety validation.

### API Reference (One-Page)

This reference summarizes the currently exposed firmware interfaces and the host-facing SPI payload contract.

#### CAN Service Public Functions

Header: App/Inc/can_service.h

| Function | Purpose | Notes |
| --- | --- | --- |
| CanService_Init(void) | Initializes CAN service runtime state and starts CAN peripheral path. | Call once during App_Init. |
| CanService_Process(void) | Periodic service loop work (RX decode plus poll scheduler). | Call from a periodic task loop. |
| CanService_RegisterMotor(uint8_t motor_index, uint8_t logical_joint_id, uint32_t configuration_version, CanService_MksModel model, uint16_t can_id) | Registers a logical motor slot bound to a joint mapping version, servo model, and CAN ID. | Valid motor index range is 0..CAN_SERVICE_MAX_MKS_MOTORS-1. |
| CanService_SendMotorEnable(uint8_t motor_index, bool enable) | Sends motor enable or disable command via MKS encoder. | Returns MksStatus. |
| CanService_SendEmergencyStop(uint8_t motor_index) | Sends emergency stop command via MKS encoder. | Returns MksStatus. |
| CanService_SendAbsolutePulseMove(uint8_t motor_index, uint16_t speed, uint8_t acc, int32_t absolute_pulses) | Sends absolute pulse move command via MKS encoder. | Returns MksStatus. |
| CanService_SendRelativePulseMove(uint8_t motor_index, bool dir_cw, uint16_t speed, uint8_t acc, uint32_t relative_pulses) | Sends relative pulse move command via MKS encoder. | Returns MksStatus. |
| CanService_RequestEncoderValue(uint8_t motor_index) | Sends encoder value request. | Returns MksStatus. |
| CanService_RequestRealtimeSpeed(uint8_t motor_index) | Sends realtime speed request. | Returns MksStatus. |
| CanService_SetPollPeriodMs(uint32_t period_ms) | Sets internal CAN poll scheduler period. | Set 0 to disable automatic poll scheduling. |
| CanService_GetLastResponse(uint8_t motor_index, MksParsedResponse *out_response) | Retrieves latest decoded MKS response for a motor. | Returns true when response is available. |
| CanService_GetRxOkCount(uint8_t motor_index) | Returns successful decode counter for a motor. | Monotonic counter since registration/init. |
| CanService_GetRxDecodeErrorCount(uint8_t motor_index) | Returns decode error counter for a motor. | Monotonic counter since registration/init. |

MksStatus result interpretation:
- MKS_OK means command was encoded and handed to CAN TX path.
- Non-MKS_OK values represent argument validation, codec, or transport handoff failure.

#### Sensor Task Diagnostics Structure

Header: App/Inc/sensor_task.h
Structure: SensorTask_BringupSnapshot

| Field | Type | Meaning |
| --- | --- | --- |
| result | SensorTask_BringupResult | Current sensor bring-up state (pass/fail category). |
| init_stage | SensorTask_InitStage | Current initialization stage (MUX, sensor, active). |
| is_active | uint8_t | Non-zero when task is in active sampling mode. |
| mux_readback_mask | uint8_t | Last observed TCA9548A channel mask. |
| last_raw_angle | uint16_t | Most recent raw encoder angle from AS5600. |
| last_status | uint8_t | Most recent AS5600 status register value. |
| last_timestamp_us | uint32_t | Timestamp (microseconds) associated with last reading. |
| sample_ok_count | uint32_t | Count of successful samples. |
| comm_error_count | uint32_t | Count of communication failures. |
| magnet_error_count | uint32_t | Count of magnetic field quality failures. |

Associated accessors:
- SensorTask_GetBringupResult(void)
- SensorTask_GetBringupSnapshot(void)
- SensorTask_GetBringupDiagWord(void)
- SensorTask_IsActive(void)

#### Expected SPI Data Contract

The complete host contract is maintained in [docs/protocols/spi-contract.md](../protocols/spi-contract.md). The SPI service implements the transport path and explicitly separates implementation state from remaining physical acceptance gates.

The key timestamp distinction is:

| Offset | Size | Field | Description |
| --- | --- | --- | --- |
| 10 | 8 | frame_time_us | Synchronized STM32 hub time at frame assembly; not a measurement timestamp. |

Individual sensor and motor records carry `measurement_timestamp_us`, representing acquisition time in the Raspberry Pi time domain. The STM32 derives that time as `local_time_us + time_offset_us`; it does not reset its monotonic local clock.

The contract also defines a `TIME_SYNC` message from the Raspberry Pi, synchronization validity reporting, sequence handling, CRC validation, explicit SPI buffer ownership, and armed-then-assert DATA_READY semantics. The first synchronization implementation may use a direct offset update; two-way delay estimation is reserved for a later version.

Draft snapshot payload concept (message_type=1):

| Field | Type | Description |
| --- | --- | --- |
| sensor_count | uint8_t | Number of encoded sensor records. |
| can_motor_count | uint8_t | Number of encoded motor response records. |
| flags | uint16_t | Bit flags for health/state summary. |
| sensor_records[] | repeated | Each record includes sensor ID, status, `measurement_timestamp_us`, and value fields. |
| motor_records[] | repeated | Each record includes motor index, CAN ID, command/status data, and `measurement_timestamp_us`. |

## MCU and Clock

- MCU: STM32F405RGT6 (LQFP64)
- HSE: 8 MHz external oscillator (PH0/PH1)
- SYSCLK: 168 MHz

## Pinout (Grouped by Interface)

### SWD Debug

| Pin | Signal | Notes |
| --- | --- | --- |
| PA13 | SYS_JTMS-SWDIO | ST-Link SWDIO |
| PA14 | SYS_JTCK-SWCLK | ST-Link SWCLK |

### Clock (HSE)

| Pin | Signal | Notes |
| --- | --- | --- |
| PH0 | RCC_OSC_IN | External crystal/clock input |
| PH1 | RCC_OSC_OUT | External crystal/clock output |

### GPIO

| Pin | Signal | Direction | Notes |
| --- | --- | --- | --- |
| PA8 | Data_Ready | Output (Push-Pull) | User-defined output, default low |

### I2C1

| Pin | Signal | Notes |
| --- | --- | --- |
| PB6 | I2C1_SCL | Fast mode (400 kHz) |
| PB7 | I2C1_SDA | Fast mode (400 kHz) |

### CAN1

| Pin | Signal | Notes |
| --- | --- | --- |
| PB8 | CAN1_RX | CAN receive |
| PB9 | CAN1_TX | CAN transmit |

### SPI3 (Slave)

| Pin | Signal | Notes |
| --- | --- | --- |
| PA15 | SPI3_NSS | Hardware NSS input |
| PC10 | SPI3_SCK | SPI clock |
| PC11 | SPI3_MISO | SPI MISO |
| PC12 | SPI3_MOSI | SPI MOSI |

## Peripheral Notes

- SPI3 runs in slave mode, 8-bit, 2-line, hardware NSS.
- SPI3 DMA:
  - RX: DMA1_Stream0 (very high priority)
  - TX: DMA1_Stream5 (high priority)
- CAN1 pins are mapped to PB8/PB9.
- FreeRTOS is enabled (CMSIS-RTOS v2), default task created.

## Build

Use the existing preset-based build flow:

```bash
cd Arm_Sensor_Hub
cmake --preset Debug
cmake --build --preset Debug
```
