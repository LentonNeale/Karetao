⚠ **ARCHIVED — Non-normative historical document**

- **Archived:** 2026-09-20
- **Historical status:** Sprint planning and completion reports, obsolete
- **Superseded by:** Current project state in `Documentation/` and `07_DECISIONS/`

---

# Sprint 1 Agent Task List

**Source of truth:** `Documentation/Conversations/CTO_DECISION_FINAL.md`

**Sprint goal:** Convert the approved v1.0 firmware decisions into verified contract updates and small, testable STM32 implementation increments. Keep hardware-dependent decisions explicit. Do not authorize energized motion from firmware changes alone.

## How To Use This File

- Give one task prompt to one agent at a time.
- An agent must change only the files named by its task unless a dependency requires a small adjacent change.
- Every task must finish with its listed validation command or an explicit blocker report.
- Agents must preserve existing user changes and avoid unrelated refactors.
- An agent must update the relevant contract and `Documentation/CONTRACT_STATUS.md` when behavior or ownership changes.
- Do not silently convert the existing millidegree wire field to radians. That requires a schema version.
- Do not claim PL/SIL compliance. Firmware response levels are not a formal machine safety rating.
- Do not enable automatic motion after reset, recovery, synchronization loss, or service reactivation.

## Shared Agent Prompt Prefix

Copy this prefix before any task prompt:

> You are working in the STM32 Sensor Hub repository. Read the named contract and nearby implementation before editing. Make the smallest focused change that satisfies the task. Preserve unrelated work. Use the existing C11, FreeRTOS, CMake, and service patterns. Add focused tests or host-testable helpers where the task requests them. Run the specified validation command. Report changed files, behavior, validation result, and unresolved assumptions. Do not claim hardware validation when only a build or host test was run.

## Dependency Order

```text
01 documentation reconciliation
02 build baseline and validation helpers
03 lifecycle startup alignment
04 fault vocabulary and health event model
05 shared monotonic time service
06 time synchronization runtime
07 calibration record model
08 joint/motor mapping validation
09 sensor latest-value records
10 motor latest-value records
11 snapshot size and serialization model
12 snapshot buffer ownership
13 CRC and frame validation
14 SPI service transaction state machine
15 DATA_READY and polling integration
16 CAN physical/timing evidence
17 CAN TX ownership and bounded recovery
18 command gating and time-sync inhibition
19 independent safety release checklist
20 sprint integration and regression audit
```

Tasks 01-15 may proceed in order. Tasks 16-18 require the earlier data/lifecycle contracts and must not be treated as approval of the physical CAN or safety design. Task 19 is a release evidence task, not a substitute for independent safety engineering.

---

## Task 01 - Reconcile CTO Decisions Into Contract Status

**Copyable prompt:**

> Read `Documentation/Conversations/CTO_DECISION_FINAL.md`, `Documentation/CONTRACT_V1_FREEZE.md`, and `Documentation/CONTRACT_STATUS.md`. Update the affected contract documents so the approved CTO decisions are reflected consistently. At minimum reconcile the 100 Hz baseline, 512-byte SPI frame, 490-byte payload, CRC-32/ISO-HDLC, 5-second time-sync timeout, time-dependent motion inhibition after sync loss, explicit inactive recovery, and the distinction between firmware response levels and formal PL/SIL ratings. Keep CAN bitrate, maximum SPI clock, exact motor controller behavior, and independent safety validation marked as integration/release gates. Do not change implementation code. Run a targeted link/text consistency check and report every remaining gate.

**Files:** `Documentation/CONTRACT_V1_FREEZE.md`, `Documentation/CONTRACT_STATUS.md`, affected contract files only.

**Done when:** No contract contradicts the final CTO decision; unresolved hardware gates remain explicit; status entries identify the next action.

**Validation:** Search for stale wording such as `5 MHz approved`, `PL/SIL mapping`, `continue motion after sync loss`, and `256-byte frame`.

**Handoff:** List the authoritative rule and the implementation task that consumes it.

```text 
Output: Updated the contract set: CONTRACT_V1_FREEZE.md, CONTRACT_STATUS.md, TIMESTAMP_SYNC_CONTRACT.md, LIFECYCLE_CONTRACT.md, and ERROR_HANDLING_STRATEGY.md. No implementation code changed.

The authoritative source remains CTO_DECISION_FINAL.md. Handoff rules and consuming tasks:

100 Hz baseline: Tasks 09, 11, 14.
512-byte frame, 490-byte payload, CRC-32/ISO-HDLC: Tasks 11, 13, 14.
Five-second sync expiry and time-dependent motion inhibition: Tasks 05, 06, 18.
Recovery returns to INACTIVE; explicit activation required: Tasks 03, 17, 18.
Firmware response levels are not PL/SIL ratings: Task 04 and Task 19.
Remaining integration/release gates are explicit with next actions: CAN bitrate/physical layer/TX-retry policy, maximum SPI clock acceptance, exact motor-controller commissioning, and independent safety validation plus machine risk assessment.

Validation passed: no stale instances of 5 MHz approved, PL/SIL mapping, continue motion after sync loss, or 256-byte frame; the reviewed contract rules have no CTO-decision contradictions; all checked relative Markdown links resolve.
```



## Task 02 - Establish a Repeatable Build and Host-Test Baseline

