# System Timing

## Authority

Authoritative Karetao system timing requirements and timing constraints are recorded here. Implementation-specific timer configuration remains component-owned.

## Requirements and constraints

- Baseline sensor/state publication and initial control-loop rate: **100 Hz** (SD-01).
- Current EKF operating rate: **500 Hz**, subject to downstream integration constraints (SD-01).
- Normal observation skew: **<5 ms**; dynamic-joint target: **<1 ms** (SD-08).
- Acquisition timestamps shall be retained (SD-08).
- SPI initial maximum operating point: **5 MHz**, pending live integration and physical-layer validation (SD-01, SD-15).
- TIME_SYNC nominal rate: **1 Hz**, configurable to **10 Hz** (SD-19).
- Synchronization becomes invalid after **5 s** without an accepted update (SD-19).
- Timestamp error target: **≤ ±1 ms** relative to the shared STM32/Pi time model (SD-18).

## Timing validation

The 500 Hz EKF setting must not be interpreted as a requirement for a complete six-axis physical sweep at 500 Hz. The indexed decision records identify an approximately 46 ms sweep and require timestamped/latest-value estimator handling. End-to-end availability, latency, oscillator drift and adequacy of the ±1 ms budget remain validation items.

