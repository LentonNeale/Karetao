# CTO Decision Brief: System Decisions v1

**Status:** Superseded by [CTO_DECISION_FINAL.md](CTO_DECISION_FINAL.md), which records the approved decisions. This brief is retained as the original proposal for historical context.

**Original status:** All entries were **PROPOSED** and awaited CTO approval. This document was the approval proposal, not a safety certification or a claim that every behavior is implemented.

**Source note:** `SYSTEM_DECISIONS_V1.md` was not present in the workspace. The decision inventory was reconstructed from the supplied draft and reconciled with the repository contracts.

## Executive Summary

The proposed architecture uses a 100 Hz sensor and state-update baseline, timestamp targets at or below 1 ms, Pi-owned historical estimation, calibrated angular values, and a fixed 512-byte pipelined SPI protocol. The repository contracts already establish the SPI frame format, six-record snapshot model, five-second synchronization validity, Pi time authority, 1 MHz extended STM32 timebase, producer-cache ownership, and lifecycle states.

Safety-related proposals use fail-closed behavior: loss of the Pi or motor feedback inhibits continued actuation, persistent transport faults enter `ERROR`, and recovery returns to `INACTIVE` until explicitly activated. These are engineering recommendations only. The CTO must approve the risk classification, stop timing, bus-off escalation, emergency-stop architecture, and independent hardware safety layers after a machine-level risk assessment.

CAN operation at 1 Mbps is proposed only as an integration target. It remains gated by the exact motor-controller manual, physical bus topology, measured bus load, transceiver limits, and STM32 APB1 bit-timing calculation. The maximum SPI clock is likewise unresolved until the Raspberry Pi driver and DMA timing are reviewed together.

## Decision Summary

| ID | Proposed value | Status |
| --- | --- | --- |
| SD-01 | 100 Hz baseline; bounded latency budget; 5 MHz SPI candidate pending integration | PROPOSED - CTO confirmation required |
| SD-02 | Four-tier fault classification mapped to risk assessment, PL/SIL where applicable | PROPOSED - CTO safety approval required |
| SD-03 | Heartbeat timeout 500 ms; controlled stop then motor disable | PROPOSED - CTO safety approval required |
| SD-04 | Feedback timeout 5x measured period; three consecutive failures escalate | PROPOSED - CTO safety approval required |
| SD-05 | 1 Mbps nominal CAN; keep measured load below 50-60%; timing gate remains open | PROPOSED - integration gate |
| SD-06 | Detect bus-off; bounded recovery; three events in a rolling window escalate | PROPOSED - CTO safety approval required |
| SD-07 | Deterministic logical joint, sensor, motor mapping with commissioned transmission ratio | PROPOSED |
| SD-08 | Joint/motor measurement skew below 5 ms; target below 1 ms | PROPOSED |
| SD-09 | Pi/EKF owns history; STM32 publishes latest coherent records | PROPOSED |
| SD-10 | Calibration computed on Pi or engineering workstation | PROPOSED |
| SD-11 | Versioned calibration stored redundantly in STM32 flash and applied by STM32 | PROPOSED |
| SD-12 | Calibrated radians authoritative; raw angle retained diagnostically | PROPOSED |
| SD-13 | State exposes position, velocity when available, validity, and acquisition timestamp | PROPOSED |
| SD-14 | Commands expose position/velocity as applicable plus enable/disable and safety gating | PROPOSED - motor commissioning gate |
| SD-15 | Fixed 512-byte frame, maximum 490-byte payload, Mode 0 | PROPOSED - contract baseline |
| SD-16 | Correlated `GET_SNAPSHOT` response takes priority over unsolicited publication | PROPOSED - contract baseline |
| SD-17 | `DATA_READY` interrupt with periodic polling fallback | PROPOSED - integration gate |
| SD-18 | Timestamp error target at or below 1 ms | PROPOSED |
| SD-19 | TIME_SYNC at 1 Hz baseline; configurable up to 10 Hz | PROPOSED |
| SD-20 | Mark unsynchronized after 5 s; continue degraded operation; escalation requires approval | PROPOSED - CTO safety approval required |
| SD-21 | Wide first-sync acceptance, then configurable bounded offset change | PROPOSED |
| SD-22 | Reset clears synchronization validity until a new accepted sync | PROPOSED - contract baseline |
| SD-23 | Bounded retries; persistent failure enters `ERROR`; recovery ends `INACTIVE` | PROPOSED - CTO safety approval required |
| SD-24 | Reset and recovery require explicit activation from `INACTIVE` | PROPOSED - CTO safety approval required |
| SD-25 | Independent E-stop, motor-disable path, watchdog, and power safety documented and tested | PROPOSED - CTO safety approval required |