**Copyable prompt:**

> Inspect the existing CMake presets and build contract. Add only the smallest host-test or validation structure needed for Sprint 1 protocol tests without disrupting the STM32 target. Confirm that Debug and Release configuration/build commands are documented and reproducible. Do not add CI or broad warning-policy changes. Run the Debug build and, if the existing project supports it, the Release build. Report the exact commands and any pre-existing failures.

**Files:** `CMakeLists.txt`, `CMakePresets.json`, `Documentation/BUILD_CONTRACT.md`, and narrowly scoped test configuration if required.

**Done when:** The firmware build remains green and a repeatable location exists for CRC, serialization, and time-service host tests.

**Validation:** `cmake --preset Debug && cmake --build --preset Debug`; run the narrow host test command if added.

**Handoff:** Record test executable names and how later agents should run one focused test.

```text
Output: Added an opt-in native CTest baseline without changing the STM32 target:

CMakeLists.txt: ARM_SENSOR_HUB_BUILD_HOST_TESTS builds only host tests.
CMakePresets.json: added HostTests configure, build, and test presets.
CMakeLists.txt and protocol_test_main.c: added sprint1_protocol_tests.
BUILD_CONTRACT.md: documented reproducible Debug, Release, and focused host-test commands.
Validation passed:

```


## Task 03 - Align Lifecycle Startup and Recovery Ordering

**Copyable prompt:**

> Read `Documentation/LIFECYCLE_CONTRACT.md` and inspect `Core/Src/main.c`, `Core/Src/freertos.c`, and application service initialization. Align source ordering with the fixed sequence: HAL hardware initialization, RTOS kernel initialization, static object creation and service configuration to INACTIVE, task creation, then dependency-ordered activation from task/system context. Ensure reset and recovery end in INACTIVE and cannot automatically resume motor motion. Preserve CubeMX-generated boundaries. Make no changes to peripheral protocol behavior. Build Debug and report any service that still violates the sequence.

**Files:** `Core/Src/main.c`, `Core/Src/freertos.c`, lifecycle files, and `Documentation/LIFECYCLE_CONTRACT.md` only as needed.

**Done when:** Startup and recovery behavior is explicit in code and contract, with no activation from an unsafe context.

**Validation:** Debug build; inspect lifecycle transition logs/status paths if available.

**Handoff:** Provide the activation order and remaining dependency blockers..


```text
Output: 
```

## Task 04 - Define Fault Levels, Events, and Health Escalation Inputs

**Copyable prompt:**

> Implement or document the smallest shared representation for `INFORMATIONAL`, `DEGRADED`, `FAULT`, and `SAFETY_CRITICAL` firmware response levels. Define event fields for detection, response, recovery owner, output inhibit behavior, and occurrence count. Do not map these levels to PL or SIL. Reuse existing health/lifecycle patterns rather than introducing a new framework. Keep HealthMonitor observational and keep recovery ownership with the System Manager. Add focused unit coverage if the representation is host-testable.

**Files:** `App/Inc/health_monitor.h`, `App/Src/health_monitor.c`, error/lifecycle files, and the corresponding contracts.

**Done when:** Services can report the four response levels without implying a formal safety rating, and persistent/uncertain faults can reach ERROR.

**Validation:** Narrow host test if available, then Debug build.

**Handoff:** Document how later CAN, SPI, time, and sensor tasks report faults.

```text
Output: Aligned lifecycle startup and status documentation.

App_Init() now runs after osKernelInitialize() and configures services to INACTIVE. App_Start() runs once from defaultTask after osKernelStart, activating dependencies in this order:

I2C Manager
CAN Service
SPI Slave Service
Sensor Service, only after I2C is ACTIVE
The one-shot start guard prevents recovery code from reusing boot activation. Existing lifecycle recovery already ends in INACTIVE; no motor-enable or motion command is called during startup.

Updated main.c, app_init.c, LIFECYCLE_CONTRACT.md, and CONTRACT_STATUS.md. freertos.c needed no change.

Validation passed:
cmake --preset Debug && cmake --build --preset Debug

No warnings or errors.

Remaining dependency blockers: configuration/calibration/time-sync/safety prerequisite validation before activation is Task 18 work; HealthMonitor still has no lifecycle record; CAN’s hardware setup occurs during configuration but normal TX remains lifecycle-gated; SensorTask’s temporary DATA_READY GPIO toggle remains for Task 15 to replace.
```

## Task 05 - Implement the Shared 64-bit Monotonic Time Service

**Copyable prompt:**

> Read the time model in `Documentation/CONTRACT_V1_FREEZE.md` and `Documentation/TIMESTAMP_SYNC_CONTRACT.md`. Implement a small shared time service around the 32-bit 1 MHz TIM2 counter that extends wraps to a 64-bit monotonic timestamp. Define initialization, wrap handling, concurrency assumptions, and behavior across reset. Do not add synchronization offset logic yet. Replace no call sites unless needed to prove the API. Add host-testable wrap and monotonicity tests using an injectable counter source if the project pattern allows it.

**Files:** new/nearby time-service files, `Core` timer setup only if required, and `Documentation/TIMESTAMP_SYNC_CONTRACT.md`.

**Done when:** The service produces monotonic microseconds across one or more TIM2 wraps and documents its execution-context assumptions.

