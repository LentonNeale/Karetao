# SPI Time-Sync Characterisation Plan (Haiku 4.5 agent)

## Context

- **Goal:** measure Pi 5 ↔ STM32F405RGT6 time synchronisation over SPI: Pi timestamps, STM32 timestamps, request/response and transport delay, reconstructed clock offset, offset stability/drift, and sync error bound. Instrumentation and measurement only; the TIME_SYNC protocol, frame layout and validation bounds are not changed.
- **Authoritative contract (Karetao):** `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` (offset = `pi_time_us − t_stm32`, captured in task context; validity 5 s; initial bound ±24 h, runtime step ±1 s; strictly newer `sync_seq`), `SPI_SYSTEM_INTERFACE.md` §4 pipelined transactions, §7 armed-then-assert DATA_READY, §11 TIME_SYNC, `SPI_PAYLOAD_SCHEMA.md` TIME_SYNC payload `<BBHQI>` = schema 1, reserved, flags, pi_time_us, sync_seq (16 bytes). Targets: SYS-SYNC-001 ±1 ms, SYS-SYNC-002 1 Hz nominal / 10 Hz max, SYS-TIM-003 5 MHz ceiling, SYS-SPI-004 20–30 cm cable (record length used).
- **Devices:** Pi 5, Ubuntu 24.04, SPI0 CE0 `/dev/spidev0.0`, Mode 0, 512-byte fixed transfers, libgpiod v1, DATA_READY on GPIO25 (`pinctrl-rp1` chip, header pin 22) wired to STM32 PA8. STM32: SPI3 slave + DMA, TIM2 32-bit 1 MHz free-running local clock (prescaler 83 at 84 MHz), services run in `StartDefaultTask` with `osDelay(1)`.
- **Pipelining consequence used for measurement:** the ACK to TIME_SYNC request N is clocked out during transaction N+1. STM32 captures `t_stm32` between DMA completion of N and the start of N+1, so the true offset error lies in the window `[T_end(N) − pi_time_us, T_start(N+1) − pi_time_us]` (Pi clock). ACK `frame_time_us` is `TimeService_NowUs()` taken in `SpiProtocol_BuildFrame` microseconds before `TimeService_AcceptSync`, so `offset_est = pi_time_us − ACK.frame_time_us` approximates the stored offset.
- **Confirmed implementation gaps (record, do not fix):** (1) `frame_time_us` is raw local TIM2 time, not hub time (`SpiProtocol_BuildFrame`, spi_protocol.c:33); (2) sensor `measurement_timestamp_us` is raw local time with only the quality flag set, offset never applied (`SensorTask_ProcessChannel`, sensor_task.c:165-173); (3) GET_STATUS returns ACK, the DIAGNOSTIC (0x03) payload with `time_sync_valid` is not implemented (`SpiProtocol_ProcessRequest`, spi_protocol.c:178; `SPI_MESSAGE_STATUS` boot frame has empty payload); (4) accepted `time_offset_us` is not carried by any v1 payload; (5) the Pi has no TIME_SYNC encoder or sender.

## Files

