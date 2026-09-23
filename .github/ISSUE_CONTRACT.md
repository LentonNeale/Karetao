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
5. Do not invent new labels for individual projects, components, states, or IDs.
6. Put detailed technical decisions in the appropriate documentation; link the issue to that record.
7. Close an issue when its acceptance criteria are met, or mark it as not planned/duplicate where appropriate.
8. GitHub issue state is workflow state; it is not a substitute for the authoritative project status register.

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

Do not encode labels, lifecycle state, priority, or release status in the title unless required by an established project convention.

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
| `estimation` | `#059669` | State estimation, EKF, sensor fusion, observability, or related estimation logic. |
| `mechanical` | `#CA8A04` | Mechanical interfaces, kinematics, end-effector mapping, or physical-system models. |
| `configuration` | `#64748B` | Calibration, parameters, configuration data, persistence, versioning, or validity. |

### Label selection

Use labels to describe the **nature of the work**, not its project identifier or workflow state.

A single issue may have multiple labels.

Examples:

- Safety architecture decision → `design` + `safety`
- CAN implementation → `implementation` + `communications`
- TIME_SYNC verification → `verification` + `timing`
- EKF design → `design` + `estimation`
- Calibration implementation and testing → `implementation` + `configuration` + `verification`
- Mechanical mapping design → `design` + `mechanical`

Do not create labels for:

- `LIVE-xx` or `SD-xx` identifiers
- open/closed status
- proposed/deferred/historical/superseded status
- individual components
- individual developers
- temporary workstreams

Those belong in issue titles, bodies, GitHub state, or the authoritative project documentation.

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

This document is the repository-level contract for issue creation and labelling.
