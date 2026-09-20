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

