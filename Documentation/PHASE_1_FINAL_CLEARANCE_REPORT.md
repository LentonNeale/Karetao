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
| `TEMP/MksServo` | Orphan/duplicate source tree | `diff -qr Middlewares/Third_Party/MksServo TEMP/MksServo` reports divergent `CMakeLists.txt`; `TEMP` adds tests not present in the active library tree | Decide whether `TEMP/MksServo` is archival-only or a maintained attachment; if archival, quarantine it from engineering truth paths |
| `App/Src/time_service.c`: `TimeService_AcceptSync`, `TimeService_IsSyncValid` | Public API with no production caller | only definitions and header declarations are present; no runtime call sites were found | Wire `TIME_SYNC` acceptance through live SPI command handling or demote the API from claimed runtime readiness |
| `App/Src/i2c_manager.c`: `I2CManager_SubmitAsync`, `I2CManager_SetEventHook`, `I2CManager_SetEventQueue`, `I2CManager_SetTaskNotifyTarget` | Unintegrated async surface | declarations/definitions exist, but no application call sites were found | Either integrate async I2C ownership into a task flow or remove/de-scope the API until needed |
| `App/Src/spi_slave_service.c`: `SpiSlaveService_BeginDmaTransfer`, `SpiSlaveService_CompleteDmaTransfer`, `SpiSlaveService_ProcessRequestFrame` | Hardware integration surface with no caller | only self-reference and documentation references were found | Complete DMA/NSS/request wiring or explicitly keep these functions in “integration target only” status |
| `App/Src/can_service.c`: motor command APIs | Unused control surface | command entrypoints are defined and documented but are not called by any current first-party module | Keep as provisional API only if a near-term MotorService/client exists; otherwise treat as unexercised surface requiring tests before use |

## Section D — Code Smell / Inconsistency Register

| ID | Severity | Rule / source | Impacted files | Technical concern | Scope |
| --- | --- | --- | --- | --- | --- |
| ASH-AUD-001 | High | Contract contradiction | `App/Src/sensor_task.c:77-85`, `Documentation/SPI_SERVICE_CONTRACT.md:15,70-77` | `SensorTask` drives `DATA_READY` low directly, but SPI service contract states `SpiSlaveService` is the sole production owner and `SensorTask` must not drive the pin | Localized but safety-relevant |
| ASH-AUD-002 | High | Logic inconsistency | `App/Src/sensor_task.c:88-99` | successful sensor bring-up transitions to `ACTIVE/PASS`, then immediately marks the latest sensor record invalid with `SENSOR_VALIDITY_COMMUNICATION_ERROR`; this can poison first-use snapshot semantics and diagnostics | Localized |
| ASH-AUD-003 | High | Contract contradiction | `App/Src/i2c_manager.c:348-353,370-375,394-399,415-419`, `Documentation/I2C_MANAGER_CONTRACT.md:38-40` | ISR callbacks invoke user completion callbacks directly even though the contract requires potentially blocking user-callback behavior to be deferred to task context | Repo-visible integration contract issue |
| ASH-AUD-004 | Medium | Contract contradiction | `App/Src/i2c_manager.c:37-40,63-65`, `App/Inc/i2c_manager.h:34-39`, `Documentation/I2C_MANAGER_CONTRACT.md:62-65` | I2C diagnostics/events timestamp with raw 32-bit TIM2 values, while the contract requires shared 64-bit monotonic timestamps and forbids exposing the raw counter as system time | Repo-visible diagnostics issue |
| ASH-AUD-005 | Medium | Observability inconsistency | `App/Src/sensor_task.c:77-85` vs `41-45,66-67,93-99,174-176,192-194,205-207,218-220,236-237` | one bring-up failure path returns without refreshing debug mirrors, leaving `g_sensor_task_snapshot_dbg` and `g_sensor_task_diag_word_dbg` stale | Localized |
| ASH-AUD-006 | Medium | Coverage smell | `tests/host/CMakeLists.txt:1-23` vs `CMakeLists.txt:61-81` | lifecycle, transport orchestration, hardware-facing services, and health monitor are absent from automated host coverage | Repo-wide |

## Section E — Loose Ends / Technical Debt Ledger

| Source | Affected functionality | Current state | Test state | Release risk |
| --- | --- | --- | --- | --- |
| `Documentation/CONTRACT_STATUS.md:13-25` | SPI/CAN/snapshot/time-sync integration | multiple rows still marked host-tested only, scaffold, absent, or gated | host primitives tested; end-to-end target flows absent | High |
| `Documentation/HEALTH_MONITOR_CONTRACT.md:22-51` | aggregate health model | contract defines required observations, but implementation is empty (`App/Src/health_monitor.c:1-9`) | none | High |
| `Documentation/TIMESTAMP_SYNC_CONTRACT.md:28-59` | `TIME_SYNC` acceptance and stale-sync gating | sync state exists, but no live SPI dispatch path calls `TimeService_AcceptSync()` | unit-level host coverage only | High |
| `Documentation/I2C_MANAGER_CONTRACT.md:56-69` | mux selection + sensor transaction atomicity | contract requires one logical ownership window; current API still uses separate select/read operations | no dedicated contention or sequencing tests | High |
| `Documentation/CAN_SERVICE_CONTRACT.md:44-46,78-89,125-133` | duplicate CAN IDs, RX overflow, command ordering, hardware recovery proof | documented as open decisions or future validation | host-only queue/policy tests | High |
| `Documentation/SPI_SERVICE_CONTRACT.md:78-135` | DMA/NSS callbacks and aborted transaction handling | contract exists; runtime wiring absent | none beyond host protocol state tests | High |

