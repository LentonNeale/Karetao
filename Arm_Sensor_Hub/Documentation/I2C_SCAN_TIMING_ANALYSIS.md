# I2C Scan Timing Analysis — Six AS5600 Sensors via TCA9548A at 400 kHz

**Status:** Reference analysis (theoretical), supporting evidence only — establishes an improvement target, does not replace measured evidence
**Owner:** Arm Sensor Hub — sensor acquisition (`I2CManager`, `SensorTask`, TCA9548A/AS5600 device drivers)
**Boundary:** Datasheet-derived I2C protocol timing for the six-sensor scan path. Does not define or measure firmware behavior.

## Authority

This document is Arm Sensor Hub component-implementation analysis. It is **not** a Karetao system requirement, does not modify `Documentation/01_SYSTEM/SYSTEM_TIMING.md` or `SYSTEM_ARCHITECTURE.md`, and does not redefine the measured sweep figure cited there (SD-01, SD-08). The AS5600 and TCA9548A datasheets remain external authority for the timing values used as inputs; this analysis only combines them into an application-specific budget for this component's six-sensor, single-mux acquisition path.

## Relationship to the measured full-sweep figure — read this before using the numbers below

Karetao's system documentation records a **measured** full six-axis sweep time of approximately 46 ms (~22 Hz), taken from a target-hardware run on 2026-09-17 (`tools/check-sensors.sh`, recorded in the archived `CONTRACT_STATUS.md` and carried into SD-01, `SYSTEM_TIMING.md`, `SYSTEM_ARCHITECTURE.md`, and `ARM_SENSOR_HUB.md`). **That figure remains the current measured evidence and is not disputed or superseded by this document.**

This document computes a different quantity: a **theoretical, zero-overhead protocol floor** of **690 µs (≈1.45 kHz)** for a six-sensor scan, about 67× faster than the measured value. It is not a measurement, has never been run on hardware, and explicitly excludes MCU/firmware overhead, interrupt latency, DMA setup, and any deliberate settle time (§11). It does not compete with the 46 ms figure as an alternative account of what the sweep takes; it answers a different question:

| Figure | Question answered | Status |
| --- | --- | --- |
| ~46 ms / ~22 Hz (2026-09-17 run) | What does the sweep actually take on target hardware? | **Current measured evidence** |
| 690 µs / 1.45 kHz (this document) | What is the minimum time the I2C bus itself requires? | Theoretical floor; never measured |

The gap between them, roughly 45.3 ms across six channels, indicates that firmware and scheduling overhead — not I2C protocol timing — dominates the measured sweep. This is recorded as an **improvement target**: closing some of that gap through firmware optimization is desirable where practical, but the specific cause (settle time, task scheduling, register-pointer writes, HAL polling overhead, etc.) is not established by this document and must not be assumed without measurement. Identifying it is the same action SD-01 already calls for: "instrument real per-axis update latency on target hardware." The 46 ms figure remains the value to use in downstream timing work (EKF rate justification, scan-period freezing, staleness budgets) until a new measurement replaces it; 690 µs is context for how much theoretical headroom exists, not a substitute value.

---

## 1. System assumptions

The system contains six AS5600 magnetic position sensors connected through a TCA9548A I2C switch.

The I2C bus operates at a fixed:

f_SCL = 400 kHz

This is the TCA9548A Fast-mode maximum. The AS5600 supports a higher I2C frequency, but in this system both the TCA9548A and selected AS5600 operate from the same 400 kHz SCL.

The calculation assumes:

- Six AS5600 sensors.
- One TCA9548A channel is selected for each sensor.
- Each sensor is read sequentially.
- The AS5600 ANGLE register pointer has already been configured.
- A two-byte ANGLE value is read from registers `0x0E` and `0x0F`.
- The AS5600 sampling period is treated as a separate internal sensor constraint of 150 µs.
- Firmware execution time and other MCU overhead are not included.

## 2. I2C clock period

At 400 kHz: T_SCL = 1/400000 = 2.5 µs.

The TCA9548A Fast-mode timing requirements include:

| Parameter | Minimum |
|---|---:|
| t_HIGH | 0.6 µs |
| t_LOW | 1.3 µs |
| t_SU;STA | 0.6 µs |
| t_SU;STO | 0.6 µs |
| t_BUF | 1.3 µs |

The AS5600 also permits operation at 400 kHz because its Fast-mode Plus maximum is 1 MHz.

The clock timing requirements are constraints on the SCL waveform and are not additional delays to be added to every SCL clock.

## 3. TCA9548A channel selection

Selecting a TCA9548A channel requires a write transaction containing START, address+R/W, ACK, control-register byte, ACK, STOP — 9 + 9 = 18 SCL clocks.

At 400 kHz: T_MUX = 18 × 2.5 = **45 µs**.

The TCA9548A requires the STOP condition immediately after the control-register acknowledge cycle before the selected channel becomes active.

## 4. TCA9548A STOP to AS5600 transaction

Conservative timing budget: t_SU;STO (0.6 µs) + t_BUF (1.3 µs) + t_SU;STA (0.6 µs) = **T_transition = 2.5 µs**.

## 5. AS5600 ANGLE read

Two-byte ANGLE value from `0x0E` (high) and `0x0F` (low). A steady-state read:

| Operation | SCL clocks |
|---|---:|
| AS5600 address + R + ACK | 9 |
| ANGLE high byte + ACK | 9 |
| ANGLE low byte + NACK | 9 |
| **Total** | **27** |

T_AS5600 = 27 × 2.5 = **67.5 µs**.