**Validation:** Focused wrap/monotonicity test; Debug build.

**Handoff:** State the API later I2C, CAN, SPI, and diagnostics code must use.

```text
Output:Implemented the shared 64-bit monotonic TIM2 time service.

time_service.h exposes:


It extends a 32-bit, 1 MHz TIM2 counter by detecting counter rollover and adding 
2
32
2 
32
  microseconds per wrap. It is initialized from App_Init() and is now the sole owner that starts TIM2; i2c_manager.c no longer starts the timer.

The portable state API accepts an injected counter reader, with wrap and multi-wrap monotonicity coverage in protocol_test_main.c. TIMESTAMP_SYNC_CONTRACT.md now defines reset behavior and the single serialized task/system-context assumption. No synchronization offsets or existing timestamp call sites were changed.

Validation passed:


The host test passed 1/1; Debug linked with no relevant warnings/errors. The initial host build exposed a main.h dependency in the portable source; this was corrected by excluding the STM32 binding under the host-test compile definition.

Handoff: later I2C, CAN, SPI, and diagnostics code must call TimeService_NowUs() for long-lived timestamps. Task 06 owns adding TIME_SYNC offset, validity, and expiry state; Task 09 owns migrating AS5600’s existing raw 32-bit timestamps.

```

## Task 06 - Add Runtime TIME_SYNC State and Validity Rules

**Copyable prompt:**

> Implement the STM32 runtime state for Pi-owned time synchronization: signed offset, sync sequence, last accepted local timestamp, validity, age, and quality. Accept an initial update within a configurable wide bound. After initialization, reject offset changes outside the configured narrow bound, initially +/-1 second. Invalidate after 5 seconds without an accepted update, retain the last accepted offset for diagnostics, and mark new records unsynchronized. Clear validity and volatile offset on reset. Do not implement slew correction or two-way RTT estimation. Add focused tests for initial acceptance, later rejection, timeout, reset, and recovery.

**Files:** timestamp service files, SPI command handling only if already available, `Documentation/TIMESTAMP_SYNC_CONTRACT.md`.

**Done when:** The state machine exactly matches SD-19 through SD-22 and has deterministic tests.

**Validation:** Focused time-sync tests; Debug build.

**Handoff:** Describe the API for command gating and record timestamp quality.

```text
Output:Implemented the Pi-owned runtime time-sync state in time_service.h and time_service.c, with no SPI changes because the SPI service has no request-dispatch path yet.

The state tracks signed offset, accepted sequence, last accepted local timestamp, validity, age, and synchronization quality. It:

accepts an initial offset within configurable bounds, defaulting to +/-24 hours;
accepts later updates only with a newer sequence and an offset step within +/-1 second;
invalidates at exactly 5 seconds, retaining the prior offset for diagnostics;
resets offset and validity to unsynchronized;
does not implement slew or RTT estimation.
Focused host tests were added to protocol_test_main.c for initial acceptance, later rejection, timeout, reset, recovery, and counter-wrap monotonicity. TIMESTAMP_SYNC_CONTRACT.md and CONTRACT_STATUS.md now reflect the implementation and remaining SPI dispatch work.

Validation passed:


1/1 host tests passed; Debug linked with no relevant warnings/errors.

Handoff API: SPI Task 14 should call TimeService_AcceptSync(pi_time_us, sync_sequence) after frame validation. Command gating uses TimeService_IsSyncValid(). Record builders and diagnostics use TimeService_GetSyncSnapshot() for validity, age, signed offset, accepted sequence, and SYNCHRONIZED/UNSYNCHRONIZED quality.

```

## Task 07 - Define Versioned Calibration Record Validation

**Copyable prompt:**

> Design and implement the data validation layer for versioned calibration records without committing to a flash-sector layout yet. Include schema version, sensor/joint identity, parameters, generation counter, CRC/validity information, and active version reporting. Reject malformed, incompatible, or CRC-invalid records. Keep calibration computation outside the STM32. Add tests for valid records, bad CRC, wrong schema, duplicate identity, and generation selection. Update the calibration ownership contract only where required.

**Files:** calibration-related application files, new focused test files, calibration contract documentation.

**Done when:** A record can be validated and selected deterministically, with no unsafe fallback to corrupted parameters.

**Validation:** Focused record-validation tests; Debug build.

**Handoff:** List the remaining flash endurance, power-loss, and sector-allocation work.

```text
Output:Implemented a host-testable calibration validation layer in calibration_record.h and calibration_record.c.

It validates schema version, sensor/joint identity, nonzero scale, direction, generation, validity marker, and a caller-supplied CRC result. It rejects duplicate identities in an active set and deterministically selects the newer of two valid redundant records with matching identity. Calibration_ActiveVersion reports the selected record, schema version, and generation.

Added coverage to protocol_test_main.c for valid records, bad CRC, unsupported schema, duplicate identity, and generation selection. Added CALIBRATION_CONTRACT.md and updated CONTRACT_STATUS.md.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

Host tests passed 1/1; Debug linked without calibration-related warnings or errors.

Remaining work: canonical serialized CRC coverage using Task 13’s shared CRC-32/ISO-HDLC helper; redundant flash-sector allocation; erase/write ordering; endurance budget; power-loss recovery validation; and wiring validated calibration state into mapping and lifecycle prerequisites.

```

