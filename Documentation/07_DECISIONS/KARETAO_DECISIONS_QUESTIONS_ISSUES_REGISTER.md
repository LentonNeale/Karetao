# Karetao Project — Decisions, Questions & Open Issues Register

> **Live reconciliation register**
>
> This document is the current reconciliation index for Karetao decisions, questions, issues, verification work, and release gates. It is **not an authority source** and does not approve, modify, or supersede system requirements, interfaces, safety requirements, verification status, or approved decisions. Those authorities remain in the source documents identified below.
>
> The register intentionally preserves historical provenance, including inherited questions and TODOs, but **historical or superseded material must not be interpreted as current open work**. Current project work is identified in the live status sections below.
>
> **GitHub tracking:** [Issue #9 — Reconcile Decisions/Questions/Issues Register and create live GitHub issues](https://github.com/LentonNeale/Karetao/issues/9)
>
> **Reconciliation baseline:** current `main` repository state as reviewed for Issue #9. Do not hard-code a "current HEAD" hash in this file; the commit containing this document necessarily becomes the new HEAD.

**Live status vocabulary**
| Status | Meaning |
|---|---|
| **OPEN — DESIGN** | An unresolved system/design decision remains. |
| **OPEN — IMPLEMENTATION** | A documented implementation gap remains. |
| **OPEN — VERIFICATION** | The design/implementation exists but required evidence is not yet accepted. |
| **OPEN — RELEASE BLOCKER** | Failure to close the item blocks the applicable release gate. |
| **PROPOSED** | A proposed decision or requirement exists but is not approved. |
| **DEFERRED** | Explicitly postponed; not current release work unless reactivated. |
| **CLOSED / VERIFIED** | The cited work is complete at the stated scope; do not infer system-level verification unless the system verification authority says so. |
| **HISTORICAL** | Retained for provenance only; not current work. |
| **SUPERSEDED** | Replaced by a later applicable source. |

**Status rule:** A checkbox or "open" wording inherited from an older source does **not** by itself make an item live. Current status must be established from the applicable authoritative source or current evidence.

**Contents**
- Live Status Vocabulary (definitions used for Section 0)
1. System Decisions (SD-01 to SD-26)
2. Historical / Source-Collected Questions (145 entries)
3. Historical / Source-Collected Issues & TODOs (by subsystem/document)
4. Release Conditions / Safety Gates
5. Source-Collected System Issues — Reconciled Against Section 0
6. Source Document Status

---

## Source Status Vocabulary

The statuses in this section are **source-status terms preserved for provenance**. They are distinct from the normalized **live reconciliation status** used in Section 0. Source wording is retained rather than silently reclassified.

| Status | Meaning |
|---|---|
| APPROVED | Explicitly approved by the identified authority. |
| MODIFIED | The approved baseline has subsequently been qualified or changed; the supporting authority/evidence must remain traceable. |
| PROPOSED | Proposed but not approved. |
| OPEN | No authoritative resolution has been identified. |
| BLOCKED | The cited source records the item as blocked; current status has not necessarily been independently revalidated. |
| HISTORICAL | Retained as evidence of an earlier project state, not treated as current authority. |
| SUPERSEDED | Replaced by a later applicable source or decision. |
| UNVERIFIED | Defined or claimed in a source but lacking the required verification evidence. |

Where a source uses a status term slightly differently from the table above (for example, the safety checklist's own wording "BLOCKED: no artifact recorded" — see Section 3.4), this register preserves that source wording verbatim and adds a clarifying note, rather than silently reclassifying it into the vocabulary above.


## 1.2 Detailed decisions

#### SD-01 — System Timing Requirements
**Status:** MODIFIED · Approved 2026-09-07

- **Decision:** 100 Hz for sensor acquisition, STM32 snapshot publication, Pi consumption, EKF updates, and the initial control loop. Freshness budget < 1×10 ms cycle; target < 2 ms transport/assembly latency. SPI clock set to 5 MHz as an *initial maximum*, pending Pi driver / signal-integrity / DMA acceptance testing.
- **Reasoning:** 100 Hz is coherent with the estimator/control architecture and leaves scheduling margin; 5 MHz gives 819.2 µs wire time for a 512-byte frame but is a configuration limit, not a proven electrical limit.
- **Open issue:** The EKF has since been *configured to run at 500 Hz*, not 100 Hz — but the full six-axis sensor sweep takes ~46 ms (≈22 Hz complete-cycle rate), more than an order of magnitude below 500 Hz.
- **Why it matters:** 500 Hz only makes sense if the EKF is an asynchronous filter — predicting forward on its motion model between updates and correcting opportunistically per-axis as timestamped readings arrive — rather than a filter expecting a fresh full-state vector every 2 ms. The prediction/correction scheduling, per-axis staleness bounding, and how SPI/CAN latency adds to effective measurement age are all still undefined.
- **Investigate:** implement the EKF as asynchronous/multi-rate (predict-at-500 Hz, correct-per-axis); instrument real per-axis update latency on target hardware to replace the 46 ms estimate; run a covariance/sensitivity study to find the rate where more compute stops helping, and consider whether 100–250 Hz removes the mismatch; prototype out-of-sequence-measurement (OOSM) handling if late axis data is common.

> **Timing improvement note (added 2026-09-20, not resolved by this correction pass):** the ~46 ms measured full-sweep figure referenced above (2026-09-17 target-hardware run, `tools/check-sensors.sh`, archived `CONTRACT_STATUS.md`) remains the current measured evidence. A datasheet-derived I2C protocol-timing analysis (`Arm_Sensor_Hub/Documentation/I2C_SCAN_TIMING_ANALYSIS.md`) separately establishes a theoretical, zero-overhead protocol floor of ~690 µs for the six-sensor scan, indicating firmware/scheduling overhead — not I2C bus timing — accounts for most of the measured sweep time. This is recorded as an improvement target, not a disputed measurement. The "instrument real per-axis update latency on target hardware" investigation item above is the action that would identify and reduce that overhead.

#### SD-02 — System-Wide Failure Classification
**Status:** MODIFIED · Approved 2026-09-07

- **Decision:** Four firmware response levels — `INFORMATIONAL`, `DEGRADED`, `FAULT`, `SAFETY_CRITICAL`. Every event needs detection, response, recovery owner, and output-inhibit behaviour defined. No PL/SIL is claimed from this taxonomy — that comes from a machine risk assessment (ISO 13849-1:2023 / IEC 62061:2021).
- **Reasoning:** Gives firmware a deterministic, auditable vocabulary while preserving the CTO's ownership of the formal safety target.
- **Open issue:** The four levels aren't yet mapped to explicit motion-inhibit behaviour and an owning component. Naming severity doesn't answer *who* has final authority to stop motion.
- **Why it matters:** Without an explicit severity → action → owner mapping, two subsystems could independently reach different conclusions about whether motion is currently permitted. Directly tied to system issue #5 (motion-permission authority) and the SD-25 safety boundary.
- **Investigate:** build a state/action matrix (severity × required motion behaviour × owning component) as its own design artifact reviewed with the risk assessment; designate a single motion-permission authority that all components defer to; model the mapping as a formal state machine and verify no reachable state has two components disagreeing on permission.

#### SD-03 — Raspberry Pi Communication Loss
**Status:** APPROVED

- **Decision:** Monotonic heartbeat + command freshness check. After 500 ms without a valid heartbeat: reject new motion commands, issue a controlled stop if transport is usable, then assert motor disable. Never hold the last motion command.
- **Reasoning:** Bounds how long stale commands can affect the machine; holding the last command is not fail-safe.
- **Open issue:** "Controlled stop" and "motor disable" need measurable fault-to-safe-state timing — how long can the arm keep moving after detection before it must be safe?
- **Why it matters:** That number depends on joint dynamics, payload, and the hazard zone from the machine risk assessment — it's what turns "stop safely" into a testable requirement (release condition #2).
- **Investigate:** derive a max stop-time budget from the risk assessment's hazard/reach-zone analysis, then work backward to a per-joint deceleration profile; measure actual worst-case stop time at max commissioned speed/payload; re-check whether 500 ms detection still leaves enough margin once stop time is known.

#### SD-04 — Motor Feedback/Command Timeout
**Status:** APPROVED

- **Decision:** Response timeout = 5× the commissioned feedback period. One miss = degraded; three consecutive misses for a motor → inhibit that motor, escalate to `FAULT`. System-level stop required if the affected motor can create a hazardous state.
- **Reasoning:** Multiple-of-period timeout tolerates jitter while still catching a failed controller.
- **Open issue:** This covers feedback going stale, but **command acknowledgement is a separate, undefined problem** — a motor can silently fail to *accept* a new command while still reporting stale-but-flowing feedback from its last accepted state.
- **Why it matters:** Feedback freshness alone can't detect "command sent but not honoured." A separate acknowledgement contract is needed, feeding into SD-13 (state fields) and SD-14 (command interface).
- **Investigate:** confirm whether the target MKS controller firmware supports an explicit command-accepted response (depends on SD-05); if yes, define an ack-timeout mirroring the feedback pattern; if not, investigate inferring acceptance by comparing commanded setpoint to the next feedback sample, flagging the added latency/ambiguity.

#### SD-05 — CAN Network Requirements
**Status:** MODIFIED

- **Decision:** 1 Mbps nominal v1 target, standard 11-bit IDs, design target < 50–60% measured average bus load. Before production freeze: verify exact MKS controller/transceiver, termination, topology, cable length, APB1-derived bit timing, sample point, SJW, retransmission, and worst-case traffic.
- **Reasoning:** 1 Mbps is a reasonable initial target but can't be approved from a generic motor-product assumption alone.
- **Open issue:** Exact MKS controller model/firmware, command semantics, feedback semantics, acknowledgement behaviour, brake behaviour, and CAN physical configuration are all still open pending real hardware evidence.
- **Why it matters:** Nearly everything above the bus layer is vendor/firmware-specific and unconfirmed. This is a direct prerequisite for closing SD-04 (acknowledgement), SD-06 (bus-failure scope), and release condition #3.
- **Investigate:** obtain and review the exact MKS CAN protocol manual for the model/firmware in use; run a bench test logging real CAN traffic under representative motion; test brake engage/release in isolation; measure actual bus load under worst-case multi-joint motion against the 50–60% target.

#### SD-06 — CAN Bus Failure
**Status:** APPROVED

- **Decision:** Detect bus-off, inhibit normal motor commands, perform bounded controller-defined recovery from task context, log every attempt, use an escalating recovery delay. Escalate to `ERROR` after three bus-off events in a configurable rolling window (or recovery timeout); require explicit reactivation before motion resumes.
- **Reasoning:** Repeated bus instability must not repeatedly re-enable actuation.
- **Open issue:** Whether a CAN failure on one motor requires a joint-level stop or a whole-system stop is undecided.
- **Why it matters:** The recovery *procedure* is defined but its *blast radius* isn't — this depends on kinematic coupling (including the SD-26 differential end effector) and is a risk-assessment question, not a protocol one.
- **Investigate:** build a coupling/hazard matrix per joint (including the differential pair) showing what becomes unsafe if that joint alone stops; feed it into the risk assessment; consider a tiered response (isolated stop only where proven safe, whole-system stop otherwise).

> **Unresolved terminology note (not resolved by this correction pass):** SD-06 uses "`ERROR`", while SD-02 defines "`FAULT`" and "`SAFETY_CRITICAL`" as response levels. It is unresolved whether "`ERROR`" is a lifecycle state distinct from fault severity, or an inconsistent severity term. This register does not substitute "`FAULT`" for "`ERROR`" and does not infer which reading is intended.

#### SD-07 — Joint/Motor Mapping
**Status:** APPROVED

- **Decision:** Versioned, deterministic mapping: logical joint → AS5600 sensor ID → motor index/CAN ID, including direction, zero offset, transmission ratio. Reject duplicate sensor or CAN-ID assignments. Coupled/differential joints need a separate mapping revision.
- **Reasoning:** Stable identity + transmission metadata is required to interpret position/velocity correctly.
- **Open issue:** This one-to-one schema doesn't cover the differential end effector — that's carved out into SD-26.
- **Why it matters:** SD-07 establishes the pattern for simple joints only; the two-motor/two-DOF differential case needs its own transformation.
- **Investigate:** no independent action on SD-07 itself; once SD-26 closes, review whether SD-07's schema needs a generalized "coupled joint group" extension so future multi-motor mechanisms don't each need a bespoke carve-out.

#### SD-08 — Motor/Joint Temporal Alignment
**Status:** APPROVED

- **Decision:** Measured observation skew < 5 ms in normal operation, target < 1 ms for dynamic joints. Independent acquisition timestamps retained; samples beyond the skew budget are flagged or down-weighted.
- **Reasoning:** A common snapshot doesn't imply simultaneous acquisition.
- **Open issue:** The ~46 ms six-axis sweep must be reconciled with estimator/control requirements — timestamping alone doesn't make stale-but-compensated data acceptable.
- **Why it matters:** Skew (how far apart readings were taken) and update *rate* (how often fresh data arrives) are different problems. If the full sweep takes 46 ms, some joints' state is up to 46 ms old no matter how well timestamped.
- **Investigate:** investigate parallelizing/reordering the six-axis sweep (simultaneous multi-sensor sampling) to cut the 46 ms figure; run a control-loop sensitivity study to find the max tolerable per-joint staleness at target speeds; consider sampling faster-changing joints more often within the sweep budget.

#### SD-09 — Measurement History Ownership
**Status:** APPROVED

- **Decision:** Pi/EKF owns measurement queues, delay compensation, and estimator history. STM32 owns only bounded latest-value caches and publishes coherent records with timestamps, validity, and freshness diagnostics.
- **Reasoning:** The Pi has the computational context for fusing delayed measurements; the STM32 stays bounded and deterministic.
- **Open issue:** The 500 Hz EKF setting requires an explicit policy for how latest-value records, asynchronous updates, timestamp age, and interpolation/hold behaviour are handled.
- **Why it matters:** "Who owns history" is an architecture answer, not an algorithm answer — when a cached value is, say, 30 ms old, does the EKF hold it, extrapolate it, discard it, or flag it degraded? That must be specified per-signal.
- **Investigate:** define and document a per-signal staleness policy (hold / model-extrapolate / reject) with a max-age threshold each; prototype hold-last-value vs. motion-model extrapolation in simulation and compare error against ground truth; expose the chosen threshold as tunable configuration.

#### SD-10 — Calibration Ownership
**Status:** APPROVED

- **Decision:** Calibration computed on the Pi/engineering workstation from recorded data via a versioned procedure. Only validated parameters transfer to the STM32 through a controlled configuration path. STM32 applies parameters and reports the active calibration version.
- **Reasoning:** Offline computation is more controllable/auditable than embedding it in real-time firmware.
- **Open issue:** Calibration must also cover the differential mechanism, not just individual motor/sensor offsets and ratios.
- **Why it matters:** The differential end effector needs calibration of the *coupling itself* (how two motor positions jointly map to two DOF zero points) — a different, coupled calibration problem that depends on SD-26 being finalized first.
- **Investigate:** once SD-26's transformation is defined, design a coupled calibration procedure (jointly zeroing both end-effector motors against known DOF references); extend the calibration parameter set and SD-10/SD-11 configuration path to include the differential's coupling ratios and zero references.

#### SD-11 — Calibration Storage
**Status:** APPROVED

- **Decision:** Versioned, CRC-protected calibration records in two STM32 flash slots (or equivalent power-loss-safe scheme). Includes schema version, joint/sensor identity, offset/gain/limits, generation counter, validity marker. Host-side source copy retained; invalid/incomplete records rejected, falling back to `UNCONFIGURED`.
- **Reasoning:** Local persistence keeps runtime self-contained; redundancy protects against interrupted writes.
- **Open issue:** Concrete flash schema layout, endurance under expected write frequency, and power-loss-mid-write behaviour are untested on hardware — this is release condition #6.
- **Why it matters:** Architecture is decided; the concrete schema, flash wear/endurance, and power-loss behaviour are not yet verified.
- **Investigate:** define the concrete flash schema (field layout, version header, CRC placement) against the target MCU's endurance datasheet; run repeated power-loss-during-write tests on actual hardware; add a boot-time integrity check that falls back to the host-side copy if both on-device records fail validation.

#### SD-12 — Authoritative Angle Representation
**Status:** MODIFIED

- **Decision:** Calibrated radians are authoritative at the host/API level; raw AS5600 counts retained diagnostically. The current processed-millidegree wire field must **not** be silently reinterpreted — radians require an explicit versioned schema change and documented conversion.
- **Reasoning:** Radians match robotics/ROS convention, but wire compatibility must change deliberately. The AS5600 is a 12-bit sensor with approximately `0.001534 rad` nominal angular quantisation per code. Four decimal places (`0.0001 rad`) are therefore used as the normal external numeric representation: this is finer than one native sensor count while avoiding any implication that the physical measurement is accurate to the displayed decimal precision. Raw AS5600 counts remain diagnostic. Detailed sensor-specific accuracy and installation considerations are recorded in `Arm_Sensor_Hub/Documentation/AS5600_PRECISION_AND_ACCURACY.md`.
- **Open issue:** Migration needs a defined schema version, conversion rules, Pi decoder update, and verification evidence before the wire field actually changes meaning. This is release condition #5.
- **Why it matters:** Changing what a wire field *means* without a version bump silently breaks any consumer still assuming the old units — a dangerous failure mode for a motion system.
- **Investigate:** assign a concrete new schema/protocol version number now; write and unit-test the conversion function against known reference angles; add a runtime schema-version check on the Pi decoder that refuses to interpret a frame as radians unless the version field confirms it; stage the rollout so STM32 and Pi update together.

#### SD-13 — Required Joint State
**Status:** APPROVED

- **Decision:** Expose stable joint identity, position, velocity where available, validity/status, acquisition timestamp, sync quality, calibration version. Effort optional until torque/current sensing is defined. ROS-facing adapter maps to standard `position`/`velocity`/optional `effort`.
- **Reasoning:** Matches ROS 2 `joint_state_broadcaster` interfaces while retaining transport metadata.
- **Open issue:** Needs explicit commanded-vs-actual state validity and command acknowledgement status, once the motor interface is final.
- **Why it matters:** Current state tells a consumer the *measured* condition, not whether the *last commanded* value was accepted/achieved — this closes the SD-04 gap.
- **Investigate:** extend the joint-state schema with a commanded-setpoint field, an actual-vs-commanded delta/validity flag, and an acknowledgement-status enum once SD-04/SD-05 settle what data is available; version this change the same way SD-12 handles its schema change.

#### SD-14 — Required Command Interface
**Status:** MODIFIED

- **Decision:** Support only commissioned position/velocity commands plus enable, disable, controlled-stop. Every command requires fresh heartbeat, valid lifecycle state, valid calibration/configuration, transport integrity. Emergency stop is a separately specified safety function, not dependent on this application command.
- **Reasoning:** Command modes must reflect actual commissioned actuator capability; separating ordinary commands from E-stop prevents mistaking a normal protocol path for an independent safety mechanism.
- **Open issue:** Command acknowledgement, freshness, timeout, cancellation, and the distinction between application-level "controlled stop" and independent "emergency stop" all need explicit definition.
- **Why it matters:** These are currently bundled informally under "stop" — but a software controlled stop and a safety-rated E-stop (SD-25) are fundamentally different mechanisms, and safety logic must never have to guess which one a signal represents.
- **Investigate:** define "controlled stop" and "emergency stop" as two distinct, separately-named operations, each with its own trigger path; document that E-stop stays reachable through the independent safety path (SD-25) even if the app command interface is unresponsive; add ack/freshness/timeout/cancel semantics to each commissioned command; fault-inject-test that E-stop still works when the normal command channel is deliberately blocked.

#### SD-15 — Fixed SPI Transaction
**Status:** APPROVED

- **Decision:** Fixed 512-byte frame, 490-byte max payload, SPI Mode 0, little-endian fields, CRC-32/ISO-HDLC, pipelined request/response ownership. Oversize payloads rejected, never truncated.
- **Reasoning:** Fixed sizing makes DMA buffers, ownership, and worst-case timing deterministic; matches the frozen v1 contract and current six-sensor/eight-motor target.
- **Open issue:** The 5 MHz operating point remains an empirical integration limit until live Pi/STM32 and physical-layer evidence is accepted.
- **Why it matters:** Frame format and integrity are implementable now, but 5 MHz depends on real cabling, connectors, and electrical noise on assembled hardware — it must be validated before being frozen (release condition #4).
- **Investigate:** run signal-integrity testing (oscilloscope eye-diagram/rise-time) at 5 MHz on the actual harness/connectors; measure CRC failure rate over an extended soak test at 5 MHz vs. a reduced clock (1–2 MHz); if 5 MHz is marginal, evaluate shielded/twisted-pair wiring, shorter runs, or a validated lower clock as fallback.

#### SD-16 — GET_SNAPSHOT Priority
**Status:** APPROVED

- **Decision:** A valid correlated `GET_SNAPSHOT` response takes priority over an unsolicited snapshot; active DMA buffers stay immutable until transaction completion; replacement frames use replace-if-new policy and increment diagnostics.
- **Reasoning:** Explicit request/response correlation is deterministic for the host and avoids corrupting an in-flight response.
- **Open issue:** Whether replacement/drop semantics preserve the freshness the 500 Hz EKF needs, without unacceptable state age, is unconfirmed.
- **Why it matters:** At 500 Hz the margin for error is small — frequent snapshot requests or DMA immutability stalls could cause replacement frames to be *dropped* rather than merely delayed, silently increasing effective data age.
- **Investigate:** instrument the replace/drop path to log every dropped/delayed replacement frame during integration testing; compute worst-case data age per joint under realistic GET_SNAPSHOT request rates; if dropped-frame age exceeds the SD-09 staleness threshold, consider prioritizing replacement over correlation, or increasing buffer depth.

#### SD-17 — SPI Host Transaction Strategy
**Status:** APPROVED

- **Decision:** Rising-edge `DATA_READY` GPIO interrupt as primary notification, configurable periodic poll (initially 1 ms) as recovery path. `DATA_READY` means a complete frame is staged; Pi remains SPI clock master.
- **Reasoning:** Interrupt minimizes latency; polling recovers from missed edges/startup races.
- **Open issue:** **No physical `DATA_READY` GPIO pin has actually been assigned on the Pi yet.** Until it is, the system runs on the 1 ms polling fallback as its *only* path.
- **Why it matters:** The design assumes interrupt-driven notification as primary with polling as fallback — but today, real transaction latency is bounded by the 1 ms poll interval, a meaningfully slower/jitterier profile than intended, relevant to SD-01/SD-08 timing.
- **Investigate:** assign an available Pi GPIO pin to `DATA_READY` and wire/test interrupt-driven notification on the bench; until then, measure actual achieved latency/jitter under polling-only so its real impact on the SD-01 timing budget is known, not assumed; once the interrupt path exists, A/B test it against polling-only.

#### SD-18 — Timestamp Accuracy
**Status:** APPROVED

- **Decision:** Target timestamp error ≤ ±1 ms relative to the shared STM32/Pi time model; capture timestamps immediately after successful decoding; expose sync validity and age.
- **Reasoning:** At 100 Hz, 1 ms is a meaningful, testable fraction of a sample period.
- **Open issue:** Whether ±1 ms is sufficient for the *actual* 500 Hz EKF operating condition is unvalidated.
- **Why it matters:** A 500 Hz EKF has a ~2 ms nominal period, so ±1 ms error is a large fraction of it — up to half a cycle of uncertainty on when a measurement was actually taken.
- **Investigate:** inject known timestamp errors up to ±1 ms into a simulation/bench test at the target 500 Hz rate and measure resulting estimate error; if unacceptable, tighten the time-sync mechanism (SD-19) or add hardware timestamping closer to the sensor, rather than relaxing the EKF rate.

#### SD-19 — TIME_SYNC Frequency
**Status:** APPROVED

- **Decision:** `TIME_SYNC` at 1 Hz nominal, configurable to 10 Hz; sync invalid after 5 seconds without an accepted update.
- **Reasoning:** Accommodates expected oscillator drift while avoiding unnecessary traffic.
- **Open issue:** Whether clock drift between syncs stays within the ±1 ms budget (SD-18) for the full interval — especially at 500 Hz where accumulated drift has more opportunities to matter — is unconfirmed.
- **Why it matters:** Sync frequency and the 5-second window were set independently of the 500 Hz EKF decision.
- **Investigate:** measure actual free-running STM32 oscillator drift on real hardware; calculate whether drift stays under ±1 ms across a full 1 Hz interval (and worst-case up to 5 seconds); if it exceeds budget, raise `TIME_SYNC` to the already-supported 10 Hz rather than changing the protocol.

#### SD-20 — Loss of Time Synchronization
**Status:** MODIFIED

- **Decision:** After 5 seconds without an accepted update: `time_sync_valid=false`, new records marked unsynchronized, local acquisition/diagnostics continue. Time-dependent motion commands are rejected/inhibited until sync returns; explicitly-defined non-motion service operations may continue.
- **Reasoning:** Stricter than "degrade everything" — separates "keep gathering data" from "don't move."
- **Open issue:** "Time-dependent motion" is not yet an enumerated, unambiguous category.
- **Why it matters:** Does it mean *all* motion (since the EKF feeding control is itself time-dependent), or only specific trajectory-timing-sensitive operations? Without a precise definition, components could apply the rule inconsistently.
- **Investigate:** produce an explicit enumerated list of what counts as time-dependent motion (likely: all closed-loop motion), documented alongside SD-02's classification matrix; implement the check as a single shared gate in the motion-permission authority, not per-component interpretation; add an integration test that forces a sync loss and confirms motion is inhibited end-to-end.

#### SD-21 — Time Offset Validation
**Status:** APPROVED

- **Decision:** Wide initial offset range accepted before first sync; narrower runtime bound afterward, initially ±1 s; implausible updates rejected (last valid offset retained, diagnostic reported); no silent slewing in v1.
- **Reasoning:** Distinguishes initial epoch acquisition from an implausible runtime jump; retaining the last valid value prevents one bad packet corrupting every timestamp.
- **Open issue:** The actual numeric bounds are provisional and need checking against real commissioning/reset scenarios.
- **Why it matters:** Need to confirm the bounds neither reject legitimate corrections nor accept implausible ones.
- **Investigate:** survey realistic worst-case cold-boot offset (STM32 with/without battery-backed RTC) to confirm the wide range covers it; during commissioning/reset testing, log any legitimate updates rejected by the ±1 s bound; tune bounds based on evidence rather than leaving them provisional.

#### SD-22 — Time Behaviour After Reset
**Status:** APPROVED

- **Decision:** Reset clears `time_sync_valid` and discards the volatile offset; timestamps stay unsynchronized until a new `TIME_SYNC` is accepted.
- **Reasoning:** A reset can invalidate the Pi/STM32 timeline relationship; reusing stale validity would create plausible-but-wrong timestamps.
- **Open issue:** Whether every consumer — especially the 500 Hz EKF — actually checks and respects the sync-validity flag after reset is unverified in the real implementation.
- **Why it matters:** If the EKF consumed unsynchronized, arbitrarily-offset timestamps as valid, it could produce a badly wrong state estimate immediately post-reset.
- **Investigate:** add an integration test that forces a reset and confirms the EKF (and every other consumer) ignores or flags data as degraded until a fresh sync; audit the EKF for any code path using a timestamp without checking validity first; consider having the STM32 refuse to publish state data at all during the unsynchronized window, removing reliance on consumer discipline.

#### SD-23 — Transient vs Persistent Fault Recovery
**Status:** APPROVED

- **Decision:** Bounded, service-specific retries for transient faults; three consecutive failures, a freshness violation, or uncertain safe operation → `ERROR`. Recovery owned by the System Manager, ends in `INACTIVE`; explicit activation required.
- **Reasoning:** Bounded retries improve availability without letting an unresponsive peripheral consume unbounded task time.
- **Open issue:** No stated rule for the moment *while* a subsystem is mid-recovery — could a different subsystem grant motion permission based on stale/partial information?
- **Why it matters:** This is a race-condition risk between per-service recovery state machines and the motion-permission logic (SD-02).
- **Investigate:** model recovery-in-progress as an explicit state visible to the motion-permission authority; run a race-condition test that triggers recovery and a motion request simultaneously to confirm permission is withheld until recovery fully completes; consider a system-wide "not ready" latch that only clears once all recovering services report healthy.

#### SD-24 — System Restart and Recovery Behaviour
**Status:** APPROVED

- **Decision:** Return services to `INACTIVE` after reset/configuration/recovery. Reactivate in dependency order, from system/task context, only after configuration, calibration, time, and safety prerequisites pass. Never automatically resume motion because a peripheral recovered.
- **Reasoning:** Explicit activation prevents unattended motion after an intermittent fault.
- **Open issue:** The actual ordered dependency sequence — across STM32, Pi, ROS 2, EKF, ros2_control, MoveIt 2, safety gating — hasn't been written down as a concrete sequence yet.
- **Why it matters:** An incorrectly-ordered restart could bring motion capability online before the safety system or EKF are actually ready.
- **Investigate:** draft an explicit startup/recovery dependency graph naming each subsystem and its readiness condition; implement it as a supervised, checked sequence (not just documentation); test under partial-failure scenarios (e.g. EKF slow to sync) to confirm it holds rather than proceeding anyway.

#### SD-25 — Independent Safety Mechanisms
**Status:** MODIFIED

- **Decision:** Before energized-motion release, document and test: independent E-stop path, hardware motor-disable/power-removal path, watchdog behaviour, actuator stop/brake behaviour, fault indication, reset behaviour, and any applicable safety-rated relay/controller. STM32/Pi heartbeat and CAN policies are supplementary controls only.
- **Reasoning:** General-purpose MCU/Pi software cannot by itself establish an independent safety function.
- **Open issue:** The boundary between "application controlled stop" and "independent emergency stop" — what triggers each, whether they interact, what happens if they disagree — isn't yet defined; that's a machine-risk-assessment/safety-architecture output.
- **Why it matters:** This is referenced as an unresolved dependency here and in SD-14.
- **Investigate:** commission/complete the machine risk assessment as the primary input (it determines required PL/SIL and what must be independent of application software); draft a safety architecture diagram showing which functions live in the independent path vs. the application path and where they interface electrically; fault-inject-test that the independent path still functions with application software deliberately disabled or hung.

#### SD-26 — Differential End-Effector Motor/DOF Mapping
**Status:** PROPOSED — added to `SYSTEM_DECISIONS.md` after the 2026-09-07 CTO approval; **not** part of that sign-off.

- **Proposed decision:** The two end-effector motors drive two end-effector rotational DOFs through a differential mechanism. This must be represented explicitly, not as two independent one-to-one joints (unlike SD-07's simple-joint pattern).
- **Open issue:** Forward/inverse transformation, motor signs, gear ratios, zero offsets, joint limits, singular/invalid configurations, and representation in ros2_control/MoveIt 2 are all undefined. Remains open until the mechanical model and mapping are verified.
- **Why it matters:** The two motors don't each map one-to-one to a DOF — their combined positions determine both outputs. Closing this requires the kinematics, the physical parameters, the safety-relevant edges (limits, singularities), and a proper representation — not an approximation as two independent joints. It's a prerequisite for SD-07 being considered complete.
- **Investigate:** derive the differential's forward/inverse kinematic equations from the CAD/physical design and verify against direct measurement; analytically identify singular/invalid motor-position combinations and add software limit checks that reject commands into them; implement the mapping as a custom ros2_control transmission (or a MoveIt 2 joint group with a mimic/coupling constraint) rather than exposing two independent joints; validate hardware-in-the-loop across full range of motion, including near-limit and near-singular configurations.

---

## 2. Historical / Source-Collected Questions (145 entries)

Source: `Open_Items_List.md`. These 145 questions are preserved as **source-collected questions**, not as a claim that all 145 remain live project work today. The source document describes itself as "the canonical register of project questions that must be answered before the corresponding requirements, interfaces, implementation decisions, or release gates can be considered complete"; that is the source document's own characterization, not an authority determination made by this register.

**Current-status rule:** A question is current work only when it is represented in the Live Reconciliation section or otherwise supported by current authoritative evidence. Questions answered or superseded by current system documents remain here for provenance.

### 2.1 System Scope and Architecture (Q1–10)
*Related: SD-02, SD-23, SD-24; system issue #5 (motion-permission authority)*

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

### 2.2 User Interface and Command Model (Q11–19)
*Related: SD-14*

11. How does the user specify the desired end-effector position?
12. Does the user provide XYZ position only, or a complete 3D pose including orientation?
13. If orientation is specified, what representation is used?
14. What coordinate frame is used for user commands?
15. What coordinate frames are required throughout the system?
16. How are invalid, unreachable, or unsafe target poses handled?
17. What feedback does the user receive when a command is accepted, rejected, or interrupted?
18. Can the user command individual joints directly, or only end-effector poses?
19. What command rate and update behaviour are required?

### 2.3 Mechanical Configuration and Degrees of Freedom (Q20–29)
*Related: SD-07, SD-26*

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

### 2.4 Sensors and Sensor Data (Q30–43)
*Related: SD-08, SD-09, SD-10, SD-11, SD-18, SD-19*

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

### 2.5 STM32 ↔ Raspberry Pi Integration (Q44–57)
*Related: SD-01, SD-04, SD-15, SD-16, SD-17*

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

### 2.6 Motor Control and ros2_control (Q58–70)
*Related: SD-04, SD-07, SD-13, SD-14, SD-26*

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

### 2.7 MoveIt 2 and Motion Planning (Q71–80)
*Related: SD-26; system issue #9*

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

### 2.8 EKF and State Estimation (Q81–90)
*Related: SD-01, SD-09; system issues #1, #10*

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

### 2.9 Safety and Fault Handling (Q91–103)
*Related: SD-02, SD-03, SD-04, SD-06, SD-25; system issues #2, #3, #4, #8*

91. What exact faults must cause immediate motion inhibition?
92. Does any sensor-data failure require an immediate stop, or are there defined tolerances for transient failures?
93. Does any unacknowledged motor command require an immediate stop?
94. What does "stop immediately" mean in measurable system terms?
95. What is the maximum permitted fault-to-motion-stop latency?
96. Which subsystem owns the emergency-stop function?
97. Is there a separate physical E-stop, and how is it integrated?
98. What is the safe state of each motor and actuator after a fault?
99. Can motion resume automatically after recovery, or must an explicit reset be performed?
100. What conditions are required before motion can resume?
101. How are faults latched, reported, logged, and cleared?
102. What safety standards or engineering practices must the project comply with?
103. What safety validation and acceptance tests are required before physical motion?

### 2.10 Calibration, Configuration, and Startup (Q104–112)
*Related: SD-10, SD-11, SD-24*

104. What configuration values are required before the system can operate?
105. Which values are fixed hardware parameters and which are runtime configuration?
106. Where are calibration and configuration values stored?
107. How are configuration versions managed?
108. What startup self-tests are required?
109. What must be verified before enabling motor power?
110. What conditions prevent startup from progressing to an armed state?
111. How are configuration or calibration mismatches detected?
112. What is the required procedure for commissioning a new or modified arm?

### 2.11 Testing and Acceptance (Q113–126)
*Related: Part 4 (release conditions), SAFETY_RELEASE_CHECKLIST*

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

### 2.12 Requirements and Documentation (Q127–135)
*Related: Part 6 (document status)*

127. Which document is authoritative for system requirements?
128. Which document is authoritative for system-level decisions?
129. Which documents are contractual interfaces versus implementation notes?
130. How are unresolved questions tracked through to decisions?
131. How are requirements traced to implementation and verification evidence?
132. What information currently marked as unspecified must be defined in the next revision?
133. What is the process for approving changes to frozen contracts?
134. How are obsolete documents identified and archived?
135. How is the project documentation kept synchronized across Karetao sub-repositories?

### 2.13 Project Planning and Release (Q136–145)
*Related: Part 4 (release conditions)*

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

## 3. Open Issues & TODOs

### 3.1 CAN Module — Bring-Up & Testing (STM32 + TJA1050 + CANable V2)

*Source: `CAN_Module_TODO.md`, mirrored verbatim in `TODO_List.md` under `Module_TODOs/CAN_Module_TODO.md`. Listed once here.*

**Current state:** `CanService` is implemented with lifecycle gating, motor registration, TX priority queue, bounded retries, RX decode path, and bus-off recovery scaffolding. CAN runs in normal mode, processed in the default FreeRTOS task loop. Pins configured: CAN1 RX on `PB8`, TX on `PB9`. Only **one motor** is currently pre-registered at startup. Current generated timing is `Prescaler=16`, `BS1=11TQ`, `BS2=2TQ` — **not yet validated against real hardware**. Host tests currently cover `can_tx_policy.c` only, not full `can_service.c` with HAL integration.

**1) Hardware bring-up**
- [ ] Confirm transceiver wiring (CAN1_TX→TJA1050 TXD, CAN1_RX→TJA1050 RXD, shared GND, 5V/3.3V compatibility)
- [ ] Add/verify 120 Ω termination at both bus ends
- [ ] Validate CANH/CANL idle and dominant levels with scope/analyzer before motion commands
- [ ] Document the exact bench topology (cable length, stubs, node count, termination locations)

**2) Bitrate and controller configuration**
- [ ] Decide initial real-test bitrate (500 kbps or 1 Mbps) and update CubeMX/HAL timing to match measured behaviour
- [ ] Verify CANable V2 bitrate matches STM32 bitrate exactly
- [ ] Re-check sample point/SJW margin against oscillator tolerance
- [ ] Record finalized timing values and rationale in `CAN_BIT_TIMING_EVIDENCE.md`

**3) Firmware readiness gaps before bench motion**
- [ ] Add duplicate CAN ID rejection in `CanService_RegisterMotor()`
- [ ] Add explicit HAL error diagnostics mapping (TX/RX/error counters by class)
- [ ] Add RX FIFO overflow tracking/handling, exposed via CAN diagnostics
- [ ] Define and implement response timeout expectations per poll/command path
- [ ] Confirm and enforce emergency-stop behaviour policy during lifecycle `ERROR`

**4) Observability for bench testing**
- [ ] Expose runtime CAN diagnostics via a host-visible channel (lifecycle state, bus-off count, queue drops, retry-exhausted count, RX ok/decode error counts)
- [ ] Add timestamped trace points for command TX, response RX, bus-off recovery attempts
- [ ] Add a bench-test checklist for power-up/idle/command/fault-recovery pass-fail logging