## 6. Total time per sensor

T_sensor = T_MUX + T_transition + T_AS5600 = 45 + 2.5 + 67.5 = **115 µs**.

## 7. Six-sensor scan (protocol floor)

T_scan = 6 × 115 = **690 µs**, corresponding to a theoretical scan frequency f_scan ≈ **1.45 kHz**.

This is the protocol-only floor before any MCU or firmware overhead — see the relationship note above before using this number.

## 8. AS5600 sampling-period constraint

The AS5600 has an internal sampling period T_sample = 150 µs. This is not an additional per-transaction delay; it is a sensor-internal constraint, not a communication delay. T_system = max(T_scan, T_sample) = max(690, 150) = **690 µs**; the I2C bus transaction time, not the sensor's internal sampling period, is the limiting factor for six sensors at this clock rate.

## 9. Six-sensor timing breakdown

| Component | Per sensor | Six sensors |
|---|---:|---:|
| TCA9548A channel selection | 45.0 µs | 270.0 µs |
| TCA STOP setup | 0.6 µs | 3.6 µs |
| STOP → next START bus-free time | 1.3 µs | 7.8 µs |
| AS5600 START setup | 0.6 µs | 3.6 µs |
| AS5600 2-byte ANGLE read | 67.5 µs | 405.0 µs |
| **Total** | **115.0 µs** | **690.0 µs** |

The 150 µs AS5600 sampling period is a separate sensor constraint and is not included as an additional 150 µs delay per sensor.

## 10. General formula for this architecture

For a fixed 400 kHz SCL and a steady-state two-byte ANGLE read:

T_scan(N) = N × [(18+27)/400000 + t_SU;STO + t_BUF + t_SU;STA] = N × [112.5 + 0.6 + 1.3 + 0.6] µs = **115N µs**

f_scan(N) = 1 / (115N × 10⁻⁶) ≈ **8695.7 / N Hz**

For six sensors: T_scan(6) = 690 µs, f_scan(6) ≈ 1.45 kHz.

## 11. Important implementation limitation

This is a theoretical datasheet timing budget. It does **not** include:

- MCU I2C driver overhead.
- Firmware execution time.
- Interrupt latency.
- DMA setup or completion overhead.
- Any additional register-pointer write.
- Delays intentionally introduced by the application (e.g. mux/sensor settle time).

If the AS5600 register pointer must be written before every ANGLE read, an additional 18 SCL clocks are required per sensor: T_pointer = 18 × 2.5 = 45 µs. The steady-state calculation above assumes the pointer has already been positioned. Even accounting for this, the protocol floor remains two orders of magnitude below the measured 46 ms sweep; the dominant cost is firmware-side, not protocol-side, and remains uncharacterized by this document.

## 12. Datasheet basis

**TCA9548A** — TI TCA9548A datasheet, SCPS207H, Revision H: §5.6 I2C Interface Timing Requirements (p.7), §7.5.3 Bus Transactions (p.16), §7.5.4 Control Register (pp.17–18). Fast-mode maximum SCL frequency 400 kHz; Fast-mode t_SU;STA, t_SU;STO, t_BUF requirements used in the timing budget; channel selection becomes active after the required STOP condition.

**AS5600** — AS5600 supplied datasheet: I2C interface/timing sections; ANGLE registers `0x0E`/`0x0F`; two-byte ANGLE read transaction; maximum I2C frequency 1 MHz (operation here fixed at 400 kHz to match the TCA9548A bus); timing characteristics 150 µs sampling period.

## Candidate causes of the gap (unconfirmed — for future instrumentation, not conclusions)

The ~45.3 ms difference between the measured sweep and the theoretical floor is not attributed to any single cause by this document. Plausible contributors, none confirmed without target-hardware instrumentation, include:

- **RTOS tick granularity** — any blocking wait or task yield inside the six-sensor loop rounds up to whole scheduler ticks (commonly 1 ms in FreeRTOS), which can dominate a microsecond-scale bus budget.
- **Mux settle time** — TCA9548A channel switching may need real bus-capacitance/pull-up settling time beyond the datasheet's electrical minimums, especially with six sensor stubs on shared wiring; the component's own scan-period/settle-time parameters are still unfrozen (`CONTRACT_STATUS.md`).
- **HAL polling overhead** — blocking I2C calls that poll status flags against a tick-resolution timeout (`I2C_MANAGER_CONTRACT.md`) can round up per wait-point well beyond the raw SCL clock count.
- **Per-channel timeout budget** — also unfrozen; if implemented as a fixed wait window rather than an early exit on success, it could pad every channel regardless of actual response time.
- **Task/mutex serialization** — the I2C manager's static mutex and task-context-only blocking APIs introduce context-switch and scheduling overhead outside the pure bus-transaction time.

## How to use this document

- As a **lower-bound reference** when evaluating whether a proposed scan-period, settle-time, or per-channel-timeout value (the open item in the decisions register) leaves the I2C bus itself as the constraint, or whether firmware/scheduling overhead dominates.
- As **input to, not a substitute for**, the still-required work: instrumenting real per-axis update latency on target hardware (SD-01 "Investigate"), which alone can attribute the ~46 ms measured figure to specific causes among those listed above.
- Do not cite §7's 1.45 kHz figure as a system timing requirement, a component status of `VERIFIED`, or a replacement for the measured sweep time in `ARM_SENSOR_HUB.md` or `SYSTEM_TIMING.md`. It is an improvement target, not a confirmed value. Any change to the measured figure itself requires a new target-hardware measurement, not a recalculation.
