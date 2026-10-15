# Raspberry Pi Sensor Hub Documentation

This directory contains the Raspberry Pi Sensor Hub component implementation documentation. It is authoritative for:

- Host-side integration and host application architecture
- SPI transport implementation (spidev, protocol encoding/decoding)
- System command and state interfaces
- Future, not now: ROS 2 integration and any estimator are charter non-goals (`Documentation/01_SYSTEM/PROJECT_CHARTER.md`)
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
- System command interface and execution
- Host-side lifecycle coordinator
- Provisioning and deployment procedures
- Host-side diagnostics and monitoring
- Build system and dependencies (Python)

This directory does **not** define system requirements or redefine Karetao system contracts.

**External authority:**

- Linux SPI subsystem (`spidev`): kernel interface and behavior
- Raspberry Pi 5 hardware: BCM2712 SoC, GPIO, pinout
- Raspberry Pi OS provisioning: cloud-init, package management
- PREEMPT_RT kernel patches: real-time scheduling extensions

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

Component verification (host protocol tests, integration testing with STM32) provides evidence that this component implements its assigned responsibilities. It does not by itself constitute Karetao system-level verification. System verification is owned by Karetao and recorded in `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`.

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

## SPI Timing Harness

`tools/spi_timing_harness.py` sweeps clock rate x CPU load x message type and writes one row per transaction for offline analysis. It measures the polled request/response path only; DATA_READY assert-to-service latency is out of scope until the GPIO watcher exists (SD-17).

```bash
python3 tools/spi_timing_harness.py --clocks 1000000,2000000,5000000 --loads 0,2,4 \
    --iterations 5000 --affinity 3 --rt-priority 50 --outdir evidence/
python3 tools/spi_timing_harness.py --fake      # exercise the harness with no STM32 attached
```

Each run writes `<run_id>_transactions.csv` (per transaction), `<run_id>_blocks.csv` (environment sampled around each block) and `<run_id>_metadata.json` (firmware identity, host state, configuration).

**`transfer_ns` and `round_trip_ns` are not the same measurement and must not be compared as if they were.** `transfer_ns` is wire time for one 512-byte transfer. Because the transaction model is pipelined (`SPI_SYSTEM_INTERFACE.md` §4), the reply to a request is staged only after that request has been clocked in, so it arrives during a later transfer; `round_trip_ns` is reconstructed from the correlation field each response carries (`response_to_seq`, or `request_seq` on ACK/NACK) and therefore spans at least two transfers. A row whose `correlated_seq` is empty had no matching outstanding request, and its `round_trip_ns` is blank rather than zero.

Runs are only admissible as evidence (`Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md`) when `metadata.json` reports `dirty_build: false`; a dirty firmware build means the reported git hash does not identify the source that produced the numbers. Check `throttled` and `cpu_temp_c` in the block records before trusting tail latencies, since a throttled Pi produces misleading p99s.

## Run records and the evidence-record tool

`src/spi/run_record.py` implements the run-directory contract in `Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md` ("Run directories"; GitHub #109, #70): `meta.json` with the run kind and name, rig, the `PRM-*`, `LIVE-*` or `SYS-*` identifiers the run informs, the local start time with its UTC offset (`started_now()`), the firmware identity decoded from `VERSION`, the Pi commit and dirty flag, and the capture command, plus one CSV per series. Capture tools write it with `write_run`, which validates before writing; the PC-side analysis and the record tool read it with `read_run`. The Pi dirty flag comes from `git status --porcelain -- RaspberryPi_Sensor_Hub shared`, the mirror of the firmware's build-time check, and a git failure is recorded as unknown and dirty rather than clean.

`tools/evidence_record.py <run directory>` drafts the evidence record from `meta.json` (see `EVIDENCE_RECORD_FORMAT.md`, "Drafting a record"):

```bash
python3 tools/evidence_record.py BenchWork/runs/2026-10-20-spi-link-phase5          # print the draft
python3 tools/evidence_record.py BenchWork/runs/2026-10-20-spi-link-phase5 --file   # file it under Documentation/05_VERIFICATION/evidence/
python3 tools/evidence_record.py <run directory> --file --require-clean              # exit 2 unless the run can satisfy a matrix row
```

The draft fills every tool-readable field and states whether the run may satisfy a matrix row (clean firmware build and clean Pi tree). Result and Accepted by are completed by hand. Tools adopt the format one at a time; `spi_link_probe.py` is first (GitHub #110).

## Documentation Structure

This documentation directory follows the Karetao component documentation model (`Documentation/DOCUMENTATION_RULES.md`):

- **System interface compliance:** How this component implements the Karetao system contracts
- **Host-side architecture:** snapshot decoding, ClockSync, single gated commands, evidence tools
- **Provisioning and deployment:** Pi image setup, software installation, configuration
- **Build and test:** Python packages, dependencies, test infrastructure
- **Component-level evidence:** Integration test results, protocol validation, timing measurements

All references to system-level requirements use stable identifiers (e.g., SYS-SPI-001, SD-18) rather than copying complete requirement text. For full requirement text, refer to Karetao's authoritative documents.
