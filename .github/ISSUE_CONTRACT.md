# Karetao Issue Contract

## Purpose

GitHub Issues are the project's **work-tracking mechanism**. They record work to be done, design questions, implementation tasks, verification activities, and miscellaneous project issues.

Issues do **not** replace authoritative requirements, architecture, safety, verification, or decision documents.

When an issue conflicts with an authoritative document, the authoritative document governs.

## Quick Rules

1. Search existing issues before creating a new one.
2. Use a clear, action-oriented title.
3. Reference the relevant `LIVE-xx`, `SD-xx`, or other project identifier when one exists.
4. Apply labels from the approved taxonomy below.
5. Record blocking as GitHub native issue dependencies; `icm-project/tools/issue_graph` derives the board order and the `Blocked`, `Ready` and `Backlog` Statuses from them (see Status and Order). Labels carry the nature of the work.
6. Do not invent new labels for individual projects, components, states, priorities, or IDs.
7. Put detailed technical decisions in the appropriate documentation; link the issue to that record.
8. Close an issue when its acceptance criteria are met, or mark it as not planned/duplicate where appropriate.
9. GitHub issue state and Project Status are work-tracking state; neither replaces the authoritative project status register.
10. Project Status and board order are planning metadata and must not be presented as engineering requirements unless an authoritative document explicitly makes them so.

## Issue Categories

Every issue should fit one primary work category:

- **Design** — architecture, requirements, interfaces, design questions, or technical decisions.
- **Implementation** — software, firmware, hardware, configuration, or integration work.
- **Verification** — testing, validation, evidence, acceptance, or release verification.
- **Miscellaneous** — project work that does not fit the technical categories, such as documentation maintenance, repository administration, tooling, or coordination.

Miscellaneous issues do not require a dedicated `miscellaneous` label. Use the most relevant existing label if one applies; otherwise leave the issue unlabeled rather than creating a one-off label.

## Naming Convention

Use concise action-oriented titles.

Preferred forms:

- `[LIVE-xx] Define ...`
- `[LIVE-xx] Verify ...`
- `[LIVE-xx] Implement ...`
- `[SD-xx] Resolve ...`
- `[SD-xx] Implement ...`
- `[SD-xx] Verify ...`

For issues without a formal project identifier:

- `Define ...`
- `Implement ...`
- `Verify ...`
- `Update ...`
- `Investigate ...`

Do not encode labels, workflow state, priority, release status, workstream, or developer names in the title unless required by an established project convention.

## Approved Labels

The standard label set is deliberately small.

| Label | Colour | Use |
|---|---|---|
| `design` | `#0E7490` | Design, architecture, interfaces, requirements, or technical decisions. |
| `implementation` | `#2563EB` | Software, firmware, hardware, or integration work implementing an approved design. |
| `verification` | `#7C3AED` | Testing, validation, evidence, or acceptance activities. |
| `safety` | `#DC2626` | Safety mechanisms, boundaries, hazards, controls, or safety evidence. |
| `timing` | `#D97706` | TIME_SYNC, clocks, scheduling, latency, freshness, or temporal validity. |
| `communications` | `#0891B2` | CAN, SPI, transport, protocols, messaging, or communication interfaces. |
| `estimation` | `#059669` | Dormant since 2026-10-03: state estimation is a charter non-goal (Documentation/01_SYSTEM/PROJECT_CHARTER.md). Kept so old issues keep their label; do not apply to new issues. |
| `mechanical` | `#CA8A04` | Mechanical interfaces, kinematics, end-effector mapping, or physical-system models. |
| `configuration` | `#64748B` | Calibration, parameters, configuration data, persistence, versioning, or validity. |

### Label selection

Use labels to describe the **nature of the work**, not its project identifier, workflow state, workstream, or priority.

A single issue may have multiple labels.

Examples:

- Safety architecture decision → `design` + `safety`
- CAN implementation → `implementation` + `communications`
- TIME_SYNC verification → `verification` + `timing`
- Link measurement → `verification` + `timing`
- Calibration implementation and testing → `implementation` + `configuration` + `verification`
- Mechanical mapping design → `design` + `mechanical`

Do not create labels for:

- `LIVE-xx` or `SD-xx` identifiers
- open/closed status
- proposed/deferred/historical/superseded status
- individual components
- individual developers
- temporary workstreams

