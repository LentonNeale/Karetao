# 04 — Implement

Change code or configuration to satisfy an issue. **The main session plans and reviews.** Mechanical, fully specified edits may go to a sonnet subagent.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Stage 02/03 | `../02-issue-spec/output/<issue#>-spec.md`, `../03-design/output/<issue#>-design.md` (if any) | Acceptance Criteria, decisions | What "done" means |
| Project | `../../../icm-project/PROJECT.md` | The component involved | Code layout and conventions |
| Project | `../../../icm-project/build.md` | The component involved | How to build and test locally |

## Process

1. Write the plan: the files to change, the tests to add or update, and the risks. **CHECKPOINT:** the user approves it.
2. Work on a branch named `<issue#>-<slug>`.
3. Implement. Keep interfaces that exist in more than one place (see `PROJECT.md`) in lockstep.
4. Run the fast local checks from `build.md` before handing over to stage 05.
5. Summarize the change against each acceptance criterion.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Change summary | `output/<issue#>-change.md` | Branch, files changed, and for each acceptance criterion: how it is met or what is still open |
