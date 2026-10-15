# Karetao Issue Framework

## 1. Purpose

This document defines the required structure and minimum content for a new GitHub Issue in the Karetao repository.

It is the supporting implementation framework for `.github/ISSUE_CONTRACT.md`.

The objective is to make every issue:

- immediately understandable to a developer or agent;
- traceable to the relevant Karetao workstream or decision;
- actionable without reconstructing missing context;
- objectively closable through explicit acceptance criteria;
- consistently categorised through the approved label taxonomy and Karetao Engineering Project fields.

GitHub Issues are work-tracking records. They do not replace authoritative requirements, architecture, safety, verification, or decision documentation.

---

## 2. Issue Structure

A new issue should contain the following structure, in this order:

1. **Title**
2. **Description / Context**
3. **Scope**
4. **Acceptance Criteria**
5. **Verification / Evidence**
6. **References**

Not every issue requires every section to contain substantial text. Sections may be marked `N/A` where genuinely not applicable.

---

## 3. Title Requirements

### 3.1 General form

The title shall be:

- concise;
- action-oriented;
- specific enough to identify the intended outcome;
- free of unnecessary implementation detail;
- free of workflow status and priority indicators.

### 3.2 Project-linked issues

Where an issue belongs to an existing formal work item, the project identifier shall appear first.

Preferred forms:

`[LIVE-xx] Define <subject>`

`[LIVE-xx] Implement <subject>`

`[LIVE-xx] Verify <subject>`

`[SD-xx] Define <subject>`

`[SD-xx] Implement <subject>`

`[SD-xx] Verify <subject>`

### 3.3 Issues without a formal identifier

Use a direct action:

`Define <subject>`

`Implement <subject>`

`Verify <subject>`

`Update <subject>`

`Investigate <subject>`

### 3.4 Title rules

Do not put the following into a title unless an established project convention explicitly requires it:

- labels;
- Project Status;
- workstream or work type;
- priority;
- severity;
- open/closed status;
- proposed/deferred status;
- developer names;
- branch names;
- implementation notes.

The title identifies **what needs to be accomplished**, not how the issue is administratively managed.

---

## 4. Description Requirements

The description shall provide enough information for another developer or agent to understand the issue without relying on private conversation history.

Use the following structure:

### Context

State:

- why the issue exists;
- the relevant system or project area;
- the current condition or problem;
- any relevant relationship to an existing decision, requirement, or work item.

### Scope

State:

- what this issue covers;
- the expected boundary of the work;
- important exclusions where ambiguity is likely.

Avoid allowing one issue to silently expand into unrelated work.

### Acceptance Criteria

Define the conditions that must be satisfied before the issue can be closed.

Acceptance criteria shall be:

- observable;
- specific;
- testable where applicable;
- written as completion conditions rather than activities.

Prefer:

- "The motion-permission API returns a deterministic reason code for each defined prerequisite failure."

Over:

- "Implement reason codes."

### Verification / Evidence

State how completion will be demonstrated.

Examples include:

- unit tests;
- integration tests;
- system verification;
- inspection;
- analysis;
- captured logs;
- configuration evidence;
- hardware evidence;
- documented review;
- update to an authoritative verification record.

Where the issue affects a release gate or safety function, the required evidence shall be explicit.

### References

Include relevant:

- authoritative documentation;
- decision records;
- requirements;
- verification records;
- related GitHub Issues;
- pull requests;
- external technical references where appropriate.

Cite the SYS-* row (Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md) or the stage the issue serves.

Use stable repository paths or issue/PR references where possible.

---

## 5. Minimum Issue Template

The following is the standard starting structure:

```markdown
## Context

<Why this issue exists and what project area it concerns.>

## Scope

<What this issue covers and, where useful, what it does not cover.>

## Acceptance Criteria

- [ ] <Observable completion condition>
- [ ] <Observable completion condition>
- [ ] <Observable completion condition>

## Verification / Evidence

<How completion will be demonstrated and where the evidence will be recorded.>

## References

- <Authoritative document / decision / related issue>
```

For a simple issue, sections that are genuinely not applicable may be omitted. Acceptance criteria should normally remain present for actionable work.

---

## 6. Label Requirements

Labels classify the **nature of the work**.

They do not replace the issue title, project identifier, Project Status, or acceptance criteria.

### 6.1 Required classification

Every substantive technical issue shall normally have at least:

- one **work-type** label; and
- zero or more **technical-domain** labels.

Work-type labels:

- `design`
- `implementation`
- `verification`

Technical-domain labels:

- `safety`
- `timing`
- `communications`
- `estimation`
- `mechanical`
- `configuration`

