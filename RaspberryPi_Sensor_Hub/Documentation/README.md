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

## SPI Interface Pin Mapping

Raspberry Pi header pins (implementation default: SPI0 CE0, `/dev/spidev0.0`; `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py`):

![RPi 5: Pinout](https://cdn.shopify.com/s/files/1/0474/7729/3217/files/1_8689da43-cdc0-488c-87f7-1ccefbff39c0.png?v=1769594138&width=2048) 

| Signal | Raspberry Pi Header pin | Wire | STM32 pin |
| --- | --- | --- | --- |
| MOSI | 19 | Dark Blue | PC12 |
| MISO | 21 | Green | PC11 |
| SCLK | 23 | Gray | PC10 |
| CE0 | 24 | Purple | PA15 |
| DATA_READY | 22 | Brown | PA8 |
| Ground | 20 | Black | Ground |

DATA_READY harness assignment: **GPIO25** (BCM numbering), `gpiochip4` line 25 on the Ubuntu 24.04 kernel (physical header pin 22), requested via libgpiod as an input with rising-edge events, Schmitt trigger enabled, and no internal pull (the STM32 drives the line push-pull). The pin is now wired on the current test rig, closing the "no physical GPIO assigned" half of SD-17's open issue (register §3.2). This is a Raspberry Sensor Hub harness decision, not a Karetao system requirement; the Karetao contract deliberately leaves the physical GPIO unspecified. SD-17's open issue remains unclosed until the pin is also **validated**: electrical and timing acceptance per `SPI_SYSTEM_INTERFACE.md` §16 has not been performed. Until that acceptance is recorded, the host runs polling-only at 1 ms, unchanged from the SD-17 baseline.

STM32 SPI3 side, for reference (`Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`, `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md`):

| Signal | STM32 pin | Direction |
| --- | --- | --- |
| NSS | PA15 | Input |
| SCK | PC10 | Input |
| MISO | PC11 | Output |
| MOSI | PC12 | Input |
| DATA_READY | PA8 | Output |

## Documentation Structure

This documentation directory follows the Karetao component documentation model:

- **System interface compliance:** How this component implements the Karetao system contracts
- **Host-side architecture:** SPI driver, estimator, command interface, ROS integration
- **Provisioning and deployment:** Pi image setup, software installation, configuration
- **Build and test:** Python packages, dependencies, test infrastructure
- **Component-level evidence:** Integration test results, protocol validation, timing measurements

All references to system-level requirements use stable identifiers (e.g., SYS-SPI-001, SD-18) rather than copying complete requirement text. For full requirement text, refer to Karetao's authoritative documents.
