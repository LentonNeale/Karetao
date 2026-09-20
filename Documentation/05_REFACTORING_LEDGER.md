# Documentation Refactoring Ledger

Working memory tracking the migration of legacy `docs/project/**` content into `Documentation/**`. This ledger records the disposition of every statement and block migrated, for acceptance criterion 1 verification.

---

## WP-1: Decisions (Completed)

Pre-made decisions that block WP-2 and WP-3:

### §4.4 Residual component content
**Decision:** Option (a) — Create `Arm_Sensor_Hub/Documentation/` and `RaspberryPi_Sensor_Hub/Documentation/`.

Each component directory receives:
- A `README.md` containing the component authority declaration per `COMPONENT_DOCUMENTATION_MODEL.md` § "Component authority declaration"
- References to Karetao requirements by SYS-* identifier, never copying complete requirements
- Implementation documentation authority within the component scope

Rationale: Empties `docs/` completely while respecting authority model's component-ownership rule.

### C-1 `DATA_READY` semantics
**Decision:** Armed-then-assert model from `protocols/spi-contract.md` §8 is authoritative.

Statement: "A frame merely staged in a software buffer but not yet DMA-armed is not sufficient."

Supersedes: `firmware/CONTRACT_V1_FREEZE.md` § DATA_READY ("HIGH means a complete response frame is staged and ready for the Raspberry Pi to clock.") — this is a lower-level refinement that contradicts the freeze document's signal definition.

Source: `protocols/spi-contract.md` §8, being more specific and system-observable, takes precedence.

### C-3 SPI frame size
**Decision:** 512 bytes is the fixed transaction length; 490 bytes is the maximum payload.

Correction to migrate: `protocols/spi-contract.md` §17 currently says "512-byte maximum frame". This will be corrected to "fixed transaction frame: 512 bytes" with "maximum payload: 490 bytes" on migration to `02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`.

Rationale: Fixed vs. maximum is a different contract for the host driver; the 512-byte framing is fixed (with DMA setup, header overhead), while payload varies.

---

## WP-2: Implementation Checklist (Completed)

Updated:
- `Documentation/06_IMPLEMENTATION_CHECKLIST.md` lines 49–50 to reflect Option (a) scope.

---

## WP-3a: SPI System Interface Expansion (In Progress)

**Files processed:**
- `docs/project/protocols/spi-contract.md` (306 lines) → Karetao
- `docs/project/protocols/spi-payload-schema.md` (164 lines) → Karetao
- `docs/project/firmware/SNAPSHOT_COHERENCY_CONTRACT.md` (109 lines) → Karetao/Component split
- `docs/project/interfaces/spi-service-contract.md` (135 lines) → Karetao/Component split
- `docs/project/interfaces/raspberry-pi-spi.md` (61 lines) → Karetao/Verification split

### `docs/project/protocols/spi-contract.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| §1 Purpose: SPI transport/framing/transaction/timestamp/sync contract | Karetao | SPI_SYSTEM_INTERFACE.md preamble | Moved (introductory) |
| §1 Three concerns model (Transport/Data/Time) | Karetao | SPI_SYSTEM_INTERFACE.md preamble (implicit) | Merged into structure |
| §2 Roles: Pi master, STM32 slave, DATA_READY signal | Karetao | SPI_SYSTEM_INTERFACE.md §1 | Moved |
| §2 Physical interface pinout (NSS/SCK/MISO/MOSI) | Karetao | SPI_SYSTEM_INTERFACE.md §1 | Moved |
| §2 "5 MHz value remains current integration ceiling..." | Karetao | SPI_SYSTEM_INTERFACE.md §1 | Moved verbatim (caveat preserved) |
| §3 Protocol rules (little-endian, serialization, CRC32, malformed frame handling) | Karetao | SPI_SYSTEM_INTERFACE.md §2 | Moved |
| §3 CRC reference vectors (empty, 123456789, test vector) | Karetao | SPI_SYSTEM_INTERFACE.md §2 | Moved |
| §4 Frame format table (magic, version, message_type, payload_len, seq, frame_time_us, payload, crc32) | Karetao | SPI_SYSTEM_INTERFACE.md §3 | Moved |
| §4 "frame_time_us is not a measurement timestamp" | Karetao | SPI_SYSTEM_INTERFACE.md §3 | Moved verbatim |
| §4 "512-byte maximum frame; 490-byte maximum payload" | Karetao | SPI_SYSTEM_INTERFACE.md §3 | **Corrected to "fixed 512 bytes, maximum 490 payload"** per C-3 decision |
| §5 Pipelined request/response transaction model diagram and explanation | Karetao | SPI_SYSTEM_INTERFACE.md §4 | Moved |
| §5 "seq identifies transmitted frame; response carries response_to_seq; async use zero" | Karetao | SPI_SYSTEM_INTERFACE.md §4 | Moved |
| §6 Message type table (SNAPSHOT, EVENT, DIAGNOSTIC, GET_SNAPSHOT, GET_STATUS, TIME_SYNC, SET_MOTOR_COMMAND, GET_VERSION, ACK, NACK) | Karetao | SPI_SYSTEM_INTERFACE.md §5 | Moved |
| §7 Sequence number rules (32-bit, monotonic, wraps, identifies frame, correlation via response_to_seq) | Karetao | SPI_SYSTEM_INTERFACE.md §6 | Moved |
| §8 DATA_READY semantics: "armed-then-assert model"; "frame merely staged...not DMA-armed is not sufficient" | Karetao | SPI_SYSTEM_INTERFACE.md §7 | Moved verbatim (C-1 resolution: supersedes CONTRACT_V1_FREEZE.md wording) |
| §8 Snapshot replacement, dropped counter, diagnostic reporting | Karetao | SPI_SYSTEM_INTERFACE.md §7 (via Snapshot Coherency §8) | Merged |
| §8 "1 ms polling fallback, 100 ms host-stall timeout, these paths exercised on STM32, physical DATA_READY/Pi path unvalidated" | Karetao | SPI_SYSTEM_INTERFACE.md §7 | Moved verbatim (caveats preserved) |
| §9 Snapshot coherency and ownership model (producer caches, Snapshot Builder, DMA ownership rules) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — buffer ownership and DMA mechanics are component-internal (per plan) |
| §10 Measurement timestamps (acquisition timestamp, not transport time, min record concepts) | Karetao | SPI_SYSTEM_INTERFACE.md §9 | Moved |
| §11 Time domain (hub_time_us = local + offset, Pi authority, monotonic local clock, timestamp usage) | Karetao | SPI_SYSTEM_INTERFACE.md §10 | Moved |
| §12 TIME_SYNC payload structure and offset calculation | Karetao | SPI_SYSTEM_INTERFACE.md §11 | Moved |
| §12 "one-way transport uncertainty; future two-way exchange may add..." | Karetao | SPI_SYSTEM_INTERFACE.md §11 | Moved verbatim (versioned enhancement note preserved) |
| §13 Synchronization validity (5 second timeout, monotonicity, offset stepping vs. slewing) | Karetao | SPI_SYSTEM_INTERFACE.md §12 | Moved |
| §14 Host responsibilities (operate as master, observe DATA_READY, validate, track seq, TIME_SYNC, maintain clock, timestamp, correlate, never use transport time) | Karetao | SPI_SYSTEM_INTERFACE.md §13 | Moved |
| §15 STM32 responsibilities (operate slave, use DMA, monotonic clock, timestamp, coherency, DATA_READY, validate, sequence numbers, sync reporting, lifecycle/safety) | Component (mostly) | Arm_Sensor_Hub/Documentation/ | **Not migrated** — DMA details, ISR/callback work, HAL usage are component-internal; lifecycle/safety gate referenced |
| §16 Error handling (reject frame validation failures, return NACK codes, malformed never changes state, transport faults) | Karetao | SPI_SYSTEM_INTERFACE.md §14 | Moved |
| §16 (duplicate section header; should be §17) Versioning and integration gates | Karetao | SPI_SYSTEM_INTERFACE.md §16 | Moved |
| §17 "remaining SPI integration gate is live-host and physical acceptance"; validation details (5 MHz clock, NSS, DATA_READY electrical, GPIO/signal, transactions, request/response) | Karetao | SPI_SYSTEM_INTERFACE.md §16 | Moved verbatim |
| §17 "current 5 MHz value is integration ceiling, not hardware approval" | Karetao | SPI_SYSTEM_INTERFACE.md §16 | Moved verbatim (caveat preserved) |
| §17 "approved v1.0 decisions must not be redefined..." | Karetao | SPI_SYSTEM_INTERFACE.md §16 | Moved |
| §18 Twelve contract invariants | Karetao | SPI_SYSTEM_INTERFACE.md §17 | Moved |