**5) CANable V2 test procedure**
- [ ] Create a repeatable capture script/procedure (startup, command-response, fault injection)
- [ ] Validate that expected MKS command IDs and response frames appear with correct DLC/payload
- [ ] Verify poll traffic cadence at the default 20 ms scheduler period; confirm no bus flooding
- [ ] Run a long-duration soak capture for dropped frames, decode errors, recurring bus-off

**6) Fault injection and recovery validation**
- [ ] Test bus disconnect/reconnect: confirm bus-off detection, command inhibition, recovery to inactive
- [ ] Confirm `CanService_Activate()` is required and sufficient to re-enable commands after recovery
- [ ] Test mailbox pressure/temporary TX failures; validate retry and drop diagnostics
- [ ] Verify behaviour on unknown CAN IDs and malformed DLC/payload frames

**7) Test coverage and automation**
- [ ] Add host-side tests for `can_service` logic without real hardware (registration constraints, scheduler behaviour, queue/retry edge cases via mocks)
- [ ] Add hardware-in-the-loop test notes (tooling, expected outputs) to Documentation
- [ ] Update contract status once integration gates close with measured evidence

**8) Commissioning expansion**
- [ ] Expand `s_mks_motors` and joint mapping only after each new motor passes single-node bench validation
- [ ] Validate per-motor direction, ID, and mapping consistency before multi-motor motion tests
- [ ] Freeze a known-good CAN commissioning baseline (timing + topology + firmware revision + test evidence)

