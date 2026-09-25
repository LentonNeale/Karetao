# 03 — Design

Resolve design questions for an issue and propose changes to the authoritative documentation. **Runs in the main session.**

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Stage 02 | `../02-issue-spec/output/<issue#>-spec.md` | Scope, Acceptance Criteria | What must be decided |
| Project | `../../../icm-project/authority.md` | The rows for the affected subjects | Which documents own the answer |
| Authority docs | The paths named by `authority.md` | Only the relevant sections | Current requirements and decisions |

## Process

1. List the decisions needed. Mark each one open, proposed or decided, and never promote proposed to decided on your own.
2. Give options with trade-offs, and a recommendation for each open decision.
3. **CHECKPOINT:** the user decides.
4. Draft the document changes as diffs against the owning documents, preferring the newest decision where documents conflict. Where documents conflict, note what supersedes what.
5. **CHECKPOINT:** the user approves the diffs. Then apply them, and comment the decision summary on the issue.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Design note | `output/<issue#>-design.md` | Decisions table (decision · status · rationale · owning doc) and a list of approved doc edits |