### `docs/project/protocols/spi-payload-schema.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| Entire document (164 lines): message payload layouts (SNAPSHOT, EVENT, DIAGNOSTIC, TIME_SYNC, ACK/NACK, GET/command requests), maximum sizes, schema decisions | Karetao | SPI_PAYLOAD_SCHEMA.md | **Moved whole** — wire payload layouts are by definition cross-boundary |

### `docs/project/firmware/SNAPSHOT_COHERENCY_CONTRACT.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| §2 Target data set (six logical axes, snapshot always six records, sensor IDs 0-5, motor mapping) | Karetao | SPI_SYSTEM_INTERFACE.md §8 (fixed six-record snapshot) | Moved |
| §2 "current firmware implements only channel 0...contract describes target model" | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — implementation status and partial availability |
| §3 Ownership model (producer caches, Snapshot Builder, DMA buffer ownership, state transitions, SnapshotFrame_Pool, task context synchronization) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — entirely DMA and task context mechanics |
| §4 Publish policy (replace-if-new, pending frames, free buffer, drop/replace counters, never block acquisition) | Karetao | SPI_SYSTEM_INTERFACE.md §8 (replace-if-new semantics) | Moved |
| §5 Coherency definition (record copying, per-record timestamps, frame assembly time, validity flags, record counts, no modification during serialization/DMA) | Karetao | SPI_SYSTEM_INTERFACE.md §8 (snapshot coherency guarantee) | Moved |
| §6 Startup and partial availability (invalid/stale flags, zeroed values, diagnostic reason, fixed six-record target) | Karetao | SPI_SYSTEM_INTERFACE.md §8 (fixed six-record snapshot, partial availability) | Moved |
| §7 Sensor and motor coordination (task/service ownership, no direct DMA buffer write, application coordinator, SPI service ownership) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — task coordination and service internals |
| §8 Timing and freshness (sensor timestamp capture, acquisition time marking, validity flags, timestamp age, 64-bit TIM2 extension) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — HAL/peripheral specifics; timestamp domain noted in SPI_SYSTEM_INTERFACE.md §10 |
| §9 Required diagnostics (sequence, replaced/dropped, ownership, publish time, SPI consume time, DMA state, partial/invalid records) | Karetao (implicit) | SPI_SYSTEM_INTERFACE.md §8 (drop diagnostics) | Referenced; full list is component diagnostic contract |
| §10 Verification requirements (ownership, atomicity, CRC/length, host stalls, partial sets, DMA completion) | Verification | 05_VERIFICATION/ | **Not migrated at this stage** — verification strategy; note for WP-7 archive decision |

### `docs/project/interfaces/spi-service-contract.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble: Status, Owner (SpiSlaveService), Boundary | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — service-specific; links to spi-contract.md and SNAPSHOT_COHERENCY_CONTRACT.md now point to Karetao |
| §1 Purpose: buffer ownership, DATA_READY semantics, lifecycle safety, RTOS behavior | Component (mostly) / Karetao (DATA_READY) | SPI_SYSTEM_INTERFACE.md §7 (DATA_READY only) | Data_READY host-observable semantics moved; buffer/service details component |
| §2 Current status (DMA path, STM32 measurements, software state machine, no live host validation) | Verification | 05_VERIFICATION/ | **Not migrated** — test/measurement evidence; reference for verification gate |
| §3 Lifecycle states (UNCONFIGURED, INACTIVE, ACTIVE, ERROR) | Component / Karetao (referenced) | Karetao: SPI_SYSTEM_INTERFACE.md §15 (lifecycle integration); Component: service state machine | Lifecycle referenced; state definitions in SYSTEM_LIFECYCLE.md |
| Buffer ownership model (producer caches, two static buffers, DMA_TX, DMA callbacks) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — entirely DMA and buffer pool |
| Protocol state validation (ProcessRequest, GET_SNAPSHOT priority, TIME_SYNC application) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — protocol handler internals |
| §8 DATA_READY: assert only after DMA-armed, armed-then-assert model, deassert rules, polling, counts | Karetao | SPI_SYSTEM_INTERFACE.md §7 | Moved (already in §7 from spi-contract.md) |
| Hardware validation procedure (5 MHz acceptance criteria: DATA_READY timing, NSS, DMA timing, signal integrity) | Verification | 05_VERIFICATION/ | **Not migrated** — validation requirements; reference for integration gate |
| DMA and deferred processing (ISR minimal, defer to task context, no blocking/serialization in ISR) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — entirely implementation strategy |
| Validation and errors (fault classes: transient, repeated, invalid command, shutdown) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — service error handling; NACK semantics in SPI_SYSTEM_INTERFACE.md §14 |
| Timing and concurrency (Process() context, no public mutation ISR-safe, no mutex across DMA, serialization bounded, CRC parameters, 5-sec sync timeout, 64-bit timestamp extension) | Component (mostly) | Karetao (timing specs, sync timeout, timestamp spec) | Sync timeout and CRC parameters in SPI_SYSTEM_INTERFACE.md §12–13; others component |
| Required diagnostics (lifecycle, DMA, CRC rejection, DATA_READY assertions, dropped frames, last sequence, sync validity) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — diagnostic contract; implied by system drop/replacement semantics |
| Verification (DATA_READY, TX buffer immutability, host stalls, NSS abort, invalid frames, lifecycle deactivation, buffer ownership) | Verification | 05_VERIFICATION/ | **Not migrated** — verification strategy |