| Path | Purpose | Read/Write |
|---|---|---|
| `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` | Time model, TIME_SYNC, validity/rejection rules | Read |
| `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | Transaction model, DATA_READY, framing, §16 gates | Read |
| `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` | TIME_SYNC / ACK / NACK / VERSION payload layouts | Read |
| `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` | SYS-SYNC-001..005, SYS-SPI-003/004, SYS-TIM-003 | Read |
| `Documentation/01_SYSTEM/SYSTEM_TIMING.md` | Timing constraints summary | Read |
| `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` | SD-17..SD-22 detail (lines 233–290); open gates §3.2 (lines 581–626) | Read/Write |
| `Documentation/05_VERIFICATION/CAN_INTEGRATION_EVIDENCE.md` | Convention template for an evidence document | Read |
| `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md` | New evidence document (audit, method, results, verdicts) | Write (new) |
| `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` | Timing/synchronization row (status stays OPEN) | Read/Write |
| `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md` | STM32 pin baseline (SPI3, PA8) | Read |
| `Arm_Sensor_Hub/App/Src/time_service.c` | `TimeService_SyncStateAccept`, `TimeService_AcceptSync`, `TimeService_NowUs`, `TimeService_ReadTim2` | Read/Write |
| `Arm_Sensor_Hub/App/Inc/time_service.h` | Sync types, default bounds (`TIME_SERVICE_DEFAULT_*`) | Read/Write |
| `Arm_Sensor_Hub/App/Src/spi_slave_service.c` | `SpiSlaveService_Process`, `SpiSlaveService_ProcessRequestFrame`, `SpiSlaveService_PublishStagedFrame`, `HAL_SPI_TxRxCpltCallback` | Read/Write |
| `Arm_Sensor_Hub/App/Inc/spi_slave_service.h` | Service API | Read/Write |
| `Arm_Sensor_Hub/App/Src/spi_protocol.c` | `SpiProtocol_BuildFrame`, `SpiProtocol_ParseTimeSyncRequest`, `SpiProtocol_ProcessRequest` | Read |
| `Arm_Sensor_Hub/App/Inc/spi_protocol.h` | `SpiProtocol_Result`, `SPI_TIME_SYNC_PAYLOAD_BYTES`, message IDs | Read |
| `Arm_Sensor_Hub/App/Inc/spi_payload_layout.h` | Frame offsets (`SPI_FRAME_OFFSET_TIME_US` = 10) | Read |
| `Arm_Sensor_Hub/App/Src/sensor_task.c` | `SensorTask_ProcessChannel` timestamp path; `SensorTask_UpdateDebugMirrors` mirror convention | Read |
| `Arm_Sensor_Hub/App/Src/app_init.c` | `g_app_*_dbg` volatile debug-mirror naming convention | Read |
| `Arm_Sensor_Hub/Core/Src/main.c` | `MX_TIM2_Init` (lines 338–372), `StartDefaultTask` loop (lines 441–456), `htim2` | Read |
| `Arm_Sensor_Hub/tests/host/protocol_test_main.c` | TIME_SYNC request test vector builder (lines 650–672) | Read/Write |
| `Arm_Sensor_Hub/tests/host/service_test_main.c` | TimeService stubs (lines 156–196), TIME_SYNC acceptance test (lines 870–892) | Read/Write |
| `Arm_Sensor_Hub/tests/host/CMakeLists.txt` | Targets `sprint1_protocol_tests`, `service_smoke_tests` | Read |
| `Arm_Sensor_Hub/Documentation/development.md` | Build/test commands (`cmake --preset HostTests`, `ctest --preset HostTests`, `cmake --preset Debug`) | Read |
| `Arm_Sensor_Hub/Documentation/README.md` | Component doc index / authority declaration | Read/Write |
| `Arm_Sensor_Hub/Documentation/TIME_SYNC_INSTRUMENTATION.md` | New component doc: debug mirrors, SWD readout | Write (new) |
| `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py` | `SpiFrame`, `MessageType`, `NackReason`, `VersionInfo`, `initial_sequence` | Read/Write |
| `RaspberryPi_Sensor_Hub/src/spi/spi_device.py` | `SpiDevice.get_version`, `DEFAULT_RETRY_DELAY_S` | Read |
| `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py` | `SpiBus`, `SpiBusConfig`, `SpiBackend` protocol | Read |
| `RaspberryPi_Sensor_Hub/src/spi/data_ready.py` | `DataReadyWatcher`, `DataReadyLike`, `DEFAULT_DATA_READY_LINE` | Read |
| `RaspberryPi_Sensor_Hub/src/spi/timing.py` | `TimingSession`, `now_ns`, `correlated_request_seq`, `nack_codes`, `summarise`, `percentiles`, `CSV_FIELDS` pattern | Read |
| `RaspberryPi_Sensor_Hub/src/spi/time_sync_session.py` | New: TIME_SYNC session records, offset/window math, analysis | Write (new) |
| `RaspberryPi_Sensor_Hub/src/spi/__init__.py` | Package exports | Read/Write |
| `RaspberryPi_Sensor_Hub/tools/spi_timing_harness.py` | `collect_metadata`, `PipelinedFakeBackend`, `sample_environment`, `_git_describe`, output conventions | Read |
| `RaspberryPi_Sensor_Hub/tools/spi_link_probe.py` | Link classification tool (run before measurements) | Read |
| `RaspberryPi_Sensor_Hub/tools/time_sync_probe.py` | New CLI: periodic TIME_SYNC characterisation run | Write (new) |
| `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py` | Protocol unit tests | Read/Write |
| `RaspberryPi_Sensor_Hub/tests/spi/test_timing.py` | `PipelinedBackend`, `FakeDataReady` fake patterns | Read |
| `RaspberryPi_Sensor_Hub/tests/spi/test_time_sync_session.py` | New unit tests | Write (new) |
| `RaspberryPi_Sensor_Hub/Documentation/README.md` | Component doc: pin map, harness usage, evidence admissibility | Read/Write |
| `RaspberryPi_Sensor_Hub/Documentation/RASPBERRY_PI_BRINGUP_V1.md` | Part C time authority (line 603), Part E GPIO25/libgpiod (lines 685–731) | Read |
| `.github/workflows/raspberry-ci.yml` | Pi test command: `python -m unittest discover -s RaspberryPi_Sensor_Hub/tests/spi -p 'test_*.py' -v` | Read |

## Docs

| Code area | Doc path | Update trigger |
|---|---|---|
| `Arm_Sensor_Hub/App/Src/time_service.c`, `spi_slave_service.c` debug mirrors | `Arm_Sensor_Hub/Documentation/TIME_SYNC_INSTRUMENTATION.md` | Any new/changed mirror symbol or readout procedure |
| `Arm_Sensor_Hub/Documentation/` index | `Arm_Sensor_Hub/Documentation/README.md` | New component doc added |
| `RaspberryPi_Sensor_Hub/src/spi/*.py`, `tools/time_sync_probe.py` | `RaspberryPi_Sensor_Hub/Documentation/README.md` | New tool, CLI flag, CSV column, or metadata key |
| Measurement results, audit table, contract comparison | `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md` | Every run set; every verdict |
| Contract-vs-implementation conflicts, open decisions | `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` §3.2 | New conflict or blocker discovered |
| Evidence linkage | `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` | Evidence document created; status remains OPEN |

## Blockers

1. **Requested document names do not exist in this repo.** `SPI_CONTRACT(2).md`, `CONTRACT_V1_FREEZE(2).md`, `SPI_SERVICE_CONTRACT.md`, `TIMESTAMP_SYNC_CONTRACT.md`, `PI-03_RASPBERRY_PI_DATA_READY.md` are absent. Non-"(2)" legacy copies exist only in the sibling repo `/home/lenton/Git_repos/STM32_Sensor_Hub/Arm_Sensor_Hub/Documentation/` (non-authoritative per `DOCUMENTATION_AUTHORITY_MODEL.md`); `CONTRACT_V1_FREEZE.md` is archived at `Documentation/99_ARCHIVE/SUPERSEDED/`. The "(2)" versions and PI-03 were not found anywhere. Use the Karetao files in the Files table; cite legacy names only as provenance.
2. **STM32 accepted offset is not observable over SPI** (gap 4). Pi-side offset is a reconstruction; the exact stored value is readable only via SWD debug mirrors (Task 2). Exposing it on the wire is a schema decision, out of scope.
3. **Exported timestamps are not hub time** (gaps 1–2), so end-to-end "timestamp error ≤ ±1 ms" of exported records cannot be assessed; only offset stability, drift, and transport-window uncertainty can. Record as conflict, do not fix.
4. **DATA_READY GPIO25 is a harness assignment, not validated** (SD-17 open; `SPI_SYSTEM_INTERFACE.md` §16 acceptance outstanding). DATA_READY-paced results are bench aids, not gate evidence.
5. **Pi clock source for `pi_time_us` is unspecified by contract.** Probe must record which clock was used; default to `CLOCK_REALTIME` (chrony is time authority, BRINGUP Part C) and log `CLOCK_MONOTONIC_RAW` alongside. Flag for confirmation.
6. **Bench tooling unconfirmed:** ST-Link + `arm-none-eabi-gdb` availability for mirror readout; `python3-spidev`, `python3-libgpiod` installed on the Pi; firmware must report `dirty_build: false` for admissible evidence.
7. **STM32 request processing runs in `StartDefaultTask` with `osDelay(1)`**, so `t_stm32` capture lags DMA completion by ≥1 tick. This is inherent one-way uncertainty; measure it, do not tune the loop.

## Tasks

### 1. Contract/implementation audit
- **Goal:** produce the audit table proving each TIME_SYNC/SPI-timing contract clause against code, with file:function evidence and gap classification.
- **Files:** `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`, `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`, `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md`, `Arm_Sensor_Hub/App/Src/time_service.c`, `Arm_Sensor_Hub/App/Src/spi_protocol.c`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c`, `Arm_Sensor_Hub/App/Src/sensor_task.c`, `Arm_Sensor_Hub/Core/Src/main.c`, `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py`, `RaspberryPi_Sensor_Hub/src/spi/spi_device.py`, `Documentation/05_VERIFICATION/CAN_INTEGRATION_EVIDENCE.md`
- **Docs:** `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md` (create, §"Audit"), `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` §3.2
- **Acceptance:** table rows: clause, status (IMPLEMENTED / GAP / CONFLICT), file:function:line. Gaps 1–5 from Context appear as register checklist items. No code changed.

### 2. STM32 TimeService debug mirror
- **Goal:** mirror every `TimeService_SyncStateAccept` call for SWD readout.
- **Files:** `Arm_Sensor_Hub/App/Inc/time_service.h`, `Arm_Sensor_Hub/App/Src/time_service.c`, `Arm_Sensor_Hub/App/Src/app_init.c` (naming convention), `Arm_Sensor_Hub/tests/host/protocol_test_main.c`, `Arm_Sensor_Hub/Documentation/development.md`
- **Docs:** `Arm_Sensor_Hub/Documentation/TIME_SYNC_INSTRUMENTATION.md` (create)
- **Acceptance:** `volatile TimeService_SyncDebugMirror g_time_sync_dbg` {pi_time_us, local_capture_us, candidate_offset_us, result, accept_count, reject_count} updated inside `TimeService_SyncStateAccept`; host test asserts fields after accept and after each rejection type; `ctest --preset HostTests` passes; `cmake --build --preset Debug` passes.

### 3. STM32 SPI transaction timing mirror
- **Goal:** timestamp DMA-complete, request-processing start, response staged, DATA_READY set for the last transaction.
- **Files:** `Arm_Sensor_Hub/App/Inc/time_service.h`, `Arm_Sensor_Hub/App/Src/time_service.c`, `Arm_Sensor_Hub/App/Inc/spi_slave_service.h`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c`, `Arm_Sensor_Hub/tests/host/service_test_main.c`
- **Docs:** `Arm_Sensor_Hub/Documentation/TIME_SYNC_INSTRUMENTATION.md`
- **Acceptance:** new `uint32_t TimeService_RawCounter(void)` (returns `__HAL_TIM_GET_COUNTER(&htim2)`, stubbed in service_test_main.c); `volatile SpiSlaveService_TimingMirror g_spi_timing_dbg` {dma_complete_raw (ISR, raw counter only, never `TimeService_NowUs`), process_start_us, response_staged_us, data_ready_set_us, request_type, request_seq}; `service_smoke_tests` asserts ordering; Debug build passes.

### 4. Pi TIME_SYNC payload encoder
- **Goal:** encode TIME_SYNC per schema and decode ACK/NACK status for it.
- **Files:** `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py`, `RaspberryPi_Sensor_Hub/src/spi/__init__.py`, `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py`, `Arm_Sensor_Hub/tests/host/protocol_test_main.c` (byte-layout cross-check)
- **Docs:** `RaspberryPi_Sensor_Hub/Documentation/README.md`
- **Acceptance:** `TIME_SYNC_PAYLOAD_BYTES = 16`, `encode_time_sync_payload(pi_time_us, sync_seq, flags=0)` → `struct '<BBHQI'`; `decode_command_reply(payload)` → (request_type, status_code, request_seq, detail_code) using `NackReason`; tests confirm offsets 0/1/2/4/12 and reject >uint64/uint32; unittest discover passes.

### 5. Pi TIME_SYNC session and offset math
- **Goal:** clock periodic TIME_SYNC transactions, capture Pi/STM32 timestamps, correlate ACKs, compute offset estimate and uncertainty window.
- **Files:** `RaspberryPi_Sensor_Hub/src/spi/time_sync_session.py`, `RaspberryPi_Sensor_Hub/src/spi/timing.py`, `RaspberryPi_Sensor_Hub/src/spi/data_ready.py`, `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py`, `RaspberryPi_Sensor_Hub/tests/spi/test_time_sync_session.py`, `RaspberryPi_Sensor_Hub/tests/spi/test_timing.py`
- **Docs:** `RaspberryPi_Sensor_Hub/Documentation/README.md`
- **Acceptance:** `TimeSyncSession(bus, data_ready=None, pi_clock=...)` records per request: `pi_time_us`, `t_start_ns`/`t_end_ns` (realtime and monotonic_raw), `request_seq`, `sync_seq`, `data_ready_wait_ns`; on correlated ACK/NACK fills `response_frame_time_us`, `status`, `detail`, `offset_est_us = pi_time_us − response_frame_time_us`, `window_lo_us`, `window_hi_us` (Context bound). Fake-backend test verifies all fields.

### 6. Logging format and drift analysis
- **Goal:** fix the CSV/metadata schema and compute drift, residual, validity and step-bound statistics.
- **Files:** `RaspberryPi_Sensor_Hub/src/spi/time_sync_session.py`, `RaspberryPi_Sensor_Hub/src/spi/timing.py`, `RaspberryPi_Sensor_Hub/tests/spi/test_time_sync_session.py`
- **Docs:** `RaspberryPi_Sensor_Hub/Documentation/README.md`
- **Acceptance:** `TIME_SYNC_CSV_FIELDS` constant; `analyse(records)` returns drift_ppm (least-squares of offset_est vs pi time), residual `summarise`, window-width `summarise`, nack_count by `NackReason`, gaps > 5 000 000 µs count, steps > 1 000 000 µs count. Synthetic test recovers injected drift within 1 ppm and counts injected NACK/gaps.

### 7. Probe CLI
- **Goal:** command-line runner writing per-sync CSV and metadata with firmware identity.
- **Files:** `RaspberryPi_Sensor_Hub/tools/time_sync_probe.py`, `RaspberryPi_Sensor_Hub/tools/spi_timing_harness.py` (reuse `collect_metadata`, `sample_environment`, `_git_describe`, `PipelinedFakeBackend` pattern), `RaspberryPi_Sensor_Hub/src/spi/time_sync_session.py`, `RaspberryPi_Sensor_Hub/src/spi/data_ready.py`
- **Docs:** `RaspberryPi_Sensor_Hub/Documentation/README.md`
- **Acceptance:** flags `--rate-hz` (1–10), `--duration-s`, `--speed-hz`, `--pi-clock {realtime,monotonic_raw}`, `--data-ready`, `--data-ready-line`, `--cable-cm`, `--outdir`, `--fake`; writes `<run_id>_time_sync.csv`, `<run_id>_metadata.json` (firmware VersionInfo, dirty warning, pi_clock, cable_cm, analysis); `--fake` run exits 0 and files validate against Task 6 fields.

### 8. SPI/DATA_READY latency measurement
- **Goal:** quantify DATA_READY assert-to-service latency and STM32 DMA-complete→process→DATA_READY intervals under polling and DATA_READY pacing.
- **Files:** `RaspberryPi_Sensor_Hub/tools/time_sync_probe.py`, `RaspberryPi_Sensor_Hub/tools/spi_link_probe.py`, `Arm_Sensor_Hub/Documentation/TIME_SYNC_INSTRUMENTATION.md`
- **Docs:** `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md` §"DATA_READY latency"
- **Acceptance:** link probe passes first; probe run with and without `--data-ready` at 1 MHz and 5 MHz; `data_ready_wait_ns` summaries and ≥10 SWD samples of `g_spi_timing_dbg` intervals tabulated; results labelled "harness GPIO, unvalidated (SD-17)".

### 9. Test execution and repeatability
- **Goal:** collect the characterisation dataset.
- **Files:** `RaspberryPi_Sensor_Hub/tools/time_sync_probe.py`, `RaspberryPi_Sensor_Hub/Documentation/RASPBERRY_PI_BRINGUP_V1.md`
- **Docs:** `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md` §"Runs"
- **Acceptance:** matrix 3 repeats × rate {1, 10} Hz × pacing {polling, data-ready}, ≥300 s each, plus one ≥30 min 1 Hz run; every metadata has `dirty_build: false`, `cable_cm` within 20–30, `pi_clock` recorded; run-to-run drift_ppm spread reported.

### 10. Validation against contracts
- **Goal:** compare measurements to contract values and state verdicts with uncertainty.
- **Files:** `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`, `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`, `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md`
- **Docs:** `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md` §"Verdicts"
- **Acceptance:** per item PASS / FAIL / INCONCLUSIVE with numbers: drift over 1 s and 5 s vs ±1 ms (SD-19); transport window width vs ±1 ms (SD-18); rejection behaviour observed for step > 1 s and stale `sync_seq` (SD-21); validity expiry at 5 s (SD-19/22). Blocker 3 items marked INCONCLUSIVE, not PASS.

### 11. Documentation closure
- **Goal:** cross-link evidence, component docs and register without changing verification status.
- **Files:** `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`, `Arm_Sensor_Hub/Documentation/README.md`, `RaspberryPi_Sensor_Hub/Documentation/README.md`, `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md`
- **Docs:** all four listed
- **Acceptance:** matrix Timing/synchronization row links the evidence document, status still OPEN; both component READMEs list the new docs/tools; register §3.2 has one checklist item per Blocker 1–5; all relative links resolve; `ctest --preset HostTests` and Pi unittest discover pass on final tree.
