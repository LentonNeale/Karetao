# Routing — Layer 1

Match the request, then open only the listed contract.

| Request | Go to |
|---|---|
| New idea, bug, question or "we should…" | Suggest the user runs `workspace/scripts/liaison.sh` (a cheap Haiku intake session). If they'd rather stay here, follow `stages/01-intake/CONTEXT.md` directly |
| "take brief <slug>" | `stages/01-intake/CONTEXT.md`, orchestrator steps 4–6 |
| Create or update an issue, milestone or board fields from an agreed brief | `stages/02-issue-spec/CONTEXT.md` |
| Design or decision work on an existing issue | `stages/03-design/CONTEXT.md` |
| Implement an issue | `stages/04-implement/CONTEXT.md` |
| Build, test or collect evidence | `stages/05-verify/CONTEXT.md` |
| Finish an issue: acceptance criteria, evidence, close, register | `stages/06-close-out/CONTEXT.md` |
| Board review or status report (routine, not a stage) | Run `scripts/board-snapshot.sh`, then summarize against `../icm-project/github.md` |
| Doc link or consistency sweep (routine) | Run `scripts/link-check.py`; for content, delegate to `doc-checker` |

## Stage flow

```
01-intake → 02-issue-spec → 03-design → 04-implement → 05-verify → 06-close-out
```

Skip stages that don't apply (a tracking-only change goes 01 → 02). Never skip a CHECKPOINT.

## Artifact naming

`output/<issue#-or-slug>-<artifact>.md`. Start every artifact with a header block:

```
issue: #NN (or "none yet")
stage: NN-name
status: draft | approved | applied
```

## Always-available references

- `../icm-project/PROJECT.md` — project identity and components
- `../icm-project/authority.md` — which document owns which subject
- `../icm-project/github.md` — tracker conventions (IDs live in `github.env`)
- `../icm-project/build.md` — build and test commands
