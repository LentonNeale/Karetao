# Timestamp Synchronization Contract

**Status:** Pre-freeze approval baseline  
**Owner:** System time service and SPI service  
**Boundary:** STM32 monotonic time -> Raspberry Pi time domain

## Time Model

The Raspberry Pi is the time authority. STM32 local time is monotonic and must never be reset by synchronization.

```text
hub_time_us = local_time_us + time_offset_us
time_offset_us = pi_time_us - stm32_capture_time_us
```

Physical measurements use `measurement_timestamp_us`. `frame_time_us` identifies frame assembly and is not a measurement timestamp.

## Current Source

`TimeService_Init()` starts TIM2 and binds the shared service to its 32-bit, 1 MHz free-running counter. `TimeService_NowUs()` extends counter wraps to a 64-bit local monotonic timestamp. TIM2 wraps after approximately 4,295 seconds.

The service detects a wrap when a newly sampled counter value is lower than the previous value and adds $2^{32}$ microseconds to the wrap base. Readers must execute from one serialized task/system context and sample at least once per TIM2 wrap interval; the first version does not provide ISR-safe or multi-reader synchronization. A hardware reset calls `TimeService_Init()` during application configuration, starts a new local-time epoch, and leaves synchronization invalid until Task 06 accepts a new update.

Existing AS5600 timestamps still use the raw TIM2 counter and are scheduled for migration with the latest-value record work. New long-lived I2C, CAN, SPI, and diagnostic timestamps must use `TimeService_NowUs()`.

The measurement timestamp is captured immediately after the AS5600 measurement bytes have been successfully received and decoded. It is not captured at mux selection or transaction start.

## TIME_SYNC

The Raspberry Pi sends `TIME_SYNC` through SPI with `pi_time_us`, `sync_seq`, and flags. The STM32 validates the frame and sequence, captures local monotonic time in task context, computes the offset, and commits the update atomically.

Required state:

- `time_sync_valid`;
- signed `time_offset_us`;
- `last_sync_sequence`;
- `last_sync_local_time_us`;
- synchronization age/fault status.

`TimeService_SyncStateAccept()` receives the validated Pi time, synchronization sequence, and captured local time. The initial accepted offset must be within the configurable initial bound (default +/-24 hours). Later updates require a strictly newer sequence and an offset change within the configurable runtime step bound, initially +/-1 second. Rejected updates retain the previous accepted offset, sequence, local timestamp, and validity state for diagnostics.

`TimeService_SyncStateGetSnapshot()` provides the retained signed offset, accepted sequence, local timestamp, validity, age, and `SYNCHRONIZED` or `UNSYNCHRONIZED` quality. `TimeService_AcceptSync()`, `TimeService_IsSyncValid()`, and `TimeService_GetSyncSnapshot()` bind this state to the TIM2 local clock for task-context users. The first implementation uses a direct offset step. `system_time_us` is therefore permitted to jump when synchronization is updated. Two-way RTT estimation and slewed correction are future versioned enhancements.

## Validity

The v1 synchronization validity timeout is 5 seconds. Until the first accepted synchronization, exported timestamps are local-only and must be marked unsynchronized. At exactly five seconds after the last accepted update, `time_sync_valid` becomes false while the retained offset remains available only for diagnostics. The STM32 must not silently label stale timestamps as Pi-synchronized.

Synchronization expiry does not stop local acquisition or diagnostics. It marks new records unsynchronized and rejects or inhibits time-dependent motion commands until a new accepted `TIME_SYNC` restores validity. Only explicitly defined non-motion service operations may continue while synchronization is invalid. Reset clears synchronization validity and the volatile offset, so time-dependent motion remains inhibited until resynchronization.

## Atomicity and Concurrency

A sync update and its validity metadata must be committed as one logical update. Measurement readers must see either the previous complete update or the new complete update, never a partially written offset/validity pair. The current implementation requires one serialized task/system-context owner for all `TimeService_SyncState` mutation and snapshot reads; ISR code must defer TIME_SYNC processing and query work. Synchronization processing occurs in task context; no lifecycle or time-state mutation occurs in an ISR.

## Remaining Integration Notes

- The v1 transaction point is the one-way Pi transaction-time estimate defined in [SPI_CONTRACT.md](SPI_CONTRACT.md).
- Offset stepping is approved for v1; slewing is a future protocol revision.
- Signed offset range and large-offset rejection limits must be bounded in the implementation without changing the v1 time model.
- Host-visible timestamp quality must expose synchronized versus local-only data.
