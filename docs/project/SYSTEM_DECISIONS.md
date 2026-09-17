# Karetao System Decisions Register

This file lists the current SD-01 through SD-25 system decisions from the approved v1.0 firmware contract baseline.

**Source:** [CTO Final Decisions](archive/Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_FINAL.md), dated 2026-09-07.

> The source document states that these decisions approve the firmware contract baseline for implementation. It does **not** certify the assembled robot as safe or authorize energized motion; release remains conditional on the listed safety, validation, and acceptance conditions.

| ID | Decision area | Final decision | Summary |
|---|---|---|---|
| SD-01 | System timing | MODIFIED | 100 Hz baseline; <2 ms transport/assembly target; 5 MHz initial maximum SPI clock subject to Pi/DMA validation. |
| SD-02 | System-wide failure classification | MODIFIED | Four response levels: INFORMATIONAL, DEGRADED, FAULT, SAFETY_CRITICAL; PL/SIL determined by machine risk assessment. |
| SD-03 | Raspberry Pi communication loss | APPROVED | 500 ms heartbeat timeout; reject motion, controlled stop if possible, then motor disable; never hold the last motion command. |
| SD-04 | Motor feedback/command timeout | APPROVED | Five times the commissioned feedback period; one miss degraded; three consecutive misses inhibit the motor and escalate to FAULT. |
| SD-05 | CAN network requirements | MODIFIED | 1 Mbps nominal v1 target, standard 11-bit IDs, <50–60% measured average load target; exact hardware and timing require validation. |
| SD-06 | CAN bus failure | APPROVED | Detect bus-off, inhibit commands, perform bounded recovery, escalate after repeated failure, and require explicit reactivation. |
| SD-07 | Joint/motor mapping | APPROVED | Versioned deterministic logical-joint, sensor-ID, motor/CAN-ID mapping including direction, zero offset, and transmission ratio. |
| SD-08 | Motor/joint temporal alignment | APPROVED | Observation skew below 5 ms normally, target below 1 ms for dynamic joints; retain acquisition timestamps. |
| SD-09 | Measurement history ownership | APPROVED | Raspberry Pi/EKF owns measurement queues and estimator history; STM32 provides bounded latest-value caches and coherent records. |
| SD-10 | Calibration ownership | APPROVED | Calibration computed on Pi/workstation; STM32 receives validated parameters through a controlled configuration path. |
| SD-11 | Calibration storage | APPROVED | Versioned, CRC-protected redundant STM32 flash records with power-loss protection and host-side source copy. |
| SD-12 | Authoritative angle representation | MODIFIED | Calibrated radians are authoritative at host/API; wire-schema change must be explicitly versioned rather than silently replacing millidegrees. |
| SD-13 | Required joint state | APPROVED | Stable joint identity, position, velocity where available, validity/status, acquisition timestamp, sync quality, and calibration version. |
| SD-14 | Required command interface | MODIFIED | Commissioned position/velocity plus enable, disable, and controlled-stop operations; heartbeat, lifecycle, calibration, and safety gating required. |
| SD-15 | Fixed SPI transaction | APPROVED | 512-byte frame, 490-byte maximum payload, SPI Mode 0, little-endian fields, CRC-32/ISO-HDLC, deterministic request/response ownership. |
| SD-16 | GET_SNAPSHOT priority | APPROVED | Correlated GET_SNAPSHOT response takes priority; active DMA buffers remain immutable; replacement frames use replace-if-new policy. |
| SD-17 | SPI host transaction strategy | APPROVED | DATA_READY interrupt for latency plus configurable polling, initially 1 ms, for recovery; Pi remains SPI clock master. |
| SD-18 | Timestamp accuracy | APPROVED | Target timestamp error ≤ ±1 ms relative to shared STM32/Pi time model; expose sync validity and age. |
| SD-19 | TIME_SYNC frequency | APPROVED | 1 Hz nominal, configurable to 10 Hz; synchronization invalid after five seconds without an accepted update. |
| SD-20 | Loss of time synchronization | MODIFIED | Continue acquisition/diagnostics but inhibit time-dependent motion until synchronization returns. |
| SD-21 | Time offset validation | APPROVED | Wide initial offset range, then narrower runtime validation initially ±1 s; reject implausible updates without silent slew. |
| SD-22 | Time behaviour after reset | APPROVED | Clear sync validity and volatile offset; timestamps remain unsynchronized until a new accepted TIME_SYNC. |
| SD-23 | Transient vs persistent fault recovery | APPROVED | Bounded service-specific retries; persistent/repeated/freshness failures enter ERROR and recover to INACTIVE. |
| SD-24 | System restart and recovery | APPROVED | Return to INACTIVE; explicit dependency-ordered reactivation required; never automatically resume motor motion after recovery. |
| SD-25 | Independent safety mechanisms | MODIFIED | Independent E-stop, motor-disable/power-removal path, watchdog, stop/brake behaviour, fault indication, reset behaviour, and applicable safety-rated architecture are release gates. |

## Decision status

- **APPROVED:** 18 decisions
- **MODIFIED:** 7 decisions
- **Total:** 25 decisions

## Important release conditions

The source approval identifies the following conditions before energized-motion release:

1. Complete and approve the machine risk assessment, including required safety functions and PL/SIL target.
2. Validate the independent E-stop and motor-disable path, measured stopping time, watchdog behaviour, and actuator brake/power behaviour on the assembled system.
3. Verify the exact MKS controller, CAN physical topology, APB1-derived bit timing, worst-case bus load, recovery behaviour, and termination before freezing CAN production configuration.
4. Validate the 5 MHz SPI limit, 1 ms polling fallback, GPIO notification, DMA timing, signal integrity, and host-stall recovery with the Raspberry Pi.
5. Version the radians representation before changing the current processed-millidegree wire field.
6. Complete calibration flash endurance, power-loss, schema, and parameter-integrity tests.
7. Treat failure of these conditions as a release blocker for energized motion.

## Authority and traceability

This register is a concise index of the approved SD decisions. The archived CTO decision document remains the detailed source for the decision rationale, value/policy, and approval conditions.

If a decision is changed, update this register and the authoritative decision record together. Do not use this summary to override a newer approved system decision.
