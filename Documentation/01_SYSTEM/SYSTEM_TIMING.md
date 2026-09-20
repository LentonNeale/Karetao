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

**Improvement target (2026-09-20):** a datasheet-derived I2C protocol-timing analysis establishes a theoretical floor of ~690 µs for the six-sensor scan, well below the measured ~46 ms; see the timing improvement note in `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md` and `Arm_Sensor_Hub/Documentation/I2C_SCAN_TIMING_ANALYSIS.md`. The 46 ms figure remains the current measured evidence; the floor identifies headroom for future firmware optimization, not a replacement value.

