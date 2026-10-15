# Architecture Decisions

This is the live decision log for architecture-level decisions. The full decision list is in the **[Karetao Decisions, Questions, and Issues Register](KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md)** (Architecture Decisions section).

## Motion gate (SYS-GATE-001)

**Status:** Decided 2026-10-03, Lenton Neale (applied per CHARTER_ALIGNMENT_PLAN.md D-3; confirmed at sign-off 2026-10-04).

**Decision:** `MOTION_PERMITTED = lifecycle ACTIVE ∧ CAN ACTIVE ∧ ¬link_stale ∧ ¬global_motion_inhibit ∧ motor_ready`.

- ClockSync validity, required-sensor validity, calibration validity and motor-feedback freshness are not gate inputs for single gated commands. They remain diagnostics and may be added by a later decision.
- Single gated commands are not time-dependent motion. This resolves the SD-20 scope question: no time-dependent motion exists in the current scope.
- The proposed SYS-MOTION-001..003 are replaced by SYS-GATE-001 ([`SYSTEM_REQUIREMENTS.md`](../01_SYSTEM/SYSTEM_REQUIREMENTS.md)).
- `motion_permission.c` today evaluates a superset (heartbeat, time sync, sensors, calibration, feedback). Simplifying it to this set is a code issue ([LIVE-20]).

## MKS drive work mode

**Status:** Provisional, 2026-10-15, Lenton Neale. Confirmed or replaced by the holding check below.

**Decision:** every MKS drive runs in SR_CLOSE (serial interface, closed loop; 82H value 04H).

Basis, from the MKS SERVO42D/57D CAN manual V1.0.9 ([`config-commands.md`](../../icm-project/references/mks-servo42d-57d-can/config-commands.md) in the vendor reference):
- Bus motion commands are valid only in the SR modes (p. 68); the factory default CR_vFOC ignores them.
- SR_CLOSE runs at a fixed working current (Ma) and is limited to a lower top speed than SR_vFOC (pp. 20, 68). The geared joints do not need the higher speed.
- In SR_CLOSE the holding current percentage (9BH) applies at rest; in SR_vFOC it does not (p. 20). A stopped joint therefore holds with only that share of Ma.

Confirmation (bench, [`BRING_UP.md`](../../Hardware/bench-wiring/BRING_UP.md) phase 9): with the chosen Ma and holding percentage, each joint holds its worst gravity pose without position drift, and the motor temperature stays acceptable after a set run time. The Ma, holding percentage, run time and limits are entered in [`PARAMETER_REGISTER.md`](../06_CONFIGURATION/PARAMETER_REGISTER.md) as Provisional rows when the check is planned. If a joint fails, SR_vFOC is the alternative for that joint and this decision is revised.

Consequences: the PID set that applies is 97H (CLOSE), left at the factory values (the manual advises against changing them, p. 46). CanRate, the 98H heartbeat and the multi-motor sync mode are separate project settings and are not changed by this decision.

## MKS multi-motor synchronisation

**Status:** In development (Provisional), 2026-10-15, Lenton Neale. Confirmed or dropped by the bench checks in [`BRING_UP.md`](../../Hardware/bench-wiring/BRING_UP.md) phase 10 and the motor command path design.

**Decision:** the MKS synchronisation-mark function (4AH to enable, 4BH to release; manual Part 12, pp. 95-98) is developed as part of the motor command path, so one gated command can start several joints together.

- Scope: a gated command that starts several joints together is still a single gated command. It plans no path between poses, so the charter's motion-planning non-goal is unaffected.
- Design rule (Provisional): while 4AH is enabled, a drive holds every motion command until it receives 4BH (manual p. 96). All motion therefore goes through stage, then release; a one-joint command is a batch of one.
- Prerequisites: drive firmware V1.0.8 or later on every drive (manual p. 2). The release may need resending at about 1 ms intervals (manual p. 97). The SET_MOTOR_COMMAND path (SYS-CMD-001, not yet implemented) and the motion gate (SYS-GATE-001) are designed with batches in mind; any requirement change is drafted with that design, not here.
- Open, for the bench (see [`multi-motor-synchronisation.md`](../../icm-project/references/mks-servo42d-57d-can/multi-motor-synchronisation.md) §10): how long a staged command waits, how far apart the drives start, what a stop, a disable, 4AH 00 or a heartbeat timeout does to a staged command, and what 4BH does with nothing staged.
- If the bench checks show it unsuitable, 4AH stays disabled (the factory default) and joints are commanded one at a time.

## MKS motion commands