### 6.2 Work-type selection

Use:

**`design`**
when the primary outcome is a design, architecture, requirement, interface, or technical decision.

**`implementation`**
when the primary outcome is implemented software, firmware, hardware, configuration, or integration.

**`verification`**
when the primary outcome is testing, validation, evidence, acceptance, or verification.

Multiple work-type labels may be used where an issue intentionally spans phases. Do not add all three merely because implementation will eventually require testing.

### 6.3 Technical-domain selection

Apply a technical-domain label when it materially describes the subject.

Examples:

- Motion safety → `design` + `safety`
- CAN implementation → `implementation` + `communications`
- TIME_SYNC verification → `verification` + `timing`
- Link measurement → `verification` + `timing`
- Mechanical mapping → `design` + `mechanical`
- Calibration implementation → `implementation` + `configuration`

Do not add technical labels merely because a component is mentioned incidentally.

---

## 7. Karetao Engineering Project Classification

The Karetao Engineering Project provides planning metadata separately from labels. Only `Status` and the item order are used (7.3).

### 7.1 Project Status

Use `Backlog`, `Ready`, `In Progress`, `Blocked`, `Verification`, and `Done`. Project Status represents work-tracking state and is not a substitute for the authoritative live status register. An agent that cannot write the board records the state in the first line of the triage comment (`> Triage state: <role>`, `docs/agents/triage-labels.md`).

### 7.2 Order

The board's manual item order within a milestone is the priority. It is not a safety classification or engineering severity.

### 7.3 Retired fields

The board was closed and reopened on 2026-10-15 when the ICM Map was retired. `Workstream`, `Work Type`, `Priority`, and `Target Date` are retired: labels carry the nature of the work, the board order replaces priority, and milestones are stages, not dates.

### 7.4 Milestones

Use native GitHub Milestones for major engineering objectives or release groupings. Milestones remain the stage grouping. Do not duplicate milestone information in labels or Project custom fields.

## 8. Miscellaneous Issues

Not every issue is a technical design, implementation, or verification task.

Examples include:

- repository maintenance;
- documentation administration;
- tooling;
- process improvements;
- coordination work;
- housekeeping.

These may be created without a work-type or technical-domain label when none accurately applies.

Do **not** create a `miscellaneous` label simply to classify these issues.

A new label should represent a stable and recurring category of work, not an exception.

---

## 9. Formal Identifiers

Where an issue is part of an established project workstream, preserve the existing identifier.

Examples:

- `[LIVE-01]`
- `[LIVE-20]`
- `[SD-01]`

Identifiers belong in the title and/or description as appropriate.

They shall **not** be converted into GitHub labels.

The authoritative meaning and status of these identifiers remains defined by the relevant Karetao documentation.

---

## 10. Issue Creation Decision

Before creating an issue, the author or agent shall determine:

1. Does an equivalent or substantially related issue already exist?
2. Is this work part of an existing `LIVE-xx` or `SD-xx` item?
3. What is the primary work type (which decides the label)?
4. Which technical domain, if any, applies?
5. What is the intended outcome?
6. What evidence will demonstrate completion?
7. Which authoritative documents or decisions govern the work?

If these questions cannot be answered, the issue should normally be clarified before creation.

---

## 11. Closing Criteria

An issue should be closed only when its acceptance criteria have been satisfied or when GitHub's closure reason appropriately records that it is:

- completed;
- not planned; or
- a duplicate.

Closing an issue is not, by itself, evidence that an authoritative project requirement or verification gate has been satisfied.

Where formal evidence is required, the issue shall reference the resulting evidence or authoritative record.

---

## 12. Agent and Developer Rules

Any developer or automated agent creating an issue shall:

1. Read `.github/ISSUE_CONTRACT.md` and this document.
2. Search existing issues before creating a new one.
3. Use the established title convention.
4. Preserve relevant `LIVE-xx` and `SD-xx` identifiers.
5. Use only approved labels.
6. Include explicit acceptance criteria for actionable work.
7. Identify verification evidence where applicable.
8. Reference authoritative project documentation.
9. Avoid creating labels for individual issues, temporary states, developers, branches, or priorities.
11. Do not treat Project Status, labels, or planning fields as authoritative engineering status.
12. Update this framework and the Issue Contract when the approved issue taxonomy or Project-field convention changes.

---

## 13. Relationship to the Issue Contract

`.github/ISSUE_CONTRACT.md` defines the repository-level policy for GitHub Issues, including the approved label taxonomy and colour convention.

This document defines the **concrete issue structure and creation framework** used to apply that policy.

Together they form the Karetao issue-management standard.
