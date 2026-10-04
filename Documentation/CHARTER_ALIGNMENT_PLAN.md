# Charter alignment plan

Status: Done 2026-10-04 (sign-off S6.5, Lenton Neale; recorded in 07_DECISIONS/ARCHITECTURE_DECISIONS.md). Sprint S7 (sign-off readiness) runs in the ICM Portal; sprints 0 to 6 were drafted outside the Portal on `docs/charter-alignment` (Sprints 0–6, documentation stories); sign-off S6.5 done 2026-10-04. Decisions D-1..D-11 were applied as recommended and were confirmed at sign-off 2026-10-04. GitHub changes (S2.5, S3.5, S4.5, S5.4, S5.6) are drafted in a held script, not executed. Decisions after execution (2026-10-03): keep 17 requirement rows; PRM-CAN-07 adopts the code's doubling sequence; PRM-ACQ-01 demoted to a 20 Hz working value bounded by the measured sweep. provenance lines in individual documents still name `docs/project` and are allowed by the check tool as provenance.
Owner: Lenton Neale (decides); drafted for the Documentation run
Role: Governance/process document. It defines no requirement and has no authority over any system document. It is the input for the documentation pruning run the charter announces, and it is executed as ICM Portal runs; nothing here is done by editing `main` directly.
Charter: [`01_SYSTEM/PROJECT_CHARTER.md`](01_SYSTEM/PROJECT_CHARTER.md) (Agreed 2026-10-03)
Index: not yet linked from `00_INDEX.md`; story S0.1 adds the link. No other file was changed to create this plan.

## 1. Purpose

Bring every document in the repository into line with the charter, so that the documentation can be used as the specification for refactoring the code. The work is done when §3 holds and Lenton has signed it off.

The method is features, not files. Each sprint takes one charter goal and aligns its whole trail: requirement → interface → configuration and parameters → verification row → GitHub issue. Pruning of material that no longer fits the charter rides along in bounded slices. The horizontal clean-up (documentation about documentation, the decisions register, the issue tracker) comes last, once the content it indexes has settled. Sprint 0 is deliberately tiny so the agile flow in the Portal is tried on something small first.

## 2. Starting point (2026-10-03)

### 2.1 Size

| Area | Now |
|---|---|
| `Documentation/**` | 43 files, 6,555 lines |
| of which documentation about documentation (index, authority model, component model, refactoring rules/plan/ledger, checklist) | 7 files, 1,812 lines |
| of which the decisions register | 849 lines |
| of which research notes (distributed motion control, MKS sync marks) | 917 lines |
| Component docs | Arm Sensor Hub 9 files, 1,221 lines; Raspberry Pi 2 files, 1,092 lines |
| System requirements | 30 `SYS-*` baseline rows + 3 proposed `SYS-MOTION-*` |
| Safety gates | `SAFE-001`..`010`: nine OPEN/BLOCKED PL/SIL-style release gates + one proposed |
| Decisions | SD-01..SD-25 approved or modified, SD-26 proposed; Issue #12 clock-sync record (decided 2026-09-24) |
| Work tracking | 35 open GitHub issues, 7 milestones (M7 empty); `For_Lenton` review list (529 lines) |
| Code | firmware `App/` 20 modules, 4,283 lines of C; Pi 5,821 lines of Python (src, tests, tools); 2 host-test executables; 2 CI workflows |
| Measured values | one: the six-axis encoder sweep, ≈46 ms (2026-09-17) |

### 2.2 What the charter contradicts

Term scan over `Documentation/**`, component docs and the root files (see Appendix B for the command):

| Charter position | Where the documents still say otherwise |
|---|---|
| No 500 Hz EKF, no high-rate estimator | EKF named in 14 `Documentation/` files (40 times in the register); 500 Hz in 8; `estimator` in overview, architecture, timing, HOST, TIME, RASPBERRY_SENSOR_HUB, Pi README; GitHub #12, #32–#36 are EKF design issues; label `estimation` |
| No ROS 2 for now | overview, architecture, lifecycle ("inspired by", harmless), root README first line, Pi `Documentation/README.md` claims ROS 2 node authority, Pi bring-up guide Part D installs ROS 2 Jazzy (35 mentions) |
| No PL or SIL claim | `SAFETY_REQUIREMENTS` SAFE-001/008/009, `SAFETY_ARCHITECTURE`, register §4 release conditions, GitHub #46, #14, #50 |
| No differential end effector until hardware exists | SYS-MECH-001, SD-26, config §2 limitation note, matrix and gates rows, GitHub #11, #15 (MoveIt 2) |
| No Pi-side planning | `DISTRIBUTED_MKS_MOTION_CONTROL_RESEARCH` (500 Hz time-triggered control), `MKS_SERVO42D_57D_SYNCHRONISATION` §9 proposed control architecture |
| Lenton Neale decides | "CTO" ×11 and "system decision authority" in the register, index, requirements, `ARCHITECTURE_DECISIONS`, `TIME_SYNC_INSTRUMENTATION` |
| No numeric requirement without a basis | about 17 numbers sit inside `SYS-*` rows; the same numbers are repeated in timing, sync, configuration and four interface docs; none carries a basis |
| Milestones are stages, not dates | M1–M7 are named after the old timing/EKF/safety programme |

### 2.3 What already fits

The SPI framing contract, payload schema, lifecycle vocabulary, CAN bus-off policy, calibration and joint-mapping models, the Issue #12 clock-sync decisions, the component authority split, the issue contract and the `icm-project/references/` vendor material are sound and are kept. They lose numbers, EKF consumers and "release gate" language; they do not change shape.

### 2.4 Known code-versus-document divergences

These are not documentation work. They become the code-alignment backlog (§11) that this plan hands over:

- Clock sync: code still runs one-way `TIME_SYNC` with an STM32-held offset; `request_received_local_us` is in no source file; Issue #12 is the documented target.
- `DIAGNOSTIC` (0x03) is defined on the wire but not implemented.
- `SET_MOTOR_COMMAND` (0x13) is "not frozen" in the schema and absent from both code bases.
- CAN runs at 875 kbps as generated; the documents say 1 Mbps.
- One motor (CAN 0x001) and one mapping record are commissioned; the charter wants six motor positions.
- Sensor records have no "not fitted" state; an unfitted axis today reads as a communication error.
- `motion_permission.c` implements the gate the documents still call "proposed".

## 3. Definition of done

The documentation is aligned and ready for code work when all of the following hold on `main`:

1. **Scope.** The term scan (Appendix B) finds EKF, ROS 2, MoveIt, PL/SIL, "CTO", "system decision authority", differential end effector and trajectory planning only in the allowed contexts: the charter's non-goals, the overview's "Future, not now" note, provenance lines, dated as-built evidence headers, and the register's "Charter" column.
2. **Numbers.** Every number in a normative document is either a contract constant in an interface document (magic, header size, CRC, frame size, record sizes, message IDs) or a `PRM-*` entry in the parameter register with a basis of Measured, Datasheet, Derived or Provisional. `SYSTEM_REQUIREMENTS.md` contains no numbers.
3. **Requirements.** The `SYS-*` baseline has about fifteen to twenty rows (17 accepted 2026-10-03), each derived from a charter goal, each with an observable acceptance criterion, and each with a row in the verification matrix naming its code module, its test (or "none yet, issue #n") and the evidence required. Every retired identifier is listed with its successor or reason.
4. **Interfaces.** No interface document contains "TBD", "not frozen" or "proposed" for anything Stages 1 to 4 need (NOT_FITTED status, six motor records, clock-sync extension, `SET_MOTOR_COMMAND`, ACK/NACK semantics). Anything still open is explicitly scoped to a later stage.
5. **Trail.** Every live item in the register §0 maps to exactly one open GitHub issue; milestones are stages; every open issue cites a `SYS-*` row or a stage; closed-as-not-planned issues cite the charter non-goal.
6. **Size.** Documentation about documentation ≤ 250 lines in total; the register ≤ 150 lines; no section README stubs; `For_Lenton` retired.
7. **Links.** Every relative link in the three documentation trees resolves; `docs/project` and `99_ARCHIVE` appear only in one provenance line in the index.
8. **Lockstep.** Every wire-format change made in a document has a GitHub issue for the C side, the Python side and their tests, and the document says "not yet implemented (issue #n)" until it is.
9. **Sign-off.** Lenton has walked this list and recorded "Documentation aligned with charter, <date>" in `07_DECISIONS/ARCHITECTURE_DECISIONS.md`.