**Status:** Decided 2026-10-14, Lenton Neale (code-review rulings R11 and R21); recorded here 2026-10-15. Not yet applied to the code: `mks_api.h` does not expose F5H or 31H, and the CAN service still polls 30H and 32H (WP11).

**Decision:** the commands below implement SYS-CMD-001 (manual pages from [`motion-commands.md`](../../icm-project/references/mks-servo42d-57d-can/motion-commands.md) and [`read-commands.md`](../../icm-project/references/mks-servo42d-57d-can/read-commands.md)).

| Purpose | MKS command | Notes |
|---|---|---|
| Move to position | F5H, absolute coordinate | Target in the 31H unit (16384 counts per motor turn), a signed 24-bit value; speed in RPM; acceleration 0 to 255 (p. 90) |
| Move at velocity | F6H, speed mode | Signed RPM |
| Controlled stop | The running command's own stop form | F5H with speed 0 and acceleration not 0 after a position move (p. 92); F6H with speed 0 after a velocity move (p. 74) |
| Fallback stop | F7H, emergency stop | Only when a controlled stop is refused or unanswered; not recommended above 1000 RPM (p. 71) |
| Position feedback | 31H, absolute coordinate | Same unit as the F5H target |
| Speed feedback | 32H | At a lower rate, or on demand |

- F5H needs a zero point set once before absolute moves: 91H (homing) or 92H (set the current position as zero) (p. 90). Whether the zero survives a drive power cycle is a bench question.
- F5H in its current form, where the target and speed can be changed while a move runs, needs drive firmware V1.0.5 or later (pp. 1, 90). Changing the target mid-move is not used in the current scope.
- RPM values are exact only at 16, 32 or 64 microsteps (p. 68), so each drive's microstep setting is recorded ([`JOINT_SHEET.md`](../../Hardware/bench-wiring/JOINT_SHEET.md)).
- F5H acknowledges a staged command in synchronised mode (status 5, p. 91), so it works with the synchronisation decision above.
- With the gear ratios in [`SYSTEM_CONFIGURATION.md`](../06_CONFIGURATION/SYSTEM_CONFIGURATION.md) §2.2, every joint's travel stays inside the signed 24-bit target range.

## MKS drive settings

**Status:** Decided 2026-10-15, Lenton Neale. The En-pin mode and the microstep value are Provisional until the `BRING_UP.md` phase 6 checks below pass. No drive has been set yet; each drive's as-found value is recorded first ([`JOINT_SHEET.md`](../../Hardware/bench-wiring/JOINT_SHEET.md)).

**Decision:** every drive is set as follows (commands from the MKS SERVO42D/57D CAN manual V1.0.9; [`config-commands.md`](../../icm-project/references/mks-servo42d-57d-can/config-commands.md), [`frame-and-checksum.md`](../../icm-project/references/mks-servo42d-57d-can/frame-and-checksum.md), [`motion-commands.md`](../../icm-project/references/mks-servo42d-57d-can/motion-commands.md)).

| Setting | Value | Why |
|---|---|---|
| Response mode (8CH) | Respond on, active on (XX = 01, YY = 01: the factory default) | The controlled stop is complete on the drive's "stop complete" reply (status 2), with a timeout as fallback (ruling R21b). A move's start and finish replies are also how the host sees the command was taken. Only this mode sends them (p. 41). |
| Power-on auto-run (FFH) | Off (enable = CA) | A drive must never move just because it was powered (ruling R25a; SAFE behaviour on power-up, ruling R23). |
| En-pin mode (85H) | Hold (Level = 02: always enabled), **Provisional** | On the 42D drives the En input carries a limit or home switch through 9EH port mapping. An En mode of L or H could then disable the drive whenever a switch is pressed. Enable and disable are bus commands instead (F3H), so the stop-and-hold rule (R21d) and an operator DISABLE stay in firmware control. Same setting on the 57D drives for one rule on every drive. |
| Microstep (84H) | 64, **Provisional** | MKS calibrates the RPM speed values at 16, 32 and 64 microsteps (p. 68). At any other setting every commanded speed is scaled, and at the highest setting the motor runs at a sixteenth of the commanded RPM. 64 is the finest of the calibrated settings. Position targets use the 31H coordinate unit, which does not depend on the microstep (see "MKS motion commands"). |

