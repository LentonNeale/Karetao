# MksServo — MKS Servo CAN protocol library (C++17, embedded)

Pure protocol/codec library for MKS Servo42/57 CAN bus servos. Ported from a Python reference implementation that is not in this repository; the MKS protocol documents are in `icm-project/references/mks-servo42d-57d-can/`.

## What it does
- Encodes MKS command frames (`[cmd][payload][checksum8]`).
- Decodes/verifies response frames (checksum includes CAN ID).
- Numeric (de)serialization, argument validation, command metadata, protocol enums.
- Represents a generic CAN frame: `CanFrame { uint16_t id; uint8_t dlc; uint8_t data[8]; }`.

## What it does NOT do
No CAN TX/RX, no HAL/bxCAN, no FreeRTOS/CMSIS, no queues/tasks, no scheduling, no retries/timeouts, no bus recovery, no motor state machines, no ROS2/SPI/Pi. The STM32 bxCAN/HAL adapter is an example only (`adapters/`); the CAN Service owns all transport concerns.

## Design constraints (STM32F405 target)
- C++17, compiled static library.
- No dynamic allocation, no exceptions (`-fno-exceptions`), no RTTI (`-fno-rtti`).
- Fixed-size buffers only; max CAN DLC = 8; actual DLC used per command.
- Errors returned as `Status` enum + out-params (no exceptions cross the API).

## Layout
- `include/mksservo/` — C++ headers (`can_frame`, `status`, `enums`, `command`, `protocol_core`, `encoder`, `decoder`, `device_config`; all `.hpp`).
- `include/mks_api.h` — C-compatible (`extern "C"`) boundary for the C11 application layer.
- `src/` — compiled implementation (`command.cpp`, `decoder.cpp`, `encoder.cpp`, `protocol_core.cpp`, `mks_api.cpp`); `mks_api.cpp` is the only C/C++ seam.
- `adapters/stm32_bxcan.hpp` — optional example mapping `CanFrame` → `HAL_CAN_AddTxMessage` (not part of the lib target).
- `CMakeLists.txt` — static library target. There is no `tests/host/` directory in this library; the application host tests are in `Arm_Sensor_Hub/tests/host/`.

## Integration (intended architecture)
```
Application (C11) → Motor Service (C11) → mks_api.h (C boundary) → MksServo lib (C++17)
    → CanFrame → CAN Service (C11, queues/retries/timeouts/bus-off) → STM32 bxCAN/HAL → MKS Servo
```

## Reference (source of truth)
- MKS protocol documents: `icm-project/references/mks-servo42d-57d-can/` (command codes, enums, response formats)
- The C++ sources above (`include/mksservo/enums.hpp`, `command.hpp`, `decoder.hpp`, `protocol_core.hpp`) are the implementation of record; the Python reference named in earlier revisions is not in this repository
