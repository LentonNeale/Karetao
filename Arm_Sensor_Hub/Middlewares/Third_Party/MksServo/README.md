# MksServo — MKS Servo CAN protocol library (C++17, embedded)

Pure protocol/codec library for MKS Servo42/57 CAN bus servos. Ported from the Python reference in `src/devices/mksservo/` + `src/protocol/`.

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
- `include/mksservo/` — C++ headers (`can_frame`, `status`, `enums`, `command`, `protocol_core`, `encoder`, `decoder`, `device_config`).
- `include/mks_api.h` — C-compatible (`extern "C"`) boundary for the C11 application layer.
- `src/` — compiled implementation; `mks_api.cpp` is the only C/C++ seam.
- `adapters/stm32_bxcan.hpp` — optional example mapping `CanFrame` → `HAL_CAN_AddTxMessage` (not part of the lib target).
- `tests/host/` — host-side (x86) unit + golden-vector + fuzz tests.

## Integration (intended architecture)
```
Application (C11) → Motor Service (C11) → mks_api.h (C boundary) → MksServo lib (C++17)
    → CanFrame → CAN Service (C11, queues/retries/timeouts/bus-off) → STM32 bxCAN/HAL → MKS Servo
```

## Reference (source of truth)
- `src/devices/mksservo/` (command codes, enums, per-group builders, decoder)
- `src/protocol/` (`core.py`, `responses.py`, `validation.py`, `message_types.py`)
