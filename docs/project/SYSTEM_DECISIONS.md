# Karetao System Decisions Register

This file lists the current SD-01 through SD-26 system decisions and the unresolved system-level issues that remain attached to them.

**Source for SD-01 through SD-25:** [CTO Final Decisions](archive/Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_FINAL.md), dated 2026-09-07.

> The source document approves the v1.0 firmware contract baseline for implementation. It does **not** certify the assembled robot as safe or authorize energized motion; release remains conditional on the listed safety, validation, and acceptance conditions.

## Decision table

| ID | Decision area | Status | Summary | Open issue / comment |
|---|---|---|---|---|
| SD-01 | System timing | MODIFIED | 100 Hz remains the baseline for sensor/state publication and the initial control loop. **The EKF update rate is currently set to 500 Hz** and will be adjusted if required by downstream system constraints. SPI remains at a 5 MHz initial maximum, subject to validation. | The current six-axis physical sweep is approximately 46 ms. The 500 Hz EKF rate therefore requires the estimator to operate from timestamped/latest-value data rather than implying a 500 Hz complete six-axis sweep. End-to-end EKF data availability and latency remain integration items. |
| SD-02 | System-wide failure classification | MODIFIED | Four response levels: INFORMATIONAL, DEGRADED, FAULT, SAFETY_CRITICAL; PL/SIL determined by machine risk assessment. | The classification must be mapped to explicit motion-inhibit behaviour and ownership. A fault classification alone does not define who has final authority to prevent motion. |
| SD-03 | Raspberry Pi communication loss | APPROVED | 500 ms heartbeat timeout; reject motion, controlled stop if possible, then motor disable; never hold the last motion command. | “Controlled stop” and “motor disable” require measurable fault-to-safe-state timing. The exact stop-time requirement remains a system/safety validation item. |
| SD-04 | Motor feedback/command timeout | APPROVED | Five times the commissioned feedback period; one miss degraded; three consecutive misses inhibit the motor and escalate to FAULT. | This primarily addresses feedback/timeout behaviour. **Command acknowledgement must be distinguished from feedback freshness.** A command that is transmitted but not acknowledged requires an explicit failure rule before motion is considered safe. |
| SD-05 | CAN network requirements | MODIFIED | 1 Mbps nominal v1 target, standard 11-bit IDs, <50–60% measured average load target; exact hardware and timing require validation. | Exact MKS controller model, firmware, command semantics, feedback semantics, acknowledgement behaviour, brake behaviour, and CAN physical configuration remain open until target-hardware evidence is recorded. |
| SD-06 | CAN bus failure | APPROVED | Detect bus-off, inhibit commands, perform bounded recovery, escalate after repeated failure, and require explicit reactivation. | Confirm whether a CAN failure affecting one motor requires a joint-level stop or whole-system stop. Final scope follows the machine risk assessment. |
| SD-07 | Joint/motor mapping | APPROVED | Versioned deterministic logical-joint, sensor-ID, motor/CAN-ID mapping including direction, zero offset, and transmission ratio. | The ordinary one-to-one mapping is insufficient for the differential end effector. SD-26 defines the separate motor-to-end-effector-DOF mapping decision. |
| SD-08 | Motor/joint temporal alignment | APPROVED | Observation skew below 5 ms normally, target below 1 ms for dynamic joints; retain acquisition timestamps. | The approximately 46 ms six-axis sweep must be reconciled with estimator/control requirements. Timestamp compensation does not by itself establish that the resulting state update rate is acceptable. |
| SD-09 | Measurement history ownership | APPROVED | Raspberry Pi/EKF owns measurement queues and estimator history; STM32 provides bounded latest-value caches and coherent records. | The 500 Hz EKF setting requires explicit definition of how latest-value records, asynchronous sensor updates, timestamp age, and interpolation/hold behaviour are handled. |
| SD-10 | Calibration ownership | APPROVED | Calibration computed on Pi/workstation; STM32 receives validated parameters through a controlled configuration path. | Calibration must cover the differential mechanism as well as individual motor/sensor offsets and ratios. |
| SD-11 | Calibration storage | APPROVED | Versioned, CRC-protected redundant STM32 flash records with power-loss protection and host-side source copy. | Calibration flash schema, endurance, power-loss behaviour, and parameter integrity remain release conditions. |
| SD-12 | Authoritative angle representation | MODIFIED | Calibrated radians are authoritative at host/API; wire-schema change must be explicitly versioned rather than silently replacing millidegrees. | Migration requires a defined schema version, conversion rules, Pi decoder update, and verification evidence before the existing wire field changes meaning. |
| SD-13 | Required joint state | APPROVED | Stable joint identity, position, velocity where available, validity/status, acquisition timestamp, sync quality, and calibration version. | Add explicit commanded-vs-actual state validity and command acknowledgement status where required by the final motor interface. |
| SD-14 | Required command interface | MODIFIED | Commissioned position/velocity plus enable, disable, and controlled-stop operations; heartbeat, lifecycle, calibration, and safety gating required. | Define command acknowledgement, freshness, timeout, cancellation, and the distinction between application controlled-stop and independent emergency stop. |
| SD-15 | Fixed SPI transaction | APPROVED | 512-byte frame, 490-byte maximum payload, SPI Mode 0, little-endian fields, CRC-32/ISO-HDLC, deterministic request/response ownership. | Protocol sizing is defined, but the 5 MHz operating point remains an empirical integration limit until live Pi/STM32 and physical-layer evidence is accepted. |
| SD-16 | GET_SNAPSHOT priority | APPROVED | Correlated GET_SNAPSHOT response takes priority; active DMA buffers remain immutable; replacement frames use replace-if-new policy. | Confirm replacement/drop semantics preserve the freshest state required by the 500 Hz EKF and do not create unacceptable state age. |
| SD-17 | SPI host transaction strategy | APPROVED | DATA_READY interrupt for latency plus configurable polling, initially 1 ms, for recovery; Pi remains SPI clock master. | Current Pi baseline does not have a physical DATA_READY GPIO assigned. Until one is assigned and tested, the 1 ms polling path is the available host notification mechanism. |
| SD-18 | Timestamp accuracy | APPROVED | Target timestamp error ≤ ±1 ms relative to shared STM32/Pi time model; expose sync validity and age. | Validate whether ±1 ms is sufficient for the 500 Hz EKF and downstream control requirements. |
| SD-19 | TIME_SYNC frequency | APPROVED | 1 Hz nominal, configurable to 10 Hz; synchronization invalid after five seconds without an accepted update. | Validate synchronization stability and timestamp error under the 500 Hz estimator operating condition. |
| SD-20 | Loss of time synchronization | MODIFIED | Continue acquisition/diagnostics but inhibit time-dependent motion until synchronization returns. | Define precisely which downstream operations are “time-dependent motion” and ensure the motion-permission layer enforces this consistently. |
| SD-21 | Time offset validation | APPROVED | Wide initial offset range, then narrower runtime validation initially ±1 s; reject implausible updates without silent slew. | Verify that the initial and runtime bounds are appropriate for commissioning and reset behaviour. |
| SD-22 | Time behaviour after reset | APPROVED | Clear sync validity and volatile offset; timestamps remain unsynchronized until a new accepted TIME_SYNC. | Confirm that all consumers, especially the 500 Hz EKF, reject or correctly classify unsynchronized data after reset. |
| SD-23 | Transient vs persistent fault recovery | APPROVED | Bounded service-specific retries; persistent/repeated/freshness failures enter ERROR and recover to INACTIVE. | Define system-level escalation when a subsystem is recovering but motion cannot be considered safe. Recovery must not race with motion permission. |
| SD-24 | System restart and recovery | APPROVED | Return to INACTIVE; explicit dependency-ordered reactivation required; never automatically resume motor motion after recovery. | Establish the complete dependency order across STM32, Pi, ROS 2, EKF, ros2_control, MoveIt 2, and safety gating before physical motion release. |
| SD-25 | Independent safety mechanisms | MODIFIED | Independent E-stop, motor-disable/power-removal path, watchdog, stop/brake behaviour, fault indication, reset behaviour, and applicable safety-rated architecture are release gates. | The boundary and interface between Karetao application controls and the independent safety system must be explicitly defined by the machine risk assessment and safety architecture. |
| SD-26 | Differential end-effector motor/DOF mapping | PROPOSED | The two end-effector motors drive two end-effector rotational DOFs through a differential mechanism. The mapping must be represented explicitly rather than as two independent one-to-one joints. | Define the forward/inverse transformation, motor signs, gear ratios, zero offsets, joint limits, singular/invalid configurations, and representation in ros2_control and MoveIt 2. This remains open until the mechanical model and mapping are verified. |

