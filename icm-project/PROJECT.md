# Project: Karetao

Monorepo for the Karetao robotic arm platform. The system documentation authority is `Documentation/**`; start at `Documentation/00_INDEX.md`. Developer quick-reference: root `CLAUDE.md`.

## Components

| Path | What it is | Notes |
|---|---|---|
| `Arm_Sensor_Hub/` | STM32F405 firmware (CubeMX, CMake/Ninja, FreeRTOS) | git subtree. App code only in `App/` or CubeMX USER CODE sections |
| `RaspberryPi_Sensor_Hub/` | Raspberry Pi host side (Python stdlib, SPI master) | git subtree |
| `Documentation/` | System requirements, interfaces, safety, verification, decisions | Authority, see `authority.md` |
| `shared/` | Placeholder (empty) | Watched by CI |
| `workspace/` | ICM engineering workspace (generic) | git subtree of the private repo `Karetao_Consulting` once it is split out |

## Shared interfaces (keep in lockstep)

| Interface | Implementations | Contract |
|---|---|---|
| SPI frame format | `Arm_Sensor_Hub/App/Src/spi_protocol.c` + `App/Inc/spi_payload_layout.h`; `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py` | `Documentation/02_INTERFACES/SPI/` |
| Clock-sync observation (`request_received_local_us`) | STM32 SPI DMA ISR + TimeService; Pi `timing.py` / ClockSync | `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` |
| Host test source lists | `Arm_Sensor_Hub/CMakeLists.txt` and `Arm_Sensor_Hub/tests/host/CMakeLists.txt` | A new App module needs entries in both |
