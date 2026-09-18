# Karetao Research, Questions, TODOs and Decisions — Collated Working File

> Collated from the files currently held in `final list/` on branch `doc/research-and-decisions`.
 > This is an un-reconciled working collation. Duplicate, conflicting, obsolete, or superseded material has intentionally not been resolved.

---

# Source 1: final list/ARCHITECTURE_DECISIONS.md

# Architecture Decisions

Framework placeholder for long-lived Karetao system and architecture decisions.

---

# Source 2: final list/CAN_Module_TODO.md

# CAN Module TODO (STM32 + TJA1050 + CANable V2)

## Current State Review

- `CanService` is implemented with lifecycle gating, motor registration, TX priority queue, bounded retries, RX decode path, and bus-off recovery scaffolding (`App/Src/can_service.c`).
- CAN runs in normal mode and is processed in the default FreeRTOS task loop through `CanService_Process()` (`Core/Src/main.c`).
- Hardware pins are configured for CAN1 on `PB8` (RX) and `PB9` (TX) (`Core/Src/stm32f4xx_hal_msp.c`).
- Only one motor is currently pre-registered in app startup config (`App/Src/app_init.c`).
- Current generated CAN timing is `Prescaler=16`, `BS1=11TQ`, `BS2=2TQ` (not yet aligned to a validated real-hardware target) (`Core/Src/main.c`).
- Host tests currently cover `can_tx_policy.c`, but not full `can_service.c` behavior with HAL integration (`tests/host/CMakeLists.txt`).
- Existing docs already mark CAN bitrate/physical-layer validation as an integration gate (`Documentation/CAN_SERVICE_CONTRACT.md`, `Documentation/CAN_BIT_TIMING_EVIDENCE.md`).

## TODO List for Real-Life Bring-Up and Testing

### 1) Hardware Bring-Up (STM32 + TJA1050)
- [ ] Confirm transceiver wiring: CAN1_TX -> TJA1050 TXD, CAN1_RX -> TJA1050 RXD, shared GND, and stable 5V/3.3V domain compatibility.
- [ ] Add/verify proper 120-ohm termination at both physical bus ends.
- [ ] Validate CANH/CANL idle and dominant levels with scope or analyzer before motion commands.
- [ ] Document the exact bench topology (cable length, stubs, node count, termination locations).

### 2) Bitrate and Controller Configuration
- [ ] Decide initial real-test bitrate (e.g., 500 kbps or 1 Mbps) and update CubeMX/HAL CAN timing settings to match measured behavior.
- [ ] Verify CANable V2 bitrate matches STM32 bitrate exactly.
- [ ] Re-check sample point/SJW margin against oscillator tolerance for STM32 + bus layout.
- [ ] Record finalized timing values and rationale in `Documentation/CAN_BIT_TIMING_EVIDENCE.md`.

### 3) Firmware Readiness Gaps Before Bench Motion
- [ ] Add duplicate CAN ID rejection in `CanService_RegisterMotor()` to prevent ambiguous RX frame ownership.
- [ ] Add explicit HAL error diagnostics mapping (TX/RX/error counters by error class).
- [ ] Add RX FIFO overflow tracking/handling and expose it through CAN diagnostics.
- [ ] Define and implement response timeout expectations per poll/command path.
- [ ] Confirm emergency-stop behavior policy during lifecycle `ERROR` and enforce/document selected behavior.

### 4) Observability for Bench Testing
- [ ] Expose runtime CAN diagnostics in a host-visible channel (SPI snapshot/log/telemetry): lifecycle state, bus-off count, queue drops, retry-exhausted count, RX ok/decode error counts.
- [ ] Add timestamped trace points for command TX, response RX, and bus-off recovery attempts.
- [ ] Add a simple bench-test checklist to log pass/fail for power-up, idle, command, and fault-recovery scenarios.

### 5) CANable V2 Test Procedure
- [ ] Create a repeatable CANable capture script/procedure (startup capture, command-response capture, fault injection capture).
- [ ] Validate that expected MKS command IDs and response frames appear on the bus with correct DLC/payload.
- [ ] Verify poll traffic cadence at default 20 ms scheduler period and confirm no unintended bus flooding.
- [ ] Run long-duration soak capture to check for dropped frames, decode errors, or recurring bus-off.

### 6) Fault Injection and Recovery Validation
- [ ] Test bus disconnection/reconnection and confirm bus-off detection, inhibition of normal commands, and recovery back to inactive state.
- [ ] Confirm `CanService_Activate()` is required and sufficient to re-enable normal commands after recovery.
- [ ] Test mailbox pressure/temporary TX failures and validate retry and drop diagnostics behavior.
- [ ] Verify behavior when receiving unknown CAN IDs and malformed DLC/payload frames.

### 7) Test Coverage and Automation
- [ ] Add host-side tests for `can_service` logic that does not require real CAN hardware (registration constraints, scheduler behavior, queue/retry edge cases via mocks).
- [ ] Add hardware-in-the-loop test notes for STM32 + TJA1050 + CANable in Documentation with required tooling and expected outputs.
- [ ] Update contract status once integration gates are closed with measured evidence.

### 8) Commissioning Expansion
- [ ] Expand `s_mks_motors` and joint mapping only after each added motor passes single-node bench validation.
- [ ] Validate per-motor direction, ID, and mapping consistency before enabling multi-motor motion tests.
- [ ] Freeze a known-good CAN commissioning baseline (timing + topology + firmware revision + test evidence).

---

# Source 3: final list/CTO_DECISION_BRIEF.md

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

---

# Source 4: final list/CTO_DECISION_FINAL.md

# CTO Final Decisions - v1.0 Firmware Contracts

**Decision authority:** CTO review of `CTO_DECISION_BRIEF.md`

**Date:** 2026-09-07

## Executive Summary

I approve the v1 architecture with the modifications and conditions recorded below. The baseline is a 100 Hz sensor/state system, bounded timestamps, Pi-owned estimator history, calibrated joint representations, fixed 512-byte SPI framing, explicit lifecycle recovery, and fail-closed actuator behavior.

The principal modifications are: safety classifications are treated as firmware response levels rather than a claimed PL/SIL rating; CAN bitrate and SPI clock are controlled configuration baselines that require physical integration validation; time-dependent motion is inhibited after synchronization expires; and all motor command semantics remain subordinate to the independent safety path.

This sign-off approves the firmware contract baseline for implementation. It does not certify the assembled robot as safe. Release for energized motion remains conditional on the machine risk assessment, independent safety validation, measured stopping performance, exact motor-controller verification, and the acceptance tests listed below.

## Decision Table

| ID | Decision Area | Proposed from brief | Final Decision | Reasoning |
| --- | --- | --- | --- | --- |
| SD-01 | System timing | 100 Hz; <2 ms transport target; 5 MHz SPI candidate | MODIFIED | Approve 100 Hz and the latency budget; make 5 MHz the initial maximum configuration, subject to Pi/DMA validation. |
| SD-02 | Failure classification | Four operational levels mapped to PL/SIL | MODIFIED | Approve the four levels, but do not infer PL/SIL from them; the machine risk assessment owns the formal safety target. |
| SD-03 | Pi communication loss | 500 ms heartbeat; controlled stop then disable | APPROVED | Stale motion commands must not be held; timeout and stop behavior are explicit and testable. |
| SD-04 | Motor timeout | 5x feedback period; three failures escalate | APPROVED | This gives bounded tolerance for jitter while preventing persistent loss of feedback from remaining active. |
| SD-05 | CAN network | 1 Mbps; 50-60% load target | MODIFIED | Approve 1 Mbps as the v1 target only after exact controller, transceiver, clock, wiring, and load validation. |
| SD-06 | CAN failure | Bus-off recovery; three events escalate | APPROVED | Recovery is bounded and repeated instability inhibits further actuation. |
| SD-07 | Joint/motor mapping | Deterministic one-to-one mapping | APPROVED | Stable identity and transmission metadata are required for correct state and command interpretation. |
| SD-08 | Temporal alignment | Below 5 ms; target below 1 ms | APPROVED | Independent acquisition timestamps and a 5 ms maximum support the 100 Hz estimator baseline. |
| SD-09 | History ownership | Pi/EKF owns history | APPROVED | The Pi owns delayed-measurement handling; the STM32 remains a bounded latest-value producer. |
| SD-10 | Calibration ownership | Compute on Pi/workstation | APPROVED | Offline calibration is more controllable and auditable than embedding calibration computation in real-time firmware. |
| SD-11 | Calibration storage | Redundant versioned STM32 flash | APPROVED | Local persistence preserves self-contained operation and power-loss-safe records protect calibration integrity. |
| SD-12 | Angle representation | Calibrated radians; raw diagnostic counts | MODIFIED | Approve radians at the host API, but require a versioned wire-schema change before replacing the current millidegree field. |
| SD-13 | Joint state | Position, velocity, validity, timestamp | APPROVED | This maps cleanly to ROS 2 interfaces while retaining transport-specific quality metadata. |
| SD-14 | Command interface | Position/velocity plus enable/disable | MODIFIED | Approve only commissioned command modes and require heartbeat, lifecycle, freshness, and independent safety gating. |
| SD-15 | SPI transaction | 512-byte frame; 490-byte payload; Mode 0 | APPROVED | The fixed frame and ownership model are deterministic and match the frozen v1 contract. |
| SD-16 | Snapshot priority | Correlated request takes priority | APPROVED | Explicit requests must not be lost, and active DMA buffers must remain immutable. |
| SD-17 | Host strategy | DATA_READY interrupt plus 1 ms poll | APPROVED | Interrupt notification gives latency; polling provides recovery from missed notification events. |
| SD-18 | Timestamp accuracy | At or below +/-1 ms | APPROVED | This is an appropriate initial error budget for a 100 Hz estimator and is measurable. |
| SD-19 | TIME_SYNC frequency | 1 Hz, configurable to 10 Hz | APPROVED | One hertz is sufficient as a baseline for expected oscillator drift; higher frequency remains available when measured. |
| SD-20 | Sync loss | Unsynchronized after 5 s; continue degraded | MODIFIED | Continue diagnostics and acquisition, but inhibit time-dependent motion commands until synchronization returns. |
| SD-21 | Offset validation | Wide initial, narrow subsequent bound | APPROVED | The two-stage policy rejects implausible runtime jumps without blocking initial epoch acquisition. |
| SD-22 | Reset time behavior | Reset validity until new sync | APPROVED | Reusing an old offset after reset could produce plausible but incorrect timestamps. |
| SD-23 | Fault recovery | Bounded retries; persistent faults enter ERROR | APPROVED | Recovery must be bounded and must not silently reactivate actuation. |
| SD-24 | Restart/recovery | Return to INACTIVE; explicit activation | APPROVED | Manual reactivation prevents an intermittent fault from causing unattended motion. |
| SD-25 | Independent safety | E-stop, motor disable, watchdog, power safety | MODIFIED | Approve the required safety layers as release gates; firmware alone is not accepted as the independent safety function. |