### `docs/project/interfaces/raspberry-pi-spi.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble: "Raspberry Pi-side companion to ARM-owned SPI contracts" | Karetao | SPI_SYSTEM_INTERFACE.md (implicit) | Contextual; no separate document needed |
| §1 Hardware baseline: Raspberry Pi as master, STM32F405 SPI3 as slave | Karetao | SPI_SYSTEM_INTERFACE.md §1 | Moved (already included in §1 "physical interface") |
| Pinout table (Pi physical pins 19/21/23/24 → MOSI/MISO/SCLK/CE0 → PC12/PC11/PC10/PA15) | Karetao | SPI_SYSTEM_INTERFACE.md §1 | Moved |
| DATA_READY GPIO unassigned, explicit SPI transfers, can be added later | Karetao | SPI_SYSTEM_INTERFACE.md §7 (caveat in DATA_READY section) | Referenced (DATA_READY section notes Pi GPIO unassigned in current baseline) |
| §2 Transport: spidev, mode 0, 8-bit words, 5 MHz max, fixed 512-byte transfers, logical frame < 512, CRC covers logical frame only | Karetao | SPI_SYSTEM_INTERFACE.md (framing, CRC scope, 512-byte fixed; 5 MHz caveat) | Moved; integration ceiling caveat preserved |
| Pipelined request/response (response staged before request, request validated after DMA completion, next response staged) | Karetao | SPI_SYSTEM_INTERFACE.md §4 | Already present from spi-contract.md; Pi implementation detail noted implicitly |
| §3 Software (spi_bus.py, spi_protocol.py, spi_device.py split, injectable backend) | Component | RaspberryPi_Sensor_Hub/Documentation/ | **Not migrated** — Pi implementation architecture |
| §4 Bring-up: spidev package, SPI0 enable, /dev/spidev0.0, 5 MHz or below | Verification / Component | `05_VERIFICATION/` (bring-up gate) or Pi docs | **Not migrated** — operational runbook; reference for bring-up validation |
| §5 Validation requirements (1. connectivity 2. Mode 0 timing 3. 512-byte DMA 4. CRC/seq 5. NSS abort 6. DATA_READY (if GPIO assigned) 7. sustained load) | Verification | `05_VERIFICATION/SPI_VALIDATION.md` or integration gates | **Not migrated as distinct document** — validation strategy; items 1–5 are SPI_SYSTEM_INTERFACE.md §16 integration gates |

### Summary of Disposition

**Moved to Karetao (SPI_SYSTEM_INTERFACE.md and SPI_PAYLOAD_SCHEMA.md):**
- spi-contract.md: §§1–8, 10–14, 16–18 (excluding §9, §15 component internals)
- spi-payload-schema.md: entire file (164 lines)
- SNAPSHOT_COHERENCY_CONTRACT.md: coherency guarantee, snapshot model, replace-if-new semantics, fixed six-record target, partial availability
- spi-service-contract.md: DATA_READY timing/assertions/deassertions, host-stall timeout, error/NACK behavior (host-observable only)
- raspberry-pi-spi.md: hardware baseline, pinout, physical interface, framing specifications, integration ceiling caveat

**Deliberately dropped, destination noted:**
- spi-contract.md §9 (buffer ownership, DMA, task sync) → Component (Arm Sensor Hub internals)
- spi-contract.md §15 (STM32 responsibilities, HAL, ISR) → Component (Arm Sensor Hub internals)
- SNAPSHOT_COHERENCY_CONTRACT.md §3 (SnapshotFrame_Pool, ownership transitions, task context) → Component (Arm Sensor Hub internals)
- spi-service-contract.md §3–7 (SpiSlaveService lifecycle, buffer ownership, DMA, protocol handler, error handling, diagnostics, verification strategy) → Component (Arm Sensor Hub internals)
- raspberry-pi-spi.md §3 (Pi software architecture) → Component (Raspberry Pi Sensor Hub internals)
- raspberry-pi-spi.md §2 Current status (test measurements, DMA evidence) → Verification (05_VERIFICATION/ evidence reference)
- raspberry-pi-spi.md §4 Bring-up (operational runbook) → Verification/Component (bring-up gate; Pi operational docs)

**Decisions applied during migration:**
- **C-1 (DATA_READY semantics):** armed-then-assert model from spi-contract.md §8 is authoritative. CONTRACT_V1_FREEZE.md "staged-then-assert" wording is superseded.
- **C-3 (SPI frame size):** Corrected spi-contract.md §4/§17 wording from "512-byte maximum frame" to "fixed 512-byte transaction, 490-byte maximum payload" per the decision that frame size is fixed (DMA setup), while payload varies.

---

## WP-3b: TIME System Interface (In Progress)

**File processed:**
- `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md` (60 lines) → split: Karetao system interface + component internals

### `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble: Status, Owner, Boundary | Context | TIME_SYSTEM_INTERFACE.md preamble | Noted; not copied |
| §1 Time model: `hub_time_us = local_time_us + time_offset_us`, Pi authority, monotonicity | Karetao | TIME_SYSTEM_INTERFACE.md §1 | Moved |
| §1 "measurement_timestamp_us" vs. "frame_time_us" distinction | Karetao | TIME_SYSTEM_INTERFACE.md §2 | Moved |
| §2 Current source: TIM2, TimeService_NowUs(), wrap detection at ~4,295 seconds | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — timer peripheral and service implementation |
| §2 "Readers must execute from one serialized task/system context...first version does not provide ISR-safe..." | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — task synchronization and concurrency model |
| §2 AS5600 timestamp migration, raw TIM2 counter, long-lived I2C/CAN/SPI/diagnostic timestamps | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — peripheral and sensor integration details |
| §2 "Measurement timestamp captured immediately after AS5600 bytes received and decoded" | Component | Arm_Sensor_Hub/Documentation/ (AS5600 integration) / Karetao (conceptual definition in §2) | Moved concept to TIME_SYSTEM_INTERFACE.md §2; peripheral timing details component |
| §3 TIME_SYNC payload (pi_time_us, sync_seq, flags), STM32 capture and offset calculation | Karetao | TIME_SYSTEM_INTERFACE.md §3 | Moved |
| §3 Required state: time_sync_valid, time_offset_us, last_sync_sequence, last_sync_local_time_us, age/fault status | Karetao | TIME_SYSTEM_INTERFACE.md §3 | Moved |
| §3 TimeService_SyncStateAccept() semantics: initial bound (±24 hours), runtime bound (±1 second), sequence validation, atomic commit | Karetao (acceptance criteria) | TIME_SYSTEM_INTERFACE.md §4 | Moved (criteria); implementation function name component |
| §3 TimeService_SyncStateGetSnapshot(), TimeService_AcceptSync(), TimeService_IsSyncValid(), TimeService_GetSyncSnapshot() | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — service API and task-context interfaces |
| §3 "first implementation uses direct offset step; system_time_us permitted to jump; two-way RTT and slewing are future enhancements" | Karetao | TIME_SYSTEM_INTERFACE.md §4 | Moved verbatim (versioned enhancement note preserved) |
| §4 Validity: 5-second timeout, unsynchronized marking, rejection of stale timestamps, export valid/unsynchronized quality | Karetao | TIME_SYSTEM_INTERFACE.md §4–5 | Moved |
| §4 "Synchronization expiry does not stop acquisition or diagnostics...marks records unsynchronized...rejects or inhibits time-dependent motion" | Karetao | TIME_SYSTEM_INTERFACE.md §5 | Moved |
| §4 Reset behavior: clears validity and volatile offset | Karetao | TIME_SYSTEM_INTERFACE.md §5 | Moved |
| §4 "Only explicitly defined non-motion service operations may continue while sync invalid" | Karetao | TIME_SYSTEM_INTERFACE.md §5 | Moved |
| §5 Atomicity and concurrency: sync update and validity as logical unit, readers see complete previous or new update, not partial | Karetao | TIME_SYSTEM_INTERFACE.md §6 | Moved |
| §5 "Current implementation requires one serialized task/system-context owner...ISR code must defer...synchronization processing in task context" | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — task context ownership and ISR handling are implementation |
| §6 Integration notes: one-way transaction point (SPI_CONTRACT.md), offset stepping approved, signed offset range bounds | Karetao (references) | TIME_SYSTEM_INTERFACE.md (§3 one-way note, §4 offset stepping) | Moved (with reference to SPI_SYSTEM_INTERFACE.md); range bounds component |
| §6 "Host-visible timestamp quality must expose synchronized versus local-only data" | Karetao | TIME_SYSTEM_INTERFACE.md §4–5 | Moved (quality reporting requirement) |

