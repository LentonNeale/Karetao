# CAN System Interface

**Scope:** Motor command and feedback transport between STM32 and MKS CAN controller.  
**Status:** Pre-freeze approval baseline

## Authority

This document defines the Karetao system-level CAN contract: bus semantics, lifecycle integration, and transport safety. The Arm Sensor Hub owns CanService implementation details (API, HAL integration, queue internals, polling scheduler). MKS documentation remains authoritative for external MKS controller protocol behavior—this document references MKS requirements without restating them.

---

## 1. CAN Configuration

- Identifier format: **standard 11-bit IDs**.
- Nominal bitrate target: **1 Mbps** for v1 (SD-05).
- Average measured bus load target: **<50–60%** (SD-05). This estimate is provisional pending controller model, firmware, command/response rate, and physical-layer evidence.
- Motor registration capacity: system target is eight motors; exceeding this capacity requires versioned change.
- Registered motor CAN IDs must be unique; duplicate registration must be rejected before production use.

**Note:** The current generated CAN configuration produces 875 kbps, not the 1 Mbps target. This is recorded as an implementation gap in the verification record (C-2). The candidate 1 Mbps configuration is calculated but not approved until controller and physical-layer validation is complete.

---

## 2. Joint, Sensor, and Motor Mapping

Logical joint, sensor, and motor/CAN-ID mappings are **deterministic and versioned** (SD-07), including:

- logical joint identity;
- sensor/axis association;
- motor CAN-ID association;
- direction convention;
- zero offset;
- transmission ratio;
- controller model and firmware version assumptions.

The mapping schema is fixed and validated at configuration time. Configuration mismatch must be detected and rejected.

---

## 3. Motor Command Lifecycle

Motor commands are permitted **only while CAN is `ACTIVE`** (SD-06).

The service enforces:
- lifecycle gate validation at transmission time;
- **system-level prerequisite note:** CAN `ACTIVE` is necessary but not sufficient for normal system motion; the proposed motion-permission gate may reject normal motion when other required prerequisites are invalid;
- rejection of commands while CAN is `UNCONFIGURED`, `INACTIVE`, or `ERROR`;
- explicit service reactivation as the only path to resume normal transmission after recovery.

Emergency-stop behavior is currently gated by the same lifecycle rule as other commands. A future safety review may authorize emergency stop during `ERROR` only when the HAL transport is demonstrably operational; that exception must not be assumed by callers.

---

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

**HAL transmission failures:** HAL errors retry the dequeued frame at most **three times** before incrementing a retry-exhausted diagnostic. Persistent transport faults may enter lifecycle `ERROR`.

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

---

## 5. Bus-Off Behavior

**Bus-off detection and recovery:**

The service checks for bus-off status in each process cycle. Upon detection:

1. Halt CAN transmission and inhibit normal queue draining.
2. Schedule recovery with escalating delay: 100 ms → 500 ms → 1 s.
3. Attempt HAL restart.
4. If successful, transition to `INACTIVE` (does not resume queue draining or motion).
5. Require explicit `CanService_Activate()` to clear the inhibit and resume transmission.

**Escalation to `ERROR`:** Three bus-off events within a 60-second rolling window enter lifecycle `ERROR`. This prevents unbounded recovery attempts and requires explicit service intervention.

**Safety:** Bus-off inhibition is the system's first line of defense against runaway CAN transport faults. A CAN failure affecting motion must be evaluated against the machine risk assessment; the scope (joint-level vs. whole-system) is left to risk analysis (SD-06).

---

## 6. Latest-Value Freshness and Snapshot Building

The CAN service owns a bounded latest-value cache for each registered motor. The cache stores:

- logical motor identity and CAN ID;
- latest decoded feedback payload (from MKS decoder);
- acquisition timestamp (64-bit monotonic);
- synchronization quality (`SYNCHRONIZED` or `UNSYNCHRONIZED`);
- validity flags (decode success, staleness, fault indicators);
- per-motor RX success and decode-error counters.

**Snapshot Builder access:** The Snapshot Builder may read the entire cache through a getter function and copy it into a separate serialization buffer. The Snapshot Builder must not write into the cache or into an SPI frame buffer.

**Freshness semantics:** A new successful decode updates the cache with fresh payload, timestamp, and quality. A failed decode marks the record stale without overwriting the last valid payload—allowing partial failures to be visible to diagnostics while keeping the last known state available.

---

## 7. Polling and Periodic Requests

The service maintains a **default polling period of 20 ms**, configurable to zero (disabled). Registered motors are polled round-robin, with each motor alternating between two poll types:

1. Encoder-value request
2. Realtime-speed request

Polling may be disabled (`period = 0`) for manual-command-only operation. Polling and manual commands currently share the same transmission path; concurrent callers must serialize at application level.

---

## 8. Lifecycle Integration

The service follows the system lifecycle state machine (SYSTEM_LIFECYCLE.md):

- **`UNCONFIGURED`**: no valid CAN configuration available; no transmission permitted.
- **`INACTIVE`**: CAN is configured but normal traffic is disabled.
- **`ACTIVE`**: normal TX, RX, and polling permitted.
- **`ERROR`**: transport cannot safely continue; motor commands are rejected; recovery is automatic with escalating delay; explicit reactivation required.

Motor commands are gated by lifecycle state at transmission time. Commands issued while not `ACTIVE` are rejected without modification to motor state.

---

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

---

## 10. Timing and Concurrency

- `CanService_Process()` runs from task context on each process cycle.
- Lifecycle mutation, recovery, and queue management run from task context only.
- Polling period is configurable; default 20 ms is a soft target and not a real-time guarantee.
- If multiple tasks issue commands concurrently, a mutex or single command-owner task is required.
- ISR handlers, if added later, shall record minimal flags and defer all lifecycle mutation, recovery, and queue processing to task context.

---

## 11. External Authority: MKS Controller

The MKS motor controller documentation defines:

- command encoding and checksum validation;
- response decoding and payload semantics;
- feedback frame format and timing;
- controller state machine and error codes;
- brake behavior and safety modes.

This contract references MKS requirements without restating them. Exact MKS controller model, firmware version, command/response lengths, and feedback rate are integration gates (SD-05).

---

## 12. Integration Gates

Before approving the CAN subsystem:

- Exact MKS controller model and firmware version.
- Command/response message lengths, encoding, and timing.
- Required polling frequency and command rate for safe operation.
- CAN transceiver part and signal levels.
- Physical bus topology, cable type/length, node count, termination, and grounding.
- Oscillator tolerance and sample-point margin.
- Measured bitrate, error counters, arbitration latency, and worst-case load under realistic traffic.
- Verified bxCAN bus-off recovery behavior.
- Logic-analyzer or CAN-analyzer evidence of stable operation through startup, host stalls, and fault recovery.

The target bitrate (1 Mbps), candidate timing calculation, bus-load estimates, and recovery strategy do not constitute hardware validation.

---

## Provenance

Reconciled from `docs/project/firmware/CAN_SERVICE_CONTRACT.md`. System-observable transport semantics, bus-off policy, lifecycle integration, and diagnostic requirements are Karetao-owned. CanService implementation details (API, queue internals, HAL integration, polling scheduler), task synchronization, and MKS decoder integration remain component authority. MKS controller semantics remain external authority.
