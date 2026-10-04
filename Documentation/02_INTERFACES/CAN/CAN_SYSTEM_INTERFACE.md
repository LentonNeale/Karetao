# CAN System Interface

**Scope:** Motor command and feedback transport between STM32 and MKS CAN controller. **Status:** Baseline; parameter values are Provisional (see `PARAMETER_REGISTER.md`)

## Authority

This document defines the Karetao system-level CAN contract: bus semantics, lifecycle integration, and transport safety. The Arm Sensor Hub owns CanService implementation details (API, HAL integration, queue internals, polling scheduler). MKS documentation remains authoritative for external MKS controller protocol behavior—this document references MKS requirements without restating them.

Tunable and physical values are referenced by PRM ID; their working values and bases are in [`PARAMETER_REGISTER.md`](../../06_CONFIGURATION/PARAMETER_REGISTER.md).

## 1. CAN Configuration

- Identifier format: **standard 11-bit IDs**.
- Nominal bitrate target: **PRM-CAN-01** for v1 (SD-05).
- Average measured bus load target: **PRM-CAN-04** (SD-05). This estimate is provisional pending controller model, firmware, command/response rate, and physical-layer evidence.
- Motor registration capacity: system target is eight motors; exceeding this capacity requires versioned change.
- Registered motor CAN IDs must be unique; duplicate registration must be rejected.

The generated configuration differs from the target; see PRM-CAN-01 and PRM-CAN-02 and [`CAN_INTEGRATION_EVIDENCE.md`](../../05_VERIFICATION/CAN_INTEGRATION_EVIDENCE.md).

## 2. Joint, Sensor, and Motor Mapping

The mapping is the commissioning table in [`SYSTEM_CONFIGURATION.md`](../../06_CONFIGURATION/SYSTEM_CONFIGURATION.md) §2.1, deterministic and versioned (SD-07, SYS-ENC-003). The motors registered there are the ones polled. "Six commissioned motors" is the charter target; one motor is registered today. Configuration mismatch must be detected and rejected.

## 3. Motor Command Lifecycle

Motor commands are permitted **only while CAN is `ACTIVE`** (SD-06).

The service enforces:
- lifecycle gate validation at transmission time;
- **system-level prerequisite note:** CAN `ACTIVE` is necessary but not sufficient for normal system motion; the motion gate (SYS-GATE-001, decided in the Sprint 4 run; see `ARCHITECTURE_DECISIONS.md`) may reject normal motion when other required prerequisites are invalid;
- rejection of commands while CAN is `UNCONFIGURED`, `INACTIVE`, or `ERROR`;
- explicit service reactivation as the only path to resume normal transmission after recovery.

Emergency-stop behavior is currently gated by the same lifecycle rule as other commands. A future safety review may authorize emergency stop during `ERROR` only when the HAL transport is demonstrably operational; that exception must not be relied on by callers.

## 4. Transport Semantics

### TX Queue and Priority

Outbound frames are enqueued in a bounded priority queue:

| Priority | Purpose | Envelope |
|---|---|---|
| `SAFETY` | Safety-critical commands | Highest priority, smallest envelope |
| `MOTION` | Normal motor commands | Medium priority |
| `POLL` | Polling requests (encoder value, realtime speed) | Lowest priority, largest envelope |

Frame ordering is FIFO within each priority band. Higher-priority frames defer lower-priority transmissions.

**Queue full:** Enqueue failures increment a queue-drop diagnostic counter. The frame is rejected without modification to motor state.

**HAL transmission failures:** HAL errors retry the dequeued frame at most **PRM-CAN-06** times before incrementing a retry-exhausted diagnostic. Persistent transport faults may enter lifecycle `ERROR`.

### RX Handling

- The service drains the RX FIFO until empty on each process cycle.
- Standard frames with data length code > 8 bytes are discarded.
- Frames from unregistered CAN IDs are silently ignored and do not modify motor state.
- Registered frames are passed to the MKS decoder (external authority).
- Successful decodes update the per-motor latest-value record:
  - decoded feedback payload (generic MKS fields);
  - acquisition timestamp (64-bit monotonic, synchronized domain);
  - synchronization quality flag (`SYNCHRONIZED` or `UNSYNCHRONIZED`);
  - RX success counter.
- Decode failures:
  - increment the per-motor decode-error counter;
  - mark the latest-value record stale without overwriting the last valid feedback payload.

## 5. Bus-Off Behavior

The service checks for bus-off status in each process cycle. Upon detection:

1. Halt CAN transmission and inhibit normal queue draining.
2. Schedule recovery with an escalating delay: it starts at the initial value, doubles after each failed recovery and is capped (PRM-CAN-07).
3. Attempt HAL restart.
4. If successful, transition to `INACTIVE` (does not resume queue draining or motion).
5. Require explicit `CanService_Activate()` to clear the inhibit and resume transmission.