### Summary of Disposition

**Moved to Karetao (TIME_SYSTEM_INTERFACE.md):**
- Time model: hub_time_us formula, Pi authority, monotonicity invariant
- Measurement vs. frame timestamp distinction and local-only marking
- TIME_SYNC transaction structure (pi_time_us, sync_seq, flags) and STM32 processing
- Required state (time_sync_valid, time_offset_us, sequence, local_time, age)
- Acceptance criteria: initial ±24-hour bound, runtime ±1-second step bound, sequence validation
- Direct offset step approved for v1; two-way RTT and slewing are future enhancements
- 5-second validity timeout, unsynchronized marking, quality reporting
- Motion inhibition while sync invalid
- Reset behavior: clears validity and offset
- Atomicity: readers see complete previous or new update
- One-way transaction-point estimate rationale (reference to SPI_SYSTEM_INTERFACE.md)

**Deliberately dropped (to component authority):**
- TIM2 implementation: 32-bit counter, 1 MHz clock, ~4,295 second wrap
- TimeService_NowUs() wrap detection mechanism and task context restriction
- AS5600 timestamp capture timing and sensor-specific timestamp migration
- Task synchronization model and ISR deferral pattern
- TimeService_SyncStateAccept/Get/Is* API and internal state management
- Signed offset range bounds and large-offset rejection limits (implementation)

---

## WP-3c: CAN System Interface (In Progress)

**Files processed:**
- `docs/project/firmware/CAN_SERVICE_CONTRACT.md` (133 lines) → split: Karetao system interface + component internals
- `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md` (48 lines) → verification reference; C-2 conflict documented

### `docs/project/firmware/CAN_SERVICE_CONTRACT.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble: Status, Owner, Boundary (CanService, MKS library separation) | Component / External | CAN_SYSTEM_INTERFACE.md §11 (MKS authority only) | Noted; service boundary component-internal |
| §1 Purpose: CAN transport, motor registration, polling, diagnostics | Karetao (observable behavior) | CAN_SYSTEM_INTERFACE.md | Moved (system-level semantics) |
| §1 "MKS library owns command encoding, checksum, decoding; does not own HAL/queues/retries" | External / Component | CAN_SYSTEM_INTERFACE.md §11 (MKS authority); component docs | Moved (MKS as external authority); HAL details component |
| §2 Public interface: Init, Activate, Process, RegisterMotor, command functions, response accessors, GetLatestMotorValues | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — API details |
| §3 Lifecycle states: UNCONFIGURED, INACTIVE, ACTIVE, ERROR; state transitions; motion gate | Karetao | CAN_SYSTEM_INTERFACE.md §8 | Moved |
| §3 "Normal motor commands permitted only while ACTIVE; enforced in CanService_TransmitFrame()" | Karetao | CAN_SYSTEM_INTERFACE.md §3 | Moved (system gate); implementation enforcement component |
| §3 "Emergency stop currently fail-closed...future safety review may authorize while ERROR" | Karetao | CAN_SYSTEM_INTERFACE.md §3 | Moved verbatim (future exception caveat preserved) |
| §4 Configuration: 11-bit IDs, CAN_BIT_TIMING_EVIDENCE reference, max motor ID 0x7FF, motor indices 0–7, eight-motor capacity, filter accepts all IDs, registered ID determines decode | Karetao / Verification | CAN_SYSTEM_INTERFACE.md §1 (11-bit, capacity); §6 (uniqueness); CAN_INTEGRATION_EVIDENCE.md (bitrate) | Moved config to interface; bitrate conflict documented in verification |
| §4 "Duplicate IDs not currently rejected...must be rejected before production" | Karetao / Component | CAN_SYSTEM_INTERFACE.md §2 (requirement); component (enforcement) | Moved requirement; enforcement component |
| §5 TX: CanTx_Queue bounded, priority ordered (SAFETY, MOTION, POLL), FIFO within priority | Karetao | CAN_SYSTEM_INTERFACE.md §4 | Moved |
| §5 TX: frames encoded to fixed MksCanFrame, eight-entry queue, Process() drains one/pass, HAL retry three times, queue-full increments diagnostic, payloads copied to eight-byte buffer | Component / Karetao (retry bound, queue semantics visible) | Karetao: CAN_SYSTEM_INTERFACE.md §4 (priority, three-retry bound, queue-full behavior); Component: queue internals | Moved observable semantics; implementation details component |
| §6 RX: drain FIFO until empty, discard DLC > 8, ignore unregistered IDs, pass to mks_decode, replace per-motor response, decode failure increments counter, successful decode updates latest-value with feedback/timestamp/quality/diagnostics | Karetao | CAN_SYSTEM_INTERFACE.md §4 (RX semantics) §6 (latest-value cache) | Moved |
| §6 "RX overflow counters and recovery not yet implemented" | Verification (open gate) | CAN_INTEGRATION_EVIDENCE.md (integration blockers) | Referenced as open gate; implementation gap |
| §7 Polling: 20 ms default, round-robin motors, alternate encoder/realtime requests, period zero disables, shared HAL path with commands | Karetao / Component | CAN_SYSTEM_INTERFACE.md §7 (observable behavior); Component (scheduler internals) | Moved observable semantics; scheduler component |
| §8 Required production decisions (1–7): retry delay, RX overflow, duplicate IDs, polling period, HAL error mapping, emergency stop, bitrate/sample-point | Karetao / Verification | CAN_SYSTEM_INTERFACE.md (lifestyle, duplicate ID uniqueness, emergency stop); CAN_INTEGRATION_EVIDENCE.md (blockers) | Noted in integration gates |
| §9 Bus-off policy: check HAL_CAN_ERROR_BOF in task context, stop CAN, inhibit queue draining, escalating recovery (100 ms–1 s), three events in 60 s enter ERROR, successful restart → INACTIVE, only CanService_Activate() resumes | Karetao | CAN_SYSTEM_INTERFACE.md §5 | Moved verbatim |
| §9 "HAL error behavior, stop/start timing, controller/transceiver recovery...remain integration gates" | Verification | CAN_INTEGRATION_EVIDENCE.md (integration blockers) | Referenced as gate |
| §10 Diagnostics: lifecycle, per-motor RX decode successes/failures, TX successes/HAL failures/queue drops, RX overflow, bus-off count, poll health, last response timestamp | Karetao | CAN_SYSTEM_INTERFACE.md §9 | Moved |
| §10 "Counters task-owned; ISR callbacks record minimal flags and defer to task context" | Karetao / Component | CAN_SYSTEM_INTERFACE.md §10 (timing/concurrency); Component (ISR implementation) | Moved concurrency model; ISR details component |
| §10 "Timestamps use 64-bit monotonic extension from TIM2, never HAL_GetTick()" | Karetao | CAN_SYSTEM_INTERFACE.md §9 | Moved (timestamp domain requirement) |
| §11 Latest-value cache: Motor_LatestValue per motor, carries identity/CAN-ID/feedback/timestamp/quality/validity/counters; Snapshot Builder reads and copies; must not mutate or write SPI buffer | Karetao | CAN_SYSTEM_INTERFACE.md §6 | Moved |
| §12 Timing and concurrency: Process() from task context, lifecycle/recovery/queue from task, no ISR mutations, bounded processing, multiple-task commands need mutex | Karetao | CAN_SYSTEM_INTERFACE.md §10 | Moved |
| §13 Verification requirements (7 items covering modal behavior, decode, unknown IDs, malformed frames, polling, bus-off, queue) | Verification | CAN_INTEGRATION_EVIDENCE.md or SYSTEM_VERIFICATION_MATRIX.md | Not migrated as document; covered in verification strategy |