## Detailed Decisions

### SD-01 - System Timing Requirements

- **Final Decision:** MODIFIED
- **Value/Policy:** Use 100 Hz for sensor acquisition targets, STM32 snapshot publication, Pi consumption, EKF updates, and the initial control loop. Budget less than one 10 ms cycle for freshness and target less than 2 ms for transport/assembly latency. Configure 5 MHz as the initial maximum SPI clock, subject to Raspberry Pi driver, signal-integrity, and STM32 DMA acceptance testing.
- **Reasoning:** The 100 Hz baseline is coherent with the proposed estimator and control architecture and leaves scheduling margin. The 5 MHz value gives 819.2 us of wire time for a 512-byte frame, but it is a configuration limit until the complete electrical and software path is tested.

### SD-02 - System-Wide Failure Classification

- **Final Decision:** MODIFIED
- **Value/Policy:** Adopt `INFORMATIONAL`, `DEGRADED`, `FAULT`, and `SAFETY_CRITICAL` as firmware response levels. Every event must define detection, response, recovery owner, and output inhibit behavior. Do not claim a PL or SIL from this taxonomy; the machine risk assessment under ISO 13849-1:2023 and/or IEC 62061:2021 determines the formal safety target.
- **Reasoning:** A common vocabulary makes firmware behavior deterministic and auditable. The standards define methods and requirements for safety-related systems but do not select the required level for this robot.

### SD-03 - Raspberry Pi Communication Loss

- **Final Decision:** APPROVED
- **Value/Policy:** Require a valid monotonic heartbeat and fresh command stream. After 500 ms without a valid heartbeat, reject new motion commands, issue a controlled stop if the transport is usable, then assert the motor-disable path. Never hold the last motion command.
- **Reasoning:** This bounds the time stale commands can affect the machine and uses a safer response than command retention. The assembled system must demonstrate the resulting stop time and verify that motor disable remains effective if software transport is unavailable.

### SD-04 - Motor Feedback/Command Timeout

- **Final Decision:** APPROVED
- **Value/Policy:** Set the response timeout to five times the commissioned feedback period. Treat one miss as degraded; after three consecutive misses for a motor, inhibit that motor and escalate to `FAULT`. Escalate to a system stop where the affected motor can create a hazardous state.
- **Reasoning:** A multiple-of-period timeout tolerates arbitration and scheduling jitter while detecting a failed controller. The per-motor versus whole-system response must be confirmed during mechanical risk analysis.

### SD-05 - CAN Network Requirements

- **Final Decision:** MODIFIED
- **Value/Policy:** Use 1 Mbps as the v1 nominal CAN bitrate, standard 11-bit identifiers, and a design target below 50-60% measured average bus load. Before production freeze, verify the exact MKS controller and transceiver, termination, topology, cable length, APB1-derived bit timing, sample point, SJW, retransmission, and worst-case command/poll traffic.
- **Reasoning:** 1 Mbps is a reasonable initial target but cannot be approved solely from a generic motor-product assumption. Physical-layer timing and measured worst-case load determine whether this target is reliable.

### SD-06 - CAN Bus Failure

- **Final Decision:** APPROVED
- **Value/Policy:** Detect bus-off, inhibit normal motor commands, perform bounded controller-defined recovery from task context, and log each attempt. Use an escalating recovery delay. Escalate to `ERROR` after three bus-off events in a configurable rolling window or after recovery timeout; require explicit activation before motion resumes.
- **Reasoning:** Repeated bus instability must not repeatedly re-enable actuation. The exact bxCAN recovery sequence and transceiver behavior must be verified against the STM32 reference material and hardware test results.

### SD-07 - Joint/Motor Mapping

- **Final Decision:** APPROVED
- **Value/Policy:** Use a versioned deterministic mapping of logical joint to AS5600 sensor ID to motor index/CAN ID, including direction, zero offset, and transmission ratio. Reject duplicate sensor or CAN-ID assignments. Differential or mechanically coupled joints require a separate mapping revision.
- **Reasoning:** State estimation and commands cannot be trusted without stable identity and transmission metadata. The final physical mapping remains a commissioning artifact, but the firmware contract is approved.

### SD-08 - Motor/Joint Temporal Alignment

- **Final Decision:** APPROVED
- **Value/Policy:** Require measured joint/motor observation skew below 5 ms in normal operation and target below 1 ms for dynamic joints. Preserve independent acquisition timestamps and flag or down-weight samples beyond the configured skew budget.
- **Reasoning:** A common snapshot does not imply simultaneous acquisition. Independent timestamps let the Pi estimator account for sequential sampling and transport delay.

### SD-09 - Measurement History Ownership

- **Final Decision:** APPROVED
- **Value/Policy:** The Raspberry Pi/EKF owns measurement queues, delayed-data handling, and estimator history. The STM32 owns bounded latest-value caches and publishes coherent records with acquisition timestamps, validity, synchronization quality, and freshness information.
- **Reasoning:** The Pi has the estimator context and resources for history management. Keeping history out of the STM32 avoids unbounded memory and timing behavior in the sensor hub.

### SD-10 - Calibration Ownership

- **Final Decision:** APPROVED
- **Value/Policy:** Compute calibration on the Pi or engineering workstation from recorded data using a versioned procedure. Transfer only validated parameters through a controlled configuration path. The STM32 applies the parameters and reports the active calibration version.
- **Reasoning:** Offline calibration is easier to inspect, reproduce, and approve. Runtime application on the STM32 keeps sensor output consistent when the Pi is absent.

### SD-11 - Calibration Storage

- **Final Decision:** APPROVED
- **Value/Policy:** Store versioned, CRC-protected calibration records in two STM32 flash slots or an equivalent power-loss-safe scheme. Include schema version, identity, parameters, generation counter, and validity marker. Keep a host-side source copy and reject invalid records.
- **Reasoning:** Local persistence supports self-contained operation, while redundant records protect against interrupted writes. Flash sector allocation and endurance must be verified before implementation.

### SD-12 - Authoritative Angle Representation

- **Final Decision:** MODIFIED
- **Value/Policy:** Use calibrated radians as the authoritative host/API representation and retain raw AS5600 counts for diagnostics. Do not silently reinterpret the current processed millidegree wire field; introduce radians through an explicit payload schema version and conversion definition.
- **Reasoning:** Radians are the correct robotics-facing representation, but wire compatibility must be preserved deliberately. The current payload schema means this decision requires a versioned protocol change rather than a field-level semantic substitution.

### SD-13 - Required Joint State

- **Final Decision:** APPROVED
- **Value/Policy:** Expose stable joint identity, position, velocity when measured or derived, validity/status, acquisition timestamp, synchronization quality, and calibration version. Effort remains optional until torque/current sensing is defined. Map the ROS-facing adapter to standard `position`, `velocity`, and optional `effort` interfaces.
- **Reasoning:** This matches the standard ROS 2 movement interface while retaining the metadata required for estimator correctness. It also aligns with the existing per-record timestamp and validity fields.

### SD-14 - Required Command Interface

- **Final Decision:** MODIFIED
- **Value/Policy:** Support only commissioned position and/or velocity commands, plus enable, disable, and controlled-stop operations. Every command requires a fresh heartbeat, valid lifecycle state, valid calibration/configuration, and transport integrity. Emergency stop is a separately specified safety function and must not depend solely on this application command.
- **Reasoning:** Command modes must reflect actual actuator capabilities and commissioning evidence. Separating ordinary commands from emergency stop prevents a normal protocol path from being mistaken for an independent safety mechanism.

### SD-15 - Fixed SPI Transaction