### 3.2 Historical Source TODOs — Firmware / Protocol Integration Gates

*Source: `TODO_List.md`, grouped by originating document.*

**`docs/architecture.md`** — flagged as "less mature / still being integrated":
- Live Raspberry Pi ↔ STM32 SPI transaction acceptance
- 5 MHz physical SPI acceptance (DMA timing, NSS, DATA_READY/GPIO timing, signal integrity)
- Sustained/repeated SPI transaction validation
- Scan timing and other six-channel sensor parameters (still unfrozen)
- Complete TIME_SYNC target validation
- Expanded health aggregation
- CAN physical validation
- Calibration persistence
- Exact motor-controller semantics
- Independent safety validation

**`docs/hardware/arm-sensor-hub-baseline.md`**
- [ ] Add CAN TX queueing policy, retry/timeout strategy, and bus-off recovery policy
- [ ] Add integration tests for end-to-end sensor-to-host data path
- [ ] Retain live SPI host validation, 5 MHz physical acceptance, and DATA_READY/NSS electrical validation as integration gates

**`docs/interfaces/spi-service-contract.md`**
- [ ] Validate the implemented DMA/NSS path with a live Raspberry Pi host
- [ ] Validate the 5 MHz initial maximum with Pi, DMA, GPIO, NSS, and signal-integrity tests