### `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md`

| Statement | Classification | Destination | Disposition |
|---|---|---|---|
| Entire document (48 lines): Status "engineering calculation; not hardware validation", current 875 kbps config, candidate 1 Mbps calculation, provisional bus-load estimate, integration blockers | Verification (evidence) | CAN_INTEGRATION_EVIDENCE.md | **Moved and documented as evidence, not requirement** |
| Current configuration: 42 MHz PCLK1, prescaler 16, BS1/BS2/SJW all 1 TQ, 875 kbps, 66.7% sample point | Verification / Implementation gap | CAN_INTEGRATION_EVIDENCE.md (C-2 conflict: 1 Mbps required, 875 kbps implemented) | Documented as open implementation gap; flagged as C-2 conflict |
| Candidate 1 Mbps: prescaler 3, BS1 11, BS2 2, SJW 1, 85.7% sample point | Verification (candidate) | CAN_INTEGRATION_EVIDENCE.md | Recorded as candidate; **not approved**; marked for future CubeMX integration |
| Bus-load estimate: 111–130 bits/frame, 1.3% load (single motor), 31.2% load (eight motors 100 Hz) | Verification | CAN_INTEGRATION_EVIDENCE.md (provisional estimate) | Recorded as provisional; neither is a validated worst case |
| Integration blockers: 8 items covering MKS model, transceiver, topology, timing, and logic-analyzer evidence | Verification (open gates) | CAN_INTEGRATION_EVIDENCE.md (blockers section) | Moved and marked as blocker list |
| "Target bitrate, candidate timing, load estimates are integration gates; do not validate physical network or authorize motion" | Verification (caveat) | CAN_INTEGRATION_EVIDENCE.md | Moved verbatim (non-validation caveat preserved) |

### Summary of Disposition

**Moved to Karetao (CAN_SYSTEM_INTERFACE.md):**
- CAN configuration: 11-bit IDs, motor capacity, ID uniqueness requirement
- Motor command lifecycle gating: ACTIVE-only transmission with state validation
- Emergency stop exception caveat (future safety review)
- TX queue semantics: priority ordering (SAFETY, MOTION, POLL), three-retry bound, queue-full behavior, frame ordering
- RX semantics: frame validation, unregistered ID ignoring, decode error handling, latest-value update atomicity
- Bus-off policy: detection, escalating recovery (100 ms–1 s), three-event escalation to ERROR, explicit reactivation requirement
- Latest-value cache: freshness, staleness on decode failure, Snapshot Builder read-only access
- Polling: 20 ms default, round-robin, alternating request types, period-zero disable
- Diagnostics: 8 counters (RX/TX/bus-off/poll/overflow/decode)
- Timing/concurrency: task context ownership, no ISR mutations, 64-bit monotonic timestamp requirement
- MKS as external authority: command encoding, checksum, response decoding (not restated)

**Deliberately dropped (to component authority):**
- CanService API: Init, Activate, Process, RegisterMotor, command functions, response accessors
- Queue implementation, HAL integration, priority scheduling
- Polling scheduler: round-robin mechanics, request alternation
- Per-motor response cache structure and update mechanics
- ISR handler implementation (deferral pattern only mentioned in concurrency)
- RX FIFO overflow implementation (marked as not-yet-implemented)
- Task synchronization specifics

**Deliberately dropped (to verification authority):**
- CAN_BIT_TIMING_EVIDENCE.md: entire file, recorded as engineering calculation evidence
- C-2 conflict: 1 Mbps requirement vs. 875 kbps implementation, documented as open gate
- Candidate 1 Mbps configuration: recorded but not approved
- 8 integration blockers: bus-off recovery, physical topology, logic-analyzer evidence, etc.

**Notes on external authority:**
- MKS controller protocol, command encoding, checksum, response format, feedback rate all remain external authority
- Document references MKS requirements; does not restate vendor specifications

---

## WP-4: Build out `01_SYSTEM/` and `06_CONFIGURATION/` (In Progress)

**Files processed:**
- `docs/project/firmware/LIFECYCLE_CONTRACT.md` (240 lines) → Karetao
- `docs/project/firmware/ERROR_HANDLING_STRATEGY.md` (68 lines) → Karetao
- `docs/project/firmware/JOINT_MAPPING_CONTRACT.md` (28 lines) → Karetao/Configuration
- `docs/project/firmware/CALIBRATION_CONTRACT.md` (30 lines) → Karetao/Configuration
- `docs/project/firmware/APP_OVERVIEW.md` (8 lines) → Karetao (rewrite)
- `docs/project/system/architecture.md` (110 lines) → Karetao
- `docs/project/firmware/CONTRACT_V1_FREEZE.md` (209 lines) → Archive with header

### `docs/project/firmware/LIFECYCLE_CONTRACT.md`

| Section | Classification | Destination | Disposition |
|---|---|---|---|
| §1 Purpose and vocabulary | Karetao | SYSTEM_LIFECYCLE.md preamble | Moved |
| §2 Canonical states (UNCONFIGURED, INACTIVE, ACTIVE, ERROR) | Karetao | SYSTEM_LIFECYCLE.md §1 | Moved |
| §2 "Implementation states remain local" | Karetao | SYSTEM_LIFECYCLE.md §1 | Moved verbatim |
| §3 Transition model with diagram and semantics | Karetao | SYSTEM_LIFECYCLE.md §2 | Moved |
| §3 "recover always ends INACTIVE; shutdown is safety operation" | Karetao | SYSTEM_LIFECYCLE.md §2 | Moved verbatim |
| §4 Fault convention (INFORMATIONAL/DEGRADED/FAULT/SAFETY_CRITICAL) | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved |
| §4 "not a PL/SIL mapping or formal machine safety rating" | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved verbatim (caveat preserved) |
| §4 Fault classes (transient/persistent/fatal/configuration) | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved |
| §5 Subsystem mapping table | Karetao | SYSTEM_LIFECYCLE.md §6 | Moved |
| §6 Dependency rules and graph | Karetao | SYSTEM_LIFECYCLE.md §7 | Moved |
| §7 Startup and shutdown sequence diagrams | Karetao | SYSTEM_LIFECYCLE.md §8 | Moved |
| §7 "CubeMX is hardware initialization, not configure; lifecycle recovery != task recovery" | Karetao | SYSTEM_LIFECYCLE.md §8 | Moved verbatim (semantic distinction preserved) |
| §8 C11 API pattern and principles | Component | SYSTEM_LIFECYCLE.md §10 (structure), Arm_Sensor_Hub docs (implementation) | Moved structure/principles; implementation component |
| §9 Lifecycle contract template (25 items) | Karetao (structure) | SYSTEM_LIFECYCLE.md §10 | Noted as guidance; individual service contracts own their items |
| §10–13 Initial interface contracts (I2C, CAN, SPI, Sensor, Motor, HealthMonitor) | Component (mostly) | SYSTEM_LIFECYCLE.md §6 (subsystem mapping only); service contracts elsewhere | Moved system-visible lifecycle states; service-specific details component |
| §14 RTOS and timing rules | Karetao / Component | SYSTEM_LIFECYCLE.md §8 (timing rules); Component (implementation) | Moved rules; implementation component |
| §15 Validation matrix (automated tests) | Verification | Not migrated at this stage | Implementation gate; reference for test strategy |