## A. Timing & Performance

### SD-01 - System Timing Requirements

**Question:** What acquisition, publication, estimation, control, and transport timing does the hub provide?

**Proposed Value:**

- Sensor acquisition target: 100 Hz per logical axis where the sensor and bus permit.
- Coherent STM32 snapshot publication target: 100 Hz.
- Pi consumer and EKF target: 100 Hz, independently schedulable.
- Control-loop target: 100 Hz unless commissioning demonstrates a higher requirement.
- Sensor-to-Pi freshness budget: less than one 10 ms cycle; target less than 2 ms transport/assembly latency.
- Fixed 512-byte SPI frame at a candidate 5 MHz clock: 819.2 us of wire time, subject to Pi and STM32 validation.

**Justification:** A 100 Hz baseline is appropriate for a first mobile/manipulator sensor-hub integration and leaves margin for filtering and scheduling. The 5 MHz value is a calculation candidate, not a frozen electrical limit: the contract explicitly requires Raspberry Pi driver and DMA timing approval. The STM32F405 reference manual and the SPI contract should govern the final clock and peripheral configuration ([ST STM32F405 documentation](https://www.st.com/en/microcontrollers-microprocessors/stm32f405-415/documentation.html), [SPI service contract](../SPI_SERVICE_CONTRACT.md)).

**Status:** PROPOSED

### SD-18 - Timestamp Accuracy

**Question:** What error is acceptable for acquisition timestamps used by state estimation?

**Proposed Value:** Target timestamp error at or below +/-1 ms relative to the shared STM32/Pi time model; expose timestamp validity and synchronization age with every record.

**Justification:** At 100 Hz, a 1 ms timing error is 10% of a sample period and is a defensible initial budget for sensor fusion. The implementation must timestamp immediately after successful sensor decoding, use the shared 64-bit extension of TIM2, and mark unsynchronized records rather than presenting them as authoritative ([ROS 2 `JointState`](https://docs.ros.org/en/ros2_packages/rolling/api/sensor_msgs/msg/JointState.html), [snapshot coherency contract](../SNAPSHOT_COHERENCY_CONTRACT.md)).

**Status:** PROPOSED

### SD-19 - TIME_SYNC Frequency

**Question:** How often does the Pi correct the STM32 clock offset?

**Proposed Value:** Send `TIME_SYNC` at 1 Hz nominal, configurable to 10 Hz for tighter experiments; invalidate synchronization after 5 seconds without an accepted update.

**Justification:** A 1 MHz local clock with a typical tens-of-ppm oscillator can remain within a millisecond-scale budget between corrections, while 10 Hz is available when measured drift or dynamics require it. The five-second validity window is already the repository v1 baseline; v1 continues to use the one-way transaction-point estimate rather than claiming PTP-grade synchronization ([TIMESTAMP_SYNC_CONTRACT.md](../TIMESTAMP_SYNC_CONTRACT.md)).

**Status:** PROPOSED

## B. Safety & Failure Policy

### SD-02 - System-Wide Failure Classification

**Question:** How are failures classified and connected to system responses?

**Proposed Value:** Use four operational levels: `INFORMATIONAL`, `DEGRADED`, `FAULT`, and `SAFETY_CRITICAL`. Each event receives severity, detectability, required response, and recovery owner. The final safety functions and required performance level or SIL must come from a machine risk assessment under ISO 13849-1:2023 and/or IEC 62061:2021, not from this document alone.

**Justification:** ISO 13849-1 defines design principles and performance-level methods for safety-related control parts but does not choose the required level for a particular machine. IEC 62061 provides a machinery functional-safety process, including verification and validation expectations. The proposed operational vocabulary gives firmware deterministic behavior while preserving the CTO's responsibility for the formal safety target ([ISO 13849-1:2023](https://www.iso.org/standard/73481.html), [IEC 62061:2021](https://webstore.iec.ch/en/publication/59927)).

**Status:** PROPOSED

### SD-03 - Raspberry Pi Communication Loss

**Question:** What happens when the Pi stops providing commands or heartbeat messages?

**Proposed Value:** Require a monotonic heartbeat and command freshness check. After 500 ms without a valid heartbeat, stop accepting motion commands, command a controlled stop if transport is still usable, then assert motor disable. Do not hold the last motion command. The exact stop time and disable mechanism require CTO approval and hardware validation.

**Justification:** A watchdog must bound the time during which stale commands can affect motion; holding the last command is not fail-safe. The sequence separates a controlled stop from final energy removal, but the software timer alone is not an independent safety function. The timeout must be validated against robot speed, inertia, brake behavior, and the risk assessment.

**Status:** PROPOSED

### SD-04 - Motor Feedback/Command Timeout

**Question:** What timeout and escalation apply when a motor controller does not respond?

**Proposed Value:** Set the response timeout to five times the commissioned feedback period, with a minimum bounded watchdog value. A single miss is a degraded event; three consecutive misses for one motor inhibit that motor and escalate to `FAULT`. A system-level stop is required if the affected motor can create a hazardous state.

**Justification:** A multiple-of-period timeout tolerates scheduling and CAN arbitration jitter while detecting a missing controller. Three consecutive failures avoid escalating on one lost frame but still bound fault persistence. The feedback period, motor stopping behavior, and whether a single-joint fault requires a whole-system stop are CTO-owned commissioning decisions.

**Status:** PROPOSED

### SD-06 - CAN Bus Failure

**Question:** How does the system respond to CAN bus-off and repeated recovery failure?

**Proposed Value:** Detect bus-off, inhibit normal motor commands, perform bounded hardware-defined recovery from task context, and log every attempt. Use an escalating retry delay. Escalate to `ERROR` after three bus-off events in a configurable rolling window or after recovery timeout; require explicit recovery and activation before resuming motion.

**Justification:** CAN error confinement defines bus-off as a state requiring controlled recovery; application policy must still prevent an unstable bus from repeatedly re-enabling actuation. Recovery details must follow the STM32 bxCAN reference manual and actual transceiver behavior. The three-event threshold is a proposal for review, not a substitute for a hazard analysis or measured fault-rate data ([ST STM32F405 documentation](https://www.st.com/en/microcontrollers-microprocessors/stm32f405-415/documentation.html), [CAN in Automation knowledge base](https://www.can-cia.org/can-knowledge/)).

**Status:** PROPOSED

## C. CAN Network

### SD-05 - CAN Network Requirements

**Question:** What bitrate, bus capacity, and physical constraints govern the motor CAN network?

**Proposed Value:** Use 1 Mbps as the nominal target only if the exact MKS controller and transceiver support it. Design for measured average bus load below 50-60%, standard 11-bit identifiers, proper termination, and a topology/length validated against the selected transceiver and bitrate. Derive CAN prescaler, time segments, sample point, and SJW from the actual STM32 APB1 clock before implementation freeze.

**Justification:** Higher bitrate reduces frame occupancy but tightens propagation and wiring constraints; bus load must include arbitration, retries, polling, commands, and safety traffic rather than only payload bytes. The repository contract explicitly leaves bitrate, sample point, SJW, TX ownership, and retry policy as integration gates. The MKS Servo42/57 manual and installed motor model must be the authoritative product-specific source; the currently available project materials do not verify a universal 1 Mbps claim.

**Status:** PROPOSED

### SD-07 - Joint/Motor Mapping

**Question:** What deterministic relationship maps logical joints to angle sensors and motors?

**Proposed Value:** Use a versioned one-to-one logical mapping for v1: logical joint -> AS5600 sensor ID -> motor index/CAN ID, with direction, zero offset, and fixed transmission ratio. Reject duplicate sensor or CAN-ID assignments. Differential or mechanically coupled joints require a later explicit mapping revision.

**Justification:** Deterministic identity and transmission metadata are prerequisites for interpreting position and velocity measurements. The target topology has six logical sensor axes and up to eight motor records, but the repository notes that the final joint-to-motor mapping remains a commissioning decision ([snapshot coherency contract](../SNAPSHOT_COHERENCY_CONTRACT.md)).

**Status:** PROPOSED

## D. Mechanical & State Estimation Architecture

### SD-08 - Motor/Joint Temporal Alignment

**Question:** What maximum time difference is allowed between joint angle and motor encoder observations?

**Proposed Value:** Require measured skew below 5 ms for normal operation and target below 1 ms for dynamic joints. Carry independent acquisition timestamps; do not infer simultaneity from a common frame timestamp. Reject, flag, or down-weight samples exceeding the configured skew budget.

**Justification:** A coherent packet can still contain sequentially acquired observations, so record timestamps are necessary for an EKF to account for delay. The 5 ms threshold is a practical initial bound at a 100 Hz update rate; the final threshold must be checked against joint speed, gearbox ratio, and estimator sensitivity.

**Status:** PROPOSED

### SD-09 - Measurement History Ownership

**Question:** Which system stores historical measurements and handles delayed data?

**Proposed Value:** The Raspberry Pi/EKF owns historical queues, delay compensation, and estimator state history. The STM32 owns only bounded latest-value caches and publishes coherent records with acquisition timestamps, validity flags, and freshness diagnostics.

**Justification:** The Pi has the computational context and estimator model needed to fuse delayed measurements, while the STM32 must remain bounded and deterministic. This matches the repository's producer-cache/snapshot-builder ownership model and keeps the transport layer from silently becoming an estimator ([robot_localization documentation](https://docs.ros.org/en/rolling/p/robot_localization/), [snapshot coherency contract](../SNAPSHOT_COHERENCY_CONTRACT.md)).

**Status:** PROPOSED

## E. Sensor Calibration

### SD-10 - Calibration Ownership

**Question:** Where are sensor calibration parameters computed and approved?

**Proposed Value:** Compute calibration on the Raspberry Pi or engineering workstation using recorded data and a versioned calibration procedure. Transfer only validated parameters to the STM32 through an authenticated/configuration-controlled command path. The STM32 applies parameters during measurement processing and reports the active calibration version.

**Justification:** Calibration is data- and procedure-intensive rather than hard real-time, so an offline-capable host is the appropriate owner of computation. Applying the approved result on the STM32 makes snapshots self-consistent even when the Pi is absent. Calibration acceptance limits and mechanical zeroing remain commissioning inputs.

**Status:** PROPOSED

### SD-11 - Calibration Storage

**Question:** Where are approved calibration values persisted?

**Proposed Value:** Store a versioned, CRC-protected calibration record in STM32 internal flash using two slots or an equivalent power-loss-safe commit scheme. Include schema version, joint/sensor identity, offset/gain/limits, generation counter, and validity marker. Keep a host-side source copy for traceability; reject incomplete or invalid records and fall back to `UNCONFIGURED`/invalid measurements.

**Justification:** STM32 persistence keeps runtime behavior self-contained and avoids dependence on a live filesystem. A redundant record and validation marker prevent an interrupted flash write from becoming an apparently valid calibration. Flash endurance, reserved sectors, and exact parameter schema must be verified against the STM32F405 memory map before implementation.

**Status:** PROPOSED

### SD-12 - Authoritative Angle Representation

**Question:** What angle representation is authoritative at the STM32-to-Pi boundary?

**Proposed Value:** Use calibrated radians as the authoritative logical-joint representation in the host API. Preserve raw AS5600 counts and status/validity flags as diagnostics; use explicit little-endian fixed-point fields on the wire where the payload schema requires them, with a documented conversion to radians.

**Justification:** Radians match common robotics and ROS conventions and avoid forcing every consumer to repeat calibration. Raw counts remain essential for diagnosing wrap, magnet, and calibration faults. The existing payload currently carries raw angle and processed millidegrees, so a schema revision is required before changing the wire field rather than silently changing its meaning ([ROS 2 `JointState`](https://docs.ros.org/en/ros2_packages/rolling/api/sensor_msgs/msg/JointState.html), [SPI payload schema](../SPI_PAYLOAD_SCHEMA.md)).

**Status:** PROPOSED

## F. ROS 2 / Control Interface

### SD-13 - Required Joint State

**Question:** What minimum joint state must the STM32/Pi interface expose?

**Proposed Value:** Expose stable joint identity, position, velocity when measured or derived with a documented method, validity/status, acquisition timestamp, synchronization quality, and calibration version. Effort is optional until current/torque sensing is defined. The ROS-facing adapter should map standard `position`, `velocity`, and optional `effort` interfaces.

**Justification:** ROS 2 `joint_state_broadcaster` publishes the standard movement interfaces `position`, `velocity`, and `effort`; timestamp and validity are essential transport metadata even though they are not a standard movement field. The STM32 payload already provides per-record timestamps and flags, which should remain distinct from the outer frame assembly time ([joint state broadcaster documentation](https://control.ros.org/master/doc/ros2_controllers/joint_state_broadcaster/doc/userdoc.html), [SPI payload schema](../SPI_PAYLOAD_SCHEMA.md)).

**Status:** PROPOSED

### SD-14 - Required Command Interface

**Question:** What commands can the Pi issue, and how are they gated?

**Proposed Value:** Support only commands justified by the commissioned motor model: position and/or velocity command interfaces, plus explicit enable, disable, controlled stop, and emergency-stop semantics. Commands require fresh heartbeat, valid lifecycle state, valid configuration, and bounded transport; stale or unauthorized commands are rejected. Exact command payloads remain a Motor Service gate.

**Justification:** Standard command interfaces should be exposed only when the underlying actuator can guarantee their semantics; the repository explicitly excludes `SET_MOTOR_COMMAND` from the frozen SPI schema until Motor Service exists. Separating normal disable, controlled stop, and emergency stop prevents a generic command API from being mistaken for an independent safety function ([ros2_control hardware interfaces](https://control.ros.org/master/doc/ros2_control/hardware_interface/doc/hardware_interface_types_userdoc.html), [CAN service contract](../CAN_SERVICE_CONTRACT.md)).

**Status:** PROPOSED

## G. SPI Protocol Policy

### SD-15 - Fixed SPI Transaction

**Question:** What physical transaction size and wire baseline are used?

**Proposed Value:** Use a fixed maximum transaction/frame of 512 bytes with a maximum 490-byte payload, SPI Mode 0, little-endian multi-byte fields, CRC-32/ISO-HDLC, and pipelined request/response ownership. Do not truncate oversize payloads. Maximum clock remains an integration gate.

**Justification:** Fixed buffers make DMA ownership and worst-case timing deterministic, while the existing snapshot schema fits the 512-byte contract. The repository freeze specifies the exact header/payload/CRC budget and Mode 0; these are proposed here for CTO sign-off rather than re-researched as generic SPI practice ([contract v1 freeze](../CONTRACT_V1_FREEZE.md), [SPI contract](../SPI_CONTRACT.md)).

**Status:** PROPOSED

### SD-16 - GET_SNAPSHOT Priority

**Question:** Does an explicit snapshot request override an unsolicited publication?

**Proposed Value:** Yes. A valid correlated `GET_SNAPSHOT` response takes priority over an unsolicited snapshot, while preserving the DMA-owned frame until transaction completion. Unread replacement frames use the contract's replace-if-new policy and increment diagnostics.

**Justification:** Explicit request/response correlation is more deterministic for a host waiting on a particular sequence and avoids overwriting an active DMA buffer. The SPI service contract already requires immutable DMA buffers, deferred callbacks, and safe ownership transitions ([SPI service contract](../SPI_SERVICE_CONTRACT.md)).

**Status:** PROPOSED

### SD-17 - SPI Host Transaction Strategy

**Question:** How does the Pi learn that a complete response is ready and initiate transactions?

**Proposed Value:** Use a rising-edge `DATA_READY` GPIO interrupt for low-latency notification and a configurable periodic poll, initially 1 ms, as a recovery path. `DATA_READY` means a complete frame is staged, not merely that data changed; the Pi remains the SPI clock master.

**Justification:** The interrupt minimizes notification latency while polling provides resilience against missed edges or startup races. The fixed frame, pipelined response, and DATA_READY semantics are already defined by the project contract; the poll period and maximum SPI clock require Pi-driver integration testing ([SPI service contract](../SPI_SERVICE_CONTRACT.md), [Linux GPIO character-device API](https://docs.kernel.org/userspace-api/gpio/chardev.html)).

**Status:** PROPOSED

## H. Time Synchronization & Validity

### SD-20 - Loss of Time Synchronization

**Question:** What happens when accepted `TIME_SYNC` messages stop arriving?

**Proposed Value:** After five seconds without an accepted update, set `time_sync_valid=false`, mark new records and diagnostics `UNSYNCHRONIZED`, and continue acquisition if local monotonic time remains healthy. Do not present synchronized host time as valid. Escalate to `FAULT` or inhibit motion only if the safety and estimator requirements demonstrate that unsynchronized time is hazardous; that threshold requires CTO approval.

**Justification:** Continuing with explicit degraded quality preserves diagnostics while preventing stale offsets from masquerading as current synchronized measurements. The five-second timeout and exposed age/quality fields are frozen v1 contract behavior ([TIMESTAMP_SYNC_CONTRACT.md](../TIMESTAMP_SYNC_CONTRACT.md), [SPI payload schema](../SPI_PAYLOAD_SCHEMA.md)).

**Status:** PROPOSED

### SD-21 - Time Offset Validation

**Question:** Which offset changes are accepted as plausible?

**Proposed Value:** Before the first valid sync, accept only a configurable wide-range offset bounded by representable and deployment-specific limits. After synchronization, reject changes exceeding a configurable narrow bound, initially +/-1 second, and retain the last valid offset while reporting a diagnostic. Do not silently slew in v1; offset stepping is the documented behavior.

**Justification:** A two-stage gate distinguishes initial epoch acquisition from an implausible runtime jump. Retaining the last valid value prevents one malformed packet from corrupting every timestamp, while the diagnostic allows the Pi to investigate. The v1 contract explicitly defers two-way RTT estimation and slew correction to a future protocol version ([contract v1 freeze](../CONTRACT_V1_FREEZE.md)).

**Status:** PROPOSED

### SD-22 - Time Behaviour After Reset

**Question:** What synchronization state exists after an STM32 reset?

**Proposed Value:** Reset `time_sync_valid` to false and discard any prior volatile offset. Start a new monotonic local epoch and mark timestamps unsynchronized until a new accepted `TIME_SYNC` is processed. Require explicit re-synchronization before synchronized host-time claims or time-dependent motion policy are enabled.

**Justification:** A reset can invalidate the relationship between the Pi and STM32 execution timelines; reusing stale validity would create plausible-looking but incorrect timestamps. This is consistent with the repository's Pi-authority and reset-invalidates-sync model ([TIMESTAMP_SYNC_CONTRACT.md](../TIMESTAMP_SYNC_CONTRACT.md)).

**Status:** PROPOSED

## I. Recovery & Lifecycle

### SD-23 - Transient vs Persistent Fault Recovery

**Question:** How are transient failures retried and persistent failures escalated?

**Proposed Value:** Use bounded, service-specific retries for transient faults. A single I2C NACK or transport interruption may retry once or within a fixed time budget. Three consecutive failures, a violated freshness deadline, or any condition that makes safe operation uncertain enters `ERROR`. Recovery is owned by the System Manager and ends in `INACTIVE`; explicit activation is required.

**Justification:** Bounded retries improve availability without allowing an unresponsive peripheral to consume unbounded task time. The lifecycle contract makes `ERROR` inhibit normal outputs and requires recovery to end in `INACTIVE`; Health Monitor observes and recommends but does not silently recover services ([lifecycle contract](../LIFECYCLE_CONTRACT.md), [error handling strategy](../ERROR_HANDLING_STRATEGY.md)).

**Status:** PROPOSED

### SD-24 - System Restart and Recovery Behaviour

**Question:** What operational state follows reset or successful recovery?

**Proposed Value:** Return all services to `INACTIVE` after reset/configuration and after recovery. Activate in dependency order only from system/task context after configuration, calibration validity, time policy, and safety prerequisites pass. Never automatically resume motor motion solely because a peripheral recovered.

**Justification:** Explicit activation prevents an intermittent fault from causing an unattended return to motion. This matches the canonical lifecycle transition `ERROR -> INACTIVE` and the documented startup ordering: hardware initialization, RTOS objects, configuration, task creation, then activation ([lifecycle contract](../LIFECYCLE_CONTRACT.md), [contract v1 freeze](../CONTRACT_V1_FREEZE.md)).

**Status:** PROPOSED

## J. Independent Safety Architecture

### SD-25 - Independent Safety Mechanisms

**Question:** Which safety mechanisms exist outside STM32/Pi application software?

**Proposed Value:** Before motion approval, document and test an independent emergency-stop path, hardware motor-disable or power-removal path, watchdog behavior, actuator brake/stop behavior, fault indication, reset behavior, and any safety-rated controller or relay. The software heartbeat and CAN policies are supplementary controls, not the sole safety layer. The CTO must approve the resulting safety architecture and required PL/SIL.

**Justification:** A general-purpose MCU and Raspberry Pi software stack cannot by itself establish an independent safety function. ISO 13849-1 and IEC 62061 require the machine's safety-related control functions to be specified, designed, and validated against the identified risk. No independent safety mechanism is evidenced by the current repository; this is an explicit hardware and commissioning gate ([ISO 13849-1:2023](https://www.iso.org/standard/73481.html), [IEC 62061:2021](https://webstore.iec.ch/en/publication/59927)).

**Status:** PROPOSED

## CTO Safety Approval Checklist

The following items require explicit human approval and, where applicable, a machine risk assessment and commissioning evidence:

- [ ] SD-02: approve the failure taxonomy, safety functions, and required PL/SIL method and target.
- [ ] SD-03: approve Pi heartbeat timeout, controlled-stop sequence, final motor-disable mechanism, and measured stop time.
- [ ] SD-04: approve motor feedback timeout, consecutive-failure threshold, and single-motor versus whole-system response.
- [ ] SD-06: approve CAN bus-off recovery, retry window, escalation threshold, and command inhibition policy.
- [ ] SD-05: approve CAN bitrate and bit timing after exact motor-controller, transceiver, topology, and load verification.
- [ ] SD-14: approve the commissioned command set and emergency-stop semantics before motor commands are frozen.
- [ ] SD-20: approve whether prolonged loss of synchronized time inhibits motion or only degrades estimation.
- [ ] SD-23: approve retry and persistent-fault behavior where actuator outputs are affected.
- [ ] SD-24: approve explicit reactivation requirements after reset and recovery.
- [ ] SD-25: identify, document, and test independent E-stop, motor-disable, watchdog, brake, and power-safety mechanisms.

## Open Assumptions and Integration Gates

1. The exact MKS Servo42/Servo57 model, firmware, CAN manual, and transceiver characteristics must be confirmed before treating 1 Mbps as an approved network value.
2. CAN bitrate, sample point, SJW, TX ownership, queueing, retry behavior, and bus-off recovery remain open under the CAN service contract.
3. Maximum SPI clock remains open until Raspberry Pi driver timing, GPIO notification behavior, STM32 DMA timing, and signal integrity are reviewed together.
4. The current firmware implements only one sensor channel and one configured motor; the six-axis/eight-motor model is the target architecture, not proof of completed implementation.
5. The current SPI service is a scaffold; contract behavior must be verified with DMA, buffer ownership, malformed frames, aborted NSS, and host-stall tests.
6. The current payload uses processed millidegrees rather than a finalized radians field; SD-12 requires an explicit schema/version decision before wire compatibility changes.
7. Stop-time, actuator inertia, brake behavior, safe torque-off capability, and hardware E-stop response must be measured on the assembled robot.
8. Calibration flash sectors, endurance, power-loss behavior, and parameter authentication/versioning must be verified against the STM32F405 memory map and deployment process.

## References

- [ISO 13849-1:2023 - Safety of machinery](https://www.iso.org/standard/73481.html)
- [IEC 62061:2021 - Functional safety of safety-related control systems](https://webstore.iec.ch/en/publication/59927)
- [ST STM32F405/415 documentation](https://www.st.com/en/microcontrollers-microprocessors/stm32f405-415/documentation.html)
- [CAN in Automation knowledge base](https://www.can-cia.org/can-knowledge/)
- [ros2_control joint state broadcaster](https://control.ros.org/master/doc/ros2_controllers/joint_state_broadcaster/doc/userdoc.html)
- [ros2_control hardware interface types](https://control.ros.org/master/doc/ros2_control/hardware_interface/doc/hardware_interface_types_userdoc.html)
- [ROS 2 `sensor_msgs/msg/JointState`](https://docs.ros.org/en/ros2_packages/rolling/api/sensor_msgs/msg/JointState.html)
- [Linux GPIO character-device API](https://docs.kernel.org/userspace-api/gpio/chardev.html)
- [Repository SPI service contract](../SPI_SERVICE_CONTRACT.md)
- [Repository SPI contract](../SPI_CONTRACT.md)
- [Repository SPI payload schema](../SPI_PAYLOAD_SCHEMA.md)
- [Repository snapshot coherency contract](../SNAPSHOT_COHERENCY_CONTRACT.md)
- [Repository timestamp synchronization contract](../TIMESTAMP_SYNC_CONTRACT.md)
- [Repository lifecycle contract](../LIFECYCLE_CONTRACT.md)
- [Repository CAN service contract](../CAN_SERVICE_CONTRACT.md)
- [Repository v1 freeze specification](../CONTRACT_V1_FREEZE.md)

## Approval Record

| Decision range | CTO disposition | Date | Notes |
| --- | --- | --- | --- |
| SD-01 to SD-25 | Pending | | |
