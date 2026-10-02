# 01 Locate

Finds the exact places a step's change goes, so the change stage can read those and little else.
You only read; you never edit.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Prompt | the step, its inputs, its design points | Full | What is to change, and where the design says |
| Prompt | the code map for this step and the exact `code_map` command | Full | Definitions with line ranges; nothing to look up in the project |
| Project files | the step's inputs (`path` or `path:start-end`) | Only the ranges you need | Where the change goes |
| References | `../../shared/references.md` | Only the rows for the code areas this step touches, then only the note and section each row names | Datasheet, protocol and API facts the change must match; never values from memory |

## Process

1. Use the code map slice in the prompt for each input's names, and the `code_map` command from
   the prompt for any file it lacks, before reading it. Never read `code-map.md` whole; use the
   slice in your prompt, or run `code_map` on one file. A range given in an input is a hint,
   not a limit.
2. Read only the ranges you need to decide (offset and limit). Never read a file over
   {{WHOLE_FILE_LINES}} lines whole.
3. Use Grep for a name the inputs do not point to (a caller, a test, a constant).
4. List at most {{MAX_LOCATIONS}} locations: `file`, `start`, `end` (1-based, inclusive) and `why`.
   Give the narrowest range that holds the code to change, or the code to copy a pattern from.
5. `notes`: assumptions, or something you looked for and could not find. Empty if nothing.

## Audit

| Check | Pass condition |
|---|---|
| Ranges | Every `start` is at most its `end` and inside the file |
| Count | No more than {{MAX_LOCATIONS}} locations |
| Read-only | Nothing was edited |

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Context | `build/<step>/context.md` in the run folder (the Portal writes it from your answer) | Structured `{locations: [{file, start, end, why}], notes}` |
