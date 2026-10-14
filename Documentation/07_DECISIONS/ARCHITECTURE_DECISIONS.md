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

## Clock synchronization (Issue #12)

**Status:** DECIDED (2026-09-24). This is a living decision record, and some parameters are open.

Full record: [`ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`](ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md). It modifies SD-03, SD-19, SD-21 and SD-22 and adds SYS-SYNC-006. In summary:
- the STM32 performs no clock math;
- every SPI exchange is a clock-sync observation for the Pi-side ClockSync model;
- STM32 link liveness (`link_stale`) and ClockSync validity are independent;
- Pi link loss is detected by a count-based check with an interim 500 ms limit.

Open: `N_moving`/`N_idle`, the expected-message-interval source, the motion-state input, counter-extension-gap recovery, and the DIAGNOSTIC v2 field layout.

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

- **3.4:** the `GET_DIAGNOSTIC` message value stays open and is scoped to a later stage.
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