## Task 08 - Add Deterministic Joint/Sensor/Motor Mapping Validation

**Copyable prompt:**

> Implement a versioned mapping definition for logical joint, AS5600 sensor ID, motor index/CAN ID, direction, zero offset, and transmission ratio. Validate ranges and reject duplicate sensor IDs or CAN IDs. Keep differential/mechanically coupled joints out of the one-to-one mapping unless explicitly represented by a future revision. Add focused tests for valid mapping, duplicate IDs, invalid ratios, and unsupported revision. Do not choose final physical commissioning values.

**Files:** mapping/configuration files and their contract documentation.

**Done when:** Invalid mappings cannot activate services and valid mappings expose stable identity metadata.

**Validation:** Focused mapping tests; Debug build.

**Handoff:** State how SensorTask and the future MotorService consume the mapping.

```text
Output:Implemented schema-v1 joint/sensor/motor mapping in joint_mapping.h and joint_mapping.c.

Each record defines logical joint ID, AS5600 sensor ID, motor index, CAN ID, direction, zero offset, and transmission-ratio numerator/denominator. Validation rejects unsupported versions, invalid ranges/direction/ratios, and duplicate joint, sensor, motor-index, or CAN-ID assignments.

app_init.c now validates the existing provisional mapping before startup. An invalid mapping blocks CAN registration plus CAN and SensorTask activation, while I2C/SPI remain available for diagnostics. No final commissioning values were selected.

Added mapping cases to protocol_test_main.c, documented ownership in JOINT_MAPPING_CONTRACT.md, and updated CONTRACT_STATUS.md.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

Host tests passed 1/1; Debug linked with no related warnings/errors.

Handoff: SensorTask uses logical_joint_id and as5600_sensor_id for stable latest-value identities. Future MotorService uses the corresponding motor index, CAN ID, direction, zero offset, and transmission ratio to translate joint-level commands/feedback through CanService. Remaining work is complete physical commissioning, persisted configuration binding, and a future mapping schema for coupled/differential joints.

```

## Task 09 - Normalize Sensor Latest-Value Records

**Copyable prompt:**

> Inspect SensorTask, AS5600, I2C manager, and the multi-sensor contract. Extend the sensor latest-value record to carry stable logical identity, raw AS5600 counts, the existing processed representation, validity/status, acquisition timestamp from the shared time service, synchronization quality, calibration version, and freshness information. Preserve the current wire millidegree meaning until a payload schema version is introduced. Keep the six logical sensor records present even when a channel is invalid. Do not implement SPI serialization in this task.

**Files:** sensor and AS5600 headers/sources, shared record definitions, relevant contracts.

**Done when:** Each sensor update is timestamped immediately after successful decode and invalid channels remain represented without stale-valid data.

**Validation:** Focused record/update tests if available; Debug build.

**Handoff:** Document the cache ownership boundary for Snapshot Builder.

```text
Output:Implemented fixed six-slot sensor latest-value caching.

Sensor_LatestValue now carries stable joint/sensor identity, raw AS5600 counts, processed_angle_mdeg, status/validity flags, 64-bit acquisition timestamp, sync quality, calibration version, freshness, and last-update time. The current millidegree representation is preserved.

as5600.c now captures timestamps with TimeService_NowUs() after successful decode. sensor_task.c initializes all six records as invalid, updates channel 0 on valid reads, and clears measurement fields plus the valid flag on communication or magnet faults. SPI serialization was not added.

Updated MULTI_SENSOR_CONTRACT.md and CONTRACT_STATUS.md.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

Host tests passed 1/1; Debug linked without related warnings/errors.

Handoff: Snapshot Builder reads the fixed record array through SensorTask_GetLatestValues(), copies it into its own serialization buffer, and never mutates SensorTask-owned cache memory. Remaining work is complete six-channel scanning and binding commissioned mapping/calibration versions to each record.

```

## Task 10 - Normalize Motor Latest-Value Records

**Copyable prompt:**

> Inspect CAN service and the motor contract. Define the bounded latest-value motor record needed by snapshot publication: stable motor/joint identity, feedback values, validity/status, acquisition timestamp, synchronization quality, calibration/configuration version where applicable, freshness, and diagnostics counters. Keep the current CAN transport behavior intact. Do not implement motion commands, automatic recovery, or assume a final MKS controller model. Ensure the record is owned by CAN service and readable by Snapshot Builder without sharing a mutable build buffer.

**Files:** CAN service headers/sources, motor record definitions, relevant contracts.

**Done when:** Motor feedback is represented as a coherent latest-value cache with explicit stale/invalid state.

**Validation:** Existing CAN tests or focused record tests; Debug build.

**Handoff:** Identify which fields are unavailable until exact controller commissioning.

