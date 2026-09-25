# 01 — Intake

Turn a raw request into a short task brief that the user agrees with. **Runs in the main session.**

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| User | Conversation | The request | What is wanted |
| Project | `../../../icm-project/PROJECT.md` | Components | Place the work |
| Project | `../../../icm-project/authority.md` | Full | Find the owning documents |
| Tracker | `../../scripts/board-snapshot.sh` output | Open items | Find duplicates and related work |

## Process

1. Restate the request in one sentence. Ask only the questions whose answers would change the brief.
2. Search for an existing issue first (`gh issue list --search "<terms>" --state all`). If one exists, the brief becomes an update to it.
3. Identify the owning document for each affected subject, using `authority.md`. Name the related register or decision IDs (for example LIVE-xx or SD-xx), if any.
4. Classify the work: Design, Implementation, Verification or Miscellaneous. Note whether it blocks a release.
5. Write the brief. **CHECKPOINT:** the user approves or edits it.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Task brief | `output/<slug>-brief.md` | Header block, then: Problem · Proposed outcome · Owning docs · Related issues/IDs · Category · Open questions |