- **Final Decision:** APPROVED
- **Value/Policy:** Use a fixed maximum 512-byte frame, maximum 490-byte payload, SPI Mode 0, little-endian multi-byte fields, CRC-32/ISO-HDLC, and pipelined request/response ownership. Reject oversize payloads; never truncate them.
- **Reasoning:** Fixed sizing makes DMA buffers, ownership, and worst-case transaction timing deterministic. These values match the repository v1 contract and support the current six-sensor/eight-motor snapshot target.

### SD-16 - GET_SNAPSHOT Priority

- **Final Decision:** APPROVED
- **Value/Policy:** A valid correlated `GET_SNAPSHOT` response takes priority over an unsolicited snapshot. The active DMA buffer remains immutable until transaction completion; unread replacement frames follow replace-if-new policy and increment diagnostics.
- **Reasoning:** Explicit request/response correlation is deterministic for the host. Buffer ownership rules prevent a high-priority request from corrupting an in-flight response.

### SD-17 - SPI Host Transaction Strategy

- **Final Decision:** APPROVED
- **Value/Policy:** Use rising-edge `DATA_READY` GPIO notification for low latency and a configurable periodic poll, initially 1 ms, as a recovery path. `DATA_READY` means a complete frame is staged; the Pi remains SPI clock master.
- **Reasoning:** The interrupt path minimizes notification latency, while polling recovers from missed edges and startup races. The 1 ms poll and 5 MHz initial clock must be verified with the Pi driver and DMA implementation.

### SD-18 - Timestamp Accuracy

- **Final Decision:** APPROVED
- **Value/Policy:** Target timestamp error at or below +/-1 ms relative to the shared STM32/Pi time model. Capture timestamps immediately after successful measurement decoding and expose synchronization validity and age.
- **Reasoning:** At 100 Hz, 1 ms is a meaningful and testable fraction of a sample period. Explicit validity prevents unsynchronized data from being treated as precise host-time data.

### SD-19 - TIME_SYNC Frequency

- **Final Decision:** APPROVED
- **Value/Policy:** Send `TIME_SYNC` at 1 Hz nominal, configurable to 10 Hz. Invalidate synchronization after five seconds without an accepted update.
- **Reasoning:** The baseline accommodates expected oscillator drift while avoiding unnecessary traffic. A higher rate is available when measured drift or estimator performance requires it.

### SD-20 - Loss of Time Synchronization

- **Final Decision:** MODIFIED
- **Value/Policy:** After five seconds without an accepted update, set `time_sync_valid=false`, mark new records unsynchronized, and continue local acquisition and diagnostics. Reject or inhibit time-dependent motion commands until synchronization returns; allow explicitly defined non-motion service operations to continue.
- **Reasoning:** Diagnostics should remain available during a clock-service fault, but motion that depends on host-time alignment must not use stale timing. This is a stricter operational response than merely degrading all behavior and is appropriate for the estimator/control boundary.

### SD-21 - Time Offset Validation

- **Final Decision:** APPROVED
- **Value/Policy:** Permit a configurable wide initial offset range, then reject runtime changes beyond a configurable narrow limit initially set to +/-1 second. Retain the last accepted offset, report the rejection, and do not silently slew in v1.
- **Reasoning:** Initial synchronization and runtime correction have different plausibility requirements. Retaining the last valid offset prevents one malformed update from corrupting every subsequent timestamp.

### SD-22 - Time Behaviour After Reset

- **Final Decision:** APPROVED
- **Value/Policy:** Clear `time_sync_valid` and discard the volatile offset after reset. Mark timestamps unsynchronized until a new accepted `TIME_SYNC` is processed; do not enable time-dependent motion policy before resynchronization.
- **Reasoning:** A reset invalidates the previous relationship between the Pi and STM32 execution timelines. Reusing stale validity could produce plausible but incorrect measurements.

### SD-23 - Transient vs Persistent Fault Recovery

- **Final Decision:** APPROVED
- **Value/Policy:** Use bounded service-specific retries for transient failures. A persistent failure, three consecutive failures, a freshness deadline violation, or uncertain safe operation enters `ERROR`. Recovery is owned by the System Manager and ends in `INACTIVE`.
- **Reasoning:** Bounded retries improve availability without permitting an unresponsive peripheral to consume unbounded time. Requiring `INACTIVE` after recovery prevents automatic return to actuation.

### SD-24 - System Restart and Recovery Behaviour

- **Final Decision:** APPROVED
- **Value/Policy:** Return services to `INACTIVE` after reset, configuration, and recovery. Reactivate only in dependency order from system/task context after configuration, calibration, time, and safety prerequisites pass. Never automatically resume motor motion because a peripheral recovered.
- **Reasoning:** Explicit activation makes restart behavior predictable and prevents unattended motion after an intermittent fault. This matches the canonical lifecycle contract.

### SD-25 - Independent Safety Mechanisms

- **Final Decision:** MODIFIED
- **Value/Policy:** Require, before energized-motion release, a documented and tested independent E-stop path, hardware motor-disable or power-removal path, watchdog behavior, actuator stop/brake behavior, fault indication, reset behavior, and applicable safety-rated relay/controller. STM32/Pi heartbeat and CAN policies are supplementary controls only.
- **Reasoning:** General-purpose application software cannot be accepted as the sole independent safety function. The required safety architecture and PL/SIL target must be established by the machine risk assessment and validated on the assembled robot.

## Clarifying Questions Asked (and Answers Received)

No questions were asked before this sign-off. The brief and repository contracts were sufficiently clear to establish the v1 firmware baseline. The unresolved hardware and commissioning items are recorded as release conditions rather than silently assumed.

## Final Approval

I, the undersigned CTO, have reviewed and approved the above decisions as the v1.0 firmware contract baseline, subject to the conditions below. This approval authorizes implementation and verification of the contracts; it does not authorize energized robot operation until the safety release conditions are satisfied.

**CTO Name:** _________________________________

**Date:** 2026-09-07

**Signature:** _________________________________

### Exceptions / Conditions

1. Complete and approve the machine risk assessment, including required safety functions and PL/SIL target, before motion release.
2. Validate the independent E-stop and motor-disable path, measured stop time, watchdog behavior, and actuator brake/power behavior on the assembled system.
3. Verify exact MKS controller support, CAN physical topology, APB1-derived bit timing, worst-case bus load, recovery behavior, and termination before freezing SD-05 and production CAN configuration.
4. Validate the initial 5 MHz SPI limit, 1 ms polling fallback, GPIO notification, DMA timing, signal integrity, and host-stall recovery with the Raspberry Pi.
5. Version the radians representation before changing the current processed-millidegree wire field.
6. Complete calibration flash endurance, power-loss, schema, and parameter-integrity tests.
7. Treat any failure of these conditions as a release blocker for energized motion, not as a reason to weaken the approved firmware behavior.

---

# Source 5: final list/QUESTIONS.md

# Karetao Project Questions Register

This file is the canonical register of project questions that must be answered before the corresponding requirements, interfaces, implementation decisions, or release gates can be considered complete.

Questions are grouped by topic. Answers should be recorded against the question, with a reference to the decision, requirement, test result, or other authoritative document where appropriate.

## 1. System Scope and Architecture

1. What is the complete end-to-end Karetao system architecture, including the STM32, Raspberry Pi, ROS 2, MoveIt 2, ros2_control, and optional EKF?
2. Which components are mandatory for the first operational release, and which are optional or deferred?
3. What constitutes a fully functioning Karetao system?
4. What exact conditions must be satisfied before motion is permitted?
5. Which subsystem has final authority to permit or inhibit motion?
6. How are subsystem health states exposed and evaluated?
7. What happens if any required subsystem becomes unavailable during operation?
8. What is the required system startup, initialization, and shutdown sequence?
9. What is the required recovery sequence after a system fault?
10. Which interfaces between the major Karetao sub-repositories are authoritative?

## 2. User Interface and Command Model

11. How does the user specify the desired end-effector position?
12. Does the user provide XYZ position only, or a complete 3D pose including orientation?
13. If orientation is specified, what representation is used?
14. What coordinate frame is used for user commands?
15. What coordinate frames are required throughout the system?
16. How are invalid, unreachable, or unsafe target poses handled?
17. What feedback does the user receive when a command is accepted, rejected, or interrupted?
18. Can the user command individual joints directly, or only end-effector poses?
19. What command rate and update behaviour are required?

## 3. Mechanical Configuration and Degrees of Freedom

20. What are the exact mechanical joint definitions and names?
21. Are there exactly six controllable mechanical degrees of freedom?
22. What are the limits, zero positions, and positive directions of each joint?
23. Which joints contain gearboxes?
24. How are joints 1–4 mechanically related to the X, Y, Z, and wrist axes?
25. How exactly does the two-motor differential end effector map motor motion to its two rotational degrees of freedom?
26. What are the mathematical forward and inverse mappings for the differential mechanism?
27. What are the mechanical limits and safe operating limits of the differential end effector?
28. Are there mechanical couplings, backlash, compliance, or other effects that must be represented in the control model?
29. What is the authoritative joint naming and ordering convention?

## 4. Sensors and Sensor Data

