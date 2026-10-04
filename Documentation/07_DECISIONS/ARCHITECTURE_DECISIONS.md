# Architecture Decisions

This is the live decision log for architecture-level decisions. The full decision list is in the **[Karetao Decisions, Questions, and Issues Register](KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md)** (Architecture Decisions section).

## Motion gate (SYS-GATE-001)

**Status:** Decided 2026-10-03, Lenton Neale (applied per CHARTER_ALIGNMENT_PLAN.md D-3; confirmed at sign-off 2026-10-04).

**Decision:** `MOTION_PERMITTED = lifecycle ACTIVE ∧ CAN ACTIVE ∧ ¬link_stale ∧ ¬global_motion_inhibit ∧ motor_ready`.

- ClockSync validity, required-sensor validity, calibration validity and motor-feedback freshness are not gate inputs for single gated commands. They remain diagnostics and may be added by a later decision.
- Single gated commands are not time-dependent motion. This resolves the SD-20 scope question: no time-dependent motion exists in the current scope.
- The proposed SYS-MOTION-001..003 are replaced by SYS-GATE-001 ([`SYSTEM_REQUIREMENTS.md`](../01_SYSTEM/SYSTEM_REQUIREMENTS.md)).
- `motion_permission.c` today evaluates a superset (heartbeat, time sync, sensors, calibration, feedback). Simplifying it to this set is a code issue ([LIVE-20]).

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
