# 02 Change

Makes the step's change, working from the located places. The Portal runs the checks after you
finish and may send you their failures.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Prompt | the step and its design points | Full | What to change and the decisions already made |
| Prompt | the code map for this step (when given) | Full | Ranges for anything beyond context.md |
| Locate output | `build/<step>/context.md` (in the prompt) | Full | The ranges to read first |
| Project files | the ranges in context.md | Those ranges only, at first | The code to change |
| References | `../../shared/references.md` | Only the rows for the code areas this step touches, then only the note and section each row names | Datasheet, protocol and API facts the change must match; never values from memory |

## Process

1. Read the ranges in context.md (offset and limit) and make the smallest change that carries out
   the design points. Never read a file over {{WHOLE_FILE_LINES}} lines whole.
2. Read beyond context.md only if it proves wrong or incomplete; then say so in `notes`.
3. Run tests only if a specific doubt needs it, and only through `run_tests`, using the one-test-
   file command in the prompt; the Portal runs the full suite after you. To check an import or a
   function, run a test file that does it (add one when the step adds code); never `python -c`. A
   refused command won't work if you retry it: use one of the allowed commands instead.
4. If a check failure is sent back, fix that failure only, then answer again in the same form.
5. If the step cannot be done as designed, stop and say why in `notes`.

## Audit

| Check | Pass condition |
|---|---|
| Scope | Only files the design points and context.md cover were changed |
| Honest | `notes` names every place you read beyond context.md |

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Change | the working copy (the Portal stages it) | Edited files |
| Answer | structured output | `work_summary` (2 to 5 plain sentences), `notes` |
