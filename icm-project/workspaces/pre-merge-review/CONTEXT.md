# pre-merge-review — task routing

Reviewing one build's whole change before it is merged: what is wrong, what is missing, what
goes beyond the request.

## Task routing

| Task type | Go to | Description |
|---|---|---|
| Read | `stages/01-gather/CONTEXT.md` | Take in the brief, the plan, the design and the diff |
| Review | `stages/02-review/CONTEXT.md` | Compare the change with what was asked; one finding per problem, each with a severity |
| Check | `stages/03-check/CONTEXT.md` | Verify each finding against the code and drop the unfounded ones |

## Shared resources

| Resource | Location | Contains |
|---|---|---|
| Severity | `shared/severity.md` | What blocker, major, minor and note mean |
| References | `shared/references.md` | Which `icm-project/references/` note and section each code area must be checked against |
