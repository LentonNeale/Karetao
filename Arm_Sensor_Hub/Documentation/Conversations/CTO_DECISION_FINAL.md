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