**`docs/protocols/spi-contract.md`**
- [ ] Validate the implemented SPI3 DMA path with a live Raspberry Pi host
- [ ] Accept the 5 MHz maximum only after DMA timing, NSS behaviour, DATA_READY/GPIO timing, signal integrity, sustained transactions, and real request/response evidence are recorded
- [ ] Retain existing protocol/schema freeze decisions — implementation details must not become new requirements
- [ ] Define lifecycle states permitted for each message type

**`docs/protocols/spi-payload-schema.md`**
- [ ] Event types and severity values remain reserved for the error-handling contract; assign before implementation
- [ ] `SET_MOTOR_COMMAND` is not frozen until the Motor Service contract exists — must not be implemented from this draft alone
- [ ] Remaining schema decisions: exact event type/severity enumerations; 32-bit vs 64-bit diagnostic counters; snapshot dropped-count width and reset behaviour; whether future records use a tagged extension mechanism

**`docs/interfaces/raspberry-pi-spi.md`**
- [ ] Confirm `DATA_READY` GPIO polarity, debounce expectations, and user-space access strategy against target hardware — the Pi GPIO is **intentionally unassigned** in the current baseline (same gap as SD-17)
- [ ] Confirm the maximum accepted SPI clock once the ARM-side 5 MHz gate closes
- [ ] Confirm final request/response retry policy for stalled/partial transactions
- [ ] Retain fixed 512-byte transfers as the current implementation; revisit only through a versioned contract change

