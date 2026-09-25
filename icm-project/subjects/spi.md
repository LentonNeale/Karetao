---
subject: spi
updated: 2026-09-25
---

# Subject: SPI link (Raspberry Pi ⇄ STM32 Arm Sensor Hub)

The Pi is the SPI master and the STM32 (SPI3) is the slave. Frames have a fixed size and a CRC; `DATA_READY` is a GPIO notification to the Pi. The frame format is implemented twice (C and Python) and must stay in lockstep.

## Owning documents

| Topic | Document | Sections |
|---|---|---|
| System SPI contract | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | §1 roles/physical, §3 frame, §4 transactions, §5 message types, §6 sequence, §7 DATA_READY, §8 coherency, §11–12 clock-sync, §13 host duties, §14 errors, §16 versioning and gates, §17 invariants |
| Payload layouts | `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` | SNAPSHOT, EVENT, DIAGNOSTIC (v1 and v2 note), VERSION, TIME_SYNC (deprecated), clock-sync extension, ACK/NACK, Maximum Sizes, Remaining Schema Decisions |
| Time model behind the sync fields | `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` | §2–§4 |
| STM32 pins and peripheral | `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md` | "SPI3 (Host Publication)", "DATA_READY GPIO" |
| Pi-side bring-up and test procedure | `RaspberryPi_Sensor_Hub/Documentation/RASPBERRY_PI_BRINGUP_V1.md` | Contract table, F4.6–F4.8 |
| Verification status | `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` ("SPI interface" row), `INTEGRATION_GATES.md` ("SPI" row) | |

## Requirements and decisions

| ID | Where defined | Status |
|---|---|---|
| SYS-SPI-001 (512-byte frame, 490-byte payload, Mode 0, LE, CRC-32/ISO-HDLC) | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` | Approved |
| SYS-SPI-002 (GET_SNAPSHOT priority, immutable DMA buffers, replace-if-new) | same | Approved |
| SYS-SPI-003 (DATA_READY notification, 1 ms polling recovery, Pi is master) | same | Approved |
| SYS-SPI-004 (20–30 cm cable, link test) | same | Proposed |
| SYS-TIM-003 (5 MHz initial ceiling) | same | Provisional |
| SD-15, SD-16, SD-17 | `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` | Approved |
| Ledger decisions C-1 (DATA_READY armed-then-assert), C-3 (512 fixed / 490 max payload) | `Documentation/05_REFACTORING_LEDGER.md` WP-1 | Decided |
| Clock-sync changes to SPI (request_received_local_us, GET_DIAGNOSTIC, TIME_SYNC deprecated) | `Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md` items 1, 4, 5, 8 | Decided; wire details open |

## Implementation

| Side / component | Files | Key entry points |
|---|---|---|
| STM32 framing and requests | `Arm_Sensor_Hub/App/Src/spi_protocol.c`, `App/Inc/spi_protocol.h` | `SpiProtocol_ValidateRequest`, `SpiProtocol_ProcessRequest`, `SpiProtocol_BuildSnapshotFrame` |
| STM32 frame constants and offsets | `Arm_Sensor_Hub/App/Inc/spi_payload_layout.h` | `SPI_FRAME_MAX_BYTES`, `SPI_FRAME_HEADER_BYTES`, offsets |
| STM32 slave service (DMA, staging) | `Arm_Sensor_Hub/App/Src/spi_slave_service.c`, `App/Inc/spi_slave_service.h` | `SpiSlaveService_Process`, `_BeginDmaTransfer`, `_CompleteDmaTransfer`, `_StageLatestSnapshot` |
| STM32 DATA_READY logic and pin | `Arm_Sensor_Hub/App/Src/spi_data_ready.c`; pin `Arm_Sensor_Hub/Core/Inc/main.h` (`Data_Ready_Pin`) | `SpiDataReady_OnFrameStaged`, `_OnFrameConsumed`, `_Poll` |
| STM32 CRC and snapshot assembly | `Arm_Sensor_Hub/App/Src/crc32_iso_hdlc.c`, `App/Src/snapshot_builder.c` | |
| Pi framing | `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py` | `SpiFrame.encode` / `decode`, `MessageType`, `NackReason` |
| Pi device and bus | `RaspberryPi_Sensor_Hub/src/spi/spi_device.py`, `spi_bus.py` | `SpiDevice.transact`, `get_status`, `get_version`; `SpidevBackend` |
| Pi DATA_READY and timing | `RaspberryPi_Sensor_Hub/src/spi/data_ready.py`, `timing.py` | `DataReadyWatcher`, `TimingSession` |
| Tests | `Arm_Sensor_Hub/tests/host/protocol_test_main.c`, `service_test_main.c`; `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py`, `test_spi_device.py` | |
| Bench tools | `RaspberryPi_Sensor_Hub/tools/spi_link_probe.py`, `spi_timing_harness.py`, `spi_measurement_harness.py` | |

## Status (as of `updated`)

| Item | State | Evidence |
|---|---|---|
| Framing, CRC, sequence, NACK (both sides) | implemented; verified (component) | host tests and Pi unit tests pass in CI |
| DMA slave service and DATA_READY (PA8) | implemented | `spi_slave_service.c`, `main.h`; hardware timing not yet measured |
| GET_SNAPSHOT, GET_VERSION | implemented | `spi_protocol.c` `SpiProtocol_ProcessRequest` |
| GET_STATUS | partial: returns a plain ACK with no status payload | `spi_protocol.c` `SpiProtocol_ProcessRequest` (default branch) |
| GET_DIAGNOSTIC / DIAGNOSTIC v2 | not implemented | Issue #12 decision item 8; #42 |
| `request_received_local_us` extension | not implemented | #42 |
| TIME_SYNC (0x12) | implemented but deprecated by Issue #12 | `SpiProtocol_ParseTimeSyncRequest` |
| Live Pi ⇄ STM32 integration at 5 MHz, cable test | not verified | verification matrix "SPI interface" row: OPEN; #44 |

## Known conflicts and open items

- **conflict:** `SYSTEM_REQUIREMENTS.md` SYS-SPI-003 qualification says "physical DATA_READY assignment remains unresolved", but `ARM_SENSOR_HUB.md` "DATA_READY GPIO" and `main.h` both use PA8.
- **open:** GET_DIAGNOSTIC message value, DIAGNOSTIC v2 field layout, and the wire placement of `request_received_local_us` (`SPI_PAYLOAD_SCHEMA.md` "Remaining Schema Decisions").
- **open:** the SYS-SPI-004 measurement method and acceptance criteria.

## Related issues

#44 (LIVE-03, SPI physical and host integration, release blocker) · #42 (clock-sync implementation touching SPI) · #45 (LIVE-04) · #13 (LIVE-09, system verification)

## Search scope

`Documentation/02_INTERFACES/`, `Documentation/01_SYSTEM/`, `Arm_Sensor_Hub/App/`, `Arm_Sensor_Hub/Documentation/`, `RaspberryPi_Sensor_Hub/src/spi/`, `RaspberryPi_Sensor_Hub/Documentation/`
