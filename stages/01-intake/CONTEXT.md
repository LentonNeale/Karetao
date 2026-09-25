# 01 — Intake

Turn a raw request into a brief that meets the Definition of Ready. **The Client Liaison runs this stage (haiku, as the main session via `scripts/liaison.sh`).** The orchestrator accepts the brief at the end of the stage.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| User | Conversation | The request | What is wanted |
| Stage reference | `references/definition-of-ready.md` | Full | The standard to meet |
| Project | `../../../icm-project/PROJECT.md` | Components | Name the "Where" |
| Project | `../../../icm-project/authority.md` | Subjects table | Name the owning docs |
| Tracker | `output/board.md` (written by the orchestrator from `../../scripts/board-snapshot.sh`) | Open items | Spot likely related issues |

## Process

**Liaison:**
1. Clarify the request conversationally until every Definition of Ready item is satisfied, or until the user says "send it".
2. Show the full brief. **CHECKPOINT:** the user confirms.
3. Write `output/<slug>-brief.md` with `status: ready` or `ready-with-gaps`.

**Orchestrator ("take brief <slug>"):**
4. Read the brief. Search the tracker for duplicates (`gh issue list --search … --state all`) and fill in *Related*.
5. Resolve the gaps: ask the user only about the items the liaison marked missing or flagged as questions.
6. Accept the brief (set `status: accepted`) and route it: to 02 for tracked work, or answer directly for pure questions.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Task brief | `output/<slug>-brief.md` | Exactly `references/brief-template.md`: a plain `key: value` header block, the ten Definition of Ready headings, then Open questions, Gaps and Revision log |
| Board snapshot | `output/board.md` | Written by the orchestrator whenever it refreshes the board; read-only for the liaison |