**`RaspberryPi_Sensor_Hub/README.md`**
- [ ] Validate the implemented Linux `spidev` backend on the target Raspberry Pi
- [ ] Close the DATA_READY GPIO integration decision only once a GPIO is actually assigned and validated

**`Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` and `SPI_SYSTEM_INTERFACE.md` § 11–12 — TIME_SYNC Implementation Gaps**

*Source: `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md` § Audit (audit date: 2026-09-21)*

Five implementation gaps are recorded without proposed fixes — these are gaps in the current implementation, not design decisions:

- [ ] **Gap 1:** `frame_time_us` in SPI frame header must carry hub time (local + offset), not raw TIM2 counter. Currently populated at `spi_protocol.c:33` with `TimeService_NowUs()` (raw time). Requires offset application before frame assembly completes.
- [ ] **Gap 2:** `measurement_timestamp_us` in sensor records must carry synchronized hub time. Currently populated at `sensor_task.c:165–173` with raw `sample.timestamp_us` without offset application. TimeService_SyncSnapshot is available but not used to convert to hub time domain.
- [ ] **Gap 3:** GET_DIAGNOSTIC request and DIAGNOSTIC response (message type 0x03) not implemented. SPI_PAYLOAD_SCHEMA.md defines DIAGNOSTIC payload with `time_sync_valid` field, but no implementation exists. GET_STATUS returns ACK with no synchronization metadata; no standard way for host to query time sync validity.
- [ ] **Gap 4:** Accepted `time_offset_us` not carried in any v1 SPI payload. STM32 accepts and stores offset, but no outbound SPI field exposes it for host verification or confirmation.
- [ ] **Gap 5:** Raspberry Pi has no TIME_SYNC encoder/sender. SpiDevice class (`RaspberryPi_Sensor_Hub/src/spi/spi_device.py`) lacks `time_sync()` method. spi_protocol.py defines MessageType.TIME_SYNC but no payload encoder. Pi cannot initiate synchronization.

