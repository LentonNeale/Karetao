# Karetao decisions and live work register

Status: Rebuilt 2026-10-03 to the charter scope. Not an authority source: requirements are in `SYSTEM_REQUIREMENTS.md`, parameters in `PARAMETER_REGISTER.md`, decisions in `ARCHITECTURE_DECISIONS.md`, verification status in `SYSTEM_VERIFICATION_MATRIX.md`. Who decides: Lenton Neale (`PROJECT_CHARTER.md`); "CTO" in provenance means Lenton Neale.

Provenance: Sections 2, 3 and 5 of the former register (145 historical questions, source-collected TODOs, source-collected issues) were removed on 2026-10-03; the last commit holding them is the parent of the commit that introduces this version (`git log -- this file`).

## 0. Live work

Status vocabulary: OPEN — DESIGN / IMPLEMENTATION / VERIFICATION; DEFERRED; CLOSED.

| ID | Status | Live item | Primary sources | GitHub |
|---|---|---|---|---|
| LIVE-17 | OPEN — IMPLEMENTATION / VERIFICATION | Fitted-encoder reading: NOT_FITTED on the wire (validity bit 6), commissioning table filled (joint names, encoder fitted), bench evidence per axis | SYS-ENC-001..003; `SPI_PAYLOAD_SCHEMA.md`; `SYSTEM_CONFIGURATION.md` §2.1 | #66, #67 (Stage 1); absorbs #48 |
| LIVE-18 | OPEN — IMPLEMENTATION / VERIFICATION | Six motor positions in the snapshot: register all commissioned motors, poll all, bench evidence at rest and in motion | SYS-MOT-001/002; `CAN_SYSTEM_INTERFACE.md` | #61, #62 (Stage 2); absorbs #22, #29, #51 (MKS controller semantics) |
| LIVE-19 | OPEN — IMPLEMENTATION | Clock-sync implementation per Issue #12 (ISR capture, request_received_local_us, Pi ClockSync, DIAGNOSTIC v2, TIME_SYNC removal) | SYS-TS-001; `ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`; `TIME_SYSTEM_INTERFACE.md` | #42, #45 (Stage 2) |
| LIVE-20 | OPEN — IMPLEMENTATION / VERIFICATION | Gated motion X/Y/Z: SET_MOTOR_COMMAND path, gate simplified to SYS-GATE-001, initial movement records written, X/Y/Z rows verified | SYS-GATE-001, SYS-CMD-001; `HOST_SYSTEM_INTERFACE.md`; matrix "Verified motion per joint" | #63, #64, #65 (Stage 4); absorbs #10, #17–#20, #23, #24, #26, #27, #49 |
| LIVE-21 | OPEN — DESIGN / VERIFICATION | Attended-operation safety behaviours SAFE-01..05: E-stop hardware confirmed, link-loss stop sequence, reset no-resume, fault visibility; watchdog and CAN-failure scope decided | `SAFETY_REQUIREMENTS.md`; matrix "Safety behaviours" | absorbs #21, #25, #31, #50 (re-scoped); #14, #46 closed as not planned (PL/SIL) |
| LIVE-22 | OPEN — VERIFICATION | Measure the links (charter goal 3): SPI clock and cable, CAN bitrate and load, sync skew and timestamp error, poll periods, per-axis latency, DATA_READY GPIO electrical validation on the Pi (SD-17); register rows move Provisional → Measured | `PARAMETER_REGISTER.md` "Measurement stages"; `EVIDENCE_RECORD_FORMAT.md` | absorbs #43 (LIVE-02), #44 (LIVE-03), #32 (Stage 3) |
| LIVE-08 | OPEN — VERIFICATION | Calibration evidence (versioning, CRC, redundancy, power-loss, host copy, controlled transfer) | SYS-CAL-001; `SYSTEM_CONFIGURATION.md` §3 | #47, #28 |
| LIVE-09 | OPEN — VERIFICATION | System verification: rows accepted by Lenton Neale in the matrix | `SYSTEM_VERIFICATION_MATRIX.md` | #13 |

Closed or merged:

- LIVE-01 → LIVE-20 (gate decided, SYS-GATE-001).
- LIVE-02, LIVE-03 → LIVE-22.
- LIVE-04 → LIVE-19.
- LIVE-05 → LIVE-21 (PL/SIL parts withdrawn).
- LIVE-06, LIVE-15 → DEFERRED (differential end effector, charter non-goal until hardware; SD-26 proposed; #11, #15 closed not planned).
- LIVE-07, LIVE-16 → CLOSED, not planned (EKF non-goal; #12, #33–#36 closed; #32 → LIVE-22).
- LIVE-10 → LIVE-17.
- LIVE-11, LIVE-13 → LIVE-18/LIVE-20.
- LIVE-12 → LIVE-21.
- LIVE-14 → closed (no independent safety function is claimed; charter).

## 1. System decisions SD-01..SD-26

| ID | Subject | Status (2026-09-07 baseline) | Charter 2026-10-03 |
|---|---|---|---|
| SD-01 | System timing | MODIFIED | qualified: EKF clause withdrawn; the 100 Hz rate is a former target, not a requirement; the working value is PRM-ACQ-01 (20 Hz, bounded by the measured sweep) |
| SD-02 | System-wide failure classification | MODIFIED | unchanged |
| SD-03 | Raspberry Pi communication loss | MODIFIED (Issue #12) | modified by Issue #12 (unchanged by charter) |
| SD-04 | Motor feedback/command timeout | APPROVED | unchanged |
| SD-05 | CAN network requirements | MODIFIED | unchanged |
| SD-06 | CAN bus failure | APPROVED | unchanged |
| SD-07 | Joint/motor mapping | APPROVED | unchanged |
| SD-08 | Motor/joint temporal alignment | APPROVED | unchanged |
| SD-09 | Measurement history ownership | APPROVED | qualified: estimator wording dropped; Pi owns measurement history |
| SD-10 | Calibration ownership | APPROVED | unchanged |
| SD-11 | Calibration storage | APPROVED | unchanged |
| SD-12 | Authoritative angle representation | MODIFIED | unchanged |
| SD-13 | Required joint state | APPROVED | unchanged |
| SD-14 | Required command interface | MODIFIED | unchanged |
| SD-15 | Fixed SPI transaction | APPROVED | unchanged |
| SD-16 | GET_SNAPSHOT priority | APPROVED | unchanged |
| SD-17 | SPI host transaction strategy | APPROVED | unchanged |
| SD-18 | Timestamp accuracy | APPROVED | unchanged |
| SD-19 | TIME_SYNC frequency | MODIFIED (Issue #12) | modified by Issue #12 (unchanged by charter) |
| SD-20 | Loss of time synchronization | MODIFIED | scope resolved: no time-dependent motion in current scope |
| SD-21 | Time offset validation | MODIFIED (Issue #12) | modified by Issue #12 (unchanged by charter) |
| SD-22 | Time behaviour after reset | MODIFIED (Issue #12) | modified by Issue #12 (unchanged by charter) |
| SD-23 | Transient vs persistent fault recovery | APPROVED | unchanged |
| SD-24 | System restart and recovery | APPROVED | unchanged |
| SD-25 | Independent safety mechanisms | MODIFIED | kept; no PL/SIL rating claimed |
| SD-26 | Differential end-effector motor/DOF mapping | PROPOSED (not yet approved by Lenton Neale) | deferred until hardware exists |

Full decision text and rationale are in git history (the former §1.2); the Issue #12 record stays in `ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`.

## 2. Before gated motion (attended operation)

Replaces the former release conditions. For each axis, before it moves under the gate:

1. Commissioning table filled for the axis.
2. SAFE-01 power cut tested by hand.
3. SAFE-02 link-loss stop observed.
4. Gate evidence for the axis (SYS-GATE-001).
5. Calibration evidence where the axis uses one.

## 3. Milestones

- Stage 1: Fitted encoders.
- Stage 2: Motor positions and timestamps.
- Stage 3: Links measured.
- Stage 4: Gated motion X/Y/Z.
- Stage 5: Remaining joints.

GitHub milestones M1–M7 are to be renamed or closed to these (held for Lenton Neale's confirmation).