These belong in issue titles, Project fields, GitHub state, or the authoritative project documentation.

## Karetao Engineering Project Fields

The GitHub Project provides management metadata separately from labels. The board was closed and reopened on 2026-10-15 when the ICM Map was retired; it is now the single ordering view above issues, and the fields below are the only ones it keeps.

### Status

Use `Backlog`, `Ready`, `In Progress`, `Blocked`, `Verification`, and `Done`. Project Status is workflow metadata, not an engineering authority. `Blocked`, `Ready` and `Backlog` are derived from GitHub native issue dependencies and the current stage by `icm-project/tools/issue_graph` (rules in its card), which also sets the board order and the tool-owned `Blocking` count field; `In Progress`, `Verification` and `Done` are set by people or by GitHub's close workflow. An agent that cannot write the board records the state in the first line of the triage comment instead (`> Triage state: ...`, `docs/agents/triage-labels.md`).

### Order

The board order is the priority, and it is computed, never set by hand: `issue_graph --apply` re-places every open issue by stage, then by how many open issues lie downstream of it (everything it holds up through the edges, in any stage), then by number, so a hand-dragged order is lost at the next refresh. To put one issue before another within a stage, add a native edge (the earlier issue blocks the later one) and say in the later issue why it needs the earlier one; a preference with no such reason is left to the tie-break. Issues with no milestone (bench bring-up phases, decision tickets, maps) sort after the stages, even when they block a staged issue (that issue's `Blocked` status shows the edge), and are picked by hand. Decided in #97 (2026-10-16). There is no `Priority` field, and order is not a safety classification, requirement status, or severity.

### Retired fields

`Workstream`, `Work Type`, `Priority`, and `Target Date` are retired. Labels carry the nature of the work, the board order replaces priority, and milestones are stages, not dates.

### Milestones

Use native GitHub Milestones for major engineering objectives or release groupings. Do not duplicate milestones in labels or custom Project fields. Milestones remain the stage grouping. Milestones are stages named after charter goals (Stage 1 Fitted encoders … Stage 5 Remaining joints), not dates.

## Adding a New Label

Add a new label only when the existing taxonomy cannot describe a recurring class of work.

Before adding one:

1. Check this contract and existing labels.
2. Confirm that the proposed label represents a **stable category of work**, not a single issue.
3. Prefer reusing an existing label.
4. Use a short lowercase name with hyphens where needed.
5. Define a one-sentence description.
6. Assign a colour consistent with the existing colour convention.
7. Update this contract in the same change.
8. Do not use a new label until the contract documents it.

New labels should normally represent either a **work type** or a **stable technical domain**.

## Colour Convention

Colours are categorical, not priority indicators.

- Teal/cyan — design and interfaces
- Blue — implementation
- Purple — verification
- Red — safety
- Amber/gold — timing and mechanical domains
- Green — estimation
- Slate — configuration

Do not use colour to imply severity, priority, completion, or approval.

## Issue Body Expectations

A useful issue should state, as applicable:

### Context
Why the issue exists and what project area it concerns.

### Scope
What the issue covers and what it does not cover.

### Acceptance Criteria
Specific conditions that determine when the issue is complete.

### Verification / Evidence
How completion will be demonstrated, where applicable.

### References
Links or references to authoritative documentation, decisions, requirements, or related issues.

For design issues, record the resulting decision in the appropriate authoritative documentation rather than leaving the decision only in issue discussion.

For verification issues, identify the required evidence or verification record.

## Relationship to Project Status

The project's formal status vocabulary and live-work index remain authoritative in the relevant documentation, particularly:

`Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md`

GitHub labels must not be used as a second status system.

Issue IDs such as `LIVE-01` identify project work; they are not labels.

## For Agents and Automated Tools

When creating or modifying an issue:

1. Read this contract first.
2. Search for an existing related issue.
3. Preserve established `LIVE-xx` / `SD-xx` references.
4. Use only approved labels.
5. Do not invent labels because an issue is unusual.
6. Keep the issue title concise and action-oriented.
7. Include acceptance criteria when the work is actionable.
8. Link to authoritative documentation where applicable.
9. Do not treat issue labels as authoritative project status.
10. Update this contract when an approved label taxonomy change is made.

This document is the repository-level contract for issue creation, labelling, and Project-field use.
