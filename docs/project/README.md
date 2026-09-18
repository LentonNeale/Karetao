> **Transitional status:** This legacy project documentation index is retained as source material. It is not the current Karetao documentation authority. Current system documentation is authoritative under [Documentation/](../../Documentation/), beginning with [Documentation/00_INDEX.md](../../Documentation/00_INDEX.md). Its historical organization and content remain available for reconciliation; directory location does not establish authority.

# Karetao Project Documentation

This directory is the canonical home for project-level engineering documentation.

## Document table

| Area | Document | Status | Purpose |
|---|---|---|---|
| System | [architecture.md](system/architecture.md) | Active | System architecture |
| System | [development.md](system/development.md) | Active | Development workflow |
| System | [TODO_List.md](system/TODO_List.md) | Active | Consolidated project TODOs |
| System | [QUESTIONS.md](QUESTIONS.md) | Active | Open project questions requiring decisions or evidence |
| System | [SYSTEM_DECISIONS.md](SYSTEM_DECISIONS.md) | Active | SD-01 through SD-25 system decision register |
| Hardware | [arm-sensor-hub-baseline.md](hardware/arm-sensor-hub-baseline.md) | Active | Arm sensor hub hardware baseline |
| Interfaces | [raspberry-pi-spi.md](interfaces/raspberry-pi-spi.md) | Active | Raspberry Pi SPI interface |
| Interfaces | [spi-service-contract.md](interfaces/spi-service-contract.md) | Active | SPI service interface contract |
| Protocols | [spi-contract.md](protocols/spi-contract.md) | Active | SPI protocol contract |
| Protocols | [spi-payload-schema.md](protocols/spi-payload-schema.md) | Active | SPI payload schema |
| Firmware | [APP_OVERVIEW.md](firmware/APP_OVERVIEW.md) | Active | STM32 application overview |
| Firmware | [BUILD_CONTRACT.md](firmware/BUILD_CONTRACT.md) | Active | STM32 build contract |
| Firmware | [CALIBRATION_CONTRACT.md](firmware/CALIBRATION_CONTRACT.md) | Active | Calibration contract |
| Firmware | [CAN_BIT_TIMING_EVIDENCE.md](firmware/CAN_BIT_TIMING_EVIDENCE.md) | Active | CAN bit-timing evidence |
| Firmware | [CAN_SERVICE_CONTRACT.md](firmware/CAN_SERVICE_CONTRACT.md) | Active | CAN service contract |
| Firmware | [CONTRACT_STATUS.md](firmware/CONTRACT_STATUS.md) | Active | Firmware contract status |
| Firmware | [CONTRACT_V1_FREEZE.md](firmware/CONTRACT_V1_FREEZE.md) | Active | Contract v1 freeze |
| Firmware | [ERROR_HANDLING_STRATEGY.md](firmware/ERROR_HANDLING_STRATEGY.md) | Active | Firmware error-handling strategy |
| Firmware | [HEALTH_MONITOR_CONTRACT.md](firmware/HEALTH_MONITOR_CONTRACT.md) | Active | Health-monitor contract |
| Firmware | [I2C_MANAGER_CONTRACT.md](firmware/I2C_MANAGER_CONTRACT.md) | Active | I2C manager contract |
| Firmware | [JOINT_MAPPING_CONTRACT.md](firmware/JOINT_MAPPING_CONTRACT.md) | Active | Joint mapping contract |
| Firmware | [LIFECYCLE_CONTRACT.md](firmware/LIFECYCLE_CONTRACT.md) | Active | Firmware lifecycle contract |
| Firmware | [MOTOR_SERVICE_CONTRACT.md](firmware/MOTOR_SERVICE_CONTRACT.md) | Active | Motor service contract |
| Firmware | [MULTI_SENSOR_CONTRACT.md](firmware/MULTI_SENSOR_CONTRACT.md) | Active | Multi-sensor contract |
| Firmware | [SAFETY_RELEASE_CHECKLIST.md](firmware/SAFETY_RELEASE_CHECKLIST.md) | Active | Safety release checklist |
| Firmware | [SNAPSHOT_COHERENCY_CONTRACT.md](firmware/SNAPSHOT_COHERENCY_CONTRACT.md) | Active | Sensor snapshot coherency contract |
| Firmware | [TIMESTAMP_SYNC_CONTRACT.md](firmware/TIMESTAMP_SYNC_CONTRACT.md) | Active | Timestamp synchronization contract |
| Operations | [RASPBERRY_PI_BRINGUP_V0.1.md](operations/RASPBERRY_PI_BRINGUP_V0.1.md) | Active | Raspberry Pi bring-up procedure |

## Archive

`archive/` contains superseded, deprecated, historical, or planning-only material retained for traceability. Archived documents are not authoritative requirements.

## Authority

When documents conflict, use the current project/system requirements and approved system decisions as the authority. Implementation status and historical review material must not silently redefine requirements.

## Migration note

Documentation formerly distributed between `docs/`, `Arm_Sensor_Hub/Documentation/`, `RaspberryPi_Sensor_Hub/docs/`, and agent-message folders has been consolidated here. Compatibility stubs are retained only where useful to avoid breaking existing links.