### `docs/project/firmware/ERROR_HANDLING_STRATEGY.md`

| Section | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble and purpose | Karetao | SYSTEM_LIFECYCLE.md preamble | Contextual; integrated |
| §1 Firmware response levels (INFORMATIONAL/DEGRADED/FAULT/SAFETY_CRITICAL) | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved (already in LIFECYCLE_CONTRACT; reinforced) |
| §1 "not a PL/SIL mapping..." caveat | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved verbatim |
| §2 Fault classes (transient/persistent/fatal/configuration) | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved (already in LIFECYCLE_CONTRACT; reinforced) |
| §2 Fault diagnostics: subsystem, operation, code, timestamp, occurrence, state | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved |
| §2 Timestamp use (64-bit monotonic, Pi-synchronized quality) | Karetao | SYSTEM_LIFECYCLE.md §3 | Moved |
| §3 Ownership: service owns local retry; lifecycle owner decides state; HealthMonitor observes | Karetao | SYSTEM_LIFECYCLE.md §11 | Moved |
| §3 "ISR callbacks set minimal flags/counters; defer to task context" | Karetao | SYSTEM_LIFECYCLE.md §11 | Moved verbatim |
| §4 Escalation policy (classify → retry → reset → ERROR → INACTIVE → activate) | Karetao | SYSTEM_LIFECYCLE.md §4 | Moved |
| §4 "Thresholds remain per-service decisions" | Karetao | SYSTEM_LIFECYCLE.md §4 | Moved verbatim |
| §5 Safety outputs (CAN/Sensor/SPI inactive, motor fault, shutdown) | Karetao | SYSTEM_LIFECYCLE.md §9 | Moved |
| §5 "TIME_SYNC expiry: acquisition continues, motion inhibited, non-motion ops continue" | Karetao | SYSTEM_LIFECYCLE.md §5 | Moved verbatim |
| §6 Reporting: diagnostics internal first, then via SPI; explicit clear semantics | Karetao | SYSTEM_LIFECYCLE.md §11 | Moved |
| §7 Open decisions (fault codes, retry/escalation thresholds, recovery, watchdog, history, host clear) | Verification/Component | Not migrated as requirements | Noted as open integration decisions |

### `docs/project/firmware/JOINT_MAPPING_CONTRACT.md`

| Section | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble: Status, Owner, Boundary | Karetao | SYSTEM_CONFIGURATION.md §2 | Noted |
| §1 Mapping model: one-to-one joint/sensor/motor, schema v1 details | Karetao | SYSTEM_CONFIGURATION.md §2 | Moved |
| §1 "Schema v1 cannot represent differential, coupled, multi-motor joints...must not be encoded as multiple records...require new schema" | Karetao | SYSTEM_CONFIGURATION.md §2 | Moved verbatim (SYS-MECH-001 caveat preserved) |
| §2 Validation and activation | Karetao | SYSTEM_CONFIGURATION.md §2 | Moved |
| §2 "Current mapping reflects bring-up registration only; commissioning required before release" | Karetao | SYSTEM_CONFIGURATION.md §2 | Moved verbatim |
| §3 Consumer ownership (SensorTask, MotorService, Calibration) | Karetao | SYSTEM_CONFIGURATION.md §2 | Moved |
| §4 Open integration work (commission physical mapping, bind to calibration, define coupled schema) | Verification/Future | Not migrated as requirements | Noted as integration work |

### `docs/project/firmware/CALIBRATION_CONTRACT.md`

| Section | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble: Status, Owner, Boundary | Karetao | SYSTEM_CONFIGURATION.md §3 | Noted |
| §1 Ownership: offline computed, Pi/workstation, STM32 validates only | Karetao | SYSTEM_CONFIGURATION.md §3 | Moved |
| §2 Record model: schema, fields, CRC coverage | Karetao | SYSTEM_CONFIGURATION.md §3 | Moved |
| §3 Validation and selection rules (redundancy, modulo-32-bit ordering, CRC) | Karetao | SYSTEM_CONFIGURATION.md §3 | Moved |
| §3 "Do not select older/corrupted fallback record when validation fails" | Karetao | SYSTEM_CONFIGURATION.md §3 | Moved verbatim |
| §3 ActiveVersion reporting | Karetao | SYSTEM_CONFIGURATION.md §3 | Moved |
| §4 Open integration work (canonical serialization, flash layout, power-loss recovery, lifecycle binding) | Verification/Component | Not migrated as requirements | Noted as integration work |

### `docs/project/firmware/APP_OVERVIEW.md`

| Content | Classification | Destination | Disposition |
|---|---|---|---|
| "STM32 is a Sensor hub...collects sensor data from CAN and I2C...sends over SPI to Raspberry Pi" | Karetao | SYSTEM_OVERVIEW.md (rewritten at system scope) | Used as seed; rewritten to system scope |
| List of functions (collect encoders, skeleton CAN, timestamp, send SPI, DATA_READY) | Karetao | SYSTEM_OVERVIEW.md §2 (purpose and responsibilities) | Abstracted to system responsibilities |

### `docs/project/system/architecture.md`

| Section | Classification | Destination | Disposition |
|---|---|---|---|
| Preamble: Transitional status note | Context | Archived; noted in provenance | Noted (legacy was already marked transitional) |
| §1 Platform Layer (CubeMX, HAL, interrupts, FreeRTOS) | Component | SYSTEM_ARCHITECTURE.md startup flow (references only); Arm_Sensor_Hub docs (details) | Framework only; implementation component |
| §2 Application Layer modules (app_init, sensor_task, i2c_manager, can_service, spi_slave_service, time_service, snapshot_builder, health_monitor) | Karetao (names/responsibilities) | SYSTEM_ARCHITECTURE.md (implicit in data flow); component docs (details) | Moved responsibility mapping; implementation component |
| §3 Protocol Library Layer (MksServo C++17) | Component | Arm_Sensor_Hub docs | Not migrated; component integration detail |
| §4 Startup Flow (1–5 steps: HAL → RTOS → App_Init → tasks → kernel start → processing) | Karetao | SYSTEM_ARCHITECTURE.md §2 | Moved |
| §5 Data Flow (sensor path, motor/CAN path, host/SPI path, time sync path) | Karetao | SYSTEM_ARCHITECTURE.md §3 | Moved |
| §6 "What Is Mature Vs Emerging" (14 items) | Verification / Component | SYSTEM_OVERVIEW.md §3 (current status); implementation details component | Moved status summary to overview; details component |
| §7 "Files Interns Should Learn Early" (7 file references) | Component | Arm_Sensor_Hub docs | **Not migrated** — component-specific learning path |

### `docs/project/firmware/CONTRACT_V1_FREEZE.md`