## 4. Ground rules

- The charter is the scope authority; `SYSTEM_REQUIREMENTS.md` keeps requirement authority; the register keeps the parameters. Nothing is copied between them, only referenced.
- Approved decisions SD-01..SD-25 keep their status (charter, "Who decides"). Where the charter contradicts one, the register's SD table gets a "Charter 2026-10-03" annotation (qualified, deferred, withdrawn clause); the decision text is not rewritten.
- "Provisional" is the word for an unconfirmed value. "Guess", "assumed" and "estimate" are not used.
- A newer statement wins over an older one, per statement (`git blame`), unless the newer one is still proposed; then the approved statement stands and Lenton is asked.
- Caveats travel with the text they qualify. When a document is shortened, the caveat ("not hardware approval", "no rating claimed", "theoretical floor, not a measurement") is kept verbatim and the words around it are cut.
- Deletion follows `05_REFACTORING_RULES.md` (git history, unique content, inbound links) until Sprint 6 folds that rule into `DOCUMENTATION_RULES.md`. Git history is the archive; nothing is moved to an archive folder.
- No code is changed in these runs. A documentation change that implies a code change creates the issue in the same run.
- Values the drafter cannot know (which axes have encoders, joint names, MKS model and firmware, what E-stop hardware exists) are asked for in the sprint's Design stage and recorded as "unknown" until answered; they are never invented.

## 5. Working method: agile in the ICM Portal

- Methodology: the Portal's `agile.toml` (tabs Backlog, Sprint plan, Design, Build, Retro). Set `[methodology] default = "agile"` in `portal.toml`, or pick agile in the picker when the run is created. Stories live in `backlog.json`; Sprint 0 loads the stories below as B5 onward.
- A sprint is one Portal run, one branch (`portal/<date>-<sprint-slug>`), one merge into `main`. Sprints are scoped by stories, not by dates (charter: no calendar commitments); a sprint ends at its Retro.
- The Design stage is where Lenton accepts, changes or rejects each decision in §6 and the proposed text of each story. The Build stage writes in a worktree; Verify runs the same commands as CI (documentation-only runs still pass them); the pre-merge review is read-only.
- Story definition of done: acceptance criteria met; links in touched files resolve; the term scan is clean for touched files; provenance or supersession recorded where text was removed; the register §0 and the GitHub issue updated in the same run when a story closes or opens a live item.
- Sprint size is capped at about 20 points so one review sitting covers the diff. Lenton's review time is the constraint, not writing time.
- Order is re-planned at each Sprint plan. Fixed dependencies: Sprint 0 first; Sprint 1 before Sprints 2–4; Sprints 5 and 6 after 2–4.
- Fallback: if the agile flow is awkward in the Portal, a sprint can run as a waterfall run with the same story list; the sprint boundaries do not change.
- Tracking: this work is work package WP1 in `lifecycle.json`; the PASS at its Requirements gate is the sign-off step of §3.9.

## 6. Decisions required from Lenton

Each is taken in the Design stage of the sprint named. A recommendation is given so the default is clear; the decision is Lenton's.

| ID | Decision | Recommendation | Sprint |
|---|---|---|---|
| D-1 | Where this plan lives and how the Portal runs it | `Documentation/CHARTER_ALIGNMENT_PLAN.md`, listed under "Framework governance" in the index; Portal default methodology `agile` | S0 |
| D-2 | Clock-sync target design | Keep the Issue #12 design (STM32 does no clock math; Pi-side ClockSync). It is decided and simpler on the STM32. Move its numeric targets (±1 ms, 5 s, 500 ms) to the register as Provisional; keep the as-built TIME_SYNC evidence as dated evidence until the code catches up | S3 |
| D-3 | The motion gate for Goal 4 | Approve a reduced, normative gate: lifecycle ACTIVE ∧ CAN ACTIVE ∧ ¬`link_stale` ∧ ¬global inhibit ∧ motor ready. Single gated commands are not "time-dependent motion", so ClockSync validity is not a gate input in this scope; this resolves the SD-20 scope question. `SYS-MOTION-001..003` are replaced by one approved `SYS-GATE-001`. `motion_permission.c` evaluates a superset today; simplifying it is a code issue | S4 |
| D-4 | Safety behaviours for attended operation | Replace the PL/SIL release gates with a short behaviours table: operator-reachable power cut or E-stop (hardware, tested by hand); link loss → stop then disable; CAN bus-off → inhibit; reset or recovery never resumes motion; faults visible to the operator. SAFE-001, 008, 009 are withdrawn as non-goals. One safety document instead of three | S4 |
| D-5 | Research notes | Move `DISTRIBUTED_MKS_MOTION_CONTROL_RESEARCH.md` to `icm-project/research/` and `MKS_SERVO42D_57D_SYNCHRONISATION.md` to `icm-project/references/mks-servo42d-57d-can/` (it summarises the vendor manual). Both leave `Documentation/` | S6 |
| D-6 | Documentation about documentation | Collapse index + authority model + component model + refactoring rules into `00_INDEX.md` (≤ 100 lines) and `DOCUMENTATION_RULES.md` (≤ 80 lines); remove the finished plan, ledger and checklist and the seven 7-line section READMEs | S6 |
| D-7 | Requirement identifiers | Keep the `SYS-<AREA>-<nnn>` scheme with new areas (ENC, MOT, TS, LINK, GATE, CMD); retire old IDs in a table rather than renumber; `LIVE-xx` continues from LIVE-17 | S2 |
| D-8 | SD annotations | SD-01 EKF clause withdrawn; SD-09 reworded without the estimator; SD-25 kept with "no rating claimed"; SD-26 deferred until hardware exists; all other SDs unchanged | S5 |
| D-9 | Evidence record format | One 30-line format: date, firmware identity from the `VERSION` message (hash, dirty flag), hardware or rig, procedure, result, accepted by. Dirty-build evidence never satisfies a matrix row | S2 |
| D-10 | NOT_FITTED on the wire | Define the sensor record `status` enumeration (undefined in the schema today) with a NOT_FITTED value and set validity bit 6 "not fitted". Additive within schema v1 since the bit is reserved today; the schema version stays 1 and the change is dated | S2 |
| D-11 | Stage names for milestones | Stage 1 Fitted encoders; Stage 2 Motor positions and timestamps; Stage 3 Links measured; Stage 4 Gated motion X/Y/Z; Stage 5 Remaining joints. M1–M7 are renamed or closed, not deleted | S5 |

## 7. Sprint plan

Points are relative size (1, 2, 3, 5). "Touches" lists the files a story edits; anything not listed is out of scope for that story.

### Sprint 0 — Wire the charter in (≈ 7 points)

Goal: the charter is reachable from every entry point, the decision authority is named, and the overview no longer contradicts it. Small on purpose: the first agile run in the Portal.

| ID | Story | Acceptance | Touches | Pts |
|---|---|---|---|---|
| S0.1 | Entry points link the charter and this plan | `00_INDEX.md` lists this plan under "Framework governance" and keeps the charter as "start here"; `01_SYSTEM/README.md` lists the charter; root `README.md` first line no longer says "ROS 2 components" and names the charter; `CLAUDE.md` gains one line: the charter is the scope authority and "Provisional" is the word for unconfirmed values. All links resolve | `00_INDEX.md`, `01_SYSTEM/README.md`, `README.md`, `CLAUDE.md` | 2 |
| S0.2 | Who decides | Live text replaces "CTO" and "the system decision authority" with "Lenton Neale"; quoted provenance (`CTO_DECISION_FINAL.md`, "2026-09-07 CTO approval") stays and the register gets one note: "CTO in provenance means Lenton Neale (charter)". Scan shows the terms only in the charter and that note | `00_INDEX.md`, `SYSTEM_REQUIREMENTS.md`, `ARCHITECTURE_DECISIONS.md`, register §0–§1, `TIME_SYNC_INSTRUMENTATION.md` | 2 |
| S0.3 | System overview at charter scope | ≤ 50 lines: purpose from the charter; the three parts (STM32 hub, MKS servos on CAN, Pi host); interfaces named without numbers; "Current status" lists what exists in code today (SPI framing both sides, DMA path, encoder sweep, CAN polling scaffold, calibration and mapping models) and what does not (clock-sync redesign, DIAGNOSTIC, motor commands); a "Future, not now" note names ROS 2, a state estimator, the differential end effector and planning. The charter's "Related documents" line about the overview is updated | `SYSTEM_OVERVIEW.md`, `PROJECT_CHARTER.md` | 2 |
| S0.4 | Portal set-up | `portal.toml` methodology default `agile`; stories S1–S6 loaded into `backlog.json` as B5 onward with their points; the requester profile cites this plan | `portal.toml`, `backlog.json`, `icm-project/requester-profile.md` | 1 |

