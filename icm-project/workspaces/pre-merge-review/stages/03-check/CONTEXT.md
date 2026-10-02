# 03 Check

Checks every finding against the code before the turn returns them.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Findings | stage 2 | The `issues` list and the `summary` | What to check |
| Project files | the working copy | Only the ranges a finding names | To confirm the finding is real |
| Severity | `../../shared/severity.md` | Full file | To confirm each severity is honest |
| References | `../../shared/references.md` | Only the rows for the code areas the diff touches, then only the note and section each row names | To judge a register, command, timing or API use against its source |

## Process

1. For each finding, Read the file it names and confirm the problem is there.
2. Drop a finding you cannot confirm. Lower a severity that is higher than the evidence supports.
3. Confirm there are at most {{MAX_FINDINGS}} findings, most severe first.
4. Confirm the `summary` agrees with the findings (no "looks good" beside a `blocker`).

## Checkpoints

None: the user decides what to do with the findings.

## Audit

| Check | Pass condition |
|---|---|
| Grounded | Every returned finding names a file you read, or is a `note` |
| Honest scale | No `blocker` without a read line that breaks the brief |
| Count | No more than {{MAX_FINDINGS}} findings |

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Checked findings | the turn's `issues` list and `summary` | Same shape as stage 2 |
