# ICM Engineering Workspace — Layer 0

This is an Interpretable Context Methodology (ICM) workspace: numbered stage folders, plain-Markdown contracts, and file-based handoffs. It turns requests into tracked engineering work and carries that work to close-out.

## Where things are

| Path | Layer | Purpose |
|---|---|---|
| `CONTEXT.md` | 1 | Routes a request to a stage or routine. Read it next. |
| `stages/NN-name/CONTEXT.md` | 2 | Stage contract: Inputs, Process, Outputs. |
| `stages/NN-name/references/`, `shared/` | 3 | Stable rules that are reusable across projects. |
| `../icm-project/` | 3 | **This project's specifics**: identity, GitHub config, authority map, build commands. |
| `stages/NN-name/output/` | 4 | Per-run artifacts. The output of stage N is input to stage N+1. Gitignored. |
| `agents/` | — | Subagent definitions, symlinked into `../.claude/agents/`. |
| `scripts/` | — | Mechanical work (board snapshot, field edits, link check). No model needed. |

This workspace is generic and is shared by several projects through `git subtree`. **Never write project-specific facts here.** They belong in `../icm-project/`.

## Operating rules

1. **Read down and stop.** Load only the layers and sections the current contract names.
2. **One home per fact.** GitHub issues, the project's authority docs, and `../icm-project/` are the sources of truth. Outputs link to them and don't copy them.
3. **Human checkpoints.** Stop at every stage boundary and at every contract step marked **CHECKPOINT**. Nothing reaches GitHub or authoritative docs without the user's approval.
4. **Scripts before models.** If a step is mechanical, run the script.
5. **No invented requirements.** Proposed or open items stay marked as proposed or open.

## Model delegation

The main session (the most capable model) plans, decides, reviews every delegated output, and talks to the user. Delegate work that is well defined and big enough to justify a cold start:

| Work | Agent | Model |
|---|---|---|
| Talk with the user until a request meets the Definition of Ready; write the brief (**its own main session** via `scripts/liaison.sh`, never spawned) | `client-liaison` | haiku |
| Create or edit issues, board fields, milestones, register rows from an approved spec | `issue-clerk` | sonnet |
| Consistency and link checks of docs against the authority map | `doc-checker` | sonnet |
| Builds, tests, evidence capture | `build-runner` | haiku |

Run a single command yourself rather than spawning an agent for it. Give the agent the contract path and the input file paths, not a restated summary.
