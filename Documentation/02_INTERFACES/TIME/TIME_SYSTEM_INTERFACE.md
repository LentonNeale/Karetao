# Time System Interface

**Scope:** Synchronization contract between Raspberry Pi (time authority) and STM32 (synchronized time consumer).  
**Status:** Pre-freeze approval baseline

## Authority

This document defines the Karetao system-level time interface. Component repositories own TIME_SYNC service implementation details, timestamp capture mechanics, and task synchronization.

---

## 1. Time Model

The **Raspberry Pi is the system time authority.** The STM32 maintains a monotonic local clock and does not reset that clock during synchronization.

```text
hub_time_us = local_time_us + time_offset_us
time_offset_us = pi_time_us - stm32_capture_time_us
```

**Invariants:**
- STM32 local time is monotonic and is never reset by synchronization.
- Exported timestamps use local time plus the current accepted offset.
- Measurement timestamps represent acquisition time, not transport or frame assembly time.

---

## 2. Measurement vs. Frame Timestamps

| Timestamp | Meaning | Ownership |
|---|---|---|
| `measurement_timestamp_us` | Acquisition time in the synchronized Pi time domain | Physical measurement record |
| `frame_time_us` | Frame assembly time (SPI) | Outer SPI frame (SPI_SYSTEM_INTERFACE.md) |

`frame_time_us` identifies frame assembly and is not a measurement timestamp. The measurement timestamp is captured immediately after the measurement bytes have been successfully received and decoded. It is not captured at transaction start or preparation time.

Until a synchronization is accepted, exported timestamps are **local-only** and must be marked unsynchronized. Consumers must not treat unsynchronized timestamps as valid.

---

## 3. TIME_SYNC Transaction

The Raspberry Pi sends `TIME_SYNC` through SPI with:

| Field | Type | Description |
| --- | --- | --- |
| `pi_time_us` | `uint64_t` | Pi time associated with the defined synchronization point. |
| `sync_seq` | `uint32_t` | Monotonic synchronization sequence. |
| `flags` | `uint16_t` | Synchronization/control flags. |

When the STM32 processes the validated message, it captures its local monotonic time `t_stm32` in task context and calculates:

```text
time_offset_us = pi_time_us - t_stm32
```

The STM32 stores and maintains:

```text
time_sync_valid         // bool: offset is synchronized
time_offset_us          // signed: current accepted offset
last_sync_sequence      // sequence of last accepted update
last_sync_local_time_us // local time of last accepted update
sync_age_us             // time since last accepted update
```

**Initial contract detail:** `pi_time_us` represents the Pi time associated with the synchronization transaction, including one-way transport uncertainty. This is a one-way transaction-point estimate (SPI_SYSTEM_INTERFACE.md § 11). A future two-way exchange may add Pi `t1`/`t3` and STM32 `t2` timestamps to estimate round-trip delay. That is a versioned enhancement, not a requirement for v1.

---

## 4. Synchronization Validity and Rejection

The v1 synchronization validity timeout is **5 seconds.** When the timeout expires:

```text
local monotonic clock continues
hub-time calculation continues
time_sync_valid = false
```

The STM32 must not claim synchronized timestamps while `time_sync_valid` is false. Status/diagnostic messages must expose synchronization validity, age since the last accepted update, and quality (`SYNCHRONIZED` or `UNSYNCHRONIZED`).

**Rejection criteria:** The initial accepted offset must be within a configurable initial bound (default ±24 hours). Later updates require:
- strictly newer sequence number;
- offset change within the configurable runtime step bound, initially ±1 second.

Rejected updates retain the previous accepted offset, sequence, local timestamp, and validity state for diagnostics. **Implausible updates are rejected without silent slew** (SD-21).

**Initial correction strategy:** The first implementation applies a direct offset step. `hub_time_us` is therefore permitted to jump when synchronization is updated. Two-way round-trip-time estimation and slewed correction are future versioned enhancements.

---

## 5. Motion Safety During Unsynchronization

Synchronization becomes invalid **5 seconds** after the last accepted TIME_SYNC update, or immediately after reset.

While synchronization is invalid (`time_sync_valid == false`):
- acquisition and diagnostics continue;
- timestamp quality must report `UNSYNCHRONIZED`;
- **time-dependent motion is inhibited** until a new accepted TIME_SYNC update restores validity (SD-20).

Reset clears synchronization validity and the volatile offset; timestamps remain marked unsynchronized until resynchronization. Only explicitly defined non-motion service operations may continue while synchronization is invalid.

---

## 6. Atomicity and Visibility

A synchronization update and its validity metadata must be committed as one logical update. Measurement readers (SPI service, diagnostic aggregators) must see either the previous complete update or the new complete update, never a partially written offset/validity pair.

The implementation must ensure that:
- offset and validity transitions are observable as atomic changes;
- timestamp readers see consistent offset/validity pairs;
- diagnostics never expose torn updates.

---

## 7. System Requirements Summary

- The shared STM32/Pi time model targets timestamp error **≤ ±1 ms** (SD-18).
- TIME_SYNC operates nominally at **1 Hz**, configurable to **10 Hz** (SD-19).
- Synchronization becomes invalid after **5 s** without an accepted update.
- While synchronization is invalid, motion is inhibited and quality is marked `UNSYNCHRONIZED`.
- Initial and runtime time-offset validation use distinct bounds.
- Reset clears synchronization validity and volatile offset.
- Implausible updates are rejected without silent slew.

---

## 8. Integration Obligations

The system must explicitly define the exact set of time-dependent motion operations and ensure one motion-permission authority enforces the rule consistently. All timestamp consumers (especially the 500 Hz EKF) must respect synchronization validity and reject unsynchronized records.

Validation of drift between synchronization updates and conformance of achieved timestamp error to the ±1 ms target remain required integration tasks. These depend on live system validation.

---

## Provenance

Reconciled from `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md`. Time model, TIME_SYNC transaction semantics, validity timeout, rejection criteria, motion safety rules, and atomicity requirements are system-owned. Component implementations of TIM2 counter wrap handling, TimeService_NowUs() mechanism, reader context restrictions, AS5600 timestamp migration, and task synchronization remain component authority.