**Escalation to `ERROR`:** Reaching the escalation threshold in PRM-CAN-08 enters lifecycle `ERROR`. This prevents unbounded recovery attempts and requires explicit service intervention.

**Safety:** Bus-off inhibition is the system's first line of defence against runaway CAN transport faults. The scope of a CAN failure (joint-level or whole-arm inhibit) is an open decision for Lenton Neale (SD-06).

## 6. Latest-Value Freshness and Snapshot Building

The CAN service owns a bounded latest-value cache per registered motor: logical motor identity and CAN ID; latest decoded feedback payload; acquisition timestamp (64-bit monotonic); synchronization quality (`SYNCHRONIZED` or `UNSYNCHRONIZED`); validity flags (decode success, staleness, fault indicators); and per-motor RX success and decode-error counters.

**Snapshot Builder access:** The Snapshot Builder may read the entire cache through a getter function and copy it into a separate serialization buffer. The Snapshot Builder must not write into the cache or into an SPI frame buffer.

**Freshness semantics:** A new successful decode updates the cache with fresh payload, timestamp, and quality. A failed decode marks the record stale without overwriting the last valid payload—allowing partial failures to be visible to diagnostics while keeping the last known state available. This is how SYS-MOT-001 and SYS-MOT-002 are met.

## 7. Polling and Periodic Requests

The service maintains a **default polling period of PRM-CAN-05**, configurable to zero (disabled). Registered motors are polled round-robin, each alternating between two poll types: encoder-value request, then realtime-speed request.

Polling may be disabled (`period = 0`) for manual-command-only operation. Polling and manual commands currently share the same transmission path; concurrent callers must serialize at application level.

## 8. Lifecycle Integration

The service follows the system lifecycle state machine (SYSTEM_LIFECYCLE.md):
- **`UNCONFIGURED`**: no valid CAN configuration available; no transmission permitted.
- **`INACTIVE`**: CAN is configured but normal traffic is disabled.
- **`ACTIVE`**: normal TX, RX, and polling permitted.
- **`ERROR`**: transport cannot safely continue; motor commands are rejected; recovery is automatic with escalating delay; explicit reactivation required.

## 9. Diagnostics

Minimum required diagnostics:
| Item | Meaning |
|---|---|
| Lifecycle state and last fault code | Service operational status |
| Per-motor RX decode successes and failures | Reception/decoding health |
| TX successes, HAL failures, queue-full failures | Transmission health |
| RX FIFO overflow count | Buffer exhaustion indicators |
| Bus-off event count and last recovery result | Bus fault history |
| Poll requests sent and poll responses received | Polling health |
| Last response timestamp and sequence/command code | Freshness and correlation tracking |

Counters are task-owned and updated in task context. Diagnostic and response timestamps use the shared 64-bit monotonic time extension (derived from TIM2), never `HAL_GetTick()` or raw 32-bit timer values.

## 10. Timing and Concurrency

- `CanService_Process()` runs from task context on each process cycle.
- Lifecycle mutation, recovery, and queue management run from task context only.
- Polling period is configurable; the default in PRM-CAN-05 is a soft target and not a real-time guarantee.
- If multiple tasks issue commands concurrently, a mutex or single command-owner task is required.
- Any future ISR handler records minimal flags and defers lifecycle mutation, recovery, and queue processing to task context.

## 11. External Authority: MKS Controller

The MKS motor controller documentation defines:

- command encoding and checksum validation;
- response decoding and payload semantics;
- feedback frame format and timing;
- controller state machine and error codes;
- brake behavior and safety modes.

This contract references MKS requirements without restating them. Exact MKS controller model, firmware version, command/response lengths, and feedback rate are open items (SD-05). The vendor reference summaries are in `icm-project/references/mks-servo42d-57d-can/`.

## 12. Verification

Verification: rows SYS-MOT-001, SYS-MOT-002 and the CAN interface row in `SYSTEM_VERIFICATION_MATRIX.md`; bitrate, load, topology and bus-off evidence are Stage 3 measurements (`PARAMETER_REGISTER.md`, Measurement stages).

The target bitrate (PRM-CAN-01), candidate timing calculation, bus-load estimates, and recovery strategy do not constitute hardware validation.

## Provenance

Reconciled from `docs/project/firmware/CAN_SERVICE_CONTRACT.md`. System-observable transport semantics, bus-off policy, lifecycle integration, and diagnostic requirements are Karetao-owned. CanService implementation details (API, queue internals, HAL integration, polling scheduler), task synchronization, and MKS decoder integration remain component authority. MKS controller semantics remain external authority.