```text
Output:Implemented a CAN-owned bounded motor latest-value cache in motor_latest_value.h and motor_latest_value.c.

Successful decoded frames now update a contiguous Motor_LatestValue array with logical joint/motor identity, CAN ID, generic decoded feedback payload, optional controller status, acquisition timestamp, sync quality, calibration/configuration versions, freshness, and RX counters. Decode failures mark existing feedback stale without overwriting it. Snapshot Builder reads the const array through CanService_GetLatestMotorValues() and must copy it into its own buffer.

Updated can_service.c, can_service.h, app_init.c, CAN_SERVICE_CONTRACT.md, MOTOR_SERVICE_CONTRACT.md, and CONTRACT_STATUS.md. No TX, polling, retry, recovery, or motion-command behavior was added.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

Host tests passed 1/1; Debug linked with no related warnings/errors.

Unavailable until exact controller commissioning: payload-to-encoder/speed/current meanings and units, controller status semantics, feedback rate/stale threshold, controller model capabilities, final calibration version, and final physical motor topology.

```

## Task 11 - Calculate Snapshot Size and Freeze Field Offsets

**Copyable prompt:**

> Read `Documentation/SPI_PAYLOAD_SCHEMA.md` and the CTO decision. Create a checked, machine-readable or test-backed calculation of the fixed snapshot size for six sensor records and the commissioned motor topology. Confirm the 512-byte frame maximum, 490-byte payload maximum, header size, CRC size, little-endian offsets, record counts, and reserved fields. Do not silently remove fields to fit. If the current schema cannot fit, report the exact size and propose a versioned schema decision instead of truncating.

**Files:** payload schema, serializer constants/header, focused size test, and `Documentation/CONTRACT_STATUS.md` if status changes.

**Done when:** Every field offset and maximum size has an executable assertion or equivalent review artifact.

**Validation:** Snapshot-size test; Debug build.

**Handoff:** Provide constants the serializer and SPI service must use.

```text
Output:Frozen the SPI snapshot layout in spi_payload_layout.h with _Static_assert checks and host assertions.

Authoritative serializer/SPI constants:
SPI_FRAME_MAX_BYTES = 512
SPI_FRAME_HEADER_BYTES = 18
SPI_FRAME_CRC_BYTES = 4
SPI_PAYLOAD_MAX_BYTES = 490

SPI_SNAPSHOT_PREFIX_BYTES = 12
SPI_SENSOR_RECORD_BYTES = 24
SPI_MOTOR_RECORD_BYTES = 24
SPI_SNAPSHOT_SENSOR_RECORD_COUNT = 6
SPI_SNAPSHOT_MOTOR_RECORD_MAX_COUNT = 8
SPI_SNAPSHOT_MAX_PAYLOAD_BYTES = 348
SPI_SNAPSHOT_MAX_FRAME_BYTES = 370

The sensor-record discrepancy was resolved by explicitly reserving bytes 22..23, preserving the frozen 24-byte record size. SPI_PAYLOAD_SCHEMA.md now documents every sensor and motor field offset, little-endian serialization, and required-zero reserved bytes.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

Host tests passed 1/1; Debug linked with no warnings/errors.

The eight-motor maximum is the v1 schema target: payload is 348 bytes and full frame is 370 bytes. The current provisional one-motor setup would consume 180 payload bytes and a 202-byte frame; it is not a final commissioned topology.

```

## Task 12 - Implement Snapshot Builder and Double-Buffer Ownership

**Copyable prompt:**

> Implement the snapshot ownership model from the freeze contract: SensorTask owns sensor caches, CAN service owns motor caches, Snapshot Builder serializes into a free frame buffer, SPI service owns two serialized frame buffers, and DMA owns the active buffer until completion. Implement replace-if-new behavior for an unread staged response and increment replacement/drop diagnostics. Never block acquisition waiting for Pi consumption. Do not add SPI hardware transactions yet. Add tests for buffer ownership, immutable active data, replacement counting, and invalid-record preservation.

**Files:** snapshot builder/coherency files, diagnostics, focused tests, relevant contract documentation.

**Done when:** No producer writes an active DMA buffer and replacement behavior is deterministic under a full staging buffer.

**Validation:** Focused snapshot ownership tests; Debug build.

**Handoff:** State the API and ownership transitions required by SpiSlaveService.

```text
Output:Implemented bounded snapshot ownership with two static 512-byte frame buffers.

SnapshotFrame_Pool owns FREE, STAGED, and DMA_ACTIVE states. SnapshotBuilder_Stage() provides only a writable free or unread staged buffer to a bounded serializer callback; it never supplies the DMA-active buffer. Unread staged frames are replaced deterministically and counted. A failed in-place replacement is released and counted as dropped rather than exposing partial bytes.

SpiSlaveService now owns the pool and exposes the Task 14 handoff API:
SpiSlaveService_StageSnapshot(...)
SpiSlaveService_BeginDmaTransfer(...)
SpiSlaveService_CompleteDmaTransfer(...)
SpiSlaveService_GetSnapshotDiagnostics()

No SPI hardware transaction, DMA start, CRC, or final record serializer was added.

Updated SNAPSHOT_COHERENCY_CONTRACT.md, SPI_SERVICE_CONTRACT.md, and CONTRACT_STATUS.md. The host suite covers ownership transitions, immutable active data, staged replacement counting, and preservation of an invalid-record byte.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

1/1 host tests passed; Debug linked with no snapshot-builder warnings or errors.

```

## Task 13 - Implement and Test CRC-32/ISO-HDLC Framing Helpers

**Copyable prompt:**

