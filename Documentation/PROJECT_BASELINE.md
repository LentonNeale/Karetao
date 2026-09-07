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
  - `sensor_task`: AS5600 bring-up and periodic sampling state machine.
  - `i2c_manager` + `tca9548a_mux`: I2C access and channel routing.
  - `can_service`: CAN transport-facing service and MKS protocol bridge.
  - `spi_slave_service`: SPI slave service skeleton for host transfer path.
  - `health_monitor`: task-context aggregate health snapshot baseline.
- Protocol library layer:
  - `Middlewares/Third_Party/MksServo`: C++17 protocol codec library.
  - `mks_api.h`: C11-compatible boundary used by application C code.

### Current Implementation Status

- Build system:
  - Root firmware project builds with C11 + C++17 support.
  - MksServo library is linked as a third-party module.
  - HostTests cover both protocol/data-plane primitives and minimal service smoke paths.
- I2C sensor path:
  - AS5600 single-channel bring-up path implemented with diagnostics and status snapshots.
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
- SPI path:
  - Interface skeleton present; full payload protocol integration remains to be completed.
- Health path:
  - Read-only aggregate snapshot baseline implemented for lifecycle states, sync validity, and core service counters.

### Runtime Flow (Current)

1. `App_Init()` initializes managers/services and registers configured MKS motors.
2. FreeRTOS default task repeatedly runs sensor processing and CAN service processing.
3. CAN service transmits encoded MKS frames and decodes inbound responses.
4. Sensor diagnostics and CAN response snapshots are retained in memory for integration/debug.

### Open Work / Next Milestones

- See [LIFECYCLE_CONTRACT.md](LIFECYCLE_CONTRACT.md) for the system-wide lifecycle vocabulary, transition rules, dependency model, and service contract template.

- Expand from single AS5600 bring-up to all six encoder channels via TCA9548A scheduling.
- Define and implement the SPI host contract to Raspberry Pi. The current pre-freeze/approval baseline is [SPI_CONTRACT.md](SPI_CONTRACT.md), reconciled by [CONTRACT_V1_FREEZE.md](CONTRACT_V1_FREEZE.md), and includes framing, timestamps, time synchronization, DATA_READY, and coherency rules.
- Add CAN TX queueing policy, retry/timeout strategy, and bus-off recovery policy.
- Add integration tests for end-to-end sensor-to-host data path.

### API Reference (One-Page)

This reference summarizes the currently exposed firmware interfaces and the draft host-facing SPI payload contract.

#### CAN Service Public Functions

Header: App/Inc/can_service.h

| Function | Purpose | Notes |
| --- | --- | --- |
| CanService_Init(void) | Initializes CAN service runtime state and starts CAN peripheral path. | Call once during App_Init. |
| CanService_Process(void) | Periodic service loop work (RX decode plus poll scheduler). | Call from a periodic task loop. |
| CanService_RegisterMotor(uint8_t motor_index, CanService_MksModel model, uint16_t can_id) | Registers a logical motor slot with servo model and CAN ID. | Valid motor index range is 0..CAN_SERVICE_MAX_MKS_MOTORS-1. |
| CanService_SendMotorEnable(uint8_t motor_index, bool enable) | Sends motor enable or disable command via MKS encoder. | Returns MksStatus. |
| CanService_SendEmergencyStop(uint8_t motor_index) | Sends emergency stop command. | Returns MksStatus. |
| CanService_SendAbsolutePulseMove(uint8_t motor_index, uint16_t speed, uint8_t acc, int32_t absolute_pulses) | Sends absolute pulse move command. | Returns MksStatus. |
| CanService_SendRelativePulseMove(uint8_t motor_index, bool dir_cw, uint16_t speed, uint8_t acc, uint32_t relative_pulses) | Sends relative pulse move command. | Returns MksStatus. |
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

The complete host contract is maintained in [SPI_CONTRACT.md](SPI_CONTRACT.md). The SPI service remains a transport scaffold; the document is the implementation target and explicitly separates transport, data model, and time synchronization.

The key timestamp distinction is:

| Offset | Size | Field | Description |
| --- | --- | --- | --- |
| 10 | 8 | frame_time_us | Synchronized STM32 hub time at frame assembly; not a measurement timestamp. |

Individual sensor and motor records must carry `measurement_timestamp_us`, representing acquisition time in the Raspberry Pi time domain. The STM32 derives that time as `local_time_us + time_offset_us`; it does not reset its monotonic local clock.

The contract also defines a `TIME_SYNC` message from the Raspberry Pi, synchronization validity reporting, sequence handling, CRC validation, explicit SPI buffer ownership, and DATA_READY semantics. The first synchronization implementation may use a direct offset update; two-way delay estimation is reserved for a later version.

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
cmake --preset Debug
cmake --build --preset Debug
```