## Section F — Coverage Gap Matrix

### Host-tested modules (`gcov -b -c`)

| Module | Current test vehicle | Line coverage | Branch coverage | Gap |
| --- | --- | ---: | ---: | --- |
| `time_service.c` | `sprint1_protocol_tests` | 71.67% | 90.70% | global/runtime wrappers not covered; no live `TIME_SYNC` ingress caller |
| `calibration_record.c` | `sprint1_protocol_tests` | 75.00% | 96.55% | additional invalid-record permutations missing |
| `joint_mapping.c` | `sprint1_protocol_tests` | 81.58% | 95.45% | negative-path permutations incomplete |
| `sensor_latest_value.c` | `sprint1_protocol_tests` | 80.00% | 66.67% | stale/freshness edge branches under-covered |
| `motor_latest_value.c` | `sprint1_protocol_tests` | 94.00% | 100.00% | remaining branch-taken paths are narrow |
| `snapshot_builder.c` | `sprint1_protocol_tests` | 78.26% | 96.15% | no-buffer and replacement combinations only partially exercised |
| `crc32_iso_hdlc.c` | `sprint1_protocol_tests` | 88.89% | 100.00% | minor branch residue |
| `spi_protocol.c` | `sprint1_protocol_tests` | 97.67% | 92.00% | some invalid-message combinations absent |
| `spi_data_ready.c` | `sprint1_protocol_tests` | 100.00% | 100.00% | clear |
| `can_tx_policy.c` | `sprint1_protocol_tests` | 100.00% | 100.00% | clear |

### Dark-matter production modules (compiled into firmware, absent from host tests)

| Module | Current test vehicle | Status |
| --- | --- | --- |
| `app_init.c` | none | startup/activation gating untested |
| `lifecycle.c` | none | core state machine untested despite central role |
| `i2c_manager.c` | none | blocking + async transport behavior untested |
| `tca9548a_mux.c` | none | mux retry/selection behavior untested |
| `as5600.c` | none | register read/error handling untested |
| `sensor_task.c` | none | bring-up and sampling state machine untested |
| `can_service.c` | none | decode, poll scheduling, queue drain, recovery wiring untested |
| `spi_slave_service.c` | none | service-level staging and GPIO ownership untested |
| `health_monitor.c` | none | no implementation to cover |

## Section G — Critical Defect Punch-List

| Priority | Issue | Evidence | Owner | Phase 2 status |
| --- | --- | --- | --- | --- |
| P0 | Remove `SensorTask` ownership of `DATA_READY` | `App/Src/sensor_task.c:84` contradicts `Documentation/SPI_SERVICE_CONTRACT.md:15,70-77` | Firmware application | Blocking |
| P0 | Correct first valid sensor-cache semantics after bring-up | `App/Src/sensor_task.c:88-99` marks latest value as communication error after successful initialization | Firmware application | Blocking |
| P0 | Make I2C async callback model contract-safe | `App/Src/i2c_manager.c:348-419` directly invokes user callbacks from ISR | Firmware application | Blocking |
| P1 | Convert I2C event timestamps to shared 64-bit time or narrow the contract | `App/Src/i2c_manager.c:37-40,63-65` vs `Documentation/I2C_MANAGER_CONTRACT.md:62-65` | Firmware application | Blocking |
| P1 | Add automated coverage for `lifecycle`, `sensor_task`, `i2c_manager`, `can_service`, `spi_slave_service` | production modules missing from `tests/host/CMakeLists.txt` | Firmware + verification | Blocking |
| P1 | Resolve `TEMP/MksServo` duplicate-tree status | active docs point to both the live library and the source attachment | Build/documentation owners | Blocking |
| P2 | Replace empty health monitor scaffold with contract-backed snapshot/aggregation | `App/Src/health_monitor.c:1-9`, `Documentation/HEALTH_MONITOR_CONTRACT.md:22-51` | Firmware application | Blocking |
| P2 | Re-establish target build evidence in CI/runner | `cmake --preset Debug` fails without `arm-none-eabi-gcc/g++` | Build/CI | Blocking |

## Section H — Clearance Decision

**Decision:** `Blocked`

### Gate reasons

- contract/implementation contradiction on `DATA_READY` ownership
- contract/implementation contradiction on I2C callback execution model
- incorrect first-use sensor-cache invalidation during successful bring-up
- large production dark-matter surface with no automated coverage
- empty health aggregation implementation despite project-wide dependency claims
- target-build evidence unavailable in current runner due missing embedded toolchain
