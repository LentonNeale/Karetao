# implement-step

Carries out one plan step as four small stages: find the exact places to change, make the
change, check it, and report it. The Portal runs it once per build card; a reviewer sees only the
final report.

## Folder map

- [CLAUDE.md](CLAUDE.md): you are here
- [CONTEXT.md](CONTEXT.md): which stage handles which task
- [setup/questionnaire.md](setup/questionnaire.md): one-time settings (run once)
- [stages/01-locate/](stages/01-locate/CONTEXT.md): find the places to change
- [stages/02-change/](stages/02-change/CONTEXT.md): make the change
- [stages/03-check/](stages/03-check/CONTEXT.md): run the checks, feed failures back
- [stages/04-report/](stages/04-report/CONTEXT.md): the card report

## Triggers

| Keyword | Action |
|---|---|
| `setup` | Read setup/questionnaire.md, ask every question in one pass, replace the placeholders it names, then scan for any `{{...}}` left over |
| `status` | List each `stages/*/output/` folder; a folder holding more than `.gitkeep` is done, otherwise it is pending |

## Routing

See CONTEXT.md. Rules this workspace follows live in icm/_core/CONVENTIONS.md.