**Who sets and who checks (decided 2026-10-15, Lenton Neale):** the firmware does not write drive settings. At CAN activation it reads each drive's settings and withholds that motor's `motor_ready` on a mismatch, reported through a health reason code. The settings are written once per drive by a Pi-side commissioning tool during `BRING_UP.md` phase 6 and the as-set values are recorded in `SYSTEM_CONFIGURATION.md` §2.2. Rejected: setting them from firmware at every boot, which writes the drives' EEPROM on each power cycle and would push a wrong value to all six drives at once.

Confirmation (bench, phase 6, one drive at a time, motor uncoupled):
- **En-pin mode:** with Hold set, pressing the axis's switch does not disable the drive, F3H disable does disable it, and the switch still reports through 9EH. If Hold also blocks F3H, this decision is revised before any gated motion.
- **Microstep:** a commanded F6H speed gives that RPM at the shaft, within what the bench can observe.

The firmware does not set these yet. Setting them at CAN activation, or checking them by a read at activation, is decided with the motor command path (WP11, WP14).

## Clock synchronization (Issue #12)

**Status:** DECIDED (2026-09-24). This is a living decision record, and some parameters are open.

Full record: [`ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`](ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md). It modifies SD-03, SD-19, SD-21 and SD-22 and adds SYS-SYNC-006. In summary:
- the STM32 performs no clock math;
- every SPI exchange is a clock-sync observation for the Pi-side ClockSync model;
- STM32 link liveness (`link_stale`) and ClockSync validity are independent;
- Pi link loss is detected by a count-based check with an interim 500 ms limit.

Open: `N_moving`/`N_idle`, the expected-message-interval source, the motion-state input, counter-extension-gap recovery, and the DIAGNOSTIC v2 field layout. All five were answered on 2026-10-14 (rulings R14, R16 and R22 in the next section).

## Code-review rulings (2026-10-14)

**Status:** Decided 2026-10-14, Lenton Neale, answering the 29 questions of the 2026-10-14 full code review (R1 to R29); recorded here 2026-10-15. None is applied to the code or the interface documents yet. Each is implemented by the work-package story named in the last column (`icm-project/backlog.json`). The motion-command choices of R11 and R21 are in "MKS motion commands" above. The question-and-answer record itself is kept with the Portal run data, outside this repository.

Where a ruling creates a value, the value is a new Provisional row in [`PARAMETER_REGISTER.md`](../06_CONFIGURATION/PARAMETER_REGISTER.md), added by story B101. Wire changes follow the lockstep rule: C, Python and the shared golden vectors change in one commit.