**Audit blockers** — all five gaps must be resolved before synchronization can be marked operational:

1. Apply offset to frame_time_us before DMA handoff
2. Apply offset to measurement_timestamp_us in sensor task
3. Implement GET_DIAGNOSTIC request handler and DIAGNOSTIC response serialization
4. Define payload extension or future schema version to export accepted offset
5. Implement TIME_SYNC encoder in Pi spi_protocol.py and caller in SpiDevice

**Related integration validation tasks** (after implementation gaps are closed):

- [ ] Validate achieved ±1 ms timestamp accuracy target (SD-18) against live system timeline
- [ ] Instrument per-axis timestamp evolution during operation; confirm no drift accumulation over 5-second sync intervals
- [ ] Confirm motion is inhibited when time_sync_valid becomes false; audit motion-permission authority for consistency (see SD-20)
- [ ] Measure timestamp discontinuities when offset is stepped; validate acceptable for EKF and motion control
- [ ] Measure round-trip TIME_SYNC latency and compare to transport uncertainty budget

### 3.3 Historical Source TODOs — Contract Status / Next Actions

*Source: `Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md`*

- [ ] Complete named CAN, SPI, motor, and safety gates
- [ ] Implement prerequisite validation and explicit post-recovery activation request
- [ ] Validate the 5 MHz initial SPI maximum with Pi, DMA, GPIO, NSS, and signal-integrity tests
- [ ] Validate exact controller, transceiver/topology/termination, candidate timing, measured load, retry timing, and recovery behaviour
- [ ] Extend coverage as more motor/sensor fields become live; retain target validation evidence
- [ ] Expand producer coverage beyond the current commissioned sensor/motor set
- [ ] Complete documented Pi/DMA/GPIO clock acceptance testing with a live host
- [ ] Expand composite-access coverage; define broader arbitration/recovery behaviour
- [ ] Freeze scan period, per-channel timeout, settle time, and healthy-channel threshold against the measured ~46 ms full-six-axis sweep
- [ ] Validate end-to-end Pi-driven TIME_SYNC behaviour on target hardware; retain build evidence
- [ ] Define canonical CRC serialization and flash persistence/power-loss handling
- [ ] Commission complete physical mapping and bind it to persisted configuration
- [ ] Implement response-level events and bounded recovery escalation
- [ ] Expand snapshot thresholds, host reporting cadence, and fault acknowledgement behaviour
- [ ] Preserve the successful CI firmware-build evidence, size/checksum output, and uploaded artifacts
- [ ] Verify exact controller behaviour before freezing command semantics

### 3.4 Historical Source Safety Checklist — Source Records All Items as BLOCKED

*Historical source material only; current live safety work is indexed by LIVE-05 and related Section 0 items. Source: `Arm_Sensor_Hub/Documentation/SAFETY_RELEASE_CHECKLIST.md`. The source checklist records all 14 items as "BLOCKED: no artifact recorded". This is a source-reported status; its currency has not been independently revalidated against the current repository state in this working register. No item below is marked complete, and no missing safety evidence has been created or inferred here. Cross-referenced to the numbered release conditions in Part 4.*

| # | Checklist item | Maps to release condition |
|---|---|---|
| 1 | Machine risk assessment and required PL/SIL target | #1 |
| 2 | Independent E-stop path | #2 |
| 3 | Hardware motor-disable or power-removal path | #2 |
| 4 | Watchdog behavior and fault recovery | #2 |
| 5 | Actuator stop/brake/power behavior | #2 |
| 6 | Fault indication and operator-visible reporting | #2 |
| 7 | Reset behavior and explicit non-automatic reactivation | #2 |
| 8 | Measured stopping time in hazardous operating conditions | #2 |
| 9 | Exact MKS controller model, firmware, command, feedback, and brake behavior | #3 |
| 10 | CAN physical layer, bitrate, load, termination, topology, and recovery | #3 |
| 11 | SPI clock, Pi driver, DMA, GPIO, polling, host-stall, and signal-integrity acceptance | #4 |
| 12 | Versioned payload schema and conversion evidence (millidegrees → radians) | #5 |
| 13 | Calibration flash schema, CRC, power-loss, sector allocation, and endurance test evidence | #6 |
| 14 | Applicable safety-rated relay/controller and safety architecture | #2 |

### 3.5 Historical / Housekeeping Items

- **`PHASE_1_FINAL_CLEARANCE_REPORT.md`** (dated 2026-09-07): recorded missing ARM toolchain evidence *at that review point*. **This historical finding should not be treated as the current build state** — current CI evidence lives in `BUILD_CONTRACT.md` and `CONTRACT_STATUS.md`. One still-open follow-up: deepen negative-path test coverage for hardware-facing service flows beyond smoke level (P2, non-blocking).
- **`LIFECYCLE_CONTRACT.md`**: automated host tests were intentionally deferred from the first implementation pass; required future test cases remain listed but unwritten.
- **`Conversations/CTO_DECISION_BRIEF.md`**: TODO_List.md lists the brief's own safety-approval checklist (SD-02, 03, 04, 06, 05, 14, 20, 23, 24, 25) and "Approval record SD-01 to SD-25" as still pending. **⚠ This appears stale** — `CTO_DECISION_FINAL.md` records the CTO's actual sign-off, dated 2026-09-07, with the seven exceptions/conditions in Part 4. Treat the FINAL document's exceptions as the live release gates, not the BRIEF's own pending-approval checklist.
- **`Sprint_1_List.md`** — remaining work:
  - Task 07: canonical serialized CRC coverage via shared CRC-32/ISO-HDLC helper; redundant flash-sector allocation; erase/write ordering; endurance budget; power-loss recovery validation; wire validated calibration state into mapping and lifecycle prerequisites
  - Task 08: complete physical commissioning; persisted configuration binding; future mapping schema for coupled/differential joints
  - Task 09: freeze scan timing parameters against the commissioned SD2–SD7 mapping and the measured ~46 ms full-axis sweep; calibration binding remains open
  - Task 18: not implemented, deferred to when Motor Service work begins (open Sprint 2+ item)
  - Sprint 1 exit criteria checklist items remain unchecked
