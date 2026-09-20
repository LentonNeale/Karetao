# Arm Sensor Hub Documentation

This directory contains the Arm Sensor Hub component implementation documentation. It is authoritative for:

- Service architecture (I2CManager, CAN Service, SPI Slave Service, Sensor Task, Health Monitor)
- STM32F405 firmware APIs and internal state machines
- HAL/DMA configuration and interrupt handling
- FreeRTOS task structure and scheduling
- Build configuration (CMake, toolchain, presets)
- Internal diagnostics and testing
- Hardware peripheral configuration

## Authority Relationship

**Karetao system authority** (`Documentation/` in parent repository):

Karetao owns system-level requirements and contracts. This component references Karetao by stable identifiers:

- System role: `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md`
- System requirements: `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` (SYS-* identifiers)
- System interfaces:
  - I2C: `Documentation/02_INTERFACES/` (system interface defined; HAL implementation component-owned)
  - CAN: `Documentation/02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md` (system observable behavior; CanService implementation component-owned)
  - SPI: `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` (system contract; SpiSlaveService internals component-owned)
  - TIME: `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` (system synchronization; TimeService implementation component-owned)
- System lifecycle: `Documentation/01_SYSTEM/SYSTEM_LIFECYCLE.md` (canonical states; service-specific contracts component-owned)
- System architecture: `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md` (system-level flow; component flow component-owned)
- Configuration: `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` (SYS-* constraints; component-specific settings component-owned)
- Verification: `Documentation/05_VERIFICATION/` (system-level verification; component evidence component-owned)

**This component's implementation authority:**

This directory owns:
- Concrete I2CManager/CAN Service/SPI Slave Service/Sensor Task API definitions
- Internal task/state/queue/buffer structures
- DMA and interrupt handling strategy
- FreeRTOS task creation and scheduling
- CMake build configuration and presets
- Toolchain settings (arm-none-eabi-gcc/g++ version, optimization, flags)
- Component-level diagnostic and test infrastructure

This directory does **not** define system requirements or redefine Karetao system contracts.

**External authority:**

- MKS motor controller protocol and firmware: `docs/project/firmware/CAN_SERVICE_CONTRACT.md` legacy source (now in Karetao CAN_SYSTEM_INTERFACE.md)
- AS5600 rotary encoder: datasheet and register map
- TCA9548A I2C multiplexer: datasheet
- STM32F405 HAL and peripherals: ST reference manual and CubeMX-generated code
- FreeRTOS CMSIS-RTOS v2 API: CMSIS documentation

## Verification Traceability

```text
Karetao system requirement (SYS-*)
        ↓
Arm Sensor Hub implementation
        ↓
Component-level verification evidence (tests, measurements)
        ↓
Integration with Karetao system verification
```

Component verification (unit tests, functional tests on target hardware) provides evidence that this component implements its assigned responsibilities. It does not by itself constitute Karetao system-level verification. System verification is owned by Karetao and recorded in `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`.

## Documentation Structure

This documentation directory follows the Karetao component documentation model:

- **System interface compliance:** How this component implements the Karetao system contracts
- **Internal architecture:** Service APIs, data structures, execution model
- **Peripheral integration:** HAL usage, DMA configuration, interrupt handling
- **Build and test:** CMake structure, build presets, test infrastructure
- **Component-level evidence:** Verification results, test coverage, validation records

All references to system-level requirements use stable identifiers (e.g., SYS-CAN-001, SD-01) rather than copying complete requirement text. For full requirement text, refer to Karetao's authoritative documents.
