# Phase 1 Final Clearance Report

Date: 2026-09-07  
Repository: `LentonNeale/Arm_Sensor_Hub`

## Section A — Audit Scope

### Included paths

- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/App`
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Core`
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/tests`
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation`
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/CMakeLists.txt`
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/CMakePresets.json`

### Excluded paths

- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Drivers` except for ownership boundaries
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS` except for ownership boundaries
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/.github/agents`

### Tooling and evidence

- Repo inspection: `view`, `glob`, `rg`
- Build/test:
  - `cmake --preset HostTests`
  - `cmake --build --preset HostTests`
  - `ctest --preset HostTests --output-on-failure`
  - `cmake --preset Debug`
- Coverage:
  - host-only coverage build in `/tmp/ash-coverage`
  - `gcov -b -c` on `sprint1_protocol_tests` object files
- Static-analysis availability:
  - `clang-tidy` available but only practical on host-test modules in this environment
  - `cppcheck` not installed
  - `lizard` not installed

### Build/test results

- `HostTests`: configure/build/test **passed**
- Focused host regression surface: `tests/host/CMakeLists.txt:1-23`
- `Debug` configure: **blocked by missing `arm-none-eabi-gcc/g++`**
- Marker sweep on first-party code/doc paths: **no `TODO`/`FIXME`/`HACK`/`BUG` matches in owned source files**

## Section B — Architecture Integrity Matrix

| Module | Owner | Inbound dependencies | Outbound dependencies | Runtime entrypoints | Contract refs | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `app_init` | App bootstrap | `Core/Src/main.c` | `time_service`, `i2c_manager`, `sensor_task`, `can_service`, `spi_slave_service`, `health_monitor` | `App_Init`, `App_Start` | `README.md`, `LIFECYCLE_CONTRACT.md` | Warning |
| `time_service` | shared clock/sync | `app_init`, `sensor_task`, `can_service`, `as5600` | TIM2/HAL | `TimeService_Init`, `TimeService_NowUs`, sync APIs | `TIMESTAMP_SYNC_CONTRACT.md` | Warning |
| `i2c_manager` | I2C1 transport | `app_init`, `tca9548a_mux`, `as5600` | FreeRTOS, HAL I2C, TIM2 | blocking APIs, async APIs, HAL callbacks | `I2C_MANAGER_CONTRACT.md` | Blocked |
| `tca9548a_mux` | mux selection | `app_init`, `as5600`, `sensor_task` | `i2c_manager` | `TCA9548A_*` | `MULTI_SENSOR_CONTRACT.md`, `I2C_MANAGER_CONTRACT.md` | Warning |
| `as5600` | device protocol | `sensor_task` | `tca9548a_mux`, `i2c_manager`, `time_service` | `AS5600_*` | `MULTI_SENSOR_CONTRACT.md`, `TIMESTAMP_SYNC_CONTRACT.md` | Warning |
| `sensor_task` | sensor acquisition | default task loop | `as5600`, `time_service`, `sensor_latest_value`, GPIO | `SensorTask_*` | `MULTI_SENSOR_CONTRACT.md`, `SPI_SERVICE_CONTRACT.md` | Blocked |
| `can_tx_policy` | queue/recovery primitives | `can_service` | none | queue and bus-off helpers | `CAN_SERVICE_CONTRACT.md` | Clear |
| `can_service` | CAN/MKS transport | default task loop, `app_init` | HAL CAN, `time_service`, `motor_latest_value`, `can_tx_policy`, `mks_api.h` | `CanService_*` | `CAN_SERVICE_CONTRACT.md` | Warning |
| `snapshot_builder` | SPI frame staging | `spi_slave_service`, tests | fixed frame buffers | `SnapshotBuilder_Stage`, pool ops | `SNAPSHOT_COHERENCY_CONTRACT.md` | Clear |
| `spi_protocol` | request/response framing | `spi_slave_service`, tests | CRC helper | `SpiProtocol_*` | `SPI_CONTRACT.md`, `SPI_SERVICE_CONTRACT.md` | Clear |
| `spi_data_ready` | DATA_READY state | `spi_slave_service`, tests | none | `SpiDataReady_*` | `SPI_SERVICE_CONTRACT.md` | Clear |
| `spi_slave_service` | SPI3 publication | default task loop, `app_init` | `snapshot_builder`, `spi_protocol`, `spi_data_ready`, GPIO | `SpiSlaveService_*` | `SPI_SERVICE_CONTRACT.md` | Warning |
| `health_monitor` | system health | default task loop, `app_init` | none | `HealthMonitor_Init`, `HealthMonitor_Process` | `HEALTH_MONITOR_CONTRACT.md` | Blocked |
| `lifecycle` | state model | most services | none | `Lifecycle_*` | `LIFECYCLE_CONTRACT.md` | Warning |

## Section C — Dead Code / Disconnected Logic Register

| File / symbol | Type | Evidence | Remediation |
| --- | --- | --- | --- |
| `App/Src/i2c_manager.c`: `I2CManager_SubmitAsync`, `I2CManager_SetEventHook`, `I2CManager_SetEventQueue`, `I2CManager_SetTaskNotifyTarget` | Unintegrated async surface | declarations/definitions exist, but no application call sites were found | Either integrate async I2C ownership into a task flow or remove/de-scope the API until needed |
| `App/Src/spi_slave_service.c`: `SpiSlaveService_BeginDmaTransfer`, `SpiSlaveService_CompleteDmaTransfer`, `SpiSlaveService_ProcessRequestFrame` | Hardware integration surface with no caller | only self-reference and documentation references were found | Complete DMA/NSS/request wiring or explicitly keep these functions in “integration target only” status |
| `App/Src/can_service.c`: motor command APIs | Unused control surface | command entrypoints are defined and documented but are not called by any current first-party module | Keep as provisional API only if a near-term MotorService/client exists; otherwise treat as unexercised surface requiring tests before use |

## Section D — Code Smell / Inconsistency Register

| ID | Severity | Rule / source | Impacted files | Technical concern | Scope |
| --- | --- | --- | --- | --- | --- |
| ASH-AUD-001 | Medium | Coverage boundary | `tests/host/CMakeLists.txt:27-58` | service smoke coverage now exists for all first-party modules, but several hardware-failure, retry, and recovery branches remain shallow by design | Repo-wide |
| ASH-AUD-002 | Medium | Architecture debt | `App/Src/i2c_manager.c:375-415`, `App/Src/tca9548a_mux.c:92-117` | the composite mux+sensor ownership window is implemented specifically for the AS5600 path; broader multi-device arbitration policy is still not generalized | Localized |
| ASH-AUD-003 | Medium | Build evidence gap | `Documentation/BUILD_CONTRACT.md:44-59`, `Documentation/CONTRACT_STATUS.md:25` | host coverage is available, but embedded target build evidence still depends on external toolchain availability | Repo-wide |
| ASH-AUD-004 | Low | Verification depth | `tests/host/service_test_main.c` | new service smoke tests validate core paths and required negative paths, but they intentionally do not replace later hardware-integration or richer failure-mode suites | Repo-wide |
| ASH-AUD-005 | Medium | Coverage smell | `tests/host/CMakeLists.txt:1-45` vs `CMakeLists.txt:61-81` | host coverage now includes protocol primitives plus minimal service smoke coverage, but negative-path depth remains intentionally shallow for several hardware-facing services | Repo-wide |

## Section E — Loose Ends / Technical Debt Ledger

| Source | Affected functionality | Current state | Test state | Release risk |
| --- | --- | --- | --- | --- |
| `Documentation/CONTRACT_STATUS.md:13-25` | SPI/CAN/snapshot/time-sync integration | multiple rows still marked host-tested only, scaffold, or gated pending target validation | host primitives tested; end-to-end target flows absent | High |
| `Documentation/HEALTH_MONITOR_CONTRACT.md:22-51` | aggregate health model | read-only snapshot baseline is implemented; host publication, thresholds, and acknowledgement policy remain open | protocol and service smoke coverage exist | Medium |
| `Documentation/TIMESTAMP_SYNC_CONTRACT.md:28-59` | `TIME_SYNC` acceptance and stale-sync gating | live SPI dispatch now validates and forwards TIME_SYNC to `TimeService_AcceptSync()` in task context; target-hardware validation remains | protocol plus service smoke coverage exist | Medium |
| `Documentation/I2C_MANAGER_CONTRACT.md:56-69` | mux selection + sensor transaction atomicity | composite mux+sensor write/read path is now implemented for AS5600 access; broader arbitration policy remains open | basic host smoke coverage exists; contention depth remains limited | Medium |
| `Documentation/CAN_SERVICE_CONTRACT.md:44-46,78-89,125-133` | duplicate CAN IDs, RX overflow, command ordering, hardware recovery proof | documented as open decisions or future validation | host-only queue/policy tests | High |
| `Documentation/SPI_SERVICE_CONTRACT.md:78-135` | DMA/NSS callbacks and aborted transaction handling | contract exists; runtime wiring absent | host protocol and service smoke coverage exist; no target-hardware validation | High |

## Section F — Coverage Gap Matrix

### Host-tested modules (`gcov -b -c`)

| Module | Current test vehicle | Line coverage | Branch coverage | Gap |
| --- | --- | ---: | ---: | --- |
| `time_service.c` | `sprint1_protocol_tests` | 71.67% | 90.70% | global/runtime wrappers still rely on host harness coverage; target-hardware ingress remains unvalidated |
| `calibration_record.c` | `sprint1_protocol_tests` | 75.00% | 96.55% | additional invalid-record permutations missing |
| `joint_mapping.c` | `sprint1_protocol_tests` | 81.58% | 95.45% | negative-path permutations incomplete |
| `sensor_latest_value.c` | `sprint1_protocol_tests` | 80.00% | 66.67% | stale/freshness edge branches under-covered |
| `motor_latest_value.c` | `sprint1_protocol_tests` | 94.00% | 100.00% | remaining branch-taken paths are narrow |
| `snapshot_builder.c` | `sprint1_protocol_tests` | 78.26% | 96.15% | no-buffer and replacement combinations only partially exercised |
| `crc32_iso_hdlc.c` | `sprint1_protocol_tests` | 88.89% | 100.00% | minor branch residue |
| `spi_protocol.c` | `sprint1_protocol_tests` | 97.67% | 92.00% | broader invalid-message permutations remain available for deeper follow-up |
| `spi_data_ready.c` | `sprint1_protocol_tests` | 100.00% | 100.00% | clear |
| `can_tx_policy.c` | `sprint1_protocol_tests` | 100.00% | 100.00% | clear |

### Dark-matter production modules (compiled into firmware, absent from host tests)

| Module | Current test vehicle | Status |
| --- | --- | --- |
| `app_init.c` | `service_smoke_tests` | startup/activation smoke path covered |
| `lifecycle.c` | `sprint1_protocol_tests`, `service_smoke_tests` | core transitions covered |
| `i2c_manager.c` | `service_smoke_tests` | bad-arg and deferred async callback/event path covered |
| `tca9548a_mux.c` | `service_smoke_tests` | invalid-channel and composite access path covered |
| `as5600.c` | `service_smoke_tests` | bad-arg and composite status-read path covered |
| `sensor_task.c` | `service_smoke_tests` | bring-up communication-failure path covered |
| `can_service.c` | `service_smoke_tests` | invalid registration and inactive/active request gating covered |
| `spi_slave_service.c` | `service_smoke_tests` | inactive TIME_SYNC acceptance, staged-frame handoff, and bad-request path covered |
| `health_monitor.c` | `sprint1_protocol_tests`, `service_smoke_tests` | snapshot baseline covered |

## Section G — Critical Defect Punch-List

| Priority | Issue | Evidence | Owner | Phase 2 status |
| --- | --- | --- | --- | --- |
| P1 | Re-establish target build evidence in CI/runner | `cmake --preset Debug` fails without `arm-none-eabi-gcc/g++` in this environment | Build/CI | Blocking |
| P2 | Deepen negative-path coverage for hardware-facing service flows beyond smoke level | `service_smoke_tests` now cover core behavior, but several failure/recovery branches remain unexercised | Firmware + verification | Non-blocking follow-up |

## Section H — Clearance Decision

**Decision:** `Blocked pending target build validation`

### Gate reasons

- target-build evidence unavailable in current runner due missing embedded toolchain