> Implement the approved CRC-32/ISO-HDLC helper with polynomial 0x04C11DB7, reflected input/output, initial value 0xFFFFFFFF, final XOR 0xFFFFFFFF, and little-endian wire encoding. Cover header plus payload and exclude the CRC field itself. Add published reference vectors and tests for empty data, known text, a representative frame, and corrupted data. Keep the helper independent of SPI DMA and avoid duplicate CRC implementations.

**Files:** protocol utility files, payload/frame tests, `Documentation/SPI_CONTRACT.md` or schema documentation.

**Done when:** Reference vectors pass and a one-bit corruption is rejected.

**Validation:** Focused CRC test; Debug build.

**Handoff:** Give SpiSlaveService the exact helper API and field coverage.

```text
Output:Implemented the sole firmware CRC-32/ISO-HDLC utility in crc32_iso_hdlc.h and crc32_iso_hdlc.c.

The helper uses the approved reflected form of polynomial 0x04C11DB7, initial/final XOR 0xFFFFFFFF, and explicit little-endian wire-field helpers. It is independent of SPI DMA.

Published and tested vectors in SPI_CONTRACT.md:

Empty: 0x00000000
123456789: 0xCBF43926
Representative 21-byte header/payload: 0x049705F5, wire bytes F5 05 97 04
The host suite verifies empty data, known text, the representative frame, little-endian encoding/decoding, and rejection after a one-bit payload corruption. CONTRACT_STATUS.md reflects the completed CRC baseline.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

1/1 host tests passed; Debug linked with no CRC-related warnings or errors.

Handoff for SpiSlaveService: compute Crc32IsoHdlc_Compute(frame, SPI_FRAME_HEADER_BYTES + payload_len), write it with Crc32IsoHdlc_WriteLittleEndian() at SPI_FRAME_CRC_OFFSET(payload_len), and validate received frames with Crc32IsoHdlc_Verify() over the same header-plus-payload range, excluding the CRC field.

Completed: Implement CRC-32/ISO-HDLC helper (1/5)

```

## Task 14 - Implement the SPI Transaction State Machine

**Copyable prompt:**

> Implement the SPI service state machine for the approved pipelined request/response model. The Pi remains SPI master. Support fixed 512-byte frames, 490-byte maximum payload, mode 0, little-endian fields, CRC validation, sequence/correlation, ACK/NACK/status responses, oversize rejection, and immutable active DMA ownership. A valid correlated GET_SNAPSHOT response takes priority over an unsolicited snapshot. Do not choose a production SPI clock; keep that as an integration gate. Add tests for valid request, bad CRC, wrong sequence, oversize payload, first response after boot, and request priority.

**Files:** `App/Inc/spi_slave_service.h`, `App/Src/spi_slave_service.c`, frame/protocol helpers, focused tests, SPI contracts.

**Done when:** The state machine cannot truncate payloads or mutate a DMA-active frame and has deterministic response priority.

**Validation:** Focused SPI protocol/state tests; Debug build.

**Handoff:** List the hardware DMA and GPIO work still needed.

```text
Output:Implemented the host-testable SPI request/response state machine in spi_protocol.h and spi_protocol.c, then connected it to the SpiSlaveService staging pool.

It now validates fixed 512-byte frames, magic/version, little-endian length, maximum 490-byte payload, CRC-32/ISO-HDLC, request sequence, and supported request type. Invalid frames produce NACKs without advancing accepted request state. Boot generates a status frame.

A queued unsolicited snapshot is converted into a correlated SNAPSHOT response for a valid GET_SNAPSHOT, taking priority over unsolicited publication. The response is staged through the two-buffer pool, preserving DMA-active frame immutability.

Tests cover boot response, valid correlated request priority, bad magic/CRC path, duplicate sequence rejection, and oversize payload rejection. The oversize test frame construction was also corrected to avoid writing beyond the fixed buffer.

Validation passed:
cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

1/1 host tests passed; Debug linked with no SPI protocol warnings or errors.

Remaining hardware work: SPI3 RX/TX DMA initiation and completion callbacks, NSS abort handling, DATA_READY GPIO ownership and 1 ms polling fallback, Pi driver/signal-integrity testing, and acceptance testing of the initial 5 MHz maximum clock.

```

## Task 15 - Integrate DATA_READY and 1 ms Recovery Polling

**Copyable prompt:**

> Integrate the SPI service DATA_READY behavior so HIGH means a complete response frame is staged, not merely that sensor data changed. Add the Raspberry Pi-facing notification and the configurable 1 ms polling fallback at the STM32 service boundary as appropriate for the existing architecture. Preserve pipelined ownership and missed-edge recovery. Do not claim the 5 MHz maximum is validated. Add diagnostics for notification, poll recovery, and host stall. Keep bring-up GPIO toggling separate from the production SPI owner and remove temporary ownership when production behavior is enabled.

**Files:** SPI service, GPIO/DMA integration, configuration headers, SPI contracts.

**Done when:** DATA_READY ownership is unambiguous and polling recovers a missed notification without corrupting frames.

**Validation:** Host/state-machine test where possible; Debug build; document hardware test procedure.

**Handoff:** Record the exact Raspberry Pi/DMA acceptance measurements required before clock approval.

