# System Synchronization

## Authority

This document defines Karetao system synchronization requirements. Component implementations define how the synchronization service is implemented.

## Requirements

- The shared STM32/Pi time model shall target timestamp error of **≤ ±1 ms** and expose synchronization validity and age (SD-18).
- TIME_SYNC shall operate at **1 Hz nominal**, configurable to **10 Hz** (SD-19).
- Synchronization shall become invalid after **5 seconds** without an accepted update (SD-19).
- While synchronization is invalid, acquisition and diagnostics continue, but time-dependent motion is inhibited (SD-20).
- Implausible time-offset updates shall be rejected without silent slew; initial and runtime validation use distinct bounds (SD-21).
- Reset clears synchronization validity and volatile offset; timestamps remain unsynchronized until a new accepted TIME_SYNC update (SD-22).

## Motion-permission integration

The synchronization rule is one prerequisite of the proposed system-level motion-permission gate. Loss of synchronization must be propagated to the single normal-motion permission authority rather than independently interpreted by each motion-producing subsystem.

This proposal does not change the approved SD-18 through SD-22 behaviour. The exact scope of time-dependent motion and any additional freshness limits remain open for system decision.

## Integration obligations

The system must define exactly which operations constitute time-dependent motion and ensure one motion-permission authority enforces the rule consistently. Consumers, especially the 500 Hz EKF, must not treat unsynchronized timestamps as valid. Validation of drift between sync updates remains required.