### Sprint 1 — Parameter register (Goal 3 foundation, ≈ 13 points)

Goal: every number has one home and a basis; requirements stop carrying numbers.

| ID | Story | Acceptance | Touches | Pts |
|---|---|---|---|---|
| S1.1 | Create the parameter register | `06_CONFIGURATION/PARAMETER_REGISTER.md` with columns ID (`PRM-<AREA>-<nn>`), parameter, working value, unit, basis (Measured / Datasheet / Derived / Provisional), source or evidence (document, datasheet section, measurement record, or "none yet"), date, used by (requirement IDs, code symbol and file). A rules block states: Provisional is a working value and never a requirement; a basis changes only with linked evidence; contract constants are not parameters. Seeded from Appendix A. Only one row is Measured (the 46 ms sweep) unless new evidence is linked. The CAN rows show both the 1 Mbps Provisional target and the 875 kbps as-generated Derived value | new file | 5 |
| S1.2 | Numbers out of the requirements | Every number in `SYSTEM_REQUIREMENTS.md` is replaced by a `PRM-*` reference ("within PRM-LINK-01"). `SYSTEM_TIMING.md` is removed after the inbound-link check: its numbers are in the register and its one rule (acquisition timestamps are retained) moves into the requirements. `SYSTEM_SYNCHRONIZATION.md` keeps its rules and references `PRM-TS-*`. `grep -E '[0-9]+ ?(Hz|MHz|Mbps|kbps|ms|µs|us|cm|s\b)' SYSTEM_REQUIREMENTS.md` matches nothing | `SYSTEM_REQUIREMENTS.md`, `SYSTEM_TIMING.md` (removed), `SYSTEM_SYNCHRONIZATION.md`, `00_INDEX.md` | 3 |
| S1.3 | Configuration and interfaces reference the register | `SYSTEM_CONFIGURATION.md` §1 and §6 become a pointer to the register; the SPI, CAN, TIME and HOST interface documents replace each tunable number with its `PRM` ID and keep contract constants. Each number appears once | `SYSTEM_CONFIGURATION.md`, four interface docs | 3 |
| S1.4 | Firmware defaults recorded | Register rows for the firmware defaults (sensor poll period, CAN poll period, host-stall timeout, TX retry limit, `counter_extension_gap_us`, legacy drift bounds) name the symbol and file, verified against the source at build time, so the code backlog can centralise them later. Documentation only | `PARAMETER_REGISTER.md` | 2 |

### Sprint 2 — Goal 1: every fitted encoder (≈ 13 points)

Goal: the full trail for reading fitted encoders exists and an unfitted axis is a state, not a fault.