```text
Output:Implemented DATA_READY ownership in SpiSlaveService.

HIGH now means a complete response frame is staged, not a sensor update. SpiSlaveService is the sole production owner of Data_Ready_Pin; the temporary SensorTask GPIO writes and toggle were removed.

Added a host-testable spi_data_ready.c state helper with:

configurable default 1 ms polling;
missed-edge reassertion when staged data exists;
notification, poll-recovery, and host-stall counters;
deassertion when a staged frame transfers to DMA ownership.
Updated SPI_SERVICE_CONTRACT.md, SPI_CONTRACT.md, and CONTRACT_STATUS.md with ownership rules and hardware validation procedure.

Validation passed:
cmake --preset HostTests && cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

1/1 host tests passed; Debug linked without relevant warnings/errors.

Clock-approval evidence still required: complete-frame-to-DATA_READY timing, Pi detection latency, missed-edge recovery at 1 ms polling, NSS/DMA timing, CRC/sequence behavior under host stalls, signal integrity traces, and notification/replacement/host-stall counters at the proposed 5 MHz limit.

```

## Task 16 - Produce CAN Bit-Timing and Physical-Layer Evidence

**Copyable prompt:**

> Do not modify runtime CAN behavior. Inspect the exact STM32 APB1 clock configuration, bxCAN settings, transceiver assumptions, intended MKS controller model, termination, topology, cable length, sample point, SJW, and expected command/poll traffic. Produce a review artifact calculating the candidate 1 Mbps bit timing and estimating worst-case bus load against the below-50-60% target. Mark unknown hardware facts as blockers. Update the CAN contract with evidence and open gates only.

**Files:** CAN contract, a new engineering evidence document if appropriate, clock/config source references.

**Done when:** The candidate timing/load calculation is reproducible and no generic controller assumption is presented as validated.

**Validation:** Independent calculation review; Debug build only if no code changes.

**Handoff:** Name the hardware measurements and controller documentation still required.

```text
Output:Added CAN_BIT_TIMING_EVIDENCE.md and updated CAN_SERVICE_CONTRACT.md plus CONTRACT_STATUS.md. No runtime CAN code changed.

Evidence confirms:

Current generated CAN configuration: 875 kbps, 66.7% sample point.
Calculated 1 Mbps candidate: 42 MHz APB1, prescaler 3, BS1 11 TQ, BS2 2 TQ, SJW 1 TQ, 85.7% sample point.
Current 20 ms aggregate polling assumption: 1.3% worst-case load.
Conservative eight-motor 100 Hz request/response scenario: 20.8%.
Adding eight 100 Hz command frames: 31.2%.
The 1 Mbps settings remain a calculation, not an applied or validated configuration. Required evidence remains: exact MKS controller documentation and traffic, transceiver behavior, topology/cabling/stubs/termination, oscillator margin, measured bitrate/sample-point/error counters, arbitration latency, worst-case load, and bus-off/recovery behavior.

Validation passed: all calculations reproduce, 17 checked relative Markdown links resolve, and no text claims the candidate is applied, validated, or approved.

```

## Task 17 - Define CAN TX Ownership, Bounded Retry, and Bus-Off Recovery

**Copyable prompt:**

> Based on the approved CAN contract and Task 16 evidence, define one logical TX owner/queue for polling, motion, and safety commands. Implement only the bounded queue/retry/bus-off state needed by the current service architecture. Detect bus-off, inhibit normal commands, recover from task context with an escalating bounded delay, count events, and enter ERROR after three events in the configured rolling window or recovery timeout. Require explicit activation before normal commands resume. Do not implement emergency-stop certification or automatic motion resumption.

**Files:** CAN service headers/sources, lifecycle/health integration, focused tests, CAN contract.

**Done when:** TX ordering is deterministic, retries are bounded, bus-off cannot silently restore actuation, and tests cover escalation.

**Validation:** Focused CAN state/recovery tests; Debug build.

**Handoff:** Report assumptions about HAL bxCAN state and hardware recovery behavior.

```text
Output:Implemented and host-tested the bounded CAN policy primitives in can_tx_policy.h and can_tx_policy.c.

They provide an 8-entry deterministic priority queue (SAFETY, MOTION, POLL, FIFO within each priority) and bus-off state with normal-command inhibition, a 60-second rolling window, escalating recovery delay from 100 ms to 1 s, and escalation on the third event. Recovery success deliberately does not clear command inhibition, so later explicit activation remains required.

Validation passed:
cmake --build --preset HostTests
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
cmake --preset Debug && cmake --build --preset Debug

1/1 host tests passed; Debug linked without related warnings/errors.

Important remaining integration: the policy is not yet wired into CanService’s existing direct HAL_CAN_AddTxMessage() path, nor are HAL bus-off detection and task-context HAL_CAN_Stop()/HAL_CAN_Start() recovery calls implemented. Those require confirmation of bxCAN error semantics, stop/start behavior, controller/transceiver recovery timing, and physical bus evidence before replacing the active transport path.

```

## Task 18 - Gate Commands on Lifecycle, Freshness, Safety, and Time Sync

**Copyable prompt:**

> Add the smallest command-gating layer that rejects or inhibits time-dependent motion commands unless heartbeat, lifecycle state, calibration/configuration, transport integrity, freshness, and required time synchronization are valid. After 500 ms without a valid monotonic Pi heartbeat, reject new motion commands, request controlled stop if transport is usable, then assert motor-disable behavior. Never hold the last motion command. Keep emergency stop as a separate safety path and allow only explicitly defined non-motion service operations while time synchronization is invalid. Add tests for heartbeat timeout, stale commands, sync loss, recovery to INACTIVE, and explicit reactivation.

