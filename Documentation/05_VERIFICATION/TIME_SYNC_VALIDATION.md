# TIME_SYNC System Validation Against Contracts

> **As-built evidence (2026-09-21).** This document records measurements against the *current* one-way TIME_SYNC implementation. That design is superseded by [Issue #12](../07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md) (2026-09-24): the STM32 performs no clock math, every SPI exchange is a ClockSync observation, and acceptance uses Gate A then Gate B. The evidence here stays valid for the current code and must be re-run once Issue #12 is implemented.
>
> **Status terms.** "VERIFIED" below means component-level evidence (code review or unit test) only. `SYSTEM_VERIFIED` is set only in `SYSTEM_VERIFICATION_MATRIX.md`.
>
> **Requirement IDs corrected (2026-09-25).** Drift and stability were previously labelled SYS-SYNC-003 and SYS-SYNC-005, and schema compliance was labelled SYS-SPI-003. Those IDs mean motion inhibit on sync loss, reset behaviour, and DATA_READY/polling respectively. Drift and stability are supporting measurements for SYS-SYNC-001, and schema compliance belongs to SYS-SPI-001.

## Authority

This document maps observed TIME_SYNC measurements and implementation evidence to system requirements defined in:
- `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` — SYS-SYNC-001/002/004, SYS-SPI-001/004, SYS-TIM-003
- `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` — time model and synchronization contract
- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` — SPI transaction semantics and DATA_READY contract
- `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` — TIME_SYNC payload structure

**Audit Date:** 2026-09-21  
**Scope:** Verification of timestamp error, synchronization frequency, offset drift, acceptance rate, and stability bounds against contract clauses and measured data.

---

## Mapping: Requirements → Measurements

### SYS-SYNC-001: Offset Accuracy Target
**Requirement (SYSTEM_REQUIREMENTS.md:31):**
> Timestamp error target shall be no more than ±1 ms relative to the shared STM32/Pi time model; synchronization validity and age shall be exposed.

**Measured Quantity:**
- `offset_us` — accepted candidate offsets from TIME_SYNC responses
- `offset_mean_us`, `offset_std_us` — mean and standard deviation of accepted offsets

**Source & Method:**
1. **spi_time_sync_probe.py** — sends repeated TIME_SYNC requests and records ACK/NACK responses
2. **time_sync_session.py:record_response()** — computes `offset_us = pi_time_us_stm32 - stm32_local_us` for each candidate
3. **time_sync_analysis.py:compute_stats()** — computes mean, std dev, min/max of accepted offsets
4. **time_sync_analysis.py:percentiles()** — computes p50 (median), p95 percentiles

**Acceptance Criterion:**
- p50 (median offset) within ±1000 µs
- p95 within ±2000 µs (allows for transient edge cases)
- offset_std_us < 500 µs (indicates stability within tighter bound)

**Current Status:** 
- **READY TO VERIFY** — measurement infrastructure in place
- Test data collected via spi_time_sync_probe.py can directly measure this
- **REMAINING:** Hardware measurements on Karetao system with actual STM32 clock source and Pi system clock

**Supporting Implementation:**
- STM32 firmware: `time_service.c:133–172` (CalculateOffset) — offset calculation implemented
- Pi host: `spi_time_sync_session.py:109–184` (record_response) — candidate offset tracking implemented

---

### SYS-SYNC-002: Synchronization Frequency
**Requirement (SYSTEM_REQUIREMENTS.md:32):**
> TIME_SYNC shall operate at 1 Hz nominal, configurable to 10 Hz; synchronization becomes invalid after five seconds without an accepted update.

**Measured Quantity:**
- Transaction interval (ms) — time between successive TIME_SYNC requests
- Validity timeout (seconds) — time from last accepted update to loss of synchronization

**Source & Method:**
1. **spi_time_sync_probe.py** — `--interval-ms` flag controls spacing between transactions (default 50 ms = 20 Hz)
2. **spi_time_sync_probe.py** — `--data-ready` flag enables DATA_READY-paced transactions
3. **time_sync_session.py** — session frequency determined by caller (probe or measurement harness)
4. **time_service.c:266–272** (TimeService_SyncStateRefresh) — implements 5-second validity timeout

**Acceptance Criterion:**
- Probe can be configured to run at 1 Hz (--interval-ms 1000) through 10 Hz (--interval-ms 100)
- Firmware implements exactly 5-second timeout in compile-time constant

**Current Status:**
- **CONFIGURABLE** — measurement harness supports all required frequencies
- Probe supports `--interval-ms` from 10 ms to any value, covering 1 Hz to 100 Hz range
- **VERIFIED (code review)** — firmware timeout constant: TIME_SERVICE_DEFAULT_VALIDITY_TIMEOUT_US = 5,000,000 µs
- **REMAINING:** Measure actual transaction frequency in production firmware during normal operation

**Supporting Implementation:**
- Pi host: `spi_time_sync_probe.py:45–46, 84–89` — configurable interval and DATA_READY pacing
- STM32 firmware: `time_service.h` line showing TIME_SERVICE_DEFAULT_VALIDITY_TIMEOUT_US = 5,000,000
- STM32 firmware: `time_service.c:266–272` (TimeService_SyncStateRefresh) — implements timeout check

---

### SYS-SYNC-001 (supporting): Offset Change Rate (Drift)
**Requirement (SYSTEM_REQUIREMENTS.md:33, 34):**
> When synchronization is invalid, acquisition and diagnostics shall continue but time-dependent motion shall be inhibited. Implausible time-offset updates shall be rejected without silent slew, using the approved wide-initial/narrow-runtime validation model.

**Interpreted Requirement (from TIME_SYSTEM_INTERFACE.md §4, SPI_SYSTEM_INTERFACE.md §12):**
- Initial offset acceptance bound: ±24 hours
- Runtime offset step bound: ±1 second per update
- Offset updates must use strictly newer sequence numbers

**Measured Quantity:**
- `drift_rate_us_per_sec` — mean offset change rate across multiple accepted updates
- Offset validation success rate — percentage of updates accepted vs. rejected

**Source & Method:**
1. **time_sync_analysis.py:compute_stats()** — lines 116–131 compute drift_rate_us_per_sec
   - Takes consecutive accepted offsets with timestamps
   - Computes mean rate of change (µs per second)
2. **time_sync_session.py:_is_within_drift_bounds()** — implements runtime step validation
3. **time_service.c:234–244** — implements sequence validation and step bound checking

**Acceptance Criterion:**
- `drift_rate_us_per_sec` < 10,000 µs/s (10 ms/s) — conservative margin on ±1 second/update bound
- System tuning targets 1,000 µs/s (±1 ms per sync) for smooth operation
- Rejection rate: implausible updates rejected (not silently slewed)

**Current Status:**
- **READY TO VERIFY** — drift tracking infrastructure in place
- Bounds implemented in firmware and validated in Python session tracking
- **VERIFIED (code review)** — firmware validates sequence and step bounds per TIME_SYSTEM_INTERFACE.md
- **REMAINING:** Long-term drift characterization (multiple hours/days) to validate thermal stability

**Supporting Implementation:**
- Pi host: `spi_time_sync_session.py:186–215` (_is_within_drift_bounds) — tracks drift limits
- Pi host: `spi_time_sync_analysis.py:116–131` — computes drift_rate_us_per_sec
- STM32 firmware: `time_service.c:234–244` — validates strictly newer sequence and step bounds
- STM32 firmware: `time_service.h` — TIME_SERVICE_DEFAULT_INITIAL_OFFSET_LIMIT_US, TIME_SERVICE_DEFAULT_RUNTIME_OFFSET_STEP_LIMIT_US

---

### SYS-SYNC-004: Acceptance Rate
**Requirement (implicit in SYSTEM_REQUIREMENTS.md:34, TIME_SYSTEM_INTERFACE.md §4):**
> Implausible time-offset updates shall be rejected without silent slew. System shall achieve high acceptance rate under normal operation.

**Measured Quantity:**
- `acceptance_rate` = accepted_count / total_attempts
- `nack_distribution` — histogram of rejection reasons

**Source & Method:**
1. **spi_time_sync_probe.py** — records all ACK and NACK responses
2. **time_sync_session.py:record_response()** — classifies each response as accepted (status_code==0) or rejected
3. **time_sync_analysis.py:compute_stats()** — lines 87–93 compute acceptance_rate and nack_distribution
4. **spi_protocol.py:NackReason** — decodes status codes to rejection reasons

**Acceptance Criterion:**
- acceptance_rate ≥ 0.90 (≥90%) — indicates robust synchronization under normal operation
- Rejection reasons logged and categorized (e.g., invalid sequence, drift exceeded, protocol error)

**Current Status:**
- **READY TO VERIFY** — acceptance tracking implemented end-to-end
- Probe collects statistics and computes acceptance rate automatically
- **REMAINING:** Run probe on Karetao hardware to measure actual acceptance rate during operation

**Supporting Implementation:**
- Pi host: `spi_time_sync_session.py:43–45` (is_accepted) — classifies candidate status
- Pi host: `spi_time_sync_analysis.py:87–137` (compute_stats) — computes acceptance metrics
- STM32 firmware: `spi_slave_service.c:325–365` (ProcessRequestFrame) — validates and ACKs/NACKs TIME_SYNC
- STM32 firmware: `time_service.c:239–244` — implements acceptance validation bounds

---

### SYS-SYNC-001 (supporting): Offset Stability
**Requirement (SYSTEM_REQUIREMENTS.md:35):**
> Reset shall clear synchronization validity and volatile offset; timestamps remain unsynchronized until a new TIME_SYNC update is accepted.

**Interpreted Requirement (from SYS-SYNC-001 and TIME_SYSTEM_INTERFACE.md §1):**
> Successive accepted offsets shall be stable and remain within the ±1 ms accuracy target bound.

**Measured Quantity:**
- `offset_std_us` — standard deviation of accepted offsets within a session
- `offset_min_us`, `offset_max_us` — minimum and maximum offsets
- Within-session variance as measure of jitter/stability

**Source & Method:**
1. **time_sync_session.py:candidates[]** — maintains complete history of all attempts
2. **time_sync_analysis.py:compute_stats()** — lines 96–106 compute offset statistics
3. **time_sync_analysis.py:percentiles()** — computes p5, p25, p50, p75, p95 to assess stability profile

**Acceptance Criterion:**
- `offset_std_us` < 500 µs (tighter than ±1 ms bound to detect anomalies)
- p95 - p5 < 2000 µs (90% of accepted offsets within 2 ms range)
- No discontinuous jumps > ±1 second between consecutive accepted updates

**Current Status:**
- **READY TO VERIFY** — stability metrics computed directly from measurement data
- Standard deviation and percentiles calculated from session candidates
- **REMAINING:** Run probe with 100+ transactions to establish baseline stability profile

**Supporting Implementation:**
- Pi host: `spi_time_sync_analysis.py:96–131` (compute_stats) — computes offset std dev and range
- Pi host: `spi_time_sync_analysis.py:155–199` (percentiles) — computes detailed percentile profile
- STM32 firmware: `time_service.c:249–254` (SyncStateAccept) — stores accepted offset without modification

---

### SYS-SPI-001: Request/Response Schema Compliance
**Requirement (SYSTEM_REQUIREMENTS.md:29):**
> DATA_READY may provide latency notification and polling shall provide recovery; polling is initially 1 ms and the Pi is SPI clock master.

**Verification Scope:**
> TIME_SYNC payload matches SPI_PAYLOAD_SCHEMA.md structure and byte layout.

**Measured Quantity:**
- None (compile-time verification)

**Source & Method:**
1. **Task 4 Unit Tests** — `Arm_Sensor_Hub/tests/host/protocol_test_main.c` validates byte offsets and sizes
2. **Unit Tests** — `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py` validates encoder/decoder round-trip
3. **Code Review** — byte-layout matches SPI_PAYLOAD_SCHEMA.md §TIME_SYNC definition

**Acceptance Criterion:**
- TIME_SYNC payload: schema_version (1B) + reserved (1B) + flags (2B) + pi_time_us (8B) + sync_seq (4B) = 16 bytes
- Byte offsets: 0/1/2–3/4–11/12–15 per SPI_PAYLOAD_SCHEMA.md
- Encoder produces exactly 16 bytes; decoder extracts all fields without error

**Current Status:**
- **VERIFIED (code review and unit tests)** — Task 4 confirmed byte-layout match with C firmware
- Protocol tests verify round-trip encoding/decoding
- **REMAINING:** None for v1 schema compliance

**Supporting Implementation:**
- STM32 firmware: `spi_protocol.c:100–123` (SpiProtocol_ParseTimeSyncRequest) — payload parsing
- Pi host: `spi_protocol.py:encode_time_sync_payload()` — payload encoding
- Tests: `protocol_test_main.c` and `test_spi_protocol.py` — schema validation

---

### SYS-SPI-004: Cable Propagation Delay
**Requirement (SYSTEM_REQUIREMENTS.md:30):**
> The SPI connection shall use a cable with a length of 20–30 cm. The implemented SPI link shall be tested over the specified cable length to measure link performance and verify that the link operates as required.

**Measured Quantity:**
- `data_ready_to_nss_*_us` — timing from DATA_READY GPIO assertion to NSS fall (cable propagation latency)
- Sustained transaction rates at 5 MHz clock
- Error rate and CRC failures on real cable

**Source & Method:**
1. **spi_time_sync_probe.py** — `--data-ready` flag enables GPIO monitoring
2. **data_ready_analysis.py** (future) — computes GPIO timing statistics from DATA_READY waveforms
3. **Hardware oscilloscope or logic analyzer** — captures timing relationships during actual transactions

**Acceptance Criterion:**
- `data_ready_to_nss_max_us` < 5000 µs (conservative upper bound for 30cm cable + margin at 170 ns/m propagation)
- Zero CRC errors over sustained 512-byte transaction sequences
- No frame loss or DMA abort/recovery events under normal operation

**Current Status:**
- **MEASURABLE (with GPIO instrumentation)** — probe can capture DATA_READY events if GPIO watcher implemented
- Basic transaction success logged in probe output
- **REMAINING:** Physical-layer measurement with oscilloscope or logic analyzer
- **REMAINING:** Measure actual GPIO timing during transactions
- **REMAINING:** Long-duration stress test (hours) on production cable length

**Supporting Implementation:**
- Pi host: `spi_time_sync_probe.py:47–50, 61–62, 85–89` — DATA_READY GPIO waiting
- Pi host: `data_ready.py` (future) — GPIO timing capture and analysis
- STM32 firmware: `spi_slave_service.c:40–82` (DATA_READY signal control) — GPIO assertion

---

### SYS-TIM-003: SPI Maximum Operating Point
**Requirement (SYSTEM_REQUIREMENTS.md:13):**
> SPI initial maximum operating point is 5 MHz pending live integration and physical-layer validation.

**Measured Quantity:**
- Achieved SPI clock frequency (Hz)
- CRC error rate and transaction success rate at operating frequency
- Frame corruption and retransmission rates

**Source & Method:**
1. **spi_time_sync_probe.py** — `--speed-hz` flag sets SPI clock (default 1 MHz, can test up to 5 MHz)
2. **spi_bus.py:SpiBusConfig** — configures kernel SPI driver frequency
3. **Probe output** — transaction success/failure rate and CRC validation

**Acceptance Criterion:**
- Zero CRC failures over 100+ consecutive transactions at 1 MHz (baseline)
- Transaction success rate ≥ 99% at operating frequency
- No frame loss or DMA corruption at target frequency

**Current Status:**
- **READY TO TEST** — probe supports configurable clock speed
- Default 1 MHz baseline has been tested in bench validation
- **REMAINING:** Sustained 5 MHz test on Karetao integration
- **REMAINING:** Temperature and noise stress testing at 5 MHz limit
- **REMAINING:** Power-supply margin validation at 5 MHz

**Supporting Implementation:**
- Pi host: `spi_time_sync_probe.py:39–42` — configurable speed parameter
- Pi host: `spi_bus.py:SpiBusConfig` — SPI driver configuration
- STM32 firmware: `main.c:MX_SPI3_Init()` — SPI3 configuration for slave operation

---

## Summary Table

| Requirement | Category | Evidence Source | Verification Status | Acceptance Criterion | Remaining Work |
|---|---|---|---|---|---|
| **SYS-SYNC-001** | Offset Accuracy | spi_time_sync_probe.py + time_sync_analysis.py + SWD readout | READY TO VERIFY | offset p50 ≤ ±1000 µs, p95 ≤ ±2000 µs, std < 500 µs | Hardware measurement on Karetao (SWD correlation per SWD_READOUT_PROCEDURES.md) |
| **SYS-SYNC-002** | Frequency | spi_time_sync_probe.py configurable interval + firmware timeout | CONFIGURABLE + COMPONENT EVIDENCE (as-built; requirement modified by Issue #12) | 1–10 Hz configurable, 5 s timeout in code | Measure actual production frequency |
| **SYS-SYNC-001 (supporting)** | Drift Rate | time_sync_analysis.py:drift_rate_us_per_sec + firmware bounds | READY TO VERIFY | drift < 10,000 µs/s, runtime bound ±1 s | Long-term (hours/days) drift measurement |
| **SYS-SYNC-004** | Acceptance Rate | time_sync_analysis.py:acceptance_rate + spi_slave_service.c validation | READY TO VERIFY | acceptance_rate ≥ 0.90 (≥90%) | Run probe on Karetao hardware |
| **SYS-SYNC-001 (supporting)** | Stability | time_sync_analysis.py:offset_std_us + percentiles | READY TO VERIFY | offset_std < 500 µs, p95–p5 < 2000 µs | Run 100+ transaction session |
| **SYS-SPI-001** | Schema Compliance | Task 4 unit tests + code review | COMPONENT EVIDENCE | 16-byte payload, correct offsets | None (v1 schema stable) |
| **SYS-SPI-004** | Cable Delay | data_ready_analysis.py (future) + hardware measurement | MEASURABLE | dr_to_nss_max < 5000 µs, zero CRC errors | Oscilloscope measurement, stress test |
| **SYS-TIM-003** | SPI Clock | spi_time_sync_probe.py:--speed-hz + transaction logging | READY TO TEST | 0 CRC failures at 1 MHz, success ≥ 99% | 5 MHz sustained test, thermal/EMI stress |

---

## Audit Status Summary

### COMPONENT EVIDENCE (code review / unit tests; not SYSTEM_VERIFIED)
- **SYS-SYNC-002:** 5-second timeout configured in firmware; 1–10 Hz range supported by probe
- **SYS-SPI-001:** TIME_SYNC payload schema matches specification; unit tests confirm byte layout

### READY TO VERIFY (infrastructure in place; measurements ready to run)
- **SYS-SYNC-001:** Offset accuracy measurement via probe statistics
- **SYS-SYNC-001 (supporting):** Drift rate and validation bounds via time_sync_analysis.py and firmware validation
- **SYS-SYNC-004:** Acceptance rate via NACKs and ACK tracking
- **SYS-SYNC-001 (supporting):** Stability (std dev, percentiles) from session data
- **SYS-TIM-003:** CRC error rate and success rate via probe at configurable clock speed

### MEASURABLE (requires additional hardware instrumentation)
- **SYS-SPI-004:** Cable propagation delay requires oscilloscope/logic analyzer or GPIO timing capture

### INTEGRATION BLOCKERS (must resolve before moving to Task 11)
1. **Gap in TIME_SYNC implementation** (from TIME_SYNC_CHARACTERISATION_EVIDENCE.md):
   - Gap 5: Raspberry Pi has no TIME_SYNC encoder/sender — `spi_device.py` lacks `time_sync()` method
   - Must implement encoder in `spi_protocol.py` and sender in `spi_device.py` to establish synchronization
2. **Missing offset export** (Gap 4):
   - Accepted `time_offset_us` not carried in SPI payload; Pi cannot verify STM32 acceptance
   - Blocking validation of SYS-SYNC-001 accuracy on real hardware
3. **Timestamp domain mismatch** (Gaps 1–2):
   - `frame_time_us` and `measurement_timestamp_us` exported as raw local time, not hub time
   - Timestamps exported by STM32 cannot be correlated to Pi clock until these are fixed

---

## Cross-Reference: Validation vs. Implementation Gaps

The TIME_SYNC_CHARACTERISATION_EVIDENCE.md audit identified 5 implementation gaps. This validation mapping shows how those gaps affect requirement verification:

| Gap | Requirement Impact | Status in This Audit |
|---|---|---|
| **Gap 1:** frame_time_us uses raw local time | SYS-SYNC-001 (cannot correlate timing) | BLOCKS FIELD VERIFICATION |
| **Gap 2:** measurement_timestamp_us exported raw | SYS-SYNC-001 (host timestamps are unsynchronized) | BLOCKS FIELD VERIFICATION |
| **Gap 3:** DIAGNOSTIC message not implemented | SYS-SYNC-001 (cannot query sync_valid from host) | BLOCKS ONLINE VALIDATION |
| **Gap 4:** Offset not exported in payload | SYS-SYNC-001 (Pi cannot verify offset acceptance) | BLOCKS ACCEPTANCE VERIFICATION |
| **Gap 5:** Pi has no TIME_SYNC sender | SYS-SYNC-002, SYS-SYNC-001 (cannot initiate sync) | **CRITICAL BLOCKER** — no synchronization possible |

**Blocking order:**
1. **First:** Close Gap 5 (implement Pi TIME_SYNC sender) — enables basic synchronization
2. **Second:** Close Gaps 1–2 (apply offset to timestamps) — enables Hub time domain usage
3. **Third:** Close Gap 3 (implement DIAGNOSTIC) — enables online sync validity monitoring
4. **Fourth:** Close Gap 4 (export offset) — enables independent verification of Pi/STM32 agreement

---

## Next Steps: Task 11 (SWD Instrumentation)

Task 11 will add software debugging (SWD) instrumentation to verify:

1. **TIM2 counter value and prescaler:** Confirm STM32 local clock runs at 1.0120 MHz (TIM2 prescaler = 83 at 84 MHz core)
2. **Actual accepted offset:** Mirror `time_offset_us` register to debug output to verify Pi and STM32 agree
3. **Timestamp application:** Verify STM32 applies offset to measurement timestamps before export
4. **Synchronization state transitions:** Trace acceptance and rejection of TIME_SYNC updates in real time

These measurements will complete the as-built validation of SYS-SYNC-001, -002 and -004 after the implementation gaps are closed.

---

## SWD Readout Integration

To complete the measurement loop and transition from "verified by probe" to "validated on hardware":

1. Build firmware with DEBUG=1: `make DEBUG=1`
2. Flash to STM32 and attach SWD debugger (ST-Link V2)
3. Run Pi probe: `python -m tools.spi_time_sync_probe --output probe_log.csv`
4. Halt firmware via OpenOCD and extract debug mirrors (see [Arm_Sensor_Hub/Documentation/SWD_READOUT_PROCEDURES.md](../../Arm_Sensor_Hub/Documentation/SWD_READOUT_PROCEDURES.md))
5. Correlate: For each probe measurement, read STM32 local_capture_us and verify offset = pi_time_us - local_capture_us
6. Report: Document any discrepancies > 100 µs as potential gaps

This closes the measurement loop and provides authoritative proof that TIME_SYNC offset calculation is correct on actual hardware.

---

## Provenance

**Authority documents:**
- SYSTEM_REQUIREMENTS.md (lines 13, 29–35)
- TIME_SYSTEM_INTERFACE.md (§1–7)
- SPI_SYSTEM_INTERFACE.md (§3, §11–12)
- SPI_PAYLOAD_SCHEMA.md (§TIME_SYNC, §ACK/NACK)

**Evidence sources:**
- spi_time_sync_probe.py (measurement harness)
- time_sync_session.py (offset tracking)
- time_sync_analysis.py (statistics computation)
- Arm_Sensor_Hub/App/Src/time_service.c, spi_protocol.c, spi_slave_service.c (STM32 firmware)
- RaspberryPi_Sensor_Hub/src/spi/ (Python protocol implementation)

**Related audit documents:**
- TIME_SYNC_CHARACTERISATION_EVIDENCE.md (implementation gap audit)
- Arm_Sensor_Hub/Documentation/TIME_SYNC_INSTRUMENTATION.md (firmware instrumentation guide)