| Section | Classification | Destination | Disposition |
|---|---|---|---|
| Entire document (209 lines) | Historical / Distributed | `99_ARCHIVE/SUPERSEDED/CONTRACT_V1_FREEZE.md` with archive header | **Moved and archived.** v1.0 decisions distributed into: SYSTEM_LIFECYCLE.md (lifecycle/startup), SPI_SYSTEM_INTERFACE.md (SPI/DATA_READY/CRC/frame), SPI_PAYLOAD_SCHEMA.md (schema), TIME_SYSTEM_INTERFACE.md (time model), CAN_SYSTEM_INTERFACE.md (CAN ownership), SYSTEM_CONFIGURATION.md (snapshot records, mapping, calibration), SYSTEM_ARCHITECTURE.md (startup order). Contract hierarchy diagram superseded by authority model. |
| C-1 conflict resolution (DATA_READY semantics) | Karetao / Historical | SPI_SYSTEM_INTERFACE.md §7 (armed-then-assert authoritative); archive header notes C-1 resolution | Armed-then-assert model from spi-contract.md §8 is authoritative; freeze document "staged-then-assert" wording superseded. |

### Summary of WP-4 Disposition

**Created:**
- `01_SYSTEM/SYSTEM_LIFECYCLE.md` (new, 280 lines) — Lifecycle vocabulary, state machine, fault handling, escalation, safety gates, subsystem mapping, dependency rules, startup/shutdown, ownership

**Updated:**
- `01_SYSTEM/SYSTEM_OVERVIEW.md` — Rewritten from 3-line placeholder to 40-line system overview
- `01_SYSTEM/SYSTEM_ARCHITECTURE.md` — Expanded with startup flow and data flow details (system-level only)
- `06_CONFIGURATION/SYSTEM_CONFIGURATION.md` — Expanded with joint mapping schema, calibration record model, and system time representation

**Archived:**
- `docs/project/firmware/CONTRACT_V1_FREEZE.md` → `99_ARCHIVE/SUPERSEDED/CONTRACT_V1_FREEZE.md` with archive header and superseding references

**Deliberately dropped (to component authority):**
- Lifecycle contract template details (25 items) — each service owns its contract
- Service-specific API and implementation (I2C_MANAGER_CONTRACT, CAN_SERVICE_CONTRACT, SPI_SERVICE_CONTRACT sections) — component authority
- C11 API implementation pattern — component internals
- Platform layer details (CubeMX, HAL, interrupts, FreeRTOS configuration) — component authority
- Application layer module implementation details (task scheduling, queue internals, codec specifics) — component authority
- Protocol Library Layer details (MksServo C++17 internals) — component/vendor authority
- Files for intern learning — component-specific training material

**Deliberately dropped (to verification authority):**
- Validation matrix and test cases — implementation gates
- "What Is Mature vs Emerging" detailed assessment — moved to SYSTEM_OVERVIEW.md as current status

**Caveats preserved verbatim:**
- "not a PL/SIL mapping or formal machine safety rating"
- "schema v1 cannot represent differential, coupled, or multi-motor joints"
- "thresholds and retry delays remain per-service contract decisions"
- "recover always ends INACTIVE; explicit activation required"
- "do not select older/corrupted fallback record when validation fails"
- "commissioning and validation required before energized-motion release"
- "firmware response levels define application behavior only"

---

## WP-5: Complete `03_COMPONENTS/` (In Progress)

**File processed:**
- `docs/project/hardware/arm-sensor-hub-baseline.md` (226 lines) → split: Karetao system-visible + component-internal

### `docs/project/hardware/arm-sensor-hub-baseline.md`

| Section | Classification | Destination | Disposition |
|---|---|---|---|
| § System Objective | Karetao | ARM_SENSOR_HUB.md §2 (System Responsibilities) | Moved (abstracted) |
| § Architecture Overview (platform/application/protocol layers) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — service architecture, implementation details |
| § Current Implementation Status (build, I2C path, CAN path, SPI path, health) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — implementation status and details |
| § Runtime Flow | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — execution architecture |
| § Open Work / Next Milestones | Verification / Component | (referenced via integration gates) | **Not migrated** — implementation roadmap |
| § API Reference: CAN Service functions | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — service API |
| § API Reference: Sensor Task diagnostics | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — diagnostic structure |
| § Expected SPI Data Contract | Karetao (referenced) | ARM_SENSOR_HUB.md (provenance) | **Referenced only** — full contract in SPI_SYSTEM_INTERFACE.md |
| § MCU: STM32F405RGT6, 8 MHz HSE, 168 MHz SYSCLK | Karetao | ARM_SENSOR_HUB.md §3 (Hardware Baseline) | Moved |
| § Clock tree: APB1 42 MHz (constrains CAN/SPI), APB2 84 MHz | Karetao | ARM_SENSOR_HUB.md §3 | Moved with caveat: "constrains CAN/SPI timing" |
| § Timing constraints: CAN 1 Mbps target, SPI 5 MHz ceiling, 46 ms sensor sweep | Karetao | ARM_SENSOR_HUB.md §3 | Moved with integration ceiling caveats |
| § SPI3 Pinout: PA15 (NSS), PC10 (SCK), PC11 (MISO), PC12 (MOSI) | Karetao | ARM_SENSOR_HUB.md §4 (SPI3) | Moved |
| § SPI3 hardware notes: slave mode, 8-bit, 2-line, hardware NSS, DMA1 streams | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — DMA and peripheral configuration |
| § I2C1 Pinout: PB6 (SCL), PB7 (SDA), 400 kHz fast mode | Karetao | ARM_SENSOR_HUB.md §3 (I2C1) | Moved |
| § CAN1 Pinout: PB8 (RX), PB9 (TX) | Karetao | ARM_SENSOR_HUB.md §3 (CAN1) | Moved |
| § CAN1 notes: ISO 11898-1, CubeMX configuration | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — peripheral and build details |
| § DATA_READY GPIO: PA8 (output, push-pull) | Karetao | ARM_SENSOR_HUB.md §3 (DATA_READY GPIO) | Moved |
| § SWD Debug pinout (PA13, PA14) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — debug/development pinout |
| § Clock pinout (PH0, PH1) | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — oscillator detail |
| § GPIO detail (PA8 DATA_READY) | Karetao (noted above) | — | Already moved |
| § Peripheral notes: FreeRTOS, DMA priorities, CAN mapping | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — implementation configuration |
| § Build: CMake presets and workflow | Component | Arm_Sensor_Hub/Documentation/ | **Not migrated** — build system |

### Summary of WP-5 Disposition

**Updated:**
- `03_COMPONENTS/ARM_SENSOR_HUB.md` — Expanded from 20-line stub to 90-line system-level component document

**System-visible content moved to Karetao:**
- MCU family (STM32F405RGT6), clock tree (HSE 8 MHz, SYSCLK 168 MHz, APB1 42 MHz, APB2 84 MHz)
- Timing constraints: CAN 1 Mbps target (integration ceiling), SPI 5 MHz maximum (integration ceiling), sensor sweep ~46 ms
- Interface pin assignments visible to other components:
  - I2C1: PB6 (SCL), PB7 (SDA), 400 kHz fast mode
  - CAN1: PB8 (RX), PB9 (TX), ISO 11898-1
  - SPI3: PA15 (NSS), PC10 (SCK), PC11 (MISO), PC12 (MOSI), slave mode 0, hardware NSS
  - DATA_READY: PA8, push-pull output, active high

**Deliberately dropped (to component authority):**
- Service architecture (I2CManager, CAN Service, SPI Slave Service, Sensor Task, Health Monitor)
- Firmware APIs and internal state machines
- DMA configuration (DMA1 Stream 0 RX, Stream 5 TX, priorities)
- FreeRTOS task structure and scheduling
- Build configuration (CMake presets, toolchain)
- Full peripheral pinout (SWD debug, clock oscillator)
- Diagnostic structures and testing details

