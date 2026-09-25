# Tracker conventions

Identifiers are in `github.env`. The full rules are in `.github/ISSUE_CONTRACT.md`; this file summarises only what the agents need.

## Titles

Action-oriented, prefixed with the register ID where one exists: `[LIVE-xx] Define …`, `[SD-xx] Resolve …`. Without an ID, start with Define / Implement / Verify / Update / Investigate.

## Labels (approved; never invent new ones)

`communications` `configuration` `design` `estimation` `implementation` `mechanical` `safety` `timing` `verification`

## Board fields (project "Karetao Engineering")

| Field | Options |
|---|---|
| Status | Backlog, Ready, In Progress, Blocked, Verification, Done |
| Workstream | Documentation, Software, Hardware, System |
| Work Type | Design, Implementation, Verification |
| Priority | High, Medium, Low (planning only, not a safety classification) |

Set all four on every open issue. Break work down using GitHub sub-issues (parent → children), not text links alone.

## Milestones

Use `gh api repos/LentonNeale/Karetao/milestones` for the current list. Don't copy the list here.

## Register

`Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` has one LIVE-xx row per tracked item. `issue-clerk` may change only the **Status** column and the **issue-link** column, plus sub-issue lists in the link column. Row descriptions change only through stage 03 design.

## Branching / push policy

Documentation-only work may be committed to `main` and pushed once the user approves. Code changes go on an `<issue#>-<slug>` branch with a PR. Never push without approval.
