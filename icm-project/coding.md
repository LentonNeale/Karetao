# Coding conventions (Karetao)

Read by `python-dev`, `c11-dev` and `cpp17-dev`. The build rules are owned by `Arm_Sensor_Hub/Documentation/BUILD_CONTRACT.md`; this file points to that contract and adds only what developers need day to day.

## General

- Change only what the approved plan names. Interfaces in `PROJECT.md` "Shared interfaces" change in lockstep on both sides, so a single-language agent escalates them.
- A firmware source change is done only when the Debug build passes. Host tests must pass too (`build.md`).
- Tests prove component behaviour only. Never describe host-test results as hardware or system verification.

## C (STM32 application, `Arm_Sensor_Hub/App/`)

- C11. Modules are `App/Src/<module>.c` + `App/Inc/<module>.h`, with public functions named `<Module>_<Action>` (for example `SpiProtocol_ProcessRequest`). Each file starts with a Doxygen `@file` / `@brief` header, and headers have include guards and `extern "C"` guards.
- **Generated code:** anything under `Core/` and `Drivers/` is CubeMX output. Edit only between `/* USER CODE BEGIN … */` and `/* USER CODE END … */`, and put application logic in `App/`.
- **New source file:** add it to `Arm_Sensor_Hub/CMakeLists.txt` **and** to the relevant executable(s) in `Arm_Sensor_Hub/tests/host/CMakeLists.txt`, and add any HAL or FreeRTOS stubs to `tests/host/stubs/`.
- **Escalate:** anything that runs in, or shares data with, an ISR or DMA callback (for example `spi_slave_service.c` DMA completion; `TimeService_NowUs()` is not ISR-safe), RTOS task or queue code, lifecycle, health and motion-permission logic, and buffer sizes in `spi_payload_layout.h`.

## C++ (MksServo library, `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/`)

- C++17, compiled with `-fno-exceptions -fno-rtti -fno-threadsafe-statics`. No heap allocation, exceptions, RTTI or iostreams.
- `include/mks_api.h` is the only C-compatible boundary; the application reaches C++ only through it. Changing it is a cross-language change, so escalate.
- It is built as part of the firmware (Debug/Release presets). The host `service_smoke_tests` include its headers.

## Python (Raspberry Pi host, `RaspberryPi_Sensor_Hub/`)

- Python 3.12+ (CI runs 3.12; the Pi runs Ubuntu 24.04's python3 3.12), **standard library only**. `from __future__ import annotations`, type hints, and a module docstring on the first line.
- Code lives in `src/spi/`, tests in `tests/spi/test_*.py` (`unittest`, no pytest-only features), and bench tools in `tools/`.
- `spi_protocol.py` mirrors the C frame format (a shared interface): escalate format or constant changes.