**Authority boundary clarified:**
- Karetao owns system role, responsibilities, and interface contracts
- Karetao owns MCU family, clock tree, timing constraints, and interface pin assignments other components depend on
- Arm Sensor Hub owns service architecture, APIs, DMA/ISR handling, FreeRTOS, build system, full pinout, peripheral configuration

**Caveats preserved:**
- "5 MHz SPI maximum is integration ceiling pending target-system validation"
- "CAN 1 Mbps target is integration ceiling; current generated configuration produces 875 kbps (implementation gap)"
- "Sensor sweep ~46 ms full-axis scan time"

---

## WP-6: Component Documentation Directories (In Progress)

**Directories created:**
- `Arm_Sensor_Hub/Documentation/` with `README.md` (authority declaration)
- `RaspberryPi_Sensor_Hub/Documentation/` with `README.md` (authority declaration)

**Files moved to Arm_Sensor_Hub/Documentation/:**
- `docs/project/firmware/BUILD_CONTRACT.md` (73 lines) — C11/C++17 split, CMake presets, toolchain, HostTests
- `docs/project/firmware/I2C_MANAGER_CONTRACT.md` (69 lines) — I2C1 transfer serialization, HAL status mapping
- `docs/project/firmware/HEALTH_MONITOR_CONTRACT.md` (51 lines) — HealthMonitor internals, design target
- `docs/project/system/development.md` (115 lines) — Local build/test commands

**Files moved to RaspberryPi_Sensor_Hub/Documentation/:**
- `docs/project/operations/RASPBERRY_PI_BRINGUP_V0.1.md` (1,757 lines) — Pi 5 provisioning, imager, cloud-init, PREEMPT_RT, ROS 2 Jazzy, SPI enable

### Authority Declarations

Each component `README.md` includes:
- Component repository and name
- Component implementation documentation authority (what it owns)
- Karetao system authority (what Karetao owns, with SYS-* references only)
- Relevant external authorities (MKS, AS5600, TCA9548A, ROS 2, etc.)
- Verification traceability model (component evidence → system verification)
- Documentation structure guidelines

Both authority declarations explicitly state:
- "This directory does **not** define system requirements or redefine Karetao system contracts"
- Component references to Karetao use stable identifiers (SYS-*, SD-*) rather than copying requirement text
- System verification is owned by Karetao and recorded in `SYSTEM_VERIFICATION_MATRIX.md`

### Disposition of Moved Content

| File | Moved to | Classification | Notes |
|---|---|---|---|
| BUILD_CONTRACT.md | Arm_Sensor_Hub/Documentation/ | Component-internal | C11/C++17 toolchain, CMake presets, build configuration |
| I2C_MANAGER_CONTRACT.md | Arm_Sensor_Hub/Documentation/ | Component-internal | I2C service API, HAL integration, transfer serialization |
| HEALTH_MONITOR_CONTRACT.md | Arm_Sensor_Hub/Documentation/ | Component-internal | Health aggregation service, diagnostic snapshot |
| development.md | Arm_Sensor_Hub/Documentation/ | Component-internal | Build/test procedures for STM32 firmware |
| RASPBERRY_PI_BRINGUP_V0.1.md | RaspberryPi_Sensor_Hub/Documentation/ | Component-internal | Operational runbook: Pi provisioning, OS setup, ROS 2 install |

None of these files define system requirements. All are implementation-specific content correctly owned by components.

---

## WP-7: Archive Historical Content (In Progress)

**Directories created:**
- `99_ARCHIVE/CONVERSATIONS/` — Early-stage design conversations
- `99_ARCHIVE/SPRINTS/` — Sprint planning and completion reports
- `99_ARCHIVE/DECISIONS/` — System decision records and question inventories

**Files moved to 99_ARCHIVE/CONVERSATIONS/ (with headers):**
- CTO_DECISION_BRIEF.md (early decision narrative)
- CTO_DECISION_FINAL.md (CTO approval of v1 baseline; **marked as approval origin for SD-01–SD-25**)
- DeepSeek.md (AI-assisted design exploration)
- GPT.md (AI-assisted design exploration)
- InterAgent_Chat.md (multi-AI conversation record)
- 2026-09-08-spi-options-engineering-assessment.md (engineering analysis)

**Files moved to 99_ARCHIVE/SPRINTS/ (with headers):**
- Sprint_1_List.md (sprint planning, obsolete)
- Sprint_2_Readiness_Report.md (sprint completion report, obsolete)
- PHASE_1_FINAL_CLEARANCE_REPORT.md (test/validation result from Phase 1)

**Files moved to 99_ARCHIVE/SUPERSEDED/ (with headers):**
- CONTRACT_V1_FREEZE.md (already archived in WP-4 with expanded header)
- proposed_phase2.md (superseded proposal)
- RASPBERRY_PI_BRINGUP_V0.md (superseded by V0.1)
- First_Week_Guide.md (superseded onboarding)
- Project_Orientation.md (superseded onboarding)
- OnboardingDocs_README.md (superseded onboarding)

**Files moved to 99_ARCHIVE/DECISIONS/ (with headers):**
- SD/ directory (all 26 system decision files: SD-01.md through SD-26.md)
- SYSTEM_DECISIONS.md (decision summary, superseded by register)
- Open_Items_List.md (145-item question inventory; **specially marked: "canonical register" self-description is superseded**)
- system_TODO_List.md (obsolete TODO tracking)
- CONTRACT_STATUS.md (tracking record, obsolete)
- SAFETY_RELEASE_CHECKLIST.md (checklist for Phase 1, obsolete)

### Archive Headers

All moved files include a standardized archive header block stating:
- Archived date: 2026-09-20
- Historical status: Marked as non-normative
- Superseding document: Reference to current authoritative location in `Documentation/**`

Special notes:
- CTO_DECISION_FINAL.md explicitly states it is "the approval origin for SD-01–SD-25, not merely a conversation"
- Open_Items_List.md explicitly states its "canonical register" self-description is superseded by the current decision register
- CONTRACT_V1_FREEZE.md (from WP-4) explicitly lists all superseding documents and notes C-1 resolution

### Disposition Summary

| Category | Location | Volume | Content Type |
|---|---|---|---|
| Conversations | 99_ARCHIVE/CONVERSATIONS/ | 1,200 lines | Design exploration, AI-assisted analysis, approval decision |
| Sprints | 99_ARCHIVE/SPRINTS/ | ~300 lines | Sprint planning, completion reports, Phase 1 clearance |
| Superseded | 99_ARCHIVE/SUPERSEDED/ | ~1,100 lines | Obsolete proposals, onboarding material, earlier versions |
| Decisions | 99_ARCHIVE/DECISIONS/ | ~2,000 lines | System decisions (SD-01–26), question inventory, status tracking |

**Total archived:** ~4,600 lines of historical content

---

## Unresolved items

(none yet)

---

## Deliberately dropped statements

From WP-3a (see disposition table above for full list with reasons). Key exclusions:
- DMA mechanics, task synchronization, buffer pool ownership → Component authority
- STM32 ISR/callback internals, HAL usage → Component authority  
- Raspberry Pi software architecture (spi_bus.py, spi_protocol.py, spi_device.py) → Component authority
- Operational bring-up procedures → Component/Verification authority
- Test measurements and validation evidence → Verification authority

