# Raspberry Pi Sensor Hub Documentation

This directory contains the Raspberry Pi Sensor Hub component implementation documentation. It is authoritative for:

- Host-side integration and host application architecture
- SPI transport implementation (spidev, protocol encoding/decoding)
- Measurement history and estimator integration
- System command and state interfaces
- ROS 2 integration
- Host-side build configuration and provisioning
- Host-side diagnostics and testing

## Authority Relationship

**Karetao system authority** (`Documentation/` in parent repository):

Karetao owns system-level requirements and contracts. This component references Karetao by stable identifiers:

- System role: `Documentation/03_COMPONENTS/RASPBERRY_SENSOR_HUB.md`
- System requirements: `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` (SYS-* identifiers)
- System interfaces:
  - SPI: `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`, `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` (system contract; host driver implementation component-owned)
  - TIME: `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` (system synchronization; host time integration component-owned)
- System lifecycle: `Documentation/01_SYSTEM/SYSTEM_LIFECYCLE.md` (canonical states; host coordinator implementation component-owned)
- System architecture: `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md` (system-level flow; host-side execution component-owned)
- Configuration: `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` (SYS-* constraints; host-specific settings component-owned)
- Verification: `Documentation/05_VERIFICATION/` (system-level verification; component evidence component-owned)

**This component's implementation authority:**

This directory owns:
- SPI transport driver and protocol encoder/decoder
- Measurement history buffer and estimator integration
- System command interface and execution
- ROS 2 node architecture and integration
- Host-side lifecycle coordinator
- Provisioning and deployment procedures
- Host-side diagnostics and monitoring
- Build system and dependencies (Python, ROS packages)

This directory does **not** define system requirements or redefine Karetao system contracts.

**External authority:**

- Linux SPI subsystem (`spidev`): kernel interface and behavior
- Raspberry Pi 5 hardware: BCM2712 SoC, GPIO, pinout
- Raspberry Pi OS provisioning: cloud-init, package management
- PREEMPT_RT kernel patches: real-time scheduling extensions
- ROS 2 Jazzy: middleware, sensor_msgs, control_msgs
- Estimator/controller algorithms: downstream system documentation

## Verification Traceability

```text
Karetao system requirement (SYS-*)
        ↓
Raspberry Pi Sensor Hub implementation
        ↓
Component-level verification evidence (host-side tests, integration tests)
        ↓
Integration with Karetao system verification
```

Component verification (host protocol tests, integration testing with STM32, ROS 2 integration testing) provides evidence that this component implements its assigned responsibilities. It does not by itself constitute Karetao system-level verification. System verification is owned by Karetao and recorded in `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`.

## Documentation Structure

This documentation directory follows the Karetao component documentation model:

- **System interface compliance:** How this component implements the Karetao system contracts
- **Host-side architecture:** SPI driver, estimator, command interface, ROS integration
- **Provisioning and deployment:** Pi image setup, software installation, configuration
- **Build and test:** Python packages, dependencies, test infrastructure
- **Component-level evidence:** Integration test results, protocol validation, timing measurements

All references to system-level requirements use stable identifiers (e.g., SYS-SPI-001, SD-18) rather than copying complete requirement text. For full requirement text, refer to Karetao's authoritative documents.