## Decision status

- **APPROVED:** 18
- **MODIFIED:** 7
- **PROPOSED:** 1
- **Total:** 26

## System-level issues still requiring closure

1. **EKF timing:** EKF is currently set to **500 Hz**; downstream constraints may require adjustment. This does not mean the complete six-axis sensor scan currently operates at 500 Hz.
2. **Sensor failure response:** The requirement that sensor-data failure stops motion needs an explicit rule covering invalid, missing, stale, and failed sensors.
3. **Motor command acknowledgement:** Command acknowledgement must be separately defined from motor feedback and communication heartbeat.
4. **Fault-to-safe-state timing:** “Stop immediately” must become a measurable timing requirement.
5. **Motion-permission authority:** Define which system component has final authority to permit or inhibit motion.
6. **Differential end effector:** The two-motor/two-DOF mechanical transformation must be formally defined before the joint model is frozen.
7. **Motor-controller semantics:** Exact MKS controller behaviour remains an integration dependency.
8. **Safety boundary:** Define the interface between application-level safety controls and the independent safety function.
9. **MoveIt 2 / ros2_control model:** The authoritative mechanical/joint model must include the differential end effector and its limits.
10. **Sensor update architecture:** Determine how a 500 Hz EKF consumes asynchronously updated sensor records and what maximum data age is acceptable.

These issues are intentionally recorded as open requirements rather than being assigned assumptions in this document.

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

This register is a concise index of the current system decisions. The archived CTO decision document remains the detailed source for SD-01 through SD-25 rationale, value/policy, and approval conditions.

SD-26 is a project-level proposed decision added after review of the current Karetao system definition and is not part of the 2026-09-07 CTO approval.

If a decision is changed, update this register and the authoritative decision record together. Do not use this summary to override a newer approved system decision.
