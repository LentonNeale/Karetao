# 03 Check

Runs the step's checks after the change. No model runs here: the Portal does it, the same way
every time.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Settings | the `[commands] check` list (default: `verify`) | Full | Which commands to run; empty means skip |
| Tool card | icm/tools/run_tests.md | Run section | Documentation only: the Portal runs it; output is small (counts, failures) |
| Working copy | the change from stage 02 | Whole | What the commands run against |

## Process

1. Run each check command with `run_tests` in the working copy, stopping at the first failure.
2. Write `check.md`: per command, pass or fail, the summary line and the failures text.
3. On a failure, resume stage 02's session with only the failures text, then run the checks
   again. Do this at most `build_check_rounds` times (default 2).
4. If a check still fails, keep the failure in `check.md` and carry on to stage 04.

## Audit

| Check | Pass condition |
|---|---|
| Recorded | `check.md` exists, also when every check was skipped |
| Bounded | No more than `build_check_rounds` fix turns ran |

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Check result | `build/<step>/check.md` in the run folder | Markdown: status, then one section per command |
