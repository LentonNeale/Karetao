# implement-step: task routing

One plan step per run, in order: locate, change, check, report. Each stage starts fresh and
reads only the file the stage before it left.

| Task | Go to | Description |
|---|---|---|
| Find where a step's change goes | stages/01-locate/CONTEXT.md | List file ranges and why, from the step's inputs |
| Make the change | stages/02-change/CONTEXT.md | Edit using only the located ranges |
| Run the checks | stages/03-check/CONTEXT.md | Run the tests, send failures back to the change |
| Write the card report | stages/04-report/CONTEXT.md | One page for the reviewer |

## Shared resources

| Resource | Location | Contains |
|---|---|---|
| Tools | icm/tools/ (`code_map`, `run_tests`, `diff_summary`) | For a model turn (01, 02) the code map path and the exact commands are given in the prompt; do not read the cards. Stages 03 and 04 are Portal-run, so their tool-card rows are documentation only |
| References | `shared/references.md` | Which `icm-project/references/` note and section each code area must be checked against |
