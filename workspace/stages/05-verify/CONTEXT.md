# 05 — Verify

Build, test and capture evidence. **Delegate to `build-runner` (haiku); the main session reviews the result.**

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Stage 04 | `../04-implement/output/<issue#>-change.md` | Files changed | What to verify |
| Stage 02 | `../02-issue-spec/output/<issue#>-spec.md` | Verification / Evidence | Required evidence |
| Project | `../../../icm-project/build.md` | Full | Exact commands |

## Process

1. `build-runner` runs every command listed in `build.md` for the affected components and records the exit status and failure excerpts.
2. The main session compares the results with the issue's required evidence.
3. Classify each item as component evidence, hardware evidence still needed, or system-level verification. Only the process named in `authority.md` can grant system-level verification.
4. **CHECKPOINT:** the user reviews any failures or gaps before close-out.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Evidence summary | `output/<issue#>-evidence.md` | For each command: result and excerpt; for each required item: met, gap or needs hardware |
