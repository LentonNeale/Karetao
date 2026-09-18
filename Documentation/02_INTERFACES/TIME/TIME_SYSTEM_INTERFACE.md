# Time System Interface

## Authority

This document defines the Karetao system-level time interface. STM32 and Raspberry implementations remain component-owned.

## Contract

- The shared STM32/Pi time model targets timestamp error **≤ ±1 ms** (SD-18).
- Synchronization validity and age shall be exposed (SD-18).
- TIME_SYNC is nominally **1 Hz**, configurable to **10 Hz** (SD-19).
- Synchronization becomes invalid after **5 s** without an accepted update (SD-19).
- Initial and runtime time-offset validation use distinct bounds; implausible updates are rejected without silent slew (SD-21).
- Reset clears synchronization validity and volatile offset; timestamps remain unsynchronized until a new accepted TIME_SYNC update (SD-22).
- Time-dependent motion is inhibited while synchronization is invalid (SD-20).

## Open integration definitions

The system must define the exact set of time-dependent motion operations and ensure all timestamp consumers respect synchronization validity. Drift and EKF adequacy require target-system validation.