- **Code vs. document consistency issues found in code review:**
  - `spi_device.py` still provides only stateless `transact`/`get_status` helpers — do not claim complete host-side outstanding-transaction state tracking merely because frame-level sequence/version validation exists
  - Live Pi/STM32 request/response, `DATA_READY` GPIO assignment, NSS behaviour, 5 MHz acceptance, and signal integrity remain physical validation work, not implementation TODOs

---

## 4. Release Conditions / Safety Gates

*Source: `CTO_DECISION_FINAL.md` "Exceptions / Conditions," restated identically as "Important release conditions" in `SYSTEM_DECISIONS.md`. These are the CTO's approval conditions — treat failure of any as a release blocker for energized motion, not a reason to weaken the approved firmware behaviour.*

1. **Machine risk assessment.** Complete and approve it, including required safety functions and PL/SIL target, before motion release.
2. **Independent safety validation.** Validate the independent E-stop and motor-disable path, measured stop time, watchdog behaviour, and actuator brake/power behaviour on the assembled system.
3. **CAN network verification.** Verify the exact MKS controller, CAN physical topology, APB1-derived bit timing, worst-case bus load, recovery behaviour, and termination before freezing SD-05 and production CAN configuration.
4. **SPI validation.** Validate the initial 5 MHz SPI limit, 1 ms polling fallback, GPIO notification, DMA timing, signal integrity, and host-stall recovery with the Raspberry Pi.
5. **Angle-representation schema versioning.** Version the radians representation before changing the current processed-millidegree wire field.
6. **Calibration storage testing.** Complete calibration flash endurance, power-loss, schema, and parameter-integrity tests.
7. **Enforcement.** Treat any failure of conditions 1–6 as a release blocker for energized motion, not as a reason to weaken the approved firmware behaviour.

