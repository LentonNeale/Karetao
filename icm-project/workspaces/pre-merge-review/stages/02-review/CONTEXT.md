# 02 Review

Compares the change with what was asked and lists the problems, each with a severity.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Understanding | stage 1 | The request and the change | What to compare |
| Severity | `../../shared/severity.md` | Full file | The scale to use |
| References | `../../shared/references.md` | Only the rows for the code areas the diff touches, then only the note and section each row names | To judge a register, command, timing or API use against its source |

## Process

1. For each thing the brief asks for, find the change that does it. A missing one is a finding.
2. For each accepted design point, check the change follows it. A departure is a finding.
3. Look for defects in the changed code: wrong results, unhandled errors, leftover debugging, a
   changed behaviour nobody asked for, tests that no longer match.
4. Write one finding per problem: `severity`, a short `title`, a `detail` of one to three plain
   sentences, and the `file` (with a line range when you read one; empty for a whole-change point).
5. At most {{MAX_FINDINGS}} findings, most severe first. Also write a `summary` of two sentences:
   whether the change does what was asked, and the most important thing to look at.
6. Say nothing about style the project does not already enforce.

## Checkpoints

None: stages 1 to 3 run as one turn.

## Audit

| Check | Pass condition |
|---|---|
| Count | No more than {{MAX_FINDINGS}} findings |
| Scale | Every `severity` is `blocker`, `major`, `minor` or `note` |
| Read-only | Nothing was edited and no command was run |

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Findings | stage 3 returns them | Structured `{summary, issues: [{severity, title, detail, file}]}` |