30. Which sensors are installed on the STM32 sensor hub?
31. What physical quantity does each sensor measure?
32. What are the range, resolution, accuracy, noise characteristics, and expected update rate of each sensor?
33. What sensor acquisition rate is required for normal operation?
34. Is 500 Hz a hard requirement or a target for EKF sampling?
35. Which sensors are sampled synchronously?
36. What constitutes a valid sensor sample?
37. How are missing, stale, invalid, or out-of-range sensor values detected?
38. What maximum sensor-data age is acceptable before motion must be inhibited?
39. What timestamp source is authoritative?
40. What timestamp synchronization accuracy is required between the STM32 and Raspberry Pi?
41. How is sensor calibration performed?
42. What calibration data must be retained, and where is it stored?
43. What happens when calibration is missing, invalid, or outside permitted limits?

## 5. STM32 ↔ Raspberry Pi Integration

44. What is the authoritative STM32-to-Raspberry-Pi transport and protocol?
45. What is the complete message structure in each direction?
46. What commands can the Raspberry Pi send to the STM32?
47. What sensor and health information does the STM32 send to the Raspberry Pi?
48. How are commands acknowledged?
49. What constitutes a valid command acknowledgement?
50. What acknowledgement timeout is permitted?
51. What happens when a command is not acknowledged?
52. What happens when acknowledgements are delayed, duplicated, or inconsistent?
53. How are communication failures detected?
54. What communication failure response is required?
55. What data integrity, sequencing, and freshness checks are required?
56. What is the required maximum communication latency and jitter?
57. How is the interface versioned and kept compatible across the two systems?

## 6. Motor Control and ros2_control

58. What is the authoritative motor command interface?
59. Which subsystem converts ROS joint commands into STM32 motor commands?
60. How are motor commands mapped to physical joints?
61. How are gearbox ratios represented?
62. How is the differential end-effector mapping represented in ros2_control?
63. What command, state, and feedback interfaces are required by ros2_control?
64. How is motor-command acknowledgement exposed to ros2_control?
65. What happens if the STM32 does not acknowledge a motor command?
66. What happens if motor feedback disagrees with the commanded state?
67. What command timeout or watchdog behaviour is required?
68. What is the required motor-control update rate?
69. How are joint limits enforced?
70. How are velocity, acceleration, and other motion limits enforced?

## 7. MoveIt 2 and Motion Planning

71. What MoveIt 2 planning model is required?
72. What robot description format and source are authoritative?
73. How are joint limits supplied to MoveIt 2?
74. What collision model is required?
75. What self-collision and environment-collision constraints are required?
76. How are unreachable or collision-producing trajectories handled?
77. What planner configuration is required for the first release?
78. How is a planned trajectory validated before execution?
79. What happens if the system becomes unhealthy while a trajectory is executing?
80. How is trajectory execution cancelled or stopped after a fault?

## 8. EKF and State Estimation

81. Is an EKF required for the first operational release?
82. If used, which sensor measurements are fused?
83. What state variables does the EKF estimate?
84. What is the required EKF update rate?
85. Is 500 Hz required for the EKF, and can the complete sensor/communication/control chain sustain it?
86. What maximum input-data age and latency can the EKF tolerate?
87. How are missing or invalid measurements handled?
88. How is EKF health determined?
89. What happens to motion if the EKF becomes unhealthy?
90. Which estimated states are exposed to ros2_control or MoveIt 2?

## 9. Safety and Fault Handling

91. What exact faults must cause immediate motion inhibition?
92. Does any sensor-data failure require an immediate stop, or are there defined tolerances for transient failures?
93. Does any unacknowledged motor command require an immediate stop?
94. What does “stop immediately” mean in measurable system terms?
95. What is the maximum permitted fault-to-motion-stop latency?
96. Which subsystem owns the emergency-stop function?
97. Is there a separate physical E-stop, and how is it integrated?
98. What is the safe state of each motor and actuator after a fault?
99. Can motion resume automatically after recovery, or must an explicit reset be performed?
100. What conditions are required before motion can resume?
101. How are faults latched, reported, logged, and cleared?
102. What safety standards or engineering practices must the project comply with?
103. What safety validation and acceptance tests are required before physical motion?

## 10. Calibration, Configuration, and Startup

104. What configuration values are required before the system can operate?
105. Which values are fixed hardware parameters and which are runtime configuration?
106. Where are calibration and configuration values stored?
107. How are configuration versions managed?
108. What startup self-tests are required?
109. What must be verified before enabling motor power?
110. What conditions prevent startup from progressing to an armed state?
111. How are configuration or calibration mismatches detected?
112. What is the required procedure for commissioning a new or modified arm?

## 11. Testing and Acceptance

113. What is the required hardware-integration test sequence?
114. What is the minimum test required to prove valid STM32 sensor data?
115. What is the minimum test required to prove valid motor commands?
116. What proves that STM32 command acknowledgements are reliable?
117. What proves that sensor-data failure inhibits motion?
118. What proves that missing motor acknowledgement inhibits motion?
119. What proves that the system cannot execute motion until all required systems are healthy?
120. What proves that motion stops within the required fault-response time?
121. What tests validate the differential end-effector mapping?
122. What tests validate joint limits and trajectory limits?
123. What tests validate MoveIt 2 planning and collision avoidance?
124. What tests validate EKF performance, if the EKF is enabled?
125. What are the acceptance criteria for the first physical motion test?
126. What are the acceptance criteria for the first complete end-to-end pose command?

## 12. Requirements and Documentation

127. Which document is authoritative for system requirements?
128. Which document is authoritative for system-level decisions?
129. Which documents are contractual interfaces versus implementation notes?
130. How are unresolved questions tracked through to decisions?
131. How are requirements traced to implementation and verification evidence?
132. What information currently marked as unspecified must be defined in the next revision?
133. What is the process for approving changes to frozen contracts?
134. How are obsolete documents identified and archived?
135. How is the project documentation kept synchronized across Karetao sub-repositories?

## 13. Project Planning and Release

136. What is the exact scope of the first release?
137. What functionality is explicitly deferred?
138. What dependencies must be completed before ROS 2 development begins?
139. What is the exit criterion for STM32 ↔ Raspberry Pi hardware integration?
140. What is the exit criterion for beginning MoveIt 2 and ros2_control integration?
141. What is the exit criterion for enabling physical motion?
142. Which requirements are hard constraints versus engineering targets?
143. Which remaining values and parameters must be specified in the next project revision?
144. Who is responsible for answering and approving each unresolved question?
145. What evidence is required before each answer is considered closed?

---

# Source 6: final list/SYSTEM_DECISIONS.md

# Karetao System Decisions Register

This file lists the current SD-01 through SD-26 system decisions and the unresolved system-level issues that remain attached to them.

**Source for SD-01 through SD-25:** [CTO Final Decisions](archive/Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_FINAL.md), dated 2026-09-07.

> The source document approves the v1.0 firmware contract baseline for implementation. It does **not** certify the assembled robot as safe or authorize energized motion; release remains conditional on the listed safety, validation, and acceptance conditions.

> **Note on the "Possible solutions to investigate" column:** these are candidate directions for closing each open issue, offered for engineering evaluation — not decisions, and not a substitute for the machine risk assessment or safety-rated analysis required before energized-motion release.

## Decision table