| ID | Story | Acceptance | Touches | Pts |
|---|---|---|---|---|
| S2.1 | Encoder requirements | `SYS-ENC-001`: the hub reads every encoder recorded as fitted in the commissioning table and publishes each reading with its acquisition timestamp and validity. `SYS-ENC-002`: an axis recorded as not fitted is published as NOT_FITTED, is not a fault, and inhibits nothing. `SYS-ENC-003`: the commissioning table is the only statement of which axes have an encoder and is versioned (absorbs SYS-MAP-001's sensor half). Each row has an acceptance criterion observable on the bench and no numbers. `SYS-STATE-001` is folded in where it overlaps | `SYSTEM_REQUIREMENTS.md` | 3 |
| S2.2 | NOT_FITTED on the wire | Per D-10: `SPI_PAYLOAD_SCHEMA.md` defines the sensor `status` enumeration including NOT_FITTED and validity bit 6; `SPI_SYSTEM_INTERFACE.md` §8 says six records always, unfitted axes carry NOT_FITTED. The C/Python divergence is recorded as one issue (both sides and tests); the schema says "not yet implemented (issue #n)" | `SPI_PAYLOAD_SCHEMA.md`, `SPI_SYSTEM_INTERFACE.md` | 3 |
| S2.3 | Commissioning table | `SYSTEM_CONFIGURATION.md` §2 holds the as-built table from `app_init.c` (axes 0–5 → mux channels 2–7; motor 0 on CAN 0x001; one mapping record), dated 2026-09-17, with columns axis, joint name (X, Y, Z, …), encoder fitted, mux channel, motor index, CAN ID, MKS model and firmware, direction, ratio, basis. Unknown cells say "unknown" until Lenton fills them. The section states that the `app_init.c` tables implement this table and must match it. `ARM_SENSOR_HUB.md` drops its own copies and points here | `SYSTEM_CONFIGURATION.md`, `ARM_SENSOR_HUB.md` | 3 |
| S2.4 | Verification rows and evidence format | Matrix rows for `SYS-ENC-001/002/003` with columns requirement, code module, test, evidence required, status. `05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md` per D-9. The evidence a bench run can produce is named (per-axis reading record with `VERSION` identity) | `SYSTEM_VERIFICATION_MATRIX.md`, new file | 2 |
| S2.5 | Work tracking | Register §0 gains `LIVE-17` Fitted-encoder reading; issues `[LIVE-17] Implement NOT_FITTED sensor status (C, Python, tests)` and `[LIVE-17] Verify fitted encoders read on the bench` per the issue contract; milestone Stage 1; #48 (sensor failure response) re-scoped under LIVE-17 or closed with the reason | register, GitHub | 2 |

### Sprint 3 — Goal 2: six motor positions with coherent timestamps (≈ 18 points)

Goal: the CAN and time trails are at hobby scope and the EKF is gone from them.

| ID | Story | Acceptance | Touches | Pts |
|---|---|---|---|---|
| S3.1 | Motor and timestamp requirements | `SYS-MOT-001`: the snapshot carries the shaft position of every commissioned motor, at rest and in motion, each with acquisition timestamp and validity. `SYS-MOT-002` (ex `SYS-FAIL-003`): feedback timeout and escalation, numbers → `PRM-MOT-*`. `SYS-TS-001`: every record carries its own acquisition timestamp in STM32 local time, the Pi converts, and the skew between records in one snapshot is derivable; target skew `PRM-TS-02`. Retired: `SYS-TIM-001` (→ `PRM-ACQ-01`), `SYS-TIM-002` (EKF, withdrawn), `SYS-TIM-003` (→ `PRM-SPI-01`), `SYS-TIM-004` (→ `SYS-TS-001`) | `SYSTEM_REQUIREMENTS.md` | 3 |
| S3.2 | CAN interface trim | ≤ 150 lines. Keeps bus semantics, lifecycle gate, bus-off policy, latest-value freshness, diagnostics; numbers → `PRM-CAN-*`; §12 gates → matrix; the 875 kbps note points at `PRM-CAN-01/02`; "six commissioned motors, see the commissioning table". `CAN_INTEGRATION_EVIDENCE.md` keeps evidence and drops the requirement restatement. No "release" language | `CAN_SYSTEM_INTERFACE.md`, `CAN_INTEGRATION_EVIDENCE.md` | 3 |
| S3.3 | Time and sync alignment | Per D-2. `TIME_SYSTEM_INTERFACE.md`: EKF removed; "Gate B ±1 ms" becomes "`PRM-TS-01` target, Provisional, measured in Stage 3"; the Issue #12 model is unchanged. `SYSTEM_SYNCHRONIZATION.md`: EKF removed, gate wording deferred to D-3. `SPI_SYSTEM_INTERFACE.md` §§10–12 keep the model; the `TIME_SYNC` row stays "deprecated, still in code". `TIME_SYNC_VALIDATION.md` and `TIME_SYNC_CHARACTERISATION_EVIDENCE.md` stay as dated as-built evidence; their process sections ("Next steps", "Task 11") are cut. `ISSUE_12_*` gets one note: the EKF consumer is dropped, ClockSync remains the model | five files | 5 |
| S3.4 | Lifecycle trim | ≤ 180 lines. §3 keeps the fault levels with the one-line "firmware levels, no rating claimed"; "5 seconds" → `PRM-TS-03`; "TIME_SYNC update" wording → "accepted ClockSync observation"; the proposed-gate paragraphs point at D-3 (settled in Sprint 4) | `SYSTEM_LIFECYCLE.md` | 2 |
| S3.5 | Verification and tracking | Matrix rows `SYS-MOT-001/002`, `SYS-TS-001`. Register §0: `LIVE-18` Six motor positions, `LIVE-19` Clock-sync implementation (re-pointing #42 and #45). Milestone Stage 2. #12, #33–#36 closed as not planned citing the EKF non-goal; #32 re-titled as the Stage 3 per-axis latency measurement | matrix, register, GitHub | 3 |
| S3.6 | Architecture at charter scope | ≤ 100 lines. The ROS 2 / estimator layer is removed; "independent safety functions" becomes "safety behaviours (attended operation)"; data-flow sections stay; the decisions list drops the EKF bullet, marks the differential bullet deferred, and points the motion-authority bullet at D-3. `RASPBERRY_SENSOR_HUB.md` rewritten ≤ 25 lines: SPI master, time authority and ClockSync owner, single gated commands, evidence tools | `SYSTEM_ARCHITECTURE.md`, `RASPBERRY_SENSOR_HUB.md` | 2 |

### Sprint 4 — Goal 4: X, Y, Z gated motion and safety at hobby scope (≈ 20 points)

Goal: a Pi developer can send one gated command from the documents alone, and safety says what is designed and tested without claiming a rating.

| ID | Story | Acceptance | Touches | Pts |
|---|---|---|---|---|
| S4.1 | Motion gate decided | Per D-3, recorded in `ARCHITECTURE_DECISIONS.md` with date and name. `SYS-GATE-001` approved; `SYS-MOTION-001..003` listed as replaced. SD-20 scope recorded: no time-dependent motion in current scope; `SYS-SYNC-003` reworded accordingly. Note that `motion_permission.c` evaluates a superset and the simplification is a code issue | `ARCHITECTURE_DECISIONS.md`, `SYSTEM_REQUIREMENTS.md`, `SYSTEM_SYNCHRONIZATION.md`, `SYSTEM_LIFECYCLE.md` | 3 |
| S4.2 | Single gated command on the wire | `SET_MOTOR_COMMAND` (0x13) frozen for the single-command case: `schema_version`, `motor_index`, command (ENABLE, DISABLE, STOP, MOVE_TO_POSITION, MOVE_AT_VELOCITY), value, reserved. Gate check → ACK (accepted by the gate and queued to CAN) or NACK (reason = the gate's reason code). "ACK is not executed; completion is observed in the snapshot motor record." `SYS-CMD-001` reworded to this; acknowledgement and freshness open items closed by the definition; timeouts → `PRM`. The MKS command used per kind is named by reference to the manual in `icm-project/references/mks-servo42d-57d-can/`, not restated. Lockstep issue created | `HOST_SYSTEM_INTERFACE.md`, `SPI_PAYLOAD_SCHEMA.md`, `SYSTEM_REQUIREMENTS.md` | 5 |
| S4.3 | Safety at attended-operation scope | Per D-4. One document `SAFETY_REQUIREMENTS.md` ≤ 60 lines: the no-rating statement from the charter; a behaviours table `SAFE-01..0n` each with the requirement it relies on (`SYS-LINK-*`, `SYS-CAN-*`, `SYS-REC-*`), the evidence required and a matrix row; a "Withdrawn by the charter" list (SAFE-001, 008, 009 and the risk-assessment gate). `SAFETY_ARCHITECTURE.md` and `SAFETY_INTEGRATION.md` merged in and removed | three safety files | 5 |
| S4.4 | Verification for X, Y and Z | Matrix rows per joint: "X verified motion", "Y", "Z". Evidence: (a) the initial movement record, written by Lenton from the tests already done, dated; (b) a command passed through the gate (ACK with reason ALLOWED and motion visible in the snapshot); (c) stop on link loss observed. Rows for the other three joints marked NOT STARTED, hardware unconfirmed. `INTEGRATION_GATES.md` merged into the matrix and removed (it repeats the same rows) | matrix, `INTEGRATION_GATES.md` (removed) | 3 |
| S4.5 | Tracking | Register §0: `LIVE-20` Gated motion X/Y/Z, `LIVE-21` Attended-operation safety behaviours. Issues: implement `SET_MOTOR_COMMAND` (C, Python, tests); simplify the gate to D-3; verify X/Y/Z. Milestone Stage 4. The LIVE-01 family (#10, #17–#20, #23–#27) re-scoped into LIVE-20 or closed with the reason; #14, #31, #46, #50 re-scoped under LIVE-21 or closed for the PL/SIL parts | register, GitHub | 2 |
| S4.6 | Calibration, configuration, deferred items | `SYS-CAL-001/002` merged into one row; `SYSTEM_CONFIGURATION.md` §3 keeps the model (`calibration_record.c` exists); "release conditions" → "evidence required". `SYS-IF-001` radians rule kept. `SYS-MECH-001` and SD-26 moved to a "Deferred (charter)" table with the hardware condition | `SYSTEM_REQUIREMENTS.md`, `SYSTEM_CONFIGURATION.md` | 2 |

### Sprint 5 — Goal 5: the trail, the register, issues and milestones (≈ 15 points)

Goal: one short live register, a requirements table that is the whole baseline, a matrix that is the trail, and an issue tracker that matches.

| ID | Story | Acceptance | Touches | Pts |
|---|---|---|---|---|
| S5.1 | Register rebuilt | ≤ 150 lines. §0 live items: LIVE-17..21 plus `LIVE-22` Measure the links (Goal 3; absorbs LIVE-02 CAN and LIVE-03 SPI verification), LIVE-08 calibration evidence, LIVE-09 system verification. SD table kept with a "Charter 2026-10-03" column per D-8. §2 (145 historical questions), §3 (historical TODOs) and §5 (source-collected issues) removed with a pointer to the last commit holding them. §4 release conditions rewritten as "Before energised motion (attended)" at hobby scope. Every §0 item has exactly one GitHub issue or milestone | register | 5 |
| S5.2 | Requirements baseline final | ≤ 15 rows: ENC-001/002/003, MOT-001/002, TS-001, LINK-001 (ex FAIL-001), LINK-002 (ex FAIL-002), CAN-001 (bus-off), MAP-001 (motor half), CAL-001, IF-001, SPI-001, CMD-001, GATE-001, REC-001 (merging REC-001/002), plus a pointer to `SAFE-*`. A "Retired and deferred" table lists every old ID with its successor or reason, so code and tests that cite old IDs can be updated. Each row has an acceptance criterion and a matrix row; no numbers | `SYSTEM_REQUIREMENTS.md` | 3 |
| S5.3 | Matrix as the trail | Columns: requirement, code module, test (host or Pi test name, or bench procedure), evidence record, status (OPEN / COMPONENT_EVIDENCE / SYSTEM_VERIFIED), accepted by and date. Code and test columns filled from the repository (`sprint1_protocol_tests`, `service_smoke_tests`, the Pi `tests/spi` modules). `VERIFICATION_STRATEGY.md` ≤ 25 lines (chain and status rule). Every row has a code module and a test or "none yet (issue #n)" | matrix, `VERIFICATION_STRATEGY.md` | 3 |
| S5.4 | GitHub milestones and issues | Per D-11, M1–M7 become Stages 1–5 (rename or close, not delete). Every open issue is re-titled under a LIVE-17+ item or closed as not planned with a comment citing the charter non-goal. Labels unchanged; `ISSUE_CONTRACT.md` notes `estimation` as dormant and swaps the EKF examples. `gh issue list` count equals the register §0 issue count plus miscellaneous | GitHub, `.github/ISSUE_CONTRACT.md`, `.github/ISSUE_FRAMEWORK.md` | 2 |
| S5.5 | `For_Lenton` retired | Each item checked against register §0: unique live items moved there, the rest dropped with the reason in the commit message; file removed; `CLAUDE.md` line updated | `For_Lenton` (removed), `CLAUDE.md` | 1 |
| S5.6 | Code-alignment backlog seeded | One issue per divergence in §11, each citing its `SYS-*` row and the lockstep rule, ordered by charter goal | GitHub | 1 |

### Sprint 6 — Collapse documentation about documentation, component docs, gate (≈ 15 points)

Goal: the framework is small enough for one person; the component docs are clean; a tool keeps it that way.

| ID | Story | Acceptance | Touches | Pts |
|---|---|---|---|---|
| S6.1 | Governance collapse | Per D-6. `00_INDEX.md` ≤ 100 lines: map, one paragraph of authority per domain, status vocabulary, who decides, how to change or remove a document, one provenance line for `docs/project` and `99_ARCHIVE`. `DOCUMENTATION_RULES.md` ≤ 80 lines: authority by subject, component boundary, verification boundary, Provisional rule, lockstep rule, deletion rule, git history as archive. Removed after the deletion check: `DOCUMENTATION_AUTHORITY_MODEL.md`, `COMPONENT_DOCUMENTATION_MODEL.md`, `05_REFACTORING_RULES.md`, `05_REFACTORING_PLAN.md`, `05_REFACTORING_LEDGER.md` (its C-1 and C-3 decisions → `ARCHITECTURE_DECISIONS.md`), `06_IMPLEMENTATION_CHECKLIST.md`, and the seven section READMEs. Governance ≤ 250 lines in total | listed files | 5 |
| S6.2 | Research notes relocated | Per D-5. Both files moved out of `Documentation/`; the index paragraph about the research note removed; no inbound link broken | two files, `00_INDEX.md` | 2 |
| S6.3 | Component docs | Pi `Documentation/README.md`: ROS 2 and estimator authority lines become a "future" note. `RASPBERRY_PI_BRINGUP_V1.md`: Part D (ROS 2 workspace) and the PREEMPT_RT part marked optional or moved to an appendix; its values table cites `PRM` IDs. Arm docs: the inventory's stale references fixed (`README.md` line 46 CAN path; `I2C_SCAN_TIMING_ANALYSIS.md` lines 13 and 150 `CONTRACT_STATUS.md`; `SWD_READOUT_PROCEDURES.md` line 192 `dump_sync_data.ocd`; `TIME_SYNC_INSTRUMENTATION.md` line 356 self-name and line 322 test name; MksServo `README.md` paths and Python file names); the one EKF mention in the I2C analysis removed. Drift tool clean on the component trees | listed files | 5 |
| S6.4 | Documentation check tool | `icm-project/tools/doc_check` (standard-library Python with its `.md` card): term scan with the allowed contexts from Appendix B; relative-link resolver over the three trees; numeric check on `SYSTEM_REQUIREMENTS.md`; every `PRM-*` reference exists in the register. Added to `[commands] verify` in `portal.toml`; optionally a `docs-ci.yml` workflow path-filtered to `Documentation/**`. Clean on `main` after S6.1–S6.3 | new tool, `portal.toml`, optional workflow | 2 |
| S6.5 | Sign-off | Lenton walks §3; the date is recorded in `ARCHITECTURE_DECISIONS.md`; this plan's status line becomes "Done <date>"; the plan is removed in the first code-alignment run (git history keeps it) | this file, `ARCHITECTURE_DECISIONS.md` | 1 |

Total ≈ 101 points over seven sprints.

## 8. Disposition of every document

Conflict column: what the charter contradicts, or "—". Sprint column: where the work lands.

### `Documentation/` root

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `00_INDEX.md` | 166 | "system decision authority"; framework-transition text; motion-permission path | Link charter and plan (S0); rewrite ≤ 100 (S6) | S0, S6 |
| `05_REFACTORING_RULES.md` | 74 | — (process) | Fold into `DOCUMENTATION_RULES.md`; remove | S6 |
| `05_REFACTORING_PLAN.md` | 193 | historical; cites 500 Hz EKF as provisional | Finished work; remove | S6 |
| `05_REFACTORING_LEDGER.md` | 704 | historical | Harvest C-1/C-3 into `ARCHITECTURE_DECISIONS.md`; remove | S6 |
| `06_IMPLEMENTATION_CHECKLIST.md` | 69 | stale | Remove | S6 |
| `CHARTER_ALIGNMENT_PLAN.md` | — | — | This plan; removed after sign-off | S6 |

### `01_SYSTEM/`

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `PROJECT_CHARTER.md` | 38 | — | Keep; update its overview note | S0 |
| `README.md` | 7 | stub | Link charter; remove with the other stubs | S0, S6 |
| `DOCUMENTATION_AUTHORITY_MODEL.md` | 338 | transition sections stale; process | Collapse into index and rules | S6 |
| `SYSTEM_OVERVIEW.md` | 56 | EKF, ROS 2, planning as core responsibilities | Rewrite ≤ 50 | S0 |
| `SYSTEM_REQUIREMENTS.md` | 66 | 500 Hz EKF; about 17 numbers; differential; PL/SIL gate; "system decision authority"; proposed SYS-MOTION | Numbers out (S1); goal requirements in (S2–S4); final baseline and retired table (S5) | S1–S5 |
| `SYSTEM_ARCHITECTURE.md` | 132 | ROS 2 layer; estimator; EKF; differential; independent safety | Rewrite ≤ 100 | S3 |
| `SYSTEM_TIMING.md` | 24 | numbers only; 500 Hz EKF | Content to the register; remove | S1 |
| `SYSTEM_SYNCHRONIZATION.md` | 27 | EKF consumer; numbers | Trim; `PRM` references; gate per D-3 | S1, S3, S4 |
| `SYSTEM_LIFECYCLE.md` | 238 | TIME_SYNC wording; proposed gate; numbers | Trim ≤ 180 | S3, S4 |
| `DISTRIBUTED_MKS_MOTION_CONTROL_RESEARCH.md` | 587 | 500 Hz time-triggered control; estimator; non-normative | Move to `icm-project/research/` | S6 |

### `02_INTERFACES/`

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `README.md` | 7 | stub | Remove | S6 |
| `CAN/CAN_SYSTEM_INTERFACE.md` | 210 | numbers; "release"; gates list | Trim ≤ 150; `PRM` references | S1, S3 |
| `CAN/MKS_SERVO42D_57D_SYNCHRONISATION.md` | 330 | sync-mark control architecture beyond scope; vendor summary | Move to `icm-project/references/mks-servo42d-57d-can/` | S6 |
| `HOST/HOST_SYSTEM_INTERFACE.md` | 22 | EKF/estimator history; open acknowledgement semantics | Rewrite around `SET_MOTOR_COMMAND` | S1, S4 |
| `SPI/SPI_SYSTEM_INTERFACE.md` | 293 | numbers (5 MHz, 1 ms, 100 ms, 5 s) | Keep; `PRM` references; NOT_FITTED note | S1, S2 |
| `SPI/SPI_PAYLOAD_SCHEMA.md` | 224 | `status` enumeration undefined; `SET_MOTOR_COMMAND` not frozen | Keep; status enum (S2); command payload (S4) | S2, S4 |
| `TIME/TIME_SYSTEM_INTERFACE.md` | 125 | EKF ×2; 500 Hz; numbers | Trim; `PRM` references | S1, S3 |

### `03_COMPONENTS/`

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `README.md` | 7 | stub | Remove | S6 |
| `COMPONENT_DOCUMENTATION_MODEL.md` | 268 | — (process) | Collapse into index and rules | S6 |
| `ARM_SENSOR_HUB.md` | 121 | EKF mention; numbers; duplicated topology | Trim ≤ 80; point at the commissioning table and register | S2 |
| `RASPBERRY_SENSOR_HUB.md` | 20 | "estimator history" | Rewrite ≤ 25 | S3 |

### `04_SAFETY/`

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `README.md` | 7 | stub | Remove | S6 |
| `SAFETY_REQUIREMENTS.md` | 43 | PL/SIL release gates | Rewrite as attended-operation behaviours | S4 |
| `SAFETY_ARCHITECTURE.md` | 29 | PL/SIL; risk assessment | Merge into `SAFETY_REQUIREMENTS.md`; remove | S4 |
| `SAFETY_INTEGRATION.md` | 26 | release checklist | Merge; remove | S4 |

### `05_VERIFICATION/`

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `README.md` | 7 | stub | Remove | S6 |
| `VERIFICATION_STRATEGY.md` | 34 | — | Trim ≤ 25 | S5 |
| `SYSTEM_VERIFICATION_MATRIX.md` | 29 | EKF adequacy; differential rows | Rebuild as the trail | S2–S5 |
| `INTEGRATION_GATES.md` | 29 | duplicates the matrix; EKF; differential | Merge into the matrix; remove | S4 |
| `CAN_INTEGRATION_EVIDENCE.md` | 105 | restates the requirement | Trim to evidence; `PRM` references | S3 |
| `TIME_SYNC_VALIDATION.md` | 396 | as-built superseded design; process sections | Keep as dated evidence; cut process sections | S3 |
| `TIME_SYNC_CHARACTERISATION_EVIDENCE.md` | 267 | as-built; one EKF mention | Keep as dated evidence; fix | S3 |
| `EVIDENCE_RECORD_FORMAT.md` | — | — | Create (D-9) | S2 |

### `06_CONFIGURATION/` and `07_DECISIONS/`

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `06_CONFIGURATION/README.md` | 7 | stub | Remove | S6 |
| `06_CONFIGURATION/SYSTEM_CONFIGURATION.md` | 122 | numbers; 500 Hz EKF; differential | §1 and §6 → register; §2 commissioning table; §3–§5 keep | S1, S2, S4 |
| `06_CONFIGURATION/PARAMETER_REGISTER.md` | — | — | Create (Goal 3) | S1 |
| `07_DECISIONS/README.md` | 7 | stub | Remove | S6 |
| `07_DECISIONS/ARCHITECTURE_DECISIONS.md` | 37 | "system decision authority"; proposed gate | Becomes the live decision log: Issue #12 summary, motion gate, C-1/C-3, charter qualifications, sign-off | S0, S4, S6 |
| `07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md` | 215 | EKF/estimator as consumer | Keep; one note | S3 |
| `07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` | 849 | CTO ×11; EKF ×40; MoveIt; differential; 145 historical questions | "CTO" note (S0); rebuild ≤ 150 (S5) | S0, S5 |

### Component documentation and root files

| File | Lines | Conflict | Disposition | Sprint |
|---|---:|---|---|---|
| `Arm_Sensor_Hub/README.md` | 15 | — | Keep | — |
| `Arm_Sensor_Hub/Documentation/README.md` | 76 | stale `docs/project` path (line 46) | Fix | S6 |
| `Arm_Sensor_Hub/Documentation/AS5600_PRECISION_AND_ACCURACY.md` | 96 | — | Keep; the register cites it (Datasheet basis) | S1 |
| `Arm_Sensor_Hub/Documentation/BUILD_CONTRACT.md` | 73 | — | Keep | — |
| `Arm_Sensor_Hub/Documentation/development.md` | 114 | — | Keep | — |
| `Arm_Sensor_Hub/Documentation/HEALTH_MONITOR_CONTRACT.md` | 51 | — | Keep | — |
| `Arm_Sensor_Hub/Documentation/I2C_MANAGER_CONTRACT.md` | 69 | — | Keep | — |
| `Arm_Sensor_Hub/Documentation/I2C_SCAN_TIMING_ANALYSIS.md` | 159 | one EKF mention; `CONTRACT_STATUS.md` references | Fix; the register cites its 690 µs floor (Derived) | S1, S6 |
| `Arm_Sensor_Hub/Documentation/SWD_READOUT_PROCEDURES.md` | 223 | `dump_sync_data.ocd` reference | Fix | S6 |
| `Arm_Sensor_Hub/Documentation/TIME_SYNC_INSTRUMENTATION.md` | 360 | as-built; "CTO"; self-name reference; unverified test name | Keep as as-built; fix | S0, S6 |
| `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/README.md` | — | wrong paths; Python file names in a C++ library | Fix | S6 |
| `RaspberryPi_Sensor_Hub/README.md` | 9 | — | Keep | — |
| `RaspberryPi_Sensor_Hub/Documentation/README.md` | 119 | ROS 2 ×4 and estimator ×4 claimed as authority | Fix | S6 |
| `RaspberryPi_Sensor_Hub/Documentation/RASPBERRY_PI_BRINGUP_V1.md` | 973 | ROS 2 ×35; EKF; PREEMPT_RT motivated by the 500 Hz loop | Trim; ROS 2 and RT parts optional or appendix; `PRM` references | S6 |
| `README.md` | — | "ROS 2 components" in the first line | Fix | S0 |
| `CLAUDE.md` | — | predates the charter and register | Update (S0); final structure (S6) | S0, S6 |
| `For_Lenton` | 529 | CTO; superseded by the register | Retire | S5 |
| `backlog.json`, `portal.toml` | — | waterfall default; B1–B4 dropped | Agile default; load stories; add `doc_check` to verify | S0, S6 |
| `.github/ISSUE_CONTRACT.md`, `ISSUE_FRAMEWORK.md` | — | EKF examples; `estimation` label | Examples swapped; label noted dormant | S5 |
| `icm-project/requester-profile.md` | — | — | Already charter-aware; cite this plan | S0 |

## 9. Appendix A — parameter register seed

This is the seed as written before execution; `06_CONFIGURATION/PARAMETER_REGISTER.md` is authoritative and differs where later decisions changed a value (PRM-ACQ-01 and PRM-CAN-07 on 2026-10-03). Every value below is a working value. The basis column is the claim the evidence supports today; "Provisional" means an engineering estimate not yet confirmed. Where a code symbol is named, it is to be verified against the source when the register is written.

| ID | Parameter | Working value | Basis | Source or evidence | Used by |
|---|---|---|---|---|---|
| PRM-ACQ-01 | Sensor and snapshot publication rate | 100 Hz | Provisional | SD-01 | SYS-ENC, SYS-MOT |
| PRM-ACQ-02 | Six-axis encoder sweep time | ≈ 46 ms | Measured 2026-09-17 | `tools/check-sensors.sh` run; archived `CONTRACT_STATUS.md` in git history | SYS-TS-001 |
| PRM-ACQ-03 | I2C protocol floor for six sensors | ≈ 690 µs | Derived | `I2C_SCAN_TIMING_ANALYSIS.md` (AS5600 datasheet, 400 kHz) | improvement target only |
| PRM-ACQ-04 | I2C bus clock | 400 kHz | Datasheet | AS5600 and TCA9548A fast mode; CubeMX `.ioc` | sensor path |
| PRM-ACQ-05 | Sensor task poll period | 20 ms | Provisional | firmware default `SENSOR_TASK_BRINGUP_POLL_PERIOD_MS`, `sensor_task.c` | sensor path |
| PRM-ACQ-06 | AS5600 resolution | 12 bit, 4096 codes/rev, ≈ 0.001534 rad/code | Datasheet | AS5600 datasheet; `AS5600_PRECISION_AND_ACCURACY.md` | SYS-IF-001 |
| PRM-SPI-01 | SPI clock, maximum | 5 MHz | Provisional (ceiling, not approval) | SD-01, SD-15 | SYS-SPI-001; Stage 3 measurement |
| PRM-SPI-02 | Wire time per 512-byte frame at PRM-SPI-01 | 819.2 µs | Derived | 512 × 8 / 5 MHz | link budget |
| PRM-SPI-03 | Host polling fallback period | 1 ms | Provisional | SD-17; firmware default `SPI_SERVICE_DEFAULT_POLL_PERIOD_MS`, `spi_slave_service.c` | SPI host |
| PRM-SPI-04 | Host-stall timeout | 100 ms | Provisional | firmware default `SPI_SERVICE_HOST_STALL_MS`, `spi_slave_service.c` | SPI slave |
| PRM-SPI-05 | SPI cable length | 20–30 cm | Provisional | former SYS-SPI-004 | Stage 3 measurement |
| PRM-CAN-01 | CAN bitrate target | 1 Mbps | Provisional | SD-05 | SYS-CAN-001 |
| PRM-CAN-02 | CAN bitrate as generated | 875 kbps (prescaler 16, BS1 1, BS2 1, SJW 1, sample point 66.7 %, APB1 42 MHz) | Derived | `CAN_INTEGRATION_EVIDENCE.md`; `.ioc` | as-built |
| PRM-CAN-03 | Candidate 1 Mbps bit timing | prescaler 3, BS1 11, BS2 2, SJW 1, sample point 85.7 % | Derived (not applied) | `CAN_INTEGRATION_EVIDENCE.md` | Stage 3 |
| PRM-CAN-04 | Average bus load ceiling | < 50–60 % | Provisional | SD-05 | Stage 3 measurement |
| PRM-CAN-05 | Motor poll period | 20 ms | Provisional | firmware default `CAN_SERVICE_DEFAULT_POLL_PERIOD_MS`, `can_service.c` | SYS-MOT-001 |
| PRM-CAN-06 | TX HAL retry limit | 3 | Provisional | `CAN_SYSTEM_INTERFACE.md` §4; code symbol to verify | CAN transport |
| PRM-CAN-07 | Bus-off recovery delays | 100 ms → 500 ms → 1 s | Provisional | `CAN_SYSTEM_INTERFACE.md` §5 | SYS-CAN-001 |
| PRM-CAN-08 | Bus-off escalation to ERROR | 3 events in 60 s | Provisional | `CAN_SYSTEM_INTERFACE.md` §5 | SYS-CAN-001 |
| PRM-MOT-01 | Motor feedback timeout | 5 × commissioned feedback period | Provisional | SD-04 | SYS-MOT-002 |
| PRM-MOT-02 | Feedback miss handling | 1 miss degraded; 3 consecutive inhibit and FAULT | Provisional | SD-04 | SYS-MOT-002 |
| PRM-LINK-01 | Pi link-loss detection limit (interim) | 500 ms | Provisional | SD-03; Issue #12 item 11 | SYS-LINK-001 |
| PRM-LINK-02 | `N_moving`, `N_idle` | open | Provisional (no value) | Issue #12 item 11 | SYS-LINK-001 |
| PRM-TS-01 | Timestamp error target | ± 1 ms | Provisional | SD-18 | SYS-TS-001; Stage 3 |
| PRM-TS-02 | Observation skew within a snapshot | < 5 ms normal; < 1 ms target for dynamic joints | Provisional | SD-08 | SYS-TS-001 |
| PRM-TS-03 | ClockSync validity window | 5 s | Provisional | SD-19; as-built `TIME_SERVICE_DEFAULT_VALIDITY_TIMEOUT_US`, `time_service.h` | SYS-TS-001, lifecycle |
| PRM-TS-04 | `counter_extension_gap_us` | 500 ms | Provisional | Issue #12 item 11; code symbol to verify | time service |
| PRM-TS-05 | Legacy drift bounds (as-built TIME_SYNC) | ± 24 h initial; ± 1 s runtime step | Provisional | as-built `TIME_SERVICE_DEFAULT_RUNTIME_OFFSET_STEP_LIMIT_US`, `time_service.h` (initial bound symbol to verify); removed with Issue #12 | as-built only |
| PRM-REP-01 | External angle precision | 4 decimal places (0.0001 rad) | Derived | SD-12 from PRM-ACQ-06 | SYS-IF-001 |
| PRM-MCU-01 | Core clocks | SYSCLK 168 MHz; APB1 42 MHz; APB2 84 MHz | Datasheet | STM32F405 and CubeMX `.ioc` | CAN and SPI timing |

Withdrawn, not registered: 500 Hz EKF rate (charter non-goal).

Contract constants that stay in the interface documents, not in the register: magic `0xA55A`, 18-byte header, CRC-32/ISO-HDLC parameters, 512-byte frame, 490-byte payload, 24-byte records, 12-byte snapshot prefix, message type values, lifecycle state names.

## 10. Appendix B — checks

Term scan (the `doc_check` tool in S6.4 automates this with the allowed contexts):

```bash
grep -rnoiE 'EKF|ROS ?2|ros2_control|MoveIt|500 Hz|PL/SIL|PL or SIL|\bCTO\b|system decision authority|differential|trajectory|estimator|guess|assum[a-z]*' \
  Documentation Arm_Sensor_Hub/Documentation RaspberryPi_Sensor_Hub/Documentation README.md CLAUDE.md
```

Allowed contexts: `PROJECT_CHARTER.md` (non-goals); `SYSTEM_OVERVIEW.md` "Future, not now"; the register SD table "Charter" column; provenance lines; headers of dated as-built evidence; vendor-manual summaries under `icm-project/`. Everything else must be zero.

Numbers in requirements: `grep -E '[0-9]+ ?(Hz|MHz|Mbps|kbps|ms|µs|us|cm|s\b)' Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` must match nothing.

Stale paths: `grep -rn 'docs/project\|99_ARCHIVE' Documentation Arm_Sensor_Hub/Documentation RaspberryPi_Sensor_Hub/Documentation` must return only the index's provenance line.

Links: every relative Markdown link in the three trees resolves to a file; the tool reports the ones that do not.

## 11. Code-alignment backlog seeded by this plan

Created in S5.6, ordered by charter goal. These are not part of this plan's definition of done; they are what the aligned documentation is for.

1. NOT_FITTED sensor status and validity bit in `spi_payload_layout.h`, `spi_protocol.c`, `spi_protocol.py` and both test suites (Goal 1).
2. Encoder-fitted flag in the `app_init.c` commissioning table; the sensor task skips unfitted axes without faulting (Goal 1).
3. Register all six commissioned motors; polling covers all of them (Goal 2).
4. Issue #12 implementation (#42): ISR raw capture, `request_received_local_us`, Pi-side ClockSync, removal of `TIME_SYNC` (Goal 2).
5. `DIAGNOSTIC` v2 and `GET_DIAGNOSTIC` for fault visibility (Goals 2 and 5, SAFE fault indication).
6. `SET_MOTOR_COMMAND` path: SPI decode → gate → MKS command on CAN → ACK/NACK (Goal 4).
7. Simplify `motion_permission.c` to D-3; count-based `link_stale` liveness (Goal 4).
8. CAN bitrate: apply PRM-CAN-03 or keep PRM-CAN-02, decided by the Stage 3 measurement (Goal 3).
9. Centralise firmware and Pi parameters in one header and one config, mirroring the register (Goals 3 and 5).
10. Evidence tooling: `VERSION` identity in every evidence record; timing-harness outputs filed as evidence (Goal 3).

Work packages (`lifecycle.json`):

- WP2 Stage 1: fitted encoders (items 1–2)
- WP3 Stage 2: motor positions and coherent timestamps (items 3–5)
- WP4 Stage 3: links measured (items 8–10)
- WP5 Stage 4: gated motion X, Y, Z (items 6–7)
- WP6 Stage 5: remaining joints

## 12. Risks

| Risk | Handling |
|---|---|
| Review load: about 100 points across seven sprints, all reviewed by one person | Sprints capped at 20 points; one review sitting each; order re-planned at each Sprint plan |
| Caveats lost while trimming (the refactoring ledger's warning) | Ground rule: caveats are kept verbatim; the `doc_check` scan lists caveat phrases so their disappearance is visible |
| Wire-format changes made on paper create immediate code debt | Lockstep rule: the issue is created in the same run; the document says "not yet implemented (issue #n)" |
| Re-opening settled decisions (Issue #12, SD statuses) | The charter protects approved SDs; the plan annotates them and recommends keeping Issue #12 (D-2) |
| Facts only Lenton has (fitted axes, joint names, MKS model and firmware, E-stop hardware) | Asked in the Design stage via the Liaison; recorded as "unknown" until answered; never invented |
| The agile methodology has not been used on Karetao before | Sprint 0 is the trial; waterfall per sprint is the fallback |
| Documentation-only commits do not trigger the path-filtered CI | The Portal's Verify runs the same commands locally; `doc_check` joins the verify list in S6.4 |

## 13. How to start

1. Read this plan and the charter; answer D-1 (where the plan lives, agile default).
2. Open the Portal, start an agile run titled "Sprint 0 — Wire the charter in", and paste stories S0.1–S0.4 as the backlog.
3. At the Retro, re-plan Sprint 1 from §7 and adjust points from what Sprint 0 cost.

## 14. Definition-of-done status (2026-10-04)

The walk was made on the Portal branch `portal/2026-10-04-sign-off-readiness-the-charter-alignment`, not on `main`; §3 asks for the items to hold on `main`, so the merge is still to come. Commands were run from the repo root. "The decisions register" in 3.6 is read as `KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md`.

| Item | Status | Evidence |
|---|---|---|
| 3.1 Scope | Holds | The §10 term scan returns many hits, all in allowed contexts: the charter, the overview's "Future, not now" note, the register, the Issue #12 record, retired-identifier and withdrawn lines, the safety list of withdrawn SAFE-001, this plan, and the Pi bring-up guide's optional ROS 2 parts. Hits in `CLAUDE.md`, `DOCUMENTATION_RULES.md` and the register state the rule or the non-goal. `python3 icm-project/tools/doc_check/doc_check.py` prints "doc_check: clean". The sorting of raw hits into allowed contexts follows `icm-project/tools/doc_check/allowed.toml`, not a hand count. |
| 3.2 Numbers | Holds | The §10 numbers grep on `SYSTEM_REQUIREMENTS.md` prints nothing. `doc_check` (prm check) finds every `PRM-*` reference defined in the register. A full audit of every number in every normative document has no tool; only these two checks were run. |
| 3.3 Requirements | Holds | `grep -c '^| SYS-'` gives 40 rows in `SYSTEM_REQUIREMENTS.md` (17 baseline rows, SYS-ENC-001 to SYS-SYNC-001, plus 23 rows in the retired table) and 17 in `SYSTEM_VERIFICATION_MATRIX.md`. Every baseline row has a source and an acceptance sentence; every matrix row names a code module, a test or "none yet" with an issue, and the evidence required. |
| 3.4 Interfaces | Does not hold | `grep -rniE 'TBD\|not frozen\|proposed' Documentation/02_INTERFACES` finds one hit: `SPI_SYSTEM_INTERFACE.md:104`, the `GET_DIAGNOSTIC` message value is "TBD". It is not one of the items §3 names (NOT_FITTED, six motor records, clock-sync extension, `SET_MOTOR_COMMAND`, ACK/NACK), but it is not scoped to a later stage either; `SPI_PAYLOAD_SCHEMA.md:264` lists it as open and backlog item 5 (§11) has no stage. Lenton to scope it to a stage or assign the value. |
| 3.5 Trail | Blocked: GitHub changes held for Lenton Neale | The held script is not in this repository's history: `git log --all --name-only --oneline -- '*github*' '*.sh'` finds only the ICM workspace scripts, the issue contract and framework, and CI files. The intended changes, per §7 S2.5, S3.5, S4.5, S5.4 and S5.6, are: new LIVE-17 to LIVE-22 issues; M1 to M7 renamed or closed into Stages 1 to 5; the EKF and PL/SIL issues closed as not planned citing the charter non-goal; one issue per §11 divergence. Nothing has been checked against GitHub. |
| 3.6 Size | Holds | `wc -l`: `00_INDEX.md` 59 and `DOCUMENTATION_RULES.md` 45, total 104 (limit 250); the register 86 (limit 150). No `README.md` or `For_Lenton` file exists under `Documentation/`. |
| 3.7 Links | Does not hold | Links: `doc_check` is clean. Stale paths: the §10 stale-path grep returns 17 lines, not one: the index provenance line, 5 lines in this plan, and 11 provenance lines elsewhere (`SYSTEM_ARCHITECTURE.md:99`, `CAN_SYSTEM_INTERFACE.md:149`, `SPI_SYSTEM_INTERFACE.md:291`, `SPI_PAYLOAD_SCHEMA.md:271`, `TIME_SYSTEM_INTERFACE.md:129`, `SYSTEM_CONFIGURATION.md:136`, `ARM_SENSOR_HUB.md:79`, `CAN_INTEGRATION_EVIDENCE.md:35` and `:80`, `RASPBERRY_PI_BRINGUP_V1.md:32` and `:916`). All are provenance or history statements and `doc_check` allows them (header of this plan); §3 item 7 as written does not. Lenton to accept them or ask for them to be cut. |
| 3.8 Lockstep | Blocked: GitHub changes held for Lenton Neale | Holds now: `SPI_PAYLOAD_SCHEMA.md:92` says "not yet implemented on either side" and names the lockstep issue by title, "[LIVE-17] Implement NOT_FITTED sensor status (C, Python, tests)"; the matrix and requirements rows say "not yet implemented" for SYS-ENC-002, SYS-CMD-001 and SYS-SYNC-001. Blocked: the issues are not yet created (see 3.5), so no row can cite an issue number from GitHub. |

3.9 Sign-off: walked by Lenton Neale 2026-10-04; 3.4, 3.5, 3.7 and 3.8 accepted as exceptions (see ARCHITECTURE_DECISIONS.md Sign-off).

### 14.1 Left for Lenton Neale

No row was changed to Holds in this pass: each of the four open rows needs a decision or an action outside the documents, and no fix agreed with Lenton Neale for them is recorded. No file other than this plan was edited.

- **3.4 Interfaces** (`GET_DIAGNOSTIC` value "TBD" at `SPI_SYSTEM_INTERFACE.md:104`, listed as open at `SPI_PAYLOAD_SCHEMA.md:264`). Reason: choosing a value or a stage is a scope and interface decision. Recommendation: scope it to a named later stage in both files and in backlog item 5 (§11), leaving the value unassigned until that stage; this clears the grep without inventing a value.
- **3.5 Trail** (GitHub changes). Reason: the held script is not in this repository's history and nothing here can change GitHub. Recommendation: run the changes listed in the row (LIVE-17 to LIVE-22, M1 to M7 renamed or closed, EKF and PL/SIL closed as not planned, one issue per §11 divergence), then record the issue numbers.
- **3.7 Links** (17 stale-path grep lines, all provenance or history statements). Reason: cutting them is a deletion that needs the `DOCUMENTATION_RULES.md` check, and accepting them changes what §3 item 7 means. Recommendation: accept them, and reword §3 item 7 to exclude provenance lines that `doc_check` allows, since they record where content came from.
- **3.8 Lockstep** (no issue numbers to cite). Reason: it depends on 3.5. Recommendation: after the issues exist, add their numbers to `SPI_PAYLOAD_SCHEMA.md:92` and the matrix and requirements rows for SYS-ENC-002, SYS-CMD-001 and SYS-SYNC-001.

## 15. Layered review (agreed 2026-10-04)

The documentation is reviewed again from the top down, one layer per Portal agile run. Each layer is reviewed read-only against the layers above it, as merged on `main`. A run never edits a layer above its own; a fault found there becomes a story for that layer. WP1 covers L0 and L1 and closes at its Requirements gate. WP7 (`lifecycle.json`) covers L2 to L5 and closes at the Architecture gate, which tags `baseline/architecture/v1`. The GitHub trail (§3 items 5 and 8) is its own short run after L5.

| Layer | Documents | Reviewed against |
|---|---|---|
| L0 Scope | `PROJECT_CHARTER.md`, `00_INDEX.md`, `DOCUMENTATION_RULES.md` | Lenton Neale |
| L1 Requirements | `SYSTEM_OVERVIEW.md`, `SYSTEM_REQUIREMENTS.md`, `SAFETY_REQUIREMENTS.md`, `PARAMETER_REGISTER.md` | L0 |
| L2 Architecture and interfaces | `SYSTEM_ARCHITECTURE.md`, `SYSTEM_LIFECYCLE.md`, `SYSTEM_SYNCHRONIZATION.md`, `02_INTERFACES/**`, `ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md` | L1, L0 |
| L3 System components and configuration | `03_COMPONENTS/*`, `SYSTEM_CONFIGURATION.md` | L2, L1 |
| L4 Component implementation | `Arm_Sensor_Hub/Documentation/*`, `RaspberryPi_Sensor_Hub/Documentation/*`, `CLAUDE.md` | L3, L2 interfaces |
| L5 Verification | `05_VERIFICATION/*` | L1 for the rows, L4 for module and test names |

`ARCHITECTURE_DECISIONS.md` and the register are updated in whichever run raises an item. They are not a layer of their own.

A layer review classes each finding as one of the following:
- **contradicts** the layer above
- **exceeds** the charter or the scope of the layer above
- **redefines** something instead of referencing it
- **orphan**: has no parent in the layers above
- **gap**: a parent item that this layer does not serve
- **unbased number**: has no `PRM-*` row or contract constant

A layer merges only when every contradicts, exceeds or redefines finding has a ruling from Lenton Neale. If a layer is over about 20 points, it is split into runs: L2 into SPI and TIME, then CAN, HOST and architecture; L4 into Arm, then Pi.
