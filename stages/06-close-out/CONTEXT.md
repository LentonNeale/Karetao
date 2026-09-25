# 06 — Close-out

Bring the tracker and the docs in line with what was actually delivered. The main session decides, and **`issue-clerk` (sonnet) applies the changes.**

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Stages 02–05 | `../0[2-5]-*/output/<issue#>-*.md` | Acceptance criteria, change, evidence | What was delivered |
| Project | `../../../icm-project/github.md` | Status and register rules | How to record completion |

## Process

1. Map each acceptance criterion to evidence: met, partially met or not met. Criteria that aren't met become follow-up issues (via stage 02), not silent closes.
2. **CHECKPOINT:** the user approves the close-out plan.
3. `issue-clerk` ticks the met criteria, posts an evidence comment, sets Status, and closes the issue only if all criteria are met. It also updates the register row and the parent issue.
4. Run `../../scripts/link-check.py`. If docs changed, delegate a consistency pass to `doc-checker`.
5. If code or docs changed, prepare the commit or PR. Never push without the user's approval.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Close-out record | `output/<issue#>-closeout.md` | Criteria → evidence table, follow-up issues, the clerk's change log, commit/PR link |