| Ruling | Decision | Story |
|---|---|---|
| R1 | Every GET request payload is the schema version followed by three reserved zero bytes. Any other length is NACKed BAD_LENGTH; another schema or non-zero reserved bytes, BAD_MESSAGE. | B70 |
| R2 | PRM-SPI-03 becomes the STM32 staged-frame recheck period. A new row holds the Pi polling period, the single default for the Pi library and every tool. | B101 |
| R3 | Request-seq stays monotonic. After a DIAGNOSTIC (boot or recovery) the STM32 accepts the first seq that arrives. The Pi has one process-wide sequencer and, on BAD_SEQUENCE to its first request, jumps forward once by a bounded step. | B69 |
| R4 | Bytes after the CRC are zero on transmit and ignored on receive, on both sides. | B70 |
| R5 | Snapshot flags bit 0 means an unread snapshot was replaced or dropped; the dropped count counts snapshots only. | B71 |
| R6 | AS5600 ML/MH are warnings, not invalidity; only MD clear or a bus error invalidates. `processed_angle_mdeg` is the RAW ANGLE scaled to millidegrees. PRM-ACQ-02 keeps its basis with a note that the method was not recorded, and is re-measured with a sweep counter. | B74 |
| R7 | `data_ready_analysis.py`, its tests and the dead record fields are removed. | B78 |
| R8 | SPI §7: the STM32 *shall* deassert DATA_READY when no frame is armed; the "exercised on target" sentence is withdrawn until a record exists. | B67, B122 |
| R9 | CAN runs at 1 Mbit/s (PRM-CAN-01, timing PRM-CAN-03) on every drive. Lenton reads each drive's CAN ID, model, firmware, work mode and response mode before CAN commissioning. The earlier X/Y/Z movements came from an earlier firmware build. An ID above 0xFF is commissioned only after its checksum rule is confirmed on a drive. | B79 |
| R10 | The snapshot motor record carries the raw 31H reply bytes, decoded on the Pi; speed and acknowledgements go to a separate field. Motor validity bits: FEEDBACK_VALID, CONTROLLER_STATUS_VALID, reserved, STALE, FAULT. | B83, B88 |
| R11 | Position feedback is polled with 31H every feedback period (new row); PRM-MOT-01 becomes Derived from it. | B84 |
| R12 | After bus-off escalates to ERROR, automatic recovery stops until the system-activate message (R19). Recovery is judged by the bus-off flag, not the HAL return. While inhibited, a safety frame is rejected with an error, never queued. The escalation window (PRM-CAN-08) is sliding. Bus-off inhibits the whole arm; one motor's FAULT clears only that motor's `motor_ready`. | B85 |
| R13 | bxCAN automatic retransmission is enabled; PRM-CAN-06 covers a full mailbox only; TX counters are added. | B86, B87 |
| R14 | Message 0x03 becomes DIAGNOSTIC v1 (lifecycle state, counters, cause), sent at boot and after recovery. GET_DIAGNOSTIC is 0x15, in Stage 2. Until v1 exists, an SWD read of the health snapshot is acceptable Stage 2 evidence. ClockSync fields stay in a Pi-side record. | B89 |
| R15 | Sensor acquisition moves to its own lower-priority task, with the latest-value stores protected. | B81 |
| R16 | Issue #12 details: T2, the STM32 receipt instant, is the end of the transfer that carried the request (corrected from "T4" on 2026-10-15, Lenton Neale: `TIME_SYSTEM_INTERFACE.md` §3 defines T4 as the Pi's receipt of the response); `request_received_local_us` is appended to ACK, VERSION and SNAPSHOT (schema version 2), never to NACK; the Pi uses one raw monotonic clock; a backwards STM32 time means a reset. The sync-quality validity bits are retired. The legacy drift check and the two as-built TIME_SYNC documents are retired with TIME_SYNC. Sensor skew is judged against PRM-ACQ-02. | B92 to B98, B101 |
| R17 | Bench instruments: a USB-CAN adapter or CAN analyser, a logic analyser or oscilloscope, a way to cut the SPI link and a way to force bus-off. The working SPI clock is a new row; the Pi DATA_READY wait is PRM-SPI-04. DATA_READY is PA8 on the STM32 and GPIO25 on the Pi; only its electrical check remains. | B101 to B103 |
| R18 | SET_MOTOR_COMMAND NACK detail: 0 ALLOWED, 1 LIFECYCLE_NOT_ACTIVE, 2 CAN_NOT_ACTIVE, 3 LINK_STALE, 4 GLOBAL_MOTION_INHIBIT, 5 MOTOR_NOT_READY, 6 CAN_QUEUE_FULL, in that precedence, with a latched flag in the upper byte. | B106, B108 |
| R19 | A system motion lifecycle starts INACTIVE after every reset while the sensing services keep auto-activating. A new system-activate SPI message (value proposed 0x16) activates the services in dependency order, then the motion lifecycle; ENABLE then enables one motor only. After `link_stale` clears, each motor needs a new ENABLE. | B111 |
| R20 | `motor_ready` = registered, an ENABLE accepted since the last disable or reset, and no MKS fault. `global_motion_inhibit` is set by bus-off escalation or a host command, latches, and is cleared only by system-activate. | B106, B111 |
| R21 | Controlled stop is the running command's own stop form; F7H is the fallback. The stop completes on the drive's reply or a Provisional timeout. **The link-loss sequence ends stopped and enabled (shaft held), not disabled**; this changes SAFE-02, SYS-LINK-002 and SYS-GATE-001 and takes effect only when WP17 amends them. Gated-move speed, acceleration and a bench speed ceiling are new rows. | B110, B126 |
| R22 | `N_moving` and `N_idle` get Provisional values (PRM-LINK-02); the expected-message interval is a fixed STM32 constant (new row). "Moving" means the drive reports non-zero speed, and unknown speed counts as moving. `link_stale` is true from reset until the first valid SPI message. | B107 |
| R23 | At boot and on every CAN activation the firmware sends the controlled stop to every registered motor before polling. The MKS 98H heartbeat is configured on every drive as the backstop for an STM32 hang (new row). | B110 |
| R24 | The IWDG is enabled through CubeMX (new row) and refreshed only when every task has run. The reset cause is latched at boot into the health snapshot and DIAGNOSTIC v1. | B113 |
| R25 | FFH power-on auto-run and the 85H En-pin mode are read on every drive and recorded in [`SYSTEM_CONFIGURATION.md`](../06_CONFIGURATION/SYSTEM_CONFIGURATION.md) §2.1 before the arm first runs this firmware. No E-stop is fitted yet; it is fitted before Stage 4, and SAFE-01 cannot be evidenced until then. | B79, B127 |
| R26 | Before the first gated motion on X, Y, Z: SAFE-01, SAFE-02 and the gate evidence. Calibration (SYS-CAL-001) is deferred after Stage 4 to its own package; gated motion uses raw shaft angles until then. | B114, B115 |
| R27 | Health YELLOW means a fault since boot not yet cleared; only system-activate clears it. | B112 |
| R28 | CubeMX stays the configuration tool. Evidence firmware is built by the CLI preset with the system `arm-none-eabi-gcc`, pinned in CI, and the compiler version joins the build identity. A dirty Pi tree disqualifies an evidence record. Stage 2 records show positions at rest and turned by hand; "follows commanded motion" is evidenced in Stage 4. | B52, B57, B60 |
| R29 | Matrix rows with passing component tests move to component evidence. WP2 is reopened at Verification. `CHARTER_ALIGNMENT_PLAN.md` stays as a dated record. Module headers are the component documentation. Retired IDs in the safety requirements are replaced in the WP17 change. The Numbers rule gains commissioning-table facts and cited vendor references. PRM-CAN-02 is corrected to the as-built rate. | B117, B120, B121, B123, B124, B126 |