| ID | Decision area | Status | Summary | Open issue / comment | Detailed explanation | Possible solutions to investigate |
|---|---|---|---|---|---|---|
| SD-01 | System timing | MODIFIED | 100 Hz remains the baseline for sensor/state publication and the initial control loop. **The EKF update rate is currently set to 500 Hz** and will be adjusted if required by downstream system constraints. SPI remains at a 5 MHz initial maximum, subject to validation. | The current six-axis physical sweep is approximately 46 ms. The 500 Hz EKF rate therefore requires the estimator to operate from timestamped/latest-value data rather than implying a 500 Hz complete six-axis sweep. End-to-end EKF data availability and latency remain integration items. | A full six-axis sweep at ~46 ms corresponds to a complete-cycle rate of roughly 22 Hz, more than an order of magnitude below the 500 Hz EKF rate. This is only workable if the EKF is designed as an asynchronous filter that predicts forward using its motion model between sensor updates and corrects opportunistically as individual, timestamped axis readings arrive — not as a filter expecting a fresh full-state vector every 2 ms. This decision does not yet specify the prediction/correction scheduling, how per-axis update staleness is bounded, or how SPI/CAN latency adds to the effective age of each measurement by the time it reaches the filter. | Implement the EKF as an asynchronous/multi-rate filter (predict-at-500-Hz, correct-per-axis-as-available) rather than a synchronous full-vector filter; instrument and log actual per-axis update latency on target hardware to replace the 46 ms estimate with measured data; run a covariance/sensitivity analysis to find the EKF rate where added computation stops improving estimate quality, and consider whether a lower, still-useful rate (e.g. 100–250 Hz) removes the mismatch entirely; prototype an out-of-sequence-measurement (OOSM) handling scheme if late-arriving axis data is common. |
| SD-02 | System-wide failure classification | MODIFIED | Four response levels: INFORMATIONAL, DEGRADED, FAULT, SAFETY_CRITICAL; PL/SIL determined by machine risk assessment. | The classification must be mapped to explicit motion-inhibit behaviour and ownership. A fault classification alone does not define who has final authority to prevent motion. | Naming four severity tiers answers "how bad is this fault," not "what happens to motion because of it." Each level needs a defined, deterministic action (allow motion, degrade capability, inhibit new commands, force stop) and an owner component responsible for enforcing that action even if other software layers disagree or lag. Without this mapping, two subsystems could reach different conclusions about whether motion is currently permitted. This ties directly to the open "motion-permission authority" question (system issue #5) and to the safety-boundary question in SD-25. | Build an explicit state/action matrix (severity level × required motion behaviour × owning component) as a standalone design artifact reviewed alongside the machine risk assessment; designate a single motion-permission authority (see SD-25) that all other components must query or defer to, rather than allowing distributed veto logic; model the classification-to-action mapping as a formal state machine and verify it has no reachable state where two components disagree on permission. |
| SD-03 | Raspberry Pi communication loss | APPROVED | 500 ms heartbeat timeout; reject motion, controlled stop if possible, then motor disable; never hold the last motion command. | "Controlled stop" and "motor disable" require measurable fault-to-safe-state timing. The exact stop-time requirement remains a system/safety validation item. | The decision fixes *when* loss is detected (500 ms) and *what* sequence follows (reject → controlled stop → disable), but not *how long* the physical arm is allowed to keep moving after detection before it must be at a safe state. That number depends on joint dynamics, payload, and the hazard zone defined by the machine risk assessment, and it is what turns "stop safely" into a testable requirement (see release condition #2). | Derive a maximum stop-time budget from the machine risk assessment's hazard/reach-zone analysis, then work backward to a required deceleration profile per joint; measure actual worst-case stop time on the assembled arm at maximum commissioned speed/payload and compare against the budget; consider whether 500 ms is still appropriate once stop-time is known, or whether detection time needs to shrink to leave enough margin for the mechanical stop. |
| SD-04 | Motor feedback/command timeout | APPROVED | Five times the commissioned feedback period; one miss degraded; three consecutive misses inhibit the motor and escalate to FAULT. | This primarily addresses feedback/timeout behaviour. **Command acknowledgement must be distinguished from feedback freshness.** A command that is transmitted but not acknowledged requires an explicit failure rule before motion is considered safe. | This rule protects against a motor going quiet (no feedback), but a motor can also silently fail to *receive or accept* a new command — feedback can keep flowing (stale, from the last accepted state) while the controller never executed the latest instruction. Feedback freshness alone cannot detect that case. A separate acknowledgement contract (does the controller confirm receipt/acceptance of each command, within what window, and what happens on a missed ack) is needed and feeds directly into SD-13 (state fields) and SD-14 (command interface). | Confirm whether the target MKS controller firmware supports an explicit command-accepted response (per SD-05); if it does, define an ack-timeout mirroring the feedback-timeout pattern (N missed acks → degraded → inhibit); if it does not natively ack, investigate an indirect check — comparing commanded setpoint against the next feedback sample to infer acceptance — as a fallback, and flag the added latency/ambiguity this introduces. |
| SD-05 | CAN network requirements | MODIFIED | 1 Mbps nominal v1 target, standard 11-bit IDs, <50–60% measured average load target; exact hardware and timing require validation. | Exact MKS controller model, firmware, command semantics, feedback semantics, acknowledgement behaviour, brake behaviour, and CAN physical configuration remain open until target-hardware evidence is recorded. | The bus-level parameters (bitrate, ID width, load ceiling) are fixed as targets, but nearly everything above the bus layer — what a specific MKS controller model actually accepts as commands, how it reports feedback, whether it acknowledges commands distinctly from reporting state, and how it engages/releases any holding brake — is vendor- and firmware-specific and has not yet been confirmed against real hardware. This is a direct prerequisite for closing SD-04 (acknowledgement), SD-06 (bus failure scope), and release condition #3. | Obtain and review the exact MKS controller datasheet/CAN protocol manual for the specific model and firmware revision in use; run a hardware bring-up/bench test logging real CAN traffic under representative motion to capture actual message IDs, payload semantics, and timing; test brake engage/release behaviour in isolation before integrating; measure actual bus load under worst-case simultaneous multi-joint motion against the 50–60% target. |
| SD-06 | CAN bus failure | APPROVED | Detect bus-off, inhibit commands, perform bounded recovery, escalate after repeated failure, and require explicit reactivation. | Confirm whether a CAN failure affecting one motor requires a joint-level stop or whole-system stop. Final scope follows the machine risk assessment. | The recovery *procedure* is defined, but its *blast radius* is not: if one motor drops off the bus, is it safe to keep other joints moving, or does the kinematic coupling (including the differential end effector in SD-26) mean any single-joint fault must halt the whole arm? This is a risk-assessment question, not a protocol question, because the answer depends on what hazardous motion or configuration becomes possible if only some joints stop. | Build a coupling/hazard matrix showing, for each joint (including the SD-26 differential pair), what motion becomes possible or unsafe if that joint alone stops while others continue; feed this matrix into the machine risk assessment to decide per-joint vs whole-system stop scope; consider a tiered response (isolated joint stop only when the risk assessment shows the remaining joints cannot create a hazard, whole-system stop otherwise) rather than a single fixed rule. |
| SD-07 | Joint/motor mapping | APPROVED | Versioned deterministic logical-joint, sensor-ID, motor/CAN-ID mapping including direction, zero offset, and transmission ratio. | The ordinary one-to-one mapping is insufficient for the differential end effector. SD-26 defines the separate motor-to-end-effector-DOF mapping decision. | This decision establishes the pattern for simple joints (one motor, one sensor, one logical joint) but explicitly does not attempt to cover the end effector, where two motors jointly produce two rotational degrees of freedom through a differential mechanism. That case needs its own transformation, which is why it is carved out into SD-26 rather than forced into this table's schema. | No independent action needed on this decision itself; track as complete pending SD-26 closure. When SD-26 is finalized, review whether the mapping schema (SD-07) needs a generalized "coupled joint group" extension so future multi-motor mechanisms don't each require a bespoke carve-out decision. |
| SD-08 | Motor/joint temporal alignment | APPROVED | Observation skew below 5 ms normally, target below 1 ms for dynamic joints; retain acquisition timestamps. | The approximately 46 ms six-axis sweep must be reconciled with estimator/control requirements. Timestamp compensation does not by itself establish that the resulting state update rate is acceptable. | Skew (how far apart in time two joints' readings were taken) and update *rate* (how often a fresh reading arrives at all) are different problems. Tagging every reading with an accurate timestamp lets the EKF correct for skew mathematically, but it cannot manufacture data that hasn't arrived yet — if the full sweep takes 46 ms, some joints' state is necessarily up to 46 ms old regardless of how well-timestamped it is. Whether that staleness, even when compensated, is acceptable for control at the target dynamics is still unresolved. | Investigate parallelizing or reordering the six-axis sweep (e.g. simultaneous multi-sensor sampling instead of sequential) to reduce the 46 ms figure directly; separately, run a control-loop sensitivity study to determine the maximum tolerable staleness per joint at target speeds, so "acceptable" becomes a number rather than a judgment call; evaluate whether faster-changing joints could be sampled preferentially/more often than slower ones within the sweep budget. |
| SD-09 | Measurement history ownership | APPROVED | Raspberry Pi/EKF owns measurement queues and estimator history; STM32 provides bounded latest-value caches and coherent records. | The 500 Hz EKF setting requires explicit definition of how latest-value records, asynchronous sensor updates, timestamp age, and interpolation/hold behaviour are handled. | Deciding *who* owns history (Pi/EKF) answers the architecture question but not the algorithm question: when the EKF ticks at 500 Hz and a given joint's cached value is, say, 30 ms old, does the filter hold that value, extrapolate it forward using the motion model, discard it as too stale, or flag it as degraded? That policy needs to be specified per-signal and validated, since it directly determines estimator accuracy. | Define and document an explicit per-signal staleness policy (hold / model-based extrapolate / reject-as-invalid) with a maximum-age threshold for each; prototype both a simple hold-last-value approach and a motion-model extrapolation approach in simulation, and compare estimate error against ground truth to choose between them; expose the chosen policy's threshold as a tunable configuration so it can be adjusted once real sweep-timing data is available. |
| SD-10 | Calibration ownership | APPROVED | Calibration computed on Pi/workstation; STM32 receives validated parameters through a controlled configuration path. | Calibration must cover the differential mechanism as well as individual motor/sensor offsets and ratios. | The current scope covers per-axis calibration (zero offsets, direction, ratio for simple joints). The differential end effector needs calibration of the *coupling* itself — e.g. how the two motor positions jointly map to the two DOF zero points — which is a different, coupled calibration problem that must be defined once SD-26's transformation is finalized. | Once SD-26's forward/inverse transformation is defined, design a coupled calibration procedure (e.g. jointly zeroing both end-effector motors against known DOF reference positions rather than calibrating each motor independently); extend the calibration parameter set and validated-configuration path (SD-10/SD-11) to include the differential mechanism's specific parameters (coupling ratios, joint zero references). |
| SD-11 | Calibration storage | APPROVED | Versioned, CRC-protected redundant STM32 flash records with power-loss protection and host-side source copy. | Calibration flash schema, endurance, power-loss behaviour, and parameter integrity remain release conditions. | The storage *architecture* (versioned, CRC-checked, redundant, mirrored to host) is decided, but the concrete schema layout, flash wear/endurance under expected write frequency, and behaviour under a power loss mid-write have not yet been tested on hardware. This is explicitly listed as release condition #6 and must pass before energized-motion release. | Define the concrete flash schema (field layout, version header, CRC placement) and review it against the target MCU's flash datasheet for write-cycle endurance at expected calibration-update frequency; run repeated power-loss-during-write tests on the actual STM32 target to confirm redundant records recover correctly; add a boot-time integrity check that falls back to the host-side source copy if both on-device records fail validation. |
| SD-12 | Authoritative angle representation | MODIFIED | Calibrated radians are authoritative at host/API; wire-schema change must be explicitly versioned rather than silently replacing millidegrees. | Migration requires a defined schema version, conversion rules, Pi decoder update, and verification evidence before the existing wire field changes meaning. | Changing what a wire field *means* (millidegrees → radians) without a version bump would silently break any consumer still assuming the old units — a subtle and dangerous failure mode for a motion system. This decision requires a concrete migration package (new schema version number, explicit conversion formula, updated Pi-side decoding, and test evidence that old and new consumers cannot misinterpret each other) before the field is actually changed. It is release condition #5. | Assign a concrete new schema/protocol version number now, even before the switch date, so it can be referenced by implementation work; write the conversion function and unit-test it against known reference angles; add a runtime schema-version check on the Pi decoder that refuses to interpret a frame as radians unless the version field confirms it, preventing silent misinterpretation; stage the rollout so STM32 and Pi are updated together rather than allowing a mismatched pair to run. |
| SD-13 | Required joint state | APPROVED | Stable joint identity, position, velocity where available, validity/status, acquisition timestamp, sync quality, and calibration version. | Add explicit commanded-vs-actual state validity and command acknowledgement status where required by the final motor interface. | The current state message tells a consumer what the joint's *measured* condition is, but not whether the *last commanded* value was actually accepted and achieved. Adding commanded-vs-actual fields and an acknowledgement-status flag closes the gap identified in SD-04 and gives downstream control/safety logic a way to detect "command sent but not honoured" without inferring it indirectly from feedback timing. | Extend the joint-state message schema with a commanded-setpoint field, an actual-vs-commanded delta or validity flag, and an acknowledgement-status enum, once SD-04/SD-05 settle what acknowledgement data is actually available from the controller; version this schema change the same way SD-12 handles the angle-representation change, so it doesn't silently redefine existing consumers' expectations. |
| SD-14 | Required command interface | MODIFIED | Commissioned position/velocity plus enable, disable, and controlled-stop operations; heartbeat, lifecycle, calibration, and safety gating required. | Define command acknowledgement, freshness, timeout, cancellation, and the distinction between application controlled-stop and independent emergency stop. | Several distinct behaviours are still bundled informally under "stop": an application-level controlled stop (software-initiated, can be smooth/coordinated) is not the same mechanism as the independent emergency stop required by SD-25 (hardware-level, safety-rated, must work even if the application software has failed). The command interface needs each of these — ack, freshness/timeout, cancellation, and the two stop types — defined as separate, unambiguous operations so that safety logic never has to guess which "stop" a given signal represents. | Define "controlled stop" and "emergency stop" as two distinct, separately-named operations in the command interface spec, each with its own trigger path, and document explicitly that emergency stop must remain reachable through the independent safety path (SD-25) even if the application-level command interface is unresponsive; add explicit ack/freshness/timeout/cancel semantics to each commissioned command type, reusing the acknowledgement contract developed for SD-04; validate with a fault-injection test that emergency stop still functions when the normal command channel is deliberately blocked. |
| SD-15 | Fixed SPI transaction | APPROVED | 512-byte frame, 490-byte maximum payload, SPI Mode 0, little-endian fields, CRC-32/ISO-HDLC, deterministic request/response ownership. | Protocol sizing is defined, but the 5 MHz operating point remains an empirical integration limit until live Pi/STM32 and physical-layer evidence is accepted. | The frame format, size limits, and integrity check are all fixed and implementable now, but the 5 MHz clock is a *target*, not a proven operating point — it depends on real cabling, connector quality, and electrical noise on the assembled hardware. It must be validated (signal integrity, error rate, timing margin) on the actual Pi/STM32 link before being frozen, per release condition #4. | Run signal-integrity testing (oscilloscope eye-diagram / rise-time checks on the physical SPI lines) at 5 MHz on the actual wiring harness and connectors used in the assembled robot; measure CRC failure rate over an extended soak test at 5 MHz vs at a reduced clock (e.g. 1–2 MHz) to establish margin; if 5 MHz proves marginal, evaluate shielded/twisted-pair wiring, shorter runs, or a lower validated clock as fallbacks. |
| SD-16 | GET_SNAPSHOT priority | APPROVED | Correlated GET_SNAPSHOT response takes priority; active DMA buffers remain immutable; replacement frames use replace-if-new policy. | Confirm replacement/drop semantics preserve the freshest state required by the 500 Hz EKF and do not create unacceptable state age. | "Replace-if-new" avoids stale data overwriting fresh data, but at 500 Hz the margin for error is small: if snapshot requests are frequent or DMA buffer immutability causes brief stalls, some replacement frames could be dropped rather than merely delayed, silently increasing the effective age of what the EKF consumes. This needs to be checked under realistic request/traffic patterns, not just verified as logically correct. | Instrument the actual replace/drop path to log every dropped or delayed replacement frame during integration testing, then compute resulting worst-case data age per joint under realistic (not just nominal) GET_SNAPSHOT request rates; if dropped-frame age exceeds the staleness threshold from SD-09, consider prioritizing replacement over snapshot correlation in specific cases, or increasing buffer depth so a snapshot request doesn't force a drop. |
| SD-17 | SPI host transaction strategy | APPROVED | DATA_READY interrupt for latency plus configurable polling, initially 1 ms, for recovery; Pi remains SPI clock master. | Current Pi baseline does not have a physical DATA_READY GPIO assigned. Until one is assigned and tested, the 1 ms polling path is the available host notification mechanism. | The design assumes a low-latency interrupt line (DATA_READY) as the primary notification path, with 1 ms polling only as a fallback for recovery scenarios. Because no GPIO pin has actually been assigned for this signal yet, the system is currently running on the fallback path as its *only* path — meaning real transaction latency today is bounded by the 1 ms poll interval rather than interrupt-driven response, which is a meaningfully different (slower, jitterier) timing profile than the design intends and is relevant to the SD-01/SD-08 timing questions. | Assign an available Pi GPIO pin to DATA_READY as a concrete near-term task, then wire and test interrupt-driven notification on the bench; until that's done, measure actual achieved latency/jitter under the 1 ms polling-only path so its real impact on SD-01's timing budget is known rather than assumed; once the interrupt path exists, A/B test interrupt-driven vs polling-only timing to confirm the expected latency improvement. |
| SD-18 | Timestamp accuracy | APPROVED | Target timestamp error ≤ ±1 ms relative to shared STM32/Pi time model; expose sync validity and age. | Validate whether ±1 ms is sufficient for the 500 Hz EKF and downstream control requirements. | A 500 Hz EKF has a ~2 ms nominal update period, so a ±1 ms timestamp error is a large fraction of that period — potentially half a cycle of uncertainty on when a measurement was actually taken. Whether this is tolerable depends on how sensitive the estimator and controller are to timing error at the target dynamics; it has not yet been validated against the actual 500 Hz operating condition, only specified as a target. | Run a simulation or bench test injecting known timestamp errors up to ±1 ms into the EKF and measure resulting state-estimate error at the target 500 Hz rate and expected joint speeds; if error is unacceptable, investigate tightening the time-sync mechanism (see SD-19) or hardware timestamping closer to the sensor to reduce jitter, rather than relaxing the EKF rate. |
| SD-19 | TIME_SYNC frequency | APPROVED | 1 Hz nominal, configurable to 10 Hz; synchronization invalid after five seconds without an accepted update. | Validate synchronization stability and timestamp error under the 500 Hz estimator operating condition. | Sync frequency and the 5-second invalidation window were set independently of the 500 Hz EKF decision. It remains to be confirmed that clock drift between syncs stays within the ±1 ms budget (SD-18) for the full duration between updates, especially at the faster estimator rate where accumulated drift has more opportunities to matter before the next correction. | Measure the actual free-running clock drift rate of the STM32 oscillator between syncs on real hardware, and calculate whether drift stays under ±1 ms across a full 1 Hz sync interval (and worst-case up to the 5-second invalidation window); if drift exceeds budget, evaluate raising TIME_SYNC frequency to the already-supported 10 Hz configuration rather than changing the protocol. |
| SD-20 | Loss of time synchronization | MODIFIED | Continue acquisition/diagnostics but inhibit time-dependent motion until synchronization returns. | Define precisely which downstream operations are "time-dependent motion" and ensure the motion-permission layer enforces this consistently. | The rule correctly separates "keep gathering data" from "don't move," but "time-dependent motion" is not yet an enumerated, unambiguous category. Does it mean all motion (since the EKF that informs control is itself time-dependent), or only specific trajectory-timing-sensitive operations? Without a precise definition, different components could apply the rule inconsistently, undermining the intended safety effect. | Produce an explicit enumerated list of which operations count as "time-dependent motion" (likely: all closed-loop motion, since the EKF feeding the controller is itself time-dependent) and document it alongside SD-02's classification matrix; implement the check as a single shared gate in the motion-permission authority (see SD-02/SD-25) rather than letting each component independently interpret "time-dependent," and add an integration test that forces a sync loss and confirms motion is actually inhibited end-to-end. |
| SD-21 | Time offset validation | APPROVED | Wide initial offset range, then narrower runtime validation initially ±1 s; reject implausible updates without silent slew. | Verify that the initial and runtime bounds are appropriate for commissioning and reset behaviour. | The two-tier bound (loose at startup, tight at runtime) and the "reject rather than silently slew" rule are sound in principle, but the actual numeric bounds are provisional. They need to be checked against real commissioning scenarios (e.g. how far off can the clock plausibly be at first boot) and reset scenarios, to confirm they neither reject legitimate corrections nor accept implausible ones. | Survey realistic worst-case initial clock offset at cold boot (e.g. STM32 with no RTC vs one with battery-backed RTC) to confirm the wide initial range actually covers it; during commissioning and reset testing, log any legitimate TIME_SYNC updates that get rejected by the ±1 s runtime bound to check for false rejections; tune the bounds based on this evidence rather than leaving them at their initial provisional values. |
| SD-22 | Time behaviour after reset | APPROVED | Clear sync validity and volatile offset; timestamps remain unsynchronized until a new accepted TIME_SYNC. | Confirm that all consumers, especially the 500 Hz EKF, reject or correctly classify unsynchronized data after reset. | Clearing sync state on reset is only effective if every downstream consumer actually checks and respects the sync-validity flag before trusting a timestamp. The EKF is the most exposed consumer, given how timing-sensitive it is at 500 Hz — if it were to consume unsynchronized, arbitrarily-offset timestamps as if they were valid, it could produce a badly wrong state estimate immediately after a reset. This needs to be verified in the actual estimator implementation, not just assumed from the protocol design. | Add an explicit unit/integration test that forces a reset, then confirms the EKF (and every other timestamp consumer) either ignores incoming data or flags it degraded until a fresh TIME_SYNC is accepted; audit the EKF implementation specifically for any code path that could use a timestamp without first checking its validity flag; consider having the STM32 refuse to publish state data at all (rather than publishing with a validity flag) during the unsynchronized window, removing reliance on every consumer checking correctly. |
| SD-23 | Transient vs persistent fault recovery | APPROVED | Bounded service-specific retries; persistent/repeated/freshness failures enter ERROR and recover to INACTIVE. | Define system-level escalation when a subsystem is recovering but motion cannot be considered safe. Recovery must not race with motion permission. | Each service's retry/recovery logic is defined locally, but there is no stated rule for the *system-level* moment in between — while a subsystem is mid-recovery, is motion automatically inhibited, or could a different subsystem (unaware of the in-progress recovery) grant motion permission based on stale or partial information? This is a race-condition risk between per-service recovery state machines and the motion-permission logic referenced in SD-02. | Model recovery-in-progress as an explicit state visible to the motion-permission authority (SD-02), so permission logic can query "is anything currently recovering" rather than relying on each service to separately signal readiness; design and run a race-condition test that deliberately triggers a recovery and a motion request at the same time to confirm permission is correctly withheld until recovery fully completes; consider a system-wide "not ready" latch that only clears once all recovering services report healthy. |
| SD-24 | System restart and recovery | APPROVED | Return to INACTIVE; explicit dependency-ordered reactivation required; never automatically resume motor motion after recovery. | Establish the complete dependency order across STM32, Pi, ROS 2, EKF, ros2_control, MoveIt 2, and safety gating before physical motion release. | "Dependency-ordered reactivation" is the principle, but the actual ordered sequence — which subsystem must be confirmed healthy before the next is allowed to activate, across firmware, middleware, estimator, control, planning, and safety layers — has not yet been written down as a concrete startup/recovery sequence. This is needed before any physical motion release, since an incorrectly-ordered restart could bring motion capability online before, e.g., the safety system or EKF are actually ready. | Draft an explicit startup/recovery dependency graph naming each subsystem (STM32 firmware, Pi/ROS 2 bring-up, EKF initialization and sync acquisition, ros2_control, MoveIt 2, independent safety system) and the specific readiness condition each must satisfy before the next may proceed; implement this as a supervised, checked sequence (not just documentation) so activation cannot skip ahead if a dependency check fails; test the sequence under partial-failure scenarios (e.g. EKF slow to sync) to confirm it holds rather than proceeding anyway. |
| SD-25 | Independent safety mechanisms | MODIFIED | Independent E-stop, motor-disable/power-removal path, watchdog, stop/brake behaviour, fault indication, reset behaviour, and applicable safety-rated architecture are release gates. | The boundary and interface between Karetao application controls and the independent safety system must be explicitly defined by the machine risk assessment and safety architecture. | This decision commits to having an independent (i.e. not solely software-dependent) safety layer, but does not yet define exactly where the line sits between "the application software's controlled stop" and "the independent safety system's emergency stop" — what triggers each, whether they can interact, and what happens if the application layer disagrees with the safety layer. That boundary is properly a machine-risk-assessment and safety-architecture output, referenced as the unresolved dependency here and in SD-14. | Commission or complete the machine risk assessment as the primary input for this boundary, since it determines the required PL/SIL and therefore what must be independent of the application software; draft a safety architecture diagram explicitly showing which functions live in the independent safety path vs the application path, and where they physically/electrically interface (e.g. does the safety system have authority to cut power regardless of application state); validate with a fault-injection test that the independent path still functions with the application software deliberately disabled or hung. |
| SD-26 | Differential end-effector motor/DOF mapping | PROPOSED | The two end-effector motors drive two end-effector rotational DOFs through a differential mechanism. The mapping must be represented explicitly rather than as two independent one-to-one joints. | Define the forward/inverse transformation, motor signs, gear ratios, zero offsets, joint limits, singular/invalid configurations, and representation in ros2_control and MoveIt 2. This remains open until the mechanical model and mapping are verified. | Unlike the simple joints covered by SD-07, the two end-effector motors do not each correspond one-to-one with a single DOF; their combined positions determine both output DOFs through the differential mechanism. Closing this decision requires: the math (forward and inverse kinematics of the coupling), the physical parameters (motor sign conventions, gear ratios, zero references), the safety-relevant edges (joint limits and any singular or invalid motor-position combinations that would produce an undefined or unsafe output), and how all of that is represented as a proper model inside ros2_control and MoveIt 2 rather than being approximated as two independent joints. This is a prerequisite for SD-07's joint model being considered complete and is still PROPOSED, not approved. | Derive the differential mechanism's forward/inverse kinematic equations from its physical/CAD design and verify them against direct measurement on the assembled end effector; identify and document any singular or invalid motor-position combinations analytically, then add software-level limit checks that reject commands leading into them; implement the mapping as a custom ros2_control transmission (or MoveIt 2 joint group with a mimic/coupling constraint) rather than exposing the two motors as independent joints, and validate with hardware-in-the-loop testing across the full range of motion including near-limit and near-singular configurations. |

## Decision status

- **APPROVED:** 18
- **MODIFIED:** 7
- **PROPOSED:** 1
- **Total:** 26

## System-level issues still requiring closure

1. **EKF timing:** EKF is currently set to **500 Hz**; downstream constraints may require adjustment. This does not mean the complete six-axis sensor scan currently operates at 500 Hz.
2. **Sensor failure response:** The requirement that sensor-data failure stops motion needs an explicit rule covering invalid, missing, stale, and failed sensors.
3. **Motor command acknowledgement:** Command acknowledgement must be separately defined from motor feedback and communication heartbeat.
4. **Fault-to-safe-state timing:** "Stop immediately" must become a measurable timing requirement.
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

---

# Source 7: final list/TODO_List.md

# TODO List (Consolidated from existing repository documentation)

## docs/architecture.md
- Less mature or still being integrated: live Raspberry Pi <-> STM32 SPI transaction acceptance.
- Less mature or still being integrated: 5 MHz physical SPI acceptance, including DMA timing, NSS, DATA_READY/GPIO timing, and signal integrity.
- Less mature or still being integrated: sustained/repeated SPI transaction validation.
- Less mature or still being integrated: scan timing and other six-channel sensor parameters that remain unfrozen.
- Less mature or still being integrated: complete TIME_SYNC target validation.
- Less mature or still being integrated: expanded health aggregation.
- Less mature or still being integrated: CAN physical validation.
- Less mature or still being integrated: calibration persistence.
- Less mature or still being integrated: exact motor-controller semantics.
- Less mature or still being integrated: independent safety validation.

## docs/hardware/arm-sensor-hub-baseline.md
- Add CAN TX queueing policy, retry/timeout strategy, and bus-off recovery policy.
- Add integration tests for end-to-end sensor-to-host data path.
- Retain live SPI host validation, 5 MHz physical acceptance, and DATA_READY/NSS electrical validation as integration gates.

## docs/interfaces/spi-service-contract.md
- Validate the implemented DMA/NSS path with a live Raspberry Pi host.
- Validate the 5 MHz initial maximum with Pi, DMA, GPIO, NSS, and signal-integrity tests.

## docs/protocols/spi-contract.md
- Validate the implemented SPI3 DMA path with a live Raspberry Pi host.
- Accept the 5 MHz maximum only after DMA timing, NSS behavior, DATA_READY/GPIO timing, signal integrity, sustained transactions, and real request/response evidence are recorded.
- Retain the existing protocol/schema freeze decisions; do not turn implementation details into new requirements.
- Lifecycle states permitted for each message type.

## docs/protocols/spi-payload-schema.md
- Event types and severity values remain reserved for the error-handling contract; values must be assigned before implementation.
- `SET_MOTOR_COMMAND` is not frozen until the Motor Service contract exists; it must not be implemented from this draft alone.
- Remaining schema decisions: exact event type and severity enumerations.
- Remaining schema decisions: whether diagnostic counters are 32-bit or 64-bit on the wire.
- Remaining schema decisions: snapshot dropped-count width and reset behavior.
- Remaining schema decisions: whether future records use a tagged extension mechanism.

## docs/interfaces/raspberry-pi-spi.md
- Confirm `DATA_READY` GPIO polarity, debounce expectations, and user-space access strategy against target hardware; the Raspberry Pi GPIO remains intentionally unassigned in the current baseline.
- Confirm the maximum accepted SPI clock after the ARM-side 5 MHz integration gate is closed.
- Confirm final request/response retry policy for stalled or partial transactions.
- Retain fixed 512-byte transfers as the current transport implementation; revisit only through a versioned contract change.

## RaspberryPi_Sensor_Hub/README.md
- Validate the implemented Linux `spidev` backend on the target Raspberry Pi.
- Close the DATA_READY GPIO integration decision only when a Raspberry Pi GPIO is actually assigned and validated.

## Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md (Next action column)
- Complete named CAN, SPI, motor, and safety gates.
- Implement prerequisite validation and explicit post-recovery activation request.
- Validate the 5 MHz initial SPI maximum with Pi, DMA, GPIO, NSS, and signal-integrity tests.
- Validate exact controller, transceiver/topology/termination, candidate timing, measured load, retry timing, and recovery behavior.
- Extend coverage as more motor/sensor fields become live and retain target validation evidence.
- Expand producer coverage beyond the current commissioned sensor/motor set.
- Complete documented Pi/DMA/GPIO clock acceptance testing with a live host.
- Expand composite-access coverage and define broader arbitration/recovery behavior.
- Freeze scan period, per-channel timeout, settle time, and healthy-channel threshold against the measured ~46 ms full-six-axis sweep.
- Validate end-to-end Pi-driven TIME_SYNC behavior on target hardware and retain build evidence.
- Define canonical CRC serialization and flash persistence/power-loss handling.
- Commission complete physical mapping and bind it to persisted configuration.
- Implement response-level events and bounded recovery escalation.
- Expand snapshot thresholds, host reporting cadence, and fault acknowledgement behavior.
- Preserve the successful CI firmware-build evidence, size/checksum output, and uploaded artifacts.
- Verify exact controller behavior before freezing command semantics.

## Arm_Sensor_Hub/Documentation/Module_TODOs/CAN_Module_TODO.md
- Confirm transceiver wiring: CAN1_TX -> TJA1050 TXD, CAN1_RX -> TJA1050 RXD, shared GND, and stable 5V/3.3V domain compatibility.
- Add/verify proper 120-ohm termination at both physical bus ends.
- Validate CANH/CANL idle and dominant levels with scope or analyzer before motion commands.
- Document the exact bench topology (cable length, stubs, node count, termination locations).
- Decide initial real-test bitrate (e.g., 500 kbps or 1 Mbps) and update CubeMX/HAL CAN timing settings to match measured behavior.
- Verify CANable V2 bitrate matches STM32 bitrate exactly.
- Re-check sample point/SJW margin against oscillator tolerance for STM32 + bus layout.
- Record finalized timing values and rationale in `Documentation/CAN_BIT_TIMING_EVIDENCE.md`.
- Add duplicate CAN ID rejection in `CanService_RegisterMotor()` to prevent ambiguous RX frame ownership.
- Add explicit HAL error diagnostics mapping (TX/RX/error counters by error class).
- Add RX FIFO overflow tracking/handling and expose it through CAN diagnostics.
- Define and implement response timeout expectations per poll/command path.
- Confirm emergency-stop behavior policy during lifecycle `ERROR` and enforce/document selected behavior.
- Expose runtime CAN diagnostics in a host-visible channel (SPI snapshot/log/telemetry): lifecycle state, bus-off count, queue drops, retry-exhausted count, RX ok/decode error counts.
- Add timestamped trace points for command TX, response RX, and bus-off recovery attempts.
- Add a simple bench-test checklist to log pass/fail for power-up, idle, command, and fault-recovery scenarios.
- Create a repeatable CANable capture script/procedure (startup capture, command-response capture, fault injection capture).
- Validate that expected MKS command IDs and response frames appear on the bus with correct DLC/payload.
- Verify poll traffic cadence at default 20 ms scheduler period and confirm no unintended bus flooding.
- Run long-duration soak capture to check for dropped frames, decode errors, or recurring bus-off.
- Test bus disconnection/reconnection and confirm bus-off detection, inhibition of normal commands, and recovery back to inactive state.
- Confirm `CanService_Activate()` is required and sufficient to re-enable normal commands after recovery.
- Test mailbox pressure/temporary TX failures and validate retry and drop diagnostics behavior.
- Verify behavior when receiving unknown CAN IDs and malformed DLC/payload frames.
- Add host-side tests for `can_service` logic that does not require real CAN hardware (registration constraints, scheduler behavior, queue/retry edge cases via mocks).
- Add hardware-in-the-loop test notes for STM32 + TJA1050 + CANable in Documentation with required tooling and expected outputs.
- Update contract status once integration gates are closed with measured evidence.
- Expand `s_mks_motors` and joint mapping only after each added motor passes single-node bench validation.
- Validate per-motor direction, ID, and mapping consistency before enabling multi-motor motion tests.
- Freeze a known-good CAN commissioning baseline (timing + topology + firmware revision + test evidence).

## Arm_Sensor_Hub/Documentation/SAFETY_RELEASE_CHECKLIST.md
- Machine risk assessment and required PL/SIL target — BLOCKED: no artifact recorded.
- Independent E-stop path — BLOCKED: no artifact recorded.
- Hardware motor-disable or power-removal path — BLOCKED: no artifact recorded.
- Watchdog behavior and fault recovery — BLOCKED: no artifact recorded.
- Actuator stop/brake/power behavior — BLOCKED: no artifact recorded.
- Fault indication and operator-visible reporting — BLOCKED: no artifact recorded.
- Reset behavior and explicit non-automatic reactivation — BLOCKED: no artifact recorded.
- Measured stopping time in hazardous operating conditions — BLOCKED: no artifact recorded.
- Exact MKS controller model, firmware, command, feedback, and brake behavior — BLOCKED: no artifact recorded.
- CAN physical layer, bitrate, load, termination, topology, and recovery — BLOCKED: no artifact recorded.
- SPI clock, Pi driver, DMA, GPIO, polling, host-stall, and signal-integrity acceptance — BLOCKED: no artifact recorded.
- Versioned payload schema and conversion evidence before replacing processed millidegrees with radians — BLOCKED: no artifact recorded.
- Calibration flash schema, CRC, power-loss, sector allocation, and endurance test evidence — BLOCKED: no artifact recorded.
- Applicable safety-rated relay/controller and safety architecture — BLOCKED: no artifact recorded.

## Arm_Sensor_Hub/Documentation/PHASE_1_FINAL_CLEARANCE_REPORT.md
- Historical report dated 2026-09-07 recorded missing ARM toolchain evidence at that review point. Do not treat that historical finding as the current repository build state; current CI evidence is tracked in `BUILD_CONTRACT.md` and `CONTRACT_STATUS.md`.
- Deepen negative-path coverage for hardware-facing service flows beyond smoke level (P2, Non-blocking follow-up).

## Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md
- Automated host tests were intentionally deferred from first implementation pass; required future cases remain listed.

## Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_BRIEF.md
- CTO safety approval checklist items SD-02, SD-03, SD-04, SD-06, SD-05, SD-14, SD-20, SD-23, SD-24, and SD-25 remain unchecked.
- Open assumptions and integration gates 1 through 8 remain listed as open.
- Approval record SD-01 to SD-25 is pending.

## Arm_Sensor_Hub/Documentation/Sprint_1_List.md
- Remaining work (Task 07): canonical serialized CRC coverage using shared CRC-32/ISO-HDLC helper; redundant flash-sector allocation; erase/write ordering; endurance budget; power-loss recovery validation; wiring validated calibration state into mapping and lifecycle prerequisites.
- Remaining work (Task 08): complete physical commissioning; persisted configuration binding; future mapping schema for coupled/differential joints.
- Remaining work (Task 09): freeze scan timing parameters against the commissioned SD2-SD7 mapping and measured ~46 ms full-axis sweep; calibration binding remains open.
- Task 18 output is not implemented and deferred to when Motor Service work begins (open Sprint 2+ item).
- Sprint 1 exit criteria checklist items remain unchecked.

## Code vs document consistency issues found in code review
- `spi_device.py` still provides stateless `transact/get_status` helpers; do not claim complete host-side outstanding-transaction state tracking merely because frame-level sequence/version validation exists.
- Live Pi/STM32 request/response, DATA_READY GPIO assignment, NSS behavior, 5 MHz acceptance, and signal integrity remain physical validation work rather than implementation TODOs.
