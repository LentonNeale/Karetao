# System Synchronization

## Authority

This document defines Karetao system synchronization requirements. Component implementations define how the synchronization service is implemented.

## Requirements

- The shared STM32/Pi time model shall target timestamp error of **≤ ±1 ms** and expose synchronization validity and age (SD-18).
- Every applicable SPI response provides a clock-sync observation; there is no separate periodic TIME_SYNC exchange. The request `seq` is the exchange ID, and the response carries `request_received_local_us` (SD-19 as modified by Issue #12 items 1, 4, 5).
- The STM32 observation instant (T2) is the raw TIM2 counter captured in the SPI DMA-complete ISR, extended to 64 bits in task context, not in the ISR. On the Pi, T1 is the request send time and T4 the response receipt time, with `T_pi_obs = (T1 + T4) / 2` (Issue #12 items 2, 3).
- The STM32 performs no clock math. It timestamps acquisitions in raw local time, and the Pi-side ClockSync model converts them to the synchronized `measurement_timestamp_us` (Issue #12 item 7).
- Synchronization shall become invalid after **5 seconds** without an accepted observation (SD-19).
- While synchronization is invalid, acquisition and diagnostics continue, but time-dependent motion is inhibited (SD-20).
- Implausible observations shall be rejected without silent slew by ClockSync, which is the single acceptance policy. The legacy drift-limit check remains temporarily as a secondary diagnostic only (SD-21 as modified by Issue #12 item 9).
- An STM32 reset invalidates the ClockSync model; timestamps remain unsynchronized until ClockSync is valid again (SD-22 as modified by Issue #12).
- STM32 link liveness (`link_stale`) and Pi-side `ClockSync.is_valid()` are independent signals. `link_stale` gates STM32 motion permission, and `ClockSync.is_valid()` governs measurement usability (Issue #12 item 6).

## Motion-permission integration

The synchronization rule is one prerequisite of the proposed system-level motion-permission gate. Loss of synchronization must be propagated to the single normal-motion permission authority rather than independently interpreted by each motion-producing subsystem.

SD-19, SD-21 and SD-22 are modified by [Issue #12](../07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md) as stated above; the motion-permission proposal does not change them further. The exact scope of time-dependent motion and any additional freshness limits remain open for system decision.

## Integration obligations

The system must define exactly which operations constitute time-dependent motion and ensure one motion-permission authority enforces the rule consistently. Consumers, especially the 500 Hz EKF, must not treat unsynchronized timestamps as valid. Validation uses two sequential gates: Gate A (ClockSync model characterized by synthetic and integration tests) and then Gate B (±1 ms accuracy validated on hardware against an independent reference). Passing Gate A does not imply Gate B (Issue #12 item 10).
