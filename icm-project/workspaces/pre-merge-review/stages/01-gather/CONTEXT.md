# 01 Gather

Takes in what was asked for and what was changed before anything is judged.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Brief | the prompt | Full, with its "Done when" section | What the user asked for |
| Plan and design | the prompt | The plan steps and the accepted design points | What was agreed to build |
| Diff | the prompt | The changed-files list and the diff (it may be cut; the prompt says so) | What was actually changed |
| Project files | the working copy | Only the ranges you need | To check a claim the diff alone cannot settle |
| Severity | `../../shared/severity.md` | Full file | The scale findings use |

## Process

1. Read the brief and list, in your head, each thing it asks for.
2. Read the plan steps and accepted design points; note the files each one names.
3. Read the changed-files list, then the diff. If the diff was cut, Read the cut files directly.
4. Do not judge yet.

## Checkpoints

None: stages 1 to 3 run as one turn.

## Audit

| Check | Pass condition |
|---|---|
| Nothing assumed | Every statement about the code comes from the diff or a file you read |

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Understanding of the request and the change | working notes only | None kept |
