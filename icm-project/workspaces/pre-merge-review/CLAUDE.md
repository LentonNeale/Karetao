# pre-merge-review

Reads a finished build's whole change against the brief, the plan and the accepted design, and
lists what a careful reviewer would want fixed or checked before it is merged, each with a severity.

## Folder map

- [CLAUDE.md](CLAUDE.md): you are here
- [CONTEXT.md](CONTEXT.md): task routing to stages
- [setup/questionnaire.md](setup/questionnaire.md): onboarding questions (run once)
- [shared/severity.md](shared/severity.md): what each severity means
- [skills/](skills/): skills this workspace alone needs
- [stages/01-gather/](stages/01-gather/CONTEXT.md): read the brief, the plan, the design and the diff
- [stages/02-review/](stages/02-review/CONTEXT.md): compare the change with what was asked and list findings
- [stages/03-check/](stages/03-check/CONTEXT.md): check each finding against the code before returning

## Triggers

| Keyword | Action |
|---|---|
| `setup` | Read `setup/questionnaire.md`, ask every question in one pass, replace the placeholders it names, then scan for any `{{...}}` left over |
| `status` | List each `stages/*/output/` folder; a folder holding more than the placeholder file is done, otherwise it is pending |

## Read-only

This workspace never edits anything and never runs git. You have read-only tools (Read, Grep,
Glob). The Portal supplies the diff, the brief, the plan and the design in the prompt and runs
stages 1 to 3 as one turn; the user decides what to do with the findings. Write for a person who
is not a developer: say what is wrong and where, and say when something is your opinion rather
than a fact from a file.

## Routing

See `CONTEXT.md` for which stage handles which kind of task. Rules this workspace follows live in
the repo's `icm/_core/CONVENTIONS.md` — this file does not repeat them.
