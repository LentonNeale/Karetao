# Time System Interface

**Scope:** Clock-synchronization contract between the Raspberry Pi (time authority, owner of the ClockSync model) and the STM32 (local monotonic clock only).  
**Status:** Pre-freeze approval baseline, revised for the Issue #12 clock-synchronization decisions ([`ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`](../../07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md)).

## Authority

This document defines the Karetao system-level time interface. Component repositories own implementation details: ISR capture, 64-bit counter extension, the ClockSync estimator, and task synchronization.

---

## 1. Time Model

The **Raspberry Pi is the system time authority.** The STM32 maintains a monotonic local clock only. It performs **no clock math**: it does not hold, apply or step a time offset.

```text
STM32 acquisition timestamp
        |
        v
STM32 local monotonic clock
        |
        v
ClockSync conversion model (Pi)  <---  SPI receive timestamps (observations)
        |
        v
synchronized measurement_timestamp_us
```

**Invariants:**
- STM32 local time is monotonic and is never reset or adjusted by synchronization.
- The STM32 exports acquisition timestamps as raw local time. The Pi-side ClockSync model converts them into the synchronized `measurement_timestamp_us` consumed by the estimator.
- The SPI receipt timestamp feeds the clock model. It never replaces the measurement acquisition timestamp.

---

## 2. Measurement, Frame and Exchange Timestamps

| Timestamp | Meaning | Ownership |
|---|---|---|
| `measurement_timestamp_us` | Acquisition instant, converted into the synchronized Pi time domain by ClockSync | Physical measurement record |
| `frame_time_us` | Frame assembly time (SPI); unchanged | Outer SPI frame (SPI_SYSTEM_INTERFACE.md) |
| `request_received_local_us` | STM32 local time at which the correlated request was received; a clock-sync observation | Versioned response payload extension |

These are three distinct fields. `frame_time_us` is not a measurement timestamp, and `request_received_local_us` is not an acquisition timestamp.

Until ClockSync is valid, converted timestamps must be marked unsynchronized. Consumers must not treat unsynchronized timestamps as valid.

---

## 3. Clock-Sync Observations

There is no separate periodic `TIME_SYNC` exchange and no `sync_seq`. **Every applicable SPI response contributes an observation:**

| Point | Definition |
|---|---|
| `T1` | Pi request send time (`monotonic_us()`). |
| `T2` | STM32 receipt: the **raw TIM2 counter captured in the SPI DMA-complete ISR**, extended to a 64-bit local timestamp in a separate, serialized **task-context** step. That extended value is carried as `request_received_local_us`. |
| `T4` | Pi response receipt time. |
| `T_pi_obs` | `(T1 + T4) / 2`, the Pi-side observation instant. |

- The existing Pi request `seq` is the exchange-correlation ID. STM32 and Pi sequence spaces are independent, but the Pi always initiates, so its `seq` is sufficient.
- `request_received_local_us` is added through a versioned payload extension on every response that contributes an observation. Diagnostic-only responses do not contribute.
- `TimeService_NowUs()` must not be called in the ISR, because it mutates wrap-extension state. `response_staged_us` must not be used as T2, because it occurs later than reception.
- The 32-bit wrap extension is guarded by a fixed, non-dynamic `counter_extension_gap_us` (currently 500 ms, to be reviewed once hardware characterization data exists). Recovery behaviour after a rejected extension gap is open.

---

## 4. Synchronization Validity and Rejection

ClockSync on the Pi estimates offset and frequency from accepted observations. It is the **single acceptance policy**.

- `ClockSync.is_valid()` governs timestamp-conversion validity and measurement usability, which feeds EKF acceptance.
- Synchronization becomes invalid **5 seconds** after the last accepted observation (SD-19).
- Implausible observations are **rejected without silent slew** (SD-21). The legacy drift-limit rejection (initial bound ±24 h, runtime step ±1 s) may remain temporarily as a secondary diagnostic check only. It must not modify ClockSync state or act as a second acceptance policy, and it is removed once ClockSync is hardware-validated.
- Diagnostics expose ClockSync state through DIAGNOSTIC v2 and a `GET_DIAGNOSTIC` request (see `SPI_PAYLOAD_SCHEMA.md`). The top-level `time_sync_valid` becomes a derived summary field.

**Open:** numeric ClockSync acceptance criteria, and field-by-field confirmation of the DIAGNOSTIC v2 content.

---

## 5. Motion Safety

Two independent signals apply (Issue #12 item 6):

- **STM32 link liveness (`link_stale`)** gates STM32 motion permission locally and fails closed. It is count-based. `missed_count` increments once per expected-message interval without an accepted, valid SPI message and resets on any accepted, valid message. It trips at `>= N_moving` while moving or `>= N_idle` while idle (`N_moving < N_idle`). Until those values are set, detection shall occur within **500 ms** (SYS-FAIL-001). `link_stale` is not derived from ClockSync quality.
- **ClockSync validity** does not itself drive motion permission. While it is invalid, acquisition and diagnostics continue, timestamps are marked `UNSYNCHRONIZED`, and **time-dependent motion is inhibited** through the motion-permission authority (SD-20).

An STM32 reset invalidates the ClockSync model. Timestamps remain unsynchronized until ClockSync is valid again.

---

## 6. Atomicity and Visibility

- The ISR-captured raw counter and its task-context 64-bit extension must be paired consistently with the response they describe.
- Pi-side ClockSync model updates and validity must be observable as one logical update. Timestamp conversions must never use a partially updated model.
- Diagnostics never expose torn updates.

---

## 7. System Requirements Summary

- Timestamp error target **≤ ±1 ms** (SD-18, SYS-SYNC-001).
- Every applicable SPI response is a clock-sync observation. The STM32 performs no clock math (SYS-SYNC-002).
- Invalid after **5 s** without an accepted observation (SYS-SYNC-002).
- Implausible observations are rejected by ClockSync without silent slew (SYS-SYNC-004).
- Reset invalidates ClockSync (SYS-SYNC-005).
- `link_stale` and `ClockSync.is_valid()` are independent (SYS-SYNC-006, SYS-FAIL-001).

---

## 8. Integration Obligations and Acceptance Gates

The system must explicitly define the set of time-dependent motion operations and ensure one motion-permission authority enforces the rule consistently. All timestamp consumers, especially the 500 Hz EKF, must respect ClockSync validity.

Acceptance uses two sequential gates (Issue #12 item 10):
- **Gate A (model characterized):** synthetic and integration tests show the ClockSync regression converges and behaves correctly.
- **Gate B (±1 ms validated):** a hardware-validated milestone against an independent reference, attempted only after Gate A passes.

Current exported measurement timestamps are **not yet** in the synchronized domain. Passing Gate A does not imply Gate B.

---

## Provenance

Originally reconciled from `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md`. The one-way `TIME_SYNC` transaction (`pi_time_us`/`sync_seq`/`flags`), STM32-held `time_offset_us`, and direct offset stepping were superseded on 2026-09-24 by the Issue #12 decisions. The superseded text is in Git history.