## Documentation conflicts resolved during the 2026-09 refactor

- **C-1:** DATA_READY armed-then-assert is authoritative.
- **C-3:** 512 bytes is the fixed transaction length and 490 bytes the maximum payload.

Both are from the former `05_REFACTORING_LEDGER.md` (see git history).

## Charter qualifications of approved decisions (2026-10-03)

- **SD-01:** the EKF clause is withdrawn; rates are PRM values ([`PARAMETER_REGISTER.md`](../06_CONFIGURATION/PARAMETER_REGISTER.md)).
- **SD-09:** the Pi owns measurement history; the estimator wording is dropped.
- **SD-20:** scope resolved as in the motion-gate decision above.
- **SD-25:** kept; no PL/SIL rating is claimed.
- **SD-26:** deferred until the hardware exists.

## Sign-off

Documentation aligned with charter, 2026-10-04 — Lenton Neale.

Accepted exceptions (`CHARTER_ALIGNMENT_PLAN.md` §14):

- **3.4:** the `GET_DIAGNOSTIC` message value stays open and is scoped to a later stage. Closed 2026-10-14 by ruling R14: 0x15, Stage 2.
- **3.5:** the GitHub changes are held for a later run.
- **3.7:** provenance lines that `doc_check` allows are accepted.
- **3.8:** issue numbers are cited once the issues exist.

Decisions applied from `CHARTER_ALIGNMENT_PLAN.md` §6 as recommended, each confirmed at sign-off:

| ID | Decision | Applied in | Confirmed |
|---|---|---|---|
| D-1 | Plan location; Portal default methodology agile | `00_INDEX.md`, `portal.toml` | 2026-10-04 |
| D-2 | Keep the Issue #12 clock-sync design as the target | `TIME_SYSTEM_INTERFACE.md`, `SYSTEM_SYNCHRONIZATION.md` | 2026-10-04 |
| D-3 | Motion gate SYS-GATE-001 (above) | this file, `SYSTEM_REQUIREMENTS.md` | 2026-10-04 |
| D-4 | Safety behaviours SAFE-01..05; PL/SIL gates withdrawn | `04_SAFETY/SAFETY_REQUIREMENTS.md` | 2026-10-04 |
| D-5 | Research notes moved to `icm-project/` | git renames 2026-10-03 | 2026-10-04 |
| D-6 | Governance collapsed into the index and `DOCUMENTATION_RULES.md` | `00_INDEX.md`, `DOCUMENTATION_RULES.md` | 2026-10-04 |
| D-7 | `SYS-<AREA>-<nnn>` kept; old IDs retired, not renumbered | `SYSTEM_REQUIREMENTS.md` retired table | 2026-10-04 |
| D-8 | SD charter annotations (SD-01, 09, 20, 25, 26) | above; register §1 | 2026-10-04 |
| D-9 | Evidence record format | `05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md` | 2026-10-04 |
| D-10 | NOT_FITTED as validity bit 6; status byte stays the raw AS5600 register | `SPI_PAYLOAD_SCHEMA.md` | 2026-10-04 |
| D-11 | Milestones are Stages 1–5 | register §3; held GitHub script | 2026-10-04 |

Also decided 2026-10-03 (Lenton Neale): the baseline keeps 17 requirement rows; PRM-CAN-07 adopts the code's doubling sequence; PRM-ACQ-01 is a 20 Hz working value bounded by the measured sweep.