See Section 3.4 for the more granular 14-item safety checklist mapped against these seven conditions — the source checklist records all 14 as BLOCKED with no artifact recorded (source-reported status; see Section 3.4's qualification).

---

## 5. Source-Collected System Issues — Reconciled Against Section 0

*Source: `SYSTEM_DECISIONS.md`. These ten items are retained as source-collected issues. They are **not an independent live-work list**: current work status is represented only by Section 0. Each item is mapped to the live item(s) that now own its reconciliation.*

| Source issue | Source-collected issue | Section 0 reconciliation |
|---|---|---|
| 1 | **EKF timing** — EKF is currently set to 500 Hz; downstream constraints may require adjustment. This does not mean the complete six-axis sensor scan currently operates at 500 Hz. | **LIVE-07 / LIVE-16** |
| 2 | **Sensor failure response** — the rule that sensor-data failure stops motion needs an explicit specification covering invalid, missing, stale, and failed sensors. | **LIVE-10** |
| 3 | **Motor command acknowledgement** — must be separately defined from motor feedback and communication heartbeat. | **LIVE-11 / LIVE-13** |
| 4 | **Fault-to-safe-state timing** — “stop immediately” must become a measurable timing requirement. | **LIVE-12 / LIVE-05** |
| 5 | **Motion-permission authority** — define which system component has final authority to permit or inhibit motion. | **LIVE-01 / LIVE-05** |
| 6 | **Differential end effector** — the two-motor/two-DOF mechanical transformation must be formally defined before the joint model is frozen. | **LIVE-06 / LIVE-15**; SD-26 remains proposed |
| 7 | **Motor-controller semantics** — exact MKS controller behaviour remains an integration dependency. | **LIVE-02 / LIVE-11 / LIVE-13** |
| 8 | **Safety boundary** — define the interface between application-level safety controls and the independent safety function. | **LIVE-05 / LIVE-14** |
| 9 | **MoveIt 2 / ros2_control model** — the authoritative mechanical/joint model must include the differential end effector and its limits. | **LIVE-06 / LIVE-15** |
| 10 | **Sensor update architecture** — determine how a 500 Hz EKF consumes asynchronously updated sensor records and what maximum data age is acceptable. | **LIVE-07 / LIVE-16** |

**Reconciliation rule:** If a source-collected issue is not mapped to a Section 0 item, it is not yet reconciled and must be either added to Section 0 or explicitly marked historical/deferred/superseded with supporting evidence. Section 0 is the sole live-work index in this document.
---

## 6. Source Document Status

| Source file | Role | Status |
|---|---|---

### 0. Live Reconciliation — Current Project Work

This section is the **current work index**. Detailed historical source collation remains below for provenance, but an item should appear here only when current repository evidence supports it as live work.

### 0.1 Current live items

| ID | Current status | Live item | Primary source(s) | GitHub tracking |
|---|---|---|---|---|
| LIVE-01 | OPEN — DESIGN | **System motion-permission authority** — approve the owner/API, prerequisite set, freshness thresholds, inhibit semantics, and recovery/reactivation behaviour for the proposed aggregate motion gate. | `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`; `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`; `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md`; `Documentation/01_SYSTEM/SYSTEM_LIFECYCLE.md` | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-02 | OPEN — VERIFICATION / RELEASE BLOCKER | **CAN integration** — reconcile the current 875 kbps implementation with the 1 Mbps system target or formally revise the requirement; validate exact MKS controller behaviour, physical topology, timing, load, and recovery. | `Documentation/02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md`; `Documentation/05_VERIFICATION/CAN_INTEGRATION_EVIDENCE.md`; `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-03 | OPEN — VERIFICATION / RELEASE BLOCKER | **SPI physical and host integration** — validate 5 MHz acceptance, DMA/NSS behaviour, DATA_READY GPIO path, signal integrity, sustained 512-byte transfers, and host-stall recovery on target hardware. | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`; `Documentation/05_VERIFICATION/INTEGRATION_GATES.md`; `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-04 | OPEN — IMPLEMENTATION / RELEASE BLOCKER | **TIME_SYNC implementation gaps** — close the five gaps identified by the 2026-09-21 audit before synchronization is treated as operational. | `Documentation/05_VERIFICATION/TIME_SYNC_CHARACTERISATION_EVIDENCE.md`; `Documentation/05_VERIFICATION/TIME_SYNC_VALIDATION.md`; `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`; `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-05 | OPEN — RELEASE BLOCKER | **Independent safety release gates** — complete the machine risk assessment and required safety architecture/evidence, including E-stop, motor-disable, watchdog, brake/stop behaviour, stopping time, fault indication, reset, and applicable safety-rated architecture. | `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md`; `Documentation/05_VERIFICATION/INTEGRATION_GATES.md`; `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-06 | PROPOSED / OPEN — DESIGN & VERIFICATION | **Differential end-effector mapping** — define and verify the two-motor/two-DOF transformation, limits, singular/invalid configurations, and its MoveIt 2 / ros2_control representation. SD-26 remains proposed and is not CTO-approved. | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` (SYS-MECH-001); `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md`; `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md`; `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-07 | OPEN — DESIGN / VERIFICATION | **EKF and sensor-timing architecture** — define the asynchronous/multi-rate EKF handling policy, acceptable per-signal data age/staleness, and verify end-to-end timing against the measured ~46 ms six-axis sweep. | `Documentation/01_SYSTEM/SYSTEM_TIMING.md`; `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`; SD-01/SD-08/SD-09 in this register | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-08 | OPEN — VERIFICATION | **Calibration/configuration release evidence** — complete the remaining calibration/configuration schema, integrity, power-loss/endurance, controlled-transfer, and commissioning evidence required by the release conditions. | `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md`; `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md`; release conditions below | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-09 | OPEN — VERIFICATION | **System verification** — all system verification groups remain OPEN; integrated evidence must be accepted before `SYSTEM_VERIFIED` can be assigned. | `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`; `Documentation/05_VERIFICATION/INTEGRATION_GATES.md` | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-10 | OPEN — DESIGN / VERIFICATION | **Sensor failure response** — define explicit handling for invalid, missing, stale, and failed sensor data, including motion-inhibit behaviour, owner, recovery, and evidence. | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`; SD-09; source-collected issue #2 below | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-11 | OPEN — DESIGN / VERIFICATION | **Motor command acknowledgement** — define command-acceptance semantics separately from feedback freshness and heartbeat, including timeout, failure response, and target-controller capability. | SD-04/SD-05; CAN interface/evidence; source-collected issue #3 below | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-12 | OPEN — DESIGN / VERIFICATION / RELEASE BLOCKER | **Fault-to-safe-state timing** — derive measurable stopping/fault-response limits from the machine risk assessment and verify worst-case stop behaviour at commissioned operating conditions. | SD-03; `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md`; release condition #2; source-collected issue #4 below | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-13 | OPEN — DESIGN / VERIFICATION | **Motor-controller semantics** — establish the exact MKS controller model/firmware, command/feedback semantics, acknowledgement behaviour, brake/stop behaviour, and recovery contract before freezing integration assumptions. | SD-05; CAN interface/evidence; safety checklist item 9 | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-14 | OPEN — DESIGN | **Safety boundary** — define the interface between application-level safety controls and the independent safety function, including ownership, inhibit path, reset, and non-automatic reactivation. | SD-25/SD-14; `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md`; source-collected issue #8 below | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-15 | OPEN — DESIGN / VERIFICATION | **MoveIt 2 / ros2_control mechanical model** — reconcile the authoritative joint model, differential end-effector mapping, limits, and control interfaces with the proposed SD-26 architecture. | SD-26/SD-07; `Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md`; source-collected issue #9 below | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |
| LIVE-16 | OPEN — DESIGN / VERIFICATION | **Sensor update architecture** — define how the 500 Hz EKF consumes asynchronously updated sensor records and the maximum acceptable data age, including late/out-of-sequence data handling where applicable. | SD-01/SD-09; `Documentation/01_SYSTEM/SYSTEM_TIMING.md`; source-collected issue #10 below | Parent reconciliation: [#9](https://github.com/LentonNeale/Karetao/issues/9); dedicated issue to be created |

### 0.2 Current release gate summary

The following remain release-relevant even when the detailed evidence work is owned elsewhere:

1. Machine risk assessment / safety architecture.
2. Independent safety-path validation.
3. CAN target-hardware and physical-layer verification.
4. SPI target-hardware and physical-layer verification.
5. Angle-representation schema migration before changing wire-field meaning.
6. Calibration storage and integrity testing.
7. Acceptance of integrated system verification evidence.

### 0.3 Reconciliation rules

- A **design question** is not closed merely because an implementation exists.
- A **component verification result** does not establish system verification.
- A **proposed** requirement or architecture decision must remain explicitly proposed until approved by the applicable decision authority.
- Historical TODOs and archived sprint checklists remain below only as provenance; they are not automatically promoted into live work.
- A current GitHub Issue is a tracking mechanism, not a source of technical authority.
- When a live item is closed, update the relevant authoritative source/evidence first where necessary, then update this register and close the corresponding GitHub Issue.
- When current evidence contradicts an inherited checklist entry, the current authoritative source takes precedence and the discrepancy should be recorded rather than silently discarded.


---

## 1. System Decisions (SD-01 to SD-26)

**Decision chain — distinct roles, not a strict authority hierarchy:**

| Document | Role |
|---|---|
| `CTO_DECISION_BRIEF.md` | Historical proposal / decision-background evidence. As an approval record it is superseded by `CTO_DECISION_FINAL.md` (see Section 6 and the conflict noted in Section 3.5). |
| `CTO_DECISION_FINAL.md` | Evidence of CTO approval for SD-01–SD-25, dated 2026-09-07, subject to the release conditions in Part 4. |
| `SYSTEM_DECISIONS.md` | **Non-authoritative decision index.** Use current approval evidence and current system requirements/architecture sources for authority; current system requirement wording is maintained in `SYSTEM_REQUIREMENTS.md`, and architecture-level proposals remain in `ARCHITECTURE_DECISIONS.md`. |
| This register | Reconciliation *working* artifact assembled for readability. It is not itself a source of Karetao authority and does not resolve conflicts between the documents above. |

SD-26 was added to `SYSTEM_DECISIONS.md` **after** the 2026-09-07 CTO approval and remains **PROPOSED — not CTO-approved** (see the SD-26 entry below). It is not part of the SD-01–SD-25 approval.

**Decision-set status:** SD-01–SD-25 are the approved/modified decision baseline subject to their release conditions; SD-26 remains **PROPOSED** and is not part of the 2026-09-07 CTO approval. Decision status is inherited from the applicable approval evidence; this register does not grant approval.

> None of these decisions certify the assembled robot as safe or authorize energized motion. Every decision below is subject to the release conditions in Part 4.

### 1.1 Status overview

| ID | Area | Status |
|---|---|---|
| SD-01 | System timing | MODIFIED |
| SD-02 | System-wide failure classification | MODIFIED |
| SD-03 | Raspberry Pi communication loss | APPROVED |
| SD-04 | Motor feedback/command timeout | APPROVED |
| SD-05 | CAN network requirements | MODIFIED |
| SD-06 | CAN bus failure | APPROVED |
| SD-07 | Joint/motor mapping | APPROVED |
| SD-08 | Motor/joint temporal alignment | APPROVED |
| SD-09 | Measurement history ownership | APPROVED |
| SD-10 | Calibration ownership | APPROVED |
| SD-11 | Calibration storage | APPROVED |
| SD-12 | Authoritative angle representation | MODIFIED |
| SD-13 | Required joint state | APPROVED |
| SD-14 | Required command interface | MODIFIED |
| SD-15 | Fixed SPI transaction | APPROVED |
| SD-16 | GET_SNAPSHOT priority | APPROVED |
| SD-17 | SPI host transaction strategy | APPROVED |
| SD-18 | Timestamp accuracy | APPROVED |
| SD-19 | TIME_SYNC frequency | APPROVED |
| SD-20 | Loss of time synchronization | MODIFIED |
| SD-21 | Time offset validation | APPROVED |
| SD-22 | Time behaviour after reset | APPROVED |
| SD-23 | Transient vs persistent fault recovery | APPROVED |
| SD-24 | System restart and recovery | APPROVED |
| SD-25 | Independent safety mechanisms | MODIFIED |
| SD-26 | Differential end-effector motor/DOF mapping | **PROPOSED (not yet CTO-approved)** |

.|
| `ARCHITECTURE_DECISIONS.md` | Framework placeholder for long-lived architecture decisions | **Empty** — no content yet |
| `CAN_Module_TODO.md` | CAN bring-up/test checklist | Active — see Section 3.1 |
| `CTO_DECISION_BRIEF.md` | Original proposal for SD-01–SD-25 | **Superseded** by `CTO_DECISION_FINAL.md`; retained for historical justification text only |
| `CTO_DECISION_FINAL.md` | CTO's approved decisions, SD-01–SD-25 | **Approved baseline**, dated 2026-09-07, subject to the 7 release conditions in Part 4 |
| `Open_Items_List.md` | Source register of 145 open project questions (describes itself as "canonical" — see Section 2's qualifying note) | Active — none marked answered |
| `SYSTEM_DECISIONS.md` | Historical decision index | **NON-AUTHORITATIVE / HISTORICAL INDEX**. Preserve for provenance; do not use it alone to establish current status. Current system requirement wording is maintained in `SYSTEM_REQUIREMENTS.md`; current architecture proposals are maintained in `ARCHITECTURE_DECISIONS.md`; this register is the reconciliation index. |
| `TODO_List.md` | Consolidated TODOs pulled from ~15 other repository documents | Active — reorganized in Section 3 |

This register (the document you are reading) is not listed above because it is not a Karetao source document — it is a reconciliation working artifact built from the sources above, and it does not itself carry authority over any of them.

**Reconciliation note:** Legacy source collation remains useful for provenance, but it is no longer sufficient to determine current status. In particular, any inherited item claiming that SD-01–SD-25 approval is pending is **SUPERSEDED / HISTORICAL** because `CTO_DECISION_FINAL.md` records the approval dated 2026-09-07. Current release conditions are the seven conditions in Part 4, and current live work is indexed in Section 0