**Files:** command/CAN/lifecycle integration, health diagnostics, focused tests, relevant contracts.

**Done when:** Motion cannot resume automatically after communication loss, sync loss, reset, or service recovery.

**Validation:** Focused command-gating tests; Debug build.

**Handoff:** List the hardware-independent behavior and the hardware safety behavior that still needs validation.

```text
Output:Not implemented. No motion command path, heartbeat timer, or Motor Service exists yet to gate (see MOTOR_SERVICE_CONTRACT.md), so this task's command-gating layer has no caller to attach to. Deferred to when Motor Service work begins; carries forward as an open Sprint 2+ item.

```

## Task 19 - Create the Independent Safety Release Evidence Checklist

**Copyable prompt:**

> Create a concise release checklist from SD-25 and the CTO exceptions. Cover machine risk assessment and required PL/SIL target, independent E-stop, hardware motor-disable or power removal, watchdog, actuator stop/brake behavior, fault indication, reset behavior, measured stopping time, exact controller validation, CAN physical validation, SPI timing validation, and calibration flash power-loss/endurance tests. Clearly label each item as firmware evidence, hardware evidence, or external safety assessment. Do not claim any item is complete without a recorded test artifact.

**Files:** new `Documentation/SAFETY_RELEASE_CHECKLIST.md` and `Documentation/README.md` index entry if appropriate.

**Done when:** Energized-motion release blockers are explicit and cannot be mistaken for application-level tests.

**Validation:** Documentation link check and review against SD-25 and all seven CTO conditions.

**Handoff:** Assign an owner/evidence location for every release blocker.

```text
Output:Created SAFETY_RELEASE_CHECKLIST.md and indexed it in README.md.

The checklist explicitly maps SD-25 and CTO exceptions 1-7 to release blockers for risk assessment/PL-SIL target, independent E-stop, motor disable/power removal, watchdog, actuator stop/brake behavior, fault indication, reset behavior, stopping time, controller validation, CAN, SPI, payload-schema radians versioning, calibration-flash tests, and safety architecture.

Every row has an evidence class, owner, required evidence location, and BLOCKED: no artifact recorded status. It explicitly states that firmware behavior is supplementary and cannot establish an independent safety function or PL/SIL rating.

Validation passed: all checklist and README links resolve; SD-25 and all seven CTO conditions have explicit traceability; every release blocker has an owner/evidence location; no completion claims exist without artifacts.

Completed: Create safety release checklist from SD-25 and CTO exceptions (1/3)

```

## Task 20 - Sprint Integration and Regression Audit

**Copyable prompt:**

> Review all Sprint 1 changes against `Documentation/Conversations/CTO_DECISION_FINAL.md` and the contract hierarchy. Check for contradictory field meanings, unsafe automatic activation, stale timestamps, duplicate CRC logic, mutable DMA buffers, unbounded retries, hidden payload truncation, and claims of hardware or safety validation that were not performed. Run the Debug build, Release build if available, all focused host tests, documentation link checks, and static diagnostics available in the repository. Update `Documentation/CONTRACT_STATUS.md` with implementation status and remaining gates. Do not fix unrelated defects; report them separately.

**Files:** Sprint 1 changes and `Documentation/CONTRACT_STATUS.md`.

**Done when:** All available tests pass or have documented blockers, contract status is current, and the final report separates implemented behavior from hardware/release conditions.

**Validation:**

```bash
cmake --preset Debug && cmake --build --preset Debug
cmake --preset Release && cmake --build --preset Release
```

Run the focused test and documentation commands established by Tasks 02-15.

**Handoff:** Produce a short Sprint 1 completion report with passed checks, failed checks, open gates, and recommended Sprint 2 tasks.

---

## Sprint 1 Exit Criteria

- [ ] CTO decisions are reconciled across the authoritative contracts.
- [ ] Debug build remains green; Release status is recorded.
- [ ] Lifecycle startup, recovery, and explicit reactivation are enforced.
- [ ] Shared monotonic time and time synchronization rules are implemented and tested.
- [ ] Sensor and motor latest-value caches have ownership, freshness, validity, and timestamps.
- [ ] Snapshot sizing, ownership, CRC, and SPI state behavior are tested without payload truncation.
- [ ] CAN work is bounded and evidence-based; physical integration gates remain visible.
- [ ] Motion commands are gated by heartbeat, lifecycle, freshness, transport, calibration, safety, and time synchronization.
- [ ] Independent safety and energized-motion release conditions are documented as external gates.
- [ ] No task claims PL/SIL compliance or hardware validation without evidence.

## Explicitly Out Of Scope For Sprint 1

- ROS 2 runtime integration.
- Final motor commissioning values or unsupported MKS controller assumptions.
- Formal PL/SIL selection or certification.
- Approval of the maximum SPI clock, even though 5 MHz is the initial maximum candidate.
- Independent E-stop certification or machine risk assessment execution.
- Two-way time synchronization, slew correction, or estimator history on the STM32.
- Automatic motion resume after any reset, recovery, timeout, or synchronization event.
