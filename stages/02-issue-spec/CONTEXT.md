# 02 — Issue Spec

Turn an approved brief into a tracker-ready issue and apply it. The main session drafts the spec, and **`issue-clerk` (sonnet) applies it.**

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Stage 01 | `../01-intake/output/<slug>-brief.md` | Full | What to track |
| Project | `../../../icm-project/github.md` | Full | Title, label, field and milestone rules |
| Project | `../../../icm-project/github.env` | Full | Repo and project identifiers (for scripts) |

## Process

1. Draft the spec: title, labels, milestone, parent issue, and the four board fields (Status, Workstream, Work Type, Priority). The body has these sections: Context · Scope · Acceptance Criteria (checkboxes) · Verification / Evidence · References.
2. For an update, list the exact changes against the current issue text (`gh issue view N`).
3. **CHECKPOINT:** the user approves the spec.
4. Delegate the approved spec to `issue-clerk`. It creates or edits the issue, links the parent, adds the issue to the board and sets the fields with `../../scripts/set-field.sh`.
5. If the project keeps a register, `issue-clerk` updates the matching row, but only for the fields named in `github.md`.
6. Review the clerk's report and record the issue URL in the spec.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Issue spec | `output/<issue#>-spec.md` | Header (`status: applied`, URL), spec body, and the clerk's change log |
